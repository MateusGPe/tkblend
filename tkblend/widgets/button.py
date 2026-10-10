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

    @property
    def text(self) -> str:
        return self.get_var("--text")

    @text.setter
    def text(self, val: str) -> None:
        self.set_var("--text", str(val))
        self.request_redraw()

    def invoke(self) -> Any:
        """Programmatically trigger button command."""
        if not self.is_disabled and callable(self._command):
            return self._command()
        return None
