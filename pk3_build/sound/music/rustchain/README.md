# RustChain combat music

This directory contains an original background music loop for RustChain Arena.
It is a fast electronic/synthwave combat track built from deterministic
oscillators, synthetic percussion, and seeded noise.

## Track

| File | Design |
|---|---|
| `chain_reactor_loop.ogg` | 160 BPM blockchain/digital combat loop with drums, bass, arps, pads, lead phrases, and transition risers |

## Format

- OGG Vorbis
- mono
- 48 kHz
- 3:12 loop length
- normalized to a -4 dB peak before Vorbis encoding

## Regeneration

From the repository root:

```sh
python3 tools/audio/generate_rustchain_music.py
```

The generator requires `numpy` and `soundfile` for synthesis and OGG Vorbis
encoding. No external samples, stems, model output, or third-party recordings
are used.

## License

The generator and generated audio in this directory are released under CC0
1.0. See `LICENSE`.
