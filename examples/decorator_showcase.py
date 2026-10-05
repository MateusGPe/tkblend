"""
Interactive Showcase: Native Surface Decorator (BlendDecorator)
Demonstrates pure Blend2D double-buffered rounded cards, soft drop shadows,
focus rings, passive state monitoring, and custom BlendDecorator-based widgets
(DecoratedButton, DecoratedSlider, DecoratedSwitch) around standard Tk child widgets.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, List, Tuple, Callable, Any

import tkblend as tb
from tkblend import BlendDecorator
from tkblend.theme import Palette, get_theme, add_theme_listener, remove_theme_listener, resolve_ancestor_bg
from tkblend.surface import parse_color


# ==============================================================================
# Pure BlendDecorator-Based Custom Widgets
# ==============================================================================

class DecoratedButton(BlendDecorator):
    """
    Modern button built entirely on top of BlendDecorator.
    Provides rounded corners, soft drop shadows, hover/focus/active state
    styling, and dynamic multi-theme support.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        command: Optional[Callable[[], Any]] = None,
        variant: str = "card",  # 'primary', 'secondary', 'card', 'ghost', 'accent'
        width: int = 80,
        height: int = 30,
        radius: float = 7.0,
        font: Tuple[str, int, str] = ("Segoe UI", 9, "normal"),
        padding: Tuple[int, int, int, int] = (10, 4, 10, 4),
        **kwargs,
    ):
        self._command = command
        self._variant = variant
        self._text = text
        self._font = font
        self._is_pressed = False
        self._is_active_toggle = False

        pal = get_theme()
        bg_col, hover_bg, border_col, hover_border, fg_col, shadow_b = self._resolve_variant_colors(pal, variant)
        calc_w = max(width, len(text) * 8 + padding[0] + padding[2] + 16)

        super().__init__(
            master=master,
            width=calc_w,
            height=height,
            radius=radius,
            bg_color=bg_col,
            hover_bg_color=hover_bg,
            border_color=border_col,
            border_hover_color=hover_border,
            border_width=1.0,
            shadow_blur=shadow_b,
            shadow_offset_y=1.0 if shadow_b > 0 else 0.0,
            shadow_enabled=(shadow_b > 0),
            **kwargs,
        )

        self._label = tk.Label(
            self,
            text=text,
            font=font,
            bg=self.bg_color,
            fg=fg_col,
            cursor="hand2",
        )
        self.decorate(self._label, padding=padding)

        # Event bindings for interactive press and click
        for w in (self, self._label):
            w.bind("<Button-1>", self._on_press)
            w.bind("<ButtonRelease-1>", self._on_release)
            w.bind("<Enter>", self._on_enter, add="+")
            w.bind("<Leave>", self._on_leave, add="+")

    def _resolve_variant_colors(self, pal: Palette, variant: str):
        if variant == "primary":
            return (pal.primary, pal.accent, pal.primary, pal.accent, "#ffffff", 3.0)
        elif variant == "accent":
            return (pal.accent, pal.primary, pal.accent, pal.primary, "#ffffff", 3.0)
        elif variant == "ghost":
            return (pal.card_bg, pal.input_bg, pal.card_bg, pal.border, pal.fg, 0.0)
        elif variant == "secondary":
            return (pal.input_bg, pal.card_border, pal.border, pal.primary, pal.fg, 2.0)
        else:  # 'card'
            return (pal.input_bg, pal.card_border, pal.border, pal.primary, pal.fg, 2.0)

    def _on_press(self, event=None):
        self._is_pressed = True
        pal = get_theme()
        if self._variant != "primary":
            self.configure(bg_color=pal.primary, border_color=pal.accent, shadow_offset_y=0.0, shadow_blur=1.0)
            self._label.configure(fg="#ffffff")
        else:
            self.configure(shadow_offset_y=0.0, shadow_blur=1.5)

    def _on_release(self, event=None):
        if self._is_pressed:
            self._is_pressed = False
            pal = get_theme()
            bg_col, hover_bg, border_col, hover_border, fg_col, shadow_b = self._resolve_variant_colors(pal, self._variant)
            if self._is_active_toggle:
                self.configure(bg_color=pal.primary, border_color=pal.accent, shadow_blur=4.0)
                self._label.configure(fg="#ffffff")
            else:
                self.configure(
                    bg_color=bg_col,
                    hover_bg_color=hover_bg,
                    border_color=border_col,
                    border_hover_color=hover_border,
                    shadow_offset_y=1.0 if shadow_b > 0 else 0.0,
                    shadow_blur=shadow_b,
                )
                self._label.configure(fg=fg_col)
            if self._command:
                self._command()

    def _on_enter(self, event=None):
        self.set_hovered(True)

    def _on_leave(self, event=None):
        self._is_pressed = False
        self.set_hovered(False)

    def set_text(self, text: str):
        self._text = text
        self._label.config(text=text)

    def set_active_toggle(self, active: bool):
        """Used for theme / tab style toggle buttons."""
        self._is_active_toggle = active
        pal = get_theme()
        if active:
            self.configure(
                bg_color=pal.primary,
                hover_bg_color=pal.accent,
                border_color=pal.accent,
                shadow_blur=4.0,
            )
            self._label.configure(bg=self.bg_color, fg="#ffffff", font=(self._font[0], self._font[1], "bold"))
        else:
            bg_col, hover_bg, border_col, hover_border, fg_col, shadow_b = self._resolve_variant_colors(pal, self._variant)
            self.configure(
                bg_color=bg_col,
                hover_bg_color=hover_bg,
                border_color=border_col,
                border_hover_color=hover_border,
                shadow_blur=shadow_b,
            )
            self._label.configure(bg=self.bg_color, fg=fg_col, font=self._font)

    def _on_theme_changed(self, pal: Palette) -> None:
        super()._on_theme_changed(pal)
        if self._is_active_toggle:
            self.configure(bg_color=pal.primary, hover_bg_color=pal.accent, border_color=pal.accent)
            self._label.configure(bg=self.bg_color, fg="#ffffff")
        else:
            bg_col, hover_bg, border_col, hover_border, fg_col, shadow_b = self._resolve_variant_colors(pal, self._variant)
            self.configure(
                bg_color=bg_col,
                hover_bg_color=hover_bg,
                border_color=border_col,
                border_hover_color=hover_border,
                shadow_blur=shadow_b,
            )
            self._label.configure(bg=self.bg_color, fg=fg_col)


