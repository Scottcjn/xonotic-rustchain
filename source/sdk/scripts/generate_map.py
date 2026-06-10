#!/usr/bin/env python3
"""
Procedural Map Generator for Xonotic
Generates .map files that can be compiled with q3map2

Usage:
    ./generate_map.py arena 1024 512 my_arena
    ./generate_map.py corridor 2048 256 my_corridor
    ./generate_map.py box 512 256 simple_box

Then compile with:
    ./sdk/scripts/compile_map.sh my_arena
"""

import sys
import os
import random
import math

# Default texture sets (using actual Xonotic texture paths)
TEXTURES = {
    'floor': 'exx/floor/floor_clang01',
    'ceiling': 'exx/base/base_metal03',
    'wall': 'exx/wall/wall_panel06',
    'trim': 'exx/trim/trim_vert01',
    'light': 'exx/light/light_panel01',
    'caulk': 'common/caulk',
}

class MapGenerator:
    def __init__(self, name="generated_map"):
        self.name = name
        self.brushes = []
        self.entities = []
        self.lights = []

    def add_brush(self, mins, maxs, texture=None):
        """Add a solid brush (box) to the map"""
        if texture is None:
            texture = TEXTURES['wall']

        x1, y1, z1 = mins
        x2, y2, z2 = maxs

        brush = f"""{{
( {x1} {y2} {z1} ) ( {x1} {y1} {z1} ) ( {x2} {y1} {z1} ) {texture} 0 0 0 0.5 0.5 0 0 0
( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) {texture} 0 0 0 0.5 0.5 0 0 0
( {x2} {y2} {z2} ) ( {x2} {y1} {z2} ) ( {x2} {y1} {z1} ) {texture} 0 0 0 0.5 0.5 0 0 0
( {x1} {y1} {z2} ) ( {x1} {y2} {z2} ) ( {x1} {y2} {z1} ) {texture} 0 0 0 0.5 0.5 0 0 0
( {x1} {y2} {z2} ) ( {x2} {y2} {z2} ) ( {x2} {y2} {z1} ) {texture} 0 0 0 0.5 0.5 0 0 0
( {x2} {y1} {z2} ) ( {x1} {y1} {z2} ) ( {x1} {y1} {z1} ) {texture} 0 0 0 0.5 0.5 0 0 0
}}"""
        self.brushes.append(brush)

    def add_hollow_room(self, center, size, height, wall_thickness=16):
        """Create a hollow room with floor, ceiling, and walls"""
        cx, cy = center
        w, d = size
        h = height
        t = wall_thickness

        # Floor
        self.add_brush(
            (cx - w//2, cy - d//2, -t),
            (cx + w//2, cy + d//2, 0),
            TEXTURES['floor']
        )

        # Ceiling
        self.add_brush(
            (cx - w//2, cy - d//2, h),
            (cx + w//2, cy + d//2, h + t),
            TEXTURES['ceiling']
        )

        # North wall
        self.add_brush(
            (cx - w//2, cy + d//2, 0),
            (cx + w//2, cy + d//2 + t, h),
            TEXTURES['wall']
        )

        # South wall
        self.add_brush(
            (cx - w//2, cy - d//2 - t, 0),
            (cx + w//2, cy - d//2, h),
            TEXTURES['wall']
        )

        # East wall
        self.add_brush(
            (cx + w//2, cy - d//2, 0),
            (cx + w//2 + t, cy + d//2, h),
            TEXTURES['wall']
        )

        # West wall
        self.add_brush(
            (cx - w//2 - t, cy - d//2, 0),
            (cx - w//2, cy + d//2, h),
            TEXTURES['wall']
        )

    def add_platform(self, center, size, height, thickness=16):
        """Add a raised platform"""
        cx, cy = center
        w, d = size

        self.add_brush(
            (cx - w//2, cy - d//2, height - thickness),
            (cx + w//2, cy + d//2, height),
            TEXTURES['floor']
        )

    def add_pillar(self, center, radius, height):
        """Add a square pillar"""
        cx, cy = center
        r = radius

        self.add_brush(
            (cx - r, cy - r, 0),
            (cx + r, cy + r, height),
            TEXTURES['trim']
        )

    def add_spawn(self, pos, angle=0):
        """Add a player spawn point"""
        x, y, z = pos
        self.entities.append(f'''{{
"classname" "info_player_deathmatch"
"origin" "{x} {y} {z}"
"angle" "{angle}"
}}''')

    def add_light(self, pos, brightness=300, color=(1, 1, 1)):
        """Add a light entity"""
        x, y, z = pos
        r, g, b = color
        self.lights.append(f'''{{
"classname" "light"
"origin" "{x} {y} {z}"
"light" "{brightness}"
"_color" "{r} {g} {b}"
}}''')

    def add_weapon(self, pos, weapon_type="weapon_rocketlauncher"):
        """Add a weapon pickup"""
        x, y, z = pos
        self.entities.append(f'''{{
"classname" "{weapon_type}"
"origin" "{x} {y} {z}"
}}''')

    def add_item(self, pos, item_type="item_health_large"):
        """Add an item pickup"""
        x, y, z = pos
        self.entities.append(f'''{{
"classname" "{item_type}"
"origin" "{x} {y} {z}"
}}''')

    def generate(self):
        """Generate the complete .map file content"""
        output = []

        # Worldspawn with brushes
        output.append('{')
        output.append('"classname" "worldspawn"')
        output.append(f'"message" "{self.name}"')
        output.append('"author" "RustChain DevKit Generator"')

        for brush in self.brushes:
            output.append(brush)

        output.append('}')

        # Entities
        for entity in self.entities:
            output.append(entity)

        # Lights
        for light in self.lights:
            output.append(light)

        return '\n'.join(output)

    def save(self, path):
        """Save to .map file"""
        content = self.generate()
        with open(path, 'w') as f:
            f.write(content)
        print(f"Saved: {path}")


def generate_arena(width, height, name):
    """Generate an arena-style map with central area and corner spawns"""
    gen = MapGenerator(name)

    # Main room
    gen.add_hollow_room((0, 0), (width, width), height)

    # Center platform
    gen.add_platform((0, 0), (200, 200), 32)

    # Corner pillars
    offset = width // 3
    for x in [-offset, offset]:
        for y in [-offset, offset]:
            gen.add_pillar((x, y), 32, height - 32)

    # Spawns at corners
    spawn_offset = width // 2 - 64
    angles = [315, 225, 135, 45]
    for i, (x, y) in enumerate([(-1, 1), (1, 1), (1, -1), (-1, -1)]):
        gen.add_spawn((x * spawn_offset, y * spawn_offset, 32), angles[i])

    # Center light
    gen.add_light((0, 0, height - 32), 400)

    # Corner lights
    for x in [-offset, offset]:
        for y in [-offset, offset]:
            gen.add_light((x, y, height - 64), 200, (1, 0.9, 0.8))

    # Weapons
    gen.add_weapon((0, 0, 64), "weapon_rocketlauncher")
    gen.add_weapon((spawn_offset, 0, 32), "weapon_shotgun")
    gen.add_weapon((-spawn_offset, 0, 32), "weapon_machinegun")
    gen.add_weapon((0, spawn_offset, 32), "weapon_electro")
    gen.add_weapon((0, -spawn_offset, 32), "weapon_crylink")

    # Health/Armor
    gen.add_item((offset, 0, 32), "item_health_large")
    gen.add_item((-offset, 0, 32), "item_health_large")
    gen.add_item((0, offset, 32), "item_armor_large")
    gen.add_item((0, -offset, 32), "item_armor_large")

    return gen


def generate_corridor(length, width, name):
    """Generate a corridor/hallway map"""
    gen = MapGenerator(name)
    height = 192

    # Main corridor
    gen.add_hollow_room((0, 0), (length, width), height)

    # Spawns at each end
    gen.add_spawn((-length//2 + 64, 0, 32), 0)
    gen.add_spawn((length//2 - 64, 0, 32), 180)

    # Lights along corridor
    for x in range(-length//2 + 128, length//2, 256):
        gen.add_light((x, 0, height - 32), 250)

    # Weapons in middle
    gen.add_weapon((0, 0, 32), "weapon_rocketlauncher")

    # Health at ends
    gen.add_item((-length//4, 0, 32), "item_health_large")
    gen.add_item((length//4, 0, 32), "item_health_large")

    return gen


def generate_box(size, height, name):
    """Generate a simple box room"""
    gen = MapGenerator(name)

    gen.add_hollow_room((0, 0), (size, size), height)

    # 4 spawns
    offset = size // 2 - 64
    for angle, (x, y) in zip([315, 225, 135, 45],
                              [(-1, 1), (1, 1), (1, -1), (-1, -1)]):
        gen.add_spawn((x * offset, y * offset, 32), angle)

    # Center light
    gen.add_light((0, 0, height - 32), 400)

    # Center weapon
    gen.add_weapon((0, 0, 32), "weapon_rocketlauncher")

    return gen


def generate_powercore(name):
    """Generate the RustChain PowerCore Arena - vertical combat around a reactor"""
    gen = MapGenerator(name)

    # Industrial texture set (using actual Xonotic texture paths)
    INDUSTRIAL = {
        'floor': 'exx/floor/floor_clang01',
        'ceiling': 'exx/base/base_metal03',
        'wall': 'exx/wall/wall_panel06',
        'trim': 'exx/trim/trim_vert01',
        'glow': 'exx/light/light_panel01',  # Glowing panels
    }

    width = 1024
    height = 384

    # Main room (1024x1024x384)
    gen.add_hollow_room((0, 0), (width, width), height)

    # === REACTOR CORE (center pillar with amber glow) ===
    # Core pillar - octagonal approximation using square
    gen.add_brush(
        (-48, -48, 0),
        (48, 48, height - 64),
        INDUSTRIAL['trim']
    )

    # Core top platform (jumpable)
    gen.add_platform((0, 0), (128, 128), height - 64, 16)

    # Amber reactor lights (multiple for glow effect)
    gen.add_light((0, 0, height // 2), 600, (1.0, 0.5, 0.1))  # Amber center
    gen.add_light((0, 0, 64), 400, (1.0, 0.6, 0.2))  # Lower amber
    gen.add_light((0, 0, height - 96), 500, (1.0, 0.4, 0.0))  # Upper amber

    # === VINTAGE MACHINE ALCOVES (server racks / old computers) ===
    alcove_offset = 350
    alcove_size = 128
    alcove_depth = 64

    # North alcove - machine bank
    gen.add_brush(
        (-alcove_size//2, alcove_offset - alcove_depth, 0),
        (alcove_size//2, alcove_offset, 96),
        INDUSTRIAL['trim']
    )
    gen.add_light((0, alcove_offset - 32, 80), 150, (0.2, 0.8, 0.2))  # Green LED glow

    # South alcove - machine bank
    gen.add_brush(
        (-alcove_size//2, -alcove_offset, 0),
        (alcove_size//2, -alcove_offset + alcove_depth, 96),
        INDUSTRIAL['trim']
    )
    gen.add_light((0, -alcove_offset + 32, 80), 150, (0.2, 0.8, 0.2))

    # East alcove - machine bank
    gen.add_brush(
        (alcove_offset - alcove_depth, -alcove_size//2, 0),
        (alcove_offset, alcove_size//2, 96),
        INDUSTRIAL['trim']
    )
    gen.add_light((alcove_offset - 32, 0, 80), 150, (0.2, 0.2, 0.8))  # Blue LED

    # West alcove - machine bank
    gen.add_brush(
        (-alcove_offset, -alcove_size//2, 0),
        (-alcove_offset + alcove_depth, alcove_size//2, 96),
        INDUSTRIAL['trim']
    )
    gen.add_light((-alcove_offset + 32, 0, 80), 150, (0.2, 0.2, 0.8))

    # === ELEVATED CATWALKS (second level) ===
    catwalk_height = 160
    catwalk_width = 96

    # North-South catwalk
    gen.add_brush(
        (-catwalk_width//2, -400, catwalk_height),
        (catwalk_width//2, 400, catwalk_height + 8),
        INDUSTRIAL['floor']
    )

    # East-West catwalk
    gen.add_brush(
        (-400, -catwalk_width//2, catwalk_height),
        (400, catwalk_width//2, catwalk_height + 8),
        INDUSTRIAL['floor']
    )

    # Catwalk railings (visual pillars at intersections)
    for x, y in [(-400, 0), (400, 0), (0, -400), (0, 400)]:
        gen.add_pillar((x, y), 16, catwalk_height + 64)

    # === JUMP PADS (4 corners, launch to catwalks) ===
    jump_offset = 380
    jump_positions = [
        (jump_offset, jump_offset),
        (-jump_offset, jump_offset),
        (jump_offset, -jump_offset),
        (-jump_offset, -jump_offset)
    ]

    for x, y in jump_positions:
        # Jump pad platform (visual)
        gen.add_brush(
            (x - 32, y - 32, 0),
            (x + 32, y + 32, 8),
            INDUSTRIAL['glow']
        )
        # Jump pad entity
        gen.entities.append(f'''{{
"classname" "trigger_push"
"target" "jumppad_dest_{x}_{y}"
"origin" "{x} {y} 16"
}}''')
        # Jump destination (catwalk level)
        gen.entities.append(f'''{{
"classname" "info_notnull"
"targetname" "jumppad_dest_{x}_{y}"
"origin" "{x//2} {y//2} {catwalk_height + 64}"
}}''')
        # Jump pad light effect
        gen.add_light((x, y, 32), 100, (1.0, 0.6, 0.0))

    # === PLAYER SPAWNS (ground level, 4 corners facing center) ===
    spawn_offset = 420
    spawn_data = [
        ((-spawn_offset, spawn_offset, 32), 315),   # NW
        ((spawn_offset, spawn_offset, 32), 225),    # NE
        ((spawn_offset, -spawn_offset, 32), 135),   # SE
        ((-spawn_offset, -spawn_offset, 32), 45),   # SW
    ]
    for pos, angle in spawn_data:
        gen.add_spawn(pos, angle)

    # Catwalk spawns (2 additional)
    gen.add_spawn((0, 300, catwalk_height + 32), 180)
    gen.add_spawn((0, -300, catwalk_height + 32), 0)

    # === WEAPONS ===
    # Rocket Launcher - top of reactor (king of the hill)
    gen.add_weapon((0, 0, height - 48), "weapon_rocketlauncher")

    # Electro - north catwalk
    gen.add_weapon((0, 300, catwalk_height + 32), "weapon_electro")

    # Shotgun - south catwalk
    gen.add_weapon((0, -300, catwalk_height + 32), "weapon_shotgun")

    # Machinegun - west ground
    gen.add_weapon((-300, 0, 32), "weapon_machinegun")

    # Crylink - east ground
    gen.add_weapon((300, 0, 32), "weapon_crylink")

    # === ITEMS ===
    # Health at machine alcoves
    gen.add_item((0, alcove_offset - 48, 32), "item_health_large")
    gen.add_item((0, -alcove_offset + 48, 32), "item_health_large")

    # Armor near jump pads
    gen.add_item((jump_offset - 64, jump_offset - 64, 32), "item_armor_large")
    gen.add_item((-jump_offset + 64, -jump_offset + 64, 32), "item_armor_large")

    # Medium armor on catwalks
    gen.add_item((250, 0, catwalk_height + 32), "item_armor_medium")
    gen.add_item((-250, 0, catwalk_height + 32), "item_armor_medium")

    # Health packs scattered
    gen.add_item((200, 200, 32), "item_health_small")
    gen.add_item((-200, 200, 32), "item_health_small")
    gen.add_item((200, -200, 32), "item_health_small")
    gen.add_item((-200, -200, 32), "item_health_small")

    # === AMBIENT LIGHTING ===
    # Corner ceiling lights
    for x in [-350, 350]:
        for y in [-350, 350]:
            gen.add_light((x, y, height - 32), 200, (0.9, 0.85, 0.8))

    # Extra reactor glow lights around the core
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x = int(100 * math.cos(rad))
        y = int(100 * math.sin(rad))
        gen.add_light((x, y, 128), 150, (1.0, 0.5, 0.1))

    return gen


def show_help():
    print("Procedural Map Generator for Xonotic")
    print("")
    print("Usage: ./generate_map.py <type> <params> <name>")
    print("")
    print("Types:")
    print("  arena <width> <height> <name>     - Arena with center platform")
    print("  corridor <length> <width> <name>  - Long corridor")
    print("  box <size> <height> <name>        - Simple box room")
    print("  powercore <name>                  - RustChain PowerCore Arena (reactor + catwalks)")
    print("")
    print("Examples:")
    print("  ./generate_map.py arena 1024 256 my_arena")
    print("  ./generate_map.py corridor 2048 256 my_corridor")
    print("  ./generate_map.py box 512 256 simple_box")
    print("  ./generate_map.py powercore rustcore_arena")
    print("")
    print("Output is saved to: /home/scott/Games/Xonotic/mapping/maps/<name>.map")
    print("")
    print("Then compile with:")
    print("  ./sdk/scripts/compile_map.sh <name>")


def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    map_type = sys.argv[1].lower()
    output_dir = "/home/scott/Games/Xonotic/mapping/maps"
    os.makedirs(output_dir, exist_ok=True)

    try:
        if map_type == "arena":
            width = int(sys.argv[2])
            height = int(sys.argv[3])
            name = sys.argv[4]
            gen = generate_arena(width, height, name)

        elif map_type == "corridor":
            length = int(sys.argv[2])
            width = int(sys.argv[3])
            name = sys.argv[4]
            gen = generate_corridor(length, width, name)

        elif map_type == "box":
            size = int(sys.argv[2])
            height = int(sys.argv[3])
            name = sys.argv[4]
            gen = generate_box(size, height, name)

        elif map_type == "powercore":
            name = sys.argv[2] if len(sys.argv) > 2 else "rustcore_arena"
            gen = generate_powercore(name)

        elif map_type in ["help", "-h", "--help"]:
            show_help()
            sys.exit(0)

        else:
            print(f"Unknown map type: {map_type}")
            show_help()
            sys.exit(1)

        output_path = os.path.join(output_dir, f"{name}.map")
        gen.save(output_path)

        print("")
        print("To compile and test:")
        print(f"  cd /home/scott/Games/Xonotic/source")
        print(f"  ./sdk/scripts/compile_map.sh {name} fast")
        print(f"  ./xonotic-linux64-sdl +map {name}")

    except (IndexError, ValueError) as e:
        print(f"Error: {e}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
