# RustChain Xonotic DevKit

A comprehensive SDK for modding Xonotic/DarkPlaces engine games, developed during the RustChain PoA FPS project.

## Table of Contents
1. [SDK Installation](#sdk-installation)
2. [Project Structure](#project-structure)
3. [NetRadiant Map Editor](#netradiant-map-editor)
4. [IQM Model Pipeline](#iqm-model-pipeline)
5. [Texturing System](#texturing-system)
6. [Shader System](#shader-system)
7. [Audio & Sound](#audio--sound)
8. [QuakeC Development](#quakec-development)
9. [Mutator System](#mutator-system)
10. [Props & Entity Spawning](#props--entity-spawning)
11. [Particle Effects](#particle-effects)
12. [HUD & UI Customization](#hud--ui-customization)
13. [Bot AI](#bot-ai)
14. [Networking & Multiplayer](#networking--multiplayer)
15. [PK3 Packaging](#pk3-packaging)
16. [Testing & Debugging](#testing--debugging)
17. [RustChain Integration](#rustchain-integration)

---

## SDK Installation

### Required Tools

| Tool | Purpose | Install Command |
|------|---------|-----------------|
| **Xonotic** | Game engine & assets | Download from xonotic.org |
| **NetRadiant** | Map editor | `sudo apt install netradiant` |
| **Blender** | 3D modeling | `sudo apt install blender` |
| **GIMP** | Texture editing | `sudo apt install gimp` |
| **Audacity** | Sound editing | `sudo apt install audacity` |
| **GMQCC** | QuakeC compiler | Included in source |
| **Git** | Version control | `sudo apt install git` |

### Install NetRadiant (Map Editor)
```bash
# Ubuntu/Debian
sudo apt install netradiant

# Or build from source
git clone https://gitlab.com/xonotic/netradiant.git
cd netradiant
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(nproc)
sudo cmake --install build
```

### Install Xonotic Mapping Support (Gamepack)
```bash
# Download Xonotic gamepack for NetRadiant
mkdir -p ~/.netradiant/gamepacks
cd ~/.netradiant/gamepacks
git clone https://gitlab.com/xonotic/netradiant-xonoticpack.git Xonotic.game

# Or use the built-in gamepack manager
netradiant --install-gamepack Xonotic
```

### Full SDK One-Liner Install
```bash
sudo apt install netradiant blender gimp audacity git zip unzip imagemagick ffmpeg
```

---

## Project Structure

```
Xonotic/
├── data/                       # Game assets (pk3 files)
│   ├── xonotic-*-data.pk3     # Core game data
│   ├── xonotic-*-maps.pk3     # Official maps
│   └── zzz_my_mod.pk3         # Your mod (zzz = load last)
├── source/
│   ├── qcsrc/                 # QuakeC source code
│   │   ├── common/            # Shared code
│   │   │   ├── mutators/      # Mutator system
│   │   │   ├── weapons/       # Weapon definitions
│   │   │   ├── items/         # Item definitions
│   │   │   └── effects/       # Visual effects
│   │   ├── server/            # Server-side code
│   │   ├── client/            # Client-side code (CSQC)
│   │   └── menu/              # Menu code
│   ├── gmqcc/                 # QuakeC compiler
│   ├── darkplaces/            # Engine source
│   └── iqm/                   # Model tools
│       ├── iqm                # IQM converter
│       ├── models_src/        # Blender source files
│       ├── models_converted/  # OBJ exports
│       └── pk3_build/         # Assets for packaging
├── mapping/                   # Map sources (create this)
│   ├── maps/                  # .map source files
│   ├── textures/              # Map textures
│   └── scripts/               # Shader scripts
└── ~/.xonotic/data/           # User data (overrides game)
```

---

## NetRadiant Map Editor

### First-Time Setup

1. **Launch NetRadiant**
   ```bash
   netradiant
   ```

2. **Select Game**: Choose "Xonotic" from the game selection dialog

3. **Set Engine Path**: Point to your Xonotic installation
   ```
   /home/scott/Games/Xonotic/
   ```

4. **Configure Preferences** (Edit → Preferences):
   - Grid: 8 units default
   - Texture quality: High
   - Enable 3D view lighting

### Creating a New Map

1. File → New Map
2. Start with a hollow box (room):
   - Draw a brush (box) for floor
   - Draw walls and ceiling
   - Make sure map is sealed (no leaks!)

3. Add spawn points:
   - Right-click → Entity → info_player_deathmatch

4. Add lights:
   - Right-click → Entity → light
   - Set "light" key to brightness (300 default)

5. Compile and test:
   ```bash
   # From NetRadiant: Build → Compile BSP
   # Or manually:
   q3map2 -fs_basepath /home/scott/Games/Xonotic -fs_game data maps/mymap.map
   q3map2 -fs_basepath /home/scott/Games/Xonotic -fs_game data -vis maps/mymap.map
   q3map2 -fs_basepath /home/scott/Games/Xonotic -fs_game data -light -fast maps/mymap.map
   ```

### Map Entities Reference

| Entity | Purpose | Key Properties |
|--------|---------|----------------|
| `info_player_deathmatch` | Spawn point | angle (facing) |
| `light` | Point light | light (brightness), color |
| `target_position` | Waypoint marker | targetname |
| `trigger_teleport` | Teleporter | target |
| `func_door` | Moving door | angle, speed, lip |
| `item_armor_large` | Armor pickup | - |
| `item_health_mega` | Mega health | - |
| `weapon_rocketlauncher` | Weapon spawn | - |

### Brush Primitives

| Brush Type | Usage |
|------------|-------|
| `worldspawn` | Static world geometry |
| `func_wall` | Toggleable wall |
| `func_door` | Door/lift |
| `func_rotating` | Rotating object |
| `func_breakable` | Destructible |
| `trigger_*` | Invisible triggers |

### Compiling Maps

```bash
# Full compile pipeline
MAP=mymap

# Step 1: BSP compile
q3map2 -fs_basepath /home/scott/Games/Xonotic -fs_game data -meta maps/$MAP.map

# Step 2: VIS (visibility)
q3map2 -fs_basepath /home/scott/Games/Xonotic -fs_game data -vis maps/$MAP.bsp

# Step 3: Light
q3map2 -fs_basepath /home/scott/Games/Xonotic -fs_game data -light -fast -patchshadows maps/$MAP.bsp

# Copy to game
cp maps/$MAP.bsp /home/scott/Games/Xonotic/data/maps/
```

### Map Testing
```bash
# Test map immediately
./xonotic-linux64-sdl +developer 1 +map mymap
```

### Valid Xonotic Texture Paths

**CRITICAL**: Xonotic uses specific texture paths. Using incorrect paths will result in missing textures (pink/black checkerboard) or completely invisible surfaces.

#### Available Texture Sets (from pk3 files)

| Texture Path | Description | Example |
|--------------|-------------|---------|
| `trak4x/base/` | Industrial metal/rust | `trak4x/base/base_rust2` |
| `trak4x/decal/` | Decals/signage | `trak4x/decal/decal_exit` |
| `trak5x/base/` | Clean metal panels | `trak5x/base/base_metal01` |
| `exx/wall/` | Modern wall panels | `exx/wall/wall_bigrib02` |
| `exx/floor/` | Floor tiles | `exx/floor/floor_clang01` |
| `exx/trim/` | Trim pieces | `exx/trim/trim_psimple04` |
| `common/caulk` | Invisible collision | Always use for hidden faces |

#### Finding Available Textures
```bash
# List textures in a pk3 file
unzip -l data/xonotic-*-maps.pk3 | grep -E "dds/textures/trak"

# Common texture folders
# dds/textures/trak4x/   - Industrial theme
# dds/textures/trak5x/   - Modern theme
# dds/textures/exx/      - Sci-fi theme
# dds/textures/evil1_*   - Gothic/evil theme
```

### Lighting Requirements

Maps **require proper lighting** or they will be completely dark. There are two options:

#### Option 1: Baked Lightmaps (Recommended)

Add light entities to your map and compile with the `-light` pass:

```
// In your .map file, add light entities:
{
"classname" "light"
"origin" "0 0 200"
"light" "400"
"_color" "1 1 1"
}
```

Compile with:
```bash
q3map2 -fs_basepath ... -light -fast -patchshadows mapname.bsp
```

#### Option 2: Ambient Light (Fallback)

Add ambient lighting to worldspawn for minimum visibility:

```
{
"classname" "worldspawn"
"_ambient" "100"
"_minlight" "100"
...
}
```

**Note**: `_ambient` provides base lighting but looks flat. Use point lights for better visuals.

### Map File Format Notes

**IMPORTANT**: Creating Q3 .map files by hand is extremely error-prone. The brush plane definitions use a specific winding order that determines:
- Which direction the surface normal points
- Whether the brush is solid or hollow
- Whether collision detection works

**Always use NetRadiant** to create and edit map geometry. The brush format consists of 6 planes (for a box brush), each defined by 3 points:

```
// Example floor brush (from NetRadiant)
{
( -512 512 0 ) ( -512 -512 0 ) ( 512 -512 0 ) texture 0 0 0 0.5 0.5 0 0 0
( 512 -512 -16 ) ( -512 -512 -16 ) ( -512 512 -16 ) common/caulk 0 0 0 0.5 0.5 0 0 0
...
}
```

The three points define the plane, and the winding order determines the normal direction.

### Compile Script (compile_map.sh)

The SDK includes a compile script at `sdk/scripts/compile_map.sh`:

```bash
# Fast compile (testing)
./sdk/scripts/compile_map.sh mapname fast

# Full compile (normal)
./sdk/scripts/compile_map.sh mapname full

# Final compile (release quality)
./sdk/scripts/compile_map.sh mapname final
```

### Creating a Mapinfo File

Every map needs a `.mapinfo` file in `data/maps/`:

```
title My Arena Map
author Your Name
description Brief description of your map
has weapons
gametype dm
gametype tdm
gametype lms
```

### Practical Workflow: Creating a Working Map

**Why Hand-Written .map Files Don't Work**

Q3/Quake brush geometry is defined by plane intersections. Each brush consists of 6+ planes (for a convex solid), where each plane is defined by 3 points. The specific winding order of these points determines:
- The plane normal direction (which side is solid)
- Whether the brush forms a closed convex volume
- Whether collision detection works

Hand-crafting these plane definitions is extremely error-prone. Even with mathematically correct planes, subtle issues with winding order will cause:
- Brushes to be ignored ("0 total world brushes")
- Geometry to not generate triangles ("0 meta triangles")
- Map leaks ("Entity leaked" errors)
- Player falling through "solid" surfaces

**The Only Reliable Solution: Use NetRadiant**

1. **Create maps in NetRadiant**, not in a text editor
2. **Start from an existing map** by extracting one from the pk3 files
3. **Use the compile script** to test your changes

**Quick Test: Compile an Existing Map**

```bash
# Extract a small working map
cd /home/scott/Games/Xonotic
unzip -p data/xonotic-*-maps.pk3 "maps/_hudsetup.map" > mapping/maps/test_extract.map

# Compile it
./source/sdk/scripts/compile_map.sh test_extract full

# Install it
cp mapping/maps/test_extract.bsp data/maps/

# Create mapinfo
cat > data/maps/test_extract.mapinfo << 'EOF'
title Test Extraction
author Original Author
description Testing compilation pipeline
has weapons
gametype dm
EOF

# Test in game
./xonotic-linux64-glx +map test_extract
```

**Brush Format Reference (NetRadiant Output)**

NetRadiant generates two brush formats:

1. **Standard Q3 Format** (older, simpler):
```
{
( x1 y1 z1 ) ( x2 y2 z2 ) ( x3 y3 z3 ) texture offsetX offsetY rotation scaleX scaleY flags contents value
}
```

2. **BrushDef Format** (newer, with texture matrix):
```
{
brushDef
{
( x1 y1 z1 ) ( x2 y2 z2 ) ( x3 y3 z3 ) ( ( s0 s1 s2 ) ( t0 t1 t2 ) ) texture flags contents value
}
}
```

Both formats are supported by q3map2. NetRadiant handles the complex mathematics automatically.

---

## IQM Model Pipeline

### Overview
IQM (Inter-Quake Model) is the preferred format for Xonotic models. It supports skeletal animation, multiple materials, and is highly optimized.

### Workflow: Blender → OBJ → IQM

#### Step 1: Create/Edit in Blender
```bash
blender model.blend
```

#### Step 2: Export to OBJ
- File → Export → Wavefront (.obj)
- Enable: UV coordinates, Normals, Materials
- Apply modifiers, triangulate faces

#### Step 3: Convert OBJ to IQM
```bash
cd /home/scott/Games/Xonotic/source/iqm
./iqm output.iqm input.obj
```

### IQM Tool Options
```bash
# Basic conversion
./iqm model.iqm model.obj

# With animations (from multiple OBJ frames)
./iqm model.iqm model_frame*.obj

# Specify mesh name
./iqm --mesh mymodel model.iqm model.obj
```

### Command-Line Blender Scripts

#### Create a Simple Box/Desk with Legs
```bash
blender --background --python - << 'EOF'
import bpy, bmesh

bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new("desk")
obj = bpy.data.objects.new("desk", mesh)
bpy.context.collection.objects.link(obj)

bm = bmesh.new()

# Table top: 200x80x5, legs: 10x10x60
top_w, top_d, top_h = 200, 80, 5
leg_size, leg_height = 10, 60

# Create table top
bmesh.ops.create_cube(bm, size=1)
for v in bm.verts:
    v.co.x *= top_w
    v.co.y *= top_d
    v.co.z *= top_h
    v.co.z += leg_height + top_h/2

# Create 4 legs at corners
inset = 15
for lx, ly in [(-top_w/2+inset, -top_d/2+inset), (top_w/2-inset, -top_d/2+inset),
               (-top_w/2+inset, top_d/2-inset), (top_w/2-inset, top_d/2-inset)]:
    bmesh.ops.create_cube(bm, size=1)
    for v in list(bm.verts)[-8:]:
        v.co.x = v.co.x * leg_size + lx
        v.co.y = v.co.y * leg_size + ly
        v.co.z = v.co.z * leg_height + leg_height/2

bm.to_mesh(mesh)
bm.free()

mat = bpy.data.materials.new(name="desk_metal")
obj.data.materials.append(mat)

bpy.ops.wm.obj_export(filepath="/tmp/desk.obj", export_materials=True)
print("Exported desk.obj")
EOF
```

#### Batch Convert OBJ to IQM
```bash
#!/bin/bash
IQM_TOOL="/home/scott/Games/Xonotic/source/iqm/iqm"
for obj in models_converted/*.obj; do
    name=$(basename "$obj" .obj)
    $IQM_TOOL "pk3_build/models/props/${name}.iqm" "$obj"
    echo "Converted: $name"
done
```

---

## Texturing System

### DarkPlaces Texture Resolution Order
1. **Skin file** (`model_0.skin`) - Explicit material → texture mapping
2. **Embedded material name** - Engine searches for texture matching material
3. **Directory fallback** - Searches in model's directory

### Skin File Format
Create `modelname_0.skin` alongside the IQM file:
```
material_name,path/to/texture
another_material,path/to/other_texture
```

**Example** (`rack_clean_0.skin`):
```
rack100,models/props/rack
rack101,models/props/rack
rack102,models/props/rack
```

**Important Notes:**
- NO comments in skin files (breaks parsing)
- NO file extension in texture path (engine adds .tga/.png/.jpg)
- Material names must match exactly what's in the IQM

### Finding Material Names
```bash
# List materials in an IQM file
strings model.iqm | grep -E '^[A-Za-z]' | head -20
```

### Texture Formats
| Format | Alpha | Use Case |
|--------|-------|----------|
| PNG | Yes | General purpose, transparency |
| TGA | Yes | Legacy, uncompressed |
| JPG | No | Smaller size, no transparency |
| DDS | Yes | GPU compressed, fastest loading |

### Texture Sizes
- Power of 2: 256, 512, 1024, 2048
- 1024x1024 is good for props
- 2048x2048 for hero models/weapons

### Special Texture Suffixes
| Suffix | Purpose |
|--------|---------|
| `_norm` | Normal map |
| `_glow` | Emission/glow map |
| `_gloss` | Specular/gloss map |
| `_pants` | Team color layer 1 |
| `_shirt` | Team color layer 2 |

Example: `weapon_rocket.tga`, `weapon_rocket_norm.tga`, `weapon_rocket_glow.tga`

---

## Shader System

Shaders control how surfaces render (transparency, glow, animation, etc.)

### Shader File Location
```
scripts/myshaders.shader    # In PK3
```

### Basic Shader Syntax
```c
// Glowing texture
textures/my/glowing_panel
{
    {
        map textures/my/panel_base.tga
    }
    {
        map textures/my/panel_glow.tga
        blendfunc add
    }
}

// Transparent texture
textures/my/glass
{
    cull none
    surfaceparm trans
    {
        map textures/my/glass.tga
        blendfunc blend
    }
}

// Animated texture (scrolling)
textures/my/scrolling
{
    {
        map textures/my/screen.tga
        tcMod scroll 0.5 0
    }
}

// Sky shader
textures/skies/mysky
{
    qer_editorimage textures/skies/mysky_preview.tga
    surfaceparm noimpact
    surfaceparm nolightmap
    surfaceparm sky
    q3map_sun 1 1 0.8 100 30 60
    skyparms env/mysky - -
}
```

### Surface Parameters
| Param | Effect |
|-------|--------|
| `trans` | Transparent surface |
| `nonsolid` | No collision |
| `noimpact` | Projectiles pass through |
| `nolightmap` | No lightmap |
| `slick` | Low friction (ice) |
| `sky` | Sky surface |
| `lava` | Damage + lava effect |
| `water` | Water effect |

### Blend Functions
| Blendfunc | Effect |
|-----------|--------|
| `blend` | Alpha transparency |
| `add` | Additive (glow) |
| `filter` | Multiply (darken) |

---

## Audio & Sound

### Supported Formats
| Format | Use Case |
|--------|----------|
| **OGG Vorbis** | Recommended - good quality, small size |
| **WAV** | Uncompressed, for short sounds |
| **MP3** | Music (larger files) |

### Sound Directory Structure
```
sound/
├── weapons/           # Weapon sounds
│   ├── rocket_fire.ogg
│   └── rocket_explode.ogg
├── player/            # Player sounds
│   ├── jump.ogg
│   └── land.ogg
├── announcer/         # Announcer voices
│   └── sophia/
│       ├── shielddown.ogg
│       └── shieldrecharge.ogg
├── ambient/           # Ambient loops
│   └── machinery.ogg
└── misc/              # Misc sounds
    └── pickup.ogg
```

### Creating Sounds with Audacity
```bash
audacity  # Open Audacity

# Export settings for OGG:
# - Sample rate: 44100 Hz
# - Channels: Mono (for 3D sounds) or Stereo (music)
# - Quality: 6-8 (good balance)
```

### Converting Audio (Command Line)
```bash
# WAV to OGG
ffmpeg -i sound.wav -c:a libvorbis -q:a 6 sound.ogg

# MP3 to OGG
ffmpeg -i music.mp3 -c:a libvorbis -q:a 8 music.ogg

# Batch convert
for f in *.wav; do
    ffmpeg -i "$f" -c:a libvorbis -q:a 6 "${f%.wav}.ogg"
done
```

### Playing Sounds in QuakeC
```c
// Simple sound
sound(entity, CHAN_WEAPON, "weapons/rocket_fire.ogg", VOL_BASE, ATTEN_NORM);

// To specific player only
stuffcmd(player, "play sound/announcer/sophia/shielddown.ogg\n");

// Precache first!
precache_sound("weapons/rocket_fire.ogg");
```

### Sound Channels
| Channel | Purpose |
|---------|---------|
| `CH_WEAPON` | Weapon fire |
| `CH_VOICE` | Voice/speech |
| `CH_TRIGGER` | Triggered sounds |
| `CH_SHOTS` | Projectile impacts |
| `CH_AMBIENT` | Ambient loops |

### Attenuation
| Value | Range |
|-------|-------|
| `ATTEN_NONE` | Global (everywhere) |
| `ATTEN_NORM` | Normal falloff |
| `ATTEN_IDLE` | Short range |
| `ATTEN_STATIC` | Very short |

---

## QuakeC Development

### Compiler: GMQCC
```bash
# Compile from qcsrc directory
cd /home/scott/Games/Xonotic/source/qcsrc
make QCC=/home/scott/Games/Xonotic/source/gmqcc/gmqcc
```

### Output Files
- `progs.dat` - Server code (MUST copy to data folders)
- `csprogs.dat` - Client code
- `menu.dat` - Menu code

### Deploying Compiled Code
```bash
# Copy to BOTH locations (user data overrides game data)
cp progs.dat ~/.xonotic/data/
cp progs.dat /home/scott/Games/Xonotic/data/
```

### Key Data Types
```c
float       // Numbers (integers and decimals)
vector      // 3D coordinates: '100 200 50'
string      // Text
entity      // Game object reference
```

### Autocvars (Console Variables)
```c
// In header file (.qh)
float autocvar_g_my_feature = 1;  // Default value

// Usage - automatically synced with console
if (autocvar_g_my_feature)
    LOG_INFO("Feature enabled!");
```

### Entity Fields
```c
// Declare in header
.float my_custom_field;
.entity my_target;

// Use on entities
player.my_custom_field = 100;
```

### Useful Functions
```c
// Logging
LOG_INFO("Message: ", ftos(value), " at ", vtos(position));

// Model/Entity
precache_model("models/props/thing.iqm");
setmodel(ent, "models/props/thing.iqm");
_setmodel(ent, modelpath);  // Dynamic string version
setorigin(ent, '100 200 0');
setsize(ent, '-16 -16 0', '16 16 32');  // Bounding box

// Math
makevectors(angles);  // Sets v_forward, v_right, v_up
normalize(vector);
vlen(vector);         // Vector length
random();             // 0.0 to 1.0

// String
strstrofs(haystack, needle, 0);  // Find substring, -1 if not found
strcat(str1, str2);
ftos(float_val);      // Float to string
vtos(vector_val);     // Vector to string

// Tracing (raycasts)
traceline(start, end, MOVE_NORMAL, ignore_ent);
// Results in: trace_endpos, trace_fraction, trace_ent, trace_plane_normal
```

---

## Mutator System

Mutators are modular gameplay modifications that can be enabled/disabled.

### File Structure
```
qcsrc/common/mutators/mutator/my_mutator/
├── my_mutator.qh       # Header - cvars, fields
├── sv_my_mutator.qc    # Server code
├── sv_my_mutator.qh    # Server header
├── cl_my_mutator.qc    # Client code (optional)
└── cl_my_mutator.qh    # Client header (optional)
```

### Basic Mutator Template

**sv_my_mutator.qh:**
```c
#pragma once

#ifdef SVQC
// Console variables
float autocvar_g_my_mutator = 1;
float autocvar_g_my_mutator_value = 100;

// Entity fields
.float my_field;
#endif
```

**sv_my_mutator.qc:**
```c
#include "sv_my_mutator.qh"

#ifdef SVQC

#include <common/resources/sv_resources.qh>
#include <server/damage.qh>
#include <server/client.qh>

// Register the mutator
REGISTER_MUTATOR(my_mutator, autocvar_g_my_mutator)
{
    MUTATOR_ONADD
    {
        LOG_INFO("[MY_MUTATOR] Activated!");
    }
    MUTATOR_ONREMOVE
    {
        LOG_INFO("[MY_MUTATOR] Deactivated");
    }
}

// Hook: Player spawns
MUTATOR_HOOKFUNCTION(my_mutator, PlayerSpawn)
{
    entity player = M_ARGV(0, entity);
    player.my_field = autocvar_g_my_mutator_value;
}

// Hook: Damage calculation
MUTATOR_HOOKFUNCTION(my_mutator, Damage_Calculate)
{
    entity attacker = M_ARGV(1, entity);
    entity target = M_ARGV(2, entity);
    float damage = M_ARGV(4, float);

    // Modify damage
    damage *= 0.5;
    M_ARGV(4, float) = damage;

    return false;
}

// Hook: Filter item spawns
MUTATOR_HOOKFUNCTION(my_mutator, FilterItem)
{
    entity item = M_ARGV(0, entity);

    if (strstrofs(item.classname, "armor", 0) >= 0)
        return true;  // Don't spawn armor

    return false;
}

#endif
```

### Common Hooks
| Hook | Purpose | Arguments |
|------|---------|-----------|
| `PlayerSpawn` | Player respawns | `M_ARGV(0, entity)` = player |
| `PlayerDies` | Player dies | attacker, target, etc. |
| `Damage_Calculate` | Modify damage | attacker, target, damage, deathtype |
| `FilterItem` | Block item spawns | `M_ARGV(0, entity)` = item |
| `ItemTouch` | Item pickup | item entity |
| `PlayerPhysics` | Modify movement | player entity |
| `PlayerRegen` | Health/armor regen | player entity |
| `ForbidDropCurrentWeapon` | Override weapon drop | player entity |
| `WeaponRateFactor` | Modify fire rate | - |
| `PlayerPreThink` | Every frame before physics | player |
| `PlayerPostThink` | Every frame after physics | player |

### Enabling Mutators

**autoexec.cfg** (`~/.xonotic/data/autoexec.cfg`):
```
set g_my_mutator 1
echo "My Mutator Enabled!"
```

---

## Props & Entity Spawning

### Spawn Function Template
```c
entity SpawnProp(string modelpath, vector pos, vector ang, float scale_factor, vector color)
{
    entity prop = new(my_prop);
    prop.solid = SOLID_BSP;       // Collision type
    prop.movetype = MOVETYPE_NONE; // Static
    setorigin(prop, pos);
    prop.angles = ang;

    precache_model(modelpath);
    _setmodel(prop, modelpath);

    prop.scale = scale_factor;
    prop.colormod = color;        // RGB tint (0-1 range)

    // Bounding box
    vector mins = '-16 -16 0' * scale_factor;
    vector maxs = '16 16 32' * scale_factor;
    setsize(prop, mins, maxs);

    return prop;
}
```

### Solid Types
| Type | Description |
|------|-------------|
| `SOLID_NOT` | No collision |
| `SOLID_TRIGGER` | Touch triggers but no blocking |
| `SOLID_BSP` | Full collision (use for props) |
| `SOLID_BBOX` | Bounding box collision |

### Move Types
| Type | Description |
|------|-------------|
| `MOVETYPE_NONE` | Static, no movement |
| `MOVETYPE_WALK` | Player-style movement |
| `MOVETYPE_TOSS` | Gravity + bounce |
| `MOVETYPE_BOUNCE` | Bouncy projectile |
| `MOVETYPE_FLY` | No gravity |

### Map-Specific Spawning
```c
void SpawnMapProps()
{
    if (mapname == "warfare")
    {
        SpawnProp("models/props/rack.iqm", '0 0 0', '0 0 0', 0.3, '1 1 1');
        SpawnProp("models/props/desk.iqm", '100 60 0', '0 90 0', 0.4, '0.5 0.5 0.5');
    }
    else if (mapname == "afterslime")
    {
        // Different props for different map
    }
}
```

---

## Particle Effects

### Effect Definition Files
```
effectinfo.txt    # Main effects file
```

### Basic Effect Syntax
```
// Explosion effect
effect explosion
count 50
type smoke
color 0xFF6600 0xFF0000
size 10 30
sizeincrease 50
alpha 256 256 300
velocityjitter 200 200 200
gravity 0.5
airfriction 3
liquidfriction 6
```

### Using Effects in QuakeC
```c
// Precache effect
float EFFECT_MY_EXPLOSION;
EFFECT_MY_EXPLOSION = particleeffectnum("my_explosion");

// Spawn effect
Send_Effect(EFFECT_ROCKET_EXPLODE, position, velocity, count);

// Or use string directly
pointparticles(particleeffectnum("my_explosion"), position, velocity, count);
```

---

## HUD & UI Customization

### HUD Files
```
hud_luma.cfg       # HUD layout configuration
gfx/hud/           # HUD graphics
```

### Custom HUD Elements (CSQC)
```c
// In client code
void HUD_MyElement()
{
    vector pos = '100 100 0';
    vector size = '200 50 0';

    // Draw background
    drawfill(pos, size, '0 0 0', 0.5, 0);

    // Draw text
    drawstring(pos + '10 10 0', "My HUD", '16 16 0', '1 1 1', 1, 0);
}
```

---

## Bot AI

### Bot Waypoints
Bots use waypoints for navigation. Create them in-game:
```
sv_cheats 1
bot_cmd waypoint spawn        # Create waypoint at current position
bot_cmd waypoint saveall      # Save waypoints for current map
```

### Bot Difficulty
```
skill 0    # Easy (0-10 scale)
skill 5    # Medium
skill 10   # Nightmare
```

### Bot Commands
```
bot_number 4                  # Add 4 bots
bot_vs_human 1               # Bots vs humans mode
bot_cmd kick all             # Remove all bots
```

---

## Networking & Multiplayer

### Server Setup
```bash
# Dedicated server
./xonotic-linux64-dedicated +serverconfig server.cfg

# LAN server
./xonotic-linux64-sdl +sv_public 0 +map warfare
```

### Server Config (server.cfg)
```
hostname "My Server"
sv_public 1
maxplayers 16
g_deathmatch 1
timelimit 15
fraglimit 30
```

### Network Cvars
```
cl_netfps 60          # Client update rate
sv_maxrate 50000      # Max bandwidth per client
```

---

## PK3 Packaging

PK3 files are ZIP archives with game assets.

### Directory Structure
```
pk3_build/
├── models/
│   └── props/
│       ├── model.iqm
│       ├── model_0.skin
│       └── texture.png
├── textures/
│   └── custom/
│       └── texture.png
├── sound/
│   └── custom/
│       └── sound.ogg
├── gfx/
│   └── hud/
│       └── custom_icon.png
├── maps/
│   └── mymap.bsp
└── scripts/
    └── shaders.shader
```

### Build PK3
```bash
cd pk3_build
zip -r ../my_mod.pk3 .

# Copy to game data
cp ../my_mod.pk3 ~/.xonotic/data/
cp ../my_mod.pk3 /home/scott/Games/Xonotic/data/
```

### Load Order
- Files are loaded alphabetically
- `zzz_*.pk3` loads last (overrides earlier files)
- User data (`~/.xonotic/data/`) overrides game data

---

## Testing & Debugging

### Launch Commands
```bash
# Quick test with bots
./xonotic-linux64-sdl +skill 1 +bot_number 3 +map warfare

# Developer mode
./xonotic-linux64-sdl +developer 1 +map warfare

# Specific mutator
./xonotic-linux64-sdl +set g_my_mutator 1 +map warfare

# Windowed mode for debugging
./xonotic-linux64-sdl +vid_fullscreen 0 +vid_width 1280 +vid_height 720
```

### Console Commands
```
developer 1          # Enable developer messages
map warfare          # Load map
restart              # Restart map
quit                 # Exit game
status               # Server status
condump log.txt      # Dump console to file

# Entity debugging
sv_cheats 1
noclip               # Fly through walls
god                  # Invincibility
notarget             # Bots ignore you
give all             # All weapons/ammo

# Graphics debugging
r_showbboxes 1       # Show entity bounding boxes
r_showtris 1         # Wireframe mode
r_showshadows 1      # Show shadow volumes
```

### Logging in QC
```c
LOG_INFO("Debug: value = ", ftos(value));
LOG_INFO("Position: ", vtos(entity.origin));
```

### Common Issues

**Mutator not activating:**
1. Check autocvar is `float` not `bool`
2. Check autoexec.cfg sets the cvar
3. Copy progs.dat to BOTH data folders

**Model not showing:**
1. Check precache_model() called
2. Check model path is correct
3. Check PK3 structure

**Textures not loading:**
1. Check skin file format (no comments!)
2. Check material names match IQM
3. Check texture path (no extension)

**Old code still running:**
```bash
# Clear ALL cached progs
rm ~/.xonotic/data/progs.dat
rm /home/scott/Games/Xonotic/data/progs.dat
# Then recompile and copy fresh
```

**Map won't load:**
1. Check BSP is in maps/ folder
2. Check for compile errors (leak, etc.)
3. Run with +developer 1 for messages

---

## RustChain Integration

### Overview
RustChain PoA FPS integrates blockchain rewards with Xonotic gameplay.

### Server-Side API Integration
```c
// In QuakeC - poll RustChain API
float autocvar_g_rustchain_api_url;
float autocvar_g_rustchain_poll_interval = 60;

void RustChain_PollAPI()
{
    // Use uri_get for HTTP requests
    uri_get("https://50.28.86.131/api/miners", 1);
}
```

### Reward Events
- Kill events → RTC rewards
- Match completion → RTC bonus
- Achievement unlocks → Special rewards

### Wallet Integration
Players register wallet addresses via chat command:
```
!wallet RTC1234567890abcdef...
```

---

## Quick Reference

### Full Build & Test Cycle
```bash
# 1. Compile QC
cd /home/scott/Games/Xonotic/source/qcsrc
make QCC=/home/scott/Games/Xonotic/source/gmqcc/gmqcc

# 2. Deploy progs.dat
cp ../progs.dat ~/.xonotic/data/
cp ../progs.dat /home/scott/Games/Xonotic/data/

# 3. Build PK3 (if assets changed)
cd ../iqm/pk3_build
zip -r ../my_mod.pk3 .
cp ../my_mod.pk3 ~/.xonotic/data/

# 4. Kill old game, restart
pkill -9 xonotic; sleep 1
cd /home/scott/Games/Xonotic
./xonotic-linux64-sdl +skill 1 +bot_number 3 +map warfare
```

### One-Liner Build & Test
```bash
make QCC=/home/scott/Games/Xonotic/source/gmqcc/gmqcc && cp ../progs.dat ~/.xonotic/data/ && cp ../progs.dat /home/scott/Games/Xonotic/data/ && pkill -9 xonotic; sleep 1 && cd /home/scott/Games/Xonotic && ./xonotic-linux64-sdl +skill 1 +bot_number 3 +map warfare
```

### Tool Locations
| Tool | Path |
|------|------|
| Game | `/home/scott/Games/Xonotic/xonotic-linux64-sdl` |
| QC Compiler | `/home/scott/Games/Xonotic/source/gmqcc/gmqcc` |
| IQM Tool | `/home/scott/Games/Xonotic/source/iqm/iqm` |
| QC Source | `/home/scott/Games/Xonotic/source/qcsrc/` |
| Game Data | `/home/scott/Games/Xonotic/data/` |
| User Data | `~/.xonotic/data/` |

---

## Credits

Developed as part of the **RustChain PoA FPS** project.
- RustChain blockchain integration for gaming rewards
- Hello Shield mutator (Halo-style gameplay)
- Library War props system

**Resources:**
- Xonotic Wiki: https://gitlab.com/xonotic/xonotic/-/wikis/home
- NetRadiant: https://netradiant.gitlab.io/
- DarkPlaces Engine: https://icculus.org/twilight/darkplaces/

**License:** GPL (following Xonotic licensing)
