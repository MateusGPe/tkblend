from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any
from tkblend.widgets.base import BaseControl
from tkblend.widgets.utils import measure_text_dimensions, bind_variable_trace, unbind_variable_trace


class Radio(BaseControl):
    """High-performance pure Blend2D vector radio button."""

    WIDGET_CLASS = "radio"
    DEFAULT_ANCHOR = "w"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        value: Any = None,
        variable: Optional[tk.Variable] = None,
        command: Optional[Callable[..., Any]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        anchor: str = "w",
        font: Any = None,
        auto_fit: bool = True,
        padding_x: int = 4,
        **kwargs,
    ):
        self._initial_text = str(text or "")
        self._value = value
        self._padding_x = int(padding_x)
        self._trace_id: Optional[str] = None

        super().__init__(
            master=master,
            widget_class="radio",
            width=width,
            height=height,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            anchor=anchor,
            font=font,
            auto_fit=auto_fit,
            command=command,
            variable=variable,
            cursor="hand2",
            **kwargs,
        )

        if text:
            self.set_var("--text", str(text))
        self.set_var("--radio-pad-x", str(self._padding_x))

        if self._variable is not None and self._value is not None:
            try:
                self.is_checked = (self._variable.get() == self._value)
            except Exception:
                pass
            self._trace_id = bind_variable_trace(self._variable, self._on_var_changed)

        self._recalculate_natural_size()

    def _on_var_changed(self, *args) -> None:
        if self._variable is not None and self._value is not None:
            try:
                should_be_checked = (self._variable.get() == self._value)
                if self.is_checked != should_be_checked:
                    self.is_checked = should_be_checked
            except Exception:
                pass

    def destroy(self) -> None:
        if self._variable is not None and self._trace_id is not None:
            unbind_variable_trace(self._variable, self._trace_id)
            self._trace_id = None
        super().destroy()

    def _get_content_size(self) -> tuple[int, int]:
        txt = self.get_var("--text") if hasattr(self, "_controller") else getattr(self, "_initial_text", "")
        cr_diameter = 16
        spacing = 8
        f_size = self._font_config.size if hasattr(self, "_font_config") else 13.0
        f_fam = self._font_config.family if hasattr(self, "_font_config") else "sans-serif"
        f_weight = self._font_config.effective_weight if hasattr(self, "_font_config") else 400

        text_w, text_h = measure_text_dimensions(
            txt,
            font_size=f_size,
            font_family=f_fam,
            font_weight=f_weight,
            pad_x=0,
            pad_y=0,
        )
        if getattr(self, "_controller", None) is not None:
            self.set_var("--text-w", str(text_w))

        total_w = cr_diameter + 2 * self._padding_x
        if txt:
            total_w += spacing + text_w

        total_h = max(30, max(cr_diameter, text_h) + 6)
        if self._explicit_height is not None:
            total_h = self._explicit_height
        if self._explicit_width is not None:
            total_w = max(self._explicit_width, total_w)

        return total_w, total_h

    @property
    def text(self) -> str:
        return self.get_var("--text")

    @text.setter
    def text(self, val: str) -> None:
        self.set_var("--text", str(val))
        self._recalculate_natural_size()
        self.request_redraw()

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, val: Any) -> None:
        self._value = val

    @property
    def is_checked(self) -> bool:
        return self.get_var("--selected") == "1"

    @is_checked.setter
    def is_checked(self, val: bool) -> None:
        self.set_var("--selected", "1" if val else "0")
        self.request_redraw()

    @property
    def is_selected(self) -> bool:
        return self.is_checked

    @is_selected.setter
    def is_selected(self, val: bool) -> None:
        self.is_checked = val

    def select(self) -> None:
        self.is_checked = True
        if self._variable is not None and self._value is not None:
            try:
                self._variable.set(self._value)
            except Exception:
                pass
        if callable(self._command):
            try:
                self._command()
            except Exception:
                pass

    def on_change(self, val: Any) -> None:
        self.is_checked = True
        if self._variable is not None and self._value is not None:
            try:
                self._variable.set(self._value)
            except Exception:
                pass
        if callable(self._command):
            try:
                self._command()
            except Exception:
                pass
