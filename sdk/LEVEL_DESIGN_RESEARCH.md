# RustChain Arena - Level Design Research
## Creating Exceptional FPS Multiplayer Maps

**Research Date:** December 2024
**Goal:** Establish level design principles for engaging arena shooter maps

---

## Executive Summary

Great FPS multiplayer maps share common principles: predictable flow patterns, meaningful player choices, balanced sightlines, and strategic item placement. This document synthesizes research from classic arena shooters (Quake, Unreal Tournament) and modern competitive FPS (CS:GO, Valorant) to guide RustChain Arena map development.

### The Core Principles
1. **Flow** - Circular/figure-8 patterns with no dead ends
2. **Connectivity** - 3+ routes between major areas
3. **Verticality** - Height variation increases gameplay density
4. **Risk/Reward** - Power items in exposed positions
5. **Readable Sightlines** - Clear lanes, not guess-work

---

## Part 1: Map Flow & Circulation

### What is Flow?
Flow describes how players move through a level—the feeling of traversing paths between areas. Good flow creates a rhythm: approach, engage, disengage, reposition, repeat.

> "A circle is the simplest kind of flow a level could have. While you would almost never design a level that only flowed in a circle, sometimes you can define your major flow path as a simple circuit through the level."
> — [On Game Design](https://www.ongamedesign.net/designing-fps-multiplayer-maps-part-1/)

### Flow Patterns

#### 1. Circular Flow
```
    ┌─────────┐
    │         │
    │    A    │
    │         │
    └────┬────┘
         │
    ┌────┴────┐
    │         │
    │    B    │
    │         │
    └────┬────┘
         │
    ┌────┴────┐
    │         │
    │    C    │
    │         │
    └─────────┘
         ↑
         └──────────┐
                    │
              loops back to A
```
- Players never need to turn around
- Minimum viable competitive layout
- Works for small deathmatch arenas

#### 2. Figure-8 Flow (Recommended)
```
       ┌─────────────┐
       │             │
   ┌───┤      A      ├───┐
   │   │             │   │
   │   └──────┬──────┘   │
   │          │          │
   │   ┌──────┴──────┐   │
   │   │             │   │
   └───┤   CENTER    ├───┘
       │   (cross)   │
   ┌───┤             ├───┐
   │   └──────┬──────┘   │
   │          │          │
   │   ┌──────┴──────┐   │
   │   │             │   │
   └───┤      B      ├───┘
       │             │
       └─────────────┘
```
- Combines benefits of circles with a crossing point
- Creates "incredibly involved and complex flows"
- Natural chokepoint at intersection
- Best for 1v1 and small team modes

#### 3. Three-Loop Overlay (CS:GO Standard)
```
          LOOP 1
       ┌─────────┐
       │    T    │
       │  SPAWN  │
       └────┬────┘
            │
     ┌──────┼──────┐
     │      │      │
  ┌──┴──┐ ┌─┴─┐ ┌──┴──┐
  │  A  │ │MID│ │  B  │     LOOP 2 & 3
  │SITE │ │   │ │SITE │     (overlapping)
  └──┬──┘ └─┬─┘ └──┬──┘
     │      │      │
     └──────┼──────┘
            │
       ┌────┴────┐
       │   CT    │
       │  SPAWN  │
       └─────────┘
```
- Three big loops overlaid on each other
- Smaller connector loops between major routes
- Prevents "guess maps" while maintaining options

### Flow Design Rules

| Rule | Why It Matters |
|------|----------------|
| No dead ends | Players shouldn't be trapped; retreating is valid strategy |
| 3+ exits per area | Prevents camping, enables flanking |
| Clear sight of exits | Players can plan escape routes |
| Varying path lengths | Creates timing decisions (fast risky vs slow safe) |
| Circulation over sequence | Multiplayer maps are networks, not linear paths |

---

## Part 2: Sightlines & Cover

### Understanding Sightlines

A sightline is an uninterrupted line from the player's view to another point. Sightlines determine:
- Where combat can occur
- Which weapons are effective
- How defensible a position is

> "Position determines your line of sight to other people. Line of sight represents a direct connection and attacking capability."
> — [CritPoints](https://critpoints.net/2018/02/18/good-fps-map-design/)

### Sightline Types

#### Long Sightlines (Sniper Alleys)
```
[Player]═══════════════════════════════[Target]
         │                           │
         └───────────────────────────┘
              No cover, long range
```
- Favor precision weapons (Vortex/Double-Spend Rifle)
- Create risk for crossers
- Should have alternative routes around them

#### Short Sightlines (Close Quarters)
```
    ┌───┐  ┌───┐
    │   ├──┤   │
    │ P │  │ T │
    │   ├──┤   │
    └───┘  └───┘
```
- Favor spread weapons (Forker shotgun)
- Quick engagement, quick disengagement
- Reward reflexes over positioning

#### Mixed Sightlines (Ideal)
```
    Long range
    ════════════════════
    ┌────────┐
    │ Cover  │  Med range
    └────────┘  ─────────────
                ┌────────┐
                │ Cover  │
                └────────┘
                    Close range
                    ────────
```

### Cover Design

#### Full Cover
- Completely blocks sightlines
- Pillars, walls, large crates
- Enables "ring-around-the-rosie" combat

#### Partial Cover (Half-Height)
- Protects body, exposes head
- Creates headshot opportunities
- Risk/reward positioning

#### Soft Cover
- Conceals but doesn't protect
- Foliage, glass, shadows
- Creates uncertainty

### Cover Placement Rules

```
BAD: Long hallway, no cover
[═══════════════════════════════════]
     ↑ Whoever sees first wins

GOOD: Long sightline with cover options
[══════╦═══════╦═══════╦═══════════]
       ║       ║       ║
    Cover   Cover   Cover
     ↑ Multiple engagement points
```

| Principle | Application |
|-----------|-------------|
| Break up long sightlines | Add pillars/walls every 15-20 meters |
| Cover near power positions | Don't punish skillful play |
| Asymmetric cover | One side exposed, one protected |
| Destructible cover | Adds dynamic element (optional) |

---

## Part 3: Verticality

### Why Verticality Matters

> "Verticality's importance in multiplayer design cannot be overstated. It increases player choices and 'gameplay per square meter.'"
> — [On Game Design](https://www.ongamedesign.net/designing-fps-multiplayer-maps-part-1/)

A flat 400x400m map can be compressed to 200x200m with equivalent gameplay by adding 2-3 vertical levels.

### Height Advantage

```
HIGH GROUND
┌─────────────────┐
│   ⚫ Sniper     │  ← Better sightlines
│                 │  ← Harder to hit (head only visible)
└─────────────────┘  ← Escape routes below

LOW GROUND
┌─────────────────┐
│   ○ Target      │  ← Full body exposed
│                 │  ← Must look up (awkward)
└─────────────────┘  ← Splash damage effective
```

### Vertical Layers for RustChain Arena

#### Recommended Height Increments
Based on Resistance: Fall of Man research:
- **3 meters** - One story, jumpable with skill
- **6 meters** - Two stories, requires stairs/lift
- **9+ meters** - Major landmark, strategic control point

#### Layer Design
```
LAYER 3 (9m) - Sniper perches, power weapon
┌─────────────────────────────────────┐
│          ╔═══╗                      │
│          ║PWR║ ← Hashcannon         │
└──────────╚═══╝──────────────────────┘
              │
              │ Jump pad / stairs
              ↓
LAYER 2 (6m) - Main combat floor
┌─────────────────────────────────────┐
│    ╔═╗                    ╔═╗       │
│    ║A║ ← Armor           ║H║ ← Health
└────╚═╝────────────────────╚═╝───────┘
              │
              │ Ramps / drops
              ↓
LAYER 1 (0m) - Ground level, connectors
┌─────────────────────────────────────┐
│          Tunnels, side routes       │
│          Quick but vulnerable       │
└─────────────────────────────────────┘
```

### Vertical Movement Options

| Method | Speed | Control | Risk |
|--------|-------|---------|------|
| Stairs | Slow | Full | Low |
| Ramps | Medium | Full | Low |
| Jump pads | Fast | Limited | Medium |
| Teleporters | Instant | None | High |
| Rocket jumps | Fast | Skill-based | Health cost |
| Grapple hooks | Variable | High | Exposure |

### RustChain-Specific Vertical Features

#### "Transaction Launcher" Jump Pads
```
CONCEPT:
- Themed as blockchain nodes
- Micro-RTC cost (0.0001) for guaranteed trajectory
- Free pads exist with slight randomness
- "Gas fee" increases with player count
```

#### "Block Height" Platforms
```
CONCEPT:
- Floating platforms at set "block heights"
- Higher platforms = better items
- Visible block number displayed
- Risk: falling resets your Style rank
```

---

## Part 4: Item Placement & Power Positions

### The Risk/Reward Principle

> "Placement of the rocket launcher, or any powerful weapon, is critical—ideally there should be either significant risk or significant difficulty in obtaining the weapon."
> — [What Makes a Good Multiplayer Level](https://fat-studios.medium.com/what-makes-a-good-multiplayer-level-d604de3385dd)

### Item Tiers

#### Tier 1: Spawn Weapons
- Available immediately
- Blaster, basic machinegun
- No risk to obtain

#### Tier 2: Standard Pickups
- Scattered throughout map
- Shotgun (Forker), Electro (Validator)
- Low-medium risk positions

#### Tier 3: Power Weapons
- Central or exposed locations
- Devastator (Hashcannon), Vortex (Double-Spend)
- High risk, high reward

#### Tier 4: Super Items
- Single spawn, long respawn timer
- Mega Health, Quad Damage equivalent
- Maximum risk positioning

### Power Position Design

A power position offers advantages but must have counterplay:

```
GOOD POWER POSITION:
┌──────────────────────────────────┐
│                                  │
│     ┌────┐                       │
│     │ 🎯 │ ← High ground         │
│     │    │ ← Has cover           │
│     └────┘ ← But exposed flank   │
│        ↖                         │
│          ↖ ← Sniper sightline    │
│            ↖                     │
│              ↖                   │
│        [Approach route visible]  │
└──────────────────────────────────┘

Advantages:
✓ Height advantage
✓ Cover from front
✓ View of approaches

Counterplay:
✗ Exposed to side/rear
✗ Limited escape routes
✗ Vulnerable to splash damage
```

### Item Timing & Map Control

Classic arena shooters use item respawn timers to create rhythm:

| Item Type | Respawn Time | Strategic Role |
|-----------|--------------|----------------|
| Small armor | 15-20 sec | Route maintenance |
| Mega health | 25-35 sec | Primary timing |
| Power weapon | 30-45 sec | Map control point |
| Quad damage | 60-120 sec | Match-defining |

### RustChain Item Concepts

#### "Mining Nodes" (Health/Armor)
```
VISUAL: Floating crystal clusters
MECHANIC: Standing near them "mines" health
TWIST: Multiple players split the yield
RTC: +0.0001 per health point mined
```

#### "Genesis Block" (Super Item)
```
VISUAL: Golden floating cube
MECHANIC: First pickup of match = 3x RTC bonus
RESPAWN: Only once per match
LOCATION: Map center, maximum exposure
```

---

## Part 5: Chokepoints

### What is a Chokepoint?

A chokepoint narrows map flow through a single viewable entrance, concentrating combat into focused battle zones.

> "Narrow the flow of your map through architecture down to a single (or double) viewable entrance."
> — [World of Level Design](https://www.worldofleveldesign.com/categories/csgo-tutorials/csgo-principles-choke-point-level-design.php)

### The 6 Principles of Chokepoint Design

#### 1. Enhance Gameplay
Chokepoints create predictable combat zones:
```
WIDE AREA          CHOKEPOINT         WIDE AREA
═══════════╗      ╔═══════╗      ╔═══════════
           ║      ║       ║      ║
           ╚══════╝       ╚══════╝
                   ↑
            Battle zone
```

#### 2. Strategic Placement
Position between spawn and objective:
```
[SPAWN] ──→ [CHOKEPOINT] ──→ [OBJECTIVE]
```

#### 3. Synchronized Timing
Both teams should reach the chokepoint simultaneously. Measure with knife-only runs:
- If Team A arrives 5+ seconds early: Adjust spawns
- If timing is close: Good design

#### 4. Limited Entry Options
Restrict to 1-2 entrances viewable from one defensive position:
```
GOOD:                    BAD:
    ┌─┐                  ┌─┐ ┌─┐ ┌─┐
    │ │ ← One entrance   │ │ │ │ │ │ ← Too many
    └─┘                  └─┘ └─┘ └─┘
```

#### 5. Varied Combat Styles
Support multiple engagement ranges:
```
┌────────────────────────────────────┐
│  LONG RANGE                        │
│  ═══════════════════════════       │
│                                    │
│  MEDIUM RANGE     ┌────┐           │
│  ════════════════ │COVR│           │
│                   └────┘           │
│  CLOSE QUARTERS                    │
│  ══════════                        │
└────────────────────────────────────┘
```

#### 6. Dynamic Chokepoints
For asymmetric modes, chokepoints shift based on defensive strategy.

### RustChain Chokepoint: "The Mempool"

```
CONCEPT: Central chokepoint themed as transaction mempool

VISUAL:
- Glowing floor showing "pending transactions"
- Holographic displays of recent kills
- Warning lights when contested

MECHANIC:
- Staying in zone builds "confirmation time"
- First to 3 seconds "confirms" and gets RTC bonus
- Death in zone = "transaction reverted"

LAYOUT:
         ┌───────────────┐
         │               │
    ═════╡   MEMPOOL     ╞═════
         │    ZONE       │
    ═════╡               ╞═════
         │               │
         └───────────────┘
```

---

## Part 6: Spawn System Design

### The Problem with Bad Spawns

Nothing frustrates players more than spawn-death loops. Good spawn systems balance:
- **Safety** - Don't spawn into enemy fire
- **Fairness** - Don't spawn behind enemies
- **Flow** - Spawn players back into the action

### Spawn Point Scoring System

```python
for each spawn_point:
    score = BASE_SCORE (100)

    # Distance from enemies (closer = worse)
    nearest_enemy = min(distance_to_all_enemies)
    score -= 50 * (1 / nearest_enemy)

    # Line of sight check (in sightline = very bad)
    if enemy_has_line_of_sight(spawn_point):
        score -= 100

    # Recent usage penalty
    if recently_used(spawn_point, last_5_seconds):
        score -= 30

    # Recent death location (don't spawn at death point)
    distance_from_death = distance_to(player.last_death)
    if distance_from_death < 500:
        score -= 40

    # Hot zone penalty (active combat area)
    combat_intensity = get_heat_map(spawn_point)
    score -= combat_intensity * 20

    return score

# Select spawn with highest score
```

### Spawn Placement Rules

| Rule | Implementation |
|------|----------------|
| Minimum distance | Spawns at least 1000 units from nearest enemy |
| No direct sightlines | Use raycasts to verify |
| Multiple spawn clusters | 3-4 spawn zones per map |
| Zone rotation | Prefer spawns far from recent spawns |
| Momentary protection | Optional: 1-2 second spawn shield |

### RustChain Spawn Concept: "Block Confirmation"

```
VISUAL:
- Spawn point shows "Confirming..." animation
- Player materializes over 0.5 seconds
- Cannot move but also invulnerable during confirmation

MECHANIC:
- Spawning player chooses from 2-3 valid locations
- Brief overview camera before spawn
- "0-confirmation spawn" = instant but vulnerable
- "3-confirmation spawn" = 3 second delay but protected
```

---

## Part 7: Map Balance

### Symmetrical vs Asymmetrical

#### Symmetrical (Mirror/Rotational)
```
        ║
   A    ║    A'
  ┌─┐   ║   ┌─┐
  │ │   ║   │ │
  └─┘   ║   └─┘
        ║
═══════════════════
        ║
  ┌─┐   ║   ┌─┐
  │ │   ║   │ │
  └─┘   ║   └─┘
   B    ║    B'
        ║

Pros: Guaranteed equal chances
Cons: Can feel repetitive, less memorable
Best for: Competitive ranked modes
```

#### Asymmetrical Balance
```
SIDE A:                SIDE B:
- More cover           - Higher ground
- Longer routes        - Shorter routes
- Defensive advantage  - Offensive advantage

Equal opportunity, different playstyles
```

### Testing for Balance

1. **Win Rate Tracking**
   - Target: 48-52% per side
   - Iterate until balanced

2. **Heat Maps**
   - Track death locations
   - Identify problem areas

3. **First Blood Statistics**
   - Should be roughly 50/50
   - If skewed, adjust spawn positions or routes

4. **Item Control Rates**
   - Power items should be contested
   - If one side dominates item control, reposition

### Common Balance Problems

| Problem | Symptom | Solution |
|---------|---------|----------|
| Spawn advantage | One team wins first fight 70%+ | Adjust spawn locations |
| Sniper dominance | Long-range weapons overpowered | Add more cover, alternative routes |
| Camping spots | Players don't move | Add more entry points, time-limited rewards |
| Dead zones | Areas never used | Add items, better connections |
| Power position lock | One spot controls map | Add counterplay angles |

---

## Part 8: Psychology & Flow State

### Achieving Player Flow

Flow state (Csikszentmihalyi) occurs when skill and challenge are balanced:

```
ANXIETY (Challenge >> Skill)
        ↑
        │
        │      ╔═══════════╗
        │      ║   FLOW    ║
        │      ║   ZONE    ║
        │      ╚═══════════╝
        │
BOREDOM (Skill >> Challenge)
        └──────────────────→
              Player Skill
```

### Flow Elements in Level Design

| Flow Factor | Level Design Application |
|-------------|-------------------------|
| Clear goals | Visible objectives, item locations |
| Immediate feedback | Kill confirms, damage indicators |
| Challenge-skill balance | Multiple difficulty routes |
| Sense of control | Predictable physics, clear rules |
| Loss of self-consciousness | Immersive environment |
| Time distortion | Engaging combat rhythm |

### Engagement Design

#### Feedback Timing
Research shows feedback 200-400ms after action creates strongest associations:
- Kill confirmation: Instant sound + visual
- Damage dealt: Immediate hitmarker
- Style rank change: Within 0.5 seconds

#### Rhythm Creation
Good maps create natural combat rhythm:
```
ENGAGE → RETREAT → RESUPPLY → REPOSITION → ENGAGE
   ↑                                          │
   └──────────────────────────────────────────┘
         Should take 15-30 seconds
```

### Player Behavior Patterns

| Behavior | Design Response |
|----------|-----------------|
| Path of least resistance | Make interesting routes attractive |
| Risk aversion | Require some risk for best rewards |
| Repetition seeking | Vary item spawns slightly |
| Power fantasy | Provide domination opportunities |
| Fairness sensitivity | Ensure counterplay exists |

---

## Part 9: RustChain Arena Map Recommendations

### Arena Style: "The Genesis Block"

Central arena for deathmatch and 51% Attack mode.

```
                    ┌─────────────────┐
                    │   UPPER RING    │ (Height: 6m)
                    │  Sniper lanes   │
           ┌────────┴────────┬────────┴────────┐
           │                 │                 │
     ┌─────┤    WEST WING    │   EAST WING     ├─────┐
     │     │                 │                 │     │
     │     └────────┬────────┴────────┬────────┘     │
     │              │                 │              │
     │         ┌────┴────┐       ┌────┴────┐         │
     │         │  LOWER  │       │  LOWER  │         │
     │         │  WEST   │       │  EAST   │         │
     │         └────┬────┘       └────┬────┘         │
     │              │                 │              │
     │              │   ╔═════════╗   │              │
     │              │   ║ GENESIS ║   │              │
     │              └───║  BLOCK  ║───┘              │
     │                  ║(CONTROL)║                  │
     │                  ╚═════════╝                  │
     │                       │                       │
     │              ┌────────┴────────┐              │
     │              │   BASEMENT      │ (Height: -3m)
     │              │   Fast routes   │
     └──────────────┴─────────────────┴──────────────┘

KEY LOCATIONS:
★ Genesis Block - Central control point, power items
◆ Upper Ring - Sniper positions with risk
● Wings - Mid-tier items, multiple routes
○ Basement - Fast traversal, vulnerable
```

### Item Placement

```
TIER 4 (Super Item):
- Genesis Block center: Quad Damage equivalent
- Respawn: 90 seconds

TIER 3 (Power Weapons):
- Upper Ring North: Hashcannon (exposed platform)
- Upper Ring South: Double-Spend Rifle
- Both require exposure to claim

TIER 2 (Standard Weapons):
- West Wing: The Forker (shotgun)
- East Wing: The Validator (electro)
- Each wing has 2 entrances

TIER 1 (Pickups):
- Scattered health/armor throughout
- Mining nodes in basement
```

### Sightline Map

```
═══════ Long sightlines (sniper viable)
─────── Medium sightlines
....... Short sightlines (close quarters)

       ═══════════════════════════════
              │              │
       ───────┤              ├───────
              │    ......    │
       ───────┤    . CП .    ├───────
              │    ......    │
       ───────┤              ├───────
              │              │
       ═══════════════════════════════

CP = Control Point (Genesis Block)
Mix of all sightline types
```

---

## Part 10: Implementation Checklist

### Pre-Production
- [ ] Define map purpose (DM, TDM, 51% Attack, etc.)
- [ ] Sketch bubble diagram of major areas
- [ ] Plan flow pattern (figure-8 recommended)
- [ ] Identify 2-3 focal points
- [ ] Determine symmetry approach

### Blockout Phase
- [ ] Create basic geometry for all areas
- [ ] Ensure 3+ routes between major zones
- [ ] Add vertical layers (3m, 6m increments)
- [ ] Place placeholder items
- [ ] Test basic bot navigation

### Gameplay Phase
- [ ] Verify sightline balance
- [ ] Test spawn points (no spawn-deaths)
- [ ] Measure timing between key points
- [ ] Verify cover placement
- [ ] Check chokepoint timing

### Balance Phase
- [ ] Track win rates per team/side
- [ ] Identify dead zones (unused areas)
- [ ] Tune item placement
- [ ] Adjust power position counterplay
- [ ] Test with varying player counts

### Polish Phase
- [ ] Add RustChain theming
- [ ] Implement blockchain visual elements
- [ ] Add environmental storytelling
- [ ] Optimize performance
- [ ] Final bot navigation pass

---

## Sources

### Level Design Theory
- [The Level Design Book - Flow](https://book.leveldesignbook.com/process/layout/flow)
- [The Level Design Book - Typology](https://book.leveldesignbook.com/process/layout/typology)
- [The Level Design Book - Balance](https://book.leveldesignbook.com/process/combat/balance)
- [The Level Design Book - Verticality](https://book.leveldesignbook.com/process/layout/flow/verticality)

### FPS-Specific Design
- [Designing FPS Multiplayer Maps – On Game Design](https://www.ongamedesign.net/designing-fps-multiplayer-maps-part-1/)
- [Good FPS Map Design – CritPoints](https://critpoints.net/2018/02/18/good-fps-map-design/)
- [6 Principles of Chokepoint Level Design – World of Level Design](https://www.worldofleveldesign.com/categories/csgo-tutorials/csgo-principles-choke-point-level-design.php)

### Analysis & Research
- [What Makes a Good Multiplayer Level – Medium](https://fat-studios.medium.com/what-makes-a-good-multiplayer-level-d604de3385dd)
- [Multiplayer Level Design Techniques – Mind Studios](https://games.themindstudios.com/post/multiplayer-level-design-techniques/)
- [Analyzing Level Layouts in Competitive FPS – Game Developer](https://www.gamedeveloper.com/design/analyzing-level-layouts-to-improve-level-design-in-competitive-fps)
- [Secrets of the Sages: Level Design – Game Developer](https://www.gamedeveloper.com/design/secrets-of-the-sages-level-design)

### Psychology & Flow
- [Cognitive Flow: The Psychology of Great Game Design](https://www.gamedeveloper.com/design/cognitive-flow-the-psychology-of-great-game-design)
- [Flow and Immersion in First-Person Shooters](https://www.diva-portal.org/smash/get/diva2:835953/FULLTEXT01.pdf)
- [Design Patterns and Analysis of Player Behavior in FPS](https://users.soe.ucsc.edu/~ejw/dissertations/Ken-Hullett-dissertation.pdf)

### Classic Arena Shooter Analysis
- [Unreal Wiki - Recurring Maps](https://unreal.fandom.com/wiki/Recurring_maps)

---

*Document generated for RustChain Arena SDK v1.2.0*
