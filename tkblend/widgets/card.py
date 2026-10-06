"""
Pure Blend2D Vector Card container powered by NativeController.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, parse_color, DrawBatch
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

        self.add_class("card")
        if self._shadow:
            self.add_class("elevated")

        # Allow child widgets to be placed inside
        self.pack_propagate(True)
        self.grid_propagate(True)

        self._update_vars()
        self._sync_batch()

    def _update_vars(self) -> None:
        pal = self._palette
        card_bg = self.inner_bg
        border_col = resolve_color_failsafe(self._custom_border_color or pal.card_border, palette=pal)
        sh_col = resolve_color_failsafe(self._custom_shadow_color or pal.shadow_color, palette=pal) if self._shadow else COLOR_TRANSPARENT

        self.set_var("--card-bg", card_bg)
        self.set_var("--card-border", border_col)
        self.set_var("--card-shadow", sh_col)
        self.set_var("--card-rx", str(self._corner_radius * self.scale_factor))
        self.set_var("--card-bw", str(self._border_width * self.scale_factor))

    def _sync_batch(self) -> None:
        w = float(self.winfo_width() if self.winfo_width() > 1 else max(1, int(self._logical_w * self.scale_factor)))
        h = float(self.winfo_height() if self.winfo_height() > 1 else max(1, int(self._logical_h * self.scale_factor)))
        s = self.scale_factor
        rx = self._corner_radius * s
        bw = self._border_width * s

        sh_blur = self._shadow_blur * s if self._shadow else 0.0
        sh_spread = self._shadow_spread * s if self._shadow else 0.0
        sh_ox = self._shadow_offset_x * s if self._shadow else 0.0
        sh_oy = self._shadow_offset_y * s if self._shadow else 0.0

        batch = DrawBatch()
        batch.clear_var("var(--parent-bg)", fallback=parse_color(self.outer_bg))
        batch.draw_card_var(
            0.0,
            0.0,
            w,
            h,
            rx=rx,
            ry=rx,
            bg_var="var(--card-bg)",
            border_var="var(--card-border)",
            border_w=bw,
            shadow_blur=sh_blur,
            shadow_spread=sh_spread,
            shadow_ox=sh_ox,
            shadow_oy=sh_oy,
            shadow_var="var(--card-shadow)",
            rx_var="var(--card-rx)",
            ry_var="var(--card-rx)",
            bw_var="var(--card-bw)",
        )
        self.bind_batch(batch)

    def on_resize(self, width: int, height: int) -> None:
        self._sync_batch()

    def _default_inner_bg(self, pal: Palette) -> str:
        return pal.card_bg

    def set_inner_bg(self, color: ColorLike, render: bool = True, explicit: bool = True) -> None:
        super().set_inner_bg(color, render=render, explicit=explicit)
        self._update_vars()
        cascade_bg_to_children(self, self.inner_bg, palette=self._palette)

    def set_outer_bg(self, color: ColorLike, render: bool = True, explicit: bool = False) -> None:
        super().set_outer_bg(color, render=render, explicit=explicit)
        self.set_var("--parent-bg", self.outer_bg)

    def on_theme_update(self, pal: Palette) -> None:
        inner_bg = self.inner_bg
        self._update_vars()
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
