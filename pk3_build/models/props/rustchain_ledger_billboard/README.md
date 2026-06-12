# RustChain Ledger Billboard Prop

Original low-poly static prop for the Xonotic RustChain Arena prop bounty #14015.

## Contents
- `rustchain_ledger_billboard.iqm` -- static IQM mesh for Xonotic packaging.
- `rustchain_ledger_billboard.obj` + `.mtl` -- editable source mesh.
- `textures/*.tga` -- 256x256 power-of-two diffuse/glow textures.
- `rustchain_ledger_billboard.skin` -- material mapping hint for frame, screen, and glow surfaces.
- `preview.png` -- generated preview render.
- `tools/generate_rustchain_ledger_billboard_prop.py` -- deterministic source generator.

## Integration
Suggested path: `pk3_build/models/props/rustchain_ledger_billboard/`.
Use near spawn corridors, score rooms, or capture-point approaches as a diegetic chain-status display. The prop footprint is about 2.4 x 0.35 x 2.7 units before mapper scaling.

## License
CC-BY-SA-4.0 / GPL-compatible for inclusion in the Xonotic RustChain Arena assets.
