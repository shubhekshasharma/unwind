#!/usr/bin/env bash
# scripts/reset-pi.sh — reset the Unwind app on a Raspberry Pi remotely
# Usage: ./scripts/reset-pi.sh [pi-host]
#   pi-host defaults to raspberrypi.local
set -e

PI_HOST="${1:-raspberrypi.local}"
PI_USER="subu"
PI_PATH="/home/subu/unwind"

echo "▶ Resetting Unwind on ${PI_HOST}..."

ssh "${PI_USER}@${PI_HOST}" bash << EOF
  set -e
  cd ${PI_PATH}

  # Clear database
  if [ -f user_device_data.db ]; then
    sqlite3 user_device_data.db "DELETE FROM sessions;"
    echo "  ✓ Session history cleared"
  fi

  # Reset prefs
  cat > prefs.json << 'PREFS'
{
  "wake_time": "07:00",
  "bedtime": "23:00",
  "unwind_duration": 30,
  "onboarding_complete": false
}
PREFS
  echo "  ✓ Preferences reset"

  # Restart service so the backend picks up the new prefs
  sudo systemctl restart unwind
  echo "  ✓ Service restarted"
EOF

echo ""
echo "  Done. The Pi will show onboarding on next interaction."
