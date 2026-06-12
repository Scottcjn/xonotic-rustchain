#!/usr/bin/env python3
"""Generate the original RustChain Arena kill-streak stinger set.

The source audio is synthesized entirely from deterministic oscillators and
noise. No samples, speech models, or third-party recordings are used.
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
    harmonics: tuple[float, ...] = (1.0, 0.28, 0.10),
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
    smoothing: float = 0.72,
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
    *,
    gain: float = 0.44,
    duration: float = 0.105,
    seed: int = 0xC0DE,
) -> None:
    add_noise(samples, start, duration * 0.55, gain * 0.28, seed, smoothing=0.44)
    add_tone(
        samples,
        start,
        duration,
        pitch,
        pitch * 0.78,
        gain,
        attack=0.001,
        release_power=3.8,
        harmonics=(1.0, 0.36, 0.16),
    )


def add_chord(
    samples: list[float],
    start: float,
    duration: float,
    pitches: tuple[float, ...],
    gain: float,
    *,
    lift: float = 1.0,
) -> None:
    per_tone = gain / math.sqrt(len(pitches))
    for pitch in pitches:
        add_tone(
            samples,
            start,
            duration,
            pitch,
            pitch * lift,
            per_tone,
            attack=0.012,
            release_power=1.7,
        )


def add_morse_tick_phrase(samples: list[float], start: float, pattern: tuple[int, ...], base: float, seed: int) -> None:
    cursor = start
    for index, length in enumerate(pattern):
        duration = 0.045 if length == 1 else 0.105
        add_pulse(samples, cursor, base + index * 28, gain=0.22, duration=duration, seed=seed + index)
        cursor += duration + 0.035


def double_spend() -> list[float]:
    samples = blank(1.38)
    add_morse_tick_phrase(samples, 0.06, (1, 1, 2, 1, 1), 720, 0xD011)
    add_morse_tick_phrase(samples, 0.54, (1, 1, 2, 1, 1), 560, 0xD051)
    add_tone(samples, 0.18, 0.48, 540, 310, 0.26, release_power=1.4)
    add_tone(samples, 0.26, 0.48, 810, 450, 0.22, release_power=1.5)
    add_noise(samples, 0.90, 0.20, 0.52, 0xD0B1, smoothing=0.55)
    add_chord(samples, 0.88, 0.42, (196.00, 293.66, 392.00), 0.54, lift=0.96)
    return samples


def triple_fork() -> list[float]:
    samples = blank(1.46)
    for index, start in enumerate((0.08, 0.33, 0.58)):
        add_noise(samples, start, 0.10, 0.28, 0xF300 + index, smoothing=0.34)
        add_pulse(samples, start, 330 + index * 98, gain=0.46, duration=0.16, seed=0xF310 + index)
        add_tone(samples, start + 0.03, 0.18, 420 + index * 120, 240 + index * 42, 0.24)
    add_tone(samples, 0.78, 0.50, 270, 1040, 0.34, release_power=1.1)
    add_chord(samples, 0.95, 0.38, (220.00, 329.63, 493.88), 0.58, lift=1.01)
    return samples


def consensus_reached() -> list[float]:
    samples = blank(1.72)
    for index, pitch in enumerate((174.61, 220.00, 261.63, 329.63, 392.00)):
        add_pulse(samples, 0.06 + index * 0.13, pitch, gain=0.32, duration=0.12, seed=0xC500 + index)
    add_tone(samples, 0.22, 0.92, 96, 64, 0.23, release_power=1.8)
    add_chord(samples, 0.78, 0.74, (196.00, 261.63, 329.63, 392.00, 523.25), 0.72, lift=1.0)
    add_noise(samples, 0.78, 0.16, 0.22, 0xC0A1, smoothing=0.38)
    return samples


def block_confirmed() -> list[float]:
    samples = blank(1.22)
    add_noise(samples, 0.03, 0.16, 0.34, 0xB10C, smoothing=0.46)
    for index, pitch in enumerate((523.25, 659.25, 783.99)):
        add_pulse(samples, 0.12 + index * 0.14, pitch, gain=0.34, duration=0.11, seed=0xB100 + index)
    add_chord(samples, 0.55, 0.46, (261.63, 329.63, 392.00), 0.55, lift=1.0)
    return samples


def attack_detected() -> list[float]:
    samples = blank(1.55)
    for index, start in enumerate((0.04, 0.22, 0.40, 0.58)):
        add_noise(samples, start, 0.14, 0.50, 0x5100 + index, smoothing=0.31)
        add_tone(samples, start, 0.16, 880 - index * 90, 110, 0.38, attack=0.001, release_power=2.8)
    add_tone(samples, 0.76, 0.50, 140, 48, 0.54, attack=0.002, release_power=2.2)
    add_chord(samples, 1.02, 0.34, (73.42, 110.00, 146.83), 0.46, lift=0.98)
    return samples


STINGERS: dict[str, Callable[[], list[float]]] = {
    "double_spend": double_spend,
    "triple_fork": triple_fork,
    "consensus_reached": consensus_reached,
    "block_confirmed": block_confirmed,
    "attack_detected": attack_detected,
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


def write_ogg_with_soundfile(path: Path, samples: list[float]) -> None:
    try:
        import soundfile as sf
    except ImportError as exc:
        raise SystemExit("ffmpeg or python-soundfile with Vorbis support is required") from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize(samples)
    with sf.SoundFile(
        path,
        mode="w",
        samplerate=SAMPLE_RATE,
        channels=1,
        format="OGG",
        subtype="VORBIS",
    ) as output:
        output.write(normalized)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("pk3_build/sound/stingers/rustchain"),
        help="Destination directory for generated OGG files.",
    )
    parser.add_argument("--encoder", default=shutil.which("ffmpeg"))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    if args.encoder:
        with tempfile.TemporaryDirectory(prefix="rustchain-stingers-") as temp_dir:
            temp_path = Path(temp_dir)
            for name, generator in STINGERS.items():
                wav_path = temp_path / f"{name}.wav"
                ogg_path = args.output / f"{name}.ogg"
                write_wav(wav_path, generator())
                encode_ogg(wav_path, ogg_path, args.encoder)
                print(f"generated {ogg_path}")
    else:
        for name, generator in STINGERS.items():
            ogg_path = args.output / f"{name}.ogg"
            write_ogg_with_soundfile(ogg_path, generator())
            print(f"generated {ogg_path}")


if __name__ == "__main__":
    main()
