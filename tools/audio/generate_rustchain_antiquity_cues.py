#!/usr/bin/env python3
"""Generate Proof-of-Antiquity hardware cue sounds for RustChain Arena.

The source audio is deterministic procedural synthesis. No samples, speech
models, recordings, or external media assets are used.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import soundfile as sf


SAMPLE_RATE = 48_000
TARGET_PEAK = 10 ** (-4.0 / 20.0)
OUTPUT_DIR = Path("pk3_build/sound/antiquity/rustchain")


def env(count: int, attack: float = 0.004, release: float = 0.09, power: float = 2.0) -> np.ndarray:
    envelope = np.ones(count, dtype=np.float32)
    attack_n = min(count, max(1, round(attack * SAMPLE_RATE)))
    release_n = min(count, max(1, round(release * SAMPLE_RATE)))
    envelope[:attack_n] *= np.linspace(0.0, 1.0, attack_n, dtype=np.float32)
    envelope[-release_n:] *= np.linspace(1.0, 0.0, release_n, dtype=np.float32) ** power
    return envelope


def tone(
    seconds: float,
    start_hz: float,
    end_hz: float | None = None,
    *,
    harmonics: tuple[float, ...] = (1.0, 0.28, 0.12),
    attack: float = 0.004,
    release: float = 0.09,
    bend_power: float = 1.0,
) -> np.ndarray:
    count = max(1, round(seconds * SAMPLE_RATE))
    t = np.arange(count, dtype=np.float32) / SAMPLE_RATE
    end = start_hz if end_hz is None else end_hz
    progress = (t / max(seconds, 1 / SAMPLE_RATE)) ** bend_power
    freq = start_hz + ((end - start_hz) * progress)
    phase = np.cumsum(freq, dtype=np.float32) * (2.0 * math.pi / SAMPLE_RATE)
    out = np.zeros(count, dtype=np.float32)
    for index, gain in enumerate(harmonics, start=1):
        out += gain * np.sin(phase * index)
    out /= max(1.0, sum(abs(gain) for gain in harmonics))
    return (out * env(count, attack=attack, release=release)).astype(np.float32)


def noise(seconds: float, seed: int, *, highpass: float = 0.72, release: float = 0.08) -> np.ndarray:
    count = max(1, round(seconds * SAMPLE_RATE))
    rng = np.random.default_rng(seed)
    raw = rng.uniform(-1.0, 1.0, count).astype(np.float32)
    shifted = np.concatenate(([0.0], raw[:-1]))
    bright = raw - (shifted * highpass)
    return (bright * env(count, attack=0.001, release=release, power=3.0)).astype(np.float32)


def blank(seconds: float) -> np.ndarray:
    return np.zeros(max(1, round(seconds * SAMPLE_RATE)), dtype=np.float32)


def add(track: np.ndarray, start: float, signal: np.ndarray, gain: float) -> None:
    offset = round(start * SAMPLE_RATE)
    if offset >= track.size:
        return
    end = min(track.size, offset + signal.size)
    track[offset:end] += signal[: end - offset] * gain


def chime(seconds: float, notes: tuple[float, ...], *, lift: float = 1.0) -> np.ndarray:
    out = blank(seconds)
    for index, hz in enumerate(notes):
        add(out, index * 0.055, tone(seconds - index * 0.055, hz, hz * lift, release=0.22), 0.55)
    return out / math.sqrt(len(notes))


def crt_boot_nonce() -> np.ndarray:
    s = blank(1.55)
    add(s, 0.02, noise(0.12, 0xC27, highpass=0.48), 0.40)
    add(s, 0.12, tone(0.44, 58, 91, harmonics=(1.0, 0.42, 0.18), release=0.18), 0.62)
    for i, start in enumerate((0.42, 0.54, 0.66, 0.78, 0.93)):
        add(s, start, tone(0.055, 880 + i * 74, 540 + i * 32, attack=0.001, release=0.028), 0.38)
        add(s, start, noise(0.035, 0xC270 + i, highpass=0.35), 0.12)
    add(s, 1.02, chime(0.42, (261.63, 329.63, 392.00), lift=1.003), 0.52)
    return s


def power8_validator_spin() -> np.ndarray:
    s = blank(1.80)
    add(s, 0.00, tone(1.30, 46, 122, harmonics=(1.0, 0.55, 0.22), attack=0.06, release=0.20), 0.66)
    for i in range(9):
        start = 0.12 + i * 0.115
        add(s, start, noise(0.10, 0x8000 + i, highpass=0.86), 0.17 + i * 0.012)
        add(s, start, tone(0.085, 210 + i * 36, 190 + i * 28, attack=0.001, release=0.035), 0.19)
    add(s, 1.16, chime(0.42, (146.83, 220.00, 293.66, 440.00), lift=0.998), 0.44)
    return s


def g4_cube_sync() -> np.ndarray:
    s = blank(1.36)
    add(s, 0.02, chime(0.82, (329.63, 415.30, 554.37, 659.25), lift=1.002), 0.58)
    add(s, 0.20, tone(0.78, 1040, 760, harmonics=(1.0, 0.12), release=0.28), 0.20)
    for i, start in enumerate((0.16, 0.34, 0.52, 0.70)):
        add(s, start, tone(0.05, 1760 + i * 80, 920, attack=0.001, release=0.03), 0.18)
    add(s, 0.92, noise(0.18, 0x6400, highpass=0.80), 0.10)
    return s


def antiquity_weight_boost() -> np.ndarray:
    s = blank(1.48)
    for i, start in enumerate((0.05, 0.20, 0.35, 0.50)):
        add(s, start, tone(0.16, 196 + i * 65, 392 + i * 110, attack=0.002, release=0.06), 0.32)
        add(s, start + 0.045, noise(0.055, 0xA900 + i, highpass=0.50), 0.10)
    add(s, 0.66, chime(0.62, (196.00, 261.63, 329.63, 493.88, 659.25), lift=1.004), 0.70)
    add(s, 0.82, tone(0.46, 84, 64, harmonics=(1.0, 0.44), release=0.20), 0.34)
    return s


def vm_rejected_flatline() -> np.ndarray:
    s = blank(1.62)
    for i, start in enumerate((0.03, 0.22, 0.41)):
        add(s, start, noise(0.12, 0xDEAD + i, highpass=0.28), 0.42)
        add(s, start, tone(0.14, 920 - i * 130, 120, attack=0.001, release=0.05), 0.38)
    add(s, 0.70, tone(0.64, 116, 103, harmonics=(1.0, 0.07), attack=0.002, release=0.24), 0.50)
    for start in (0.78, 0.94, 1.10):
        add(s, start, tone(0.045, 68, 68, harmonics=(1.0,), attack=0.001, release=0.02), 0.28)
    return s


CUES = {
    "crt_boot_nonce": crt_boot_nonce,
    "power8_validator_spin": power8_validator_spin,
    "g4_cube_sync": g4_cube_sync,
    "antiquity_weight_boost": antiquity_weight_boost,
    "vm_rejected_flatline": vm_rejected_flatline,
}

README = """# RustChain Proof-of-Antiquity hardware cues

