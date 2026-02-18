# RustChain Xonotic Mapping SDK - Texture Guide

## Custom Texture Workflow

This guide documents how to add custom textures (like RustChain branding) to Xonotic maps.

### Directory Structure

```
/home/scott/Games/Xonotic/data/
├── textures/
│   └── rustchain/           # Custom texture folder
│       ├── sophia_terminal.tga
│       ├── sophia_poster.tga
│       ├── rustchain_logo_new.tga
│       ├── circuit_panel.tga
│       └── ...
├── scripts/
│   └── rustchain.shader     # Optional shader definitions
└── zzz_rustchain_textures.pk3   # Packaged textures (zzz_ prefix loads last)
```

### Step 1: Prepare Textures

**Format Requirements:**
- TGA format (24-bit RGB or 32-bit RGBA for transparency)
- Power-of-two dimensions recommended (256x256, 512x512, 1024x512, etc.)
- Non-power-of-two works but may have performance impact

**Convert PNG to TGA:**
```bash
# Using ImageMagick
convert input.png output.tga

# For transparency support
convert input.png -alpha on output.tga
```

### Step 2: Place Textures

Put TGA files in: `/home/scott/Games/Xonotic/data/textures/rustchain/`

### Step 3: Reference in Map

**IMPORTANT: Texture path format in .map files:**
```
# CORRECT - no 'textures/' prefix (engine adds it automatically)
rustchain/sophia_terminal

# WRONG - doubled path causes "could not load texture"
textures/rustchain/sophia_terminal
```

**In Python map generator:**
```python
# Define texture paths WITHOUT 'textures/' prefix
RC_TERMINAL = "rustchain/sophia_terminal"
RC_POSTER = "rustchain/sophia_poster"
RC_LOGO = "rustchain/rustchain_logo_new"
```

### Step 4: Package as PK3

**Create pk3 (zip with .pk3 extension):**
```bash
cd /home/scott/Games/Xonotic/data
zip -r zzz_rustchain_textures.pk3 textures/rustchain/
```

**Note:** The `zzz_` prefix ensures the pk3 loads after core game files.

### Step 5: Texture Scaling in Brushes

**Default texture parameters:**
```
TEXTURE_NAME offset_x offset_y rotation scale_x scale_y flags contents value
rustchain/sophia_terminal 0 0 0 0.25 0.25 0 0 0
```

**Scale values:**
- `0.25 0.25` = texture repeats 4x (default, tiles the texture)
- `1.0 1.0` = texture at original size (1 texel = 1 unit)
- `0.5 0.5` = texture repeats 2x
- `2.0 2.0` = texture stretched 2x

**For a single non-tiled image on a surface:**
Calculate scale based on brush size and texture size:
```
scale = brush_size / texture_size
```

Example: 128-unit wide brush, 512-pixel texture
```
scale = 128 / 512 = 0.25
```

### Optional: Shader Definitions

Shaders add effects like glow, animation, transparency.

**File:** `/home/scott/Games/Xonotic/data/scripts/rustchain.shader`

**Basic lightmapped texture:**
```
rustchain/sophia_terminal
{
    qer_editorimage textures/rustchain/sophia_terminal.tga
    {
        map textures/rustchain/sophia_terminal.tga
        rgbGen identity
    }
    {
        map $lightmap
        blendfunc filter
        rgbGen identity
        tcGen lightmap
    }
}
```

**Self-illuminated (glowing) texture:**
```
rustchain/sophia_terminal
{
    qer_editorimage textures/rustchain/sophia_terminal.tga
    q3map_surfacelight 100
    {
        map textures/rustchain/sophia_terminal.tga
        rgbGen identity
    }
}
```

**Animated/scrolling texture:**
```
rustchain/data_stream
{
    {
        map textures/rustchain/data_stream.tga
        tcMod scroll 0 0.5   // Scroll vertically
        rgbGen identity
    }
}
```

### Troubleshooting

**Problem: Checkerboard pattern (missing texture)**
- Check console: `could not load texture "textures/textures/rustchain/..."`
- Fix: Remove `textures/` prefix from map file references

**Problem: Texture not found**
- Verify TGA exists in `textures/rustchain/` folder
- Verify pk3 contains the file: `unzip -l zzz_rustchain_textures.pk3`
- Restart Xonotic to reload pk3 files

**Problem: Texture appears stretched/tiled wrong**
- Adjust scale values in brush definition
- Use 1.0 scale for 1:1 mapping

### Example: Adding Screen to Map Generator

```python
# Texture definitions (no 'textures/' prefix!)
RC_TERMINAL = "rustchain/sophia_terminal"

# Create a screen brush on reactor
# brush_box(x1, y1, z1, x2, y2, z2, textures)
# textures = [top, bottom, north, south, east, west]
output.append(brush_box(
    -64, REACTOR_SIZE, HEIGHT - 128,    # min corner
    64, REACTOR_SIZE + 2, HEIGHT - 16,  # max corner
    [WALL, WALL, RC_TERMINAL, WALL, WALL, WALL]  # north face is screen
))
```

### Files Reference

| File | Purpose |
|------|---------|
| `generate_powercore.py` | Python map generator |
| `rustcore_v3.map` | Generated map source |
| `rustcore_v3.bsp` | Compiled map binary |
| `zzz_rustchain_textures.pk3` | Texture package |
| `rustchain.shader` | Shader definitions |

### Compilation Commands

```bash
# Generate map
python3 generate_powercore.py

# Compile (BSP → VIS → LIGHT)
Q3MAP2=/home/scott/Games/Xonotic/source/netradiant_1.5.0-20220628-linux-amd64/q3map2
$Q3MAP2 -game xonotic -fs_basepath /home/scott/Games/Xonotic -meta -bsp rustcore_v3.map
$Q3MAP2 -game xonotic -fs_basepath /home/scott/Games/Xonotic -vis -saveprt rustcore_v3.map
$Q3MAP2 -game xonotic -fs_basepath /home/scott/Games/Xonotic -light -fast -samples 2 rustcore_v3.map

# Copy to game
cp rustcore_v3.bsp /home/scott/Games/Xonotic/data/maps/

# Test
cd /home/scott/Games/Xonotic && ./xonotic-linux64-sdl +map rustcore_v3
```
