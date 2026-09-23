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
        dot: bool = False,
        width: int = 90,
        height: int = 24,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._text = text
        self._variant = variant
        self._dot = dot
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
            self._surface.fill_rounded_rect(pad, pad, w, h, r, r, style["bg"])
            self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, style["border"], 1.0 * s)

            font_sz = 11.0 * s
            if self._dot:
                dot_cx = pad + 10.0 * s
                dot_cy = self._widget_h / 2.0
                self._surface.fill_circle(dot_cx, dot_cy, 3.0 * s, style["fg"])
                text_x = dot_cx + 8.0 * s + (w - 18.0 * s) / 2.0
            else:
                text_x = self._widget_w / 2.0

            self._surface.draw_text(
                self._text,
                text_x,
                self._widget_h / 2.0 + (font_sz * 0.35),
                font_size=font_sz,
                font_family="sans-serif",
                color=style["fg"],
                align="center",
            )
            self._surface.blit(self._photo)
        except Exception as e:
            logger.debug("Render failed in Badge: %s", e, exc_info=True)


ModernBadge = Badge


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
        status: Optional[str] = "online",
        size: int = 44,
        bg_gradient_start: Optional[ColorLike] = None,
        bg_gradient_end: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._initials = initials
        self._status = status
        pal = get_theme()
        self._grad_start = bg_gradient_start or pal.primary
        self._grad_end = bg_gradient_end or pal.accent
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


ModernAvatar = Avatar
