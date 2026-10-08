#!/usr/bin/env bash

# =======================================================
#          VaniForge Neural Speech Studio (TTS)
#     Optimized for macOS Apple Silicon (Mac mini M4)
# =======================================================

set -e

# Change directory to the script location
cd "$(dirname "$0")"

# Graceful cleanup on exit
trap 'kill 0' SIGINT SIGTERM EXIT

echo "======================================================="
echo "        VaniForge Neural Speech Studio (TTS)           "
echo "   Cross-Platform • Hindi & English Voice Synthesis   "
echo "======================================================="

# Detect Apple Silicon / Architecture
ARCH=$(uname -m)
OS=$(uname -s)

echo "[INFO] Detected OS: $OS ($ARCH)"
if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    echo "[INFO] Apple Silicon detected! MPS (Metal Performance Shaders) acceleration enabled."
fi

# Detect Python 3
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 is not installed or not in PATH."
    echo "Install via Homebrew: brew install python"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -f ".venv/bin/python" ]; then
    echo "[1/3] Creating virtual environment..."
    $PY_CMD -m venv .venv
    echo "[2/3] Installing dependencies..."
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

echo "[3/3] Starting VaniForge Studio Server at http://127.0.0.1:8000..."
echo ""

# Auto open browser in macOS or Linux
if [ "$OS" = "Darwin" ]; then
    (sleep 2 && open "http://127.0.0.1:8000") &
elif command -v xdg-open >/dev/null 2>&1; then
    (sleep 2 && xdg-open "http://127.0.0.1:8000") &
fi

# Run FastAPI backend
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
