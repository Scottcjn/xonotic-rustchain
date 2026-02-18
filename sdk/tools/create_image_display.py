#!/usr/bin/env python3
"""
RustChain SDK - Image Display Creator for Xonotic Maps

Creates OBJ quad models for displaying images in Xonotic/DarkPlaces maps.
Bypasses the Q3 brush texture coordinate system entirely by using proper
UV-mapped OBJ models that display textures 1:1 regardless of world position.

Usage:
    python3 create_image_display.py <image_path> [--width 256] [--height 256] [--name display_name]

Examples:
    # Create a display from an image (auto-detects size)
    python3 create_image_display.py ~/Pictures/my_poster.png

    # Create with custom size
    python3 create_image_display.py ~/Pictures/logo.png --width 512 --height 256

    # Create with custom name
    python3 create_image_display.py ~/Pictures/art.png --name museum_artwork

Output:
    Creates in data/models/displays/:
        - display_<name>.obj  (3D model)
        - display_<name>.mtl  (material file)

    Copies texture to data/textures/rustchain/:
        - <original_filename>

Map Usage:
    Add as misc_model entity:
    {
        "classname" "misc_model"
        "model" "models/displays/display_<name>.obj"
        "origin" "x y z"
        "angle" "0"        // 0=north, 90=east, 180=south, 270=west
        "modelscale" "1.0"
    }
"""

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def get_xonotic_dir():
    """Find the Xonotic installation directory."""
    # Check common locations
    candidates = [
        Path("/home") / os.environ.get("USER", "user") / "Games/Xonotic",
        Path.home() / "Games/Xonotic",
        Path.home() / ".xonotic",
        Path("/opt/Xonotic"),
        Path("/usr/share/games/xonotic"),
    ]

    for path in candidates:
        if (path / "data").exists():
            return path

    # Fallback to current script location
    script_dir = Path(__file__).resolve().parent
    if "Xonotic" in str(script_dir):
        # Walk up to find Xonotic root
        for parent in script_dir.parents:
            if (parent / "data").exists():
                return parent

    raise RuntimeError("Could not find Xonotic installation. Set XONOTIC_DIR environment variable.")


def get_image_dimensions(image_path: Path) -> tuple:
    """Get image dimensions using ImageMagick identify."""
    try:
        result = subprocess.run(
            ["identify", "-format", "%w %h", str(image_path)],
            capture_output=True, text=True, check=True
        )
        w, h = result.stdout.strip().split()
        return int(w), int(h)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to default
        return 256, 256


def create_quad_obj(name: str, width: float, height: float, texture_path: str) -> str:
    """
    Create an OBJ file for a textured quad.

    The quad is centered horizontally, with bottom at z=0.
    Faces +Y direction (north) by default - use angle in misc_model to rotate.
    UV coords are 0-1, so texture maps perfectly regardless of world position.
    """
    hw = width / 2

    # Vertices: bottom-left, bottom-right, top-right, top-left
    # Quad in XZ plane at Y=0, facing +Y (north)
    vertices = [
        (-hw, 0, 0),       # bottom-left
        (hw, 0, 0),        # bottom-right
        (hw, 0, height),   # top-right
        (-hw, 0, height),  # top-left
    ]

    # UV coordinates (0-1 range, maps entire texture)
    uvs = [
        (0, 0),  # bottom-left
        (1, 0),  # bottom-right
        (1, 1),  # top-right
        (0, 1),  # top-left
    ]

    obj_content = f"""# RustChain SDK - Image Display Quad
# Model: {name}
# Size: {width}x{height} game units
# Texture: {texture_path}
#
# Usage in map:
#   "classname" "misc_model"
#   "model" "models/displays/{name}.obj"
#   "origin" "x y z"
#   "angle" "0"  // 0=north, 90=east, 180=south, 270=west

mtllib {name}.mtl

o {name}
"""

    # Vertices
    for v in vertices:
        obj_content += f"v {v[0]} {v[1]} {v[2]}\n"

    # Texture coordinates
    for uv in uvs:
        obj_content += f"vt {uv[0]} {uv[1]}\n"

    # Normal (facing +Y)
    obj_content += "vn 0 1 0\n"

    # Faces - double-sided for visibility from both directions
    obj_content += f"\nusemtl {name}_mat\n"
    # Front face (CCW winding, visible from +Y)
    obj_content += "f 1/1/1 2/2/1 3/3/1 4/4/1\n"
    # Back face (CW winding, visible from -Y)
    obj_content += "f 4/4/1 3/3/1 2/2/1 1/1/1\n"

    return obj_content


