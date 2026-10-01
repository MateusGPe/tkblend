"""
Text entry and numeric stepper widgets: TextInput and SpinBox.
"""

from __future__ import annotations
import logging
import tkinter as tk
from typing import Optional, Callable, Any, Union, Tuple

from tkblend.surface import StyleEngine, PseudoState
from tkblend.theme import get_theme, Palette, resolve_color_failsafe
from tkblend.font import FontConfig, parse_font
from tkblend.widgets.base import Widget, ScalingTracker
from tkblend.widgets.drawing import draw_vector_plus, draw_vector_minus

logger = logging.getLogger(__name__)


class _TextInputBackground(Widget):
    """Backing vector surface for TextInput."""

    def __init__(self, owner: Entry, master: tk.Misc, width: int, height: int, bg: Optional[str] = None):
        import weakref
        self._owner_ref = weakref.ref(owner)
        super().__init__(master=master, width=width, height=height, bg=bg)

    @property
    def _owner(self) -> Optional[Entry]:
        return self._owner_ref() if hasattr(self, "_owner_ref") else None

    def _on_configure(self, event) -> None:
        super()._on_configure(event)
        owner = self._owner
        if owner is not None and hasattr(owner, "winfo_exists") and owner.winfo_exists():
            owner._update_entry_geometry()

    def _on_theme_changed(self, palette: Palette) -> None:
        super()._on_theme_changed(palette)
        owner = self._owner
        if owner is not None and hasattr(owner, "winfo_exists") and owner.winfo_exists():
            owner._update_theme_colors()

    def render(self) -> None:
        owner = self._owner
        if owner is not None:
            owner._render_bg()


