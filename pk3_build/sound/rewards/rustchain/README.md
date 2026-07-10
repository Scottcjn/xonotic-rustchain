# RustChain Blood Economy Reward Alerts

Original blood economy reward alerts and procedural audio cue set for Xonotic
RustChain Arena reward, mining, wallet, and chain-state events. The six cues
are designed as short nonverbal HUD/gameplay alerts that can sit beside the
existing weapon and announcer sound sets without duplicating them.

## Files

| File | Intended event |
|------|----------------|
| `block_confirmed_pulse.ogg` | Block confirmed / round reward acknowledged |
| `reward_mint.ogg` | Reward minted or earned |
| `wallet_credit.ogg` | Wallet credited / payout landed |
| `chain_reorg_warning.ogg` | Chain reorganization or danger warning |
| `mining_tick_burst.ogg` | Mining/proof tick burst |
| `style_multiplier_lock.ogg` | Style multiplier or momentum lock-in |

## Technical Notes

- Format: OGG Vorbis, mono, 48 kHz.
- Source: deterministic oscillator/noise synthesis in
  `tools/audio/generate_rustchain_reward_alerts.py`.
- No external samples, recordings, speech models, or copyrighted source audio.
- Suggested virtual path: `sound/rewards/rustchain/<cue>.ogg`.

## License

CC0 1.0 Universal. See `LICENSE`.
