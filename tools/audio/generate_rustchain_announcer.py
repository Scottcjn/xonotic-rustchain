#!/usr/bin/env python3
"""Generate the original RustChain Arena nonverbal announcer cue set.

The source audio is synthesized entirely from deterministic oscillators and
noise. No samples, speech models, or third-party recordings are used.
"""

from __future__ import annotations

import argparse
import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Callable


SAMPLE_RATE = 48_000
TARGET_PEAK = 10 ** (-1.0 / 20.0)


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
    release_power: float = 2.2,
    harmonics: tuple[float, ...] = (1.0, 0.24, 0.08),
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
    smoothing: float = 0.75,
    release_power: float = 3.0,
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


def add_pulse(
    samples: list[float],
    start: float,
    pitch: float,
    gain: float = 0.48,
    duration: float = 0.12,
) -> None:
    add_tone(
        samples,
        start,
        duration,
        pitch,
        pitch * 0.82,
        gain,
        attack=0.001,
        release_power=3.8,
        harmonics=(1.0, 0.36, 0.14),
    )


def add_chord(
    samples: list[float],
    start: float,
    duration: float,
    pitches: tuple[float, ...],
    gain: float,
) -> None:
    per_tone = gain / math.sqrt(len(pitches))
    for pitch in pitches:
        add_tone(
            samples,
            start,
            duration,
            pitch,
            pitch * 0.985,
            per_tone,
            attack=0.012,
            release_power=1.8,
        )


def countdown_cue(number: int) -> list[float]:
    samples = blank(0.38 + number * 0.13)
    for index in range(number):
        add_pulse(samples, 0.08 + index * 0.13, 660 + number * 36, 0.38, 0.105)
    add_tone(
        samples,
        0.08,
        0.22 + number * 0.13,
        82 + number * 7,
        68,
        0.15,
        attack=0.004,
        release_power=2.4,
    )
    return samples


def begin() -> list[float]:
    samples = blank(1.20)
    for index, pitch in enumerate((165, 220, 330, 440)):
        add_pulse(samples, 0.08 + index * 0.14, pitch, 0.34, 0.14)
    add_chord(samples, 0.64, 0.48, (220, 330, 440), 0.54)
    add_noise(samples, 0.62, 0.12, 0.18, 0xB10C, smoothing=0.60)
    return samples


def prepare() -> list[float]:
    samples = blank(1.42)
    for index, pitch in enumerate((174.61, 220.00, 261.63, 329.63, 440.00)):
        add_tone(samples, 0.08 + index * 0.17, 0.30, pitch, pitch * 1.04, 0.31)
    add_tone(samples, 0.88, 0.45, 110, 880, 0.33, release_power=1.2)
    return samples


def go() -> list[float]:
    samples = blank(0.92)
    add_noise(samples, 0.02, 0.18, 0.52, 0x600D, smoothing=0.42)
    add_tone(samples, 0.02, 0.42, 140, 1680, 0.63, release_power=0.9)
    add_chord(samples, 0.32, 0.52, (261.63, 392.00, 523.25), 0.66)
    return samples


def firstblood() -> list[float]:
    samples = blank(1.36)
    add_noise(samples, 0.04, 0.32, 0.75, 0xF17B, smoothing=0.91)
    add_tone(samples, 0.04, 0.62, 96, 42, 0.72, release_power=2.6)
    for index, pitch in enumerate((130.81, 196.00, 261.63, 392.00)):
        add_pulse(samples, 0.50 + index * 0.15, pitch, 0.34, 0.16)
    add_chord(samples, 1.02, 0.30, (130.81, 196.00, 261.63), 0.47)
    return samples


def impressive() -> list[float]:
    samples = blank(1.08)
    for index, pitch in enumerate((293.66, 369.99, 440.00, 587.33)):
        add_tone(samples, 0.06 + index * 0.13, 0.25, pitch, pitch * 1.03, 0.31)
    add_chord(samples, 0.58, 0.44, (293.66, 440.00, 587.33), 0.56)
    return samples


def excellent() -> list[float]:
    samples = blank(1.28)
    for index, pitch in enumerate((261.63, 329.63, 392.00, 523.25)):
        add_tone(samples, 0.05 + index * 0.15, 0.32, pitch, pitch, 0.33)
    add_chord(samples, 0.70, 0.52, (261.63, 329.63, 392.00, 523.25), 0.62)
    add_noise(samples, 0.70, 0.10, 0.13, 0xEACE, smoothing=0.45)
    return samples


def humiliation() -> list[float]:
    samples = blank(1.18)
    add_tone(samples, 0.04, 0.80, 370, 74, 0.58, release_power=1.4)
    for index in range(5):
        add_noise(
            samples,
            0.20 + index * 0.11,
            0.09,
            0.22,
            0xBAD0 + index,
            smoothing=0.24,
            release_power=2.5,
        )
    add_chord(samples, 0.75, 0.36, (92.50, 130.81), 0.42)
    return samples


def lead_taken() -> list[float]:
    samples = blank(0.96)
    for index, pitch in enumerate((196.00, 261.63, 392.00)):
        add_pulse(samples, 0.08 + index * 0.16, pitch, 0.40, 0.19)
    add_chord(samples, 0.53, 0.36, (196.00, 261.63, 392.00), 0.52)
    return samples


def lead_lost() -> list[float]:
    samples = blank(0.96)
    for index, pitch in enumerate((392.00, 261.63, 196.00)):
        add_pulse(samples, 0.08 + index * 0.16, pitch, 0.40, 0.19)
    add_chord(samples, 0.53, 0.36, (98.00, 146.83, 196.00), 0.48)
    return samples


CUES: dict[str, Callable[[], list[float]]] = {
    "begin": begin,
    "prepare": prepare,
    "go": go,
    "firstblood": firstblood,
    "impressive": impressive,
    "excellent": excellent,
    "humiliation": humiliation,
    "lead_taken": lead_taken,
    "lead_lost": lead_lost,
    **{str(number): lambda number=number: countdown_cue(number) for number in range(1, 6)},
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


def encode_ogg(wav_path: Path, ogg_path: Path, encoder: str) -> None:
    command = [
        encoder,
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
    ]
    subprocess.run(command, check=True)


def find_encoder(requested: str | None) -> str:
    if requested:
        return requested
    from shutil import which

    encoder = which("ffmpeg")
    if encoder is None:
        raise SystemExit("ffmpeg with libvorbis support is required")
    return encoder


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("pk3_build/sound/announcer/rustchain"),
    )
    parser.add_argument("--encoder")
    args = parser.parse_args()

    encoder = find_encoder(args.encoder)
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rustchain-announcer-") as temp_dir:
        temp_path = Path(temp_dir)
        for name, generator in CUES.items():
            wav_path = temp_path / f"{name}.wav"
            ogg_path = args.output / f"{name}.ogg"
            write_wav(wav_path, generator())
            encode_ogg(wav_path, ogg_path, encoder)
            print(f"generated {ogg_path}")


if __name__ == "__main__":
    main()
