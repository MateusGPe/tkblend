"""
High-performance pure vector UI widgets powered by Blend2D and Tkinter PhotoImage.
Zero TTK theme dependencies. Antialiased vector rendering, High-DPI coordinate scaling,
and dynamic theming support.
"""

from __future__ import annotations
import math
import sys
import tkinter as tk
from math import floor, ceil
from typing import Optional, Callable, Union, List, Tuple, Any, Dict

from tkblend.surface import (
    Surface,
    LinearGradient,
    RadialGradient,
    Path,
    ColorLike,
    parse_color,
)
from tkblend.theme import get_theme, Palette, blend_color_hex, add_theme_listener, remove_theme_listener


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
# Base Modern Blend2D Component
# ============================================================================

class Widget(tk.Label):
    """
    Base vector widget rendering on a Blend2D Surface with zero-copy blit
    to a backing Tkinter PhotoImage. Handles DPI scaling, resize, mouse states,
    and dynamic theme notifications.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 120,
        height: int = 40,
        bg: Optional[str] = None,
        **kwargs,
    ):
        self._logical_w = max(1, width)
        self._logical_h = max(1, height)
        self._scale = ScalingTracker.get_scaling_factor(master)

        self._widget_w = max(1, int(self._logical_w * self._scale))
        self._widget_h = max(1, int(self._logical_h * self._scale))
        self._explicit_bg = bg
        self._parent_bg = bg or get_theme().bg

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
            background=self._parent_bg,
            **kwargs,
        )

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Destroy>", self._on_destroy)

        # Register for theme notifications
        add_theme_listener(self._on_theme_changed)

        self.after_idle(self.render)

    @property
    def surface(self) -> Surface:
        return self._surface

    @property
    def photo(self) -> tk.PhotoImage:
        return self._photo

    def _on_destroy(self, event) -> None:
        remove_theme_listener(self._on_theme_changed)

    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        if self._explicit_bg is None:
            self._parent_bg = palette.bg
            try:
                self.configure(background=self._parent_bg)
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
        """Override in subclasses to draw custom vector UI."""
        self._surface.clear(self._parent_bg)
        self._surface.blit(self._photo)


ModernWidget = Widget


# ============================================================================
# Containers: Frame and Card
# ============================================================================

class Frame(tk.Frame):
    """
    Modern container with dynamic corner radius, customizable border,
    and soft elevation drop shadow.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 200,
        height: int = 150,
        rx: float = 16.0,
        ry: float = 16.0,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        elevation: float = 8.0,
        shadow_color: Optional[ColorLike] = None,
        shadow_offset_y: float = 4.0,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._scale = ScalingTracker.get_scaling_factor(master)
        pal = get_theme()
        self._parent_bg = parent_bg or pal.bg
        super().__init__(
            master,
            width=max(1, int(width * self._scale)),
            height=max(1, int(height * self._scale)),
            background=self._parent_bg,
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
        self._bg_color = bg_color or pal.card_bg
        self._border_color = border_color or pal.card_border
        self._border_width = max(1.0, border_width * self._scale)
        self._elevation = elevation * self._scale
        self._shadow_color = shadow_color or pal.shadow_color
        self._shadow_offset_y = shadow_offset_y * self._scale

        self._photo = tk.PhotoImage(master=self, width=self._widget_w, height=self._widget_h)
        self._surface = Surface(self._widget_w, self._widget_h)

        self._bg_label = tk.Label(
            self,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            background=self._parent_bg,
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


ModernFrame = Frame


class Card(Frame):
    """
    Card container with elevation drop shadow and optional header title.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: str = "",
        width: int = 280,
        height: int = 180,
        rx: float = 16.0,
        ry: float = 16.0,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        elevation: float = 10.0,
        shadow_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        pal = get_theme()
        super().__init__(
            master=master,
            width=width,
            height=height,
            rx=rx,
            ry=ry,
            bg_color=bg_color or pal.surface,
            border_color=border_color or pal.card_border,
            border_width=border_width,
            elevation=elevation,
            shadow_color=shadow_color or pal.shadow_color,
            parent_bg=parent_bg or pal.bg,
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
                y=pad + 26.0 * self._scale,
                font_size=14.0 * self._scale,
                font_family="sans-serif",
                color=pal.fg,
            )
            # Divider line below title
            line_y = pad + 36.0 * self._scale
            self._surface.draw_line(
                pad + 16.0 * self._scale,
                line_y,
                self._widget_w - pad - 16.0 * self._scale,
                line_y,
                stroke=pal.card_border,
                stroke_width=1.0,
            )
            self._surface.blit(self._photo)


ModernCard = Card


# ============================================================================
# Widget 1: Button (Variants, Elevation, Text)
# ============================================================================

class Button(Widget):
    """
    Modern Button supporting variants ('primary', 'secondary', 'accent', 'destructive', 'outline'),
    micro-elevation on hover, pressed drop-depth animation, and antialiased typography.
    """

    VARIANT_COLORS: Dict[str, Dict[str, str]] = {
        "primary": {"bg": "#89b4fa", "hover": "#b4befe", "press": "#74c7ec", "fg": "#11111b", "border": "#ffffff22"},
        "secondary": {"bg": "#313244", "hover": "#45475a", "press": "#585b70", "fg": "#cdd6f4", "border": "#585b70"},
        "accent": {"bg": "#cba6f7", "hover": "#f5c2e7", "press": "#b4befe", "fg": "#11111b", "border": "#ffffff22"},
        "destructive": {"bg": "#f38ba8", "hover": "#eba0ac", "press": "#e78284", "fg": "#11111b", "border": "#ffffff22"},
        "outline": {"bg": "#18182500", "hover": "#31324466", "press": "#45475a88", "fg": "#89b4fa", "border": "#89b4fa"},
    }

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Button",
        command: Optional[Callable[[], None]] = None,
        variant: str = "primary",
        width: int = 120,
        height: int = 38,
        rx: float = 10.0,
        ry: float = 10.0,
        font_size: float = 13.0,
        elevation: float = 5.0,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._text = text
        self._command = command
        self._variant = variant if variant in self.VARIANT_COLORS else "primary"
        scale = ScalingTracker.get_scaling_factor(master)
        self._rx = rx * scale
        self._ry = ry * scale
        self._font_size = font_size * scale
        self._elevation = elevation * scale

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

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        colors = self.VARIANT_COLORS.get(self._variant, self.VARIANT_COLORS["primary"])

        cur_bg = colors["bg"]
        cur_elev = self._elevation
        offset_y = 2.0 * self._scale

        if self._is_pressed:
            cur_bg = colors["press"]
            cur_elev = max(1.0, self._elevation * 0.3)
            offset_y = 1.0 * self._scale
        elif self._is_hovered:
            cur_bg = colors["hover"]
            cur_elev = self._elevation * 1.3
            offset_y = 3.0 * self._scale

        pad = 3.0 * self._scale
        btn_w = self._widget_w - pad * 2.0
        btn_h = self._widget_h - pad * 2.0

        if self._variant != "outline" and cur_elev > 0:
            self._surface.draw_shadow(
                pad, pad, btn_w, btn_h,
                self._rx, self._ry,
                blur_radius=cur_elev * 1.5,
                offset_y=offset_y,
                shadow_color="#00000055",
            )

        self._surface.fill_rounded_rect(pad, pad, btn_w, btn_h, self._rx, self._ry, cur_bg)
        border_col = colors["border"]
        self._surface.stroke_rounded_rect(pad, pad, btn_w, btn_h, self._rx, self._ry, border_col, 1.0 * self._scale)

        text_x = self._widget_w / 2.0
        text_y = self._widget_h / 2.0 + (self._font_size * 0.35)
        if self._is_pressed:
            text_y += 1.0

        self._surface.draw_text(
            self._text,
            x=text_x,
            y=text_y,
            font_size=self._font_size,
            font_family="sans-serif",
            color=colors["fg"],
            align="center",
        )
        self._surface.blit(self._photo)


ModernButton = Button


# ============================================================================
# Widget 2: ProgressBar (Linear Capsule Gradient)
# ============================================================================

class ProgressBar(Widget):
    """
    Antialiased smooth linear progress bar with capsule geometry and gradient fill.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 16,
        value: float = 0.0,
        track_color: Optional[ColorLike] = None,
        fill_color_start: Optional[ColorLike] = None,
        fill_color_end: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._value = max(0.0, min(100.0, float(value)))
        pal = get_theme()
        self._track_color = track_color or pal.track_bg
        self._fill_start = fill_color_start or pal.primary
        self._fill_end = fill_color_end or pal.accent
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

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
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        r = h / 2.0

        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, self._track_color)

        if self._value > 0.5:
            fill_w = max(r * 2.0, (self._value / 100.0) * w)
            grad = LinearGradient(pad, pad, pad + fill_w, pad)
            grad.add_stop(0.0, self._fill_start)
            grad.add_stop(1.0, self._fill_end)
            self._surface.fill_rounded_rect(pad, pad, fill_w, h, r, r, grad)

        self._surface.blit(self._photo)


ModernProgressBar = ProgressBar


# ============================================================================
# Widget 3: CircularProgress (Radial Gauge / Donut Ring)
# ============================================================================

class CircularProgress(Widget):
    """
    Antialiased circular progress ring / radial gauge with center numeric readout.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 110,
        value: float = 65.0,
        stroke_width: float = 8.0,
        track_color: Optional[ColorLike] = None,
        fill_color: Optional[ColorLike] = None,
        unit: str = "%",
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._value = max(0.0, min(100.0, float(value)))
        self._stroke_w = stroke_width
        pal = get_theme()
        self._track_color = track_color or pal.track_bg
        self._fill_color = fill_color or pal.primary
        self._unit = unit
        super().__init__(master=master, width=size, height=size, bg=parent_bg, **kwargs)

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
        s = self._scale
        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        sw = self._stroke_w * s
        r = (min(self._widget_w, self._widget_h) - sw * 2.0) / 2.0

        if r <= 0:
            return

        # Background circular track
        self._surface.stroke_circle(cx, cy, r, self._track_color, stroke_width=sw)

        # Progress Arc using Path arc_to
        if self._value > 0.0:
            sweep = (self._value / 100.0) * (2.0 * math.pi)
            p = Path()
            p.arc_to(cx, cy, r, r, -math.pi / 2.0, sweep)
            self._surface.stroke_path(p, self._fill_color, stroke_width=sw)

        # Center Value Readout
        font_sz = 16.0 * s
        pal = get_theme()
        self._surface.draw_text(
            f"{int(self._value)}{self._unit}",
            cx,
            cy + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color=pal.fg,
            align="center",
        )
        self._surface.blit(self._photo)


ModernCircularProgress = CircularProgress


# ============================================================================
# Widget 4: Slider (Smooth Draggable Track & Glowing Knob)
# ============================================================================

class Slider(Widget):
    """
    Smooth interactive slider with custom groove track, active fill, and glowing knob.
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
        track_color: Optional[ColorLike] = None,
        active_track_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        knob_radius: float = 9.0,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._min = min_val
        self._max = max_val
        self._value = max(min_val, min(max_val, float(value)))
        self._on_change = on_change
        pal = get_theme()
        self._track_color = track_color or pal.track_bg
        self._active_track_color = active_track_color or pal.primary
        self._knob_color = knob_color or "#f5e0dc"
        scale = ScalingTracker.get_scaling_factor(master)
        self._knob_r = knob_radius * scale
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Button-1>", self._on_drag)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = max(self._min, min(self._max, float(val)))
        self.render()

    def set_value(self, val: float) -> None:
        self.value = val

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


ModernSlider = Slider


# ============================================================================
# Widget 5: RangeSlider (Dual-Knob Min/Max Selector)
# ============================================================================

class RangeSlider(Widget):
    """
    Dual-thumb vector range slider for selecting a sub-interval [low, high].
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 28,
        min_val: float = 0.0,
        max_val: float = 100.0,
        low_val: float = 20.0,
        high_val: float = 80.0,
        on_change: Optional[Callable[[float, float], None]] = None,
        track_color: Optional[ColorLike] = None,
        active_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._min = min_val
        self._max = max_val
        self._low = max(min_val, min(max_val, float(low_val)))
        self._high = max(self._low, min(max_val, float(high_val)))
        self._on_change = on_change
        pal = get_theme()
        self._track_color = track_color or pal.track_bg
        self._active_color = active_color or pal.success
        self._knob_color = knob_color or "#f5e0dc"
        scale = ScalingTracker.get_scaling_factor(master)
        self._knob_r = 8.5 * scale
        self._dragging_thumb: Optional[str] = None

        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

        self.bind("<Button-1>", self._on_press_event)
        self.bind("<B1-Motion>", self._on_drag_event)
        self.bind("<ButtonRelease-1>", self._on_release_event)

    @property
    def range(self) -> Tuple[float, float]:
        return (self._low, self._high)

    def _val_to_x(self, val: float, pad: float, usable_w: float) -> float:
        rel = (val - self._min) / (self._max - self._min) if self._max > self._min else 0.0
        return pad + rel * usable_w

    def _x_to_val(self, x: float, pad: float, usable_w: float) -> float:
        rel = max(0.0, min(1.0, (x - pad) / usable_w)) if usable_w > 0 else 0.0
        return self._min + rel * (self._max - self._min)

    def _on_press_event(self, event) -> None:
        pad = self._knob_r + 4.0 * self._scale
        usable_w = self._widget_w - pad * 2.0
        low_x = self._val_to_x(self._low, pad, usable_w)
        high_x = self._val_to_x(self._high, pad, usable_w)

        d_low = abs(event.x - low_x)
        d_high = abs(event.x - high_x)
        self._dragging_thumb = "low" if d_low <= d_high else "high"
        self._on_drag_event(event)

    def _on_drag_event(self, event) -> None:
        pad = self._knob_r + 4.0 * self._scale
        usable_w = self._widget_w - pad * 2.0
        val = self._x_to_val(event.x, pad, usable_w)

        if self._dragging_thumb == "low":
            self._low = max(self._min, min(self._high - 1.0, val))
        elif self._dragging_thumb == "high":
            self._high = min(self._max, max(self._low + 1.0, val))

        self.render()
        if self._on_change:
            self._on_change(self._low, self._high)

    def _on_release_event(self, event) -> None:
        self._dragging_thumb = None

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        pad = self._knob_r + 4.0 * self._scale
        track_h = 6.0 * self._scale
        track_y = (self._widget_h - track_h) / 2.0
        usable_w = self._widget_w - pad * 2.0

        self._surface.fill_rounded_rect(
            pad, track_y, usable_w, track_h, track_h / 2.0, track_h / 2.0, self._track_color
        )

        low_x = self._val_to_x(self._low, pad, usable_w)
        high_x = self._val_to_x(self._high, pad, usable_w)

        if high_x > low_x:
            self._surface.fill_rounded_rect(
                low_x, track_y, high_x - low_x, track_h, track_h / 2.0, track_h / 2.0, self._active_color
            )

        for cx in (low_x, high_x):
            self._surface.draw_shadow(
                cx - self._knob_r,
                (self._widget_h / 2.0) - self._knob_r,
                self._knob_r * 2.0,
                self._knob_r * 2.0,
                self._knob_r,
                self._knob_r,
                blur_radius=5.0 * self._scale,
                offset_y=1.5 * self._scale,
                shadow_color="#00000066",
            )
            self._surface.fill_circle(cx, self._widget_h / 2.0, self._knob_r, self._knob_color)
            self._surface.stroke_circle(cx, self._widget_h / 2.0, self._knob_r, "#ffffff88", stroke_width=1.2)

        self._surface.blit(self._photo)


ModernRangeSlider = RangeSlider


# ============================================================================
# Widget 6: Switch (iOS / Fluent Toggle Pill)
# ============================================================================

class Switch(Widget):
    """
    Modern iOS / Fluent style toggle switch with smooth pill knob.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 54,
        height: int = 28,
        is_on: bool = False,
        on_toggle: Optional[Callable[[bool], None]] = None,
        on_color: Optional[ColorLike] = None,
        off_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._is_on = is_on
        self._on_toggle = on_toggle
        pal = get_theme()
        self._on_color = on_color or pal.success
        self._off_color = off_color or pal.track_bg
        self._knob_color = knob_color or pal.thumb_color
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)
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
        if not self._is_disabled and 0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h:
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


