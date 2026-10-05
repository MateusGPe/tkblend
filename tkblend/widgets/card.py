"""
Pure Blend2D Vector Card container powered by NativeController.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    cascade_bg_to_children,
)
from tkblend.widgets.constants import (
    DEFAULT_CARD_WIDTH,
    DEFAULT_CARD_HEIGHT,
    DEFAULT_CARD_CORNER_RADIUS,
    DEFAULT_CARD_BORDER_WIDTH,
    DEFAULT_CARD_SHADOW_BLUR,
    DEFAULT_CARD_SHADOW_SPREAD,
    DEFAULT_CARD_SHADOW_OFFSET_X,
    DEFAULT_CARD_SHADOW_OFFSET_Y,
    CURSOR_DEFAULT,
    COLOR_TRANSPARENT,
)


class Card(BaseControl):
    """
    Modern container card with soft drop shadow, rounded corners, and border.
    Conforms to the compound container background protocol (.bg_color / .inner_bg).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = DEFAULT_CARD_WIDTH,
        height: int = DEFAULT_CARD_HEIGHT,
        corner_radius: float = DEFAULT_CARD_CORNER_RADIUS,
        inner_bg: Optional[ColorLike] = None,
        outer_bg: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = DEFAULT_CARD_BORDER_WIDTH,
        shadow: bool = True,
        shadow_blur: float = DEFAULT_CARD_SHADOW_BLUR,
        shadow_spread: float = DEFAULT_CARD_SHADOW_SPREAD,
        shadow_offset_x: float = DEFAULT_CARD_SHADOW_OFFSET_X,
        shadow_offset_y: float = DEFAULT_CARD_SHADOW_OFFSET_Y,
        shadow_color: Optional[ColorLike] = None,
        shadow_insets: bool = True,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._corner_radius = float(corner_radius)
        self._custom_border_color = border_color
        self._border_width = float(border_width)

        self._shadow = shadow
        self._shadow_blur = float(shadow_blur)
        self._shadow_spread = float(shadow_spread)
        self._shadow_offset_x = float(shadow_offset_x)
        self._shadow_offset_y = float(shadow_offset_y)
        self._custom_shadow_color = shadow_color
        self._shadow_insets = shadow_insets

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

        # Allow child widgets to be placed inside
        self.pack_propagate(True)
        self.grid_propagate(True)

    def _default_inner_bg(self, pal: Palette) -> str:
        return pal.card_bg

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

        rx = self._corner_radius * s
        ry = rx

        card_bg = self.inner_bg
        border_col = resolve_color_failsafe(self._custom_border_color or pal.card_border, palette=pal)
        bw = self._border_width * s

        sh_col = resolve_color_failsafe(self._custom_shadow_color or pal.shadow_color, palette=pal) if self._shadow else COLOR_TRANSPARENT
        sh_blur = self._shadow_blur * s if self._shadow else 0.0
        sh_spread = self._shadow_spread * s if self._shadow else 0.0
        sh_ox = self._shadow_offset_x * s if self._shadow else 0.0
        sh_oy = self._shadow_offset_y * s if self._shadow else 0.0

        # Clear background with outer background
        surf.clear(self.outer_bg)

        # Draw card with soft shadow, fill, and border
        surf.draw_card(
            0.0,
            0.0,
            w,
            h,
            rx=rx,
            ry=ry,
            bg_color=card_bg,
            border_color=border_col,
            border_width=bw,
            shadow_blur=sh_blur,
            shadow_spread=sh_spread,
            shadow_offset_x=sh_ox,
            shadow_offset_y=sh_oy,
            shadow_color=sh_col,
        )

    def configure(self, cnf=None, **kwargs):
        return super().configure(cnf, **kwargs)
