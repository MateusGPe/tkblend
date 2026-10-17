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
        self._visible_span = 0.3

        super().__init__(
            master=master,
            widget_class="scrollbar",
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )

        self.set_var("--orientation", str(orientation))
        self.set_var("--thumb-pos", "0.0")
        self.set_var("--thumb-progress", "0.0")
        self.set_var("--thumb-size", "0.3")

    def set(self, first: float, last: float) -> None:
        try:
            f = float(first)
            l = float(last)
        except Exception:
            return
        span = max(0.0001, min(1.0, l - f))
        self._visible_span = span
        if span >= 0.999:
            self.set_var("--thumb-hidden", "1")
            self.set_var("--thumb-pos", "0.0")
            self.set_var("--thumb-progress", "0.0")
            self.set_var("--thumb-size", "1.0")
        else:
            self.remove_var("--thumb-hidden")
            max_first = max(0.0001, 1.0 - span)
            progress = max(0.0, min(1.0, f / max_first))
            self.set_var("--thumb-pos", str(progress))
            self.set_var("--thumb-progress", str(progress))
            self.set_var("--thumb-size", str(span))
        self.request_redraw()

    def get(self) -> tuple[float, float]:
        try:
            progress = float(self.get_var("--thumb-pos", "0.0"))
            max_first = max(0.0001, 1.0 - self._visible_span)
            f = progress * max_first
            return f, min(1.0, f + self._visible_span)
        except Exception:
            return 0.0, 1.0

    def on_change(self, val: Any) -> None:
        try:
            progress = float(val)
        except Exception:
            progress = 0.0
        max_first = max(0.0, 1.0 - self._visible_span)
        target_f = progress * max_first
        if callable(self._command):
            try:
                self._command("moveto", target_f)
            except Exception:
                pass


class ScrollableFrame(BaseControl):
    """
    High-performance Material Design 3 scrollable container with integrated vector scrollbar
    and smooth animated mouse-wheel interpolation.
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

        self._scrollbar_width = int(scrollbar_width)
        self._target_y = 0.0
        self._anim_timer: Optional[str] = None
        self._is_hovered_for_scroll = False

        # Canvas viewport
        self._canvas = tk.Canvas(
            self,
            background=bg_hex,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
        )
        self._canvas.place(x=0, y=0, relwidth=1.0, relheight=1.0, width=-self._scrollbar_width)

        # Inner scrollable content frame
        self._content = tk.Frame(self._canvas, background=bg_hex)
        self._content_window = self._canvas.create_window((0, 0), window=self._content, anchor="nw")

        # Vector Scrollbar
        self._scrollbar = VectorScrollbar(
            self,
            orientation="vertical",
            command=self._on_scrollbar_move,
            width=self._scrollbar_width,
            height=height,
        )
        self._scrollbar.place(relx=1.0, rely=0.0, relheight=1.0, x=-self._scrollbar_width, width=self._scrollbar_width)

        self._canvas.configure(xscrollcommand=None, yscrollcommand=self._scrollbar.set)

        # Content configure event
        self._content.bind("<Configure>", self._on_content_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Enter / Leave bindings for responsive mouse wheel routing
        self.bind("<Enter>", self._on_mouse_enter, add="+")
        self.bind("<Leave>", self._on_mouse_leave, add="+")
        self._canvas.bind("<Enter>", self._on_mouse_enter, add="+")
        self._canvas.bind("<Leave>", self._on_mouse_leave, add="+")
        self._content.bind("<Enter>", self._on_mouse_enter, add="+")
        self._content.bind("<Leave>", self._on_mouse_leave, add="+")

    @property
    def content(self) -> tk.Frame:
        """Inner frame where children should be added."""
        return self._content

    @property
    def scrollbar(self) -> VectorScrollbar:
        return self._scrollbar

    def _on_content_configure(self, event: Optional[tk.Event] = None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        # Match content width to canvas width
        self._canvas.itemconfig(self._content_window, width=event.width)

    def _on_scrollbar_move(self, *args) -> None:
        if self._anim_timer is not None:
            try:
                self.after_cancel(self._anim_timer)
            except Exception:
                pass
            self._anim_timer = None
        self._canvas.yview(*args)
        view = self._canvas.yview()
        if view:
            self._target_y = view[0]

    def _on_mouse_enter(self, event: Optional[tk.Event] = None) -> None:
        self._is_hovered_for_scroll = True
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_mousewheel, add="+")
        self.bind_all("<Button-5>", self._on_mousewheel, add="+")

    def _on_mouse_leave(self, event: Optional[tk.Event] = None) -> None:
        try:
            x, y = self.winfo_pointerxy()
            rx = self.winfo_rootx()
            ry = self.winfo_rooty()
            rw = self.winfo_width()
            rh = self.winfo_height()
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                return  # Still inside container bounds
        except Exception:
            pass
        self._is_hovered_for_scroll = False
        try:
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")
        except Exception:
            pass

    def _on_mousewheel(self, event: tk.Event) -> None:
        if not self._is_hovered_for_scroll:
            return
        if sys.platform == "darwin":
            raw_delta = getattr(event, "delta", 0)
            if raw_delta != 0:
                delta = -1 * raw_delta
            elif getattr(event, "num", None) == 5:
                delta = 1
            elif getattr(event, "num", None) == 4:
                delta = -1
            else:
                delta = 0
        elif getattr(event, "num", None) == 5:
            delta = 1
        elif getattr(event, "num", None) == 4:
            delta = -1
        else:
            delta = -1 * int(getattr(event, "delta", 0) / 120) if getattr(event, "delta", 0) else 1

        view = self._canvas.yview()
        if not view:
            return
        first, last = view
        visible_span = max(0.001, last - first)
        if visible_span >= 0.999:
            return

        max_pos = max(0.0, 1.0 - visible_span)
        bbox = self._canvas.bbox("all")
        total_h = max(1, bbox[3] - bbox[1]) if bbox else self.winfo_height()
        step_px = 40.0
        step_frac = (step_px / total_h) * delta

        if self._anim_timer is None:
            self._target_y = first

        self._target_y = max(0.0, min(max_pos, self._target_y + step_frac))

        if self._anim_timer is None:
            self._step_smooth_scroll()

    def _step_smooth_scroll(self) -> None:
        view = self._canvas.yview()
        if not view:
            self._anim_timer = None
            return
        curr_y = view[0]
        diff = self._target_y - curr_y

        if abs(diff) < 0.001:
            self._canvas.yview_moveto(self._target_y)
            self._anim_timer = None
        else:
            new_y = curr_y + diff * 0.35
            self._canvas.yview_moveto(new_y)
            self._anim_timer = self.after(16, self._step_smooth_scroll)

    def on_theme_update(self, pal: Palette) -> None:
        super().on_theme_update(pal)
        bg_hex = to_tk_hex(self.inner_bg)
        try:
            self._canvas.configure(background=bg_hex)
            self._content.configure(background=bg_hex)
        except Exception:
            pass
        cascade_bg_to_children(self._content, self.inner_bg, palette=pal)

    def destroy(self) -> None:
        if self._anim_timer is not None:
            try:
                self.after_cancel(self._anim_timer)
            except Exception:
                pass
            self._anim_timer = None
        try:
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")
        except Exception:
            pass
        super().destroy()
