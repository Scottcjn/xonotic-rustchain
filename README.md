# Xonotic RustChain Arena

[![BCOS Certified](https://img.shields.io/badge/BCOS-Certified-brightgreen?style=flat&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAxTDMgNXY2YzAgNS41NSAzLjg0IDEwLjc0IDkgMTIgNS4xNi0xLjI2IDktNi40NSA5LTEyVjVsLTktNHptLTIgMTZsLTQtNCA1LjQxLTUuNDEgMS40MSAxLjQxTDEwIDE0bDYtNiAxLjQxIDEuNDFMMTAgMTd6Ii8+PC9zdmc+)](BCOS.md)

**Xonotic RustChain Arena is an open-source Xonotic FPS mod that combines skill-based arena combat with verifiable RTC token rewards on the RustChain network.**

Built on the [Xonotic](https://xonotic.org/) DarkPlaces engine, the project adds a damage-driven blood economy, style multipliers, blockchain-themed weapons, local AI bots, anti-cheat checks, and optional Discord integration.

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

## Frequently Asked Questions

### What is Xonotic RustChain Arena?

Xonotic RustChain Arena is a GPL-licensed Xonotic mod that turns arena performance into locally tracked RTC rewards and provides bridges for syncing eligible rewards with RustChain.

### What is RTC?

RTC is the native token of [RustChain](https://rustchain.org), a Proof-of-Antiquity network designed to reward participation by vintage and uncommon computer hardware. In this mod, RTC amounts represent gameplay rewards generated from kills, style combos, and match results.

### Do I need cryptocurrency to play?

No. You can run the arena and its gameplay systems locally without owning RTC. RustChain connectivity is only needed when you want to participate in the network or sync eligible rewards.

### How do I start a local arena?

Install [Xonotic](https://xonotic.org/download/), clone this repository into the Xonotic directory, install the Python dependencies, and run `./rustchain_arena_full.sh`. The [Quick Start](#quick-start) section lists the exact commands.

### How are rewards calculated?

The game master combines weapon rewards, style rank multipliers, combos, and match outcomes. Reward tracking and network synchronization are implemented in `rustchain_rewards_bridge.py`; style progression is implemented in `rustchain_style_system.py`.

### How does the project discourage reward farming?

The project includes consensus-inspired anti-cheat checks for suspicious movement, stat manipulation, and coordinated farming. These controls are implemented in `rustchain_51_attack.py` and complement normal server administration.

### Can the AI features run locally?

Yes. Bot tactics can use a local [Ollama](https://ollama.com/) model, and the announcer can use a local XTTS setup. These integrations are optional; the core arena can run without an external hosted AI service.

### Where can I find related projects and contribution bounties?

Use the canonical [RustChain repository](https://github.com/Scottcjn/Rustchain), [RustChain Bounties](https://github.com/Scottcjn/rustchain-bounties), and [BoTTube](https://bottube.ai). Project-specific contribution opportunities are also listed below.

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
