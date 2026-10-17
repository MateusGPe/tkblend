from __future__ import annotations

import tkinter as tk
from typing import Optional, Any
from tkblend.widgets.base import BaseControl
from tkblend.theme import Palette, cascade_bg_to_children
from tkblend.surface import ColorLike


class Frame(BaseControl):
    """
    High-performance Material Design 3 pure Blend2D vector frame container.
    Conforms to the compound container protocol (.bg_color).
    """

    WIDGET_CLASS = "frame"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: Optional[int] = 200,
        height: Optional[int] = 150,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        corner_radius: float = 12.0,
        border_width: float = 0.0,
        inner_bg: Optional[ColorLike] = None,
        outer_bg: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        **kwargs,
    ):
        self._corner_radius = float(corner_radius)
        self._border_width = float(border_width)

        super().__init__(
            master=master,
            widget_class="frame",
            width=width,
            height=height,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            corner_radius=corner_radius,
            inner_bg=inner_bg or bg_color,
            outer_bg=outer_bg or parent_bg,
            takefocus=False,
            **kwargs,
        )

        self.set_var("--rx", str(self._corner_radius))
        self.set_var("--ry", str(self._corner_radius))
        self.set_var("--bw", str(self._border_width))

        self.pack_propagate(True)
        self.grid_propagate(True)

    @property
    def corner_radius(self) -> float:
        return self._corner_radius

    @corner_radius.setter
    def corner_radius(self, val: float) -> None:
        self._corner_radius = float(val)
        self.set_var("--rx", str(val))
        self.set_var("--ry", str(val))
        self.request_redraw()

    @property
    def border_width(self) -> float:
        return self._border_width

    @border_width.setter
    def border_width(self, val: float) -> None:
        self._border_width = float(val)
        self.set_var("--bw", str(val))
        self.request_redraw()

    def set_inner_bg(self, color: ColorLike, render: bool = True, explicit: bool = True) -> None:
        super().set_inner_bg(color, render=render, explicit=explicit)
        cascade_bg_to_children(self, self.inner_bg, palette=self._palette)

    def on_theme_update(self, pal: Palette) -> None:
        super().on_theme_update(pal)
        cascade_bg_to_children(self, self.inner_bg, palette=pal)