def create_mtl(name: str, texture_path: str) -> str:
    """Create MTL material file for the quad."""
    return f"""# RustChain SDK - Material for {name}
# Texture: {texture_path}

newmtl {name}_mat
Ka 1.0 1.0 1.0
Kd 1.0 1.0 1.0
Ks 0.0 0.0 0.0
Ns 0
d 1.0
illum 1
map_Kd {texture_path}
"""


def create_display(image_path: str, width: int = None, height: int = None,
                   name: str = None, texture_subdir: str = "rustchain"):
    """
    Create a complete image display (OBJ + MTL + copy texture).

    Args:
        image_path: Path to source image
        width: Display width in game units (default: image width or 256)
        height: Display height in game units (default: image height or 256)
        name: Model name (default: derived from image filename)
        texture_subdir: Subdirectory under textures/ for the image

    Returns:
        Path to created OBJ file
    """
    image_path = Path(image_path).resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    xonotic_dir = get_xonotic_dir()
    models_dir = xonotic_dir / "data" / "models" / "displays"
    textures_dir = xonotic_dir / "data" / "textures" / texture_subdir

    # Create directories
    models_dir.mkdir(parents=True, exist_ok=True)
    textures_dir.mkdir(parents=True, exist_ok=True)

    # Determine name from image filename if not provided
    if name is None:
        name = "display_" + image_path.stem.lower().replace(" ", "_").replace("-", "_")
    elif not name.startswith("display_"):
        name = "display_" + name

    # Get image dimensions if not specified
    if width is None or height is None:
        img_w, img_h = get_image_dimensions(image_path)
        if width is None:
            width = min(img_w, 512)  # Cap at 512 for reasonable in-game size
        if height is None:
            # Maintain aspect ratio
            height = int(width * img_h / img_w)

    # Copy texture to Xonotic data folder
    texture_filename = image_path.name
    texture_dest = textures_dir / texture_filename
    if not texture_dest.exists() or texture_dest.stat().st_mtime < image_path.stat().st_mtime:
        shutil.copy2(image_path, texture_dest)
        print(f"Copied texture: {texture_dest}")

    # Texture path relative to Xonotic data folder
    texture_path = f"textures/{texture_subdir}/{texture_filename}"

    # Create OBJ
    obj_content = create_quad_obj(name, width, height, texture_path)
    obj_path = models_dir / f"{name}.obj"
    with open(obj_path, 'w') as f:
        f.write(obj_content)
    print(f"Created model: {obj_path}")

    # Create MTL
    mtl_content = create_mtl(name, texture_path)
    mtl_path = models_dir / f"{name}.mtl"
    with open(mtl_path, 'w') as f:
        f.write(mtl_content)
    print(f"Created material: {mtl_path}")

    # Print usage info
    print()
    print("=" * 60)
    print("To use in your map, add this entity:")
    print("=" * 60)
    print('{')
    print('    "classname" "misc_model"')
    print(f'    "model" "models/displays/{name}.obj"')
    print('    "origin" "0 0 64"  // Adjust position')
    print('    "angle" "0"        // 0=N, 90=E, 180=S, 270=W')
    print('    "modelscale" "1.0"')
    print('}')
    print("=" * 60)

    return obj_path


def main():
    parser = argparse.ArgumentParser(
        description="Create image display models for Xonotic maps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("image", help="Path to image file (PNG, TGA, JPG)")
    parser.add_argument("--width", "-w", type=int, help="Display width in game units")
    parser.add_argument("--height", "-H", type=int, help="Display height in game units")
    parser.add_argument("--name", "-n", help="Model name (default: from filename)")
    parser.add_argument("--texture-dir", "-t", default="rustchain",
                       help="Texture subdirectory (default: rustchain)")

    args = parser.parse_args()

    try:
        create_display(
            args.image,
            width=args.width,
            height=args.height,
            name=args.name,
            texture_subdir=args.texture_dir
        )
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