ModernSwitch = Switch
ToggleSwitch = Switch


# ============================================================================
# Widget 7: Checkbox (Rounded Box with Vector Checkmark)
# ============================================================================

class Checkbox(Widget):
    """
    Antialiased vector checkbox with custom checkmark Path and label text.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Checkbox",
        checked: bool = False,
        on_change: Optional[Callable[[bool], None]] = None,
        width: int = 160,
        height: int = 28,
        active_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._text = text
        self._checked = checked
        self._on_change = on_change
        pal = get_theme()
        self._active_color = active_color or pal.primary
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)
        self.bind("<ButtonRelease-1>", self._handle_click)

    @property
    def checked(self) -> bool:
        return self._checked

    @checked.setter
    def checked(self, val: bool) -> None:
        self._checked = bool(val)
        self.render()

    def toggle(self) -> None:
        self._checked = not self._checked
        self.render()
        if self._on_change:
            self._on_change(self._checked)

    def _handle_click(self, event) -> None:
        if not self._is_disabled and 0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h:
            self.toggle()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        box_size = 18.0 * s
        box_x = 4.0 * s
        box_y = (self._widget_h - box_size) / 2.0
        r = 5.0 * s

        pal = get_theme()
        if self._checked:
            self._surface.fill_rounded_rect(box_x, box_y, box_size, box_size, r, r, self._active_color)
            p = Path()
            p.move_to(box_x + 4.5 * s, box_y + 9.0 * s)
            p.line_to(box_x + 7.5 * s, box_y + 12.5 * s)
            p.line_to(box_x + 13.5 * s, box_y + 5.5 * s)
            self._surface.stroke_path(p, pal.primary_fg, stroke_width=2.0 * s)
        else:
            border = pal.primary if self._is_hovered else pal.card_border
            bg = pal.secondary if self._is_hovered else pal.surface
            self._surface.fill_rounded_rect(box_x, box_y, box_size, box_size, r, r, bg)
            self._surface.stroke_rounded_rect(box_x, box_y, box_size, box_size, r, r, border, 1.2 * s)

        text_x = box_x + box_size + 10.0 * s
        font_sz = 13.0 * s
        self._surface.draw_text(
            self._text,
            text_x,
            self._widget_h / 2.0 + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color=pal.fg,
            align="left",
        )
        self._surface.blit(self._photo)


ModernCheckbox = Checkbox


# ============================================================================
# Widget 8: Radio & RadioGroup (Concentric Dot Radios)
# ============================================================================

class Radio(Widget):
    """
    Individual circular vector radio button with concentric animated dot indicator.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Radio",
        value: str = "",
        group: Optional["RadioGroup"] = None,
        width: int = 150,
        height: int = 28,
        active_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._text = text
        self._value = value
        self._group = group
        pal = get_theme()
        self._active_color = active_color or pal.accent
        self._selected = False
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)
        if group:
            group.register(self)
        self.bind("<ButtonRelease-1>", self._handle_click)

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, val: bool) -> None:
        self._selected = bool(val)
        self.render()

    def _handle_click(self, event) -> None:
        if not self._is_disabled and 0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h:
            if self._group:
                self._group.select(self._value)
            else:
                self._selected = True
                self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        r = 8.5 * s
        cx = 4.0 * s + r
        cy = self._widget_h / 2.0

        pal = get_theme()
        if self._selected:
            self._surface.stroke_circle(cx, cy, r, self._active_color, stroke_width=2.0 * s)
            self._surface.fill_circle(cx, cy, r * 0.52, self._active_color)
        else:
            border = self._active_color if self._is_hovered else pal.card_border
            self._surface.stroke_circle(cx, cy, r, border, stroke_width=1.5 * s)

        font_sz = 13.0 * s
        self._surface.draw_text(
            self._text,
            cx + r + 10.0 * s,
            self._widget_h / 2.0 + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color=pal.fg,
            align="left",
        )
        self._surface.blit(self._photo)


