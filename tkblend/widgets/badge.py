from __future__ import annotations

import math
import tkinter as tk
from typing import Optional
from tkblend.widgets.base import BaseControl


class Badge(BaseControl):
    """High-performance pure Blend2D vector pill-shaped badge."""

    WIDGET_CLASS = "badge"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        variant: str = "default",
        width: Optional[int] = None,
        height: int = 24,
        padding_x: Optional[int] = None,
        min_width: Optional[int] = None,
        **kwargs,
    ):
        self._explicit_width = int(width) if width is not None and width > 0 else None
        self._padding_x = 8 if padding_x is None else max(0, int(padding_x))
        self._min_width = min_width
        self._base_height = height

        # If an explicit width was given, use it; otherwise start with a sensible base for BaseControl init
        initial_w = self._explicit_width if self._explicit_width is not None else max(24, height)

        super().__init__(
            master=master,
            widget_class="badge",
            width=initial_w,
            height=height,
            **kwargs,
        )
        if text:
            self.set_var("--text", str(text))
        self._variant = str(variant or "default").lower()
        if self._variant and self._variant != "default":
            self.set_var("--variant", self._variant)
            self.add_class(f"badge-{self._variant}")
            self.add_class(self._variant)

        # If auto-sizing is active, calculate fit and apply initial geometry
        if self._explicit_width is None:
            self._recalculate_size()

    def _calculate_auto_width(self, text: str, height: Optional[int] = None) -> int:
        h = height if height is not None else getattr(self, "_logical_h", self._base_height)
        min_w = self._min_width if self._min_width is not None else h
        if not text:
            return max(1, min_w)

        # Measure text using Blend2D typography
        try:
            font_size = float(self.get_var("--badge-font-size", "11.0") or 11.0)
            font_family = self.get_var("--badge-font-family", "sans-serif") or "sans-serif"
            font_weight = int(float(self.get_var("--badge-font-weight", "600") or 600))
            metrics = self.surface.measure_text(
                str(text),
                font_size=font_size,
                font_family=font_family,
                weight=font_weight,
            )
            text_width = metrics.advance_x
        except Exception:
            # Fallback estimation if surface/font engine is not yet available
            text_width = len(str(text)) * 7.0

        calc_w = int(math.ceil(text_width + 2 * self._padding_x))
        return max(min_w, calc_w)

    def _recalculate_size(self) -> None:
        if self._explicit_width is None:
            new_w = self._calculate_auto_width(self.text)
            if new_w != self._logical_w:
                self.set_geometry_request(new_w, self._logical_h)

    @property
    def padding_x(self) -> int:
        return self._padding_x

    @padding_x.setter
    def padding_x(self, val: int) -> None:
        self._padding_x = max(0, int(val))
        self._recalculate_size()
        self.request_redraw()

    @property
    def min_width(self) -> Optional[int]:
        return self._min_width

    @min_width.setter
    def min_width(self, val: Optional[int]) -> None:
        self._min_width = val
        self._recalculate_size()
        self.request_redraw()

    @property
    def width(self) -> int:
        return self._logical_w

    @width.setter
    def width(self, val: Optional[int]) -> None:
        if val is None or val <= 0:
            self._explicit_width = None
            self._recalculate_size()
        else:
            self._explicit_width = int(val)
            self.set_geometry_request(self._explicit_width, self._logical_h)

    @property
    def text(self) -> str:
        return self.get_var("--text")

    @text.setter
    def text(self, val: str) -> None:
        str_val = str(val or "")
        self.set_var("--text", str_val)
        self._recalculate_size()
        self.request_redraw()

    def set_text(self, val: str) -> Badge:
        self.text = val
        return self

    @property
    def variant(self) -> str:
        return self._variant

    @variant.setter
    def variant(self, val: str) -> None:
        val = str(val or "default").lower()
        if val != self._variant:
            if self._variant and self._variant != "default":
                self.remove_class(f"badge-{self._variant}")
                self.remove_class(self._variant)
            self._variant = val
            if val != "default":
                self.set_var("--variant", val)
                self.add_class(f"badge-{val}")
                self.add_class(val)
            self.request_redraw()
