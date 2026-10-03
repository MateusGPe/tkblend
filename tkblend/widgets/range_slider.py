"""
Pure Blend2D Vector Dual-Handle RangeSlider powered by BaseControl.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Tuple, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    blend_color_hex,
)
from tkblend.widgets.constants import (
    CURSOR_HAND,
    CURSOR_DEFAULT,
)


class RangeSlider(BaseControl):
    """
    Modern dual-handle range slider with smooth continuous dragging,
    accent-filled active range segment, and glowing thumb knobs.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        from_: float = 0.0,
        to: float = 100.0,
        values: Tuple[float, float] = (25.0, 75.0),
        command: Optional[Callable[[Tuple[float, float]], None]] = None,
        active_color: Optional[ColorLike] = None,
        track_color: Optional[ColorLike] = None,
        thumb_color: Optional[ColorLike] = None,
        track_height: float = 6.0,
        thumb_radius: float = 9.0,
        width: int = 240,
        height: int = 32,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._from = float(from_)
        self._to = float(to)
        low, high = values
        self._low = max(self._from, min(self._to, float(low)))
        self._high = max(self._low, min(self._to, float(high)))

        self._command = command
        self._active_color = active_color
        self._track_color = track_color
        self._thumb_color = thumb_color
        self._track_height = float(track_height)
        self._thumb_radius = float(thumb_radius)

        self._dragging_thumb: Optional[str] = None  # 'low' or 'high'
        self._hover_thumb: Optional[str] = None

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or CURSOR_HAND,
            takefocus=True,
            **kwargs,
        )

        self.bind("<Button-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)

    def get(self) -> Tuple[float, float]:
        return (self._low, self._high)

    def set(self, low: float, high: float) -> None:
        self._low = max(self._from, min(self._to, float(low)))
        self._high = max(self._low, min(self._to, float(high)))
        self.request_redraw()

    def _val_to_x(self, val: float, w: float, pad: float) -> float:
        rng = max(0.0001, self._to - self._from)
        fraction = (val - self._from) / rng
        return pad + fraction * (w - pad * 2.0)

    def _x_to_val(self, x: float, w: float, pad: float) -> float:
        usable_w = max(1.0, w - pad * 2.0)
        rel_x = max(0.0, min(usable_w, x - pad))
        fraction = rel_x / usable_w
        return self._from + fraction * (self._to - self._from)

    def _on_press(self, event) -> None:
        if self.is_disabled:
            return
        w = float(self.winfo_width() or self._logical_w)
        s = self._scale_factor
        pad = self._thumb_radius * s + 4.0 * s
        x_low = self._val_to_x(self._low, w, pad)
        x_high = self._val_to_x(self._high, w, pad)

        d_low = abs(event.x - x_low)
        d_high = abs(event.x - x_high)

        if d_low <= d_high:
            self._dragging_thumb = "low"
            self._low = min(self._high, self._x_to_val(event.x, w, pad))
        else:
            self._dragging_thumb = "high"
            self._high = max(self._low, self._x_to_val(event.x, w, pad))

        self.request_redraw()
        if self._command:
            try:
                self._command(self.get())
            except Exception:
                pass

    def _on_drag(self, event) -> None:
        if self.is_disabled or not self._dragging_thumb:
            return
        w = float(self.winfo_width() or self._logical_w)
        s = self._scale_factor
        pad = self._thumb_radius * s + 4.0 * s
        val = self._x_to_val(event.x, w, pad)

        if self._dragging_thumb == "low":
            self._low = max(self._from, min(self._high, val))
        else:
            self._high = max(self._low, min(self._to, val))

        self.request_redraw()
        if self._command:
            try:
                self._command(self.get())
            except Exception:
                pass

    def _on_release(self, event) -> None:
        self._dragging_thumb = None
        self.request_redraw()

    def _on_motion(self, event) -> None:
        if self.is_disabled:
            return
        w = float(self.winfo_width() or self._logical_w)
        s = self._scale_factor
        pad = self._thumb_radius * s + 4.0 * s
        x_low = self._val_to_x(self._low, w, pad)
        x_high = self._val_to_x(self._high, w, pad)
        thresh = self._thumb_radius * s * 1.5

        if abs(event.x - x_low) <= thresh:
            new_hover = "low"
        elif abs(event.x - x_high) <= thresh:
            new_hover = "high"
        else:
            new_hover = None

        if new_hover != self._hover_thumb:
            self._hover_thumb = new_hover
            self.request_redraw()

    def _on_leave(self, event) -> None:
        if self._hover_thumb is not None:
            self._hover_thumb = None
            self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        cy = h / 2.0
        tr_h = self._track_height * s
        tr_r = tr_h / 2.0
        th_r = self._thumb_radius * s
        pad = th_r + 4.0 * s

        tr_col = resolve_color_failsafe(self._track_color or pal.track_bg, palette=pal)
        act_col = resolve_color_failsafe(self._active_color or pal.primary, palette=pal)
        th_col = resolve_color_failsafe(self._thumb_color or pal.thumb_color, palette=pal)

        # 1. Full track
        surf.clear(self._resolved_parent_bg)
        surf.fill_rounded_rect(pad, cy - tr_r, w - pad * 2.0, tr_h, tr_r, tr_r, tr_col)

        # 2. Highlighted range track
        x_low = self._val_to_x(self._low, w, pad)
        x_high = self._val_to_x(self._high, w, pad)
        if x_high > x_low:
            surf.fill_rounded_rect(x_low, cy - tr_r, x_high - x_low, tr_h, tr_r, tr_r, act_col)

        # 3. Low Thumb
        surf.fill_circle(x_low, cy, th_r, th_col)
        surf.stroke_circle(x_low, cy, th_r, act_col if self._hover_thumb == "low" or self._dragging_thumb == "low" else pal.card_border, stroke_width=2.0 * s)

        # 4. High Thumb
        surf.fill_circle(x_high, cy, th_r, th_col)
        surf.stroke_circle(x_high, cy, th_r, act_col if self._hover_thumb == "high" or self._dragging_thumb == "high" else pal.card_border, stroke_width=2.0 * s)
