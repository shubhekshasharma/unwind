import asyncio
import json
import os
import platform
import sqlite3
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import paho.mqtt.client as mqtt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

IS_PI = platform.machine().lower().startswith(("arm", "aarch"))

# spidev is only available on Linux / Raspberry Pi
try:
    import spidev as _spidev_mod
    SPI_AVAILABLE = True
except ImportError:
    SPI_AVAILABLE = False

# ── Force sensor config ───────────────────────────────────────────────────────
SPI_BUS         = 0       # SPI bus (BCM: SPI0)
SPI_DEVICE      = 0       # CE0
SPI_ADC_CHANNEL = 0       # MCP3008 channel connected to FSR voltage divider
SPI_SPEED_HZ    = 1_350_000
DOCK_THRESHOLD  = 8       # ADC units (0–1023); BELOW = phone present (sensor reads ~0 under pressure, 12-15 at rest)
DEBOUNCE_COUNT  = 3       # consecutive matching readings before firing an event

BASE_DIR   = Path(__file__).parent.parent
PREFS_FILE = BASE_DIR / "prefs.json"
DB_FILE    = BASE_DIR / "user_device_data.db"
STATIC_DIR = BASE_DIR / "frontend" / "dist"

START_TOPIC  = "device/events/unwind_start"
STOP_TOPIC   = "device/events/unwind_stop"
PICKUP_TOPIC = "device/events/phone_pickup"
DOCK_TOPIC   = "device/events/phone_dock"
DEVICE_ID    = "device1"
BROKER       = "localhost"
BROKER_PORT  = 1883

_DEFAULT_PREFS = {
    "wake_time": "07:00",
    "bedtime": "23:00",
    "unwind_duration": 30,
    "onboarding_complete": False,
}


# ── State ─────────────────────────────────────────────────────────────────────

