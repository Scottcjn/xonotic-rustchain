#!/bin/bash
#
# Sophia Arena Launcher
# Runs Xonotic with external Sophia voice announcer
#

XONOTIC_DIR="$HOME/Games/Xonotic"
LOG_FILE="/tmp/xon_sophia.log"
ANNOUNCER_SCRIPT="$XONOTIC_DIR/data/sophia_arena/sophia_announcer.py"

echo "=========================================="
echo "    SOPHIA ARENA LAUNCHER"
echo "=========================================="

# Kill any existing instances
pkill -9 xonotic 2>/dev/null
pkill -f sophia_announcer.py 2>/dev/null
sleep 1

# Clear log file
> "$LOG_FILE"

# Start the external Sophia announcer in background
echo "[1/2] Starting Sophia Voice Announcer..."
python3 "$ANNOUNCER_SCRIPT" "$LOG_FILE" &
ANNOUNCER_PID=$!
echo "      Announcer PID: $ANNOUNCER_PID"

# Give announcer time to start
sleep 1

# Launch Xonotic with console output piped to log file
echo "[2/2] Launching Xonotic..."
echo "      Log file: $LOG_FILE"
echo ""
echo "Press Ctrl+C to stop both"
echo ""

cd "$XONOTIC_DIR"
./xonotic-linux64-sophia \
    +set developer 1 \
    +set cl_announcer sophia \
    +map warfare \
    +bot_number 4 \
    +skill 5 \
    2>&1 | tee "$LOG_FILE"

# When Xonotic exits, kill the announcer
echo ""
echo "Shutting down Sophia announcer..."
kill $ANNOUNCER_PID 2>/dev/null
echo "Done!"
