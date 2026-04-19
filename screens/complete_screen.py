"""Session complete — goodnight summary."""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.app import App

from screens.theme import BG, CARD, AMBER, ROSE, CREAM, PEACH, MUTED, MAUVE, btn, fmt_12h, BreathingOrb

_COMPLETE_BG = (0.09, 0.06, 0.13, 1)   # deep calm plum


class CompleteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build()

    def _build(self):
        with self.canvas.before:
            Color(*_COMPLETE_BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, "pos", self.pos),
                  size=lambda *_: setattr(self._bg, "size", self.size))

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(28), dp(54), dp(28), dp(40)],
            spacing=dp(14),
        )

        root.add_widget(Label(
            text="RITUAL COMPLETE",
            font_size=sp(13), color=AMBER,
            size_hint_y=None, height=dp(22),
        ))

        root.add_widget(Widget(size_hint_y=0.03))

        # Gentle orb (smaller, calmer)
        self._orb = BreathingOrb(color_rgba=(0.61, 0.50, 0.66, 1))  # mauve
        orb_wrap = Widget(size_hint_y=None, height=dp(160))
        self._orb.size_hint = (1, 1)
        self._orb.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        orb_wrap.add_widget(self._orb)
        root.add_widget(orb_wrap)

        root.add_widget(Label(
            text="Good night ☽",
            font_size=sp(36), bold=True, color=CREAM,
            size_hint_y=None, height=dp(56),
        ))

        root.add_widget(Widget(size_hint_y=0.02))

        # ── Stats cards ───────────────────────────────────────────────────
        self._duration_lbl = Label(
            text="", font_size=sp(20), color=PEACH,
            size_hint_y=None, height=dp(32),
        )
        self._pickups_lbl = Label(
            text="", font_size=sp(20), color=MUTED,
            size_hint_y=None, height=dp(32),
        )
        self._wake_lbl = Label(
            text="", font_size=sp(22), bold=True, color=AMBER,
            size_hint_y=None, height=dp(36),
        )
        root.add_widget(self._duration_lbl)
        root.add_widget(self._pickups_lbl)

        root.add_widget(Widget(size_hint_y=0.04))

        root.add_widget(Label(
            text="ALARM SET FOR", font_size=sp(11), color=MUTED,
            size_hint_y=None, height=dp(20),
        ))
        root.add_widget(self._wake_lbl)

        root.add_widget(Widget(size_hint_y=0.08))

        root.add_widget(btn(
            "View sleep stats", CARD, MAUVE,
            lambda *_: App.get_running_app().go_to("stats"),
            height=dp(60), font_size=sp(18), bold=False,
        ))

        root.add_widget(Widget(size_hint_y=0.02))

        root.add_widget(btn(
            "Done", AMBER, (0.11, 0.07, 0.12, 1),
            lambda *_: App.get_running_app().go_to("home", "right"),
            height=dp(76), font_size=sp(22),
        ))

        self.add_widget(root)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        app = App.get_running_app()
        elapsed = app.get_elapsed()
        dur_m = int(elapsed / 60)
        h, m = divmod(dur_m, 60)
        dur_str = f"{h}h {m:02d}m" if h else f"{m}m"

        pickups = app.session.get("pickup_count", 0)
        p_str = (
            "Phone never left the dock  ✓"
            if pickups == 0
            else f"Picked up {pickups} time{'s' if pickups != 1 else ''}"
        )

        self._duration_lbl.text = f"Unwound for  {dur_str}"
        self._pickups_lbl.text = p_str
        self._wake_lbl.text = fmt_12h(app.prefs.get("wake_time", ""))
        self._orb.start()

    def on_leave(self):
        self._orb.stop()
