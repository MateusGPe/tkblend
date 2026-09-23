"""
Display widgets: Badge (status pill) and Avatar (circular profile).
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Dict

from tkblend.surface import LinearGradient, ColorLike
from tkblend.theme import get_theme
from tkblend.widgets.base import Widget


class Badge(Widget):
    """
    Status pill badge with variant fills, borders, optional status dot, and antialiased text.
    """

    VARIANT_STYLES: Dict[str, Dict[str, str]] = {
        "primary": {"bg": "#89b4fa25", "border": "#89b4fa", "fg": "#89b4fa"},
        "success": {"bg": "#a6e3a125", "border": "#a6e3a1", "fg": "#a6e3a1"},
        "warning": {"bg": "#f9e2af25", "border": "#f9e2af", "fg": "#f9e2af"},
        "destructive": {"bg": "#f38ba825", "border": "#f38ba8", "fg": "#f38ba8"},
        "outline": {"bg": "#18182500", "border": "#585b70", "fg": "#cdd6f4"},
    }

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
        self._variant = variant if variant in self.VARIANT_STYLES else "primary"
        self._dot = dot
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

    def set_text(self, text: str) -> None:
        self._text = text
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        pad = 1.5 * s
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        r = h / 2.0

        style = self.VARIANT_STYLES.get(self._variant, self.VARIANT_STYLES["primary"])
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


ModernBadge = Badge


class Avatar(Widget):
    """
    Circular vector avatar displaying initials with optional status indicator dot.
    """

    STATUS_COLORS: Dict[str, str] = {
        "online": "#a6e3a1",
        "busy": "#f9e2af",
        "offline": "#6c7086",
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
        self._surface.clear(self._parent_bg)
        s = self._scale
        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        r = min(cx, cy) - 3.0 * s

        grad = LinearGradient(cx - r, cy - r, cx + r, cy + r)
        grad.add_stop(0.0, self._grad_start)
        grad.add_stop(1.0, self._grad_end)

        self._surface.fill_circle(cx, cy, r, grad)
        self._surface.stroke_circle(cx, cy, r, "#ffffff44", stroke_width=1.2 * s)

        font_sz = 14.0 * s
        self._surface.draw_text(
            self._initials,
            cx,
            cy + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color="#11111b",
            align="center",
        )

        if self._status in self.STATUS_COLORS:
            dot_color = self.STATUS_COLORS[self._status]
            dot_r = 4.5 * s
            dot_cx = cx + r * 0.65
            dot_cy = cy + r * 0.65
            self._surface.fill_circle(dot_cx, dot_cy, dot_r + 1.5 * s, self._parent_bg)
            self._surface.fill_circle(dot_cx, dot_cy, dot_r, dot_color)

        self._surface.blit(self._photo)


ModernAvatar = Avatar
