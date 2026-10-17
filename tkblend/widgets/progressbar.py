from __future__ import annotations

import tkinter as tk
from typing import Optional, Any
from tkblend.widgets.base import BaseControl
from tkblend.widgets.utils import bind_variable_trace, unbind_variable_trace


class Progressbar(BaseControl):
    """High-performance pure Blend2D vector progress bar."""

    WIDGET_CLASS = "progressbar"
    DEFAULT_ANCHOR = "center"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        value: float = 0.0,
        maximum: float = 100.0,
        variable: Optional[tk.Variable] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        corner_radius: Optional[float] = None,
        **kwargs,
    ):
        self._maximum = float(maximum) if float(maximum) > 0.0 else 100.0
        self._trace_id: Optional[str] = None

        super().__init__(
            master=master,
            widget_class="progressbar",
            width=width,
            height=height,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            corner_radius=corner_radius,
            variable=variable,
            takefocus=False,
            **kwargs,
        )

        init_val = value
        if self._variable is not None:
            try:
                init_val = float(self._variable.get())
            except Exception:
                pass
            self._trace_id = bind_variable_trace(self._variable, self._on_var_changed)

        self.set(init_val)

    def _get_content_size(self) -> tuple[int, int]:
        return self._explicit_width or 200, self._explicit_height or 12

    def _on_var_changed(self, *args) -> None:
        if self._variable is not None:
            try:
                v = float(self._variable.get())
                if abs(self.get() - v) > 1e-5:
                    self.set(v)
            except Exception:
                pass

    def destroy(self) -> None:
        if self._variable is not None and self._trace_id is not None:
            unbind_variable_trace(self._variable, self._trace_id)
            self._trace_id = None
        super().destroy()

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

    def step(self, amount: float = 1.0) -> None:
        """Step progress value by amount, wrapping around maximum if needed."""
        new_val = self.get() + float(amount)
        if new_val > self._maximum:
            new_val = new_val % self._maximum
        self.set(new_val)

