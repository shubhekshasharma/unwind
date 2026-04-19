import os
import json
import time
import platform
import sqlite3
from datetime import datetime, timedelta

IS_PI = platform.machine().lower().startswith(("arm", "aarch"))

from kivy.config import Config

if not IS_PI:
    Config.set("graphics", "width", "360")
    Config.set("graphics", "height", "640")
    Config.set("graphics", "resizable", "1")
else:
    Config.set("graphics", "fullscreen", "1")
    Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition, FadeTransition
from kivy.core.window import Window
from kivy.clock import Clock

import paho.mqtt.client as mqtt

START_TOPIC  = "device/events/unwind_start"
STOP_TOPIC   = "device/events/unwind_stop"
PICKUP_TOPIC = "device/events/phone_pickup"
DOCK_TOPIC   = "device/events/phone_dock"
DEVICE_ID    = "device1"
DATABASE_FILE = "user_device_data.db"
PREFS_FILE    = "prefs.json"
BROKER        = "localhost"
BROKER_PORT   = 1883

_DEFAULT_PREFS = {
    "wake_time": "07:00",
    "bedtime": "23:00",
    "unwind_duration": 30,
    "onboarding_complete": False,
}


class UnwindApp(App):
    title = "Unwind"

    def build(self):
        Window.clearcolor = (0.11, 0.07, 0.12, 1)

        self.prefs = self._load_prefs()
        self.session = self._blank_session()
        self._warned_5min = False   # fired T-5 chime this cycle
        self._warned_start = False  # fired T-0 chime this cycle
        self._schedule_clock = None

        self._setup_mqtt()
        self._build_db()

        from screens.onboarding_screen import OnboardingScreen
        from screens.home_screen      import HomeScreen
        from screens.ready_screen     import ReadyScreen
        from screens.session_screen   import SessionScreen
        from screens.paused_screen    import PausedScreen
        from screens.incomplete_screen import IncompleteScreen
        from screens.complete_screen  import CompleteScreen
        from screens.stats_screen     import StatsScreen
        from screens.settings_screen  import SettingsScreen

        self.sm = ScreenManager()
        self.sm.add_widget(OnboardingScreen(name="onboarding"))
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(ReadyScreen(name="ready"))
        self.sm.add_widget(SessionScreen(name="session"))
        self.sm.add_widget(PausedScreen(name="paused"))
        self.sm.add_widget(IncompleteScreen(name="incomplete"))
        self.sm.add_widget(CompleteScreen(name="complete"))
        self.sm.add_widget(StatsScreen(name="stats"))
        self.sm.add_widget(SettingsScreen(name="settings"))

        if self.prefs.get("onboarding_complete"):
            self.sm.current = "home"
        else:
            self.sm.current = "onboarding"

        self._schedule_clock = Clock.schedule_interval(self._tick_schedule, 30)
        return self.sm

    # ── Navigation ───────────────────────────────────────────────────────────

    def go_to(self, name, direction="left"):
        self.sm.transition = SlideTransition(direction=direction)
        self.sm.current = name

    def fade_to(self, name):
        self.sm.transition = FadeTransition(duration=0.6)
        self.sm.current = name

    # ── Preferences ──────────────────────────────────────────────────────────

    def _load_prefs(self):
        try:
            with open(PREFS_FILE) as f:
                data = json.load(f)
            return {**_DEFAULT_PREFS, **data}
        except Exception:
            return dict(_DEFAULT_PREFS)

    def save_prefs(self):
        with open(PREFS_FILE, "w") as f:
            json.dump(self.prefs, f, indent=2)

    # ── SQLite ───────────────────────────────────────────────────────────────

    def _build_db(self):
        try:
            conn = sqlite3.connect(DATABASE_FILE)
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

    def get_sessions(self, n=10):
        try:
            conn = sqlite3.connect(DATABASE_FILE)
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

    def _save_session_to_db(self, data):
        try:
            conn = sqlite3.connect(DATABASE_FILE)
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

    # ── MQTT ─────────────────────────────────────────────────────────────────

    def _setup_mqtt(self):
        self._mqtt = mqtt.Client()
        self._mqtt.on_connect = lambda c, u, f, rc: print(
            f"[MQTT] {'connected' if rc == 0 else f'failed rc={rc}'}"
        )
        try:
            self._mqtt.connect(BROKER, BROKER_PORT, 60)
            self._mqtt.loop_start()
        except Exception as e:
            print(f"[MQTT] broker offline: {e}")

    def _pub(self, topic, data):
        try:
            self._mqtt.publish(topic, json.dumps(data), qos=1)
        except Exception:
            pass

    # ── Schedule / time helpers ───────────────────────────────────────────────

    def _blank_session(self):
        return dict(
            experience_state="IDLE",
            is_phone_docked=True,
            timer_start=None,
            is_timer_running=False,
            is_timer_paused=False,
            paused_at=None,
            total_paused=0.0,
            pickup_count=0,
        )

    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d")

    def _ts(self, t=None):
        return datetime.fromtimestamp(t or time.time()).strftime("%y%m%d%H%M%S")

    def _resolve_dt(self, time_str, base=None):
        """Return next occurrence of HH:MM as a datetime (today or tomorrow)."""
        if not time_str:
            return None
        base = base or datetime.now()
        h, m = map(int, time_str.split(":"))
        dt = base.replace(hour=h, minute=m, second=0, microsecond=0)
        if dt <= base:
            dt += timedelta(days=1)
        return dt

    def bedtime_dt(self):
        return self._resolve_dt(self.prefs.get("bedtime"))

    def unwind_start_dt(self):
        bd = self.bedtime_dt()
        if bd is None:
            return None
        return bd - timedelta(minutes=int(self.prefs.get("unwind_duration", 30)))

    def secs_to_unwind(self):
        dt = self.unwind_start_dt()
        return (dt - datetime.now()).total_seconds() if dt else None

    def secs_to_bedtime(self):
        dt = self.bedtime_dt()
        return (dt - datetime.now()).total_seconds() if dt else None

    def get_elapsed(self):
        s = self.session
        if not s["is_timer_running"] or s["timer_start"] is None:
            return 0.0
        now = time.time()
        extra = (now - s["paused_at"]) if s["is_timer_paused"] and s["paused_at"] else 0
        return now - s["timer_start"] - s["total_paused"] - extra

    def is_bedtime_passed(self):
        secs = self.secs_to_bedtime()
        return secs is not None and secs <= 0

    # ── Schedule checker (every 30 s) ─────────────────────────────────────────

    def _tick_schedule(self, dt):
        if not self.prefs.get("onboarding_complete"):
            return

        current = self.sm.current
        # Don't interrupt active sessions
        if current in ("session", "paused", "incomplete", "complete", "onboarding"):
            return

        secs_unwind = self.secs_to_unwind()
        secs_bed    = self.secs_to_bedtime()
        if secs_unwind is None:
            return

        if secs_unwind <= 0 and (secs_bed is None or secs_bed > 0):
            # It's unwind time
            if current != "ready":
                self._warned_start = False
                self.fade_to("ready")
                self._play_chime("alert")
        elif secs_unwind <= 300:
            # T-5 warning window
            if not self._warned_5min and current == "home":
                self._warned_5min = True
                self._play_chime("gentle")
                home = self.sm.get_screen("home")
                if hasattr(home, "show_warn"):
                    home.show_warn(int(secs_unwind))
        else:
            # Reset flags for next cycle
            self._warned_5min = False

    def _play_chime(self, level="gentle"):
        path = f"sounds/{level}_chime.wav"
        if os.path.exists(path):
            try:
                from kivy.core.audio import SoundLoader
                snd = SoundLoader.load(path)
                if snd:
                    snd.play()
            except Exception:
                pass

    # ── Session actions ───────────────────────────────────────────────────────

    def start_session(self):
        s = self.session
        if s["is_timer_running"]:
            return
        now = time.time()
        s.update(
            timer_start=now,
            is_timer_running=True,
            is_timer_paused=False,
            paused_at=None,
            total_paused=0.0,
            is_phone_docked=True,
            experience_state="PLAYING",
            pickup_count=0,
        )
        self._pub(START_TOPIC, {
            "date": self._now_str(),
            "start_time": self._ts(now),
            "command": "start_unwind",
            "device_id": DEVICE_ID,
            "experience_state": "PLAYING",
            "alarm_time": self.prefs.get("bedtime"),
        })

    def stop_session(self, skip=False):
        s = self.session
        if not s["is_timer_running"]:
            return
        now = time.time()
        extra = (now - s["paused_at"]) if s["is_timer_paused"] and s["paused_at"] else 0
        duration = now - s["timer_start"] - s["total_paused"] - extra
        data = {
            "date": self._now_str(),
            "start_time": self._ts(s["timer_start"]),
            "stop_time": self._ts(now),
            "duration": duration,
            "command": "stop_unwind",
            "device_id": DEVICE_ID,
            "experience_state": "IDLE",
            "alarm_time": self.prefs.get("bedtime"),
            "pickup_count": s["pickup_count"],
        }
        self._pub(STOP_TOPIC, data)
        self._save_session_to_db(data)
        s.update(is_timer_running=False, is_timer_paused=False,
                 experience_state="IDLE", timer_start=None, paused_at=None,
                 total_paused=0.0)

    def pickup_phone(self):
        s = self.session
        if not s["is_timer_running"] or not s["is_phone_docked"]:
            return
        now = time.time()
        s.update(
            is_phone_docked=False,
            is_timer_paused=True,
            paused_at=now,
            experience_state="PAUSED",
            pickup_count=s["pickup_count"] + 1,
        )
        self._pub(PICKUP_TOPIC, {
            "date": self._now_str(),
            "timestamp": self._ts(now),
            "command": "pickup",
            "device_id": DEVICE_ID,
            "experience_state": "PAUSED",
            "pickup_count": s["pickup_count"],
        })
        self.fade_to("paused")

    def dock_phone(self):
        s = self.session
        if not s["is_timer_running"] or s["is_phone_docked"]:
            return
        now = time.time()
        s["total_paused"] += now - (s["paused_at"] or now)
        s.update(is_phone_docked=True, paused_at=None,
                 is_timer_paused=False, experience_state="PLAYING")
        self._pub(DOCK_TOPIC, {
            "date": self._now_str(),
            "timestamp": self._ts(now),
            "command": "dock",
            "device_id": DEVICE_ID,
            "experience_state": "PLAYING",
        })
        if self.is_bedtime_passed():
            self.fade_to("incomplete")
        else:
            self.fade_to("session")

    def on_stop(self):
        try:
            self._mqtt.loop_stop()
            self._mqtt.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    UnwindApp().run()
