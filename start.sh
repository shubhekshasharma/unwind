#!/usr/bin/env bash
# Unwind startup script — works on both Raspberry Pi and macOS dev machine.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if present
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

# Verify frontend is built
if [ ! -f "frontend/dist/index.html" ]; then
  echo "[Unwind] frontend/dist not found — building now..."
  cd frontend
  npm install
  npm run build
  cd ..
fi

# Start Python backend in background
echo "[Unwind] Starting backend on http://localhost:8000"
python backend/main.py &
BACKEND_PID=$!

# Give backend a moment to start
sleep 2

# Kill any existing Chromium instance pointing at this app before relaunching
pkill -f "chromium.*localhost:8000" 2>/dev/null || true
sleep 1

# Launch browser in kiosk mode
if command -v chromium &>/dev/null; then
  chromium \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-restore-session-state \
    --disk-cache-size=1 \
    --app=http://localhost:8000 &
elif command -v open &>/dev/null; then
  # macOS — open in default browser for dev
  open http://localhost:8000
fi

# Wait for backend; clean up on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
wait $BACKEND_PID
