"""
Display widgets: Badge (status pill), Avatar (circular profile), and vector Label.
"""

from __future__ import annotations
import logging
import tkinter as tk
from typing import Optional, Dict

from tkblend.surface import LinearGradient, ColorLike
from tkblend.theme import get_theme
from tkblend.widgets.base import Widget

logger = logging.getLogger(__name__)


class Badge(Widget):
    """
    Status pill badge with CSS-driven variant fills, borders, optional status dot, and antialiased text.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Badge",
        variant: str = "primary",
        bootstyle: Optional[str] = None,
        color: Optional[str] = None,
        text_color: Optional[str] = None,
        border_color: Optional[str] = None,
        dot: bool = False,
        width: Optional[int] = None,
        height: int = 24,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._dot = dot
        self._explicit_bg = color
        self._explicit_fg = text_color
        self._explicit_border_color = border_color
        eff_variant = bootstyle or variant
        if width is None:
            width = max(40, int(len(str(text)) * 9 + 24))
        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            tag_name="badge",
            class_name=f".badge-{eff_variant}" if eff_variant else "",
            **kwargs,
        )
        self._text = text
        self._variant = eff_variant

    def render(self) -> None:
        s = self.begin_render()
        if s <= 0.0:
            return
        try:
            pad = 1.5 * s
            w = max(1.0, self._widget_w - pad * 2.0)
            h = max(1.0, self._widget_h - pad * 2.0)

            cls_sel = f".badge-{self._variant}" if self._variant and not self._variant.startswith(".") else self._variant
            style = self.get_computed_style("badge", cls_sel)
            style.border_radius = float(h / 2.0)
            style.font_size = float(11.0 * s)

            if self._dot:
                self._handle.render_box(float(pad), float(pad), float(w), float(h), style, "", 1)
                dot_cx = pad + 10.0 * s
                dot_cy = self._widget_h / 2.0
                self._handle.fill_circle(dot_cx, dot_cy, 3.0 * s, style.fg_color)
                text_x = dot_cx + 8.0 * s + (w - 18.0 * s) / 2.0
                font_sz = float(style.font_size)
                self._handle.draw_text(
                    str(self._text),
                    text_x,
                    self._widget_h / 2.0 + (font_sz * 0.35),
                    font_size=font_sz,
                    font_family=style.font_family,
                    color=style.fg_color,
                    align="center",
                )
            else:
                self._handle.render_box(
                    float(pad), float(pad), float(w), float(h),
                    style,
                    str(self._text),
                    1,
                )
            self.end_render()
        except Exception as e:
            logger.debug("Render failed in Badge: %s", e, exc_info=True)


class Avatar(Widget):
    """
    Circular vector avatar displaying initials with optional status indicator dot.
    """

    STATUS_COLORS: Dict[str, str] = {
        "online": "#85d697",
        "busy": "#ffb877",
        "offline": "#79747e",
    }

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        initials: str = "TK",
        text: Optional[str] = None,
        status: Optional[str] = "online",
        size: int = 44,
        bg_color: Optional[ColorLike] = None,
        color: Optional[ColorLike] = None,
        bg_gradient_start: Optional[ColorLike] = None,
        bg_gradient_end: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._initials = text or initials
        self._status = status
        pal = get_theme()
        solid_bg = bg_color or color
        self._grad_start = bg_gradient_start or solid_bg or pal.primary
        self._grad_end = bg_gradient_end or solid_bg or pal.accent
        super().__init__(master=master, width=size, height=size, bg=parent_bg, **kwargs)

    def render(self) -> None:
        s = self.begin_render()
        if s <= 0.0:
            return
        try:
            cx = self._widget_w / 2.0
            cy = self._widget_h / 2.0
            r = min(cx, cy) - 3.0 * s
            if r <= 0:
                return

            grad = LinearGradient(cx - r, cy - r, cx + r, cy + r)
            grad.add_stop(0.0, self._grad_start)
            grad.add_stop(1.0, self._grad_end)

            self._surface.fill_circle(cx, cy, r, grad)
            self._surface.stroke_circle(cx, cy, r, "#ffffff44", stroke_width=1.2 * s)

            pal = get_theme()
            txt_col = pal.primary_fg if pal.dark_mode else "#ffffff"

            font_sz = 14.0 * s
            self._surface.draw_text(
                self._initials,
                cx,
                cy + (font_sz * 0.35),
                font_size=font_sz,
                font_family="sans-serif",
                color=txt_col,
                align="center",
            )

            if self._status in self.STATUS_COLORS:
                dot_color = pal.success if self._status == "online" else (pal.warning if self._status == "busy" else pal.text_muted)
                dot_r = 4.5 * s
                dot_cx = cx + r * 0.65
                dot_cy = cy + r * 0.65
                self._surface.fill_circle(dot_cx, dot_cy, dot_r + 1.5 * s, self._parent_bg)
                self._surface.fill_circle(dot_cx, dot_cy, dot_r, dot_color)

            self.end_render()
        except Exception as e:
            logger.debug("Render failed in Avatar: %s", e, exc_info=True)


class Label(Widget):
    """
    Pure Blend2D antialiased vector Label widget.
    Supports auto-sizing, text alignment, font styling, dynamic theming, and High-DPI scaling.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        font: Optional[str] = None,
        font_size: int = 13,
        fg: Optional[ColorLike] = None,
        color: Optional[ColorLike] = None,
        align: str = "left",
        width: Optional[int] = None,
        height: Optional[int] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._align = align
        self._auto_w = (width is None)
        self._auto_h = (height is None)
        calc_w = width if width is not None else self._calc_width(str(text), font_size)
        calc_h = height if height is not None else max(24, int(font_size * 1.8))
        
        super().__init__(
            master=master,
            width=calc_w,
            height=calc_h,
            bg=parent_bg,
            font=font,
            font_size=font_size,
            **kwargs,
        )
        self._text = str(text)
        self._explicit_fg = fg or color

    @staticmethod
    def _calc_width(text: str, font_size: int) -> int:
        lines = str(text).splitlines() or [""]
        max_len = max(len(l) for l in lines)
        return max(20, int(max_len * font_size * 0.65 + 12))

    def set_text(self, val: str) -> None:
        self._text = str(val)
        if self._auto_w or self._auto_h:
            fsz = int(self._font_config.size)
            new_w = self._calc_width(self._text, fsz) if self._auto_w else self._logical_w
            new_h = max(24, int(fsz * 1.8)) if self._auto_h else self._logical_h
            if new_w != self._logical_w or new_h != self._logical_h:
                self._logical_w = new_w
                self._logical_h = new_h
                self._widget_w = max(1, int(new_w * self._scale))
                self.configure(width=self._widget_w, height=self._widget_h)
        self.render()

    def set_color(self, col: ColorLike) -> None:
        self.fg_color = col

    def render(self) -> None:
        s = self.begin_render()
        if s <= 0.0:
            return
        try:
            w = float(self._widget_w)
            h = float(self._widget_h)
            pal = get_theme()
            txt_col = self._explicit_fg or pal.fg
            fsz = self._font_config.size * s

            lines = self._text.splitlines() or [""]
            line_height = fsz * 1.3
            total_text_h = len(lines) * line_height
            start_y = max(fsz * 0.9, (h - total_text_h) / 2.0 + fsz * 0.85)

            if self._align == "center":
                x = w / 2.0
            elif self._align == "right":
                x = w - 6.0 * s
            else:
                x = 6.0 * s

            for i, line in enumerate(lines):
                y = start_y + (i * line_height)
                self._surface.draw_text(
                    line,
                    x,
                    y,
                    font_size=fsz,
                    font_family=self._font_config.family,
                    color=txt_col,
                    align=self._align,
                )

            self.end_render()
        except Exception as e:
            logger.debug("Render failed in Label: %s", e, exc_info=True)
