# RustChain Mempool player skin

One original blockchain-themed player skin texture set for the RustChain Arena.

| File | Purpose |
|---|---|
| `rustchain_mempool_diffuse.tga` | 1024x1024 diffuse map with queued transaction nodes, fee lanes, and swarm links |
| `rustchain_mempool_glow.tga` | 1024x1024 glow/emission map for transaction nodes, lane traces, and the pending-tx core |
| `rustchain_mempool_preview.png` | Preview render and texture thumbnails |
| `rustchain_mempool.skin` | Minimal DarkPlaces skin mapping for the texture pair |

## Theme

The design implements **Mempool** from the skin wishlist: a cluster/swarm
character built from pending transaction nodes, queue bands, fee-lane markings,
and a bright pending-tx reactor.

## Integration notes

The texture files live under `models/player/skins/rustchain_mempool/` so they
can be packed into the RustChain PK3 with the rest of `pk3_build`.

The `.skin` file uses generic `default` and `glow` material names because this
repository does not currently include a canonical default player-model skin
template. If the final player model exposes specific material names, update
`rustchain_mempool.skin` to map those material names to the same TGA files.

## Regeneration

From the repository root:

```bash
python tools/generate_rustchain_mempool_skin.py
```

The generator is deterministic and uses Pillow only for raster drawing and file
encoding.

## License

The generated textures, preview, and procedural source are licensed under
CC-BY-SA-4.0. See `LICENSE`.
