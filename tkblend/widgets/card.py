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
    INNER_PAD_X: int = 18
    INNER_PAD_Y: int = 14

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 180,
        pad_x: Optional[int] = None,
        pad_y: Optional[int] = None,
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
        self._pad_x = pad_x if pad_x is not None else self.INNER_PAD_X
        self._pad_y = pad_y if pad_y is not None else self.INNER_PAD_Y
        self._controller.container_layer = ContainerLayer.Surface
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._content: Optional[tk.Frame] = None

    @property
    def pad_x(self) -> int:
        """Horizontal inner padding inset for content container."""
        return self._pad_x

    @property
    def pad_y(self) -> int:
        """Vertical inner padding inset for content container."""
        return self._pad_y

    @property
    def content(self) -> tk.Frame:
        """Lazy inner content container frame positioned inside the card's rounded surface with inset padding."""
        if self._content is None:
            self._content = tk.Frame(self, background=self.inner_bg)
            total_pad_x = self.SHADOW_PAD_X + self._pad_x
            total_pad_top = self.SHADOW_PAD_TOP + self._pad_y
            total_pad_bottom = self.SHADOW_PAD_BOTTOM + self._pad_y
            self._content.place(
                x=total_pad_x,
                y=total_pad_top,
                relwidth=1.0,
                relheight=1.0,
                width=-(2 * total_pad_x),
                height=-(total_pad_top + total_pad_bottom),
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
