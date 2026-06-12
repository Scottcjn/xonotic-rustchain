# RustChain Validator player skin

One original blockchain-themed player skin texture set for the RustChain Arena.

| File | Purpose |
|---|---|
| `rustchain_validator_diffuse.tga` | 1024x1024 diffuse map with dark armor plates and green validator circuit traces |
| `rustchain_validator_glow.tga` | 1024x1024 glow/emission map for the circuit traces and validator core |
| `rustchain_validator_preview.png` | Preview render and texture thumbnails |
| `rustchain_validator.skin` | Minimal DarkPlaces skin mapping for the texture pair |

## Theme

The design implements **The Validator** from the bounty brief: armored plating,
green circuit paths, a validator core, and RustChain/RTC markings suitable for a
network-validator player identity.

## Integration notes

The texture files live under `models/player/skins/rustchain_validator/` so they
can be packed into the RustChain PK3 with the rest of `pk3_build`.

The `.skin` file uses generic `default` and `glow` material names because this
repository does not currently include a canonical default player-model skin
template. If the final player model exposes specific material names, update
`rustchain_validator.skin` to map those material names to the same TGA files.

## Regeneration

From the repository root:

```bash
python tools/generate_rustchain_validator_skin.py
```

The generator is deterministic and uses Pillow only for raster drawing and file
encoding.

## License

The generated textures, preview, and procedural source are licensed under
CC-BY-SA-4.0. See `LICENSE`.
