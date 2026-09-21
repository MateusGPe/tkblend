"""
Dialog and modal overlay widgets for tkblend: ModernModal and ModernDialog.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, List, Tuple, Any

from tkblend.surface import Surface, ColorLike
from tkblend.widgets.theme import Theme, ThemeManager
from tkblend.widgets.controls import ModernButton
from tkblend.widgets.containers import ModernCard


class ModernDialog(tk.Toplevel):
    """
    Modern modal dialog with elevated card, antialiased typography, and action buttons.
    """

    def __init__(
        self,
        parent: tk.Misc,
        title: str = "Dialog",
        message: str = "This is a modern dialog message.",
        confirm_text: str = "OK",
        cancel_text: Optional[str] = "Cancel",
        on_confirm: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
        variant: str = "primary",  # "primary", "danger", "success"
        width: int = 380,
        height: int = 210,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._theme = t
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        self.result: Optional[bool] = None

        super().__init__(parent, **kwargs)
        self.title(title)
        self.resizable(False, False)
        self.configure(background=t.bg_window)

        # Center on parent
        self.geometry(f"{width}x{height}")
        self.transient(parent)
        self.grab_set()

        card = ModernCard(
            self,
            title=title,
            width=width - 20,
            height=height - 20,
            theme=t,
        )
        card.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Message text label
        msg_lbl = tk.Label(
            card,
            text=message,
            font=(t.font_family, int(t.font_size_sm)),
            fg=t.text,
            bg=t.bg_card,
            wraplength=width - 60,
            justify="left",
            anchor="w",
        )
        msg_lbl.place(x=20, y=55, width=width - 60)

        # Action Buttons frame
        btn_frame = tk.Frame(card, bg=t.bg_card)
        btn_frame.place(x=20, y=height - 85, width=width - 60, height=45)

        if cancel_text:
            btn_cancel = ModernButton(
                btn_frame,
                text=cancel_text,
                variant="secondary",
                width=100,
                height=36,
                command=self._handle_cancel,
                theme=t,
            )
            btn_cancel.pack(side=tk.RIGHT, padx=4)

        btn_ok = ModernButton(
            btn_frame,
            text=confirm_text,
            variant=variant,
            width=100,
            height=36,
            command=self._handle_confirm,
            theme=t,
        )
        btn_ok.pack(side=tk.RIGHT, padx=4)

        self.protocol("WM_DELETE_WINDOW", self._handle_cancel)

    def _handle_confirm(self) -> None:
        self.result = True
        if self._on_confirm:
            self._on_confirm()
        self.destroy()

    def _handle_cancel(self) -> None:
        self.result = False
        if self._on_cancel:
            self._on_cancel()
        self.destroy()


def show_alert(
    parent: tk.Misc,
    title: str,
    message: str,
    variant: str = "primary",
    theme: Optional[Theme] = None,
    wait: bool = True,
) -> ModernDialog:
    """Helper to show a simple modal alert."""
    dlg = ModernDialog(
        parent=parent,
        title=title,
        message=message,
        confirm_text="OK",
        cancel_text=None,
        variant=variant,
        theme=theme,
    )
    if wait:
        parent.wait_window(dlg)
    return dlg
