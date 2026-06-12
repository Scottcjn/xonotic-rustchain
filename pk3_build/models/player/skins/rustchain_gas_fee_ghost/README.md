# RustChain Gas Fee Ghost player skin

One original blockchain-themed player skin texture set for the RustChain Arena.

| File | Purpose |
|---|---|
| `rustchain_gas_fee_ghost_diffuse.tga` | 1024x1024 diffuse map with spectral armor, fee wisps, and floating transaction numerals |
| `rustchain_gas_fee_ghost_glow.tga` | 1024x1024 glow/emission map for the ghost core, gas trails, and transaction glyphs |
| `rustchain_gas_fee_ghost_preview.png` | Preview render and texture thumbnails |
| `rustchain_gas_fee_ghost.skin` | Minimal DarkPlaces skin mapping for the texture pair |

## Theme

The design implements **Gas Fee Ghost** from the bounty brief: an ethereal,
transparent-looking player identity with pale cyan vapor, magenta fee spikes,
floating transaction numbers, RTC markings, and a bright gas-meter core.

## Integration notes

The texture files live under
`models/player/skins/rustchain_gas_fee_ghost/` so they can be packed into the
RustChain PK3 with the rest of `pk3_build`.

The `.skin` file uses generic `default` and `glow` material names because this
repository does not currently include a canonical default player-model skin
template. If the final player model exposes specific material names, update
`rustchain_gas_fee_ghost.skin` to map those material names to the same TGA
files.

## Regeneration

From the repository root:

```bash
python3 tools/generate_rustchain_gas_fee_ghost_skin.py
```

The generator is deterministic and uses Pillow only for raster drawing and file
encoding.

## License

The generated textures, preview, and procedural source are licensed under
CC-BY-SA-4.0. See `LICENSE`.
