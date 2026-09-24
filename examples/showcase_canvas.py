"""
tkblend Modern Vector Canvas Showcase Application.
Restored from the initial tkblend showcase: demonstrates soft elevation shadows,
linear & radial gradients, antialiased vector geometry, real-time 60 FPS fluid wave animation,
floating glassmorphic cards, and self-contained interactive vector widgets with DPI awareness.
"""

from __future__ import annotations
import math
import sys
import time
import tkinter as tk
from math import floor, ceil
from typing import Optional, Callable, Union, List, Tuple, Any

from tkblend import (
    Surface,
    BlendCanvas,
    LinearGradient,
    RadialGradient,
    Path,
    ColorLike,
    parse_color,
)
from tkblend.theme import get_theme, set_theme, Palette
from tkblend.widgets import SegmentedControl


# ============================================================================
# High-DPI Scaling Tracker
# ============================================================================

def _round_half_away(value: float) -> int:
    """Round halves away from zero without Banker's rounding bias."""
    if value >= 0:
        return floor(value + 0.5)
    return ceil(value - 0.5)


class ScalingTracker:
    """
    Manages process-level High-DPI awareness, Tk scaling factor tracking,
    and logical-to-physical pixel conversion for 4K / Retina displays.
    """

    _dpi_awareness_initialized: bool = False
    _user_widget_scaling: float = 1.0

    @classmethod
    def activate_high_dpi_awareness(cls) -> None:
        """Enable Per-Monitor High-DPI awareness where supported."""
        if cls._dpi_awareness_initialized:
            return

        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    import ctypes
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

        cls._dpi_awareness_initialized = True

    @classmethod
    def get_scaling_factor(cls, widget_or_window: Optional[tk.Misc] = None) -> float:
        """Calculate effective display scaling factor (1.0 = standard 96 DPI)."""
        if widget_or_window is None:
            return cls._user_widget_scaling

        try:
            ws = str(widget_or_window.tk.call("tk", "windowingsystem"))
            baseline = 1.0 if (ws == "aqua" and tk.TkVersion < 8.7) else (4.0 / 3.0)
            raw_scaling = float(widget_or_window.tk.call("tk", "scaling"))
            factor = raw_scaling / baseline
            quarter = round(factor * 4.0) / 4.0
            if abs(factor - quarter) <= 0.005:
                factor = quarter
            return max(0.5, factor * cls._user_widget_scaling)
        except Exception:
            return max(0.5, cls._user_widget_scaling)

    @classmethod
    def scale(cls, value: Union[int, float, List, Tuple], widget: Optional[tk.Misc] = None) -> Any:
        """Convert logical UI units to physical pixel values."""
        factor = cls.get_scaling_factor(widget)
        if factor == 1.0:
            if isinstance(value, (int, float)):
                return int(value)
            return value

        if isinstance(value, (int, float)):
            if value == 0:
                return 0
            return _round_half_away(float(value) * factor)
        elif isinstance(value, (tuple, list)):
            return [cls.scale(v, widget) for v in value]
        return value


# Auto-activate DPI awareness early
ScalingTracker.activate_high_dpi_awareness()


# ============================================================================
# Self-Contained Modern Blend2D Widgets
# ============================================================================

