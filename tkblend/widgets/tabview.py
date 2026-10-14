from __future__ import annotations

import tkinter as tk
from typing import Optional, Dict
from tkblend.widgets.base import BaseControl
from tkblend.widgets.segmented_button import SegmentedButton
from tkblend.theme import (
    Palette,
    to_tk_hex,
    cascade_bg_to_children,
    is_inside_card,
    resolve_ancestor_bg,
)
from tkblend.surface import ColorLike


class Tabview(BaseControl):
    """
    High-performance Material Design 3 tabbed container.
    """

    WIDGET_CLASS = "frame"

    def _default_inner_bg(self, pal: Palette) -> str:
        m = getattr(self, "master", None) or getattr(self, "_master_ref", None)
        if m is not None and is_inside_card(m):
            return pal.card_bg
        return resolve_ancestor_bg(m, pal) if m is not None else pal.bg

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 360,
        height: int = 240,
        inner_bg: Optional[ColorLike] = None,
        outer_bg: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        **kwargs,
    ):
        super().__init__(
            master=master,
            widget_class="frame",
            width=width,
            height=height,
            inner_bg=inner_bg or bg_color,
            outer_bg=outer_bg or parent_bg,
            takefocus=False,
            **kwargs,
        )

        self._tabs: Dict[str, tk.Frame] = {}
        self._current_tab: str = ""

        bg_hex = to_tk_hex(self.inner_bg)
        self.set_var("--bg", bg_hex)
        self.set_var("--bw", "0")

        # Header switcher
        self._segmented = SegmentedButton(
            self,
            values=[],
            command=self._on_segment_changed,
            height=36,
            parent_bg=self.inner_bg,
        )
        self._segmented.pack(fill="x", padx=12, pady=(10, 8))

        # Container for tab pages
        self._page_container = tk.Frame(self, background=bg_hex)
        self._page_container.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    @property
    def bg_color(self) -> str:
        """Active inner background color conforming to Compound Container Protocol."""
        return self.inner_bg

    @bg_color.setter
    def bg_color(self, val: ColorLike) -> None:
        self.set_inner_bg(val)

    def set_inner_bg(self, color: ColorLike, render: bool = True, explicit: bool = True) -> None:
        super().set_inner_bg(color, render=render, explicit=explicit)
        bg_hex = to_tk_hex(self.inner_bg)
        self.set_var("--bg", bg_hex)
        self.set_var("--bw", "0")
        try:
            self._page_container.configure(background=bg_hex)
            for f in self._tabs.values():
                f.configure(background=bg_hex)
        except Exception:
            pass
        if hasattr(self, "_segmented"):
            self._segmented.set_outer_bg(self.inner_bg, render=render)
        cascade_bg_to_children(self._page_container, self.inner_bg, palette=self._palette)

    def add(self, name: str) -> tk.Frame:
        """Add a named tab page and return its content frame."""
        name_str = str(name)
        if name_str in self._tabs:
            return self._tabs[name_str]

        bg_hex = to_tk_hex(self.inner_bg)
        frame = tk.Frame(self._page_container, background=bg_hex)
        self._tabs[name_str] = frame

        cur_values = self._segmented.values
        cur_values.append(name_str)
        self._segmented.values = cur_values

        if not self._current_tab:
            self.set(name_str)

        return frame

    def get(self) -> str:
        return self._current_tab

    def set(self, name: str) -> None:
        name_str = str(name)
        if name_str not in self._tabs:
            return

        self._current_tab = name_str
        self._segmented.set(name_str)

        for tab_name, page_frame in self._tabs.items():
            if tab_name == name_str:
                page_frame.pack(fill="both", expand=True)
            else:
                page_frame.pack_forget()

    def _on_segment_changed(self, chosen: str) -> None:
        self.set(chosen)

    def on_theme_update(self, pal: Palette) -> None:
        super().on_theme_update(pal)
        if self._explicit_inner_bg is None:
            self._resolved_inner_bg = self._default_inner_bg(pal)
        bg_hex = to_tk_hex(self.inner_bg)
        self.set_var("--bg", bg_hex)
        self.set_var("--bw", "0")
        try:
            self._page_container.configure(background=bg_hex)
            for f in self._tabs.values():
                f.configure(background=bg_hex)
        except Exception:
            pass
        if hasattr(self, "_segmented"):
            self._segmented.set_outer_bg(self.inner_bg, render=True)
        cascade_bg_to_children(self._page_container, self.inner_bg, palette=pal)
