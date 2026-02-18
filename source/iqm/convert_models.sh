#!/bin/bash
# Model Conversion Pipeline for Xonotic
# Converts .blend/.fbx/.obj files to IQM format
# Usage: ./convert_models.sh [input_dir] [output_dir]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
IQM_COMPILER="$SCRIPT_DIR/iqm"
RAW_DIR="${1:-$SCRIPT_DIR/models_raw}"
FBX_DIR="$SCRIPT_DIR/models_fbx"
OUTPUT_DIR="${2:-$SCRIPT_DIR/models_converted}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  IQM Model Conversion Pipeline"
echo "=========================================="
echo "Input:  $RAW_DIR"
echo "FBX:    $FBX_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

# Check for IQM compiler
if [ ! -x "$IQM_COMPILER" ]; then
    echo -e "${RED}ERROR: IQM compiler not found at $IQM_COMPILER${NC}"
    echo "Build it with: cd $SCRIPT_DIR && make"
    exit 1
fi

# Check for Blender
BLENDER=$(which blender 2>/dev/null)
if [ -z "$BLENDER" ]; then
    echo -e "${YELLOW}WARNING: Blender not found - .blend files will be skipped${NC}"
fi

mkdir -p "$FBX_DIR" "$OUTPUT_DIR"

converted=0
failed=0
skipped=0

# Process .blend files (need Blender to export to FBX first)
if [ -n "$BLENDER" ]; then
    for blend in "$RAW_DIR"/*.blend 2>/dev/null; do
        [ -f "$blend" ] || continue
        name=$(basename "$blend" .blend)
        fbx_out="$FBX_DIR/${name}.fbx"
        iqm_out="$OUTPUT_DIR/${name}.iqm"

        echo -e "${YELLOW}[BLEND→FBX]${NC} $name"

        # Export to FBX using Blender CLI
        "$BLENDER" -b "$blend" --python-expr "
import bpy
bpy.ops.export_scene.fbx(filepath='$fbx_out', use_selection=False, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL')
" > /dev/null 2>&1

        if [ -f "$fbx_out" ]; then
            echo -e "  ${GREEN}→ FBX exported${NC}"

            # Convert FBX to IQM
            echo -e "${YELLOW}[FBX→IQM]${NC} $name"
            if "$IQM_COMPILER" "$iqm_out" "$fbx_out" 2>/dev/null; then
                echo -e "  ${GREEN}✓ Converted to IQM${NC}"
                ((converted++))
            else
                echo -e "  ${RED}✗ IQM conversion failed${NC}"
                ((failed++))
            fi
        else
            echo -e "  ${RED}✗ FBX export failed${NC}"
            ((failed++))
        fi
    done
fi

# Process .fbx files directly
for fbx in "$RAW_DIR"/*.fbx "$RAW_DIR"/*.FBX 2>/dev/null; do
    [ -f "$fbx" ] || continue
    name=$(basename "$fbx" | sed 's/\.[fF][bB][xX]$//')
    iqm_out="$OUTPUT_DIR/${name}.iqm"

    echo -e "${YELLOW}[FBX→IQM]${NC} $name"
    if "$IQM_COMPILER" "$iqm_out" "$fbx" 2>/dev/null; then
        echo -e "  ${GREEN}✓ Converted${NC}"
        ((converted++))
    else
        echo -e "  ${RED}✗ Failed${NC}"
        ((failed++))
    fi
done

# Process .obj files directly
for obj in "$RAW_DIR"/*.obj "$RAW_DIR"/*.OBJ 2>/dev/null; do
    [ -f "$obj" ] || continue
    name=$(basename "$obj" | sed 's/\.[oO][bB][jJ]$//')
    iqm_out="$OUTPUT_DIR/${name}.iqm"

    echo -e "${YELLOW}[OBJ→IQM]${NC} $name"
    if "$IQM_COMPILER" "$iqm_out" "$obj" 2>/dev/null; then
        echo -e "  ${GREEN}✓ Converted${NC}"
        ((converted++))
    else
        echo -e "  ${RED}✗ Failed${NC}"
        ((failed++))
    fi
done

echo ""
echo "=========================================="
echo "  Results"
echo "=========================================="
echo -e "  ${GREEN}Converted:${NC} $converted"
echo -e "  ${RED}Failed:${NC}    $failed"
echo -e "  ${YELLOW}Skipped:${NC}   $skipped"
echo ""

if [ $converted -gt 0 ]; then
    echo "Converted models are in: $OUTPUT_DIR"
    ls -la "$OUTPUT_DIR"/*.iqm 2>/dev/null
fi
