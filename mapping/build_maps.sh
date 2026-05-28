#!/bin/bash
# Build RustChain story maps via q3map2 (BSP + VIS + LIGHT stages).
# Run from the Xonotic project root or from anywhere — the script resolves
# its own location.
#
# Output: mapping/maps/<name>.bsp + .srf + .prt
# Deploy: cp -v mapping/maps/<name>.bsp data/maps/ (done automatically below)
#
# Pass --no-deploy to skip the data/maps/ copy.
# Pass MAP=<name> in env to build a single map.

set -euo pipefail

# Resolve project root from this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

Q3M="$ROOT/source/netradiant_1.5.0-20220628-linux-amd64/q3map2"
if [ ! -x "$Q3M" ]; then
    echo "ERROR: q3map2 not found at $Q3M" >&2
    echo "Expected the netradiant linux-amd64 bundle under source/" >&2
    exit 1
fi

DEPLOY=1
for arg in "$@"; do
    [ "$arg" = "--no-deploy" ] && DEPLOY=0
done

DATA_MAPS="$ROOT/data/maps"
mkdir -p "$DATA_MAPS"

if [ -n "${MAP:-}" ]; then
    MAPS=("$MAP")
else
    MAPS=(chambers_ruins elyan_labs first_signal museum_vault)
fi

start=$(date +%s)
for m in "${MAPS[@]}"; do
    src="$ROOT/mapping/maps/$m.map"
    if [ ! -f "$src" ]; then
        echo "WARN: skipping $m — $src not found"
        continue
    fi
    echo
    echo "==== $m ===="
    echo "--- BSP stage ---"
    "$Q3M" -game xonotic -fs_basepath "$ROOT" "$src" 2>&1 | tail -3
    echo "--- VIS stage ---"
    "$Q3M" -game xonotic -fs_basepath "$ROOT" -vis -saveprt "$src" 2>&1 | tail -3
    echo "--- LIGHT stage (-fast -patchshadows) ---"
    "$Q3M" -game xonotic -fs_basepath "$ROOT" -light -fast -patchshadows "$src" 2>&1 | tail -3
    bsp="$ROOT/mapping/maps/$m.bsp"
    [ -f "$bsp" ] && echo "built: $bsp ($(stat -c %s "$bsp") bytes)"
    if [ "$DEPLOY" = "1" ] && [ -f "$bsp" ]; then
        cp -v "$bsp" "$DATA_MAPS/$m.bsp"
    fi
done
elapsed=$(( $(date +%s) - start ))
echo
echo "==== all done in ${elapsed}s ===="
