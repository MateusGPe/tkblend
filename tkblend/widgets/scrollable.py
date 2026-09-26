"""
ScrollableFrame - Modern scrollable container with integrated Blend2D vector scrollbars.
"""

from __future__ import annotations
import sys
import tkinter as tk
from typing import Optional, Union

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
from tkblend.widgets.scrollbar import VectorScrollbar


class ScrollableFrame(tk.Frame):
    """
    Scrollable container frame with integrated Blend2D vector scrollbars,
    smooth card background, mousewheel handling, and automatic geometry propagation.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 250,
        height: int = 300,
        rx: float = 12.0,
        ry: float = 12.0,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        elevation: float = 4.0,
        scrollbar_width: int = 8,
        orientation: str = "vertical",  # "vertical", "horizontal", or "both"
        parent_bg: Optional[str] = None,
        clip_children: bool = True,
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
        self._scrollbar_width = scrollbar_width
        self._orientation = orientation
        self._clip_children = clip_children

        super().__init__(
            master,
            width=max(1, int(width * self._scale)),
            height=max(1, int(height * self._scale)),
            background=self._parent_bg,
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )

        # Container card frame
        self._card = Frame(
            self,
            rx=self._rx,
            ry=self._ry,
            bg_color=self._bg_color,
            border_color=self._border_color,
            border_width=self._border_width,
            elevation=self._elevation,
            parent_bg=self._parent_bg,
            clip_children=self._clip_children,
        )
        self._card.pack(fill="both", expand=True)

        inner_bg = self._card.bg_color

        # Canvas viewport
        self._canvas = tk.Canvas(
            self._card,
            background=inner_bg,
            borderwidth=0,
            highlightthickness=0,
        )

        # Scrollable interior content frame
        self._scrollable_content = tk.Frame(
            self._canvas,
            background=inner_bg,
            borderwidth=0,
            highlightthickness=0,
        )
        self._window_id = self._canvas.create_window((0, 0), window=self._scrollable_content, anchor="nw")

        # Vertical Scrollbar
        self._v_scrollbar: Optional[VectorScrollbar] = None
        if self._orientation in ("vertical", "both"):
            self._v_scrollbar = VectorScrollbar(
                self._card,
                command=self._canvas.yview,
                orientation="vertical",
                width=self._scrollbar_width,
                parent_bg=inner_bg,
            )
            self._canvas.configure(yscrollcommand=self._v_scrollbar.set)
            self._v_scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)

        # Horizontal Scrollbar
        self._h_scrollbar: Optional[VectorScrollbar] = None
        if self._orientation in ("horizontal", "both"):
            self._h_scrollbar = VectorScrollbar(
                self._card,
                command=self._canvas.xview,
                orientation="horizontal",
                height=self._scrollbar_width,
                parent_bg=inner_bg,
            )
            self._canvas.configure(xscrollcommand=self._h_scrollbar.set)
            self._h_scrollbar.pack(side="bottom", fill="x", padx=4, pady=(0, 4))

        self._canvas.pack(side="left", fill="both", expand=True, padx=4, pady=4)

        # Geometry & scroll bindings
        self._scrollable_content.bind("<Configure>", self._on_content_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._bind_mousewheel(self)
        self._bind_mousewheel(self._canvas)
        self._bind_mousewheel(self._scrollable_content)

        add_theme_listener(self._on_theme_changed)
        self.bind("<Destroy>", self._on_destroy, add="+")

    @property
    def bg_color(self) -> str:
        """Return the current interior background color."""
        return self._card.bg_color

    @property
    def scrollable_frame(self) -> tk.Frame:
        """Access the interior frame where children widgets should be placed."""
        return self._scrollable_content

    @property
    def content(self) -> tk.Frame:
        """Alias for scrollable_frame."""
        return self._scrollable_content

    def _on_content_configure(self, event) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        # Fit content width to canvas if single vertical scrolling
        if self._orientation == "vertical":
            self._canvas.itemconfig(self._window_id, width=event.width)
        elif self._orientation == "horizontal":
            self._canvas.itemconfig(self._window_id, height=event.height)

    def _bind_mousewheel(self, widget: tk.Misc) -> None:
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel_linux, add="+")
        widget.bind("<Button-5>", self._on_mousewheel_linux, add="+")

    def _on_mousewheel(self, event) -> None:
        if self._orientation in ("vertical", "both"):
            # Windows / macOS
            delta = event.delta
            if sys.platform == "darwin":
                self._canvas.yview_scroll(int(-1 * delta), "units")
            else:
                self._canvas.yview_scroll(int(-1 * (delta / 120)), "units")

    def _on_mousewheel_linux(self, event) -> None:
        if self._orientation in ("vertical", "both"):
            if event.num == 4:
                self._canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self._canvas.yview_scroll(1, "units")

    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        resolved_bg = self._explicit_parent_bg or Widget._resolve_default_bg(self.master, palette)
        self._parent_bg = resolved_bg
        self.configure(background=self._parent_bg)
        if self._bg_color is None:
            self._card._bg_color = palette.card_bg
        if self._border_color is None:
            self._card._border_color = palette.card_border
        self._card.set_parent_bg(self._parent_bg)
        self._card.render()

        inner_bg = self._card.bg_color
        self._canvas.configure(background=inner_bg)
        self._scrollable_content.configure(background=inner_bg)
        if self._v_scrollbar:
            self._v_scrollbar.set_parent_bg(inner_bg)
        if self._h_scrollbar:
            self._h_scrollbar.set_parent_bg(inner_bg)
        cascade_bg_to_children(self._scrollable_content, inner_bg)

    def _on_destroy(self, event) -> None:
        if event.widget == self:
            remove_theme_listener(self._on_theme_changed)


