# RustChain weapon sound set

Five original sound effects for the blockchain-themed arena weapons:

| File | Cue |
|---|---|
| `validator_pistol.ogg` | Rising validator charge followed by an energy discharge |
| `forker_shotgun.ogg` | Mechanical fork action and a staggered dual blast |
| `hashcannon.ogg` | Accelerating computation ticks followed by a rail beam |
| `mempool_grenade.ogg` | Transaction-cluster ticks and an area-fill detonation |
| `double_spend_smg.ogg` | Alternating rapid transaction clicks with a mechanical tail |

All files are mono OGG Vorbis at 48 kHz. The paths passed to QuakeC are relative
to `sound/`, for example:

```c
precache_sound("weapons/rustchain/hashcannon.ogg");
sound(self, CHAN_WEAPON, "weapons/rustchain/hashcannon.ogg", VOL_BASE, ATTEN_NORM);
```

## Regeneration

From the repository root:

```bash
python tools/audio/generate_rustchain_sfx.py
```

The generator uses deterministic procedural synthesis and Python's standard
library. It requires `ffmpeg` with `libvorbis` support for the final encoding.

## License

The sound design, PCM synthesis code, and generated audio are dedicated to the
public domain under CC0 1.0. See `LICENSE`.
