# RustChain HashCannon player skin

One original blockchain-themed player skin texture set for the RustChain Arena.

| File | Purpose |
|---|---|
| `rustchain_hashcannon_diffuse.tga` | 1024x1024 diffuse map with railgun armor, hash streams, and compute markings |
| `rustchain_hashcannon_glow.tga` | 1024x1024 glow/emission map for hash traces, reactor core, and railgun coils |
| `rustchain_hashcannon_preview.png` | Preview render and texture thumbnails |
| `rustchain_hashcannon.skin` | Minimal DarkPlaces skin mapping for the texture pair |

## Theme

The design implements **HashCannon** from the skin wishlist: a railgun/compute
player identity with glowing hash patterns, a blue-gold accelerator core, and
nonce/SHA-256 details.

## Integration notes

The texture files live under `models/player/skins/rustchain_hashcannon/` so
they can be packed into the RustChain PK3 with the rest of `pk3_build`.

The `.skin` file uses generic `default` and `glow` material names because this
repository does not currently include a canonical default player-model skin
template. If the final player model exposes specific material names, update
`rustchain_hashcannon.skin` to map those material names to the same TGA files.

## Regeneration

From the repository root:

```bash
python tools/generate_rustchain_hashcannon_skin.py
```

The generator is deterministic and uses Pillow only for raster drawing and file
encoding.

## License

The generated textures, preview, and procedural source are licensed under
CC-BY-SA-4.0. See `LICENSE`.
