#!/usr/bin/env python3
"""
Quake/Xonotic MCP Server
========================
An MCP server that enables AI assistants like Claude to:
- Create and edit Quake .map files
- Generate QuakeC code
- Spawn entities in maps
- Compile maps using q3map2
- Manage textures and shaders

First of its kind - built for RustChain PoA FPS project.
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Quake/Xonotic MCP Server")

# Configuration
XONOTIC_DIR = Path("/home/scott/Games/Xonotic")
MAPPING_DIR = XONOTIC_DIR / "mapping" / "maps"
DATA_DIR = XONOTIC_DIR / "data"
MAPS_OUTPUT_DIR = DATA_DIR / "maps"
Q3MAP2 = XONOTIC_DIR / "source" / "netradiant_1.5.0-20220628-linux-amd64" / "q3map2"
QCSRC_DIR = XONOTIC_DIR / "source" / "qcsrc"

# Ensure directories exist
MAPPING_DIR.mkdir(parents=True, exist_ok=True)
MAPS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# MAP FILE TOOLS
# =============================================================================

@mcp.tool()
def list_maps() -> str:
    """List all available .map source files in the mapping directory."""
    maps = list(MAPPING_DIR.glob("*.map"))
    if not maps:
        return "No .map files found in mapping directory."

    result = "Available map files:\n"
    for m in sorted(maps):
        size = m.stat().st_size
        result += f"  - {m.name} ({size:,} bytes)\n"
    return result


@mcp.tool()
def read_map(map_name: str) -> str:
    """
    Read the contents of a .map file.

    Args:
        map_name: Name of the map (with or without .map extension)
    """
    if not map_name.endswith(".map"):
        map_name += ".map"

    map_path = MAPPING_DIR / map_name
    if not map_path.exists():
        return f"Error: Map '{map_name}' not found in {MAPPING_DIR}"

    content = map_path.read_text()
    lines = content.split('\n')

    # If file is large, truncate with note
    if len(lines) > 500:
        return f"// Map: {map_name} ({len(lines)} lines total, showing first 500)\n" + '\n'.join(lines[:500]) + "\n// ... truncated ..."

    return f"// Map: {map_name}\n{content}"


@mcp.tool()
def create_map(map_name: str, content: str) -> str:
    """
    Create a new .map file with the given content.

    Args:
        map_name: Name for the new map (with or without .map extension)
        content: The full .map file content (Quake brush format)
    """
    if not map_name.endswith(".map"):
        map_name += ".map"

    map_path = MAPPING_DIR / map_name

    # Backup if exists
    if map_path.exists():
        backup_path = map_path.with_suffix(f".map.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        map_path.rename(backup_path)

    map_path.write_text(content)
    return f"Created map: {map_path}\nSize: {len(content):,} bytes"


@mcp.tool()
def append_to_map(map_name: str, entity_content: str) -> str:
    """
    Append an entity (brush or point entity) to an existing map.

    Args:
        map_name: Name of the map to modify
        entity_content: The entity definition to append (must be a complete entity block)
    """
    if not map_name.endswith(".map"):
        map_name += ".map"

    map_path = MAPPING_DIR / map_name
    if not map_path.exists():
        return f"Error: Map '{map_name}' not found"

    content = map_path.read_text()

    # Append the new entity
    new_content = content.rstrip() + "\n" + entity_content + "\n"
    map_path.write_text(new_content)

    return f"Appended entity to {map_name}"


# =============================================================================
# ENTITY TOOLS
# =============================================================================

@mcp.tool()
def add_spawn_point(map_name: str, x: float, y: float, z: float, angle: float = 0) -> str:
    """
    Add a player spawn point to a map.

    Args:
        map_name: Name of the map
        x, y, z: Position coordinates
        angle: Facing angle in degrees (0=east, 90=north, 180=west, 270=south)
    """
    entity = f'''// Player Spawn Point
{{
"classname" "info_player_deathmatch"
"origin" "{x} {y} {z}"
"angle" "{angle}"
}}'''
    return append_to_map(map_name, entity)


@mcp.tool()
def add_light(map_name: str, x: float, y: float, z: float,
              brightness: int = 300, color: str = "1 1 1") -> str:
    """
    Add a light entity to a map.

    Args:
        map_name: Name of the map
        x, y, z: Position coordinates
        brightness: Light intensity (100-1000 typical)
        color: RGB color as "R G B" (0-1 range, e.g., "1 0.9 0.8" for warm)
    """
    entity = f'''// Light
{{
"classname" "light"
"origin" "{x} {y} {z}"
"light" "{brightness}"
"_color" "{color}"
}}'''
    return append_to_map(map_name, entity)


@mcp.tool()
def add_weapon(map_name: str, weapon_type: str, x: float, y: float, z: float) -> str:
    """
    Add a weapon pickup to a map.

    Args:
        map_name: Name of the map
        weapon_type: One of: shotgun, machinegun, rocketlauncher, grenadelauncher,
                     electro, crylink, nex, hagar, mortar, devastator
        x, y, z: Position coordinates
    """
    weapon_map = {
        "shotgun": "weapon_shotgun",
        "machinegun": "weapon_machinegun",
        "rocketlauncher": "weapon_rocketlauncher",
        "grenadelauncher": "weapon_grenadelauncher",
        "electro": "weapon_electro",
        "crylink": "weapon_crylink",
        "nex": "weapon_nex",
        "hagar": "weapon_hagar",
        "mortar": "weapon_mortar",
        "devastator": "weapon_devastator",
    }

    classname = weapon_map.get(weapon_type.lower())
    if not classname:
        return f"Unknown weapon type: {weapon_type}. Valid types: {', '.join(weapon_map.keys())}"

    entity = f'''// Weapon: {weapon_type}
{{
"classname" "{classname}"
"origin" "{x} {y} {z}"
}}'''
    return append_to_map(map_name, entity)


@mcp.tool()
def add_item(map_name: str, item_type: str, x: float, y: float, z: float) -> str:
    """
    Add an item pickup (health, armor, ammo) to a map.

    Args:
        map_name: Name of the map
        item_type: One of: health_small, health_medium, health_large, health_mega,
                   armor_small, armor_medium, armor_large, armor_mega
        x, y, z: Position coordinates
    """
    item_map = {
        "health_small": "item_health_small",
        "health_medium": "item_health_medium",
        "health_large": "item_health_large",
        "health_mega": "item_health_mega",
        "armor_small": "item_armor_small",
        "armor_medium": "item_armor_medium",
        "armor_large": "item_armor_large",
        "armor_mega": "item_armor_mega",
    }

    classname = item_map.get(item_type.lower())
    if not classname:
        return f"Unknown item type: {item_type}. Valid types: {', '.join(item_map.keys())}"

    entity = f'''// Item: {item_type}
{{
"classname" "{classname}"
"origin" "{x} {y} {z}"
}}'''
    return append_to_map(map_name, entity)


# =============================================================================
# COMPILATION TOOLS
# =============================================================================

@mcp.tool()
def compile_map(map_name: str, mode: str = "fast") -> str:
    """
    Compile a .map file to .bsp using q3map2.

    Args:
        map_name: Name of the map to compile
        mode: Compilation mode - "fast" (quick test), "full" (normal), "final" (release quality)
    """
    if not map_name.endswith(".map"):
        map_name += ".map"

    map_path = MAPPING_DIR / map_name
    if not map_path.exists():
        return f"Error: Map '{map_name}' not found"

    if not Q3MAP2.exists():
        return f"Error: q3map2 not found at {Q3MAP2}"

    results = []
    base_opts = f"-fs_basepath {XONOTIC_DIR} -game xonotic"

    # Step 1: BSP
    results.append("=== BSP Compile ===")
    cmd = f"{Q3MAP2} {base_opts} -meta {map_path}"
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    results.append(proc.stdout[-2000:] if len(proc.stdout) > 2000 else proc.stdout)
    if proc.returncode != 0:
        results.append(f"BSP FAILED: {proc.stderr[-500:]}")
        return '\n'.join(results)

    bsp_path = map_path.with_suffix(".bsp")

    # Step 2: VIS (skip for fast mode)
    if mode in ["full", "final"]:
        results.append("\n=== VIS Compile ===")
        vis_opts = "-vis" if mode == "full" else "-vis -saveprt"
        cmd = f"{Q3MAP2} {base_opts} {vis_opts} {map_path}"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
        results.append(proc.stdout[-1000:] if len(proc.stdout) > 1000 else proc.stdout)

    # Step 3: LIGHT
    results.append("\n=== LIGHT Compile ===")
    if mode == "fast":
        light_opts = "-light -fast -patchshadows"
    elif mode == "full":
        light_opts = "-light -patchshadows -bounce 2"
    else:  # final
        light_opts = "-light -patchshadows -bounce 8 -samples 3"

    cmd = f"{Q3MAP2} {base_opts} {light_opts} {map_path}"
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=900)
    results.append(proc.stdout[-1000:] if len(proc.stdout) > 1000 else proc.stdout)

    # Copy to output directory
    if bsp_path.exists():
        output_bsp = MAPS_OUTPUT_DIR / bsp_path.name
        import shutil
        shutil.copy2(bsp_path, output_bsp)
        results.append(f"\n=== SUCCESS ===\nCompiled: {output_bsp}\nSize: {output_bsp.stat().st_size:,} bytes")

    return '\n'.join(results)


@mcp.tool()
def create_mapinfo(map_name: str, title: str, author: str,
                   description: str = "", gametypes: str = "dm,tdm,lms") -> str:
    """
    Create a .mapinfo file for a map (required for Xonotic to recognize it).

    Args:
        map_name: Name of the map (without extension)
        title: Display title for the map
        author: Map author name
        description: Brief description of the map
        gametypes: Comma-separated game types (dm, tdm, ctf, lms, ca, dom, kh, etc.)
    """
    if map_name.endswith(".map") or map_name.endswith(".bsp"):
        map_name = map_name.rsplit(".", 1)[0]

    mapinfo_path = MAPS_OUTPUT_DIR / f"{map_name}.mapinfo"

    lines = [
        f"title {title}",
        f"author {author}",
    ]

    if description:
        lines.append(f"description {description}")

    lines.append("has weapons")

    for gt in gametypes.split(","):
        gt = gt.strip().lower()
        if gt:
            lines.append(f"gametype {gt}")

    content = '\n'.join(lines)
    mapinfo_path.write_text(content)

    return f"Created mapinfo: {mapinfo_path}\n\n{content}"


# =============================================================================
# QUAKEC TOOLS
# =============================================================================

@mcp.tool()
def list_qc_files(subdir: str = "") -> str:
    """
    List QuakeC source files in the qcsrc directory.

    Args:
        subdir: Subdirectory to list (e.g., "common/mutators", "server", "client")
    """
    search_dir = QCSRC_DIR / subdir if subdir else QCSRC_DIR

    if not search_dir.exists():
        return f"Directory not found: {search_dir}"

    qc_files = list(search_dir.rglob("*.qc")) + list(search_dir.rglob("*.qh"))

    if not qc_files:
        return f"No QuakeC files found in {search_dir}"

    # Group by directory
    by_dir = {}
    for f in sorted(qc_files):
        rel = f.relative_to(QCSRC_DIR)
        parent = str(rel.parent)
        if parent not in by_dir:
            by_dir[parent] = []
        by_dir[parent].append(rel.name)

    result = f"QuakeC files in {search_dir}:\n"
    for dir_name, files in sorted(by_dir.items())[:20]:  # Limit output
        result += f"\n{dir_name}/\n"
        for f in files[:10]:
            result += f"  - {f}\n"
        if len(files) > 10:
            result += f"  ... and {len(files) - 10} more\n"

    return result


@mcp.tool()
def read_qc_file(filepath: str) -> str:
    """
    Read a QuakeC source file.

    Args:
        filepath: Path relative to qcsrc directory (e.g., "common/mutators/mutator/hook/hook.qc")
    """
    qc_path = QCSRC_DIR / filepath

    if not qc_path.exists():
        return f"File not found: {qc_path}"

    content = qc_path.read_text()
    lines = content.split('\n')

    if len(lines) > 300:
        return f"// File: {filepath} ({len(lines)} lines, showing first 300)\n" + '\n'.join(lines[:300]) + "\n// ... truncated ..."

    return f"// File: {filepath}\n{content}"


@mcp.tool()
def search_qc(pattern: str, file_pattern: str = "*.qc") -> str:
    """
    Search for a pattern in QuakeC source files.

    Args:
        pattern: Text pattern to search for
        file_pattern: File glob pattern (default: *.qc)
    """
    results = []
    count = 0
    max_results = 50

    for qc_file in QCSRC_DIR.rglob(file_pattern):
        try:
            content = qc_file.read_text()
            for i, line in enumerate(content.split('\n'), 1):
                if pattern.lower() in line.lower():
                    rel_path = qc_file.relative_to(QCSRC_DIR)
                    results.append(f"{rel_path}:{i}: {line.strip()[:100]}")
                    count += 1
                    if count >= max_results:
                        results.append(f"\n... stopped at {max_results} results")
                        return '\n'.join(results)
        except Exception:
            continue

    if not results:
        return f"No matches found for '{pattern}'"

    return f"Found {count} matches for '{pattern}':\n" + '\n'.join(results)


# =============================================================================
# IMAGE DISPLAY TOOLS - Production quality image loading for wall displays
# =============================================================================

@mcp.tool()
def create_wall_display(
    map_name: str,
    image_path: str,
    cx: float,
    cy: float,
    z_base: float,
    width: int = 256,
    height: int = 256,
    direction: str = "south",
    texture_name: str = ""
) -> str:
    """
    Create a wall-mounted image display with properly centered texture.

    This tool handles all the complexity of Q3 texture mapping:
    - Creates the brush geometry
    - Generates a clampMap shader to prevent tiling
    - Resizes/converts the source image to match display dimensions
    - Calculates proper texture offsets for centering

    Args:
        map_name: Name of the map to add the display to
        image_path: Path to source image (PNG, JPG, TGA)
        cx, cy: Center X,Y position of the display
        z_base: Bottom Z coordinate of the display
        width: Display width in world units (default 256)
        height: Display height in world units (default 256)
        direction: Wall direction - "north", "south", "east", "west"
        texture_name: Optional custom texture name (auto-generated if empty)

    Returns:
        Status message with texture path and brush geometry added
    """
    from PIL import Image
    import hashlib

    image_path = Path(image_path)
    if not image_path.exists():
        return f"Error: Image not found: {image_path}"

    # Generate texture name from image if not provided
    if not texture_name:
        img_hash = hashlib.md5(image_path.name.encode()).hexdigest()[:8]
        texture_name = f"display_{image_path.stem}_{img_hash}"

    # Full texture path for Q3 format
    texture_dir = DATA_DIR / "textures" / "displays"
    texture_dir.mkdir(parents=True, exist_ok=True)

    # Process image - resize to match display dimensions
    try:
        img = Image.open(image_path)

        # Convert to RGB if necessary (handle RGBA, P mode, etc)
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Create white background for transparent images
            background = Image.new('RGB', img.size, (0, 0, 0))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize to match display dimensions (maintain aspect ratio, fit within bounds)
        img = img.resize((width, height), Image.Resampling.LANCZOS)

        # Save as TGA (Xonotic-compatible)
        tga_path = texture_dir / f"{texture_name}.tga"
        img.save(tga_path, format='TGA')

    except Exception as e:
        return f"Error processing image: {e}"

    # Create shader for this texture (clampMap prevents tiling)
    shader_content = f'''// Auto-generated shader for wall display
textures/displays/{texture_name}
{{
    qer_editorimage textures/displays/{texture_name}.tga
    surfaceparm nomarks
    surfaceparm nolightmap
    {{
        clampMap textures/displays/{texture_name}.tga
    }}
}}
'''

    # Append to displays shader file
    shader_dir = DATA_DIR / "scripts"
    shader_dir.mkdir(parents=True, exist_ok=True)
    shader_file = shader_dir / "displays.shader"

    # Check if shader already exists
    existing_content = ""
    if shader_file.exists():
        existing_content = shader_file.read_text()

    if f"textures/displays/{texture_name}" not in existing_content:
        with open(shader_file, 'a') as f:
            f.write(shader_content)

    # Ensure displays is in shaderlist.txt
    shaderlist = shader_dir / "shaderlist.txt"
    shaderlist_content = ""
    if shaderlist.exists():
        shaderlist_content = shaderlist.read_text()
    if "displays" not in shaderlist_content:
        with open(shaderlist, 'a') as f:
            f.write("displays\n")

    # Generate brush geometry with proper texture offsets
    CAULK = "common/caulk"
    hw = width // 2
    thickness = 4
    scale = 1.0  # 1:1 mapping since texture matches display size
    texture = f"textures/displays/{texture_name}"

    lines = ["{"]

    if direction == "south":
        x1, x2 = cx - hw, cx + hw
        y1, y2 = cy - thickness, cy
        z1, z2 = z_base, z_base + height
        off_x, off_z = -x1, -z1

        lines.append(f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {texture} {off_x} {off_z} 0 {scale} {scale} 0 0 0")
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")

    elif direction == "north":
        x1, x2 = cx - hw, cx + hw
        y1, y2 = cy, cy + thickness
        z1, z2 = z_base, z_base + height
        off_x, off_z = -x1, -z1

        lines.append(f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {texture} {off_x} {off_z} 0 {scale} {scale} 0 0 0")
        lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")

    elif direction == "east":
        x1, x2 = cx, cx + thickness
        y1, y2 = cy - hw, cy + hw
        z1, z2 = z_base, z_base + height
        off_y, off_z = -y1, -z1

        lines.append(f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {texture} {off_y} {off_z} 0 {scale} {scale} 0 0 0")

    elif direction == "west":
        x1, x2 = cx - thickness, cx
        y1, y2 = cy - hw, cy + hw
        z1, z2 = z_base, z_base + height
        off_y, off_z = -y1, -z1

        lines.append(f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {texture} {off_y} {off_z} 0 {scale} {scale} 0 0 0")
        lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {CAULK} 0 0 0 0.25 0.25 0 0 0")

    lines.append("}")
    brush_content = "\n".join(lines)

    # Append to map
    result = append_to_map(map_name, brush_content)

    return f"""Wall display created successfully!
