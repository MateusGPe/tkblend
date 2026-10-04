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
from tkblend.widgets.constants import (
    DEFAULT_LABEL_WIDTH,
    DEFAULT_LABEL_HEIGHT,
    DEFAULT_LABEL_CORNER_RADIUS,
    DEFAULT_LABEL_BORDER_WIDTH,
    DEFAULT_LABEL_ALIGN,
    DEFAULT_LABEL_ICON_TEXT_SPACING,
    DEFAULT_LABEL_SIDE_PADDING,
    DEFAULT_FONT_SIZE,
    DEFAULT_ICON_FAMILY,
    ICON_FONT_SIZE_RATIO,
    ICON_STANDALONE_SIZE_RATIO,
    CURSOR_DEFAULT,
)
from tkblend.widgets.utils import (
    compute_text_baseline_y,
    compute_icon_baseline_y,
)


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
        icon_family: str = DEFAULT_ICON_FAMILY,
        icon_size: Optional[float] = None,
        font: Optional[Any] = None,
        font_size: Optional[float] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        fg_color: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        corner_radius: float = DEFAULT_LABEL_CORNER_RADIUS,
        border_color: Optional[ColorLike] = None,
        border_width: float = DEFAULT_LABEL_BORDER_WIDTH,
        align: str = DEFAULT_LABEL_ALIGN,
        width: Optional[int] = None,
        height: Optional[int] = None,
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
        self._auto_width = (width is None)
        self._auto_height = (height is None)

        eff_w = width if width is not None else self._calc_auto_width()
        eff_h = height if height is not None else self._calc_auto_height()

        super().__init__(
            master=master,
            width=eff_w,
            height=eff_h,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            **kwargs,
        )

    def _calc_auto_width(self) -> int:
        f_sz = self._font_size or DEFAULT_FONT_SIZE
        char_w = f_sz * 0.65
        extra = 28 if self._icon else 16
        auto_w = int(len(self._text) * char_w + extra)
        return max(DEFAULT_LABEL_WIDTH, auto_w)

    def _calc_auto_height(self) -> int:
        f_sz = self._font_size or DEFAULT_FONT_SIZE
        return max(DEFAULT_LABEL_HEIGHT, int(f_sz * 1.6))

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        self._text = str(val)
        if self._auto_width or self._auto_height:
            new_w = self._calc_auto_width() if self._auto_width else self._logical_w
            new_h = self._calc_auto_height() if self._auto_height else self._logical_h
            self.set_geometry_request(new_w, new_h)
        else:
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
            font_size=self._font_size or DEFAULT_FONT_SIZE,
            bold=self._bold,
            italic=self._italic,
        )
        scaled_font_sz = float(font_cfg.size) * s
        center_y = h / 2.0

        has_text = bool(self._text)
        has_icon = bool(self._icon)

        if has_icon and has_text:
            icon_sz = (self._icon_size or (font_cfg.size * ICON_FONT_SIZE_RATIO)) * s
            spacing = DEFAULT_LABEL_ICON_TEXT_SPACING * s
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
                start_x = w - total_content_w - DEFAULT_LABEL_SIDE_PADDING * s
            else:
                start_x = DEFAULT_LABEL_SIDE_PADDING * s

            icon_y = compute_icon_baseline_y(center_y, icon_sz)
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
            text_y = compute_text_baseline_y(center_y, scaled_font_sz)
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
            icon_sz = (self._icon_size or (min(w, h) * ICON_STANDALONE_SIZE_RATIO)) * s
            icon_y = compute_icon_baseline_y(center_y, icon_sz)
            surf.draw_icon(
                self._icon,
                w / 2.0 if self._align == "center" else (DEFAULT_LABEL_SIDE_PADDING * s if self._align == "left" else w - DEFAULT_LABEL_SIDE_PADDING * s),
                icon_y,
                size=icon_sz,
                color=fg_col,
                family=self._icon_family,
                align=self._align,
            )
        elif has_text:
            text_x = DEFAULT_LABEL_SIDE_PADDING * s if self._align == "left" else (w / 2.0 if self._align == "center" else w - DEFAULT_LABEL_SIDE_PADDING * s)
            text_y = compute_text_baseline_y(center_y, scaled_font_sz)
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
        return super().configure(cnf, **kwargs)
