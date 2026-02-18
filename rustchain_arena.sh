#!/bin/bash
# RustChain Arena - Full Launcher

cd "$(dirname "$0")"

# Load config
[ -f arena_config.sh ] && source arena_config.sh

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║            RUSTCHAIN ARENA - Play to Earn RTC             ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  Kill: 0.001 RTC    │  Win: 0.01 RTC                      ║"
echo "║  Boris Kill: +0.002 │  Sophia Kill: +0.002                ║"
echo "║  Killstreak 5: +0.005 │ Rampage 10: +0.01                 ║"
echo "╠═══════════════════════════════════════════════════════════╣"
if [ -n "$DISCORD_WEBHOOK" ]; then
echo "║  📡 Discord: Connected                                    ║"
else
echo "║  📡 Discord: Not configured (edit arena_config.sh)        ║"
fi
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Start Discord bridge in background
echo "[*] Starting rewards bridge..."
python3 rustchain_discord_bridge.py &
BRIDGE_PID=$!
sleep 1

# Launch game
echo "[*] Launching RustChain Arena..."
./xonotic-linux64-sdl \
    +log_file "server.log" \
    +sv_public 0 \
    +minplayers 4 \
    +skill 5 \
    +map rustcore \
    "$@"

# Cleanup
echo "[*] Stopping bridge..."
kill $BRIDGE_PID 2>/dev/null
wait $BRIDGE_PID 2>/dev/null

echo ""
echo "[*] Session complete! Check your stats:"
python3 rustchain_progression.py ${PLAYER_NAME:-Scott}
