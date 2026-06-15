#!/usr/bin/env python3
"""Generate original RustChain Arena objective/control cue sounds.

The cues are deterministic procedural synthesis: no samples, speech models,
recordings, or third-party audio are used. ffmpeg is used only for OGG Vorbis
encoding.
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
    attack: float = 0.006,
    release_power: float = 2.0,
    harmonics: tuple[float, ...] = (1.0, 0.25, 0.08),
) -> None:
    start_index = round(start * SAMPLE_RATE)
    count = min(round(duration * SAMPLE_RATE), len(samples) - start_index)
    phases = [0.0] * len(harmonics)
    for offset in range(max(0, count)):
        progress = offset / max(1, count - 1)
        frequency = start_hz + (end_hz - start_hz) * progress
        envelope = min(1.0, offset / max(1, round(attack * SAMPLE_RATE)))
        envelope *= (1.0 - progress) ** release_power
        value = 0.0
        for harmonic_index, harmonic_gain in enumerate(harmonics, start=1):
            phases[harmonic_index - 1] += (
                2.0 * math.pi * frequency * harmonic_index / SAMPLE_RATE
            )
            value += harmonic_gain * math.sin(phases[harmonic_index - 1])
        samples[start_index + offset] += gain * envelope * value


def add_noise(
    samples: list[float],
    start: float,
    duration: float,
    gain: float,
    seed: int,
    *,
    smoothing: float = 0.68,
    release_power: float = 2.8,
) -> None:
    start_index = round(start * SAMPLE_RATE)
    count = min(round(duration * SAMPLE_RATE), len(samples) - start_index)
    noise = Noise(seed)
    filtered = 0.0
    for offset in range(max(0, count)):
        progress = offset / max(1, count - 1)
        filtered = smoothing * filtered + (1.0 - smoothing) * noise.next()
        envelope = min(1.0, offset / max(1, round(0.002 * SAMPLE_RATE)))
        envelope *= (1.0 - progress) ** release_power
        samples[start_index + offset] += gain * envelope * filtered


def add_tick(samples: list[float], start: float, pitch: float, seed: int, gain: float = 0.34) -> None:
    add_noise(samples, start, 0.045, gain * 0.45, seed, smoothing=0.34, release_power=4.0)
    add_tone(
        samples,
        start,
        0.085,
        pitch,
        pitch * 0.70,
        gain,
        attack=0.001,
        release_power=4.2,
        harmonics=(1.0, 0.34, 0.12),
    )


def add_chord(samples: list[float], start: float, duration: float, pitches: tuple[float, ...], gain: float) -> None:
    per_tone = gain / math.sqrt(len(pitches))
    for pitch in pitches:
        add_tone(samples, start, duration, pitch, pitch * 1.005, per_tone, release_power=1.6)


def capture_initiated() -> list[float]:
    samples = blank(1.12)
    for index, pitch in enumerate((392.0, 493.88, 659.25)):
        add_tick(samples, 0.06 + index * 0.13, pitch, 0xC410 + index, 0.34)
    add_tone(samples, 0.40, 0.48, 196.0, 329.63, 0.28, release_power=1.4)
    add_chord(samples, 0.62, 0.34, (261.63, 329.63, 392.0), 0.46)
    return samples


def node_contested() -> list[float]:
    samples = blank(1.34)
    for index, start in enumerate((0.05, 0.25, 0.45, 0.65)):
        add_noise(samples, start, 0.12, 0.42, 0xC0A0 + index, smoothing=0.28)
        add_tone(samples, start, 0.18, 880 - index * 80, 140, 0.36, attack=0.001, release_power=2.5)
    add_tone(samples, 0.86, 0.30, 110.0, 82.41, 0.42, release_power=2.2)
    return samples


def validator_lock() -> list[float]:
    samples = blank(1.26)
    for index, pitch in enumerate((220.0, 277.18, 329.63, 440.0)):
        add_tick(samples, 0.08 + index * 0.12, pitch, 0x10CC + index, 0.30)
    add_chord(samples, 0.58, 0.52, (220.0, 329.63, 440.0, 554.37), 0.62)
    add_noise(samples, 0.58, 0.10, 0.18, 0x10CF, smoothing=0.45)
    return samples


def reward_route_open() -> list[float]:
    samples = blank(1.46)
    for index in range(6):
        add_tick(samples, 0.05 + index * 0.085, 520 + index * 70, 0x7EED + index, 0.24)
    add_tone(samples, 0.52, 0.70, 174.61, 698.46, 0.34, release_power=1.2)
    add_chord(samples, 0.84, 0.44, (261.63, 392.0, 523.25, 659.25), 0.56)
    return samples


def objective_lost() -> list[float]:
    samples = blank(1.38)
    add_noise(samples, 0.04, 0.16, 0.48, 0x1057, smoothing=0.32)
    for index, start in enumerate((0.14, 0.36, 0.58)):
        add_tone(samples, start, 0.22, 620 - index * 120, 150 - index * 22, 0.42, attack=0.002, release_power=2.6)
        add_noise(samples, start, 0.08, 0.26, 0x1060 + index, smoothing=0.42)
    add_chord(samples, 0.82, 0.40, (98.0, 146.83, 196.0), 0.44)
    return samples


OBJECTIVE_CUES: dict[str, Callable[[], list[float]]] = {
    "capture_initiated": capture_initiated,
    "node_contested": node_contested,
    "validator_lock": validator_lock,
    "reward_route_open": reward_route_open,
    "objective_lost": objective_lost,
}


def normalize(samples: list[float]) -> list[float]:
    peak = max((abs(sample) for sample in samples), default=0.0)
    scale = TARGET_PEAK / peak if peak else 1.0
    normalized = [max(-1.0, min(1.0, sample * scale)) for sample in samples]
    fade_samples = min(round(0.008 * SAMPLE_RATE), len(normalized) // 2)
    for index in range(fade_samples):
        fade = index / max(1, fade_samples)
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
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(wav_path),
            "-map_metadata",
            "-1",
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-c:a",
            "libvorbis",
            "-q:a",
            "6",
            str(ogg_path),
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("pk3_build/sound/objectives/rustchain"),
        help="Destination directory for generated OGG files.",
    )
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    args = parser.parse_args()

    if not args.ffmpeg:
        raise SystemExit("ffmpeg was not found on PATH")

    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rustchain-objectives-") as temp_dir:
        temp_path = Path(temp_dir)
        for name, generator in OBJECTIVE_CUES.items():
            wav_path = temp_path / f"{name}.wav"
            ogg_path = args.output / f"{name}.ogg"
            write_wav(wav_path, generator())
            encode_ogg(wav_path, ogg_path, args.ffmpeg)
            print(f"generated {ogg_path}")


if __name__ == "__main__":
    main()
