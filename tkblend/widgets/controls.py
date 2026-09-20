"""
Interactive control widgets for tkblend: Button, Checkbox, RadioButton, RadioGroup, Switch, Slider, SegmentedControl.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, Union, List, Tuple, Any

from tkblend.surface import (
    Surface,
    ColorLike,
    LinearGradient,
    Path,
)
from tkblend.widgets.base import ModernWidget
from tkblend.widgets.theme import Theme, ThemeManager


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
        rx: Optional[float] = None,
        ry: Optional[float] = None,
        variant: str = "primary",  # "primary", "secondary", "danger", "success"
        bg_color: Optional[ColorLike] = None,
        hover_color: Optional[ColorLike] = None,
        press_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        elevation: Optional[float] = None,
        shadow_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._text = text
        self._command = command
        self._variant = variant
        self._rx = rx if rx is not None else t.radius_sm
        self._ry = ry if ry is not None else self._rx

        # Color defaults based on variant
        if variant == "primary":
            self._bg_color = bg_color if bg_color is not None else t.primary
            self._hover_color = hover_color if hover_color is not None else t.primary_hover
            self._press_color = press_color if press_color is not None else t.primary_press
            self._text_color = text_color if text_color is not None else t.primary_text
        elif variant == "secondary":
            self._bg_color = bg_color if bg_color is not None else t.secondary
            self._hover_color = hover_color if hover_color is not None else t.secondary_hover
            self._press_color = press_color if press_color is not None else t.secondary_press
            self._text_color = text_color if text_color is not None else t.secondary_text
        elif variant == "danger":
            self._bg_color = bg_color if bg_color is not None else t.danger
            self._hover_color = hover_color if hover_color is not None else "#eba0ac"
            self._press_color = press_color if press_color is not None else "#e78284"
            self._text_color = text_color if text_color is not None else "#11111b"
        elif variant == "success":
            self._bg_color = bg_color if bg_color is not None else t.success
            self._hover_color = hover_color if hover_color is not None else "#b4eec4"
            self._press_color = press_color if press_color is not None else "#81c8be"
            self._text_color = text_color if text_color is not None else "#11111b"
        else:
            self._bg_color = bg_color if bg_color is not None else t.primary
            self._hover_color = hover_color if hover_color is not None else t.primary_hover
            self._press_color = press_color if press_color is not None else t.primary_press
            self._text_color = text_color if text_color is not None else t.primary_text

        self._font_size = font_size if font_size is not None else t.font_size_md
        self._font_family = font_family or t.font_family
        self._elevation = elevation if elevation is not None else t.elevation_sm
        self._shadow_color = shadow_color if shadow_color is not None else t.shadow_color
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=self._parent_bg,
            theme=theme,
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

        cur_bg = self._bg_color
        cur_elev = self._elevation
        offset_y = 2.0

        if self._is_disabled:
            cur_bg = self._theme.secondary
            cur_elev = 0.0
            offset_y = 0.0
        elif self._is_pressed:
            cur_bg = self._press_color
            cur_elev = max(1.0, self._elevation * 0.4)
            offset_y = 1.0
        elif self._is_hovered:
            cur_bg = self._hover_color
            cur_elev = self._elevation * 1.3
            offset_y = 3.0

        pad = 4.0
        btn_w = max(1.0, self._widget_w - pad * 2.0)
        btn_h = max(1.0, self._widget_h - pad * 2.0)

        # Draw drop shadow + button background
        self._surface.draw_card(
            x=pad,
            y=pad,
            w=btn_w,
            h=btn_h,
            rx=self._rx,
            ry=self._ry,
            bg_color=cur_bg,
            border_color="#ffffff22" if self._variant == "primary" else self._theme.border,
            border_width=1.0,
            shadow_blur=cur_elev * 1.5,
            shadow_spread=0.0,
            shadow_offset_x=0.0,
            shadow_offset_y=offset_y,
            shadow_color=self._shadow_color if cur_elev > 0 else "#00000000",
        )

        # Draw centered text
        text_x = self._widget_w / 2.0
        text_y = self._widget_h / 2.0 + (self._font_size * 0.35)
        if self._is_pressed and not self._is_disabled:
            text_y += 1.0

        color = self._theme.text_disabled if self._is_disabled else self._text_color
        self._surface.draw_text(
            self._text,
            x=text_x,
            y=text_y,
            font_size=self._font_size,
            font_family=self._font_family,
            color=color,
            align="center",
        )

        self._surface.blit(self._photo)


class ModernSwitch(ModernWidget):
    """
    Modern iOS / Fluent-style toggle switch with smooth animated knob.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 56,
        height: int = 30,
        is_on: bool = False,
        on_toggle: Optional[Callable[[bool], None]] = None,
        on_color: Optional[ColorLike] = None,
        off_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._is_on = bool(is_on)
        self._on_toggle = on_toggle
        self._on_color = on_color if on_color is not None else t.primary
        self._off_color = off_color if off_color is not None else t.track
        self._knob_color = knob_color if knob_color is not None else t.knob
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window

        # Animation state: knob progress from 0.0 (off) to 1.0 (on)
        self._progress: float = 1.0 if self._is_on else 0.0

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=self._parent_bg,
            theme=theme,
            **kwargs,
        )

        self.bind("<ButtonRelease-1>", self._handle_toggle)

    @property
    def is_on(self) -> bool:
        return self._is_on

    @is_on.setter
    def is_on(self, val: bool) -> None:
        new_val = bool(val)
        if self._is_on != new_val:
            self._is_on = new_val
            target = 1.0 if self._is_on else 0.0
            self.animate_property(
                start_val=self._progress,
                end_val=target,
                duration_ms=180,
                on_update=self._set_progress,
            )

    def _set_progress(self, val: float) -> None:
        self._progress = val

    def toggle(self) -> None:
        self.is_on = not self._is_on
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
        bg = self._on_color if self._progress > 0.5 else self._off_color
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, bg)

        # Interpolated knob center X
        knob_r = r - 3.0
        knob_cy = pad + r
        off_x = pad + r
        on_x = pad + w - r
        knob_cx = off_x + (on_x - off_x) * self._progress

        # Knob shadow
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


