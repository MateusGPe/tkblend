"""
Interactive control widgets for tkblend: ModernButton, ModernSwitch, ModernCheckbox,
ModernRadioButton, ModernRadioGroup, ModernSlider, and ModernSegmentedControl.

Supports CustomTkinter and ttkbootstrap styling conventions, full .configure() / .cget() protocol,
semantic variants (primary, secondary, success, danger, warning, info, outline, ghost),
and Blend2D hardware-accelerated vector drawing with smooth animations.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, Union, List, Tuple, Any, Dict

from tkblend.surface import (
    Surface,
    ColorLike,
    LinearGradient,
    Path,
)
from tkblend.widgets.base import ModernWidget, _resolve_parent_bg
from tkblend.widgets.theme import Theme, ThemeManager, accent_on_color, RampColor


# ============================================================================
# ModernButton
# ============================================================================

class ModernButton(ModernWidget):
    """
    Modern Button with hover/press elevation animations, gradients,
    soft drop shadows, antialiased typography, click callback, and semantic variants.
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
        corner_radius: Optional[float] = None,
        variant: str = "primary",
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
        self._text = text
        self._command = command
        self._variant = (variant or "primary").lower()
        self._rx_custom = corner_radius if corner_radius is not None else rx
        self._ry_custom = corner_radius if corner_radius is not None else (ry if ry is not None else self._rx_custom)
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

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        redraw = False
        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
            redraw = True
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "variant" in kwargs:
            self._variant = str(kwargs.pop("variant")).lower()
            redraw = True
        if "corner_radius" in kwargs:
            cr = kwargs.pop("corner_radius")
            self._rx_custom = cr
            self._ry_custom = cr
            redraw = True
        if "rx" in kwargs:
            self._rx_custom = kwargs.pop("rx")
            redraw = True
        if "ry" in kwargs:
            self._ry_custom = kwargs.pop("ry")
            redraw = True
        if "bg_color" in kwargs:
            self._custom_bg_color = kwargs.pop("bg_color")
            redraw = True
        if "hover_color" in kwargs:
            self._custom_hover_color = kwargs.pop("hover_color")
            redraw = True
        if "press_color" in kwargs:
            self._custom_press_color = kwargs.pop("press_color")
            redraw = True
        if "text_color" in kwargs or "fg_color" in kwargs:
            self._custom_text_color = kwargs.pop("text_color", None) or kwargs.pop("fg_color", None)
            redraw = True
        if "font_size" in kwargs:
            self._custom_font_size = kwargs.pop("font_size")
            redraw = True
        if "font_family" in kwargs:
            self._custom_font_family = kwargs.pop("font_family")
            redraw = True
        if "elevation" in kwargs:
            self._custom_elevation = kwargs.pop("elevation")
            redraw = True
        if "shadow_color" in kwargs:
            self._custom_shadow_color = kwargs.pop("shadow_color")
            redraw = True
        return redraw

    def _cget_subclass(self, key: str) -> Optional[Any]:
        if key == "text":
            return self._text
        elif key == "command":
            return self._command
        elif key == "variant":
            return self._variant
        elif key in ("corner_radius", "rx"):
            return self._rx_custom
        elif key == "ry":
            return self._ry_custom
        elif key == "bg_color":
            return self._custom_bg_color
        elif key == "hover_color":
            return self._custom_hover_color
        elif key == "press_color":
            return self._custom_press_color
        elif key in ("text_color", "fg_color"):
            return self._custom_text_color
        elif key == "font_size":
            return self._custom_font_size
        elif key == "font_family":
            return self._custom_font_family
        elif key == "elevation":
            return self._custom_elevation
        elif key == "shadow_color":
            return self._custom_shadow_color
        return None

    def _handle_click(self, event) -> None:
        if not self._is_disabled and self._command:
            if 0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h:
                self._command()

    def set_text(self, text: str) -> None:
        self.configure(text=text)

    def _resolve_colors(self) -> Tuple[ColorLike, ColorLike, ColorLike, ColorLike]:
        t = self._theme
        norm, hov, prs, txt = t.get_variant_colors(self._variant)

        bg = self._custom_bg_color if self._custom_bg_color is not None else norm
        hover = self._custom_hover_color if self._custom_hover_color is not None else hov
        press = self._custom_press_color if self._custom_press_color is not None else prs
        
        # Auto-compute text color with WCAG contrast if not overridden
        if self._custom_text_color is not None:
            text_c = self._custom_text_color
        elif self._variant in ("outline", "ghost"):
            text_c = txt
        else:
            text_c = txt if isinstance(bg, str) and not bg.startswith("#") else accent_on_color(str(bg))

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
            cur_bg = t.bg_surface
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
        border_col = "#ffffff22" if self._variant == "primary" else (t.primary if self._variant == "outline" else t.border)
        is_transparent_bg = (cur_bg == "transparent")

        if not is_transparent_bg or cur_elev > 0:
            self._surface.draw_card(
                x=pad,
                y=pad,
                w=btn_w,
                h=btn_h,
                rx=rx,
                ry=ry,
                bg_color=cur_bg if not is_transparent_bg else self._parent_bg,
                border_color=border_col,
                border_width=1.0,
                shadow_blur=cur_elev * 1.5,
                shadow_spread=0.0,
                shadow_offset_x=0.0,
                shadow_offset_y=offset_y,
                shadow_color=shadow_color if (cur_elev > 0 and not self._is_disabled) else "#00000000",
            )
        elif self._variant == "outline":
            self._surface.stroke_rounded_rect(pad, pad, btn_w, btn_h, rx, ry, border_col, stroke_width=1.2)

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


