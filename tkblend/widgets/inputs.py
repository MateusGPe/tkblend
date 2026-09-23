"""
Text entry and numeric stepper widgets: TextInput and SpinBox.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable

from tkblend.theme import get_theme, Palette
from tkblend.widgets.base import Widget, ScalingTracker
from tkblend.widgets.drawing import draw_vector_plus


class _TextInputBackground(Widget):
    """Backing vector surface for TextInput."""

    def __init__(self, owner: "TextInput", master: tk.Misc, width: int, height: int, bg: Optional[str] = None):
        self._owner = owner
        super().__init__(master=master, width=width, height=height, bg=bg)

    def _on_theme_changed(self, palette: Palette) -> None:
        super()._on_theme_changed(palette)
        if hasattr(self, "_owner") and self._owner.winfo_exists():
            self._owner._update_theme_colors()

    def render(self) -> None:
        if hasattr(self, "_owner"):
            self._owner._render_bg()


class TextInput(tk.Frame):
    """
    Modern vector text entry with rounded border, glowing focus ring,
    placeholder text, and clear button icon (✕).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        placeholder: str = "Enter text...",
        width: int = 240,
        height: int = 38,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._scale = ScalingTracker.get_scaling_factor(master)
        s = self._scale
        pal = get_theme()
        self._parent_bg = parent_bg or pal.bg
        super().__init__(
            master,
            width=max(1, int(width * s)),
            height=max(1, int(height * s)),
            bg=self._parent_bg,
            **kwargs,
        )
        self.pack_propagate(False)

        self._placeholder = placeholder
        self._placeholder_active = False
        self._has_focus = False

        self._bg_widget = _TextInputBackground(self, master=self, width=width, height=height, bg=self._parent_bg)
        self._bg_widget.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        entry_pad_x = int(14 * s)
        entry_pad_r = int(32 * s)
        self._entry = tk.Entry(
            self,
            bg=pal.input_bg,
            fg=pal.fg,
            insertbackground=pal.input_focus,
            borderwidth=0,
            highlightthickness=0,
            font=("DejaVu Sans", int(12 * s)),
        )
        self._entry.place(x=entry_pad_x, y=int(7 * s), relwidth=1.0, width=-(entry_pad_x + entry_pad_r), height=int(24 * s))

        if self._placeholder:
            self._placeholder_active = True
            self._entry.insert(0, self._placeholder)
            self._entry.configure(fg=pal.text_muted)

        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<KeyRelease>", self._on_key_release)
        self._bg_widget.bind("<Button-1>", self._on_bg_click)

        self._render_bg()

    def _update_theme_colors(self) -> None:
        if not self.winfo_exists():
            return
        pal = get_theme()
        fg_col = pal.text_muted if self._placeholder_active else pal.fg
        self._entry.configure(
            bg=pal.input_bg,
            fg=fg_col,
            insertbackground=pal.input_focus,
        )

    def _on_focus_in(self, event) -> None:
        self._has_focus = True
        if self._placeholder_active:
            self._entry.delete(0, "end")
            pal = get_theme()
            self._entry.configure(fg=pal.fg)
            self._placeholder_active = False
        self._render_bg()

    def _on_focus_out(self, event) -> None:
        self._has_focus = False
        if not self._entry.get() and self._placeholder:
            self._placeholder_active = True
            self._entry.insert(0, self._placeholder)
            pal = get_theme()
            self._entry.configure(fg=pal.text_muted)
        self._render_bg()

    def _on_key_release(self, event) -> None:
        self._render_bg()

    def _on_bg_click(self, event) -> None:
        s = self._scale
        clear_cx = self._bg_widget._widget_w - 20.0 * s
        if abs(event.x - clear_cx) <= 12.0 * s and self.get():
            self.set("")
            self._entry.focus_set()
            return
        self._entry.focus_set()

    def get(self) -> str:
        if self._placeholder_active:
            return ""
        return self._entry.get()

    def set(self, text: str) -> None:
        self._entry.delete(0, "end")
        pal = get_theme()
        if text:
            self._placeholder_active = False
            self._entry.configure(fg=pal.fg)
            self._entry.insert(0, text)
        else:
            if not self._has_focus and self._placeholder:
                self._placeholder_active = True
                self._entry.configure(fg=pal.text_muted)
                self._entry.insert(0, self._placeholder)
            else:
                self._placeholder_active = False
                self._entry.configure(fg=pal.fg)
        self._render_bg()

    def _render_bg(self) -> None:
        surf = self._bg_widget.surface
        surf.clear(self._parent_bg)
        s = self._scale
        pad = 2.0 * s
        w = max(1.0, self._bg_widget._widget_w - pad * 2.0)
        h = max(1.0, self._bg_widget._widget_h - pad * 2.0)
        r = 8.0 * s

        pal = get_theme()
        if self._has_focus:
            border_col = pal.input_focus
            border_w = 1.5 * s
        elif getattr(self._bg_widget, "_is_hovered", False):
            border_col = pal.secondary_hover
            border_w = 1.2 * s
        else:
            border_col = pal.input_border
            border_w = 1.0 * s

        surf.fill_rounded_rect(pad, pad, w, h, r, r, pal.input_bg)
        surf.stroke_rounded_rect(pad, pad, w, h, r, r, border_col, border_w)

        if self.get():
            cx = self._bg_widget._widget_w - 20.0 * s
            cy = self._bg_widget._widget_h / 2.0
            surf.fill_circle(cx, cy, 7.0 * s, pal.secondary)
            cr = 3.0 * s
            surf.draw_line(cx - cr, cy - cr, cx + cr, cy + cr, pal.fg, 1.2 * s)
            surf.draw_line(cx + cr, cy - cr, cx - cr, cy + cr, pal.fg, 1.2 * s)

        surf.blit(self._bg_widget.photo)


