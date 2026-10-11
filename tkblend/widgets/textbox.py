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
        **kwargs,
    ):
        self._placeholder = placeholder

        super().__init__(
            master=master,
            widget_class="entry",
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
            font=("sans-serif", 11),
        )
        self._entry.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=1.0, x=12, width=-24)

        if text:
            self._entry.insert(0, str(text))

        self._entry.bind("<FocusIn>", self._on_entry_focus_in, add="+")
        self._entry.bind("<FocusOut>", self._on_entry_focus_out, add="+")

    def _on_entry_focus_in(self, event: Optional[tk.Event] = None) -> None:
        self._controller.set_focused(True)
        self.request_redraw()

    def _on_entry_focus_out(self, event: Optional[tk.Event] = None) -> None:
        self._controller.set_focused(False)
        self.request_redraw()

    @property
    def text(self) -> str:
        return self._entry.get()

    @text.setter
    def text(self, val: str) -> None:
        self._entry.delete(0, "end")
        self._entry.insert(0, str(val))

    def get(self) -> str:
        return self._entry.get()

    def insert(self, index: Any, string: str) -> None:
        self._entry.insert(index, string)

    def delete(self, first: Any, last: Any = None) -> None:
        self._entry.delete(first, last)

    @property
    def entry(self) -> tk.Entry:
        return self._entry

    def on_theme_update(self, pal: Palette) -> None:
        super().on_theme_update(pal)
        bg_hex = to_tk_hex(pal.input_bg)
        fg_hex = to_tk_hex(pal.fg)
        try:
            self._entry.configure(
                background=bg_hex,
                foreground=fg_hex,
                insertbackground=fg_hex,
            )
        except Exception:
            pass


class SearchEntry(Entry):
    """
    Material Design 3 Search input pre-configured with search placeholder.
    """

    def __init__(self, master: Optional[tk.Misc] = None, placeholder: str = "Search...", **kwargs):
        super().__init__(master=master, placeholder=placeholder, **kwargs)


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
        **kwargs,
    ):
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
            font=("sans-serif", 10),
            wrap="word",
        )
        self._text.place(relx=0.0, rely=0.0, relwidth=1.0, relheight=1.0, x=10, y=8, width=-20, height=-16)

        self._text.bind("<FocusIn>", lambda e: (self._controller.set_focused(True), self.request_redraw()), add="+")
        self._text.bind("<FocusOut>", lambda e: (self._controller.set_focused(False), self.request_redraw()), add="+")

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