# ============================================================================
# ModernSwitch
# ============================================================================

class ModernSwitch(ModernWidget):
    """
    Modern iOS / Fluent-style toggle switch with smooth animated knob and .configure() / .cget() support.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 56,
        height: int = 30,
        is_on: bool = False,
        on_toggle: Optional[Callable[[bool], None]] = None,
        command: Optional[Callable[[], None]] = None,
        on_color: Optional[ColorLike] = None,
        off_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        self._is_on = bool(is_on)
        self._on_toggle = on_toggle
        self._command = command
        self._custom_on_color = on_color
        self._custom_off_color = off_color
        self._custom_knob_color = knob_color
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

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        redraw = False
        if "is_on" in kwargs:
            self.is_on = bool(kwargs.pop("is_on"))
            redraw = True
        if "on_toggle" in kwargs:
            self._on_toggle = kwargs.pop("on_toggle")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "on_color" in kwargs:
            self._custom_on_color = kwargs.pop("on_color")
            redraw = True
        if "off_color" in kwargs:
            self._custom_off_color = kwargs.pop("off_color")
            redraw = True
        if "knob_color" in kwargs:
            self._custom_knob_color = kwargs.pop("knob_color")
            redraw = True
        return redraw

    def _cget_subclass(self, key: str) -> Optional[Any]:
        if key == "is_on":
            return self._is_on
        elif key == "on_toggle":
            return self._on_toggle
        elif key == "command":
            return self._command
        elif key == "on_color":
            return self._custom_on_color
        elif key == "off_color":
            return self._custom_off_color
        elif key == "knob_color":
            return self._custom_knob_color
        return None

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
        if self._command:
            self._command()

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

        bg = on_color if self._progress > 0.5 else off_color
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, bg)

        knob_r = r - 3.0
        knob_cy = pad + r
        off_x = pad + r
        on_x = pad + w - r
        knob_cx = off_x + (on_x - off_x) * self._progress

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


# ============================================================================
# ModernCheckbox
# ============================================================================

class ModernCheckbox(ModernWidget):
    """
    Modern antialiased Checkbox with animated checkmark, label, and .configure() / .cget().
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Checkbox",
        is_checked: bool = False,
        on_change: Optional[Callable[[bool], None]] = None,
        command: Optional[Callable[[], None]] = None,
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
        self._command = command
        self._box_size = box_size
        self._custom_checked_color = checked_color
        self._custom_box_color = box_color
        self._custom_checkmark_color = checkmark_color
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

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        redraw = False
        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
            redraw = True
        if "is_checked" in kwargs:
            self.is_checked = bool(kwargs.pop("is_checked"))
            redraw = True
        if "on_change" in kwargs:
            self._on_change = kwargs.pop("on_change")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "checked_color" in kwargs:
            self._custom_checked_color = kwargs.pop("checked_color")
            redraw = True
        if "box_color" in kwargs:
            self._custom_box_color = kwargs.pop("box_color")
            redraw = True
        if "checkmark_color" in kwargs:
            self._custom_checkmark_color = kwargs.pop("checkmark_color")
            redraw = True
        if "text_color" in kwargs:
            self._custom_text_color = kwargs.pop("text_color")
            redraw = True
        return redraw

    def _cget_subclass(self, key: str) -> Optional[Any]:
        if key == "text":
            return self._text
        elif key == "is_checked":
            return self._is_checked
        elif key == "on_change":
            return self._on_change
        elif key == "command":
            return self._command
        elif key == "checked_color":
            return self._custom_checked_color
        elif key == "box_color":
            return self._custom_box_color
        elif key == "checkmark_color":
            return self._custom_checkmark_color
        elif key == "text_color":
            return self._custom_text_color
        return None

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
        if self._command:
            self._command()

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

        bg = checked_color if self._check_progress > 0.5 else box_color
        border_col = checked_color if self._check_progress > 0.5 else t.border

        self._surface.fill_rounded_rect(box_x, box_y, self._box_size, self._box_size, r, r, bg)
        self._surface.stroke_rounded_rect(
            box_x, box_y, self._box_size, self._box_size, r, r, border_col, stroke_width=1.5
        )

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


