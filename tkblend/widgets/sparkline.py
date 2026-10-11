from __future__ import annotations

import tkinter as tk
from typing import Optional, Sequence, Any
from tkblend.widgets.base import BaseControl


class Sparkline(BaseControl):
    """
    High-performance Material Design 3 pure Blend2D vector trend sparkline.
    """

    WIDGET_CLASS = "sparkline"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        data: Optional[Sequence[float]] = None,
        width: int = 120,
        height: int = 36,
        **kwargs,
    ):
        self._data = list(data) if data is not None else [10.0, 25.0, 18.0, 42.0, 30.0, 55.0]

        super().__init__(
            master=master,
            widget_class="sparkline",
            width=width,
            height=height,
            takefocus=False,
            **kwargs,
        )

        self.set_data(self._data)

    @property
    def data(self) -> list[float]:
        return list(self._data)

    @data.setter
    def data(self, vals: Sequence[float]) -> None:
        self.set_data(vals)

    def set_data(self, vals: Sequence[float]) -> None:
        self._data = [float(v) for v in vals]
        self.set_var("--data", ",".join(str(v) for v in self._data))
        self.request_redraw()
