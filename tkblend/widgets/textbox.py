from __future__ import annotations

import tkinter as tk
from typing import Optional, Any
from tkblend.widgets.base import BaseControl
from tkblend.theme import Palette, to_tk_hex, get_theme


class Entry(BaseControl):
    """
    High-performance Material Design 3 vector text entry.
    """

    WIDGET_CLASS = "entry"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        placeholder: str = "",
        text: str = "",
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        auto_fit: bool = False,
        corner_radius: float = 8.0,
        border_width: float = 1.0,
        font: Any = ("sans-serif", 11),
        state: str = "normal",
        variable: Optional[tk.Variable] = None,
        textvariable: Optional[tk.Variable] = None,
        widget_class: Optional[str] = None,
        **kwargs,
    ):
        self._placeholder = str(placeholder or "")
        self._init_text = str(text or "")
        self._is_showing_placeholder = False
        self._corner_radius = float(corner_radius)
        self._border_width = float(border_width)
        effective_cls = widget_class or self.WIDGET_CLASS
        eff_var = variable if variable is not None else textvariable

        super().__init__(
            master=master,
            widget_class=effective_cls,
            width=width,
            height=height,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            auto_fit=auto_fit,
            font=font,
            state=state,
            corner_radius=corner_radius,
            variable=eff_var,
            cursor="xterm",
            **kwargs,
        )

        pal = self._palette
        bg_hex = to_tk_hex(pal.input_bg)
        fg_hex = to_tk_hex(pal.fg)

        self._entry = tk.Entry(
            self,
            background=bg_hex,
            foreground=fg_hex,
            insertbackground=fg_hex,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=self._font_config.to_tk_font(self),
        )

        self._apply_layout()

        init_text = self._init_text
        if eff_var is not None:
            try:
                var_val = str(eff_var.get() or "")
                if var_val:
                    init_text = var_val
            except Exception:
                pass

        if init_text:
            self._entry.insert(0, init_text)
        elif self._placeholder:
            self._show_placeholder()

        self._init_variable(self._variable, self._on_var_changed)

        self._entry.bind("<FocusIn>", self._on_entry_focus_in, add="+")
        self._entry.bind("<FocusOut>", self._on_entry_focus_out, add="+")
        self._entry.bind("<KeyRelease>", self._on_entry_key_release, add="+")
        self.bind("<Button-1>", self._on_container_click, add="+")

        if self.is_disabled:
            try:
                self._entry.configure(state="disabled")
            except Exception:
                pass

    def _get_content_size(self) -> tuple[Optional[int], Optional[int]]:
        from tkblend.widgets.utils import measure_text_dimensions

        entry_obj = getattr(self, "_entry", None)
        sample = (entry_obj.get() if entry_obj is not None else getattr(self, "_init_text", "")) or getattr(self, "_placeholder", "")
        if getattr(self, "auto_fit", False) and sample:
            tw, th = measure_text_dimensions(sample, font=getattr(self, "font", None))
            pad_left, pad_right = self._calc_padding() if hasattr(self, "_calc_padding") else (16, 16)
            return max(180, tw + pad_left + pad_right + 12), max(38, th + 18)
        return 180, 38

    def _on_var_changed(self, var_val: Any) -> None:
        val_str = str(var_val or "")
        if self.text != val_str:
            self.text = val_str

    def _on_entry_key_release(self, event: Optional[tk.Event] = None) -> None:
        self._sync_variable_out(self.text)
        if self.auto_fit:
            self._recalculate_natural_size()

    def _calc_padding(self) -> tuple[int, int]:
        """Compute horizontal insets dynamically based on corner radius, border width, and scale factor."""
        scale = self._scale_factor
        margin_x = int(self._palette.get_scalar("input_pad_x", 3.0) * scale)
        pad_x = margin_x + max(int(self._corner_radius * scale + 6), int(self._border_width * scale + 10))
        return pad_x, pad_x

    def _apply_layout(self) -> None:
        pad_left, pad_right = self._calc_padding()
        scale = self._scale_factor
        pad_top = self._palette.get_scalar("input_pad_top", 2.0)
        pad_bottom = self._palette.get_scalar("input_pad_bottom", 4.0)
        y_offset = -int(((pad_bottom - pad_top) / 2.0) * scale)
        self._entry.place(
            x=pad_left,
            rely=0.5,
            y=y_offset,
            anchor="w",
            relwidth=1.0,
            width=-(pad_left + pad_right),
        )

    def _on_container_click(self, event: Optional[tk.Event] = None) -> None:
        if not self.is_disabled:
            self._entry.focus_set()

    def _show_placeholder(self) -> None:
        if self._placeholder and not self._entry.get() and not self._controller.is_focused:
            self._is_showing_placeholder = True
            self._entry.delete(0, "end")
            self._entry.insert(0, self._placeholder)
            pal = self._palette
            muted_hex = to_tk_hex(getattr(pal, "text_muted", "#71717a"))
            self._entry.configure(foreground=muted_hex)

    def _hide_placeholder(self) -> None:
        if self._is_showing_placeholder:
            self._is_showing_placeholder = False
            self._entry.delete(0, "end")
            pal = self._palette
            self._entry.configure(foreground=to_tk_hex(pal.fg))

    def _on_entry_focus_in(self, event: Optional[tk.Event] = None) -> None:
        self._controller.is_focused = True
        self._hide_placeholder()
        self.request_redraw()

    def _on_entry_focus_out(self, event: Optional[tk.Event] = None) -> None:
        self._controller.is_focused = False
        if not self._entry.get():
            self._show_placeholder()
        self.request_redraw()

    @property
    def placeholder(self) -> str:
        return self._placeholder

    @placeholder.setter
    def placeholder(self, val: str) -> None:
        was_showing = self._is_showing_placeholder
        self._placeholder = str(val or "")
        if was_showing or not self._entry.get():
            self._hide_placeholder()
            self._show_placeholder()
        if self.auto_fit:
            self._recalculate_natural_size()

    @property
    def text(self) -> str:
        return "" if self._is_showing_placeholder else self._entry.get()

    @text.setter
    def text(self, val: str) -> None:
        self._hide_placeholder()
        self._entry.delete(0, "end")
        if val:
            self._entry.configure(foreground=to_tk_hex(self._palette.fg))
            self._entry.insert(0, str(val))
        else:
            self._show_placeholder()
        self._sync_variable_out(str(val or ""))
        if self.auto_fit:
            self._recalculate_natural_size()

    def set(self, val: str) -> None:
        """Set the text value of the entry."""
        self.text = val

    def get(self) -> str:
        return "" if self._is_showing_placeholder else self._entry.get()

    def insert(self, index: Any, string: str) -> None:
        self._hide_placeholder()
        self._entry.insert(index, string)
        self._sync_variable_out(self.text)
        if self.auto_fit:
            self._recalculate_natural_size()

    def delete(self, first: Any, last: Any = None) -> None:
        self._entry.delete(first, last)
        if not self._entry.get() and not self._controller.is_focused:
            self._show_placeholder()
        self._sync_variable_out(self.text)
        if self.auto_fit:
            self._recalculate_natural_size()

    @property
    def entry(self) -> tk.Entry:
        return self._entry

    @property
    def entry_widget(self) -> tk.Entry:
        return self._entry

    def configure(self, **kwargs) -> Any:
        super().configure(**kwargs)
        if "state" in kwargs:
            try:
                tk_st = "disabled" if self.is_disabled else "normal"
                self._entry.configure(state=tk_st)
            except Exception:
                pass
        if "font" in kwargs:
            try:
                self._entry.configure(font=self._font_config.to_tk_font(self))
            except Exception:
                pass

    def on_theme_update(self, pal: Palette) -> None:
        super().on_theme_update(pal)
        self._apply_layout()
        bg_hex = to_tk_hex(pal.input_bg)
        fg_hex = to_tk_hex(getattr(pal, "text_muted", "#71717a") if self._is_showing_placeholder else pal.fg)
        try:
            self._entry.configure(
                background=bg_hex,
                foreground=fg_hex,
                insertbackground=to_tk_hex(pal.fg),
            )
        except Exception:
            pass


