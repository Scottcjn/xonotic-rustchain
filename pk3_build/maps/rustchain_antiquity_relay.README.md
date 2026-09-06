# RustChain Antiquity Relay Yard — Bounty #14014

Original deterministic Xonotic DM/CA map package targeting one remaining distinct-layout slot under #14014.

## Concept

**Antiquity Relay Yard** is a two-lane arena inspired by vintage compute relay infrastructure. Parallel cyan relay lanes cross an offset central transfer spine, with asymmetric raised platforms, eight cover fins, and four compute bays. The flow is materially different from Mempool Vault, Antiquity Vault, Checkpoint Spire, and the separately submitted Ledger Exchange map.

## Deliverables

- editable `.map`
- compiled `.bsp`
- `.mapinfo` with DM + CA support
- deterministic 512x384 schematic levelshot
- four original 64x64 textures
- CC-BY-SA-4.0 license notice
- generator, validator, compiler logs, and SHA-256 manifest

The levelshot is a generated top-down schematic preview, not a claimed gameplay screenshot.

## QA

GitHub Actions builds the official Xonotic NetRadiant `q3map2`, compiles BSP/VIS/LIGHT against the current `Scottcjn/xonotic-rustchain` tree, rejects compiler error/leak markers, validates structural counts and image dimensions, and publishes the resulting BSP and logs.

## License

Original assets and source are CC-BY-SA-4.0.

## Claim boundary

Submission artifact only. No merge, acceptance, queued payout, pending transaction, or received RTC is asserted without authoritative maintainer evidence.
