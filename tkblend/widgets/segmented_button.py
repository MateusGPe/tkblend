"""
Pure Blend2D Vector SegmentedButton and SegmentedControl powered by BaseControl.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, List, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    blend_color_hex,
)
from tkblend.font import parse_font
from tkblend.widgets.constants import (
    DEFAULT_FONT_SIZE,
    CURSOR_HAND,
    CURSOR_DEFAULT,
)
from tkblend.widgets.utils import compute_text_baseline_y


class SegmentedButton(BaseControl):
    """
    Modern iOS / Fluent style segmented pill switcher with recessed track,
    elevated active segment indicator, and hover states.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        values: Optional[List[str]] = None,
        selected_index: int = 0,
        selected_value: Optional[str] = None,
        command: Optional[Callable[[str], None]] = None,
        on_change: Optional[Callable[[str], None]] = None,
        active_color: Optional[ColorLike] = None,
        track_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        active_text_color: Optional[ColorLike] = None,
        corner_radius: Optional[float] = None,
        font_size: float = 12.0,
        bold: bool = False,
        width: int = 280,
        height: int = 36,
        cursor: Optional[str] = None,
        inner_bg: Optional[str] = None,
        outer_bg: Optional[str] = None,
        parent_bg: Optional[str] = None,
        bg_color: Optional[str] = None,
        **kwargs,
    ):
        raw_vals = values or ["Option 1", "Option 2"]
        self._values = [str(v) for v in raw_vals]
        self._command = command or on_change
        self._active_color = active_color
        self._track_color = track_color
        self._text_color = text_color
        self._active_text_color = active_text_color
        self._corner_radius = corner_radius
        self._font_size = float(font_size)
        self._bold = bold

        if selected_value is not None and selected_value in self._values:
            self._selected = self._values.index(selected_value)
        else:
            self._selected = max(0, min(len(self._values) - 1, selected_index))

        self._hovered_idx: Optional[int] = None

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or CURSOR_HAND,
            takefocus=True,
            inner_bg=inner_bg,
            outer_bg=outer_bg,
            parent_bg=parent_bg,
            bg_color=bg_color,
            **kwargs,
        )

        self.bind("<Button-1>", self._on_click)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Left>", self._on_key_left)
        self.bind("<Right>", self._on_key_right)

    def _default_inner_bg(self, pal: Palette) -> str:
        return pal.track_bg

    @property
    def values(self) -> List[str]:
        return self._values

    @values.setter
    def values(self, vals: List[str]) -> None:
        self._values = [str(v) for v in vals]
        if self._selected >= len(self._values):
            self._selected = max(0, len(self._values) - 1)
        self.request_redraw()

    def get(self) -> str:
        if 0 <= self._selected < len(self._values):
            return self._values[self._selected]
        return ""

    def set(self, val: Union[str, int]) -> None:
        if isinstance(val, int):
            self._selected = max(0, min(len(self._values) - 1, val))
        elif isinstance(val, str) and val in self._values:
            self._selected = self._values.index(val)
        self.request_redraw()

    @property
    def selected_index(self) -> int:
        return self._selected

    @selected_index.setter
    def selected_index(self, idx: int) -> None:
        self.set(idx)

    def _get_segment_idx_at(self, x: float) -> Optional[int]:
        if not self._values:
            return None
        w = float(self.winfo_width() or self._logical_w)
        seg_w = w / len(self._values)
        if 0 <= x <= w:
            idx = int(x // seg_w)
            return max(0, min(len(self._values) - 1, idx))
        return None

    def _on_click(self, event) -> None:
        if self.is_disabled:
            return
        idx = self._get_segment_idx_at(event.x)
        if idx is not None and idx != self._selected:
            self._selected = idx
            self.request_redraw()
            if self._command:
                try:
                    self._command(self._values[idx])
                except Exception:
                    pass

    def _on_motion(self, event) -> None:
        if self.is_disabled:
            return
        idx = self._get_segment_idx_at(event.x)
        if idx != self._hovered_idx:
            self._hovered_idx = idx
            self.request_redraw()

    def _on_leave(self, event) -> None:
        if self._hovered_idx is not None:
            self._hovered_idx = None
            self.request_redraw()

    def _on_key_left(self, event) -> None:
        if self.is_disabled or not self._values:
            return
        self.set(max(0, self._selected - 1))
        if self._command:
            try:
                self._command(self.get())
            except Exception:
                pass

    def _on_key_right(self, event) -> None:
        if self.is_disabled or not self._values:
            return
        self.set(min(len(self._values) - 1, self._selected + 1))
        if self._command:
            try:
                self._command(self.get())
            except Exception:
                pass

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        n = len(self._values)
        if n == 0:
            return

        cr = (self._corner_radius if self._corner_radius is not None else (h / 2.0 / s)) * s
        track_col = resolve_color_failsafe(self._track_color or self.inner_bg or pal.track_bg, palette=pal)
        act_col = resolve_color_failsafe(self._active_color or pal.primary, palette=pal)
        txt_col = resolve_color_failsafe(self._text_color or pal.fg, palette=pal)
        act_txt_col = resolve_color_failsafe(self._active_text_color or "#FFFFFF", palette=pal)

        # 1. Background Track
        surf.clear(self.outer_bg)
        surf.fill_rounded_rect(0.0, 0.0, w, h, cr, cr, track_col)
        surf.stroke_rounded_rect(0.0, 0.0, w, h, cr, cr, pal.border, stroke_width=1.0 * s)

        # 2. Segment calculations
        pad = 3.0 * s
        inner_w = w - pad * 2.0
        seg_w = inner_w / n
        inner_h = h - pad * 2.0
        inner_cr = max(2.0, cr - pad)

        scaled_font_sz = self._font_size * s
        font_cfg = parse_font(font_size=self._font_size, bold=self._bold)
        center_y = h / 2.0

        for i, val in enumerate(self._values):
            seg_x = pad + i * seg_w
            is_active = (i == self._selected)
            is_hover = (i == self._hovered_idx and not is_active)

            if is_active:
                # Active pill with subtle elevation
                surf.fill_rounded_rect(seg_x, pad, seg_w, inner_h, inner_cr, inner_cr, act_col)
            elif is_hover:
                hover_fill = blend_color_hex(track_col, pal.fg, 0.08)
                surf.fill_rounded_rect(seg_x, pad, seg_w, inner_h, inner_cr, inner_cr, hover_fill)

            # Text
            seg_cx = seg_x + seg_w / 2.0
            cur_txt_col = act_txt_col if is_active else (pal.text_muted if self.is_disabled else txt_col)
            text_y = compute_text_baseline_y(center_y, scaled_font_sz)
            surf.draw_text(
                val,
                seg_cx,
                text_y,
                font_size=scaled_font_sz,
                font_family=font_cfg.family,
                color=cur_txt_col,
                bold=is_active or font_cfg.bold,
                align="center",
            )


# Alias
SegmentedControl = SegmentedButton
