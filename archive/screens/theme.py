"""Shared palette, utilities, and reusable widgets."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse
from kivy.animation import Animation

# ── Warm sunset palette ──────────────────────────────────────────────────────
BG     = (0.11, 0.07, 0.12, 1)   # #1c1220  deep plum
CARD   = (0.19, 0.12, 0.21, 1)   # #301e36  warm card
AMBER  = (0.98, 0.63, 0.26, 1)   # #f9a142  amber
ROSE   = (0.91, 0.53, 0.47, 1)   # #e88778  dusty rose
CREAM  = (0.99, 0.94, 0.88, 1)   # #fcf0e0  warm cream
PEACH  = (0.96, 0.75, 0.55, 1)   # #f5bf8d  soft peach
MUTED  = (0.55, 0.43, 0.55, 1)   # #8c6e8c  muted purple
MAUVE  = (0.61, 0.50, 0.66, 1)   # #9c7fa8  lavender mauve
WARN   = (0.22, 0.13, 0.08, 1)   # warm dark for T-5 warning
URGENT = (0.30, 0.12, 0.06, 1)   # deeper orange-brown for T-0


def fmt_12h(time_str):
    """'23:00' → '11:00 PM'"""
    if not time_str:
        return "—"
    try:
        h, m = map(int, time_str.split(":"))
        period = "AM" if h < 12 else "PM"
        h12 = h % 12 or 12
        return f"{h12}:{m:02d} {period}"
    except Exception:
        return time_str


def btn(text, bg, fg, on_press=None, height=dp(80), font_size=sp(22), bold=True):
    b = Button(
        text=text,
        font_size=font_size,
        bold=bold,
        color=fg,
        background_color=bg,
        background_normal="",
        background_down="",
        size_hint_y=None,
        height=height,
    )
    if on_press:
        b.bind(on_press=on_press)
    return b


def section_label(text):
    return Label(
        text=text,
        font_size=sp(12),
        color=MUTED,
        size_hint_y=None,
        height=dp(22),
        halign="center",
    )


class TimePicker(BoxLayout):
    """Reusable ▲/▼ time picker widget."""

    def __init__(self, hour=7, minute=0, minute_step=5, **kwargs):
        super().__init__(orientation="horizontal", spacing=dp(16), **kwargs)
        self._hour = hour
        self._minute = minute
        self._step = minute_step
        self._build()

    @property
    def time_str(self):
        return f"{self._hour:02d}:{self._minute:02d}"

    def set_time(self, time_str):
        try:
            h, m = map(int, time_str.split(":"))
            self._hour, self._minute = h, m
            self._hour_lbl.text = f"{h:02d}"
            self._min_lbl.text = f"{m:02d}"
            self._preview_lbl.text = fmt_12h(self.time_str)
        except Exception:
            pass

    def _build(self):
        self.add_widget(self._col("hour"))
        self.add_widget(Label(
            text=":", font_size=sp(72), bold=True, color=CREAM,
            size_hint_x=None, width=dp(28),
        ))
        self.add_widget(self._col("minute"))

    def _col(self, field):
        col = BoxLayout(orientation="vertical", spacing=dp(6))

        up = Button(
            text="▲", font_size=sp(26), color=AMBER,
            background_color=CARD, background_normal="", background_down="",
            size_hint_y=None, height=dp(70),
        )
        up.bind(on_press=lambda *_: self._adjust(field, 1))

        lbl = Label(font_size=sp(72), bold=True, color=CREAM)
        if field == "hour":
            lbl.text = f"{self._hour:02d}"
            self._hour_lbl = lbl
        else:
            lbl.text = f"{self._minute:02d}"
            self._min_lbl = lbl

        dn = Button(
            text="▼", font_size=sp(26), color=AMBER,
            background_color=CARD, background_normal="", background_down="",
            size_hint_y=None, height=dp(70),
        )
        dn.bind(on_press=lambda *_: self._adjust(field, -1))

        # 12-h preview lives at the bottom of the first column
        if field == "hour":
            self._preview_lbl = Label(
                text=fmt_12h(self.time_str),
                font_size=sp(17), color=PEACH,
                size_hint_y=None, height=dp(28),
            )

        col.add_widget(up)
        col.add_widget(lbl)
        col.add_widget(dn)
        if field == "hour":
            col.add_widget(self._preview_lbl)
        else:
            col.add_widget(Widget(size_hint_y=None, height=dp(28)))
        return col

    def _adjust(self, field, delta):
        if field == "hour":
            self._hour = (self._hour + delta) % 24
            self._hour_lbl.text = f"{self._hour:02d}"
        else:
            self._minute = (self._minute + delta * self._step) % 60
            self._min_lbl.text = f"{self._minute:02d}"
        self._preview_lbl.text = fmt_12h(self.time_str)


class BreathingOrb(Widget):
    """Softly pulsing ambient orb for the active session screen."""
    orb_r = NumericProperty(dp(88))

    def __init__(self, color_rgba=(0.98, 0.63, 0.26, 1), **kwargs):
        self._c = color_rgba
        super().__init__(**kwargs)
        with self.canvas:
            Color(self._c[0], self._c[1], self._c[2], 0.10)
            self._g2 = Ellipse()
            Color(self._c[0], self._c[1], self._c[2], 0.20)
            self._g1 = Ellipse()
            Color(self._c[0], self._c[1], self._c[2], 0.60)
            self._core = Ellipse()
        self.bind(pos=self._draw, size=self._draw, orb_r=self._draw)

    def _draw(self, *_):
        cx, cy = self.center
        r = self.orb_r
        for ellipse, f in ((self._g2, 1.75), (self._g1, 1.35), (self._core, 1.0)):
            s = r * 2 * f
            ellipse.pos = (cx - s / 2, cy - s / 2)
            ellipse.size = (s, s)

    def start(self):
        anim = (
            Animation(orb_r=dp(100), duration=4, t="in_out_sine")
            + Animation(orb_r=dp(78), duration=4, t="in_out_sine")
        )
        anim.repeat = True
        anim.start(self)

    def stop(self):
        Animation.cancel_all(self)
        self.orb_r = dp(88)
