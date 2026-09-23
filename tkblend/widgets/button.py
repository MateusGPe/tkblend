"""
Modern Button widget with support for variants, micro-elevation, and antialiased typography.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, Dict

from tkblend.theme import get_theme, adjust_brightness
from tkblend.widgets.base import Widget, ScalingTracker


class Button(Widget):
    """
    Modern Button supporting variants ('primary', 'secondary', 'accent', 'destructive', 'outline'),
    micro-elevation on hover, pressed drop-depth animation, keyboard focus ring, and antialiased typography.
    """

    @classmethod
    def _get_variant_colors(cls, variant: str) -> Dict[str, str]:
        pal = get_theme()
        if variant == "secondary":
            return {
                "bg": pal.secondary,
                "hover": pal.secondary_hover,
                "press": pal.secondary_active,
                "fg": pal.secondary_fg,
                "border": pal.card_border,
            }
        elif variant == "accent":
            return {
                "bg": pal.accent,
                "hover": adjust_brightness(pal.accent, 1.15),
                "press": adjust_brightness(pal.accent, 0.9),
                "fg": "#ffffff" if not pal.dark_mode else "#11111b",
                "border": "#ffffff22" if pal.dark_mode else "#00000015",
            }
        elif variant == "destructive":
            return {
                "bg": pal.destructive,
                "hover": adjust_brightness(pal.destructive, 1.15),
                "press": adjust_brightness(pal.destructive, 0.9),
                "fg": "#ffffff",
                "border": "#ffffff22" if pal.dark_mode else "#00000015",
            }
        elif variant == "outline":
            return {
                "bg": "#00000000",
                "hover": pal.secondary if not pal.dark_mode else "#31324466",
                "press": pal.secondary_active if not pal.dark_mode else "#45475a88",
                "fg": pal.primary,
                "border": pal.primary,
            }
        else:  # primary
            return {
                "bg": pal.primary,
                "hover": pal.primary_hover,
                "press": pal.primary_active,
                "fg": pal.primary_fg,
                "border": "#ffffff22" if pal.dark_mode else "#00000015",
            }

    VARIANT_COLORS = property(lambda self: {v: Button._get_variant_colors(v) for v in ("primary", "secondary", "accent", "destructive", "outline")})

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
        self._variant = variant
        scale = ScalingTracker.get_scaling_factor(master)
        self._rx = rx * scale
        self._ry = ry * scale
        self._font_size = font_size * scale
        self._elevation = elevation * scale

        kwargs.setdefault("takefocus", True)
        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            **kwargs,
        )

        self.bind("<space>", self._on_key_activate)
        self.bind("<Return>", self._on_key_activate)

    def _on_key_activate(self, event) -> None:
        if not self._is_disabled:
            self._is_pressed = True
            self.render()

            def _reset_and_invoke():
                self._is_pressed = False
                self.render()
                if self._command:
                    self._command()

            self.after(100, _reset_and_invoke)

    def _handle_click(self, event) -> None:
        if not self._is_disabled and self._command:
            self._command()

    def set_text(self, text: str) -> None:
        self._text = text
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        colors = self._get_variant_colors(self._variant)

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

        pad = 3.5 * self._scale
        btn_w = self._widget_w - pad * 2.0
        btn_h = self._widget_h - pad * 2.0

        if self._variant != "outline" and cur_elev > 0:
            safe_blur = min(cur_elev * 0.8, pad * 0.65)
            safe_offset_y = min(offset_y, pad * 0.25)
            shadow_color = "#00000040" if self._is_hovered else "#00000028"
            self._surface.draw_shadow(
                pad, pad, btn_w, btn_h,
                self._rx, self._ry,
                blur_radius=safe_blur,
                offset_y=safe_offset_y,
                shadow_color=shadow_color,
            )

        self._surface.fill_rounded_rect(pad, pad, btn_w, btn_h, self._rx, self._ry, cur_bg)
        border_col = colors["border"]
        self._surface.stroke_rounded_rect(pad, pad, btn_w, btn_h, self._rx, self._ry, border_col, 1.0 * self._scale)

        if self._has_focus:
            pal = get_theme()
            focus_col = pal.input_focus
            self._surface.stroke_rounded_rect(
                pad - 1.5 * self._scale,
                pad - 1.5 * self._scale,
                btn_w + 3.0 * self._scale,
                btn_h + 3.0 * self._scale,
                self._rx + 1.5 * self._scale,
                self._ry + 1.5 * self._scale,
                focus_col,
                1.5 * self._scale,
            )

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
