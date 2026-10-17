from __future__ import annotations

import time
import tkinter as tk
from typing import Optional, Callable, Sequence, Any

from tkblend.surface import ColorLike
from tkblend.theme import Palette, to_tk_hex, get_theme
from tkblend.widgets.base import BaseControl, ScalingTracker
from tkblend.widgets.scrollable_frame import VectorScrollbar


class DropdownPopup(tk.Toplevel):
    """
    Floating Material Design 3 vector styled dropdown list.
    Features:
      - Zero flicker / corner flash: kept withdrawn during layout and geometry calculation
      - Multi-monitor / screen bounds clamping and auto-flip (opens upwards if below space is limited)
      - Scrollable item list with modern VectorScrollbar when items exceed max_visible_items
      - Keyboard navigation (Up/Down arrow keys, Enter/Space to select, Escape to dismiss)
      - App-wide click-outside listener with anchor exclusion to prevent reopening race conditions
      - Clean resource teardown and lifecycle management
    """

    def __init__(
        self,
        master: tk.Widget,
        values: Sequence[str],
        current_value: str = "",
        on_select: Optional[Callable[[str], None]] = None,
        on_dismiss: Optional[Callable[[], None]] = None,
        target_bounds: Optional[tuple[int, int, int, int]] = None,
        max_visible_items: int = 8,
        min_width: Optional[int] = None,
    ):
        super().__init__(master)
        # CRITICAL: Keep hidden immediately to prevent opening at (0, 0) in corner of screen
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self._master = master
        self._root_widget = master._root()
        self._on_select = on_select
        self._on_dismiss = on_dismiss
        self._values = list(values)
        self._current_value = str(current_value) if current_value is not None else ""
        self._max_visible_items = max(1, max_visible_items)
        self._min_width = min_width
        self._target_bounds = target_bounds
        self._selected = False
        self._dismissed = False

        self._bind_id_b1: Optional[str] = None
        self._bind_id_b3: Optional[str] = None
        self._top_conf_id: Optional[str] = None
        self._toplevel_master: Optional[tk.Misc] = None

        pal = getattr(master, "_palette", None) or get_theme()
        bg_hex = to_tk_hex(getattr(pal, "card_bg", "#25232a"))
        border_hex = to_tk_hex(getattr(pal, "card_border", "#49454f"))
        fg_hex = to_tk_hex(getattr(pal, "fg", "#e6e0e9"))
        primary_hex = to_tk_hex(getattr(pal, "primary", "#8b5cf6"))
        hover_hex = to_tk_hex(getattr(pal, "surface", "#2f2d38"))

        self._bg_hex = bg_hex
        self._fg_hex = fg_hex
        self._primary_hex = primary_hex
        self._hover_hex = hover_hex

        scale = ScalingTracker.get_scaling_factor(master)
        font_size = max(8, int(10 * scale))
        item_pad_x = max(8, int(12 * scale))
        item_pad_y = max(4, int(6 * scale))
        self._scrollbar_width = max(8, int(10 * scale))

        self.configure(bg=border_hex, padx=1, pady=1)

        container = tk.Frame(self, bg=bg_hex)
        container.pack(fill="both", expand=True)

        self._needs_scroll = len(self._values) > self._max_visible_items
        self._labels: list[tk.Label] = []
        self._highlighted_idx: int = -1

        for idx, val in enumerate(self._values):
            if str(val) == self._current_value:
                self._highlighted_idx = idx
                break
        if self._highlighted_idx == -1 and self._values:
            self._highlighted_idx = 0

        if self._needs_scroll:
            self._scrollbar = VectorScrollbar(
                container,
                orientation="vertical",
                command=self._on_scrollbar_move,
                width=self._scrollbar_width,
                parent_bg=bg_hex,
            )
            self._scrollbar.pack(side="right", fill="y", padx=(1, 3), pady=2)

            self._canvas = tk.Canvas(
                container,
                bg=bg_hex,
                highlightthickness=0,
                bd=0,
            )
            self._canvas.pack(side="left", fill="both", expand=True)
            self._canvas.configure(yscrollcommand=self._scrollbar.set)

            self._items_frame = tk.Frame(self._canvas, bg=bg_hex)
            self._canvas_win = self._canvas.create_window((0, 0), window=self._items_frame, anchor="nw")

            def _on_frame_configure(e):
                self._canvas.configure(scrollregion=self._canvas.bbox("all"))

            def _on_canvas_configure(e):
                self._canvas.itemconfig(self._canvas_win, width=e.width)

            self._items_frame.bind("<Configure>", _on_frame_configure)
            self._canvas.bind("<Configure>", _on_canvas_configure)
        else:
            self._canvas = None
            self._scrollbar = None
            self._items_frame = container

        for idx, val in enumerate(self._values):
            is_active = (str(val) == self._current_value)
            item_fg = primary_hex if is_active else fg_hex
            item_font = ("sans-serif", font_size, "bold" if is_active else "normal")
            lbl = tk.Label(
                self._items_frame,
                text=str(val),
                bg=bg_hex,
                fg=item_fg,
                font=item_font,
                anchor="w",
                padx=item_pad_x,
                pady=item_pad_y,
                cursor="hand2",
            )
            lbl.pack(fill="x")
            self._labels.append(lbl)

            def _make_callbacks(i: int):
                def _on_enter(e):
                    self._set_highlight(i, scroll_into_view=False)
                def _on_click(e):
                    self._choose_index(i)
                lbl.bind("<Enter>", _on_enter)
                lbl.bind("<Button-1>", _on_click)

            _make_callbacks(idx)

        # Mouse wheel bindings
        if self._needs_scroll:
            widgets_to_bind = [self, container, self._canvas, self._items_frame] + self._labels
            if self._scrollbar is not None:
                widgets_to_bind.append(self._scrollbar)
            for w in widgets_to_bind:
                w.bind("<Button-4>", self._on_mousewheel)
                w.bind("<Button-5>", self._on_mousewheel)
                w.bind("<MouseWheel>", self._on_mousewheel)

        # Keyboard bindings
        self.bind("<Up>", lambda e: self._on_key_nav(-1))
        self.bind("<Down>", lambda e: self._on_key_nav(1))
        self.bind("<Return>", lambda e: self._on_key_select())
        self.bind("<KP_Enter>", lambda e: self._on_key_select())
        self.bind("<space>", lambda e: self._on_key_select())
        self.bind("<Escape>", lambda e: self.dismiss())

        # Determine geometry while STILL withdrawn
        self.update_idletasks()

        if self._target_bounds is not None:
            bx, by, bw, bh = self._target_bounds
            anchor_rx = master.winfo_rootx() + bx
            anchor_ry = master.winfo_rooty() + by
            anchor_rw = bw
            anchor_rh = bh
        else:
            anchor_rx = master.winfo_rootx()
            anchor_ry = master.winfo_rooty()
            anchor_rw = master.winfo_width()
            anchor_rh = master.winfo_height()

        self._anchor_rect = (anchor_rx, anchor_ry, anchor_rw, anchor_rh)

        item_h = self._labels[0].winfo_reqheight() if self._labels else int(32 * scale)
        items_req_w = self._items_frame.winfo_reqwidth() if self._items_frame else anchor_rw
        sb_space = (self._scrollbar_width + 4) if self._needs_scroll else 0

        req_w = max(anchor_rw, items_req_w + sb_space, self._min_width or 0)

        if self._needs_scroll and self._canvas is not None:
            canvas_h = item_h * self._max_visible_items
            canvas_w = req_w - sb_space
            self._canvas.configure(width=canvas_w, height=canvas_h)
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
            self._canvas.itemconfig(self._canvas_win, width=canvas_w)
            self.update_idletasks()
            req_h = canvas_h + 2
        else:
            req_h = self.winfo_reqheight()

        # Multi-monitor / screen boundary clamping & auto-flip
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        space_below = screen_h - (anchor_ry + anchor_rh) - 12
        space_above = anchor_ry - 12

        if req_h <= space_below or space_below >= space_above:
            pos_y = anchor_ry + anchor_rh + 2
            if req_h > space_below and space_below > 60:
                req_h = space_below
        else:
            pos_y = anchor_ry - req_h - 2
            if pos_y < 4:
                pos_y = 4
                req_h = min(req_h, space_above)

        pos_x = anchor_rx
        if pos_x + req_w > screen_w - 4:
            pos_x = max(4, screen_w - req_w - 4)
        if pos_x < 4:
            pos_x = 4

        self._popup_rect = (pos_x, pos_y, req_w, req_h)
        self.geometry(f"{int(req_w)}x{int(req_h)}+{int(pos_x)}+{int(pos_y)}")

        if self._highlighted_idx >= 0:
            self._set_highlight(self._highlighted_idx, scroll_into_view=True)

        # Deiconify now that geometry and layout are completely ready
        self.deiconify()
        self.lift()
        self.focus_set()

        # Global outside-click dismissal
        self._bind_id_b1 = self._root_widget.bind_all("<Button-1>", self._on_global_click, add="+")
        self._bind_id_b3 = self._root_widget.bind_all("<Button-3>", self._on_global_click, add="+")

        try:
            self._toplevel_master = master.winfo_toplevel()
            self._top_conf_id = self._toplevel_master.bind("<Configure>", self._on_master_configure, add="+")
        except Exception:
            self._toplevel_master = None

        self.bind("<Destroy>", self._on_destroy_event)

    def _on_mousewheel(self, event) -> str:
        if not self._needs_scroll or self._canvas is None:
            return "break"
        if event.num == 4:
            self._canvas.yview_scroll(-2, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(2, "units")
        elif getattr(event, "delta", 0):
            delta = event.delta
            steps = int(-1 * (delta / 120) * 2) if abs(delta) >= 120 else int(-1 * delta)
            if steps == 0:
                steps = -1 if delta > 0 else 1
            self._canvas.yview_scroll(steps, "units")
        return "break"

    def _on_scrollbar_move(self, *args) -> None:
        if not args or self._canvas is None:
            return
        cmd = args[0]
        if cmd == "moveto" and len(args) > 1:
            try:
                self._canvas.yview_moveto(float(args[1]))
            except Exception:
                pass
        elif cmd == "scroll" and len(args) > 2:
            try:
                self._canvas.yview_scroll(int(args[1]), str(args[2]))
            except Exception:
                pass

    def _set_highlight(self, idx: int, scroll_into_view: bool = False) -> None:
        if not (0 <= idx < len(self._labels)):
            return
        old_idx = self._highlighted_idx
        self._highlighted_idx = idx

        if 0 <= old_idx < len(self._labels) and old_idx != idx:
            old_lbl = self._labels[old_idx]
            is_cur = (str(self._values[old_idx]) == self._current_value)
            old_lbl.configure(
                bg=self._bg_hex,
                fg=self._primary_hex if is_cur else self._fg_hex,
            )

        new_lbl = self._labels[idx]
        new_lbl.configure(bg=self._hover_hex)

        if scroll_into_view and self._needs_scroll and self._canvas is not None:
            self._scroll_item_into_view(idx)

    def _scroll_item_into_view(self, idx: int) -> None:
        if not self._needs_scroll or self._canvas is None or not self._values:
            return
        total = len(self._values)
        if total <= self._max_visible_items:
            return
        top_frac, bot_frac = self._canvas.yview()
        item_top_frac = idx / total
        item_bot_frac = (idx + 1) / total
        if item_top_frac < top_frac:
            self._canvas.yview_moveto(item_top_frac)
        elif item_bot_frac > bot_frac:
            vis_span = bot_frac - top_frac
            self._canvas.yview_moveto(max(0.0, item_bot_frac - vis_span))

    def _on_key_nav(self, delta: int) -> None:
        if not self._labels:
            return
        new_idx = max(0, min(len(self._labels) - 1, self._highlighted_idx + delta))
        self._set_highlight(new_idx, scroll_into_view=True)

    def _on_key_select(self) -> None:
        if 0 <= self._highlighted_idx < len(self._labels):
            self._choose_index(self._highlighted_idx)

    def _choose_index(self, idx: int) -> None:
        if not (0 <= idx < len(self._values)):
            return
        self._selected = True
        chosen = self._values[idx]
        self.dismiss()
        if callable(self._on_select):
            try:
                self._on_select(chosen)
            except Exception:
                pass

    def _on_global_click(self, event) -> None:
        if self._dismissed:
            return
        try:
            if not self.winfo_exists():
                return
            x = event.x_root
            y = event.y_root

            px, py, pw, ph = self._popup_rect
            if px <= x <= px + pw and py <= y <= py + ph:
                return

            clicked_w = getattr(event, "widget", None)
            is_anchor = (clicked_w == self._master)
            if not is_anchor and self._target_bounds is not None:
                ax, ay, aw, ah = self._anchor_rect
                if aw > 1 and ah > 1 and ax <= x <= ax + aw and ay <= y <= ay + ah:
                    is_anchor = True

            self.dismiss(by_anchor=is_anchor)
        except Exception:
            self.dismiss(by_anchor=False)

    def _on_master_configure(self, event) -> None:
        if event.widget == self._toplevel_master:
            self.dismiss(by_anchor=False)

    def _on_destroy_event(self, event) -> None:
        if event.widget == self:
            self.dismiss(by_anchor=False)

    def dismiss(self, by_anchor: bool = False) -> None:
        if self._dismissed:
            return
        self._dismissed = True
        self._cleanup_bindings()
        try:
            self.destroy()
        except Exception:
            pass
        if not self._selected and callable(self._on_dismiss):
            try:
                self._on_dismiss(by_anchor)
            except TypeError:
                try:
                    self._on_dismiss()
                except Exception:
                    pass
            except Exception:
                pass

    def _cleanup_bindings(self) -> None:
        try:
            if self._bind_id_b1:
                self._root_widget._unbind(('bind', 'all', '<Button-1>'), self._bind_id_b1)
                self._bind_id_b1 = None
        except Exception:
            pass
        try:
            if self._bind_id_b3:
                self._root_widget._unbind(('bind', 'all', '<Button-3>'), self._bind_id_b3)
                self._bind_id_b3 = None
        except Exception:
            pass
        try:
            if self._top_conf_id and self._toplevel_master:
                self._toplevel_master.unbind("<Configure>", self._top_conf_id)
                self._top_conf_id = None
        except Exception:
            pass


_DropdownPopup = DropdownPopup


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
        current_value: Optional[str] = None,
        command: Optional[Callable[[str], Any]] = None,
        variable: Optional[tk.Variable] = None,
        width: int = 160,
        height: int = 38,
        max_visible_items: int = 8,
        **kwargs,
    ):
        self._values = list(values) if values else []
        self._variable = variable
        self._command = command
        self._popup: Optional[DropdownPopup] = None
        self._max_visible_items = max_visible_items
        self._last_dismiss_time: float = 0.0

        super().__init__(
            master=master,
            widget_class="combobox",
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )

        init_val = str(value if value != "" else (current_value or ""))
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

        now = time.monotonic()
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.dismiss(by_anchor=True)
            self._popup = None
            self._last_dismiss_time = now
            return

        # Prevent immediate reopening when click on combobox caused dismiss
        if now - self._last_dismiss_time < 0.25:
            return

        def _on_select(chosen: str):
            self.set(chosen)
            self._popup = None
            self._last_dismiss_time = 0.0
            if callable(self._command):
                try:
                    self._command(chosen)
                except Exception:
                    pass

        def _on_dismiss(by_anchor: bool = False):
            self._popup = None
            if by_anchor:
                self._last_dismiss_time = time.monotonic()

        self._popup = DropdownPopup(
            master=self,
            values=self._values,
            current_value=self.get(),
            on_select=_on_select,
            on_dismiss=_on_dismiss,
            max_visible_items=self._max_visible_items,
        )


OptionMenu = ComboBox

__all__ = ["ComboBox", "OptionMenu", "DropdownPopup", "_DropdownPopup"]
