from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any
from tkblend.widgets.base import BaseControl
from tkblend.widgets.utils import measure_text_dimensions, normalize_anchor


class Button(BaseControl):
    """High-performance pure Blend2D vector push button."""

    WIDGET_CLASS = "button"
    DEFAULT_ANCHOR = "center"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        command: Optional[Callable[..., Any]] = None,
        variable: Optional[tk.Variable] = None,
        variant: str = "default",
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        anchor: str = "center",
        corner_radius: float = 8.0,
        font: Any = None,
        auto_fit: bool = True,
        padding_x: int = 16,
        padding_y: int = 8,
        **kwargs,
    ):
        self._initial_text = str(text or "")
        self._padding_x = int(padding_x)
        self._padding_y = int(padding_y)

        super().__init__(
            master=master,
            widget_class="button",
            width=width,
            height=height,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            auto_fit=auto_fit,
            anchor=anchor,
            corner_radius=corner_radius,
            font=font,
            command=command,
            variable=variable,
            cursor="hand2",
            **kwargs,
        )

        if text:
            self.set_var("--text", str(text))
        self.set_var("--btn-pad-x", str(self._padding_x))
        self._variant = str(variant or "default").lower()
        if self._variant and self._variant != "default":
            self.set_var("--variant", self._variant)
            self.add_class(f"btn-{self._variant}")

        # Recalculate natural content size now that vars/font are in place
        self._recalculate_natural_size()

    def _get_content_size(self) -> tuple[int, int]:
        txt = self.get_var("--text") if hasattr(self, "_controller") else getattr(self, "_initial_text", "")
        f_size = self._font_config.size if hasattr(self, "_font_config") else 13.0
        f_fam = self._font_config.family if hasattr(self, "_font_config") else "sans-serif"
        f_weight = self._font_config.effective_weight if hasattr(self, "_font_config") else 500
        w, h = measure_text_dimensions(
            txt,
            font_size=f_size,
            font_family=f_fam,
            font_weight=f_weight,
            pad_x=self._padding_x,
            pad_y=self._padding_y,
            min_w=self._explicit_width or 40,
            min_h=self._explicit_height or 36,
        )
        return w, h

    @property
    def text(self) -> str:
        return self.get_var("--text")

    @text.setter
    def text(self, val: str) -> None:
        self.set_var("--text", str(val))
        self._recalculate_natural_size()
        self.request_redraw()

    @property
    def padding_x(self) -> int:
        return self._padding_x

    @padding_x.setter
    def padding_x(self, val: int) -> None:
        self._padding_x = max(0, int(val))
        self.set_var("--btn-pad-x", str(self._padding_x))
        self._recalculate_natural_size()
        self.request_redraw()

    @property
    def padding_y(self) -> int:
        return self._padding_y

    @padding_y.setter
    def padding_y(self, val: int) -> None:
        self._padding_y = max(0, int(val))
        self._recalculate_natural_size()
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
