#!/bin/bash
# Compile a map for Xonotic using q3map2
# Usage: ./compile_map.sh mapname [fast|full|final]
#
# Modes:
#   fast  - Quick compile for testing (no vis, fast light)
#   full  - Normal compile (vis + light)
#   final - Release quality (vis + high quality light)

MAP_NAME="$1"
MODE="${2:-full}"
Q3MAP2="/home/scott/Games/Xonotic/source/netradiant_1.5.0-20220628-linux-amd64/q3map2"
XONOTIC_DIR="/home/scott/Games/Xonotic"
MAP_DIR="$XONOTIC_DIR/mapping/maps"
OUTPUT_DIR="$XONOTIC_DIR/data/maps"

if [ -z "$MAP_NAME" ]; then
    echo "Usage: $0 mapname [fast|full|final]"
    echo ""
    echo "Modes:"
    echo "  fast  - Quick test compile (30 sec)"
    echo "  full  - Normal compile (2-5 min)"
    echo "  final - Release quality (10+ min)"
    exit 1
fi

# Find map file
MAP_FILE=""
if [ -f "$MAP_NAME" ]; then
    MAP_FILE="$MAP_NAME"
elif [ -f "$MAP_DIR/$MAP_NAME.map" ]; then
    MAP_FILE="$MAP_DIR/$MAP_NAME.map"
elif [ -f "$MAP_NAME.map" ]; then
    MAP_FILE="$MAP_NAME.map"
else
    echo "ERROR: Cannot find map file: $MAP_NAME"
    exit 1
fi

echo "=============================================="
echo "  Compiling: $(basename "$MAP_FILE" .map)"
echo "  Mode: $MODE"
echo "=============================================="
echo ""

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Common q3map2 options
Q3_OPTS="-game xonotic -fs_basepath $XONOTIC_DIR -fs_game data"

# Step 1: BSP compile
echo "[1/3] BSP Compile..."
"$Q3MAP2" -bsp $Q3_OPTS -meta "$MAP_FILE"
if [ $? -ne 0 ]; then
    echo "ERROR: BSP compile failed!"
    exit 1
fi

BSP_FILE="${MAP_FILE%.map}.bsp"

# Step 2: VIS (visibility)
case "$MODE" in
    fast)
        echo "[2/3] Skipping VIS (fast mode)"
        ;;
    *)
        echo "[2/3] VIS Compile..."
        "$Q3MAP2" -vis $Q3_OPTS "$BSP_FILE"
        if [ $? -ne 0 ]; then
            echo "ERROR: VIS compile failed!"
            exit 1
        fi
        ;;
esac

# Step 3: Light
case "$MODE" in
    fast)
        echo "[3/3] Fast Lighting..."
        "$Q3MAP2" -light $Q3_OPTS -fast -samples 1 "$BSP_FILE"
        ;;
    full)
        echo "[3/3] Normal Lighting..."
        "$Q3MAP2" -light $Q3_OPTS -fast -patchshadows "$BSP_FILE"
        ;;
    final)
        echo "[3/3] High Quality Lighting..."
        "$Q3MAP2" -light $Q3_OPTS -patchshadows -samples 3 -bounce 2 "$BSP_FILE"
        ;;
esac
if [ $? -ne 0 ]; then
    echo "ERROR: LIGHT compile failed!"
    exit 1
fi

# Copy to game data
echo ""
echo "Copying to game data..."
cp "$BSP_FILE" "$OUTPUT_DIR/"

echo ""
echo "=============================================="
echo "  Compile Complete!"
echo "  Output: $OUTPUT_DIR/$(basename "$BSP_FILE")"
echo "=============================================="
echo ""
echo "Test with:"
echo "  cd $XONOTIC_DIR"
echo "  ./xonotic-linux64-sdl +developer 1 +map $(basename "$BSP_FILE" .bsp)"
