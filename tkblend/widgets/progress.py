"""
Progress indicator widgets: ProgressBar (linear capsule) and CircularProgress (radial gauge).
"""

from __future__ import annotations
import math
import tkinter as tk
from typing import Optional

from tkblend.surface import LinearGradient, Path, ColorLike
from tkblend.theme import get_theme
from tkblend.widgets.base import Widget


class ProgressBar(Widget):
    """
    Antialiased smooth linear progress bar with capsule geometry and gradient fill.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 16,
        value: float = 0.0,
        track_color: Optional[ColorLike] = None,
        fill_color_start: Optional[ColorLike] = None,
        fill_color_end: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._value = max(0.0, min(100.0, float(value)))
        pal = get_theme()
        self._track_color = track_color or pal.track_bg
        self._fill_start = fill_color_start or pal.primary
        self._fill_end = fill_color_end or pal.accent
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = max(0.0, min(100.0, float(val)))
        self.render()

    def set_value(self, val: float) -> None:
        self.value = val

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        pad = 2.0 * self._scale
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        r = h / 2.0

        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, self._track_color)

        if self._value > 0.5:
            fill_w = max(r * 2.0, (self._value / 100.0) * w)
            grad = LinearGradient(pad, pad, pad + fill_w, pad)
            grad.add_stop(0.0, self._fill_start)
            grad.add_stop(1.0, self._fill_end)
            self._surface.fill_rounded_rect(pad, pad, fill_w, h, r, r, grad)

        self._surface.blit(self._photo)


ModernProgressBar = ProgressBar


class CircularProgress(Widget):
    """
    Antialiased circular progress ring / radial gauge with center numeric readout.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 110,
        value: float = 65.0,
        stroke_width: float = 8.0,
        track_color: Optional[ColorLike] = None,
        fill_color: Optional[ColorLike] = None,
        unit: str = "%",
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._value = max(0.0, min(100.0, float(value)))
        self._stroke_w = stroke_width
        pal = get_theme()
        self._track_color = track_color or pal.track_bg
        self._fill_color = fill_color or pal.primary
        self._unit = unit
        super().__init__(master=master, width=size, height=size, bg=parent_bg, **kwargs)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = max(0.0, min(100.0, float(val)))
        self.render()

    def set_value(self, val: float) -> None:
        self.value = val

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        sw = self._stroke_w * s
        r = (min(self._widget_w, self._widget_h) - sw * 2.0) / 2.0

        if r <= 0:
            return

        # Background circular track
        self._surface.stroke_circle(cx, cy, r, self._track_color, stroke_width=sw)

        # Progress Arc using Path arc_to
        if self._value > 0.0:
            sweep = (self._value / 100.0) * (2.0 * math.pi)
            p = Path()
            p.arc_to(cx, cy, r, r, -math.pi / 2.0, sweep)
            self._surface.stroke_path(p, self._fill_color, stroke_width=sw)

        # Center Value Readout
        font_sz = 16.0 * s
        pal = get_theme()
        self._surface.draw_text(
            f"{int(self._value)}{self._unit}",
            cx,
            cy + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color=pal.fg,
            align="center",
        )
        self._surface.blit(self._photo)


ModernCircularProgress = CircularProgress
