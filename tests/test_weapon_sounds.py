#!/usr/bin/env python3
"""Verify the RustChain weapon sound set is wired into the weapon system.

Checks (no game build required):
  1. Every gameplay weapon has a fire sound mapping.
  2. Every mapped sound file actually ships in pk3_build/sound/.
  3. Each file is a real OGG (Vorbis) when `ffprobe` is available.

Run: python3 tests/test_weapon_sounds.py   (exit 0 = pass)
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import rustchain_weapons as rw  # noqa: E402

SOUND_ROOT = REPO / "pk3_build" / "sound"
WEAPON_KEYS = {"validator", "forker", "hashcannon", "mempool_grenade", "double_spend"}


def fail(msg: str) -> None:
    print(f"  FAIL: {msg}")
    sys.exit(1)


def main() -> None:
    print("RustChain weapon-sound integration test")

    # 1. Every gameplay weapon is mapped to a sound.
    missing = WEAPON_KEYS - set(rw.WEAPON_SOUNDS)
    if missing:
        fail(f"weapons with no fire sound: {sorted(missing)}")
    print(f"  [1/3] all {len(WEAPON_KEYS)} weapons mapped to a sound — OK")

    # 2. Every mapped file exists under pk3_build/sound/.
    ffprobe = shutil.which("ffprobe")
    for key, vfs in rw.WEAPON_SOUNDS.items():
        path = SOUND_ROOT / vfs
        if not path.is_file():
            fail(f"{key} -> {vfs} missing on disk ({path})")
        # 3. Validate it's a real OGG when tooling is present.
        if ffprobe:
            out = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries",
                 "stream=codec_name", "-of", "default=nw=1:nk=1", str(path)],
                capture_output=True, text=True,
            )
            if "vorbis" not in out.stdout:
                fail(f"{vfs} is not OGG Vorbis (got: {out.stdout.strip()!r})")
    label = "exist + valid OGG" if ffprobe else "exist (ffprobe absent, skipped codec check)"
    print(f"  [2/3] all sound files {label} — OK")

    # 4. The cfg generator emits the fire-sound cvars and the API exposes them.
    cfg = rw.generate_weapon_config()
    for cvar in ("g_rustchain_forker_fire_sound", "g_rustchain_hashcannon_fire_sound"):
        if cvar not in cfg:
            fail(f"generate_weapon_config() missing cvar {cvar}")
    bw = rw.BlockchainWeapons()
    if bw.get_weapon_info("hashcannon").get("fire_sound") != rw.WEAPON_SOUNDS["hashcannon"]:
        fail("get_weapon_info() does not expose fire_sound")
    print("  [3/3] cfg cvars emitted + get_weapon_info exposes fire_sound — OK")

    print("PASS")


if __name__ == "__main__":
    main()
