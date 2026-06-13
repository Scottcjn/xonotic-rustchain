#!/usr/bin/env python3
"""Generate the original RustChain blood-economy reward alert sound set.

The source audio is synthesized from deterministic oscillators and noise. No
samples, speech models, or third-party recordings are used.
"""

from __future__ import annotations

import argparse
import math
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Callable


SAMPLE_RATE = 48_000
TARGET_PEAK = 10 ** (-1.2 / 20.0)


class Noise:
    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFF

    def next(self) -> float:
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return ((self.state / 0xFFFFFFFF) * 2.0) - 1.0


def blank(seconds: float) -> list[float]:
    return [0.0] * round(seconds * SAMPLE_RATE)


def add_tone(
    samples: list[float],
    start: float,
    duration: float,
    start_hz: float,
    end_hz: float,
    gain: float,
    *,
    attack: float = 0.004,
    release_power: float = 2.0,
    harmonics: tuple[float, ...] = (1.0, 0.28, 0.09),
) -> None:
    start_index = round(start * SAMPLE_RATE)
    count = min(round(duration * SAMPLE_RATE), len(samples) - start_index)
    phases = [0.0] * len(harmonics)
    for offset in range(max(0, count)):
        progress = offset / max(1, count - 1)
        frequency = start_hz + ((end_hz - start_hz) * progress)
        attack_gain = min(1.0, offset / max(1, round(attack * SAMPLE_RATE)))
        release_gain = (1.0 - progress) ** release_power
        value = 0.0
        for harmonic_index, harmonic_gain in enumerate(harmonics, start=1):
            phases[harmonic_index - 1] += (
                2.0 * math.pi * frequency * harmonic_index / SAMPLE_RATE
            )
            value += harmonic_gain * math.sin(phases[harmonic_index - 1])
        samples[start_index + offset] += gain * attack_gain * release_gain * value


def add_noise(
    samples: list[float],
    start: float,
    duration: float,
    gain: float,
    seed: int,
    *,
    smoothing: float = 0.78,
    release_power: float = 2.6,
) -> None:
    start_index = round(start * SAMPLE_RATE)
    count = min(round(duration * SAMPLE_RATE), len(samples) - start_index)
    noise = Noise(seed)
    filtered = 0.0
    for offset in range(max(0, count)):
        progress = offset / max(1, count - 1)
        filtered = smoothing * filtered + (1.0 - smoothing) * noise.next()
        envelope = min(1.0, offset / max(1, round(0.003 * SAMPLE_RATE)))
        envelope *= (1.0 - progress) ** release_power
        samples[start_index + offset] += gain * envelope * filtered


def add_click_train(
    samples: list[float],
    start: float,
    count: int,
    interval: float,
    base_hz: float,
    gain: float,
) -> None:
    for index in range(count):
        pitch = base_hz * (1.0 + 0.045 * index)
        add_tone(
            samples,
            start + index * interval,
            0.055,
            pitch,
            pitch * 0.72,
            gain,
            attack=0.001,
            release_power=4.0,
            harmonics=(1.0, 0.42, 0.18),
        )


def normalize(samples: list[float]) -> list[float]:
    peak = max(max(abs(sample) for sample in samples), 0.0001)
    scale = TARGET_PEAK / peak
    return [max(-1.0, min(1.0, sample * scale)) for sample in samples]


def block_confirmed_pulse() -> list[float]:
    samples = blank(0.92)
    add_click_train(samples, 0.05, 4, 0.09, 780, 0.44)
    add_tone(samples, 0.41, 0.42, 392, 523, 0.34, release_power=1.3)
    add_tone(samples, 0.45, 0.30, 784, 1046, 0.24, release_power=1.8)
    return normalize(samples)


def reward_mint() -> list[float]:
    samples = blank(1.05)
    for index, pitch in enumerate((523, 659, 784, 988)):
        add_tone(samples, 0.06 + index * 0.12, 0.22, pitch, pitch * 1.05, 0.28)
    add_tone(samples, 0.52, 0.42, 247, 370, 0.30, release_power=1.5)
    add_noise(samples, 0.18, 0.58, 0.055, 0xC0FFEE, smoothing=0.92)
    return normalize(samples)


