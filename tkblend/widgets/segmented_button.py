from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Sequence, Any
from tkblend.widgets.base import BaseControl


class SegmentedButton(BaseControl):
    """
    High-performance Material Design 3 connected pill switcher.
    """

    WIDGET_CLASS = "segmented_button"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        values: Optional[Sequence[str]] = None,
        selected_index: int = 0,
        selected_value: Optional[str] = None,
        command: Optional[Callable[[str], Any]] = None,
        variable: Optional[tk.Variable] = None,
        width: int = 220,
        height: int = 40,
        **kwargs,
    ):
        self._values = list(values) if values else ["Option 1", "Option 2"]
        self._variable = variable
        self._command = command
        self._selected_index = max(0, min(len(self._values) - 1, int(selected_index)))

        super().__init__(
            master=master,
            widget_class="segmented_button",
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )

        self._update_vars()

        if selected_value and selected_value in self._values:
            self.set(selected_value)
        elif self._variable is not None:
            try:
                cur_v = self._variable.get()
                if cur_v in self._values:
                    self.set(cur_v)
            except Exception:
                pass

    def _update_vars(self) -> None:
        self.set_var("--count", str(len(self._values)))
        self.set_var("--selected-index", str(self._selected_index))
        for i, val in enumerate(self._values):
            self.set_var(f"--seg-{i}-text", str(val))

    @property
    def values(self) -> list[str]:
        return list(self._values)

    @values.setter
    def values(self, vals: Sequence[str]) -> None:
        self._values = list(vals) if vals else ["Option 1"]
        self._selected_index = min(self._selected_index, len(self._values) - 1)
        self._update_vars()
        self.request_redraw()

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @selected_index.setter
    def selected_index(self, idx: int) -> None:
        self.select(idx)

    @property
    def selected_value(self) -> str:
        if 0 <= self._selected_index < len(self._values):
            return self._values[self._selected_index]
        return ""

    @selected_value.setter
    def selected_value(self, val: str) -> None:
        self.set(val)

    def get(self) -> str:
        return self.selected_value

    def set(self, val: str) -> None:
        if val in self._values:
            idx = self._values.index(val)
            self.select(idx)

    def select(self, idx: int) -> None:
        if 0 <= idx < len(self._values):
            self._selected_index = idx
            self.set_var("--selected-index", str(idx))
            cur_val = self.selected_value
            if self._variable is not None:
                try:
                    self._variable.set(cur_val)
                except Exception:
                    pass
            self.request_redraw()
            if callable(self._command):
                try:
                    self._command(cur_val)
                except Exception:
                    pass

    def on_change(self, val: Any) -> None:
        try:
            idx = int(val)
        except Exception:
            idx = 0
        if 0 <= idx < len(self._values):
            self._selected_index = idx
            self.set_var("--selected-index", str(idx))
            cur_val = self.selected_value
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
