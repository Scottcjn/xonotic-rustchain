#!/bin/bash
# RustChain Arena Launcher
# Starts Xonotic with custom bots and RTC rewards bridge

XONOTIC_DIR="$HOME/Games/Xonotic"
cd "$XONOTIC_DIR"

echo "╔══════════════════════════════════════════════════╗"
echo "║       RUSTCHAIN ARENA - Earn RTC Gaming!        ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Kill Reward:     0.001 RTC                     ║"
echo "║  Win Reward:      0.01 RTC                      ║"
echo "║  Kill Boris:      +0.002 RTC bonus              ║"
echo "║  Kill Sophia:     +0.002 RTC bonus              ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Bots: Boris_Volkov, Sophia_Elya, Miner_Node1   ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Start rewards bridge in background
echo "[*] Starting RTC Rewards Bridge..."
python3 rustchain_rewards_bridge.py &
BRIDGE_PID=$!

# Give bridge time to start
sleep 1

# Launch Xonotic with custom settings
echo "[*] Launching RustChain Arena..."
./xonotic-linux64-sdl \
    +log_file "server.log" \
    +exec bots_rustchain.cfg \
    +bot_number 3 \
    +g_bot_names "Boris_Volkov Sophia_Elya Miner_Node1" \
    +minplayers 4 \
    +map rustcore \
    "$@"

# Cleanup
echo "[*] Shutting down rewards bridge..."
kill $BRIDGE_PID 2>/dev/null

echo "[*] Session ended. Check your RTC rewards!"
python3 rustchain_progression.py
