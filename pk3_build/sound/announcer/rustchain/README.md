# RustChain announcer cue pack

Fourteen original announcer cues for the blockchain-themed arena:

| File | Cue |
|---|---|
| `begin.ogg` | Match start stinger |
| `prepare.ogg` | Pre-match preparation warning |
| `go.ogg` | Fight/go cue |
| `firstblood.ogg` | First frag / genesis block moment |
| `impressive.ogg` | Impressive play |
| `excellent.ogg` | Excellent play |
| `humiliation.ogg` | Humiliation event |
| `lead_taken.ogg` | Player takes the lead |
| `lead_lost.ogg` | Player loses the lead |
| `1.ogg` - `5.ogg` | Countdown cues |

All files are mono OGG Vorbis at 48 kHz. The paths passed to the engine are
relative to `sound/`, for example:

```c
precache_sound("announcer/rustchain/go.ogg");
localsound("announcer/rustchain/go.ogg");
```

## Regeneration

From the repository root:

```bash
python tools/audio/generate_rustchain_announcer.py
```

The generator uses deterministic procedural synthesis and Python's standard
library. It requires `ffmpeg` with `libvorbis` support for the final encoding.

## License

The sound design, PCM synthesis code, and generated audio are dedicated to the
public domain under CC0 1.0. See `LICENSE`.
