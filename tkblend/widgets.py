"""
Modern high-level UI components powered by Blend2D vector graphics and TTK theme engine.
Includes ToggleSwitch, Badge, SegmentedControl, and Card containers.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any, List, Tuple

from tkblend.canvas import BlendCanvas
from tkblend.theme import (
    get_theme_palette,
    is_inside_card,
    sync_card_children,
    bind_theme_changed,
)


def blend_color_hex(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex color strings at factor t (0.0 to 1.0)."""
    if t <= 0.0:
        return c1
    if t >= 1.0:
        return c2

    def _to_rgb(s: str) -> Tuple[int, int, int]:
        s = s.lstrip("#")
        if len(s) == 3:
            s = "".join(c + c for c in s)
        val = int(s[:6], 16)
        return ((val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF)

    try:
        r1, g1, b1 = _to_rgb(c1)
        r2, g2, b2 = _to_rgb(c2)
        inv = 1.0 - t
        r = int(r1 * inv + r2 * t)
        g = int(g1 * inv + g2 * t)
        b = int(b1 * inv + b2 * t)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return c1 if t < 0.5 else c2


class Card(ttk.Frame):
    """
    Modern elevated card container with rounded card styling and automatic child color syncing.
    """
    def __init__(self, master=None, style: str = "Card.TFrame", padding: Any = 16, **kwargs):
        super().__init__(master, style=style, padding=padding, **kwargs)
        bind_theme_changed(self, self._sync_children)
        self.after_idle(self._sync_children)

    def _sync_children(self):
        sync_card_children(self)


class ToggleSwitch(BlendCanvas):
    """
    Modern iOS/Fluent-style interactive toggle switch with smooth 60fps animated sliding thumb,
    antialiased vector track, two-way variable data binding, and full theme integration.
    """
    def __init__(
        self,
        master=None,
        text: str = "",
        variable: Optional[tk.BooleanVar] = None,
        command: Optional[Callable[[], None]] = None,
        width: int = 44,
        height: int = 24,
        state: str = "normal",
        **kwargs,
    ):
        super().__init__(master, width=width, height=height, **kwargs)
        self.text = text
        self.command = command
        self._state = state
        self._anim_timer = None

        if variable is None:
            self.variable = tk.BooleanVar(value=False)
        else:
            self.variable = variable

        self._target_progress = 1.0 if self.variable.get() else 0.0
        self._current_progress = self._target_progress

        self._trace_id = self.variable.trace_add("write", self._on_var_changed)

        self._is_hovered = False
        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")
        self.bind("<Button-1>", self._on_click, add="+")

        bind_theme_changed(self, self._redraw)
        self.after_idle(self._redraw)

    def _on_enter(self, _event=None):
        if self._state != "disabled":
            self._is_hovered = True
            self.configure(cursor="hand2")
            self._redraw()

    def _on_leave(self, _event=None):
        self._is_hovered = False
        self.configure(cursor="")
        self._redraw()

    def _on_click(self, _event=None):
        if self._state == "disabled":
            return
        self.toggle()
        if self.command:
            self.command()

    def _on_var_changed(self, *args):
        target = 1.0 if self.variable.get() else 0.0
        if target != self._target_progress:
            self._target_progress = target
            self._start_animation()

    def toggle(self):
        self.variable.set(not self.variable.get())

    def get(self) -> bool:
        return bool(self.variable.get())

    def set(self, value: bool):
        self.variable.set(bool(value))

    def _start_animation(self):
        if self._anim_timer is not None:
            try:
                self.after_cancel(self._anim_timer)
            except Exception:
                pass
            self._anim_timer = None
        self._step_animation()

    def _step_animation(self):
        diff = self._target_progress - self._current_progress
        if abs(diff) < 0.04:
            self._current_progress = self._target_progress
            self._anim_timer = None
            self._redraw()
            return

        self._current_progress += diff * 0.35
        self._redraw()
        self._anim_timer = self.after(16, self._step_animation)

    def _redraw(self):
        if not self.winfo_exists():
            return
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            w = int(self.cget("width"))
            h = int(self.cget("height"))

        pal = get_theme_palette()
        is_inside = is_inside_card(self)
        bg_color = pal["card_bg"] if is_inside else pal["bg"]

        with self.render() as ctx:
            ctx.clear(bg_color)

            track_w = float(w - 4)
            track_h = float(h - 4)
            tx = 2.0
            ty = 2.0
            tr = track_h / 2.0

            disabled = (self._state == "disabled")
            t = self._current_progress

            off_fill = pal["input_bg"] if not self._is_hovered else pal["secondary_hover"]
            on_fill = pal["primary_hover"] if self._is_hovered else pal["primary"]
            track_fill = blend_color_hex(off_fill, on_fill, t) if not disabled else pal["disabled_bg"]

            border_col = pal["input_border"] if not self._is_hovered else pal["primary_hover"]
            if t > 0.5:
                border_col = track_fill

            ctx.fill_rounded_rect(tx, ty, track_w, track_h, tr, tr, track_fill)
            ctx.stroke_rounded_rect(tx, ty, track_w, track_h, tr, tr, border_col, stroke_width=1.2)

            # Circular thumb position & soft shadow
            thumb_radius = (track_h - 4.0) / 2.0
            start_x = tx + 2.0 + thumb_radius
            end_x = tx + track_w - 2.0 - thumb_radius
            cx = start_x + (end_x - start_x) * t
            cy = ty + track_h / 2.0

            if not disabled:
                ctx.fill_circle(cx, cy + 1.0, thumb_radius, "rgba(0, 0, 0, 0.2)")

            thumb_col = pal["fg"] if (not disabled and self._is_hovered and t < 0.5) else (
                pal["primary_fg"] if t >= 0.5 else pal["thumb"]
            )
            if disabled:
                thumb_col = pal["disabled_fg"]

            ctx.fill_circle(cx, cy, thumb_radius, thumb_col)


class Badge(BlendCanvas):
    """
    Modern pill badge displaying status, counts, or tags with antialiased vector borders,
    subtle tint fills, and theme palette synchronization.
    Variants: 'primary', 'secondary', 'success', 'warning', 'destructive', 'outline'.
    """
    def __init__(
        self,
        master=None,
        text: str = "",
        variant: str = "primary",
        dot: bool = False,
        font_size: float = 11.0,
        font_family: str = "sans-serif",
        **kwargs,
    ):
        self._text = text
        self._variant = variant
        self._dot = dot
        self._font_size = font_size
        self._font_family = font_family

        w = max(42, len(text) * 8 + (32 if dot else 20))
        h = 24
        kwargs.setdefault("width", w)
        kwargs.setdefault("height", h)
        super().__init__(master, **kwargs)

        bind_theme_changed(self, self._redraw)
        self.after_idle(self._redraw)

    def set_text(self, text: str):
        self._text = text
        w = max(42, len(text) * 8 + (32 if self._dot else 20))
        self.configure(width=w)
        self._redraw()

    def set_variant(self, variant: str):
        self._variant = variant
        self._redraw()

    def _redraw(self):
        if not self.winfo_exists():
            return
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            w = int(self.cget("width"))
            h = int(self.cget("height"))

        pal = get_theme_palette()
        is_inside = is_inside_card(self)
        bg_color = pal["card_bg"] if is_inside else pal["bg"]

        with self.render() as ctx:
            ctx.clear(bg_color)

            r = (h - 4.0) / 2.0
            px = 2.0
            py = 2.0
            pw = float(w - 4)
            ph = float(h - 4)

            v = self._variant.lower()
            if v in ("primary", "accent"):
                fill_col = blend_color_hex(bg_color, pal["primary"], 0.20)
                border_col = pal["primary"]
                text_col = pal["primary"]
            elif v == "success":
                fill_col = blend_color_hex(bg_color, pal["success"], 0.20)
                border_col = pal["success"]
                text_col = pal["success"]
            elif v in ("destructive", "danger"):
                fill_col = blend_color_hex(bg_color, pal["destructive"], 0.20)
                border_col = pal["destructive"]
                text_col = pal["destructive"]
            elif v == "warning":
                fill_col = blend_color_hex(bg_color, pal["warning"], 0.20)
                border_col = pal["warning"]
                text_col = pal["warning"]
            elif v == "outline":
                fill_col = bg_color
                border_col = pal["card_border"]
                text_col = pal["fg"]
            else:  # secondary / default
                fill_col = pal["secondary"]
                border_col = pal["card_border"]
                text_col = pal["secondary_fg"]

            ctx.fill_rounded_rect(px, py, pw, ph, r, r, fill_col)
            ctx.stroke_rounded_rect(px, py, pw, ph, r, r, border_col, stroke_width=1.0)

            text_x = px + pw / 2.0
            if self._dot:
                dot_r = 3.0
                dot_x = px + 10.0
                dot_y = py + ph / 2.0
                ctx.fill_circle(dot_x, dot_y, dot_r, text_col)
                text_x += 6.0

            text_y = py + ph / 2.0 + (self._font_size * 0.35)
            ctx.draw_text(
                self._text,
                text_x,
                text_y,
                font_size=self._font_size,
                font_family=self._font_family,
                color=text_col,
                align="center",
            )


class SegmentedControl(ttk.Frame):
    """
    Modern segmented tab / pill switcher with active indicator and Tkinter variable data binding.
    """
    def __init__(
        self,
        master=None,
        values: Optional[List[str]] = None,
        variable: Optional[tk.StringVar] = None,
        command: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(master, style="Card.TFrame", padding=3, **kwargs)
        self.values = values or []
        self.command = command
        self._buttons: List[Tuple[str, ttk.Button]] = []

        if variable is None:
            initial = self.values[0] if self.values else ""
            self.variable = tk.StringVar(value=initial)
        else:
            self.variable = variable

        self._trace_id = self.variable.trace_add("write", self._on_var_changed)

        for val in self.values:
            btn = ttk.Button(
                self,
                text=val,
                command=lambda v=val: self.set(v),
            )
            btn.pack(side="left", fill="both", expand=True, padx=2, pady=1)
            self._buttons.append((val, btn))

        self._update_button_styles()
        bind_theme_changed(self, self._update_button_styles)

    def _on_var_changed(self, *args):
        self._update_button_styles()
        if self.command:
            self.command(self.variable.get())

    def get(self) -> str:
        return self.variable.get()

    def set(self, value: str):
        self.variable.set(value)

    def _update_button_styles(self):
        cur = self.variable.get()
        for val, btn in self._buttons:
            if val == cur:
                btn.configure(style="Primary.TButton")
            else:
                btn.configure(style="Ghost.TButton")
