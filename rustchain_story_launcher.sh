#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

# Starts the RustChain offline story mode (Xonotic campaign system).
# Requires: maps/campaignrustchain.txt deployed to data/ or ~/.xonotic/data/.

MAP_START="elyan_labs"

# The Codex sandbox environment can forbid opening sockets and audio devices.
# These env vars reduce noisy init failures (launcher also passes -noudp/-nosound).
export SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-dummy}"

exec ./xonotic-linux64-sophia \
  -noudp \
  -nosound \
  +set sv_cheats 0 \
  +set _campaign_testrun 0 \
  +set g_campaign 1 \
  +set g_campaign_name rustchain \
  +set _campaign_name rustchain \
  +set _campaign_index 0 \
  +map "$MAP_START"