ModernRadio = Radio


class RadioGroup:
    """
    Manages mutual exclusion and selection state among a group of Radio buttons.
    """

    def __init__(self, on_change: Optional[Callable[[str], None]] = None):
        self._radios: List[Radio] = []
        self._value: str = ""
        self._on_change = on_change

    def register(self, radio: Radio) -> None:
        self._radios.append(radio)
        if not self._value:
            self._value = radio._value
            radio.selected = True

    def select(self, value: str) -> None:
        self._value = value
        for r in self._radios:
            r.selected = (r._value == value)
        if self._on_change:
            self._on_change(value)

    @property
    def value(self) -> str:
        return self._value


ModernRadioGroup = RadioGroup


# ============================================================================
# Widget 9: SegmentedControl (Elevated Sliding Pill Tab Switcher)
# ============================================================================

class SegmentedControl(Widget):
    """
    Antialiased segmented tab / pill switcher with recessed capsule track
    and elevated active indicator pill.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        values: Optional[List[str]] = None,
        selected_index: int = 0,
        on_change: Optional[Callable[[int, str], None]] = None,
        width: int = 340,
        height: int = 34,
        active_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._values = list(values) if values else ["Option 1", "Option 2"]
        self._selected = max(0, min(len(self._values) - 1, selected_index))
        self._on_change = on_change
        pal = get_theme()
        self._active_color = active_color or pal.primary
        self._hovered_index: Optional[int] = None
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave_seg)
        self.bind("<ButtonRelease-1>", self._on_click_seg)

    @property
    def selected_index(self) -> int:
        return self._selected

    @selected_index.setter
    def selected_index(self, idx: int) -> None:
        self._selected = max(0, min(len(self._values) - 1, idx))
        self.render()

    def _index_at(self, x: float) -> Optional[int]:
        if not self._values:
            return None
        pad = 3.0 * self._scale
        usable_w = self._widget_w - pad * 2.0
        seg_w = usable_w / len(self._values)
        rel_x = x - pad
        if 0 <= rel_x <= usable_w:
            return int(rel_x // seg_w)
        return None

    def _on_mouse_move(self, event) -> None:
        idx = self._index_at(event.x)
        if idx != self._hovered_index:
            self._hovered_index = idx
            self.render()

    def _on_mouse_leave_seg(self, event) -> None:
        self._hovered_index = None
        self.render()

    def _on_click_seg(self, event) -> None:
        idx = self._index_at(event.x)
        if idx is not None and idx != self._selected:
            self._selected = idx
            self.render()
            if self._on_change:
                self._on_change(idx, self._values[idx])

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        pad = 3.0 * s
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        r = h / 2.0

        pal = get_theme()
        # Recessed capsule track
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, pal.surface)
        self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, pal.surface_border, 1.0 * s)

        num_segs = max(1, len(self._values))
        seg_w = w / num_segs

        if self._hovered_index is not None and self._hovered_index != self._selected:
            hx = pad + self._hovered_index * seg_w
            self._surface.fill_rounded_rect(hx, pad, seg_w, h, r, r, pal.secondary)

        ax = pad + self._selected * seg_w
        self._surface.draw_shadow(
            ax + 1.0, pad + 1.0, seg_w - 2.0, h - 2.0,
            r, r, blur_radius=4.0 * s, offset_y=1.0 * s, shadow_color="#00000044"
        )
        self._surface.fill_rounded_rect(ax + 1.0, pad + 1.0, seg_w - 2.0, h - 2.0, r, r, self._active_color)

        font_sz = 12.0 * s
        for i, val in enumerate(self._values):
            tx = pad + (i + 0.5) * seg_w
            ty = pad + h / 2.0 + (font_sz * 0.35)
            color = pal.primary_fg if i == self._selected else pal.fg
            self._surface.draw_text(val, tx, ty, font_size=font_sz, font_family="sans-serif", color=color, align="center")

        self._surface.blit(self._photo)


ModernSegmentedControl = SegmentedControl


# ============================================================================
# Widget 10: TextInput (Focus Ring, Rounded Border, Clear Button)
# ============================================================================

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


# ============================================================================
# Widget 10b: VectorScrollbar (Pure Blend2D Vector Scrollbar)
# ============================================================================

class VectorScrollbar(Widget):
    """
    Pure Blend2D vector scrollbar widget with zero TTK dependencies.
    Renders rounded track, draggable high-contrast thumb capsule, and
    interfaces with any scrollable Tkinter widget (Canvas, Text, etc.).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        command: Optional[Callable[..., None]] = None,
        orientation: str = "vertical",
        width: int = 8,
        height: int = 120,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._command = command
        self._orientation = orientation
        self._first: float = 0.0
        self._last: float = 1.0
        self._is_dragging: bool = False
        self._drag_start_pos: float = 0.0
        self._drag_start_first: float = 0.0

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            **kwargs,
        )

        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)

    def set(self, first: Union[str, float], last: Union[str, float]) -> None:
        """Standard Tkinter scrollbar set protocol: set(first, last)."""
        try:
            self._first = max(0.0, min(1.0, float(first)))
            self._last = max(0.0, min(1.0, float(last)))
            self.render()
        except Exception:
            pass

    def _get_thumb_geometry(self) -> Tuple[float, float, float, float]:
        s = self._scale
        pad = 1.0 * s
        w = max(1.0, float(self._widget_w) - pad * 2.0)
        h = max(1.0, float(self._widget_h) - pad * 2.0)

        total_span = max(0.05, min(1.0, self._last - self._first))
        min_thumb = 18.0 * s
        thumb_h = max(min_thumb, h * total_span)
        available_travel = max(0.0, h - thumb_h)

        max_first = max(0.001, 1.0 - total_span)
        norm_first = max(0.0, min(1.0, self._first / max_first)) if max_first > 0 else 0.0
        thumb_y = pad + norm_first * available_travel

        return pad, thumb_y, w, thumb_h

    def _on_press(self, event) -> None:
        if self._is_disabled:
            return
        pad, ty, tw, th = self._get_thumb_geometry()
        py = float(event.y)

        if ty <= py <= ty + th:
            self._is_dragging = True
            self._drag_start_pos = py
            self._drag_start_first = self._first
            self.render()
        else:
            if py < ty:
                if self._command:
                    self._command("scroll", -1, "pages")
            else:
                if self._command:
                    self._command("scroll", 1, "pages")

    def _on_drag(self, event) -> None:
        if not self._is_dragging or self._is_disabled:
            return
        s = self._scale
        pad = 1.0 * s
        h = max(1.0, float(self._widget_h) - pad * 2.0)
        total_span = max(0.05, min(1.0, self._last - self._first))
        min_thumb = 18.0 * s
        thumb_h = max(min_thumb, h * total_span)
        available_travel = max(1.0, h - thumb_h)

        delta_px = float(event.y) - self._drag_start_pos
        max_first = max(0.001, 1.0 - total_span)
        delta_fraction = (delta_px / available_travel) * max_first
        new_first = max(0.0, min(max_first, self._drag_start_first + delta_fraction))

        if self._command:
            self._command("moveto", new_first)

    def _on_release(self, event) -> None:
        if self._is_dragging:
            self._is_dragging = False
            self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        pad = 1.0 * s
        w = max(1.0, float(self._widget_w) - pad * 2.0)
        h = max(1.0, float(self._widget_h) - pad * 2.0)
        r = min(w / 2.0, 4.0 * s)

        pal = get_theme()
        # Draw track with distinct contrast
        track_col = "#252538" if pal.dark_mode else "#e2e8f0"
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, track_col)

        # Draw thumb with high contrast
        _, ty, tw, th = self._get_thumb_geometry()
        thumb_r = min(tw / 2.0, 4.0 * s)

        if self._is_dragging:
            thumb_col = pal.primary
        elif self._is_hovered:
            thumb_col = "#89b4fa" if pal.dark_mode else "#3b82f6"
        else:
            thumb_col = "#6c7086" if pal.dark_mode else "#94a3b8"

        self._surface.fill_rounded_rect(pad, ty, tw, th, thumb_r, thumb_r, thumb_col)
        self._surface.blit(self._photo)


