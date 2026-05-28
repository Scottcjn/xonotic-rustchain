#!/bin/bash
# RustChain Arena Configuration
# Source from launchers: [ -f arena_config.sh ] && source arena_config.sh

# --- Discord ---
# Create a webhook at: Discord Server Settings > Integrations > Webhooks
export DISCORD_WEBHOOK="${DISCORD_WEBHOOK:-}"

# --- RustChain on-chain payouts ---
# Public IP of the RustChain node (Node 1, LiquidWeb VPS)
export RUSTCHAIN_API="${RUSTCHAIN_API:-https://50.28.86.131}"

# Source wallet for RTC payouts (must have balance — see balances table on node)
export RTC_SOURCE_WALLET="${RTC_SOURCE_WALLET:-founder_community}"

# Admin key for /wallet/transfer. Read from per-user secrets file (mode 600).
# Bootstrap: ssh root@.131 'grep RC_ADMIN_KEY /etc/default/rustchain | cut -d= -f2' > ~/.config/rustchain/admin_key
ADMIN_KEY_FILE="${ADMIN_KEY_FILE:-$HOME/.config/rustchain/admin_key}"
if [ -r "$ADMIN_KEY_FILE" ]; then
  export RC_ADMIN_KEY="$(tr -d '\n\r' < "$ADMIN_KEY_FILE")"
else
  # rustchain_rewards_bridge.py will warn loudly and run audit-only.
  export RC_ADMIN_KEY=""
fi

# --- LLM backend for bot_brain + announcer (see rustchain_llm_client.py) ---
# Defaults: openai backend pointing at POWER8 GPT-OSS 120B
export LLM_BACKEND="${LLM_BACKEND:-openai}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-http://100.75.100.89:8082}"
# Set LLM_BACKEND=ollama and OLLAMA_BASE_URL to switch backends.

# --- Player wallet hint (used by some launchers for local-only display) ---
export PLAYER_WALLET="${PLAYER_WALLET:-scott-victus-arena}"
