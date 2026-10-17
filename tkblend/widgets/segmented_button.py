from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Sequence, Any
from tkblend.widgets.base import BaseControl
from tkblend.widgets.utils import measure_text_dimensions


class SegmentedButton(BaseControl):
    """
    High-performance Material Design 3 connected pill switcher.
    """

    WIDGET_CLASS = "segmented_button"
    DEFAULT_ANCHOR = "center"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        values: Optional[Sequence[str]] = None,
        value: Optional[str] = None,
        selected_index: int = 0,
        selected_value: Optional[str] = None,
        command: Optional[Callable[[str], Any]] = None,
        variable: Optional[tk.Variable] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        anchor: str = "center",
        corner_radius: Optional[float] = None,
        font: Any = None,
        auto_fit: Optional[bool] = None,
        **kwargs,
    ):
        self._values = list(values) if values is not None else ["Option 1", "Option 2"]
        self._selected_index = max(0, min(len(self._values) - 1, int(selected_index))) if self._values else -1

        super().__init__(
            master=master,
            widget_class="segmented_button",
            width=width,
            height=height,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            anchor=anchor,
            corner_radius=corner_radius,
            font=font,
            auto_fit=auto_fit,
            command=command,
            variable=variable,
            cursor="hand2",
            **kwargs,
        )

        self._update_vars()

        init_val = value if value is not None else selected_value
        if init_val and init_val in self._values:
            self.set(init_val)
        elif self._variable is not None:
            try:
                cur_v = self._variable.get()
                if cur_v in self._values:
                    self.set(cur_v)
            except Exception:
                pass

        self._recalculate_natural_size()

    def _get_content_size(self) -> tuple[int, int]:
        f_size = self._font_config.size if hasattr(self, "_font_config") else 13.0
        f_fam = self._font_config.family if hasattr(self, "_font_config") else "sans-serif"
        f_weight = self._font_config.effective_weight if hasattr(self, "_font_config") else 500

        total_w = 12  # outer margins
        max_h = 40

        for val in self._values:
            seg_w, seg_h = measure_text_dimensions(
                str(val),
                font_size=f_size,
                font_family=f_fam,
                font_weight=f_weight,
                pad_x=16,
                pad_y=8,
                min_w=40,
                min_h=36,
            )
            total_w += seg_w
            if seg_h > max_h:
                max_h = seg_h

        if self._explicit_height is not None:
            max_h = self._explicit_height
        if self._explicit_width is not None:
            total_w = max(self._explicit_width, total_w)

        return total_w, max_h

    def _update_vars(self) -> None:
        self.set_var("--count", str(len(self._values)))
        self.set_var("--selected-index", str(self._selected_index if self._values else -1))
        for i, val in enumerate(self._values):
            self.set_var(f"--seg-{i}-text", str(val))

    @property
    def values(self) -> list[str]:
        return list(self._values)

    @values.setter
    def values(self, vals: Sequence[str]) -> None:
        self._values = list(vals) if vals is not None else []
        if self._values:
            self._selected_index = max(0, min(self._selected_index, len(self._values) - 1))
        else:
            self._selected_index = -1
        self._update_vars()
        self._recalculate_natural_size()
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

    @property
    def value(self) -> str:
        return self.selected_value

    @value.setter
    def value(self, val: str) -> None:
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
            if 0 <= idx < len(self._values):
                self._selected_index = idx
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
        except Exception:
            pass
