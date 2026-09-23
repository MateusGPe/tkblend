"""
Progress indicator widgets: ProgressBar (linear capsule) and CircularProgress (radial gauge).
"""

from __future__ import annotations
import math
import tkinter as tk
from typing import Optional

from tkblend.surface import LinearGradient, Path, ColorLike
from tkblend.theme import get_theme, Palette, resolve_color_failsafe
from tkblend.widgets.base import Widget


def _resolve_color(color: Optional[ColorLike], fallback: str, pal: Palette) -> ColorLike:
    if color is None:
        return fallback
    if isinstance(color, str):
        return resolve_color_failsafe(color, fallback=fallback, palette=pal)
    return color


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
        self._explicit_track_color = track_color
        self._explicit_fill_start = fill_color_start
        self._explicit_fill_end = fill_color_end
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

    @property
    def track_color(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_track_color, pal.track_bg, pal)

    @track_color.setter
    def track_color(self, val: Optional[ColorLike]) -> None:
        self._explicit_track_color = val
        self.render()

    @property
    def _track_color(self) -> ColorLike:
        return self.track_color

    @property
    def _fill_start(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_fill_start, pal.primary, pal)

    @property
    def _fill_end(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_fill_end, pal.accent, pal)

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
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            pad = 2.0 * self._scale
            w = max(1.0, self._widget_w - pad * 2.0)
            h = max(1.0, self._widget_h - pad * 2.0)
            r = h / 2.0

            pal = get_theme()
            track_col = _resolve_color(self._explicit_track_color, pal.track_bg, pal)
            fill_start = _resolve_color(self._explicit_fill_start, pal.primary, pal)

            prog = max(0.0, min(1.0, self._value / 100.0))
            self._surface.draw_progress_bar(
                x=pad,
                y=pad,
                w=w,
                h=h,
                rx=r,
                ry=r,
                track_bg=track_col,
                bar_bg=fill_start,
                progress_t=prog,
            )
            self._surface.blit(self._photo)
        except Exception:
            pass


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
        self._explicit_track_color = track_color
        self._explicit_fill_color = fill_color
        self._unit = unit
        super().__init__(master=master, width=size, height=size, bg=parent_bg, **kwargs)

    @property
    def track_color(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_track_color, pal.track_bg, pal)

    @track_color.setter
    def track_color(self, val: Optional[ColorLike]) -> None:
        self._explicit_track_color = val
        self.render()

    @property
    def _track_color(self) -> ColorLike:
        return self.track_color

    @property
    def fill_color(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_fill_color, pal.primary, pal)

    @fill_color.setter
    def fill_color(self, val: Optional[ColorLike]) -> None:
        self._explicit_fill_color = val
        self.render()

    @property
    def _fill_color(self) -> ColorLike:
        return self.fill_color

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
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            cx = self._widget_w / 2.0
            cy = self._widget_h / 2.0
            sw = self._stroke_w * s
            r = (min(self._widget_w, self._widget_h) - sw * 2.0) / 2.0

            if r <= 0:
                return

            pal = get_theme()
            track_col = _resolve_color(self._explicit_track_color, pal.track_bg, pal)
            fill_col = _resolve_color(self._explicit_fill_color, pal.primary, pal)

            # Background circular track
            self._surface.stroke_circle(cx, cy, r, track_col, stroke_width=sw)

            # Progress Arc using Path arc_to
            if self._value > 0.0:
                sweep = (self._value / 100.0) * (2.0 * math.pi)
                p = Path()
                p.arc_to(cx, cy, r, r, -math.pi / 2.0, sweep)
                self._surface.stroke_path(p, fill_col, stroke_width=sw)

            # Center Value Readout
            font_sz = 16.0 * s
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
        except Exception:
            pass


ModernCircularProgress = CircularProgress
