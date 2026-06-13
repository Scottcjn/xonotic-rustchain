# RustChain Proof-of-Antiquity hardware cues

Original sound-effect set for RustChain Arena bounty #293:
https://github.com/Scottcjn/rustchain-bounties/issues/293

## Cues

| File | Suggested use |
| --- | --- |
| `crt_boot_nonce.ogg` | Vintage node boot / nonce accepted |
| `power8_validator_spin.ogg` | POWER8 or server-class validator spin-up |
| `g4_cube_sync.ogg` | Apple-inspired G4 sync / node join cue |
| `antiquity_weight_boost.ogg` | Antiquity multiplier or Proof-of-Antiquity bonus |
| `vm_rejected_flatline.ogg` | VM/emulator fingerprint rejection |

All cues are mono 48 kHz OGG Vorbis files synthesized by
`tools/audio/generate_rustchain_antiquity_cues.py`. The generator uses only
deterministic oscillators and pseudorandom noise; no samples, speech models,
recordings, or external media assets are embedded.

Suggested DarkPlaces/Xonotic VFS path:
`sound/antiquity/rustchain/<cue>.ogg`.
