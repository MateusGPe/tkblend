from __future__ import annotations

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
        width: int = 60,
        height: int = 24,
        **kwargs,
    ):
        super().__init__(
            master=master,
            widget_class="badge",
            width=width,
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

    @property
    def text(self) -> str:
        return self.get_var("--text")

    @text.setter
    def text(self, val: str) -> None:
        self.set_var("--text", str(val))
        self.request_redraw()

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
