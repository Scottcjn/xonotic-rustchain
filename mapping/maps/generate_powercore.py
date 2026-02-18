#!/usr/bin/env python3
"""
Generate RustChain PowerCore Arena v3 map file
Large industrial arena with central reactor, catwalks with ramp access

SDK Texture Guide:
- Texture paths should NOT include 'textures/' prefix
- Example: "rustchain/sophia_terminal" not "textures/rustchain/sophia_terminal"
- Scale 0.25 = texture tiles 4x, Scale 1.0 = 1 texel per unit
- For screens: calculate scale = brush_size / texture_size
"""

def brush_box(x1, y1, z1, x2, y2, z2, textures, scale=0.25):
    """
    Generate a solid box brush from min (x1,y1,z1) to max (x2,y2,z2)
    textures = [top, bottom, north, south, east, west] or single texture
    scale = texture scale (0.25 default tiles 4x, use 1.0 for 1:1)
    """
    if isinstance(textures, str):
        textures = [textures] * 6

    if x1 > x2: x1, x2 = x2, x1
    if y1 > y2: y1, y2 = y2, y1
    if z1 > z2: z1, z2 = z2, z1

    s = scale  # shorthand

    lines = ["{"]
    lines.append(f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {textures[0]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {textures[1]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {textures[2]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {textures[3]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {textures[4]} 0 0 0 {s} {s} 0 0 0")
    lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {textures[5]} 0 0 0 {s} {s} 0 0 0")
    lines.append("}")
    return "\n".join(lines)


def brush_screen_single(x1, y1, z1, x2, y2, z2, screen_tex, back_tex, face, tex_width=256, tex_height=256):
    """
    Generate a screen brush with proper texture centering and orientation.
    face: 'north', 'south', 'east', 'west' - which face shows the screen texture
    tex_width, tex_height: texture pixel dimensions

    The texture format is: TEXTURE offset_x offset_y rotation scale_x scale_y flags contents value
    - offset: shifts texture in pixels (positive = shift texture right/up)
    - scale: texel-to-unit ratio (0.5 = each texel covers 2 units)
    """
    if x1 > x2: x1, x2 = x2, x1
    if y1 > y2: y1, y2 = y2, y1
    if z1 > z2: z1, z2 = z2, z1

    # Calculate brush dimensions
    brush_width_x = x2 - x1   # X dimension
    brush_width_y = y2 - y1   # Y dimension
    brush_height = z2 - z1    # Z dimension

    # Determine which dimensions the screen face uses
    if face in ['north', 'south']:
        brush_face_width = brush_width_x
    else:  # east, west
        brush_face_width = brush_width_y

    # Calculate scale to fit texture exactly once on the face
    # scale = brush_size / texture_size means texture fits once
    scale_x = brush_face_width / tex_width
    scale_z = brush_height / tex_height

    # For proper centering, we use offset to shift the texture
    # The texture origin is at world 0,0 so we need to shift it to center on the brush
    if face in ['north', 'south']:
        # For north/south faces, X maps to texture U, Z maps to texture V
        brush_center_x = (x1 + x2) / 2
        brush_center_z = (z1 + z2) / 2
        # Offset to center: shift by half brush size minus where origin lands
        # With centering, we want texture center at brush center
        offset_u = -(brush_center_x / scale_x) + (tex_width / 2)
        offset_v = -(brush_center_z / scale_z) + (tex_height / 2)
    else:  # east, west
        # For east/west faces, Y maps to texture U, Z maps to texture V
        brush_center_y = (y1 + y2) / 2
        brush_center_z = (z1 + z2) / 2
        offset_u = -(brush_center_y / scale_x) + (tex_width / 2)
        offset_v = -(brush_center_z / scale_z) + (tex_height / 2)

    # Round offsets
    offset_u = round(offset_u)
    offset_v = round(offset_v)

    # Back texture uses default tiling
    bs = 0.25  # back texture scale

    lines = ["{"]
    # Top face
    lines.append(f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")
    # Bottom face
    lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")

    # Apply screen texture to the appropriate face with centering
    if face == 'north':
        # North face (positive Y direction) - screen texture
        lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {screen_tex} {offset_u} {offset_v} 0 {scale_x} {scale_z} 0 0 0")
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")
    elif face == 'south':
        # South face (negative Y direction) - screen texture, flipped horizontally
        # Use negative scale_x to flip the texture so it reads correctly from outside
        lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {screen_tex} {offset_u} {offset_v} 0 {-scale_x} {scale_z} 0 0 0")
    elif face == 'east':
        # East face (positive X direction) - screen texture
        lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")
        lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {screen_tex} {offset_u} {offset_v} 0 {scale_x} {scale_z} 0 0 0")
        lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")
    else:  # west
        # West face (negative X direction) - screen texture, flipped
        lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")
        lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")
        lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {screen_tex} {offset_u} {offset_v} 0 {-scale_x} {scale_z} 0 0 0")

    # Add remaining side faces if not already added
    if face in ['north', 'south']:
        lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")
        lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {back_tex} 0 0 0 {bs} {bs} 0 0 0")

    lines.append("}")
    return "\n".join(lines)


def brush_ramp(x1, y1, z1, x2, y2, z2, direction, texture):
    """
    Generate a ramp brush. Direction: 'north', 'south', 'east', 'west'
    Ramp goes UP in the specified direction
    """
    if x1 > x2: x1, x2 = x2, x1
    if y1 > y2: y1, y2 = y2, y1
    if z1 > z2: z1, z2 = z2, z1

    lines = ["{"]

    # The angled surface depends on direction
    if direction == 'north':  # Ramp rises toward +Y
        # Top angled face - rises from z1 at y1 to z2 at y2
        lines.append(f"( {x2} {y1} {z1} ) ( {x1} {y1} {z1} ) ( {x1} {y2} {z2} ) {texture} 0 0 0 0.25 0.25 0 0 0")
        # Bottom face
        lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        # Back face (high end)
        lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        # Front face (low end) - triangular, defined by 3 points at z1
        lines.append(f"( {x1} {y1} {z1} ) ( {x2} {y1} {z1} ) ( {x2} {y1} {z1} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        # East face
        lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        # West face
        lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) ( {x1} {y2} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
    elif direction == 'south':  # Ramp rises toward -Y
        lines.append(f"( {x1} {y2} {z1} ) ( {x2} {y2} {z1} ) ( {x2} {y1} {z2} ) {texture} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y2} {z1} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y2} {z1} ) ( {x2} {y1} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
    elif direction == 'east':  # Ramp rises toward +X
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y2} {z1} ) ( {x2} {y2} {z2} ) {texture} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x2} {y1} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y2} {z1} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y2} {z1} ) ( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y1} {z1} ) ( {x1} {y1} {z1} ) ( {x2} {y1} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
    else:  # west - Ramp rises toward -X
        lines.append(f"( {x2} {y2} {z1} ) ( {x2} {y1} {z1} ) ( {x1} {y1} {z2} ) {texture} 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y1} {z1} ) ( {x2} {y2} {z1} ) ( {x2} {y2} {z1} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x1} {y2} {z1} ) ( {x2} {y2} {z1} ) ( {x1} {y2} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")
        lines.append(f"( {x2} {y1} {z1} ) ( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) common/caulk 0 0 0 0.25 0.25 0 0 0")

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


def generate_powercore_arena():
    """Generate the full PowerCore Arena map - LARGE version"""

    # Textures - industrial reactor theme (evillair eX + evil8 packs)
    FLOOR = "eX/eX_floor_simple_05_d"          # Solid metal floor (was grate)
    CEILING = "eX/eX_mtl_bigplate_04_d"        # Big metal ceiling plates
    WALL = "eX/eX_wall_panels_08_d"            # Tech wall panels
    REACTOR = "eX/eXmetalBase05Rust_d"         # Rusty reactor sides
    REACTOR_TOP = "eX/eX_floor_tread_01_d"     # Tread plate reactor top
    CATWALK = "eX/eX_floor_grate_03_d"         # Catwalk grating
    TRIM = "eX/eX_trim_vert_01_d"              # Vertical trim
    RAMP = "evil8_floor/e8clangfloor04warn"    # Warning stripe stairs
    CAULK = "common/caulk"

    output = []

    # Worldspawn header
    output.append('{')
    output.append('"classname" "worldspawn"')
    output.append('"message" "RustChain PowerCore Arena v3"')
    output.append('"author" "RustChain DevKit"')
    output.append('"_description" "The Living Reactor - Halo shields, no health pickups"')
    output.append('"_lightmapscale" "0.125"')
    output.append('"_ambient" "25"')

    # LARGER Arena: 2048x2048, height 512
    SIZE = 1024  # half-size (full arena is 2048x2048)
    HEIGHT = 512
    WALL_THICK = 64

    # Floor
    output.append(brush_box(-SIZE, -SIZE, -WALL_THICK, SIZE, SIZE, 0,
                            [FLOOR, CAULK, CAULK, CAULK, CAULK, CAULK]))

    # Ceiling
    output.append(brush_box(-SIZE, -SIZE, HEIGHT, SIZE, SIZE, HEIGHT + WALL_THICK,
                            [CAULK, CEILING, CAULK, CAULK, CAULK, CAULK]))

    # Corridor dimensions
    CORR_WIDTH = 256   # corridor width
    CORR_LENGTH = 512  # how far corridors extend
    CORR_OPENING = 256  # corridor opening height in arena walls
    CORR_HEIGHT = 256  # corridor internal height (lower than arena for visual interest)
    CORR_HALF = CORR_WIDTH // 2

    # Walls with openings for corridors
    # North wall - split into 3 sections around corridor opening
    output.append(brush_box(-SIZE, SIZE, 0, -CORR_HALF, SIZE + WALL_THICK, HEIGHT,
                            [CAULK, CAULK, CAULK, WALL, CAULK, CAULK]))  # West section
    output.append(brush_box(CORR_HALF, SIZE, 0, SIZE, SIZE + WALL_THICK, HEIGHT,
                            [CAULK, CAULK, CAULK, WALL, CAULK, CAULK]))  # East section
    output.append(brush_box(-CORR_HALF, SIZE, CORR_OPENING, CORR_HALF, SIZE + WALL_THICK, HEIGHT,
                            [CAULK, CAULK, CAULK, WALL, CAULK, CAULK]))  # Above opening

    # South wall - split into 3 sections around corridor opening
    output.append(brush_box(-SIZE, -SIZE - WALL_THICK, 0, -CORR_HALF, -SIZE, HEIGHT,
                            [CAULK, CAULK, WALL, CAULK, CAULK, CAULK]))  # West section
    output.append(brush_box(CORR_HALF, -SIZE - WALL_THICK, 0, SIZE, -SIZE, HEIGHT,
                            [CAULK, CAULK, WALL, CAULK, CAULK, CAULK]))  # East section
    output.append(brush_box(-CORR_HALF, -SIZE - WALL_THICK, CORR_OPENING, CORR_HALF, -SIZE, HEIGHT,
                            [CAULK, CAULK, WALL, CAULK, CAULK, CAULK]))  # Above opening

    # East wall - split into 3 sections around corridor opening
    output.append(brush_box(SIZE, -SIZE, 0, SIZE + WALL_THICK, -CORR_HALF, HEIGHT,
                            [CAULK, CAULK, CAULK, CAULK, CAULK, WALL]))  # South section
    output.append(brush_box(SIZE, CORR_HALF, 0, SIZE + WALL_THICK, SIZE, HEIGHT,
                            [CAULK, CAULK, CAULK, CAULK, CAULK, WALL]))  # North section
    output.append(brush_box(SIZE, -CORR_HALF, CORR_OPENING, SIZE + WALL_THICK, CORR_HALF, HEIGHT,
                            [CAULK, CAULK, CAULK, CAULK, CAULK, WALL]))  # Above opening

    # West wall - split into 3 sections around corridor opening
    output.append(brush_box(-SIZE - WALL_THICK, -SIZE, 0, -SIZE, -CORR_HALF, HEIGHT,
                            [CAULK, CAULK, CAULK, CAULK, WALL, CAULK]))  # South section
    output.append(brush_box(-SIZE - WALL_THICK, CORR_HALF, 0, -SIZE, SIZE, HEIGHT,
                            [CAULK, CAULK, CAULK, CAULK, WALL, CAULK]))  # North section
    output.append(brush_box(-SIZE - WALL_THICK, -CORR_HALF, CORR_OPENING, -SIZE, CORR_HALF, HEIGHT,
                            [CAULK, CAULK, CAULK, CAULK, WALL, CAULK]))  # Above opening

    # ============ CORRIDORS WITH OUTER RING ============
    # 4 corridors extending from arena, connected by outer ring
    CORR_WALL = "eX/eX_wall_bigrib_02_d"  # Ribbed corridor walls
    CORR_FLOOR = "eX/eX_floor_simple_05_d"  # Corridor floor
    CORR_CEIL = "eX/eX_mtl_panel_02_d"  # Corridor ceiling
    RING_WALL = "eX/eX_wall_b01_d"  # Different wall for ring

    # Corridor length - longer for more playable space
    CORR_LEN = 768  # Extended corridors (was 512)
    # Outer ring distance from center
    RING_DIST = SIZE + CORR_LEN  # 1792

    # North corridor (no end wall - connects to ring)
    output.append(brush_box(-CORR_HALF, SIZE, -WALL_THICK, CORR_HALF, SIZE + CORR_LEN, 0,
                            [CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR]))
    output.append(brush_box(-CORR_HALF, SIZE, CORR_HEIGHT, CORR_HALF, SIZE + CORR_LEN, CORR_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    output.append(brush_box(-CORR_HALF - WALL_THICK, SIZE, 0, -CORR_HALF, SIZE + CORR_LEN, CORR_HEIGHT,
                            [CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL]))
    output.append(brush_box(CORR_HALF, SIZE, 0, CORR_HALF + WALL_THICK, SIZE + CORR_LEN, CORR_HEIGHT,
                            [CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL]))

    # South corridor (no end wall - connects to ring)
    output.append(brush_box(-CORR_HALF, -SIZE - CORR_LEN, -WALL_THICK, CORR_HALF, -SIZE, 0,
                            [CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR]))
    output.append(brush_box(-CORR_HALF, -SIZE - CORR_LEN, CORR_HEIGHT, CORR_HALF, -SIZE, CORR_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    output.append(brush_box(-CORR_HALF - WALL_THICK, -SIZE - CORR_LEN, 0, -CORR_HALF, -SIZE, CORR_HEIGHT,
                            [CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL]))
    output.append(brush_box(CORR_HALF, -SIZE - CORR_LEN, 0, CORR_HALF + WALL_THICK, -SIZE, CORR_HEIGHT,
                            [CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL]))

    # East corridor (no end wall - connects to ring)
    output.append(brush_box(SIZE, -CORR_HALF, -WALL_THICK, SIZE + CORR_LEN, CORR_HALF, 0,
                            [CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR]))
    output.append(brush_box(SIZE, -CORR_HALF, CORR_HEIGHT, SIZE + CORR_LEN, CORR_HALF, CORR_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    output.append(brush_box(SIZE, -CORR_HALF - WALL_THICK, 0, SIZE + CORR_LEN, -CORR_HALF, CORR_HEIGHT,
                            [CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL]))
    output.append(brush_box(SIZE, CORR_HALF, 0, SIZE + CORR_LEN, CORR_HALF + WALL_THICK, CORR_HEIGHT,
                            [CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL]))

    # West corridor (no end wall - connects to ring)
    output.append(brush_box(-SIZE - CORR_LEN, -CORR_HALF, -WALL_THICK, -SIZE, CORR_HALF, 0,
                            [CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR]))
    output.append(brush_box(-SIZE - CORR_LEN, -CORR_HALF, CORR_HEIGHT, -SIZE, CORR_HALF, CORR_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    output.append(brush_box(-SIZE - CORR_LEN, -CORR_HALF - WALL_THICK, 0, -SIZE, -CORR_HALF, CORR_HEIGHT,
                            [CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL]))
    output.append(brush_box(-SIZE - CORR_LEN, CORR_HALF, 0, -SIZE, CORR_HALF + WALL_THICK, CORR_HEIGHT,
                            [CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL, CORR_WALL]))

    # ============ OUTER RING (square ring connecting all corridors) ============
    # The ring is a hollow square corridor at distance RING_DIST from center
    # Ring inner edge = RING_DIST, outer edge = RING_DIST + CORR_WIDTH

    RING_IN = RING_DIST              # Inner edge of ring (1792)
    RING_OUT = RING_DIST + CORR_WIDTH  # Outer edge of ring (2048)

    # === NORTH RING SEGMENT ===
    # Floor (full width including corners)
    output.append(brush_box(-RING_OUT, RING_IN, -WALL_THICK, RING_OUT, RING_OUT, 0,
                            [CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR]))
    # Ceiling
    output.append(brush_box(-RING_OUT, RING_IN, CORR_HEIGHT, RING_OUT, RING_OUT, CORR_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    # Inner wall (with gap for north corridor)
    output.append(brush_box(-RING_OUT, RING_IN - WALL_THICK, 0, -CORR_HALF, RING_IN, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))
    output.append(brush_box(CORR_HALF, RING_IN - WALL_THICK, 0, RING_OUT, RING_IN, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))
    # Outer wall (north edge)
    output.append(brush_box(-RING_OUT, RING_OUT, 0, RING_OUT, RING_OUT + WALL_THICK, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))

    # === SOUTH RING SEGMENT ===
    output.append(brush_box(-RING_OUT, -RING_OUT, -WALL_THICK, RING_OUT, -RING_IN, 0,
                            [CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR]))
    output.append(brush_box(-RING_OUT, -RING_OUT, CORR_HEIGHT, RING_OUT, -RING_IN, CORR_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    output.append(brush_box(-RING_OUT, -RING_IN, 0, -CORR_HALF, -RING_IN + WALL_THICK, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))
    output.append(brush_box(CORR_HALF, -RING_IN, 0, RING_OUT, -RING_IN + WALL_THICK, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))
    output.append(brush_box(-RING_OUT, -RING_OUT - WALL_THICK, 0, RING_OUT, -RING_OUT, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))

    # === EAST RING SEGMENT (middle section only - corners covered by N/S) ===
    output.append(brush_box(RING_IN, -RING_IN, -WALL_THICK, RING_OUT, RING_IN, 0,
                            [CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR]))
    output.append(brush_box(RING_IN, -RING_IN, CORR_HEIGHT, RING_OUT, RING_IN, CORR_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    output.append(brush_box(RING_IN - WALL_THICK, -RING_IN, 0, RING_IN, -CORR_HALF, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))
    output.append(brush_box(RING_IN - WALL_THICK, CORR_HALF, 0, RING_IN, RING_IN, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))
    # East outer wall - extends to corners
    output.append(brush_box(RING_OUT, -RING_OUT, 0, RING_OUT + WALL_THICK, RING_OUT, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))

    # === WEST RING SEGMENT (middle section only) ===
    output.append(brush_box(-RING_OUT, -RING_IN, -WALL_THICK, -RING_IN, RING_IN, 0,
                            [CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR, CORR_FLOOR]))
    output.append(brush_box(-RING_OUT, -RING_IN, CORR_HEIGHT, -RING_IN, RING_IN, CORR_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    output.append(brush_box(-RING_IN, -RING_IN, 0, -RING_IN + WALL_THICK, -CORR_HALF, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))
    output.append(brush_box(-RING_IN, CORR_HALF, 0, -RING_IN + WALL_THICK, RING_IN, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))
    # West outer wall - extends to corners
    output.append(brush_box(-RING_OUT - WALL_THICK, -RING_OUT, 0, -RING_OUT, RING_OUT, CORR_HEIGHT,
                            [RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL, RING_WALL]))

    # LARGER Central reactor core (256x256, height 384)
    REACTOR_SIZE = 128
    REACTOR_HEIGHT = 384
    output.append(brush_box(-REACTOR_SIZE, -REACTOR_SIZE, 0, REACTOR_SIZE, REACTOR_SIZE, REACTOR_HEIGHT,
                            [REACTOR_TOP, CAULK, REACTOR, REACTOR, REACTOR, REACTOR]))

    # Catwalks at z=192 (higher for bigger arena), 16 units thick
    CATWALK_Z = 192
    CATWALK_THICK = 16
    CATWALK_WIDTH = 128
    CATWALK_DIST = 700  # distance from center to catwalk inner edge

    # North catwalk - use solid floor texture on bottom so it's visible from below
    CATWALK_BOTTOM = "eX/eX_mtl_panel_02_d"  # Metal panel underside
    output.append(brush_box(-384, CATWALK_DIST, CATWALK_Z - CATWALK_THICK,
                            384, CATWALK_DIST + CATWALK_WIDTH, CATWALK_Z,
                            [CATWALK, CATWALK_BOTTOM, TRIM, TRIM, TRIM, TRIM]))

    # South catwalk
    output.append(brush_box(-384, -CATWALK_DIST - CATWALK_WIDTH, CATWALK_Z - CATWALK_THICK,
                            384, -CATWALK_DIST, CATWALK_Z,
                            [CATWALK, CATWALK_BOTTOM, TRIM, TRIM, TRIM, TRIM]))

    # East catwalk
    output.append(brush_box(CATWALK_DIST, -384, CATWALK_Z - CATWALK_THICK,
                            CATWALK_DIST + CATWALK_WIDTH, 384, CATWALK_Z,
                            [CATWALK, CATWALK_BOTTOM, TRIM, TRIM, TRIM, TRIM]))

    # West catwalk
    output.append(brush_box(-CATWALK_DIST - CATWALK_WIDTH, -384, CATWALK_Z - CATWALK_THICK,
                            -CATWALK_DIST, 384, CATWALK_Z,
                            [CATWALK, CATWALK_BOTTOM, TRIM, TRIM, TRIM, TRIM]))

    # RAMPS to catwalks (stairs-style using multiple steps)
    STEP_HEIGHT = 32
    STEP_DEPTH = 64
    NUM_STEPS = CATWALK_Z // STEP_HEIGHT  # 6 steps to reach 192

    # Stair texture - all faces need to be solid for visibility
    STAIR_SIDE = "eX/eX_trim_baseboard_d"  # Metal trim for stair sides
    STAIR_BOTTOM = "eX/eX_mtl_panel_02_d"  # Solid bottom panel

    # North ramp (stairs going toward +Y)
    for i in range(NUM_STEPS):
        z = i * STEP_HEIGHT
        y_start = CATWALK_DIST - (NUM_STEPS - i) * STEP_DEPTH
        output.append(brush_box(-64, y_start, z, 64, y_start + STEP_DEPTH, z + STEP_HEIGHT,
                                [RAMP, STAIR_BOTTOM, STAIR_SIDE, TRIM, STAIR_SIDE, STAIR_SIDE]))

    # South ramp (stairs going toward -Y)
    for i in range(NUM_STEPS):
        z = i * STEP_HEIGHT
        y_end = -CATWALK_DIST + (NUM_STEPS - i) * STEP_DEPTH
        output.append(brush_box(-64, y_end - STEP_DEPTH, z, 64, y_end, z + STEP_HEIGHT,
                                [RAMP, STAIR_BOTTOM, TRIM, STAIR_SIDE, STAIR_SIDE, STAIR_SIDE]))

    # East ramp (stairs going toward +X)
    for i in range(NUM_STEPS):
        z = i * STEP_HEIGHT
        x_start = CATWALK_DIST - (NUM_STEPS - i) * STEP_DEPTH
        output.append(brush_box(x_start, -64, z, x_start + STEP_DEPTH, 64, z + STEP_HEIGHT,
                                [RAMP, STAIR_BOTTOM, STAIR_SIDE, STAIR_SIDE, STAIR_SIDE, TRIM]))

    # West ramp (stairs going toward -X)
    for i in range(NUM_STEPS):
        z = i * STEP_HEIGHT
        x_end = -CATWALK_DIST + (NUM_STEPS - i) * STEP_DEPTH
        output.append(brush_box(x_end - STEP_DEPTH, -64, z, x_end, 64, z + STEP_HEIGHT,
                                [RAMP, STAIR_BOTTOM, STAIR_SIDE, STAIR_SIDE, TRIM, STAIR_SIDE]))

    # ============ RISK/REWARD ZONES ============
    # RustChain branded areas with high-value pickups but dangerous exposure

    # RustChain branded textures (in rustchain_textures.pk3)
    # Note: Don't prefix with 'textures/' - engine adds that automatically
    RC_TERMINAL = "rustchain/sophia_terminal"
    RC_POSTER = "rustchain/sophia_poster"
    RC_LOGO = "rustchain/rustchain_logo_new"
    RC_CIRCUIT = "rustchain/circuit_panel"
    # Fallback Xonotic textures
    TECH_SCREEN = "eX/eX_lightpanel_01_d"    # Glowing tech panel
    TECH_FLOOR = "eX/eX_floor_tread_01_d"     # Tech floor
    GLOW_FLOOR = "eX/eX_floor_tread_01_d"     # Tech floor panel
    JUMP_PAD_TEX = "evil8_fx/e8_jumppad02"    # Jump pad texture (animated)

    # === 1. UNDERGROUND TUNNEL (beneath reactor) ===
    # Tight corridor passing under the reactor - close quarters combat
    TUNNEL_HEIGHT = 128
    TUNNEL_WIDTH = 192
    TUNNEL_HALF = TUNNEL_WIDTH // 2
    TUNNEL_Z = -128  # Below ground level

    # Tunnel floor (runs N-S under reactor)
    output.append(brush_box(-TUNNEL_HALF, -400, TUNNEL_Z - 32, TUNNEL_HALF, 400, TUNNEL_Z,
                            [GLOW_FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR]))
    # Tunnel ceiling
    output.append(brush_box(-TUNNEL_HALF, -400, TUNNEL_Z + TUNNEL_HEIGHT, TUNNEL_HALF, 400, TUNNEL_Z + TUNNEL_HEIGHT + 32,
                            [CEILING, RC_CIRCUIT, CEILING, CEILING, CEILING, CEILING]))
    # Tunnel walls (east/west) - RustChain terminals
    output.append(brush_box(-TUNNEL_HALF - 32, -400, TUNNEL_Z, -TUNNEL_HALF, 400, TUNNEL_Z + TUNNEL_HEIGHT,
                            [WALL, WALL, RC_TERMINAL, RC_TERMINAL, WALL, WALL]))
    output.append(brush_box(TUNNEL_HALF, -400, TUNNEL_Z, TUNNEL_HALF + 32, 400, TUNNEL_Z + TUNNEL_HEIGHT,
                            [WALL, WALL, RC_TERMINAL, RC_TERMINAL, WALL, WALL]))

    # Tunnel entrance ramps (from ground level down)
    # North entrance - solid ramp with visible sides
    output.append(brush_box(-TUNNEL_HALF, 400, TUNNEL_Z, TUNNEL_HALF, 550, 0,
                            [RAMP, FLOOR, WALL, WALL, WALL, WALL]))
    # South entrance
    output.append(brush_box(-TUNNEL_HALF, -550, TUNNEL_Z, TUNNEL_HALF, -400, 0,
                            [RAMP, FLOOR, WALL, WALL, WALL, WALL]))

    # === 2. CORNER SNIPER PLATFORMS (elevated, exposed) ===
    # Small platforms in arena corners at catwalk height - great sightlines, no cover
    SNIPER_SIZE = 96
    SNIPER_Z = CATWALK_Z  # Same height as catwalks
    SNIPER_DIST = 850  # Distance from center to platform center

    corner_positions = [
        (SNIPER_DIST, SNIPER_DIST),    # NE
        (-SNIPER_DIST, SNIPER_DIST),   # NW
        (SNIPER_DIST, -SNIPER_DIST),   # SE
        (-SNIPER_DIST, -SNIPER_DIST),  # SW
    ]

    for cx, cy in corner_positions:
        # Platform
        output.append(brush_box(cx - SNIPER_SIZE//2, cy - SNIPER_SIZE//2, SNIPER_Z - 16,
                                cx + SNIPER_SIZE//2, cy + SNIPER_SIZE//2, SNIPER_Z,
                                [CATWALK, CATWALK_BOTTOM, TRIM, TRIM, TRIM, TRIM]))

    # === 3. REACTOR TOP EXPANSION (larger platform with RustChain branding) ===
    # Wider platform on reactor top for more fighting space - RustChain logo!
    REACTOR_TOP_SIZE = 160  # Slightly larger than reactor
    output.append(brush_box(-REACTOR_TOP_SIZE, -REACTOR_TOP_SIZE, REACTOR_HEIGHT,
                            REACTOR_TOP_SIZE, REACTOR_TOP_SIZE, REACTOR_HEIGHT + 8,
                            [RC_LOGO, REACTOR_TOP, TRIM, TRIM, TRIM, TRIM]))

    # === 3b. VINTAGE COMPUTERS ON REACTOR TOP ===
    # PowerPC G4 and G5 towers - the RustChain mining rigs earning antiquity bonuses!
    # These are the sacred machines of RIP-PoA consensus

    COMP_BASE_Z = REACTOR_HEIGHT + 8  # Sits on top of reactor platform
    COMP_TEX = "eX/eX_mtl_panel_02_d"  # Metal panel for computer case
    COMP_SCREEN = RC_TERMINAL  # Sophia terminal on screens
    COMP_VENT = "eX/eX_floor_grate_03_d"  # Grate texture for vents/fans

    # G4 Power Mac towers (NE and SW corners) - tall narrow towers
    # Dimensions: 48 wide x 48 deep x 80 tall (scaled for gameplay visibility)
    G4_W, G4_D, G4_H = 48, 48, 80
    G4_DIST = 100  # Distance from center

    # NE corner - G4 tower
    output.append(brush_box(G4_DIST - G4_W//2, G4_DIST - G4_D//2, COMP_BASE_Z,
                            G4_DIST + G4_W//2, G4_DIST + G4_D//2, COMP_BASE_Z + G4_H,
                            [COMP_VENT, COMP_TEX, COMP_TEX, COMP_TEX, COMP_TEX, COMP_TEX]))
    # G4 screen (front face - south facing)
    output.append(brush_screen_single(
        G4_DIST - 20, G4_DIST - G4_D//2 - 2, COMP_BASE_Z + 40,
        G4_DIST + 20, G4_DIST - G4_D//2, COMP_BASE_Z + 72,
        COMP_SCREEN, COMP_TEX, 'south', 512, 512))

    # SW corner - G4 tower
    output.append(brush_box(-G4_DIST - G4_W//2, -G4_DIST - G4_D//2, COMP_BASE_Z,
                            -G4_DIST + G4_W//2, -G4_DIST + G4_D//2, COMP_BASE_Z + G4_H,
                            [COMP_VENT, COMP_TEX, COMP_TEX, COMP_TEX, COMP_TEX, COMP_TEX]))
    # G4 screen (front face - north facing)
    output.append(brush_screen_single(
        -G4_DIST - 20, -G4_DIST + G4_D//2, COMP_BASE_Z + 40,
        -G4_DIST + 20, -G4_DIST + G4_D//2 + 2, COMP_BASE_Z + 72,
        COMP_SCREEN, COMP_TEX, 'north', 512, 512))

    # G5 Power Mac towers (NW and SE corners) - iconic cheese grater design
    # Slightly larger than G4: 56 wide x 56 deep x 96 tall
    G5_W, G5_D, G5_H = 56, 56, 96
    G5_DIST = 100  # Same distance from center

    # NW corner - G5 tower
    output.append(brush_box(-G5_DIST - G5_W//2, G5_DIST - G5_D//2, COMP_BASE_Z,
                            -G5_DIST + G5_W//2, G5_DIST + G5_D//2, COMP_BASE_Z + G5_H,
                            [COMP_VENT, COMP_TEX, COMP_VENT, COMP_VENT, COMP_TEX, COMP_TEX]))
    # G5 screen (front face - south facing)
    output.append(brush_screen_single(
        -G5_DIST - 24, G5_DIST - G5_D//2 - 2, COMP_BASE_Z + 48,
        -G5_DIST + 24, G5_DIST - G5_D//2, COMP_BASE_Z + 88,
        COMP_SCREEN, COMP_TEX, 'south', 512, 512))

    # SE corner - G5 tower
    output.append(brush_box(G5_DIST - G5_W//2, -G5_DIST - G5_D//2, COMP_BASE_Z,
                            G5_DIST + G5_W//2, -G5_DIST + G5_D//2, COMP_BASE_Z + G5_H,
                            [COMP_VENT, COMP_TEX, COMP_VENT, COMP_VENT, COMP_TEX, COMP_TEX]))
    # G5 screen (front face - north facing)
    output.append(brush_screen_single(
        G5_DIST - 24, -G5_DIST + G5_D//2, COMP_BASE_Z + 48,
        G5_DIST + 24, -G5_DIST + G5_D//2 + 2, COMP_BASE_Z + 88,
        COMP_SCREEN, COMP_TEX, 'north', 512, 512))

    # Central server pedestal - raised platform for the "main node"
    PEDESTAL_SIZE = 64
    PEDESTAL_H = 32
    output.append(brush_box(-PEDESTAL_SIZE//2, -PEDESTAL_SIZE//2, COMP_BASE_Z,
                            PEDESTAL_SIZE//2, PEDESTAL_SIZE//2, COMP_BASE_Z + PEDESTAL_H,
                            [RC_LOGO, COMP_TEX, COMP_TEX, COMP_TEX, COMP_TEX, COMP_TEX]))

    # Cable conduits connecting computers to central pedestal
    CABLE_TEX = "eX/eX_trim_baseboard_d"  # Dark trim for cables
    CABLE_SIZE = 8  # Cable conduit width/height

    # NE cable run (from G4 to center)
    output.append(brush_box(PEDESTAL_SIZE//2, PEDESTAL_SIZE//2, COMP_BASE_Z,
                            G4_DIST - G4_W//2, PEDESTAL_SIZE//2 + CABLE_SIZE, COMP_BASE_Z + CABLE_SIZE,
                            CABLE_TEX))
    # SW cable run
    output.append(brush_box(-G4_DIST + G4_W//2, -PEDESTAL_SIZE//2 - CABLE_SIZE, COMP_BASE_Z,
                            -PEDESTAL_SIZE//2, -PEDESTAL_SIZE//2, COMP_BASE_Z + CABLE_SIZE,
                            CABLE_TEX))
    # NW cable run (from G5 to center)
    output.append(brush_box(-G5_DIST + G5_W//2, PEDESTAL_SIZE//2, COMP_BASE_Z,
                            -PEDESTAL_SIZE//2, PEDESTAL_SIZE//2 + CABLE_SIZE, COMP_BASE_Z + CABLE_SIZE,
                            CABLE_TEX))
    # SE cable run
    output.append(brush_box(PEDESTAL_SIZE//2, -PEDESTAL_SIZE//2 - CABLE_SIZE, COMP_BASE_Z,
                            G5_DIST - G5_W//2, -PEDESTAL_SIZE//2, COMP_BASE_Z + CABLE_SIZE,
                            CABLE_TEX))

    # Server rack behind central pedestal (the "main node" server)
    RACK_W, RACK_D, RACK_H = 40, 24, 72
    RACK_TEX = "eX/eX_wall_b01_d"  # Server rack texture
    RACK_FRONT = "eX/eX_lightpanel_01_d"  # Glowing front panel
    output.append(brush_box(-RACK_W//2, -RACK_D - 8, COMP_BASE_Z + PEDESTAL_H,
                            RACK_W//2, -8, COMP_BASE_Z + PEDESTAL_H + RACK_H,
                            [COMP_VENT, RACK_TEX, RACK_FRONT, RACK_TEX, RACK_TEX, RACK_TEX]))

    # Status indicator pillars (small glowing columns at corners of pedestal)
    STATUS_SIZE = 6
    STATUS_H = 48
    STATUS_TEX = "eX/eX_lightpanel_01_d"  # Glowing status lights
    status_positions = [
        (PEDESTAL_SIZE//2 - STATUS_SIZE, PEDESTAL_SIZE//2 - STATUS_SIZE),
        (-PEDESTAL_SIZE//2, PEDESTAL_SIZE//2 - STATUS_SIZE),
        (PEDESTAL_SIZE//2 - STATUS_SIZE, -PEDESTAL_SIZE//2),
        (-PEDESTAL_SIZE//2, -PEDESTAL_SIZE//2),
    ]
    for sx, sy in status_positions:
        output.append(brush_box(sx, sy, COMP_BASE_Z + PEDESTAL_H,
                                sx + STATUS_SIZE, sy + STATUS_SIZE, COMP_BASE_Z + PEDESTAL_H + STATUS_H,
                                STATUS_TEX))

    # Add lights to illuminate the computers (warm glow for the sacred machines)
    # These are point entities added later in the lights section

    # === 3c. STAIRS TO REACTOR TOP ===
    # Stairs from ground level to reactor top - positioned at CORNERS to not block screens
    # Screens are on N/S/E/W faces, so stairs go at NE and SW corners

    STAIR_STEP_H = 24  # Step height
    STAIR_STEP_D = 32  # Step depth
    STAIR_W = 80  # Stair width
    STAIR_START_Z = 0  # Start from ground
    STAIR_END_Z = REACTOR_HEIGHT + 8  # 392 - reactor top platform
    NUM_REACTOR_STEPS = (STAIR_END_Z - STAIR_START_Z) // STAIR_STEP_H  # ~16 steps

    # NE corner stairs - diagonal approach, doesn't block any screen
    # Stairs run from NE direction toward reactor top
    for i in range(NUM_REACTOR_STEPS + 1):
        step_z = STAIR_START_Z + (i * STAIR_STEP_H)
        # Start far out and move toward reactor as we go up
        step_dist = REACTOR_SIZE + 200 - (i * 10)  # Gets closer as we climb
        step_x = step_dist * 0.7  # NE diagonal
        step_y = step_dist * 0.7

        output.append(brush_box(int(step_x) - STAIR_W//2, int(step_y) - STAIR_STEP_D//2, step_z,
                                int(step_x) + STAIR_W//2, int(step_y) + STAIR_STEP_D//2, step_z + STAIR_STEP_H,
                                [RAMP, FLOOR, TRIM, TRIM, TRIM, TRIM]))

    # SW corner stairs - opposite diagonal
    for i in range(NUM_REACTOR_STEPS + 1):
        step_z = STAIR_START_Z + (i * STAIR_STEP_H)
        step_dist = REACTOR_SIZE + 200 - (i * 10)
        step_x = -step_dist * 0.7  # SW diagonal
        step_y = -step_dist * 0.7

        output.append(brush_box(int(step_x) - STAIR_W//2, int(step_y) - STAIR_STEP_D//2, step_z,
                                int(step_x) + STAIR_W//2, int(step_y) + STAIR_STEP_D//2, step_z + STAIR_STEP_H,
                                [RAMP, FLOOR, TRIM, TRIM, TRIM, TRIM]))

    # RustChain screens on reactor sides - using proper centering and orientation
    # Screen dimensions and position - larger screens, positioned lower
    SCREEN_WIDTH = 128   # Screen width in world units (increased from 96)
    SCREEN_HEIGHT = 128  # Screen height in world units (increased from 96)
    SCREEN_Z_BASE = REACTOR_HEIGHT - 180  # Moved down more (was -112)
    SCREEN_Z_TOP = SCREEN_Z_BASE + SCREEN_HEIGHT

    # sophia_terminal.tga is 512x512, rustchain_logo_new.tga is 256x256
    SOPHIA_TEX_W, SOPHIA_TEX_H = 512, 512
    LOGO_TEX_W, LOGO_TEX_H = 256, 256

    # Alternating Sophia/RustChain: N=Sophia, S=RustChain, E=RustChain, W=Sophia

    # North face - Sophia terminal
    output.append(brush_screen_single(
        -SCREEN_WIDTH//2, REACTOR_SIZE, SCREEN_Z_BASE,
        SCREEN_WIDTH//2, REACTOR_SIZE + 2, SCREEN_Z_TOP,
        RC_TERMINAL, WALL, 'north', SOPHIA_TEX_W, SOPHIA_TEX_H))

    # South face - RustChain logo (RIP-PoA branding)
    output.append(brush_screen_single(
        -SCREEN_WIDTH//2, -REACTOR_SIZE - 2, SCREEN_Z_BASE,
        SCREEN_WIDTH//2, -REACTOR_SIZE, SCREEN_Z_TOP,
        RC_LOGO, WALL, 'south', LOGO_TEX_W, LOGO_TEX_H))

    # East face - RustChain logo (RIP-PoA branding)
    output.append(brush_screen_single(
        REACTOR_SIZE, -SCREEN_WIDTH//2, SCREEN_Z_BASE,
        REACTOR_SIZE + 2, SCREEN_WIDTH//2, SCREEN_Z_TOP,
        RC_LOGO, WALL, 'east', LOGO_TEX_W, LOGO_TEX_H))

    # West face - Sophia terminal
    output.append(brush_screen_single(
        -REACTOR_SIZE - 2, -SCREEN_WIDTH//2, SCREEN_Z_BASE,
        -REACTOR_SIZE, SCREEN_WIDTH//2, SCREEN_Z_TOP,
        RC_TERMINAL, WALL, 'west', SOPHIA_TEX_W, SOPHIA_TEX_H))

    # === 4. CORRIDOR DECORATION PANELS ===
    # RustChain posters in corridors
    # North corridor - poster on west wall
    output.append(brush_box(-CORR_HALF - WALL_THICK, SIZE + 200, 32, -CORR_HALF - WALL_THICK + 2, SIZE + 328, 160,
                            [WALL, WALL, WALL, WALL, RC_POSTER, WALL]))
    # South corridor - poster on east wall
    output.append(brush_box(CORR_HALF + WALL_THICK - 2, -SIZE - 328, 32, CORR_HALF + WALL_THICK, -SIZE - 200, 160,
                            [WALL, WALL, WALL, WALL, WALL, RC_POSTER]))
    # East corridor - poster on south wall
    output.append(brush_box(SIZE + 200, -CORR_HALF - WALL_THICK, 32, SIZE + 328, -CORR_HALF - WALL_THICK + 2, 160,
                            [WALL, WALL, RC_POSTER, WALL, WALL, WALL]))
    # West corridor - poster on north wall
    output.append(brush_box(-SIZE - 328, CORR_HALF + WALL_THICK - 2, 32, -SIZE - 200, CORR_HALF + WALL_THICK, 160,
                            [WALL, WALL, WALL, RC_POSTER, WALL, WALL]))

    # === 5. JUMP PAD BASES (visible indicators) ===
    # Add visible jump pad platform bases at each corner
    JUMP_BASE_SIZE = 64
    jump_pad_positions = [
        (750, 750),    # NE
        (-750, 750),   # NW
        (750, -750),   # SE
        (-750, -750),  # SW
    ]
    for jx, jy in jump_pad_positions:
        # Jump pad base platform (raised slightly)
        output.append(brush_box(jx - JUMP_BASE_SIZE//2, jy - JUMP_BASE_SIZE//2, 0,
                                jx + JUMP_BASE_SIZE//2, jy + JUMP_BASE_SIZE//2, 8,
                                [JUMP_PAD_TEX, FLOOR, TRIM, TRIM, TRIM, TRIM]))

    # === 6. HIDING AREAS AND TACTICAL COVER ===
    # Various cover options for tactical gameplay

    # --- 6a. ALCOVES IN OUTER RING (recessed hiding spots) ---
    # Small alcoves carved into the outer ring walls for ambush positions
    ALCOVE_DEPTH = 96   # How deep into the wall
    ALCOVE_WIDTH = 128  # Width of alcove
    ALCOVE_HEIGHT = 160 # Height (crouch-friendly)

    # NE corner alcove (in north ring, east side)
    output.append(brush_box(RING_OUT - ALCOVE_WIDTH, RING_OUT, 0,
                            RING_OUT, RING_OUT + ALCOVE_DEPTH, ALCOVE_HEIGHT,
                            [CORR_CEIL, FLOOR, WALL, WALL, WALL, WALL]))
    # NW corner alcove (in north ring, west side)
    output.append(brush_box(-RING_OUT, RING_OUT, 0,
                            -RING_OUT + ALCOVE_WIDTH, RING_OUT + ALCOVE_DEPTH, ALCOVE_HEIGHT,
                            [CORR_CEIL, FLOOR, WALL, WALL, WALL, WALL]))
    # SE corner alcove (in south ring, east side)
    output.append(brush_box(RING_OUT - ALCOVE_WIDTH, -RING_OUT - ALCOVE_DEPTH, 0,
                            RING_OUT, -RING_OUT, ALCOVE_HEIGHT,
                            [CORR_CEIL, FLOOR, WALL, WALL, WALL, WALL]))
    # SW corner alcove (in south ring, west side)
    output.append(brush_box(-RING_OUT, -RING_OUT - ALCOVE_DEPTH, 0,
                            -RING_OUT + ALCOVE_WIDTH, -RING_OUT, ALCOVE_HEIGHT,
                            [CORR_CEIL, FLOOR, WALL, WALL, WALL, WALL]))

    # --- 6b. REACTOR PILLARS (cover near center) ---
    # 4 pillars around the reactor providing cover
    PILLAR_SIZE = 64
    PILLAR_HEIGHT = 256
    PILLAR_DIST = 300  # Distance from center

    pillar_positions = [
        (PILLAR_DIST, PILLAR_DIST),    # NE
        (-PILLAR_DIST, PILLAR_DIST),   # NW
        (PILLAR_DIST, -PILLAR_DIST),   # SE
        (-PILLAR_DIST, -PILLAR_DIST),  # SW
    ]
    for px, py in pillar_positions:
        output.append(brush_box(px - PILLAR_SIZE//2, py - PILLAR_SIZE//2, 0,
                                px + PILLAR_SIZE//2, py + PILLAR_SIZE//2, PILLAR_HEIGHT,
                                [REACTOR_TOP, FLOOR, WALL, WALL, WALL, WALL]))

    # --- 6c. CATWALK BARRIERS (low walls for cover) ---
    # Low barriers on catwalks providing crouch cover
    BARRIER_HEIGHT = 48   # Low enough to shoot over when standing
    BARRIER_THICK = 16
    BARRIER_TEX = "eX/eX_trim_vert_01_d"

    # North catwalk barriers (left and right sides)
    output.append(brush_box(-256, CATWALK_DIST + 32, CATWALK_Z,
                            -128, CATWALK_DIST + 32 + BARRIER_THICK, CATWALK_Z + BARRIER_HEIGHT,
                            BARRIER_TEX))
    output.append(brush_box(128, CATWALK_DIST + 32, CATWALK_Z,
                            256, CATWALK_DIST + 32 + BARRIER_THICK, CATWALK_Z + BARRIER_HEIGHT,
                            BARRIER_TEX))
    # South catwalk barriers
    output.append(brush_box(-256, -CATWALK_DIST - 32 - BARRIER_THICK, CATWALK_Z,
                            -128, -CATWALK_DIST - 32, CATWALK_Z + BARRIER_HEIGHT,
                            BARRIER_TEX))
    output.append(brush_box(128, -CATWALK_DIST - 32 - BARRIER_THICK, CATWALK_Z,
                            256, -CATWALK_DIST - 32, CATWALK_Z + BARRIER_HEIGHT,
                            BARRIER_TEX))
    # East catwalk barriers
    output.append(brush_box(CATWALK_DIST + 32, -256, CATWALK_Z,
                            CATWALK_DIST + 32 + BARRIER_THICK, -128, CATWALK_Z + BARRIER_HEIGHT,
                            BARRIER_TEX))
    output.append(brush_box(CATWALK_DIST + 32, 128, CATWALK_Z,
                            CATWALK_DIST + 32 + BARRIER_THICK, 256, CATWALK_Z + BARRIER_HEIGHT,
                            BARRIER_TEX))
    # West catwalk barriers
    output.append(brush_box(-CATWALK_DIST - 32 - BARRIER_THICK, -256, CATWALK_Z,
                            -CATWALK_DIST - 32, -128, CATWALK_Z + BARRIER_HEIGHT,
                            BARRIER_TEX))
    output.append(brush_box(-CATWALK_DIST - 32 - BARRIER_THICK, 128, CATWALK_Z,
                            -CATWALK_DIST - 32, 256, CATWALK_Z + BARRIER_HEIGHT,
                            BARRIER_TEX))

    # --- 6d. CRATE CLUSTERS (ground-level cover) ---
    # Stacked crates near walls providing cover and height variation
    CRATE_TEX = "eX/eX_wall_panels_08_d"  # Use existing wall texture for crates
    CRATE_SMALL = 48
    CRATE_LARGE = 64

    # Crate cluster near north wall (east side)
    output.append(brush_box(600, SIZE - 128, 0, 600 + CRATE_LARGE, SIZE - 128 + CRATE_LARGE, CRATE_LARGE,
                            CRATE_TEX))
    output.append(brush_box(600 + 48, SIZE - 128, 0, 600 + 48 + CRATE_SMALL, SIZE - 128 + CRATE_SMALL, CRATE_SMALL,
                            CRATE_TEX))
    output.append(brush_box(600, SIZE - 128, CRATE_LARGE, 600 + CRATE_SMALL, SIZE - 128 + CRATE_SMALL, CRATE_LARGE + CRATE_SMALL,
                            CRATE_TEX))  # Stacked on top

    # Crate cluster near south wall (west side)
    output.append(brush_box(-600 - CRATE_LARGE, -SIZE + 128 - CRATE_LARGE, 0, -600, -SIZE + 128, CRATE_LARGE,
                            CRATE_TEX))
    output.append(brush_box(-600 - CRATE_LARGE - CRATE_SMALL, -SIZE + 128 - CRATE_SMALL, 0, -600 - CRATE_LARGE, -SIZE + 128, CRATE_SMALL,
                            CRATE_TEX))

    # Crate cluster near east wall
    output.append(brush_box(SIZE - 128, 400, 0, SIZE - 128 + CRATE_LARGE, 400 + CRATE_LARGE, CRATE_LARGE,
                            CRATE_TEX))
    output.append(brush_box(SIZE - 128, 400 + CRATE_LARGE, 0, SIZE - 128 + CRATE_SMALL, 400 + CRATE_LARGE + CRATE_SMALL, CRATE_SMALL,
                            CRATE_TEX))

    # Crate cluster near west wall
    output.append(brush_box(-SIZE + 128 - CRATE_LARGE, -400 - CRATE_LARGE, 0, -SIZE + 128, -400, CRATE_LARGE,
                            CRATE_TEX))

    # --- 6e. SIDE TUNNEL CONNECTIONS (crawlspace between corridors) ---
    # Low tunnels connecting adjacent corridors for flanking routes
    CRAWL_HEIGHT = 96   # Low ceiling - crouch to move faster
    CRAWL_WIDTH = 128
    CRAWL_TEX = "eX/eX_mtl_panel_02_d"

    # NE crawlspace (connects N corridor to E corridor through corner)
    # Entrance from N corridor (at outer ring intersection)
    output.append(brush_box(CORR_HALF + WALL_THICK, RING_IN - CRAWL_WIDTH, 0,
                            RING_IN - WALL_THICK, RING_IN, CRAWL_HEIGHT,
                            [CRAWL_TEX, FLOOR, WALL, WALL, WALL, WALL]))
    # NW crawlspace
    output.append(brush_box(-RING_IN + WALL_THICK, RING_IN - CRAWL_WIDTH, 0,
                            -CORR_HALF - WALL_THICK, RING_IN, CRAWL_HEIGHT,
                            [CRAWL_TEX, FLOOR, WALL, WALL, WALL, WALL]))
    # SE crawlspace
    output.append(brush_box(CORR_HALF + WALL_THICK, -RING_IN, 0,
                            RING_IN - WALL_THICK, -RING_IN + CRAWL_WIDTH, CRAWL_HEIGHT,
                            [CRAWL_TEX, FLOOR, WALL, WALL, WALL, WALL]))
    # SW crawlspace
    output.append(brush_box(-RING_IN + WALL_THICK, -RING_IN, 0,
                            -CORR_HALF - WALL_THICK, -RING_IN + CRAWL_WIDTH, CRAWL_HEIGHT,
                            [CRAWL_TEX, FLOOR, WALL, WALL, WALL, WALL]))

    # === 7. UPPER BALCONY / MEZZANINE LEVEL ===
    # Elevated walkway around the arena perimeter at height 320
    BALCONY_Z = 320          # Height of balcony floor
    BALCONY_WIDTH = 128      # Width of walkway
    BALCONY_THICK = 16       # Floor thickness
    BALCONY_RAIL = 48        # Railing height
    BALCONY_TEX = "eX/eX_floor_grate_03_d"
    RAIL_TEX = "eX/eX_trim_vert_01_d"

    # Balcony runs along the inner edge of each wall (inset from arena walls)
    BALCONY_DIST = SIZE - BALCONY_WIDTH  # 896 from center

    # North balcony segment (with gap for corridor)
    output.append(brush_box(-SIZE + WALL_THICK, BALCONY_DIST, BALCONY_Z - BALCONY_THICK,
                            -CORR_HALF - 64, SIZE - WALL_THICK, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(CORR_HALF + 64, BALCONY_DIST, BALCONY_Z - BALCONY_THICK,
                            SIZE - WALL_THICK, SIZE - WALL_THICK, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))
    # North balcony railings (inner edge)
    output.append(brush_box(-SIZE + WALL_THICK, BALCONY_DIST - 8, BALCONY_Z,
                            -CORR_HALF - 64, BALCONY_DIST, BALCONY_Z + BALCONY_RAIL,
                            RAIL_TEX))
    output.append(brush_box(CORR_HALF + 64, BALCONY_DIST - 8, BALCONY_Z,
                            SIZE - WALL_THICK, BALCONY_DIST, BALCONY_Z + BALCONY_RAIL,
                            RAIL_TEX))

    # South balcony segment
    output.append(brush_box(-SIZE + WALL_THICK, -SIZE + WALL_THICK, BALCONY_Z - BALCONY_THICK,
                            -CORR_HALF - 64, -BALCONY_DIST, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(CORR_HALF + 64, -SIZE + WALL_THICK, BALCONY_Z - BALCONY_THICK,
                            SIZE - WALL_THICK, -BALCONY_DIST, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))
    # South balcony railings
    output.append(brush_box(-SIZE + WALL_THICK, -BALCONY_DIST, BALCONY_Z,
                            -CORR_HALF - 64, -BALCONY_DIST + 8, BALCONY_Z + BALCONY_RAIL,
                            RAIL_TEX))
    output.append(brush_box(CORR_HALF + 64, -BALCONY_DIST, BALCONY_Z,
                            SIZE - WALL_THICK, -BALCONY_DIST + 8, BALCONY_Z + BALCONY_RAIL,
                            RAIL_TEX))

    # East balcony segment
    output.append(brush_box(BALCONY_DIST, -SIZE + WALL_THICK, BALCONY_Z - BALCONY_THICK,
                            SIZE - WALL_THICK, -CORR_HALF - 64, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(BALCONY_DIST, CORR_HALF + 64, BALCONY_Z - BALCONY_THICK,
                            SIZE - WALL_THICK, SIZE - WALL_THICK, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))
    # East balcony railings
    output.append(brush_box(BALCONY_DIST - 8, -SIZE + WALL_THICK, BALCONY_Z,
                            BALCONY_DIST, -CORR_HALF - 64, BALCONY_Z + BALCONY_RAIL,
                            RAIL_TEX))
    output.append(brush_box(BALCONY_DIST - 8, CORR_HALF + 64, BALCONY_Z,
                            BALCONY_DIST, SIZE - WALL_THICK, BALCONY_Z + BALCONY_RAIL,
                            RAIL_TEX))

    # West balcony segment
    output.append(brush_box(-SIZE + WALL_THICK, -SIZE + WALL_THICK, BALCONY_Z - BALCONY_THICK,
                            -BALCONY_DIST, -CORR_HALF - 64, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))
    output.append(brush_box(-SIZE + WALL_THICK, CORR_HALF + 64, BALCONY_Z - BALCONY_THICK,
                            -BALCONY_DIST, SIZE - WALL_THICK, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))
    # West balcony railings
    output.append(brush_box(-BALCONY_DIST, -SIZE + WALL_THICK, BALCONY_Z,
                            -BALCONY_DIST + 8, -CORR_HALF - 64, BALCONY_Z + BALCONY_RAIL,
                            RAIL_TEX))
    output.append(brush_box(-BALCONY_DIST, CORR_HALF + 64, BALCONY_Z,
                            -BALCONY_DIST + 8, SIZE - WALL_THICK, BALCONY_Z + BALCONY_RAIL,
                            RAIL_TEX))

    # Corner balcony connections (L-shaped platforms at corners)
    CORNER_SIZE = BALCONY_WIDTH + 64
    # NE corner
    output.append(brush_box(SIZE - WALL_THICK - CORNER_SIZE, SIZE - WALL_THICK - CORNER_SIZE, BALCONY_Z - BALCONY_THICK,
                            SIZE - WALL_THICK, SIZE - WALL_THICK, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))
    # NW corner
    output.append(brush_box(-SIZE + WALL_THICK, SIZE - WALL_THICK - CORNER_SIZE, BALCONY_Z - BALCONY_THICK,
                            -SIZE + WALL_THICK + CORNER_SIZE, SIZE - WALL_THICK, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))
    # SE corner
    output.append(brush_box(SIZE - WALL_THICK - CORNER_SIZE, -SIZE + WALL_THICK, BALCONY_Z - BALCONY_THICK,
                            SIZE - WALL_THICK, -SIZE + WALL_THICK + CORNER_SIZE, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))
    # SW corner
    output.append(brush_box(-SIZE + WALL_THICK, -SIZE + WALL_THICK, BALCONY_Z - BALCONY_THICK,
                            -SIZE + WALL_THICK + CORNER_SIZE, -SIZE + WALL_THICK + CORNER_SIZE, BALCONY_Z,
                            [BALCONY_TEX, CRAWL_TEX, TRIM, TRIM, TRIM, TRIM]))

    # === 8. SIDE ROOMS OFF OUTER RING ===
    # Small combat rooms branching off the outer ring
    ROOM_SIZE = 256
    ROOM_HEIGHT = 192
    ROOM_DEPTH = 320  # How far room extends from ring
    ROOM_TEX = "eX/eX_wall_bigrib_02_d"

    # NE side room (off north ring, east side)
    ROOM_X = RING_IN - ROOM_SIZE  # 1536
    ROOM_Y = RING_OUT  # 2048
    # Floor
    output.append(brush_box(ROOM_X, ROOM_Y, -WALL_THICK,
                            ROOM_X + ROOM_SIZE, ROOM_Y + ROOM_DEPTH, 0,
                            [CORR_FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR]))
    # Ceiling
    output.append(brush_box(ROOM_X, ROOM_Y, ROOM_HEIGHT,
                            ROOM_X + ROOM_SIZE, ROOM_Y + ROOM_DEPTH, ROOM_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    # Walls (3 sides - opening toward ring)
    output.append(brush_box(ROOM_X - WALL_THICK, ROOM_Y, 0,
                            ROOM_X, ROOM_Y + ROOM_DEPTH, ROOM_HEIGHT,
                            ROOM_TEX))  # West wall
    output.append(brush_box(ROOM_X + ROOM_SIZE, ROOM_Y, 0,
                            ROOM_X + ROOM_SIZE + WALL_THICK, ROOM_Y + ROOM_DEPTH, ROOM_HEIGHT,
                            ROOM_TEX))  # East wall
    output.append(brush_box(ROOM_X, ROOM_Y + ROOM_DEPTH, 0,
                            ROOM_X + ROOM_SIZE, ROOM_Y + ROOM_DEPTH + WALL_THICK, ROOM_HEIGHT,
                            ROOM_TEX))  # North wall (back)

    # NW side room (off north ring, west side)
    ROOM_X2 = -RING_IN  # -1792
    output.append(brush_box(ROOM_X2, ROOM_Y, -WALL_THICK,
                            ROOM_X2 + ROOM_SIZE, ROOM_Y + ROOM_DEPTH, 0,
                            [CORR_FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR]))
    output.append(brush_box(ROOM_X2, ROOM_Y, ROOM_HEIGHT,
                            ROOM_X2 + ROOM_SIZE, ROOM_Y + ROOM_DEPTH, ROOM_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    output.append(brush_box(ROOM_X2 - WALL_THICK, ROOM_Y, 0,
                            ROOM_X2, ROOM_Y + ROOM_DEPTH, ROOM_HEIGHT,
                            ROOM_TEX))
    output.append(brush_box(ROOM_X2 + ROOM_SIZE, ROOM_Y, 0,
                            ROOM_X2 + ROOM_SIZE + WALL_THICK, ROOM_Y + ROOM_DEPTH, ROOM_HEIGHT,
                            ROOM_TEX))
    output.append(brush_box(ROOM_X2, ROOM_Y + ROOM_DEPTH, 0,
                            ROOM_X2 + ROOM_SIZE, ROOM_Y + ROOM_DEPTH + WALL_THICK, ROOM_HEIGHT,
                            ROOM_TEX))

    # SE side room (off south ring)
    output.append(brush_box(ROOM_X, -ROOM_Y - ROOM_DEPTH, -WALL_THICK,
                            ROOM_X + ROOM_SIZE, -ROOM_Y, 0,
                            [CORR_FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR]))
    output.append(brush_box(ROOM_X, -ROOM_Y - ROOM_DEPTH, ROOM_HEIGHT,
                            ROOM_X + ROOM_SIZE, -ROOM_Y, ROOM_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    output.append(brush_box(ROOM_X - WALL_THICK, -ROOM_Y - ROOM_DEPTH, 0,
                            ROOM_X, -ROOM_Y, ROOM_HEIGHT,
                            ROOM_TEX))
    output.append(brush_box(ROOM_X + ROOM_SIZE, -ROOM_Y - ROOM_DEPTH, 0,
                            ROOM_X + ROOM_SIZE + WALL_THICK, -ROOM_Y, ROOM_HEIGHT,
                            ROOM_TEX))
    output.append(brush_box(ROOM_X, -ROOM_Y - ROOM_DEPTH - WALL_THICK, 0,
                            ROOM_X + ROOM_SIZE, -ROOM_Y - ROOM_DEPTH, ROOM_HEIGHT,
                            ROOM_TEX))

    # SW side room
    output.append(brush_box(ROOM_X2, -ROOM_Y - ROOM_DEPTH, -WALL_THICK,
                            ROOM_X2 + ROOM_SIZE, -ROOM_Y, 0,
                            [CORR_FLOOR, FLOOR, FLOOR, FLOOR, FLOOR, FLOOR]))
    output.append(brush_box(ROOM_X2, -ROOM_Y - ROOM_DEPTH, ROOM_HEIGHT,
                            ROOM_X2 + ROOM_SIZE, -ROOM_Y, ROOM_HEIGHT + WALL_THICK,
                            [CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL, CORR_CEIL]))
    output.append(brush_box(ROOM_X2 - WALL_THICK, -ROOM_Y - ROOM_DEPTH, 0,
                            ROOM_X2, -ROOM_Y, ROOM_HEIGHT,
                            ROOM_TEX))
    output.append(brush_box(ROOM_X2 + ROOM_SIZE, -ROOM_Y - ROOM_DEPTH, 0,
                            ROOM_X2 + ROOM_SIZE + WALL_THICK, -ROOM_Y, ROOM_HEIGHT,
                            ROOM_TEX))
    output.append(brush_box(ROOM_X2, -ROOM_Y - ROOM_DEPTH - WALL_THICK, 0,
                            ROOM_X2 + ROOM_SIZE, -ROOM_Y - ROOM_DEPTH, ROOM_HEIGHT,
                            ROOM_TEX))

    # === 9. HAZARD ZONE - REACTOR PIT ===
    # Dangerous pit around the reactor base with damaging floor
    PIT_INNER = REACTOR_SIZE + 32   # Just outside reactor
    PIT_OUTER = REACTOR_SIZE + 128  # Width of pit
    PIT_DEPTH = 64
    HAZARD_TEX = "evil8_floor/e8clangfloor04warn"  # Warning stripe texture

    # Pit floor (slightly below ground - visual hazard)
    # North pit section
    output.append(brush_box(-PIT_OUTER, PIT_INNER, -PIT_DEPTH,
                            PIT_OUTER, PIT_OUTER, 0,
                            [HAZARD_TEX, FLOOR, WALL, WALL, WALL, WALL]))
    # South pit section
    output.append(brush_box(-PIT_OUTER, -PIT_OUTER, -PIT_DEPTH,
                            PIT_OUTER, -PIT_INNER, 0,
                            [HAZARD_TEX, FLOOR, WALL, WALL, WALL, WALL]))
    # East pit section
    output.append(brush_box(PIT_INNER, -PIT_INNER, -PIT_DEPTH,
                            PIT_OUTER, PIT_INNER, 0,
                            [HAZARD_TEX, FLOOR, WALL, WALL, WALL, WALL]))
    # West pit section
    output.append(brush_box(-PIT_OUTER, -PIT_INNER, -PIT_DEPTH,
                            -PIT_INNER, PIT_INNER, 0,
                            [HAZARD_TEX, FLOOR, WALL, WALL, WALL, WALL]))

    # === 10. WINDOW LEDGES (sniper perches) ===
    # Small ledges high up on walls for skilled players
    LEDGE_WIDTH = 96
    LEDGE_DEPTH = 48
    LEDGE_Z = 384  # High up

    # North wall ledge
    output.append(brush_box(-LEDGE_WIDTH//2, SIZE - WALL_THICK - LEDGE_DEPTH, LEDGE_Z,
                            LEDGE_WIDTH//2, SIZE - WALL_THICK, LEDGE_Z + 16,
                            [BALCONY_TEX, WALL, WALL, WALL, WALL, WALL]))
    # South wall ledge
    output.append(brush_box(-LEDGE_WIDTH//2, -SIZE + WALL_THICK, LEDGE_Z,
                            LEDGE_WIDTH//2, -SIZE + WALL_THICK + LEDGE_DEPTH, LEDGE_Z + 16,
                            [BALCONY_TEX, WALL, WALL, WALL, WALL, WALL]))
    # East wall ledge
    output.append(brush_box(SIZE - WALL_THICK - LEDGE_DEPTH, -LEDGE_WIDTH//2, LEDGE_Z,
                            SIZE - WALL_THICK, LEDGE_WIDTH//2, LEDGE_Z + 16,
                            [BALCONY_TEX, WALL, WALL, WALL, WALL, WALL]))
    # West wall ledge
    output.append(brush_box(-SIZE + WALL_THICK, -LEDGE_WIDTH//2, LEDGE_Z,
                            -SIZE + WALL_THICK + LEDGE_DEPTH, LEDGE_WIDTH//2, LEDGE_Z + 16,
                            [BALCONY_TEX, WALL, WALL, WALL, WALL, WALL]))

    # Close worldspawn
    output.append("}")

    # Spawn points - more spread out for bigger arena
    spawns = [
        # Ground level corners
        ("800 800 16", "225"),
        ("-800 800 16", "315"),
        ("800 -800 16", "135"),
        ("-800 -800 16", "45"),
        # Ground level cardinals
        ("0 900 16", "270"),
        ("0 -900 16", "90"),
        ("900 0 16", "180"),
        ("-900 0 16", "0"),
        # Catwalk spawns
        ("0 720 208", "270"),
        ("0 -720 208", "90"),
        ("720 0 208", "180"),
        ("-720 0 208", "0"),
        # Balcony spawns (new upper level)
        ("900 900 336", "225"),
        ("-900 900 336", "315"),
        ("900 -900 336", "135"),
        ("-900 -900 336", "45"),
        # Outer ring spawns
        ("0 1920 16", "270"),
        ("0 -1920 16", "90"),
        ("1920 0 16", "180"),
        ("-1920 0 16", "0"),
        # Side room spawns
        ("1600 2200 16", "180"),
        ("-1600 2200 16", "180"),
        ("1600 -2200 16", "0"),
        ("-1600 -2200 16", "0"),
    ]
    for origin, angle in spawns:
        output.append(entity("info_player_deathmatch", {"origin": origin, "angle": angle}))

    # Weapons - spread across arena
    weapons = [
        # Top of reactor - prize weapon (on central pedestal, above computers)
        ("weapon_rocketlauncher", "0 0 432"),
        # Ground floor
        ("weapon_electro", "600 600 16"),
        ("weapon_electro", "-600 -600 16"),
        ("weapon_crylink", "600 -600 16"),
        ("weapon_crylink", "-600 600 16"),
        ("weapon_machinegun", "400 0 16"),
        ("weapon_machinegun", "-400 0 16"),
        ("weapon_machinegun", "0 400 16"),
        ("weapon_machinegun", "0 -400 16"),
        # On catwalks
        ("weapon_hagar", "0 720 208"),
        ("weapon_hagar", "0 -720 208"),
        ("weapon_mortar", "720 0 208"),
        ("weapon_mortar", "-720 0 208"),
        # Balcony weapons (new upper level)
        ("weapon_vortex", "900 920 336"),        # Sniper rifle on NE balcony
        ("weapon_arc", "-900 920 336"),          # Arc on NW balcony
        # Side rooms (high-value weapons)
        ("weapon_devastator", "1600 2200 16"),  # NE side room - rocket launcher
        ("weapon_vortex", "-1600 2200 16"),     # NW side room - sniper
        ("weapon_vortex", "1600 -2200 16"),     # SE side room - sniper
        ("weapon_devastator", "-1600 -2200 16"), # SW side room - rocket launcher
        # Outer ring weapons
        ("weapon_hagar", "1920 1920 16"),   # NE corner
        ("weapon_hagar", "-1920 1920 16"),  # NW corner
        ("weapon_crylink", "1920 -1920 16"), # SE corner
        ("weapon_crylink", "-1920 -1920 16"), # SW corner
        # Underground tunnel
        ("weapon_minelayer", "0 0 -112"),  # Center of tunnel - mine layer
    ]
    for weapon, origin in weapons:
        output.append(entity(weapon, {"origin": origin}))

    # Jump pads to access balcony level
    # Format: origin, target (where you land)
    jump_pads_balcony = [
        # From corners to balcony
        ("850 850 8", "920 920 336"),    # NE corner to NE balcony
        ("-850 850 8", "-920 920 336"),  # NW corner to NW balcony
        ("850 -850 8", "920 -920 336"),  # SE corner to SE balcony
        ("-850 -850 8", "-920 -920 336"), # SW corner to SW balcony
    ]
    for pad_origin, target_origin in jump_pads_balcony:
        # Jump pad trigger
        output.append(entity("trigger_push", {
            "origin": pad_origin,
            "target": f"balcony_dest_{pad_origin.replace(' ', '_')}"
        }))
        # Destination
        output.append(entity("info_notnull", {
            "origin": target_origin,
            "targetname": f"balcony_dest_{pad_origin.replace(' ', '_')}"
        }))

    # Ammo pickups
    ammo = [
        ("item_rockets", "300 300 16"),
        ("item_rockets", "-300 -300 16"),
        ("item_cells", "300 -300 16"),
        ("item_cells", "-300 300 16"),
        ("item_bullets", "500 0 16"),
        ("item_bullets", "-500 0 16"),
        ("item_bullets", "0 500 16"),
        ("item_bullets", "0 -500 16"),
        # Balcony ammo
        ("item_rockets", "900 900 336"),
        ("item_cells", "-900 -900 336"),
        # Side room ammo
        ("item_rockets", "1650 2150 16"),
        ("item_rockets", "-1650 -2150 16"),
    ]
    for item, origin in ammo:
        output.append(entity(item, {"origin": origin}))

    # Lights - amber reactor theme with more coverage
    lights = [
        # Reactor core lights - bright amber
        ("0 0 200", "1500", "1 0.6 0.2"),
        ("0 0 390", "1200", "1 0.5 0.1"),
        # Ground level ambient - 8 lights in octagon
        ("700 0 100", "600", "1 0.7 0.3"),
        ("-700 0 100", "600", "1 0.7 0.3"),
        ("0 700 100", "600", "1 0.7 0.3"),
        ("0 -700 100", "600", "1 0.7 0.3"),
        ("500 500 100", "500", "1 0.8 0.4"),
        ("-500 500 100", "500", "1 0.8 0.4"),
        ("500 -500 100", "500", "1 0.8 0.4"),
        ("-500 -500 100", "500", "1 0.8 0.4"),
        # Ceiling lights - cooler white
        ("512 512 480", "800", "1 0.95 0.9"),
        ("-512 512 480", "800", "1 0.95 0.9"),
        ("512 -512 480", "800", "1 0.95 0.9"),
        ("-512 -512 480", "800", "1 0.95 0.9"),
        # Catwalk lights
        ("0 750 280", "400", "1 0.7 0.3"),
        ("0 -750 280", "400", "1 0.7 0.3"),
        ("750 0 280", "400", "1 0.7 0.3"),
        ("-750 0 280", "400", "1 0.7 0.3"),
        # Corridor lights - DISTINCTIVE COLORS per direction
        # NORTH = BLUE
        ("0 1200 128", "500", "0.3 0.5 1.0"),      # North corridor near - blue
        ("0 1500 128", "500", "0.3 0.5 1.0"),      # North corridor mid - blue
        ("0 1920 128", "600", "0.2 0.4 1.0"),      # North ring - bright blue
        # SOUTH = RED
        ("0 -1200 128", "500", "1.0 0.3 0.3"),     # South corridor near - red
        ("0 -1500 128", "500", "1.0 0.3 0.3"),     # South corridor mid - red
        ("0 -1920 128", "600", "1.0 0.2 0.2"),     # South ring - bright red
        # EAST = GREEN
        ("1200 0 128", "500", "0.3 1.0 0.3"),      # East corridor near - green
        ("1500 0 128", "500", "0.3 1.0 0.3"),      # East corridor mid - green
        ("1920 0 128", "600", "0.2 1.0 0.2"),      # East ring - bright green
        # WEST = YELLOW/ORANGE
        ("-1200 0 128", "500", "1.0 0.8 0.2"),     # West corridor near - yellow
        ("-1500 0 128", "500", "1.0 0.8 0.2"),     # West corridor mid - yellow
        ("-1920 0 128", "600", "1.0 0.7 0.1"),     # West ring - bright yellow
        # Corner lights - blend adjacent colors
        ("1920 1920 128", "400", "0.3 0.8 0.8"),   # NE corner - cyan (blue+green)
        ("1920 -1920 128", "400", "0.8 0.6 0.3"),  # SE corner - orange (red+green)
        ("-1920 -1920 128", "400", "1.0 0.5 0.3"), # SW corner - orange (red+yellow)
        ("-1920 1920 128", "400", "0.5 0.7 0.8"),  # NW corner - teal (blue+yellow)
        # Teleporter lights at ring dead ends (bright cyan to mark teleporters)
        # DEAD_END = 1744, RING_CENTER = 1920
        # North ring dead ends
        ("1744 1920 64", "400", "0.5 1.0 1.0"),    # North ring east end
        ("-1744 1920 64", "400", "0.5 1.0 1.0"),   # North ring west end
        # South ring dead ends
        ("1744 -1920 64", "400", "0.5 1.0 1.0"),   # South ring east end
        ("-1744 -1920 64", "400", "0.5 1.0 1.0"),  # South ring west end
        # East ring dead ends
        ("1920 1744 64", "400", "0.5 1.0 1.0"),    # East ring north end
        ("1920 -1744 64", "400", "0.5 1.0 1.0"),   # East ring south end
        # West ring dead ends
        ("-1920 1744 64", "400", "0.5 1.0 1.0"),   # West ring north end
        ("-1920 -1744 64", "400", "0.5 1.0 1.0"),  # West ring south end
        # Balcony lights (new upper level) - warm white
        ("920 920 380", "400", "1.0 0.9 0.8"),     # NE balcony
        ("-920 920 380", "400", "1.0 0.9 0.8"),    # NW balcony
        ("920 -920 380", "400", "1.0 0.9 0.8"),    # SE balcony
        ("-920 -920 380", "400", "1.0 0.9 0.8"),   # SW balcony
        # Side room lights - cool blue accent
        ("1600 2200 128", "500", "0.4 0.6 1.0"),   # NE side room
        ("-1600 2200 128", "500", "0.4 0.6 1.0"),  # NW side room
        ("1600 -2200 128", "500", "0.4 0.6 1.0"),  # SE side room
        ("-1600 -2200 128", "500", "0.4 0.6 1.0"), # SW side room
        # Reactor pit hazard lights - red warning
        ("200 200 -32", "300", "1.0 0.2 0.1"),     # NE pit
        ("-200 200 -32", "300", "1.0 0.2 0.1"),    # NW pit
        ("200 -200 -32", "300", "1.0 0.2 0.1"),    # SE pit
        ("-200 -200 -32", "300", "1.0 0.2 0.1"),   # SW pit
        # Sniper ledge lights - purple accent
        ("0 980 400", "300", "0.8 0.3 1.0"),       # North ledge
        ("0 -980 400", "300", "0.8 0.3 1.0"),      # South ledge
        ("980 0 400", "300", "0.8 0.3 1.0"),       # East ledge
        ("-980 0 400", "300", "0.8 0.3 1.0"),      # West ledge
        # Vintage computer lights (reactor top) - warm amber glow for sacred machines
        ("100 100 480", "400", "1.0 0.7 0.3"),     # NE G4 tower
        ("-100 -100 480", "400", "1.0 0.7 0.3"),   # SW G4 tower
        ("-100 100 496", "400", "1.0 0.7 0.3"),    # NW G5 tower
        ("100 -100 496", "400", "1.0 0.7 0.3"),    # SE G5 tower
        ("0 0 440", "500", "0.3 1.0 0.5"),         # Central pedestal - green glow
    ]
    for origin, light, color in lights:
        output.append(entity("light", {"origin": origin, "light": light, "_color": color}))

    # Corridor weapons - in corridors and ring
    corridor_weapons = [
        # Mid-corridor weapons
        ("weapon_machinegun", "0 1350 16"),    # North corridor mid
        ("weapon_machinegun", "0 -1350 16"),   # South corridor mid
        ("weapon_machinegun", "1350 0 16"),    # East corridor mid
        ("weapon_machinegun", "-1350 0 16"),   # West corridor mid
        # Ring weapons (cardinal points)
        ("weapon_vortex", "0 1920 16"),        # North ring - sniper
        ("weapon_devastator", "0 -1920 16"),   # South ring - rockets
        ("weapon_arc", "1920 0 16"),           # East ring - arc
        ("weapon_minelayer", "-1920 0 16"),    # West ring - mines
        # Corner powerups
        ("item_health_mega", "1920 1920 16"),   # NE corner
        ("item_armor_large", "-1920 1920 16"),  # NW corner
        ("item_health_mega", "-1920 -1920 16"), # SW corner
        ("item_armor_large", "1920 -1920 16"),  # SE corner
    ]
    for weapon, origin in corridor_weapons:
        output.append(entity(weapon, {"origin": origin}))

    # Corridor and ring spawns
    corridor_spawns = [
        # Corridor spawns
        ("0 1300 16", "270"),     # North corridor
        ("0 -1300 16", "90"),     # South corridor
        ("1300 0 16", "180"),     # East corridor
        ("-1300 0 16", "0"),      # West corridor
        # Ring spawns (corners)
        ("1920 1920 16", "225"),   # NE corner
        ("-1920 1920 16", "315"),  # NW corner
        ("-1920 -1920 16", "45"),  # SW corner
        ("1920 -1920 16", "135"),  # SE corner
    ]
    for origin, angle in corridor_spawns:
        output.append(entity("info_player_deathmatch", {"origin": origin, "angle": angle}))

    # ============ RISK/REWARD ZONE ENTITIES ============

    # Jump pads to corner sniper platforms (from ground level)
    # These launch players to elevated platforms - exposed during flight!
    JUMP_SIZE = 48  # Jump pad size
    jump_pads = [
        # (pad_x, pad_y, target_x, target_y, target_z, name)
        (750, 750, 850, 850, 220, "ne"),
        (-750, 750, -850, 850, 220, "nw"),
        (750, -750, 850, -850, 220, "se"),
        (-750, -750, -850, -850, 220, "sw"),
    ]
    for px, py, tx, ty, tz, name in jump_pads:
        # Jump pad target (where player lands)
        output.append(entity("target_position", {
            "origin": f"{tx} {ty} {tz}",
            "targetname": f"jump_{name}"
        }))
        # Jump pad trigger (brush entity)
        x1, y1, z1 = px - JUMP_SIZE//2, py - JUMP_SIZE//2, 1
        x2, y2, z2 = px + JUMP_SIZE//2, py + JUMP_SIZE//2, 32
        tex = "common/trigger"
        output.append("{")
        output.append('"classname" "trigger_push"')
        output.append(f'"target" "jump_{name}"')
        output.append("{")
        output.append(f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append("}")
        output.append("}")

    # Underground tunnel items (high value, tight quarters)
    tunnel_items = [
        ("weapon_vaporizer", "0 0 -112"),        # Center of tunnel - instakill weapon
        ("item_strength", "0 -200 -112"),         # Quad damage in tunnel
        ("item_armor_large", "0 200 -112"),       # Armor in tunnel
    ]
    for item, origin in tunnel_items:
        output.append(entity(item, {"origin": origin}))

    # Corner platform items (exposed, but valuable)
    platform_items = [
        ("item_invincible", "850 850 208"),      # NE - invincibility (very exposed)
        ("weapon_vortex", "-850 850 208"),        # NW - sniper rifle
        ("item_strength", "850 -850 208"),        # SE - quad damage
        ("weapon_devastator", "-850 -850 208"),   # SW - rocket launcher
    ]
    for item, origin in platform_items:
        output.append(entity(item, {"origin": origin}))

    # Tunnel lights (eerie cyan glow)
    tunnel_lights = [
        ("0 0 -80", "400", "0.2 0.8 1.0"),       # Center
        ("0 300 -80", "300", "0.2 0.8 1.0"),     # North
        ("0 -300 -80", "300", "0.2 0.8 1.0"),    # South
    ]
    for origin, light, color in tunnel_lights:
        output.append(entity("light", {"origin": origin, "light": light, "_color": color}))

    # Corner platform lights (bright to highlight exposure)
    for cx, cy in [(850, 850), (-850, 850), (850, -850), (-850, -850)]:
        output.append(entity("light", {
            "origin": f"{cx} {cy} 280",
            "light": "500",
            "_color": "1.0 0.5 0.8"  # Pink/magenta for danger
        }))

    # ============ TELEPORTERS AT RING CORRIDOR DEAD ENDS ============
    # The ring has 4 segments. Each segment has 2 dead ends (at the corners).
    # Place teleporters at the FAR ENDS of each ring segment (where you hit a wall)
    #
    # Ring layout (looking from above):
    #   NW corner -------- NORTH ring -------- NE corner
    #       |                                      |
    #   WEST ring                              EAST ring
    #       |                                      |
    #   SW corner -------- SOUTH ring -------- SE corner
    #
    # Each corner has walls. Teleporters go at the ends of the ring segments.

    TELE_SIZE = 64
    TELE_HEIGHT = 96

    # Ring center line is at RING_IN + CORR_WIDTH/2 = 1920
    RING_CENTER = RING_IN + CORR_WIDTH // 2  # 1920

    # The ring ends at RING_OUT (2048) but inner walls create dead-ends
    # For North ring: dead ends are at x = ±(RING_IN - 32) where inner walls block
    # Actually the ring goes from -RING_OUT to +RING_OUT but has inner walls with gaps

    # Dead end positions - at the far ends of each ring segment, just before the corner
    DEAD_END = RING_IN - 48  # 1744 - just inside where inner wall blocks the ring

    tele_positions = [
        # North ring segment: runs E-W at y=RING_CENTER, dead ends at x=±DEAD_END
        ("north_east_end", (DEAD_END, RING_CENTER, 0), "east"),      # -> East corridor
        ("north_west_end", (-DEAD_END, RING_CENTER, 0), "west"),     # -> West corridor
        # South ring segment: runs E-W at y=-RING_CENTER
        ("south_east_end", (DEAD_END, -RING_CENTER, 0), "east"),     # -> East corridor
        ("south_west_end", (-DEAD_END, -RING_CENTER, 0), "west"),    # -> West corridor
        # East ring segment: runs N-S at x=RING_CENTER
        ("east_north_end", (RING_CENTER, DEAD_END, 0), "north"),     # -> North corridor
        ("east_south_end", (RING_CENTER, -DEAD_END, 0), "south"),    # -> South corridor
        # West ring segment: runs N-S at x=-RING_CENTER
        ("west_north_end", (-RING_CENTER, DEAD_END, 0), "north"),    # -> North corridor
        ("west_south_end", (-RING_CENTER, -DEAD_END, 0), "south"),   # -> South corridor
    ]

    # Destinations - at the START of each corridor (near arena entrance)
    DEST_DIST = SIZE + 96
    dest_positions = {
        "north": (0, DEST_DIST, 32),
        "east":  (DEST_DIST, 0, 32),
        "south": (0, -DEST_DIST, 32),
        "west":  (-DEST_DIST, 0, 32),
    }

    dest_angles = {
        "north": "270",
        "east": "180",
        "south": "90",
        "west": "0",
    }

    # Create destinations (only 4 needed, one per corridor)
    for name, (dx, dy, dz) in dest_positions.items():
        output.append(entity("info_teleport_destination", {
            "origin": f"{dx} {dy} {dz}",
            "angle": dest_angles[name],
            "targetname": f"tele_dest_{name}"
        }))

    # Create teleporter triggers at ring dead ends
    for tele_name, (sx, sy, sz), dest in tele_positions:
        x1, y1, z1 = sx - TELE_SIZE//2, sy - TELE_SIZE//2, 1
        x2, y2, z2 = sx + TELE_SIZE//2, sy + TELE_SIZE//2, TELE_HEIGHT
        tex = "common/trigger"
        output.append("{")
        output.append('"classname" "trigger_teleport"')
        output.append(f'"target" "tele_dest_{dest}"')
        output.append("{")
        output.append(f"( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append(f"( {x2} {y2} {z1} ) ( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append(f"( {x2} {y2} {z1} ) ( {x2} {y2} {z2} ) ( {x1} {y2} {z2} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append(f"( {x1} {y1} {z1} ) ( {x1} {y1} {z2} ) ( {x2} {y1} {z2} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append(f"( {x2} {y1} {z1} ) ( {x2} {y1} {z2} ) ( {x2} {y2} {z2} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append(f"( {x1} {y2} {z1} ) ( {x1} {y2} {z2} ) ( {x1} {y1} {z2} ) {tex} 0 0 0 0.25 0.25 0 0 0")
        output.append("}")
        output.append("}")

    return "\n".join(output)


if __name__ == "__main__":
    map_content = generate_powercore_arena()

    output_path = "/home/scott/Games/Xonotic/mapping/maps/rustcore_v3.map"
    with open(output_path, "w") as f:
        f.write(map_content)

    print(f"Generated {output_path}")
    print(f"Size: {len(map_content)} bytes")
