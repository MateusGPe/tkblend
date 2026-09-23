"""
tkblend Extended Vector Canvas Showcase Application.
A comprehensive catalog of 15+ modern, self-contained vector widgets built strictly from
scratch using Blend2D's Surface and BlendCanvas without any TTK theme dependencies.

Features:
- DPI-aware coordinate scaling with ScalingTracker
- Zero-copy Tk_PhotoPutBlock blitting via Surface.blit()
- Comprehensive widget catalog:
    * ModernButton (multiple variants, hover/press elevation depth)
    * ModernProgressBar (capsule linear gradient)
    * ModernCircularProgress (vector arc ring / radial gauge with readout)
    * ModernSlider (smooth draggable track & glowing thumb)
    * ModernRangeSlider (dual-thumb min/max range selector)
    * ModernSwitch (iOS / Fluent style toggle pill)
    * ModernCheckbox (rounded vector box with animated vector checkmark path)
    * ModernRadio & ModernRadioGroup (concentric animated dot vector radios)
    * ModernSegmentedControl (capsule track with elevated active pill indicator)
    * ModernTextInput (rounded focus-ring input with placeholder & clear icon)
    * ModernDropdown (vector selector with chevron and popup menu)
    * ModernSpinBox (numeric stepper with vector +/- buttons)
    * ModernBadge (status pills: primary, success, warning, destructive, outline)
    * ModernAvatar (circular gradient avatar with status dot)
    * ModernAccordion (collapsible card with rotating vector chevron)
    * ModernCard & ModernFrame (elevated containers with soft drop shadow)
- 4-View Category Navigation via ModernSegmentedControl:
    1. Controls & Forms
    2. Sliders & Gauges
    3. Display & Cards
    4. Live Vector Canvas (60 FPS fluid waves, glassmorphic cards, HUD FPS)
- Real-time interconnected state: adjusting controls updates gauges & live canvas parameters.
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
from tkblend.widgets import TextInput, Accordion, Dropdown, ModernDropdown, DropdownItem, VectorScrollbar, ModernScrollbar


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

class ModernWidget(tk.Label):
    """
    Base vector widget rendering on a Blend2D Surface with zero-copy blit
    to a backing Tkinter PhotoImage. Handles DPI scaling, resize, and mouse states.
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
        self._parent_bg = bg

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


# ============================================================================
# Containers: ModernFrame and ModernCard
# ============================================================================

class ModernFrame(tk.Frame):
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


class ModernCard(ModernFrame):
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
        bg_color: ColorLike = "#181825",
        border_color: ColorLike = "#313244",
        border_width: float = 1.0,
        elevation: float = 10.0,
        shadow_color: ColorLike = "#00000077",
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
            self._surface.draw_text(
                self._title,
                x=pad + 16.0 * self._scale,
                y=pad + 26.0 * self._scale,
                font_size=14.0 * self._scale,
                font_family="sans-serif",
                color="#cdd6f4",
            )
            # Divider line below title
            line_y = pad + 36.0 * self._scale
            self._surface.draw_line(
                pad + 16.0 * self._scale,
                line_y,
                self._widget_w - pad - 16.0 * self._scale,
                line_y,
                stroke="#31324488",
                stroke_width=1.0,
            )
            self._surface.blit(self._photo)


# ============================================================================
# Widget 1: ModernButton (Variants, Elevation, Text)
# ============================================================================

