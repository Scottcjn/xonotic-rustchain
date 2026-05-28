#!/usr/bin/env python3
"""
RustChain Story — extract target_rustchain_dialogue entities from .map files.

Walks `mapping/maps/*.map` (Quake-format BSP source) and produces a
manifest JSON consumable by `rustchain_dialogue_packager.py batch`:

  {
    "entries": [
      {"map": "elyan_labs",
       "targetname": "elyan_intro",
       "speaker": "sophia",
       "scenario": "intro",
       "original": "Power readings are unstable. Find the RustChain node..."},
      ...
    ]
  }

Scenarios are guessed from `targetname` substrings (intro / followup / wave /
log / exit / outro). When no scenario word matches, falls back to "general".

Usage:
  python3 rustchain_map_extractor.py \\
      --maps mapping/maps/elyan_labs.map mapping/maps/first_signal.map \\
      --out /tmp/dialogue_manifest.json

  python3 rustchain_map_extractor.py --all-story \\
      --out data/dialogue_manifest.json
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

# A .map entity block: { "key" "value" ... } with optional brushes between.
# We only care about the simple key/value pairs at the top of each entity.
ENTITY_RE = re.compile(r"\{([^{}]*?)\}", re.DOTALL)
KV_RE = re.compile(r'"([^"]+)"\s+"([^"]*)"')

STORY_MAPS = ("chambers_ruins", "elyan_labs", "first_signal", "museum_vault")

SCENARIO_HINTS = (
    ("intro", "intro"),
    ("followup", "followup"),
    ("outro", "outro"),
    ("exit", "exit"),
    ("log", "log"),
    ("wave", "wave"),
    ("actor", "encounter"),
    ("survivor", "survivor"),
    ("bbd", "bbd"),
    ("boris", "boris"),
    ("relay", "relay"),
    ("node", "node"),
)


def parse_entities(map_path: Path):
    """Yield dicts of key/value pairs for each entity block in the .map file."""
    text = map_path.read_text(encoding="utf-8", errors="ignore")
    for block in ENTITY_RE.findall(text):
        kvs = dict(KV_RE.findall(block))
        if kvs:
            yield kvs


def guess_scenario(targetname: str) -> str:
    t = (targetname or "").lower()
    for hint, label in SCENARIO_HINTS:
        if hint in t:
            return label
    return "general"


def normalize_speaker(raw: str) -> str:
    """Map QC ActorHeader tags to packager personality keys."""
    s = (raw or "").strip().lower()
    if s in {"bb_d", "bbd"}:
        return "bbd"
    if s in {"sophia", "boris", "survivor", "archivist", "vossl", "narrator"}:
        return s
    if s == "player":
        # Treat the player slot as narrator for generation purposes
        return "narrator"
    return "sophia"  # safe fallback


def extract_map(map_path: Path) -> list:
    map_name = map_path.stem
    out = []
    for ent in parse_entities(map_path):
        if ent.get("classname") != "target_rustchain_dialogue":
            continue
        speaker = normalize_speaker(ent.get("message", "sophia"))
        original = ent.get("netname", "").strip()
        if not original:
            continue
        out.append({
            "map": map_name,
            "targetname": ent.get("targetname", ""),
            "speaker": speaker,
            "scenario": guess_scenario(ent.get("targetname", "")),
            "original": original,
        })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--maps", nargs="+", help="explicit map file paths")
    g.add_argument("--all-story", action="store_true",
                   help="use the canonical 4 RustChain story maps in mapping/maps/")
    ap.add_argument("--out", required=True, help="output manifest JSON path")
    args = ap.parse_args()

    if args.all_story:
        base = Path("mapping/maps")
        paths = [base / f"{n}.map" for n in STORY_MAPS]
    else:
        paths = [Path(p) for p in args.maps]

    missing = [p for p in paths if not p.exists()]
    if missing:
        print(f"[extractor] missing: {missing}", file=sys.stderr)
        sys.exit(2)

    all_entries = []
    for p in paths:
        entries = extract_map(p)
        print(f"[extractor] {p.name}: {len(entries)} dialogue entities", file=sys.stderr)
        all_entries.extend(entries)

    manifest = {"entries": all_entries}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"[extractor] wrote {len(all_entries)} entries → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