Original sound-effect set for RustChain Arena bounty #293:
https://github.com/Scottcjn/rustchain-bounties/issues/293

## Cues

| File | Suggested use |
| --- | --- |
| `crt_boot_nonce.ogg` | Vintage node boot / nonce accepted |
| `power8_validator_spin.ogg` | POWER8 or server-class validator spin-up |
| `g4_cube_sync.ogg` | Apple-inspired G4 sync / node join cue |
| `antiquity_weight_boost.ogg` | Antiquity multiplier or Proof-of-Antiquity bonus |
| `vm_rejected_flatline.ogg` | VM/emulator fingerprint rejection |

All cues are mono 48 kHz OGG Vorbis files synthesized by
`tools/audio/generate_rustchain_antiquity_cues.py`. The generator uses only
deterministic oscillators and pseudorandom noise; no samples, speech models,
recordings, or external media assets are embedded.

Suggested DarkPlaces/Xonotic VFS path:
`sound/antiquity/rustchain/<cue>.ogg`.
"""

LICENSE = """RustChain Proof-of-Antiquity hardware cue sound set

Copyright 2026 EldwinMemoryOps

This sound set and its deterministic procedural source are released under
CC0 1.0 Universal.

To the extent possible under law, the author has waived all copyright and
related or neighboring rights to this work.

License text: https://creativecommons.org/publicdomain/zero/1.0/
"""


def normalize(samples: np.ndarray) -> np.ndarray:
    shaped = np.tanh(samples * 1.15).astype(np.float32)
    peak = float(np.max(np.abs(shaped)))
    if peak:
        shaped *= TARGET_PEAK / peak
    fade_n = min(round(0.006 * SAMPLE_RATE), shaped.size // 2)
    fade = np.linspace(0.0, 1.0, fade_n, dtype=np.float32)
    shaped[:fade_n] *= fade
    shaped[-fade_n:] *= fade[::-1]
    return shaped.astype(np.float32)


def write_ogg(path: Path, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sf.SoundFile(
        path,
        mode="w",
        samplerate=SAMPLE_RATE,
        channels=1,
        format="OGG",
        subtype="VORBIS",
    ) as output:
        output.write(normalize(samples))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    for name, generator in CUES.items():
        target = args.output / f"{name}.ogg"
        write_ogg(target, generator())
        print(f"generated {target}")
    (args.output / "README.md").write_text(README, encoding="utf-8")
    (args.output / "LICENSE").write_text(LICENSE, encoding="utf-8")


if __name__ == "__main__":
    main()