class ModernButton(ModernWidget):
    """
    Modern Button supporting variants ('primary', 'secondary', 'accent', 'destructive', 'outline'),
    micro-elevation on hover, pressed drop-depth animation, and antialiased typography.
    """

    VARIANT_COLORS = {
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
        parent_bg: str = "#1e1e2e",
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


# ============================================================================
# Widget 2: ModernProgressBar (Linear Capsule Gradient)
# ============================================================================

class ModernProgressBar(ModernWidget):
    """
    Antialiased smooth linear progress bar with capsule geometry and gradient fill.
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


# ============================================================================
# Widget 3: ModernCircularProgress (Radial Gauge / Donut Ring)
# ============================================================================

class ModernCircularProgress(ModernWidget):
    """
    Antialiased circular progress ring / radial gauge with center numeric readout.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 110,
        value: float = 65.0,
        stroke_width: float = 8.0,
        track_color: ColorLike = "#313244",
        fill_color: ColorLike = "#89b4fa",
        unit: str = "%",
        parent_bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._value = max(0.0, min(100.0, float(value)))
        self._stroke_w = stroke_width
        self._track_color = track_color
        self._fill_color = fill_color
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
        self._surface.draw_text(
            f"{int(self._value)}{self._unit}",
            cx,
            cy + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color="#cdd6f4",
            align="center",
        )
        self._surface.blit(self._photo)


# ============================================================================
# Widget 4: ModernSlider (Smooth Draggable Track & Glowing Knob)
# ============================================================================

class ModernSlider(ModernWidget):
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


# ============================================================================
# Widget 5: ModernRangeSlider (Dual-Knob Min/Max Selector)
# ============================================================================

class ModernRangeSlider(ModernWidget):
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
        track_color: ColorLike = "#313244",
        active_color: ColorLike = "#a6e3a1",
        knob_color: ColorLike = "#f5e0dc",
        parent_bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._min = min_val
        self._max = max_val
        self._low = max(min_val, min(max_val, float(low_val)))
        self._high = max(self._low, min(max_val, float(high_val)))
        self._on_change = on_change
        self._track_color = track_color
        self._active_color = active_color
        self._knob_color = knob_color
        scale = ScalingTracker.get_scaling_factor(master)
        self._knob_r = 8.5 * scale
        self._dragging_thumb: Optional[str] = None  # 'low' or 'high'

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

        # Background track
        self._surface.fill_rounded_rect(
            pad, track_y, usable_w, track_h, track_h / 2.0, track_h / 2.0, self._track_color
        )

        low_x = self._val_to_x(self._low, pad, usable_w)
        high_x = self._val_to_x(self._high, pad, usable_w)

        # Active range segment
        if high_x > low_x:
            self._surface.fill_rounded_rect(
                low_x, track_y, high_x - low_x, track_h, track_h / 2.0, track_h / 2.0, self._active_color
            )

        # Draw two knobs
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


# ============================================================================
# Widget 6: ModernSwitch (iOS / Fluent Toggle Pill)
# ============================================================================

class ModernSwitch(ModernWidget):
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


# ============================================================================
# Widget 7: ModernCheckbox (Rounded Box with Vector Checkmark)
# ============================================================================

class ModernCheckbox(ModernWidget):
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
        active_color: ColorLike = "#89b4fa",
        parent_bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._text = text
        self._checked = checked
        self._on_change = on_change
        self._active_color = active_color
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

        if self._checked:
            self._surface.fill_rounded_rect(box_x, box_y, box_size, box_size, r, r, self._active_color)
            # Draw vector checkmark
            p = Path()
            p.move_to(box_x + 4.5 * s, box_y + 9.0 * s)
            p.line_to(box_x + 7.5 * s, box_y + 12.5 * s)
            p.line_to(box_x + 13.5 * s, box_y + 5.5 * s)
            self._surface.stroke_path(p, "#11111b", stroke_width=2.0 * s)
        else:
            border = "#89b4fa" if self._is_hovered else "#45475a"
            bg = "#31324455" if self._is_hovered else "#181825"
            self._surface.fill_rounded_rect(box_x, box_y, box_size, box_size, r, r, bg)
            self._surface.stroke_rounded_rect(box_x, box_y, box_size, box_size, r, r, border, 1.2 * s)

        # Label text
        text_x = box_x + box_size + 10.0 * s
        font_sz = 13.0 * s
        self._surface.draw_text(
            self._text,
            text_x,
            self._widget_h / 2.0 + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color="#cdd6f4",
            align="left",
        )
        self._surface.blit(self._photo)


# ============================================================================
# Widget 8: ModernRadio & ModernRadioGroup (Concentric Dot Radios)
# ============================================================================

class ModernRadio(ModernWidget):
    """
    Individual circular vector radio button with concentric animated dot indicator.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Radio",
        value: str = "",
        group: Optional["ModernRadioGroup"] = None,
        width: int = 150,
        height: int = 28,
        active_color: ColorLike = "#cba6f7",
        parent_bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._text = text
        self._value = value
        self._group = group
        self._active_color = active_color
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

        if self._selected:
            self._surface.stroke_circle(cx, cy, r, self._active_color, stroke_width=2.0 * s)
            self._surface.fill_circle(cx, cy, r * 0.52, self._active_color)
        else:
            border = "#cba6f7" if self._is_hovered else "#45475a"
            self._surface.stroke_circle(cx, cy, r, border, stroke_width=1.5 * s)

        font_sz = 13.0 * s
        self._surface.draw_text(
            self._text,
            cx + r + 10.0 * s,
            self._widget_h / 2.0 + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color="#cdd6f4",
            align="left",
        )
        self._surface.blit(self._photo)


class ModernRadioGroup:
    """
    Manages mutual exclusion and selection state among a group of ModernRadio buttons.
    """

    def __init__(self, on_change: Optional[Callable[[str], None]] = None):
        self._radios: List[ModernRadio] = []
        self._value: str = ""
        self._on_change = on_change

    def register(self, radio: ModernRadio) -> None:
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


# ============================================================================
# Widget 9: ModernSegmentedControl (Elevated Sliding Pill Tab Switcher)
# ============================================================================

class ModernSegmentedControl(ModernWidget):
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
        active_color: ColorLike = "#89b4fa",
        parent_bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._values = list(values) if values else ["Option 1", "Option 2"]
        self._selected = max(0, min(len(self._values) - 1, selected_index))
        self._on_change = on_change
        self._active_color = active_color
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

        # Recessed capsule track
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, "#181825")
        self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, "#313244", 1.0 * s)

        num_segs = max(1, len(self._values))
        seg_w = w / num_segs

        # Hover highlight on inactive segment
        if self._hovered_index is not None and self._hovered_index != self._selected:
            hx = pad + self._hovered_index * seg_w
            self._surface.fill_rounded_rect(hx, pad, seg_w, h, r, r, "#31324455")

        # Active Segment Pill
        ax = pad + self._selected * seg_w
        self._surface.draw_shadow(
            ax + 1.0, pad + 1.0, seg_w - 2.0, h - 2.0,
            r, r, blur_radius=4.0 * s, offset_y=1.0 * s, shadow_color="#00000044"
        )
        self._surface.fill_rounded_rect(ax + 1.0, pad + 1.0, seg_w - 2.0, h - 2.0, r, r, self._active_color)

        # Labels
        font_sz = 12.0 * s
        for i, val in enumerate(self._values):
            tx = pad + (i + 0.5) * seg_w
            ty = pad + h / 2.0 + (font_sz * 0.35)
            color = "#11111b" if i == self._selected else "#cdd6f4"
            self._surface.draw_text(val, tx, ty, font_size=font_sz, font_family="sans-serif", color=color, align="center")

        self._surface.blit(self._photo)


# ============================================================================
# Widget 10: ModernTextInput (Focus Ring, Rounded Border, Clear Button)
# ============================================================================

ModernTextInput = TextInput


# ============================================================================
# Widget 11: ModernDropdown (Vector Combobox / Select with Popup)
# ============================================================================
# ModernDropdown & DropdownItem are imported directly from tkblend.widgets



# ============================================================================
# Widget 12: ModernSpinBox (Stepper with Vector +/- Buttons)
# ============================================================================

class ModernSpinBox(ModernWidget):
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
        parent_bg: str = "#1e1e2e",
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
            # Minus
            self.value -= self._step
            if self._on_change:
                self._on_change(self._value)
        elif event.x >= self._widget_w - btn_w:
            # Plus
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

        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, "#181825")
        self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, "#313244", 1.0 * s)

        btn_w = 32.0 * s
        # Minus button
        self._surface.fill_rounded_rect(pad, pad, btn_w, h, r, r, "#313244")
        self._surface.draw_line(pad + 10.0 * s, self._widget_h / 2.0, pad + btn_w - 10.0 * s, self._widget_h / 2.0, "#cdd6f4", 1.8 * s)

        # Plus button
        plus_x = self._widget_w - pad - btn_w
        self._surface.fill_rounded_rect(plus_x, pad, btn_w, h, r, r, "#313244")
        cy = self._widget_h / 2.0
        cx = plus_x + btn_w / 2.0
        arm = 5.0 * s
        self._surface.draw_line(cx - arm, cy, cx + arm, cy, "#cdd6f4", 1.8 * s)
        self._surface.draw_line(cx, cy - arm, cx, cy + arm, "#cdd6f4", 1.8 * s)

        # Value text in middle
        font_sz = 14.0 * s
        self._surface.draw_text(
            str(self._value),
            self._widget_w / 2.0,
            cy + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color="#cdd6f4",
            align="center",
        )
        self._surface.blit(self._photo)


# ============================================================================
# Widget 13: ModernBadge (Status Pills & Tags)
# ============================================================================

class ModernBadge(ModernWidget):
    """
    Status pill badge with variant fills, borders, optional status dot, and antialiased text.
    """

    VARIANT_STYLES = {
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
        parent_bg: str = "#1e1e2e",
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


# ============================================================================
# Widget 14: ModernAvatar (Circular Profile with Status Dot)
# ============================================================================

class ModernAvatar(ModernWidget):
    """
    Circular vector avatar displaying initials with optional status indicator dot.
    """

    STATUS_COLORS = {
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
        bg_gradient_start: ColorLike = "#89b4fa",
        bg_gradient_end: ColorLike = "#cba6f7",
        parent_bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._initials = initials
        self._status = status
        self._grad_start = bg_gradient_start
        self._grad_end = bg_gradient_end
        super().__init__(master=master, width=size, height=size, bg=parent_bg, **kwargs)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        r = min(cx, cy) - 3.0 * s

        # Background gradient
        grad = LinearGradient(cx - r, cy - r, cx + r, cy + r)
        grad.add_stop(0.0, self._grad_start)
        grad.add_stop(1.0, self._grad_end)

        self._surface.fill_circle(cx, cy, r, grad)
        self._surface.stroke_circle(cx, cy, r, "#ffffff44", stroke_width=1.2 * s)

        # Initials Text
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

        # Status badge dot at bottom right
        if self._status in self.STATUS_COLORS:
            dot_color = self.STATUS_COLORS[self._status]
            dot_r = 4.5 * s
            dot_cx = cx + r * 0.65
            dot_cy = cy + r * 0.65
            self._surface.fill_circle(dot_cx, dot_cy, dot_r + 1.5 * s, self._parent_bg)
            self._surface.fill_circle(dot_cx, dot_cy, dot_r, dot_color)

        self._surface.blit(self._photo)


# ============================================================================
# Widget 15: ModernAccordion (Collapsible Card with Vector Chevron)
# ============================================================================

ModernAccordion = Accordion


# ============================================================================
# Main Showcase Application
# ============================================================================

class ExtendedCanvasShowcaseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend Extended Vector Canvas Showcase - All Modern Widgets")
        self._scale = ScalingTracker.get_scaling_factor(root)

        w = int(1140 * self._scale)
        h = int(740 * self._scale)
        self.root.geometry(f"{w}x{h}")
        self.root.minsize(int(960 * self._scale), int(640 * self._scale))
        self.root.configure(bg="#11111b")

        self._start_time = time.perf_counter()
        self._fps_frames = 0
        self._fps_last_time = time.perf_counter()
        self._fps = 60.0

        # Live interconnected state
        self._shared_progress = 65.0
        self._wave_speed = 1.0
        self._wave_amplitude = 35.0
        self._anim_radius = 20.0 * self._scale
        self._wave_active = True

        self._setup_top_nav()
        self._setup_views()

        # Start 60 FPS animation loop
        self._tick_anim()

    def _setup_top_nav(self):
        s = self._scale
        top_bar = tk.Frame(self.root, bg="#181825", height=int(56 * s))
        top_bar.pack(fill="x", padx=int(12 * s), pady=(int(12 * s), int(8 * s)))
        top_bar.pack_propagate(False)

        # Title & Subtitle on left
        title_box = tk.Frame(top_bar, bg="#181825")
        title_box.pack(side="left", padx=int(16 * s), pady=int(6 * s))

        tk.Label(
            title_box,
            text="tkblend Vector Suite",
            font=("DejaVu Sans", int(14 * s), "bold"),
            fg="#cdd6f4",
            bg="#181825",
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="15+ Pure Surface Vector Widgets",
            font=("DejaVu Sans", int(9 * s)),
            fg="#a6adc8",
            bg="#181825",
        ).pack(anchor="w")

        # Category Navigator Pill Switcher
        self.nav_tabs = ModernSegmentedControl(
            top_bar,
            values=["Controls & Forms", "Sliders & Gauges", "Display & Cards", "Live Vector Canvas"],
            selected_index=0,
            on_change=self._on_tab_changed,
            width=580,
            height=36,
            active_color="#89b4fa",
            parent_bg="#181825",
        )
        self.nav_tabs.pack(side="right", padx=int(16 * s))

    def _setup_views(self):
        s = self._scale
        self.views_container = tk.Frame(self.root, bg="#11111b")
        self.views_container.pack(fill="both", expand=True, padx=int(12 * s), pady=(0, int(12 * s)))

        # Create the 4 View frames
        self.view_controls = tk.Frame(self.views_container, bg="#11111b")
        self.view_sliders = tk.Frame(self.views_container, bg="#11111b")
        self.view_display = tk.Frame(self.views_container, bg="#11111b")
        self.view_canvas = tk.Frame(self.views_container, bg="#11111b")

        self._build_view_controls()
        self._build_view_sliders()
        self._build_view_display()
        self._build_view_canvas()

        # Display first view
        self._show_view(0)

    def _on_tab_changed(self, idx: int, name: str):
        self._show_view(idx)

    def _show_view(self, idx: int):
        for v in (self.view_controls, self.view_sliders, self.view_display, self.view_canvas):
            v.pack_forget()
        views = [self.view_controls, self.view_sliders, self.view_display, self.view_canvas]
        if 0 <= idx < len(views):
            views[idx].pack(fill="both", expand=True)

    # ------------------------------------------------------------------------
    # View 1: Controls & Forms
    # ------------------------------------------------------------------------
    def _build_view_controls(self):
        s = self._scale
        # 3-Column Card Layout
        col1 = ModernCard(self.view_controls, title="Buttons & Variants", width=340, height=600, parent_bg="#11111b")
        col1.pack(side="left", fill="both", expand=True, padx=int(6 * s))

        col2 = ModernCard(self.view_controls, title="Selection & Toggles", width=340, height=600, parent_bg="#11111b")
        col2.pack(side="left", fill="both", expand=True, padx=int(6 * s))

        col3 = ModernCard(self.view_controls, title="Text & Dropdowns", width=340, height=600, parent_bg="#11111b")
        col3.pack(side="left", fill="both", expand=True, padx=int(6 * s))

        # Buttons column
        btn_box = tk.Frame(col1, bg="#181825")
        btn_box.pack(fill="both", expand=True, padx=int(16 * s), pady=(int(52 * s), int(16 * s)))

        ModernButton(btn_box, text="Primary Action", variant="primary", command=self._inc_progress, width=280, height=40, parent_bg="#181825").pack(pady=int(6 * s))
        ModernButton(btn_box, text="Secondary Action", variant="secondary", width=280, height=40, parent_bg="#181825").pack(pady=int(6 * s))
        ModernButton(btn_box, text="Accent Action", variant="accent", command=self._reset_progress, width=280, height=40, parent_bg="#181825").pack(pady=int(6 * s))
        ModernButton(btn_box, text="Destructive Button", variant="destructive", width=280, height=40, parent_bg="#181825").pack(pady=int(6 * s))
        ModernButton(btn_box, text="Outline Button", variant="outline", width=280, height=40, parent_bg="#181825").pack(pady=int(6 * s))

        # Selection column
        sel_box = tk.Frame(col2, bg="#181825")
        sel_box.pack(fill="both", expand=True, padx=int(16 * s), pady=(int(52 * s), int(16 * s)))

        tk.Label(sel_box, text="Toggle Switches:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(0, int(6 * s)))
        switch_row = tk.Frame(sel_box, bg="#181825")
        switch_row.pack(fill="x", pady=int(4 * s))
        tk.Label(switch_row, text="Dynamic Wave Animation", fg="#a6adc8", bg="#181825").pack(side="left")
        ModernSwitch(switch_row, is_on=True, on_toggle=self._on_wave_toggle, parent_bg="#181825").pack(side="right")

        tk.Label(sel_box, text="Vector Checkboxes:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(14 * s), int(6 * s)))
        ModernCheckbox(sel_box, text="Hardware Acceleration", checked=True, width=280, parent_bg="#181825").pack(pady=int(3 * s))
        ModernCheckbox(sel_box, text="High-DPI Per-Monitor", checked=True, width=280, parent_bg="#181825").pack(pady=int(3 * s))
        ModernCheckbox(sel_box, text="Enable Bloom Shaders", checked=False, width=280, parent_bg="#181825").pack(pady=int(3 * s))

        tk.Label(sel_box, text="Radio Option Group:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(14 * s), int(6 * s)))
        self.radio_group = ModernRadioGroup()
        ModernRadio(sel_box, text="Vector Engine 2D", value="blend2d", group=self.radio_group, width=280, parent_bg="#181825").pack(pady=int(3 * s))
        ModernRadio(sel_box, text="Direct Blit Pipeline", value="direct", group=self.radio_group, width=280, parent_bg="#181825").pack(pady=int(3 * s))
        ModernRadio(sel_box, text="Legacy GDI Mode", value="legacy", group=self.radio_group, width=280, parent_bg="#181825").pack(pady=int(3 * s))

        # Inputs column
        inp_box = tk.Frame(col3, bg="#181825")
        inp_box.pack(fill="both", expand=True, padx=int(16 * s), pady=(int(52 * s), int(16 * s)))

        tk.Label(inp_box, text="Vector Text Input:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(0, int(6 * s)))
        self.txt_input = ModernTextInput(inp_box, placeholder="Type something...", width=280, height=38, parent_bg="#181825")
        self.txt_input.pack(fill="x", pady=int(4 * s))
        self.txt_input.set("tkblend vector canvas")

        tk.Label(inp_box, text="Dropdown Selector (Scrollable & Vector):", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(16 * s), int(6 * s)))
        self.dropdown = ModernDropdown(
            inp_box,
            options=[
                "High Quality (60 FPS)",
                "Balanced (30 FPS)",
                "Power Saver (15 FPS)",
                "Ultra Vector HD",
                "Cinematic 120 FPS",
                "Eco Mode (Minimal GPU)",
                "Low Latency Gaming",
                "Custom Dynamic Scaling",
            ],
            selected="High Quality (60 FPS)",
            max_visible_items=5,
            width=280,
            height=36,
            parent_bg="#181825",
        )
        self.dropdown.pack(fill="x", pady=int(4 * s))

        tk.Label(inp_box, text="Numeric Stepper:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(16 * s), int(6 * s)))
        self.spinbox = ModernSpinBox(inp_box, min_val=0, max_val=100, value=int(self._shared_progress), on_change=self._on_stepper_change, width=280, height=36, parent_bg="#181825")
        self.spinbox.pack(fill="x", pady=int(4 * s))

    # ------------------------------------------------------------------------
    # View 2: Sliders & Gauges
    # ------------------------------------------------------------------------
    def _build_view_sliders(self):
        s = self._scale
        col1 = ModernCard(self.view_sliders, title="Progress Indicators", width=520, height=600, parent_bg="#11111b")
        col1.pack(side="left", fill="both", expand=True, padx=int(6 * s))

        col2 = ModernCard(self.view_sliders, title="Continuous & Range Sliders", width=520, height=600, parent_bg="#11111b")
        col2.pack(side="right", fill="both", expand=True, padx=int(6 * s))

        # Progress side
        p_box = tk.Frame(col1, bg="#181825")
        p_box.pack(fill="both", expand=True, padx=int(20 * s), pady=(int(52 * s), int(16 * s)))

        tk.Label(p_box, text="Capsule Linear Progress:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(0, int(6 * s)))
        self.progress_linear = ModernProgressBar(p_box, width=460, height=18, value=self._shared_progress, parent_bg="#181825")
        self.progress_linear.pack(fill="x", pady=int(4 * s))

        tk.Label(p_box, text="Accent Secondary Progress:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(16 * s), int(6 * s)))
        self.progress_accent = ModernProgressBar(p_box, width=460, height=14, value=40.0, fill_color_start="#a6e3a1", fill_color_end="#94e2d5", parent_bg="#181825")
        self.progress_accent.pack(fill="x", pady=int(4 * s))

        tk.Label(p_box, text="Circular Gauges / Radial Progress:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(20 * s), int(10 * s)))
        gauge_row = tk.Frame(p_box, bg="#181825")
        gauge_row.pack(fill="x", pady=int(6 * s))

        self.gauge_main = ModernCircularProgress(gauge_row, size=110, value=self._shared_progress, stroke_width=8.0, fill_color="#89b4fa", parent_bg="#181825")
        self.gauge_main.pack(side="left", padx=int(16 * s))

        self.gauge_secondary = ModernCircularProgress(gauge_row, size=110, value=85.0, stroke_width=8.0, fill_color="#cba6f7", unit="°C", parent_bg="#181825")
        self.gauge_secondary.pack(side="left", padx=int(16 * s))

        self.gauge_accent = ModernCircularProgress(gauge_row, size=110, value=42.0, stroke_width=8.0, fill_color="#a6e3a1", unit=" FPS", parent_bg="#181825")
        self.gauge_accent.pack(side="left", padx=int(16 * s))

        # Sliders side
        s_box = tk.Frame(col2, bg="#181825")
        s_box.pack(fill="both", expand=True, padx=int(20 * s), pady=(int(52 * s), int(16 * s)))

        tk.Label(s_box, text="Master Shared Slider (Wires to all gauges):", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(0, int(6 * s)))
        self.slider_master = ModernSlider(s_box, width=460, height=30, value=self._shared_progress, on_change=self._on_slider_change, parent_bg="#181825")
        self.slider_master.pack(fill="x", pady=int(4 * s))

        tk.Label(s_box, text="Wave Speed & Amplitude Slider:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(18 * s), int(6 * s)))
        self.slider_wave = ModernSlider(s_box, width=460, height=30, min_val=10.0, max_val=60.0, value=self._wave_amplitude, on_change=self._on_wave_amp_change, active_track_color="#cba6f7", parent_bg="#181825")
        self.slider_wave.pack(fill="x", pady=int(4 * s))

        tk.Label(s_box, text="Dual-Thumb Min/Max Range Slider:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(18 * s), int(6 * s)))
        self.range_slider = ModernRangeSlider(s_box, width=460, height=30, low_val=25.0, high_val=75.0, parent_bg="#181825")
        self.range_slider.pack(fill="x", pady=int(4 * s))

    # ------------------------------------------------------------------------
    # View 3: Display & Cards
    # ------------------------------------------------------------------------
    def _build_view_display(self):
        s = self._scale
        col1 = ModernCard(self.view_display, title="Badges, Avatars & Tags", width=520, height=600, parent_bg="#11111b")
        col1.pack(side="left", fill="both", expand=True, padx=int(6 * s))

        col2 = ModernCard(self.view_display, title="Collapsible Accordion Cards", width=520, height=600, parent_bg="#11111b")
        col2.pack(side="right", fill="both", expand=True, padx=int(6 * s))

        # Display items
        d_box = tk.Frame(col1, bg="#181825")
        d_box.pack(fill="both", expand=True, padx=int(20 * s), pady=(int(52 * s), int(16 * s)))

        tk.Label(d_box, text="Vector Badges / Status Pills:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(0, int(6 * s)))
        badge_row1 = tk.Frame(d_box, bg="#181825")
        badge_row1.pack(fill="x", pady=int(4 * s))
        ModernBadge(badge_row1, text="Primary", variant="primary", dot=True, parent_bg="#181825").pack(side="left", padx=int(4 * s))
        ModernBadge(badge_row1, text="Success", variant="success", dot=True, parent_bg="#181825").pack(side="left", padx=int(4 * s))
        ModernBadge(badge_row1, text="Warning", variant="warning", dot=True, parent_bg="#181825").pack(side="left", padx=int(4 * s))
        ModernBadge(badge_row1, text="Error", variant="destructive", dot=True, parent_bg="#181825").pack(side="left", padx=int(4 * s))

        tk.Label(d_box, text="Profile Avatars with Status Badges:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(20 * s), int(8 * s)))
        avatar_row = tk.Frame(d_box, bg="#181825")
        avatar_row.pack(fill="x", pady=int(4 * s))
        ModernAvatar(avatar_row, initials="AG", status="online", size=48, parent_bg="#181825").pack(side="left", padx=int(8 * s))
        ModernAvatar(avatar_row, initials="BL", status="busy", size=48, bg_gradient_start="#a6e3a1", bg_gradient_end="#94e2d5", parent_bg="#181825").pack(side="left", padx=int(8 * s))
        ModernAvatar(avatar_row, initials="TK", status="offline", size=48, bg_gradient_start="#f38ba8", bg_gradient_end="#fab387", parent_bg="#181825").pack(side="left", padx=int(8 * s))

        # Accordions
        a_box = tk.Frame(col2, bg="#181825")
        a_box.pack(fill="both", expand=True, padx=int(16 * s), pady=(int(52 * s), int(16 * s)))

        self.acc1 = ModernAccordion(a_box, title="Zero-Copy Pipeline Architecture", width=460, parent_bg="#181825")
        self.acc1.pack(fill="x", pady=int(6 * s))
        tk.Label(
            self.acc1.content_frame,
            text="Blend2D renders directly to an internal PRGB32 buffer,\nwhich is blitted directly into Tkinter's PhotoImage via\nTk_PhotoPutBlock with 0 Python heap allocations.",
            fg="#a6adc8",
            bg="#181825",
            justify="left",
            font=("DejaVu Sans", int(10 * s)),
        ).pack(anchor="w")

        self.acc2 = ModernAccordion(a_box, title="Antialiasing & Vector Paths", width=460, parent_bg="#181825")
        self.acc2.pack(fill="x", pady=int(6 * s))
        tk.Label(
            self.acc2.content_frame,
            text="Subpixel font rasterization and analytic antialiased\ngeometric primitives eliminate jagged edges on any display DPI.",
            fg="#a6adc8",
            bg="#181825",
            justify="left",
            font=("DejaVu Sans", int(10 * s)),
        ).pack(anchor="w")

        self.acc3 = ModernAccordion(a_box, title="Pure Surface Independence", width=460, parent_bg="#181825")
        self.acc3.pack(fill="x", pady=int(6 * s))
        tk.Label(
            self.acc3.content_frame,
            text="Every widget in this showcase is built strictly from\nscratch using Blend2D's Surface and BlendCanvas, completely\nfree of any TTK or theme dependencies.",
            fg="#a6adc8",
            bg="#181825",
            justify="left",
            font=("DejaVu Sans", int(10 * s)),
        ).pack(anchor="w")

    # ------------------------------------------------------------------------
    # View 4: Live Vector Canvas (Fluid Waves, HUD, 60 FPS)
    # ------------------------------------------------------------------------
    def _build_view_canvas(self):
        s = self._scale
        self.blend_canvas = BlendCanvas(
            self.view_canvas,
            width=int(1100 * s),
            height=int(660 * s),
            bg="#11111b",
            on_draw=self._draw_canvas_scene,
        )
        self.blend_canvas.pack(fill="both", expand=True)

    def _draw_canvas_scene(self, surf: Surface):
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

        # Background Soft Radial Glow
        surf.clear("#11111b")
        glow_cx = w * 0.5 + math.cos(t * 0.8) * 150.0 * s
        glow_cy = h * 0.4 + math.sin(t * 0.6) * 100.0 * s
        glow_grad = RadialGradient(glow_cx, glow_cy, 0, glow_cx, glow_cy, max(w, h) * 0.7)
        glow_grad.add_stop(0.0, "#1e1e2e")
        glow_grad.add_stop(0.6, "#181825")
        glow_grad.add_stop(1.0, "#11111b")
        surf.fill_rect(0, 0, w, h, glow_grad)

        # Dynamic Fluid Waves (wired to controls)
        if self._wave_active:
            for layer, col in enumerate(["#89b4fa33", "#cba6f744", "#f38ba855"]):
                p = Path()
                p.move_to(0, h)
                p.line_to(0, h * 0.65)
                steps = 18
                for i in range(steps + 1):
                    x = (w / steps) * i
                    phase = t * (1.8 * self._wave_speed) + layer * 1.5 + (i * 0.4)
                    y = h * (0.65 + layer * 0.06) + math.sin(phase) * (self._wave_amplitude * s)
                    p.line_to(x, y)
                p.line_to(w, h)
                p.close()
                surf.fill_path(p, col)

        # Floating Glassmorphic Cards
        card_w, card_h = 240.0 * s, 150.0 * s
        card1_x = 60.0 * s
        card1_y = 60.0 * s + math.sin(t * 1.2) * 12.0 * s

        card1_grad = LinearGradient(card1_x, card1_y, card1_x + card_w, card1_y + card_h)
        card1_grad.add_stop(0.0, "#313244dd")
        card1_grad.add_stop(1.0, "#1e1e2edd")

        surf.draw_shadow(
            card1_x, card1_y, card_w, card_h,
            self._anim_radius, self._anim_radius,
            blur_radius=self._anim_radius * 1.2,
            shadow_color="#00000088",
            offset_y=8.0 * s,
        )
        surf.fill_rounded_rect(card1_x, card1_y, card_w, card_h, self._anim_radius, self._anim_radius, card1_grad)
        surf.stroke_rounded_rect(card1_x, card1_y, card_w, card_h, self._anim_radius, self._anim_radius, "#89b4fa66", 1.5 * s)

        surf.draw_text("Vector Card Alpha", card1_x + 20 * s, card1_y + 36 * s, font_size=15 * s, color="#cdd6f4")
        surf.draw_text("Anti-aliased subpixel text", card1_x + 20 * s, card1_y + 64 * s, font_size=12 * s, color="#a6adc8")
        surf.fill_circle(card1_x + 190 * s, card1_y + 110 * s, 14 * s, "#a6e3a1")

        # Card 2
        card2_x = 340.0 * s
        card2_y = 100.0 * s + math.cos(t * 1.4) * 12.0 * s
        surf.draw_card(
            card2_x, card2_y, card_w, card_h,
            rx=self._anim_radius, ry=self._anim_radius,
            bg_color="#181825ee",
            border_color="#cba6f788",
            border_width=1.5 * s,
            shadow_blur=self._anim_radius * 1.2,
            shadow_color="#00000088",
            shadow_offset_y=8.0 * s,
        )
        surf.draw_text("Zero-Copy Blit", card2_x + 20 * s, card2_y + 36 * s, font_size=15 * s, color="#cdd6f4")
        surf.draw_text("Tk_PhotoPutBlock Direct", card2_x + 20 * s, card2_y + 64 * s, font_size=12 * s, color="#a6adc8")
        surf.fill_rounded_rect(card2_x + 20 * s, card2_y + 100 * s, 140 * s, 10 * s, 5 * s, 5 * s, "#cba6f7")

        # HUD / Status Overlay
        hud_w, hud_h = 160.0 * s, 48.0 * s
        hud_x = w - hud_w - 20.0 * s
        hud_y = 20.0 * s

        surf.draw_card(
            hud_x, hud_y, hud_w, hud_h,
            rx=12 * s, ry=12 * s,
            bg_color="#181825cc",
            border_color="#ffffff22",
            border_width=1.0,
            shadow_blur=8.0 * s,
            shadow_color="#00000044",
        )
        surf.draw_text(
            f"{self._fps:.1f} FPS",
            hud_x + hud_w / 2.0,
            hud_y + hud_h / 2.0 + 5.0 * s,
            font_size=16 * s,
            color="#a6e3a1",
            align="center",
        )

    # ------------------------------------------------------------------------
    # State Synchronization Callbacks
    # ------------------------------------------------------------------------
    def _inc_progress(self):
        self._shared_progress = (self._shared_progress + 15.0) % 100.0
        self._sync_progress_widgets()

    def _reset_progress(self):
        self._shared_progress = 0.0
        self._sync_progress_widgets()

    def _on_slider_change(self, val: float):
        self._shared_progress = val
        self._sync_progress_widgets()

    def _on_stepper_change(self, val: int):
        self._shared_progress = float(val)
        self._sync_progress_widgets()

    def _sync_progress_widgets(self):
        val = self._shared_progress
        self.progress_linear.value = val
        self.gauge_main.value = val
        self.spinbox.value = int(val)
        self.slider_master.value = val

    def _on_wave_amp_change(self, val: float):
        self._wave_amplitude = val

    def _on_wave_toggle(self, state: bool):
        self._wave_active = state

    def _tick_anim(self):
        if hasattr(self, "blend_canvas") and self.blend_canvas.winfo_exists():
            self.blend_canvas.redraw()
        self.root.after(16, self._tick_anim)  # ~60 FPS


def main():
    root = tk.Tk()
    app = ExtendedCanvasShowcaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
