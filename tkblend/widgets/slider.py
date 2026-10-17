from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any
from tkblend.widgets.base import BaseControl
from tkblend.widgets.utils import bind_variable_trace, unbind_variable_trace


class Slider(BaseControl):
    """High-performance pure Blend2D vector slider."""

    WIDGET_CLASS = "slider"
    DEFAULT_ANCHOR = "center"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        from_: float = 0.0,
        to: float = 100.0,
        value: float = 0.0,
        command: Optional[Callable[[float], Any]] = None,
        variable: Optional[tk.Variable] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        **kwargs,
    ):
        self._from = float(from_)
        self._to = float(to)
        self._trace_id: Optional[str] = None

        super().__init__(
            master=master,
            widget_class="slider",
            width=width,
            height=height,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            command=command,
            variable=variable,
            cursor="hand2",
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
        return self._explicit_width or 180, self._explicit_height or 30

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
        pos_str = self.get_var("--thumb-pos", "0.0")
        try:
            pos = float(pos_str)
        except Exception:
            pos = 0.0
        return self._from + pos * (self._to - self._from)

    def set(self, val: float) -> None:
        span = self._to - self._from
        if abs(span) < 1e-9:
            pos = 0.0
        else:
            pos = max(0.0, min(1.0, (float(val) - self._from) / span))
        self.set_var("--thumb-pos", f"{pos:.4f}")
        if self._variable is not None:
            try:
                self._variable.set(float(val))
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
            pos = max(0.0, min(1.0, float(val)))
            real_val = self._from + pos * (self._to - self._from)
            if self._variable is not None:
                try:
                    self._variable.set(real_val)
                except Exception:
                    pass
            if callable(self._command):
                try:
                    self._command(real_val)
                except Exception:
                    pass
        except Exception:
            pass