Texture: textures/displays/{texture_name}
Image: {tga_path}
Shader: {shader_file}
Display size: {width}x{height} units
Position: ({cx}, {cy}, {z_base})
Direction: {direction}
{result}"""


@mcp.tool()
def batch_create_displays(
    map_name: str,
    displays: str
) -> str:
    """
    Create multiple wall displays from a JSON specification.

    Args:
        map_name: Name of the map
        displays: JSON array of display specs, each with:
                  - image_path: Path to source image
                  - cx, cy, z_base: Position
                  - width, height: Size (optional, default 256)
                  - direction: "north", "south", "east", "west"
                  - texture_name: Optional custom name

    Example displays JSON:
    [
        {"image_path": "/path/to/img1.png", "cx": 0, "cy": -500, "z_base": 80, "direction": "south"},
        {"image_path": "/path/to/img2.png", "cx": 500, "cy": 0, "z_base": 80, "direction": "east"}
    ]
    """
    try:
        display_list = json.loads(displays)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    results = []
    for i, spec in enumerate(display_list):
        try:
            result = create_wall_display(
                map_name=map_name,
                image_path=spec.get("image_path", ""),
                cx=float(spec.get("cx", 0)),
                cy=float(spec.get("cy", 0)),
                z_base=float(spec.get("z_base", 80)),
                width=int(spec.get("width", 256)),
                height=int(spec.get("height", 256)),
                direction=spec.get("direction", "south"),
                texture_name=spec.get("texture_name", "")
            )
            results.append(f"Display {i+1}: OK")
        except Exception as e:
            results.append(f"Display {i+1}: ERROR - {e}")

    return f"Batch display creation complete:\n" + "\n".join(results)


# =============================================================================
# TEXTURE TOOLS
# =============================================================================

@mcp.tool()
def list_textures(texture_set: str = "trak4x") -> str:
    """
    List available textures from a texture set.

    Args:
        texture_set: Texture set name (trak4x, trak5x, exx, etc.)
    """
    # Search in pk3 files
    import zipfile

    textures = set()
    for pk3 in DATA_DIR.glob("*.pk3"):
        try:
            with zipfile.ZipFile(pk3, 'r') as zf:
                for name in zf.namelist():
                    if f"textures/{texture_set}/" in name and name.endswith(".dds"):
                        # Extract texture path without extension
                        tex_path = name.replace("dds/", "").replace(".dds", "")
                        textures.add(tex_path)
        except Exception:
            continue

    if not textures:
        return f"No textures found for set '{texture_set}'"

    result = f"Textures in {texture_set} ({len(textures)} total):\n"
    for tex in sorted(textures)[:50]:
        result += f"  {tex}\n"

    if len(textures) > 50:
        result += f"  ... and {len(textures) - 50} more"

    return result


@mcp.tool()
def get_valid_texture_sets() -> str:
    """Get a list of all available texture sets in Xonotic."""
    import zipfile

    texture_sets = set()
    for pk3 in DATA_DIR.glob("*.pk3"):
        try:
            with zipfile.ZipFile(pk3, 'r') as zf:
                for name in zf.namelist():
                    if "textures/" in name and ".dds" in name:
                        # Extract texture set name
                        parts = name.split("textures/")
                        if len(parts) > 1:
                            set_name = parts[1].split("/")[0]
                            if set_name and not set_name.endswith(".dds"):
                                texture_sets.add(set_name)
        except Exception:
            continue

    result = "Available texture sets:\n"
    for ts in sorted(texture_sets):
        result += f"  - {ts}\n"

    return result


# =============================================================================
# GAME LAUNCH TOOLS
# =============================================================================

@mcp.tool()
def launch_xonotic(map_name: Optional[str] = None) -> str:
    """
    Launch Xonotic, optionally loading a specific map.

    Args:
        map_name: Optional map name to load immediately
    """
    xonotic_bin = XONOTIC_DIR / "xonotic-linux64-glx"

    if not xonotic_bin.exists():
        return f"Xonotic binary not found at {xonotic_bin}"

    cmd = [str(xonotic_bin)]
    if map_name:
        if map_name.endswith(".map") or map_name.endswith(".bsp"):
            map_name = map_name.rsplit(".", 1)[0]
        cmd.extend(["+map", map_name])

    # Launch in background
    subprocess.Popen(cmd, cwd=XONOTIC_DIR,
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)

    if map_name:
        return f"Launched Xonotic with map: {map_name}"
    else:
        return "Launched Xonotic"


# =============================================================================
# RESOURCE/CONTEXT PROVIDERS
# =============================================================================

@mcp.resource("quake://textures")
def get_texture_reference() -> str:
    """Provides reference for valid Xonotic texture paths."""
    return """# Xonotic Texture Reference

