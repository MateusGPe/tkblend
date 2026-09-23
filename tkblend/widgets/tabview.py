"""
Tabview - Multi-tab container widget with pure Blend2D vector styling.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, Dict, List, Union

from tkblend.surface import ColorLike
from tkblend.theme import (
    get_theme,
    Palette,
    add_theme_listener,
    remove_theme_listener,
    resolve_color_failsafe,
)
from tkblend.widgets.base import Widget, ScalingTracker, cascade_bg_to_children
from tkblend.widgets.containers import Frame


class _TabHeaderBar(Widget):
    """Internal segmented vector header bar for Tabview."""

    def __init__(
        self,
        master: tk.Misc,
        tabs: List[str],
        active_tab: Optional[str] = None,
        on_tab_change: Optional[Callable[[str], None]] = None,
        rx: float = 8.0,
        ry: float = 8.0,
        tab_bg: Optional[ColorLike] = None,
        active_tab_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        active_text_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._tabs = list(tabs)
        self._active_tab = active_tab or (self._tabs[0] if self._tabs else "")
        self._on_tab_change = on_tab_change
        self._rx = rx
        self._ry = ry
        self._explicit_tab_bg = tab_bg
        self._explicit_active_tab_color = active_tab_color
        self._explicit_text_color = text_color
        self._explicit_active_text_color = active_text_color
        self._hovered_index: Optional[int] = None

        pal = get_theme()
        super().__init__(
            master=master,
            width=200,
            height=36,
            bg=parent_bg,
            **kwargs,
        )

        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)

    def set_tabs(self, tabs: List[str], active_tab: Optional[str] = None) -> None:
        self._tabs = list(tabs)
        if active_tab:
            self._active_tab = active_tab
        elif self._tabs and self._active_tab not in self._tabs:
            self._active_tab = self._tabs[0]
        self.render()

    def set_active_tab(self, tab: str) -> None:
        if tab in self._tabs and self._active_tab != tab:
            self._active_tab = tab
            self.render()

    def get_active_tab(self) -> str:
        return self._active_tab

    def _index_at(self, x: float) -> Optional[int]:
        if not self._tabs:
            return None
        s = self._scale
        pad = 2.0 * s
        usable_w = max(1.0, self._widget_w - pad * 2.0)
        tab_w = usable_w / len(self._tabs)
        rel_x = x - pad
        if 0 <= rel_x <= usable_w:
            idx = int(rel_x // tab_w)
            return min(len(self._tabs) - 1, max(0, idx))
        return None

    def _on_mouse_move(self, event) -> None:
        idx = self._index_at(event.x)
        if idx != self._hovered_index:
            self._hovered_index = idx
            self.render()

    def _on_mouse_leave(self, event) -> None:
        if self._hovered_index is not None:
            self._hovered_index = None
            self.render()

    def _handle_click(self, event) -> None:
        idx = self._index_at(event.x)
        if idx is not None and 0 <= idx < len(self._tabs):
            tab_name = self._tabs[idx]
            if tab_name != self._active_tab:
                self._active_tab = tab_name
                self.render()
                if self._on_tab_change:
                    self._on_tab_change(tab_name)

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            pad = 2.0 * s
            w = max(1.0, self._widget_w - pad * 2.0)
            h = max(1.0, self._widget_h - pad * 2.0)
            r = min(self._rx * s, h / 2.0)

            pal = get_theme()
            bar_bg = self._explicit_tab_bg or pal.surface
            active_col = self._explicit_active_tab_color or pal.primary
            fg_col = self._explicit_text_color or pal.fg
            active_fg = self._explicit_active_text_color or pal.primary_fg

            # Track background
            self._surface.fill_rounded_rect(pad, pad, w, h, r, r, bar_bg)
            self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, pal.surface_border, 1.0 * s)

            num_tabs = len(self._tabs)
            if num_tabs > 0:
                tab_w = w / num_tabs

                # Hover highlight
                if self._hovered_index is not None and 0 <= self._hovered_index < num_tabs:
                    hov_name = self._tabs[self._hovered_index]
                    if hov_name != self._active_tab:
                        hx = pad + self._hovered_index * tab_w
                        self._surface.fill_rounded_rect(
                            hx + 1.0, pad + 1.0, tab_w - 2.0, h - 2.0, max(2.0, r - 2.0), max(2.0, r - 2.0), pal.secondary
                        )

                # Active tab indicator
                if self._active_tab in self._tabs:
                    act_idx = self._tabs.index(self._active_tab)
                    ax = pad + act_idx * tab_w
                    safe_blur = min(2.0 * s, pad * 0.8)
                    safe_offset_y = min(0.8 * s, pad * 0.3)
                    self._surface.draw_shadow(
                        ax + 1.0, pad + 1.0, tab_w - 2.0, h - 2.0,
                        max(2.0, r - 2.0), max(2.0, r - 2.0),
                        blur_radius=safe_blur, offset_y=safe_offset_y, shadow_color=pal.shadow_color
                    )
                    self._surface.fill_rounded_rect(
                        ax + 1.0, pad + 1.0, tab_w - 2.0, h - 2.0,
                        max(2.0, r - 2.0), max(2.0, r - 2.0), active_col
                    )

                # Tab text labels
                font_sz = max(9.0, 12.0 * s)
                for i, tab_name in enumerate(self._tabs):
                    tx = pad + (i + 0.5) * tab_w
                    ty = pad + h / 2.0 + (font_sz * 0.35)
                    col = active_fg if tab_name == self._active_tab else fg_col
                    self._surface.draw_text(
                        tab_name, tx, ty,
                        font_size=font_sz,
                        font_family="sans-serif",
                        color=col,
                        align="center"
                    )

            self._surface.blit(self._photo)
        except Exception:
            pass


class Tabview(tk.Frame):
    """
    Modern Tabview widget: Multi-tab container with a top segmented
    Blend2D vector header bar and dynamic page swapping.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 300,
        height: int = 250,
        rx: float = 12.0,
        ry: float = 12.0,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        elevation: float = 4.0,
        active_tab_color: Optional[ColorLike] = None,
        header_height: int = 36,
        command: Optional[Callable[[str], None]] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._scale = ScalingTracker.get_scaling_factor(master)
        pal = get_theme()
        self._explicit_parent_bg = parent_bg
        self._parent_bg = parent_bg or Widget._resolve_default_bg(master, pal)
        self._rx = rx
        self._ry = ry
        self._bg_color = bg_color
        self._border_color = border_color
        self._border_width = border_width
        self._elevation = elevation
        self._active_tab_color = active_tab_color
        self._header_height = header_height
        self._command = command

        self._tabs: Dict[str, Frame] = {}
        self._current_tab: Optional[str] = None

        super().__init__(
            master,
            width=max(1, int(width * self._scale)),
            height=max(1, int(height * self._scale)),
            background=self._parent_bg,
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )

        # Main container frame (card-style)
        self._container_frame = Frame(
            self,
            rx=self._rx,
            ry=self._ry,
            bg_color=self._bg_color,
            border_color=self._border_color,
            border_width=self._border_width,
            elevation=self._elevation,
            parent_bg=self._parent_bg,
        )
        self._container_frame.pack(fill="both", expand=True)

        # Header bar
        self._header = _TabHeaderBar(
            self._container_frame,
            tabs=[],
            on_tab_change=self._on_header_tab_clicked,
            rx=max(4.0, self._rx - 4.0),
            ry=max(4.0, self._ry - 4.0),
            active_tab_color=self._active_tab_color,
            parent_bg=self._container_frame.bg_color,
        )
        self._header.pack(fill="x", padx=8, pady=(8, 4))

        # Content area
        self._content_area = tk.Frame(
            self._container_frame,
            background=self._container_frame.bg_color,
            borderwidth=0,
            highlightthickness=0,
        )
        self._content_area.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        add_theme_listener(self._on_theme_changed)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def add(self, name: str) -> Frame:
        """Create and return a new Frame page for the specified tab name."""
        if name in self._tabs:
            return self._tabs[name]

        tab_frame = Frame(
            self._content_area,
            rx=max(2.0, self._rx - 6.0),
            ry=max(2.0, self._ry - 6.0),
            bg_color=self._bg_color,
            border_width=0,
            elevation=0,
            parent_bg=self._container_frame.bg_color,
        )
        self._tabs[name] = tab_frame

        tab_list = list(self._tabs.keys())
        if self._current_tab is None:
            self._current_tab = name
            tab_frame.pack(fill="both", expand=True)

        self._header.set_tabs(tab_list, active_tab=self._current_tab)
        return tab_frame

    def tab(self, name: str) -> Frame:
        """Retrieve the Frame container for the specified tab name."""
        if name not in self._tabs:
            raise KeyError(f"Tab '{name}' does not exist in Tabview.")
        return self._tabs[name]

    def set(self, name: str) -> None:
        """Switch active tab to the specified tab name."""
        if name not in self._tabs or name == self._current_tab:
            return
        if self._current_tab in self._tabs:
            self._tabs[self._current_tab].pack_forget()

        self._current_tab = name
        self._tabs[name].pack(fill="both", expand=True)
        self._header.set_active_tab(name)

        if self._command:
            try:
                self._command(name)
            except TypeError:
                self._command()

    @property
    def bg_color(self) -> str:
        """Return the container card background color."""
        return self._container_frame.bg_color

    def get(self) -> Optional[str]:
        """Return the name of the currently active tab."""
        return self._current_tab

    def delete(self, name: str) -> None:
        """Remove a tab page from the tabview."""
        if name not in self._tabs:
            return
        frame = self._tabs.pop(name)
        frame.destroy()

        tab_list = list(self._tabs.keys())
        if self._current_tab == name:
            self._current_tab = tab_list[0] if tab_list else None
            if self._current_tab:
                self._tabs[self._current_tab].pack(fill="both", expand=True)

        self._header.set_tabs(tab_list, active_tab=self._current_tab)

    def _on_header_tab_clicked(self, name: str) -> None:
        self.set(name)

    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        resolved_bg = self._explicit_parent_bg or Widget._resolve_default_bg(self.master, palette)
        self._parent_bg = resolved_bg
        self.configure(background=self._parent_bg)
        if self._bg_color is None:
            self._container_frame._bg_color = palette.card_bg
        if self._border_color is None:
            self._container_frame._border_color = palette.card_border
        self._container_frame.set_parent_bg(self._parent_bg)
        self._container_frame.render()

        inner_bg = self._container_frame.bg_color
        self._content_area.configure(background=inner_bg)
        self._header.set_parent_bg(inner_bg)
        self._header.render()

        for tab_frame in self._tabs.values():
            if self._bg_color is None:
                tab_frame._bg_color = inner_bg
            tab_frame.set_parent_bg(inner_bg)
            tab_frame.render()
            cascade_bg_to_children(tab_frame, inner_bg)

    def _on_destroy(self, event) -> None:
        if event.widget == self:
            remove_theme_listener(self._on_theme_changed)


ModernTabview = Tabview
