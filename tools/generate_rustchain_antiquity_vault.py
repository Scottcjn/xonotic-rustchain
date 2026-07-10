#!/usr/bin/env python3
"""Generate the RustChain Antiquity Vault arena map assets.

The bounty requires a source map, mapinfo, levelshot, license/readme, and a
compiled BSP. This generator creates all text/preview assets deterministically;
q3map2 is used separately to compile the BSP from the generated .map.
"""

from __future__ import annotations

from pathlib import Path
import struct


ROOT = Path(__file__).resolve().parents[1]
MAP_DIR = ROOT / "pk3_build" / "maps"
NAME = "rustchain_antiquity_vault"


FLOOR = "trak4x/floor/floor_tile3a"
GRATE = "eX/eX_floor_grate_03_d"
WALL = "eX/eX_wall_panels_08_d"
STONE = "trak4x/wall/wall_brick1"
RUST = "eX/eXmetalBase05Rust_d"
CEILING = "eX/eX_mtl_panel_03_d"
TRIM = "eX/eX_trim_vert_01_d"
LIGHT = "exx/light/light_panel01"
WARNING = "evil8_floor/e8clangfloor04warn"
CAULK = "common/caulk"


def brush_box(x1, y1, z1, x2, y2, z2, textures, scale=0.25):
    """Return one axis-aligned convex brush in q3 .map plane format."""
    if isinstance(textures, str):
        textures = [textures] * 6
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
    if z1 > z2:
        z1, z2 = z2, z1
    s = scale
    return "\n".join([
        "{",
        f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {textures[0]} 0 0 0 {s} {s} 0 0 0",
        f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {textures[1]} 0 0 0 {s} {s} 0 0 0",
        f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {textures[2]} 0 0 0 {s} {s} 0 0 0",
        f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {textures[3]} 0 0 0 {s} {s} 0 0 0",
        f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {textures[4]} 0 0 0 {s} {s} 0 0 0",
        f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {textures[5]} 0 0 0 {s} {s} 0 0 0",
        "}",
    ])


def entity(classname, properties):
    lines = ["{", f'"classname" "{classname}"']
    lines.extend(f'"{key}" "{value}"' for key, value in properties.items())
    lines.append("}")
    return "\n".join(lines)


def add_stairs(out, x1, y1, x2, y2, axis, reverse=False):
    steps = 8
    height = 16
    if axis == "x":
        span = abs(x2 - x1) // steps
        for i in range(steps):
            z = (i + 1) * height
            if reverse:
                xa, xb = x2 - (i + 1) * span, x2 - i * span
            else:
                xa, xb = x1 + i * span, x1 + (i + 1) * span
            out.append(brush_box(xa, y1, 0, xb, y2, z, [WARNING, CAULK, TRIM, TRIM, TRIM, TRIM]))
    else:
        span = abs(y2 - y1) // steps
        for i in range(steps):
            z = (i + 1) * height
            if reverse:
                ya, yb = y2 - (i + 1) * span, y2 - i * span
            else:
                ya, yb = y1 + i * span, y1 + (i + 1) * span
            out.append(brush_box(x1, ya, 0, x2, yb, z, [WARNING, CAULK, TRIM, TRIM, TRIM, TRIM]))