ModernTextInput = TextInput


class SpinBox(Widget):
    """
    Numeric stepper component with decrement (-) and increment (+) vector buttons.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        min_val: int = 0,
        max_val: int = 100,
        value: int = 10,
        step: int = 1,
        on_change: Optional[Callable[[int], None]] = None,
        width: int = 140,
        height: int = 36,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._min = min_val
        self._max = max_val
        self._value = max(min_val, min(max_val, int(value)))
        self._step = step
        self._on_change = on_change
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)
        self.bind("<ButtonRelease-1>", self._handle_click)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, val: int) -> None:
        self._value = max(self._min, min(self._max, int(val)))
        self.render()

    def _handle_click(self, event) -> None:
        s = self._scale
        btn_w = 34.0 * s
        if event.x <= btn_w:
            self.value -= self._step
            if self._on_change:
                self._on_change(self._value)
        elif event.x >= self._widget_w - btn_w:
            self.value += self._step
            if self._on_change:
                self._on_change(self._value)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        pad = 2.0 * s
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        r = 8.0 * s

        pal = get_theme()
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, pal.surface)
        self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, pal.card_border, 1.0 * s)

        btn_w = 32.0 * s
        # Minus button
        self._surface.fill_rounded_rect(pad, pad, btn_w, h, r, r, pal.secondary)
        self._surface.draw_line(pad + 10.0 * s, self._widget_h / 2.0, pad + btn_w - 10.0 * s, self._widget_h / 2.0, pal.fg, 1.8 * s)

        # Plus button
        plus_x = self._widget_w - pad - btn_w
        self._surface.fill_rounded_rect(plus_x, pad, btn_w, h, r, r, pal.secondary)
        cy = self._widget_h / 2.0
        cx = plus_x + btn_w / 2.0
        arm = 5.0 * s
        draw_vector_plus(self._surface, cx, cy, arm, pal.fg, 1.8 * s)

        # Middle text
        font_sz = 14.0 * s
        self._surface.draw_text(
            str(self._value),
            self._widget_w / 2.0,
            cy + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color=pal.fg,
            align="center",
        )
        self._surface.blit(self._photo)


ModernSpinBox = SpinBox
