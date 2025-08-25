#!/bin/bash

# Move to the script's directory
cd "$(dirname "$0")" || exit 1

# Kill any process using port 5001 (macOS/Linux)
echo "[INFO] Killing any process using port 5001..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
sleep 1

# Activate virtual environment if exists
if [ -f "../venv/bin/activate" ]; then
    echo "[INFO] Activating virtual environment..."
    source ../venv/bin/activate
else
    echo "[WARNING] Virtual environment not found at ../venv/bin/activate."
fi

# Run the Flask/SocketIO app on port 5001
echo "[INFO] Starting simple_pipeline_api.py on port 5001..."
python3 simple_pipeline_api.py
