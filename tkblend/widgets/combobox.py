from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Sequence, Any
from tkblend.widgets.base import BaseControl
from tkblend.theme import Palette, to_tk_hex, get_theme


class _DropdownPopup(tk.Toplevel):
    """Floating Material Design 3 vector styled dropdown list."""

    def __init__(
        self,
        master_control: ComboBox,
        values: Sequence[str],
        current_value: str,
        on_select: Callable[[str], None],
    ):
        super().__init__(master_control)
        self._master_ctrl = master_control
        self._on_select = on_select
        self._values = list(values)
        self._current_value = current_value

        self.overrideredirect(True)
        self.attributes("-topmost", True)

        pal = master_control._palette
        bg_hex = to_tk_hex(pal.card_bg)
        border_hex = to_tk_hex(pal.card_border)
        fg_hex = to_tk_hex(pal.fg)
        primary_hex = to_tk_hex(pal.primary)
        hover_hex = to_tk_hex(pal.surface)

        self.configure(bg=border_hex, padx=1, pady=1)

        container = tk.Frame(self, bg=bg_hex)
        container.pack(fill="both", expand=True)

        for val in self._values:
            is_active = (val == current_value)
            item_fg = primary_hex if is_active else fg_hex
            item_font = ("sans-serif", 10, "bold" if is_active else "normal")
            lbl = tk.Label(
                container,
                text=str(val),
                bg=bg_hex,
                fg=item_fg,
                font=item_font,
                anchor="w",
                padx=12,
                pady=6,
                cursor="hand2",
            )
            lbl.pack(fill="x")

            def _make_callbacks(v: str, label_widget: tk.Label):
                def _on_enter(e):
                    label_widget.configure(bg=hover_hex)
                def _on_leave(e):
                    label_widget.configure(bg=bg_hex)
                def _on_click(e):
                    self.dismiss()
                    self._on_select(v)
                label_widget.bind("<Enter>", _on_enter)
                label_widget.bind("<Leave>", _on_leave)
                label_widget.bind("<Button-1>", _on_click)

            _make_callbacks(val, lbl)

        # Position below the master control
        self.update_idletasks()
        rx = master_control.winfo_rootx()
        ry = master_control.winfo_rooty() + master_control.winfo_height() + 2
        rw = max(master_control.winfo_width(), self.winfo_reqwidth())
        rh = self.winfo_reqheight()
        self.geometry(f"{rw}x{rh}+{rx}+{ry}")

        # Auto-dismiss on click outside or escape
        self.bind("<Escape>", lambda e: self.dismiss())
        self.bind("<FocusOut>", lambda e: self.dismiss())
        self.focus_set()

    def dismiss(self) -> None:
        try:
            self.destroy()
        except Exception:
            pass


class ComboBox(BaseControl):
    """
    High-performance Material Design 3 vector dropdown combo selector.
    """

    WIDGET_CLASS = "combobox"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        values: Optional[Sequence[str]] = None,
        value: str = "",
        command: Optional[Callable[[str], Any]] = None,
        variable: Optional[tk.Variable] = None,
        width: int = 160,
        height: int = 38,
        **kwargs,
    ):
        self._values = list(values) if values else []
        self._variable = variable
        self._command = command
        self._popup: Optional[_DropdownPopup] = None

        super().__init__(
            master=master,
            widget_class="combobox",
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )

        init_val = str(value)
        if not init_val and self._values:
            init_val = self._values[0]
        if self._variable is not None:
            try:
                cur_v = str(self._variable.get() or "")
                if cur_v:
                    init_val = cur_v
            except Exception:
                pass

        self.set(init_val)

    @property
    def values(self) -> list[str]:
        return list(self._values)

    @values.setter
    def values(self, vals: Sequence[str]) -> None:
        self._values = list(vals) if vals else []
        if self.get() not in self._values and self._values:
            self.set(self._values[0])

    @property
    def value(self) -> str:
        return self.get()

    @value.setter
    def value(self, val: str) -> None:
        self.set(val)

    def get(self) -> str:
        return self.get_var("--text") or ""

    def set(self, val: str) -> None:
        val_str = str(val or "")
        self.set_var("--text", val_str)
        if self._variable is not None:
            try:
                self._variable.set(val_str)
            except Exception:
                pass
        self.request_redraw()

    def on_click(self, x: int, y: int, button: int) -> None:
        if self.is_disabled:
            return
        if self._popup is not None:
            self._popup.dismiss()
            self._popup = None
            return

        def _on_select(chosen: str):
            self.set(chosen)
            self._popup = None
            if callable(self._command):
                try:
                    self._command(chosen)
                except Exception:
                    pass

        self._popup = _DropdownPopup(
            master_control=self,
            values=self._values,
            current_value=self.get(),
            on_select=_on_select,
        )


OptionMenu = ComboBox
