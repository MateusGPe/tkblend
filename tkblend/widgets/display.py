"""
Display widgets: Badge (status pill) and Avatar (circular profile).
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
    Status pill badge with variant fills, borders, optional status dot, and antialiased text.
    """

    VARIANT_STYLES: Dict[str, Dict[str, str]] = {
        "primary": {"bg": "#d0bcff26", "border": "#d0bcff", "fg": "#d0bcff"},
        "success": {"bg": "#85d69726", "border": "#85d697", "fg": "#85d697"},
        "warning": {"bg": "#ffb87726", "border": "#ffb877", "fg": "#ffb877"},
        "destructive": {"bg": "#ffb4ab26", "border": "#ffb4ab", "fg": "#ffb4ab"},
        "outline": {"bg": "#00000000", "border": "#49454f", "fg": "#e6e0e9"},
    }

    @classmethod
    def _get_style(cls, variant: str) -> Dict[str, str]:
        pal = get_theme()
        if variant == "success":
            return {"bg": f"{pal.success[:7]}26", "border": pal.success, "fg": pal.success}
        elif variant == "warning":
            return {"bg": f"{pal.warning[:7]}26", "border": pal.warning, "fg": pal.warning}
        elif variant == "destructive":
            return {"bg": f"{pal.destructive[:7]}26", "border": pal.destructive, "fg": pal.destructive}
        elif variant == "outline":
            return {"bg": "#00000000", "border": pal.card_border, "fg": pal.fg}
        else:  # primary
            return {"bg": f"{pal.primary[:7]}26", "border": pal.primary, "fg": pal.primary}

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
        self._text = text
        self._variant = bootstyle or variant
        self._explicit_color = color
        self._explicit_text_color = text_color
        self._explicit_border_color = border_color
        self._dot = dot
        if width is None:
            width = max(40, int(len(str(text)) * 9 + 24))
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        self.set_text(val)

    def set_text(self, text: str) -> None:
        self._text = str(text)
        self.render()

    @property
    def variant(self) -> str:
        return self._variant

    @variant.setter
    def variant(self, val: str) -> None:
        self.set_variant(val)

    def set_variant(self, variant: str) -> None:
        self._variant = str(variant)
        self.render()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            pad = 1.5 * s
            w = max(1.0, self._widget_w - pad * 2.0)
            h = max(1.0, self._widget_h - pad * 2.0)
            r = h / 2.0

            style = self._get_style(self._variant)
            bg_col = self._explicit_color or style["bg"]
            if self._explicit_color and len(bg_col) == 7 and bg_col.startswith("#"):
                bg_col = f"{bg_col}26"
            border_col = self._explicit_border_color or self._explicit_color or style["border"]
            fg_col = self._explicit_text_color or self._explicit_color or style["fg"]

            self._surface.fill_rounded_rect(pad, pad, w, h, r, r, bg_col)
            self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, border_col, 1.0 * s)

            font_sz = 11.0 * s
            if self._dot:
                dot_cx = pad + 10.0 * s
                dot_cy = self._widget_h / 2.0
                self._surface.fill_circle(dot_cx, dot_cy, 3.0 * s, fg_col)
                text_x = dot_cx + 8.0 * s + (w - 18.0 * s) / 2.0
            else:
                text_x = self._widget_w / 2.0

            self._surface.draw_text(
                self._text,
                text_x,
                self._widget_h / 2.0 + (font_sz * 0.35),
                font_size=font_sz,
                font_family="sans-serif",
                color=fg_col,
                align="center",
            )
            self._surface.blit(self._photo)
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
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
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

            self._surface.blit(self._photo)
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
        self._text = str(text)
        self._font_family = font or "sans-serif"
        self._font_size = font_size
        self._fg = fg or color
        self._align = align
        self._auto_w = (width is None)
        self._auto_h = (height is None)
        
        calc_w = width if width is not None else self._calc_width(self._text, self._font_size)
        calc_h = height if height is not None else max(24, int(self._font_size * 1.8))
        
        super().__init__(master=master, width=calc_w, height=calc_h, bg=parent_bg, **kwargs)

    @staticmethod
    def _calc_width(text: str, font_size: int) -> int:
        lines = str(text).splitlines() or [""]
        max_len = max(len(l) for l in lines)
        return max(20, int(max_len * font_size * 0.65 + 12))

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        self.set_text(val)

    def set_text(self, val: str) -> None:
        self._text = str(val)
        if self._auto_w or self._auto_h:
            new_w = self._calc_width(self._text, self._font_size) if self._auto_w else self._logical_w
            new_h = max(24, int(self._font_size * 1.8)) if self._auto_h else self._logical_h
            if new_w != self._logical_w or new_h != self._logical_h:
                self._logical_w = new_w
                self._logical_h = new_h
                self._widget_w = max(1, int(new_w * self._scale))
                self._widget_h = max(1, int(new_h * self._scale))
                if self._photo and self._surface:
                    self._photo.configure(width=self._widget_w, height=self._widget_h)
                    self._surface.resize(self._widget_w, self._widget_h)
        self.render()

    def set_color(self, col: ColorLike) -> None:
        self._fg = col
        self.render()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            w = float(self._widget_w)
            h = float(self._widget_h)
            pal = get_theme()
            txt_col = self._fg or pal.fg
            fsz = self._font_size * s

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
                    font_family=self._font_family,
                    color=txt_col,
                    align=self._align,
                )

            self._surface.blit(self._photo)
        except Exception as e:
            logger.debug("Render failed in Label: %s", e, exc_info=True)
