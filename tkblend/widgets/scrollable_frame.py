from __future__ import annotations

import sys
import tkinter as tk
from typing import Optional, Callable, Any
from tkblend.widgets.base import BaseControl
from tkblend.theme import Palette, to_tk_hex, cascade_bg_to_children
from tkblend.surface import ColorLike


class VectorScrollbar(BaseControl):
    """
    High-performance Material Design 3 vector scrollbar with capsule thumb.
    """

    WIDGET_CLASS = "scrollbar"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        orientation: str = "vertical",
        command: Optional[Callable[..., Any]] = None,
        width: int = 8,
        height: int = 120,
        **kwargs,
    ):
        self._orientation = orientation
        self._command = command

        super().__init__(
            master=master,
            widget_class="scrollbar",
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )

        self.set_var("--thumb-pos", "0.0")
        self.set_var("--thumb-size", "0.3")

    def set(self, first: float, last: float) -> None:
        try:
            f = float(first)
            l = float(last)
        except Exception:
            return
        size = max(0.05, min(1.0, l - f))
        pos = max(0.0, min(1.0 - size, f))
        self.set_var("--thumb-pos", str(pos))
        self.set_var("--thumb-size", str(size))
        self.request_redraw()

    def on_change(self, val: Any) -> None:
        try:
            pos = float(val)
        except Exception:
            pos = 0.0
        if callable(self._command):
            try:
                self._command("moveto", pos)
            except Exception:
                pass


class ScrollableFrame(BaseControl):
    """
    High-performance Material Design 3 scrollable container with integrated vector scrollbar.
    """

    WIDGET_CLASS = "frame"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 300,
        height: int = 300,
        corner_radius: float = 12.0,
        inner_bg: Optional[ColorLike] = None,
        outer_bg: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        scrollbar_width: int = 8,
        **kwargs,
    ):
        super().__init__(
            master=master,
            widget_class="frame",
            width=width,
            height=height,
            inner_bg=inner_bg or bg_color,
            outer_bg=outer_bg or parent_bg,
            takefocus=False,
            **kwargs,
        )

        pal = self._palette
        bg_hex = to_tk_hex(self.inner_bg)

        # Canvas viewport
        self._canvas = tk.Canvas(
            self,
            background=bg_hex,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
        )
        self._canvas.place(x=0, y=0, relwidth=1.0, relheight=1.0, width=-scrollbar_width)

        # Inner scrollable content frame
        self._content = tk.Frame(self._canvas, background=bg_hex)
        self._content_window = self._canvas.create_window((0, 0), window=self._content, anchor="nw")

        # Vector Scrollbar
        self._scrollbar = VectorScrollbar(
            self,
            orientation="vertical",
            command=self._canvas.yview,
            width=scrollbar_width,
            height=height,
        )
        self._scrollbar.place(relx=1.0, rely=0.0, relheight=1.0, x=-scrollbar_width, width=scrollbar_width)

        self._canvas.configure(xscrollcommand=None, yscrollcommand=self._scrollbar.set)

        # Events
        self._content.bind("<Configure>", self._on_content_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-4>", self._on_mousewheel)
        self.bind("<Button-5>", self._on_mousewheel)

    @property
    def content(self) -> tk.Frame:
        """Inner frame where children should be added."""
        return self._content

    def _on_content_configure(self, event: Optional[tk.Event] = None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        # Match content width to canvas width
        self._canvas.itemconfig(self._content_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        if sys.platform == "darwin":
            delta = -1 * event.delta
        elif event.num == 5:
            delta = 1
        elif event.num == 4:
            delta = -1
        else:
            delta = -1 * int(event.delta / 120)
        self._canvas.yview_scroll(delta, "units")

    def on_theme_update(self, pal: Palette) -> None:
        super().on_theme_update(pal)
        bg_hex = to_tk_hex(self.inner_bg)
        try:
            self._canvas.configure(background=bg_hex)
            self._content.configure(background=bg_hex)
        except Exception:
            pass
        cascade_bg_to_children(self._content, self.inner_bg, palette=pal)
