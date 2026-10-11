from __future__ import annotations

import tkinter as tk
from typing import Optional, Any
from tkblend.widgets.base import BaseControl


class CircularProgress(BaseControl):
    """
    High-performance Material Design 3 pure Blend2D vector circular progress indicator.
    """

    WIDGET_CLASS = "circular_progress"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 110,
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
        self._variable = variable
        self._show_value = show_value
        self._stroke_w = float(stroke_width)
        self._start_angle = float(start_angle)
        self._sweep_angle = float(sweep_angle)

        super().__init__(
            master=master,
            widget_class="circular_progress",
            width=size,
            height=size,
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
        self.set(init_val)

    @property
    def value(self) -> float:
        return self.get()

    @value.setter
    def value(self, val: float) -> None:
        self.set(val)

    def get(self) -> float:
        try:
            norm = float(self.get_var("--progress") or 0.0)
        except Exception:
            norm = 0.0
        return self._min + norm * (self._max - self._min)

    def set(self, val: float) -> None:
        clamped = max(self._min, min(self._max, float(val)))
        span = max(0.0001, self._max - self._min)
        norm = (clamped - self._min) / span
        self.set_var("--progress", str(max(0.0, min(1.0, norm))))

        val_str = f"{int(clamped) if clamped.is_integer() else clamped:.1f}{self._unit}"
        self.set_var("--text", val_str)

        if self._variable is not None:
            try:
                self._variable.set(clamped)
            except Exception:
                pass
        self.request_redraw()

    def step(self, amount: float = 1.0) -> None:
        self.set(self.get() + float(amount))

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
        size: int = 140,
        value: float = 50.0,
        min_value: float = 0.0,
        max_value: float = 100.0,
        title: Optional[str] = "Speed",
        unit: str = "km/h",
        **kwargs,
    ):
        super().__init__(
            master=master,
            size=size,
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
