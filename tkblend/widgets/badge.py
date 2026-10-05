"""
Pure Blend2D Vector Badge and Avatar controls powered by BaseControl.
"""

from __future__ import annotations

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
from tkblend.icons import Icons
from tkblend.widgets.constants import (
    DEFAULT_FONT_SIZE,
    DEFAULT_ICON_FAMILY,
    ICON_FONT_SIZE_RATIO,
    CURSOR_DEFAULT,
)
from tkblend.widgets.utils import compute_text_baseline_y, compute_icon_baseline_y


class Badge(BaseControl):
    """
    Modern pill / tag / status badge with crisp vector geometry, optional icons,
    variant styles, and subtle borders.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Badge",
        variant: str = "primary",
        color: Optional[ColorLike] = None,
        icon: Optional[str] = None,
        icon_family: str = DEFAULT_ICON_FAMILY,
        dot: bool = False,
        dot_color: Optional[ColorLike] = None,
        inner_bg: Optional[ColorLike] = None,
        outer_bg: Optional[ColorLike] = None,
        fg_color: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        corner_radius: Optional[float] = None,
        font_size: float = 10.0,
        bold: bool = True,
        width: Optional[int] = None,
        height: int = 22,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._text = str(text)
        if isinstance(color, str) and color in ("primary", "secondary", "success", "warning", "danger", "info"):
            self._variant = color.lower()
        else:
            self._variant = variant.lower()
        self._icon = icon
        self._icon_family = icon_family
        self._dot = dot
        self._custom_dot_color = dot_color
        self._custom_fg = fg_color
        self._custom_border = border_color
        self._border_width = float(border_width)
        self._corner_radius = corner_radius
        self._font_size = float(font_size)
        self._bold = bold

        # Default auto-width estimation
        w = width if width is not None else max(40, int(len(self._text) * 8 + (30 if icon or dot else 20)))

        explicit_bg = inner_bg or bg_color or (color if color not in ("primary", "secondary", "success", "warning", "danger", "info") else None)

        super().__init__(
            master=master,
            width=w,
            height=height,
            inner_bg=explicit_bg,
            outer_bg=outer_bg or parent_bg,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            **kwargs,
        )

    def _default_inner_bg(self, pal: Palette) -> str:
        return pal.primary

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        self._text = str(val)
        self.request_redraw()

    @property
    def variant(self) -> str:
        return self._variant

    @variant.setter
    def variant(self, val: str) -> None:
        self._variant = val.lower()
        self.request_redraw()

    def _resolve_variant_colors(self, pal: Palette) -> tuple[str, str, str]:
        if self._explicit_inner_bg is not None and self._custom_fg:
            bg = self.inner_bg
            fg = resolve_color_failsafe(self._custom_fg, palette=pal)
            bc = resolve_color_failsafe(self._custom_border or bg, palette=pal)
            return bg, fg, bc

        v = self._variant
        if v in ("success", "online", "active"):
            base = pal.success
            bg = blend_color_hex(base, pal.bg, 0.2)
            fg = base
            bc = blend_color_hex(base, pal.bg, 0.4)
        elif v in ("danger", "destructive", "error", "offline"):
            base = pal.destructive
            bg = blend_color_hex(base, pal.bg, 0.2)
            fg = base
            bc = blend_color_hex(base, pal.bg, 0.4)
        elif v in ("warning", "alert", "busy"):
            base = pal.warning
            bg = blend_color_hex(base, pal.bg, 0.2)
            fg = base
            bc = blend_color_hex(base, pal.bg, 0.4)
        elif v in ("info", "secondary"):
            base = pal.secondary
            bg = blend_color_hex(base, pal.bg, 0.2)
            fg = base
            bc = blend_color_hex(base, pal.bg, 0.4)
        elif v == "outline":
            bg = "transparent"
            fg = pal.fg
            bc = pal.border
        else:  # primary / default
            base = pal.primary
            bg = blend_color_hex(base, pal.bg, 0.2)
            fg = base
            bc = blend_color_hex(base, pal.bg, 0.4)

        if self._explicit_inner_bg is not None:
            bg = self.inner_bg
        if self._custom_fg:
            fg = resolve_color_failsafe(self._custom_fg, palette=pal)
        if self._custom_border:
            bc = resolve_color_failsafe(self._custom_border, palette=pal)

        return bg, fg, bc

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        bg_col, fg_col, border_col = self._resolve_variant_colors(pal)
        cr = (self._corner_radius if self._corner_radius is not None else (h / 2.0 / s)) * s

        surf.clear(self.outer_bg)
        if bg_col != "transparent":
            surf.fill_rounded_rect(0.0, 0.0, w, h, cr, cr, bg_col)

        if self._border_width > 0.0 and border_col != "transparent":
            surf.stroke_rounded_rect(0.0, 0.0, w, h, cr, cr, border_col, stroke_width=self._border_width * s)

        scaled_font_sz = self._font_size * s
        font_cfg = parse_font(font_size=self._font_size, bold=self._bold)
        center_y = h / 2.0

        # Calculate content layout
        items_w = 0.0
        spacing = 4.0 * s
        dot_radius = 3.0 * s
        icon_sz = scaled_font_sz * ICON_FONT_SIZE_RATIO

        has_dot = self._dot
        has_icon = bool(self._icon)
        has_text = bool(self._text)

        text_metrics = None
        if has_text:
            text_metrics = surf.measure_text(
                self._text,
                font_size=scaled_font_sz,
                font_family=font_cfg.family,
                bold=font_cfg.bold,
            )
            items_w += text_metrics.width

        if has_dot:
            items_w += (dot_radius * 2.0) + (spacing if has_text or has_icon else 0.0)
        if has_icon:
            items_w += icon_sz + (spacing if has_text else 0.0)

        cur_x = (w - items_w) / 2.0

        if has_dot:
            d_col = resolve_color_failsafe(self._custom_dot_color or fg_col, palette=pal)
            surf.fill_circle(cur_x + dot_radius, center_y, dot_radius, d_col)
            cur_x += dot_radius * 2.0 + spacing

        if has_icon:
            icon_y = compute_icon_baseline_y(center_y, icon_sz)
            surf.draw_icon(
                self._icon,
                cur_x,
                icon_y,
                size=icon_sz,
                color=fg_col,
                family=self._icon_family,
                align="left",
            )
            cur_x += icon_sz + spacing

        if has_text:
            text_y = compute_text_baseline_y(center_y, scaled_font_sz)
            surf.draw_text(
                self._text,
                cur_x,
                text_y,
                font_size=scaled_font_sz,
                font_family=font_cfg.family,
                color=fg_col,
                bold=font_cfg.bold,
                align="left",
            )


class Avatar(BaseControl):
    """
    Vector user avatar supporting initials, icons, or status indicator rings.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        icon: Optional[str] = "user",
        icon_family: str = DEFAULT_ICON_FAMILY,
        size: int = 36,
        status: Optional[str] = None,
        inner_bg: Optional[ColorLike] = None,
        outer_bg: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        fg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.5,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._text = str(text)
        self._icon = icon if not text else None
        self._icon_family = icon_family
        self._status = status
        self._custom_fg = fg_color
        self._custom_border = border_color
        self._border_width = float(border_width)

        super().__init__(
            master=master,
            width=size,
            height=size,
            inner_bg=inner_bg or bg_color,
            outer_bg=outer_bg or parent_bg,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            **kwargs,
        )

    def _default_inner_bg(self, pal: Palette) -> str:
        return pal.primary

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        r = min(w, h) / 2.0 - self._border_width * s
        cx = w / 2.0
        cy = h / 2.0

        bg_col = self.inner_bg
        fg_col = resolve_color_failsafe(self._custom_fg or pal.primary_fg, palette=pal)
        b_col = resolve_color_failsafe(self._custom_border or pal.card_border, palette=pal)

        # Background circle
        surf.clear(self.outer_bg)
        surf.fill_circle(cx, cy, r, bg_col)
        if self._border_width > 0.0:
            surf.stroke_circle(cx, cy, r, b_col, stroke_width=self._border_width * s)

        # Text or Icon
        if self._text:
            font_sz = r * 0.9
            font_cfg = parse_font(font_size=font_sz / s, bold=True)
            text_y = compute_text_baseline_y(cy, font_sz)
            surf.draw_text(
                self._text[:2].upper(),
                cx,
                text_y,
                font_size=font_sz,
                font_family=font_cfg.family,
                color=fg_col,
                bold=True,
                align="center",
            )
        elif self._icon:
            icon_sz = r * 1.1
            icon_y = compute_icon_baseline_y(cy, icon_sz)
            surf.draw_icon(
                self._icon,
                cx,
                icon_y,
                size=icon_sz,
                color=fg_col,
                family=self._icon_family,
                align="center",
            )

        # Status badge dot
        if self._status:
            stat = self._status.lower()
            dot_r = r * 0.32
            dot_x = cx + r * 0.707
            dot_y = cy + r * 0.707
            if stat in ("online", "active"):
                st_col = pal.success
            elif stat in ("busy", "dnd", "away"):
                st_col = pal.warning
            else:
                st_col = pal.text_muted

            surf.fill_circle(dot_x, dot_y, dot_r, st_col)
            surf.stroke_circle(dot_x, dot_y, dot_r, pal.bg, stroke_width=1.5 * s)
