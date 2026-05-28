#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

LOG="/tmp/rustchain_story_smoke.log"
rm -f "$LOG"

# Quick non-interactive boot test: verifies campaign map boots with story entities.
timeout 25s ./xonotic-linux64-sophia \
  -nosound \
  +set g_campaign 1 \
  +set g_campaign_name rustchain \
  +set _campaign_name rustchain \
  +set _campaign_index 0 \
  +set sv_cheats 0 \
  +map elyan_labs >"$LOG" 2>&1 || true

echo "Spawn sequence observed:"
rg -n "SpawnServer:" "$LOG" | sed -n '1,20p'

echo
echo "Story entity load summary:"
rg -n "new entities parsed|target_rustchain_|campaign initialization failed|ERROR in CampaignBailout" "$LOG" | sed -n '1,40p' || true

echo
echo "Smoke log: $LOG"
