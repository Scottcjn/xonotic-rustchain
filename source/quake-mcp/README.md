# Quake/Xonotic MCP Server

**The first MCP server for Quake-engine game development!**

This MCP (Model Context Protocol) server enables AI assistants like Claude to directly interact with Xonotic/Quake game development:

- Create and edit `.map` files
- Add entities (spawns, lights, weapons, items)
- Compile maps using q3map2
- Search and read QuakeC source code
- Browse available textures
- Launch the game for testing

## Installation

### 1. Install Dependencies

```bash
cd /home/scott/Games/Xonotic/source/quake-mcp
source venv/bin/activate
# Already installed: pip install mcp fastmcp
```

### 2. Configure Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "quake-xonotic": {
      "command": "/home/scott/Games/Xonotic/source/quake-mcp/venv/bin/python",
      "args": ["/home/scott/Games/Xonotic/source/quake-mcp/quake_mcp_server.py"],
      "env": {}
    }
  }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop. The Quake/Xonotic tools should now be available.

## Available Tools

### Map Editing
- `list_maps()` - List all .map source files
- `read_map(map_name)` - Read a map file's contents
- `create_map(map_name, content)` - Create a new map
- `append_to_map(map_name, entity)` - Add an entity to existing map

### Entity Spawning
- `add_spawn_point(map, x, y, z, angle)` - Add player spawn
- `add_light(map, x, y, z, brightness, color)` - Add light
- `add_weapon(map, weapon_type, x, y, z)` - Add weapon pickup
- `add_item(map, item_type, x, y, z)` - Add health/armor

### Compilation
- `compile_map(map_name, mode)` - Compile map (fast/full/final)
- `create_mapinfo(map_name, title, author, ...)` - Create mapinfo file

### QuakeC Development
- `list_qc_files(subdir)` - List QuakeC source files
- `read_qc_file(filepath)` - Read a QuakeC file
- `search_qc(pattern)` - Search QuakeC codebase

### Textures & Resources
- `list_textures(texture_set)` - List textures in a set
- `get_valid_texture_sets()` - List all texture sets

### Game Control
- `launch_xonotic(map_name)` - Launch Xonotic with a map

## Resources

The server also provides reference documentation as MCP resources:

- `quake://textures` - Texture path reference
- `quake://entities` - Entity classname reference

## Example Usage with Claude

"Create a simple deathmatch arena with 4 spawn points, a rocket launcher in the center, and proper lighting"

Claude can then:
1. Use `create_map()` to make the base geometry
2. Use `add_spawn_point()` 4 times for player spawns
3. Use `add_weapon()` to place the rocket launcher
4. Use `add_light()` to add lighting
5. Use `compile_map()` to build the BSP
6. Use `create_mapinfo()` for game integration
7. Use `launch_xonotic()` to test it

## Built For

- **RustChain PoA FPS** - Blockchain-integrated arena shooter
- **Xonotic** - Open-source arena FPS
- **Any Quake-engine game** - DarkPlaces, Quake, etc.

## Verification

### Test the Server Standalone

```bash
cd /home/scott/Games/Xonotic/source/quake-mcp
source venv/bin/activate
python test_tools.py
```

Expected output shows available maps, texture sets, and QuakeC search results.

### Test MCP Server Startup

```bash
cd /home/scott/Games/Xonotic/source/quake-mcp
source venv/bin/activate
timeout 3 python quake_mcp_server.py || true
```

You should see the FastMCP banner with "Quake/Xonotic MCP Server".

## Troubleshooting

### Claude Desktop Not Seeing Tools

1. Verify config file exists: `cat ~/.config/claude/claude_desktop_config.json`
2. Ensure paths are absolute (no `~` or `$HOME`)
3. Restart Claude Desktop completely (quit and relaunch)

### Python Environment Issues

```bash
# Recreate venv if needed
cd /home/scott/Games/Xonotic/source/quake-mcp
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install mcp fastmcp
```

### Map Compilation Fails

Ensure q3map2 is executable:
```bash
chmod +x /home/scott/Games/Xonotic/source/netradiant_1.5.0-20220628-linux-amd64/q3map2
```

## Directory Structure

```
/home/scott/Games/Xonotic/
├── source/
│   ├── quake-mcp/              # This MCP server
│   │   ├── quake_mcp_server.py # Main server
│   │   ├── test_tools.py       # Test utilities
│   │   ├── README.md           # This file
│   │   └── venv/               # Python environment
│   ├── netradiant_*/           # Contains q3map2
│   └── qcsrc/                  # QuakeC source code
├── mapping/
│   └── maps/                   # .map source files
└── data/
    └── maps/                   # Compiled .bsp files
```

## Author

Created for the RustChain DevKit project.

## Status

- [x] MCP server implemented with FastMCP
- [x] Map editing tools (create, read, append)
- [x] Entity spawning (spawns, lights, weapons, items)
- [x] q3map2 compilation integration
- [x] QuakeC code browser
- [x] Texture discovery from pk3 files
- [x] Claude Desktop configuration
- [ ] Claude Code integration (you're using it now!)