ModernScrollbar = VectorScrollbar
Scrollbar = VectorScrollbar


# ============================================================================
# Widget 11: Dropdown & DropdownItem (Vector Combobox / Select with Popup)
# ============================================================================

class DropdownItem(Widget):
    """
    Lightweight vector row widget for modern dropdown popup items.
    Renders rounded hover highlight pill, clean typography, and selected checkmark
    with vibrant, high-contrast theme styling.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        is_selected: bool = False,
        on_select: Optional[Callable[[str], None]] = None,
        width: int = 180,
        height: int = 32,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._text = text
        self._is_selected = is_selected
        self._on_select = on_select
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)
        self.bind("<ButtonRelease-1>", self._handle_click)

    @property
    def text(self) -> str:
        return self._text

    @property
    def is_selected(self) -> bool:
        return self._is_selected

    def set_selected(self, val: bool) -> None:
        if self._is_selected != val:
            self._is_selected = val
            self.render()

    def _handle_click(self, event) -> None:
        if not self._is_disabled and self._on_select:
            self._on_select(self._text)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        w = float(self._widget_w)
        h = float(self._widget_h)
        pal = get_theme()

        pad_x = 4.0 * s
        pad_y = 2.0 * s
        pill_w = max(1.0, w - pad_x * 2.0)
        pill_h = max(1.0, h - pad_y * 2.0)
        r = 6.0 * s

        # High-contrast states
        if self._is_selected:
            if pal.dark_mode:
                sel_bg = "#2a3d66" if not self._is_hovered else "#344c7d"
                sel_border = pal.primary
                text_color = "#ffffff"
                chk_color = pal.primary
            else:
                sel_bg = blend_color_hex(pal.primary, "#ffffff", 0.25)
                sel_border = pal.primary
                text_color = pal.primary
                chk_color = pal.primary

            self._surface.fill_rounded_rect(pad_x, pad_y, pill_w, pill_h, r, r, sel_bg)
            self._surface.stroke_rounded_rect(pad_x, pad_y, pill_w, pill_h, r, r, sel_border, 1.2 * s)

        elif self._is_hovered:
            hover_bg = "#383a52" if pal.dark_mode else "#e2e8f0"
            hover_border = "#585b70" if pal.dark_mode else "#cbd5e1"
            text_color = "#ffffff" if pal.dark_mode else "#0f172a"
            self._surface.fill_rounded_rect(pad_x, pad_y, pill_w, pill_h, r, r, hover_bg)
            self._surface.stroke_rounded_rect(pad_x, pad_y, pill_w, pill_h, r, r, hover_border, 1.0 * s)

        else:
            text_color = pal.fg if pal.dark_mode else "#1e293b"

        # Typography
        font_sz = 12.5 * s
        text_x = pad_x + 12.0 * s
        text_y = h / 2.0 + (font_sz * 0.35)
        self._surface.draw_text(
            self._text,
            text_x,
            text_y,
            font_size=font_sz,
            font_family="sans-serif",
            color=text_color,
            align="left",
        )

        # Draw vector checkmark on the right if selected
        if self._is_selected:
            chk_x = w - pad_x - 14.0 * s
            chk_y = h / 2.0
            p = Path()
            p.move_to(chk_x - 4.5 * s, chk_y - 0.5 * s)
            p.line_to(chk_x - 1.0 * s, chk_y + 3.0 * s)
            p.line_to(chk_x + 5.0 * s, chk_y - 3.5 * s)
            self._surface.stroke_path(p, chk_color, stroke_width=2.2 * s)

        self._surface.blit(self._photo)


class Dropdown(Widget):
    """
    Vector dropdown select with current value, animated chevron icon,
    and elevated popup option picker featuring modular vector item rows.
    Supports keyboard navigation, auto-flip positioning, and visible high-contrast VectorScrollbar.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        options: Optional[List[str]] = None,
        selected: Optional[str] = None,
        on_select: Optional[Callable[[str], None]] = None,
        width: int = 180,
        height: int = 36,
        max_visible_items: int = 6,
        placeholder: str = "Select...",
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._dropdown_items = list(options) if options else ["Option A", "Option B"]
        self._selected = selected if selected in self._dropdown_items else (self._dropdown_items[0] if self._dropdown_items else "")
        self._on_select = on_select
        self._max_visible_items = max(1, max_visible_items)
        self._placeholder = placeholder
        self._is_open = False
        self._is_focused = False
        self._popup_win: Optional[tk.Toplevel] = None
        self._item_widgets: List[DropdownItem] = []
        self._scroll_canvas: Optional[tk.Canvas] = None
        self._scrollbar: Optional[VectorScrollbar] = None
        self._root_bind_id: Optional[str] = None
        self._parent_bind_id: Optional[str] = None
        self._escape_bind_id: Optional[str] = None
        self._root_focus_bind_id: Optional[str] = None

        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

        # Enable keyboard focus and bindings
        self.configure(takefocus=1)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<KeyPress-Down>", self._on_key_down)
        self.bind("<KeyPress-Up>", self._on_key_up)
        self.bind("<Return>", self._on_key_enter)
        self.bind("<space>", self._on_key_enter)
        self.bind("<Escape>", lambda e: self._close_popup())
        self.bind("<Home>", self._on_key_home)
        self.bind("<End>", self._on_key_end)
        self.bind("<ButtonRelease-1>", self._handle_click)

    @property
    def value(self) -> str:
        return self._selected

    @value.setter
    def value(self, val: str) -> None:
        self._selected = val
        self.render()
        if self._is_open:
            self._update_item_states()

    @property
    def options(self) -> List[str]:
        return list(self._dropdown_items)

    @options.setter
    def options(self, new_opts: List[str]) -> None:
        self._dropdown_items = list(new_opts) if new_opts else []
        if self._selected not in self._dropdown_items:
            self._selected = self._dropdown_items[0] if self._dropdown_items else ""
        self.render()

    def set_options(self, options: List[str], selected: Optional[str] = None) -> None:
        """Update options list and optionally choose selected item."""
        self._dropdown_items = list(options) if options else []
        if selected and selected in self._dropdown_items:
            self._selected = selected
        elif self._dropdown_items:
            self._selected = self._dropdown_items[0]
        else:
            self._selected = ""
        self.render()

    def _handle_click(self, event) -> None:
        if self._is_disabled:
            return
        self._is_pressed = False
        try:
            self.focus_set()
        except Exception:
            pass
        self._toggle_popup(event)

    def _on_focus_in(self, event) -> None:
        self._is_focused = True
        self.render()

    def _on_focus_out(self, event) -> None:
        self._is_focused = False
        self.render()

    def _on_key_down(self, event) -> str:
        if not self._dropdown_items:
            return "break"
        idx = self._dropdown_items.index(self._selected) if self._selected in self._dropdown_items else -1
        new_idx = min(len(self._dropdown_items) - 1, idx + 1)
        self._select_option(self._dropdown_items[new_idx], notify=True, close=False)
        if self._is_open:
            self._scroll_item_into_view(new_idx)
        return "break"

    def _on_key_up(self, event) -> str:
        if not self._dropdown_items:
            return "break"
        idx = self._dropdown_items.index(self._selected) if self._selected in self._dropdown_items else 0
        new_idx = max(0, idx - 1)
        self._select_option(self._dropdown_items[new_idx], notify=True, close=False)
        if self._is_open:
            self._scroll_item_into_view(new_idx)
        return "break"

    def _on_key_home(self, event) -> str:
        if self._dropdown_items:
            self._select_option(self._dropdown_items[0], notify=True, close=False)
            if self._is_open:
                self._scroll_item_into_view(0)
        return "break"

    def _on_key_end(self, event) -> str:
        if self._dropdown_items:
            last_idx = len(self._dropdown_items) - 1
            self._select_option(self._dropdown_items[last_idx], notify=True, close=False)
            if self._is_open:
                self._scroll_item_into_view(last_idx)
        return "break"

    def _on_key_enter(self, event) -> str:
        if self._is_open:
            self._close_popup()
        else:
            self._open_popup()
        return "break"

    def _toggle_popup(self, event=None) -> None:
        if self._is_open:
            self._close_popup()
        else:
            self._open_popup()

    def _scroll_item_into_view(self, idx: int) -> None:
        if self._scroll_canvas and len(self._dropdown_items) > self._max_visible_items:
            total = len(self._dropdown_items)
            frac = idx / max(1, total - 1)
            self._scroll_canvas.yview_moveto(max(0.0, min(1.0, frac - 0.2)))

    def _open_popup(self) -> None:
        if self._is_open:
            return
        self._is_open = True
        self.render()

        self.update_idletasks()
        rx = self.winfo_rootx()
        ry = self.winfo_rooty()
        rw = self._widget_w
        rh = self._widget_h
        s = self._scale

        item_h = max(24, int(32 * s))
        total_items = len(self._dropdown_items)
        visible_count = min(total_items, self._max_visible_items)
        pop_pad = int(4 * s)
        pop_h = visible_count * item_h + pop_pad * 2 + int(4 * s)

        screen_h = self.winfo_screenheight()
        space_below = screen_h - (ry + rh + int(4 * s))

        # Auto-flip upward if not enough room below
        if space_below < pop_h and ry > pop_h:
            pop_y = ry - pop_h - int(4 * s)
        else:
            pop_y = ry + rh + int(4 * s)

        pop_x = max(0, rx)
        pop_w = rw

        pal = get_theme()
        toplevel = self.winfo_toplevel()

        border_col = "#585b70" if pal.dark_mode else "#94a3b8"
        popup_bg = "#1e1e2e" if pal.dark_mode else "#ffffff"

        self._popup_win = tk.Toplevel(self)
        self._popup_win.wm_overrideredirect(True)
        try:
            self._popup_win.transient(toplevel)
        except Exception:
            pass
        self._popup_win.geometry(f"{pop_w}x{pop_h}+{pop_x}+{pop_y}")
        self._popup_win.configure(bg=border_col)

        # Border container frame for crisp 1.5px border
        border_frame = tk.Frame(self._popup_win, bg=border_col, padx=1, pady=1)
        border_frame.pack(fill="both", expand=True)

        inner_frame = tk.Frame(border_frame, bg=popup_bg)
        inner_frame.pack(fill="both", expand=True)

        self._item_widgets = []

        # If items exceed max_visible_items, use a scrollable canvas with high-contrast VectorScrollbar
        if total_items > self._max_visible_items:
            scrollbar_w = int(10 * s)
            content_w = max(10, pop_w - scrollbar_w - int(10 * s))

            canvas = tk.Canvas(
                inner_frame,
                bg=popup_bg,
                highlightthickness=0,
                bd=0,
                width=content_w,
                height=visible_count * item_h,
            )

            scrollbar = VectorScrollbar(
                inner_frame,
                command=canvas.yview,
                width=10,
                height=int((visible_count * item_h) / s),
                parent_bg=popup_bg,
            )
            canvas.configure(yscrollcommand=scrollbar.set)

            scrollbar.pack(side="right", fill="y", padx=(int(2 * s), int(4 * s)), pady=int(3 * s))
            canvas.pack(side="left", fill="both", expand=True, padx=(int(4 * s), int(2 * s)), pady=int(3 * s))
            self._scroll_canvas = canvas
            self._scrollbar = scrollbar

            scroll_frame = tk.Frame(canvas, bg=popup_bg)
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=content_w)

            def _on_frame_configure(e):
                canvas.configure(scrollregion=canvas.bbox("all"))

            scroll_frame.bind("<Configure>", _on_frame_configure)

            def _on_wheel(e):
                if sys.platform == "darwin":
                    canvas.yview_scroll(int(-1 * e.delta), "units")
                elif sys.platform.startswith("win"):
                    canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
                else:
                    if getattr(e, "num", None) == 4:
                        canvas.yview_scroll(-2, "units")
                    elif getattr(e, "num", None) == 5:
                        canvas.yview_scroll(2, "units")
                    elif hasattr(e, "delta") and e.delta:
                        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
                return "break"

            canvas.bind("<MouseWheel>", _on_wheel)
            canvas.bind("<Button-4>", _on_wheel)
            canvas.bind("<Button-5>", _on_wheel)

            item_w_logical = int(content_w / s)
            for opt in self._dropdown_items:
                it = DropdownItem(
                    scroll_frame,
                    text=opt,
                    is_selected=(opt == self._selected),
                    on_select=self._on_item_clicked,
                    width=item_w_logical,
                    height=30,
                    parent_bg=popup_bg,
                )
                it.pack(fill="x", pady=1)
                it.bind("<MouseWheel>", _on_wheel, add="+")
                it.bind("<Button-4>", _on_wheel, add="+")
                it.bind("<Button-5>", _on_wheel, add="+")
                self._item_widgets.append(it)

            # Scroll selected into view initially
            if self._selected in self._dropdown_items:
                sel_idx = self._dropdown_items.index(self._selected)
                self._scroll_item_into_view(sel_idx)
        else:
            self._scroll_canvas = None
            self._scrollbar = None
            item_w_logical = int(self._logical_w)
            for opt in self._dropdown_items:
                it = DropdownItem(
                    inner_frame,
                    text=opt,
                    is_selected=(opt == self._selected),
                    on_select=self._on_item_clicked,
                    width=item_w_logical - 6,
                    height=30,
                    parent_bg=popup_bg,
                )
                it.pack(fill="x", pady=1, padx=int(3 * s))
                self._item_widgets.append(it)

        # Global event listeners for rock-solid dismissal
        self._root_bind_id = toplevel.bind("<ButtonPress-1>", self._on_root_click, add="+")
        self._parent_bind_id = toplevel.bind("<Configure>", self._on_root_configure, add="+")
        self._escape_bind_id = toplevel.bind("<Escape>", lambda e: self._close_popup(), add="+")
        self._root_focus_bind_id = toplevel.bind("<FocusOut>", self._on_root_focus_out, add="+")

    def _on_root_click(self, event) -> None:
        if not self._is_open or not self._popup_win or not self._popup_win.winfo_exists():
            return
        px = event.x_root
        py = event.y_root

        # Check if click is inside the popup
        try:
            pop_x = self._popup_win.winfo_rootx()
            pop_y = self._popup_win.winfo_rooty()
            pop_w = self._popup_win.winfo_width()
            pop_h = self._popup_win.winfo_height()
            if pop_x <= px <= pop_x + pop_w and pop_y <= py <= pop_h + pop_y:
                return
        except Exception:
            pass

        # Check if click is on the trigger widget itself
        try:
            trig_x = self.winfo_rootx()
            trig_y = self.winfo_rooty()
            trig_w = self.winfo_width()
            trig_h = self.winfo_height()
            if trig_x <= px <= trig_x + trig_w and trig_y <= py <= trig_h + trig_y:
                return
        except Exception:
            pass

        # Otherwise clicked outside: close cleanly
        self._close_popup()

    def _on_root_configure(self, event) -> None:
        if self._is_open and event.widget == self.winfo_toplevel():
            self._close_popup()

    def _on_root_focus_out(self, event) -> None:
        if not self._is_open:
            return
        top = self.winfo_toplevel()
        if event.widget == top:
            try:
                if top.focus_displayof() is None:
                    self._close_popup()
            except Exception:
                pass

    def _close_popup(self) -> None:
        if not self._is_open and not self._popup_win:
            return
        self._is_open = False

        try:
            top = self.winfo_toplevel()
            if self._root_bind_id:
                top.unbind("<ButtonPress-1>", self._root_bind_id)
                self._root_bind_id = None
            if self._parent_bind_id:
                top.unbind("<Configure>", self._parent_bind_id)
                self._parent_bind_id = None
            if self._escape_bind_id:
                top.unbind("<Escape>", self._escape_bind_id)
                self._escape_bind_id = None
            if self._root_focus_bind_id:
                top.unbind("<FocusOut>", self._root_focus_bind_id)
                self._root_focus_bind_id = None
        except Exception:
            pass

        if self._popup_win:
            try:
                self._popup_win.destroy()
            except Exception:
                pass
            self._popup_win = None
        self._item_widgets = []
        self._scroll_canvas = None
        self._scrollbar = None
        self.render()

    def _on_item_clicked(self, opt: str) -> None:
        self._select_option(opt, notify=True, close=True)

    def _select_option(self, opt: str, notify: bool = True, close: bool = True) -> None:
        self._selected = opt
        if close:
            self._close_popup()
        else:
            self._update_item_states()
            self.render()

        if notify and self._on_select:
            try:
                self._on_select(opt)
            except Exception:
                pass

    def _update_item_states(self) -> None:
        for it in self._item_widgets:
            it.set_selected(it.text == self._selected)

    def _on_destroy(self, event) -> None:
        self._close_popup()
        super()._on_destroy(event)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        pad = 2.0 * s
        w = max(1.0, float(self._widget_w) - pad * 2.0)
        h = max(1.0, float(self._widget_h) - pad * 2.0)
        r = 8.0 * s

        pal = get_theme()

        # High-contrast background for field
        if pal.dark_mode:
            field_bg = "#252538" if self._parent_bg in ("#181825", "#11111b", "#1e1e2e") else blend_color_hex(pal.surface, "#ffffff", 0.08)
        else:
            field_bg = "#ffffff"

        # Focus ring and border styling with high contrast
        if self._is_open:
            border = pal.primary
            border_w = 2.0 * s
            field_bg = "#2a2b42" if pal.dark_mode else "#ffffff"
        elif self._is_focused:
            border = pal.primary
            border_w = 1.8 * s
        elif self._is_hovered:
            border = pal.primary_hover if hasattr(pal, "primary_hover") else pal.primary
            border_w = 1.6 * s
            field_bg = "#2b2c44" if pal.dark_mode else "#ffffff"
        else:
            border = "#585b70" if pal.dark_mode else "#cbd5e1"
            border_w = 1.4 * s

        # Outer soft focus glow if focused or open
        if self._is_focused or self._is_open:
            glow_color = blend_color_hex(pal.primary, self._parent_bg, 0.45)
            self._surface.stroke_rounded_rect(
                pad - 1.0 * s,
                pad - 1.0 * s,
                w + 2.0 * s,
                h + 2.0 * s,
                r + 1.0 * s,
                r + 1.0 * s,
                glow_color,
                2.5 * s,
            )

        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, field_bg)
        self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, border, border_w)

        # Draw selected text or placeholder with high contrast
        font_sz = 13.0 * s
        display_text = self._selected if self._selected else self._placeholder
        text_color = ("#ffffff" if pal.dark_mode else "#0f172a") if self._selected else pal.text_muted

        # Truncate text if needed to avoid overlapping chevron
        max_text_w = self._widget_w - pad * 2.0 - 44.0 * s
        char_est = max(5, int(max_text_w / (font_sz * 0.58)))
        if len(display_text) > char_est:
            clipped_text = display_text[: max(1, char_est - 3)] + "..."
        else:
            clipped_text = display_text

        self._surface.draw_text(
            clipped_text,
            pad + 12.0 * s,
            self._widget_h / 2.0 + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color=text_color,
            align="left",
        )

        # Smooth vector chevron icon (pointing up if open, down if closed)
        chev_x = self._widget_w - pad - 16.0 * s
        chev_y = self._widget_h / 2.0
        chev_color = pal.primary if (self._is_open or self._is_hovered or self._is_focused) else ("#bac2de" if pal.dark_mode else "#64748b")
        p = Path()
        if self._is_open:
            p.move_to(chev_x - 4.5 * s, chev_y + 2.0 * s)
            p.line_to(chev_x, chev_y - 2.5 * s)
            p.line_to(chev_x + 4.5 * s, chev_y + 2.0 * s)
        else:
            p.move_to(chev_x - 4.5 * s, chev_y - 2.0 * s)
            p.line_to(chev_x, chev_y + 2.5 * s)
            p.line_to(chev_x + 4.5 * s, chev_y - 2.0 * s)
        self._surface.stroke_path(p, chev_color, stroke_width=2.0 * s)

        self._surface.blit(self._photo)


