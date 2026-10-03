"""
Pure Blend2D Vector Circular Progress and Gauge widgets powered by BaseControl.
"""

from __future__ import annotations

import math
import tkinter as tk
from typing import Optional, Callable, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    blend_color_hex,
)
from tkblend.font import parse_font
from tkblend.widgets.constants import (
    DEFAULT_FONT_SIZE,
    CURSOR_DEFAULT,
)
from tkblend.widgets.utils import compute_text_baseline_y


class CircularProgress(BaseControl):
    """
    Antialiased circular progress ring / radial gauge with customizable track,
    gradient/solid indicator, and center text readout.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 110,
        value: float = 65.0,
        min_value: float = 0.0,
        max_value: float = 100.0,
        stroke_width: float = 8.0,
        thickness: Optional[float] = None,
        track_color: Optional[ColorLike] = None,
        fill_color: Optional[ColorLike] = None,
        color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        show_value: bool = True,
        unit: str = "%",
        title: Optional[str] = None,
        start_angle: float = -90.0,
        sweep_angle: float = 360.0,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        if thickness is not None:
            stroke_width = float(thickness)
        elif "thickness" in kwargs:
            stroke_width = float(kwargs.pop("thickness"))

        self._min = float(min_value)
        self._max = float(max_value)
        self._value = max(self._min, min(self._max, float(value)))
        self._stroke_w = float(stroke_width)
        self._custom_track_color = track_color
        self._custom_fill_color = color or fill_color
        self._custom_text_color = text_color
        self._show_value = show_value
        self._unit = unit
        self._title = title
        self._start_angle = float(start_angle)
        self._sweep_angle = float(sweep_angle)

        super().__init__(
            master=master,
            width=size,
            height=size,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            **kwargs,
        )

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = max(self._min, min(self._max, float(val)))
        self.request_redraw()

    def get(self) -> float:
        return self.value

    def set(self, val: float) -> None:
        self.value = val

    def step(self, amount: float = 1.0) -> None:
        self.value = self._value + amount

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        cx = w / 2.0
        cy = h / 2.0
        sw = self._stroke_w * s
        r = min(w, h) / 2.0 - sw / 2.0 - 2.0 * s

        track_col = resolve_color_failsafe(self._custom_track_color or pal.track_bg, palette=pal)
        fill_col = resolve_color_failsafe(self._custom_fill_color or pal.primary, palette=pal)
        text_col = resolve_color_failsafe(self._custom_text_color or pal.fg, palette=pal)

        # Clear parent background
        surf.clear(self._resolved_parent_bg)

        # Draw full background track
        if self._sweep_angle >= 359.9:
            surf.stroke_circle(cx, cy, r, track_col, stroke_width=sw)
        else:
            surf.stroke_arc(
                cx, cy, r,
                math.radians(self._start_angle),
                math.radians(self._sweep_angle),
                track_col,
                stroke_width=sw,
            )

        # Draw progress arc
        val_range = max(0.0001, self._max - self._min)
        fraction = (self._value - self._min) / val_range
        arc_sweep = self._sweep_angle * fraction

        if abs(arc_sweep) > 0.1:
            surf.stroke_arc(
                cx, cy, r,
                math.radians(self._start_angle),
                math.radians(arc_sweep),
                fill_col,
                stroke_width=sw,
            )

        # Draw center readout text
        if self._show_value:
            main_val_str = f"{int(self._value) if self._value.is_integer() else self._value:.1f}{self._unit}"
            font_sz = max(10.0, (r * 0.45))
            font_cfg = parse_font(font_size=font_sz / s, bold=True)
            
            if self._title:
                val_y = compute_text_baseline_y(cy - 4.0 * s, font_sz)
                surf.draw_text(
                    main_val_str,
                    cx,
                    val_y,
                    font_size=font_sz,
                    font_family=font_cfg.family,
                    color=text_col,
                    bold=True,
                    align="center",
                )
                title_sz = max(8.0, font_sz * 0.5)
                title_cfg = parse_font(font_size=title_sz / s, bold=False)
                title_y = compute_text_baseline_y(cy + font_sz * 0.6, title_sz)
                surf.draw_text(
                    self._title,
                    cx,
                    title_y,
                    font_size=title_sz,
                    font_family=title_cfg.family,
                    color=pal.text_muted,
                    bold=False,
                    align="center",
                )
            else:
                val_y = compute_text_baseline_y(cy, font_sz)
                surf.draw_text(
                    main_val_str,
                    cx,
                    val_y,
                    font_size=font_sz,
                    font_family=font_cfg.family,
                    color=text_col,
                    bold=True,
                    align="center",
                )


class Gauge(CircularProgress):
    """
    Radial dial gauge with a 240-degree sweep, tick marks, and pointer needle.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 140,
        value: float = 50.0,
        min_value: float = 0.0,
        max_value: float = 100.0,
        title: Optional[str] = "Speed",
        unit: str = "km/h",
        **kwargs,
    ):
        super().__init__(
            master=master,
            size=size,
            value=value,
            min_value=min_value,
            max_value=max_value,
            start_angle=150.0,
            sweep_angle=240.0,
            title=title,
            unit=unit,
            **kwargs,
        )