class Widget(tk.Label):
    """
    Base class for interactive vector-drawn Tkinter widgets powered by Blend2D.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 120,
        height: int = 40,
        bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._logical_w = max(1, width)
        self._logical_h = max(1, height)
        self._scale = ScalingTracker.get_scaling_factor(master)

        self._widget_w = max(1, int(self._logical_w * self._scale))
        self._widget_h = max(1, int(self._logical_h * self._scale))
        self._bg_window = bg

        self._photo = tk.PhotoImage(master=master, width=self._widget_w, height=self._widget_h)
        self._surface = Surface(self._widget_w, self._widget_h)

        self._is_hovered = False
        self._is_pressed = False
        self._is_disabled = False

        super().__init__(
            master,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            background=bg,
            **kwargs,
        )

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

        self.after_idle(self.render)

    @property
    def surface(self) -> Surface:
        return self._surface

    @property
    def photo(self) -> tk.PhotoImage:
        return self._photo

    def set_parent_bg(self, bg: str) -> None:
        self._bg_window = bg
        self._parent_bg = bg
        try:
            self.configure(background=bg)
        except Exception:
            pass
        self.render()

    def _on_configure(self, event) -> None:
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        if new_w != self._widget_w or new_h != self._widget_h:
            self._widget_w = new_w
            self._widget_h = new_h
            self._photo.configure(width=self._widget_w, height=self._widget_h)
            self._surface.resize(self._widget_w, self._widget_h)
            self.render()

    def _on_enter(self, event) -> None:
        if not self._is_disabled:
            self._is_hovered = True
            self.render()

    def _on_leave(self, event) -> None:
        if not self._is_disabled:
            self._is_hovered = False
            self._is_pressed = False
            self.render()

    def _on_press(self, event) -> None:
        if not self._is_disabled:
            self._is_pressed = True
            self.render()

    def _on_release(self, event) -> None:
        if not self._is_disabled:
            self._is_pressed = False
            self.render()

    def render(self) -> None:
        """Override in subclasses to draw vector UI."""
        self._surface.clear("#00000000")
        self._surface.blit(self._photo)


class Frame(tk.Frame):
    """
    Modern container with dynamic corner radius, customizable border,
    and elevation / soft drop shadow.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 200,
        height: int = 150,
        rx: float = 16.0,
        ry: float = 16.0,
        bg_color: ColorLike = "#1e1e2e",
        border_color: ColorLike = "#313244",
        border_width: float = 1.0,
        elevation: float = 8.0,
        shadow_color: ColorLike = "#00000066",
        shadow_offset_y: float = 4.0,
        parent_bg: str = "#11111b",
        **kwargs,
    ):
        self._scale = ScalingTracker.get_scaling_factor(master)
        super().__init__(
            master,
            width=max(1, int(width * self._scale)),
            height=max(1, int(height * self._scale)),
            background=parent_bg,
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._widget_w = max(1, int(width * self._scale))
        self._widget_h = max(1, int(height * self._scale))
        self._rx = rx * self._scale
        self._ry = ry * self._scale
        self._bg_color = bg_color
        self._border_color = border_color
        self._border_width = max(1.0, border_width * self._scale)
        self._elevation = elevation * self._scale
        self._shadow_color = shadow_color
        self._shadow_offset_y = shadow_offset_y * self._scale
        self._parent_bg = parent_bg

        # Background Label with Blend2D PhotoImage
        self._photo = tk.PhotoImage(master=self, width=self._widget_w, height=self._widget_h)
        self._surface = Surface(self._widget_w, self._widget_h)

        self._bg_label = tk.Label(
            self,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            background=parent_bg,
        )
        self._bg_label.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._bg_label.lower()

        self.bind("<Configure>", self._on_configure)
        self.after_idle(self.render)

    def _on_configure(self, event) -> None:
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        if new_w != self._widget_w or new_h != self._widget_h:
            self._widget_w = new_w
            self._widget_h = new_h
            self._photo.configure(width=self._widget_w, height=self._widget_h)
            self._surface.resize(self._widget_w, self._widget_h)
            self.render()

    def set_background(self, bg_color: ColorLike) -> None:
        self._bg_color = bg_color
        self.render()

    def set_theme_colors(self, bg_color: ColorLike, border_color: ColorLike, parent_bg: str) -> None:
        self._bg_color = bg_color
        self._border_color = border_color
        self._parent_bg = parent_bg
        try:
            self.configure(background=parent_bg)
            if hasattr(self, "_bg_label"):
                self._bg_label.configure(background=parent_bg)
        except Exception:
            pass
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        pad = max(4.0 * self._scale, self._elevation * 0.8)
        draw_x = pad
        draw_y = pad
        draw_w = max(1.0, self._widget_w - pad * 2.0)
        draw_h = max(1.0, self._widget_h - pad * 2.0)

        self._surface.draw_card(
            x=draw_x,
            y=draw_y,
            w=draw_w,
            h=draw_h,
            rx=self._rx,
            ry=self._ry,
            bg_color=self._bg_color,
            border_color=self._border_color,
            border_width=self._border_width,
            shadow_blur=self._elevation * 1.5,
            shadow_spread=0.0,
            shadow_offset_x=0.0,
            shadow_offset_y=self._shadow_offset_y,
            shadow_color=self._shadow_color,
        )
        self._surface.blit(self._photo)


class Card(Frame):
    """
    High-fidelity Card container with elevation drop shadow and optional title.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: str = "",
        width: int = 280,
        height: int = 180,
        rx: float = 16.0,
        ry: float = 16.0,
        bg_color: ColorLike = "#181825",
        border_color: ColorLike = "#313244",
        border_width: float = 1.0,
        elevation: float = 12.0,
        shadow_color: ColorLike = "#00000088",
        parent_bg: str = "#11111b",
        **kwargs,
    ):
        super().__init__(
            master=master,
            width=width,
            height=height,
            rx=rx,
            ry=ry,
            bg_color=bg_color,
            border_color=border_color,
            border_width=border_width,
            elevation=elevation,
            shadow_color=shadow_color,
            parent_bg=parent_bg,
            **kwargs,
        )
        self._title = title

    def render(self) -> None:
        super().render()
        if self._title:
            pad = max(4.0 * self._scale, self._elevation * 0.8)
            pal = get_theme()
            self._surface.draw_text(
                self._title,
                x=pad + 16.0 * self._scale,
                y=pad + 28.0 * self._scale,
                font_size=15.0 * self._scale,
                font_family="sans-serif",
                color=pal.fg,
            )
            self._surface.blit(self._photo)


class Button(Widget):
    """
    Modern Button with hover/press elevation animations, gradients,
    soft drop shadows, antialiased typography, and click callback.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Button",
        command: Optional[Callable[[], None]] = None,
        width: int = 130,
        height: int = 42,
        rx: float = 10.0,
        ry: float = 10.0,
        bg_color: ColorLike = "#89b4fa",
        hover_color: ColorLike = "#b4befe",
        press_color: ColorLike = "#74c7ec",
        text_color: ColorLike = "#11111b",
        font_size: float = 14.0,
        font_family: str = "sans-serif",
        elevation: float = 6.0,
        shadow_color: ColorLike = "#00000055",
        parent_bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._text = text
        self._command = command
        scale = ScalingTracker.get_scaling_factor(master)
        self._rx = rx * scale
        self._ry = ry * scale
        self._bg_color = bg_color
        self._hover_color = hover_color
        self._press_color = press_color
        self._text_color = text_color
        self._font_size = font_size * scale
        self._font_family = font_family
        self._elevation = elevation * scale
        self._shadow_color = shadow_color
        self._parent_bg = parent_bg

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            **kwargs,
        )

        self.bind("<ButtonRelease-1>", self._handle_click)

    def _handle_click(self, event) -> None:
        if not self._is_disabled and self._command:
            if 0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h:
                self._command()

    def set_text(self, text: str) -> None:
        self._text = text
        self.render()

    def set_theme_colors(self, bg_color: ColorLike, hover_color: ColorLike, press_color: ColorLike, text_color: ColorLike, parent_bg: str) -> None:
        self._bg_color = bg_color
        self._hover_color = hover_color
        self._press_color = press_color
        self._text_color = text_color
        self.set_parent_bg(parent_bg)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        cur_bg = self._bg_color
        cur_elev = self._elevation
        offset_y = 2.0 * self._scale

        if self._is_pressed:
            cur_bg = self._press_color
            cur_elev = max(1.0, self._elevation * 0.4)
            offset_y = 1.0 * self._scale
        elif self._is_hovered:
            cur_bg = self._hover_color
            cur_elev = self._elevation * 1.3
            offset_y = 3.0 * self._scale

        pad = 4.0 * self._scale
        btn_w = self._widget_w - pad * 2.0
        btn_h = self._widget_h - pad * 2.0

        self._surface.draw_card(
            x=pad,
            y=pad,
            w=btn_w,
            h=btn_h,
            rx=self._rx,
            ry=self._ry,
            bg_color=cur_bg,
            border_color="#ffffff22",
            border_width=1.0,
            shadow_blur=cur_elev * 1.5,
            shadow_spread=0.0,
            shadow_offset_x=0.0,
            shadow_offset_y=offset_y,
            shadow_color=self._shadow_color,
        )

        text_x = self._widget_w / 2.0
        text_y = self._widget_h / 2.0 + (self._font_size * 0.35)
        if self._is_pressed:
            text_y += 1.0

        self._surface.draw_text(
            self._text,
            x=text_x,
            y=text_y,
            font_size=self._font_size,
            font_family=self._font_family,
            color=self._text_color,
            align="center",
        )
        self._surface.blit(self._photo)


