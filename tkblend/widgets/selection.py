"""
Selection and toggle controls: Switch, Checkbox, Radio, RadioGroup, and SegmentedControl.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, List

from tkblend.surface import ColorLike
from tkblend.theme import get_theme, resolve_color_failsafe
from tkblend.widgets.base import Widget
from tkblend.widgets.drawing import draw_vector_checkmark


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
        command: Optional[Callable] = None,
        variable: Optional[Any] = None,
        on_color: Optional[ColorLike] = None,
        off_color: Optional[ColorLike] = None,
        knob_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._variable = variable
        if self._variable is not None:
            try:
                is_on = bool(self._variable.get())
            except Exception:
                pass
        self._is_on = is_on
        self._on_toggle = on_toggle or command
        self._explicit_on_color = on_color
        self._explicit_off_color = off_color
        self._explicit_knob_color = knob_color
        pal = get_theme()
        self._on_color = on_color or pal.primary
        self._off_color = off_color or pal.track_bg
        self._knob_color = knob_color or pal.thumb_color
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

        if self._variable is not None:
            try:
                self._trace_id = self._variable.trace_add("write", self._on_var_changed)
            except Exception:
                pass

    def _on_var_changed(self, *args) -> None:
        if self._variable is not None:
            try:
                new_val = bool(self._variable.get())
                if new_val != self._is_on:
                    self._is_on = new_val
                    self.render()
            except Exception:
                pass

    @property
    def is_on(self) -> bool:
        return self._is_on

    @is_on.setter
    def is_on(self, val: bool) -> None:
        self._is_on = bool(val)
        if self._variable is not None:
            try:
                self._variable.set(self._is_on)
            except Exception:
                pass
        self.render()

    def toggle(self) -> None:
        self._is_on = not self._is_on
        if self._variable is not None:
            try:
                self._variable.set(self._is_on)
            except Exception:
                pass
        self.render()
        if self._on_toggle:
            try:
                self._on_toggle(self._is_on)
            except TypeError:
                self._on_toggle()

    def _handle_click(self, event) -> None:
        if not self._is_disabled:
            self.toggle()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            pad = 2.0 * self._scale
            w = max(1.0, self._widget_w - pad * 2.0)
            h = max(1.0, self._widget_h - pad * 2.0)

            pal = get_theme()
            on_col = resolve_color_failsafe(self._explicit_on_color, palette=pal) if self._explicit_on_color else pal.primary
            off_col = resolve_color_failsafe(self._explicit_off_color, palette=pal) if self._explicit_off_color else pal.track_bg

            if self._explicit_knob_color is not None:
                knob_col = resolve_color_failsafe(self._explicit_knob_color, palette=pal)
            else:
                if self._is_on:
                    knob_col = pal.card_bg if pal.dark_mode else "#ffffff"
                else:
                    knob_col = pal.text_muted if pal.dark_mode else "#ffffff"

            track_col = on_col if self._is_on else off_col
            progress = 1.0 if self._is_on else 0.0

            focus_col = pal.input_focus if self._has_focus else "#00000000"
            focus_width = 1.5 * self._scale if self._has_focus else 0.0
            thumb_border = "#00000020" if not pal.dark_mode else "#ffffff15"

            self._surface.draw_switch(
                x=pad,
                y=pad,
                w=w,
                h=h,
                track_color=track_col,
                thumb_color=knob_col,
                thumb_border_color=thumb_border,
                progress_t=progress,
                is_hovered=self._is_hovered,
                focus_ring_color=focus_col,
                focus_ring_width=focus_width,
            )
            self._surface.blit(self._photo)
        except Exception:
            pass


ModernSwitch = Switch
ToggleSwitch = Switch


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
        if not self._is_disabled:
            self.toggle()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            box_size = 18.0 * s
            box_x = 4.0 * s
            box_y = (self._widget_h - box_size) / 2.0
            r = 5.0 * s

            pal = get_theme()
            if self._checked:
                box_bg = self._active_color
                border_col = "#00000000"
                border_w = 0.0
                check_col = pal.primary_fg
            else:
                box_bg = pal.secondary if self._is_hovered else pal.surface
                border_col = pal.primary if self._is_hovered else pal.card_border
                border_w = 1.2 * s
                check_col = "#00000000"

            focus_col = pal.input_focus if self._has_focus else "#00000000"
            focus_width = 1.5 * s if self._has_focus else 0.0

            self._surface.draw_checkbox(
                x=box_x,
                y=box_y,
                size=box_size,
                rx=r,
                ry=r,
                box_bg=box_bg,
                border_color=border_col,
                border_width=border_w,
                check_color=check_col,
                is_checked=self._checked,
                is_hovered=self._is_hovered,
                focus_ring_color=focus_col,
                focus_ring_width=focus_width,
            )

            text_x = box_x + box_size + 10.0 * s
            font_sz = self._font_config.size * s
            self._surface.draw_text(
                self._text,
                text_x,
                self._widget_h / 2.0 + (font_sz * 0.35),
                font=self._font_config.copy_with(size=font_sz),
                color=pal.fg,
                align="left",
            )
            self._surface.blit(self._photo)
        except Exception:
            pass


ModernCheckbox = Checkbox


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

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, val: bool) -> None:
        self._selected = bool(val)
        self.render()

    def _handle_click(self, event) -> None:
        if not self._is_disabled:
            if self._group:
                self._group.select(self._value)
            else:
                self._selected = True
                self.render()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
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
        except Exception:
            pass


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
        on_change: Optional[Callable] = None,
        command: Optional[Callable] = None,
        width: int = 340,
        height: int = 34,
        active_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._values = list(values) if values else ["Option 1", "Option 2"]
        self._selected = max(0, min(len(self._values) - 1, selected_index))
        self._on_change = on_change or command
        self._explicit_active_color = active_color
        pal = get_theme()
        self._active_color = active_color or pal.primary
        self._hovered_index: Optional[int] = None
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

        self.bind("<Motion>", self._on_mouse_move)

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

    def _handle_leave(self, event) -> None:
        self._hovered_index = None

    def _handle_click(self, event) -> None:
        idx = self._index_at(event.x)
        if idx is not None and idx != self._selected and idx < len(self._values):
            self._selected = idx
            self.render()
            if self._on_change:
                val = self._values[idx]
                try:
                    self._on_change(idx, val)
                except TypeError:
                    try:
                        self._on_change(val)
                    except TypeError:
                        self._on_change()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            pad = 3.0 * s
            w = max(1.0, self._widget_w - pad * 2.0)
            h = max(1.0, self._widget_h - pad * 2.0)
            r = h / 2.0

            pal = get_theme()
            active_col = self._explicit_active_color or pal.primary
            # Recessed capsule track
            self._surface.fill_rounded_rect(pad, pad, w, h, r, r, pal.surface)
            self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, pal.surface_border, 1.0 * s)

            num_segs = max(1, len(self._values))
            seg_w = w / num_segs

            if self._hovered_index is not None and self._hovered_index != self._selected:
                hx = pad + self._hovered_index * seg_w
                self._surface.fill_rounded_rect(hx, pad, seg_w, h, r, r, pal.secondary)

            ax = pad + self._selected * seg_w
            safe_blur = min(1.8 * s, pad * 0.6)
            safe_offset_y = min(0.6 * s, pad * 0.2)
            self._surface.draw_shadow(
                ax + 1.0, pad + 1.0, seg_w - 2.0, h - 2.0,
                r, r, blur_radius=safe_blur, offset_y=safe_offset_y, shadow_color=pal.shadow_color
            )
            self._surface.fill_rounded_rect(ax + 1.0, pad + 1.0, seg_w - 2.0, h - 2.0, r, r, active_col)

            font_sz = 12.0 * s
            for i, val in enumerate(self._values):
                tx = pad + (i + 0.5) * seg_w
                ty = pad + h / 2.0 + (font_sz * 0.35)
                color = pal.primary_fg if i == self._selected else pal.fg
                self._surface.draw_text(val, tx, ty, font_size=font_sz, font_family="sans-serif", color=color, align="center")

            self._surface.blit(self._photo)
        except Exception:
            pass


ModernSegmentedControl = SegmentedControl
