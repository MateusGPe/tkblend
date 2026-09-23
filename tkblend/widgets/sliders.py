"""
Interactive slider widgets: Slider (single thumb) and RangeSlider (dual thumb interval selector).
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, Tuple

from tkblend.surface import ColorLike
from tkblend.theme import get_theme
from tkblend.widgets.base import Widget, ScalingTracker


class Slider(Widget):
    """
    Smooth interactive slider with custom groove track, active fill, and glowing knob.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 28,
        min_val: float = 0.0,
        max_val: float = 100.0,
        value: float = 50.0,
        on_change: Optional[Callable[[float], None]] = None,
        track_color: Optional[ColorLike] = None,
        active_track_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        knob_radius: float = 9.0,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._min = min_val
        self._max = max_val
        self._value = max(min_val, min(max_val, float(value)))
        self._on_change = on_change
        pal = get_theme()
        self._track_color = track_color or pal.track_bg
        self._active_track_color = active_track_color or pal.primary
        self._knob_color = knob_color or "#f5e0dc"
        scale = ScalingTracker.get_scaling_factor(master)
        self._knob_r = knob_radius * scale
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Button-1>", self._on_drag)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = max(self._min, min(self._max, float(val)))
        self.render()

    def set_value(self, val: float) -> None:
        self.value = val

    def _on_drag(self, event) -> None:
        pad = self._knob_r + 4.0 * self._scale
        usable_w = self._widget_w - pad * 2.0
        if usable_w > 0:
            rel = max(0.0, min(1.0, (event.x - pad) / usable_w))
            self._value = self._min + rel * (self._max - self._min)
            self.render()
            if self._on_change:
                self._on_change(self._value)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        pad = self._knob_r + 4.0 * self._scale
        track_h = 6.0 * self._scale
        track_y = (self._widget_h - track_h) / 2.0
        usable_w = self._widget_w - pad * 2.0

        self._surface.fill_rounded_rect(
            pad, track_y, usable_w, track_h, track_h / 2.0, track_h / 2.0, self._track_color
        )

        rel = (self._value - self._min) / (self._max - self._min) if self._max > self._min else 0.0
        knob_cx = pad + rel * usable_w
        if rel > 0.0:
            self._surface.fill_rounded_rect(
                pad, track_y, rel * usable_w, track_h, track_h / 2.0, track_h / 2.0, self._active_track_color
            )

        self._surface.draw_shadow(
            knob_cx - self._knob_r,
            (self._widget_h / 2.0) - self._knob_r,
            self._knob_r * 2.0,
            self._knob_r * 2.0,
            self._knob_r,
            self._knob_r,
            blur_radius=6.0 * self._scale,
            offset_y=2.0 * self._scale,
            shadow_color="#00000066",
        )

        self._surface.fill_circle(knob_cx, self._widget_h / 2.0, self._knob_r, self._knob_color)
        self._surface.stroke_circle(knob_cx, self._widget_h / 2.0, self._knob_r, "#ffffff88", stroke_width=1.5)
        self._surface.blit(self._photo)


ModernSlider = Slider


class RangeSlider(Widget):
    """
    Dual-thumb vector range slider for selecting a sub-interval [low, high].
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 28,
        min_val: float = 0.0,
        max_val: float = 100.0,
        low_val: float = 20.0,
        high_val: float = 80.0,
        on_change: Optional[Callable[[float, float], None]] = None,
        track_color: Optional[ColorLike] = None,
        active_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._min = min_val
        self._max = max_val
        self._low = max(min_val, min(max_val, float(low_val)))
        self._high = max(self._low, min(max_val, float(high_val)))
        self._on_change = on_change
        pal = get_theme()
        self._track_color = track_color or pal.track_bg
        self._active_color = active_color or pal.success
        self._knob_color = knob_color or "#f5e0dc"
        scale = ScalingTracker.get_scaling_factor(master)
        self._knob_r = 8.5 * scale
        self._dragging_thumb: Optional[str] = None

        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

        self.bind("<Button-1>", self._on_press_event)
        self.bind("<B1-Motion>", self._on_drag_event)
        self.bind("<ButtonRelease-1>", self._on_release_event)

    @property
    def range(self) -> Tuple[float, float]:
        return (self._low, self._high)

    def _val_to_x(self, val: float, pad: float, usable_w: float) -> float:
        rel = (val - self._min) / (self._max - self._min) if self._max > self._min else 0.0
        return pad + rel * usable_w

    def _x_to_val(self, x: float, pad: float, usable_w: float) -> float:
        rel = max(0.0, min(1.0, (x - pad) / usable_w)) if usable_w > 0 else 0.0
        return self._min + rel * (self._max - self._min)

    def _on_press_event(self, event) -> None:
        pad = self._knob_r + 4.0 * self._scale
        usable_w = self._widget_w - pad * 2.0
        low_x = self._val_to_x(self._low, pad, usable_w)
        high_x = self._val_to_x(self._high, pad, usable_w)

        d_low = abs(event.x - low_x)
        d_high = abs(event.x - high_x)
        self._dragging_thumb = "low" if d_low <= d_high else "high"
        self._on_drag_event(event)

    def _on_drag_event(self, event) -> None:
        pad = self._knob_r + 4.0 * self._scale
        usable_w = self._widget_w - pad * 2.0
        val = self._x_to_val(event.x, pad, usable_w)

        if self._dragging_thumb == "low":
            self._low = max(self._min, min(self._high - 1.0, val))
        elif self._dragging_thumb == "high":
            self._high = min(self._max, max(self._low + 1.0, val))

        self.render()
        if self._on_change:
            self._on_change(self._low, self._high)

    def _on_release_event(self, event) -> None:
        self._dragging_thumb = None

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        pad = self._knob_r + 4.0 * self._scale
        track_h = 6.0 * self._scale
        track_y = (self._widget_h - track_h) / 2.0
        usable_w = self._widget_w - pad * 2.0

        self._surface.fill_rounded_rect(
            pad, track_y, usable_w, track_h, track_h / 2.0, track_h / 2.0, self._track_color
        )

        low_x = self._val_to_x(self._low, pad, usable_w)
        high_x = self._val_to_x(self._high, pad, usable_w)

        if high_x > low_x:
            self._surface.fill_rounded_rect(
                low_x, track_y, high_x - low_x, track_h, track_h / 2.0, track_h / 2.0, self._active_color
            )

        for cx in (low_x, high_x):
            self._surface.draw_shadow(
                cx - self._knob_r,
                (self._widget_h / 2.0) - self._knob_r,
                self._knob_r * 2.0,
                self._knob_r * 2.0,
                self._knob_r,
                self._knob_r,
                blur_radius=5.0 * self._scale,
                offset_y=1.5 * self._scale,
                shadow_color="#00000066",
            )
            self._surface.fill_circle(cx, self._widget_h / 2.0, self._knob_r, self._knob_color)
            self._surface.stroke_circle(cx, self._widget_h / 2.0, self._knob_r, "#ffffff88", stroke_width=1.2)

        self._surface.blit(self._photo)


ModernRangeSlider = RangeSlider
