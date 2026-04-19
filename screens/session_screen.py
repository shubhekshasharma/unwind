"""Active unwind session — calming animation + countdown + nudges."""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from kivy.app import App

from screens.theme import BG, CARD, AMBER, ROSE, CREAM, PEACH, MUTED, MAUVE, btn, fmt_12h, BreathingOrb

NUDGES = [
    "Try writing in a journal tonight",
    "Take five slow, deep breaths",
    "Read a few pages of your book",
    "Note three things you're grateful for",
    "Gently stretch your neck and shoulders",
    "Reflect on something that went well today",
    "Prepare tomorrow's to-do list on paper",
    "Try a quiet body-scan meditation",
    "Dim the lights and let your mind rest",
]


class SessionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ticker = None
        self._nudge_ticker = None
        self._nudge_idx = 0
        self._build()

    def _build(self):
        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, "pos", self.pos),
                  size=lambda *_: setattr(self._bg, "size", self.size))

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(28), dp(44), dp(28), dp(32)],
            spacing=dp(8),
        )

        # ── Header ────────────────────────────────────────────────────────
        root.add_widget(Label(
            text="UNWIND SESSION",
            font_size=sp(12), color=MUTED,
            size_hint_y=None, height=dp(22),
        ))

        # ── Breathing orb (centrepiece) ───────────────────────────────────
        self._orb = BreathingOrb(color_rgba=(0.98, 0.63, 0.26, 1))
        orb_wrap = Widget(size_hint_y=None, height=dp(220))
        self._orb.size_hint = (1, 1)
        self._orb.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        orb_wrap.add_widget(self._orb)
        root.add_widget(orb_wrap)

        # ── Countdown ─────────────────────────────────────────────────────
        root.add_widget(Label(
            text="TIME REMAINING",
            font_size=sp(11), color=MUTED,
            size_hint_y=None, height=dp(20),
        ))
        self._countdown_lbl = Label(
            text="--:--",
            font_size=sp(64), bold=True, color=AMBER,
            size_hint_y=None, height=dp(90),
        )
        root.add_widget(self._countdown_lbl)

        # ── Bedtime + dock status row ─────────────────────────────────────
        info_row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(20))
        self._bed_lbl = Label(text="", font_size=sp(16), color=PEACH)
        self._dock_lbl = Label(text="● docked", font_size=sp(16), color=(0.4, 0.8, 0.5, 1))
        info_row.add_widget(self._bed_lbl)
        info_row.add_widget(self._dock_lbl)
        root.add_widget(info_row)

        root.add_widget(Widget(size_hint_y=0.04))

        # ── Nudge strip ───────────────────────────────────────────────────
        self._nudge_lbl = Label(
            text=NUDGES[0],
            font_size=sp(17), color=MAUVE,
            halign="center",
            size_hint_y=None, height=dp(50),
        )
        root.add_widget(self._nudge_lbl)

        root.add_widget(Widget(size_hint_y=0.04))

        # ── Phone picked up (jarring interruption) ────────────────────────
        self._pickup_btn = btn(
            "Phone Picked Up",
            (0.28, 0.10, 0.10, 1), ROSE, self._pickup,
            height=dp(76), font_size=sp(22),
        )
        root.add_widget(self._pickup_btn)

        root.add_widget(Widget(size_hint_y=0.02))

        end = btn("End Session", CARD, MUTED, self._end,
                  height=dp(56), font_size=sp(17), bold=False)
        root.add_widget(end)

        self.add_widget(root)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        app = App.get_running_app()
        self._bed_lbl.text = f"Bedtime  {fmt_12h(app.prefs.get('bedtime', ''))}"
        self._orb.start()
        self._tick(0)
        if self._ticker is None:
            self._ticker = Clock.schedule_interval(self._tick, 1)
        if self._nudge_ticker is None:
            self._nudge_ticker = Clock.schedule_interval(self._rotate_nudge, 30)

    def on_leave(self):
        self._orb.stop()
        if self._ticker:
            self._ticker.cancel()
            self._ticker = None
        if self._nudge_ticker:
            self._nudge_ticker.cancel()
            self._nudge_ticker = None

    # ── Tick ──────────────────────────────────────────────────────────────────

    def _tick(self, dt):
        app = App.get_running_app()

        # Countdown: time remaining in unwind session (to bedtime)
        secs_left = app.secs_to_bedtime()
        if secs_left is not None and secs_left > 0:
            m, s = divmod(int(secs_left), 60)
            h, m = divmod(m, 60)
            self._countdown_lbl.text = f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        elif secs_left is not None and secs_left <= 0:
            # Bedtime reached — complete
            self._complete()
            return
        else:
            self._countdown_lbl.text = "--:--"

        # Pickup count in dock label
        pickups = app.session.get("pickup_count", 0)
        p_str = f"  ·  {pickups} pickup{'s' if pickups != 1 else ''}" if pickups else ""
        self._dock_lbl.text = f"● docked{p_str}"

    def _rotate_nudge(self, dt):
        self._nudge_idx = (self._nudge_idx + 1) % len(NUDGES)
        anim = Animation(opacity=0, duration=0.5)
        def _swap(a, w):
            self._nudge_lbl.text = NUDGES[self._nudge_idx]
            Animation(opacity=1, duration=0.5).start(self._nudge_lbl)
        anim.bind(on_complete=_swap)
        anim.start(self._nudge_lbl)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _pickup(self, *_):
        App.get_running_app().pickup_phone()  # navigates to paused_screen

    def _end(self, *_):
        app = App.get_running_app()
        app.stop_session()
        app.fade_to("complete")

    def _complete(self):
        App.get_running_app().fade_to("complete")
