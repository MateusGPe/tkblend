from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any
from tkblend.widgets.base import BaseControl


class Slider(BaseControl):
    """High-performance pure Blend2D vector slider."""

    WIDGET_CLASS = "slider"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        from_: float = 0.0,
        to: float = 100.0,
        value: float = 0.0,
        command: Optional[Callable[[float], Any]] = None,
        variable: Optional[tk.Variable] = None,
        width: int = 180,
        height: int = 30,
        **kwargs,
    ):
        self._from = float(from_)
        self._to = float(to)
        self._variable = variable
        super().__init__(
            master=master,
            widget_class="slider",
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )

        init_val = value
        if self._variable is not None:
            try:
                init_val = float(self._variable.get())
            except Exception:
                pass
        self.set(init_val)

    @property
    def from_(self) -> float:
        return self._from

    @from_.setter
    def from_(self, val: float) -> None:
        self._from = float(val)
        self.request_redraw()

    @property
    def to(self) -> float:
        return self._to

    @to.setter
    def to(self, val: float) -> None:
        self._to = float(val)
        self.request_redraw()

    def get(self) -> float:
        try:
            norm = float(self.get_var("--thumb-pos") or 0.0)
        except Exception:
            norm = 0.0
        return self._from + norm * (self._to - self._from)

    def set(self, val: float) -> None:
        clamped = max(min(self._from, self._to), min(max(self._from, self._to), float(val)))
        span = self._to - self._from
        norm = (clamped - self._from) / span if span != 0 else 0.0
        self.set_var("--thumb-pos", str(max(0.0, min(1.0, norm))))
        if self._variable is not None:
            try:
                self._variable.set(clamped)
            except Exception:
                pass
        self.request_redraw()

    @property
    def value(self) -> float:
        return self.get()

    @value.setter
    def value(self, val: float) -> None:
        self.set(val)

    def on_change(self, val: Any) -> None:
        try:
            norm = float(val)
        except Exception:
            norm = 0.0
        cur_val = self._from + norm * (self._to - self._from)
        if self._variable is not None:
            try:
                self._variable.set(cur_val)
            except Exception:
                pass
        if callable(self._command):
            try:
                self._command(cur_val)
            except Exception:
                pass
