from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Tuple, Any
from tkblend.widgets.base import BaseControl


class RangeSlider(BaseControl):
    """
    High-performance Material Design 3 dual-handle range slider.
    """

    WIDGET_CLASS = "range_slider"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        from_: float = 0.0,
        to: float = 100.0,
        values: Tuple[float, float] = (25.0, 75.0),
        command: Optional[Callable[[Tuple[float, float]], Any]] = None,
        width: int = 220,
        height: int = 36,
        **kwargs,
    ):
        self._from = float(from_)
        self._to = float(to)
        self._command = command

        super().__init__(
            master=master,
            widget_class="range_slider",
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )

        low, high = values
        self.set(low, high)

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

    def get(self) -> Tuple[float, float]:
        span = self._to - self._from
        try:
            min_p = float(self.get_var("--thumb-min-pos") or 0.25)
        except Exception:
            min_p = 0.25
        try:
            max_p = float(self.get_var("--thumb-max-pos") or 0.75)
        except Exception:
            max_p = 0.75
        return (self._from + min_p * span, self._from + max_p * span)

    def set(self, low: float, high: float) -> None:
        span = max(0.0001, self._to - self._from)
        clamped_low = max(self._from, min(self._to, float(low)))
        clamped_high = max(self._from, min(self._to, float(high)))
        if clamped_low > clamped_high:
            clamped_low, clamped_high = clamped_high, clamped_low

        min_p = (clamped_low - self._from) / span
        max_p = (clamped_high - self._from) / span

        self.set_var("--thumb-min-pos", str(max(0.0, min(1.0, min_p))))
        self.set_var("--thumb-max-pos", str(max(0.0, min(1.0, max_p))))
        self.request_redraw()

    @property
    def values(self) -> Tuple[float, float]:
        return self.get()

    @values.setter
    def values(self, vals: Tuple[float, float]) -> None:
        self.set(vals[0], vals[1])

    def on_change(self, val: Any) -> None:
        try:
            if isinstance(val, (tuple, list)) and len(val) >= 2:
                min_p, max_p = float(val[0]), float(val[1])
            else:
                return
        except Exception:
            return

        span = self._to - self._from
        cur_low = self._from + min_p * span
        cur_high = self._from + max_p * span
        if callable(self._command):
            try:
                self._command((cur_low, cur_high))
            except Exception:
                pass
