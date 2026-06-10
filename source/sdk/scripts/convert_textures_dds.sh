#!/bin/bash
# Convert PNG/TGA textures to DDS (GPU-compressed) for faster loading
# Usage: ./convert_textures_dds.sh [input_dir] [output_dir]
#
# Requires: ImageMagick (convert) or nvcompress (NVIDIA Texture Tools)

INPUT_DIR="${1:-.}"
OUTPUT_DIR="${2:-./dds}"

mkdir -p "$OUTPUT_DIR"

echo "Converting textures to DDS format..."
echo "Input:  $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

# Check for nvcompress (best quality)
if command -v nvcompress &>/dev/null; then
    echo "Using NVIDIA Texture Tools (nvcompress)"
    TOOL="nvcompress"
else
    echo "Using ImageMagick (install nvidia-texture-tools for better quality)"
    TOOL="convert"
fi

count=0
for img in "$INPUT_DIR"/*.{png,tga,PNG,TGA} 2>/dev/null; do
    [ -f "$img" ] || continue

    name=$(basename "$img")
    base="${name%.*}"
    output="$OUTPUT_DIR/${base}.dds"

    echo "  Converting: $name -> ${base}.dds"

    if [ "$TOOL" = "nvcompress" ]; then
        # DXT5 for textures with alpha, DXT1 for opaque
        if identify "$img" | grep -q "RGBA"; then
            nvcompress -bc3 "$img" "$output" 2>/dev/null
        else
            nvcompress -bc1 "$img" "$output" 2>/dev/null
        fi
    else
        # ImageMagick fallback (less optimal but works)
        convert "$img" -define dds:compression=dxt5 "$output" 2>/dev/null
    fi

    ((count++))
done

echo ""
echo "Converted $count textures to DDS format"
