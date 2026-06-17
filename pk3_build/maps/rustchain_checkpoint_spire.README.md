# RustChain Checkpoint Spire

Original Xonotic RustChain Arena map for bounty #14014:
https://github.com/Scottcjn/rustchain-bounties/issues/14014

## Package

- `rustchain_checkpoint_spire.map` - source map
- `rustchain_checkpoint_spire.bsp` - compiled BSP generated from q3map2
- `rustchain_checkpoint_spire.mapinfo` - DM/CA map metadata
- `rustchain_checkpoint_spire.tga` - 512x384 levelshot preview
- `rustchain_checkpoint_spire.LICENSE` - CC-BY-SA-4.0 license grant

## Design

Checkpoint Spire is a compact cross-flow arena built around a glowing central checkpoint
tower, four raised validation decks, stair-fed side routes, and low hash blocks for
duel cover. It is distinct from the existing museum, mempool-vault, and antiquity-vault
layouts: this one emphasizes a central vertical reward pillar with four fast re-entry
routes rather than a vault-room or museum-showcase structure.

The geometry, levelshot, and metadata are generated deterministically by:

```bash
python3 tools/generate_rustchain_checkpoint_spire.py
```
