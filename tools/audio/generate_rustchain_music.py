#!/usr/bin/env python3
"""Generate an original RustChain Arena combat music loop.

The source audio is synthesized from deterministic oscillators and noise.
No samples, stems, model output, or third-party recordings are used.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import soundfile as sf


SAMPLE_RATE = 48_000
BPM = 160
BARS = 128
BEAT_SECONDS = 60.0 / BPM
BAR_SECONDS = BEAT_SECONDS * 4.0
DURATION_SECONDS = BARS * BAR_SECONDS
TOTAL_SAMPLES = round(DURATION_SECONDS * SAMPLE_RATE)
TARGET_PEAK = 10 ** (-4.0 / 20.0)
OUTPUT_PATH = Path("pk3_build/sound/music/rustchain/chain_reactor_loop.ogg")


def midi_to_hz(note: float) -> float:
    return 440.0 * (2.0 ** ((note - 69.0) / 12.0))


def envelope(
    count: int,
    attack: float = 0.01,
    release: float = 0.08,
    decay_power: float = 1.0,
) -> np.ndarray:
    env = np.ones(count, dtype=np.float32)
    attack_samples = max(1, round(attack * SAMPLE_RATE))
    release_samples = max(1, round(release * SAMPLE_RATE))
    attack_count = min(attack_samples, count)
    release_count = min(release_samples, count)
    env[:attack_count] *= np.linspace(0.0, 1.0, attack_count, dtype=np.float32)
    release_curve = np.linspace(1.0, 0.0, release_count, dtype=np.float32) ** decay_power
    env[-release_count:] *= release_curve
    return env


def add(track: np.ndarray, start_seconds: float, signal: np.ndarray, gain: float) -> None:
    start = round(start_seconds * SAMPLE_RATE)
    if start >= track.size:
        return
    end = min(track.size, start + signal.size)
    track[start:end] += signal[: end - start] * gain


def tonal_note(
    frequency: float,
    seconds: float,
    *,
    attack: float = 0.006,
    release: float = 0.08,
    brightness: float = 0.28,
    pulse_width: float = 0.0,
) -> np.ndarray:
    count = max(1, round(seconds * SAMPLE_RATE))
    t = np.arange(count, dtype=np.float32) / SAMPLE_RATE
    phase = 2.0 * math.pi * frequency * t
    tone = np.sin(phase)
    tone += brightness * np.sin(phase * 2.0)
    tone += (brightness * 0.30) * np.sin(phase * 3.0)
    if pulse_width:
        tone = np.tanh((1.0 + pulse_width) * tone)
    return (tone * envelope(count, attack=attack, release=release, decay_power=1.8)).astype(np.float32)


def chord(notes: tuple[int, ...], seconds: float) -> np.ndarray:
    count = round(seconds * SAMPLE_RATE)
    output = np.zeros(count, dtype=np.float32)
    for index, note in enumerate(notes):
        detune = 1.0 + ((index - 1) * 0.0018)
        output += tonal_note(
            midi_to_hz(note) * detune,
            seconds,
            attack=0.08,
            release=0.30,
            brightness=0.18,
        )
    return output / math.sqrt(len(notes))


def kick() -> np.ndarray:
    seconds = 0.30
    count = round(seconds * SAMPLE_RATE)
    t = np.arange(count, dtype=np.float32) / SAMPLE_RATE
    frequency = 42.0 + (108.0 * np.exp(-t * 32.0))
    phase = np.cumsum(frequency, dtype=np.float32) * (2.0 * math.pi / SAMPLE_RATE)
    body = np.sin(phase) * np.exp(-t * 9.2)
    click = np.sin(2.0 * math.pi * 1800.0 * t) * np.exp(-t * 95.0) * 0.18
    return ((body + click) * envelope(count, attack=0.001, release=0.04, decay_power=2.8)).astype(np.float32)


def snare(seed: int) -> np.ndarray:
    seconds = 0.22
    count = round(seconds * SAMPLE_RATE)
    t = np.arange(count, dtype=np.float32) / SAMPLE_RATE
    rng = np.random.default_rng(seed)
    noise = rng.uniform(-1.0, 1.0, count).astype(np.float32)
    noise = noise - np.concatenate(([0.0], noise[:-1])) * 0.52
    body = np.sin(2.0 * math.pi * 190.0 * t) * np.exp(-t * 13.0) * 0.35
    return ((noise * np.exp(-t * 18.0) * 0.78) + body).astype(np.float32)


def hat(seed: int, seconds: float = 0.055) -> np.ndarray:
    count = round(seconds * SAMPLE_RATE)
    t = np.arange(count, dtype=np.float32) / SAMPLE_RATE
    rng = np.random.default_rng(seed)
    noise = rng.uniform(-1.0, 1.0, count).astype(np.float32)
    bright = noise - np.concatenate(([0.0], noise[:-1])) * 0.76
    return (bright * np.exp(-t * 45.0) * envelope(count, attack=0.001, release=0.02, decay_power=2.5)).astype(np.float32)


def riser(seconds: float, seed: int) -> np.ndarray:
    count = round(seconds * SAMPLE_RATE)
    t = np.arange(count, dtype=np.float32) / SAMPLE_RATE
    rng = np.random.default_rng(seed)
    noise = rng.uniform(-1.0, 1.0, count).astype(np.float32)
    frequency = 140.0 + (1800.0 * (t / max(seconds, 0.001)) ** 1.4)
    phase = np.cumsum(frequency, dtype=np.float32) * (2.0 * math.pi / SAMPLE_RATE)
    sweep = np.sin(phase) * 0.50
    growth = (t / max(seconds, 0.001)) ** 1.6
    return ((noise * 0.16 + sweep) * growth * envelope(count, attack=0.18, release=0.12)).astype(np.float32)


def build_track() -> np.ndarray:
    track = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    roots = [41, 36, 44, 39, 41, 32, 39, 36]
    chords = [
        (41, 48, 53, 56),
        (36, 48, 53, 60),
        (44, 51, 55, 60),
        (39, 46, 51, 55),
        (41, 48, 53, 60),
        (32, 44, 51, 56),
        (39, 46, 51, 58),
        (36, 43, 48, 55),
    ]
    arp_degrees = [12, 19, 24, 31, 24, 19, 12, 7]
    lead_steps = [0, 3, 7, 10, 12, 10, 7, 3, 5, 8, 12, 15, 12, 8, 7, 3]

    for bar in range(BARS):
        bar_start = bar * BAR_SECONDS
        pattern = bar % len(roots)
        root = roots[pattern]

        add(track, bar_start, chord(chords[pattern], BAR_SECONDS * 0.92), 0.095)

        for beat in range(4):
            beat_start = bar_start + beat * BEAT_SECONDS
            add(track, beat_start, kick(), 0.55)
            if beat in (1, 3):
                add(track, beat_start, snare(0xC0DE + bar * 4 + beat), 0.30)
            bass_note = root - (12 if beat == 3 and pattern in (1, 5) else 0)
            add(
                track,
                beat_start,
                tonal_note(
                    midi_to_hz(bass_note),
                    BEAT_SECONDS * 0.78,
                    attack=0.004,
                    release=0.055,
                    brightness=0.42,
                    pulse_width=1.1,
                ),
                0.34,
            )

        for step in range(8):
            step_start = bar_start + step * (BEAT_SECONDS / 2.0)
            add(track, step_start, hat(0xA000 + bar * 8 + step), 0.12 if step % 2 else 0.18)
            note = root + arp_degrees[(step + (bar // 8)) % len(arp_degrees)]
            add(
                track,
                step_start,
                tonal_note(
                    midi_to_hz(note),
                    BEAT_SECONDS * 0.34,
                    attack=0.002,
                    release=0.045,
                    brightness=0.52,
                    pulse_width=0.45,
                ),
                0.105,
            )

        if 16 <= (bar % 64) < 32 or 48 <= (bar % 64) < 56:
            phrase_step = bar % len(lead_steps)
            for offset, step in enumerate((0.0, 0.75, 1.5, 2.5, 3.25)):
                note = root + 24 + lead_steps[(phrase_step + offset) % len(lead_steps)]
                add(
                    track,
                    bar_start + step * BEAT_SECONDS,
                    tonal_note(
                        midi_to_hz(note),
                        BEAT_SECONDS * 0.48,
                        attack=0.004,
                        release=0.075,
                        brightness=0.38,
                    ),
                    0.17,
                )

        if bar % 16 == 14:
            add(track, bar_start, riser(BAR_SECONDS * 2.0, 0x5150 + bar), 0.18)

    track = np.tanh(track * 1.25).astype(np.float32)
    peak = float(np.max(np.abs(track)))
    if peak:
        track *= TARGET_PEAK / peak
    boundary_fade = round(0.006 * SAMPLE_RATE)
    fade = np.linspace(0.0, 1.0, boundary_fade, dtype=np.float32)
    track[:boundary_fade] *= fade
    track[-boundary_fade:] *= fade[::-1]
    return track.astype(np.float32)


def write_ogg(path: Path, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    block_size = SAMPLE_RATE
    with sf.SoundFile(
        path,
        mode="w",
        samplerate=SAMPLE_RATE,
        channels=1,
        format="OGG",
        subtype="VORBIS",
    ) as output:
        for start in range(0, samples.size, block_size):
            output.write(samples[start : start + block_size])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    samples = build_track()
    write_ogg(args.output, samples)
    duration = samples.size / SAMPLE_RATE
    peak = float(np.max(np.abs(samples)))
    rms = float(np.sqrt(np.mean(np.square(samples))))
    print(f"generated {args.output}")
    print(f"duration={duration:.2f}s sample_rate={SAMPLE_RATE} peak={peak:.4f} rms={rms:.4f}")


if __name__ == "__main__":
    main()
