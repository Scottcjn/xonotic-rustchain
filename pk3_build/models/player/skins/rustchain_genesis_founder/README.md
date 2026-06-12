# RustChain Genesis / Founder player skin

One original blockchain-themed player skin texture set for the RustChain Arena.

| File | Purpose |
|---|---|
| `rustchain_genesis_founder_diffuse.tga` | 1024x1024 diffuse map with founder-gold armor, genesis block core, laurel trim, and origin ledger markings |
| `rustchain_genesis_founder_glow.tga` | 1024x1024 glow/emission map for gold traces, crest halo, and genesis medallion |
| `rustchain_genesis_founder_preview.png` | Preview render and texture thumbnails |
| `rustchain_genesis_founder.skin` | Minimal DarkPlaces skin mapping for the texture pair |

## Theme

The design implements **Genesis / Founder** from the skin wishlist: a
gold-accent prestige character with a genesis block chest medallion, founder
crest, laurel trim, origin-block hash fragments, and warm white-gold glow.

## Integration notes

The texture files live under `models/player/skins/rustchain_genesis_founder/`
so they can be packed into the RustChain PK3 with the rest of `pk3_build`.

The `.skin` file uses generic `default` and `glow` material names to match the
accepted RustChain skin submissions in this repository.

## Regeneration

From the repository root:

```bash
python tools/generate_rustchain_genesis_founder_skin.py
```

The generator is deterministic and uses Pillow only for raster drawing and file
encoding.

## License

The generated textures, preview, and procedural source are licensed under
CC-BY-SA-4.0. See `LICENSE`.