class AppState:
    def __init__(self):
        self.prefs = self._load_prefs()
        self.session = self._blank_session()
        self.screen: str = "home" if self.prefs.get("onboarding_complete") else "onboarding"
        self._warned_5min = False
        self._mqtt: Optional[mqtt.Client] = None

    # Prefs

    def _load_prefs(self) -> dict:
        try:
            with open(PREFS_FILE) as f:
                data = json.load(f)
            return {**_DEFAULT_PREFS, **data}
        except Exception:
            return dict(_DEFAULT_PREFS)

    def save_prefs(self):
        with open(PREFS_FILE, "w") as f:
            json.dump(self.prefs, f, indent=2)

    # Session

    def _blank_session(self) -> dict:
        return dict(
            is_phone_docked=True,
            timer_start=None,
            is_running=False,
            is_paused=False,
            paused_at=None,
            total_paused=0.0,
            pickup_count=0,
        )

    def get_elapsed(self) -> float:
        s = self.session
        if not s["is_running"] or s["timer_start"] is None:
            return 0.0
        now = time.time()
        extra = (now - s["paused_at"]) if s["is_paused"] and s["paused_at"] else 0
        return max(0.0, now - s["timer_start"] - s["total_paused"] - extra)

    def get_paused_secs(self) -> float:
        s = self.session
        if not s["is_paused"] or s["paused_at"] is None:
            return 0.0
        return time.time() - s["paused_at"]

    # Time helpers

    def _resolve_dt(self, time_str: str) -> Optional[datetime]:
        if not time_str:
            return None
        base = datetime.now()
        h, m = map(int, time_str.split(":"))
        dt = base.replace(hour=h, minute=m, second=0, microsecond=0)
        if dt <= base:
            dt += timedelta(days=1)
        return dt

    def bedtime_dt(self) -> Optional[datetime]:
        return self._resolve_dt(self.prefs.get("bedtime", ""))

    def unwind_start_dt(self) -> Optional[datetime]:
        bd = self.bedtime_dt()
        return bd - timedelta(minutes=int(self.prefs.get("unwind_duration", 30))) if bd else None

    def secs_to_unwind(self) -> Optional[float]:
        dt = self.unwind_start_dt()
        return (dt - datetime.now()).total_seconds() if dt else None

    def secs_to_bedtime(self) -> Optional[float]:
        dt = self.bedtime_dt()
        return (dt - datetime.now()).total_seconds() if dt else None

    def is_bedtime_passed(self) -> bool:
        secs = self.secs_to_bedtime()
        return secs is not None and secs <= 0

    # MQTT

    def setup_mqtt(self):
        try:
            self._mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        except AttributeError:
            # paho-mqtt < 2.0 fallback
            self._mqtt = mqtt.Client()  # type: ignore[call-arg]
        self._mqtt.on_connect = lambda c, u, f, rc: print(
            f"[MQTT] {'connected' if rc == 0 else f'failed rc={rc}'}"
        )
        try:
            self._mqtt.connect(BROKER, BROKER_PORT, 60)
            self._mqtt.loop_start()
        except Exception as e:
            print(f"[MQTT] broker offline (MQTT events disabled): {e}")

    def _pub(self, topic: str, data: dict):
        if self._mqtt:
            try:
                self._mqtt.publish(topic, json.dumps(data), qos=1)
            except Exception:
                pass

    def _now_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _ts(self, t=None) -> str:
        return datetime.fromtimestamp(t or time.time()).strftime("%y%m%d%H%M%S")

    # Session actions

    def start_session(self):
        if self.session["is_running"]:
            return
        if not self.session["is_phone_docked"]:
            return
        now = time.time()
        self.session.update(
            timer_start=now,
            is_running=True,
            is_paused=False,
            paused_at=None,
            total_paused=0.0,
            is_phone_docked=True,
            pickup_count=0,
        )
        self._pub(START_TOPIC, {
            "date": self._now_str(),
            "start_time": self._ts(now),
            "command": "start_unwind",
            "device_id": DEVICE_ID,
            "alarm_time": self.prefs.get("bedtime"),
        })

    def stop_session(self):
        s = self.session
        if not s["is_running"]:
            return
        now = time.time()
        extra = (now - s["paused_at"]) if s["is_paused"] and s["paused_at"] else 0
        duration = now - s["timer_start"] - s["total_paused"] - extra
        data = {
            "date": self._now_str(),
            "start_time": self._ts(s["timer_start"]),
            "stop_time": self._ts(now),
            "duration": duration,
            "command": "stop_unwind",
            "device_id": DEVICE_ID,
            "alarm_time": self.prefs.get("bedtime"),
            "pickup_count": s["pickup_count"],
        }
        self._pub(STOP_TOPIC, data)
        _save_session_to_db(data)
        s.update(is_running=False, is_paused=False, timer_start=None,
                 paused_at=None, total_paused=0.0)

    def pickup_phone(self):
        s = self.session
        if not s["is_running"] or not s["is_phone_docked"]:
            return
        now = time.time()
        s.update(
            is_phone_docked=False,
            is_paused=True,
            paused_at=now,
            pickup_count=s["pickup_count"] + 1,
        )
        self._pub(PICKUP_TOPIC, {
            "date": self._now_str(),
            "timestamp": self._ts(now),
            "command": "pickup",
            "device_id": DEVICE_ID,
            "pickup_count": s["pickup_count"],
        })
        self.screen = "paused"

    def dock_phone(self):
        s = self.session
        if not s["is_running"] or s["is_phone_docked"]:
            return
        now = time.time()
        s["total_paused"] += now - (s["paused_at"] or now)
        s.update(is_phone_docked=True, paused_at=None, is_paused=False)
        self._pub(DOCK_TOPIC, {
            "date": self._now_str(),
            "timestamp": self._ts(now),
            "command": "dock",
            "device_id": DEVICE_ID,
        })
        self.screen = "incomplete" if self.is_bedtime_passed() else "session"

    # Serialise to client

    def to_client_state(self) -> dict:
        s = self.session
        secs_left = self.secs_to_bedtime()
        return {
            "screen": self.screen,
            "session": {
                "timeRemaining": max(0.0, secs_left) if secs_left is not None else 0.0,
                "elapsed": self.get_elapsed(),
                "pickupCount": s["pickup_count"],
                "isPhoneDocked": s["is_phone_docked"],
                "isRunning": s["is_running"],
                "pausedSecs": self.get_paused_secs(),
            },
            "prefs": {
                "bedtime": self.prefs.get("bedtime", "23:00"),
                "wakeTime": self.prefs.get("wake_time", "07:00"),
                "unwindDuration": self.prefs.get("unwind_duration", 30),
                "onboardingComplete": bool(self.prefs.get("onboarding_complete")),
            },
        }