ModernDropdown = Dropdown


# ============================================================================
# Widget 12: SpinBox (Stepper with Vector +/- Buttons)
# ============================================================================

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
        self._surface.draw_line(cx - arm, cy, cx + arm, cy, pal.fg, 1.8 * s)
        self._surface.draw_line(cx, cy - arm, cx, cy + arm, pal.fg, 1.8 * s)

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


# ============================================================================
# Widget 13: Badge (Status Pills & Tags)
# ============================================================================

class Badge(Widget):
    """
    Status pill badge with variant fills, borders, optional status dot, and antialiased text.
    """

    VARIANT_STYLES: Dict[str, Dict[str, str]] = {
        "primary": {"bg": "#89b4fa25", "border": "#89b4fa", "fg": "#89b4fa"},
        "success": {"bg": "#a6e3a125", "border": "#a6e3a1", "fg": "#a6e3a1"},
        "warning": {"bg": "#f9e2af25", "border": "#f9e2af", "fg": "#f9e2af"},
        "destructive": {"bg": "#f38ba825", "border": "#f38ba8", "fg": "#f38ba8"},
        "outline": {"bg": "#18182500", "border": "#585b70", "fg": "#cdd6f4"},
    }

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Badge",
        variant: str = "primary",
        dot: bool = False,
        width: int = 90,
        height: int = 24,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._text = text
        self._variant = variant if variant in self.VARIANT_STYLES else "primary"
        self._dot = dot
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

    def set_text(self, text: str) -> None:
        self._text = text
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        pad = 1.5 * s
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        r = h / 2.0

        style = self.VARIANT_STYLES.get(self._variant, self.VARIANT_STYLES["primary"])
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, style["bg"])
        self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, style["border"], 1.0 * s)

        font_sz = 11.0 * s
        if self._dot:
            dot_cx = pad + 10.0 * s
            dot_cy = self._widget_h / 2.0
            self._surface.fill_circle(dot_cx, dot_cy, 3.0 * s, style["fg"])
            text_x = dot_cx + 8.0 * s + (w - 18.0 * s) / 2.0
        else:
            text_x = self._widget_w / 2.0

        self._surface.draw_text(
            self._text,
            text_x,
            self._widget_h / 2.0 + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color=style["fg"],
            align="center",
        )
        self._surface.blit(self._photo)


