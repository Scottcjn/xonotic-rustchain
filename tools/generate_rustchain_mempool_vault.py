#!/usr/bin/env python3
"""Generate the RustChain Mempool Vault arena bounty assets.

The output is intentionally deterministic so reviewers can regenerate the
source map, mapinfo, README/license, and levelshot preview from one command.
The compiled BSP is produced separately with q3map2 from the generated .map.
"""

from __future__ import annotations

from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
MAP_DIR = ROOT / "pk3_build" / "maps"
NAME = "rustchain_mempool_vault"


FLOOR = "eX/eX_floor_tread_01_d"
FLOOR_ALT = "eX/eX_floor_grate_03_d"
WALL = "eX/eX_wall_panels_08_d"
WALL_ACCENT = "eX/eXmetalBase05Rust_d"
CEILING = "eX/eX_mtl_panel_03_d"
TRIM = "eX/eX_trim_vert_01_d"
WARNING = "evil8_floor/e8clangfloor04warn"
GLOW = "exx/light/light_panel01"
CAULK = "common/caulk"


def brush_box(x1, y1, z1, x2, y2, z2, textures, scale=0.25):
    """Return a sealed axis-aligned brush with NetRadiant/q3map2 winding."""
    if isinstance(textures, str):
        textures = [textures] * 6

    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    if z1 > z2:
        z1, z2 = z2, z1

    s = scale
    lines = ["{"]
    lines.append(f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {textures[0]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {textures[1]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {textures[2]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {textures[3]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {textures[4]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {textures[5]} 0 0 0 {s} {s} 0 0 0")
    lines.append("}")
    return "\n".join(lines)


def entity(classname, properties):
    lines = ["{"]
    lines.append(f'"classname" "{classname}"')
    for key, value in properties.items():
        lines.append(f'"{key}" "{value}"')
    lines.append("}")
    return "\n".join(lines)


def add_steps(output, x1, y1, x2, y2, direction):
    """Add compact 16-unit steps up to a 96-unit catwalk."""
    step_h = 16
    steps = 6
    if direction in {"north", "south"}:
        depth = abs(y2 - y1) // steps
        for i in range(steps):
            z_top = (i + 1) * step_h
            if direction == "north":
                ya = y1 + i * depth
                yb = y1 + (i + 1) * depth
            else:
                ya = y2 - (i + 1) * depth
                yb = y2 - i * depth
            output.append(brush_box(x1, ya, 0, x2, yb, z_top, [WARNING, CAULK, TRIM, TRIM, TRIM, TRIM]))
    else:
        depth = abs(x2 - x1) // steps
        for i in range(steps):
            z_top = (i + 1) * step_h
            if direction == "east":
                xa = x1 + i * depth
                xb = x1 + (i + 1) * depth
            else:
                xa = x2 - (i + 1) * depth
                xb = x2 - i * depth
            output.append(brush_box(xa, y1, 0, xb, y2, z_top, [WARNING, CAULK, TRIM, TRIM, TRIM, TRIM]))


def generate_map_text():
    output = []

    output.append("{")
    output.append('"classname" "worldspawn"')
    output.append('"message" "RustChain Mempool Vault"')
    output.append('"author" "Nomad Codex"')
    output.append('"_description" "A tight vertical DM/CA vault with mempool chokepoints and validator balconies."')
    output.append('"_lightmapscale" "0.125"')
    output.append('"_ambient" "28"')
    output.append('"music" "sound/music/rustchain/chain_reactor_loop.ogg"')

    half_x = 1024
    half_y = 768
    height = 384
    wall = 64

    # Sealed shell.
    output.append(brush_box(-half_x, -half_y, -wall, half_x, half_y, 0, [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))
    output.append(brush_box(-half_x, -half_y, height, half_x, half_y, height + wall, [CAULK, CEILING, CAULK, CAULK, CAULK, CAULK]))
    output.append(brush_box(-half_x - wall, -half_y, 0, -half_x, half_y, height, WALL))
    output.append(brush_box(half_x, -half_y, 0, half_x + wall, half_y, height, WALL))
    output.append(brush_box(-half_x, half_y, 0, half_x, half_y + wall, height, WALL))
    output.append(brush_box(-half_x, -half_y - wall, 0, half_x, -half_y, height, WALL))

    # Central vault and low cover. The layout keeps four clear loops around it.
    output.append(brush_box(-256, -256, 0, 256, 256, 32, [FLOOR_ALT, CAULK, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(-80, -80, 32, 80, 80, 112, [GLOW, CAULK, WALL_ACCENT, WALL_ACCENT, WALL_ACCENT, WALL_ACCENT], scale=0.5))
    for x1, y1, x2, y2 in [
        (-704, -96, -496, 96),
        (496, -96, 704, 96),
        (-128, -624, 128, -432),
        (-128, 432, 128, 624),
    ]:
        output.append(brush_box(x1, y1, 0, x2, y2, 144, [TRIM, CAULK, WALL_ACCENT, WALL_ACCENT, WALL_ACCENT, WALL_ACCENT]))

    # Elevated validator balconies with symmetric stair access.
    output.append(brush_box(-640, 448, 96, 640, 704, 128, [FLOOR_ALT, CAULK, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(-640, -704, 96, 640, -448, 128, [FLOOR_ALT, CAULK, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(736, -288, 96, 960, 288, 128, [FLOOR_ALT, CAULK, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(-960, -288, 96, -736, 288, 128, [FLOOR_ALT, CAULK, TRIM, TRIM, TRIM, TRIM]))

    add_steps(output, -192, 272, 192, 448, "north")
    add_steps(output, -192, -448, 192, -272, "south")
    add_steps(output, 560, -144, 736, 144, "east")
    add_steps(output, -736, -144, -560, 144, "west")

    # Thin visual ledgers on the walls; short enough not to seal paths.
    for x in (-896, 896):
        output.append(brush_box(x - 24, -520, 64, x + 24, -232, 192, [GLOW, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))
        output.append(brush_box(x - 24, 232, 64, x + 24, 520, 192, [GLOW, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))
    for y in (-672, 672):
        output.append(brush_box(-520, y - 24, 64, -232, y + 24, 192, [GLOW, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))
        output.append(brush_box(232, y - 24, 64, 520, y + 24, 192, [GLOW, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))

    output.append("}")

    # Player starts.
    spawns = [
        ("320 -360 40", "120"),
        ("-320 360 40", "300"),
        ("-760 0 40", "0"),
        ("760 0 40", "180"),
        ("-480 -480 40", "45"),
        ("480 -480 40", "135"),
        ("-480 480 40", "315"),
        ("480 480 40", "225"),
        ("-420 584 168", "315"),
        ("420 -584 168", "135"),
    ]
    for origin, angle in spawns:
        output.append(entity("info_player_deathmatch", {"origin": origin, "angle": angle}))

    # Weapons and economy-driving pickups.
    pickups = [
        ("weapon_devastator", "0 0 144"),
        ("weapon_vortex", "0 592 168"),
        ("weapon_electro", "0 -592 168"),
        ("weapon_hagar", "848 0 168"),
        ("weapon_crylink", "-848 0 168"),
        ("weapon_machinegun", "-392 -352 40"),
        ("weapon_machinegun", "392 352 40"),
        ("weapon_shotgun", "392 -352 40"),
        ("weapon_mortar", "-392 352 40"),
        ("item_armor_large", "-848 224 168"),
        ("item_health_mega", "848 -224 168"),
        ("item_armor_medium", "-320 340 40"),
        ("item_armor_medium", "320 -340 40"),
        ("item_health_large", "-360 0 40"),
        ("item_health_large", "360 0 40"),
        ("item_cells", "-220 220 40"),
        ("item_rockets", "220 -220 40"),
        ("item_bullets", "-220 -220 40"),
        ("item_shells", "220 220 40"),
    ]
    for classname, origin in pickups:
        output.append(entity(classname, {"origin": origin}))

    # High/low colored lights create visible vertical reads.
    lights = [
        ("0 0 300", "650", "0.9 0.55 0.2"),
        ("0 0 128", "320", "0.2 0.75 1.0"),
        ("-760 -560 220", "360", "0.3 0.8 1.0"),
        ("760 560 220", "360", "1.0 0.45 0.25"),
        ("-720 560 220", "260", "0.8 0.9 1.0"),
        ("720 -560 220", "260", "1.0 0.75 0.35"),
    ]
    for origin, value, color in lights:
        output.append(entity("light", {"origin": origin, "light": value, "_color": color}))

    return "\n".join(output) + "\n"


def write_levelshot(path: Path):
    width, height = 512, 384
    pixels = bytearray()

    # Draw a simple top-down stylized preview in uncompressed 24-bit TGA.
    def color_at(x, y):
        nx = (x - width / 2) / (width / 2)
        ny = (y - height / 2) / (height / 2)
        bg = int(24 + 18 * (1 - min(1, (nx * nx + ny * ny) ** 0.5)))
        r, g, b = bg + 24, bg + 16, bg + 8

        def rect(cx, cy, hw, hh, col):
            if abs(x - cx) <= hw and abs(y - cy) <= hh:
                return col
            return None

        shapes = [
            rect(width // 2, height // 2, 72, 54, (230, 132, 44)),
            rect(width // 2, height // 2, 24, 18, (58, 190, 230)),
            rect(width // 2, 62, 150, 28, (82, 128, 150)),
            rect(width // 2, height - 62, 150, 28, (82, 128, 150)),
            rect(56, height // 2, 28, 92, (82, 128, 150)),
            rect(width - 56, height // 2, 28, 92, (82, 128, 150)),
            rect(116, height // 2, 12, 84, (162, 72, 48)),
            rect(width - 116, height // 2, 12, 84, (162, 72, 48)),
        ]
        for shape in shapes:
            if shape:
                r, g, b = shape
        grid = (x % 32 == 0) or (y % 32 == 0)
        if grid:
            r = min(255, r + 22)
            g = min(255, g + 22)
            b = min(255, b + 22)
        return b, g, r

    for y in range(height - 1, -1, -1):
        for x in range(width):
            pixels.extend(color_at(x, y))

    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, width, height, 24, 0)
    path.write_bytes(header + pixels)


def write_text_assets():
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    (MAP_DIR / f"{NAME}.map").write_text(generate_map_text(), encoding="utf-8")
    (MAP_DIR / f"{NAME}.mapinfo").write_text(
        "\n".join([
            "title RustChain Mempool Vault",
            "description Tight vertical RustChain DM/CA arena with mempool chokepoints, validator balconies, and aggressive center reward flow.",
            "author Nomad Codex",
            "cdtrack 5",
            "has weapons",
            "gametype dm pointlimit=30 timelimit=15",
            "gametype ca pointlimit=10 timelimit=15 teams=2",
            "",
        ]),
        encoding="utf-8",
    )
    (MAP_DIR / f"{NAME}.README.md").write_text(
        "\n".join([
            "# RustChain Mempool Vault",
            "",
            "`rustchain_mempool_vault` is a compact vertical Xonotic/RustChain arena built for the blood-economy mode.",
            "",
            "## Layout",
            "",
            "- Sealed single-vault layout with four ground loops around a central reward pedestal.",
            "- Four elevated validator balconies reached by 16-unit steps for safe Xonotic movement.",
            "- Low mempool chokepoints break sightlines without creating dead ends.",
            "- DM and CA mapinfo entries, 10 spawn points, weapons, armor, health, ammo, colored lighting, and brush-built RustChain set pieces.",
            "",
            "## Build",
            "",
            "```bash",
            "q3map2 -game xonotic -fs_basepath <repo-root> pk3_build/maps/rustchain_mempool_vault.map",
            "q3map2 -game xonotic -fs_basepath <repo-root> -vis -saveprt pk3_build/maps/rustchain_mempool_vault.map",
            "q3map2 -game xonotic -fs_basepath <repo-root> -light -fast -patchshadows pk3_build/maps/rustchain_mempool_vault.map",
            "```",
            "",
            "Generated by `tools/generate_rustchain_mempool_vault.py`.",
            "",
        ]),
        encoding="utf-8",
    )
    (MAP_DIR / f"{NAME}.LICENSE").write_text(
        "\n".join([
            "RustChain Mempool Vault map assets",
            "",
            "Copyright 2026 Nomad Codex",
            "",
            "Licensed under Creative Commons Attribution-ShareAlike 4.0 International",
            "(CC-BY-SA-4.0), compatible with the bounty requirement for map content.",
            "The generated source map may also be redistributed with the Xonotic",
            "RustChain package under GPL-compatible project terms where required.",
            "",
        ]),
        encoding="utf-8",
    )
    write_levelshot(MAP_DIR / f"{NAME}.tga")


def main():
    write_text_assets()
    print(f"generated {NAME} assets in {MAP_DIR}")


if __name__ == "__main__":
    main()
