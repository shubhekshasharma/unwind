"""T-0 screen: it's unwind time. Dock your phone to begin."""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from kivy.app import App
from datetime import datetime

from screens.theme import URGENT, CARD, AMBER, ROSE, CREAM, PEACH, MUTED, btn, fmt_12h, BreathingOrb


class ReadyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ticker = None
        self._phone_docked = False  # simulated dock state for testing
        self._build()

    def _build(self):
        with self.canvas.before:
            Color(*URGENT)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, "pos", self.pos),
                  size=lambda *_: setattr(self._bg, "size", self.size))

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(28), dp(50), dp(28), dp(40)],
            spacing=dp(14),
        )

        # Header label
        root.add_widget(Label(
            text="TIME TO UNWIND",
            font_size=sp(13), color=AMBER,
            size_hint_y=None, height=dp(24),
        ))

        root.add_widget(Widget(size_hint_y=0.04))

        # Pulsing orb
        self._orb = BreathingOrb(color_rgba=(0.98, 0.63, 0.26, 1))
        orb_wrap = Widget(size_hint_y=None, height=dp(200))
        self._orb.size_hint = (1, 1)
        self._orb.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        orb_wrap.add_widget(self._orb)
        root.add_widget(orb_wrap)

        # Headline
        root.add_widget(Label(
            text="Your ritual begins now.",
            font_size=sp(26), bold=True, color=CREAM,
            size_hint_y=None, height=dp(44),
        ))

        # Bedtime info
        self._bed_lbl = Label(
            text="", font_size=sp(18), color=PEACH,
            size_hint_y=None, height=dp(30),
        )
        root.add_widget(self._bed_lbl)

        root.add_widget(Widget(size_hint_y=0.06))

        # Dock instruction
        self._dock_instr = Label(
            text="Place your phone face-down\non the dock to begin",
            font_size=sp(20), color=MUTED,
            halign="center",
            size_hint_y=None, height=dp(70),
        )
        root.add_widget(self._dock_instr)

        root.add_widget(Widget(size_hint_y=0.04))

        # Simulated dock toggle (for desktop/testing)
        self._sim_btn = btn(
            "Simulate: Dock Phone",
            CARD, AMBER, self._toggle_sim_dock,
            height=dp(60), font_size=sp(17), bold=False,
        )
        root.add_widget(self._sim_btn)

        root.add_widget(Widget(size_hint_y=0.02))

        # Start button (enabled only when docked)
        self._start_btn = btn(
            "Start Unwind  →",
            AMBER, (0.11, 0.07, 0.12, 1), self._start,
            height=dp(86), font_size=sp(24),
        )
        self._start_btn.disabled = True
        self._start_btn.opacity = 0.35
        root.add_widget(self._start_btn)

        root.add_widget(Widget(size_hint_y=0.02))

        # Skip
        skip = btn("Not tonight", (0, 0, 0, 0), MUTED, self._skip,
                   height=dp(48), font_size=sp(16), bold=False)
        root.add_widget(skip)

        self.add_widget(root)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        app = App.get_running_app()
        bedtime = fmt_12h(app.prefs.get("bedtime", "23:00"))
        dur = app.prefs.get("unwind_duration", 30)
        self._bed_lbl.text = f"Bedtime at {bedtime}  ·  {dur}-minute ritual"
        self._orb.start()
        if self._ticker is None:
            self._ticker = Clock.schedule_interval(self._check_auto_start, 30)

    def on_leave(self):
        self._orb.stop()
        if self._ticker:
            self._ticker.cancel()
            self._ticker = None

    # ── Actions ───────────────────────────────────────────────────────────────

    def _toggle_sim_dock(self, *_):
        self._phone_docked = not self._phone_docked
        if self._phone_docked:
            self._sim_btn.text = "Simulate: Phone is docked ✓"
            self._sim_btn.color = (0.3, 0.7, 0.4, 1)
            self._start_btn.disabled = False
            self._start_btn.opacity = 1.0
            self._dock_instr.text = "Phone docked. Ready to begin!"
            self._dock_instr.color = (0.3, 0.7, 0.4, 1)
        else:
            self._sim_btn.text = "Simulate: Dock Phone"
            self._sim_btn.color = AMBER
            self._start_btn.disabled = True
            self._start_btn.opacity = 0.35
            self._dock_instr.text = "Place your phone face-down\non the dock to begin"
            self._dock_instr.color = MUTED

    def _start(self, *_):
        app = App.get_running_app()
        app.start_session()
        app.fade_to("session")

    def _skip(self, *_):
        App.get_running_app().go_to("home", "right")

    def _check_auto_start(self, dt):
        # Auto-navigate away if bedtime has passed (missed window)
        if App.get_running_app().is_bedtime_passed():
            App.get_running_app().go_to("home", "right")
