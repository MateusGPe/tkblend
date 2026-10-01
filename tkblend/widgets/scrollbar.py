"""
VectorScrollbar widget implemented with pure Blend2D vector surface.
"""

from __future__ import annotations
import logging
import tkinter as tk
from typing import Optional, Callable, Union, Tuple

from tkblend.theme import get_theme
from tkblend.widgets.base import Widget

logger = logging.getLogger(__name__)


class Scrollbar(Widget):
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
        except Exception as e:
            logger.debug("Failed parsing/setting scrollbar fraction (%r, %r): %s", first, last, e)

    def _get_thumb_geometry(self) -> Tuple[float, float, float, float]:
        s = self._scale
        pad = 1.0 * s
        w = max(1.0, float(self._widget_w) - pad * 2.0)
        h = max(1.0, float(self._widget_h) - pad * 2.0)

        total_span = max(0.05, min(1.0, self._last - self._first))
        min_thumb = 18.0 * s

        if self._orientation == "horizontal":
            thumb_w = max(min_thumb, w * total_span)
            available_travel = max(0.0, w - thumb_w)
            max_first = max(0.001, 1.0 - total_span)
            norm_first = max(0.0, min(1.0, self._first / max_first)) if max_first > 0 else 0.0
            thumb_x = pad + norm_first * available_travel
            return thumb_x, pad, thumb_w, h
        else:
            thumb_h = max(min_thumb, h * total_span)
            available_travel = max(0.0, h - thumb_h)
            max_first = max(0.001, 1.0 - total_span)
            norm_first = max(0.0, min(1.0, self._first / max_first)) if max_first > 0 else 0.0
            thumb_y = pad + norm_first * available_travel
            return pad, thumb_y, w, thumb_h

    def _on_press(self, event) -> None:
        if self._is_disabled:
            return
        tx, ty, tw, th = self._get_thumb_geometry()

        if self._orientation == "horizontal":
            px = float(getattr(event, "x", 0.0))
            if tx <= px <= tx + tw:
                self._is_dragging = True
                self._drag_start_pos = px
                self._drag_start_first = self._first
                self.render()
            else:
                if px < tx:
                    if self._command:
                        self._command("scroll", -1, "pages")
                else:
                    if self._command:
                        self._command("scroll", 1, "pages")
        else:
            py = float(getattr(event, "y", 0.0))
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
        total_span = max(0.05, min(1.0, self._last - self._first))
        min_thumb = 18.0 * s
        max_first = max(0.001, 1.0 - total_span)

        if self._orientation == "horizontal":
            w = max(1.0, float(self._widget_w) - pad * 2.0)
            thumb_w = max(min_thumb, w * total_span)
            available_travel = max(1.0, w - thumb_w)
            delta_px = float(getattr(event, "x", 0.0)) - self._drag_start_pos
            delta_fraction = (delta_px / available_travel) * max_first
            new_first = max(0.0, min(max_first, self._drag_start_first + delta_fraction))
        else:
            h = max(1.0, float(self._widget_h) - pad * 2.0)
            thumb_h = max(min_thumb, h * total_span)
            available_travel = max(1.0, h - thumb_h)
            delta_px = float(getattr(event, "y", 0.0)) - self._drag_start_pos
            delta_fraction = (delta_px / available_travel) * max_first
            new_first = max(0.0, min(max_first, self._drag_start_first + delta_fraction))

        if self._command:
            self._command("moveto", new_first)

    def _on_release(self, event) -> None:
        if self._is_dragging:
            self._is_dragging = False
            self.render()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            pad = 1.0 * s
            w = max(1.0, float(self._widget_w) - pad * 2.0)
            h = max(1.0, float(self._widget_h) - pad * 2.0)
            r = min(min(w, h) / 2.0, 4.0 * s)

            pal = get_theme()
            # Draw track with distinct contrast
            track_col = "#252538" if pal.dark_mode else "#e2e8f0"
            self._surface.fill_rounded_rect(pad, pad, w, h, r, r, track_col)

            # Draw thumb with high contrast
            tx, ty, tw, th = self._get_thumb_geometry()
            thumb_r = min(min(tw, th) / 2.0, 4.0 * s)

            if self._is_dragging:
                thumb_col = pal.primary
            elif self._is_hovered:
                thumb_col = "#89b4fa" if pal.dark_mode else "#3b82f6"
            else:
                thumb_col = "#6c7086" if pal.dark_mode else "#94a3b8"

            self._surface.fill_rounded_rect(tx, ty, tw, th, thumb_r, thumb_r, thumb_col)
            self.end_render()
        except Exception as e:
            logger.debug("Render failed in VectorScrollbar: %s", e, exc_info=True)



VectorScrollbar = Scrollbar

