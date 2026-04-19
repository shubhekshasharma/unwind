"""Edit schedule: bedtime, wake-up, unwind duration."""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.app import App
from kivy.uix.button import Button

from screens.theme import BG, CARD, AMBER, CREAM, PEACH, MUTED, btn, TimePicker, fmt_12h

DURATIONS = [15, 20, 25, 30, 45, 60]


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dur_idx = DURATIONS.index(30)
        self._build()

    def _build(self):
        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, "pos", self.pos),
                  size=lambda *_: setattr(self._bg, "size", self.size))

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(28), dp(48), dp(28), dp(36)],
            spacing=dp(14),
        )

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(54))
        back = Button(
            text="←", font_size=sp(28), color=CREAM,
            background_color=(0, 0, 0, 0), background_normal="",
            size_hint_x=None, width=dp(54),
        )
        back.bind(on_press=lambda *_: App.get_running_app().go_to("home", "right"))
        hdr.add_widget(back)
        hdr.add_widget(Label(text="Your Schedule", font_size=sp(24), bold=True, color=CREAM))
        hdr.add_widget(Widget(size_hint_x=None, width=dp(54)))
        root.add_widget(hdr)

        root.add_widget(Widget(size_hint_y=0.02))

        # ── Wake-up ───────────────────────────────────────────────────────
        root.add_widget(Label(
            text="WAKE-UP TIME",
            font_size=sp(12), color=MUTED,
            size_hint_y=None, height=dp(20),
        ))
        self._wake_picker = TimePicker(hour=7, minute=0, size_hint_y=None, height=dp(240))
        root.add_widget(self._wake_picker)

        root.add_widget(Widget(size_hint_y=0.02))

        # ── Bedtime ───────────────────────────────────────────────────────
        root.add_widget(Label(
            text="BEDTIME",
            font_size=sp(12), color=MUTED,
            size_hint_y=None, height=dp(20),
        ))
        self._bed_picker = TimePicker(hour=23, minute=0, size_hint_y=None, height=dp(240))
        root.add_widget(self._bed_picker)

        root.add_widget(Widget(size_hint_y=0.02))

        # ── Ritual duration ───────────────────────────────────────────────
        root.add_widget(Label(
            text="UNWIND RITUAL LENGTH",
            font_size=sp(12), color=MUTED,
            size_hint_y=None, height=dp(20),
        ))
        dur_row = BoxLayout(spacing=dp(12), size_hint_y=None, height=dp(60))
        for d in DURATIONS:
            b = Button(
                text=f"{d}m",
                font_size=sp(18),
                background_normal="", background_down="",
            )
            b._dur = d
            b.bind(on_press=self._pick_dur)
            dur_row.add_widget(b)
            self._style_dur_btn(b)
        self._dur_row = dur_row
        root.add_widget(dur_row)

        self._dur_hint_lbl = Label(
            text="", font_size=sp(16), color=PEACH,
            size_hint_y=None, height=dp(28),
        )
        root.add_widget(self._dur_hint_lbl)

        root.add_widget(Widget(size_hint_y=0.04))

        root.add_widget(btn(
            "Save", AMBER, (0.11, 0.07, 0.12, 1), self._save,
            height=dp(80), font_size=sp(22),
        ))

        self.add_widget(root)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        app = App.get_running_app()
        self._wake_picker.set_time(app.prefs.get("wake_time", "07:00"))
        self._bed_picker.set_time(app.prefs.get("bedtime", "23:00"))
        cur_dur = app.prefs.get("unwind_duration", 30)
        if cur_dur in DURATIONS:
            self._dur_idx = DURATIONS.index(cur_dur)
        self._refresh_dur_buttons()
        self._update_dur_hint()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _style_dur_btn(self, b):
        selected = (b._dur == DURATIONS[self._dur_idx])
        b.background_color = AMBER if selected else CARD
        b.color = (0.11, 0.07, 0.12, 1) if selected else MUTED

    def _refresh_dur_buttons(self):
        for b in self._dur_row.children:
            self._style_dur_btn(b)

    def _pick_dur(self, b):
        self._dur_idx = DURATIONS.index(b._dur)
        self._refresh_dur_buttons()
        self._update_dur_hint()

    def _update_dur_hint(self):
        dur = DURATIONS[self._dur_idx]
        bed = self._bed_picker.time_str
        try:
            from datetime import datetime, timedelta
            h, m = map(int, bed.split(":"))
            now = datetime.now()
            bed_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            start_dt = bed_dt - timedelta(minutes=dur)
            start_str = fmt_12h(f"{start_dt.hour:02d}:{start_dt.minute:02d}")
            self._dur_hint_lbl.text = f"Session starts at {start_str}"
        except Exception:
            self._dur_hint_lbl.text = ""

    def _save(self, *_):
        app = App.get_running_app()
        app.prefs["wake_time"] = self._wake_picker.time_str
        app.prefs["bedtime"]   = self._bed_picker.time_str
        app.prefs["unwind_duration"] = DURATIONS[self._dur_idx]
        app.save_prefs()
        app.go_to("home", "right")
