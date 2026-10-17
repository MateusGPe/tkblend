from __future__ import annotations

import tkinter as tk
from typing import Optional, Any
from tkblend.widgets.base import BaseControl
from tkblend.widgets.utils import bind_variable_trace, unbind_variable_trace


class CircularProgress(BaseControl):
    """
    High-performance Material Design 3 pure Blend2D vector circular progress indicator.
    """

    WIDGET_CLASS = "circular_progress"
    DEFAULT_ANCHOR = "center"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        value: float = 65.0,
        min_value: float = 0.0,
        max_value: float = 100.0,
        stroke_width: float = 8.0,
        variable: Optional[tk.Variable] = None,
        show_value: bool = True,
        unit: str = "%",
        title: Optional[str] = None,
        start_angle: float = -90.0,
        sweep_angle: float = 360.0,
        **kwargs,
    ):
        self._min = float(min_value)
        self._max = float(max_value)
        self._unit = str(unit or "")
        self._title = title
        self._show_value = show_value
        self._stroke_w = float(stroke_width)
        self._start_angle = float(start_angle)
        self._sweep_angle = float(sweep_angle)
        self._trace_id: Optional[str] = None

        eff_size = size or width or height or 110

        super().__init__(
            master=master,
            widget_class="circular_progress",
            width=width or eff_size,
            height=height or eff_size,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            variable=variable,
            takefocus=False,
            **kwargs,
        )

        self.set_var("--stroke-width", str(self._stroke_w))
        self.set_var("--start-angle", str(self._start_angle))
        self.set_var("--sweep-angle", str(self._sweep_angle))
        self.set_var("--show-value", "1" if show_value else "0")
        if title:
            self.set_var("--title", str(title))

        init_val = value
        if self._variable is not None:
            try:
                init_val = float(self._variable.get())
            except Exception:
                pass
            self._trace_id = bind_variable_trace(self._variable, self._on_var_changed)

        self.set(init_val)

    def _get_content_size(self) -> tuple[int, int]:
        s = self._explicit_width or self._explicit_height or 110
        return s, s

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

    def get(self) -> float:
        norm = float(self.get_var("--progress", "0.0") or 0.0)
        return self._min + norm * (self._max - self._min)

    def set(self, val: float) -> None:
        span = self._max - self._min
        clamped = max(self._min, min(self._max, float(val)))
        norm = (clamped - self._min) / span if span > 0 else 0.0
        self.set_var("--progress", f"{norm:.4f}")
        if self._show_value:
            display_str = f"{int(round(clamped))}{self._unit}"
            self.set_var("--text", display_str)
        if self._variable is not None:
            try:
                self._variable.set(clamped)
            except Exception:
                pass
        self.request_redraw()

    def step(self, amount: float = 1.0) -> None:
        """Step progress value by amount, clamping to max_value."""
        self.set(self.get() + float(amount))

    @property
    def value(self) -> float:
        return self.get()

    @value.setter
    def value(self, val: float) -> None:
        self.set(val)

    @property
    def title(self) -> Optional[str]:
        return self._title

    @title.setter
    def title(self, val: Optional[str]) -> None:
        self._title = val
        if val:
            self.set_var("--title", str(val))
        else:
            self.remove_var("--title")
        self.request_redraw()


class Gauge(CircularProgress):
    """
    Material Design 3 Radial Dial Gauge with 240-degree sweep and center readout.
    """

    WIDGET_CLASS = "gauge"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        value: float = 50.0,
        min_value: float = 0.0,
        max_value: float = 100.0,
        title: Optional[str] = "Speed",
        unit: str = "km/h",
        **kwargs,
    ):
        super().__init__(
            master=master,
            size=size or width or height or 140,
            width=width,
            height=height,
            value=value,
            min_value=min_value,
            max_value=max_value,
            stroke_width=10.0,
            start_angle=150.0,
            sweep_angle=240.0,
            title=title,
            unit=unit,
            **kwargs,
        )