## Common Texture Sets

### trak4x (Industrial/Rust)
- trak4x/base/base_concrete3 - Gray concrete floor
- trak4x/base/base_rust2 - Rusty metal wall
- trak4x/base/base_metal01 - Clean metal

### trak5x (Modern/Clean)
- trak5x/base/base_metal01 - Polished metal
- trak5x/floor/floor_tile01 - Floor tiles

### exx (Sci-Fi)
- exx/wall/wall_bigrib02 - Ribbed wall panels
- exx/floor/floor_clang01 - Metal grate floor
- exx/trim/trim_psimple04 - Trim pieces

### common (Special)
- common/caulk - Invisible (use for hidden faces)
- common/trigger - Trigger volumes
- common/clip - Player clip

## Texture Format in .map Files
```
( x1 y1 z1 ) ( x2 y2 z2 ) ( x3 y3 z3 ) texture offsetX offsetY rotation scaleX scaleY flags contents value
```

Example:
```
( 0 0 0 ) ( 0 1 0 ) ( 1 0 0 ) trak4x/base/base_concrete3 0 0 0 0.25 0.25 0 0 0
```
"""


@mcp.resource("quake://entities")
def get_entity_reference() -> str:
    """Provides reference for Xonotic entity classnames."""
    return """# Xonotic Entity Reference

