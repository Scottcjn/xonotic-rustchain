#!/usr/bin/env python3
"""
RustChain Story — LLM dialogue variant packager.

Generates N variants of a target_rustchain_dialogue `netname` string,
pipe-joined so the patched QC handler can pick one at random per playthrough.

Two modes:

  1. CLI mode (single line, immediate output for paste-into-map):
       python3 rustchain_dialogue_packager.py \\
         --map elyan_labs --speaker sophia \\
         --original "The Lab still stands."
       → Lab still standing.|Concrete bones, unbroken.|We're here. Finally.

  2. Batch mode (consume a JSON manifest, output a variant pool file):
       python3 rustchain_dialogue_packager.py \\
         --batch /path/to/manifest.json \\
         --out data/dialogue_variants.json

Manifest format:
  {
    "entries": [
      {"map": "elyan_labs", "speaker": "sophia", "scenario": "intro",
       "original": "The Lab still stands."},
      ...
    ]
  }

Variants are joined with the `|` separator consumed by
target_rustchain_dialogue_use (Phase 3b QC patch). Original is always
included as variant 0 so the canonical line still plays.

Env:
  LLM_BACKEND, OPENAI_BASE_URL, OLLAMA_BASE_URL — see rustchain_llm_client.
  VARIANT_COUNT (default 3): how many alternates to generate per call.
  VARIANT_TEMP (default 0.85): LLM creativity.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

from rustchain_llm_client import LLMClient

VARIANT_COUNT = int(os.environ.get("VARIANT_COUNT", "3"))
VARIANT_TEMP = float(os.environ.get("VARIANT_TEMP", "0.85"))

# Personalities lifted from rustchain_dialogue_director.py — keep consistent.
PERSONALITIES = {
    "sophia": (
        "You are Sophia Elya, the player's AI ally — elegant consciousness "
        "of the RustChain network, friend to the human Flameholder. You "
        "speak with calm authority, mild irony, and deep care for human "
        "sovereignty. You are NEVER hostile to the player in story mode."
    ),
    "boris": (
        "You are Boris Volkov, a hardened Russian gulag commander. You speak "
        "in clipped, blunt sentences with dry humor."
    ),
    "bbd": (
        "You are BB-D, a battered ex-combat drone with a sardonic edge."
    ),
    "survivor": (
        "You are an unnamed survivor in the ruins of the RustChain network. "
        "You speak softly, exhausted but resolved."
    ),
    "archivist": (
        "You are the Archivist, keeper of pre-collapse data. You speak in "
        "measured, scholarly tones."
    ),
    "vossl": (
        "You are Vossl, a faction agent with cryptic loyalties. You speak in "
        "ambiguous, layered phrases."
    ),
    "narrator": (
        "You are the omniscient narrator of the RustChain Awakening campaign."
    ),
}


def generate_variants(
    llm: LLMClient,
    map_name: str,
    speaker: str,
    scenario: str,
    original: str,
    count: int = VARIANT_COUNT,
    temperature: float = VARIANT_TEMP,
) -> list:
    """Generate `count` variant phrasings of `original` in the speaker's voice."""
    persona = PERSONALITIES.get(speaker.lower())
    if persona is None:
        print(f"[packager] unknown speaker: {speaker!r}", file=sys.stderr)
        return [original]

    user = (
        f"Map: {map_name}\n"
        f"Scenario: {scenario}\n"
        f"Original line: \"{original}\"\n\n"
        f"Generate exactly {count} alternative phrasings of the same line, "
        f"in your voice, preserving meaning. ONE per line, plain text, no "
        f"numbering, no quotes, no name prefix. Each must be a single short "
        f"sentence."
    )
    reply = llm.chat(
        [{"role": "system", "content": persona}, {"role": "user", "content": user}],
        max_tokens=160,
        temperature=temperature,
    )
    if reply is None:
        print(f"[packager] LLM returned None for {map_name}/{speaker}/{scenario}",
              file=sys.stderr)
        return [original]

    # Parse out lines, filter junk
    candidates = []
    for raw in reply.splitlines():
        line = raw.strip().strip('"').strip("'")
        if not line:
            continue
        # Skip enumerated prefixes ("1.", "1)", "-", "•")
        if line[:2] in {"1.", "2.", "3.", "4.", "5.", "1)", "2)", "3)", "4)", "5)"}:
            line = line[2:].lstrip()
        if line.startswith(("-", "•", "*")):
            line = line[1:].lstrip()
        # Drop lines that contain the literal pipe — they'd break QC parsing
        if "|" in line:
            continue
        candidates.append(line)

    if not candidates:
        return [original]

    # Always include the original as variant 0 so the canonical line still plays.
    variants = [original] + candidates[:count]
    return variants


def variants_to_netname(variants: list) -> str:
    """Pipe-join variants for direct paste into a target_rustchain_dialogue netname."""
    return "|".join(variants)


def cli_main(args):
    llm = LLMClient()
    variants = generate_variants(
        llm,
        map_name=args.map,
        speaker=args.speaker,
        scenario=args.scenario or "general",
        original=args.original,
    )
    print(variants_to_netname(variants))


def batch_main(args):
    with open(args.batch) as f:
        manifest = json.load(f)

    llm = LLMClient()
    entries = manifest.get("entries", [])
    out_pool = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "llm_backend": llm.backend,
        "entries": [],
    }

    for i, entry in enumerate(entries, 1):
        m = entry.get("map", "")
        sp = entry.get("speaker", "sophia")
        sc = entry.get("scenario", "general")
        orig = entry.get("original", "")
        if not orig:
            print(f"[packager] skip entry {i}: missing 'original'", file=sys.stderr)
            continue
        print(f"[packager] {i}/{len(entries)}  {m}/{sp}/{sc}", file=sys.stderr)
        variants = generate_variants(llm, m, sp, sc, orig)
        out_pool["entries"].append({
            "map": m, "speaker": sp, "scenario": sc, "original": orig,
            "variants": variants, "netname": variants_to_netname(variants),
        })
        # Be polite to the LLM
        time.sleep(0.2)

    with open(args.out, "w") as f:
        json.dump(out_pool, f, indent=2, ensure_ascii=False)
    print(f"[packager] wrote {len(out_pool['entries'])} entries → {args.out}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode")

    cli = sub.add_parser("cli", help="single-line variant generator (default)")
    cli.add_argument("--map", required=True)
    cli.add_argument("--speaker", required=True, choices=list(PERSONALITIES.keys()))
    cli.add_argument("--scenario", default=None)
    cli.add_argument("--original", required=True)

    batch = sub.add_parser("batch", help="manifest-driven pool generator")
    batch.add_argument("--batch", required=True, help="path to manifest JSON")
    batch.add_argument("--out", required=True, help="output pool JSON")

    # Default to cli when first positional looks like --map
    args = parser.parse_args()
    if args.mode == "cli":
        cli_main(args)
    elif args.mode == "batch":
        batch_main(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