# ── Database ──────────────────────────────────────────────────────────────────

def _build_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE,
                user_id TEXT,
                event_type TEXT,
                session_started_at TEXT,
                status TEXT,
                created_at TEXT,
                pickup_count INTEGER DEFAULT 0,
                alarm_time TEXT,
                duration_seconds REAL
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] init error: {e}")


def _save_session_to_db(data: dict):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        mid = data.get("command", "") + "_" + data.get("start_time", "")
        c.execute("""
            INSERT OR IGNORE INTO sessions
                (message_id, user_id, event_type, session_started_at,
                 status, created_at, pickup_count, alarm_time, duration_seconds)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            mid, data.get("device_id"), data.get("command"),
            data.get("start_time"), "completed", data.get("date"),
            data.get("pickup_count", 0), data.get("alarm_time"),
            data.get("duration"),
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] save error: {e}")


def get_sessions(n: int = 20) -> list:
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT * FROM sessions WHERE event_type='stop_unwind' ORDER BY id DESC LIMIT ?",
            (n,),
        )
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] {e}")
        return []


# ── WebSocket manager ─────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.connections = [c for c in self.connections if c is not ws]

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send(self, ws: WebSocket, data: dict):
        try:
            await ws.send_json(data)
        except Exception:
            self.disconnect(ws)


# ── Globals ───────────────────────────────────────────────────────────────────

state   = AppState()
manager = ConnectionManager()


# ── Background ticker ─────────────────────────────────────────────────────────

async def schedule_ticker():
    """Pushes state to clients every second during active screens; checks schedule every 30s."""
    last_check = 0.0

    while True:
        await asyncio.sleep(1)

        if not manager.connections:
            continue

        now = time.time()
        changed = False

        # Push countdown updates every second while session is active or paused
        if state.session["is_running"] and state.screen in ("session", "paused"):
            if not state.session["is_paused"] and state.is_bedtime_passed():
                state.stop_session()
                state.screen = "complete"
            changed = True

        # Schedule check every 30 s
        if now - last_check >= 30:
            last_check = now
            if (
                state.prefs.get("onboarding_complete")
                and state.screen not in ("session", "paused", "incomplete", "complete", "onboarding")
            ):
                secs_unwind = state.secs_to_unwind()
                secs_bed    = state.secs_to_bedtime()

                if secs_unwind is not None and secs_unwind <= 0 and (secs_bed is None or secs_bed > 0):
                    if state.screen != "reminderPulse":
                        state.screen = "reminderPulse"
                        changed = True
                elif secs_unwind is not None and secs_unwind <= 300:
                    if state.screen == "home" and not state._warned_5min:
                        state._warned_5min = True
                        state.screen = "reminder"
                        changed = True
                else:
                    if state._warned_5min and (secs_unwind is None or secs_unwind > 300):
                        state._warned_5min = False

        if changed:
            await manager.broadcast(state.to_client_state())


# ── Force sensor (SPI / MCP3008) ─────────────────────────────────────────────

def _read_mcp3008(spi, channel: int) -> int:
    """Read a 10-bit value (0–1023) from an MCP3008 ADC over SPI."""
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    return ((r[1] & 3) << 8) + r[2]


async def force_sensor_task():
    """
    Poll the FSR via SPI and fire pickup / dock events.
    Silently exits on non-Pi systems or if the SPI device can't be opened.
    """
    if not SPI_AVAILABLE:
        print("[SPI] spidev not available — force sensor disabled")
        return

    spi = None
    try:
        import spidev
        spi = spidev.SpiDev()
        spi.open(SPI_BUS, SPI_DEVICE)
        spi.max_speed_hz = SPI_SPEED_HZ
        spi.mode = 0
        print(f"[SPI] force sensor ready — bus {SPI_BUS} dev {SPI_DEVICE} ch {SPI_ADC_CHANNEL}")
    except Exception as e:
        print(f"[SPI] cannot open SPI device: {e}")
        return

    high_run = 0  # consecutive readings above threshold
    low_run  = 0  # consecutive readings below threshold

    try:
        while True:
            await asyncio.sleep(0.1)

            try:
                value = _read_mcp3008(spi, SPI_ADC_CHANNEL)
            except Exception as e:
                print(f"[SPI] read error: {e}")
                continue

            is_docked = state.session.get("is_phone_docked", True)

            if value < DOCK_THRESHOLD:
                high_run += 1
                low_run = 0
                if high_run == DEBOUNCE_COUNT and not is_docked:
                    if state.session["is_running"]:
                        state.dock_phone()
                    else:
                        state.session["is_phone_docked"] = True
                    await manager.broadcast(state.to_client_state())
            else:
                low_run += 1
                high_run = 0
                if low_run == DEBOUNCE_COUNT and is_docked:
                    if state.session["is_running"]:
                        state.pickup_phone()
                    else:
                        state.session["is_phone_docked"] = False
                    await manager.broadcast(state.to_client_state())
    finally:
        try:
            spi.close()
        except Exception:
            pass


# ── App lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    _build_db()
    state.setup_mqtt()
    ticker = asyncio.create_task(schedule_ticker())
    sensor = asyncio.create_task(force_sensor_task())
    yield
    ticker.cancel()
    sensor.cancel()
    if state._mqtt:
        try:
            state._mqtt.loop_stop()
            state._mqtt.disconnect()
        except Exception:
            pass


app = FastAPI(lifespan=lifespan)


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    await manager.send(ws, state.to_client_state())

    try:
        while True:
            data = await ws.receive_json()
            cmd = data.get("cmd")

            if cmd == "set_prefs":
                p = data.get("prefs", {})
                if "bedtime" in p:
                    state.prefs["bedtime"] = p["bedtime"]
                if "wakeTime" in p:
                    state.prefs["wake_time"] = p["wakeTime"]
                if "unwindDuration" in p:
                    state.prefs["unwind_duration"] = int(p["unwindDuration"])
                if "onboardingComplete" in p:
                    state.prefs["onboarding_complete"] = bool(p["onboardingComplete"])
                state.save_prefs()
                state.screen = "home"
                state._warned_5min = False

            elif cmd == "start_session":
                state.start_session()
                state.screen = "session"

            elif cmd == "stop_session":
                elapsed = state.get_elapsed()
                state.stop_session()
                state.session["_last_elapsed"] = elapsed  # carry into complete screen
                state.screen = "complete"

            elif cmd == "pickup":
                state.pickup_phone()

            elif cmd == "dock":
                state.dock_phone()

            elif cmd == "skip":
                state.screen = "home"

            elif cmd == "continue_session":
                state.screen = "session"

            elif cmd == "navigate":
                target = data.get("screen", "home")
                if target in ("home", "stats"):
                    state.screen = target

            elif cmd == "reset":
                # Stop any running session cleanly
                if state.session["is_running"]:
                    state.stop_session()
                # Clear database
                try:
                    conn = sqlite3.connect(DB_FILE)
                    conn.execute("DELETE FROM sessions")
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"[reset] db clear error: {e}")
                # Reset prefs and session state
                state.prefs = dict(_DEFAULT_PREFS)
                state.save_prefs()
                state.session = state._blank_session()
                state._warned_5min = False
                state.screen = "onboarding"

            await manager.broadcast(state.to_client_state())

    except WebSocketDisconnect:
        manager.disconnect(ws)


# ── REST ──────────────────────────────────────────────────────────────────────

@app.get("/api/sessions")
async def api_sessions():
    return get_sessions(20)


# ── Static files (production) ─────────────────────────────────────────────────

if STATIC_DIR.exists():
    _assets = STATIC_DIR / "assets"
    if _assets.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(str(STATIC_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    host = "0.0.0.0"
    port = 8000
    print(f"[Unwind] http://localhost:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")
