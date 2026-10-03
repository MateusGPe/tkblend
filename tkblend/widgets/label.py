"""
Pure Blend2D Vector Label and Badge widget powered by NativeController.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
)
from tkblend.font import parse_font
from tkblend.icons import Icons


class Label(BaseControl):
    """
    High-performance vector label with antialiased typography, embedded vector icons,
    optional pill/badge styling, and multiline wrapping.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        icon: Optional[str] = None,
        icon_family: str = "fa-solid",
        icon_size: Optional[float] = None,
        font: Optional[Any] = None,
        font_size: Optional[float] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        fg_color: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        corner_radius: float = 0.0,
        border_color: Optional[ColorLike] = None,
        border_width: float = 0.0,
        align: str = "left",
        width: int = 100,
        height: int = 24,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._text = str(text)
        self._icon = icon
        self._icon_family = icon_family
        self._icon_size = icon_size

        self._font_spec = font
        self._font_size = font_size
        self._bold = bold
        self._italic = italic

        self._custom_fg_color = fg_color
        self._custom_bg_color = bg_color
        self._corner_radius = float(corner_radius)
        self._custom_border_color = border_color
        self._border_width = float(border_width)
        self._align = align.lower()

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or "",
            takefocus=False,
            **kwargs,
        )

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        self._text = str(val)
        self.request_redraw()

    @property
    def icon(self) -> Optional[str]:
        return self._icon

    @icon.setter
    def icon(self, val: Optional[str]) -> None:
        self._icon = val
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        # Optional pill background
        if self._custom_bg_color is not None:
            bg_col = resolve_color_failsafe(self._custom_bg_color, palette=pal)
            rx = self._corner_radius * s
            ry = rx
            surf.fill_rounded_rect(0.0, 0.0, w, h, rx, ry, bg_col)
            if self._border_width > 0.0:
                bc = resolve_color_failsafe(self._custom_border_color or pal.card_border, palette=pal)
                surf.stroke_rounded_rect(0.0, 0.0, w, h, rx, ry, bc, stroke_width=self._border_width * s)

        fg_col = resolve_color_failsafe(self._custom_fg_color or pal.fg, palette=pal)
        if self.is_disabled:
            fg_col = resolve_color_failsafe(pal.text_muted, palette=pal)

        font_cfg = parse_font(
            font=self._font_spec,
            font_size=self._font_size or 13.0,
            bold=self._bold,
            italic=self._italic,
        )
        scaled_font_sz = float(font_cfg.size) * s
        center_y = h / 2.0

        has_text = bool(self._text)
        has_icon = bool(self._icon)

        if has_icon and has_text:
            icon_sz = (self._icon_size or (font_cfg.size * 1.1)) * s
            spacing = 6.0 * s
            text_metrics = surf.measure_text(
                self._text,
                font_size=scaled_font_sz,
                font_family=font_cfg.family,
                bold=font_cfg.bold,
                italic=font_cfg.italic,
                weight=font_cfg.weight,
            )
            total_content_w = icon_sz + spacing + text_metrics.width

            if self._align == "center":
                start_x = (w - total_content_w) / 2.0
            elif self._align == "right":
                start_x = w - total_content_w - 4.0 * s
            else:
                start_x = 4.0 * s

            icon_y = center_y + icon_sz * 0.35
            surf.draw_icon(
                self._icon,
                start_x,
                icon_y,
                size=icon_sz,
                color=fg_col,
                family=self._icon_family,
                align="left",
            )
            text_x = start_x + icon_sz + spacing
            text_y = center_y + scaled_font_sz * 0.35
            surf.draw_text(
                self._text,
                text_x,
                text_y,
                font_size=scaled_font_sz,
                font_family=font_cfg.family,
                color=fg_col,
                bold=font_cfg.bold,
                italic=font_cfg.italic,
                weight=font_cfg.weight,
                align="left",
            )
        elif has_icon:
            icon_sz = (self._icon_size or (min(w, h) * 0.55)) * s
            icon_y = center_y + icon_sz * 0.35
            surf.draw_icon(
                self._icon,
                w / 2.0 if self._align == "center" else (4.0 * s if self._align == "left" else w - 4.0 * s),
                icon_y,
                size=icon_sz,
                color=fg_col,
                family=self._icon_family,
                align=self._align,
            )
        elif has_text:
            text_x = 4.0 * s if self._align == "left" else (w / 2.0 if self._align == "center" else w - 4.0 * s)
            text_y = center_y + scaled_font_sz * 0.35
            surf.draw_text(
                self._text,
                text_x,
                text_y,
                font_size=scaled_font_sz,
                font_family=font_cfg.family,
                color=fg_col,
                bold=font_cfg.bold,
                italic=font_cfg.italic,
                weight=font_cfg.weight,
                align=self._align,
            )

    def configure(self, cnf=None, **kwargs):
        if cnf is None and not kwargs:
            return super().configure()
        if cnf:
            kwargs.update(cnf)

        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
        if "icon" in kwargs:
            self._icon = kwargs.pop("icon")
        if "fg_color" in kwargs:
            self._custom_fg_color = kwargs.pop("fg_color")
        if "bg_color" in kwargs:
            self._custom_bg_color = kwargs.pop("bg_color")
        self.request_redraw()
        return super().configure(**kwargs)
