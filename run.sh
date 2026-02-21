#!/usr/bin/env bash
# Install dependencies and run the server (Mac/Linux)
# Usage: ./run.sh

set -e
cd "$(dirname "$0")"

echo "Installing dependencies..."
pip install -q -r requirements.txt 2>/dev/null || pip3 install -q -r requirements.txt

echo "Starting server at http://127.0.0.1:8000"
echo "Press Ctrl+C to stop."
python -m uvicorn main:app --host 127.0.0.1 --port 8000 2>/dev/null || python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
