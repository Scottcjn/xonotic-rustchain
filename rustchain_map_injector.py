#!/usr/bin/env python3
"""
RustChain Story — inject LLM-generated variant pools into .map files.

Reads a pool JSON (output of `rustchain_dialogue_packager.py batch`),
matches each entry back to its `target_rustchain_dialogue` entity in the
source .map files via `(map, targetname)`, and rewrites the entity's
`netname` to the pipe-joined variant string. Original .map is preserved
as `<name>.map.bak.<unixts>` before any write.

After injection, the maps must be recompiled to .bsp by q3map2 (the
heavy step — minutes per map). This tool only does the source rewrite.

Usage:
  python3 rustchain_map_injector.py \\
      --pool /tmp/dialogue_pool.json \\
      --map-dir mapping/maps \\
      [--dry-run]
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

# Entity block regex (same as extractor). Captures the inner k/v body for rewrite.
ENTITY_RE = re.compile(r"(\{[^{}]*?\})", re.DOTALL)
TARGETNAME_RE = re.compile(r'"targetname"\s+"([^"]+)"')
CLASSNAME_RE = re.compile(r'"classname"\s+"([^"]+)"')
NETNAME_RE = re.compile(r'("netname"\s+")([^"]*)(")')


def load_pool(pool_path: Path):
    """Load a pool JSON and return a dict {(map, targetname): netname_pipe_joined}."""
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    out = {}
    for entry in pool.get("entries", []):
        tname = entry.get("targetname")
        m = entry.get("map")
        netname = entry.get("netname")
        if not (m and tname and netname):
            continue
        out[(m, tname)] = netname
    return out


def rewrite_block(block: str, lookup_map: str, lookup: dict) -> tuple:
    """If this entity block is a target_rustchain_dialogue and we have a pool
    entry for it, rewrite its netname. Returns (new_block, replaced_bool)."""
    cm = CLASSNAME_RE.search(block)
    if not cm or cm.group(1) != "target_rustchain_dialogue":
        return block, False
    tm = TARGETNAME_RE.search(block)
    if not tm:
        return block, False
    tname = tm.group(1)
    new_netname = lookup.get((lookup_map, tname))
    if not new_netname:
        return block, False
    # Escape backslashes/quotes for safe write
    safe = new_netname.replace("\\", "\\\\").replace('"', '\\"')
    new_block, count = NETNAME_RE.subn(rf'\g<1>{safe}\g<3>', block, count=1)
    if count == 0:
        # entity didn't have a netname key — add one
        new_block = block.rstrip()
        if new_block.endswith("}"):
            new_block = new_block[:-1].rstrip() + f'\n"netname" "{safe}"\n}}'
    return new_block, True


def process_map(map_path: Path, pool: dict, dry_run: bool) -> int:
    """Rewrite the given .map file in place. Returns count of entities updated."""
    name = map_path.stem
    text = map_path.read_text(encoding="utf-8", errors="ignore")

    parts = []
    last = 0
    replacements = 0
    for m in ENTITY_RE.finditer(text):
        parts.append(text[last:m.start()])
        block, replaced = rewrite_block(m.group(1), name, pool)
        parts.append(block)
        if replaced:
            replacements += 1
        last = m.end()
    parts.append(text[last:])
    new_text = "".join(parts)

    if replacements == 0:
        print(f"[injector] {map_path.name}: no pool entries matched", file=sys.stderr)
        return 0

    if dry_run:
        print(f"[injector] DRY {map_path.name}: would inject {replacements} entries",
              file=sys.stderr)
        return replacements

    backup = map_path.with_suffix(map_path.suffix + f".bak.{int(time.time())}")
    backup.write_bytes(map_path.read_bytes())
    map_path.write_text(new_text, encoding="utf-8")
    print(f"[injector] {map_path.name}: injected {replacements} entries  (backup: {backup.name})",
          file=sys.stderr)
    return replacements


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pool", required=True, help="pool JSON from packager batch mode")
    ap.add_argument("--map-dir", default="mapping/maps",
                    help="directory containing the .map files")
    ap.add_argument("--dry-run", action="store_true", help="report changes without writing")
    args = ap.parse_args()

    pool_path = Path(args.pool)
    if not pool_path.exists():
        print(f"[injector] pool not found: {pool_path}", file=sys.stderr)
        sys.exit(2)
    map_dir = Path(args.map_dir)
    if not map_dir.is_dir():
        print(f"[injector] map dir not found: {map_dir}", file=sys.stderr)
        sys.exit(2)

    pool = load_pool(pool_path)
    print(f"[injector] pool has {len(pool)} (map, targetname) keys", file=sys.stderr)

    # Group pool keys by map for efficiency
    maps_to_touch = {m for (m, _) in pool}
    total = 0
    for name in sorted(maps_to_touch):
        mp = map_dir / f"{name}.map"
        if not mp.exists():
            print(f"[injector] skip {name}: {mp} not found", file=sys.stderr)
            continue
        total += process_map(mp, pool, args.dry_run)

    verb = "would update" if args.dry_run else "updated"
    print(f"[injector] {verb} {total} dialogue entities across {len(maps_to_touch)} maps",
          file=sys.stderr)


if __name__ == "__main__":
    main()
