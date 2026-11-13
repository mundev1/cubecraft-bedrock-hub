#!/usr/bin/env bash
# ==============================================================================
# CubeCraft Bedrock Official Discord Bot Runner
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

echo "Starting CubeCraft Bedrock Discord Bot..."
exec .venv/bin/python3 discord_bot.py
