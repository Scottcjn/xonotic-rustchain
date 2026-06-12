# RustChain Forker player skin

One original blockchain-themed player skin texture set for the RustChain Arena.

| File | Purpose |
|---|---|
| `rustchain_forker_diffuse.tga` | 1024x1024 diffuse map with split-chain armor, cold canonical side, and hot reorg side |
| `rustchain_forker_glow.tga` | 1024x1024 glow/emission map for fork crack, chain traces, and side-specific circuitry |
| `rustchain_forker_preview.png` | Preview render and texture thumbnails |
| `rustchain_forker.skin` | Minimal DarkPlaces skin mapping for the texture pair |

## Theme

The design implements **Forker** from the live bounty wishlist: a mirrored
dual-tone player skin with a visible chain split, cold canonical circuitry, hot
reorg circuitry, and a fractured center line.

## Integration notes

The texture files live under `models/player/skins/rustchain_forker/` so they can
be packed into the RustChain PK3 with the rest of `pk3_build`.

The `.skin` file uses generic `default` and `glow` material names because this
repository does not currently include a canonical default player-model skin
template. If the final player model exposes specific material names, update
`rustchain_forker.skin` to map those material names to the same TGA files.

## Regeneration

From the repository root:

```bash
python tools/generate_rustchain_forker_skin.py
```

The generator is deterministic and uses Pillow only for raster drawing and file
encoding.

## License

The generated textures, preview, and procedural source are licensed under
CC-BY-SA-4.0. See `LICENSE`.
