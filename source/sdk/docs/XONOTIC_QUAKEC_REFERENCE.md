# Xonotic QuakeC Reference Guide

Official documentation compiled from the Xonotic Wiki and Doxygen sources.

## Table of Contents
1. [QuakeC Language Basics](#quakec-language-basics)
2. [Code Organization](#code-organization)
3. [Mutator System](#mutator-system)
4. [Hook Reference](#hook-reference)
5. [Weapon Development](#weapon-development)
6. [Model Formats](#model-formats)
7. [Effects & Visuals](#effects--visuals)
8. [Gametype Development](#gametype-development)

---

## QuakeC Language Basics

QuakeC is a simplified C dialect used by the Quake engine. Xonotic uses the GMQCC compiler dialect.

### Data Types

| Type | Description |
|------|-------------|
| `float` | Numbers (integers and decimals) |
| `vector` | 3D coordinates (three floats) |
| `string` | Immutable text references |
| `entity` | Reference to game objects |

### Vectors

Vectors consist of three floats accessible via:
```c
// Underscore notation
v_x, v_y, v_z

// Dot notation
v.x, v.y, v.z

// Vector literals
vector pos = '100 200 50';
```

### Strings

Strings are immutable. Use these functions to manipulate:
```c
strcat(str1, str2)           // Concatenate
substring(str, start, len)   // Extract portion
strreplace(find, replace, str) // Replace text
strlen(str)                  // Get length
```

### Entity Fields

Extend entities with custom fields:
```c
// Declare field (in header)
.float my_field;
.entity my_target;
.string my_name;

// Use on entities
player.my_field = 100;
player.my_target = other_ent;
```

### Variable Scope

```c
// Global - visible from declaration onward
float global_var;

// Local - visible only in function block
void my_function() {
    float local_var;
}

// Use 'var' to disambiguate from function declarations
var float my_var;
```

### Common Pitfalls

1. **Complex operators unreliable**: `+=` and `++` may fail in complex expressions
2. **No pointers**: QuakeC has no pointer type
3. **Array performance**: Arrays are slow, avoid heavy use
4. **Function + array mixing**: Don't mix function calls with array access in one statement

---

## Code Organization

### Compilation Targets

| Target | Output | Preprocessor | Purpose |
|--------|--------|--------------|---------|
| SVQC | progs.dat | `#ifdef SVQC` | Server code |
| CSQC | csprogs.dat | `#ifdef CSQC` | Client code |
| MENUQC | menu.dat | `#ifdef MENUQC` | Menu code |
| GAMEQC | Both | `#ifdef GAMEQC` | Shared client+server |

### CVar Prefixes

| Prefix | Context | Use With |
|--------|---------|----------|
| `g_*` | Server/game | `#ifdef SVQC` |
| `sv_*` | Server | `#ifdef SVQC` |
| `cl_*` | Client | `#ifdef CSQC` |
| `hud_*` | HUD | `#ifdef CSQC` |

### Directory Structure

```
qcsrc/
├── dpdefs/          # Engine declarations
├── lib/             # Reusable libraries
├── common/          # Shared code
│   ├── mutators/    # Mutator system
│   ├── weapons/     # Weapon definitions
│   ├── items/       # Item definitions
│   └── effects/     # Visual effects
├── server/          # Server-only code
├── client/          # Client-only code
├── menu/            # Menu code
└── tools/           # Build scripts
```

### File Prefixes

| Prefix | Compiled Into |
|--------|---------------|
| `sv_` | Server only (progs.dat) |
| `cl_` | Client only (csprogs.dat) |
| (none) | Both if in common/ |

---

## Mutator System

### Creating a Mutator

**Step 1: Create mutator directory**
```
qcsrc/common/mutators/mutator/my_mutator/
├── sv_my_mutator.qh   # Server header
└── sv_my_mutator.qc   # Server code
```

**Step 2: Register the mutator**
```c
// sv_my_mutator.qc
#include "sv_my_mutator.qh"

#ifdef SVQC

REGISTER_MUTATOR(my_mutator, cvar("g_my_mutator"));

#endif
```

**Step 3: Add hooks**
```c
MUTATOR_HOOKFUNCTION(my_mutator, PlayerSpawn)
{
    entity player = M_ARGV(0, entity);
    PrintToChatAll(strcat(player.netname, " spawned!"));
}
```

**Step 4: Update build files**
```bash
./tools/genmod.sh
```

**Step 5: Add config**
```
// In mutators.cfg
set g_my_mutator 0 "Enable my mutator"
```

### Hook Variable Access

Use `M_ARGV(index, type)` to access hook variables:
```c
MUTATOR_HOOKFUNCTION(my_mutator, Damage_Calculate)
{
    entity inflictor = M_ARGV(0, entity);
    entity attacker = M_ARGV(1, entity);
    entity target = M_ARGV(2, entity);
    float deathtype = M_ARGV(3, float);
    float damage = M_ARGV(4, float);

    // Modify damage
    damage *= 0.5;
    M_ARGV(4, float) = damage;

    return false;  // Allow other hooks to run
}
```

---

## Hook Reference

Hooks are defined in `qcsrc/server/mutators/events.qh`

### Player Hooks

| Hook | Arguments | Description |
|------|-----------|-------------|
| `PlayerSpawn` | 0: player, 1: spawn_spot | Player spawned |
| `PlayerDies` | 0: inflictor, 1: attacker, 2: target, 3: deathtype, 4: damage | Player died |
| `PlayerPreThink` | 0: player | Every frame before physics |
| `PlayerPostThink` | 0: player | Every frame after physics |
| `ClientConnect` | 0: player | Player connected |
| `ClientDisconnect` | 0: player | Player disconnected |
| `PlayerRegen` | 0: player | Health/armor regeneration |
| `PlayerPhysics` | 0: player | Modify movement |
| `PlayerJump` | 0: player | Player jumped |
| `PlayerUseKey` | 0: player | Use key pressed |

### Combat Hooks

| Hook | Arguments | Description |
|------|-----------|-------------|
| `Damage_Calculate` | 0: inflictor, 1: attacker, 2: target, 3: deathtype, 4: damage, 5: mirrordamage, 6: force | Modify damage |
| `PlayerDamaged` | 0: attacker, 1: target, 2: deathtype, 3: damage | After damage applied |
| `GiveFragsForKill` | 0: attacker, 1: target, 2: f | Modify frag count |
| `FragCenterMessage` | 0: attacker, 1: target, 2: deathtype | Kill notification |

### Item Hooks

| Hook | Arguments | Description |
|------|-----------|-------------|
| `ItemTouch` | 0: item, 1: toucher | Item pickup attempt |
| `FilterItem` | 0: item | Block item spawn |
| `Item_Spawn` | 0: item | Item spawning |

### Weapon Hooks

| Hook | Arguments | Description |
|------|-----------|-------------|
| `W_DecreaseAmmo` | 0: actor, 1: wep, 2: ammo_use | Ammo consumption |
| `W_Reload` | 0: actor, 1: wep | Weapon reload |
| `ForbidDropCurrentWeapon` | 0: player | Block weapon drop |
| `ForbidThrowCurrentWeapon` | 0: player | Block weapon throw |

### Game Flow Hooks

| Hook | Arguments | Description |
|------|-----------|-------------|
| `MatchCountdown` | - | Match starting |
| `ReadyRestart_Deny` | - | Block ready restart |
| `reset_map_global` | - | Map reset |
| `reset_map_players` | - | Reset all players |

---

## Weapon Development

### Weapon Class Methods

**Initialization:**
```c
METHOD(MyWeapon, wr_init, void(Weapon this)) {
    // Precache models and sounds
}

METHOD(MyWeapon, wr_setup, void(Weapon this, entity actor)) {
    // Setup weapon data
}
```

**Combat:**
```c
METHOD(MyWeapon, wr_think, void(Weapon this, entity actor, int fire)) {
    // Per-frame logic, handle fire buttons
    if (fire & 1) {
        // Primary fire
    }
    if (fire & 2) {
        // Secondary fire
    }
}

METHOD(MyWeapon, wr_checkammo1, bool(Weapon this, entity actor, bool use)) {
    // Check primary ammo
    return GetResource(actor, RES_ROCKETS) >= WEP_CVAR(devastator, ammo);
}
```

**Events:**
```c
METHOD(MyWeapon, wr_pickup, void(Weapon this, entity actor)) {
    // Weapon picked up
}

METHOD(MyWeapon, wr_drop, void(Weapon this, entity actor)) {
    // Weapon dropped
}
```

### Key Weapon Properties

| Property | Type | Description |
|----------|------|-------------|
| `netname` | string | Reference name |
| `m_name` | string | Display name |
| `impulse` | float | Weapon slot number |
| `ammo_type` | Resource | Ammo resource type |
| `mdl` | string | Model filename |
| `w_crosshair` | string | Crosshair image |
| `m_muzzleeffect` | Effect | Muzzle flash effect |

### Projectile Functions

```c
// Think function - called every frame
void W_MyProjectile_Think(entity this) {
    // Update projectile
    this.nextthink = time + 0.1;
}

// Touch function - called on collision
void W_MyProjectile_Touch(entity this, entity toucher) {
    if (toucher == this.realowner) return;  // Don't hit self

    // Explode
    RadiusDamage(this, this.realowner, damage, edgedamage, radius,
                 NULL, NULL, push, deathtype, DMG_NOWEP, toucher);
    delete(this);
}

// Explode function
void W_MyProjectile_Explode(entity this) {
    Send_Effect(EFFECT_ROCKET_EXPLODE, this.origin, '0 0 0', 1);
    RadiusDamage(...);
    delete(this);
}
```

---

## Model Formats

### Supported Formats

| Format | Animation | Features |
|--------|-----------|----------|
| **IQM** | Skeletal | Multiple meshes, smooth skinning, smallest files |
| MDL | Vertex | Multiple skins, Quake 1 format |
| MD2 | Vertex | Better animation quality |
| MD3 | Vertex | Multiple mesh textures |
| ZYM | Skeletal | Smooth skinning |
| DPM | Skeletal | DarkPlaces native |
| PSK | Skeletal | Unreal format |
| OBJ | None | Static models only |

### Animation Configuration

Create `.framegroups` file alongside model:
```
# firstframe numframes framerate loopflag
0 30 10 1       # idle (looping)
30 20 20 1      # walk (looping)
50 15 25 1      # run (looping)
65 10 20 0      # jump (not looping)
75 20 15 0      # death (not looping)
```

### IQM Export (Recommended)

```bash
# Convert OBJ to IQM
./iqm output.iqm input.obj

# With animations from multiple frames
./iqm output.iqm frame_*.obj
```

---

## Effects & Visuals

### Spawning Effects

```c
// Basic effect
Send_Effect(EFFECT_ROCKET_EXPLODE, position, velocity, count);

// Using effect number
float eff = particleeffectnum("my_effect");
pointparticles(eff, position, velocity, count);
```

### Common Effects

| Effect | Description |
|--------|-------------|
| `EFFECT_ROCKET_EXPLODE` | Rocket explosion |
| `EFFECT_GRENADE_EXPLODE` | Grenade explosion |
| `EFFECT_ELECTRO_COMBO` | Electro combo |
| `EFFECT_TR_ROCKET` | Rocket trail |
| `EFFECT_TR_NEXUIZPLASMA` | Plasma trail |
| `EFFECT_SPAWN_NEUTRAL` | Player spawn |

### Custom Effects

Define in `effectinfo.txt`:
```
effect my_explosion
count 50
type smoke
color 0xFF6600 0xFF0000
size 10 30
sizeincrease 50
alpha 256 256 300
velocityjitter 200 200 200
gravity 0.5
```

---

## Gametype Development

### Required Files

1. **Server implementation** (`sv_mygametype.qc`)
2. **Client implementation** (`cl_mygametype.qc`)
3. **Map configuration** (`.mapinfo` with gametype)
4. **Configuration files** (hooks, CVars)

### Map Configuration

In `.mapinfo` file:
```
gametype mgt  // Your gametype shortcut
```

### Registration

```c
// Register gametype
REGISTER_GAMETYPE(mygametype, MGT, "My Gametype", "mgt", GAMETYPE_FLAG_TEAMPLAY);
```

### Reference Implementations

- **GunGame**: https://github.com/Lyberta/GunGame
- **Survival**: Mario's Survival gametype
- **Official gametypes**: `qcsrc/common/gamemodes/`

---

## Useful Functions

### Entity Management

```c
entity new_ent = new(classname);     // Create entity
delete(ent);                         // Remove entity
setorigin(ent, position);            // Set position
setmodel(ent, "models/thing.iqm");   // Set model
setsize(ent, mins, maxs);            // Set bounding box
```

### Resources

```c
GetResource(ent, RES_HEALTH)         // Get health
SetResource(ent, RES_HEALTH, 100)    // Set health
GiveResource(ent, RES_ARMOR, 50)     // Add armor

// Resource types: RES_HEALTH, RES_ARMOR, RES_SHELLS,
//                 RES_BULLETS, RES_ROCKETS, RES_CELLS, RES_FUEL
```

### Math

```c
makevectors(angles);    // Sets v_forward, v_right, v_up
normalize(vector);      // Unit vector
vlen(vector);           // Vector length
random();               // 0.0 to 1.0
randomvec();            // Random unit vector
```

### Tracing

```c
traceline(start, end, MOVE_NORMAL, ignore_ent);
// Results:
//   trace_endpos - Hit position
//   trace_fraction - 0-1 how far trace went
//   trace_ent - Entity hit
//   trace_plane_normal - Surface normal
```

### Communication

```c
PrintToChatAll("Message");                    // To all players
PrintToChat(player, "Private message");       // To one player
centerprint(player, "Center screen");         // Center message
stuffcmd(player, "play sound/file.ogg\n");    // Run console command
```

---

## Sources

- [Introduction to QuakeC](https://gitlab.com/xonotic/xonotic/-/wikis/Introduction-to-QuakeC)
- [Writing Your First Mutator](https://github.com/xonotic/xonotic/wiki/writing-your-first-mutator)
- [Programming QuakeC in Xonotic](https://gitlab.com/xonotic/xonotic/-/wikis/Programming-QuakeC-stuff-in-Xonotic)
- [Modeling Guide](https://github.com/xonotic/xonotic/wiki/Modeling)
- [Xonotic Doxygen Reference](https://xonotic.org/doxygen/qcsrc/)
- [Weapon Class Reference](https://xonotic.org/doxygen/qcsrc/classWeapon.html)
