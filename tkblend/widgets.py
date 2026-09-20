"""
Modern UI widgets for Tkinter powered by tkblend's Blend2D vector engine.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, Union, Tuple, Any

from tkblend.surface import (
    Surface,
    ColorLike,
    GradientLike,
    LinearGradient,
    RadialGradient,
    parse_color,
)


class ModernWidget(tk.Label):
    """
    Base class for interactive vector-drawn Tkinter widgets.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 120,
        height: int = 40,
        bg: str = "#1e1e2e",
        **kwargs,
    ):
        self._widget_w = max(1, width)
        self._widget_h = max(1, height)
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


class ModernFrame(tk.Frame):
    """
    Modern container with dynamic corner radius, customizable border,
    and elevation / soft drop shadow. Allows nesting standard Tk child widgets.
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
        super().__init__(
            master,
            width=width,
            height=height,
            background=parent_bg,
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._widget_w = max(1, width)
        self._widget_h = max(1, height)
        self._rx = rx
        self._ry = ry
        self._bg_color = bg_color
        self._border_color = border_color
        self._border_width = border_width
        self._elevation = elevation
        self._shadow_color = shadow_color
        self._shadow_offset_y = shadow_offset_y
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

        # Lower background label so user widgets placed inside appear on top
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

        # Reserve padding for shadow
        pad = max(4.0, self._elevation * 0.8)
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
            pad = max(4.0, self._elevation * 0.8)
            self._surface.draw_text(
                self._title,
                x=pad + 16.0,
                y=pad + 28.0,
                font_size=15.0,
                font_family="sans-serif",
                color="#cdd6f4",
            )
            self._surface.blit(self._photo)


class ModernButton(ModernWidget):
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
        self._rx = rx
        self._ry = ry
        self._bg_color = bg_color
        self._hover_color = hover_color
        self._press_color = press_color
        self._text_color = text_color
        self._font_size = font_size
        self._font_family = font_family
        self._elevation = elevation
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
            # Verify mouse is inside button bounds on release
            if 0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h:
                self._command()

    def set_text(self, text: str) -> None:
        self._text = text
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        # Dynamic state colors and elevation
        cur_bg = self._bg_color
        cur_elev = self._elevation
        offset_y = 2.0

        if self._is_pressed:
            cur_bg = self._press_color
            cur_elev = max(1.0, self._elevation * 0.4)
            offset_y = 1.0
        elif self._is_hovered:
            cur_bg = self._hover_color
            cur_elev = self._elevation * 1.3
            offset_y = 3.0

        pad = 4.0
        btn_w = self._widget_w - pad * 2.0
        btn_h = self._widget_h - pad * 2.0

        # Draw drop shadow + button background
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

        # Draw centered text
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


class ModernProgressBar(ModernWidget):
    """
    Antialiased smooth progress bar with gradient fill and rounded capsule geometry.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 16,
        value: float = 0.0,  # [0.0 - 100.0]
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

        pad = 2.0
        r = (self._widget_h - pad * 2.0) / 2.0
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0

        # Background track
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, self._track_color)

        # Progress fill
        if self._value > 0.5:
            fill_w = max(r * 2.0, (self._value / 100.0) * w)
            grad = LinearGradient(pad, pad, pad + fill_w, pad)
            grad.add_stop(0.0, self._fill_start)
            grad.add_stop(1.0, self._fill_end)
            self._surface.fill_rounded_rect(pad, pad, fill_w, h, r, r, grad)

        self._surface.blit(self._photo)


class ModernSlider(ModernWidget):
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
        self._knob_r = knob_radius
        self._parent_bg = parent_bg
        self._is_dragging = False

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
        pad = self._knob_r + 4.0
        usable_w = self._widget_w - pad * 2.0
        if usable_w > 0:
            rel = max(0.0, min(1.0, (event.x - pad) / usable_w))
            self._value = self._min + rel * (self._max - self._min)
            self.render()
            if self._on_change:
                self._on_change(self._value)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        pad = self._knob_r + 4.0
        track_h = 6.0
        track_y = (self._widget_h - track_h) / 2.0
        usable_w = self._widget_w - pad * 2.0

        # Background track
        self._surface.fill_rounded_rect(
            pad, track_y, usable_w, track_h, track_h / 2.0, track_h / 2.0, self._track_color
        )

        # Active track portion
        rel = (self._value - self._min) / (self._max - self._min) if self._max > self._min else 0.0
        knob_cx = pad + rel * usable_w
        if rel > 0.0:
            self._surface.fill_rounded_rect(
                pad, track_y, rel * usable_w, track_h, track_h / 2.0, track_h / 2.0, self._active_track_color
            )

        # Knob Drop Shadow
        self._surface.draw_shadow(
            knob_cx - self._knob_r,
            (self._widget_h / 2.0) - self._knob_r,
            self._knob_r * 2.0,
            self._knob_r * 2.0,
            self._knob_r,
            self._knob_r,
            blur_radius=6.0,
            offset_y=2.0,
            shadow_color="#00000066",
        )

        # Knob circle
        self._surface.fill_circle(knob_cx, self._widget_h / 2.0, self._knob_r, self._knob_color)
        self._surface.stroke_circle(knob_cx, self._widget_h / 2.0, self._knob_r, "#ffffff88", stroke_width=1.5)

        self._surface.blit(self._photo)


class ModernSwitch(ModernWidget):
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

        pad = 2.0
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        r = h / 2.0

        # Background track
        bg = self._on_color if self._is_on else self._off_color
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, bg)

        # Knob
        knob_r = r - 3.0
        knob_cy = pad + r
        knob_cx = (pad + w - r) if self._is_on else (pad + r)

        # Knob Shadow
        self._surface.draw_shadow(
            knob_cx - knob_r,
            knob_cy - knob_r,
            knob_r * 2.0,
            knob_r * 2.0,
            knob_r,
            knob_r,
            blur_radius=4.0,
            offset_y=1.5,
            shadow_color="#00000055",
        )

        self._surface.fill_circle(knob_cx, knob_cy, knob_r, self._knob_color)
        self._surface.blit(self._photo)
