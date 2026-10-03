"""
Pure Blend2D Vector Toggle Switch powered by NativeController.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    blend_color_hex,
)
from tkblend.font import parse_font
from tkblend.widgets.constants import (
    DEFAULT_SWITCH_WIDTH,
    DEFAULT_SWITCH_HEIGHT,
    DEFAULT_SWITCH_TRACK_WIDTH,
    DEFAULT_SWITCH_TRACK_HEIGHT,
    DEFAULT_SWITCH_LEFT_MARGIN,
    DEFAULT_SWITCH_TEXT_SPACING,
    DEFAULT_SWITCH_COMPACT_EXTRA_PAD,
    DEFAULT_FONT_SIZE,
    FOCUS_RING_WIDTH,
    SWITCH_ANIM_DURATION_MS,
    FALLBACK_THUMB_COLOR,
    FALLBACK_THUMB_BORDER_COLOR,
    CURSOR_HAND,
    STATE_NORMAL,
    COLOR_TRANSPARENT,
)
from tkblend.widgets.utils import (
    compute_text_baseline_y,
    bind_variable_trace,
    unbind_variable_trace,
)


class Switch(BaseControl):
    """
    Modern vector toggle switch with smooth sliding thumb animations,
    integrated text label, and Tk variable synchronization.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        command: Optional[Callable[[], None]] = None,
        variable: Optional[Union[tk.BooleanVar, tk.IntVar, tk.StringVar, tk.Variable]] = None,
        onvalue: Any = True,
        offvalue: Any = False,
        width: int = DEFAULT_SWITCH_WIDTH,
        height: int = DEFAULT_SWITCH_HEIGHT,
        switch_width: int = DEFAULT_SWITCH_TRACK_WIDTH,
        switch_height: int = DEFAULT_SWITCH_TRACK_HEIGHT,
        corner_radius: Optional[float] = None,
        track_color: Optional[ColorLike] = None,
        active_color: Optional[ColorLike] = None,
        thumb_color: Optional[ColorLike] = None,
        thumb_border_color: Optional[ColorLike] = None,
        fg_color: Optional[ColorLike] = None,
        font: Optional[Any] = None,
        font_size: Optional[float] = None,
        focus_ring: bool = True,
        focus_ring_color: Optional[ColorLike] = None,
        animated: bool = True,
        cursor: str = CURSOR_HAND,
        state: str = STATE_NORMAL,
        **kwargs,
    ):
        self._text = str(text)
        self._command = command
        self._variable = variable
        self._onvalue = onvalue
        self._offvalue = offvalue

        self._switch_w = int(switch_width)
        self._switch_h = int(switch_height)
        self._corner_radius = corner_radius

        self._custom_track_color = track_color
        self._custom_active_color = active_color
        self._custom_thumb_color = thumb_color
        self._custom_thumb_border = thumb_border_color
        self._custom_fg_color = fg_color

        self._font_spec = font
        self._font_size = font_size
        self._focus_ring = focus_ring
        self._custom_focus_ring_color = focus_ring_color

        self._animated = animated
        self._is_on = False
        self._progress_t = 0.0

        # Sync initial variable state if present
        if self._variable is not None:
            self._is_on = (self._variable.get() == self._onvalue)
            self._progress_t = 1.0 if self._is_on else 0.0
            self._var_trace_id = bind_variable_trace(self._variable, self._on_variable_write)
        else:
            self._var_trace_id = None

        # Determine default widget size
        eff_width = width if text else switch_width + DEFAULT_SWITCH_COMPACT_EXTRA_PAD

        super().__init__(
            master=master,
            width=eff_width,
            height=height,
            cursor=cursor,
            state=state,
            takefocus=True,
            **kwargs,
        )

    def _on_variable_write(self, *args) -> None:
        if self._variable is not None:
            val = self._variable.get()
            new_is_on = (val == self._onvalue)
            if new_is_on != self._is_on:
                self._is_on = new_is_on
                self._animate_to_state(new_is_on)

    def _animate_to_state(self, is_on: bool) -> None:
        target_t = 1.0 if is_on else 0.0
        if self._animated and self.winfo_exists():
            self.animate_property("thumb", self._progress_t, target_t, duration_ms=SWITCH_ANIM_DURATION_MS, on_update=self._set_progress_t)
        else:
            self._progress_t = target_t
            self.request_redraw()

    def _set_progress_t(self, val: float) -> None:
        self._progress_t = val

    def get(self) -> Any:
        return self._onvalue if self._is_on else self._offvalue

    def is_on(self) -> bool:
        return self._is_on

    def set(self, value: Any) -> None:
        self._is_on = (value == self._onvalue)
        if self._variable is not None:
            self._variable.set(self._onvalue if self._is_on else self._offvalue)
        self._animate_to_state(self._is_on)

    def select(self) -> None:
        self.set(self._onvalue)

    def deselect(self) -> None:
        self.set(self._offvalue)

    def toggle(self) -> None:
        if self.is_disabled:
            return
        self._is_on = not self._is_on
        if self._variable is not None:
            self._variable.set(self._onvalue if self._is_on else self._offvalue)
        self._animate_to_state(self._is_on)
        if self._command is not None:
            self._command()

    def on_click(self, x: int, y: int, button: int) -> None:
        if button == 1:
            self.toggle()

    def on_key_press(self, event: tk.Event) -> None:
        if event.keysym in ("space", "Return"):
            self.toggle()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        sw = float(self._switch_w) * s
        sh = float(self._switch_h) * s
        sy = (h - sh) / 2.0
        sx = DEFAULT_SWITCH_LEFT_MARGIN * s

        # Colors
        track_off = resolve_color_failsafe(self._custom_track_color or pal.track_bg, palette=pal)
        track_on = resolve_color_failsafe(self._custom_active_color or pal.primary, palette=pal)
        cur_track = blend_color_hex(track_off, track_on, self._progress_t) or track_off
        if self.is_disabled:
            cur_track = resolve_color_failsafe(pal.surface_border, palette=pal)

        thumb_col = resolve_color_failsafe(self._custom_thumb_color or FALLBACK_THUMB_COLOR, palette=pal)
        if self.is_disabled:
            thumb_col = resolve_color_failsafe(pal.text_muted, palette=pal)
        thumb_border = resolve_color_failsafe(self._custom_thumb_border or FALLBACK_THUMB_BORDER_COLOR, palette=pal)

        fr_col = resolve_color_failsafe(self._custom_focus_ring_color or pal.input_focus, palette=pal) if (self._focus_ring and self.is_focused and not self.is_disabled) else COLOR_TRANSPARENT
        fr_w = FOCUS_RING_WIDTH * s if (self._focus_ring and self.is_focused and not self.is_disabled) else 0.0

        # Draw native switch
        surf.draw_switch(
            sx,
            sy,
            sw,
            sh,
            track_color=cur_track,
            thumb_color=thumb_col,
            thumb_border_color=thumb_border,
            progress_t=self._progress_t,
            is_hovered=self.is_hovered,
            focus_ring_color=fr_col,
            focus_ring_width=fr_w,
        )

        # Draw label text if present
        if self._text:
            text_x = sx + sw + DEFAULT_SWITCH_TEXT_SPACING * s
            fg_col = resolve_color_failsafe(self._custom_fg_color or pal.fg, palette=pal)
            if self.is_disabled:
                fg_col = resolve_color_failsafe(pal.text_muted, palette=pal)

            font_cfg = parse_font(font=self._font_spec, font_size=self._font_size or DEFAULT_FONT_SIZE)
            scaled_font_sz = float(font_cfg.size) * s
            text_y = compute_text_baseline_y(h / 2.0, scaled_font_sz)

            surf.draw_text(
                self._text,
                text_x,
                text_y,
                font_size=scaled_font_sz,
                font_family=font_cfg.family,
                color=fg_col,
                bold=font_cfg.bold,
                italic=font_cfg.italic,
                weight=font_cfg.weight,
                align="left",
            )

    def configure(self, cnf=None, **kwargs):
        if cnf is None and not kwargs:
            return super().configure()
        if cnf:
            kwargs.update(cnf)

        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "variable" in kwargs:
            self._variable = kwargs.pop("variable")
        self.request_redraw()
        return super().configure(**kwargs)
