# RustChain Arena Announcer Cues

This directory contains an original, nonverbal announcer/SFX pack for the
RustChain Arena. The cues use blockchain-themed boot, confirmation, consensus,
failure, and countdown motifs.

## Format

- OGG Vorbis
- mono
- 48 kHz
- normalized to a -1 dB peak

## Cues

| File | Event design |
|---|---|
| `begin.ogg` | validator nodes booting into a stable chord |
| `prepare.ogg` | rising validation sequence |
| `go.ogg` | launch sweep and consensus impact |
| `firstblood.ogg` | low genesis impact followed by block confirmations |
| `impressive.ogg` | short bright confirmation fanfare |
| `excellent.ogg` | extended major consensus fanfare |
| `humiliation.ogg` | slashing descent and data-corruption texture |
| `lead_taken.ogg` | ascending chain-lead motif |
| `lead_lost.ogg` | descending chain-lead motif |
| `1.ogg`-`5.ogg` | one to five clearly separated countdown pulses |

## Regeneration

The source is deterministic and uses only Python's standard library:

```sh
python3 tools/audio/generate_rustchain_announcer.py
```

Encoding requires `ffmpeg` built with `libvorbis`. No external samples, speech
models, or third-party recordings are used.

## License

The generator and generated audio in this directory are released under CC0
1.0. See `LICENSE`.
