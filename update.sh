#!/bin/bash

set -e

main() {
    local SCRIPT_DIR
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"

    local GITHUB_REPO="B3XAL/BHManager"
    local RAW_BASE="https://raw.githubusercontent.com/${GITHUB_REPO}/main"

    echo ""
    echo "╔══════════════════════════════════════╗"
    echo "║       BHManager — Update Script      ║"
    echo "╚══════════════════════════════════════╝"
    echo ""

    if ! command -v docker &> /dev/null; then
        echo "[✘] Docker not found."
        exit 1
    fi

    echo "[+] Downloading latest app.py from GitHub..."
    wget -q -O app.py "${RAW_BASE}/app.py"
    echo "[✔] app.py updated."

    echo "[+] Downloading latest update.sh from GitHub..."
    wget -q -O update.sh.tmp "${RAW_BASE}/update.sh"
    chmod +x update.sh.tmp
    echo "[✔] update.sh downloaded (will replace after script finishes)."

    echo "[+] Downloading latest requirements.txt from GitHub..."
    wget -q -O requirements.txt "${RAW_BASE}/requirements.txt"
    echo "[✔] requirements.txt updated."

    echo "[+] Downloading latest Dockerfile from GitHub..."
    wget -q -O Dockerfile "${RAW_BASE}/Dockerfile"
    echo "[✔] Dockerfile updated."

    echo "[+] Downloading latest docker-compose.yml from GitHub..."
    wget -q -O docker-compose.yml "${RAW_BASE}/docker-compose.yml"
    echo "[✔] docker-compose.yml updated."

    echo ""
    echo "[+] Stopping existing container..."
    local INSTANCES_PATH
    INSTANCES_PATH=$(docker inspect bhce-manager --format '{{range .Mounts}}{{if eq .Destination "/bhce-instances"}}{{.Source}}{{end}}{{end}}' 2>/dev/null || echo "")
    if [ -z "$INSTANCES_PATH" ]; then
        INSTANCES_PATH="/opt/BHManager/instances"
    fi
    docker stop bhce-manager 2>/dev/null || true
    docker rm bhce-manager 2>/dev/null || true
    sleep 5
    echo "[✔] Container stopped."

    echo ""
    echo "[+] Rebuilding Docker image..."
    docker compose build
    echo "[✔] Image rebuilt."

    echo ""
    echo "[+] Starting updated container..."
    local started=false
    for attempt in 1 2 3; do
        if docker run -d \
            --name bhce-manager \
            --restart unless-stopped \
            -p 8501:8501 \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v "${INSTANCES_PATH}:/bhce-instances" \
            -e PYTHONUNBUFFERED=1 \
            -e STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2048 \
            --user root \
            app-bhce-manager 2>/dev/null; then
            started=true
            break
        fi
        docker rm bhce-manager 2>/dev/null || true
        echo "[!] Port busy, retrying in 5 seconds... (attempt ${attempt}/3)"
        sleep 5
    done
    sleep 2
    if $started && docker ps --filter "name=^bhce-manager$" --filter "status=running" -q | grep -q .; then
        echo "[✔] Container started."
    else
        echo "[✘] Container failed to start after 3 attempts."
        exit 1
    fi

    echo ""
    echo "[✔] Update complete. Your instances and data are untouched."
    echo "    Open http://localhost:8501"
    echo ""

    mv update.sh.tmp update.sh
}

main
