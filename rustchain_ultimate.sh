#!/bin/bash
# RustChain Arena - Ultimate Launcher
# Full system with Style Ranks, Announcer, RTC Rewards

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
PURPLE='\033[0;35m'
NC='\033[0m'

clear
echo -e "${PURPLE}"
cat << 'BANNER'
    ____             __  ________          _
   / __ \__  _______/ /_/ ____/ /_  ____ _(_)___
  / /_/ / / / / ___/ __/ /   / __ \/ __ `/ / __ \
 / _, _/ /_/ (__  ) /_/ /___/ / / / /_/ / / / / /
/_/ |_|\__,_/____/\__/\____/_/ /_/\__,_/_/_/ /_/

     █████╗ ██████╗ ███████╗███╗   ██╗ █████╗
    ██╔══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗
    ███████║██████╔╝█████╗  ██╔██╗ ██║███████║
    ██╔══██║██╔══██╗██╔══╝  ██║╚██╗██║██╔══██║
    ██║  ██║██║  ██║███████╗██║ ╚████║██║  ██║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝

           ★ ULTIMATE EDITION ★
BANNER
echo -e "${NC}"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Features:${NC}"
echo -e "    ✦ Style Rank System (D → SSS SATOSHI)"
echo -e "    ✦ Blood Economy (Heal through Violence)"
echo -e "    ✦ Blockchain Weapons (Forker, Validator, Hashcannon)"
echo -e "    ✦ RTC Multipliers (1x → 5x)"
echo -e "    ✦ Dynamic Sophia Announcer"
echo -e "    ✦ Combo & Killstreak Rewards"
echo -e "    ✦ 51% Attack Game Mode"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}[System] Shutting down all systems...${NC}"
    [ -n "$MASTER_PID" ] && kill $MASTER_PID 2>/dev/null && echo "  ✓ Game Master stopped"
    [ -n "$ML_PID" ] && kill $ML_PID 2>/dev/null && echo "  ✓ ML Trainer stopped"
    [ -n "$REWARDS_PID" ] && kill $REWARDS_PID 2>/dev/null && echo "  ✓ Rewards bridge stopped"
    echo -e "${GREEN}[System] Goodbye!${NC}"
    exit 0
}
trap cleanup EXIT INT TERM

# Check for Ollama (optional)
echo -e "${CYAN}[1/3] Checking LLM availability...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Ollama connected - Dynamic announcer enabled${NC}"
    export OLLAMA_AVAILABLE=1
else
    echo -e "  ${YELLOW}○ Ollama not running - Using fallback announcer${NC}"
    echo -e "    (Optional: curl -fsSL https://ollama.ai/install.sh | sh)"
fi

# Start Game Master (includes Style, Announcer, Rewards)
echo -e "${CYAN}[2/3] Starting Game Master...${NC}"
PYTHONUNBUFFERED=1 python3 rustchain_game_master.py &
MASTER_PID=$!
echo -e "  ${GREEN}✓ Game Master started (PID: $MASTER_PID)${NC}"


# Start RTC rewards bridge (on-chain payouts)
echo -e "${CYAN}[2.5/3] Starting RTC rewards bridge...${NC}"
if [ -f "rustchain_rewards_bridge.py" ]; then
    PYTHONUNBUFFERED=1 python3 rustchain_rewards_bridge.py > /tmp/arena_rewards.log 2>&1 &
    REWARDS_PID=$!
    echo -e "  ${GREEN}✓ Rewards bridge started (PID: $REWARDS_PID)${NC}"
fi

# Optional: Start ML Bot Trainer
if [ -f "rustchain_bot_ml.py" ]; then
    echo -e "${CYAN}[3/3] Starting ML Bot Trainer...${NC}"
    PYTHONUNBUFFERED=1 python3 rustchain_bot_ml.py > /tmp/arena_ml.log 2>&1 &
    ML_PID=$!
    echo -e "  ${GREEN}✓ ML Trainer started (PID: $ML_PID)${NC}"
fi

# Wait for systems to initialize
sleep 2

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  STYLE RANK MULTIPLIERS:${NC}"
echo -e "    D DORMANT     ${CYAN}1.0x${NC} - Default state"
echo -e "    C CALCULATING ${CYAN}1.2x${NC} - Getting started"
echo -e "    B BUILDING    ${GREEN}1.5x${NC} - Building momentum"
echo -e "    A ATTACKING   ${YELLOW}2.0x${NC} - Aggressive play"
echo -e "    S STAKING     ${PURPLE}3.0x${NC} - Dominating"
echo -e "    SS SLASHING   ${RED}4.0x${NC} - On fire!"
echo -e "    ✦ SATOSHI ✦   ${YELLOW}5.0x${NC} - LEGENDARY"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}  BLOOD ECONOMY:${NC}"
echo -e "    💉 Shields regenerate ONLY through violence"
echo -e "    🔪 Close range combat = 3x shield gain"
echo -e "    ⚔️  Melee kills grant +50 instant shield"
echo -e "    ⏳ Hiding? Your shields DECAY after 5 seconds"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}  BLOCKCHAIN WEAPONS:${NC}"
echo -e "    🔫 The Forker      - Multi-target shotgun"
echo -e "    📍 The Validator   - Teleport node + scan"
echo -e "    ⛏️  The Hashcannon  - Charge for instakill"
echo -e "    💣 Mempool Grenade - Delayed explosion"
echo -e "    💸 Double-Spend    - Free shot after kill"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}Launching Xonotic...${NC}"
echo ""

# Launch Xonotic
./xonotic-linux64-sophia \
    +exec rustcore_bots.cfg \
    +log_file "server.log" \
    +sv_eventlog 1 \
    +sv_logscores_console 1 \
    +sv_public 0 \
    +rcon_password "rustchain" \
    +rcon_secure 0 \
    +minplayers 4 \
    +skill 6 \
    +map rustcore

# Show final stats
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  SESSION COMPLETE${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Show RTC earnings
if [ -f "rustchain_rewards.db" ]; then
    echo -e "\n${GREEN}  TOP RTC EARNERS:${NC}"
    sqlite3 rustchain_rewards.db "SELECT player, printf('%.4f', SUM(CAST(amount AS REAL))) as rtc FROM rewards WHERE timestamp > datetime('now', '-1 hour') GROUP BY player ORDER BY rtc DESC LIMIT 5;" 2>/dev/null | while read line; do
        player=$(echo $line | cut -d'|' -f1)
        rtc=$(echo $line | cut -d'|' -f2)
        echo "    $player: $rtc RTC"
    done
fi

echo ""
