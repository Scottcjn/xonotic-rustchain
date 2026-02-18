#!/usr/bin/env python3
"""
Create textured quad models for image displays in Xonotic.
Bypasses Q3 brush texture coordinate system entirely.

This creates simple OBJ files that can be converted to IQM for use as misc_model.
Each display is a flat quad with proper UV mapping (0-1 range).
"""

import os
import struct
from pathlib import Path

XONOTIC_DIR = Path("/home/scott/Games/Xonotic")
MODELS_DIR = XONOTIC_DIR / "data" / "models" / "displays"
TEXTURES_DIR = XONOTIC_DIR / "data" / "textures" / "rustchain"


def create_quad_obj(name: str, width: float, height: float, texture_path: str) -> str:
    """
    Create an OBJ file for a textured quad.

    The quad is centered at origin, facing +Y direction (north).
    UV coords are 0-1, so texture maps perfectly regardless of world position.
    """
    hw = width / 2
    hh = height / 2

    # Vertices: bottom-left, bottom-right, top-right, top-left
    # Quad faces +Y (north), so X is horizontal, Z is vertical
    vertices = [
        (-hw, 0, 0),      # bottom-left
        (hw, 0, 0),       # bottom-right
        (hw, 0, height),  # top-right
        (-hw, 0, height), # top-left
    ]

    # UV coordinates (0-1 range, maps entire texture)
    uvs = [
        (0, 0),  # bottom-left
        (1, 0),  # bottom-right
        (1, 1),  # top-right
        (0, 1),  # top-left
    ]

    # Face (quad as two triangles)
    # Front face (visible from +Y)

    obj_content = f"""# Display quad: {name}
# Size: {width}x{height} units
# Texture: {texture_path}

mtllib {name}.mtl

o {name}
"""

    # Vertices
    for v in vertices:
        obj_content += f"v {v[0]} {v[1]} {v[2]}\n"

    # Texture coordinates
    for uv in uvs:
        obj_content += f"vt {uv[0]} {uv[1]}\n"

    # Normals (facing +Y)
    obj_content += "vn 0 1 0\n"

    # Face with material - double-sided (front and back)
    obj_content += f"\nusemtl {name}_mat\n"
    # Front face (CCW winding, visible from +Y)
    obj_content += "f 1/1/1 2/2/1 3/3/1 4/4/1\n"
    # Back face (CW winding, visible from -Y)
    obj_content += "f 4/4/1 3/3/1 2/2/1 1/1/1\n"

    return obj_content


def create_mtl(name: str, texture_path: str) -> str:
    """Create MTL material file for the quad."""
    return f"""# Material for {name}
newmtl {name}_mat
Ka 1.0 1.0 1.0
Kd 1.0 1.0 1.0
Ks 0.0 0.0 0.0
Ns 0
d 1.0
illum 1
map_Kd {texture_path}
"""


def create_display_model(name: str, texture_name: str, width: int = 256, height: int = 256):
    """
    Create a complete display model (OBJ + MTL).

    Args:
        name: Model name (e.g., "museum_sign_display")
        texture_name: Texture filename in rustchain folder (e.g., "museum_sign.png")
        width: Display width in world units
        height: Display height in world units
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    texture_path = f"textures/rustchain/{texture_name}"

    # Create OBJ
    obj_content = create_quad_obj(name, width, height, texture_path)
    obj_path = MODELS_DIR / f"{name}.obj"
    with open(obj_path, 'w') as f:
        f.write(obj_content)
    print(f"Created: {obj_path}")

    # Create MTL
    mtl_content = create_mtl(name, texture_path)
    mtl_path = MODELS_DIR / f"{name}.mtl"
    with open(mtl_path, 'w') as f:
        f.write(mtl_content)
    print(f"Created: {mtl_path}")

    return obj_path


def main():
    """Create display models for all museum images."""

    displays = [
        ("display_museum_sign", "museum_sign.png", 256, 256),
        ("display_sophia_poster", "sophia_poster.tga", 256, 256),
        ("display_sophia_terminal", "sophia_terminal.tga", 256, 256),
        ("display_sophia_portrait", "sophia_portrait.tga", 256, 256),
        ("display_robot_janitor", "robot_janitor.png", 256, 256),
        ("display_doginal_dog", "doginal_dog.png", 256, 256),
        ("display_rustchain_logo", "rustchain_logo_new.tga", 256, 256),
        ("display_art1", "art1.tga", 256, 256),
    ]

    print("Creating display models...")
    print(f"Output directory: {MODELS_DIR}")
    print()

    for name, texture, w, h in displays:
        create_display_model(name, texture, w, h)

    print()
    print("Done! Models created as OBJ files.")
    print()
    print("To use in map, add misc_model entities like:")
    print('  "classname" "misc_model"')
    print('  "model" "models/displays/display_museum_sign.obj"')
    print('  "origin" "0 -1536 192"')
    print('  "angles" "0 0 0"')
    print()
    print("The OBJ format is supported directly by DarkPlaces/Xonotic.")


if __name__ == "__main__":
    main()
