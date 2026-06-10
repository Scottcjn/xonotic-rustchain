#!/bin/bash
# RustChain Xonotic DevKit - SDK Status & Setup

echo "=============================================="
echo "  RustChain Xonotic DevKit - SDK Status"
echo "=============================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_tool() {
    local name="$1"
    local cmd="$2"
    local install="$3"
    if command -v "$cmd" &>/dev/null || [ -x "$cmd" ]; then
        echo -e "  [${GREEN}OK${NC}] $name"
        return 0
    else
        echo -e "  [${RED}MISSING${NC}] $name"
        echo -e "       ${YELLOW}Install: $install${NC}"
        return 1
    fi
}

check_file() {
    local name="$1"
    local path="$2"
    if [ -f "$path" ] || [ -d "$path" ]; then
        echo -e "  [${GREEN}OK${NC}] $name"
        return 0
    else
        echo -e "  [${RED}MISSING${NC}] $name"
        return 1
    fi
}

echo "=== Core Game Tools ==="
check_tool "Xonotic Game" "/home/scott/Games/Xonotic/xonotic-linux64-sdl" "Download from xonotic.org"
check_tool "GMQCC Compiler" "/home/scott/Games/Xonotic/source/gmqcc/gmqcc" "cd source/gmqcc && make"
check_tool "IQM Tool" "/home/scott/Games/Xonotic/source/iqm/iqm" "cd source/iqm && make"
check_tool "NetRadiant" "/home/scott/Games/Xonotic/source/netradiant_1.5.0-20220628-linux-amd64/netradiant" "See DevKit docs"
check_tool "q3map2" "/home/scott/Games/Xonotic/source/netradiant_1.5.0-20220628-linux-amd64/q3map2" "Included with NetRadiant"
echo ""

echo "=== 3D Modeling & Graphics ==="
check_tool "Blender" "blender" "sudo apt install blender"
check_tool "GIMP" "gimp" "sudo apt install gimp"
check_tool "ImageMagick" "convert" "sudo apt install imagemagick"
echo ""

echo "=== Audio ==="
check_tool "Audacity" "audacity" "sudo apt install audacity"
check_tool "FFmpeg" "ffmpeg" "sudo apt install ffmpeg"
echo ""

echo "=== Development ==="
check_tool "Git" "git" "sudo apt install git"
check_tool "Make" "make" "sudo apt install build-essential"
check_tool "GCC" "gcc" "sudo apt install build-essential"
check_tool "Python3" "python3" "sudo apt install python3"
echo ""

echo "=== SDK Scripts ==="
check_file "build.sh" "/home/scott/Games/Xonotic/source/build.sh"
check_file "compile_map.sh" "/home/scott/Games/Xonotic/source/sdk/scripts/compile_map.sh"
check_file "create_prop.py" "/home/scott/Games/Xonotic/source/sdk/scripts/create_prop.py"
check_file "batch_convert_audio.sh" "/home/scott/Games/Xonotic/source/sdk/scripts/batch_convert_audio.sh"
check_file "convert_textures_dds.sh" "/home/scott/Games/Xonotic/source/sdk/scripts/convert_textures_dds.sh"
check_file "export_player_model.py" "/home/scott/Games/Xonotic/source/sdk/scripts/export_player_model.py"
echo ""

echo "=== Project Files ==="
check_file "QuakeC Source" "/home/scott/Games/Xonotic/source/qcsrc"
check_file "Hello Shield Mutator" "/home/scott/Games/Xonotic/source/qcsrc/common/mutators/mutator/hello_shield"
check_file "PK3 Build Dir" "/home/scott/Games/Xonotic/source/iqm/pk3_build"
check_file "Mapping Dir" "/home/scott/Games/Xonotic/mapping/maps"
check_file "Map Template" "/home/scott/Games/Xonotic/mapping/maps/template_deathmatch.map"
echo ""

echo "=== Documentation ==="
check_file "DevKit Manual" "/home/scott/Games/Xonotic/source/RUSTCHAIN_DEVKIT.md"
check_file "QuakeC Reference" "/home/scott/Games/Xonotic/source/sdk/docs/XONOTIC_QUAKEC_REFERENCE.md"
check_file "IQM Texturing Guide" "/home/scott/Games/Xonotic/source/iqm/XONOTIC_IQM_TEXTURING.md"
echo ""

echo "=============================================="
echo "  Quick Commands"
echo "=============================================="
echo ""
echo "  Build & Test:"
echo "    ./build.sh compile     # Compile QuakeC"
echo "    ./build.sh full        # Full rebuild + test"
echo "    ./build.sh test        # Just restart game"
echo ""
echo "  Map Editing:"
echo "    ./netradiant_*/netradiant           # Launch map editor"
echo "    ./sdk/scripts/compile_map.sh mymap  # Compile map"
echo ""
echo "  Create Props:"
echo "    ./sdk/scripts/create_prop.py box 100 50 30 crate"
echo "    ./sdk/scripts/create_prop.py desk 200 80 75 table"
echo ""
echo "  Convert Assets:"
echo "    ./sdk/scripts/batch_convert_audio.sh ./sounds ./ogg"
echo "    ./sdk/scripts/convert_textures_dds.sh ./textures ./dds"
echo ""
