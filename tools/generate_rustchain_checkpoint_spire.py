#!/usr/bin/env python3
"""Generate the RustChain Checkpoint Spire arena bounty assets.

The output is deterministic so reviewers can regenerate the source map,
mapinfo, README/license, and levelshot preview from one command. The compiled
BSP is produced separately with q3map2 from the generated .map file.
"""

from __future__ import annotations

from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
MAP_DIR = ROOT / "pk3_build" / "maps"
NAME = "rustchain_checkpoint_spire"

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
    """Add compact 16-unit steps to the raised checkpoint decks."""
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
    output.append('"message" "RustChain Checkpoint Spire"')
    output.append('"author" "gchahal1982"')
    output.append('"_description" "A cross-flow DM/CA arena around a glowing checkpoint spire and four raised validation decks."')
    output.append('"_lightmapscale" "0.125"')
    output.append('"_ambient" "30"')
    output.append('"music" "sound/music/rustchain/chain_reactor_loop.ogg"')

    half_x = 1152
    half_y = 896
    height = 416
    wall = 64

    # Sealed shell.
    output.append(brush_box(-half_x, -half_y, -wall, half_x, half_y, 0, [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))
    output.append(brush_box(-half_x, -half_y, height, half_x, half_y, height + wall, [CAULK, CEILING, CAULK, CAULK, CAULK, CAULK]))
    output.append(brush_box(-half_x - wall, -half_y, 0, -half_x, half_y, height, WALL))
    output.append(brush_box(half_x, -half_y, 0, half_x + wall, half_y, height, WALL))
    output.append(brush_box(-half_x, half_y, 0, half_x, half_y + wall, height, WALL))
    output.append(brush_box(-half_x, -half_y - wall, 0, half_x, -half_y, height, WALL))

    # Cross lanes and central spire. The center is readable but not a full blocker.
    output.append(brush_box(-352, -352, 0, 352, 352, 32, [FLOOR_ALT, CAULK, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(-96, -96, 32, 96, 96, 176, [GLOW, CAULK, WALL_ACCENT, WALL_ACCENT, WALL_ACCENT, WALL_ACCENT], scale=0.5))
    output.append(brush_box(-48, -48, 176, 48, 48, 288, [GLOW, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))

    # Four checkpoint pylons create cover and line-of-sight breaks.
    for x1, y1, x2, y2 in [
        (-736, -128, -560, 128),
        (560, -128, 736, 128),
        (-144, -704, 144, -528),
        (-144, 528, 144, 704),
    ]:
        output.append(brush_box(x1, y1, 0, x2, y2, 160, [TRIM, CAULK, WALL_ACCENT, WALL_ACCENT, WALL_ACCENT, WALL_ACCENT]))

    # Raised validation decks, one for each route, connected by stairs.
    output.append(brush_box(-704, 544, 96, 704, 832, 128, [FLOOR_ALT, CAULK, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(-704, -832, 96, 704, -544, 128, [FLOOR_ALT, CAULK, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(832, -320, 96, 1088, 320, 128, [FLOOR_ALT, CAULK, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(-1088, -320, 96, -832, 320, 128, [FLOOR_ALT, CAULK, TRIM, TRIM, TRIM, TRIM]))

    add_steps(output, -224, 352, 224, 544, "north")
    add_steps(output, -224, -544, 224, -352, "south")
    add_steps(output, 640, -160, 832, 160, "east")
    add_steps(output, -832, -160, -640, 160, "west")

    # Narrow ledger rails and glow strips sell the blockchain theme while
    # leaving movement lanes clear.
    for x in (-1040, 1040):
        output.append(brush_box(x - 24, -632, 72, x + 24, -392, 224, [GLOW, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))
        output.append(brush_box(x - 24, 392, 72, x + 24, 632, 224, [GLOW, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))
    for y in (-808, 808):
        output.append(brush_box(-600, y - 24, 72, -320, y + 24, 224, [GLOW, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))
        output.append(brush_box(320, y - 24, 72, 600, y + 24, 224, [GLOW, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))

    # Low hash blocks give duel cover without turning the arena into corridors.
    for x, y in [(-448, -416), (448, 416), (-448, 416), (448, -416)]:
        output.append(brush_box(x - 96, y - 64, 0, x + 96, y + 64, 80, [FLOOR_ALT, CAULK, WALL_ACCENT, WALL_ACCENT, WALL_ACCENT, WALL_ACCENT]))

    output.append("}")

    spawns = [
        ("320 -600 40", "120"),
        ("-320 600 40", "300"),
        ("-880 0 40", "0"),
        ("880 0 40", "180"),
        ("-560 -560 40", "45"),
        ("560 -560 40", "135"),
        ("-560 560 40", "315"),
        ("560 560 40", "225"),
        ("-496 696 168", "315"),
        ("496 -696 168", "135"),
        ("-944 -224 168", "20"),
        ("944 224 168", "200"),
    ]
    for origin, angle in spawns:
        output.append(entity("info_player_deathmatch", {"origin": origin, "angle": angle}))

    pickups = [
        ("weapon_devastator", "0 0 312"),
        ("weapon_vortex", "0 696 168"),
        ("weapon_electro", "0 -696 168"),
        ("weapon_hagar", "960 0 168"),
        ("weapon_crylink", "-960 0 168"),
        ("weapon_machinegun", "-464 -416 104"),
        ("weapon_machinegun", "464 416 104"),
        ("weapon_shotgun", "464 -416 104"),
        ("weapon_mortar", "-464 416 104"),
        ("item_armor_large", "-960 256 168"),
        ("item_health_mega", "960 -256 168"),
        ("item_armor_medium", "-336 336 40"),
        ("item_armor_medium", "336 -336 40"),
        ("item_health_large", "-456 0 40"),
        ("item_health_large", "456 0 40"),
        ("item_cells", "-256 256 40"),
        ("item_rockets", "256 -256 40"),
        ("item_bullets", "-256 -256 40"),
        ("item_shells", "256 256 40"),
    ]
    for classname, origin in pickups:
        output.append(entity(classname, {"origin": origin}))

    lights = [
        ("0 0 336", "720", "0.95 0.55 0.18"),
        ("0 0 304", "380", "0.2 0.8 1.0"),
        ("-872 -672 236", "360", "0.3 0.8 1.0"),
        ("872 672 236", "360", "1.0 0.45 0.25"),
        ("-872 672 236", "280", "0.8 0.9 1.0"),
        ("872 -672 236", "280", "1.0 0.75 0.35"),
        ("0 768 260", "240", "0.3 0.9 1.0"),
        ("0 -768 260", "240", "1.0 0.6 0.25"),
    ]
    for origin, value, color in lights:
        output.append(entity("light", {"origin": origin, "light": value, "_color": color}))

    return "\n".join(output) + "\n"


def write_levelshot(path: Path):
    width, height = 512, 384
    pixels = bytearray()

    def color_at(x, y):
        nx = (x - width / 2) / (width / 2)
        ny = (y - height / 2) / (height / 2)
        bg = int(24 + 18 * (1 - min(1, (nx * nx + ny * ny) ** 0.5)))
        r, g, b = bg + 22, bg + 15, bg + 9

        def rect(cx, cy, hw, hh, col):
            if abs(x - cx) <= hw and abs(y - cy) <= hh:
                return col
            return None

        shapes = [
            rect(width // 2, height // 2, 80, 62, (220, 130, 42)),
            rect(width // 2, height // 2, 28, 28, (52, 196, 232)),
            rect(width // 2, 50, 164, 28, (78, 128, 150)),
            rect(width // 2, height - 50, 164, 28, (78, 128, 150)),
            rect(44, height // 2, 28, 104, (78, 128, 150)),
            rect(width - 44, height // 2, 28, 104, (78, 128, 150)),
            rect(120, height // 2, 12, 96, (168, 74, 48)),
            rect(width - 120, height // 2, 12, 96, (168, 74, 48)),
            rect(width // 2, 96, 44, 10, (232, 166, 54)),
            rect(width // 2, height - 96, 44, 10, (232, 166, 54)),
        ]
        for shape in shapes:
            if shape:
                r, g, b = shape
        if x % 32 == 0 or y % 32 == 0:
            r = min(255, r + 22)
            g = min(255, g + 22)
            b = min(255, b + 22)
        return b, g, r

    for y in range(height - 1, -1, -1):
        for x in range(width):
            pixels.extend(color_at(x, y))

    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, width, height, 24, 0)
    path.write_bytes(header + pixels)


def write_assets():
    MAP_DIR.mkdir(parents=True, exist_ok=True)
    (MAP_DIR / f"{NAME}.map").write_text(generate_map_text(), encoding="utf-8")
    (MAP_DIR / f"{NAME}.mapinfo").write_text(
        "\n".join(
            [
                "title RustChain Checkpoint Spire",
                "description Cross-flow RustChain DM/CA arena with a central checkpoint spire, raised validation decks, and aggressive reward-loop sightlines.",
                "author gchahal1982",
                "cdtrack 5",
                "has weapons",
                "gametype dm pointlimit=30 timelimit=15",
                "gametype ca pointlimit=10 timelimit=15 teams=2",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (MAP_DIR / f"{NAME}.README.md").write_text(
        "\n".join(
            [
                "# RustChain Checkpoint Spire",
                "",
                "Original Xonotic RustChain Arena map for bounty #14014:",
                "https://github.com/Scottcjn/rustchain-bounties/issues/14014",
                "",
                "## Package",
                "",
                f"- `{NAME}.map` - source map",
                f"- `{NAME}.bsp` - compiled BSP generated from q3map2",
                f"- `{NAME}.mapinfo` - DM/CA map metadata",
                f"- `{NAME}.tga` - 512x384 levelshot preview",
                f"- `{NAME}.LICENSE` - CC-BY-SA-4.0 license grant",
                "",
                "## Design",
                "",
                "Checkpoint Spire is a compact cross-flow arena built around a glowing central checkpoint",
                "tower, four raised validation decks, stair-fed side routes, and low hash blocks for",
                "duel cover. It is distinct from the existing museum, mempool-vault, and antiquity-vault",
                "layouts: this one emphasizes a central vertical reward pillar with four fast re-entry",
                "routes rather than a vault-room or museum-showcase structure.",
                "",
                "The geometry, levelshot, and metadata are generated deterministically by:",
                "",
                "```bash",
                f"python3 tools/generate_{NAME}.py",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (MAP_DIR / f"{NAME}.LICENSE").write_text(
        "\n".join(
            [
                "RustChain Checkpoint Spire arena map",
                "",
                "Copyright 2026 gchahal1982",
                "",
                "This map source, levelshot, metadata, and generated layout are licensed under",
                "the Creative Commons Attribution-ShareAlike 4.0 International License",
                "(CC-BY-SA-4.0).",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_levelshot(MAP_DIR / f"{NAME}.tga")


if __name__ == "__main__":
    write_assets()
