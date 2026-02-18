# Quake .map Brush Format Guide

## Discovery Summary

After extensive testing with q3map2 compiler, we discovered the correct brush plane format for generating valid Quake/Xonotic maps programmatically. The key insight is that **plane winding order matters critically** - incorrect winding results in "0 total world brushes" during compilation.

## The Problem

Hand-written axis-aligned box brushes often fail to compile:
```
// THIS FAILS - all 3 points have same Z coordinate (degenerate plane)
( -512 -512 0 ) ( -512 512 0 ) ( 512 -512 0 ) texture 0 0 0 0.25 0.25 0 0 0
```

## The Solution

Use the winding order pattern from NetRadiant-generated maps. Each plane needs 3 non-collinear points that define the plane with proper normal direction.

### Working Brush Box Function (Python)

```python
def brush_box(x1, y1, z1, x2, y2, z2, textures):
    """
    Generate a solid box brush from min (x1,y1,z1) to max (x2,y2,z2)
    textures = [top, bottom, north, south, east, west] or single texture string
    """
    if isinstance(textures, str):
        textures = [textures] * 6

    # Ensure proper min/max ordering
    if x1 > x2: x1, x2 = x2, x1
    if y1 > y2: y1, y2 = y2, y1
    if z1 > z2: z1, z2 = z2, z1

    lines = ["{"]

    # TOP face (z = z2) - normal points +Z
    lines.append(f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {textures[0]} 0 0 0 0.25 0.25 0 0 0")

    # BOTTOM face (z = z1) - normal points -Z
    lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {textures[1]} 0 0 0 0.25 0.25 0 0 0")

    # NORTH face (y = y2) - normal points +Y
    lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {textures[2]} 0 0 0 0.25 0.25 0 0 0")

    # SOUTH face (y = y1) - normal points -Y
    lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {textures[3]} 0 0 0 0.25 0.25 0 0 0")

    # EAST face (x = x2) - normal points +X
    lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {textures[4]} 0 0 0 0.25 0.25 0 0 0")

    # WEST face (x = x1) - normal points -X
    lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {textures[5]} 0 0 0 0.25 0.25 0 0 0")

    lines.append("}")
    return "\n".join(lines)
```

## Plane Format Explained

Each brush face is defined by a plane using 3 points:
```
( x1 y1 z1 ) ( x2 y2 z2 ) ( x3 y3 z3 ) texture xoff yoff rot xscale yscale flags unknown unknown
```

### Key Rules:
1. **Three points define the plane** - they must be non-collinear
2. **Winding order determines normal direction** - counter-clockwise when viewed from outside the brush
3. **Normal points INTO the solid** - the half-space "behind" the plane is solid
4. **All 6 faces must form a closed convex volume** - no gaps or overlaps

### Texture Parameters:
- `texture` - Path like `facility114x/floor-floor02` or `common/caulk`
- `xoff yoff` - Texture offset (usually 0 0)
- `rot` - Texture rotation in degrees (usually 0)
- `xscale yscale` - Texture scale (0.25 0.25 is common)
- `flags` - Surface flags (usually 0)
- Last two values - Content flags (usually 0 0)

## Map File Structure

```
{
"classname" "worldspawn"
"message" "Map Title"
"author" "Author Name"
"_lightmapscale" "0.125"
// Brush 1
{
( plane1 ) texture params
( plane2 ) texture params
( plane3 ) texture params
( plane4 ) texture params
( plane5 ) texture params
( plane6 ) texture params
}
// Brush 2
{
...
}
}
// Point entities outside worldspawn
{
"classname" "info_player_deathmatch"
"origin" "0 0 32"
"angle" "0"
}
{
"classname" "light"
"origin" "0 0 200"
"light" "500"
"_color" "1 1 1"
}
```

## Common Textures (Xonotic)

| Category | Texture Path | Use |
|----------|--------------|-----|
| Floor | `facility114x/floor-floor02` | Main floor surfaces |
| Ceiling | `facility114x/ceiling-ceiling01` | Ceiling surfaces |
| Wall | `facility114x/wall-corridor01` | Wall surfaces |
| Trim | `facility114x/trim-trim01` | Edge trim, catwalks |
| Caulk | `common/caulk` | Non-visible faces (optimization) |
| Base | `facility114x/base-base` | Reactor/pillar tops |

## Compilation Pipeline

```bash
Q3MAP2=/path/to/netradiant/q3map2
BASEPATH=/path/to/Xonotic
MAP=mapname.map

# Stage 1: BSP (converts brushes to BSP tree)
$Q3MAP2 -meta -fs_basepath $BASEPATH -fs_game data $MAP

# Stage 2: VIS (calculates visibility, requires no leaks)
$Q3MAP2 -vis -fs_basepath $BASEPATH -fs_game data $MAP

# Stage 3: LIGHT (calculates lighting)
$Q3MAP2 -light -fast -fs_basepath $BASEPATH -fs_game data $MAP

# Copy to game data folder
cp mapname.bsp $BASEPATH/data/maps/
```

## Debugging Tips

### "0 total world brushes"
- Plane winding order is wrong
- Three points are collinear (degenerate plane)
- Use the brush_box() function above

### "Entity leaked"
- Map isn't sealed - there's a gap in the walls
- Check that floor, ceiling, and all walls overlap properly
- Wall thickness should extend past floor/ceiling

### "Entity in solid"
- A point entity (spawn, weapon, light) is inside a brush
- Move the entity origin outside solid geometry

## MCP Integration Note

The Quake MCP server can assist with level development by:
- Providing texture listings
- Validating brush geometry
- Suggesting entity placements
- Checking for common errors

This format guide enables Claude to generate valid .map files programmatically, opening up procedural level generation possibilities.

## Files

- Generator script: `/home/scott/Games/Xonotic/mapping/maps/generate_powercore.py`
- Example map: `/home/scott/Games/Xonotic/mapping/maps/rustcore_v3.map`
- Compiled BSP: `/home/scott/Games/Xonotic/data/maps/rustcore_v3.bsp`

## Credits

Format discovered through analysis of NetRadiant-generated maps and iterative testing with q3map2 compiler. Special thanks to the Xonotic/DarkPlaces community for maintaining the toolchain.
