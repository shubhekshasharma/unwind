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

# Launch browser in kiosk mode
if command -v chromium-browser &>/dev/null; then
  # Raspberry Pi OS
  chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-restore-session-state \
    --app=http://localhost:8000 &
elif command -v chromium &>/dev/null; then
  chromium \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --app=http://localhost:8000 &
elif command -v open &>/dev/null; then
  # macOS — open in default browser for dev
  open http://localhost:8000
fi

# Wait for backend; clean up on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
wait $BACKEND_PID