# ============================================================================
# ModernRadioButton & ModernRadioGroup
# ============================================================================

class ModernRadioButton(ModernWidget):
    """
    Modern RadioButton with animated bullet, text label, and .configure() / .cget().
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Option",
        value: Any = None,
        is_selected: bool = False,
        on_select: Optional[Callable[[Any], None]] = None,
        command: Optional[Callable[[], None]] = None,
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
        self._command = command
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

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        redraw = False
        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
            redraw = True
        if "value" in kwargs:
            self._value = kwargs.pop("value")
        if "is_selected" in kwargs:
            self.is_selected = bool(kwargs.pop("is_selected"))
            redraw = True
        if "on_select" in kwargs:
            self._on_select = kwargs.pop("on_select")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "selected_color" in kwargs:
            self._custom_selected_color = kwargs.pop("selected_color")
            redraw = True
        if "text_color" in kwargs:
            self._custom_text_color = kwargs.pop("text_color")
            redraw = True
        return redraw

    def _cget_subclass(self, key: str) -> Optional[Any]:
        if key == "text":
            return self._text
        elif key == "value":
            return self._value
        elif key == "is_selected":
            return self._is_selected
        elif key == "selected_color":
            return self._custom_selected_color
        elif key == "text_color":
            return self._custom_text_color
        return None

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
        if self._command:
            self._command()

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

        border_col = selected_color if self._bullet_progress > 0.5 else t.border
        bg_col = t.bg_surface_alt
        self._surface.fill_circle(cx, cy, self._r, bg_col)
        self._surface.stroke_circle(cx, cy, self._r, border_col, stroke_width=1.8)

        if self._bullet_progress > 0.05:
            inner_r = (self._r - 4.5) * self._bullet_progress
            self._surface.fill_circle(cx, cy, max(1.0, inner_r), selected_color)

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
    Manager container for mutually exclusive ModernRadioButtons with clean container theming.
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


# ============================================================================
# ModernSlider
# ============================================================================

class ModernSlider(ModernWidget):
    """
    Smooth interactive slider with custom track, glowing knob, discrete step snapping,
    and CustomTkinter-style configure / cget parity.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 28,
        min_val: float = 0.0,
        max_val: float = 100.0,
        from_: Optional[float] = None,
        to: Optional[float] = None,
        value: float = 50.0,
        step: Optional[float] = None,
        on_change: Optional[Callable[[float], None]] = None,
        command: Optional[Callable[[float], None]] = None,
        track_color: Optional[ColorLike] = None,
        active_track_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        knob_radius: float = 9.0,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        self._min = float(from_ if from_ is not None else min_val)
        self._max = float(to if to is not None else max_val)
        self._step = float(step) if step is not None else None
        self._value = max(self._min, min(self._max, float(value)))
        self._on_change = on_change or command
        self._custom_track_color = track_color
        self._custom_active_track_color = active_track_color
        self._custom_knob_color = knob_color
        self._knob_r = knob_radius

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

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        redraw = False
        if "value" in kwargs:
            self.value = float(kwargs.pop("value"))
            redraw = True
        if "from_" in kwargs or "min_val" in kwargs:
            self._min = float(kwargs.pop("from_", None) or kwargs.pop("min_val"))
            redraw = True
        if "to" in kwargs or "max_val" in kwargs:
            self._max = float(kwargs.pop("to", None) or kwargs.pop("max_val"))
            redraw = True
        if "step" in kwargs:
            self._step = float(kwargs.pop("step"))
        if "on_change" in kwargs or "command" in kwargs:
            self._on_change = kwargs.pop("on_change", None) or kwargs.pop("command", None)
        if "track_color" in kwargs:
            self._custom_track_color = kwargs.pop("track_color")
            redraw = True
        if "active_track_color" in kwargs:
            self._custom_active_track_color = kwargs.pop("active_track_color")
            redraw = True
        if "knob_color" in kwargs:
            self._custom_knob_color = kwargs.pop("knob_color")
            redraw = True
        return redraw

    def _cget_subclass(self, key: str) -> Optional[Any]:
        if key == "value":
            return self._value
        elif key in ("from_", "min_val"):
            return self._min
        elif key in ("to", "max_val"):
            return self._max
        elif key == "step":
            return self._step
        elif key == "track_color":
            return self._custom_track_color
        elif key == "active_track_color":
            return self._custom_active_track_color
        elif key == "knob_color":
            return self._custom_knob_color
        return None

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

    def get(self) -> float:
        return self._value

    def set(self, val: float) -> None:
        self.value = val

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

        self._surface.fill_rounded_rect(
            pad, track_y, usable_w, track_h, track_h / 2.0, track_h / 2.0, track_color
        )

        rel = (self._value - self._min) / (self._max - self._min) if self._max > self._min else 0.0
        knob_cx = pad + rel * usable_w
        if rel > 0.0:
            self._surface.fill_rounded_rect(
                pad, track_y, rel * usable_w, track_h, track_h / 2.0, track_h / 2.0, active_track_color
            )

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

        self._surface.fill_circle(knob_cx, self._widget_h / 2.0, self._knob_r, knob_color)
        self._surface.stroke_circle(
            knob_cx, self._widget_h / 2.0, self._knob_r, "#ffffff88", stroke_width=1.5
        )

        self._surface.blit(self._photo)


