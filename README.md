# Unwind — Bedside Device

A Raspberry Pi bedside device that guides you through a nightly unwind ritual, helping you put down your phone before bed.

**Architecture:** Python (FastAPI + WebSocket) backend + React/Tailwind frontend displayed in Chromium kiosk mode.

---

## Project structure

```
.
├── backend/
│   └── main.py            # FastAPI server — session logic, WebSocket, MQTT, SQLite
├── frontend/
│   ├── src/components/    # All screens (Onboarding, Home, Reminder, Session, etc.)
│   ├── package.json
│   └── dist/              # Built output — gitignored, served by Python in production
├── scripts/
│   ├── dev.sh             # Start full dev environment in one command
│   ├── sync.sh            # Build + rsync + restart Pi service in one command
│   ├── reset.sh           # Wipe local data and restart onboarding
│   ├── reset-pi.sh        # Reset Pi remotely over SSH
│   └── setup-pi.sh        # One-time Pi setup script (run on the Pi)
├── archive/               # Legacy Kivy app — kept for reference, not active
│   ├── main_ui.py
│   ├── screens/
│   ├── device.py
│   ├── publisher.py
│   ├── subscriber.py
│   ├── llm.py
│   └── visualization.py
├── prefs.json             # User preferences — gitignored, created at runtime
├── user_device_data.db    # SQLite session history — gitignored
├── start.sh               # Pi launcher (backend + Chromium kiosk)
└── unwind.service         # systemd unit for auto-start on Pi boot
```

---

## Development

### Prerequisites (one-time)

```bash
# Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Node
cd frontend && npm install && cd ..

# MQTT broker (macOS)
brew install mosquitto

# Create the config file (required — won't start without it)
cat > /usr/local/etc/mosquitto/mosquitto.conf << 'EOF'
listener 1883
allow_anonymous true
log_type all
persistence true
persistence_location /usr/local/var/mosquitto/
EOF

mkdir -p /usr/local/var/mosquitto
brew services start mosquitto
```

---

### Quick start — single command

```bash
./scripts/dev.sh
```

This starts Mosquitto (if not running), the Python backend on port 8000, and the Vite dev server on port 5173 with hot reload — then opens `http://localhost:5173` in your browser. Press `Ctrl+C` to stop everything.

```bash
# Don't auto-open browser
./scripts/dev.sh --no-browser
```

---

### Manual start (if you prefer separate terminals)

**Terminal 1 — backend**
```bash
source venv/bin/activate
python backend/main.py
# http://localhost:8000
```

**Terminal 2 — frontend (hot reload)**
```bash
cd frontend
npm run dev
# http://localhost:5173  (proxies /ws and /api to port 8000)
```

---

### Testing each screen

The app is driven entirely by the Python backend. To test individual screens without waiting for real time:

| Screen | How to trigger |
|---|---|
| Onboarding | Delete `prefs.json` and restart the backend |
| Home | Complete onboarding |
| T-5 reminder | Set bedtime to 5 min from now in settings |
| T-0 pulse (dock prompt) | Set bedtime to match the ritual duration from now |
| Active session | Click "Start Unwind" on the pulse screen (dock toggle on) |
| Paused | Click "Simulate phone pickup" on the session screen |
| Incomplete | Pick up phone, put it back after bedtime passes |
| Complete | Let countdown reach zero, or click "End ritual" |
| Stats | "View sleep history" from home or completion screen |

**Simulate dock/pickup on desktop:** the session screen has a "Simulate phone pickup" button and the reminder screen has a dock toggle. On the Pi, these come from the physical sensor via MQTT.

**Monitor MQTT events live:**
```bash
mosquitto_sub -t 'device/events/#' -v
```

---

## Deployment

### First-time Pi setup

SSH into the Pi and run the setup script — it installs all dependencies, configures Mosquitto, sets up the Python venv, and registers the systemd service:

```bash
# Option A: run remotely from your Mac
ssh subu@192.168.1.92 'bash -s' < scripts/setup-pi.sh

# Option B: copy to Pi first, then run on it
scp scripts/setup-pi.sh pi@raspberrypi.local:~
ssh pi@raspberrypi.local "bash setup-pi.sh"
```

---

### Sync code to Pi — single command

```bash
./scripts/sync.sh
```

This builds the frontend locally (faster than building on the Pi), rsyncs everything to `/home/pi/unwind/`, and restarts the systemd service. The Pi will show the updated app immediately.

```bash
# Target a different hostname or IP
./scripts/sync.sh pi@192.168.1.42

# Sync without restarting the service
./scripts/sync.sh raspberrypi.local --no-restart
```

---

### Manual sync (step by step)

```bash
# 1. Build frontend
cd frontend && npm run build && cd ..

# 2. Push to Pi
rsync -avz \
  --exclude venv --exclude node_modules --exclude __pycache__ \
  --exclude "*.pyc" --exclude .git \
  ./ pi@raspberrypi.local:/home/pi/unwind/

# 3. Restart service
ssh pi@raspberrypi.local "sudo systemctl restart unwind"
```

---

### Running on the Pi

```bash
# One-time manual start
cd /home/pi/unwind && ./start.sh
```

`start.sh` builds the frontend if `dist/` is missing, starts the Python backend on port 8000, then launches Chromium in fullscreen kiosk mode.

---

### Auto-start on boot (systemd)

The `setup-pi.sh` script handles this automatically. To manage it manually:

```bash
# Install and enable
sudo cp /home/pi/unwind/unwind.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable unwind
sudo systemctl start unwind

# View logs
journalctl -u unwind -f

# Restart / stop
sudo systemctl restart unwind
sudo systemctl stop unwind
```

---

### Resetting the app on Pi

**Option A — from your Mac (remotely):**
```bash
./scripts/reset-pi.sh
# or with a custom host
./scripts/reset-pi.sh 192.168.1.42
```
This SSHs in, wipes the database, resets prefs, and restarts the service. The Pi will show onboarding immediately.

**Option B — in the app UI:**
Open the app on the Pi touchscreen → Settings gear → scroll down → "Reset app & clear data". Works without SSH.

**Option C — directly on the Pi via SSH:**
```bash
ssh pi@raspberrypi.local
cd /home/pi/unwind
./scripts/reset.sh --yes
sudo systemctl restart unwind
```

---

### Git pull workflow (alternative to rsync)

```bash
# On the Pi
cd /home/pi/unwind
git pull
source venv/bin/activate
pip install -r requirements.txt       # if requirements changed
cd frontend && npm run build && cd ..  # if frontend changed
sudo systemctl restart unwind
```

---

## MQTT topics

The backend publishes session events to Mosquitto. Subscribe from any device on the same network for logging or LLM insights.

| Topic | Payload fields | Fired when |
|---|---|---|
| `device/events/unwind_start` | `start_time`, `alarm_time` | Session begins |
| `device/events/unwind_stop` | `duration`, `pickup_count` | Session ends |
| `device/events/phone_pickup` | `timestamp`, `pickup_count` | Phone lifted mid-session |
| `device/events/phone_dock` | `timestamp` | Phone returned to dock |

```bash
mosquitto_sub -t 'device/events/#' -v
```

---

## Legacy Kivy app

The original Kivy-based UI has been moved to `archive/` — kept for reference, no longer active.

```bash
pip install kivy==2.3.0
python archive/main_ui.py
```
