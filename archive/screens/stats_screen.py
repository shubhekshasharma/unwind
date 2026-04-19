from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.app import App

from screens.theme import BG, CARD, AMBER, ROSE, CREAM, PEACH, MUTED, MAUVE, btn, fmt_12h


def _fmt_dur(secs):
    if not secs:
        return "—"
    m = int(secs / 60)
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


class _Card(BoxLayout):
    def __init__(self, data, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(8),
            size_hint_y=None,
            height=dp(152),
            **kwargs,
        )
        with self.canvas.before:
            Color(*CARD)
            self._r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self.bind(pos=lambda *_: setattr(self._r, "pos", self.pos),
                  size=lambda *_: setattr(self._r, "size", self.size))

        date     = data.get("created_at") or "—"
        dur      = _fmt_dur(data.get("duration_seconds"))
        pickups  = int(data.get("pickup_count") or 0)
        alarm    = fmt_12h(data.get("alarm_time")) if data.get("alarm_time") else "—"

        self.add_widget(Label(
            text=date, font_size=sp(14), color=MUTED,
            size_hint_y=None, height=dp(22), halign="left",
        ))
        self.add_widget(Label(
            text=f"Unwound for  {dur}",
            font_size=sp(22), bold=True, color=CREAM,
            size_hint_y=None, height=dp(36), halign="left",
        ))
        row = BoxLayout(size_hint_y=None, height=dp(28))
        p_color = ROSE if pickups > 2 else (0.4, 0.8, 0.5, 1)
        row.add_widget(Label(text=f"Pickups: {pickups}", font_size=sp(17), color=p_color))
        row.add_widget(Label(text=f"Bedtime: {alarm}",  font_size=sp(17), color=AMBER))
        self.add_widget(row)


class StatsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        from kivy.uix.button import Button
        back = Button(
            text="←", font_size=sp(28), color=CREAM,
            background_color=(0, 0, 0, 0), background_normal="",
            size_hint_x=None, width=dp(54),
        )
        back.bind(on_press=lambda *_: App.get_running_app().go_to("home", "right"))
        hdr.add_widget(back)
        hdr.add_widget(Label(text="Sleep Stats", font_size=sp(24), bold=True, color=CREAM))
        hdr.add_widget(Widget(size_hint_x=None, width=dp(54)))
        root.add_widget(hdr)

        self._summary_lbl = Label(
            text="", font_size=sp(16), color=MUTED,
            size_hint_y=None, height=dp(26),
        )
        root.add_widget(self._summary_lbl)

        scroll = ScrollView(do_scroll_x=False)
        self._list = GridLayout(
            cols=1, spacing=dp(14), size_hint_y=None,
            padding=[0, dp(4), 0, dp(4)],
        )
        self._list.bind(minimum_height=self._list.setter("height"))
        scroll.add_widget(self._list)
        root.add_widget(scroll)

        self.add_widget(root)

    def on_enter(self):
        self._refresh()

    def _refresh(self):
        self._list.clear_widgets()
        sessions = App.get_running_app().get_sessions(n=10)
        if not sessions:
            self._summary_lbl.text = "No completed sessions yet"
            self._list.add_widget(Label(
                text="Complete your first Unwind\nsession to see stats here.",
                font_size=sp(19), color=MUTED, halign="center",
                size_hint_y=None, height=dp(110),
            ))
            return
        total = sum(s.get("duration_seconds") or 0 for s in sessions)
        avg = total / len(sessions)
        self._summary_lbl.text = f"{len(sessions)} sessions  ·  avg {_fmt_dur(avg)}"
        for s in sessions:
            self._list.add_widget(_Card(s))
