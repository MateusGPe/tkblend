from __future__ import annotations

import tkinter as tk
from typing import Optional
from tkblend._tkblend import ContainerLayer
from tkblend.widgets.base import BaseControl
from tkblend.theme import Palette, cascade_bg_to_children


class Card(BaseControl):
    """High-performance pure Blend2D vector elevated container card."""

    WIDGET_CLASS = "card"
    SHADOW_PAD_X: int = 10
    SHADOW_PAD_TOP: int = 8
    SHADOW_PAD_BOTTOM: int = 12

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 180,
        **kwargs,
    ):
        super().__init__(
            master=master,
            widget_class="card",
            width=width,
            height=height,
            takefocus=False,
            **kwargs,
        )
        self._controller.container_layer = ContainerLayer.Surface
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._content: Optional[tk.Frame] = None

    @property
    def content(self) -> tk.Frame:
        """Lazy inner content container frame positioned inside the card's rounded surface."""
        if self._content is None:
            self._content = tk.Frame(self, background=self.inner_bg)
            self._content.place(
                x=self.SHADOW_PAD_X,
                y=self.SHADOW_PAD_TOP,
                relwidth=1.0,
                relheight=1.0,
                width=-(2 * self.SHADOW_PAD_X),
                height=-(self.SHADOW_PAD_TOP + self.SHADOW_PAD_BOTTOM),
            )
        return self._content

    def on_theme_update(self, pal: Palette) -> None:
        super().on_theme_update(pal)
        if self._content is not None:
            try:
                self._content.configure(background=pal.card_bg)
            except Exception:
                pass
        cascade_bg_to_children(self, pal.card_bg, palette=pal)
