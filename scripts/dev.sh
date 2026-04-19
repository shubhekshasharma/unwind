#!/usr/bin/env bash
# scripts/dev.sh — start full dev environment with hot reload
# Usage: ./scripts/dev.sh [--no-browser]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

NO_BROWSER=false
[[ "$1" == "--no-browser" ]] && NO_BROWSER=true

echo "▶ Starting Unwind dev environment..."

# ── Mosquitto ──────────────────────────────────────────────────────────────
if ! pgrep -x mosquitto >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "  [mosquitto] starting via brew services..."
    brew services start mosquitto
    sleep 1
  else
    echo "  [mosquitto] WARNING: not running and brew not found — MQTT events will be disabled"
  fi
else
  echo "  [mosquitto] already running ✓"
fi

# ── Python backend ─────────────────────────────────────────────────────────
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
else
  echo "  [backend] ERROR: venv not found. Run: python3 -m venv venv && pip install -r requirements.txt"
  exit 1
fi

echo "  [backend] starting on http://localhost:8000..."
python backend/main.py &
BACKEND_PID=$!

sleep 1

# Verify backend started
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "  [backend] ERROR: failed to start"
  exit 1
fi
echo "  [backend] running (pid $BACKEND_PID) ✓"

# ── Frontend dev server ────────────────────────────────────────────────────
cd frontend
echo "  [frontend] installing deps if needed..."
npm install --silent

echo "  [frontend] starting dev server on http://localhost:5173..."
npm run dev &
FRONTEND_PID=$!
cd ..

sleep 2
echo ""
echo "  ┌──────────────────────────────────────────┐"
echo "  │  Unwind dev environment ready             │"
echo "  │  App:     http://localhost:5173           │"
echo "  │  API:     http://localhost:8000           │"
echo "  │  MQTT:    localhost:1883                  │"
echo "  └──────────────────────────────────────────┘"
echo ""

# Open browser
if [ "$NO_BROWSER" = false ]; then
  if command -v open >/dev/null 2>&1; then
    open http://localhost:5173
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:5173
  fi
fi

# Clean up all processes on exit
trap "echo ''; echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; brew services stop mosquitto 2>/dev/null; exit 0" INT TERM

wait $BACKEND_PID