class Entry(tk.Frame):
    """
    Modern vector text entry with rounded border, glowing focus ring,
    placeholder text, and clear button icon (✕).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        placeholder: str = "Enter text...",
        placeholder_text: Optional[str] = None,
        width: int = 240,
        height: int = 38,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        if placeholder_text is not None:
            placeholder = placeholder_text
        self._scale = ScalingTracker.get_scaling_factor(master)
        s = self._scale
        pal = get_theme()
        self._explicit_parent_bg = parent_bg
        self._parent_bg = parent_bg or Widget._resolve_default_bg(master, pal)

        # Typography configuration
        font_spec = kwargs.pop("font", None)
        font_size = kwargs.pop("font_size", None)
        font_family = kwargs.pop("font_family", None)
        bold = kwargs.pop("bold", None)
        italic = kwargs.pop("italic", None)
        weight = kwargs.pop("weight", None)

        self._custom_font_override = any(
            x is not None for x in (font_spec, font_size, font_family, bold, italic, weight)
        )
        self._font_config = parse_font(
            font=font_spec,
            font_size=font_size,
            font_family=font_family,
            bold=bold,
            italic=italic,
            weight=weight,
            default_family="default",
            default_size=12.0,
        )

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

        entry_font = self._get_effective_tk_font()
        self._entry = tk.Entry(
            self,
            bg=pal.input_bg,
            fg=pal.fg,
            insertbackground=pal.input_focus,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            font=entry_font,
        )
        self._entry._tkblend_injected_font = entry_font
        if self._custom_font_override:
            self._entry._tkblend_custom_font_override = True

        self._update_entry_geometry()

        if self._placeholder:
            self._placeholder_active = True
            self._entry.insert(0, self._placeholder)
            self._entry.configure(fg=pal.text_muted)

        self.bind("<Configure>", self._on_configure)
        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<KeyRelease>", self._on_key_release)
        self._bg_widget.bind("<Button-1>", self._on_bg_click)

        self._render_bg()

    def _on_configure(self, event) -> None:
        self._update_entry_geometry()

    def _update_entry_geometry(self) -> None:
        if not hasattr(self, "_entry") or not self._entry.winfo_exists():
            return
        s = self._scale
        pad_l = int(14.0 * s)
        pad_r = int(32.0 * s)
        w_total = getattr(self._bg_widget, "_widget_w", self.winfo_width())
        h_total = getattr(self._bg_widget, "_widget_h", self.winfo_height())
        if w_total <= 1:
            w_total = max(1, self.winfo_reqwidth())
        if h_total <= 1:
            h_total = max(1, self.winfo_reqheight())
        entry_w = max(10, w_total - pad_l - pad_r)

        eff_size = self._font_config.size * s
        entry_h = max(10, min(h_total - 4, int(eff_size * 1.5 + 4)))
        entry_y = max(2, int((h_total - entry_h) / 2.0))
        self._entry.place(x=pad_l, y=entry_y, width=entry_w, height=entry_h)

    def _get_effective_tk_font(self) -> Union[Tuple[Any, ...], Any]:
        eff_fc = self._font_config.copy_with(size=self._font_config.size * self._scale)
        return eff_fc.to_tk_font()

    def _update_entry_font(self) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            entry_font = self._get_effective_tk_font()
            self._entry.configure(font=entry_font)
            self._entry._tkblend_injected_font = entry_font
            if self._custom_font_override:
                self._entry._tkblend_custom_font_override = True
            self._update_entry_geometry()

    @property
    def font(self) -> Any:
        return self._font_config

    @font.setter
    def font(self, val: Any) -> None:
        self._custom_font_override = True
        self._font_config = parse_font(
            font=val,
            default_family=self._font_config.family,
            default_size=self._font_config.size,
        )
        self._update_entry_font()

    @property
    def font_size(self) -> float:
        return self._font_config.size

    @font_size.setter
    def font_size(self, size: float) -> None:
        self._custom_font_override = True
        self._font_config = self._font_config.copy_with(size=size)
        self._update_entry_font()

    @property
    def font_family(self) -> str:
        return self._font_config.family

    @font_family.setter
    def font_family(self, family: str) -> None:
        self._custom_font_override = True
        self._font_config = self._font_config.copy_with(family=family)
        self._update_entry_font()

    @property
    def font_config(self) -> FontConfig:
        return self._font_config

    @font_config.setter
    def font_config(self, fc: FontConfig) -> None:
        self.font = fc

    @property
    def surface(self) -> Any:
        return self._bg_widget.surface

    @property
    def _widget_w(self) -> int:
        return getattr(self._bg_widget, "_widget_w", self.winfo_width())

    @property
    def _widget_h(self) -> int:
        return getattr(self._bg_widget, "_widget_h", self.winfo_height())

    def render(self) -> None:
        self._render_bg()

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)
        font_spec = kwargs.pop("font", None)
        font_size = kwargs.pop("font_size", None)
        font_family = kwargs.pop("font_family", None)
        placeholder = kwargs.pop("placeholder", None)
        bg = kwargs.pop("bg", kwargs.pop("background", None))

        if font_spec is not None or font_size is not None or font_family is not None:
            self._custom_font_override = True
            self._font_config = parse_font(
                font=font_spec if font_spec is not None else self._font_config,
                font_size=font_size,
                font_family=font_family,
                default_family=self._font_config.family,
                default_size=self._font_config.size,
            )
            self._update_entry_font()

        if placeholder is not None:
            self._placeholder = placeholder
            if not self.get() and not self._has_focus:
                self.set("")

        if bg is not None:
            self.set_parent_bg(bg)

        if kwargs:
            return super().configure(**kwargs)
        return None

    config = configure

    def set_parent_bg(self, bg: str, force: bool = False, render: bool = True) -> None:
        """Update parent background and re-render."""
        self._parent_bg = resolve_color_failsafe(bg, master=self, fallback=self._parent_bg)
        if force:
            self._explicit_parent_bg = None
        try:
            self.configure(bg=self._parent_bg)
        except Exception as e:
            logger.debug("Failed configuring Entry background: %s", e)
        if hasattr(self, "_bg_widget") and self._bg_widget is not None:
            self._bg_widget.set_parent_bg(self._parent_bg, force=force, render=render)
        if render:
            self._render_bg()

    def _update_theme_colors(self) -> None:
        if not self.winfo_exists():
            return
        pal = get_theme()
        if self._explicit_parent_bg is None:
            self._parent_bg = Widget._resolve_default_bg(getattr(self, "master", None), pal)
            try:
                super().configure(bg=self._parent_bg)
            except Exception as e:
                logger.debug("Failed updating Entry super bg in _update_theme_colors: %s", e)
        fg_col = pal.text_muted if self._placeholder_active else pal.fg
        self._entry.configure(
            bg=pal.input_bg,
            fg=fg_col,
            insertbackground=pal.input_focus,
        )
        if not self._custom_font_override:
            self._update_entry_font()
        self._render_bg()

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
        if self.get() and abs(event.x - clear_cx) <= 12.0 * s:
            self.set("")
            self._entry.focus_set()
            return
        self._entry.focus_set()

    def get(self) -> str:
        if self._placeholder_active:
            return ""
        return self._entry.get()

    def insert(self, index: Union[int, str], string: str) -> None:
        """Insert text at index, handling placeholder if active."""
        if self._placeholder_active:
            self._entry.delete(0, "end")
            pal = get_theme()
            self._entry.configure(fg=pal.fg)
            self._placeholder_active = False
        self._entry.insert(index, string)
        self._render_bg()

    def delete(self, first: Union[int, str], last: Optional[Union[int, str]] = None) -> None:
        """Delete characters between first and last indices."""
        if self._placeholder_active:
            if not self._has_focus:
                return
            self._entry.delete(0, "end")
            self._placeholder_active = False
        if last is None:
            self._entry.delete(first)
        else:
            self._entry.delete(first, last)
        if not self._entry.get() and not self._has_focus and self._placeholder:
            self._placeholder_active = True
            pal = get_theme()
            self._entry.configure(fg=pal.text_muted)
            self._entry.insert(0, self._placeholder)
        self._render_bg()

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
        if self._bg_widget._widget_w <= 1 or self._bg_widget._widget_h <= 1:
            return
        try:
            from tkblend.surface import parse_color
            self._bg_widget.handle.clear(parse_color(self._parent_bg))
            s = self._scale
            pad = 2.0 * s
            w = max(1.0, self._bg_widget._widget_w - pad * 2.0)
            h = max(1.0, self._bg_widget._widget_h - pad * 2.0)

            state = int(PseudoState.Focused) if self._has_focus else (int(PseudoState.Hover) if getattr(self._bg_widget, "_is_hovered", False) else 0)
            style = StyleEngine.resolve("input", "", state)
            style.border_radius = float(8.0 * s)
            style.border_width = float(1.5 * s if self._has_focus else 1.0 * s)

            self._bg_widget.handle.render_box(
                float(pad), float(pad), float(w), float(h),
                style, "", 0
            )

            pal = get_theme()
            if self.get():
                cx = self._bg_widget._widget_w - 20.0 * s
                cy = self._bg_widget._widget_h / 2.0
                self._bg_widget.handle.fill_circle(cx, cy, 7.0 * s, parse_color(pal.secondary))
                cr = 3.0 * s
                self._bg_widget.handle.draw_line(cx - cr, cy - cr, cx + cr, cy + cr, parse_color(pal.fg), 1.2 * s)
                self._bg_widget.handle.draw_line(cx + cr, cy - cr, cx - cr, cy + cr, parse_color(pal.fg), 1.2 * s)

            self._bg_widget.end_render()
        except Exception as e:
            logger.debug("Render failed in Entry _render_bg: %s", e, exc_info=True)

    def bind(self, sequence=None, func=None, add=None):
        """Bind event to container frame and internal entry widget."""
        super().bind(sequence, func, add=add)
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            return self._entry.bind(sequence, func, add=add)
        return ""

    def focus_set(self) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            self._entry.focus_set()
        else:
            super().focus_set()

    def select_range(self, start: int, end: int) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            self._entry.select_range(start, end)

    def select_clear(self) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            self._entry.select_clear()

    def select_present(self) -> bool:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            return self._entry.select_present()
        return False

    def select_adjust(self, index: int) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            self._entry.select_adjust(index)

    def select_from(self, index: int) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            self._entry.select_from(index)

    def select_to(self, index: int) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            self._entry.select_to(index)

    def icursor(self, index: int) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            self._entry.icursor(index)

    def index(self, index: Any) -> int:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            return self._entry.index(index)
        return 0

    def xview(self, *args) -> Any:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            return self._entry.xview(*args)
        return ()

    def xview_moveto(self, fraction: float) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            self._entry.xview_moveto(fraction)

    def xview_scroll(self, number: int, what: str) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            self._entry.xview_scroll(number, what)

    def render(self) -> None:
        """Render backing vector entry background."""
        self._render_bg()

    def destroy(self) -> None:
        """Cleanly destroy backing widgets and frame."""
        if hasattr(self, "_bg_widget") and self._bg_widget is not None:
            try:
                self._bg_widget.destroy()
            except Exception as e:
                logger.debug("Error destroying _bg_widget in Entry.destroy: %s", e)
            self._bg_widget = None  # type: ignore
        super().destroy()


class Spinbox(Widget):
    """
    Numeric stepper component with decrement (-) and increment (+) vector buttons,
    inline text entry, keyboard navigation (Up/Down arrow keys), auto-repeat on hold,
    and distinct hover/pressed user feedback.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        min_val: int = 0,
        max_val: int = 100,
        from_: Optional[int] = None,
        to: Optional[int] = None,
        value: int = 10,
        step: int = 1,
        on_change: Optional[Callable[[int], None]] = None,
        width: int = 140,
        height: int = 36,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        if from_ is not None:
            min_val = from_
        if to is not None:
            max_val = to
        self._min = min_val
        self._max = max_val
        self._step = step
        self._on_change = on_change
        self._value = max(min_val, min(max_val, int(value)))

        self._hovered_btn: Optional[str] = None
        self._pressed_btn: Optional[str] = None
        self._repeat_timer: Optional[str] = None

        super().__init__(master=master, width=width, height=height, bg=parent_bg, tag_name="input", **kwargs)

        pal = get_theme()
        entry_font = self._get_effective_tk_font()
        self._entry = tk.Entry(
            self,
            bg=pal.input_bg,
            fg=pal.fg,
            insertbackground=pal.input_focus,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            justify="left",
            font=entry_font,
        )
        self._entry._tkblend_injected_font = entry_font
        if getattr(self, "_custom_font_override", False):
            self._entry._tkblend_custom_font_override = True
        self._entry.insert(0, str(self._value))
        self._update_entry_geometry()

        self._entry.bind("<FocusIn>", self._on_entry_focus_in)
        self._entry.bind("<FocusOut>", self._on_entry_focus_out)
        self._entry.bind("<Return>", self._on_entry_commit)
        self._entry.bind("<KP_Enter>", self._on_entry_commit)
        self._entry.bind("<Up>", self._on_entry_up)
        self._entry.bind("<Down>", self._on_entry_down)

        self.bind("<Motion>", self._on_mouse_motion)

    def _get_effective_tk_font(self) -> Union[Tuple[Any, ...], Any]:
        eff_fc = self._font_config.copy_with(size=self._font_config.size * self._scale)
        return eff_fc.to_tk_font()

    def _update_entry_font(self) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            entry_font = self._get_effective_tk_font()
            self._entry.configure(font=entry_font)
            self._entry._tkblend_injected_font = entry_font
            if getattr(self, "_custom_font_override", False):
                self._entry._tkblend_custom_font_override = True
            self._update_entry_geometry()

    def _on_font_changed(self) -> None:
        self._update_entry_font()

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, val: int) -> None:
        self._value = max(self._min, min(self._max, int(val)))
        self._sync_entry()
        self.render()

    def step_by(self, delta: int) -> None:
        new_val = max(self._min, min(self._max, self._value + delta))
        if new_val != self._value:
            self._value = new_val
            self._sync_entry()
            self.render()
            if self._on_change:
                self._on_change(self._value)
        else:
            self.render()

    def _sync_entry(self) -> None:
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            cur = self._entry.get()
            val_str = str(self._value)
            if cur != val_str:
                self._entry.delete(0, "end")
                self._entry.insert(0, val_str)

    def _button_geometry(self) -> Tuple[float, float, float, float, float, float]:
        """Return (minus_x, plus_x, btn_y, btn_w, btn_h, btn_r)."""
        s = self._scale
        btn_w = 26.0 * s
        btn_h = min(26.0 * s, max(10.0, self._widget_h - 10.0 * s))
        btn_gap = 4.0 * s
        right_margin = 6.0 * s

        plus_x = self._widget_w - right_margin - btn_w
        minus_x = plus_x - btn_gap - btn_w
        btn_y = (self._widget_h - btn_h) / 2.0
        btn_r = 5.0 * s
        return minus_x, plus_x, btn_y, btn_w, btn_h, btn_r

    def _update_entry_geometry(self) -> None:
        if not hasattr(self, "_entry") or not self._entry.winfo_exists():
            return
        s = self._scale
        minus_x, _, _, _, _, _ = self._button_geometry()
        entry_x = int(12.0 * s)
        entry_w = max(10, int(minus_x - entry_x - 6.0 * s))
        eff_size = self._font_config.size * s
        entry_h = max(10, min(self._widget_h - 4, int(eff_size * 1.5 + 4)))
        entry_y = max(2, int((self._widget_h - entry_h) / 2.0))
        self._entry.place(x=entry_x, y=entry_y, width=entry_w, height=entry_h)

    def _on_configure(self, event) -> None:
        super()._on_configure(event)
        if hasattr(self, "_entry"):
            self._update_entry_geometry()

    def _on_destroy(self, event=None) -> None:
        self._cancel_repeat()
        super()._on_destroy(event)

    def _on_theme_changed(self, palette: Palette) -> None:
        super()._on_theme_changed(palette)
        if hasattr(self, "_entry") and self._entry.winfo_exists():
            self._entry.configure(
                bg=palette.input_bg,
                fg=palette.fg,
                insertbackground=palette.input_focus,
            )
            if not getattr(self, "_custom_font_override", False):
                self._update_entry_font()

    def _on_entry_focus_in(self, event) -> None:
        self._has_focus = True
        self.render()

    def _on_entry_focus_out(self, event) -> None:
        self._has_focus = False
        self._on_entry_commit()

    def _on_entry_commit(self, event=None) -> None:
        text = self._entry.get().strip()
        try:
            val = int(text)
        except ValueError:
            try:
                val = int(float(text))
            except ValueError:
                val = self._value
        old_val = self._value
        self._value = max(self._min, min(self._max, val))
        self._sync_entry()
        self.render()
        if self._value != old_val and self._on_change:
            self._on_change(self._value)

    def _on_entry_up(self, event) -> str:
        self.step_by(self._step)
        return "break"

    def _on_entry_down(self, event) -> str:
        self.step_by(-self._step)
        return "break"

    def _button_at(self, x: float, y: Optional[float] = None) -> Optional[str]:
        minus_x, plus_x, btn_y, btn_w, btn_h, _ = self._button_geometry()
        check_y = self._widget_h / 2.0 if y is None else y
        if btn_y <= check_y <= btn_y + btn_h:
            if minus_x <= x <= minus_x + btn_w:
                return "minus"
            elif plus_x <= x <= plus_x + btn_w:
                return "plus"
        return None

    def _on_mouse_motion(self, event) -> None:
        btn = self._button_at(event.x, event.y)
        if btn != self._hovered_btn:
            self._hovered_btn = btn
            self.render()

    def _handle_press(self, event) -> None:
        btn = self._button_at(event.x, event.y)
        if btn == "minus":
            if self._value > self._min:
                self._pressed_btn = "minus"
                self.step_by(-self._step)
                self._start_repeat(-self._step)
            else:
                self._pressed_btn = None
        elif btn == "plus":
            if self._value < self._max:
                self._pressed_btn = "plus"
                self.step_by(self._step)
                self._start_repeat(self._step)
            else:
                self._pressed_btn = None
        else:
            self._pressed_btn = None
            self._cancel_repeat()

    def _start_repeat(self, delta: int) -> None:
        self._cancel_repeat()
        self._repeat_timer = self.after(400, lambda: self._do_repeat(delta, interval=80))

    def _do_repeat(self, delta: int, interval: int) -> None:
        if self._pressed_btn:
            self.step_by(delta)
            next_int = max(30, int(interval * 0.9))
            self._repeat_timer = self.after(next_int, lambda: self._do_repeat(delta, next_int))

    def _cancel_repeat(self) -> None:
        if self._repeat_timer is not None:
            try:
                self.after_cancel(self._repeat_timer)
            except Exception:
                pass
            self._repeat_timer = None

    def _handle_release(self, event) -> None:
        self._cancel_repeat()
        self._pressed_btn = None

    def _handle_leave(self, event) -> None:
        self._cancel_repeat()
        self._hovered_btn = None
        self._pressed_btn = None

    def render(self) -> None:
        s = self.begin_render()
        if s <= 0.0:
            return
        try:
            pad = 2.0 * s
            w = max(1.0, self._widget_w - pad * 2.0)
            h = max(1.0, self._widget_h - pad * 2.0)

            state = int(PseudoState.Focused) if self._has_focus else (int(PseudoState.Hover) if self._is_hovered else 0)
            style = StyleEngine.resolve("input", "", state)
            style.border_radius = float(8.0 * s)
            style.border_width = float(1.5 * s if self._has_focus else 1.0 * s)

            self._handle.render_box(
                float(pad), float(pad), float(w), float(h),
                style, "", 0
            )

            pal = get_theme()
            minus_x, plus_x, btn_y, btn_w, btn_h, btn_r = self._button_geometry()
            cy = btn_y + btn_h / 2.0

            # Minus button
            minus_disabled = (self._value <= self._min)
            if minus_disabled:
                minus_bg = pal.input_bg
                minus_fg = pal.text_muted
            elif self._pressed_btn == "minus":
                minus_bg = pal.primary
                minus_fg = pal.primary_fg
            elif self._hovered_btn == "minus":
                minus_bg = pal.secondary_hover
                minus_fg = pal.fg
            else:
                minus_bg = pal.secondary
                minus_fg = pal.fg

            self._surface.fill_rounded_rect(minus_x, btn_y, btn_w, btn_h, btn_r, btn_r, minus_bg)
            draw_vector_minus(self._surface, minus_x + btn_w / 2.0, cy, 4.0 * s, minus_fg, 1.6 * s)

            # Plus button
            plus_disabled = (self._value >= self._max)
            if plus_disabled:
                plus_bg = pal.input_bg
                plus_fg = pal.text_muted
            elif self._pressed_btn == "plus":
                plus_bg = pal.primary
                plus_fg = pal.primary_fg
            elif self._hovered_btn == "plus":
                plus_bg = pal.secondary_hover
                plus_fg = pal.fg
            else:
                plus_bg = pal.secondary
                plus_fg = pal.fg

            self._surface.fill_rounded_rect(plus_x, btn_y, btn_w, btn_h, btn_r, btn_r, plus_bg)
            draw_vector_plus(self._surface, plus_x + btn_w / 2.0, cy, 4.0 * s, plus_fg, 1.6 * s)

            self.end_render()
        except Exception as e:
            logger.debug("Render failed in SpinBox: %s", e, exc_info=True)

    def destroy(self) -> None:
        self._cancel_repeat()
        super().destroy()


TextInput = Entry
SpinBox = Spinbox
