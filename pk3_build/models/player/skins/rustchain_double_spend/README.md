# RustChain Double Spend player skin

One original blockchain-themed player skin texture set for the RustChain Arena.

| File | Purpose |
|---|---|
| `rustchain_double_spend_diffuse.tga` | 1024x1024 diffuse map with split duplicate armor, conflicting transaction packets, and fork-race glyphs |
| `rustchain_double_spend_glow.tga` | 1024x1024 glow/emission map for the twin silhouettes, disputed center line, packet trails, and glitch tears |
| `rustchain_double_spend_preview.png` | Preview render and texture thumbnails |
| `rustchain_double_spend.skin` | Minimal DarkPlaces skin mapping for the texture pair |

## Theme

The design implements **Double Spend** from the open skin wishlist: a
twin/glitch-duplicate character with one cool cyan spend, one hot red spend,
and a disputed gold center line where both transactions race for the same
input.

## Integration notes

The texture files live under
`models/player/skins/rustchain_double_spend/` so they can be packed into the
RustChain PK3 with the rest of `pk3_build`.

The `.skin` file uses generic `default` and `glow` material names because this
repository does not currently include a canonical default player-model skin
template. If the final player model exposes specific material names, update
`rustchain_double_spend.skin` to map those material names to the same TGA
files.

## Regeneration

From the repository root:

```bash
python3 tools/generate_rustchain_double_spend_skin.py
```

The generator is deterministic and uses Pillow only for raster drawing and file
encoding.

## License

The generated textures, preview, and procedural source are licensed under
CC-BY-SA-4.0. See `LICENSE`.
