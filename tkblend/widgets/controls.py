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
from tkblend.widgets.base import ModernWidget, _resolve_parent_bg
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
        self._rx_custom = rx
        self._ry_custom = ry
        self._custom_bg_color = bg_color
        self._custom_hover_color = hover_color
        self._custom_press_color = press_color
        self._custom_text_color = text_color
        self._custom_font_size = font_size
        self._custom_font_family = font_family
        self._custom_elevation = elevation
        self._custom_shadow_color = shadow_color

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
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

    def _resolve_colors(self) -> Tuple[ColorLike, ColorLike, ColorLike, ColorLike]:
        t = self._theme
        if self._variant == "primary":
            bg = self._custom_bg_color if self._custom_bg_color is not None else t.primary
            hover = self._custom_hover_color if self._custom_hover_color is not None else t.primary_hover
            press = self._custom_press_color if self._custom_press_color is not None else t.primary_press
            text_c = self._custom_text_color if self._custom_text_color is not None else t.primary_text
        elif self._variant == "secondary":
            bg = self._custom_bg_color if self._custom_bg_color is not None else t.secondary
            hover = self._custom_hover_color if self._custom_hover_color is not None else t.secondary_hover
            press = self._custom_press_color if self._custom_press_color is not None else t.secondary_press
            text_c = self._custom_text_color if self._custom_text_color is not None else t.secondary_text
        elif self._variant == "danger":
            bg = self._custom_bg_color if self._custom_bg_color is not None else t.danger
            hover = self._custom_hover_color if self._custom_hover_color is not None else ("#eba0ac" if t.name == "dark" else "#ea999c")
            press = self._custom_press_color if self._custom_press_color is not None else ("#e78284" if t.name == "dark" else "#d20f39")
            text_c = self._custom_text_color if self._custom_text_color is not None else t.primary_text
        elif self._variant == "success":
            bg = self._custom_bg_color if self._custom_bg_color is not None else t.success
            hover = self._custom_hover_color if self._custom_hover_color is not None else ("#b4eec4" if t.name == "dark" else "#81c8be")
            press = self._custom_press_color if self._custom_press_color is not None else ("#81c8be" if t.name == "dark" else "#40a02b")
            text_c = self._custom_text_color if self._custom_text_color is not None else t.primary_text
        else:
            bg = self._custom_bg_color if self._custom_bg_color is not None else t.primary
            hover = self._custom_hover_color if self._custom_hover_color is not None else t.primary_hover
            press = self._custom_press_color if self._custom_press_color is not None else t.primary_press
            text_c = self._custom_text_color if self._custom_text_color is not None else t.primary_text
        return bg, hover, press, text_c

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        t = self._theme
        rx = self._rx_custom if self._rx_custom is not None else t.radius_sm
        ry = self._ry_custom if self._ry_custom is not None else rx
        font_size = self._custom_font_size if self._custom_font_size is not None else t.font_size_md
        font_family = self._custom_font_family or t.font_family
        elevation = self._custom_elevation if self._custom_elevation is not None else t.elevation_sm
        shadow_color = self._custom_shadow_color if self._custom_shadow_color is not None else t.shadow_color

        base_bg, base_hover, base_press, base_text = self._resolve_colors()

        cur_bg = base_bg
        cur_elev = elevation
        offset_y = 2.0

        if self._is_disabled:
            cur_bg = t.secondary
            cur_elev = 0.0
            offset_y = 0.0
        elif self._is_pressed:
            cur_bg = base_press
            cur_elev = max(1.0, elevation * 0.4)
            offset_y = 1.0
        elif self._is_hovered:
            cur_bg = base_hover
            cur_elev = elevation * 1.3
            offset_y = 3.0

        pad = 4.0
        btn_w = max(1.0, self._widget_w - pad * 2.0)
        btn_h = max(1.0, self._widget_h - pad * 2.0)

        # Draw drop shadow + button background
        border_col = "#ffffff22" if self._variant == "primary" else t.border
        self._surface.draw_card(
            x=pad,
            y=pad,
            w=btn_w,
            h=btn_h,
            rx=rx,
            ry=ry,
            bg_color=cur_bg,
            border_color=border_col,
            border_width=1.0,
            shadow_blur=cur_elev * 1.5,
            shadow_spread=0.0,
            shadow_offset_x=0.0,
            shadow_offset_y=offset_y,
            shadow_color=shadow_color if cur_elev > 0 else "#00000000",
        )

        # Draw centered text
        text_x = self._widget_w / 2.0
        text_y = self._widget_h / 2.0 + (font_size * 0.35)
        if self._is_pressed and not self._is_disabled:
            text_y += 1.0

        color = t.text_disabled if self._is_disabled else base_text
        self._surface.draw_text(
            self._text,
            x=text_x,
            y=text_y,
            font_size=font_size,
            font_family=font_family,
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
        self._is_on = bool(is_on)
        self._on_toggle = on_toggle
        self._custom_on_color = on_color
        self._custom_off_color = off_color
        self._custom_knob_color = knob_color

        # Animation state: knob progress from 0.0 (off) to 1.0 (on)
        self._progress: float = 1.0 if self._is_on else 0.0

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
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

        t = self._theme
        on_color = self._custom_on_color if self._custom_on_color is not None else t.primary
        off_color = self._custom_off_color if self._custom_off_color is not None else t.track
        knob_color = self._custom_knob_color if self._custom_knob_color is not None else t.knob

        pad = 2.0
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        r = h / 2.0

        # Background track
        bg = on_color if self._progress > 0.5 else off_color
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

        self._surface.fill_circle(knob_cx, knob_cy, knob_r, knob_color)
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
        self._text = text
        self._is_checked = bool(is_checked)
        self._on_change = on_change
        self._box_size = box_size
        self._custom_checked_color = checked_color
        self._custom_box_color = box_color
        self._custom_checkmark_color = checkmarkmark_color if (checkmarkmark_color := checkmark_color) is not None else None
        self._custom_text_color = text_color
        self._custom_font_size = font_size
        self._custom_font_family = font_family

        self._check_progress: float = 1.0 if self._is_checked else 0.0

        t = theme or ThemeManager.get_theme()
        f_size = font_size if font_size is not None else t.font_size_md
        needed_w = int(box_size + 16.0 + len(text) * f_size * 0.75 + 16.0)
        calc_w = max(width, needed_w) if width != 160 else needed_w

        super().__init__(
            master=master,
            width=calc_w,
            height=height,
            bg=parent_bg,
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

        t = self._theme
        checked_color = self._custom_checked_color if self._custom_checked_color is not None else t.primary
        box_color = self._custom_box_color if self._custom_box_color is not None else t.bg_surface_alt
        checkmark_color = self._custom_checkmark_color if self._custom_checkmark_color is not None else t.primary_text
        text_color = self._custom_text_color if self._custom_text_color is not None else t.text
        font_size = self._custom_font_size if self._custom_font_size is not None else t.font_size_md
        font_family = self._custom_font_family or t.font_family

        box_y = (self._widget_h - self._box_size) / 2.0
        box_x = 4.0
        r = 5.0

        # Draw box
        bg = checked_color if self._check_progress > 0.5 else box_color
        border_col = checked_color if self._check_progress > 0.5 else t.border

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

            self._surface.stroke_path(p, checkmark_color, stroke_width=2.2)

        # Draw Label Text
        text_x = box_x + self._box_size + 10.0
        text_y = self._widget_h / 2.0 + (font_size * 0.35)
        color = t.text_disabled if self._is_disabled else text_color
        self._surface.draw_text(
            self._text,
            x=text_x,
            y=text_y,
            font_size=font_size,
            font_family=font_family,
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
        self._text = text
        self._value = value if value is not None else text
        self._is_selected = bool(is_selected)
        self._on_select = on_select
        self._r = radius
        self._custom_selected_color = selected_color
        self._custom_text_color = text_color
        self._custom_font_size = font_size
        self._custom_font_family = font_family

        self._bullet_progress: float = 1.0 if self._is_selected else 0.0

        t = theme or ThemeManager.get_theme()
        f_size = font_size if font_size is not None else t.font_size_md
        needed_w = int(radius * 2.0 + 16.0 + len(text) * f_size * 0.75 + 16.0)
        calc_w = max(width, needed_w) if width != 150 else needed_w

        super().__init__(
            master=master,
            width=calc_w,
            height=height,
            bg=parent_bg,
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

        t = self._theme
        selected_color = self._custom_selected_color if self._custom_selected_color is not None else t.primary
        text_color = self._custom_text_color if self._custom_text_color is not None else t.text
        font_size = self._custom_font_size if self._custom_font_size is not None else t.font_size_md
        font_family = self._custom_font_family or t.font_family

        cx = 4.0 + self._r
        cy = self._widget_h / 2.0

        # Outer ring
        border_col = selected_color if self._bullet_progress > 0.5 else t.border
        bg_col = t.bg_surface_alt
        self._surface.fill_circle(cx, cy, self._r, bg_col)
        self._surface.stroke_circle(cx, cy, self._r, border_col, stroke_width=1.8)

        # Inner bullet
        if self._bullet_progress > 0.05:
            inner_r = (self._r - 4.5) * self._bullet_progress
            self._surface.fill_circle(cx, cy, max(1.0, inner_r), selected_color)

        # Label text
        text_x = cx + self._r + 10.0
        text_y = self._widget_h / 2.0 + (font_size * 0.35)
        color = t.text_disabled if self._is_disabled else text_color
        self._surface.draw_text(
            self._text,
            x=text_x,
            y=text_y,
            font_size=font_size,
            font_family=font_family,
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
        self._theme = t
        self._custom_parent_bg = parent_bg
        self._parent_bg = _resolve_parent_bg(master, self._custom_parent_bg, self._theme)
        super().__init__(master, background=self._parent_bg, **kwargs)

        self._on_change = on_change
        self._buttons: List[ModernRadioButton] = []
        self._selected_value = selected_value
        self._horizontal = horizontal

        ThemeManager.subscribe(self._on_theme_changed)
        self.bind("<Destroy>", lambda e: ThemeManager.unsubscribe(self._on_theme_changed))

        if options:
            for opt in options:
                self.add_option(opt, opt)

        if selected_value is not None:
            self.set_value(selected_value)

    def _on_theme_changed(self, new_theme: Theme) -> None:
        if self.winfo_exists():
            self._theme = new_theme
            self._parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, new_theme)
            self.configure(background=self._parent_bg)
            for btn in self._buttons:
                btn._on_theme_changed(new_theme)

    def add_option(self, label: str, value: Any) -> ModernRadioButton:
        is_sel = (self._selected_value == value)
        btn = ModernRadioButton(
            self,
            text=label,
            value=value,
            is_selected=is_sel,
            on_select=self._on_btn_selected,
            parent_bg=self._custom_parent_bg,
            theme=self._theme,
        )
        self._buttons.append(btn)
        btn.pack(
            side=tk.LEFT if self._horizontal else tk.TOP,
            anchor="w",
            fill=tk.X if not self._horizontal else None,
            expand=True if not self._horizontal else False,
            pady=2,
            padx=(0, 8 if self._horizontal else 0),
        )
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
        self._min = float(min_val)
        self._max = float(max_val)
        self._step = float(step) if step is not None else None
        self._value = max(self._min, min(self._max, float(value)))
        self._on_change = on_change
        self._custom_track_color = track_color
        self._custom_active_track_color = active_track_color
        self._custom_knob_color = knob_color
        self._knob_r = knob_radius
        self._is_dragging = False

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
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

        t = self._theme
        track_color = self._custom_track_color if self._custom_track_color is not None else t.track
        active_track_color = self._custom_active_track_color if self._custom_active_track_color is not None else t.primary
        knob_color = self._custom_knob_color if self._custom_knob_color is not None else t.knob

        pad = self._knob_r + 4.0
        track_h = 6.0
        track_y = (self._widget_h - track_h) / 2.0
        usable_w = self._widget_w - pad * 2.0

        # Background track
        self._surface.fill_rounded_rect(
            pad, track_y, usable_w, track_h, track_h / 2.0, track_h / 2.0, track_color
        )

        # Active track portion
        rel = (self._value - self._min) / (self._max - self._min) if self._max > self._min else 0.0
        knob_cx = pad + rel * usable_w
        if rel > 0.0:
            self._surface.fill_rounded_rect(
                pad, track_y, rel * usable_w, track_h, track_h / 2.0, track_h / 2.0, active_track_color
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
        self._surface.fill_circle(knob_cx, self._widget_h / 2.0, self._knob_r, knob_color)
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
        self._items = items or ["Option 1", "Option 2"]
        self._selected_index = max(0, min(len(self._items) - 1, selected_index))
        self._on_select = on_select
        self._custom_rx = rx
        self._anim_index: float = float(self._selected_index)

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
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

        t = self._theme
        rx = self._custom_rx if self._custom_rx is not None else t.radius_sm

        pad = 3.0
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        n = len(self._items)
        seg_w = w / n

        # Container backdrop
        self._surface.fill_rounded_rect(pad, pad, w, h, rx, rx, t.bg_surface_alt)
        self._surface.stroke_rounded_rect(
            pad, pad, w, h, rx, rx, t.border, stroke_width=1.0
        )

        # Sliding Pill Indicator
        pill_pad = 2.0
        pill_x = pad + self._anim_index * seg_w + pill_pad
        pill_y = pad + pill_pad
        pill_w = max(1.0, seg_w - pill_pad * 2.0)
        pill_h = max(1.0, h - pill_pad * 2.0)
        pill_r = max(2.0, rx - 2.0)

        # Pill Shadow + Background
        self._surface.draw_card(
            x=pill_x,
            y=pill_y,
            w=pill_w,
            h=pill_h,
            rx=pill_r,
            ry=pill_r,
            bg_color=t.primary,
            border_color="#ffffff22",
            border_width=1.0,
            shadow_blur=4.0,
            shadow_offset_y=1.5,
            shadow_color="#00000044",
        )

        # Draw segment texts
        for i, item in enumerate(self._items):
            item_cx = pad + (i + 0.5) * seg_w
            item_cy = self._widget_h / 2.0 + (t.font_size_sm * 0.35)
            # Text color depends on whether active
            color = t.primary_text if i == self._selected_index else t.text_muted
            self._surface.draw_text(
                item,
                x=item_cx,
                y=item_cy,
                font_size=t.font_size_sm,
                font_family=t.font_family,
                color=color,
                align="center",
            )

        self._surface.blit(self._photo)
