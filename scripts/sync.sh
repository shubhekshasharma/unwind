#!/usr/bin/env bash
# scripts/sync.sh — build frontend and sync everything to Raspberry Pi
# Usage: ./scripts/sync.sh [pi-host] [--no-restart]
#   pi-host defaults to raspberrypi.local
#   --no-restart  skips restarting the systemd service after sync
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

PI_HOST="${1:-raspberrypi.local}"
NO_RESTART=false
[[ "$2" == "--no-restart" ]] && NO_RESTART=true

PI_USER="subu"
PI_PATH="/home/subu/unwind"
PI_DEST="${PI_USER}@${PI_HOST}:${PI_PATH}"

echo "▶ Syncing Unwind to ${PI_HOST}..."

# ── Build frontend ─────────────────────────────────────────────────────────
echo "  [frontend] building..."
cd frontend
npm install --silent
npm run build
cd ..
echo "  [frontend] build complete ✓"

# ── rsync to Pi ────────────────────────────────────────────────────────────
echo "  [rsync] pushing to ${PI_DEST}..."
rsync -avz --progress \
  --exclude venv \
  --exclude node_modules \
  --exclude __pycache__ \
  --exclude "*.pyc" \
  --exclude ".git" \
  --exclude "frontend/node_modules" \
  ./ "${PI_DEST}/"
echo "  [rsync] sync complete ✓"

# ── Restart service ────────────────────────────────────────────────────────
if [ "$NO_RESTART" = false ]; then
  echo "  [pi] restarting unwind service..."
  ssh "${PI_USER}@${PI_HOST}" "sudo systemctl restart unwind"
  echo "  [pi] service restarted ✓"
fi

echo ""
echo "  ┌──────────────────────────────────────────────┐"
echo "  │  Sync complete!                               │"
echo "  │  Device: http://${PI_HOST}:8000               │"
echo "  └──────────────────────────────────────────────┘"
echo ""
