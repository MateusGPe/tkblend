from __future__ import annotations

import tkinter as tk
from typing import Optional, Any
from tkblend.widgets.base import BaseControl


class Progressbar(BaseControl):
    """High-performance pure Blend2D vector progress bar."""

    WIDGET_CLASS = "progressbar"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        value: float = 0.0,
        maximum: float = 100.0,
        variable: Optional[tk.Variable] = None,
        width: int = 200,
        height: int = 12,
        **kwargs,
    ):
        self._maximum = float(maximum) if float(maximum) > 0.0 else 100.0
        self._variable = variable
        super().__init__(
            master=master,
            widget_class="progressbar",
            width=width,
            height=height,
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
    def maximum(self) -> float:
        return self._maximum

    @maximum.setter
    def maximum(self, val: float) -> None:
        self._maximum = max(0.001, float(val))
        self.set(self.get())

    def get(self) -> float:
        try:
            norm = float(self.get_var("--progress") or 0.0)
        except Exception:
            norm = 0.0
        return norm * self._maximum

    def set(self, val: float) -> None:
        clamped = max(0.0, min(self._maximum, float(val)))
        norm = clamped / self._maximum if self._maximum > 0 else 0.0
        self.set_var("--progress", str(max(0.0, min(1.0, norm))))
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

    def step(self, amount: float = 1.0) -> None:
        self.set(self.get() + float(amount))
