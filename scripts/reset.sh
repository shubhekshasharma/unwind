#!/usr/bin/env bash
# scripts/reset.sh — wipe local data and restart from onboarding
# Usage: ./scripts/reset.sh [--yes]
#   --yes  skip the confirmation prompt
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

SKIP_CONFIRM=false
[[ "$1" == "--yes" ]] && SKIP_CONFIRM=true

if [ "$SKIP_CONFIRM" = false ]; then
  echo "This will:"
  echo "  • Clear all session history (user_device_data.db)"
  echo "  • Reset preferences to defaults (prefs.json)"
  echo "  • Restart onboarding on next launch"
  echo ""
  read -r -p "Are you sure? [y/N] " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 0; }
fi

# Clear database
if [ -f "user_device_data.db" ]; then
  sqlite3 user_device_data.db "DELETE FROM sessions;"
  echo "✓ Session history cleared"
else
  echo "- No database found, skipping"
fi

# Reset prefs
cat > prefs.json << 'EOF'
{
  "wake_time": "07:00",
  "bedtime": "23:00",
  "unwind_duration": 30,
  "onboarding_complete": false
}
EOF
echo "✓ Preferences reset to defaults"

echo ""
echo "Done. Restart the backend to begin fresh from onboarding."
