#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       BHManager — Update Script      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check git
if [ ! -d ".git" ]; then
    echo "[✘] No .git directory found. Make sure you cloned the repo."
    exit 1
fi

# Check docker
if ! command -v docker &> /dev/null; then
    echo "[✘] Docker not found."
    exit 1
fi

echo "[+] Pulling latest changes from GitHub..."
git pull origin main
echo "[✔] Code updated."

echo ""
echo "[+] Rebuilding Docker image..."
docker compose build --no-cache
echo "[✔] Image rebuilt."

echo ""
echo "[+] Restarting manager container..."
docker compose up -d
echo "[✔] Manager restarted."

echo ""
echo "[✔] Update complete. Your instances and data are untouched."
echo "    Open http://localhost:8501"
echo ""
