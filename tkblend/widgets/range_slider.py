from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Tuple, Any
from tkblend.widgets.base import BaseControl


class RangeSlider(BaseControl):
    """
    High-performance Material Design 3 dual-handle range slider.
    """

    WIDGET_CLASS = "range_slider"
    DEFAULT_ANCHOR = "center"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        from_: float = 0.0,
        to: float = 100.0,
        values: Optional[Tuple[float, float]] = None,
        lower_value: Optional[float] = None,
        upper_value: Optional[float] = None,
        command: Optional[Callable[[Tuple[float, float]], Any]] = None,
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
        self._command = command

        super().__init__(
            master=master,
            widget_class="range_slider",
            width=width,
            height=height,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            command=command,
            cursor="hand2",
            **kwargs,
        )

        low = lower_value if lower_value is not None else (values[0] if values else 25.0)
        high = upper_value if upper_value is not None else (values[1] if values else 75.0)
        self.set(low, high)

    def _get_content_size(self) -> tuple[int, int]:
        return self._explicit_width or 220, self._explicit_height or 36

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
        min_p = float(self.get_var("--thumb-min-pos", "0.25"))
        max_p = float(self.get_var("--thumb-max-pos", "0.75"))
        span = self._to - self._from
        return self._from + min_p * span, self._from + max_p * span

    def set(self, low: float, high: float) -> None:
        span = self._to - self._from
        if abs(span) < 1e-9:
            min_p, max_p = 0.0, 1.0
        else:
            min_p = max(0.0, min(1.0, (float(low) - self._from) / span))
            max_p = max(0.0, min(1.0, (float(high) - self._from) / span))
            if min_p > max_p:
                min_p, max_p = max_p, min_p
        self.set_var("--thumb-min-pos", f"{min_p:.4f}")
        self.set_var("--thumb-max-pos", f"{max_p:.4f}")
        self.request_redraw()

    @property
    def value(self) -> Tuple[float, float]:
        return self.get()

    @value.setter
    def value(self, val: Tuple[float, float]) -> None:
        self.set(val[0], val[1])

    @property
    def lower_value(self) -> float:
        return self.get()[0]

    @lower_value.setter
    def lower_value(self, val: float) -> None:
        _, high = self.get()
        self.set(val, high)

    @property
    def upper_value(self) -> float:
        return self.get()[1]

    @upper_value.setter
    def upper_value(self, val: float) -> None:
        low, _ = self.get()
        self.set(low, val)

    def configure(self, **kwargs) -> Any:
        low = kwargs.pop("lower_value", None)
        high = kwargs.pop("upper_value", None)
        if low is not None or high is not None:
            cur_low, cur_high = self.get()
            self.set(cur_low if low is None else low, cur_high if high is None else high)
        return super().configure(**kwargs)

    def on_change(self, val: Any) -> None:
        try:
            if isinstance(val, (tuple, list)) and len(val) >= 2:
                min_p = max(0.0, min(1.0, float(val[0])))
                max_p = max(0.0, min(1.0, float(val[1])))
                span = self._to - self._from
                real_low = self._from + min_p * span
                real_high = self._from + max_p * span
                if callable(self._command):
                    try:
                        self._command((real_low, real_high))
                    except Exception:
                        pass
        except Exception:
            pass
