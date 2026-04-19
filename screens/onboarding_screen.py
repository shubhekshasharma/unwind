from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.app import App

from screens.theme import (
    BG, CARD, AMBER, CREAM, PEACH, MUTED, MAUVE,
    btn, TimePicker, fmt_12h,
)

DURATIONS = [15, 20, 30, 45, 60]

STEPS = [
    ("Rise & shine", "When do you want to wake up?"),
    ("Wind-down time", "When do you want to be in bed?"),
    ("Your ritual", "How long is your nightly unwind?"),
]


class OnboardingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._step = 0
        self._wake_picker = TimePicker(hour=7, minute=0)
        self._bed_picker  = TimePicker(hour=23, minute=0)
        self._dur_idx     = DURATIONS.index(30)
        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, "pos", self.pos),
                  size=lambda *_: setattr(self._bg, "size", self.size))

        self._root = BoxLayout(
            orientation="vertical",
            padding=[dp(30), dp(50), dp(30), dp(40)],
            spacing=dp(16),
        )

        # App name
        self._root.add_widget(Label(
            text="unwind", font_size=sp(15), color=MUTED,
            size_hint_y=None, height=dp(24),
        ))

        # Step dots
        self._dots_row = BoxLayout(
            size_hint_y=None, height=dp(16), spacing=dp(10),
        )
        self._root.add_widget(self._dots_row)

        self._root.add_widget(Widget(size_hint_y=0.04))

        # Title + subtitle
        self._title = Label(font_size=sp(28), bold=True, color=CREAM,
                            size_hint_y=None, height=dp(44))
        self._sub   = Label(font_size=sp(18), color=MUTED,
                            size_hint_y=None, height=dp(32))
        self._root.add_widget(self._title)
        self._root.add_widget(self._sub)

        self._root.add_widget(Widget(size_hint_y=0.06))

        # Content area (swapped each step)
        self._content = BoxLayout(orientation="vertical")
        self._root.add_widget(self._content)

        self._root.add_widget(Widget(size_hint_y=0.06))

        # Next / Done button
        self._next_btn = btn("Next →", AMBER, BG, self._next, height=dp(80), font_size=sp(22))
        self._root.add_widget(self._next_btn)

        self.add_widget(self._root)
        self._show_step(0)

    # ── Steps ─────────────────────────────────────────────────────────────────

    def _show_step(self, step):
        self._step = step
        title, sub = STEPS[step]
        self._title.text = title
        self._sub.text   = sub

        # Dots
        self._dots_row.clear_widgets()
        self._dots_row.add_widget(Widget())  # spacer
        for i in range(3):
            dot = Widget(size_hint=(None, None), size=(dp(10), dp(10)))
            with dot.canvas:
                Color(*(AMBER if i == step else MUTED))
                Ellipse(pos=dot.pos, size=dot.size)
            self._dots_row.add_widget(dot)
        self._dots_row.add_widget(Widget())

        self._next_btn.text = "Done  ✓" if step == 2 else "Next →"

        self._content.clear_widgets()
        if step == 0:
            self._content.add_widget(self._wake_picker)
        elif step == 1:
            self._content.add_widget(self._bed_picker)
        else:
            self._content.add_widget(self._dur_picker_widget())

    def _dur_picker_widget(self):
        col = BoxLayout(orientation="vertical", spacing=dp(12))

        up = btn("▲", CARD, AMBER, lambda *_: self._adj_dur(1), height=dp(70))
        self._dur_lbl = Label(
            text=f"{DURATIONS[self._dur_idx]} min",
            font_size=sp(72), bold=True, color=CREAM,
        )
        dn = btn("▼", CARD, AMBER, lambda *_: self._adj_dur(-1), height=dp(70))
        self._dur_sub_lbl = Label(
            text=self._dur_hint(), font_size=sp(17), color=PEACH,
            size_hint_y=None, height=dp(28),
        )

        col.add_widget(up)
        col.add_widget(self._dur_lbl)
        col.add_widget(dn)
        col.add_widget(self._dur_sub_lbl)
        return col

    def _adj_dur(self, delta):
        self._dur_idx = (self._dur_idx + delta) % len(DURATIONS)
        self._dur_lbl.text = f"{DURATIONS[self._dur_idx]} min"
        self._dur_sub_lbl.text = self._dur_hint()

    def _dur_hint(self):
        dur = DURATIONS[self._dur_idx]
        app = App.get_running_app()
        bed = app.prefs.get("bedtime") or self._bed_picker.time_str
        try:
            from datetime import datetime, timedelta
            h, m = map(int, bed.split(":"))
            now = datetime.now()
            bed_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            start_dt = bed_dt - timedelta(minutes=dur)
            start_str = fmt_12h(f"{start_dt.hour:02d}:{start_dt.minute:02d}")
            return f"Starts at {start_str}"
        except Exception:
            return ""

    # ── Navigation ────────────────────────────────────────────────────────────

    def _next(self, *_):
        app = App.get_running_app()

        if self._step == 0:
            app.prefs["wake_time"] = self._wake_picker.time_str
        elif self._step == 1:
            app.prefs["bedtime"] = self._bed_picker.time_str
        elif self._step == 2:
            app.prefs["unwind_duration"] = DURATIONS[self._dur_idx]
            app.prefs["onboarding_complete"] = True
            app.save_prefs()
            app.go_to("home")
            return

        self._show_step(self._step + 1)