## Spawn Points
- info_player_deathmatch - DM/TDM spawn
- info_player_team1 - Red team spawn (CTF/TDM)
- info_player_team2 - Blue team spawn (CTF/TDM)

## Weapons
- weapon_shotgun
- weapon_machinegun
- weapon_rocketlauncher
- weapon_grenadelauncher
- weapon_electro
- weapon_crylink
- weapon_nex (sniper)
- weapon_hagar
- weapon_mortar
- weapon_devastator

## Items
- item_health_small (5 HP)
- item_health_medium (25 HP)
- item_health_large (50 HP)
- item_health_mega (100 HP)
- item_armor_small (5 armor)
- item_armor_medium (25 armor)
- item_armor_large (50 armor)
- item_armor_mega (100 armor)

## Powerups
- item_strength (damage multiplier)
- item_shield (damage reduction)
- item_invincible

## Lighting
- light - Point light
  - "light" "300" - brightness
  - "_color" "1 1 1" - RGB color

## Triggers
- trigger_multiple - Repeatable trigger
- trigger_once - Single-use trigger
- trigger_hurt - Damage zone
- trigger_push - Jump pad

## Entity Format
```
{
"classname" "entity_type"
"origin" "x y z"
"angle" "degrees"  // optional
"key" "value"      // additional properties
}
```
"""


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("Starting Quake/Xonotic MCP Server...")
    print(f"Xonotic directory: {XONOTIC_DIR}")
    print(f"Mapping directory: {MAPPING_DIR}")
    print(f"Q3Map2: {Q3MAP2}")
    mcp.run()
