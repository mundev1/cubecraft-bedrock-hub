#!/usr/bin/env bash
set -e

echo "=================================================="
echo "🚀 Starting CubeCraft Bedrock Hub & Discord Bot"
echo "=================================================="

PORT=${PORT:-7860}

# 1. Start Discord Bot in the background (if token configured)
if [ -n "$DISCORD_BOT_TOKEN" ]; then
    echo "🤖 Starting CubeCraft Bedrock Discord Bot..."
    python3 discord_bot.py &
    BOT_PID=$!
    echo "✅ Discord Bot launched (PID: $BOT_PID)"
else
    echo "⚠️ DISCORD_BOT_TOKEN is not set. Discord Bot skipped."
fi

# 2. Trap signals for graceful shutdown of background processes
cleanup() {
    echo "Stopping background processes..."
    if [ -n "$BOT_PID" ]; then
        kill -TERM "$BOT_PID" 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

# 3. Start Flask Web Server in the foreground
echo "🌐 Starting Flask Server on 0.0.0.0:${PORT:-5055}..."
exec python3 server.py
