"""Docked after bedtime — show ritual progress and offer a choice."""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.app import App

from screens.theme import BG, CARD, AMBER, ROSE, CREAM, PEACH, MUTED, btn, fmt_12h

_INCOMPLETE_BG = (0.16, 0.09, 0.06, 1)   # warm dark amber-brown


class IncompleteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build()

    def _build(self):
        with self.canvas.before:
            Color(*_INCOMPLETE_BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, "pos", self.pos),
                  size=lambda *_: setattr(self._bg, "size", self.size))

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(28), dp(54), dp(28), dp(40)],
            spacing=dp(16),
        )

        root.add_widget(Label(
            text="RITUAL INCOMPLETE",
            font_size=sp(13), color=ROSE,
            size_hint_y=None, height=dp(24),
        ))

        root.add_widget(Widget(size_hint_y=0.04))

        root.add_widget(Label(
            text="Bedtime has passed.",
            font_size=sp(30), bold=True, color=CREAM,
            size_hint_y=None, height=dp(48),
        ))

        root.add_widget(Widget(size_hint_y=0.04))

        # Progress summary
        self._progress_lbl = Label(
            text="",
            font_size=sp(22), color=PEACH,
            halign="center",
            size_hint_y=None, height=dp(60),
        )
        root.add_widget(self._progress_lbl)

        # Visual bar
        bar_wrap = BoxLayout(size_hint_y=None, height=dp(20), padding=[dp(20), 0])
        self._bar_bg = BoxLayout(size_hint_y=None, height=dp(10))
        with self._bar_bg.canvas.before:
            Color(*CARD)
            self._bar_track = Rectangle(pos=self._bar_bg.pos, size=self._bar_bg.size)
        self._bar_bg.bind(
            pos=lambda *_: setattr(self._bar_track, "pos", self._bar_bg.pos),
            size=lambda *_: setattr(self._bar_track, "size", self._bar_bg.size),
        )
        self._bar_fill = BoxLayout(size_hint=(0, 1), height=dp(10))
        with self._bar_fill.canvas.before:
            Color(*AMBER)
            self._bar_rect = Rectangle(pos=self._bar_fill.pos, size=self._bar_fill.size)
        self._bar_fill.bind(
            pos=lambda *_: setattr(self._bar_rect, "pos", self._bar_fill.pos),
            size=lambda *_: setattr(self._bar_rect, "size", self._bar_fill.size),
        )
        self._bar_bg.add_widget(self._bar_fill)
        bar_wrap.add_widget(self._bar_bg)
        root.add_widget(bar_wrap)

        root.add_widget(Widget(size_hint_y=0.06))

        self._sub_lbl = Label(
            text="",
            font_size=sp(18), color=MUTED,
            halign="center",
            size_hint_y=None, height=dp(52),
        )
        root.add_widget(self._sub_lbl)

        root.add_widget(Widget(size_hint_y=0.08))

        # Continue option
        self._continue_btn = btn(
            "Continue ritual anyway",
            AMBER, (0.11, 0.07, 0.12, 1), self._continue_session,
            height=dp(80), font_size=sp(22),
        )
        root.add_widget(self._continue_btn)

        root.add_widget(Widget(size_hint_y=0.02))

        root.add_widget(btn(
            "End now & sleep  ☽",
            CARD, CREAM, self._end_now,
            height=dp(76), font_size=sp(20),
        ))

        self.add_widget(root)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        app = App.get_running_app()
        elapsed = app.get_elapsed()
        dur_secs = app.prefs.get("unwind_duration", 30) * 60
        completed_m = int(elapsed / 60)
        total_m = int(dur_secs / 60)
        remaining_m = max(0, total_m - completed_m)
        fraction = min(1.0, elapsed / dur_secs) if dur_secs > 0 else 0

        self._progress_lbl.text = (
            f"You completed {completed_m} of {total_m} minutes"
        )
        self._bar_fill.size_hint_x = fraction

        bed = fmt_12h(app.prefs.get("bedtime", ""))
        if remaining_m > 0:
            self._sub_lbl.text = (
                f"Continuing means {remaining_m} more minutes\npast your {bed} bedtime."
            )
            self._continue_btn.disabled = False
            self._continue_btn.opacity = 1.0
        else:
            self._sub_lbl.text = f"You completed the full ritual.\nTime to sleep!"
            self._continue_btn.disabled = True
            self._continue_btn.opacity = 0.3

    # ── Actions ───────────────────────────────────────────────────────────────

    def _continue_session(self, *_):
        # Resume — go back to active session
        App.get_running_app().fade_to("session")

    def _end_now(self, *_):
        app = App.get_running_app()
        app.stop_session()
        app.fade_to("complete")
