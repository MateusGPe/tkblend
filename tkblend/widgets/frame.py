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
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 0.0,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._corner_radius = float(corner_radius)
        self._custom_bg_color = bg_color
        self._custom_border_color = border_color
        self._border_width = float(border_width)

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            **kwargs,
        )

        self.pack_propagate(True)
        self.grid_propagate(True)

    @property
    def bg_color(self) -> str:
        """Return the active inner surface fill color for compound container recursion."""
        return resolve_color_failsafe(self._custom_bg_color or self._palette.bg, palette=self._palette)

    def on_theme_update(self, pal: Palette) -> None:
        inner_bg = self.bg_color
        cascade_bg_to_children(self, inner_bg, palette=pal)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        fill_col = resolve_color_failsafe(self._custom_bg_color or pal.bg, palette=pal)
        rx = self._corner_radius * s
        ry = rx

        surf.clear(self._resolved_parent_bg)
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
        if cnf is None and not kwargs:
            return super().configure()
        if cnf:
            kwargs.update(cnf)

        if 'corner_radius' in kwargs:
            self._corner_radius = float(kwargs.pop('corner_radius'))
        if 'bg_color' in kwargs:
            self._custom_bg_color = kwargs.pop('bg_color')
        if 'border_color' in kwargs:
            self._custom_border_color = kwargs.pop('border_color')
        if 'border_width' in kwargs:
            self._border_width = float(kwargs.pop('border_width'))
        self.request_redraw()
        return super().configure(**kwargs)
