#!/usr/bin/env python3
"""Test the Quake MCP tools directly without the decorator overhead."""

import os
import json
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configuration
XONOTIC_DIR = Path("/home/scott/Games/Xonotic")
MAPPING_DIR = XONOTIC_DIR / "mapping" / "maps"
DATA_DIR = XONOTIC_DIR / "data"
MAPS_OUTPUT_DIR = DATA_DIR / "maps"
Q3MAP2 = XONOTIC_DIR / "source" / "netradiant_1.5.0-20220628-linux-amd64" / "q3map2"
QCSRC_DIR = XONOTIC_DIR / "source" / "qcsrc"

def list_maps():
    """List all available .map source files."""
    maps = list(MAPPING_DIR.glob("*.map"))
    if not maps:
        return "No .map files found."

    result = "Available map files:\n"
    for m in sorted(maps):
        size = m.stat().st_size
        result += f"  - {m.name} ({size:,} bytes)\n"
    return result

def get_valid_texture_sets():
    """Get available texture sets."""
    texture_sets = set()
    for pk3 in DATA_DIR.glob("*.pk3"):
        try:
            with zipfile.ZipFile(pk3, 'r') as zf:
                for name in zf.namelist():
                    if "textures/" in name and ".dds" in name:
                        parts = name.split("textures/")
                        if len(parts) > 1:
                            set_name = parts[1].split("/")[0]
                            if set_name and not set_name.endswith(".dds"):
                                texture_sets.add(set_name)
        except:
            continue

    result = "Available texture sets:\n"
    for ts in sorted(texture_sets)[:30]:
        result += f"  - {ts}\n"
    return result

def search_qc(pattern):
    """Search QuakeC files."""
    results = []
    count = 0

    for qc_file in QCSRC_DIR.rglob("*.qc"):
        try:
            content = qc_file.read_text()
            for i, line in enumerate(content.split('\n'), 1):
                if pattern.lower() in line.lower():
                    rel_path = qc_file.relative_to(QCSRC_DIR)
                    results.append(f"{rel_path}:{i}: {line.strip()[:80]}")
                    count += 1
                    if count >= 20:
                        return f"Found {count}+ matches:\n" + '\n'.join(results)
        except:
            continue

    if not results:
        return f"No matches for '{pattern}'"
    return f"Found {count} matches:\n" + '\n'.join(results)

if __name__ == "__main__":
    print("=== Testing Quake MCP Tools ===\n")

    print("1. List maps:")
    print(list_maps())

    print("\n2. Available texture sets:")
    print(get_valid_texture_sets())

    print("\n3. Search QuakeC for 'mutator':")
    print(search_qc("mutator"))

    print("\n4. Paths configured:")
    print(f"   XONOTIC_DIR: {XONOTIC_DIR}")
    print(f"   MAPPING_DIR: {MAPPING_DIR}")
    print(f"   Q3MAP2: {Q3MAP2} (exists: {Q3MAP2.exists()})")
    print(f"   QCSRC_DIR: {QCSRC_DIR} (exists: {QCSRC_DIR.exists()})")
