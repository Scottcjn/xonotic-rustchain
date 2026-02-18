#!/bin/bash
set -e

# RustChain Arena Docker Entrypoint

echo "Initializing RustChain Arena Server..."

# Ensure data directory exists and has permissions
mkdir -p /opt/xonotic/data

# Function to handle shutdown signals
cleanup() {
    echo "Stopping services..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}
trap cleanup SIGTERM SIGINT

# Start Discord Bridge if configured
if [ -n "$DISCORD_TOKEN" ] && [ -f "rustchain_discord_bridge.py" ]; then
    echo "[Bridge] Starting Discord integration..."
    python3 rustchain_discord_bridge.py > /var/log/discord_bridge.log 2>&1 &
fi

# Start Bot ML Trainer
if [ "$ENABLE_ML" = "true" ] && [ -f "rustchain_bot_ml.py" ]; then
    echo "[AI] Starting ML Bot Trainer..."
    python3 rustchain_bot_ml.py > /var/log/bot_ml.log 2>&1 &
fi

# Start LLM Bot Brain (requires Ollama)
if [ "$ENABLE_LLM" = "true" ] && [ -f "rustchain_bot_brain.py" ]; then
    if [ -n "$OLLAMA_HOST" ]; then
        echo "[AI] Starting LLM Bot Brain (Ollama: $OLLAMA_HOST)..."
        # Ensure script knows where to look if it uses env vars, otherwise we rely on network alias
        python3 rustchain_bot_brain.py > /var/log/bot_brain.log 2>&1 &
    else
        echo "[AI] OLLAMA_HOST not set, skipping LLM Brain."
    fi
fi

# Start Rewards Bridge (if separate)
if [ -f "rustchain_rewards_bridge.py" ]; then
    echo "[Economy] Starting Rewards Bridge..."
    python3 rustchain_rewards_bridge.py > /var/log/rewards.log 2>&1 &
fi

# Launch Xonotic Dedicated Server
echo "[Server] Launching Xonotic..."
# We use exec to let Xonotic take PID 1 if it was the only thing, 
# but here we have background jobs, so we run it in foreground and wait.
./xonotic-linux64-dedicated \
    -userdir /opt/xonotic/data \
    "$@" &

# Wait for Xonotic
wait $!
