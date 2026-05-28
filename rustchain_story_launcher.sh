#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

# Starts the RustChain offline story mode (Xonotic campaign system).
# Requires: maps/campaignrustchain.txt deployed to data/ or ~/.xonotic/data/.

# Load env (LLM backend, RTC config, RCON password)
[ -f arena_config.sh ] && source arena_config.sh

MAP_START="elyan_labs"

# Story-mode launcher uses RCON for the dialogue director, so we need a
# password and an internal-only socket. Override only if not already set
# by arena_config.sh.
export XONOTIC_RCON_PASSWORD="${XONOTIC_RCON_PASSWORD:-rustchain}"
export XONOTIC_RCON_HOST="${XONOTIC_RCON_HOST:-127.0.0.1}"
export XONOTIC_RCON_PORT="${XONOTIC_RCON_PORT:-26000}"

# Note: -noudp disables network — sockets aren't bound, so RCON injection
# can't happen. The smoke test (story_smoke_test.sh) keeps -noudp/-nosound
# for headless boot validation. The interactive story launcher needs UDP +
# sound, so DON'T set them here.

# Start the dialogue director in the background BEFORE the game so it's
# tailing the log when the first dialogue trigger fires.
if [ -f rustchain_dialogue_director.py ]; then
  echo "[story] starting LLM dialogue director (backend=${LLM_BACKEND:-openai})"
  PYTHONUNBUFFERED=1 python3 rustchain_dialogue_director.py \
    > /tmp/rustchain_dialogue_director.log 2>&1 &
  DIRECTOR_PID=$!
  trap "kill $DIRECTOR_PID 2>/dev/null || true" EXIT
fi

exec ./xonotic-linux64-sophia \
  +set sv_cheats 0 \
  +set _campaign_testrun 0 \
  +set g_campaign 1 \
  +set g_campaign_name rustchain \
  +set _campaign_name rustchain \
  +set _campaign_index 0 \
  +set rcon_password "$XONOTIC_RCON_PASSWORD" \
  +set rcon_secure 0 \
  +set net_address "$XONOTIC_RCON_HOST" \
  +set port "$XONOTIC_RCON_PORT" \
  +map "$MAP_START"
