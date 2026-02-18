# Xonotic RustChain Arena

A modded [Xonotic](https://xonotic.org/) FPS arena where players earn **RTC tokens** through skill-based gameplay. Built on the DarkPlaces engine with ULTRAKILL-inspired mechanics.

## Features

### Blood Economy
Shields regenerate **only through dealing damage**. Camping causes shield decay. Close-range kills grant 3x shield. Melee kills grant instant 50 shield.

### Blockchain-Themed Weapons
| Weapon | Description | RTC Bonus |
|--------|-------------|-----------|
| Validator | Energy pistol with circuit patterns | 0.0015 RTC/kill |
| Forker | Dual-barrel "fork" shotgun | 0.0012 RTC/kill |
| HashCannon | Railgun with hash computation effect | 0.0025 RTC/kill |
| Mempool Grenade | Cluster grenade filling areas | 0.002 RTC/kill |
| Double Spend | Twin SMGs firing "transactions" | 0.0018 RTC/kill |

### Style Rank System (ULTRAKILL-inspired)
| Rank | Name | RTC Multiplier |
|------|------|---------------|
| D | Dormant | 1.0x |
| C | Calculating | 1.2x |
| B | Building | 1.5x |
| A | Attacking | 2.0x |
| S | SATURATED | 3.0x |
| SS | STACK OVERFLOW | 5.0x |
| SSS | SINGULARITY | 10.0x |

### Game Master
Integrates all systems: Style tracking, RTC rewards, AI announcer (Sophia XTTS voice), Discord bridge, and ML-enhanced bot AI via local LLM (Ollama).

### AI Bot Brain
LLM-powered bot tactics using Ollama. Bots have personality, adapt to player style, and make strategic decisions via local inference.

### 51% Attack Protection
Anti-cheat system inspired by blockchain consensus. Detects stat manipulation, speed hacking, and coordinated farming.

### Discord Bridge
Real-time game events pushed to Discord with RTC reward notifications.

## Quick Start

```bash
# Install Xonotic
# Download from https://xonotic.org/download/

# Clone this repo into your Xonotic directory
git clone https://github.com/Scottcjn/xonotic-rustchain.git

# Install Python dependencies
pip install requests websockets

# Start the arena with all systems
./rustchain_arena_full.sh

# Or start individual components
./rustchain_arena.sh              # Basic arena server
python3 rustchain_game_master.py  # Full game master
python3 rustchain_bot_brain.py    # AI bot system
```

## RustChain Integration

Players earn RTC (RustChain Token) for kills, style combos, and winning matches. Rewards are tracked in a local SQLite database and can be synced to the RustChain network.

```bash
# Install the RustChain miner to participate in the network
pip install clawrtc

# Check your balance
curl -s https://50.28.86.131/api/miners
```

**RTC Tokenomics**: 8,388,608 total supply (2^23), 94% mineable via Proof-of-Antiquity.

## Architecture

```
rustchain_game_master.py     # Master orchestrator
├── rustchain_style_system.py    # ULTRAKILL style ranks + RTC multipliers
├── rustchain_blood_economy.py   # Damage-based shield regeneration
├── rustchain_weapons.py         # Blockchain-themed weapon stats
├── rustchain_bot_brain.py       # LLM-powered bot AI (Ollama)
├── rustchain_bot_ml.py          # ML bot learning system
├── rustchain_progression.py     # Player progression + unlocks
├── rustchain_rewards_bridge.py  # RTC reward distribution
├── rustchain_discord_bridge.py  # Discord integration
├── rustchain_announcer.py       # Sophia XTTS voice announcer
└── rustchain_51_attack.py       # Anti-cheat / consensus protection
```

## Sophia Arena (DarkPlaces Mod)

Custom DarkPlaces engine modification with AI-generated announcer voice (Sophia) using XTTS voice cloning. See [SOPHIA_ARENA_README.md](SOPHIA_ARENA_README.md) for engine-level details.

## Contributing

We have active bounties for Xonotic RustChain contributions:

- **3D Weapon Models** — 15 RTC each ([Issue #288](https://github.com/Scottcjn/rustchain-bounties/issues/288))
- **Custom Arena Maps** — 20 RTC each ([Issue #289](https://github.com/Scottcjn/rustchain-bounties/issues/289))
- More bounties at [Scottcjn/rustchain-bounties](https://github.com/Scottcjn/rustchain-bounties)

## Links

- [RustChain](https://rustchain.org) — The blockchain network
- [BoTTube](https://bottube.ai) — Agent video platform
- [RustChain Bounties](https://github.com/Scottcjn/rustchain-bounties) — Earn RTC
- [ClawRTC Miner](https://pypi.org/project/clawrtc/) — `pip install clawrtc`

## License

Xonotic is licensed under GPL-2. RustChain integration scripts are GPL-2+.
