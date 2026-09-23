"""
VectorScrollbar widget implemented with pure Blend2D vector surface.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, Union, Tuple

from tkblend.theme import get_theme
from tkblend.widgets.base import Widget


class VectorScrollbar(Widget):
    """
    Pure Blend2D vector scrollbar widget with zero TTK dependencies.
    Renders rounded track, draggable high-contrast thumb capsule, and
    interfaces with any scrollable Tkinter widget (Canvas, Text, etc.).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        command: Optional[Callable[..., None]] = None,
        orientation: str = "vertical",
        width: int = 8,
        height: int = 120,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._command = command
        self._orientation = orientation
        self._first: float = 0.0
        self._last: float = 1.0
        self._is_dragging: bool = False
        self._drag_start_pos: float = 0.0
        self._drag_start_first: float = 0.0

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            **kwargs,
        )

        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def set(self, first: Union[str, float], last: Union[str, float]) -> None:
        """Standard Tkinter scrollbar set protocol: set(first, last)."""
        try:
            self._first = max(0.0, min(1.0, float(first)))
            self._last = max(0.0, min(1.0, float(last)))
            self.render()
        except Exception:
            pass

    def _get_thumb_geometry(self) -> Tuple[float, float, float, float]:
        s = self._scale
        pad = 1.0 * s
        w = max(1.0, float(self._widget_w) - pad * 2.0)
        h = max(1.0, float(self._widget_h) - pad * 2.0)

        total_span = max(0.05, min(1.0, self._last - self._first))
        min_thumb = 18.0 * s
        thumb_h = max(min_thumb, h * total_span)
        available_travel = max(0.0, h - thumb_h)

        max_first = max(0.001, 1.0 - total_span)
        norm_first = max(0.0, min(1.0, self._first / max_first)) if max_first > 0 else 0.0
        thumb_y = pad + norm_first * available_travel

        return pad, thumb_y, w, thumb_h

    def _on_press(self, event) -> None:
        if self._is_disabled:
            return
        pad, ty, tw, th = self._get_thumb_geometry()
        py = float(event.y)

        if ty <= py <= ty + th:
            self._is_dragging = True
            self._drag_start_pos = py
            self._drag_start_first = self._first
            self.render()
        else:
            if py < ty:
                if self._command:
                    self._command("scroll", -1, "pages")
            else:
                if self._command:
                    self._command("scroll", 1, "pages")

    def _on_drag(self, event) -> None:
        if not self._is_dragging or self._is_disabled:
            return
        s = self._scale
        pad = 1.0 * s
        h = max(1.0, float(self._widget_h) - pad * 2.0)
        total_span = max(0.05, min(1.0, self._last - self._first))
        min_thumb = 18.0 * s
        thumb_h = max(min_thumb, h * total_span)
        available_travel = max(1.0, h - thumb_h)

        delta_px = float(event.y) - self._drag_start_pos
        max_first = max(0.001, 1.0 - total_span)
        delta_fraction = (delta_px / available_travel) * max_first
        new_first = max(0.0, min(max_first, self._drag_start_first + delta_fraction))

        if self._command:
            self._command("moveto", new_first)

    def _on_release(self, event) -> None:
        if self._is_dragging:
            self._is_dragging = False
            self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        pad = 1.0 * s
        w = max(1.0, float(self._widget_w) - pad * 2.0)
        h = max(1.0, float(self._widget_h) - pad * 2.0)
        r = min(w / 2.0, 4.0 * s)

        pal = get_theme()
        # Draw track with distinct contrast
        track_col = "#252538" if pal.dark_mode else "#e2e8f0"
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, track_col)

        # Draw thumb with high contrast
        _, ty, tw, th = self._get_thumb_geometry()
        thumb_r = min(tw / 2.0, 4.0 * s)

        if self._is_dragging:
            thumb_col = pal.primary
        elif self._is_hovered:
            thumb_col = "#89b4fa" if pal.dark_mode else "#3b82f6"
        else:
            thumb_col = "#6c7086" if pal.dark_mode else "#94a3b8"

        self._surface.fill_rounded_rect(pad, ty, tw, th, thumb_r, thumb_r, thumb_col)
        self._surface.blit(self._photo)


ModernScrollbar = VectorScrollbar
Scrollbar = VectorScrollbar
