#!/usr/bin/env bash
# Media Integrity / SecureCall One-Click Demo Starter (Bash)
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "=========================================================="
echo "  SECURECALL: Real-Time Multimodal Media Integrity Platform"
echo "=========================================================="

echo "[1/3] Starting Backend Server..."
./.venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 3

echo "[2/3] Checking Backend Health..."
curl -s http://localhost:8000/api/v1/health || true

echo "[3/3] Starting Frontend Server..."
cd "$DIR/frontend"
npm run start -- -p 3000 &
FRONTEND_PID=$!

echo "=========================================================="
echo "  SECURECALL PLATFORM READY"
echo "  - Frontend: http://localhost:3000"
echo "  - Call:     http://localhost:3000/call/demo-room"
echo "  - API Docs: http://localhost:8000/docs"
echo "=========================================================="

wait
