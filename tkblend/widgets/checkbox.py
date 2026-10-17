from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any
from tkblend.widgets.base import BaseControl
from tkblend.widgets.utils import measure_text_dimensions, bind_variable_trace, unbind_variable_trace


class Checkbox(BaseControl):
    """High-performance pure Blend2D vector checkbox."""

    WIDGET_CLASS = "checkbox"
    DEFAULT_ANCHOR = "w"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        command: Optional[Callable[..., Any]] = None,
        variable: Optional[tk.Variable] = None,
        is_checked: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        anchor: str = "w",
        corner_radius: float = 4.0,
        font: Any = None,
        auto_fit: bool = True,
        padding_x: int = 4,
        **kwargs,
    ):
        self._initial_text = str(text or "")
        self._padding_x = int(padding_x)
        self._trace_id: Optional[str] = None

        super().__init__(
            master=master,
            widget_class="checkbox",
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

        if text:
            self.set_var("--text", str(text))
        self.set_var("--checkbox-pad-x", str(self._padding_x))

        if self._variable is not None:
            try:
                is_checked = bool(self._variable.get())
            except Exception:
                pass
            self._trace_id = bind_variable_trace(self._variable, self._on_var_changed)

        self.is_checked = is_checked
        self._recalculate_natural_size()

    def _on_var_changed(self, *args) -> None:
        if self._variable is not None:
            try:
                val = bool(self._variable.get())
                if self.is_checked != val:
                    self.is_checked = val
            except Exception:
                pass

    def destroy(self) -> None:
        if self._variable is not None and self._trace_id is not None:
            unbind_variable_trace(self._variable, self._trace_id)
            self._trace_id = None
        super().destroy()

    def _get_content_size(self) -> tuple[int, int]:
        txt = self.get_var("--text") if hasattr(self, "_controller") else getattr(self, "_initial_text", "")
        box_size = 18
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

        total_w = box_size + 2 * self._padding_x
        if txt:
            total_w += spacing + text_w

        total_h = max(30, max(box_size, text_h) + 6)
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
    def checked(self) -> bool:
        return self.is_checked

    @checked.setter
    def checked(self, val: bool) -> None:
        self.is_checked = val

    def toggle(self) -> None:
        self.is_checked = not self.is_checked
        if self._variable is not None:
            try:
                self._variable.set(self.is_checked)
            except Exception:
                pass
        if callable(self._command):
            try:
                self._command()
            except Exception:
                pass

    def on_change(self, val: Any) -> None:
        if self._variable is not None:
            try:
                self._variable.set(bool(val))
            except Exception:
                pass
        if callable(self._command):
            try:
                self._command()
            except Exception:
                pass
