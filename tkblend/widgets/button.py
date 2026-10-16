import math
import tkinter as tk
from typing import Optional, Callable, Any
from tkblend.widgets.base import BaseControl


class Button(BaseControl):
    """High-performance pure Blend2D vector push button."""

    WIDGET_CLASS = "button"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        command: Optional[Callable[..., Any]] = None,
        variant: str = "default",
        width: Optional[int] = 120,
        height: int = 36,
        padding_x: int = 14,
        auto_fit: bool = False,
        **kwargs,
    ):
        self._padding_x = int(padding_x)
        self._auto_fit = bool(auto_fit or (width is None))
        self._explicit_width = width

        init_w = width if width is not None else 120
        if text and (auto_fit or width is None):
            init_w = self._calculate_auto_width(text, min_w=width or 0)

        super().__init__(
            master=master,
            widget_class="button",
            width=init_w,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )
        if text:
            self.set_var("--text", str(text))
        self._variant = str(variant or "default").lower()
        if self._variant and self._variant != "default":
            self.set_var("--variant", self._variant)
            self.add_class(f"btn-{self._variant}")

    def _calculate_auto_width(self, text: str, min_w: Optional[int] = None) -> int:
        if not text:
            return max(1, min_w or 40)
        try:
            metrics = self.surface.measure_text(
                str(text),
                font_size=13.0,
                font_family="sans-serif",
                weight=500,
            )
            text_width = metrics.advance_x
        except Exception:
            text_width = len(str(text)) * 8.0
        calc_w = int(math.ceil(text_width + 2 * self._padding_x))
        return max(min_w or 0, calc_w)

    @property
    def auto_fit(self) -> bool:
        return self._auto_fit

    @auto_fit.setter
    def auto_fit(self, val: bool) -> None:
        self._auto_fit = bool(val)
        if self._auto_fit:
            new_w = self._calculate_auto_width(self.text, self._explicit_width)
            if new_w != self._logical_w:
                self.set_geometry_request(new_w, self._logical_h)
            self.request_redraw()

    @property
    def text(self) -> str:
        return self.get_var("--text")

    @text.setter
    def text(self, val: str) -> None:
        self.set_var("--text", str(val))
        if self._auto_fit:
            new_w = self._calculate_auto_width(str(val), self._explicit_width)
            if new_w != self._logical_w:
                self.set_geometry_request(new_w, self._logical_h)
        self.request_redraw()

    @property
    def variant(self) -> str:
        return self._variant

    @variant.setter
    def variant(self, val: str) -> None:
        val = str(val or "default").lower()
        if val != self._variant:
            if self._variant and self._variant != "default":
                self.remove_class(f"btn-{self._variant}")
            self._variant = val
            if val != "default":
                self.set_var("--variant", val)
                self.add_class(f"btn-{val}")
            else:
                self.set_var("--variant", "")
            self.request_redraw()

    def invoke(self) -> Any:
        """Programmatically trigger button command."""
        if not self.is_disabled and callable(self._command):
            return self._command()
        return None