class Progressbar(Widget):
    """
    Antialiased smooth progress bar with gradient fill and rounded capsule geometry.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 16,
        value: float = 0.0,
        track_color: ColorLike = "#313244",
        fill_color_start: ColorLike = "#89b4fa",
        fill_color_end: ColorLike = "#cba6f7",
        parent_bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._value = max(0.0, min(100.0, float(value)))
        self._track_color = track_color
        self._fill_start = fill_color_start
        self._fill_end = fill_color_end
        self._parent_bg = parent_bg

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            **kwargs,
        )

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = max(0.0, min(100.0, float(val)))
        self.render()

    def set_value(self, val: float) -> None:
        self.value = val

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        pad = 2.0 * self._scale
        r = (self._widget_h - pad * 2.0) / 2.0
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0

        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, self._track_color)

        if self._value > 0.5:
            fill_w = max(r * 2.0, (self._value / 100.0) * w)
            grad = LinearGradient(pad, pad, pad + fill_w, pad)
            grad.add_stop(0.0, self._fill_start)
            grad.add_stop(1.0, self._fill_end)
            self._surface.fill_rounded_rect(pad, pad, fill_w, h, r, r, grad)

        self._surface.blit(self._photo)


class Scale(Widget):
    """
    Smooth interactive slider with custom track, glowing knob, and value callback.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 28,
        min_val: float = 0.0,
        max_val: float = 100.0,
        value: float = 50.0,
        on_change: Optional[Callable[[float], None]] = None,
        track_color: ColorLike = "#313244",
        active_track_color: ColorLike = "#89b4fa",
        knob_color: ColorLike = "#f5e0dc",
        knob_radius: float = 9.0,
        parent_bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._min = min_val
        self._max = max_val
        self._value = max(min_val, min(max_val, float(value)))
        self._on_change = on_change
        self._track_color = track_color
        self._active_track_color = active_track_color
        self._knob_color = knob_color
        scale = ScalingTracker.get_scaling_factor(master)
        self._knob_r = knob_radius * scale
        self._parent_bg = parent_bg

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            **kwargs,
        )

        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Button-1>", self._on_drag)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = max(self._min, min(self._max, float(val)))
        self.render()

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
        self._surface.clear(self._parent_bg)

        pad = self._knob_r + 4.0 * self._scale
        track_h = 6.0 * self._scale
        track_y = (self._widget_h - track_h) / 2.0
        usable_w = self._widget_w - pad * 2.0

        self._surface.fill_rounded_rect(
            pad, track_y, usable_w, track_h, track_h / 2.0, track_h / 2.0, self._track_color
        )

        rel = (self._value - self._min) / (self._max - self._min) if self._max > self._min else 0.0
        knob_cx = pad + rel * usable_w
        if rel > 0.0:
            self._surface.fill_rounded_rect(
                pad, track_y, rel * usable_w, track_h, track_h / 2.0, track_h / 2.0, self._active_track_color
            )

        self._surface.draw_shadow(
            knob_cx - self._knob_r,
            (self._widget_h / 2.0) - self._knob_r,
            self._knob_r * 2.0,
            self._knob_r * 2.0,
            self._knob_r,
            self._knob_r,
            blur_radius=6.0 * self._scale,
            offset_y=2.0 * self._scale,
            shadow_color="#00000066",
        )

        self._surface.fill_circle(knob_cx, self._widget_h / 2.0, self._knob_r, self._knob_color)
        self._surface.stroke_circle(knob_cx, self._widget_h / 2.0, self._knob_r, "#ffffff88", stroke_width=1.5)

        self._surface.blit(self._photo)


