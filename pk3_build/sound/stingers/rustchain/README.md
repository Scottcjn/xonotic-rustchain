# RustChain kill-streak stinger set

Five original short stingers for RustChain Arena streak and match-event moments:

| File | Cue |
|---|---|
| `double_spend.ogg` | Paired transaction-click motif for a double-spend streak |
| `triple_fork.ogg` | Three split-chain impacts and rising fork chord |
| `consensus_reached.ogg` | Confirming pulse ladder and resolved major chord |
| `block_confirmed.ogg` | Fast block-confirmation chime |
| `attack_detected.ogg` | Alert siren texture for a 51% attack / danger event |

All files are mono OGG Vorbis at 48 kHz and are generated from deterministic
procedural synthesis. No external samples, speech models, or recordings are
used.

Suggested virtual paths are relative to `sound/`, for example:

```c
precache_sound("stingers/rustchain/consensus_reached.ogg");
sound(world, CHAN_AUTO, "stingers/rustchain/consensus_reached.ogg", VOL_BASE, ATTEN_NONE);
```

## Regeneration

From the repository root:

```bash
python tools/audio/generate_rustchain_stingers.py
```

The generator uses Python's standard library for synthesis and ffmpeg only for
OGG Vorbis encoding.

## License

The sound design, PCM synthesis code, and generated audio are dedicated to the
public domain under CC0 1.0. See `LICENSE`.
