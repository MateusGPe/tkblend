from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any
from tkblend.widgets.base import BaseControl


class Switch(BaseControl):
    """High-performance pure Blend2D vector toggle switch."""

    WIDGET_CLASS = "switch"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        command: Optional[Callable[..., Any]] = None,
        variable: Optional[tk.Variable] = None,
        is_checked: bool = False,
        width: int = 120,
        height: int = 30,
        **kwargs,
    ):
        self._variable = variable
        super().__init__(
            master=master,
            widget_class="switch",
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )
        if text:
            self.set_var("--text", str(text))

        if self._variable is not None:
            try:
                is_checked = bool(self._variable.get())
            except Exception:
                pass
        self.is_checked = is_checked

    @property
    def text(self) -> str:
        return self.get_var("--text")

    @text.setter
    def text(self, val: str) -> None:
        self.set_var("--text", str(val))
        self.request_redraw()

    def toggle(self) -> None:
        self.is_checked = not self.is_checked
        if self._variable is not None:
            try:
                self._variable.set(self.is_checked)
            except Exception:
                pass
        if callable(self._command):
            try:
                self._command()
            except Exception:
                pass

    def on_change(self, val: Any) -> None:
        if self._variable is not None:
            try:
                self._variable.set(bool(val))
            except Exception:
                pass
        if callable(self._command):
            try:
                self._command()
            except Exception:
                pass