def generate_map_text():
    out = [
        "{",
        '"classname" "worldspawn"',
        '"message" "RustChain Antiquity Vault"',
        '"author" "EldwinMemoryOps"',
        '"_description" "Two-level RustChain arena through a vintage-hardware vault and validator archive."',
        '"_ambient" "30"',
        '"_lightmapscale" "0.125"',
        '"music" "sound/music/rustchain/chain_reactor_loop.ogg"',
    ]

    half_x, half_y, top, wall = 1152, 896, 448, 64

    # Sealed arena shell.
    out.append(brush_box(-half_x, -half_y, -wall, half_x, half_y, 0, [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))
    out.append(brush_box(-half_x, -half_y, top, half_x, half_y, top + wall, [CAULK, CEILING, CAULK, CAULK, CAULK, CAULK]))
    out.append(brush_box(-half_x - wall, -half_y, 0, -half_x, half_y, top, STONE))
    out.append(brush_box(half_x, -half_y, 0, half_x + wall, half_y, top, STONE))
    out.append(brush_box(-half_x, -half_y - wall, 0, half_x, -half_y, top, WALL))
    out.append(brush_box(-half_x, half_y, 0, half_x, half_y + wall, top, WALL))

    # Distinct hourglass center, not a square vault: two ledger bridges cross over
    # a low central reward dais and force multiple attack angles.
    out.append(brush_box(-192, -160, 0, 192, 160, 48, [GRATE, CAULK, RUST, RUST, RUST, RUST]))
    out.append(brush_box(-64, -64, 48, 64, 64, 160, [LIGHT, CAULK, RUST, RUST, RUST, RUST], scale=0.5))
    out.append(brush_box(-960, -96, 128, 960, 96, 160, [GRATE, CAULK, TRIM, TRIM, TRIM, TRIM]))
    out.append(brush_box(-96, -704, 128, 96, 704, 160, [GRATE, CAULK, TRIM, TRIM, TRIM, TRIM]))

    # Four hardware archive alcoves with asymmetric low cover.
    for sx, sy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        out.append(brush_box(sx * 624 - 160, sy * 496 - 128, 0, sx * 624 + 160, sy * 496 + 128, 96, [GRATE, CAULK, TRIM, TRIM, TRIM, TRIM]))
        out.append(brush_box(sx * 624 - 56, sy * 496 - 56, 96, sx * 624 + 56, sy * 496 + 56, 224, [RUST, CAULK, LIGHT, LIGHT, LIGHT, LIGHT], scale=0.5))

    # Low "antique rack" cover that breaks sightlines but leaves clean loops.
    cover = [
        (-824, -176, -568, -96, 112),
        (568, 96, 824, 176, 112),
        (-824, 96, -568, 176, 80),
        (568, -176, 824, -96, 80),
        (-176, -704, -96, -448, 112),
        (96, 448, 176, 704, 112),
        (-176, 448, -96, 704, 80),
        (96, -704, 176, -448, 80),
    ]
    for x1, y1, x2, y2, z2 in cover:
        out.append(brush_box(x1, y1, 0, x2, y2, z2, [TRIM, CAULK, RUST, RUST, RUST, RUST]))

    # Four stair ramps, deliberately offset to make a different flow from the
    # existing mempool-vault PR.
    add_stairs(out, -512, -320, -192, -192, "x")
    add_stairs(out, 192, 192, 512, 320, "x", reverse=True)
    add_stairs(out, -320, 192, -192, 512, "y", reverse=True)
    add_stairs(out, 192, -512, 320, -192, "y")

    # Wall-mounted circuit traces.
    for y in (-848, 848):
        out.append(brush_box(-768, y - 16, 96, -256, y + 16, 224, [LIGHT, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))
        out.append(brush_box(256, y - 16, 96, 768, y + 16, 224, [LIGHT, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))
    for x in (-1104, 1104):
        out.append(brush_box(x - 16, -512, 96, x + 16, -160, 224, [LIGHT, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))
        out.append(brush_box(x - 16, 160, 96, x + 16, 512, 224, [LIGHT, CAULK, TRIM, TRIM, TRIM, TRIM], scale=0.5))

    out.append("}")

    spawns = [
        ("-880 -640 40", "45"),
        ("880 640 40", "225"),
        ("-880 640 40", "315"),
        ("880 -640 40", "135"),
        ("-420 0 40", "0"),
        ("420 0 40", "180"),
        ("0 -420 40", "90"),
        ("0 420 40", "270"),
        ("-760 0 192", "0"),
        ("760 0 192", "180"),
        ("0 -600 192", "90"),
        ("0 600 192", "270"),
    ]
    for origin, angle in spawns:
        out.append(entity("info_player_deathmatch", {"origin": origin, "angle": angle}))

    pickups = [
        ("weapon_devastator", "0 0 184"),
        ("weapon_vortex", "-760 0 192"),
        ("weapon_hagar", "760 0 192"),
        ("weapon_electro", "0 -600 192"),
        ("weapon_crylink", "0 600 192"),
        ("weapon_mortar", "-624 -320 72"),
        ("weapon_machinegun", "624 320 72"),
        ("weapon_shotgun", "624 -320 72"),
        ("item_armor_big", "-624 320 72"),
        ("item_health_mega", "320 -624 72"),
        ("item_armor_medium", "-320 -96 72"),
        ("item_armor_medium", "320 96 72"),
        ("item_health_medium", "-96 320 72"),
        ("item_health_medium", "96 -320 72"),
        ("ammo_rockets", "384 -384 72"),
        ("ammo_cells", "-384 384 72"),
        ("ammo_bullets", "-384 -384 72"),
        ("ammo_shells", "384 384 72"),
    ]
    for classname, origin in pickups:
        out.append(entity(classname, {"origin": origin}))

    lights = [
        ("0 0 360", "760", "1.0 0.62 0.25"),
        ("0 0 220", "360", "0.25 0.8 1.0"),
        ("-900 -660 260", "300", "0.9 0.55 0.25"),
        ("900 660 260", "300", "0.25 0.75 1.0"),
        ("-900 660 260", "260", "0.35 0.9 0.85"),
        ("900 -660 260", "260", "1.0 0.75 0.3"),
        ("0 760 296", "260", "0.8 0.9 1.0"),
        ("0 -760 296", "260", "1.0 0.5 0.25"),
    ]
    for origin, strength, color in lights:
        out.append(entity("light", {"origin": origin, "light": strength, "_color": color}))

    return "\n".join(out) + "\n"


def write_levelshot(path: Path):
    width, height = 512, 384
    pixels = bytearray()

    def maybe_rect(x, y, cx, cy, hw, hh, color):
        return color if abs(x - cx) <= hw and abs(y - cy) <= hh else None

    def color_at(x, y):
        nx = (x - width / 2) / (width / 2)
        ny = (y - height / 2) / (height / 2)
        glow = int(30 * max(0, 1 - (nx * nx + ny * ny) ** 0.5))
        r, g, b = 34 + glow, 38 + glow, 44 + glow

        for rect in [
            (width // 2, height // 2, 42, 34, (220, 126, 44)),
            (width // 2, height // 2, 14, 14, (60, 205, 235)),
            (width // 2, height // 2, 190, 14, (92, 136, 150)),
            (width // 2, height // 2, 14, 138, (92, 136, 150)),
            (112, 86, 42, 30, (142, 82, 54)),
            (400, 86, 42, 30, (142, 82, 54)),
            (112, 298, 42, 30, (142, 82, 54)),
            (400, 298, 42, 30, (142, 82, 54)),
        ]:
            chosen = maybe_rect(x, y, *rect)
            if chosen:
                r, g, b = chosen
        if x % 32 == 0 or y % 32 == 0:
            r, g, b = min(255, r + 22), min(255, g + 22), min(255, b + 22)
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
        "\n".join([
            "title RustChain Antiquity Vault",
            "description Two-level RustChain arena through an antique hardware vault, crossed ledger bridges, and aggressive center reward flow.",
            "author EldwinMemoryOps",
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
            "# RustChain Antiquity Vault",
            "",
            "`rustchain_antiquity_vault` is an original Xonotic/RustChain arena built for the blood-economy mode.",
            "",
            "## Layout",
            "",
            "- Two-level hourglass layout with crossed ledger bridges over a central reward pedestal.",
            "- Four antique hardware archive alcoves, offset stairs, and low rack cover to create distinct routes.",
            "- Twelve spawn points plus DM/CA mapinfo entries, weapons, armor, health, ammo, colored lights, and brush-built RustChain motifs.",
            "- Designed as a different layout from the existing mempool-vault submission.",
            "",
            "## Build",
            "",
            "```bash",
            "q3map2 -game xonotic -fs_basepath <repo-root> -fs_game data -bsp -meta pk3_build/maps/rustchain_antiquity_vault.map",
            "q3map2 -game xonotic -fs_basepath <repo-root> -fs_game data -vis pk3_build/maps/rustchain_antiquity_vault.bsp",
            "q3map2 -game xonotic -fs_basepath <repo-root> -fs_game data -light -fast -patchshadows pk3_build/maps/rustchain_antiquity_vault.bsp",
            "```",
            "",
            "Generated by `tools/generate_rustchain_antiquity_vault.py`.",
            "",
        ]),
        encoding="utf-8",
    )
    (MAP_DIR / f"{NAME}.LICENSE").write_text(
        "\n".join([
            "RustChain Antiquity Vault map assets",
            "",
            "Copyright 2026 EldwinMemoryOps",
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
    write_assets()
    print(f"generated {NAME} assets in {MAP_DIR}")


if __name__ == "__main__":
    main()
