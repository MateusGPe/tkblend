"""
Pure Blend2D Vector CheckBox powered by NativeController.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, Path
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    blend_color_hex,
)
from tkblend.font import parse_font
from tkblend.widgets.constants import (
    DEFAULT_CHECKBOX_WIDTH,
    DEFAULT_CHECKBOX_HEIGHT,
    DEFAULT_CHECKBOX_BOX_SIZE,
    DEFAULT_CHECKBOX_CORNER_RADIUS,
    DEFAULT_CHECKBOX_BORDER_WIDTH,
    DEFAULT_CHECKBOX_STROKE_WIDTH,
    DEFAULT_CHECKBOX_LEFT_MARGIN,
    DEFAULT_CHECKBOX_TEXT_SPACING,
    DEFAULT_CHECKBOX_COMPACT_EXTRA_PAD,
    DEFAULT_FONT_SIZE,
    FOCUS_RING_WIDTH,
    FOCUS_RING_PADDING,
    CHECKBOX_ANIM_DURATION_MS,
    CHECKMARK_P1,
    CHECKMARK_P2,
    CHECKMARK_P3,
    CHECKMARK_SPLIT_THRESHOLD,
    CURSOR_HAND,
    STATE_NORMAL,
    COLOR_TRANSPARENT,
)
from tkblend.widgets.utils import (
    draw_focus_ring,
    compute_text_baseline_y,
    bind_variable_trace,
    unbind_variable_trace,
)


class CheckBox(BaseControl):
    """
    Modern vector checkbox with animated checkmark, customizable corner radius,
    keyboard accessibility, and Tk variable synchronization.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        command: Optional[Callable[[], None]] = None,
        variable: Optional[Union[tk.BooleanVar, tk.IntVar, tk.StringVar, tk.Variable]] = None,
        onvalue: Any = True,
        offvalue: Any = False,
        width: int = DEFAULT_CHECKBOX_WIDTH,
        height: int = DEFAULT_CHECKBOX_HEIGHT,
        size: int = DEFAULT_CHECKBOX_BOX_SIZE,
        corner_radius: float = DEFAULT_CHECKBOX_CORNER_RADIUS,
        box_color: Optional[ColorLike] = None,
        check_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = DEFAULT_CHECKBOX_BORDER_WIDTH,
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

        self._box_size = int(size)
        self._corner_radius = float(corner_radius)

        self._custom_box_color = box_color
        self._custom_check_color = check_color
        self._custom_border_color = border_color
        self._border_width = float(border_width)
        self._custom_fg_color = fg_color

        self._font_spec = font
        self._font_size = font_size
        self._focus_ring = focus_ring
        self._custom_focus_ring_color = focus_ring_color

        self._animated = animated
        self._is_checked = False
        self._check_t = 0.0

        if self._variable is not None:
            self._is_checked = (self._variable.get() == self._onvalue)
            self._check_t = 1.0 if self._is_checked else 0.0
            self._var_trace_id = bind_variable_trace(self._variable, self._on_variable_write)
        else:
            self._var_trace_id = None

        eff_width = width if text else size + DEFAULT_CHECKBOX_COMPACT_EXTRA_PAD

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
            new_checked = (val == self._onvalue)
            if new_checked != self._is_checked:
                self._is_checked = new_checked
                self._animate_to_state(new_checked)

    def _animate_to_state(self, is_checked: bool) -> None:
        target_t = 1.0 if is_checked else 0.0
        if self._animated and self.winfo_exists():
            self.animate_property("check", self._check_t, target_t, duration_ms=CHECKBOX_ANIM_DURATION_MS, on_update=self._set_check_t)
        else:
            self._check_t = target_t
            self.request_redraw()

    def _set_check_t(self, val: float) -> None:
        self._check_t = val

    def get(self) -> Any:
        return self._onvalue if self._is_checked else self._offvalue

    def is_checked(self) -> bool:
        return self._is_checked

    def set(self, value: Any) -> None:
        self._is_checked = (value == self._onvalue)
        if self._variable is not None:
            self._variable.set(self._onvalue if self._is_checked else self._offvalue)
        self._animate_to_state(self._is_checked)

    def select(self) -> None:
        self.set(self._onvalue)

    def deselect(self) -> None:
        self.set(self._offvalue)

    def toggle(self) -> None:
        if self.is_disabled:
            return
        self._is_checked = not self._is_checked
        if self._variable is not None:
            self._variable.set(self._onvalue if self._is_checked else self._offvalue)
        self._animate_to_state(self._is_checked)
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

        box_sz = float(self._box_size) * s
        rx = self._corner_radius * s
        ry = rx

        bx = DEFAULT_CHECKBOX_LEFT_MARGIN * s
        by = (h - box_sz) / 2.0

        # Clear parent background
        surf.clear(self._resolved_parent_bg)

        # Colors
        active_box = resolve_color_failsafe(self._custom_box_color or pal.primary, palette=pal)
        inactive_box = resolve_color_failsafe(pal.input_bg, palette=pal)
        cur_box = blend_color_hex(inactive_box, active_box, self._check_t) or inactive_box

        border_col = resolve_color_failsafe(self._custom_border_color or pal.input_border, palette=pal)
        cur_border = blend_color_hex(border_col, active_box, self._check_t) or border_col

        check_col = resolve_color_failsafe(self._custom_check_color or pal.primary_fg, palette=pal)

        if self.is_disabled:
            cur_box = resolve_color_failsafe(pal.surface, palette=pal)
            cur_border = resolve_color_failsafe(pal.surface_border, palette=pal)
            check_col = resolve_color_failsafe(pal.text_muted, palette=pal)

        # Draw box container & border
        surf.fill_rounded_rect(bx, by, box_sz, box_sz, rx, ry, cur_box)
        if self._border_width > 0.0:
            surf.stroke_rounded_rect(bx, by, box_sz, box_sz, rx, ry, cur_border, stroke_width=self._border_width * s)

        # Draw focus ring
        if self._focus_ring and self.is_focused and not self.is_disabled:
            fr_col = resolve_color_failsafe(self._custom_focus_ring_color or pal.input_focus, palette=pal)
            draw_focus_ring(
                surf,
                bx,
                by,
                box_sz,
                box_sz,
                rx,
                ry,
                fr_col,
                stroke_width=FOCUS_RING_WIDTH,
                padding=FOCUS_RING_PADDING,
                scale=s,
            )

        # Draw animated vector checkmark path
        if self._check_t > 0.0:
            p1 = (bx + box_sz * CHECKMARK_P1[0], by + box_sz * CHECKMARK_P1[1])
            p2 = (bx + box_sz * CHECKMARK_P2[0], by + box_sz * CHECKMARK_P2[1])
            p3 = (bx + box_sz * CHECKMARK_P3[0], by + box_sz * CHECKMARK_P3[1])

            chk_path = Path()
            chk_path.move_to(p1[0], p1[1])

            if self._check_t <= CHECKMARK_SPLIT_THRESHOLD:
                # First leg
                t_leg = self._check_t / CHECKMARK_SPLIT_THRESHOLD
                cur_x = p1[0] + (p2[0] - p1[0]) * t_leg
                cur_y = p1[1] + (p2[1] - p1[1]) * t_leg
                chk_path.line_to(cur_x, cur_y)
            else:
                chk_path.line_to(p2[0], p2[1])
                # Second leg
                t_leg = (self._check_t - CHECKMARK_SPLIT_THRESHOLD) / (1.0 - CHECKMARK_SPLIT_THRESHOLD)
                cur_x = p2[0] + (p3[0] - p2[0]) * t_leg
                cur_y = p2[1] + (p3[1] - p2[1]) * t_leg
                chk_path.line_to(cur_x, cur_y)

            surf.stroke_path(chk_path, check_col, stroke_width=DEFAULT_CHECKBOX_STROKE_WIDTH * s)

        # Label Text
        if self._text:
            text_x = bx + box_sz + DEFAULT_CHECKBOX_TEXT_SPACING * s
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
            new_var = kwargs.pop("variable")
            if self._var_trace_id is not None and self._variable is not None:
                unbind_variable_trace(self._variable, self._var_trace_id)
            self._variable = new_var
            if self._variable is not None:
                self._is_checked = (self._variable.get() == self._onvalue)
                self._check_t = 1.0 if self._is_checked else 0.0
                self._var_trace_id = bind_variable_trace(self._variable, self._on_variable_write)
            else:
                self._var_trace_id = None
        self.request_redraw()
        return super().configure(**kwargs)
