# Xonotic Map Building Guide

## SOLVED: The Correct Brush Plane Format (December 2024)

### The Problem
Wall brushes were being silently rejected during compilation. The issue was **incorrect plane definitions**.

### The Solution: Corner-Based Plane Definitions

Each brush must have 6 planes. The key is defining planes using **corner vertices**, not spread-out face points.

**Pattern:**
1. **Origin-corner planes** (X_min, Y_min, Z_min): Start from origin corner, extend along two edges
2. **Far-corner planes** (X_max, Y_max, Z_max): Start from far corner, extend along two edges

### Working Brush Template

For a brush from `(x1, y1, z1)` to `(x2, y2, z2)`:

```
{
( x1 y1 z1 ) ( x1 y2 z1 ) ( x1 y1 z2 ) texture 0 0 0 0.5 0.5 0 0 0
( x1 y1 z1 ) ( x2 y1 z1 ) ( x1 y2 z1 ) texture 0 0 0 0.5 0.5 0 0 0
( x1 y1 z1 ) ( x1 y1 z2 ) ( x2 y1 z1 ) texture 0 0 0 0.5 0.5 0 0 0
( x2 y2 z2 ) ( x2 y2 z1 ) ( x2 y1 z2 ) texture 0 0 0 0.5 0.5 0 0 0
( x2 y2 z2 ) ( x2 y1 z2 ) ( x1 y2 z2 ) texture 0 0 0 0.5 0.5 0 0 0
( x2 y2 z2 ) ( x1 y2 z2 ) ( x2 y2 z1 ) texture 0 0 0 0.5 0.5 0 0 0
}
```

### Example: Floor Brush (-512,-512,-64) to (512,512,0)

```
{
( -512 -512 -64 ) ( -512 512 -64 ) ( -512 -512 0 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( -512 -512 -64 ) ( 512 -512 -64 ) ( -512 512 -64 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( -512 -512 -64 ) ( -512 -512 0 ) ( 512 -512 -64 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( 512 512 0 ) ( 512 512 -64 ) ( 512 -512 0 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( 512 512 0 ) ( 512 -512 0 ) ( -512 512 0 ) exx/floor-panel01 0 0 0 0.5 0.5 0 0 0
( 512 512 0 ) ( -512 512 0 ) ( 512 512 -64 ) common/caulk 0 0 0 0.5 0.5 0 0 0
}
```

### Example: Wall Brush (-512,512,0) to (512,576,512)

```
{
( -512 512 0 ) ( -512 576 0 ) ( -512 512 512 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( -512 512 0 ) ( 512 512 0 ) ( -512 576 0 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( -512 512 0 ) ( -512 512 512 ) ( 512 512 0 ) exx/wall-crete01 0 0 0 0.5 0.5 0 0 0
( 512 576 512 ) ( 512 576 0 ) ( 512 512 512 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( 512 576 512 ) ( 512 512 512 ) ( -512 576 512 ) common/caulk 0 0 0 0.5 0.5 0 0 0
( 512 576 512 ) ( -512 576 512 ) ( 512 576 0 ) common/caulk 0 0 0 0.5 0.5 0 0 0
}
```

## Compilation Commands

### Full Compile (3 phases)
```bash
Q3MAP2=/home/scott/Games/Xonotic/source/netradiant_1.5.0-20220628-linux-amd64/q3map2
BASEPATH=/home/scott/Games/Xonotic
MAPFILE=/home/scott/Games/Xonotic/data/maps/mapname.map

# Phase 1: BSP
$Q3MAP2 -game xonotic -fs_basepath $BASEPATH -fs_game data -bsp $MAPFILE

# Phase 2: VIS (visibility optimization)
$Q3MAP2 -game xonotic -fs_basepath $BASEPATH -fs_game data -vis ${MAPFILE%.map}.bsp

# Phase 3: LIGHT
$Q3MAP2 -game xonotic -fs_basepath $BASEPATH -fs_game data -light -fast ${MAPFILE%.map}.bsp
```

### Verification
```bash
# Get BSP info
$Q3MAP2 -info mapname.bsp

# Expected output for 6-brush arena:
#   6 brushes
#   5 drawsurfaces (visible textured faces)
```

## Texture Names (Correct Format)

The shader names use hyphens, not directory slashes:

**Correct:**
- `exx/floor-panel01`
- `exx/wall-crete01`
- `common/caulk`

**Incorrect:**
- `exx/floor/floor_panel01`
- `exx/wall/wall_crete01`

Both may work, but the shader-defined names use hyphens.

## Entity Types

### Spawn Points
```
{
"classname" "info_player_deathmatch"
"origin" "0 0 32"
"angle" "90"
}
```

### Weapons
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

### Lights
```
{
"classname" "light"
"origin" "0 0 480"
"light" "1000"
"_color" "1 1 1"
}
```

## Genesis Block Arena

Working map: `/home/scott/Games/Xonotic/data/maps/genesis_block.map`

**Stats:**
- 6 brushes (floor, ceiling, 4 walls)
- 5 visible surfaces
- 4 spawn points
- 1 light
- Weapons and items

## Testing

```bash
# Launch game with map
cd /home/scott/Games/Xonotic && ./xonotic-linux64-sdl +developer 1 +map genesis_block
```

## Key Learnings

1. **Plane definitions matter** - Use corner-based vertices, not spread-out face points
2. **"0 meta surfaces" is normal** - Caulk textures are "stripped" not "meta"
3. **"Entity leaked" is NOT fatal** - Map can still play, just affects VIS optimization
4. **Multiple brushes work** - The issue was plane format, not brush count
5. **Check BSP info** - Use `q3map2 -info` to verify brush count

## NetRadiant Location
```
/home/scott/Games/Xonotic/source/netradiant_1.5.0-20220628-linux-amd64/netradiant
```