ModernBadge = Badge


# ============================================================================
# Widget 14: Avatar (Circular Profile with Status Dot)
# ============================================================================

class Avatar(Widget):
    """
    Circular vector avatar displaying initials with optional status indicator dot.
    """

    STATUS_COLORS: Dict[str, str] = {
        "online": "#a6e3a1",
        "busy": "#f9e2af",
        "offline": "#6c7086",
    }

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        initials: str = "TK",
        status: Optional[str] = "online",
        size: int = 44,
        bg_gradient_start: Optional[ColorLike] = None,
        bg_gradient_end: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._initials = initials
        self._status = status
        pal = get_theme()
        self._grad_start = bg_gradient_start or pal.primary
        self._grad_end = bg_gradient_end or pal.accent
        super().__init__(master=master, width=size, height=size, bg=parent_bg, **kwargs)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        r = min(cx, cy) - 3.0 * s

        grad = LinearGradient(cx - r, cy - r, cx + r, cy + r)
        grad.add_stop(0.0, self._grad_start)
        grad.add_stop(1.0, self._grad_end)

        self._surface.fill_circle(cx, cy, r, grad)
        self._surface.stroke_circle(cx, cy, r, "#ffffff44", stroke_width=1.2 * s)

        font_sz = 14.0 * s
        self._surface.draw_text(
            self._initials,
            cx,
            cy + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color="#11111b",
            align="center",
        )

        if self._status in self.STATUS_COLORS:
            dot_color = self.STATUS_COLORS[self._status]
            dot_r = 4.5 * s
            dot_cx = cx + r * 0.65
            dot_cy = cy + r * 0.65
            self._surface.fill_circle(dot_cx, dot_cy, dot_r + 1.5 * s, self._parent_bg)
            self._surface.fill_circle(dot_cx, dot_cy, dot_r, dot_color)

        self._surface.blit(self._photo)


