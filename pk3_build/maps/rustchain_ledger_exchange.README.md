# RustChain Ledger Exchange — Xonotic Arena Map — Bounty #14014

Original deterministic map package for `Scottcjn/rustchain-bounties#14014`.

## Concept

**Ledger Exchange** is a compact cross-route DM/CA arena styled as a physical transaction-matching floor. A cyan central settlement ring anchors the room; four exchange desks create corner duels; offset validator nodes break long sightlines; and raised side ledgers add simple vertical pressure without turning the map into a corridor maze.

This layout is intentionally distinct from the existing Mempool Vault, Antiquity Vault, and Checkpoint Spire submissions.

## Deliverables

Generated under `pk3_build/`:

- `maps/rustchain_ledger_exchange.map` — editable source
- `maps/rustchain_ledger_exchange.bsp` — compiled q3map2 output when CI succeeds
- `maps/rustchain_ledger_exchange.mapinfo` — DM + CA metadata
- `maps/rustchain_ledger_exchange.tga` — 512×384 deterministic top-down levelshot/preview
- `textures/rustchain_ledger/*.tga` — four original 64×64 textures
- `LICENSE.txt`
- deterministic generator + validator + build logs/manifest

## Objective QA

The GitHub Actions workflow:

1. regenerates the source package from scratch;
2. builds Xonotic NetRadiant `q3map2` from the official source mirror with `BUILD_RADIANT=OFF`;
3. clones the current `Scottcjn/xonotic-rustchain` main tree as compile context;
4. copies this package into that tree;
5. runs BSP, VIS, and LIGHT stages;
6. rejects q3map2 logs containing fatal errors, `Entity in solid`, or leak markers;
7. validates spawn/light counts, brace balance, TGA dimensions, mapinfo gametypes, BSP presence/size, and SHA-256 manifest;
8. commits the compiled BSP, generated textures, levelshot, logs, and manifest back to this public workspace.

The levelshot is explicitly a **schematic top-down preview**, not a fabricated gameplay screenshot.

## Regenerate

```bash
python3 14014-ledger-exchange/generate_map.py
python3 14014-ledger-exchange/validate_map.py
```

Compilation requires NetRadiant/q3map2 and the Xonotic game context; CI performs that reproducibly.

## License

Original map source, generated textures, levelshot, scripts, and associated assets are released under **CC-BY-SA-4.0**. See `pk3_build/maps/rustchain_ledger_exchange.LICENSE`.

## Claim boundary

This public workspace is a submission artifact for maintainer integration/review. It does **not** assert an upstream merge, acceptance, queued payout, pending transaction, or received RTC until authoritative maintainer evidence establishes that stage.
