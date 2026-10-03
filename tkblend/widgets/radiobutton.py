"""
Pure Blend2D Vector RadioButton powered by NativeController.
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


class RadioButton(BaseControl):
    """
    Modern vector radio button with animated inner dot, keyboard accessibility,
    and Tk variable synchronization.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        value: Any = None,
        variable: Optional[Union[tk.StringVar, tk.IntVar, tk.Variable]] = None,
        command: Optional[Callable[[], None]] = None,
        width: int = 140,
        height: int = 24,
        size: int = 20,
        radio_color: Optional[ColorLike] = None,
        dot_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.5,
        fg_color: Optional[ColorLike] = None,
        font: Optional[Any] = None,
        font_size: Optional[float] = None,
        focus_ring: bool = True,
        focus_ring_color: Optional[ColorLike] = None,
        animated: bool = True,
        cursor: str = "hand2",
        state: str = "normal",
        **kwargs,
    ):
        self._text = str(text)
        self._value = value
        self._variable = variable
        self._command = command

        self._radio_size = int(size)
        self._custom_radio_color = radio_color
        self._custom_dot_color = dot_color
        self._custom_border_color = border_color
        self._border_width = float(border_width)
        self._custom_fg_color = fg_color

        self._font_spec = font
        self._font_size = font_size
        self._focus_ring = focus_ring
        self._custom_focus_ring_color = focus_ring_color

        self._animated = animated
        self._is_selected = False
        self._dot_t = 0.0

        if self._variable is not None:
            self._is_selected = (self._variable.get() == self._value)
            self._dot_t = 1.0 if self._is_selected else 0.0
            try:
                self._var_trace_id = self._variable.trace_add("write", self._on_variable_write)
            except Exception:
                try:
                    self._var_trace_id = self._variable.trace("w", self._on_variable_write)
                except Exception:
                    self._var_trace_id = None
        else:
            self._var_trace_id = None

        eff_width = width if text else size + 6

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
            new_sel = (val == self._value)
            if new_sel != self._is_selected:
                self._is_selected = new_sel
                self._animate_to_state(new_sel)

    def _animate_to_state(self, is_sel: bool) -> None:
        target_t = 1.0 if is_sel else 0.0
        if self._animated and self.winfo_exists():
            self.animate_property("dot", self._dot_t, target_t, duration_ms=140, on_update=self._set_dot_t)
        else:
            self._dot_t = target_t
            self.request_redraw()

    def _set_dot_t(self, val: float) -> None:
        self._dot_t = val

    def select(self) -> None:
        if self.is_disabled:
            return
        self._is_selected = True
        if self._variable is not None:
            self._variable.set(self._value)
        self._animate_to_state(True)
        if self._command is not None:
            self._command()

    def on_click(self, x: int, y: int, button: int) -> None:
        if button == 1:
            self.select()

    def on_key_press(self, event: tk.Event) -> None:
        if event.keysym in ("space", "Return"):
            self.select()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        r_sz = float(self._radio_size) * s
        r = r_sz / 2.0
        cx = 2.0 * s + r
        cy = h / 2.0

        active_col = resolve_color_failsafe(self._custom_radio_color or pal.primary, palette=pal)
        inactive_bg = resolve_color_failsafe(pal.input_bg, palette=pal)
        cur_bg = blend_color_hex(inactive_bg, active_col, self._dot_t) or inactive_bg

        border_col = resolve_color_failsafe(self._custom_border_color or pal.input_border, palette=pal)
        cur_border = blend_color_hex(border_col, active_col, self._dot_t) or border_col

        dot_col = resolve_color_failsafe(self._custom_dot_color or pal.primary_fg, palette=pal)

        if self.is_disabled:
            cur_bg = resolve_color_failsafe(pal.surface, palette=pal)
            cur_border = resolve_color_failsafe(pal.surface_border, palette=pal)
            dot_col = resolve_color_failsafe(pal.text_muted, palette=pal)

        fr_col = resolve_color_failsafe(self._custom_focus_ring_color or pal.input_focus, palette=pal) if (self._focus_ring and self.is_focused and not self.is_disabled) else "#00000000"
        fr_w = 2.0 * s if (self._focus_ring and self.is_focused and not self.is_disabled) else 0.0

        # Outer circle
        surf.fill_circle(cx, cy, r, cur_bg)
        if self._border_width > 0.0:
            surf.stroke_circle(cx, cy, r, cur_border, stroke_width=self._border_width * s)

        # Focus ring
        if self._focus_ring and self.is_focused and not self.is_disabled:
            surf.stroke_circle(cx, cy, r + 2.0 * s, fr_col, stroke_width=fr_w)

        # Inner animated dot
        if self._dot_t > 0.0:
            inner_r = (r * 0.45) * self._dot_t
            surf.fill_circle(cx, cy, inner_r, dot_col)

        # Text Label
        if self._text:
            text_x = cx + r + 10.0 * s
            fg_col = resolve_color_failsafe(self._custom_fg_color or pal.fg, palette=pal)
            if self.is_disabled:
                fg_col = resolve_color_failsafe(pal.text_muted, palette=pal)

            font_cfg = parse_font(font=self._font_spec, font_size=self._font_size or 13.0)
            scaled_font_sz = float(font_cfg.size) * s
            text_y = cy + scaled_font_sz * 0.35

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
        if "value" in kwargs:
            self._value = kwargs.pop("value")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "variable" in kwargs:
            self._variable = kwargs.pop("variable")
        self.request_redraw()
        return super().configure(**kwargs)