ModernAvatar = Avatar


# ============================================================================
# Widget 15: Accordion (Collapsible Card with Vector Chevron)
# ============================================================================

class _AccordionHeader(Widget):
    """Backing vector surface for Accordion header."""

    def __init__(self, accordion: "Accordion", master: tk.Misc, width: int, height: int, bg: Optional[str] = None):
        self._accordion = accordion
        super().__init__(master=master, width=width, height=height, bg=bg, cursor="hand2")

    def _on_theme_changed(self, palette: Palette) -> None:
        super()._on_theme_changed(palette)
        if hasattr(self, "_accordion") and self._accordion.winfo_exists():
            try:
                self._accordion._content.configure(bg=palette.surface)
            except Exception:
                pass

    def render(self) -> None:
        if hasattr(self, "_accordion"):
            self._accordion._render_header()


class Accordion(tk.Frame):
    """
    Expandable / collapsible card container with animated rotating chevron arrow.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: str = "Collapsible Section",
        width: int = 280,
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
            bg=self._parent_bg,
            **kwargs,
        )
        self._is_open = False
        self._title = title

        self._header = _AccordionHeader(self, master=self, width=width, height=38, bg=self._parent_bg)
        self._header.pack(fill="x")
        self._header.bind("<ButtonRelease-1>", self._toggle)

        self._content = tk.Frame(self, bg=pal.surface, padx=int(12 * s), pady=int(10 * s))
        self._render_header()

    @property
    def content_frame(self) -> tk.Frame:
        return self._content

    def _toggle(self, event) -> None:
        self._is_open = not self._is_open
        if self._is_open:
            self._content.pack(fill="both", expand=True, padx=int(4 * self._scale), pady=(0, int(4 * self._scale)))
        else:
            self._content.pack_forget()
        self._header.render()

    def _render_header(self) -> None:
        surf = self._header.surface
        surf.clear(self._parent_bg)
        s = self._scale
        pad = 2.0 * s
        w = max(1.0, self._header._widget_w - pad * 2.0)
        h = max(1.0, self._header._widget_h - pad * 2.0)
        r = 8.0 * s

        pal = get_theme()
        is_hovered = getattr(self._header, "_is_hovered", False)
        is_pressed = getattr(self._header, "_is_pressed", False)

        if is_pressed:
            header_bg = pal.secondary_active
            border_col = pal.primary
            chev_col = pal.primary_active
        elif is_hovered:
            header_bg = pal.card_bg
            border_col = pal.primary_hover
            chev_col = pal.primary_hover
        else:
            header_bg = pal.surface
            border_col = pal.card_border
            chev_col = pal.primary

        surf.fill_rounded_rect(pad, pad, w, h, r, r, header_bg)
        surf.stroke_rounded_rect(pad, pad, w, h, r, r, border_col, 1.2 * s if (is_hovered or is_pressed) else 1.0 * s)

        chev_x = pad + 16.0 * s
        chev_y = self._header._widget_h / 2.0
        p = Path()
        if self._is_open:
            p.move_to(chev_x - 4.0 * s, chev_y - 2.0 * s)
            p.line_to(chev_x, chev_y + 3.0 * s)
            p.line_to(chev_x + 4.0 * s, chev_y - 2.0 * s)
        else:
            p.move_to(chev_x - 2.0 * s, chev_y - 4.0 * s)
            p.line_to(chev_x + 3.0 * s, chev_y)
            p.line_to(chev_x - 2.0 * s, chev_y + 4.0 * s)
        surf.stroke_path(p, chev_col, stroke_width=1.8 * s)

        font_sz = 13.0 * s
        surf.draw_text(
            self._title,
            chev_x + 14.0 * s,
            self._header._widget_h / 2.0 + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color=pal.fg,
            align="left",
        )
        surf.blit(self._header.photo)


ModernAccordion = Accordion


__all__ = [
    "ScalingTracker",
    "Widget",
    "ModernWidget",
    "Frame",
    "ModernFrame",
    "Card",
    "ModernCard",
    "Button",
    "ModernButton",
    "ProgressBar",
    "ModernProgressBar",
    "CircularProgress",
    "ModernCircularProgress",
    "Slider",
    "ModernSlider",
    "RangeSlider",
    "ModernRangeSlider",
    "Switch",
    "ModernSwitch",
    "ToggleSwitch",
    "Checkbox",
    "ModernCheckbox",
    "Radio",
    "ModernRadio",
    "RadioGroup",
    "ModernRadioGroup",
    "SegmentedControl",
    "ModernSegmentedControl",
    "TextInput",
    "ModernTextInput",
    "VectorScrollbar",
    "ModernScrollbar",
    "Scrollbar",
    "Dropdown",
    "ModernDropdown",
    "DropdownItem",
    "SpinBox",
    "ModernSpinBox",
    "Badge",
    "ModernBadge",
    "Avatar",
    "ModernAvatar",
    "Accordion",
    "ModernAccordion",
    "blend_color_hex",
]
