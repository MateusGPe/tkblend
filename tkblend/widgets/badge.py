from __future__ import annotations

import tkinter as tk
from typing import Optional, Any
from tkblend.widgets.base import BaseControl
from tkblend.widgets.utils import measure_text_dimensions


class Badge(BaseControl):
    """High-performance pure Blend2D vector pill-shaped badge."""

    WIDGET_CLASS = "badge"
    DEFAULT_ANCHOR = "center"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        variant: str = "default",
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        anchor: str = "center",
        font: Any = None,
        padding_x: Optional[int] = None,
        auto_fit: Optional[bool] = None,
        **kwargs,
    ):
        self._initial_text = str(text or "")
        self._padding_x = 8 if padding_x is None else max(0, int(padding_x))
        self._base_height = height if height is not None else 24

        super().__init__(
            master=master,
            widget_class="badge",
            width=width,
            height=height or self._base_height,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            anchor=anchor,
            font=font,
            auto_fit=auto_fit,
            takefocus=False,
            **kwargs,
        )

        if text:
            self.set_var("--text", str(text))
        self.set_var("--badge-pad-x", str(self._padding_x))

        self._variant = str(variant or "default").lower()
        if self._variant and self._variant != "default":
            self.set_var("--variant", self._variant)
            self.add_class(f"badge-{self._variant}")
            self.add_class(self._variant)

        self._recalculate_natural_size()

    def _get_content_size(self) -> tuple[int, int]:
        txt = self.get_var("--text") if hasattr(self, "_controller") else getattr(self, "_initial_text", "")
        f_size = self._font_config.size if hasattr(self, "_font_config") else 11.0
        f_fam = self._font_config.family if hasattr(self, "_font_config") else "sans-serif"
        f_weight = self._font_config.effective_weight if hasattr(self, "_font_config") else 600

        text_w, text_h = measure_text_dimensions(
            txt,
            font_size=f_size,
            font_family=f_fam,
            font_weight=f_weight,
            pad_x=self._padding_x,
            pad_y=2,
            min_w=self._min_width or self._base_height,
            min_h=self._base_height,
        )
        if getattr(self, "_controller", None) is not None:
            self.set_var("--text-w", str(text_w))

        return text_w, self._explicit_height or self._base_height

    @property
    def padding_x(self) -> int:
        return self._padding_x

    @padding_x.setter
    def padding_x(self, val: int) -> None:
        self._padding_x = max(0, int(val))
        self.set_var("--badge-pad-x", str(self._padding_x))
        self._recalculate_natural_size()
        self.request_redraw()

    @property
    def text(self) -> str:
        return self.get_var("--text")

    @text.setter
    def text(self, val: str) -> None:
        str_val = str(val or "")
        self.set_var("--text", str_val)
        self._recalculate_natural_size()
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
