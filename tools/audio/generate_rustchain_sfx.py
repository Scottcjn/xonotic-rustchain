#!/usr/bin/env python3
"""Generate the original RustChain Arena weapon sound set.

The synthesizer intentionally uses only Python's standard library. ffmpeg is
used solely to encode the generated PCM WAV files as OGG Vorbis.
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


SAMPLE_RATE = 48_000
TARGET_PEAK = 10 ** (-1.0 / 20.0)


class Noise:
    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFF

    def next(self) -> float:
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return ((self.state / 0xFFFFFFFF) * 2.0) - 1.0


def blank(seconds: float) -> list[float]:
    return [0.0] * int(seconds * SAMPLE_RATE)


def add_tone(
    samples: list[float],
    start: float,
    duration: float,
    start_hz: float,
    end_hz: float,
    gain: float,
    attack: float = 0.01,
    decay_power: float = 1.0,
    harmonic: float = 0.0,
) -> None:
    start_index = int(start * SAMPLE_RATE)
    count = min(int(duration * SAMPLE_RATE), len(samples) - start_index)
    phase = 0.0
    harmonic_phase = 0.0
    for offset in range(max(0, count)):
        progress = offset / max(1, count - 1)
        frequency = start_hz + ((end_hz - start_hz) * progress)
        phase += (2.0 * math.pi * frequency) / SAMPLE_RATE
        harmonic_phase += (4.0 * math.pi * frequency) / SAMPLE_RATE
        attack_gain = min(1.0, offset / max(1, int(attack * SAMPLE_RATE)))
        release_gain = (1.0 - progress) ** decay_power
        value = math.sin(phase) + (harmonic * math.sin(harmonic_phase))
        samples[start_index + offset] += gain * attack_gain * release_gain * value


def add_noise(
    samples: list[float],
    start: float,
    duration: float,
    gain: float,
    seed: int,
    smoothing: float,
    attack: float = 0.002,
    decay_power: float = 2.0,
) -> None:
    start_index = int(start * SAMPLE_RATE)
    count = min(int(duration * SAMPLE_RATE), len(samples) - start_index)
    noise = Noise(seed)
    filtered = 0.0
    for offset in range(max(0, count)):
        progress = offset / max(1, count - 1)
        filtered = (smoothing * filtered) + ((1.0 - smoothing) * noise.next())
        attack_gain = min(1.0, offset / max(1, int(attack * SAMPLE_RATE)))
        release_gain = (1.0 - progress) ** decay_power
        samples[start_index + offset] += gain * attack_gain * release_gain * filtered


def add_click(
    samples: list[float],
    start: float,
    gain: float,
    pitch: float,
    seed: int,
) -> None:
    add_noise(samples, start, 0.045, gain, seed, smoothing=0.35, decay_power=4.0)
    add_tone(
        samples,
        start,
        0.08,
        pitch,
        pitch * 0.72,
        gain * 0.45,
        attack=0.001,
        decay_power=4.5,
        harmonic=0.25,
    )


def validator_pistol() -> list[float]:
    samples = blank(1.15)
    add_tone(samples, 0.00, 0.54, 180, 940, 0.28, attack=0.03, decay_power=0.18, harmonic=0.22)
    add_tone(samples, 0.10, 0.44, 360, 1350, 0.12, attack=0.02, decay_power=0.25)
    add_noise(samples, 0.535, 0.18, 0.70, 0xA11CE, smoothing=0.48, decay_power=3.1)
    add_tone(samples, 0.535, 0.48, 1720, 135, 0.72, attack=0.001, decay_power=2.2, harmonic=0.16)
    add_tone(samples, 0.57, 0.50, 118, 58, 0.27, attack=0.005, decay_power=2.8)
    return samples


def forker_shotgun() -> list[float]:
    samples = blank(1.35)
    add_click(samples, 0.06, 0.65, 980, 0xF001)
    add_click(samples, 0.24, 0.58, 720, 0xF002)
    for start, seed, pitch in ((0.49, 0xF010, 180), (0.625, 0xF011, 158)):
        add_noise(samples, start, 0.43, 1.05, seed, smoothing=0.91, decay_power=2.5)
        add_noise(samples, start, 0.12, 0.55, seed + 1, smoothing=0.25, decay_power=3.5)
        add_tone(samples, start, 0.52, pitch, 46, 0.50, attack=0.001, decay_power=2.8)
    add_click(samples, 1.10, 0.32, 640, 0xF020)
    return samples


def hashcannon() -> list[float]:
    samples = blank(1.62)
    for index in range(7):
        start = 0.08 + (index * 0.095)
        pitch = 310 + (index * 92)
        add_tone(samples, start, 0.07, pitch, pitch * 1.12, 0.20 + (index * 0.018), attack=0.002, decay_power=2.2)
        add_click(samples, start, 0.12, pitch * 1.8, 0xC000 + index)
    add_tone(samples, 0.72, 0.70, 2050, 520, 0.70, attack=0.001, decay_power=1.8, harmonic=0.20)
    add_tone(samples, 0.72, 0.76, 112, 72, 0.40, attack=0.003, decay_power=2.1)
    add_noise(samples, 0.72, 0.34, 0.38, 0xC0DE, smoothing=0.72, decay_power=2.6)
    return samples


def mempool_grenade() -> list[float]:
    samples = blank(1.90)
    for index, start in enumerate((0.10, 0.23, 0.35, 0.47, 0.59, 0.70)):
        pitch = 690 + (index * 85)
        add_click(samples, start, 0.22, pitch, 0xD100 + index)
        add_tone(samples, start, 0.06, pitch, pitch * 1.35, 0.14, attack=0.001, decay_power=2.8)
    add_noise(samples, 0.82, 0.70, 1.10, 0xD200, smoothing=0.94, decay_power=2.5)
    add_noise(samples, 0.82, 0.18, 0.75, 0xD201, smoothing=0.30, decay_power=3.2)
    add_tone(samples, 0.82, 0.78, 96, 38, 0.72, attack=0.002, decay_power=2.7)
    for index, start in enumerate((1.02, 1.17, 1.31, 1.48)):
        add_noise(samples, start, 0.18, 0.38, 0xD300 + index, smoothing=0.62, decay_power=3.5)
        add_tone(samples, start, 0.20, 260 - (index * 24), 72, 0.25, attack=0.001, decay_power=3.2)
    return samples


def double_spend_smg() -> list[float]:
    samples = blank(1.42)
    for index in range(12):
        start = 0.08 + (index * 0.085)
        pitch = 1180 if index % 2 == 0 else 930
        add_click(samples, start, 0.50, pitch, 0xB000 + index)
        add_noise(samples, start, 0.075, 0.42, 0xB100 + index, smoothing=0.58, decay_power=3.8)
        add_tone(samples, start, 0.11, 150, 72, 0.23, attack=0.001, decay_power=3.5)
    add_tone(samples, 1.06, 0.30, 510, 180, 0.20, attack=0.002, decay_power=3.0, harmonic=0.30)
    return samples


SOUNDS = {
    "validator_pistol": validator_pistol,
    "forker_shotgun": forker_shotgun,
    "hashcannon": hashcannon,
    "mempool_grenade": mempool_grenade,
    "double_spend_smg": double_spend_smg,
}


def normalize(samples: list[float]) -> list[float]:
    peak = max(abs(sample) for sample in samples)
    scale = TARGET_PEAK / peak if peak else 1.0
    normalized = [max(-1.0, min(1.0, sample * scale)) for sample in samples]
    fade_samples = int(0.008 * SAMPLE_RATE)
    for index in range(fade_samples):
        fade = index / fade_samples
        normalized[index] *= fade
        normalized[-index - 1] *= fade
    return normalized


def write_wav(path: Path, samples: list[float]) -> None:
    pcm = bytearray()
    for sample in normalize(samples):
        pcm.extend(struct.pack("<h", round(sample * 32767)))
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm)


def encode_ogg(wav_path: Path, ogg_path: Path, ffmpeg: str) -> None:
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
        default=Path("pk3_build/sound/weapons/rustchain"),
        help="Destination directory for generated OGG files.",
    )
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    args = parser.parse_args()

    if not args.ffmpeg:
        raise SystemExit("ffmpeg was not found on PATH")

    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rustchain-sfx-") as temp_dir:
        temp_path = Path(temp_dir)
        for name, generator in SOUNDS.items():
            wav_path = temp_path / f"{name}.wav"
            ogg_path = args.output / f"{name}.ogg"
            write_wav(wav_path, generator())
            encode_ogg(wav_path, ogg_path, args.ffmpeg)
            print(f"generated {ogg_path}")


if __name__ == "__main__":
    main()
