#!/bin/bash
# RustChain Xonotic DevKit - Master Build Script
# Usage: ./build.sh [command]
#   compile   - Compile QuakeC only
#   assets    - Build PK3 only
#   full      - Compile + build PK3 + restart game
#   test      - Restart game only
#   clean     - Clean build artifacts

set -e
set -o pipefail

# Paths
XONOTIC_DIR="/home/scott/Games/Xonotic"
SOURCE_DIR="$XONOTIC_DIR/source"
QCSRC_DIR="$SOURCE_DIR/qcsrc"
IQM_DIR="$SOURCE_DIR/iqm"
PK3_BUILD="$IQM_DIR/pk3_build"
GMQCC="$SOURCE_DIR/gmqcc/gmqcc"
DATA_DIR="$XONOTIC_DIR/data"
USER_DATA="$HOME/.xonotic/data"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Compile QuakeC
compile_qc() {
    log_info "Compiling QuakeC..."
    cd "$QCSRC_DIR"
    make QCC="$GMQCC" 2>&1 | tail -5
    rc=${PIPESTATUS[0]}
    if [ "$rc" -ne 0 ]; then
        log_error "QuakeC compile failed (make exit $rc)"
        exit "$rc"
    fi

    log_info "Deploying progs.dat..."
    cp "$SOURCE_DIR/progs.dat" "$USER_DATA/"
    cp "$SOURCE_DIR/progs.dat" "$DATA_DIR/"

    log_info "QuakeC compiled and deployed!"
}

# Build PK3 assets
build_assets() {
    log_info "Building PK3 assets..."
    cd "$PK3_BUILD"

    PK3_NAME="zzz_hello_props.pk3"
    rm -f "$IQM_DIR/$PK3_NAME"
    zip -r "$IQM_DIR/$PK3_NAME" . -x "*.git*"

    cp "$IQM_DIR/$PK3_NAME" "$USER_DATA/"
    cp "$IQM_DIR/$PK3_NAME" "$DATA_DIR/"

    log_info "PK3 built and deployed: $PK3_NAME"
}

# Deploy story/campaign files
deploy_story() {
    local STORY_SRC="$XONOTIC_DIR/story/maps/campaignrustchain.txt"
    local DST_DATA="$DATA_DIR/maps/campaignrustchain.txt"
    local DST_USER="$USER_DATA/maps/campaignrustchain.txt"

    if [ ! -f "$STORY_SRC" ]; then
        log_warn "Story campaign file not found: $STORY_SRC"
        return 0
    fi

    log_info "Deploying RustChain story campaign..."
    mkdir -p "$DATA_DIR/maps" "$USER_DATA/maps"
    cp "$STORY_SRC" "$DST_DATA"
    cp "$STORY_SRC" "$DST_USER"
    log_info "Campaign deployed: maps/campaignrustchain.txt"
}

# Convert OBJ to IQM
convert_models() {
    log_info "Converting models..."
    cd "$IQM_DIR"

    for obj in models_converted/*.obj; do
        if [ -f "$obj" ]; then
            name=$(basename "$obj" .obj)
            ./iqm "pk3_build/models/props/${name}.iqm" "$obj"
            log_info "  Converted: $name"
        fi
    done
}

# Restart game
restart_game() {
    log_info "Restarting Xonotic..."
    pkill -9 xonotic 2>/dev/null || true
    sleep 1

    cd "$XONOTIC_DIR"
    ./xonotic-linux64-sdl +skill 1 +bot_number 3 +map warfare &>/dev/null &

    log_info "Xonotic launched!"
}

# Clean build
clean_build() {
    log_info "Cleaning build artifacts..."
    rm -f "$SOURCE_DIR/progs.dat"
    rm -f "$SOURCE_DIR/progs.lno"
    rm -f "$IQM_DIR/zzz_*.pk3"
    log_info "Clean complete!"
}

# Show help
show_help() {
    echo "RustChain Xonotic DevKit - Build Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  compile   Compile QuakeC and deploy progs.dat"
    echo "  assets    Build PK3 from pk3_build directory"
    echo "  story     Deploy RustChain offline story campaign file"
    echo "  models    Convert all OBJ files to IQM"
    echo "  full      Compile + assets + restart game"
    echo "  test      Restart game only"
    echo "  clean     Remove build artifacts"
    echo "  help      Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 compile    # Quick compile and deploy"
    echo "  $0 full       # Full rebuild and test"
}

# Main
case "${1:-help}" in
    compile)
        compile_qc
        ;;
    assets)
        build_assets
        ;;
    story)
        deploy_story
        ;;
    models)
        convert_models
        ;;
    full)
        compile_qc
        build_assets
        deploy_story
        restart_game
        ;;
    test)
        restart_game
        ;;
    clean)
        clean_build
        ;;
    help|*)
        show_help
        ;;
esac
