from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any
from tkblend.widgets.base import BaseControl


class Radio(BaseControl):
    """High-performance pure Blend2D vector radio button."""

    WIDGET_CLASS = "radio"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        value: Any = None,
        variable: Optional[tk.Variable] = None,
        command: Optional[Callable[..., Any]] = None,
        width: int = 140,
        height: int = 30,
        **kwargs,
    ):
        self._value = value
        self._variable = variable
        super().__init__(
            master=master,
            widget_class="radio",
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )
        if text:
            self.set_var("--text", str(text))

        if self._variable is not None and self._value is not None:
            try:
                self.is_checked = (self._variable.get() == self._value)
            except Exception:
                pass

    @property
    def text(self) -> str:
        return self.get_var("--text")

    @text.setter
    def text(self, val: str) -> None:
        self.set_var("--text", str(val))
        self.request_redraw()

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, val: Any) -> None:
        self._value = val

    def select(self) -> None:
        self.is_checked = True
        if self._variable is not None and self._value is not None:
            try:
                self._variable.set(self._value)
            except Exception:
                pass
        if callable(self._command):
            try:
                self._command()
            except Exception:
                pass

    def on_change(self, val: Any) -> None:
        self.is_checked = True
        if self._variable is not None and self._value is not None:
            try:
                self._variable.set(self._value)
            except Exception:
                pass
        if callable(self._command):
            try:
                self._command()
            except Exception:
                pass
