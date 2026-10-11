from __future__ import annotations

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
        width: int = 120,
        height: int = 36,
        **kwargs,
    ):
        super().__init__(
            master=master,
            widget_class="button",
            width=width,
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
