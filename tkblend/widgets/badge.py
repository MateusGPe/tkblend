from __future__ import annotations

import tkinter as tk
from typing import Optional
from tkblend.widgets.base import BaseControl


class Badge(BaseControl):
    """High-performance pure Blend2D vector pill-shaped badge."""

    WIDGET_CLASS = "badge"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        width: int = 60,
        height: int = 24,
        **kwargs,
    ):
        super().__init__(
            master=master,
            widget_class="badge",
            width=width,
            height=height,
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
