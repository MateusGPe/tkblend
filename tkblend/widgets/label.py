from __future__ import annotations

import tkinter as tk
from typing import Optional
from tkblend.widgets.base import BaseControl


class Label(BaseControl):
    """High-performance pure Blend2D vector label."""

    WIDGET_CLASS = "label"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        width: int = 120,
        height: int = 26,
        **kwargs,
    ):
        super().__init__(
            master=master,
            widget_class="label",
            width=width,
            height=height,
            takefocus=False,
            **kwargs,
        )
        if text:
            self.set_var("--text", str(text))

    @property
    def text(self) -> str:
        return self.get_var("--text")

    @text.setter
    def text(self, val: str) -> None:
        self.set_var("--text", str(val))
        self.request_redraw()
