#!/usr/bin/env bash
# scripts/setup-pi.sh — one-time setup on a fresh Raspberry Pi
# Run this ON THE PI via SSH: bash setup-pi.sh
# Or run remotely:           ssh pi@raspberrypi.local 'bash -s' < scripts/setup-pi.sh
set -e

INSTALL_DIR="/home/subu/unwind"

echo "▶ Setting up Unwind on Raspberry Pi..."

# ── System packages ────────────────────────────────────────────────────────
echo "  [apt] installing system packages..."
sudo apt update -qq
sudo apt install -y \
  chromium \
  mosquitto \
  mosquitto-clients \
  python3-pip \
  python3-venv \
  nodejs \
  npm

# ── Mosquitto config ───────────────────────────────────────────────────────
echo "  [mosquitto] configuring..."
sudo tee /etc/mosquitto/conf.d/unwind.conf > /dev/null << 'EOF'
listener 1883
allow_anonymous true
EOF
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto
echo "  [mosquitto] running ✓"

# ── Python environment ─────────────────────────────────────────────────────
echo "  [python] creating venv and installing deps..."
cd "$INSTALL_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt --quiet
pip install -r requirements-pi.txt --quiet
echo "  [python] deps installed ✓"

# ── systemd service ────────────────────────────────────────────────────────
echo "  [systemd] installing unwind.service..."
sudo cp "$INSTALL_DIR/unwind.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable unwind
echo "  [systemd] service enabled ✓"

# ── Disable screen blanking ────────────────────────────────────────────────
echo "  [display] disabling screen blanking..."
if [ -f /etc/lightdm/lightdm.conf ]; then
  sudo sed -i 's/#xserver-command=X/xserver-command=X -s 0 -dpms/' /etc/lightdm/lightdm.conf
fi

echo ""
echo "  ┌──────────────────────────────────────────────┐"
echo "  │  Pi setup complete!                           │"
echo "  │                                               │"
echo "  │  To start now:  sudo systemctl start unwind   │"
echo "  │  To view logs:  journalctl -u unwind -f       │"
echo "  └──────────────────────────────────────────────┘"
echo ""