# ============================================================================
# ModernSegmentedControl
# ============================================================================

class ModernSegmentedControl(ModernWidget):
    """
    Modern iOS / macOS style Segmented Control with animated sliding pill indicator
    and .configure() / .cget() support.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        items: Optional[List[str]] = None,
        values: Optional[List[str]] = None,
        selected_index: int = 0,
        on_select: Optional[Callable[[int, str], None]] = None,
        command: Optional[Callable[[str], None]] = None,
        width: int = 280,
        height: int = 36,
        rx: Optional[float] = None,
        corner_radius: Optional[float] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        self._items = values or items or ["Option 1", "Option 2"]
        self._selected_index = max(0, min(len(self._items) - 1, selected_index))
        self._on_select = on_select
        self._command = command
        self._custom_rx = corner_radius if corner_radius is not None else rx
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

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        redraw = False
        if "items" in kwargs or "values" in kwargs:
            self._items = kwargs.pop("items", None) or kwargs.pop("values", None)
            self._selected_index = max(0, min(len(self._items) - 1, self._selected_index))
            self._anim_index = float(self._selected_index)
            redraw = True
        if "selected_index" in kwargs:
            self.selected_index = int(kwargs.pop("selected_index"))
            redraw = True
        if "on_select" in kwargs:
            self._on_select = kwargs.pop("on_select")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "corner_radius" in kwargs or "rx" in kwargs:
            self._custom_rx = kwargs.pop("corner_radius", None) or kwargs.pop("rx", None)
            redraw = True
        return redraw

    def _cget_subclass(self, key: str) -> Optional[Any]:
        if key in ("items", "values"):
            return self._items
        elif key == "selected_index":
            return self._selected_index
        elif key == "selected_value":
            return self.get()
        elif key in ("corner_radius", "rx"):
            return self._custom_rx
        return None

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

    def get(self) -> str:
        if self._items and 0 <= self._selected_index < len(self._items):
            return self._items[self._selected_index]
        return ""

    def set(self, value: str) -> None:
        if value in self._items:
            self.selected_index = self._items.index(value)

    def _handle_click(self, event) -> None:
        if self._is_disabled or not self._items:
            return
        seg_w = self._widget_w / len(self._items)
        idx = int(event.x // seg_w)
        idx = max(0, min(len(self._items) - 1, idx))
        self.selected_index = idx
        if self._on_select:
            self._on_select(self._selected_index, self._items[self._selected_index])
        if self._command:
            self._command(self._items[self._selected_index])

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

        self._surface.fill_rounded_rect(pad, pad, w, h, rx, rx, t.bg_surface_alt)
        self._surface.stroke_rounded_rect(
            pad, pad, w, h, rx, rx, t.border, stroke_width=1.0
        )

        pill_pad = 2.0
        pill_x = pad + self._anim_index * seg_w + pill_pad
        pill_y = pad + pill_pad
        pill_w = max(1.0, seg_w - pill_pad * 2.0)
        pill_h = max(1.0, h - pill_pad * 2.0)
        pill_r = max(2.0, rx - 2.0)

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

        for i, item in enumerate(self._items):
            item_cx = pad + (i + 0.5) * seg_w
            item_cy = self._widget_h / 2.0 + (t.font_size_sm * 0.35)
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
