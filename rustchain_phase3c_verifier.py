#!/usr/bin/env python3
"""
RustChain Phase 3c — real-time variant verifier.

Tails the live Xonotic server log AND the static variant pool. When the QC
story system emits a `=== SPEAKER ===` actor print, this script:
  1. Captures the body line
  2. Looks up the variant pool for that speaker
  3. Reports which variant slot was selected (original / LLM #1 / #2 / #3)

Lets Scott see the variant pool fire in real-time on a second terminal
while playing the game in another window. No game modification — purely
observational.

Usage:
    python3 rustchain_phase3c_verifier.py             # default paths
    python3 rustchain_phase3c_verifier.py --pool mapping/dialogue_pool.json

Env:
    XONOTIC_LOG       default ~/.xonotic/data/server.log
    VERIFIER_POOL     default mapping/dialogue_pool.json
"""
import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

# Match the bprint header from RustchainStory_PrintBlock:
#   "^3=== SPEAKER ===^7\n<body>\n"
SPEAKER_HEADER_RE = re.compile(r"=== (SOPHIA|BB_D|BORIS|SURVIVOR|ARCHIVIST|VOSSL|PLAYER|NARRATOR) ===")
COLOR_CODE_RE = re.compile(r"\^\d")
KNOWN_SPEAKERS = {"SOPHIA", "BB_D", "BORIS", "SURVIVOR", "ARCHIVIST", "VOSSL", "PLAYER", "NARRATOR"}

# Map QC ActorHeader to packager speaker tag (lowercased)
SPEAKER_TAG = {
    "SOPHIA": "sophia",
    "BB_D": "bbd",
    "BORIS": "boris",
    "SURVIVOR": "survivor",
    "ARCHIVIST": "archivist",
    "VOSSL": "vossl",
    "NARRATOR": "narrator",
    "PLAYER": "sophia",   # PrintActor maps PLAYER → SOPHIA personality in dialogue
}


def strip_color(s: str) -> str:
    return COLOR_CODE_RE.sub("", s).rstrip()


def load_pool(pool_path: Path) -> dict:
    """Returns dict keyed by speaker tag → list of {original, variants[]} dicts.
    For verification we don't need (map, targetname) — body match by line text
    is enough since LLM-generated lines are distinct."""
    raw = json.loads(pool_path.read_text(encoding="utf-8"))
    by_speaker = {}
    for entry in raw.get("entries", []):
        sp = entry.get("speaker", "").lower()
        by_speaker.setdefault(sp, []).append({
            "map": entry.get("map", ""),
            "targetname": entry.get("targetname", ""),
            "original": entry.get("original", "").strip(),
            "variants": [v.strip() for v in entry.get("variants", [])],
        })
    return by_speaker


def identify_variant(speaker_tag: str, body: str, pool: dict):
    """Search the speaker's pool for a matching variant.
    Returns (entry, variant_index) or (None, None) if no match."""
    candidates = pool.get(speaker_tag, [])
    if not candidates:
        return None, None
    for entry in candidates:
        for i, v in enumerate(entry["variants"]):
            if v == body:
                return entry, i
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", default=os.environ.get("XONOTIC_LOG",
                    os.path.expanduser("~/.xonotic/data/server.log")))
    ap.add_argument("--pool", default=os.environ.get("VERIFIER_POOL",
                    "mapping/dialogue_pool.json"))
    args = ap.parse_args()

    log_path = Path(args.log)
    pool_path = Path(args.pool)

    if not pool_path.exists():
        print(f"[verifier] pool not found: {pool_path}", file=sys.stderr)
        sys.exit(2)

    pool = load_pool(pool_path)
    total_entries = sum(len(v) for v in pool.values())
    print(f"[verifier] loaded pool: {total_entries} dialogue entries across "
          f"{len(pool)} speakers: {sorted(pool.keys())}", flush=True)

    print(f"[verifier] watching {log_path}", flush=True)
    if not log_path.exists():
        print(f"[verifier] log not yet present — waiting...", flush=True)

    stats = Counter()  # (speaker, variant_index) → count
    pending_speaker = None

    while not log_path.exists():
        time.sleep(2)

    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)  # tail mode
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.3)
                continue
            stripped = strip_color(line)
            m = SPEAKER_HEADER_RE.search(stripped)
            if m:
                pending_speaker = m.group(1)
                continue
            # Body follows the header. Skip empty + obvious noise.
            if pending_speaker and stripped and not stripped.startswith("==="):
                speaker_header = pending_speaker
                body = stripped.strip()
                pending_speaker = None
                if len(body) < 3:
                    continue

                tag = SPEAKER_TAG.get(speaker_header, speaker_header.lower())
                entry, idx = identify_variant(tag, body, pool)
                if entry is None:
                    print(f"\n  ⚠️  UNMATCHED {speaker_header}: {body!r}\n"
                          f"     (no entry in pool with this body; may be the "
                          f"dialogue director's runtime LLM commentary OR a non-"
                          f"campaign line)", flush=True)
                    continue

                label = "ORIGINAL" if idx == 0 else f"VARIANT #{idx}"
                stats[(tag, idx)] += 1
                source_map = entry["map"]
                target = entry["targetname"]
                pool_size = len(entry["variants"])
                print(f"\n  ✅ {speaker_header}  [{source_map}/{target}]  → {label} "
                      f"(of {pool_size})", flush=True)
                print(f"     {body}", flush=True)
                # Print other unselected variants for comparison (truncated)
                print(f"     pool had:", flush=True)
                for i, v in enumerate(entry["variants"]):
                    marker = " <" if i == idx else "  "
                    print(f"       [{i}]{marker} {v[:80]}", flush=True)

                # Periodic stats
                total = sum(stats.values())
                if total % 5 == 0:
                    print(f"\n[verifier stats] {total} matches  "
                          f"originals={sum(c for (_,i),c in stats.items() if i==0)}  "
                          f"variants={sum(c for (_,i),c in stats.items() if i>0)}",
                          flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[verifier] interrupted")
        sys.exit(0)
