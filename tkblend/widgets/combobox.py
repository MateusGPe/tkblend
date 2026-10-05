"""
Pure Blend2D Vector ComboBox and OptionMenu dropdown widgets powered by BaseControl.
Zero TTK dependencies, zero PhotoImage allocations.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, List, Any, Union, Tuple

from tkblend.widgets.base import BaseControl, ScalingTracker
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    get_theme,
    resolve_color_failsafe,
    blend_color_hex,
    to_tk_hex,
)
from tkblend.font import parse_font
from tkblend.widgets.constants import (
    DEFAULT_FONT_SIZE,
    CURSOR_HAND,
    CURSOR_DEFAULT,
)
from tkblend.widgets.utils import compute_text_baseline_y


class _DropdownListControl(BaseControl):
    """Internal vector list control for floating dropdown."""

    def __init__(
        self,
        master: tk.Misc,
        master_control: "ComboBox",
        values: List[str],
        selected_value: str,
        on_select: Callable[[str], None],
        width: int,
        height: int,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._master_ctrl = master_control
        self._values = values
        self._selected_value = selected_value
        self._on_select = on_select
        self._hovered_idx: Optional[int] = None
        self._item_h = 32

        super().__init__(
            master=master,
            width=width,
            height=height,
            parent_bg=parent_bg,
            cursor=CURSOR_HAND,
            takefocus=True,
            **kwargs,
        )

        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_motion(self, event: tk.Event) -> None:
        s = self._scale_factor
        pad = int(4.0 * s)
        scaled_item_h = max(1, int(self._item_h * s))
        idx = (event.y - pad) // scaled_item_h
        if 0 <= idx < len(self._values):
            if idx != self._hovered_idx:
                self._hovered_idx = idx
                self.request_redraw()
        else:
            if self._hovered_idx is not None:
                self._hovered_idx = None
                self.request_redraw()

    def _on_leave(self, event: tk.Event) -> None:
        if self._hovered_idx is not None:
            self._hovered_idx = None
            self.request_redraw()

    def _on_click(self, event: tk.Event) -> None:
        s = self._scale_factor
        pad = int(4.0 * s)
        scaled_item_h = max(1, int(self._item_h * s))
        idx = (event.y - pad) // scaled_item_h
        if 0 <= idx < len(self._values):
            val = self._values[idx]
            self._on_select(val)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        if w <= 1.0 or h <= 1.0:
            return

        bg_color = resolve_color_failsafe(pal.card_bg, palette=pal)
        border_color = resolve_color_failsafe(pal.card_border, palette=pal)

        # Clear background
        surf.clear(bg_color)

        # Background & subtle border
        cr = 6.0 * s
        surf.fill_rounded_rect(0.0, 0.0, w, h, cr, cr, bg_color)
        surf.stroke_rounded_rect(0.0, 0.0, w, h, cr, cr, border_color, stroke_width=1.0 * s)

        pad = 4.0 * s
        item_h = float(self._item_h) * s
        font_sz = 11.0 * s
        font_cfg = parse_font(font_size=11.0)
        pad_x = 12.0 * s

        for i, val in enumerate(self._values):
            item_y = pad + i * item_h
            if item_y + item_h > h + 1.0:
                break
            is_selected = (val == self._selected_value)
            is_hover = (i == self._hovered_idx)

            if is_selected:
                surf.fill_rounded_rect(pad, item_y, w - pad * 2.0, item_h, 4.0 * s, 4.0 * s, pal.primary)
                txt_col = "#FFFFFF"
            elif is_hover:
                hover_bg = blend_color_hex(pal.card_bg, pal.fg, 0.08)
                surf.fill_rounded_rect(pad, item_y, w - pad * 2.0, item_h, 4.0 * s, 4.0 * s, hover_bg)
                txt_col = pal.fg
            else:
                txt_col = pal.fg

            text_y = compute_text_baseline_y(item_y + item_h / 2.0, font_sz)
            surf.draw_text(
                val,
                pad_x,
                text_y,
                font_size=font_sz,
                font_family=font_cfg.family,
                color=txt_col,
                bold=is_selected,
                align="left",
            )


class _DropdownPopup(tk.Toplevel):
    """Floating vector popup list window for ComboBox/OptionMenu."""

    def __init__(
        self,
        master_control: ComboBox,
        values: List[str],
        selected_value: str,
        on_select: Callable[[str], None],
    ):
        super().__init__(master_control)
        self.withdraw()
        self.overrideredirect(True)
        self._master_ctrl = master_control
        self._values = values
        self._selected_value = selected_value
        self._on_select_cb = on_select

        pal = master_control._palette
        bg_hex = to_tk_hex(pal.card_bg)
        self.configure(bg=bg_hex)

        scale = master_control._scale_factor
        item_h = int(32 * scale)
        total_h = min(int(260 * scale), len(values) * item_h + int(8 * scale))
        total_h = max(int(36 * scale), total_h)

        # Position under master control
        master_control.update_idletasks()
        root_x = master_control.winfo_rootx()
        root_y = master_control.winfo_rooty() + master_control.winfo_height() + 3
        ctrl_w = max(int(100 * scale), master_control.winfo_width())

        self.geometry(f"{ctrl_w}x{total_h}+{root_x}+{root_y}")

        # Vector List Control
        self._list_ctrl = _DropdownListControl(
            self,
            master_control=master_control,
            values=values,
            selected_value=selected_value,
            on_select=self._handle_select,
            width=ctrl_w,
            height=total_h,
            parent_bg=pal.card_bg,
        )
        self._list_ctrl.pack(fill="both", expand=True)

        # Grab & dismiss bindings
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Escape>", lambda e: self._dismiss())
        self.bind("<Button-1>", self._on_root_click)

        self.deiconify()
        self.lift()
        self.focus_force()

    def _handle_select(self, val: str) -> None:
        self._dismiss()
        self._on_select_cb(val)

    def _on_root_click(self, event: tk.Event) -> None:
        if event.widget not in (self, self._list_ctrl):
            self._dismiss()

    def _on_focus_out(self, event: tk.Event) -> None:
        # Check if focus is still within popup
        self.after(50, self._check_focus)

    def _check_focus(self) -> None:
        if not self.winfo_exists():
            return
        try:
            focus_widget = self.focus_get()
            if focus_widget not in (self, self._list_ctrl):
                self._dismiss()
        except Exception:
            self._dismiss()

    def _dismiss(self) -> None:
        if hasattr(self._master_ctrl, "_popup_active"):
            self._master_ctrl._popup_active = False
        try:
            if self.winfo_exists():
                self.destroy()
        except Exception:
            pass


class ComboBox(BaseControl):
    """
    Modern vector dropdown combo selector with antialiased typography,
    chevron indicator, and floating popup list.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        values: Optional[List[str]] = None,
        selected_value: Optional[str] = None,
        default_value: Optional[str] = None,
        command: Optional[Callable[[str], None]] = None,
        bg_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        corner_radius: float = 6.0,
        font_size: float = 11.0,
        width: int = 160,
        height: int = 34,
        cursor: Optional[str] = None,
        inner_bg: Optional[str] = None,
        outer_bg: Optional[str] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        raw_vals = values or ["Option 1", "Option 2"]
        self._values = [str(v) for v in raw_vals]
        self._value = selected_value or default_value or (self._values[0] if self._values else "")
        self._command = command
        self._custom_text_color = text_color
        self._custom_border = border_color
        self._border_width = float(border_width)
        self._corner_radius = float(corner_radius)
        self._font_size = float(font_size)
        self._is_hovered = False
        self._popup_active = False
        self._active_popup: Optional[_DropdownPopup] = None

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or CURSOR_HAND,
            takefocus=True,
            inner_bg=inner_bg or bg_color,
            outer_bg=outer_bg or parent_bg,
            **kwargs,
        )

        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _default_inner_bg(self, pal: Palette) -> str:
        return pal.input_bg

    @property
    def values(self) -> List[str]:
        return self._values

    @values.setter
    def values(self, vals: List[str]) -> None:
        self._values = [str(v) for v in vals]
        if self._value not in self._values and self._values:
            self._value = self._values[0]
        self.request_redraw()

    def get(self) -> str:
        return self._value

    def set(self, val: str) -> None:
        self._value = str(val)
        self.request_redraw()

    def current(self, index: Optional[int] = None) -> Optional[int]:
        if index is None:
            return self._values.index(self._value) if self._value in self._values else -1
        if 0 <= index < len(self._values):
            self.set(self._values[index])
            return index
        return None

    def on_theme_update(self, pal: Palette) -> None:
        if self._active_popup and self._active_popup.winfo_exists():
            try:
                self._active_popup.destroy()
            except Exception:
                pass
            self._active_popup = None
            self._popup_active = False

        # If dropdown values contain theme names (e.g. theme switcher), synchronize selected value
        norm_theme = pal.name.lower()
        for v in self._values:
            if v.lower() == norm_theme:
                self._value = v
                break

    def _on_enter(self, event) -> None:
        self._is_hovered = True
        self.request_redraw()

    def _on_leave(self, event) -> None:
        self._is_hovered = False
        self.request_redraw()

    def _on_click(self, event) -> None:
        if self.is_disabled or not self._values:
            return

        if self._active_popup and self._active_popup.winfo_exists():
            self._active_popup.destroy()
            self._active_popup = None
            self._popup_active = False
            return

        def on_selected(val: str) -> None:
            self.set(val)
            self._popup_active = False
            self._active_popup = None
            if self._command:
                try:
                    self._command(val)
                except Exception:
                    pass

        self._popup_active = True
        self._active_popup = _DropdownPopup(self, self._values, self._value, on_selected)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        cr = self._corner_radius * s
        bg_col = self.inner_bg
        txt_col = resolve_color_failsafe(self._custom_text_color or pal.fg, palette=pal)
        border_col = resolve_color_failsafe(
            self._custom_border or (pal.primary if (self._is_hovered or self._popup_active) else pal.border),
            palette=pal,
        )

        # Clear background with outer bg
        surf.clear(self.outer_bg)

        # Background & border
        surf.fill_rounded_rect(0.0, 0.0, w, h, cr, cr, bg_col)
        if self._border_width > 0.0:
            surf.stroke_rounded_rect(0.0, 0.0, w, h, cr, cr, border_col, stroke_width=self._border_width * s)

        # Value text
        scaled_font_sz = self._font_size * s
        font_cfg = parse_font(font_size=self._font_size)
        pad_x = 12.0 * s
        center_y = h / 2.0
        text_y = compute_text_baseline_y(center_y, scaled_font_sz)

        surf.draw_text(
            self._value,
            pad_x,
            text_y,
            font_size=scaled_font_sz,
            font_family=font_cfg.family,
            color=txt_col,
            align="left",
        )

        # Chevron icon on right
        chv_x = w - 16.0 * s
        chevron_icon = "chevron-up" if self._popup_active else "chevron-down"
        surf.draw_icon(
            chevron_icon,
            chv_x,
            center_y + 4.0 * s,
            size=12.0 * s,
            color=pal.text_muted if not (self._is_hovered or self._popup_active) else pal.primary,
            align="center",
        )


# Aliases
OptionMenu = ComboBox
Dropdown = ComboBox
