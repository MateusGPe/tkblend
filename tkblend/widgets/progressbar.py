"""
Pure Blend2D Vector ProgressBar powered by NativeController.
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
    DEFAULT_PROGRESS_WIDTH,
    DEFAULT_PROGRESS_HEIGHT,
    DEFAULT_PROGRESS_DETERMINATE_SPEED,
    DEFAULT_PROGRESS_INDETERMINATE_SPEED,
    DEFAULT_PROGRESS_BORDER_WIDTH,
    DEFAULT_PROGRESS_STEP_AMOUNT,
    PROGRESS_ANIM_INTERVAL_MS,
    PROGRESS_INDETERMINATE_PHASE_STEP,
    PROGRESS_DETERMINATE_AUTO_STEP,
    STATE_NORMAL,
    CURSOR_DEFAULT,
)
from tkblend.widgets.utils import (
    bind_variable_trace,
    unbind_variable_trace,
)


class ProgressBar(BaseControl):
    """
    Modern vector progress bar with determinate and indeterminate modes,
    continuous 60fps marquee animation, and Tk variable synchronization.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = DEFAULT_PROGRESS_WIDTH,
        height: int = DEFAULT_PROGRESS_HEIGHT,
        value: float = 0.0,
        corner_radius: Optional[float] = None,
        mode: str = "determinate",
        determinate_speed: float = DEFAULT_PROGRESS_DETERMINATE_SPEED,
        indeterminate_speed: float = DEFAULT_PROGRESS_INDETERMINATE_SPEED,
        track_color: Optional[ColorLike] = None,
        progress_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = DEFAULT_PROGRESS_BORDER_WIDTH,
        variable: Optional[Union[tk.DoubleVar, tk.IntVar, tk.Variable]] = None,
        animated: bool = True,
        cursor: Optional[str] = None,
        state: str = STATE_NORMAL,
        inner_bg: Optional[str] = None,
        outer_bg: Optional[str] = None,
        parent_bg: Optional[str] = None,
        bg_color: Optional[str] = None,
        **kwargs,
    ):
        self._mode = mode.lower()
        self._determinate_speed = float(determinate_speed)
        self._indeterminate_speed = float(indeterminate_speed)
        self._corner_radius = corner_radius

        self._custom_track_color = track_color
        self._custom_progress_color = progress_color
        self._custom_border_color = border_color
        self._border_width = float(border_width)

        self._variable = variable
        self._animated = animated

        self._progress = max(0.0, min(1.0, float(value)))
        self._phase_offset = 0.0
        self._running = False
        self._timer_id: Optional[str] = None

        if self._variable is not None:
            try:
                self._progress = max(0.0, min(1.0, float(self._variable.get())))
            except Exception:
                pass
            self._var_trace_id = bind_variable_trace(self._variable, self._on_variable_write)
        else:
            self._var_trace_id = None

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or CURSOR_DEFAULT,
            state=state,
            takefocus=False,
            inner_bg=inner_bg,
            outer_bg=outer_bg,
            parent_bg=parent_bg,
            bg_color=bg_color,
            **kwargs,
        )

        self.add_class("progressbar")
        self.add_class(self._mode)
        self._update_progress_vars()

    def _update_progress_vars(self) -> None:
        pal = self._palette
        track_col = resolve_color_failsafe(self._custom_track_color or pal.track_bg, palette=pal)
        prog_col = resolve_color_failsafe(self._custom_progress_color or pal.primary, palette=pal)

        self.set_var("--track-bg", track_col)
        self.set_var("--progress-bg", prog_col)
        self.set_var("--progress", str(self._progress))

    def _default_inner_bg(self, pal: Palette) -> str:
        return pal.track_bg

    def _on_variable_write(self, *args) -> None:
        if self._variable is not None:
            try:
                val = max(0.0, min(1.0, float(self._variable.get())))
                if val != self._progress:
                    self._progress = val
                    self.set_var("--progress", str(self._progress))
                    self.request_redraw()
            except Exception:
                pass

    def get(self) -> float:
        return self._progress

    def set(self, value: float) -> None:
        self._progress = max(0.0, min(1.0, float(value)))
        self.set_var("--progress", str(self._progress))
        if self._variable is not None:
            self._variable.set(self._progress)
        self.request_redraw()

    def step(self, amount: float = DEFAULT_PROGRESS_STEP_AMOUNT) -> None:
        new_val = (self._progress + amount) % 1.000001
        self.set(new_val)

    def start(self, interval_ms: int = PROGRESS_ANIM_INTERVAL_MS) -> None:
        """Start marquee animation for indeterminate mode or continuous spinning."""
        if self._running:
            return
        self._running = True
        self._loop_animation(interval_ms)

    def stop(self) -> None:
        """Stop animation loop."""
        self._running = False
        if self._timer_id is not None:
            try:
                self.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None

    def _loop_animation(self, interval_ms: int) -> None:
        if not self._running or not self.winfo_exists():
            return

        if self._mode == "indeterminate":
            self._phase_offset = (self._phase_offset + PROGRESS_INDETERMINATE_PHASE_STEP * self._indeterminate_speed) % 1.0
            self.request_redraw()
        elif self._mode == "determinate":
            self.step(PROGRESS_DETERMINATE_AUTO_STEP * self._determinate_speed)

        self._timer_id = self.after(interval_ms, lambda: self._loop_animation(interval_ms))

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        rx = (self._corner_radius * s) if self._corner_radius is not None else (h / 2.0)
        ry = rx

        track_bg = resolve_color_failsafe(self._custom_track_color or self.inner_bg or pal.track_bg, palette=pal)
        bar_bg = resolve_color_failsafe(self._custom_progress_color or pal.primary, palette=pal)

        # Clear outer background
        surf.clear(self.outer_bg)
        if self.is_disabled:
            track_bg = resolve_color_failsafe(pal.surface_border, palette=pal)
            bar_bg = resolve_color_failsafe(pal.text_muted, palette=pal)

        is_indet = (self._mode == "indeterminate")

        # Native progress bar call
        surf.draw_progress_bar(
            0.0,
            0.0,
            w,
            h,
            rx=rx,
            ry=ry,
            track_bg=track_bg,
            bar_bg=bar_bg,
            progress_t=self._progress,
            is_indeterminate=is_indet,
            phase_offset=self._phase_offset,
        )

        # Border
        bw = self._border_width * s
        if bw > 0.0:
            bc = resolve_color_failsafe(self._custom_border_color or pal.card_border, palette=pal)
            surf.stroke_rounded_rect(0.0, 0.0, w, h, rx, ry, bc, stroke_width=bw)

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)
        if "mode" in kwargs:
            self._mode = str(kwargs.pop("mode")).lower()
        if "variable" in kwargs:
            new_var = kwargs.pop("variable")
            if self._var_trace_id is not None and self._variable is not None:
                unbind_variable_trace(self._variable, self._var_trace_id)
            self._variable = new_var
            if self._variable is not None:
                try:
                    self._progress = max(0.0, min(1.0, float(self._variable.get())))
                except Exception:
                    pass
                self._var_trace_id = bind_variable_trace(self._variable, self._on_variable_write)
            else:
                self._var_trace_id = None
        return super().configure(**kwargs)
