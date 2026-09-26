"""
Interactive slider widgets: Slider (single thumb) and RangeSlider (dual thumb interval selector).
"""

from __future__ import annotations
import logging
import tkinter as tk
from typing import Optional, Callable, Tuple

from tkblend.surface import ColorLike
from tkblend.theme import get_theme, Palette, resolve_color_failsafe
from tkblend.widgets.base import Widget, ScalingTracker, _resolve_color

logger = logging.getLogger(__name__)


class Scale(Widget):
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
        from_: Optional[float] = None,
        to: Optional[float] = None,
        value: float = 50.0,
        on_change: Optional[Callable[[float], None]] = None,
        command: Optional[Callable[[float], None]] = None,
        track_color: Optional[ColorLike] = None,
        active_track_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        knob_radius: float = 9.0,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        if "from" in kwargs:
            from_ = kwargs.pop("from")
        if from_ is not None:
            min_val = float(from_)
        if to is not None:
            max_val = float(to)
        if command is not None:
            on_change = command

        self._min = min_val
        self._max = max_val
        self._value = max(min_val, min(max_val, float(value)))
        self._on_change = on_change
        self._explicit_track_color = track_color
        self._explicit_active_track_color = active_track_color
        self._explicit_knob_color = knob_color
        scale = ScalingTracker.get_scaling_factor(master)
        self._knob_r = knob_radius * scale
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Button-1>", self._on_drag)


    @property
    def track_color(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_track_color, pal.track_bg, pal)

    @track_color.setter
    def track_color(self, val: Optional[ColorLike]) -> None:
        self._explicit_track_color = val
        self.render()

    @property
    def _track_color(self) -> ColorLike:
        return self.track_color

    @property
    def active_track_color(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_active_track_color, pal.primary, pal)

    @active_track_color.setter
    def active_track_color(self, val: Optional[ColorLike]) -> None:
        self._explicit_active_track_color = val
        self.render()

    @property
    def _active_track_color(self) -> ColorLike:
        return self.active_track_color

    @property
    def knob_color(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_knob_color, pal.thumb_color, pal)

    @knob_color.setter
    def knob_color(self, val: Optional[ColorLike]) -> None:
        self._explicit_knob_color = val
        self.render()

    @property
    def _knob_color(self) -> ColorLike:
        return self.knob_color

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = max(self._min, min(self._max, float(val)))
        self.render()

    def get(self) -> float:
        """Get current slider value (Tkinter compatible)."""
        return self._value

    def get_value(self) -> float:
        """Get current slider value."""
        return self._value

    def set(self, val: float) -> None:
        """Set slider value (Tkinter compatible)."""
        self.value = val

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
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            pad = self._knob_r + 4.0 * self._scale
            track_h = 6.0 * self._scale
            usable_w = max(1.0, self._widget_w - pad * 2.0)

            pal = get_theme()
            track_col = _resolve_color(self._explicit_track_color, pal.track_bg, pal)
            active_col = _resolve_color(self._explicit_active_track_color, pal.primary, pal)
            knob_col = _resolve_color(self._explicit_knob_color, pal.thumb_color, pal)
            border_col = "#ffffff88" if pal.dark_mode else "#00000018"

            rel = (self._value - self._min) / (self._max - self._min) if self._max > self._min else 0.0

            focus_col = pal.input_focus if self._has_focus else "#00000000"
            focus_width = 1.5 * self._scale if self._has_focus else 0.0

            self._surface.draw_slider(
                x=pad,
                y=0,
                w=usable_w,
                h=self._widget_h,
                track_bg=track_col,
                active_bg=active_col,
                thumb_color=knob_col,
                thumb_border_color=border_col,
                value_t=rel,
                track_thickness=track_h,
                thumb_radius=self._knob_r,
                is_hovered=self._is_hovered,
                is_dragging=self._is_pressed,
                focus_ring_color=focus_col,
                focus_ring_width=focus_width,
            )
            self._surface.blit(self._photo)
        except Exception as e:
            logger.debug("Render failed in Slider: %s", e, exc_info=True)


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
        from_: Optional[float] = None,
        to: Optional[float] = None,
        low_value: Optional[float] = None,
        high_value: Optional[float] = None,
        on_change: Optional[Callable[[float, float], None]] = None,
        track_color: Optional[ColorLike] = None,
        active_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._min = from_ if from_ is not None else min_val
        self._max = to if to is not None else max_val
        eff_low = low_value if low_value is not None else low_val
        eff_high = high_value if high_value is not None else high_val
        self._low = max(self._min, min(self._max, float(eff_low)))
        self._high = max(self._low, min(self._max, float(eff_high)))
        self._on_change = on_change
        self._explicit_track_color = track_color
        self._explicit_active_color = active_color
        self._explicit_knob_color = knob_color
        scale = ScalingTracker.get_scaling_factor(master)
        self._knob_r = 8.5 * scale
        self._dragging_thumb: Optional[str] = None

        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

        self.bind("<Button-1>", self._on_press_event)
        self.bind("<B1-Motion>", self._on_drag_event)
        self.bind("<ButtonRelease-1>", self._on_release_event)

    @property
    def track_color(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_track_color, pal.track_bg, pal)

    @track_color.setter
    def track_color(self, val: Optional[ColorLike]) -> None:
        self._explicit_track_color = val
        self.render()

    @property
    def _track_color(self) -> ColorLike:
        return self.track_color

    @property
    def active_color(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_active_color, pal.success, pal)

    @active_color.setter
    def active_color(self, val: Optional[ColorLike]) -> None:
        self._explicit_active_color = val
        self.render()

    @property
    def _active_color(self) -> ColorLike:
        return self.active_color

    @property
    def knob_color(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_knob_color, pal.thumb_color, pal)

    @knob_color.setter
    def knob_color(self, val: Optional[ColorLike]) -> None:
        self._explicit_knob_color = val
        self.render()

    @property
    def _knob_color(self) -> ColorLike:
        return self.knob_color

    @property
    def range(self) -> Tuple[float, float]:
        return (self._low, self._high)

    def get(self) -> Tuple[float, float]:
        """Get current (low, high) range values."""
        return (self._low, self._high)

    def get_values(self) -> Tuple[float, float]:
        """Get current (low, high) range values."""
        return (self._low, self._high)

    def set_values(self, low: float, high: float) -> None:
        """Set (low, high) range values."""
        self._low = max(self._min, min(self._max, float(low)))
        self._high = max(self._min, min(self._max, float(high)))
        if self._low > self._high:
            self._low, self._high = self._high, self._low
        self.render()

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
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            pad = self._knob_r + 4.0 * self._scale
            track_h = 6.0 * self._scale
            track_y = (self._widget_h - track_h) / 2.0
            usable_w = max(1.0, self._widget_w - pad * 2.0)

            pal = get_theme()
            track_col = _resolve_color(self._explicit_track_color, pal.track_bg, pal)
            active_col = _resolve_color(self._explicit_active_color, pal.success, pal)
            knob_col = _resolve_color(self._explicit_knob_color, pal.thumb_color, pal)
            shadow_col = pal.shadow_color
            border_col = "#ffffff88" if pal.dark_mode else "#00000018"

            self._surface.fill_rounded_rect(
                pad, track_y, usable_w, track_h, track_h / 2.0, track_h / 2.0, track_col
            )

            low_x = self._val_to_x(self._low, pad, usable_w)
            high_x = self._val_to_x(self._high, pad, usable_w)

            if high_x > low_x:
                self._surface.fill_rounded_rect(
                    low_x, track_y, high_x - low_x, track_h, track_h / 2.0, track_h / 2.0, active_col
                )

            v_margin = max(1.0, (self._widget_h / 2.0) - self._knob_r)
            safe_blur = min(2.5 * self._scale, v_margin * 0.65)
            safe_offset_y = min(0.8 * self._scale, v_margin * 0.25)
            for cx in (low_x, high_x):
                self._surface.draw_shadow(
                    cx - self._knob_r,
                    (self._widget_h / 2.0) - self._knob_r,
                    self._knob_r * 2.0,
                    self._knob_r * 2.0,
                    self._knob_r,
                    self._knob_r,
                    blur_radius=safe_blur,
                    offset_y=safe_offset_y,
                    shadow_color=shadow_col,
                )
                self._surface.fill_circle(cx, self._widget_h / 2.0, self._knob_r, knob_col)
                self._surface.stroke_circle(cx, self._widget_h / 2.0, self._knob_r, border_col, stroke_width=1.2)

            self._surface.blit(self._photo)
        except Exception as e:
            logger.debug("Render failed in RangeSlider: %s", e, exc_info=True)




Slider = Scale