class SearchEntry(Entry):
    """
    Material Design 3 Search input with integrated vector magnifying glass icon and placeholder.
    """

    WIDGET_CLASS = "search_entry"

    def __init__(self, master: Optional[tk.Misc] = None, placeholder: str = "Search...", **kwargs):
        super().__init__(master=master, placeholder=placeholder, widget_class="search_entry", **kwargs)

    def _calc_padding(self) -> tuple[int, int]:
        """Account for the vector search icon on the left while computing insets."""
        scale = self._scale_factor
        margin_x = int(self._palette.get_scalar("input_pad_x", 3.0) * scale)
        pad_right = margin_x + max(int(self._corner_radius * scale + 6), int(self._border_width * scale + 10))
        # Icon center is at margin_x + 14px, diameter ~9px; inset text comfortably past the icon
        pad_left = margin_x + max(int(self._corner_radius * scale + 28), int(36 * scale))
        return pad_left, pad_right


class TextBox(BaseControl):
    """
    High-performance Material Design 3 multiline text editor.
    """

    WIDGET_CLASS = "textbox_frame"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        corner_radius: float = 8.0,
        border_width: float = 1.0,
        font: Any = ("sans-serif", 10),
        state: str = "normal",
        **kwargs,
    ):
        self._corner_radius = float(corner_radius)
        self._border_width = float(border_width)

        super().__init__(
            master=master,
            widget_class="textbox_frame",
            width=width,
            height=height,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            font=font,
            state=state,
            corner_radius=corner_radius,
            cursor="xterm",
            **kwargs,
        )

        pal = self._palette
        bg_hex = to_tk_hex(pal.input_bg)
        fg_hex = to_tk_hex(pal.fg)

        self._text = tk.Text(
            self,
            background=bg_hex,
            foreground=fg_hex,
            insertbackground=fg_hex,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=self._font_config.to_tk_font(self),
            wrap="word",
            padx=4,
            pady=3,
        )
        self._apply_layout()

        self._text.bind("<FocusIn>", self._on_text_focus_in, add="+")
        self._text.bind("<FocusOut>", self._on_text_focus_out, add="+")
        self.bind("<Button-1>", self._on_container_click, add="+")

        if self.is_disabled:
            try:
                self._text.configure(state="disabled")
            except Exception:
                pass

    def _get_content_size(self) -> tuple[Optional[int], Optional[int]]:
        return 280, 140

    def _apply_layout(self) -> None:
        scale = self._scale_factor
        margin_x = int(self._palette.get_scalar("input_pad_x", 3.0) * scale)
        margin_top = int(self._palette.get_scalar("input_pad_top", 2.0) * scale)
        margin_bottom = int(self._palette.get_scalar("input_pad_bottom", 4.0) * scale)
        pad_x = margin_x + max(int(self._corner_radius * scale + 4), int(self._border_width * scale + 8))
        pad_top = margin_top + max(int(self._corner_radius * scale + 2), int(self._border_width * scale + 6))
        pad_bottom = margin_bottom + max(int(self._corner_radius * scale + 2), int(self._border_width * scale + 6))

        self._text.place(
            x=pad_x,
            y=pad_top,
            relwidth=1.0,
            relheight=1.0,
            width=-(pad_x * 2),
            height=-(pad_top + pad_bottom),
        )

    def _on_container_click(self, event: Optional[tk.Event] = None) -> None:
        if not self.is_disabled:
            self._text.focus_set()

    def _on_text_focus_in(self, event: Optional[tk.Event] = None) -> None:
        self._controller.is_focused = True
        self.request_redraw()

    def _on_text_focus_out(self, event: Optional[tk.Event] = None) -> None:
        self._controller.is_focused = False
        self.request_redraw()

    @property
    def text_widget(self) -> tk.Text:
        return self._text

    def get(self, index1: str = "1.0", index2: str = "end-1c") -> str:
        return self._text.get(index1, index2)

    def insert(self, index: str, chars: str, *args) -> None:
        self._text.insert(index, chars, *args)

    def delete(self, index1: str, index2: Optional[str] = None) -> None:
        self._text.delete(index1, index2)

    def configure(self, **kwargs) -> Any:
        super().configure(**kwargs)
        if "state" in kwargs:
            try:
                tk_st = "disabled" if self.is_disabled else "normal"
                self._text.configure(state=tk_st)
            except Exception:
                pass
        if "font" in kwargs:
            try:
                self._text.configure(font=self._font_config.to_tk_font(self))
            except Exception:
                pass

    def on_theme_update(self, pal: Palette) -> None:
        super().on_theme_update(pal)
        self._apply_layout()
        bg_hex = to_tk_hex(pal.input_bg)
        fg_hex = to_tk_hex(pal.fg)
        try:
            self._text.configure(
                background=bg_hex,
                foreground=fg_hex,
                insertbackground=fg_hex,
            )
        except Exception:
            pass

