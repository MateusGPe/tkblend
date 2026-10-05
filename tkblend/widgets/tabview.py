"""
Pure Blend2D Vector Tabview navigation container powered by BaseControl.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Dict, List, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.widgets.frame import Frame
from tkblend.widgets.segmented_button import SegmentedButton
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    to_tk_hex,
    cascade_bg_to_children,
)
from tkblend.widgets.constants import (
    CURSOR_DEFAULT,
)


class Tabview(BaseControl):
    """
    Modern tabbed view container featuring top vector segmented tab switcher
    and dynamic tab page switching.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 400,
        height: int = 300,
        corner_radius: float = 8.0,
        inner_bg: Optional[ColorLike] = None,
        outer_bg: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        command: Optional[Callable[[str], None]] = None,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._corner_radius = float(corner_radius)
        self._custom_border = border_color
        self._border_width = float(border_width)
        self._command = command

        self._tabs: Dict[str, tk.Frame] = {}
        self._tab_names: List[str] = []
        self._current_tab: Optional[str] = None

        super().__init__(
            master=master,
            width=width,
            height=height,
            inner_bg=inner_bg or bg_color,
            outer_bg=outer_bg or parent_bg,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            **kwargs,
        )

        # Tab bar
        self._tab_bar = SegmentedButton(
            self,
            values=["Tab 1"],
            command=self._on_tab_switched,
            outer_bg=self.inner_bg,
            height=32,
        )

        # Content container
        self._container = tk.Frame(self, background=to_tk_hex(self.inner_bg))

        self._layout_components()

    def _default_inner_bg(self, pal: Palette) -> str:
        return pal.card_bg

    def _layout_components(self) -> None:
        s = self._scale_factor
        pad = int(8.0 * s)
        bar_h = int(32.0 * s)

        self._tab_bar.place(x=pad, y=pad, relwidth=1.0, width=-pad * 2, height=bar_h)
        self._container.place(
            x=pad,
            y=pad + bar_h + int(6.0 * s),
            relwidth=1.0,
            relheight=1.0,
            width=-pad * 2,
            height=-pad * 2 - bar_h - int(6.0 * s),
        )

    def add(self, name: str) -> tk.Frame:
        name_str = str(name)
        if name_str in self._tabs:
            return self._tabs[name_str]

        tab_frame = tk.Frame(self._container, background=to_tk_hex(self.inner_bg))
        self._tabs[name_str] = tab_frame
        self._tab_names.append(name_str)
        self._tab_bar.values = list(self._tab_names)

        if self._current_tab is None:
            self.set(name_str)

        return tab_frame

    def tab(self, name: str) -> tk.Frame:
        return self._tabs[str(name)]

    def get(self) -> Optional[str]:
        return self._current_tab

    def set(self, name: str) -> None:
        name_str = str(name)
        if name_str not in self._tabs:
            return

        self._current_tab = name_str
        self._tab_bar.set(name_str)

        for tname, tframe in self._tabs.items():
            if tname == name_str:
                tframe.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            else:
                tframe.place_forget()

        if self._command:
            try:
                self._command(name_str)
            except Exception:
                pass

    def _on_tab_switched(self, name: str) -> None:
        self.set(name)

    def on_theme_update(self, pal: Palette) -> None:
        bg_hex = to_tk_hex(self.inner_bg)
        self._container.configure(background=bg_hex)
        if hasattr(self, "_tab_bar"):
            self._tab_bar.set_outer_bg(self.inner_bg)
        for tframe in self._tabs.values():
            tframe.configure(background=bg_hex)
            cascade_bg_to_children(tframe, self.inner_bg, palette=pal)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        cr = self._corner_radius * s
        bg_col = self.inner_bg
        border_col = resolve_color_failsafe(self._custom_border or pal.card_border, palette=pal)

        surf.clear(self.outer_bg)
        surf.fill_rounded_rect(0.0, 0.0, w, h, cr, cr, bg_col)
        if self._border_width > 0.0:
            surf.stroke_rounded_rect(0.0, 0.0, w, h, cr, cr, border_col, stroke_width=self._border_width * s)


# Alias
TabView = Tabview
