# Xonotic IQM Model Texturing Guide

## Overview

Xonotic (DarkPlaces engine) uses **IQM (Inter-Quake Model)** format for 3D models. Texturing IQM models requires understanding how material names are mapped to texture files.

## The Texture Resolution Chain

When DarkPlaces loads an IQM model, it resolves textures in this order:

1. **Skin file** (`.skin`) - Explicit material-to-texture mapping
2. **Embedded material name** - Uses material name as texture path
3. **Model directory fallback** - Looks for textures in same folder as model

## File Structure

```
pk3_root/
├── models/
│   └── props/
│       ├── mymodel.iqm          # The model file
│       ├── mymodel_0.skin       # Skin 0 (default)
│       ├── mymodel_1.skin       # Skin 1 (alternate)
│       └── mytexture.png        # Texture file (or .tga, .jpg)
└── textures/
    └── models/
        └── props/
            └── mytexture.png    # Alternative texture location
```

## Skin File Format

Skin files map **material names** (embedded in IQM) to **texture paths**.

### Syntax
```
material_name,texture_path
```

### Example: `mymodel_0.skin`
```
# Comments start with #
Mat_1,models/props/metal_diffuse
Mat_2,models/props/glass_diffuse
Material.001,models/props/rust
```

### Key Rules

1. **Material name** = exact string from IQM file (case-sensitive)
2. **Texture path** = relative to pk3 root, **without file extension**
3. **No spaces** around the comma
4. **One mapping per line**

## Finding Material Names in IQM

Use `strings` to extract embedded material names:

```bash
strings mymodel.iqm | head -20
```

Output example:
```
INTERQUAKEMODEL
mesh_body
mesh_glass
Mat_1          <-- Material name
Mat_2          <-- Material name
```

## Texture File Extensions

DarkPlaces searches for textures in this order:
1. `.tga` (recommended - supports alpha)
2. `.png` (good quality, alpha support)
3. `.jpg` (smaller size, no alpha)

You specify the path **without extension** - DarkPlaces finds the right file.

## Special Texture Suffixes (PBR/Shaders)

DarkPlaces supports additional texture maps:

| Suffix | Purpose |
|--------|---------|
| `_norm` | Normal map |
| `_gloss` | Glossiness/specular |
| `_glow` | Emissive/self-illumination |
| `_pants` | Team color layer 1 |
| `_shirt` | Team color layer 2 |

Example:
```
models/props/metal         # Diffuse (base color)
models/props/metal_norm    # Normal map (auto-loaded)
models/props/metal_glow    # Glow map (auto-loaded)
```

## Complete Workflow

### 1. Export from Blender

```
File → Export → IQM (.iqm)
```

**Important Blender settings:**
- Use simple material names (avoid `#` and special chars)
- Or rename materials before export to clean names like `mat00`, `mat01`

### 2. Check Material Names

```bash
strings mymodel.iqm | grep -E "^[A-Za-z]"
```

### 3. Create Skin File

```bash
# Create mymodel_0.skin
cat > mymodel_0.skin << 'EOF'
mat00,models/props/mymodel_diffuse
mat01,models/props/mymodel_metal
mat02,models/props/mymodel_glass
EOF
```

### 4. Prepare Textures

- Convert to PNG or TGA
- Place in `models/props/` or `textures/models/props/`
- Name must match skin file path (without extension)

### 5. Build PK3

```bash
cd pk3_build
zip -r ../mymod.pk3 models/ textures/
```

### 6. Test in Game

```
# In Xonotic console
map warfare
sv_cheats 1
give all
```

## Troubleshooting

### Model appears white/untextured

1. Check skin file exists: `modelname_0.skin`
2. Verify material names match exactly (case-sensitive)
3. Ensure texture file exists at specified path
4. Check texture has no extension in skin file

### "texture not found" errors in console

```
# Enable texture debug logging
developer 1
```

Look for lines like:
```
loading textures/models/props/mytexture.tga
```

### Wrong texture on mesh

Material names in skin file don't match IQM. Re-check with `strings`.

## Example: Server Rack Model

**IQM file**: `server_rack.iqm`
**Materials found**: `Mat_1`, `Mat_2`

**Skin file** (`server_rack_0.skin`):
```
Mat_1,models/props/rack_metal
Mat_2,models/props/rack_metal
```

**Texture file**: `models/props/rack_metal.png`

## Blender Material Name Gotchas

Blender adds problematic characters to material names:

| Blender Shows | IQM Gets | Problem |
|---------------|----------|---------|
| `Material #0` | `Material_#0` | Hash symbol |
| `Material.001` | `Material.001` | Dots work but messy |
| `Untitled` | `Untitled` | Generic name |

**Solution**: Rename materials in Blender before export:
1. Select object
2. Go to Material Properties
3. Click material name → rename to `mat00`, `mat01`, etc.

## Code Reference: Loading Models in QuakeC

```c
// Server-side (sv_hello_shield.qc)
precache_model("models/props/rack_clean.iqm");
_setmodel(prop, "models/props/rack_clean.iqm");

// Optional: Force specific skin
prop.skin = 0;  // Uses rack_clean_0.skin
prop.skin = 1;  // Uses rack_clean_1.skin
```

## DarkPlaces Texture Search Paths

1. `models/props/texturename.tga`
2. `models/props/texturename.png`
3. `models/props/texturename.jpg`
4. `textures/models/props/texturename.tga`
5. `textures/models/props/texturename.png`
6. `textures/models/props/texturename.jpg`

## Quick Reference

| Task | Command/File |
|------|--------------|
| Find materials | `strings model.iqm \| head -20` |
| Skin file name | `modelname_0.skin` |
| Skin syntax | `material,path/without/extension` |
| Build pk3 | `zip -r mod.pk3 models/ textures/` |
| Test in game | `developer 1` then load map |

---

*Document created for Xonotic/DarkPlaces modding - Hello Shield project*
