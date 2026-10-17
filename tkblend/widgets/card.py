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
        width: Optional[int] = 240,
        height: Optional[int] = 180,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        pad_x: Optional[int] = None,
        pad_y: Optional[int] = None,
        auto_height: bool = False,
        **kwargs,
    ):
        eff_h = height if (height is not None and height > 0) else 180
        super().__init__(
            master=master,
            widget_class="card",
            width=width,
            height=eff_h,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            takefocus=False,
            **kwargs,
        )
        self._pad_x = pad_x if pad_x is not None else self.INNER_PAD_X
        self._pad_y = pad_y if pad_y is not None else self.INNER_PAD_Y
        self._auto_height = bool(auto_height or (height is None))
        self._controller.container_layer = ContainerLayer.Surface
        if not self._auto_height:
            self.pack_propagate(False)
            self.grid_propagate(False)
        else:
            self.pack_propagate(True)
            self.grid_propagate(True)
        self._content: Optional[tk.Frame] = None

    @property
    def auto_height(self) -> bool:
        """Whether the card dynamically sizes its height to fit packed/gridded child widgets."""
        return self._auto_height

    @auto_height.setter
    def auto_height(self, val: bool) -> None:
        self._auto_height = bool(val)
        if not self._auto_height:
            self.pack_propagate(False)
            self.grid_propagate(False)
        else:
            self.pack_propagate(True)
            self.grid_propagate(True)

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
