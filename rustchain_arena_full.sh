#!/bin/bash
# RustChain Arena - Full Launch Script
# Integrates: Game + Discord Bridge + Bot AI (ML & LLM)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Load config
[ -f arena_config.sh ] && source arena_config.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ██████╗ ██╗   ██╗███████╗████████╗ ██████╗██╗  ██╗ █████╗ ██╗  ║
║   ██╔══██╗██║   ██║██╔════╝╚══██╔══╝██╔════╝██║  ██║██╔══██╗██║  ║
║   ██████╔╝██║   ██║███████╗   ██║   ██║     ███████║███████║██║  ║
║   ██╔══██╗██║   ██║╚════██║   ██║   ██║     ██╔══██║██╔══██║██║  ║
║   ██║  ██║╚██████╔╝███████║   ██║   ╚██████╗██║  ██║██║  ██║██║  ║
║   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ║
║                         ARENA                                     ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${GREEN}[System] Starting RustChain Arena...${NC}"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}[System] Shutting down...${NC}"

    # Kill all background processes
    [ -n "$DISCORD_PID" ] && kill $DISCORD_PID 2>/dev/null && echo "  Stopped Discord bridge"
    [ -n "$ML_PID" ] && kill $ML_PID 2>/dev/null && echo "  Stopped ML trainer"
    [ -n "$LLM_PID" ] && kill $LLM_PID 2>/dev/null && echo "  Stopped LLM brain"

    echo -e "${GREEN}[System] Goodbye!${NC}"
    exit 0
}
trap cleanup EXIT INT TERM

# Start Discord bridge
echo -e "${CYAN}[1/4] Starting Discord bridge...${NC}"
if [ -f "rustchain_discord_bridge.py" ]; then
    PYTHONUNBUFFERED=1 python3 rustchain_discord_bridge.py > /tmp/arena_discord.log 2>&1 &
    DISCORD_PID=$!
    echo "  PID: $DISCORD_PID"
else
    echo "  ${YELLOW}Warning: Discord bridge not found${NC}"
fi

# Start ML bot trainer
echo -e "${CYAN}[2/4] Starting ML bot trainer...${NC}"
if [ -f "rustchain_bot_ml.py" ]; then
    PYTHONUNBUFFERED=1 python3 rustchain_bot_ml.py > /tmp/arena_ml.log 2>&1 &
    ML_PID=$!
    echo "  PID: $ML_PID"
else
    echo "  ${YELLOW}Warning: ML trainer not found${NC}"
fi

# Start LLM bot brain (optional - needs Ollama)
echo -e "${CYAN}[3/4] Starting LLM bot brain...${NC}"
if [ -f "rustchain_bot_brain.py" ]; then
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        PYTHONUNBUFFERED=1 python3 rustchain_bot_brain.py > /tmp/arena_llm.log 2>&1 &
        LLM_PID=$!
        echo "  PID: $LLM_PID (Ollama connected)"
    else
        echo "  ${YELLOW}Skipped: Ollama not running (install with: curl -fsSL https://ollama.ai/install.sh | sh)${NC}"
    fi
else
    echo "  ${YELLOW}Warning: LLM brain not found${NC}"
fi

# Wait for bridges to initialize
sleep 2

# Launch Xonotic
echo -e "${CYAN}[4/4] Launching Xonotic...${NC}"
echo ""

./xonotic-linux64-sdl \
    +exec rustcore_bots.cfg \
    +log_file "server.log" \
    +sv_eventlog 1 \
    +sv_logscores_console 1 \
    +sv_public 0 \
    +rcon_password "rustchain" \
    +rcon_secure 0 \
    +map rustcore

# When game exits, show session stats
echo -e "\n${CYAN}═══════ SESSION STATS ═══════${NC}"
if [ -f "/tmp/arena_ml.log" ]; then
    tail -20 /tmp/arena_ml.log | grep -E "BOT|STATS|decisions" || true
fi
if [ -f "rustchain_rewards.db" ]; then
    echo -e "\n${GREEN}RTC Rewards:${NC}"
    sqlite3 rustchain_rewards.db "SELECT player, SUM(CAST(amount AS REAL)) as rtc FROM rewards GROUP BY player ORDER BY rtc DESC LIMIT 5;" 2>/dev/null || true
fi

# Show progression
if [ -f "rustchain_progression.py" ]; then
    python3 rustchain_progression.py ${PLAYER_NAME:-Player}
fi