class DecoratedSwitch(tk.Frame):
    """
    Modern capsule toggle switch built with BlendDecorator.
    Features a rounded pill track and a sliding BlendDecorator thumb with drop shadow.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        variable: Optional[tk.BooleanVar] = None,
        command: Optional[Callable[[], Any]] = None,
        initial_value: bool = False,
        width: int = 44,
        height: int = 24,
        bg_color: Optional[str] = None,
        **kwargs,
    ):
        pal = get_theme()
        container_bg = bg_color or pal.card_bg
        super().__init__(master, bg=container_bg, **kwargs)

        self._variable = variable
        self._command = command
        self._value = variable.get() if variable is not None else initial_value
        self._width = width
        self._height = height
        self._thumb_size = 18

        # Pill Track Decorator
        self.track = BlendDecorator(
            self,
            width=width,
            height=height,
            radius=height / 2.0,
            bg_color=pal.primary if self._value else pal.input_bg,
            border_color=pal.accent if self._value else pal.border,
            border_width=1.0,
            shadow_blur=3.0 if self._value else 0.0,
            shadow_offset_y=1.0,
            shadow_enabled=self._value,
        )
        self.track.pack(side="left", padx=(0, 8), pady=2)

        # Sliding Thumb Decorator inside track
        self.thumb = BlendDecorator(
            self.track,
            width=self._thumb_size,
            height=self._thumb_size,
            radius=self._thumb_size / 2.0,
            bg_color="#ffffff" if self._value else pal.text_muted,
            border_width=0.0,
            shadow_blur=2.0,
            shadow_offset_y=1.0,
        )
        self._update_thumb_pos()

        # Optional companion label
        self.label: Optional[tk.Label] = None
        if text:
            self.label = tk.Label(
                self,
                text=text,
                font=("Segoe UI", 9),
                fg=pal.fg,
                bg=container_bg,
                cursor="hand2",
            )
            self.label.pack(side="left")
            self.label.bind("<Button-1>", self._on_toggle)

        # Interactivity
        for w in (self.track, self.thumb):
            w.bind("<Button-1>", self._on_toggle)

        add_theme_listener(self._on_theme_changed)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _on_destroy(self, event=None):
        if event is not None and getattr(event, "widget", None) == self:
            try:
                remove_theme_listener(self._on_theme_changed)
            except Exception:
                pass

    def _update_thumb_pos(self):
        insets = self.track.insets
        card_w = self._width
        card_h = self._height
        y_pos = int(insets[1] + (card_h - self._thumb_size) / 2)
        if self._value:
            x_pos = int(insets[0] + card_w - self._thumb_size - 3)
        else:
            x_pos = int(insets[0] + 3)
        self.thumb.place(x=x_pos, y=y_pos, width=self._thumb_size, height=self._thumb_size)

    def _on_toggle(self, event=None):
        self._value = not self._value
        if self._variable is not None:
            self._variable.set(self._value)
        self._sync_visual_state()
        if self._command:
            self._command()

    def _sync_visual_state(self):
        pal = get_theme()
        if self._value:
            self.track.configure(
                bg_color=pal.primary,
                border_color=pal.accent,
                shadow_blur=3.0,
                shadow_enabled=True,
            )
            self.thumb.configure(
                bg_color="#ffffff",
                shadow_blur=3.0,
            )
        else:
            self.track.configure(
                bg_color=pal.input_bg,
                border_color=pal.border,
                shadow_blur=0.0,
                shadow_enabled=False,
            )
            self.thumb.configure(
                bg_color=pal.text_muted,
                shadow_blur=1.0,
            )
        self._update_thumb_pos()

    def get(self) -> bool:
        return self._value

    def set(self, val: bool):
        self._value = bool(val)
        if self._variable is not None:
            self._variable.set(self._value)
        self._sync_visual_state()

    def _on_theme_changed(self, pal: Palette):
        try:
            self.configure(bg=pal.card_bg)
            if self.label:
                self.label.configure(bg=pal.card_bg, fg=pal.fg)
            self._sync_visual_state()
        except Exception:
            pass


class DecoratedSlider(tk.Frame):
    """
    Smooth, modern horizontal slider control built using BlendDecorator.
    Features a rounded decorator track and an interactive draggable BlendDecorator thumb.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        from_: float = 0.0,
        to: float = 100.0,
        value: float = 0.0,
        command: Optional[Callable[[float], Any]] = None,
        bg_color: Optional[str] = None,
        **kwargs,
    ):
        pal = get_theme()
        container_bg = bg_color or pal.card_bg
        super().__init__(master, bg=container_bg, **kwargs)

        self._min = float(from_)
        self._max = float(to)
        self._value = float(value)
        self._command = command
        self._thumb_size = 20
        self._thumb_radius = self._thumb_size / 2.0
        self._is_dragging = False

        # Interactive Slider Area container
        self.slider_area = tk.Frame(self, bg=container_bg, height=28)
        self.slider_area.pack(fill="x", expand=True, pady=(2, 4))
        self.slider_area.pack_propagate(False)

        # Track Decorator (flat pill with border)
        self.track = BlendDecorator(
            self.slider_area,
            height=6,
            radius=3.0,
            bg_color=pal.input_bg,
            border_color=pal.border,
            border_width=1.0,
            shadow_enabled=False,
            shadow_blur=0.0,
        )
        self.track.place(x=int(self._thumb_radius), rely=0.5, y=-3, relwidth=1.0, width=-self._thumb_size)

        # Thumb Decorator (pill circle with soft drop shadow)
        self.thumb = BlendDecorator(
            self.slider_area,
            width=self._thumb_size,
            height=self._thumb_size,
            radius=self._thumb_radius,
            bg_color=pal.primary,
            border_color="#ffffff",
            border_width=2.0,
            shadow_blur=3.0,
            shadow_offset_y=1.0,
            shadow_enabled=True,
        )

        # Event bindings
        for w in (self.slider_area, self.track, self.thumb):
            w.bind("<Button-1>", self._on_click)
            w.bind("<B1-Motion>", self._on_drag)
            w.bind("<ButtonRelease-1>", self._on_release)
            w.bind("<MouseWheel>", self._on_wheel)
            w.bind("<Button-4>", self._on_wheel_linux_up)
            w.bind("<Button-5>", self._on_wheel_linux_down)

        self.slider_area.bind("<Configure>", lambda e: self._update_thumb_pos())

        add_theme_listener(self._on_theme_changed)
        self.bind("<Destroy>", self._on_destroy, add="+")
        self.after(20, self._update_thumb_pos)

    def _on_destroy(self, event=None):
        if event is not None and getattr(event, "widget", None) == self:
            try:
                remove_theme_listener(self._on_theme_changed)
            except Exception:
                pass

    def _get_fraction(self) -> float:
        span = self._max - self._min
        if span <= 0:
            return 0.0
        return max(0.0, min(1.0, (self._value - self._min) / span))

    def _update_thumb_pos(self):
        total_w = self.slider_area.winfo_width()
        if total_w <= 1:
            total_w = 200
        usable_w = max(1, total_w - self._thumb_size)
        frac = self._get_fraction()
        x = int(frac * usable_w)
        y = int((28 - self._thumb_size) / 2)
        self.thumb.place(x=x, y=y, width=self._thumb_size, height=self._thumb_size)

    def _set_from_x(self, mouse_x_relative: int):
        total_w = self.slider_area.winfo_width()
        usable_w = max(1, total_w - self._thumb_size)
        clamped_x = max(0, min(usable_w, mouse_x_relative - int(self._thumb_radius)))
        frac = clamped_x / usable_w
        new_val = self._min + frac * (self._max - self._min)
        self.set(new_val)
        if self._command:
            self._command(self._value)

    def _on_click(self, event):
        self._is_dragging = True
        self.thumb.configure(shadow_blur=5.0, shadow_offset_y=1.5)
        abs_x = event.x_root
        area_x = self.slider_area.winfo_rootx()
        self._set_from_x(abs_x - area_x)

    def _on_drag(self, event):
        if self._is_dragging:
            abs_x = event.x_root
            area_x = self.slider_area.winfo_rootx()
            self._set_from_x(abs_x - area_x)

    def _on_release(self, event):
        self._is_dragging = False
        self.thumb.configure(shadow_blur=3.0, shadow_offset_y=1.0)

    def _on_wheel(self, event):
        step = (self._max - self._min) * 0.05
        if event.delta > 0:
            self.set(self._value + step)
        else:
            self.set(self._value - step)
        if self._command:
            self._command(self._value)

    def _on_wheel_linux_up(self, event):
        step = (self._max - self._min) * 0.05
        self.set(self._value + step)
        if self._command:
            self._command(self._value)

    def _on_wheel_linux_down(self, event):
        step = (self._max - self._min) * 0.05
        self.set(self._value - step)
        if self._command:
            self._command(self._value)

    def get(self) -> float:
        return self._value

    def set(self, val: float):
        self._value = max(self._min, min(self._max, float(val)))
        self._update_thumb_pos()

    def _on_theme_changed(self, pal: Palette):
        try:
            self.configure(bg=pal.card_bg)
            self.slider_area.configure(bg=pal.card_bg)
            self.track.configure(bg_color=pal.input_bg, border_color=pal.border)
            self.thumb.configure(bg_color=pal.primary, border_color="#ffffff")
            self._update_thumb_pos()
        except Exception:
            pass


