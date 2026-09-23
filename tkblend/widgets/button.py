"""
Modern Button widget with support for variants, micro-elevation, and antialiased typography.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, Dict

from tkblend.widgets.base import Widget, ScalingTracker


class Button(Widget):
    """
    Modern Button supporting variants ('primary', 'secondary', 'accent', 'destructive', 'outline'),
    micro-elevation on hover, pressed drop-depth animation, and antialiased typography.
    """

    VARIANT_COLORS: Dict[str, Dict[str, str]] = {
        "primary": {"bg": "#89b4fa", "hover": "#b4befe", "press": "#74c7ec", "fg": "#11111b", "border": "#ffffff22"},
        "secondary": {"bg": "#313244", "hover": "#45475a", "press": "#585b70", "fg": "#cdd6f4", "border": "#585b70"},
        "accent": {"bg": "#cba6f7", "hover": "#f5c2e7", "press": "#b4befe", "fg": "#11111b", "border": "#ffffff22"},
        "destructive": {"bg": "#f38ba8", "hover": "#eba0ac", "press": "#e78284", "fg": "#11111b", "border": "#ffffff22"},
        "outline": {"bg": "#18182500", "hover": "#31324466", "press": "#45475a88", "fg": "#89b4fa", "border": "#89b4fa"},
    }

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Button",
        command: Optional[Callable[[], None]] = None,
        variant: str = "primary",
        width: int = 120,
        height: int = 38,
        rx: float = 10.0,
        ry: float = 10.0,
        font_size: float = 13.0,
        elevation: float = 5.0,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._text = text
        self._command = command
        self._variant = variant if variant in self.VARIANT_COLORS else "primary"
        scale = ScalingTracker.get_scaling_factor(master)
        self._rx = rx * scale
        self._ry = ry * scale
        self._font_size = font_size * scale
        self._elevation = elevation * scale

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            **kwargs,
        )

        self.bind("<ButtonRelease-1>", self._handle_click)

    def _handle_click(self, event) -> None:
        if not self._is_disabled and self._command:
            if 0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h:
                self._command()

    def set_text(self, text: str) -> None:
        self._text = text
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        colors = self.VARIANT_COLORS.get(self._variant, self.VARIANT_COLORS["primary"])

        cur_bg = colors["bg"]
        cur_elev = self._elevation
        offset_y = 2.0 * self._scale

        if self._is_pressed:
            cur_bg = colors["press"]
            cur_elev = max(1.0, self._elevation * 0.3)
            offset_y = 1.0 * self._scale
        elif self._is_hovered:
            cur_bg = colors["hover"]
            cur_elev = self._elevation * 1.3
            offset_y = 3.0 * self._scale

        pad = 3.0 * self._scale
        btn_w = self._widget_w - pad * 2.0
        btn_h = self._widget_h - pad * 2.0

        if self._variant != "outline" and cur_elev > 0:
            self._surface.draw_shadow(
                pad, pad, btn_w, btn_h,
                self._rx, self._ry,
                blur_radius=cur_elev * 1.5,
                offset_y=offset_y,
                shadow_color="#00000055",
            )

        self._surface.fill_rounded_rect(pad, pad, btn_w, btn_h, self._rx, self._ry, cur_bg)
        border_col = colors["border"]
        self._surface.stroke_rounded_rect(pad, pad, btn_w, btn_h, self._rx, self._ry, border_col, 1.0 * self._scale)

        text_x = self._widget_w / 2.0
        text_y = self._widget_h / 2.0 + (self._font_size * 0.35)
        if self._is_pressed:
            text_y += 1.0

        self._surface.draw_text(
            self._text,
            x=text_x,
            y=text_y,
            font_size=self._font_size,
            font_family="sans-serif",
            color=colors["fg"],
            align="center",
        )
        self._surface.blit(self._photo)


ModernButton = Button
