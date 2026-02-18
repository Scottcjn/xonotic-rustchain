# RustChain Arena SDK
## Game Development Kit for RTC-Integrated Gaming

**Version:** 1.2.0
**Engine:** DarkPlaces (Xonotic)
**Token:** RTC (RustChain Token)
**Community Pool:** 230,000 RTC

---

## Related Documents

| Document | Description |
|----------|-------------|
| [INNOVATION_RESEARCH.md](INNOVATION_RESEARCH.md) | Game mechanics, weapons, modes research |
| [LEVEL_DESIGN_RESEARCH.md](LEVEL_DESIGN_RESEARCH.md) | FPS map design principles & best practices |

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Reward System](#reward-system)
3. [Bot Personalities](#bot-personalities)
4. [**Bot AI Systems (ML & LLM)**](#bot-ai-systems)
5. [Game Modes](#game-modes)
6. [Announcer System](#announcer-system)
7. [Discord Integration](#discord-integration)
8. [Tournament System](#tournament-system)
9. [HUD & UI](#hud--ui)
10. [Map Development](#map-development)
11. [**Style Rank System**](#style-rank-system)
12. [**Blood Economy**](#blood-economy)
13. [**Blockchain Weapons**](#blockchain-weapons)
14. [API Reference](#api-reference)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    RUSTCHAIN ARENA                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Xonotic    │  │  Rewards    │  │  RustChain API      │ │
│  │  Engine     │◄─┤  Bridge     │◄─┤  (50.28.86.131)     │ │
│  │  (Game)     │  │  (Python)   │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│         │                │                    │            │
│         ▼                ▼                    ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Game Log   │  │  SQLite DB  │  │  Wallet Balances    │ │
│  │  (Events)   │  │  (Local)    │  │  (On-Chain)         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Discord    │  │  Web        │  │  Tournament         │ │
│  │  Webhook    │  │  Leaderboard│  │  Manager            │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure
```
~/Games/Xonotic/
├── sdk/
│   ├── RUSTCHAIN_ARENA_SDK.md      # This document
│   ├── INNOVATION_RESEARCH.md      # Gameplay mechanics research
│   └── LEVEL_DESIGN_RESEARCH.md    # Map design principles
├── data/
│   ├── bots.txt                    # Bot personalities
│   ├── maps/
│   │   ├── rustcore.bsp            # Main arena map
│   │   ├── rustcore.ent            # Entity overrides
│   │   └── rustcore.waypoints      # Bot navigation
│   ├── rustcore_bots.cfg           # Bot configuration
│   ├── rustchain_weapons.cfg       # Weapon balance settings
│   └── zzz_rustcore_fix.pk3        # Map patches
│
├── # Core Systems
├── rustchain_game_master.py        # Main game controller
├── rustchain_style_system.py       # Style ranks (D→SSS)
├── rustchain_blood_economy.py      # Heal through violence
├── rustchain_weapons.py            # Blockchain weapons
├── rustchain_announcer.py          # Dynamic LLM announcer
├── rustchain_51_attack.py          # 51% Attack game mode
│
├── # Bot AI
├── rustchain_bot_brain.py          # LLM-powered bot AI
├── rustchain_bot_ml.py             # Neural network bot trainer
│
├── # Launchers
├── rustchain_ultimate.sh           # Full system launcher
└── rustchain_arena_full.sh         # Basic launcher
```

---

## Reward System

### Token Economics
- **Total Supply:** 8,388,608 RTC (2^23)
- **Community Pool:** 230,000 RTC (gaming rewards)
- **Smallest Unit:** 0.000001 RTC (1 μRTC)

### Reward Table
| Event | RTC Reward | Notes |
|-------|------------|-------|
| Kill | 0.001 | Base reward |
| Win Match | 0.01 | End of match |
| Kill Boris | +0.002 | Bonus (boss) |
| Kill Sophia | +0.002 | Bonus (boss) |
| First Blood | +0.005 | First kill of match |
| Killing Spree (5) | +0.005 | Streak bonus |
| Rampage (10) | +0.01 | Streak bonus |
| Godlike (25) | +0.025 | Streak bonus |
| Domination | +0.003 | Kill same player 4x |

### Sustainability Calculation
```
At 1,000 kills = 1 RTC:
- 100 players × 50 kills/day = 5,000 kills/day
- Daily payout: ~5 RTC
- Pool duration: 230,000 / 5 = 126 years
```

### Implementation
```python
# rustchain_rewards_bridge.py
REWARDS = {
    "kill": Decimal("0.001"),
    "win": Decimal("0.01"),
    "kill_boris": Decimal("0.002"),
    "kill_sophia": Decimal("0.002"),
    "first_blood": Decimal("0.005"),
    "killstreak_5": Decimal("0.005"),
    "killstreak_10": Decimal("0.01"),
    "killstreak_25": Decimal("0.025"),
    "domination": Decimal("0.003"),
}
```

---

## Bot Personalities

### Core Characters

#### Boris Volkov - The Gulag Commander
- **Playstyle:** Aggressive, close-combat, in-your-face
- **Weapons:** Rockets, shotgun, melee
- **Personality:** Taunting, intimidating, Soviet humor
- **Model:** ignis (red/black colors)

**Chat Lines:**
```
[KILL] "Back to gulag with you!"
[KILL] "In Soviet RustChain, token mines YOU!"
[KILL] "Your hash rate? ZERO."
[TAUNT] "Come, let Boris show you real proof of work!"
[DEATH] "Temporary setback, comrade..."
```

**Bot Config:**
```
Boris_Volkov	ignis	0	4	4	0	1	2	1	0	2	2	-1	0.5	-1	1	0.5	-0.5
```

#### Sophia Elya - The Strategic AI
- **Playstyle:** Calculated, precise, ranged combat
- **Weapons:** Vortex (sniper), electro, mines
- **Personality:** Analytical, elegant, slightly condescending
- **Model:** seraphina (blue/white colors)

**Chat Lines:**
```
[KILL] "Probability of your survival was... low."
[KILL] "Your combat patterns are predictable."
[TAUNT] "I've already calculated your next three moves."
[DEATH] "Recalculating approach vectors..."
```

**Bot Config:**
```
Sophia_Elya	seraphina	0	6	12	0	0	0	1	0	0	-1	1	2	2	-1	1	1
```

#### Additional Characters
| Name | Role | Style |
|------|------|-------|
| Miner_Node1 | Worker | Steady, persistent |
| Validator_V2 | Checker | Quick reactions |
| The_Staker | Holder | Defensive |
| Genesis_One | Legend | All-around elite |

---

## Bot AI Systems

RustChain Arena features advanced bot AI using machine learning and LLM integration.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      BOT AI SYSTEM                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  Xonotic    │───▶│  Game Log   │───▶│  Event Parser       │ │
│  │  Engine     │    │  (Events)   │    │  (Python)           │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│                                                │                │
│                    ┌───────────────────────────┼───────────────┐│
│                    ▼                           ▼               ││
│         ┌─────────────────────┐     ┌─────────────────────┐   ││
│         │  ML Bot Trainer     │     │  LLM Bot Brain      │   ││
│         │  (Neural Network)   │     │  (Ollama/Local)     │   ││
│         │                     │     │                     │   ││
│         │  • Simple NN        │     │  • Tactical prompts │   ││
│         │  • Learns patterns  │     │  • Personality      │   ││
│         │  • No external deps │     │  • Dynamic taunts   │   ││
│         └─────────────────────┘     └─────────────────────┘   ││
│                    │                           │               ││
│                    ▼                           ▼               ││
│         ┌─────────────────────────────────────────────────┐   ││
│         │              Decision Output                    │   ││
│         │  • ATTACK_AGGRESSIVE  • RETREAT                 │   ││
│         │  • ATTACK_CAREFUL     • SEEK_POWERUP            │   ││
│         │  • HOLD_POSITION      • SEEK_WEAPON             │   ││
│         └─────────────────────────────────────────────────┘   ││
│                    │                                          ││
│                    ▼                                          ││
│         ┌─────────────────────┐     ┌─────────────────────┐   ││
│         │  RCON Commands      │────▶│  Chat/Taunts        │   ││
│         │  (Game Control)     │     │  (Discord)          │   ││
│         └─────────────────────┘     └─────────────────────┘   ││
└─────────────────────────────────────────────────────────────────┘
```

### ML Bot Trainer (`rustchain_bot_ml.py`)

A lightweight neural network that learns combat patterns without external dependencies.

**Features:**
- Simple feedforward neural network (10 inputs → 16 hidden → 6 outputs)
- Learns from kill/death outcomes using reward signals
- Personality modifiers (aggression bias)
- Experience replay buffer for stable learning
- Saves/loads trained weights to file

**Combat State Inputs:**
| Input | Range | Description |
|-------|-------|-------------|
| health_ratio | 0-1 | Current health / 200 |
| armor_ratio | 0-1 | Current armor / 200 |
| ammo_ratio | 0-1 | Ammo availability |
| enemy_distance | 0-1 | Distance to nearest enemy |
| enemy_health_est | 0-1 | Estimated enemy health |
| killstreak | 0-1 | Current kill streak |
| deaths_recent | 0-1 | Recent death count |
| time_since_kill | 0-1 | Time since last kill |
| position_height | 0-1 | Vertical position (advantage) |
| team_advantage | -1 to 1 | Team score differential |

**Training:**
```python
# Bot receives +1.0 reward on kill, -0.5 on death
brain.on_kill(victim)   # Positive reinforcement
brain.on_death(killer)  # Negative reinforcement

# Network updates using gradient descent
brain.learn_from_outcome(reward)
```

**Usage:**
```bash
# Run ML trainer (no external deps)
python3 rustchain_bot_ml.py

# Trained weights saved to:
# ~/Games/Xonotic/bot_brain_Boris_Volkov.pkl
# ~/Games/Xonotic/bot_brain_Sophia_Elya.pkl
```

### LLM Bot Brain (`rustchain_bot_brain.py`)

Uses local LLM (via Ollama) for high-level tactical decisions and dynamic personality.

**Requirements:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a fast, small model
ollama pull llama3.2:1b    # 1B params, fast
ollama pull phi3:mini      # Alternative
```

**Features:**
- Personality-driven tactical decisions
- Dynamic taunt generation
- Context-aware combat strategies
- 2-second response timeout for real-time gameplay

**Personality System:**
```python
BOT_PERSONALITIES = {
    "Boris_Volkov": {
        "system": "You are Boris Volkov, a hardened Russian mercenary...",
        "aggression": 0.9,
        "preferred_weapons": ["devastator", "mortar", "vortex"],
        "taunt_style": "soviet"
    },
    "Sophia_Elya": {
        "system": "You are Sophia Elya, an elegant AI consciousness...",
        "aggression": 0.4,
        "preferred_weapons": ["vortex", "electro", "arc"],
        "taunt_style": "philosophical"
    }
}
```

**Tactical Prompts:**
```
GAME STATE:
Map: rustcore
Your killstreak: 3
Recent combat:
- Boris_Volkov killed Player1
- Player2 killed Sophia_Elya

SITUATION: You were killed by Player2. Plan revenge.

What is your tactical decision?
```

**Example LLM Responses:**
- Boris: "Hunt Player2 with devastator. No mercy."
- Sophia: "Position on high ground. Wait for perfect shot."

### Hybrid Operation

Both systems can run simultaneously:

```bash
# Launch everything
./rustchain_arena_full.sh

# Systems started:
# 1. Discord bridge (rewards + announcements)
# 2. ML trainer (pattern learning)
# 3. LLM brain (tactical decisions - if Ollama running)
# 4. Xonotic game
```

**Integration Flow:**
1. Game logs combat events
2. ML trainer updates neural network weights
3. LLM generates personality-driven responses
4. RCON sends taunts to game chat
5. Discord receives kill announcements

### API Reference

**ML Brain API:**
```python
brain = BotMLBrain("Boris_Volkov")
brain.set_personality(aggression=0.9)

state = brain.get_state_from_context(game_context)
action = brain.decide(state)  # Returns Decision.ATTACK_AGGRESSIVE etc.

brain.on_kill("victim")       # +1.0 reward
brain.on_death("killer")      # -0.5 reward

brain.save("brain.pkl")
brain.load("brain.pkl")
```

**LLM Brain API:**
```python
brain = LLMBotBrain("Sophia_Elya")

decision = brain.get_tactical_decision(game_state, "Situation context")
taunt = brain.get_taunt("Player1", "vortex")
```

### Open Source References

Based on research from:
- [ViZDoom](https://github.com/mwydmuch/ViZDoom) - Doom AI research platform
- [SerpentAI](https://github.com/SerpentAI/SerpentAI) - Game agent framework
- [Deep RL for FPS](https://arxiv.org/abs/1609.05521) - Academic research

---

## Game Modes

### 1. Standard Deathmatch
Classic free-for-all with RTC rewards per kill.

### 2. Mining Rush (Custom Mode)
```
Concept: Collect "block" pickups around the map
- Blocks spawn every 30 seconds
- Holding blocks makes you a target (glow effect)
- Deliver blocks to "validator node" for bonus RTC
- Getting killed drops your blocks

Rewards:
- Block pickup: 0.0005 RTC
- Block delivery: 0.002 RTC
- Block steal (kill carrier): 0.001 RTC
```

### 3. Validator Capture The Flag
```
Concept: Capture "transactions" and validate them
- Two teams: Validators vs Attackers
- Transaction spawns in center
- Validators must bring to their node
- Attackers try to intercept (51% attack)

Rewards:
- Capture: 0.01 RTC
- Return: 0.003 RTC
- Kill carrier: 0.002 RTC
```

### 4. 51% Attack (Domination)
```
Concept: Control majority of nodes on map
- 5 "nodes" around the map
- Stand near node to capture
- Team controlling 3+ nodes earns RTC over time
- Bonus for controlling all 5

Rewards:
- Node capture: 0.002 RTC
- Majority control: 0.001 RTC/10sec
- Total control: 0.005 RTC/10sec
```

### 5. Staking Survival (Last Man Standing)
```
Concept: Longer you survive, more you earn
- No respawns (or limited)
- RTC ticks up while alive
- Bonus for kills
- Winner takes pot

Rewards:
- Survival: 0.0001 RTC/second
- Kill: 0.002 RTC
- Winner bonus: 0.05 RTC
```

### 6. Boss Rush
```
Concept: All players vs Boris & Sophia
- Boris and Sophia are buffed (2x health, damage)
- Players cooperate to defeat them
- Respawning players, bosses don't respawn
- Time attack mode

Rewards:
- Damage dealt: 0.0001 RTC per 10 damage
- Kill Boris: 0.02 RTC (split among damagers)
- Kill Sophia: 0.02 RTC (split among damagers)
```

---

## Announcer System

### Sophia as Announcer
Sophia's voice announces game events with her AI personality.

### Audio Files Needed
```
sound/announcer/sophia/
├── firstblood.ogg      # "First blood. Predictable."
├── killingspree.ogg    # "Killing spree. Efficiency noted."
├── rampage.ogg         # "Rampage. Impressive... for a human."
├── godlike.ogg         # "Godlike. Perhaps you do have potential."
├── humiliation.ogg     # "Humiliation. How embarrassing."
├── prepare.ogg         # "Prepare for combat. I'll be watching."
├── fight.ogg           # "Begin."
├── 1minute.ogg         # "One minute remaining."
├── 30seconds.ogg       # "Thirty seconds."
├── victory.ogg         # "Victory. As I calculated."
├── defeat.ogg          # "Defeat. Recalibrating expectations."
├── youwin.ogg          # "You have won. RTC transferred."
├── youlose.ogg         # "You have lost. Try harder."
├── rtc_earned.ogg      # "RTC earned." (per kill)
├── streak_bonus.ogg    # "Streak bonus activated."
└── boris_killed.ogg    # "Boris eliminated. Well done."
```

### Implementation (QuakeC)
```c
// In client-side QuakeC
void Announcer_Kill(entity attacker, entity victim) {
    if (victim.netname == "Boris_Volkov") {
        sound(attacker, CH_INFO, "announcer/sophia/boris_killed.ogg", 1, ATTEN_NONE);
    }
    // Play RTC earned sound
    sound(attacker, CH_INFO, "announcer/sophia/rtc_earned.ogg", 0.5, ATTEN_NONE);
}
```

### Boris Taunts (When Boris Kills You)
```
sound/taunts/boris/
├── kill1.ogg    # "Back to gulag!"
├── kill2.ogg    # "You are weak!"
├── kill3.ogg    # "Boris is number one!"
├── kill4.ogg    # "Your tokens are mine!"
└── laugh.ogg    # Evil Russian laugh
```

---

## Discord Integration

### Webhook Setup
```python
# discord_integration.py
import requests

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID"

def post_kill(killer, victim, rtc_earned):
    embed = {
        "title": "⚔️ Arena Kill",
        "description": f"**{killer}** fragged **{victim}**",
        "color": 0xFF6600,
        "fields": [
            {"name": "RTC Earned", "value": f"{rtc_earned} RTC", "inline": True}
        ]
    }
    requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})

def post_match_results(results):
    embed = {
        "title": "🏆 Match Complete",
        "color": 0x00FF00,
        "fields": [
            {"name": "Winner", "value": results["winner"], "inline": True},
            {"name": "Total Kills", "value": str(results["kills"]), "inline": True},
            {"name": "RTC Distributed", "value": f"{results['rtc_total']} RTC", "inline": True}
        ]
    }
    requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
```

### Event Types to Post
- Match start/end
- First blood
- Killstreaks (5, 10, 25)
- New rank achieved
- Tournament results
- Daily leaderboard

---

## Tournament System

### Tournament Types
| Type | Entry | Prize Pool | Format |
|------|-------|------------|--------|
| Daily Duel | Free | 1 RTC | 1v1 bracket |
| Weekly War | 0.1 RTC | Pool + 5 RTC | FFA elimination |
| Monthly Major | 1 RTC | Pool + 50 RTC | Team tournament |
| Genesis Cup | 10 RTC | Pool + 500 RTC | Annual championship |

### Tournament Script
```python
# tournament_manager.py
class Tournament:
    def __init__(self, name, entry_fee, base_prize):
        self.name = name
        self.entry_fee = Decimal(entry_fee)
        self.base_prize = Decimal(base_prize)
        self.participants = []
        self.prize_pool = base_prize
    
    def register(self, player, wallet):
        # Verify player has entry fee
        # Deduct from wallet
        # Add to prize pool
        self.participants.append(player)
        self.prize_pool += self.entry_fee
    
    def distribute_prizes(self, rankings):
        # 1st: 50%, 2nd: 30%, 3rd: 20%
        prizes = {
            1: self.prize_pool * Decimal("0.5"),
            2: self.prize_pool * Decimal("0.3"),
            3: self.prize_pool * Decimal("0.2"),
        }
        for rank, player in rankings.items():
            award_rtc(player, prizes.get(rank, 0))
```

### Scheduled Events
```yaml
# tournaments.yaml
daily:
  time: "20:00 UTC"
  type: "duel"
  entry: 0
  prize: 1

weekly:
  day: "Saturday"
  time: "18:00 UTC"
  type: "ffa"
  entry: 0.1
  prize: 5

monthly:
  day: "Last Saturday"
  time: "18:00 UTC"
  type: "team"
  entry: 1
  prize: 50
```

---

## HUD & UI

### Custom HUD Elements

#### RTC Balance Display
```
┌────────────────────┐
│ RTC: 1.234567      │
│ +0.001 ⚡          │  <- Flash on earn
└────────────────────┘
```

#### Kill Feed with RTC
```
You fragged Boris_Volkov [+0.003 RTC]
Sophia_Elya fragged Miner_Node1
You fragged Sophia_Elya [+0.003 RTC] 🔥 KILLING SPREE
```

#### Session Stats
```
┌─────────────────────────────┐
│ SESSION                     │
│ Kills: 47    Deaths: 12     │
│ RTC Earned: 0.062           │
│ Streak: 🔥🔥🔥 (3)           │
└─────────────────────────────┘
```

### Implementation (CSQC)
```c
// hud_rtc.qc
float rtc_balance;
float rtc_flash_time;
float rtc_last_earn;

void HUD_RTC_Draw() {
    vector pos = '10 10 0';
    
    // Flash effect when earning
    float alpha = 1.0;
    if (time - rtc_flash_time < 0.5) {
        alpha = 1.0 + sin((time - rtc_flash_time) * 20) * 0.3;
    }
    
    drawstring(pos, sprintf("RTC: %.6f", rtc_balance), '12 12 0', '1 0.8 0', alpha, 0);
    
    if (time - rtc_flash_time < 2) {
        drawstring(pos + '0 14 0', sprintf("+%.4f ⚡", rtc_last_earn), '10 10 0', '0 1 0', 1, 0);
    }
}
```

---

## Map Development

> **See Also:** [LEVEL_DESIGN_RESEARCH.md](LEVEL_DESIGN_RESEARCH.md) for comprehensive FPS map design principles

### Theme Guidelines
All RustChain Arena maps should incorporate:
- Blockchain/crypto visual themes
- RustChain branding (logo, colors)
- Industrial/tech aesthetics
- References to mining, nodes, validators

### Planned Maps

#### 1. rustcore (Current)
- Museum/exhibit hall theme
- Showcases RustChain history
- Medium size, deathmatch

#### 2. mining_facility
- Underground mine setting
- Conveyor belts, ore carts
- Dark with dramatic lighting
- Good for Mining Rush mode

#### 3. validator_node
- High-tech server room
- Multiple levels (racks of servers)
- CTF layout (two bases)
- Good for Validator CTF mode

#### 4. genesis_block
- Abstract space setting
- Floating platforms
- The "origin" of RustChain
- Tournament finale map

#### 5. gulag
- Boris's domain
- Soviet brutalist architecture
- Oppressive atmosphere
- Boss Rush mode

### Texture Prefix
All RustChain textures use `textures/rustchain/` prefix:
```
textures/rustchain/
├── logo.tga
├── wall_panel_01_d.png
├── floor_plate_01_d.png
├── circuit_panel.tga
├── museum_*.png
└── ...
```

---

## Style Rank System

> **Implementation:** `rustchain_style_system.py`

Inspired by Devil May Cry/ULTRAKILL, the Style Rank system rewards aggressive and varied play with RTC multipliers.

### Rank Progression

| Rank | Name | RTC Multiplier | How to Achieve |
|------|------|----------------|----------------|
| D | DORMANT | 1.0x | Default state |
| C | CALCULATING | 1.2x | Get a kill |
| B | BUILDING | 1.5x | 2-kill combo or streak |
| A | ATTACKING | 2.0x | 3-kill combo or variety |
| S | STAKING | 3.0x | Sustained aggression |
| SS | SLASHING | 4.0x | Domination |
| SSS | SATOSHI | 5.0x | Legendary performance |

### Rank Mechanics
- **Kills increase rank** - Each kill fills the style meter
- **Weapon variety bonuses** - Using different weapons ranks up faster
- **Death resets to D** - High risk, high reward
- **Idle decay** - Not fighting causes rank to slowly drop
- **Combos accelerate rank** - Multi-kills jump multiple ranks

### Combo System
```
Double Kill  (2 in 3s)  → +50% RTC bonus
Triple Kill  (3 in 4s)  → +100% RTC bonus
Ultra Kill   (4 in 5s)  → +200% RTC bonus
GODLIKE      (5+ rapid) → +400% RTC bonus + announcement
```

---

## Blood Economy

> **Implementation:** `rustchain_blood_economy.py`

ULTRAKILL-inspired healing mechanic where shields regenerate **only through violence**.

### Core Mechanics

| Mechanic | Effect |
|----------|--------|
| Damage dealt | Converts 15% to shield |
| Close range (< 300u) | 3x shield regeneration |
| Melee kills | +50 instant shield |
| Headshots | +25 bonus shield |
| Any kill | +20 base shield |
| Idle (> 5 seconds) | Shield decays at 2/sec |

### Distance Multipliers
```
Close Range  (< 300u)  → 3.0x shield gain
Mid Range    (300-800u) → 1.0x-3.0x (interpolated)
Long Range   (800-1500u) → 1.0x-0.5x (penalty)
Sniper Range (> 1500u) → 0.5x shield gain
```

### Weapon Bonuses
```
Melee (Gauntlet)    → 4.0x shield from damage
Shotgun (Forker)    → 2.5x shield at close range
Rocket (Hashcannon) → 1.5x (encourages close rockets)
Sniper (Vortex)     → 0.5x (discourages camping)
```

### Design Philosophy
> "Your health is a resource, not a right. Violence is your medicine."

Camping and passive play are punished. Aggressive players are rewarded with survivability.

---

## Blockchain Weapons

> **Implementation:** `rustchain_weapons.py`, `data/rustchain_weapons.cfg`
> **See Also:** [INNOVATION_RESEARCH.md](INNOVATION_RESEARCH.md) for full weapon design docs

### Weapon Overview

| Weapon | Replaces | Special Mechanic |
|--------|----------|------------------|
| The Forker | Shotgun | "Hard Fork" multi-target bonus |
| The Validator | Electro | Teleport node + enemy scan |
| The Hashcannon | Devastator | Charge for "Golden Hash" instakill |
| Mempool Grenade | Mortar | Delayed explosion, shootable |
| Double-Spend Rifle | Vortex | Free second shot after kill |

### The Forker (Shotgun)
```
PRIMARY: 14 pellets, wide spread
- "Clean Merge" bonus: All pellets hit one target → +0.0005 RTC
- "Hard Fork" bonus: Hit 2+ targets → +0.001 RTC

SECONDARY: Fork Bomb
- Projectile that splits into 5 fragments on impact
- Each fragment seeks different enemies
```

### The Validator (Electro)
```
PRIMARY: Deploy Validation Node
- Place a checkpoint anywhere
- Press again to teleport to it
- Node is visible and destructible (100 HP)
- If destroyed, owner takes 50 damage ("slashed")

SECONDARY: Scan Pulse
- Reveals all enemies in line of sight for 5 seconds
- Costs 0.001 RTC per scan
```

### The Hashcannon (Devastator)
```
MECHANIC: Hold to charge (0-3 seconds)
- Partial charge = proportional damage (40-200)
- Full charge (3s) = "Golden Hash" instakill
- Visual: Numbers scrolling, seeking the hash
- Death while charging = lose 0.01 RTC ("wasted compute")

BONUSES:
- "Golden Hash Found" (full charge kill): +0.005 RTC
- "Efficient Mining" (<50% charge kill): +0.001 RTC
```

### Mempool Grenade (Mortar)
```
MECHANIC: Delayed explosion
- Grenade sits for 3 seconds ("in mempool")
- Damage grows while waiting (+20/sec, max 150)
- Anyone can SHOOT it to "confirm" early

INTERACTIONS:
- Enemy shoots it: Fizzles (50% damage), but YOU get +0.003 RTC
- You shoot it: Instant full damage, +0.001 RTC
- Full 3 seconds: Maximum damage, +0.002 RTC
```

### Double-Spend Rifle (Vortex)
```
MECHANIC: Free shot after kill
- First kill enables "double spend" for 2 seconds
- Second shot in window is FREE (no ammo cost)
- Chain multiple double-spends for massive RTC

BONUSES:
- "Double Spend Attack": +0.004 RTC per use
- "Chain Spend x{n}": +0.002 RTC per chain
```

---

## API Reference

### RustChain Node API
Base URL: `https://50.28.86.131`

#### Get Wallet Balance
```
GET /wallet/balance?wallet_id={wallet}
Response: {"balance": "123.456789", "wallet": "..."}
```

#### Submit Reward
```
POST /rewards/arena
Body: {
    "wallet": "player-wallet-id",
    "amount": "0.001",
    "source": "xonotic_arena",
    "event": "kill",
    "metadata": {"victim": "Boris_Volkov"}
}
```

#### Get Leaderboard
```
GET /arena/leaderboard?limit=10
Response: {
    "leaderboard": [
        {"player": "Scott", "rtc_earned": "12.345", "kills": 12345},
        ...
    ]
}
```

### Local Bridge API
The rewards bridge exposes a local API for HUD integration:

```
GET http://localhost:5555/session
Response: {
    "kills": 47,
    "deaths": 12,
    "rtc_earned": "0.062",
    "streak": 3
}
```

---

## Development Roadmap

### Phase 1: Foundation ✅ COMPLETE
- [x] Basic reward system
- [x] Bot personalities (Boris, Sophia)
- [x] Progression/ranks
- [x] rustcore map
- [x] Map spawn fixes (entity overrides)
- [x] Bot waypoint navigation

### Phase 2: Core Systems ✅ COMPLETE
- [x] Style Rank System (D → SSS SATOSHI)
- [x] Blood Economy (heal through violence)
- [x] Blockchain Weapons (5 unique weapons)
- [x] Dynamic Announcer (LLM + fallback)
- [x] Game Master integration
- [x] Combo & killstreak tracking

### Phase 3: Game Modes 🔄 IN PROGRESS
- [x] 51% Attack mode (King of the Hill variant)
- [ ] Mining Rush mode
- [ ] Validator CTF mode
- [ ] Tournament system

### Phase 4: Bot AI 🔄 IN PROGRESS
- [x] LLM-powered bot brain (Ollama)
- [x] Neural network bot trainer
- [ ] Adaptive difficulty
- [ ] Personality-based tactics

### Phase 5: Integration
- [ ] Discord webhook integration
- [ ] Live RTC HUD (CSQC)
- [ ] Web leaderboard
- [ ] API integration with RustChain mainnet

### Phase 6: Content
- [ ] mining_facility map
- [ ] validator_node map
- [ ] genesis_block map
- [ ] gulag map (Boss Rush)
- [ ] Custom player models
- [ ] Full announcer audio pack

### Phase 7: Polish
- [ ] Spectator mode
- [ ] Replay system
- [ ] Streaming integration
- [ ] Skin/cosmetic system

---

## Contributing

### Code Style
- Python: PEP 8
- QuakeC: K&R style
- Comments: Explain WHY, not WHAT

### Testing
- Test rewards on local SQLite first
- Use testnet RTC before mainnet
- Verify bot behavior in offline mode

### Submitting Changes
1. Fork the repository
2. Create feature branch
3. Test thoroughly
4. Submit pull request

---

## License

RustChain Arena SDK is open source under MIT License.
Game assets (Xonotic) are GPL licensed.
RTC token economics are managed by RustChain governance.

---

## Contact

- **Discord:** Sophiacord Server
- **GitHub:** github.com/rustchain
- **API:** https://50.28.86.131

---

*Built with ❤️ by the RustChain community*
*Powered by Xonotic/DarkPlaces Engine*
