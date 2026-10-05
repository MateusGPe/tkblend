"""
Pure Blend2D Vector Sparkline widget powered by BaseControl.
"""

from __future__ import annotations

import math
import tkinter as tk
from typing import Optional, Sequence, List, Union, Tuple

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, Path, LinearGradient, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    blend_color_hex,
)
from tkblend.widgets.constants import (
    CURSOR_DEFAULT,
)


class Sparkline(BaseControl):
    """
    Miniature vector sparkline widget for dashboards, metrics, and cards.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        data: Sequence[float] = (),
        kind: str = "area",
        width: int = 120,
        height: int = 36,
        color: Optional[ColorLike] = None,
        line_width: float = 2.0,
        fill_alpha: float = 0.25,
        highlight_last: bool = True,
        cursor: Optional[str] = None,
        inner_bg: Optional[str] = None,
        outer_bg: Optional[str] = None,
        parent_bg: Optional[str] = None,
        bg_color: Optional[str] = None,
        **kwargs,
    ):
        self._data: List[float] = [float(v) for v in data] if data else [0.0]
        self._kind = kind.lower()
        self._custom_color = color or inner_bg
        self._line_width = float(line_width)
        self._fill_alpha = float(fill_alpha)
        self._highlight_last = highlight_last

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            inner_bg=inner_bg,
            outer_bg=outer_bg,
            parent_bg=parent_bg,
            bg_color=bg_color,
            **kwargs,
        )

    def _default_inner_bg(self, pal: Palette) -> str:
        return pal.primary

    @property
    def data(self) -> List[float]:
        return self._data

    @data.setter
    def data(self, vals: Sequence[float]) -> None:
        self._data = [float(v) for v in vals] if vals else [0.0]
        self.request_redraw()

    def set_data(self, vals: Sequence[float]) -> None:
        self.data = vals

    def push(self, val: float, max_points: int = 50) -> None:
        self._data.append(float(val))
        if len(self._data) > max_points:
            self._data.pop(0)
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        n = len(self._data)
        if n < 2:
            return

        col = resolve_color_failsafe(self._custom_color or self.inner_bg or pal.primary, palette=pal)
        min_v = min(self._data)
        max_v = max(self._data)
        rng = max(0.0001, max_v - min_v)

        surf.clear(self.outer_bg)

        pad_x = 4.0 * s
        pad_y = 4.0 * s
        usable_w = w - pad_x * 2.0
        usable_h = h - pad_y * 2.0
        lw = self._line_width * s

        pts = []
        for i, val in enumerate(self._data):
            x = pad_x + (i / (n - 1)) * usable_w
            norm_y = (val - min_v) / rng
            y = (h - pad_y) - norm_y * usable_h
            pts.append((x, y))

        if self._kind in ("line", "area"):
            path = Path()
            path.move_to(pts[0][0], pts[0][1])
            for i in range(1, len(pts)):
                path.line_to(pts[i][0], pts[i][1])

            if self._kind == "area":
                area_path = Path()
                area_path.move_to(pts[0][0], h - pad_y)
                area_path.line_to(pts[0][0], pts[0][1])
                for i in range(1, len(pts)):
                    area_path.line_to(pts[i][0], pts[i][1])
                area_path.line_to(pts[-1][0], h - pad_y)
                area_path.close()

                # Gradient fill
                grad = LinearGradient(0, pad_y, 0, h - pad_y)
                grad.add_stop(0.0, col, alpha=self._fill_alpha)
                grad.add_stop(1.0, col, alpha=0.0)
                surf.fill_path(area_path, grad)

            # Stroke line
            surf.stroke_path(path, col, stroke_width=lw)

            # Highlight last point
            if self._highlight_last and pts:
                lx, ly = pts[-1]
                surf.fill_circle(lx, ly, 3.5 * s, col)
                surf.stroke_circle(lx, ly, 3.5 * s, pal.card_bg, stroke_width=1.5 * s)

        elif self._kind == "bar":
            bar_w = max(2.0 * s, (usable_w / n) - 2.0 * s)
            for x, y in pts:
                bar_h = (h - pad_y) - y
                surf.fill_rounded_rect(x - bar_w / 2.0, y, bar_w, max(2.0 * s, bar_h), bar_w / 2.0, bar_w / 2.0, col)