class ModernCheckbox(ModernWidget):
    """
    Modern antialiased Checkbox with animated checkmark and text label.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Checkbox",
        is_checked: bool = False,
        on_change: Optional[Callable[[bool], None]] = None,
        box_size: float = 20.0,
        checked_color: Optional[ColorLike] = None,
        box_color: Optional[ColorLike] = None,
        checkmark_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        width: int = 160,
        height: int = 32,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._text = text
        self._is_checked = bool(is_checked)
        self._on_change = on_change
        self._box_size = box_size
        self._checked_color = checked_color if checked_color is not None else t.primary
        self._box_color = box_color if box_color is not None else t.bg_surface_alt
        self._checkmark_color = checkmark_color if checkmark_color is not None else t.primary_text
        self._text_color = text_color if text_color is not None else t.text
        self._font_size = font_size if font_size is not None else t.font_size_md
        self._font_family = font_family or t.font_family
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window

        self._check_progress: float = 1.0 if self._is_checked else 0.0

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=self._parent_bg,
            theme=theme,
            **kwargs,
        )

        self.bind("<ButtonRelease-1>", self._handle_click)

    @property
    def is_checked(self) -> bool:
        return self._is_checked

    @is_checked.setter
    def is_checked(self, val: bool) -> None:
        new_val = bool(val)
        if self._is_checked != new_val:
            self._is_checked = new_val
            target = 1.0 if self._is_checked else 0.0
            self.animate_property(
                start_val=self._check_progress,
                end_val=target,
                duration_ms=160,
                on_update=self._set_progress,
            )

    def _set_progress(self, val: float) -> None:
        self._check_progress = val

    def toggle(self) -> None:
        self.is_checked = not self._is_checked
        if self._on_change:
            self._on_change(self._is_checked)

    def _handle_click(self, event) -> None:
        if not self._is_disabled:
            if 0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h:
                self.toggle()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        box_y = (self._widget_h - self._box_size) / 2.0
        box_x = 4.0
        r = 5.0

        # Draw box
        bg = self._checked_color if self._check_progress > 0.5 else self._box_color
        border_col = self._checked_color if self._check_progress > 0.5 else self._theme.border

        self._surface.fill_rounded_rect(box_x, box_y, self._box_size, self._box_size, r, r, bg)
        self._surface.stroke_rounded_rect(
            box_x, box_y, self._box_size, self._box_size, r, r, border_col, stroke_width=1.5
        )

        # Draw checkmark path if checked
        if self._check_progress > 0.1:
            p = Path()
            p1_x = box_x + self._box_size * 0.25
            p1_y = box_y + self._box_size * 0.52
            p2_x = box_x + self._box_size * 0.44
            p2_y = box_y + self._box_size * 0.72
            p3_x = box_x + self._box_size * 0.78
            p3_y = box_y + self._box_size * 0.28

            p.move_to(p1_x, p1_y)
            p.line_to(p2_x, p2_y)
            p.line_to(p3_x, p3_y)

            self._surface.stroke_path(p, self._checkmark_color, stroke_width=2.2)

        # Draw Label Text
        text_x = box_x + self._box_size + 10.0
        text_y = self._widget_h / 2.0 + (self._font_size * 0.35)
        color = self._theme.text_disabled if self._is_disabled else self._text_color
        self._surface.draw_text(
            self._text,
            x=text_x,
            y=text_y,
            font_size=self._font_size,
            font_family=self._font_family,
            color=color,
            align="left",
        )

        self._surface.blit(self._photo)


class ModernRadioButton(ModernWidget):
    """
    Modern RadioButton with animated bullet and text label.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Option",
        value: Any = None,
        is_selected: bool = False,
        on_select: Optional[Callable[[Any], None]] = None,
        radius: float = 10.0,
        selected_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        width: int = 150,
        height: int = 32,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._text = text
        self._value = value if value is not None else text
        self._is_selected = bool(is_selected)
        self._on_select = on_select
        self._r = radius
        self._selected_color = selected_color if selected_color is not None else t.primary
        self._text_color = text_color if text_color is not None else t.text
        self._font_size = font_size if font_size is not None else t.font_size_md
        self._font_family = font_family or t.font_family
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window

        self._bullet_progress: float = 1.0 if self._is_selected else 0.0

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=self._parent_bg,
            theme=theme,
            **kwargs,
        )

        self.bind("<ButtonRelease-1>", self._handle_click)

    @property
    def value(self) -> Any:
        return self._value

    @property
    def is_selected(self) -> bool:
        return self._is_selected

    @is_selected.setter
    def is_selected(self, val: bool) -> None:
        new_val = bool(val)
        if self._is_selected != new_val:
            self._is_selected = new_val
            target = 1.0 if self._is_selected else 0.0
            self.animate_property(
                start_val=self._bullet_progress,
                end_val=target,
                duration_ms=160,
                on_update=self._set_progress,
            )

    def _set_progress(self, val: float) -> None:
        self._bullet_progress = val

    def select(self) -> None:
        self.is_selected = True
        if self._on_select:
            self._on_select(self._value)

    def _handle_click(self, event) -> None:
        if not self._is_disabled:
            if 0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h:
                self.select()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        cx = 4.0 + self._r
        cy = self._widget_h / 2.0

        # Outer ring
        border_col = self._selected_color if self._bullet_progress > 0.5 else self._theme.border
        bg_col = self._theme.bg_surface_alt
        self._surface.fill_circle(cx, cy, self._r, bg_col)
        self._surface.stroke_circle(cx, cy, self._r, border_col, stroke_width=1.8)

        # Inner bullet
        if self._bullet_progress > 0.05:
            inner_r = (self._r - 4.5) * self._bullet_progress
            self._surface.fill_circle(cx, cy, max(1.0, inner_r), self._selected_color)

        # Label text
        text_x = cx + self._r + 10.0
        text_y = self._widget_h / 2.0 + (self._font_size * 0.35)
        color = self._theme.text_disabled if self._is_disabled else self._text_color
        self._surface.draw_text(
            self._text,
            x=text_x,
            y=text_y,
            font_size=self._font_size,
            font_family=self._font_family,
            color=color,
            align="left",
        )

        self._surface.blit(self._photo)


