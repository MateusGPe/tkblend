"""
Pure Blend2D Vector Frame container powered by BaseControl and NativeController.
Zero TTK dependencies, conforms to compound container protocol (.bg_color).
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    cascade_bg_to_children,
)
from tkblend.widgets.constants import (
    DEFAULT_BASE_WIDTH,
    DEFAULT_BASE_HEIGHT,
    CURSOR_DEFAULT,
    COLOR_TRANSPARENT,
)


class Frame(BaseControl):
    """
    Antialiased vector frame container with optional rounded corners, background fill,
    border stroke, and child background inheritance.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = DEFAULT_BASE_WIDTH,
        height: int = DEFAULT_BASE_HEIGHT,
        corner_radius: float = 0.0,
        inner_bg: Optional[ColorLike] = None,
        outer_bg: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 0.0,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._corner_radius = float(corner_radius)
        self._custom_border_color = border_color
        self._border_width = float(border_width)

        super().__init__(
            master=master,
            width=width,
            height=height,
            inner_bg=inner_bg or bg_color,
            outer_bg=outer_bg or parent_bg,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            **kwargs,
        )

        self.pack_propagate(True)
        self.grid_propagate(True)

    def _default_inner_bg(self, pal: Palette) -> str:
        return self.outer_bg or pal.bg

    def set_inner_bg(self, color: ColorLike, render: bool = True, explicit: bool = True) -> None:
        super().set_inner_bg(color, render=render, explicit=explicit)
        cascade_bg_to_children(self, self.inner_bg, palette=self._palette)

    def on_theme_update(self, pal: Palette) -> None:
        inner_bg = self.inner_bg
        cascade_bg_to_children(self, inner_bg, palette=pal)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        fill_col = self.inner_bg
        rx = self._corner_radius * s
        ry = rx

        surf.clear(self.outer_bg)
        if rx > 0.5:
            surf.fill_rounded_rect(0.0, 0.0, w, h, rx, ry, fill_col)
            if self._border_width > 0.0:
                bc = resolve_color_failsafe(self._custom_border_color or pal.border, palette=pal)
                surf.stroke_rounded_rect(0.0, 0.0, w, h, rx, ry, bc, stroke_width=self._border_width * s)
        else:
            surf.fill_rect(0.0, 0.0, w, h, fill_col)
            if self._border_width > 0.0:
                bc = resolve_color_failsafe(self._custom_border_color or pal.border, palette=pal)
                surf.stroke_rect(0.0, 0.0, w, h, bc, stroke_width=self._border_width * s)

    def configure(self, cnf=None, **kwargs):
        return super().configure(cnf, **kwargs)
