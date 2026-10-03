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
    Conforms to the compound container background protocol (.bg_color).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = DEFAULT_CARD_WIDTH,
        height: int = DEFAULT_CARD_HEIGHT,
        corner_radius: float = DEFAULT_CARD_CORNER_RADIUS,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = DEFAULT_CARD_BORDER_WIDTH,
        shadow: bool = True,
        shadow_blur: float = DEFAULT_CARD_SHADOW_BLUR,
        shadow_spread: float = DEFAULT_CARD_SHADOW_SPREAD,
        shadow_offset_x: float = DEFAULT_CARD_SHADOW_OFFSET_X,
        shadow_offset_y: float = DEFAULT_CARD_SHADOW_OFFSET_Y,
        shadow_color: Optional[ColorLike] = None,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._corner_radius = float(corner_radius)
        self._custom_card_bg = bg_color
        self._custom_border_color = border_color
        self._border_width = float(border_width)

        self._shadow = shadow
        self._shadow_blur = float(shadow_blur)
        self._shadow_spread = float(shadow_spread)
        self._shadow_offset_x = float(shadow_offset_x)
        self._shadow_offset_y = float(shadow_offset_y)
        self._custom_shadow_color = shadow_color

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            **kwargs,
        )

        # Allow child widgets to be placed inside
        self.pack_propagate(True)
        self.grid_propagate(True)

    @property
    def bg_color(self) -> str:
        """Return the active inner surface fill color for child recursion."""
        return resolve_color_failsafe(self._custom_card_bg or self._palette.card_bg, palette=self._palette)

    def on_theme_update(self, pal: Palette) -> None:
        inner_bg = self.bg_color
        cascade_bg_to_children(self, inner_bg, palette=pal)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        rx = self._corner_radius * s
        ry = rx

        card_bg = resolve_color_failsafe(self._custom_card_bg or pal.card_bg, palette=pal)
        border_col = resolve_color_failsafe(self._custom_border_color or pal.card_border, palette=pal)
        bw = self._border_width * s

        sh_col = resolve_color_failsafe(self._custom_shadow_color or pal.shadow_color, palette=pal) if self._shadow else COLOR_TRANSPARENT
        sh_blur = self._shadow_blur * s if self._shadow else 0.0
        sh_spread = self._shadow_spread * s if self._shadow else 0.0
        sh_ox = self._shadow_offset_x * s if self._shadow else 0.0
        sh_oy = self._shadow_offset_y * s if self._shadow else 0.0

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
        if cnf is None and not kwargs:
            return super().configure()
        if cnf:
            kwargs.update(cnf)

        if "corner_radius" in kwargs:
            self._corner_radius = float(kwargs.pop("corner_radius"))
        if "bg_color" in kwargs:
            self._custom_card_bg = kwargs.pop("bg_color")
        if "border_color" in kwargs:
            self._custom_border_color = kwargs.pop("border_color")
        if "border_width" in kwargs:
            self._border_width = float(kwargs.pop("border_width"))
        self.request_redraw()
        return super().configure(**kwargs)