class Switch(Widget):
    """
    Modern iOS / Fluent-style toggle switch with smooth pill knob.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 56,
        height: int = 30,
        is_on: bool = False,
        on_toggle: Optional[Callable[[bool], None]] = None,
        on_color: ColorLike = "#a6e3a1",
        off_color: ColorLike = "#313244",
        knob_color: ColorLike = "#ffffff",
        parent_bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._is_on = is_on
        self._on_toggle = on_toggle
        self._on_color = on_color
        self._off_color = off_color
        self._knob_color = knob_color
        self._parent_bg = parent_bg

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            **kwargs,
        )

        self.bind("<ButtonRelease-1>", self._handle_toggle)

    @property
    def is_on(self) -> bool:
        return self._is_on

    @is_on.setter
    def is_on(self, val: bool) -> None:
        self._is_on = bool(val)
        self.render()

    def toggle(self) -> None:
        self._is_on = not self._is_on
        self.render()
        if self._on_toggle:
            self._on_toggle(self._is_on)

    def _handle_toggle(self, event) -> None:
        if not self._is_disabled:
            if 0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h:
                self.toggle()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        pad = 2.0 * self._scale
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        r = h / 2.0

        bg = self._on_color if self._is_on else self._off_color
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, bg)

        knob_r = r - 3.0 * self._scale
        knob_cy = pad + r
        knob_cx = (pad + w - r) if self._is_on else (pad + r)

        self._surface.draw_shadow(
            knob_cx - knob_r,
            knob_cy - knob_r,
            knob_r * 2.0,
            knob_r * 2.0,
            knob_r,
            knob_r,
            blur_radius=4.0 * self._scale,
            offset_y=1.5 * self._scale,
            shadow_color="#00000055",
        )

        self._surface.fill_circle(knob_cx, knob_cy, knob_r, self._knob_color)
        self._surface.blit(self._photo)


# ============================================================================
# Main Showcase Application
# ============================================================================

class ShowcaseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend Modern Vector Canvas Showcase")
        self._scale = ScalingTracker.get_scaling_factor(root)

        w = int(1100 * self._scale)
        h = int(720 * self._scale)
        min_w = int(900 * self._scale)
        min_h = int(600 * self._scale)

        self.root.geometry(f"{w}x{h}")
        self.root.minsize(min_w, min_h)
        pal = get_theme()
        self.root.configure(bg=pal.bg)

        self._start_time = time.perf_counter()
        self._fps_frames = 0
        self._fps_last_time = time.perf_counter()
        self._fps = 60.0

        # Main Layout: Sidebar & Content Area
        sidebar_w = int(300 * self._scale)
        pad = int(12 * self._scale)

        self.sidebar = tk.Frame(root, bg=pal.surface, width=sidebar_w)
        self.sidebar.pack(side="left", fill="y", padx=pad, pady=pad)
        self.sidebar.pack_propagate(False)

        self.content = tk.Frame(root, bg=pal.bg)
        self.content.pack(side="right", fill="both", expand=True, padx=pad, pady=pad)

        self._setup_sidebar()
        self._setup_content()

    def _setup_sidebar(self):
        s = self._scale
        pal = get_theme()
        card_bg = pal.surface if pal.dark_mode else pal.card_bg

        # Header Card
        self.header_card = Card(
            self.sidebar,
            title="",
            width=276,
            height=90,
            rx=16,
            ry=16,
            bg_color=card_bg,
            border_color=pal.card_border,
            border_width=1.0,
            elevation=10.0,
            parent_bg=pal.surface,
        )
        self.header_card.pack(fill="x", pady=(0, int(10 * s)))

        # Title Label within card
        self.lbl_title = tk.Label(
            self.header_card,
            text="tkblend Engine",
            font=("DejaVu Sans", int(16 * s), "bold"),
            fg=pal.fg,
            bg=card_bg,
        )
        self.lbl_title.pack(anchor="w", padx=int(16 * s), pady=(int(16 * s), int(2 * s)))

        self.lbl_sub = tk.Label(
            self.header_card,
            text="Blend2D + Tk_PhotoPutBlock",
            font=("DejaVu Sans", int(10 * s)),
            fg=pal.text_muted,
            bg=card_bg,
        )
        self.lbl_sub.pack(anchor="w", padx=int(16 * s))

        # Theme Switcher Segmented Control
        self.theme_switcher = SegmentedControl(
            self.sidebar,
            values=["🌙 Dark", "☀️ Light"],
            selected_index=0 if pal.dark_mode else 1,
            on_change=self._on_theme_switch,
            width=276,
            height=34,
            parent_bg=pal.surface,
        )
        self.theme_switcher.pack(fill="x", pady=(0, int(12 * s)))

        # Controls Section
        self.ctrl_card = Card(
            self.sidebar,
            title="",
            width=276,
            height=540,
            rx=16,
            ry=16,
            bg_color=card_bg,
            border_color=pal.card_border,
            border_width=1.0,
            elevation=10.0,
            parent_bg=pal.surface,
        )
        self.ctrl_card.pack(fill="both", expand=True)

        # Action Buttons
        self.lbl_actions = tk.Label(
            self.ctrl_card,
            text="Interactive Widgets",
            font=("DejaVu Sans", int(12 * s), "bold"),
            fg=pal.fg,
            bg=card_bg,
        )
        self.lbl_actions.pack(anchor="w", padx=int(16 * s), pady=(int(16 * s), int(12 * s)))

        self.btn_primary = Button(
            self.ctrl_card,
            text="Primary Action",
            command=self._on_btn_click,
            width=244,
            height=42,
            rx=12,
            ry=12,
            bg_color=pal.primary,
            hover_color=pal.primary_hover,
            press_color=pal.primary_active,
            text_color=pal.primary_fg,
            font_size=13.0,
            elevation=6.0,
            parent_bg=card_bg,
        )
        self.btn_primary.pack(fill="x", padx=int(16 * s), pady=int(6 * s))

        self.btn_secondary = Button(
            self.ctrl_card,
            text="Accent Action",
            command=self._on_accent_click,
            width=244,
            height=42,
            rx=12,
            ry=12,
            bg_color=pal.accent,
            hover_color=pal.primary_hover,
            press_color=pal.accent,
            text_color="#ffffff" if not pal.dark_mode else "#11111b",
            font_size=13.0,
            elevation=6.0,
            parent_bg=card_bg,
        )
        self.btn_secondary.pack(fill="x", padx=int(16 * s), pady=int(6 * s))

        # Progress Section
        self.lbl_progress = tk.Label(
            self.ctrl_card,
            text="Vector Progress",
            font=("DejaVu Sans", int(11 * s), "bold"),
            fg=pal.fg,
            bg=card_bg,
        )
        self.lbl_progress.pack(anchor="w", padx=int(16 * s), pady=(int(16 * s), int(6 * s)))

        self.progress_bar = Progressbar(
            self.ctrl_card,
            width=244,
            height=14,
            value=65.0,
            fill_color_start="#f38ba8",
            fill_color_end="#fab387",
            parent_bg=card_bg,
        )
        self.progress_bar.pack(fill="x", padx=int(16 * s), pady=int(4 * s))

        # Slider Section
        self.lbl_slider = tk.Label(
            self.ctrl_card,
            text="Elevation & Radius Slider",
            font=("DejaVu Sans", int(11 * s), "bold"),
            fg=pal.fg,
            bg=card_bg,
        )
        self.lbl_slider.pack(anchor="w", padx=int(16 * s), pady=(int(16 * s), int(6 * s)))

        self.slider = Scale(
            self.ctrl_card,
            width=244,
            height=28,
            min_val=5.0,
            max_val=40.0,
            value=20.0,
            on_change=self._on_slider_change,
            active_track_color=pal.accent,
            knob_color="#f5e0dc" if pal.dark_mode else "#ffffff",
            parent_bg=card_bg,
        )
        self.slider.pack(fill="x", padx=int(16 * s), pady=int(4 * s))

        # Toggle Switch Section
        self.switch_frame = tk.Frame(self.ctrl_card, bg=card_bg)
        self.switch_frame.pack(fill="x", padx=int(16 * s), pady=(int(20 * s), int(8 * s)))

        self.lbl_switch = tk.Label(
            self.switch_frame,
            text="Animated Wave Mode",
            font=("DejaVu Sans", int(11 * s)),
            fg=pal.fg,
            bg=card_bg,
        )
        self.lbl_switch.pack(side="left")

        self.switch = Switch(
            self.switch_frame,
            width=54,
            height=28,
            is_on=True,
            on_toggle=self._on_switch_toggle,
            on_color=pal.success,
            off_color=pal.track_bg,
            parent_bg=card_bg,
        )
        self.switch.pack(side="right")

    def _on_theme_switch(self, idx: int, name: str):
        theme_name = "dark" if idx == 0 else "light"
        set_theme(theme_name)
        pal = get_theme()
        self._apply_theme(pal)

    def _apply_theme(self, pal: Palette):
        self.root.configure(bg=pal.bg)
        self.sidebar.configure(bg=pal.surface)
        self.content.configure(bg=pal.bg)
        self.canvas.configure(bg=pal.bg)

        self.theme_switcher.set_parent_bg(pal.surface)

        card_bg = pal.surface if pal.dark_mode else pal.card_bg
        border_col = pal.card_border

        self.header_card.set_theme_colors(card_bg, border_col, pal.surface)
        self.lbl_title.configure(bg=card_bg, fg=pal.fg)
        self.lbl_sub.configure(bg=card_bg, fg=pal.text_muted)

        self.ctrl_card.set_theme_colors(card_bg, border_col, pal.surface)
        self.lbl_actions.configure(bg=card_bg, fg=pal.fg)
        self.lbl_progress.configure(bg=card_bg, fg=pal.fg)
        self.lbl_slider.configure(bg=card_bg, fg=pal.fg)
        self.switch_frame.configure(bg=card_bg)
        self.lbl_switch.configure(bg=card_bg, fg=pal.fg)

        self.btn_primary.set_theme_colors(
            bg_color=pal.primary,
            hover_color=pal.primary_hover,
            press_color=pal.primary_active,
            text_color=pal.primary_fg,
            parent_bg=card_bg,
        )
        self.btn_secondary.set_theme_colors(
            bg_color=pal.accent,
            hover_color=pal.primary_hover,
            press_color=pal.accent,
            text_color="#ffffff" if not pal.dark_mode else "#11111b",
            parent_bg=card_bg,
        )
        self.progress_bar.set_parent_bg(card_bg)
        self.slider.set_parent_bg(card_bg)
        self.switch.set_parent_bg(card_bg)

    def _setup_content(self):
        s = self._scale
        pal = get_theme()
        # BlendCanvas for live real-time interactive vector drawing
        self.canvas = BlendCanvas(
            self.content,
            width=int(760 * s),
            height=int(680 * s),
            bg=pal.bg,
            on_draw=self._draw_scene,
        )
        self.canvas.pack(fill="both", expand=True)

        self._anim_radius = 20.0 * s
        self._wave_active = True
        self._tick_anim()

    def _on_btn_click(self):
        self.progress_bar.value = (self.progress_bar.value + 15.0) % 100.0

    def _on_accent_click(self):
        self.progress_bar.value = 0.0

    def _on_slider_change(self, val: float):
        self._anim_radius = val * self._scale

    def _on_switch_toggle(self, state: bool):
        self._wave_active = state

    def _draw_scene(self, surf: Surface):
        w, h = surf.width, surf.height
        s = self._scale
        t = time.perf_counter() - self._start_time

        # FPS calculation
        self._fps_frames += 1
        now = time.perf_counter()
        if now - self._fps_last_time >= 0.5:
            self._fps = self._fps_frames / (now - self._fps_last_time)
            self._fps_frames = 0
            self._fps_last_time = now

        pal = get_theme()
        # 1. Background Soft Radial Glow
        surf.clear(pal.bg)
        glow_cx = w * 0.5 + math.cos(t * 0.8) * 150.0 * s
        glow_cy = h * 0.4 + math.sin(t * 0.6) * 100.0 * s
        glow_grad = RadialGradient(glow_cx, glow_cy, 0, glow_cx, glow_cy, max(w, h) * 0.7)
        if pal.dark_mode:
            glow_grad.add_stop(0.0, "#1e1e2e")
            glow_grad.add_stop(0.6, "#181825")
            glow_grad.add_stop(1.0, "#11111b")
        else:
            glow_grad.add_stop(0.0, "#ffffff")
            glow_grad.add_stop(0.6, "#f1f5f9")
            glow_grad.add_stop(1.0, "#e2e8f0")
        surf.fill_rect(0, 0, w, h, glow_grad)

        # 2. Dynamic Fluid Waves
        if self._wave_active:
            wave_cols = (
                ["#89b4fa33", "#cba6f744", "#f38ba855"]
                if pal.dark_mode
                else ["#2563eb28", "#7c3aed38", "#dc262638"]
            )
            for layer, col in enumerate(wave_cols):
                p = Path()
                p.move_to(0, h)
                p.line_to(0, h * 0.65)
                steps = 16
                for i in range(steps + 1):
                    x = (w / steps) * i
                    phase = t * 2.0 + layer * 1.5 + (i * 0.4)
                    y = h * (0.65 + layer * 0.06) + math.sin(phase) * 35.0 * s
                    p.line_to(x, y)
                p.line_to(w, h)
                p.close()
                surf.fill_path(p, col)

        # 3. Interactive Floating Glassmorphic Cards
        card_w, card_h = 220.0 * s, 140.0 * s
        card1_x = 40.0 * s
        card1_y = 60.0 * s + math.sin(t * 1.2) * 12.0 * s

        # Gradient Card 1
        card1_grad = LinearGradient(card1_x, card1_y, card1_x + card_w, card1_y + card_h)
        if pal.dark_mode:
            card1_grad.add_stop(0.0, f"{pal.card_bg[:7]}dd")
            card1_grad.add_stop(1.0, f"{pal.surface[:7]}dd")
            c1_border = f"{pal.primary[:7]}66"
            c1_shadow = "#00000055"
        else:
            card1_grad.add_stop(0.0, "#ffffffdd")
            card1_grad.add_stop(1.0, f"{pal.surface[:7]}dd")
            c1_border = f"{pal.primary[:7]}44"
            c1_shadow = "#00000010"

        surf.draw_shadow(
            card1_x, card1_y, card_w, card_h,
            self._anim_radius, self._anim_radius,
            blur_radius=self._anim_radius * 1.2,
            shadow_color=c1_shadow,
            offset_y=8.0 * s
        )
        surf.fill_rounded_rect(card1_x, card1_y, card_w, card_h, self._anim_radius, self._anim_radius, card1_grad)
        surf.stroke_rounded_rect(card1_x, card1_y, card_w, card_h, self._anim_radius, self._anim_radius, c1_border, 1.5 * s)

        surf.draw_text("Vector Card Alpha", card1_x + 20 * s, card1_y + 36 * s, font_size=15 * s, color=pal.fg)
        surf.draw_text("Anti-aliased subpixel text", card1_x + 20 * s, card1_y + 64 * s, font_size=12 * s, color=pal.text_muted)
        surf.fill_circle(card1_x + 180 * s, card1_y + 105 * s, 14 * s, pal.success)

        # Card 2 (Radial Gradient Accent)
        card2_x = 300.0 * s
        card2_y = 100.0 * s + math.cos(t * 1.4) * 12.0 * s
        surf.draw_card(
            card2_x, card2_y, card_w, card_h,
            rx=self._anim_radius, ry=self._anim_radius,
            bg_color=f"{pal.card_bg[:7]}ee" if pal.dark_mode else "#ffffffee",
            border_color=f"{pal.primary[:7]}66" if pal.dark_mode else f"{pal.primary[:7]}44",
            border_width=1.5 * s,
            shadow_blur=self._anim_radius * 1.2,
            shadow_color="#00000055" if pal.dark_mode else "#00000010",
            shadow_offset_y=8.0 * s
        )
        surf.draw_text("Zero-Copy Blit", card2_x + 20 * s, card2_y + 36 * s, font_size=15 * s, color=pal.fg)
        surf.draw_text("Direct Tk_PhotoPutBlock", card2_x + 20 * s, card2_y + 64 * s, font_size=12 * s, color=pal.text_muted)
        surf.fill_rounded_rect(card2_x + 20 * s, card2_y + 90 * s, 120 * s, 10 * s, 5 * s, 5 * s, pal.accent)

        # 4. HUD / Status Overlay
        hud_w, hud_h = 160.0 * s, 48.0 * s
        hud_x = w - hud_w - 20.0 * s
        hud_y = 20.0 * s

        surf.draw_card(
            hud_x, hud_y, hud_w, hud_h,
            rx=12 * s, ry=12 * s,
            bg_color=f"{pal.surface[:7]}cc" if pal.dark_mode else "#ffffffdd",
            border_color=f"{pal.surface_border[:7]}66" if pal.dark_mode else "#00000015",
            border_width=1.0,
            shadow_blur=8.0 * s,
            shadow_color="#00000033" if pal.dark_mode else "#0000000e",
        )
        surf.draw_text(
            f"{self._fps:.1f} FPS",
            hud_x + hud_w / 2.0,
            hud_y + hud_h / 2.0 + 5.0 * s,
            font_size=16 * s,
            color=pal.success,
            align="center",
        )

    def _tick_anim(self):
        self.canvas.redraw()
        self.root.after(16, self._tick_anim)  # ~60 FPS target


def main():
    root = tk.Tk()
    app = ShowcaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
