# RustChain objective control cue set

Five original short nonverbal cues for RustChain Arena objective, capture, and
reward-route moments:

| File | Cue |
|---|---|
| `capture_initiated.ogg` | Objective capture started / node handshake |
| `node_contested.ogg` | Validator node contested / control conflict |
| `validator_lock.ogg` | Capture lock or validator control secured |
| `reward_route_open.ogg` | Reward route, payout lane, or bonus gate opened |
| `objective_lost.ogg` | Objective lost / control reverted |

All files are mono OGG Vorbis at 48 kHz and are generated from deterministic
procedural synthesis. No external samples, speech models, or recordings are
used.

Suggested virtual paths are relative to `sound/`, for example:

```c
precache_sound("objectives/rustchain/validator_lock.ogg");
sound(world, CHAN_AUTO, "objectives/rustchain/validator_lock.ogg", VOL_BASE, ATTEN_NORM);
```

## Regeneration

From the repository root:

```sh
python3 tools/audio/generate_rustchain_objective_cues.py
```

The generator uses Python's standard library for synthesis and ffmpeg only for
OGG Vorbis encoding.

## License

The sound design, PCM synthesis code, and generated audio are dedicated to the
public domain under CC0 1.0. See `LICENSE`.