def wallet_credit() -> list[float]:
    samples = blank(0.84)
    add_click_train(samples, 0.04, 3, 0.075, 1180, 0.34)
    add_tone(samples, 0.31, 0.24, 880, 1320, 0.28, release_power=2.0)
    add_tone(samples, 0.42, 0.28, 1760, 1568, 0.15, release_power=2.5)
    return normalize(samples)


def chain_reorg_warning() -> list[float]:
    samples = blank(1.18)
    add_tone(samples, 0.04, 0.72, 270, 160, 0.36, release_power=1.0)
    add_tone(samples, 0.10, 0.32, 640, 480, 0.22, release_power=2.8)
    add_tone(samples, 0.48, 0.28, 620, 410, 0.24, release_power=2.4)
    add_noise(samples, 0.08, 0.92, 0.10, 0x51A7E, smoothing=0.82, release_power=2.0)
    return normalize(samples)


def mining_tick_burst() -> list[float]:
    samples = blank(0.98)
    add_click_train(samples, 0.03, 8, 0.075, 430, 0.30)
    add_noise(samples, 0.02, 0.78, 0.075, 0xB10C, smoothing=0.55, release_power=1.7)
    add_tone(samples, 0.67, 0.22, 180, 118, 0.30, release_power=2.6)
    return normalize(samples)


def style_multiplier_lock() -> list[float]:
    samples = blank(1.08)
    for index in range(5):
        add_tone(samples, 0.06 + index * 0.11, 0.14, 330 + index * 88, 440 + index * 96, 0.20)
    add_tone(samples, 0.63, 0.36, 660, 990, 0.25, release_power=1.4)
    add_tone(samples, 0.65, 0.31, 990, 1320, 0.16, release_power=1.8)
    return normalize(samples)


CUES: dict[str, Callable[[], list[float]]] = {
    "block_confirmed_pulse": block_confirmed_pulse,
    "reward_mint": reward_mint,
    "wallet_credit": wallet_credit,
    "chain_reorg_warning": chain_reorg_warning,
    "mining_tick_burst": mining_tick_burst,
    "style_multiplier_lock": style_multiplier_lock,
}


def write_wav(path: Path, samples: list[float]) -> None:
    pcm = bytearray()
    for sample in normalize(samples):
        pcm.extend(struct.pack("<h", round(sample * 32767)))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm)


def write_ogg_with_soundfile(path: Path, samples: list[float]) -> bool:
    try:
        import numpy as np
        import soundfile as sf
    except ImportError:
        return False
    sf.write(
        path,
        np.asarray(normalize(samples), dtype=np.float32),
        SAMPLE_RATE,
        format="OGG",
        subtype="VORBIS",
    )
    return True


def encode_ogg_with_ffmpeg(wav_path: Path, ogg_path: Path, ffmpeg: str) -> None:
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(wav_path),
        "-map_metadata",
        "-1",
        "-c:a",
        "libvorbis",
        "-q:a",
        "6",
        str(ogg_path),
    ]
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("pk3_build/sound/rewards/rustchain"),
        help="Destination directory for generated OGG files.",
    )
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rustchain-reward-alerts-") as temp_dir:
        temp_path = Path(temp_dir)
        for name, generator in CUES.items():
            ogg_path = args.output / f"{name}.ogg"
            samples = generator()
            if not write_ogg_with_soundfile(ogg_path, samples):
                if not args.ffmpeg:
                    raise SystemExit("soundfile or ffmpeg is required to encode OGG Vorbis")
                wav_path = temp_path / f"{name}.wav"
                write_wav(wav_path, samples)
                encode_ogg_with_ffmpeg(wav_path, ogg_path, args.ffmpeg)
            print(f"generated {ogg_path}")


if __name__ == "__main__":
    main()
