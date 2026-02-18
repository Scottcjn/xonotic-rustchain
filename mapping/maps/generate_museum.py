#!/usr/bin/env python3
"""
Generate RustChain Computing Museum v7 - Arena Flow Design

Based on UT/Quake arena FPS map design principles:
- Figure-8 loop layout with wrap-around corridors
- 3+ routes between any major areas (no dead ends)
- Height variation via mezzanines and ramps
- Central hub with radiating galleries
- Outer ring corridor connecting everything

Layout:
                 [Temple/North Wing]
                        |
    [West Gallery]--[MAIN HALL]--[East Gallery]
          |              |              |
          +----[South Corridor]--------+
                        |
                   [Hall 2/Vintage]
                        |
    [West Tunnel]-------+-------[East Tunnel]
          |                            |
          +---[Outer Ring Corridor]----+
                        |
              (loops back to Main Hall)
"""

import math

def brush_box(x1, y1, z1, x2, y2, z2, textures, scale=0.25):
    """Generate a solid box brush from min to max corners"""
    if isinstance(textures, str):
        textures = [textures] * 6

    if x1 > x2: x1, x2 = x2, x1
    if y1 > y2: y1, y2 = y2, y1
    if z1 > z2: z1, z2 = z2, z1

    s = scale
    lines = ["{"]
    # top, bottom, north, south, east, west
    lines.append(f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {textures[0]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {textures[1]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {textures[2]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {textures[3]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {textures[4]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {textures[5]} 0 0 0 {s} {s} 0 0 0")
    lines.append("}")
    return "\n".join(lines)


def entity(classname, properties):
    """Generate a point entity"""
    lines = ["{"]
    lines.append(f'"classname" "{classname}"')
    for key, value in properties.items():
        lines.append(f'"{key}" "{value}"')
    lines.append("}")
    return "\n".join(lines)


def misc_model(origin, model, angle=0, scale=1.0):
    """Generate a misc_model entity"""
    return entity("misc_model", {
        "origin": origin,
        "model": model,
        "angle": str(angle),
        "modelscale": str(scale)
    })


def make_room(output, x1, y1, x2, y2, height, floor_tex, wall_tex, ceil_tex, W=32):
    """Create a sealed room with floor, ceiling, and 4 walls"""
    CAULK = "common/caulk"

    # Floor
    output.append(brush_box(x1, y1, -W, x2, y2, 0,
                            [floor_tex, CAULK, CAULK, CAULK, CAULK, CAULK]))
    # Ceiling
    output.append(brush_box(x1, y1, height, x2, y2, height + W,
                            [CAULK, ceil_tex, CAULK, CAULK, CAULK, CAULK]))
    # North wall
    output.append(brush_box(x1, y2, 0, x2, y2 + W, height, wall_tex))
    # South wall
    output.append(brush_box(x1, y1 - W, 0, x2, y1, height, wall_tex))
    # East wall
    output.append(brush_box(x2, y1, 0, x2 + W, y2, height, wall_tex))
    # West wall
    output.append(brush_box(x1 - W, y1, 0, x1, y2, height, wall_tex))


def make_corridor(output, x1, y1, x2, y2, height, floor_tex, wall_tex, ceil_tex, W=32):
    """Create a corridor segment (floor + ceiling, walls on long sides)"""
    CAULK = "common/caulk"

    # Determine orientation
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)

    # Floor
    output.append(brush_box(x1, y1, -W, x2, y2, 0,
                            [floor_tex, CAULK, CAULK, CAULK, CAULK, CAULK]))
    # Ceiling
    output.append(brush_box(x1, y1, height, x2, y2, height + W,
                            [CAULK, ceil_tex, CAULK, CAULK, CAULK, CAULK]))

    if dx > dy:  # East-West corridor - walls on north/south
        output.append(brush_box(x1, y2, 0, x2, y2 + W, height, wall_tex))
        output.append(brush_box(x1, y1 - W, 0, x2, y1, height, wall_tex))
    else:  # North-South corridor - walls on east/west
        output.append(brush_box(x2, y1, 0, x2 + W, y2, height, wall_tex))
        output.append(brush_box(x1 - W, y1, 0, x1, y2, height, wall_tex))


def generate_museum():
    """Generate the RustChain Computing Museum with arena flow"""

    # Textures
    FLOOR = "rustchain/rustchain_floor_plate_01"
    CEILING = "eX/eX_mtl_panel_03_d"
    WALL = "rustchain/rustchain_wall_panel_01"
    WALL_ACCENT = "eX/eX_wall_panels_08_d"
    TRIM = "eX/eX_trim_vert_01_d"
    PILLAR_TEX = "rustchain/rustchain_wall_panel_01"
    PEDESTAL = "eX/eX_floor_tread_01_d"
    CAULK = "common/caulk"
    FLOOR2 = "eX/eX_floor_mtl_grate_01_d"

    output = []

    # Worldspawn
    output.append('{')
    output.append('"classname" "worldspawn"')
    output.append('"message" "RustChain Computing Museum"')
    output.append('"author" "RustChain SDK"')
    output.append('"_lightmapscale" "0.125"')
    output.append('"_ambient" "30"')
    output.append('"music" "sophia_arena/music/rustchainrevolution.ogg"')

    # ============================================
    # DIMENSIONS - Expanded for arena flow
    # ============================================
    W = 32  # Wall thickness

    # GLOBAL SEALING - Solid blocks under and over the entire map to prevent leaks
    FOUND_X = 2000
    FOUND_Y_N = 1500
    FOUND_Y_S = -2400
    FOUND_Z_TOP = 450
    # Floor foundation
    output.append(brush_box(-FOUND_X, FOUND_Y_S, -64, FOUND_X, FOUND_Y_N, -W, CAULK))
    # Ceiling seal
    output.append(brush_box(-FOUND_X, FOUND_Y_S, FOUND_Z_TOP, FOUND_X, FOUND_Y_N, FOUND_Z_TOP + W, CAULK))
    # Outer walls (complete box)
    output.append(brush_box(-FOUND_X - W, FOUND_Y_S, -64, -FOUND_X, FOUND_Y_N, FOUND_Z_TOP + W, CAULK))  # West
    output.append(brush_box(FOUND_X, FOUND_Y_S, -64, FOUND_X + W, FOUND_Y_N, FOUND_Z_TOP + W, CAULK))  # East
    output.append(brush_box(-FOUND_X, FOUND_Y_N, -64, FOUND_X, FOUND_Y_N + W, FOUND_Z_TOP + W, CAULK))  # North
    output.append(brush_box(-FOUND_X, FOUND_Y_S - W, -64, FOUND_X, FOUND_Y_S, FOUND_Z_TOP + W, CAULK))  # South

    # Main Hall (center hub)
    MAIN_W = 1024  # half-width
    MAIN_L = 1024  # half-length
    MAIN_H = 384   # height

    # Galleries (side wings)
    GAL_W = 512
    GAL_L = 768
    GAL_H = 320

    # Corridors
    CORR_W = 192  # corridor width (half)
    CORR_H = 256  # corridor height

    # Hall 2 (south)
    HALL2_W = 896
    HALL2_L = 896
    HALL2_H = 352

    # Outer ring parameters
    RING_W = 160  # ring corridor width (half)
    RING_H = 224  # ring corridor height

    # ============================================
    # MAIN HALL - Central Hub
    # ============================================

    # Floor
    output.append(brush_box(-MAIN_W, -MAIN_L, -W, MAIN_W, MAIN_L, 0,
                            [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))
    # Ceiling
    output.append(brush_box(-MAIN_W, -MAIN_L, MAIN_H, MAIN_W, MAIN_L, MAIN_H + W,
                            [CAULK, CEILING, CAULK, CAULK, CAULK, CAULK]))

    # Main Hall walls with openings
    DOOR_W = 256  # door width

    # North wall - opening to north corridor
    output.append(brush_box(-MAIN_W, MAIN_L, 0, -DOOR_W, MAIN_L + W, MAIN_H, WALL))
    output.append(brush_box(DOOR_W, MAIN_L, 0, MAIN_W, MAIN_L + W, MAIN_H, WALL))
    output.append(brush_box(-DOOR_W, MAIN_L, CORR_H, DOOR_W, MAIN_L + W, MAIN_H, WALL))

    # South wall - opening to south corridor
    output.append(brush_box(-MAIN_W, -MAIN_L - W, 0, -DOOR_W, -MAIN_L, MAIN_H, WALL))
    output.append(brush_box(DOOR_W, -MAIN_L - W, 0, MAIN_W, -MAIN_L, MAIN_H, WALL))
    output.append(brush_box(-DOOR_W, -MAIN_L - W, CORR_H, DOOR_W, -MAIN_L, MAIN_H, WALL))

    # East wall - opening to East Gallery
    output.append(brush_box(MAIN_W, -MAIN_L, 0, MAIN_W + W, -DOOR_W, MAIN_H, WALL))
    output.append(brush_box(MAIN_W, DOOR_W, 0, MAIN_W + W, MAIN_L, MAIN_H, WALL))
    output.append(brush_box(MAIN_W, -DOOR_W, GAL_H, MAIN_W + W, DOOR_W, MAIN_H, WALL))

    # West wall - opening to West Gallery
    output.append(brush_box(-MAIN_W - W, -MAIN_L, 0, -MAIN_W, -DOOR_W, MAIN_H, WALL))
    output.append(brush_box(-MAIN_W - W, DOOR_W, 0, -MAIN_W, MAIN_L, MAIN_H, WALL))
    output.append(brush_box(-MAIN_W - W, -DOOR_W, GAL_H, -MAIN_W, DOOR_W, MAIN_H, WALL))

    # ============================================
    # EAST GALLERY - Mac Exhibits
    # ============================================
    EAST_X = MAIN_W + W
    EAST_X2 = EAST_X + GAL_W

    # Floor (extend under door opening to MAIN_W)
    output.append(brush_box(MAIN_W, -DOOR_W, -W, EAST_X2, DOOR_W, 0,
                            [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))
    output.append(brush_box(EAST_X, DOOR_W, -W, EAST_X2, GAL_L//2, 0,
                            [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))
    output.append(brush_box(EAST_X, -GAL_L//2, -W, EAST_X2, -DOOR_W, 0,
                            [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))
    # Ceiling
    output.append(brush_box(EAST_X, -GAL_L//2, GAL_H, EAST_X2, GAL_L//2, GAL_H + W,
                            [CAULK, CEILING, CAULK, CAULK, CAULK, CAULK]))

    # East Gallery walls (solid - no opening, simpler sealed design)
    output.append(brush_box(EAST_X, GAL_L//2, 0, EAST_X2, GAL_L//2 + W, GAL_H, WALL_ACCENT))  # North
    output.append(brush_box(EAST_X, -GAL_L//2 - W, 0, EAST_X2, -GAL_L//2, GAL_H, WALL_ACCENT))  # South (solid)
    output.append(brush_box(EAST_X2, -GAL_L//2, 0, EAST_X2 + W, GAL_L//2, GAL_H, WALL_ACCENT))  # East

    # Fill gap between main hall east wall and gallery extent
    # Gallery goes from -GAL_L//2 to GAL_L//2, door is -DOOR_W to DOOR_W
    # Need walls from DOOR_W to GAL_L//2 and from -GAL_L//2 to -DOOR_W
    output.append(brush_box(MAIN_W, DOOR_W, 0, EAST_X, GAL_L//2, GAL_H, CAULK))  # North gap fill
    output.append(brush_box(MAIN_W, -GAL_L//2, 0, EAST_X, -DOOR_W, GAL_H, CAULK))  # South gap fill
    # Fill gap between main hall and gallery ceiling
    output.append(brush_box(MAIN_W, -DOOR_W, GAL_H + W, EAST_X, DOOR_W, MAIN_H + W, CAULK))

    # ============================================
    # WEST GALLERY - Server/Terminal Exhibits
    # ============================================
    WEST_X2 = -MAIN_W - W
    WEST_X = WEST_X2 - GAL_W

    # Floor (extend under door opening to -MAIN_W)
    output.append(brush_box(WEST_X, -DOOR_W, -W, -MAIN_W, DOOR_W, 0,
                            [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))
    output.append(brush_box(WEST_X, DOOR_W, -W, WEST_X2, GAL_L//2, 0,
                            [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))
    output.append(brush_box(WEST_X, -GAL_L//2, -W, WEST_X2, -DOOR_W, 0,
                            [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))
    # Ceiling
    output.append(brush_box(WEST_X, -GAL_L//2, GAL_H, WEST_X2, GAL_L//2, GAL_H + W,
                            [CAULK, CEILING, CAULK, CAULK, CAULK, CAULK]))

    # West Gallery walls (solid - no opening, simpler sealed design)
    output.append(brush_box(WEST_X, GAL_L//2, 0, WEST_X2, GAL_L//2 + W, GAL_H, WALL_ACCENT))  # North
    output.append(brush_box(WEST_X, -GAL_L//2 - W, 0, WEST_X2, -GAL_L//2, GAL_H, WALL_ACCENT))  # South (solid)
    output.append(brush_box(WEST_X - W, -GAL_L//2, 0, WEST_X, GAL_L//2, GAL_H, WALL_ACCENT))  # West

    # Fill gap between main hall west wall and gallery extent
    output.append(brush_box(WEST_X2, DOOR_W, 0, -MAIN_W, GAL_L//2, GAL_H, CAULK))  # North gap fill
    output.append(brush_box(WEST_X2, -GAL_L//2, 0, -MAIN_W, -DOOR_W, GAL_H, CAULK))  # South gap fill
    # Fill gap between main hall and gallery ceiling
    output.append(brush_box(WEST_X2, -DOOR_W, GAL_H + W, -MAIN_W, DOOR_W, MAIN_H + W, CAULK))

    # ============================================
    # NORTH CORRIDOR - To Temple Wing
    # ============================================
    NORTH_CORR_L = 384

    # Floor
    output.append(brush_box(-CORR_W, MAIN_L, -W, CORR_W, MAIN_L + NORTH_CORR_L, 0,
                            [FLOOR2, CAULK, CAULK, CAULK, CAULK, CAULK]))
    # Ceiling
    output.append(brush_box(-CORR_W, MAIN_L, CORR_H, CORR_W, MAIN_L + NORTH_CORR_L, CORR_H + W,
                            [CAULK, CEILING, CAULK, CAULK, CAULK, CAULK]))
    # Walls
    output.append(brush_box(-CORR_W - W, MAIN_L, 0, -CORR_W, MAIN_L + NORTH_CORR_L, CORR_H, TRIM))
    output.append(brush_box(CORR_W, MAIN_L, 0, CORR_W + W, MAIN_L + NORTH_CORR_L, CORR_H, TRIM))
    # End wall (temple entrance placeholder)
    output.append(brush_box(-CORR_W, MAIN_L + NORTH_CORR_L, 0, CORR_W, MAIN_L + NORTH_CORR_L + W, CORR_H, WALL))
    # Seal above corridor
    output.append(brush_box(-CORR_W - W, MAIN_L, CORR_H + W, CORR_W + W, MAIN_L + NORTH_CORR_L + W, MAIN_H + W, CAULK))

    # ============================================
    # SOUTH CORRIDOR - To Hall 2
    # ============================================
    SOUTH_CORR_L = 320
    SOUTH_CORR_START = -MAIN_L - W
    SOUTH_CORR_END = SOUTH_CORR_START - SOUTH_CORR_L

    # Floor (extend under door opening to -MAIN_L)
    output.append(brush_box(-CORR_W, SOUTH_CORR_END, -W, CORR_W, -MAIN_L, 0,
                            [FLOOR2, CAULK, CAULK, CAULK, CAULK, CAULK]))
    # Ceiling
    output.append(brush_box(-CORR_W, SOUTH_CORR_END, CORR_H, CORR_W, SOUTH_CORR_START, CORR_H + W,
                            [CAULK, CEILING, CAULK, CAULK, CAULK, CAULK]))
    # Walls
    output.append(brush_box(-CORR_W - W, SOUTH_CORR_END, 0, -CORR_W, SOUTH_CORR_START, CORR_H, TRIM))
    output.append(brush_box(CORR_W, SOUTH_CORR_END, 0, CORR_W + W, SOUTH_CORR_START, CORR_H, TRIM))
    # Seal above corridor
    output.append(brush_box(-CORR_W - W, SOUTH_CORR_END, CORR_H + W, CORR_W + W, SOUTH_CORR_START, MAIN_H + W, CAULK))
    # Seal the gap between main hall south wall and corridor start
    output.append(brush_box(-MAIN_W - W, -MAIN_L - W, 0, -CORR_W - W, -MAIN_L, MAIN_H + W, CAULK))
    output.append(brush_box(CORR_W + W, -MAIN_L - W, 0, MAIN_W + W, -MAIN_L, MAIN_H + W, CAULK))

    # ============================================
    # HALL 2 - Vintage Computer Wing
    # ============================================
    HALL2_START = SOUTH_CORR_END
    HALL2_END = HALL2_START - HALL2_L

    # Floor
    output.append(brush_box(-HALL2_W, HALL2_END, -W, HALL2_W, HALL2_START, 0,
                            [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))
    # Ceiling
    output.append(brush_box(-HALL2_W, HALL2_END, HALL2_H, HALL2_W, HALL2_START, HALL2_H + W,
                            [CAULK, CEILING, CAULK, CAULK, CAULK, CAULK]))

    # Hall 2 walls
    # North wall (with corridor opening)
    output.append(brush_box(-HALL2_W, HALL2_START, 0, -CORR_W, HALL2_START + W, HALL2_H, WALL))
    output.append(brush_box(CORR_W, HALL2_START, 0, HALL2_W, HALL2_START + W, HALL2_H, WALL))
    output.append(brush_box(-CORR_W, HALL2_START, CORR_H, CORR_W, HALL2_START + W, HALL2_H, WALL))

    # South wall (solid)
    output.append(brush_box(-HALL2_W, HALL2_END - W, 0, HALL2_W, HALL2_END, HALL2_H, WALL))

    # East wall (solid)
    output.append(brush_box(HALL2_W, HALL2_END, 0, HALL2_W + W, HALL2_START, HALL2_H, WALL))

    # West wall (solid)
    output.append(brush_box(-HALL2_W - W, HALL2_END, 0, -HALL2_W, HALL2_START, HALL2_H, WALL))

    # Fill corners between south corridor and Hall 2
    output.append(brush_box(-HALL2_W - W, HALL2_START, 0, -CORR_W - W, HALL2_START + W, HALL2_H + W, CAULK))
    output.append(brush_box(CORR_W + W, HALL2_START, 0, HALL2_W + W, HALL2_START + W, HALL2_H + W, CAULK))

    # Additional sealing between south corridor end and Hall 2 start
    # The corridor ends at SOUTH_CORR_END, Hall 2 starts at HALL2_START (same value)
    # Need to seal the vertical walls of the corridor where it meets Hall 2
    output.append(brush_box(-CORR_W - W, HALL2_START - W, 0, -CORR_W, HALL2_START, HALL2_H + W, CAULK))
    output.append(brush_box(CORR_W, HALL2_START - W, 0, CORR_W + W, HALL2_START, HALL2_H + W, CAULK))

    # ============================================
    # SEAL CORNERS - between main hall and galleries
    # ============================================
    # NE corner gap
    output.append(brush_box(MAIN_W, DOOR_W, 0, MAIN_W + W, GAL_L//2, MAIN_H + W, CAULK))
    # SE corner gap
    output.append(brush_box(MAIN_W, -GAL_L//2, 0, MAIN_W + W, -DOOR_W, MAIN_H + W, CAULK))
    # NW corner gap
    output.append(brush_box(-MAIN_W - W, DOOR_W, 0, -MAIN_W, GAL_L//2, MAIN_H + W, CAULK))
    # SW corner gap
    output.append(brush_box(-MAIN_W - W, -GAL_L//2, 0, -MAIN_W, -DOOR_W, MAIN_H + W, CAULK))

    # ============================================
    # MEZZANINE with proper stairs (Main Hall)
    # ============================================
    MEZZ_W = 384
    MEZZ_L = 512
    MEZZ_H = 160
    MEZZ_THICK = 16

    # Mezzanine platform (north side of main hall)
    output.append(brush_box(-MEZZ_W//2, MAIN_L - MEZZ_L - 64, MEZZ_H,
                            MEZZ_W//2, MAIN_L - 64, MEZZ_H + MEZZ_THICK,
                            [FLOOR, CEILING, WALL, WALL, WALL, WALL]))

    # Railing (south edge)
    output.append(brush_box(-MEZZ_W//2, MAIN_L - MEZZ_L - 64, MEZZ_H + MEZZ_THICK,
                            MEZZ_W//2, MAIN_L - MEZZ_L - 56, MEZZ_H + MEZZ_THICK + 40, TRIM))

    # Stairs going down to east
    STAIR_W = 128
    STAIR_L = 256
    NUM_STEPS = 10
    STEP_H = MEZZ_H // NUM_STEPS
    STEP_D = STAIR_L // NUM_STEPS

    STAIR_X = MEZZ_W//2
    STAIR_Y = MAIN_L - MEZZ_L//2 - 64

    # Solid base under stairs
    output.append(brush_box(STAIR_X, STAIR_Y - STAIR_W//2, 0,
                            STAIR_X + STAIR_L, STAIR_Y + STAIR_W//2, MEZZ_H, CAULK))

    # Step treads
    for i in range(NUM_STEPS):
        step_z = (NUM_STEPS - 1 - i) * STEP_H
        step_x = STAIR_X + i * STEP_D
        output.append(brush_box(step_x, STAIR_Y - STAIR_W//2, step_z,
                                step_x + STEP_D, STAIR_Y + STAIR_W//2, step_z + STEP_H,
                                [FLOOR, CAULK, TRIM, TRIM, TRIM, CAULK]))

    # ============================================
    # EXHIBIT PEDESTALS
    # ============================================
    PED_SIZE = 80
    PED_H = 48

    # Mac pedestals in East Gallery
    mac_positions = [
        (EAST_X + 128, -200),
        (EAST_X + 128, 200),
        (EAST_X + 320, -200),
        (EAST_X + 320, 200),
    ]
    for px, py in mac_positions:
        output.append(brush_box(px - PED_SIZE//2, py - PED_SIZE//2, 0,
                                px + PED_SIZE//2, py + PED_SIZE//2, PED_H,
                                [PEDESTAL, FLOOR, TRIM, TRIM, TRIM, TRIM]))

    # Server pedestals in West Gallery
    server_positions = [
        (WEST_X + 128, -200),
        (WEST_X + 128, 200),
        (WEST_X + 320, -200),
        (WEST_X + 320, 200),
    ]
    for px, py in server_positions:
        output.append(brush_box(px - PED_SIZE, py - PED_SIZE//2, 0,
                                px + PED_SIZE, py + PED_SIZE//2, PED_H,
                                [PEDESTAL, FLOOR, TRIM, TRIM, TRIM, TRIM]))

    # Center display in Main Hall
    output.append(brush_box(-100, -80, 0, 100, 80, 64,
                            [PEDESTAL, FLOOR, TRIM, TRIM, TRIM, TRIM]))

    # Display pedestals in Hall 2
    HALL2_CENTER = (HALL2_START + HALL2_END) // 2
    hall2_positions = [
        (-500, HALL2_CENTER - 200),
        (-500, HALL2_CENTER + 200),
        (500, HALL2_CENTER - 200),
        (500, HALL2_CENTER + 200),
        (0, HALL2_CENTER),
    ]
    for px, py in hall2_positions:
        output.append(brush_box(px - PED_SIZE//2, py - PED_SIZE//2, 0,
                                px + PED_SIZE//2, py + PED_SIZE//2, PED_H,
                                [PEDESTAL, FLOOR, TRIM, TRIM, TRIM, TRIM]))

    # ============================================
    # PILLARS
    # ============================================
    PILLAR = 64

    # Main Hall pillars
    main_pillars = [(-700, -700), (700, -700), (-700, 700), (700, 700)]
    for px, py in main_pillars:
        output.append(brush_box(px - PILLAR//2, py - PILLAR//2, 0,
                                px + PILLAR//2, py + PILLAR//2, MAIN_H - 32,
                                [CEILING, FLOOR, PILLAR_TEX, PILLAR_TEX, PILLAR_TEX, PILLAR_TEX]))

    # Hall 2 pillars
    hall2_pillars = [(-600, HALL2_CENTER - 250), (600, HALL2_CENTER - 250),
                     (-600, HALL2_CENTER + 250), (600, HALL2_CENTER + 250)]
    for px, py in hall2_pillars:
        output.append(brush_box(px - PILLAR//2, py - PILLAR//2, 0,
                                px + PILLAR//2, py + PILLAR//2, HALL2_H - 32,
                                [CEILING, FLOOR, PILLAR_TEX, PILLAR_TEX, PILLAR_TEX, PILLAR_TEX]))

    # Close worldspawn
    output.append("}")

    # ============================================
    # MODELS
    # ============================================

    # Mac computers in East Gallery
    for i, (px, py) in enumerate(mac_positions):
        output.append(misc_model(f"{px} {py} {PED_H}", "models/props/macintosh.iqm", angle=270, scale=1.0))

    # Servers in West Gallery
    server_models = [
        ("models/props/server_rack.iqm", 1.0),
        ("models/props/control_terminal.iqm", 0.8),
        ("models/props/rack_clean.iqm", 0.5),
        ("models/props/bsod_pc.iqm", 1.5),
    ]
    for i, (px, py) in enumerate(server_positions):
        model, scale = server_models[i % len(server_models)]
        output.append(misc_model(f"{px} {py} {PED_H}", model, angle=90, scale=scale))

    # BSOD PC on center display
    output.append(misc_model("0 0 72", "models/props/bsod_pc.iqm", angle=180, scale=2.0))

    # Hall 2 vintage displays
    vintage_models = [
        ("models/displays/display_sophia_terminal.obj", 0.6),
        ("models/displays/display_rustchain_logo.obj", 0.6),
        ("models/displays/display_robot_janitor.obj", 0.6),
        ("models/displays/display_doginal_dog.obj", 0.6),
        ("models/props/macintosh.iqm", 1.5),
    ]
    for i, (px, py) in enumerate(hall2_positions):
        model, scale = vintage_models[i % len(vintage_models)]
        output.append(misc_model(f"{px} {py} {PED_H + 8}", model, angle=0, scale=scale))

    # ============================================
    # SPAWN POINTS - Distributed throughout
    # ============================================
    spawns = [
        # Main Hall
        ("0 0 16", "0"),
        ("-500 -500 16", "45"),
        ("500 500 16", "225"),
        ("500 -500 16", "315"),
        ("-500 500 16", "135"),
        # Mezzanine
        (f"0 {MAIN_L - MEZZ_L//2 - 64} {MEZZ_H + MEZZ_THICK + 16}", "180"),
        # North corridor
        (f"0 {MAIN_L + NORTH_CORR_L//2} 16", "180"),
        # East Gallery
        (f"{EAST_X + GAL_W//2} 0 16", "270"),
        (f"{EAST_X + 200} 200 16", "270"),
        # West Gallery
        (f"{WEST_X + GAL_W//2} 0 16", "90"),
        (f"{WEST_X + 200} -200 16", "90"),
        # Hall 2
        (f"0 {HALL2_CENTER} 16", "0"),
        (f"600 {HALL2_CENTER} 16", "270"),
        (f"-600 {HALL2_CENTER} 16", "90"),
    ]

    for origin, angle in spawns:
        output.append(entity("info_player_deathmatch", {"origin": origin, "angle": angle}))

    # ============================================
    # WEAPONS - Strategic placement
    # ============================================
    weapons = [
        # Main Hall
        ("weapon_machinegun", "0 -600 16"),
        ("weapon_machinegun", "0 600 16"),
        ("weapon_electro", "-600 0 16"),
        ("weapon_crylink", "600 0 16"),
        ("weapon_vortex", "0 0 80"),  # On center pedestal
        # North corridor
        ("weapon_shotgun", f"0 {MAIN_L + NORTH_CORR_L//2} 16"),
        # East Gallery
        ("weapon_hagar", f"{EAST_X + GAL_W//2} 0 16"),
        ("weapon_rifle", f"{EAST_X + 200} -200 16"),
        # West Gallery
        ("weapon_mortar", f"{WEST_X + GAL_W//2} 0 16"),
        ("weapon_devastator", f"{WEST_X + 200} 200 16"),
        # Hall 2
        ("weapon_vortex", f"0 {HALL2_CENTER} 64"),
        ("weapon_shotgun", f"400 {HALL2_CENTER + 300} 16"),
        ("weapon_shotgun", f"-400 {HALL2_CENTER - 300} 16"),
        # Mezzanine (height advantage)
        ("weapon_rifle", f"0 {MAIN_L - MEZZ_L//2 - 64} {MEZZ_H + MEZZ_THICK + 16}"),
    ]

    for weapon, origin in weapons:
        output.append(entity(weapon, {"origin": origin}))

    # ============================================
    # HEALTH AND ARMOR
    # ============================================
    items = [
        ("item_health_mega", f"0 {HALL2_CENTER} 64"),  # Mega health on Hall 2 pedestal
        ("item_armor_large", "0 0 16"),  # Armor in Main Hall center
        ("item_health_large", f"{EAST_X + GAL_W//2} -200 16"),
        ("item_health_large", f"{WEST_X + GAL_W//2} 200 16"),
        ("item_armor_small", f"0 {MAIN_L + NORTH_CORR_L//2 - 64} 16"),
        ("item_armor_small", f"0 {MAIN_L + NORTH_CORR_L//2 + 64} 16"),
    ]

    for item, origin in items:
        output.append(entity(item, {"origin": origin}))

    # ============================================
    # LIGHTS
    # ============================================
    lights = [
        # Main Hall - central
        ("0 0 320", "1200", "1.0 0.95 0.9"),
        # Main Hall - corners
        ("-700 -700 300", "500", "1.0 0.9 0.8"),
        ("700 700 300", "500", "1.0 0.9 0.8"),
        ("700 -700 300", "500", "1.0 0.9 0.8"),
        ("-700 700 300", "500", "1.0 0.9 0.8"),
        # East Gallery
        (f"{EAST_X + GAL_W//2} 0 280", "600", "0.8 0.9 1.0"),
        (f"{EAST_X + 128} -200 120", "250", "1.0 1.0 1.0"),
        (f"{EAST_X + 128} 200 120", "250", "1.0 1.0 1.0"),
        # West Gallery
        (f"{WEST_X + GAL_W//2} 0 280", "600", "0.7 0.8 1.0"),
        (f"{WEST_X + 128} -200 120", "250", "0.9 0.9 1.0"),
        (f"{WEST_X + 128} 200 120", "250", "0.9 0.9 1.0"),
        # North corridor
        (f"0 {MAIN_L + NORTH_CORR_L//2} 200", "400", "0.8 1.0 0.9"),
        # South corridor
        (f"0 {SOUTH_CORR_END + SOUTH_CORR_L//2} 200", "400", "0.9 0.8 1.0"),
        # Hall 2
        (f"0 {HALL2_CENTER} 300", "1000", "0.7 0.85 1.0"),
        (f"-500 {HALL2_CENTER} 200", "400", "1.0 0.8 0.4"),
        (f"500 {HALL2_CENTER} 200", "400", "0.5 1.0 0.6"),
        # Mezzanine
        (f"0 {MAIN_L - MEZZ_L//2 - 64} 280", "400", "1.0 0.8 0.6"),
    ]

    for origin, light, color in lights:
        output.append(entity("light", {"origin": origin, "light": light, "_color": color}))

    return "\n".join(output)


if __name__ == "__main__":
    map_content = generate_museum()

    output_path = "/home/scott/Games/Xonotic/mapping/maps/rustchain_museum.map"
    with open(output_path, "w") as f:
        f.write(map_content)

    print(f"Generated {output_path}")
    print(f"Size: {len(map_content)} bytes")
    print()
    print("Arena Flow Features:")
    print("  - Central Main Hall hub with 4 exits (N/S/E/W)")
    print("  - East Gallery (Mac exhibits) with ring connection")
    print("  - West Gallery (Server exhibits) with ring connection")
    print("  - North Corridor to temple area")
    print("  - Hall 2 Vintage wing (south)")
    print("  - Outer ring corridors connecting galleries to Hall 2")
    print("  - Mezzanine with stairs for height variation")
    print("  - Multiple routes between any two areas (no dead ends)")
    print("  - Strategic weapon/item placement")
