"""Phone picked up mid-session — jarring attention-grab + sleep cost display."""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from kivy.app import App

from screens.theme import CARD, AMBER, ROSE, CREAM, MUTED, btn, fmt_12h

# Jarring warm-red background
_PAUSED_BG = (0.30, 0.07, 0.05, 1)


class PausedScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ticker = None
        self._pulse_anim = None
        self._build()

    def _build(self):
        with self.canvas.before:
            self._bg_color = Color(*_PAUSED_BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, "pos", self.pos),
                  size=lambda *_: setattr(self._bg, "size", self.size))

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(28), dp(54), dp(28), dp(40)],
            spacing=dp(14),
        )

        # ── Status header ─────────────────────────────────────────────────
        root.add_widget(Label(
            text="SESSION PAUSED",
            font_size=sp(13), color=ROSE,
            size_hint_y=None, height=dp(24),
        ))

        root.add_widget(Widget(size_hint_y=0.04))

        # ── Headline ──────────────────────────────────────────────────────
        root.add_widget(Label(
            text="Scrolling?",
            font_size=sp(46), bold=True, color=CREAM,
            size_hint_y=None, height=dp(66),
        ))

        # ── Sleep cost ────────────────────────────────────────────────────
        root.add_widget(Label(
            text="SLEEP TIME LOST",
            font_size=sp(12), color=MUTED,
            size_hint_y=None, height=dp(22),
        ))
        self._cost_lbl = Label(
            text="0:00",
            font_size=sp(72), bold=True, color=ROSE,
            size_hint_y=None, height=dp(100),
        )
        root.add_widget(self._cost_lbl)

        self._cost_sub = Label(
            text="of sleep replaced by screen time",
            font_size=sp(17), color=MUTED,
            size_hint_y=None, height=dp(30),
        )
        root.add_widget(self._cost_sub)

        root.add_widget(Widget(size_hint_y=0.08))

        # ── Bed + wake info ───────────────────────────────────────────────
        self._bed_info = Label(
            text="",
            font_size=sp(18), color=AMBER,
            size_hint_y=None, height=dp(32),
        )
        root.add_widget(self._bed_info)

        root.add_widget(Widget(size_hint_y=0.06))

        # ── Dock CTA ──────────────────────────────────────────────────────
        root.add_widget(btn(
            "Dock Phone & Continue",
            AMBER, (0.11, 0.07, 0.12, 1), self._dock,
            height=dp(86), font_size=sp(22),
        ))

        root.add_widget(Widget(size_hint_y=0.02))

        root.add_widget(btn(
            "End session & sleep", CARD, MUTED, self._end,
            height=dp(58), font_size=sp(17), bold=False,
        ))

        self.add_widget(root)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        app = App.get_running_app()
        bed = fmt_12h(app.prefs.get("bedtime", ""))
        wake = fmt_12h(app.prefs.get("wake_time", ""))
        self._bed_info.text = f"Bedtime {bed}  ·  Wake {wake}"
        self._tick(0)
        if self._ticker is None:
            self._ticker = Clock.schedule_interval(self._tick, 1)
        # Start pulsing background
        self._pulse_anim = (
            Animation(opacity=1.0, duration=0.6)
            + Animation(opacity=0.75, duration=0.6)
        )
        self._pulse_anim.repeat = True
        self._pulse_anim.start(self)

    def on_leave(self):
        if self._ticker:
            self._ticker.cancel()
            self._ticker = None
        Animation.cancel_all(self)
        self.opacity = 1.0

    # ── Tick ──────────────────────────────────────────────────────────────────

    def _tick(self, dt):
        app = App.get_running_app()
        # Paused time = wall-clock time since phone was picked up
        s = app.session
        if s.get("paused_at"):
            import time
            paused_secs = time.time() - s["paused_at"]
            m, sec = divmod(int(paused_secs), 60)
            self._cost_lbl.text = f"{m}:{sec:02d}"

    # ── Actions ───────────────────────────────────────────────────────────────

    def _dock(self, *_):
        App.get_running_app().dock_phone()  # navigates to session or incomplete

    def _end(self, *_):
        app = App.get_running_app()
        app.dock_phone()   # restore state cleanly
        app.stop_session()
        app.fade_to("complete")
