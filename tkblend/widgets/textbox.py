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
        width: int = 180,
        height: int = 38,
        corner_radius: float = 8.0,
        border_width: float = 1.0,
        font: Any = ("sans-serif", 11),
        widget_class: Optional[str] = None,
        **kwargs,
    ):
        self._placeholder = str(placeholder or "")
        self._is_showing_placeholder = False
        self._corner_radius = float(corner_radius)
        self._border_width = float(border_width)
        self._font_spec = font
        effective_cls = widget_class or self.WIDGET_CLASS

        super().__init__(
            master=master,
            widget_class=effective_cls,
            width=width,
            height=height,
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
            font=self._font_spec,
        )

        self._apply_layout()

        if text:
            self._entry.insert(0, str(text))
        elif self._placeholder:
            self._show_placeholder()

        self._entry.bind("<FocusIn>", self._on_entry_focus_in, add="+")
        self._entry.bind("<FocusOut>", self._on_entry_focus_out, add="+")
        self.bind("<Button-1>", self._on_container_click, add="+")

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

    def set(self, val: str) -> None:
        """Set the text value of the entry."""
        self.text = val

    def get(self) -> str:
        return "" if self._is_showing_placeholder else self._entry.get()

    def insert(self, index: Any, string: str) -> None:
        self._hide_placeholder()
        self._entry.insert(index, string)

    def delete(self, first: Any, last: Any = None) -> None:
        self._entry.delete(first, last)
        if not self._entry.get() and not self._controller.is_focused:
            self._show_placeholder()

    @property
    def entry(self) -> tk.Entry:
        return self._entry

    @property
    def entry_widget(self) -> tk.Entry:
        return self._entry

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
        width: int = 280,
        height: int = 140,
        corner_radius: float = 8.0,
        border_width: float = 1.0,
        font: Any = ("sans-serif", 10),
        **kwargs,
    ):
        self._corner_radius = float(corner_radius)
        self._border_width = float(border_width)
        self._font_spec = font

        super().__init__(
            master=master,
            widget_class="textbox_frame",
            width=width,
            height=height,
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
            font=self._font_spec,
            wrap="word",
            padx=4,
            pady=3,
        )
        self._apply_layout()

        self._text.bind("<FocusIn>", self._on_text_focus_in, add="+")
        self._text.bind("<FocusOut>", self._on_text_focus_out, add="+")
        self.bind("<Button-1>", self._on_container_click, add="+")

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
