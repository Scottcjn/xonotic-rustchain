#!/usr/bin/env python3
"""Generate the original RustChain Arena announcer cue pack.

The cues are deterministic procedural synthesis: no recorded samples, TTS
voices, or external sound libraries are used. ffmpeg is used only to encode the
generated PCM WAV files as OGG Vorbis.
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


def envelope(offset: int, count: int, attack: float, release: float) -> float:
    attack_count = max(1, int(attack * SAMPLE_RATE))
    release_count = max(1, int(release * SAMPLE_RATE))
    return min(1.0, offset / attack_count, (count - offset) / release_count)


def add_tone(
    samples: list[float],
    start: float,
    duration: float,
    start_hz: float,
    end_hz: float,
    gain: float,
    attack: float = 0.01,
    release: float = 0.04,
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
        env = envelope(offset, count, attack, release)
        value = math.sin(phase) + (harmonic * math.sin(harmonic_phase))
        samples[start_index + offset] += gain * env * value


def add_noise(
    samples: list[float],
    start: float,
    duration: float,
    gain: float,
    seed: int,
    smoothing: float = 0.5,
    attack: float = 0.002,
    release: float = 0.04,
) -> None:
    start_index = int(start * SAMPLE_RATE)
    count = min(int(duration * SAMPLE_RATE), len(samples) - start_index)
    noise = Noise(seed)
    filtered = 0.0
    for offset in range(max(0, count)):
        filtered = (smoothing * filtered) + ((1.0 - smoothing) * noise.next())
        env = envelope(offset, count, attack, release)
        samples[start_index + offset] += gain * env * filtered


def add_voice_syllable(
    samples: list[float],
    start: float,
    duration: float,
    pitch: float,
    vowel: tuple[float, float, float],
    gain: float,
    seed: int,
) -> None:
    """Add a synthetic talkbox-like syllable with three formants."""
    start_index = int(start * SAMPLE_RATE)
    count = min(int(duration * SAMPLE_RATE), len(samples) - start_index)
    phases = [0.0, 0.0, 0.0, 0.0]
    noise = Noise(seed)
    for offset in range(max(0, count)):
        t = offset / SAMPLE_RATE
        progress = offset / max(1, count - 1)
        env = envelope(offset, count, 0.018, 0.055)
        vibrato = 1.0 + (0.012 * math.sin(2.0 * math.pi * 7.0 * t))
        fundamental = pitch * (1.0 + (0.05 * math.sin(math.pi * progress))) * vibrato
        phases[0] += (2.0 * math.pi * fundamental) / SAMPLE_RATE
        glottal = math.sin(phases[0]) + (0.35 * math.sin(2.0 * phases[0]))

        formant_mix = 0.0
        for index, formant in enumerate(vowel):
            phases[index + 1] += (2.0 * math.pi * formant) / SAMPLE_RATE
            formant_mix += (0.35 / (index + 1)) * math.sin(phases[index + 1])

        grit = 0.08 * noise.next()
        samples[start_index + offset] += gain * env * ((0.58 * glottal) + formant_mix + grit)


def add_phrase(
    samples: list[float],
    start: float,
    pattern: list[float],
    base_pitch: float,
    gain: float,
    seed: int,
) -> None:
    vowels = [
        (720.0, 1220.0, 2440.0),
        (520.0, 1740.0, 2500.0),
        (360.0, 920.0, 2320.0),
        (780.0, 1420.0, 2680.0),
    ]
    cursor = start
    for index, step in enumerate(pattern):
        add_noise(samples, cursor - 0.018, 0.045, gain * 0.12, seed + index, smoothing=0.2)
        add_voice_syllable(
            samples,
            cursor,
            0.155,
            base_pitch * step,
            vowels[index % len(vowels)],
            gain,
            seed + 0x100 + index,
        )
        cursor += 0.145


def add_glitch_tail(samples: list[float], start: float, seed: int, gain: float = 0.18) -> None:
    for index in range(4):
        t = start + (index * 0.055)
        add_tone(samples, t, 0.05, 720 + (index * 160), 360 + (index * 80), gain, attack=0.001)
        add_noise(samples, t, 0.035, gain * 0.35, seed + index, smoothing=0.35)


def cue(
    seconds: float,
    pattern: list[float],
    pitch: float,
    seed: int,
    intro: tuple[float, float] | None = None,
    tail: bool = True,
) -> list[float]:
    samples = blank(seconds)
    if intro:
        add_tone(samples, 0.04, 0.22, intro[0], intro[1], 0.23, attack=0.006, harmonic=0.2)
    add_phrase(samples, 0.22 if intro else 0.08, pattern, pitch, 0.36, seed)
    if tail:
        add_glitch_tail(samples, seconds - 0.34, seed + 0x400)
    add_tone(samples, seconds - 0.22, 0.18, 90, 46, 0.12, attack=0.003)
    return samples


def begin() -> list[float]:
    return cue(1.24, [1.00, 1.10, 0.94, 1.26], 142, 0xB001, intro=(160, 620))


def prepare() -> list[float]:
    return cue(1.34, [0.88, 0.98, 1.12, 0.92, 1.18], 132, 0xB002, intro=(240, 520))


def go() -> list[float]:
    samples = cue(0.86, [1.35, 0.72], 156, 0xB003, intro=(620, 1180), tail=False)
    add_noise(samples, 0.48, 0.22, 0.55, 0xB103, smoothing=0.78)
    add_tone(samples, 0.48, 0.26, 1320, 240, 0.45, attack=0.001, harmonic=0.18)
    return samples


def firstblood() -> list[float]:
    return cue(1.52, [0.80, 1.05, 1.24, 0.92, 1.34, 1.08], 126, 0xB004, intro=(72, 360))


def impressive() -> list[float]:
    return cue(1.22, [1.10, 1.18, 1.32, 1.44], 148, 0xB005, intro=(440, 880))


def excellent() -> list[float]:
    return cue(1.22, [1.20, 1.36, 1.48, 1.72], 152, 0xB006, intro=(520, 1040))


def humiliation() -> list[float]:
    return cue(1.42, [0.92, 0.76, 0.68, 0.60, 0.82], 118, 0xB007, intro=(260, 120))


def lead_taken() -> list[float]:
    return cue(1.24, [0.96, 1.06, 1.28, 1.42], 138, 0xB008, intro=(330, 760))


def lead_lost() -> list[float]:
    return cue(1.20, [1.06, 0.88, 0.74, 0.62], 134, 0xB009, intro=(480, 190))


def countdown(number: int) -> list[float]:
    seconds = 0.72
    samples = blank(seconds)
    pitch_steps = {
        5: [1.24, 1.02],
        4: [1.16, 0.94],
        3: [1.08, 0.88],
        2: [0.98, 0.82],
        1: [0.88, 0.70],
    }
    add_phrase(samples, 0.09, pitch_steps[number], 150, 0.36, 0xC000 + number)
    add_tone(samples, 0.42, 0.16, 420 + (number * 70), 260 + (number * 45), 0.24, attack=0.001)
    return samples


SOUNDS = {
    "begin": begin,
    "prepare": prepare,
    "go": go,
    "firstblood": firstblood,
    "impressive": impressive,
    "excellent": excellent,
    "humiliation": humiliation,
    "lead_taken": lead_taken,
    "lead_lost": lead_lost,
    "5": lambda: countdown(5),
    "4": lambda: countdown(4),
    "3": lambda: countdown(3),
    "2": lambda: countdown(2),
    "1": lambda: countdown(1),
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
        default=Path("pk3_build/sound/announcer/rustchain"),
        help="Destination directory for generated OGG files.",
    )
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    args = parser.parse_args()

    if not args.ffmpeg:
        raise SystemExit("ffmpeg was not found on PATH")

    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rustchain-announcer-") as temp_dir:
        temp_path = Path(temp_dir)
        for name, generator in SOUNDS.items():
            wav_path = temp_path / f"{name}.wav"
            ogg_path = args.output / f"{name}.ogg"
            write_wav(wav_path, generator())
            encode_ogg(wav_path, ogg_path, args.ffmpeg)
            print(f"generated {ogg_path}")


if __name__ == "__main__":
    main()
