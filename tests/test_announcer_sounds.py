#!/usr/bin/env python3
"""Verify the RustChain announcer cue pack ships all required files.

Run: python tests/test_announcer_sounds.py [--ffprobe path/to/ffprobe]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
ANNOUNCER_DIR = REPO / "pk3_build" / "sound" / "announcer" / "rustchain"
REQUIRED = {
    "begin.ogg",
    "prepare.ogg",
    "go.ogg",
    "firstblood.ogg",
    "impressive.ogg",
    "excellent.ogg",
    "humiliation.ogg",
    "lead_taken.ogg",
    "lead_lost.ogg",
    "1.ogg",
    "2.ogg",
    "3.ogg",
    "4.ogg",
    "5.ogg",
}


def fail(message: str) -> None:
    print(f"  FAIL: {message}")
    sys.exit(1)


def probe(path: Path, ffprobe: str) -> tuple[str, str, str]:
    out = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,sample_rate,channels",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    codec, sample_rate, channels = out.stdout.strip().splitlines()
    return codec, sample_rate, channels


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffprobe", default=shutil.which("ffprobe"))
    args = parser.parse_args()

    print("RustChain announcer cue pack test")
    missing = sorted(name for name in REQUIRED if not (ANNOUNCER_DIR / name).is_file())
    if missing:
        fail(f"missing required cues: {missing}")
    print(f"  [1/2] all {len(REQUIRED)} required cues exist - OK")

    if args.ffprobe:
        for name in sorted(REQUIRED):
            codec, sample_rate, channels = probe(ANNOUNCER_DIR / name, args.ffprobe)
            if (codec, sample_rate, channels) != ("vorbis", "48000", "1"):
                fail(f"{name} is {codec}/{sample_rate}Hz/{channels}ch, expected vorbis/48000Hz/1ch")
        print("  [2/2] all cues are mono 48 kHz OGG Vorbis - OK")
    else:
        print("  [2/2] ffprobe absent, codec check skipped")

    print("PASS")


if __name__ == "__main__":
    main()
