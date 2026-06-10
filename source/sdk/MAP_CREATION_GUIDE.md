# Xonotic/Quake 3 Map Creation Guide

## Map File Format (.map)

Quake 3 / DarkPlaces map files use a specific text format:

### Basic Structure
```
// Comments start with //
{
"classname" "worldspawn"
"message" "Map Name"
// other key-value pairs...

// Brushes go inside worldspawn
{
// 6 planes define a convex brush
( x1 y1 z1 ) ( x2 y2 z2 ) ( x3 y3 z3 ) texture 0 0 0 scale_x scale_y 0 0 0
... 5 more planes ...
}
}
// Point entities follow
{
"classname" "info_player_deathmatch"
"origin" "x y z"
"angle" "degrees"
}
```

### Brush Plane Format
Each plane is defined by 3 points followed by texture info:
```
( x1 y1 z1 ) ( x2 y2 z2 ) ( x3 y3 z3 ) texture x_off y_off rot scale_x scale_y flags flags flags
```

Example floor brush (16 units thick, 1024x1024):
```
{
( -512 512 0 ) ( -512 -512 0 ) ( 512 -512 0 ) trak4x/floor/floor_tile3a 0 0 0 0.25 0.25 0 0 0
( 512 -512 -16 ) ( -512 -512 -16 ) ( -512 512 -16 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( 512 512 0 ) ( 512 -512 0 ) ( 512 -512 -16 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( -512 -512 0 ) ( -512 512 0 ) ( -512 512 -16 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( -512 512 0 ) ( 512 512 0 ) ( 512 512 -16 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( 512 -512 0 ) ( -512 -512 0 ) ( -512 -512 -16 ) common/caulk 0 0 0 0.5 0.5 0 0 0
}
```

## Critical Lessons Learned

### 1. File Creation Method Matters
**Problem**: Files created with Python's `Write` tool may have encoding issues that cause q3map2 to silently fail (0 meta surfaces).

**Solution**: Use bash `cat` with heredoc to create map files:
```bash
cat > mapname.map << 'EOF'
{
"classname" "worldspawn"
...
}
EOF
```

### 2. Line Endings
- q3map2 works with both LF (Unix) and CRLF (Windows) line endings
- Not the cause of parsing failures

### 3. Minimum Brush Requirements
- A single brush (just a floor) will NOT compile properly
- You need a complete sealed box (floor, ceiling, 4 walls) minimum
- "99999, 99999, 99999 to -99999, -99999, -99999" in output means NO brushes were parsed

### 4. Texture Names
Texture names do NOT include the `textures/` prefix in .map files:
- Correct: `trak4x/floor/floor_tile3a`
- Wrong: `textures/trak4x/floor/floor_tile3a`

### 5. "Entity leaked" Warning
This warning is NOT fatal. It means:
- The map isn't perfectly sealed for VIS optimization
- BSP compilation still succeeds
- Map is playable, just not optimally compiled

### 6. Q3map2 Compilation
```bash
/path/to/q3map2 -fs_basepath /path/to/Xonotic -fs_game data -meta mapname.map
```

Output to check:
- `Size: X Y Z` - Should show actual map bounds, NOT 99999
- `N total meta surfaces` - Should be > 0
- File size > 4KB indicates successful brush compilation

## Available Textures (from trak4x.pk3)

### Floors
- `trak4x/floor/floor_tile3a`

### Walls
- `trak4x/wall/wall_brick1`

### Base/Industrial
- `trak4x/base/base_rust1`
- `trak4x/base/base_concrete3`

### Special
- `common/caulk` - Non-rendered (use on hidden faces)

## Entity Reference

### Spawn Points
```
{
"classname" "info_player_deathmatch"
"origin" "x y z"
"angle" "degrees"  // 0=east, 90=north, 180=west, 270=south
}
```

### Weapons (Xonotic names)
- `weapon_devastator` (rocket launcher)
- `weapon_shotgun`
- `weapon_electro`
- `weapon_vortex` (sniper)
- `weapon_mortar`
- `weapon_machinegun`
- `weapon_crylink`
- `weapon_hagar`

### Items
- `item_health_mega`, `item_health_small`, `item_health_medium`
- `item_armor_big`, `item_armor_small`, `item_armor_medium`
- `ammo_rockets`, `ammo_shells`, `ammo_cells`, `ammo_bullets`

### Jump Pads
```
{
"classname" "trigger_push"
"origin" "x y z"
"mins" "-32 -32 0"
"maxs" "32 32 64"
"target" "jump_target_name"
}
{
"classname" "target_position"
"targetname" "jump_target_name"
"origin" "landing_x landing_y landing_z"
}
```

### Lights
```
{
"classname" "light"
"origin" "x y z"
"light" "intensity"  // 200-600 typical
"_color" "r g b"     // 0-1 range
}
```

## Mapinfo File
Required for Xonotic to list the map:
```
title Map Display Name
description Short description
author Your Name
cdtrack 5
has weapons
gametype dm
gametype tdm
gametype ffa
```
