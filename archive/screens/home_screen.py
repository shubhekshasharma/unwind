from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.animation import Animation
from kivy.app import App
from datetime import datetime

from screens.theme import BG, CARD, AMBER, ROSE, CREAM, PEACH, MUTED, MAUVE, WARN, fmt_12h, btn


class _ScheduleChip(Button):
    """Tappable pill showing one schedule value."""

    def __init__(self, label, value, on_tap, **kwargs):
        super().__init__(
            background_color=CARD,
            background_normal="",
            background_down="",
            size_hint_y=None,
            height=dp(64),
            **kwargs,
        )
        self._label_str = label
        self._value_str = value

        inner = BoxLayout(orientation="vertical", padding=[dp(10), dp(6)])
        self._lbl = Label(text=label, font_size=sp(11), color=MUTED)
        self._val = Label(text=value, font_size=sp(19), bold=True, color=PEACH)
        inner.add_widget(self._lbl)
        inner.add_widget(self._val)
        self.add_widget(inner)
        self.bind(on_press=lambda *_: on_tap())

    def update(self, value):
        self._val.text = value


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ticker = None
        self._warn_anim = None
        self._build()

    def _build(self):
        with self.canvas.before:
            self._bg_color = Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, "pos", self.pos),
                  size=lambda *_: setattr(self._bg, "size", self.size))

        self._root = BoxLayout(
            orientation="vertical",
            padding=[dp(28), dp(50), dp(28), dp(36)],
            spacing=dp(10),
        )

        # App name
        self._root.add_widget(Label(
            text="unwind", font_size=sp(14), color=MUTED,
            size_hint_y=None, height=dp(22),
        ))

        self._root.add_widget(Widget(size_hint_y=0.06))

        # ── Large clock ───────────────────────────────────────────────────
        self._time_lbl = Label(
            text="00:00",
            font_size=sp(96), bold=True, color=CREAM,
            size_hint_y=None, height=dp(124),
        )
        self._ampm_lbl = Label(
            text="AM",
            font_size=sp(28), color=PEACH,
            size_hint_y=None, height=dp(38),
        )
        self._date_lbl = Label(
            text="",
            font_size=sp(18), color=MUTED,
            size_hint_y=None, height=dp(30),
        )
        self._root.add_widget(self._time_lbl)
        self._root.add_widget(self._ampm_lbl)
        self._root.add_widget(self._date_lbl)

        self._root.add_widget(Widget(size_hint_y=0.12))

        # ── Warning strip (hidden by default) ─────────────────────────────
        self._warn_strip = BoxLayout(
            orientation="vertical", size_hint_y=None, height=0,
            opacity=0,
        )
        with self._warn_strip.canvas.before:
            Color(*WARN)
            self._warn_bg = Rectangle(pos=self._warn_strip.pos, size=self._warn_strip.size)
        self._warn_strip.bind(
            pos=lambda *_: setattr(self._warn_bg, "pos", self._warn_strip.pos),
            size=lambda *_: setattr(self._warn_bg, "size", self._warn_strip.size),
        )
        self._warn_lbl = Label(
            text="", font_size=sp(17), color=AMBER,
            size_hint_y=None, height=dp(56),
        )
        self._warn_strip.add_widget(self._warn_lbl)
        self._root.add_widget(self._warn_strip)

        # ── Schedule chips ────────────────────────────────────────────────
        chips_lbl = Label(
            text="YOUR SCHEDULE",
            font_size=sp(11), color=MUTED,
            size_hint_y=None, height=dp(20),
        )
        self._root.add_widget(chips_lbl)

        chips_row = BoxLayout(orientation="horizontal", spacing=dp(10),
                              size_hint_y=None, height=dp(64))

        app = App.get_running_app()

        def _go_settings():
            App.get_running_app().go_to("settings")

        self._chip_bed  = _ScheduleChip("Bedtime",  fmt_12h(app.prefs.get("bedtime",  "23:00")), _go_settings)
        self._chip_wake = _ScheduleChip("Wake up",  fmt_12h(app.prefs.get("wake_time","07:00")), _go_settings)
        dur = app.prefs.get("unwind_duration", 30)
        self._chip_dur  = _ScheduleChip("Ritual",   f"{dur} min", _go_settings)

        chips_row.add_widget(self._chip_bed)
        chips_row.add_widget(self._chip_wake)
        chips_row.add_widget(self._chip_dur)
        self._root.add_widget(chips_row)

        self._root.add_widget(Widget(size_hint_y=0.04))

        # ── Stats shortcut ────────────────────────────────────────────────
        self._root.add_widget(btn(
            "View Sleep History", CARD, MAUVE,
            lambda *_: App.get_running_app().go_to("stats"),
            height=dp(60), font_size=sp(18), bold=False,
        ))

        self.add_widget(self._root)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        self._refresh_chips()
        self._tick(0)
        if self._ticker is None:
            self._ticker = Clock.schedule_interval(self._tick, 1)

    def on_leave(self):
        if self._ticker:
            self._ticker.cancel()
            self._ticker = None

    # ── Updates ───────────────────────────────────────────────────────────────

    def _tick(self, dt):
        now = datetime.now()
        h = now.hour
        h12 = h % 12 or 12
        self._time_lbl.text = f"{h12}:{now.minute:02d}"
        self._ampm_lbl.text = "AM" if h < 12 else "PM"
        self._date_lbl.text = now.strftime("%A, %B %-d")

    def _refresh_chips(self):
        app = App.get_running_app()
        self._chip_bed.update(fmt_12h(app.prefs.get("bedtime", "23:00")))
        self._chip_wake.update(fmt_12h(app.prefs.get("wake_time", "07:00")))
        self._chip_dur.update(f"{app.prefs.get('unwind_duration', 30)} min")

    def show_warn(self, secs_remaining):
        """Called by main_ui when T-5 warning fires."""
        mins = max(1, secs_remaining // 60)
        self._warn_lbl.text = f"✦  Unwind session starts in {mins} minute{'s' if mins != 1 else ''}  ✦"
        Animation(height=dp(56), opacity=1, duration=0.4).start(self._warn_strip)
        # Pulse the warning gently
        anim = Animation(opacity=0.5, duration=1.2) + Animation(opacity=1.0, duration=1.2)
        anim.repeat = True
        anim.start(self._warn_strip)

    def hide_warn(self):
        Animation.cancel_all(self._warn_strip)
        Animation(height=0, opacity=0, duration=0.3).start(self._warn_strip)
