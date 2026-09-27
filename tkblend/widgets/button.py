"""
Modern Button widget with declarative CSS-like style resolution and zero-copy Blend2D rendering.
"""

from __future__ import annotations
import logging
import tkinter as tk
from typing import Optional, Callable

from tkblend.surface import ColorLike
from tkblend.theme import get_theme
from tkblend.widgets.base import Widget, ScalingTracker

logger = logging.getLogger(__name__)


class Button(Widget):
    """
    Modern Button widget supporting CSS-driven styling, variants ('primary', 'secondary',
    'accent', 'destructive', 'outline'), hover/active micro-elevation, and antialiased typography.
    """

    @classmethod
    def _get_variant_colors(cls, variant: str) -> dict[str, str]:
        pal = get_theme()
        v = (variant or "primary").lower()
        if v == "secondary":
            return {
                "bg": pal.secondary,
                "hover": pal.secondary_hover,
                "press": pal.secondary_active,
                "fg": pal.secondary_fg,
                "border": pal.card_border,
            }
        elif v in ("accent", "info"):
            return {
                "bg": pal.accent,
                "hover": pal.primary_hover,
                "press": pal.primary_active,
                "fg": pal.fg if not pal.dark_mode else "#100e14",
                "border": "#00000000",
            }
        elif v in ("destructive", "danger"):
            return {
                "bg": pal.destructive,
                "hover": pal.destructive,
                "press": pal.destructive,
                "fg": "#ffffff" if not pal.dark_mode else "#410002",
                "border": "#00000000",
            }
        elif v == "success":
            return {
                "bg": pal.success,
                "hover": pal.success,
                "press": pal.success,
                "fg": "#ffffff" if not pal.dark_mode else "#003912",
                "border": "#00000000",
            }
        elif v == "warning":
            return {
                "bg": pal.warning,
                "hover": pal.warning,
                "press": pal.warning,
                "fg": "#ffffff" if not pal.dark_mode else "#100e14",
                "border": "#00000000",
            }
        elif v.startswith("outline"):
            return {
                "bg": "#00000000",
                "hover": pal.primary_hover,
                "press": pal.primary_active,
                "fg": pal.primary,
                "border": pal.primary,
            }
        else:
            return {
                "bg": pal.primary,
                "hover": pal.primary_hover,
                "press": pal.primary_active,
                "fg": pal.primary_fg,
                "border": "#00000000",
            }

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Button",
        command: Optional[Callable[[], None]] = None,
        variant: str = "primary",
        bootstyle: Optional[str] = None,
        width: int = 120,
        height: int = 38,
        rx: Optional[float] = None,
        ry: Optional[float] = None,
        font_size: Optional[float] = None,
        elevation: float = 0.0,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        scale = ScalingTracker.get_scaling_factor(master)
        self._custom_rx = (rx * scale) if rx is not None else None
        self._custom_ry = (ry * scale) if ry is not None else None
        self._elevation = elevation * scale
        eff_variant = bootstyle or variant

        kwargs.setdefault("takefocus", True)
        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            font_size=font_size,
            tag_name="button",
            class_name=f".btn-{eff_variant}" if eff_variant else "",
            **kwargs,
        )
        self._text = text
        self._command = command
        self._variant = eff_variant

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

    def render(self) -> None:
        try:
            s = self.begin_render()
            if s <= 0:
                return
            cls_sel = f".btn-{self._variant}" if self._variant and not self._variant.startswith(".") else self._variant
            style = self.get_computed_style("button", cls_sel)

            pad = 2.0 * s
            btn_w = max(1.0, self._widget_w - pad * 2.0)
            btn_h = max(1.0, self._widget_h - pad * 2.0)

            self._handle.render_box(
                float(pad), float(pad),
                float(btn_w), float(btn_h),
                style,
                str(self._text),
                1,  # center
            )
            self.end_render()
        except Exception as e:
            logger.debug("Render failed in Button: %s", e, exc_info=True)
