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
        font_size: Optional[float] = None,
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
        eff_size = font_size if font_size is not None else 13.0
        self._font_size = eff_size * scale
        self._elevation = elevation * scale

        kwargs.setdefault("takefocus", True)
        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            font_size=font_size,
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

        safe_blur = 0.0
        safe_offset_y = 0.0
        shadow_col = "#00000000"
        if self._variant != "outline" and cur_elev > 0:
            safe_blur = min(cur_elev * 0.8, pad * 0.65)
            safe_offset_y = min(offset_y, pad * 0.25)
            shadow_col = "#00000040" if self._is_hovered else "#00000028"

        pal = get_theme()
        focus_col = pal.input_focus if self._has_focus else "#00000000"
        focus_width = 1.5 * self._scale if self._has_focus else 0.0
        f_size = self._font_config.size * self._scale

        self._surface.draw_button(
            x=pad,
            y=pad,
            w=btn_w,
            h=btn_h,
            rx=self._rx,
            ry=self._ry,
            bg_color=cur_bg,
            border_color=colors["border"],
            border_width=1.0 * self._scale,
            fg_color=colors["fg"],
            text=self._text,
            font=self._font_config.copy_with(size=f_size),
            shadow_blur=safe_blur,
            shadow_offset_y=safe_offset_y,
            shadow_color=shadow_col,
            focus_ring_color=focus_col,
            focus_ring_width=focus_width,
            is_pressed=self._is_pressed,
        )
        self._surface.blit(self._photo)


ModernButton = Button
