"""
Pure Blend2D Vector ScrollableFrame and VectorScrollbar powered by BaseControl.
"""

from __future__ import annotations

import sys
import tkinter as tk
from typing import Optional, Callable, Any, Union

from tkblend.widgets.base import BaseControl, ScalingTracker
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    blend_color_hex,
    to_tk_hex,
    cascade_bg_to_children,
)
from tkblend.widgets.constants import (
    CURSOR_DEFAULT,
    CURSOR_HAND,
)


class VectorScrollbar(BaseControl):
    """
    Modern vector scrollbar with capsule thumb knob, hover glow, and drag tracking.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        orientation: str = "vertical",
        command: Optional[Callable] = None,
        width: int = 8,
        height: int = 100,
        thumb_color: Optional[ColorLike] = None,
        track_color: Optional[ColorLike] = None,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._orientation = orientation.lower()
        self._command = command
        self._custom_thumb = thumb_color
        self._custom_track = track_color
        self._start_fraction = 0.0
        self._end_fraction = 1.0
        self._is_dragging = False
        self._drag_start_pos = 0.0
        self._drag_start_fraction = 0.0
        self._is_hovered = False

        w = width if self._orientation == "vertical" else height
        h = height if self._orientation == "vertical" else width

        super().__init__(
            master=master,
            width=w,
            height=h,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            **kwargs,
        )

        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def set(self, first: float, last: float) -> None:
        self._start_fraction = max(0.0, min(1.0, float(first)))
        self._end_fraction = max(self._start_fraction, min(1.0, float(last)))
        self.request_redraw()

    def get(self) -> tuple[float, float]:
        return (self._start_fraction, self._end_fraction)

    def _on_enter(self, event) -> None:
        self._is_hovered = True
        self.request_redraw()

    def _on_leave(self, event) -> None:
        self._is_hovered = False
        self.request_redraw()

    def _on_press(self, event) -> None:
        if self._orientation == "vertical":
            total = float(self.winfo_height() or self._logical_h)
            pos = float(event.y)
        else:
            total = float(self.winfo_width() or self._logical_w)
            pos = float(event.x)

        thumb_start = self._start_fraction * total
        thumb_end = self._end_fraction * total

        if thumb_start <= pos <= thumb_end:
            self._is_dragging = True
            self._drag_start_pos = pos
            self._drag_start_fraction = self._start_fraction
        else:
            # Click jump
            frac = pos / max(1.0, total)
            span = self._end_fraction - self._start_fraction
            new_first = max(0.0, min(1.0 - span, frac - span / 2.0))
            if self._command:
                try:
                    self._command("moveto", f"{new_first}")
                except Exception:
                    pass

    def _on_drag(self, event) -> None:
        if not self._is_dragging:
            return
        if self._orientation == "vertical":
            total = float(self.winfo_height() or self._logical_h)
            pos = float(event.y)
        else:
            total = float(self.winfo_width() or self._logical_w)
            pos = float(event.x)

        delta_px = pos - self._drag_start_pos
        delta_frac = delta_px / max(1.0, total)
        span = self._end_fraction - self._start_fraction
        new_first = max(0.0, min(1.0 - span, self._drag_start_fraction + delta_frac))
        if self._command:
            try:
                self._command("moveto", f"{new_first}")
            except Exception:
                pass

    def _on_release(self, event) -> None:
        self._is_dragging = False
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        th_col = resolve_color_failsafe(self._custom_thumb or pal.thumb_color, palette=pal)
        if self._is_hovered or self._is_dragging:
            th_col = blend_color_hex(th_col, pal.primary, 0.4)

        if self._orientation == "vertical":
            cr = w / 2.0
            span_h = max(16.0 * s, (self._end_fraction - self._start_fraction) * h)
            start_y = self._start_fraction * (h - span_h)
            surf.fill_rounded_rect(0.0, start_y, w, span_h, cr, cr, th_col)
        else:
            cr = h / 2.0
            span_w = max(16.0 * s, (self._end_fraction - self._start_fraction) * w)
            start_x = self._start_fraction * (w - span_w)
            surf.fill_rounded_rect(start_x, 0.0, span_w, h, cr, cr, th_col)


class ScrollableFrame(BaseControl):
    """
    Modern vector scrollable frame container with high-performance mousewheel scrolling,
    integrated vector scrollbars, and dynamic compound theme inheritance.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 300,
        height: int = 300,
        corner_radius: float = 8.0,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        scrollbar_width: int = 8,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._corner_radius = float(corner_radius)
        self._custom_bg = bg_color
        self._custom_border = border_color
        self._border_width = float(border_width)
        self._scrollbar_w = int(scrollbar_width)

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            **kwargs,
        )

        # Viewport Canvas
        pal = self._palette
        bg_hex = to_tk_hex(self.bg_color)
        self._canvas = tk.Canvas(
            self,
            bd=0,
            highlightthickness=0,
            relief="flat",
            background=bg_hex,
        )

        # Internal scrollable content frame
        self._scrollable_frame = tk.Frame(self._canvas, background=bg_hex)
        self._window_id = self._canvas.create_window((0, 0), window=self._scrollable_frame, anchor="nw")

        # Vector Scrollbar
        self._v_scrollbar = VectorScrollbar(
            self,
            orientation="vertical",
            width=self._scrollbar_w,
            command=self._canvas.yview,
        )
        self._canvas.configure(xscrollcommand=None, yscrollcommand=self._on_canvas_scroll)

        # Mousewheel bindings
        self._bind_mousewheel(self)
        self._bind_mousewheel(self._canvas)
        self._bind_mousewheel(self._scrollable_frame)

        self._scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        self._layout_components()

    @property
    def scrollable_frame(self) -> tk.Frame:
        return self._scrollable_frame

    @property
    def content_frame(self) -> tk.Frame:
        return self._scrollable_frame

    @property
    def bg_color(self) -> str:
        return resolve_color_failsafe(self._custom_bg or self._palette.card_bg, palette=self._palette)

    def _layout_components(self) -> None:
        s = self._scale_factor
        pad = int(4.0 * s)
        sb_w = int(self._scrollbar_w * s)

        self._canvas.place(
            x=pad,
            y=pad,
            relwidth=1.0,
            relheight=1.0,
            width=-pad * 2 - sb_w - 2,
            height=-pad * 2,
        )
        self._v_scrollbar.place(
            relx=1.0,
            y=pad,
            relheight=1.0,
            x=-pad - sb_w,
            width=sb_w,
            height=-pad * 2,
        )

    def _on_frame_configure(self, event) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        # Match inner frame width to canvas width
        self._canvas.itemconfig(self._window_id, width=event.width)

    def _on_canvas_scroll(self, first: str, last: str) -> None:
        self._v_scrollbar.set(float(first), float(last))

    def _bind_mousewheel(self, widget: tk.Misc) -> None:
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel, add="+")
        widget.bind("<Button-5>", self._on_mousewheel, add="+")

    def _on_mousewheel(self, event) -> None:
        if event.num == 4 or event.delta > 0:
            self._canvas.yview_scroll(-2, "units")
        elif event.num == 5 or event.delta < 0:
            self._canvas.yview_scroll(2, "units")

    def on_theme_update(self, pal: Palette) -> None:
        bg_hex = to_tk_hex(self.bg_color)
        self._canvas.configure(background=bg_hex)
        self._scrollable_frame.configure(background=bg_hex)
        if hasattr(self, "_v_scrollbar") and self._v_scrollbar.winfo_exists():
            self._v_scrollbar.set_parent_bg(self.bg_color)
        cascade_bg_to_children(self._scrollable_frame, self.bg_color, palette=pal)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        cr = self._corner_radius * s
        bg_col = resolve_color_failsafe(self._custom_bg or pal.card_bg, palette=pal)
        border_col = resolve_color_failsafe(self._custom_border or pal.card_border, palette=pal)

        surf.clear(self._resolved_parent_bg)
        surf.fill_rounded_rect(0.0, 0.0, w, h, cr, cr, bg_col)
        if self._border_width > 0.0:
            surf.stroke_rounded_rect(0.0, 0.0, w, h, cr, cr, border_col, stroke_width=self._border_width * s)


# Aliases
ScrollBar = VectorScrollbar
