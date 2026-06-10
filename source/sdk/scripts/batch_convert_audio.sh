#!/bin/bash
# Batch convert audio files to OGG Vorbis for Xonotic
# Usage: ./batch_convert_audio.sh [input_dir] [output_dir] [quality]
#
# Quality: 0-10 (default 6, higher = better quality, larger file)

INPUT_DIR="${1:-.}"
OUTPUT_DIR="${2:-./ogg}"
QUALITY="${3:-6}"

mkdir -p "$OUTPUT_DIR"

echo "Converting audio to OGG Vorbis..."
echo "Input:   $INPUT_DIR"
echo "Output:  $OUTPUT_DIR"
echo "Quality: $QUALITY"
echo ""

count=0
for audio in "$INPUT_DIR"/*.{wav,mp3,flac,aiff,WAV,MP3,FLAC,AIFF} 2>/dev/null; do
    [ -f "$audio" ] || continue

    name=$(basename "$audio")
    base="${name%.*}"
    output="$OUTPUT_DIR/${base}.ogg"

    echo "  Converting: $name -> ${base}.ogg"

    # Convert to mono for 3D sounds, preserve stereo for music
    # Detect if stereo
    channels=$(ffprobe -v error -select_streams a:0 -show_entries stream=channels -of csv=p=0 "$audio" 2>/dev/null)

    if [ "$channels" = "2" ] && [[ "$name" == *music* || "$name" == *ambient* ]]; then
        # Keep stereo for music/ambient
        ffmpeg -y -i "$audio" -c:a libvorbis -q:a "$QUALITY" "$output" 2>/dev/null
    else
        # Convert to mono for 3D positional sounds
        ffmpeg -y -i "$audio" -c:a libvorbis -q:a "$QUALITY" -ac 1 "$output" 2>/dev/null
    fi

    ((count++))
done

echo ""
echo "Converted $count audio files to OGG Vorbis"
echo ""
echo "Recommended locations in PK3:"
echo "  sound/weapons/     - Weapon sounds"
echo "  sound/player/      - Player sounds (jump, land, pain)"
echo "  sound/ambient/     - Ambient/environmental loops"
echo "  sound/announcer/   - Announcer voices"
echo "  sound/misc/        - Other sounds"