# ==============================================================================
# Main Interactive Showcase Application
# ==============================================================================

class DecoratorShowcase(tk.Frame):
    """Interactive gallery and live playground for BlendDecorator."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill="both", expand=True)

        self._current_radius = 12.0
        self._current_border_w = 1.5
        self._current_blur = 10.0
        self._current_spread = 0.0
        self._current_offset_y = 3.0
        self._current_focus_ring_w = 2.5
        self._current_focus_ring_offset = 2.0
        self._shadows_enabled = True

        self._is_simulated_hover = False
        self._is_simulated_focus = False
        self._is_error_state = False

        # Registries for dynamic theme tracking
        self._bg_frames: List[tk.Frame] = []
        self._card_frames: List[tk.Widget] = []
        self._primary_labels: List[tk.Label] = []
        self._muted_labels: List[tk.Label] = []
        self._entries: List[tk.Widget] = []
        self._decorators: List[BlendDecorator] = []
        self._theme_buttons: List[DecoratedButton] = []
        self._preset_buttons: List[DecoratedButton] = []
        self._slider_controls: List[dict] = []

        self._build_ui()

    def _build_ui(self):
        pal = tb.get_theme()
        self.configure(bg=pal.bg)
        self._bg_frames.append(self)

        # ----------------------------------------------------------------------
        # Header bar
        # ----------------------------------------------------------------------
        self.header = tk.Frame(self, bg=pal.bg)
        self.header.pack(fill="x", padx=20, pady=(12, 6))
        self._bg_frames.append(self.header)

        self.title_lbl = tk.Label(
            self.header,
            text="BlendDecorator Surface Showcase",
            font=("Segoe UI", 16, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        )
        self.title_lbl.pack(side="left")

        # Theme selector bar using DecoratedButton
        self.theme_bar = tk.Frame(self.header, bg=pal.bg)
        self.theme_bar.pack(side="right")
        self._bg_frames.append(self.theme_bar)

        self.theme_lbl = tk.Label(self.theme_bar, text="Theme:", font=("Segoe UI", 10), fg=pal.text_muted, bg=pal.bg)
        self.theme_lbl.pack(side="left", padx=(0, 6))

        for theme_name in ("dark", "light", "tokyo-night", "dracula", "nord"):
            btn = DecoratedButton(
                self.theme_bar,
                text=theme_name.capitalize(),
                width=80,
                height=28,
                radius=6.0,
                variant="card",
                command=lambda t=theme_name: self._on_change_theme(t),
            )
            btn.pack(side="left", padx=2)
            self._theme_buttons.append(btn)
            if theme_name == "tokyo-night":
                btn.set_active_toggle(True)

        # ----------------------------------------------------------------------
        # Main content container (2 columns: Practical Demos & Live Studio)
        # ----------------------------------------------------------------------
        self.body = tk.Frame(self, bg=pal.bg)
        self.body.pack(fill="both", expand=True, padx=20, pady=(4, 12))
        self._bg_frames.append(self.body)

        self.body.columnconfigure(0, weight=1, uniform="col")
        self.body.columnconfigure(1, weight=1, uniform="col")
        self.body.rowconfigure(0, weight=1)

        # ======================================================================
        # Left Column: Practical UI Components & State Demos
        # ======================================================================
        self.left_col = BlendDecorator(self.body, radius=14, shadow_blur=10, bg_color=pal.card_bg)
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        self._decorators.append(self.left_col)

        self.left_inner = tk.Frame(self.left_col, bg=pal.card_bg)
        self.left_inner.pack(fill="both", expand=True, padx=16, pady=14)
        self._card_frames.append(self.left_inner)

        col1_title = tk.Label(
            self.left_inner,
            text="Practical Components & State Triggers",
            font=("Segoe UI", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        col1_title.pack(anchor="w", pady=(0, 8))
        self._primary_labels.append(col1_title)

        # 1. Pill Search Input with Decorated Action Button
        p1_lbl = tk.Label(self.left_inner, text="1. Pill Search Input with Action Button", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg)
        p1_lbl.pack(anchor="w", pady=(0, 3))
        self._primary_labels.append(p1_lbl)

        self.search_dec = BlendDecorator(
            self.left_inner,
            width=320,
            height=44,
            radius=22.0,
            border_width=1.2,
            shadow_blur=8.0,
            shadow_offset_y=2.0,
            focus_ring_width=2.5,
        )
        self.search_dec.pack(fill="x", pady=(0, 8))
        self._decorators.append(self.search_dec)

        search_box = tk.Frame(self.search_dec, bg=self.search_dec.bg_color)
        self._card_frames.append(search_box)
        self.search_entry = tk.Entry(search_box, font=("Segoe UI", 10), bg=self.search_dec.bg_color, fg=pal.fg, relief="flat", bd=0, highlightthickness=0)
        self.search_entry.insert(0, "Search documents, commands, and assets...")
        self.search_entry.pack(side="left", fill="both", expand=True, padx=(8, 6))
        self._entries.append(self.search_entry)

        search_btn = DecoratedButton(
            search_box,
            text="Search",
            variant="primary",
            width=76,
            height=28,
            radius=14.0,
            command=lambda: self.search_entry.delete(0, tk.END),
        )
        search_btn.pack(side="right", padx=(0, 4))
        self.search_dec.decorate(search_box, padding=(4, 4, 4, 4))

        # 2. Credentials & Interactive Focus Hooking
        p2_lbl = tk.Label(self.left_inner, text="2. Floating Credentials (Passive Focus Hooking)", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg)
        p2_lbl.pack(anchor="w", pady=(0, 3))
        self._primary_labels.append(p2_lbl)

        self.user_dec = BlendDecorator(
            self.left_inner,
            width=320,
            height=38,
            radius=9.0,
            border_width=1.0,
            shadow_blur=6.0,
            shadow_offset_y=2.0,
        )
        self.user_dec.pack(fill="x", pady=(0, 6))
        self._decorators.append(self.user_dec)

        self.user_entry = tk.Entry(self.user_dec, font=("Segoe UI", 10), bg=self.user_dec.bg_color, fg=pal.fg, relief="flat", bd=0)
        self.user_entry.insert(0, "developer@antigravity.io")
        self.user_dec.decorate(self.user_entry, padding=(10, 4, 10, 4))
        self._entries.append(self.user_entry)

        self.pass_dec = BlendDecorator(
            self.left_inner,
            width=320,
            height=38,
            radius=9.0,
            border_width=1.0,
            shadow_blur=6.0,
            shadow_offset_y=2.0,
        )
        self.pass_dec.pack(fill="x", pady=(0, 6))
        self._decorators.append(self.pass_dec)

        self.pass_entry = tk.Entry(self.pass_dec, font=("Segoe UI", 10), show="•", bg=self.pass_dec.bg_color, fg=pal.fg, relief="flat", bd=0)
        self.pass_entry.insert(0, "SecretPassword123!")
        self.pass_dec.decorate(self.pass_entry, padding=(10, 4, 10, 4))
        self._entries.append(self.pass_entry)

        # Focus hook control bar using DecoratedButtons
        focus_bar = tk.Frame(self.left_inner, bg=pal.card_bg)
        focus_bar.pack(fill="x", pady=(0, 8))
        self._card_frames.append(focus_bar)

        for text, cmd in [
            ("Focus User", self.user_entry.focus_set),
            ("Focus Password", self.pass_entry.focus_set),
            ("Unfocus All", self.focus_set),
        ]:
            b = DecoratedButton(focus_bar, text=text, variant="secondary", width=105, height=28, radius=6.0, command=cmd)
            b.pack(side="left", padx=3)

        # 3. Dynamic Validation & Error State Trigger
        p3_lbl = tk.Label(self.left_inner, text="3. Dynamic Validation / Error State", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg)
        p3_lbl.pack(anchor="w", pady=(0, 3))
        self._primary_labels.append(p3_lbl)

        val_row = tk.Frame(self.left_inner, bg=pal.card_bg)
        val_row.pack(fill="x", pady=(0, 6))
        self._card_frames.append(val_row)

        self.val_dec = BlendDecorator(
            val_row,
            width=180,
            height=38,
            radius=9.0,
            border_width=1.0,
            shadow_blur=6.0,
            shadow_offset_y=2.0,
        )
        self.val_dec.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._decorators.append(self.val_dec)

        self.val_entry = tk.Entry(self.val_dec, font=("Segoe UI", 10), bg=self.val_dec.bg_color, fg=pal.fg, relief="flat", bd=0)
        self.val_entry.insert(0, "BLND-8941-XJ92 (Valid)")
        self.val_dec.decorate(self.val_entry, padding=(10, 4, 10, 4))
        self._entries.append(self.val_entry)

        self._err_var = tk.BooleanVar(value=False)
        self.val_switch = DecoratedSwitch(
            val_row,
            text="Simulate Error",
            variable=self._err_var,
            command=self._on_toggle_error_state,
        )
        self.val_switch.pack(side="right")

        # 4. Multiline Borderless Text Snippet
        p4_lbl = tk.Label(self.left_inner, text="4. Borderless Code / Note Decorator", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg)
        p4_lbl.pack(anchor="w", pady=(0, 3))
        self._primary_labels.append(p4_lbl)

        self.text_dec = BlendDecorator(
            self.left_inner,
            width=320,
            height=60,
            radius=10.0,
            border_width=1.0,
            shadow_blur=8.0,
            shadow_offset_y=2.0,
        )
        self.text_dec.pack(fill="x", pady=(0, 6))
        self._decorators.append(self.text_dec)

        self.text_widget = tk.Text(self.text_dec, font=("Consolas", 9), height=2, bg=self.text_dec.bg_color, fg=pal.fg, relief="flat", bd=0)
        self.text_widget.insert("1.0", "# Pure Blend2D Surface Decorator\ndec = tb.BlendDecorator(root, radius=12)")
        self.text_dec.decorate(self.text_widget, padding=(10, 4, 10, 4))
        self._entries.append(self.text_widget)

        # 5. Native Window Corner Clipping (clip_child)
        p5_lbl = tk.Label(self.left_inner, text="5. Full-Bleed Container (Native OS Window Clipping)", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg)
        p5_lbl.pack(anchor="w", pady=(0, 3))
        self._primary_labels.append(p5_lbl)

        clip_row = tk.Frame(self.left_inner, bg=pal.card_bg)
        clip_row.pack(fill="x", pady=(0, 2))
        self._card_frames.append(clip_row)

        self.clip_dec = BlendDecorator(
            clip_row,
            width=200,
            height=48,
            radius=14.0,
            border_width=1.5,
            shadow_blur=8.0,
            shadow_offset_y=2.0,
            clip_child=True,
        )
        self.clip_dec.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._decorators.append(self.clip_dec)

        self.clip_child_frame = tk.Frame(self.clip_dec, bg="#2563eb")
        clip_inner_lbl = tk.Label(self.clip_child_frame, text="⚡ Shaped Child OS Window", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#2563eb")
        clip_inner_lbl.pack(expand=True)
        self.clip_dec.decorate(self.clip_child_frame, padding=(0, 0, 0, 0))

        self._clip_var = tk.BooleanVar(value=True)
        self.clip_switch = DecoratedSwitch(
            clip_row,
            text="Clip Child",
            variable=self._clip_var,
            command=self._on_toggle_demo_clip,
        )
        self.clip_switch.pack(side="right")

        # ======================================================================
        # Right Column: Live Style Studio & Inset Inspector
        # ======================================================================
        self.right_col = BlendDecorator(self.body, radius=14, shadow_blur=10, bg_color=pal.card_bg)
        self.right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        self._decorators.append(self.right_col)

        self.right_inner = tk.Frame(self.right_col, bg=pal.card_bg)
        self.right_inner.pack(fill="both", expand=True, padx=16, pady=14)
        self._card_frames.append(self.right_inner)

        col2_title = tk.Label(
            self.right_inner,
            text="Live Style Studio & Inset Inspector",
            font=("Segoe UI", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        col2_title.pack(anchor="w", pady=(0, 6))
        self._primary_labels.append(col2_title)

        # Target Live Preview Box
        self.preview_box = tk.Frame(self.right_inner, bg=pal.card_bg)
        self.preview_box.pack(fill="x", pady=(0, 4))
        self._card_frames.append(self.preview_box)

        self.live_dec = BlendDecorator(
            self.preview_box,
            width=340,
            height=54,
            radius=self._current_radius,
            border_width=self._current_border_w,
            shadow_blur=self._current_blur,
            shadow_spread=self._current_spread,
            shadow_offset_y=self._current_offset_y,
            focus_ring_width=self._current_focus_ring_w,
            focus_ring_offset=self._current_focus_ring_offset,
        )
        self.live_dec.pack(fill="x", padx=4, pady=2)
        self._decorators.append(self.live_dec)

        self.live_entry = tk.Entry(self.live_dec, font=("Segoe UI", 11, "bold"), bg=self.live_dec.bg_color, fg=pal.fg, relief="flat", bd=0)
        self.live_entry.insert(0, "Live Decorated Entry Box")
        self.live_dec.decorate(self.live_entry, padding=(12, 4, 12, 4))
        self._entries.append(self.live_entry)

        # Simulation state buttons using DecoratedButton
        sim_bar = tk.Frame(self.right_inner, bg=pal.card_bg)
        sim_bar.pack(fill="x", pady=(0, 6))
        self._card_frames.append(sim_bar)

        sim_lbl = tk.Label(sim_bar, text="Preview State:", font=("Segoe UI", 9), fg=pal.text_muted, bg=pal.card_bg)
        sim_lbl.pack(side="left", padx=(0, 6))
        self._muted_labels.append(sim_lbl)

        self.hover_btn = DecoratedButton(sim_bar, text="Hover", variant="secondary", width=68, height=28, radius=6.0, command=self._toggle_sim_hover)
        self.hover_btn.pack(side="left", padx=2)

        self.focus_btn = DecoratedButton(sim_bar, text="Focus", variant="secondary", width=68, height=28, radius=6.0, command=self._toggle_sim_focus)
        self.focus_btn.pack(side="left", padx=2)

        reset_btn = DecoratedButton(sim_bar, text="Reset", variant="ghost", width=68, height=28, radius=6.0, command=self._reset_sim_states)
        reset_btn.pack(side="left", padx=2)

        # Inset Readout
        insets = self.live_dec.insets
        self.insets_lbl = tk.Label(
            self.right_inner,
            text=f"Active Insets: L={insets[0]:.1f}px, T={insets[1]:.1f}px, R={insets[2]:.1f}px, B={insets[3]:.1f}px",
            font=("Segoe UI", 9),
            fg=pal.text_muted,
            bg=pal.card_bg,
        )
        self.insets_lbl.pack(anchor="w", pady=(0, 6))
        self._muted_labels.append(self.insets_lbl)

        # Style Presets Bar using DecoratedButtons
        presets_box = tk.Frame(self.right_inner, bg=pal.card_bg)
        presets_box.pack(fill="x", pady=(0, 6))
        self._card_frames.append(presets_box)

        presets_lbl = tk.Label(presets_box, text="Quick Presets:", font=("Segoe UI", 9), fg=pal.text_muted, bg=pal.card_bg)
        presets_lbl.pack(side="left", padx=(0, 6))
        self._muted_labels.append(presets_lbl)

        presets = [
            ("Pill", 22.0, 1.5, 10.0, 3.0, 2.5),
            ("Subtle", 8.0, 1.0, 6.0, 2.0, 2.0),
            ("Neon Glow", 14.0, 2.0, 12.0, 0.0, 3.5),
            ("Flat", 6.0, 1.5, 0.0, 0.0, 2.0),
        ]
        for name, r, bw, blur, off_y, ring_w in presets:
            pb = DecoratedButton(
                presets_box,
                text=name,
                width=76,
                height=26,
                radius=5.0,
                variant="card",
                command=lambda r=r, bw=bw, bl=blur, oy=off_y, rw=ring_w: self._apply_preset(r, bw, bl, oy, rw),
            )
            pb.pack(side="left", padx=2)
            self._preset_buttons.append(pb)

        # Sliders Controls using DecoratedSlider
        self.controls = tk.Frame(self.right_inner, bg=pal.card_bg)
        self.controls.pack(fill="both", expand=True)
        self._card_frames.append(self.controls)

        self._slider_controls.clear()
        self.sl_radius = self._create_slider(self.controls, "Corner Radius", 0.0, 26.0, self._current_radius, self._on_radius_changed)
        self.sl_border = self._create_slider(self.controls, "Border Width", 0.0, 5.0, self._current_border_w, self._on_border_w_changed)
        self.sl_blur = self._create_slider(self.controls, "Shadow Blur", 0.0, 25.0, self._current_blur, self._on_blur_changed)
        self.sl_offset_y = self._create_slider(self.controls, "Shadow Offset Y", -5.0, 15.0, self._current_offset_y, self._on_offset_y_changed)
        self.sl_ring_w = self._create_slider(self.controls, "Focus Ring Width", 0.0, 6.0, self._current_focus_ring_w, self._on_focus_ring_w_changed)

        # Shadow toggle switch using DecoratedSwitch
        self.switch_row = tk.Frame(self.controls, bg=pal.card_bg)
        self.switch_row.pack(fill="x", pady=(4, 0))
        self._card_frames.append(self.switch_row)

        self._shadow_var = tk.BooleanVar(value=True)
        self.shadow_sw = DecoratedSwitch(
            self.switch_row,
            text="Enable Soft Drop Shadow",
            variable=self._shadow_var,
            command=lambda: self._on_toggle_shadows(self._shadow_var.get()),
        )
        self.shadow_sw.pack(side="left")

    def _create_slider(self, parent, label_text, min_val, max_val, init_val, callback) -> dict:
        pal = tb.get_theme()
        row = tk.Frame(parent, bg=pal.card_bg)
        row.pack(fill="x", pady=1)
        self._card_frames.append(row)

        val_lbl = tk.Label(row, text=f"{label_text}: {init_val:.1f}px", font=("Segoe UI", 9), fg=pal.fg, bg=pal.card_bg)
        val_lbl.pack(anchor="w")
        self._primary_labels.append(val_lbl)

        def on_val(v: float):
            val_lbl.config(text=f"{label_text}: {v:.1f}px")
            callback(v)

        sl = DecoratedSlider(
            row,
            from_=min_val,
            to=max_val,
            value=init_val,
            command=on_val,
        )
        sl.pack(fill="x", pady=(1, 2))

        ctrl = {
            "name": label_text,
            "row": row,
            "label": val_lbl,
            "slider": sl,
            "set_fn": lambda v: (val_lbl.config(text=f"{label_text}: {v:.1f}px"), sl.set(v)),
        }
        self._slider_controls.append(ctrl)
        return ctrl

    def _apply_preset(self, radius: float, border_w: float, blur: float, offset_y: float, ring_w: float):
        self._current_radius = radius
        self._current_border_w = border_w
        self._current_blur = blur
        self._current_offset_y = offset_y
        self._current_focus_ring_w = ring_w

        self.sl_radius["set_fn"](radius)
        self.sl_border["set_fn"](border_w)
        self.sl_blur["set_fn"](blur)
        self.sl_offset_y["set_fn"](offset_y)
        self.sl_ring_w["set_fn"](ring_w)

        self.live_dec.configure(
            radius=radius,
            border_width=border_w,
            shadow_blur=blur,
            shadow_offset_y=offset_y,
            focus_ring_width=ring_w,
        )
        self._update_insets_display()

    def _on_radius_changed(self, val: float):
        self._current_radius = val
        self.live_dec.configure(radius=val)
        self._update_insets_display()

    def _on_border_w_changed(self, val: float):
        self._current_border_w = val
        self.live_dec.configure(border_width=val)
        self._update_insets_display()

    def _on_blur_changed(self, val: float):
        self._current_blur = val
        self.live_dec.configure(shadow_blur=val)
        self._update_insets_display()

    def _on_offset_y_changed(self, val: float):
        self._current_offset_y = val
        self.live_dec.configure(shadow_offset_y=val)
        self._update_insets_display()

    def _on_focus_ring_w_changed(self, val: float):
        self._current_focus_ring_w = val
        self.live_dec.configure(focus_ring_width=val)
        self._update_insets_display()

    def _on_toggle_shadows(self, enabled: bool):
        self._shadows_enabled = enabled
        self.live_dec.configure(shadow_enabled=enabled)
        self._update_insets_display()

    def _on_toggle_error_state(self):
        is_err = self._err_var.get()
        self._is_error_state = is_err
        pal = tb.get_theme()
        if is_err:
            self.val_dec.configure(
                border_color="#ef4444",
                border_hover_color="#f87171",
                focus_ring_color="#ef4444",
                shadow_color="#ef444455",
            )
            self.val_entry.delete(0, tk.END)
            self.val_entry.insert(0, "Error: Invalid License Key Format")
            self.val_entry.configure(fg="#ef4444")
        else:
            self.val_dec.configure(
                border_color=pal.border,
                border_hover_color=pal.primary,
                focus_ring_color=pal.primary,
                shadow_color="#00000033",
            )
            self.val_entry.delete(0, tk.END)
            self.val_entry.insert(0, "BLND-8941-XJ92 (Valid)")
            self.val_entry.configure(fg=pal.fg)

    def _on_toggle_demo_clip(self):
        is_clipped = self._clip_var.get()
        self.clip_dec.configure(clip_child=is_clipped)

    def _toggle_sim_hover(self):
        self._is_simulated_hover = not self._is_simulated_hover
        self.live_dec.set_hovered(self._is_simulated_hover)
        self.live_dec.redraw()

    def _toggle_sim_focus(self):
        self._is_simulated_focus = not self._is_simulated_focus
        self.live_dec.set_focused(self._is_simulated_focus)
        self.live_dec.redraw()

    def _reset_sim_states(self):
        self._is_simulated_hover = False
        self._is_simulated_focus = False
        self.live_dec.set_hovered(False)
        self.live_dec.set_focused(False)
        self.live_dec.redraw()

    def _update_insets_display(self):
        insets = self.live_dec.insets
        self.insets_lbl.config(
            text=f"Active Insets: L={insets[0]:.1f}px, T={insets[1]:.1f}px, R={insets[2]:.1f}px, B={insets[3]:.1f}px"
        )

    def _on_change_theme(self, theme_name: str):
        tb.set_theme(theme_name)
        pal = tb.get_theme()

        # Update theme buttons active state
        for btn in self._theme_buttons:
            btn.set_active_toggle(btn._text.lower() == theme_name.lower())

        # Update root and background frames
        for f in self._bg_frames:
            try:
                f.configure(bg=pal.bg)
            except Exception:
                pass

        # Update header title and theme labels
        try:
            self.title_lbl.configure(fg=pal.fg, bg=pal.bg)
            self.theme_lbl.configure(fg=pal.text_muted, bg=pal.bg)
        except Exception:
            pass

        # Update card inner frames
        for f in self._card_frames:
            try:
                f.configure(bg=pal.card_bg)
            except Exception:
                pass

        # Update labels with active theme palette
        for lbl in self._primary_labels:
            try:
                lbl.configure(fg=pal.fg, bg=pal.card_bg)
            except Exception:
                pass

        for lbl in self._muted_labels:
            try:
                lbl.configure(fg=pal.text_muted, bg=pal.card_bg)
            except Exception:
                pass

        # Update entries & text widgets
        for entry in self._entries:
            try:
                entry.configure(bg=pal.card_bg, fg=pal.fg, insertbackground=pal.fg)
            except Exception:
                pass

        if not self._is_error_state:
            try:
                self.val_entry.configure(fg=pal.fg)
            except Exception:
                pass

        self._update_insets_display()


def main():
    root = tk.Tk()
    root.title("tkblend - BlendDecorator Showcase")
    root.geometry("960x640")
    root.minsize(940, 600)

    tb.set_theme("tokyo-night")

    app = DecoratorShowcase(root)

    def on_close():
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