class ModernRadioGroup(tk.Frame):
    """
    Manager container for mutually exclusive ModernRadioButtons.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        options: Optional[List[str]] = None,
        selected_value: Optional[Any] = None,
        on_change: Optional[Callable[[Any], None]] = None,
        horizontal: bool = False,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window
        super().__init__(master, background=self._parent_bg, **kwargs)

        self._on_change = on_change
        self._buttons: List[ModernRadioButton] = []
        self._selected_value = selected_value
        self._theme = t

        if options:
            for opt in options:
                self.add_option(opt, opt)

        if selected_value is not None:
            self.set_value(selected_value)

    def add_option(self, label: str, value: Any) -> ModernRadioButton:
        is_sel = (self._selected_value == value)
        btn = ModernRadioButton(
            self,
            text=label,
            value=value,
            is_selected=is_sel,
            on_select=self._on_btn_selected,
            parent_bg=self._parent_bg,
            theme=self._theme,
        )
        self._buttons.append(btn)
        btn.pack(side=tk.LEFT if getattr(self, "_horizontal", False) else tk.TOP, anchor="w", pady=2)
        return btn

    def _on_btn_selected(self, val: Any) -> None:
        self._selected_value = val
        for btn in self._buttons:
            btn.is_selected = (btn.value == val)
        if self._on_change:
            self._on_change(val)

    def set_value(self, val: Any) -> None:
        self._selected_value = val
        for btn in self._buttons:
            btn.is_selected = (btn.value == val)

    @property
    def value(self) -> Any:
        return self._selected_value


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
        step: Optional[float] = None,
        on_change: Optional[Callable[[float], None]] = None,
        track_color: Optional[ColorLike] = None,
        active_track_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        knob_radius: float = 9.0,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._min = float(min_val)
        self._max = float(max_val)
        self._step = float(step) if step is not None else None
        self._value = max(self._min, min(self._max, float(value)))
        self._on_change = on_change
        self._track_color = track_color if track_color is not None else t.track
        self._active_track_color = active_track_color if active_track_color is not None else t.primary
        self._knob_color = knob_color if knob_color is not None else t.knob
        self._knob_r = knob_radius
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window
        self._is_dragging = False

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=self._parent_bg,
            theme=theme,
            **kwargs,
        )

        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Button-1>", self._on_drag)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        clamped = max(self._min, min(self._max, float(val)))
        if self._step and self._step > 0:
            clamped = round((clamped - self._min) / self._step) * self._step + self._min
            clamped = max(self._min, min(self._max, clamped))
        self._value = clamped
        self.render()

    def _on_drag(self, event) -> None:
        if self._is_disabled:
            return
        pad = self._knob_r + 4.0
        usable_w = self._widget_w - pad * 2.0
        if usable_w > 0:
            rel = max(0.0, min(1.0, (event.x - pad) / usable_w))
            raw_val = self._min + rel * (self._max - self._min)
            if self._step and self._step > 0:
                raw_val = round((raw_val - self._min) / self._step) * self._step + self._min
                raw_val = max(self._min, min(self._max, raw_val))
            self._value = raw_val
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
        self._surface.stroke_circle(
            knob_cx, self._widget_h / 2.0, self._knob_r, "#ffffff88", stroke_width=1.5
        )

        self._surface.blit(self._photo)


class ModernSegmentedControl(ModernWidget):
    """
    Modern iOS / macOS style Segmented Control with animated sliding pill indicator.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        items: Optional[List[str]] = None,
        selected_index: int = 0,
        on_select: Optional[Callable[[int, str], None]] = None,
        width: int = 280,
        height: int = 36,
        rx: Optional[float] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._items = items or ["Option 1", "Option 2"]
        self._selected_index = max(0, min(len(self._items) - 1, selected_index))
        self._on_select = on_select
        self._rx = rx if rx is not None else t.radius_sm
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window

        # Animation progress for indicator X position
        self._anim_index: float = float(self._selected_index)

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=self._parent_bg,
            theme=theme,
            **kwargs,
        )

        self.bind("<ButtonRelease-1>", self._handle_click)

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @selected_index.setter
    def selected_index(self, idx: int) -> None:
        idx = max(0, min(len(self._items) - 1, int(idx)))
        if self._selected_index != idx:
            self._selected_index = idx
            self.animate_property(
                start_val=self._anim_index,
                end_val=float(idx),
                duration_ms=180,
                on_update=self._set_anim_index,
            )

    def _set_anim_index(self, val: float) -> None:
        self._anim_index = val

    def _handle_click(self, event) -> None:
        if self._is_disabled or not self._items:
            return
        seg_w = self._widget_w / len(self._items)
        idx = int(event.x // seg_w)
        idx = max(0, min(len(self._items) - 1, idx))
        self.selected_index = idx
        if self._on_select:
            self._on_select(self._selected_index, self._items[self._selected_index])

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        if not self._items:
            self._surface.blit(self._photo)
            return

        pad = 3.0
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        n = len(self._items)
        seg_w = w / n

        # Container backdrop
        self._surface.fill_rounded_rect(pad, pad, w, h, self._rx, self._rx, self._theme.bg_surface_alt)
        self._surface.stroke_rounded_rect(
            pad, pad, w, h, self._rx, self._rx, self._theme.border, stroke_width=1.0
        )

        # Sliding Pill Indicator
        pill_pad = 2.0
        pill_x = pad + self._anim_index * seg_w + pill_pad
        pill_y = pad + pill_pad
        pill_w = max(1.0, seg_w - pill_pad * 2.0)
        pill_h = max(1.0, h - pill_pad * 2.0)
        pill_r = max(2.0, self._rx - 2.0)

        # Pill Shadow + Background
        self._surface.draw_card(
            x=pill_x,
            y=pill_y,
            w=pill_w,
            h=pill_h,
            rx=pill_r,
            ry=pill_r,
            bg_color=self._theme.primary,
            border_color="#ffffff22",
            border_width=1.0,
            shadow_blur=4.0,
            shadow_offset_y=1.5,
            shadow_color="#00000044",
        )

        # Draw segment texts
        for i, item in enumerate(self._items):
            item_cx = pad + (i + 0.5) * seg_w
            item_cy = self._widget_h / 2.0 + (self._theme.font_size_sm * 0.35)
            # Text color depends on whether active
            color = self._theme.primary_text if i == self._selected_index else self._theme.text_muted
            self._surface.draw_text(
                item,
                x=item_cx,
                y=item_cy,
                font_size=self._theme.font_size_sm,
                font_family=self._theme.font_family,
                color=color,
                align="center",
            )

        self._surface.blit(self._photo)
