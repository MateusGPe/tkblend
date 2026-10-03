"""
Pure Blend2D Vector Slider powered by NativeController.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
)
from tkblend.widgets.constants import (
    DEFAULT_SLIDER_WIDTH,
    DEFAULT_SLIDER_HEIGHT,
    DEFAULT_SLIDER_FROM,
    DEFAULT_SLIDER_TO,
    DEFAULT_SLIDER_VALUE,
    DEFAULT_SLIDER_THUMB_RADIUS,
    DEFAULT_SLIDER_TRACK_THICKNESS,
    DEFAULT_SLIDER_ORIENTATION,
    SLIDER_TRACK_PADDING_EXTRA,
    SLIDER_KEY_STEP_RATIO,
    SLIDER_VERTICAL_SHADOW_OFFSET_Y,
    SLIDER_VERTICAL_SHADOW_BLUR,
    SLIDER_VERTICAL_SHADOW_COLOR,
    SLIDER_VERTICAL_BORDER_WIDTH,
    SLIDER_VERTICAL_FOCUS_RING_OFFSET,
    FOCUS_RING_WIDTH,
    FALLBACK_THUMB_COLOR,
    CURSOR_HAND,
    STATE_NORMAL,
    COLOR_TRANSPARENT,
)
from tkblend.widgets.utils import (
    draw_circular_focus_ring,
    bind_variable_trace,
    unbind_variable_trace,
)


class Slider(BaseControl):
    """
    Modern vector slider with smooth thumb dragging, discrete step quantization,
    keyboard navigation, and Tk variable synchronization.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        from_: float = DEFAULT_SLIDER_FROM,
        to: float = DEFAULT_SLIDER_TO,
        number_of_steps: Optional[int] = None,
        value: float = DEFAULT_SLIDER_VALUE,
        command: Optional[Callable[[float], None]] = None,
        variable: Optional[Union[tk.DoubleVar, tk.IntVar, tk.Variable]] = None,
        width: int = DEFAULT_SLIDER_WIDTH,
        height: int = DEFAULT_SLIDER_HEIGHT,
        orientation: str = DEFAULT_SLIDER_ORIENTATION,
        track_color: Optional[ColorLike] = None,
        active_color: Optional[ColorLike] = None,
        thumb_color: Optional[ColorLike] = None,
        thumb_border_color: Optional[ColorLike] = None,
        thumb_radius: float = DEFAULT_SLIDER_THUMB_RADIUS,
        track_thickness: float = DEFAULT_SLIDER_TRACK_THICKNESS,
        focus_ring: bool = True,
        focus_ring_color: Optional[ColorLike] = None,
        animated: bool = True,
        cursor: str = CURSOR_HAND,
        state: str = STATE_NORMAL,
        **kwargs,
    ):
        self._from = float(from_)
        self._to = float(to)
        self._number_of_steps = number_of_steps
        self._command = command
        self._variable = variable
        self._orientation = orientation.lower()

        self._custom_track_color = track_color
        self._custom_active_color = active_color
        self._custom_thumb_color = thumb_color
        self._custom_thumb_border = thumb_border_color
        self._thumb_radius = float(thumb_radius)
        self._track_thickness = float(track_thickness)

        self._focus_ring = focus_ring
        self._custom_focus_ring_color = focus_ring_color
        self._animated = animated

        self._is_dragging = False
        self._value = float(value if value != DEFAULT_SLIDER_VALUE else from_)

        # Variable synchronization
        if self._variable is not None:
            try:
                self._value = float(self._variable.get())
            except Exception:
                pass
            self._var_trace_id = bind_variable_trace(self._variable, self._on_variable_write)
        else:
            self._var_trace_id = None

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor,
            state=state,
            takefocus=True,
            **kwargs,
        )

        # Mouse Drag Event Bindings
        self.bind("<ButtonPress-1>", self._on_mouse_press, add="+")
        self.bind("<B1-Motion>", self._on_mouse_drag, add="+")
        self.bind("<ButtonRelease-1>", self._on_mouse_release, add="+")

    def _on_variable_write(self, *args) -> None:
        if self._variable is not None and not self._is_dragging:
            try:
                val = float(self._variable.get())
                if val != self._value:
                    self._value = val
                    self.request_redraw()
            except Exception:
                pass

    def _quantize_value(self, val: float) -> float:
        min_v = min(self._from, self._to)
        max_v = max(self._from, self._to)
        clamped = max(min_v, min(max_v, val))
        if self._number_of_steps is not None and self._number_of_steps > 0:
            step_sz = (max_v - min_v) / float(self._number_of_steps)
            step_idx = round((clamped - min_v) / step_sz)
            return min_v + step_idx * step_sz
        return clamped

    def get(self) -> float:
        return self._value

    def set(self, value: float) -> None:
        self._value = self._quantize_value(float(value))
        if self._variable is not None:
            self._variable.set(self._value)
        self.request_redraw()

    def _value_to_progress(self) -> float:
        rng = self._to - self._from
        if rng == 0.0:
            return 0.0
        return (self._value - self._from) / rng

    def _progress_to_value(self, progress: float) -> float:
        p = max(0.0, min(1.0, progress))
        return self._from + p * (self._to - self._from)

    def _update_from_mouse(self, event_x: int, event_y: int) -> None:
        s = self.scale_factor
        w = max(1.0, float(self.winfo_width()))
        h = max(1.0, float(self.winfo_height()))
        pad = (self._thumb_radius + SLIDER_TRACK_PADDING_EXTRA) * s

        if self._orientation == "vertical":
            track_len = max(1.0, h - 2.0 * pad)
            # Invert Y so bottom is min, top is max
            progress = 1.0 - ((float(event_y) - pad) / track_len)
        else:
            track_len = max(1.0, w - 2.0 * pad)
            progress = (float(event_x) - pad) / track_len

        new_val = self._quantize_value(self._progress_to_value(progress))
        if new_val != self._value:
            self._value = new_val
            if self._variable is not None:
                self._variable.set(self._value)
            if self._command is not None:
                self._command(self._value)
            self.request_redraw()

    def _on_mouse_press(self, event: tk.Event) -> None:
        if self.is_disabled:
            return
        self.focus_set()
        self._is_dragging = True
        self._update_from_mouse(event.x, event.y)

    def _on_mouse_drag(self, event: tk.Event) -> None:
        if self.is_disabled or not self._is_dragging:
            return
        self._update_from_mouse(event.x, event.y)

    def _on_mouse_release(self, event: tk.Event) -> None:
        self._is_dragging = False
        self.request_redraw()

    def on_key_press(self, event: tk.Event) -> None:
        if self.is_disabled:
            return
        rng = abs(self._to - self._from)
        step = (rng / float(self._number_of_steps)) if (self._number_of_steps and self._number_of_steps > 0) else (rng * SLIDER_KEY_STEP_RATIO)

        if event.keysym in ("Left", "Down"):
            self.set(self._value - step)
            if self._command is not None:
                self._command(self._value)
        elif event.keysym in ("Right", "Up"):
            self.set(self._value + step)
            if self._command is not None:
                self._command(self._value)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        pad = (self._thumb_radius + SLIDER_TRACK_PADDING_EXTRA) * s
        prog = self._value_to_progress()

        track_bg = resolve_color_failsafe(self._custom_track_color or pal.track_bg, palette=pal)
        active_bg = resolve_color_failsafe(self._custom_active_color or pal.primary, palette=pal)
        if self.is_disabled:
            track_bg = resolve_color_failsafe(pal.surface_border, palette=pal)
            active_bg = resolve_color_failsafe(pal.text_muted, palette=pal)

        thumb_col = resolve_color_failsafe(self._custom_thumb_color or pal.primary, palette=pal)
        thumb_border = resolve_color_failsafe(self._custom_thumb_border or FALLBACK_THUMB_COLOR, palette=pal)
        if self.is_disabled:
            thumb_col = resolve_color_failsafe(pal.surface, palette=pal)
            thumb_border = resolve_color_failsafe(pal.surface_border, palette=pal)

        fr_col = resolve_color_failsafe(self._custom_focus_ring_color or pal.input_focus, palette=pal) if (self._focus_ring and self.is_focused and not self.is_disabled) else COLOR_TRANSPARENT
        fr_w = FOCUS_RING_WIDTH * s if (self._focus_ring and self.is_focused and not self.is_disabled) else 0.0

        if self._orientation == "horizontal":
            track_w = max(1.0, w - 2.0 * pad)
            surf.draw_slider(
                pad,
                0.0,
                track_w,
                h,
                track_bg=track_bg,
                active_bg=active_bg,
                thumb_color=thumb_col,
                thumb_border_color=thumb_border,
                value_t=prog,
                track_thickness=self._track_thickness * s,
                thumb_radius=self._thumb_radius * s,
                is_hovered=self.is_hovered,
                is_dragging=self._is_dragging,
                focus_ring_color=fr_col,
                focus_ring_width=fr_w,
            )
        else:
            # Vertical orientation
            track_h = max(1.0, h - 2.0 * pad)
            th = self._track_thickness * s
            tr = self._thumb_radius * s
            cx = w / 2.0
            track_x = cx - th / 2.0
            track_y = pad

            # Track background
            surf.fill_rounded_rect(track_x, track_y, th, track_h, th / 2.0, th / 2.0, track_bg)

            # Active segment (from bottom up)
            active_h = track_h * prog
            if active_h > 0.0:
                surf.fill_rounded_rect(track_x, track_y + track_h - active_h, th, active_h, th / 2.0, th / 2.0, active_bg)

            # Thumb
            thumb_cy = track_y + track_h * (1.0 - prog)
            surf.draw_shadow(
                cx - tr,
                thumb_cy - tr + SLIDER_VERTICAL_SHADOW_OFFSET_Y * s,
                tr * 2.0,
                tr * 2.0,
                tr,
                tr,
                blur_radius=SLIDER_VERTICAL_SHADOW_BLUR * s,
                shadow_color=SLIDER_VERTICAL_SHADOW_COLOR,
            )
            surf.fill_circle(cx, thumb_cy, tr, thumb_col)
            surf.stroke_circle(cx, thumb_cy, tr, thumb_border, stroke_width=SLIDER_VERTICAL_BORDER_WIDTH * s)
            if self._focus_ring and self.is_focused and not self.is_disabled:
                draw_circular_focus_ring(
                    surf,
                    cx,
                    thumb_cy,
                    tr,
                    fr_col,
                    stroke_width=FOCUS_RING_WIDTH,
                    offset=SLIDER_VERTICAL_FOCUS_RING_OFFSET,
                    scale=s,
                )

    def configure(self, cnf=None, **kwargs):
        if cnf is None and not kwargs:
            return super().configure()
        if cnf:
            kwargs.update(cnf)

        if "from_" in kwargs:
            self._from = float(kwargs.pop("from_"))
        if "to" in kwargs:
            self._to = float(kwargs.pop("to"))
        if "number_of_steps" in kwargs:
            self._number_of_steps = kwargs.pop("number_of_steps")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "variable" in kwargs:
            new_var = kwargs.pop("variable")
            if self._var_trace_id is not None and self._variable is not None:
                unbind_variable_trace(self._variable, self._var_trace_id)
            self._variable = new_var
            if self._variable is not None:
                try:
                    self._value = float(self._variable.get())
                except Exception:
                    pass
                self._var_trace_id = bind_variable_trace(self._variable, self._on_variable_write)
            else:
                self._var_trace_id = None
        if "value" in kwargs:
            self.set(kwargs.pop("value"))
        self.request_redraw()
        return super().configure(**kwargs)
