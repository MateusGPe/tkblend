"""
Dropdown and DropdownItem widgets providing a modern popup select menu.
"""

from __future__ import annotations
import sys
import tkinter as tk
from typing import Optional, Callable, List

from tkblend.theme import get_theme, blend_color_hex
from tkblend.widgets.base import Widget
from tkblend.widgets.scrollbar import VectorScrollbar
from tkblend.widgets.drawing import draw_vector_checkmark, draw_vector_chevron, truncate_text


class DropdownItem(Widget):
    """
    Lightweight vector row widget for modern dropdown popup items.
    Renders rounded hover highlight pill, clean typography, and selected checkmark
    with vibrant, high-contrast theme styling.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        is_selected: bool = False,
        on_select: Optional[Callable[[str], None]] = None,
        width: int = 180,
        height: int = 32,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._text = text
        self._is_selected = is_selected
        self._on_select = on_select
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)
        self.bind("<ButtonRelease-1>", self._handle_click)

    @property
    def text(self) -> str:
        return self._text

    @property
    def is_selected(self) -> bool:
        return self._is_selected

    def set_selected(self, val: bool) -> None:
        if self._is_selected != val:
            self._is_selected = val
            self.render()

    def _handle_click(self, event) -> None:
        if not self._is_disabled and self._on_select:
            self._on_select(self._text)

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            w = float(self._widget_w)
            h = float(self._widget_h)
            pal = get_theme()

            pad_x = 4.0 * s
            pad_y = 2.0 * s
            pill_w = max(1.0, w - pad_x * 2.0)
            pill_h = max(1.0, h - pad_y * 2.0)
            r = 6.0 * s

            # High-contrast states
            if self._is_selected:
                sel_bg = blend_color_hex(pal.secondary, pal.primary, 0.25)
                sel_border = pal.primary
                text_color = pal.primary
                chk_color = pal.primary

                self._surface.fill_rounded_rect(pad_x, pad_y, pill_w, pill_h, r, r, sel_bg)
                self._surface.stroke_rounded_rect(pad_x, pad_y, pill_w, pill_h, r, r, sel_border, 1.2 * s)

            elif self._is_hovered:
                hover_bg = pal.secondary_hover
                hover_border = pal.card_border
                text_color = pal.fg
                self._surface.fill_rounded_rect(pad_x, pad_y, pill_w, pill_h, r, r, hover_bg)
                self._surface.stroke_rounded_rect(pad_x, pad_y, pill_w, pill_h, r, r, hover_border, 1.0 * s)

            else:
                text_color = pal.fg

            # Typography
            font_sz = 12.5 * s
            text_x = pad_x + 12.0 * s
            text_y = h / 2.0 + (font_sz * 0.35)
            self._surface.draw_text(
                self._text,
                text_x,
                text_y,
                font_size=font_sz,
                font_family="sans-serif",
                color=text_color,
                align="left",
            )

            # Draw vector checkmark on the right if selected
            if self._is_selected:
                chk_x = w - pad_x - 14.0 * s
                chk_y = h / 2.0
                draw_vector_checkmark(self._surface, chk_x, chk_y, s, chk_color, stroke_width=2.2 * s)

            self._surface.blit(self._photo)
        except Exception:
            pass


class Dropdown(Widget):
    """
    Vector dropdown select with current value, animated chevron icon,
    and elevated popup option picker featuring modular vector item rows.
    Supports keyboard navigation, auto-flip positioning, and visible high-contrast VectorScrollbar.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        options: Optional[List[str]] = None,
        selected: Optional[str] = None,
        on_select: Optional[Callable[[str], None]] = None,
        width: int = 180,
        height: int = 36,
        max_visible_items: int = 6,
        placeholder: str = "Select...",
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._dropdown_items = list(options) if options else ["Option A", "Option B"]
        self._selected = selected if selected in self._dropdown_items else (self._dropdown_items[0] if self._dropdown_items else "")
        self._on_select = on_select
        self._max_visible_items = max(1, max_visible_items)
        self._placeholder = placeholder
        self._is_open = False
        self._is_focused = False
        self._popup_win: Optional[tk.Toplevel] = None
        self._item_widgets: List[DropdownItem] = []
        self._scroll_canvas: Optional[tk.Canvas] = None
        self._scrollbar: Optional[VectorScrollbar] = None
        self._root_bind_id: Optional[str] = None
        self._parent_bind_id: Optional[str] = None
        self._escape_bind_id: Optional[str] = None
        self._root_focus_bind_id: Optional[str] = None

        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

        # Enable keyboard focus and bindings
        self.configure(takefocus=1)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<KeyPress-Down>", self._on_key_down)
        self.bind("<KeyPress-Up>", self._on_key_up)
        self.bind("<Return>", self._on_key_enter)
        self.bind("<space>", self._on_key_enter)
        self.bind("<Escape>", lambda e: self._close_popup())
        self.bind("<Home>", self._on_key_home)
        self.bind("<End>", self._on_key_end)
        self.bind("<ButtonRelease-1>", self._handle_click)

    @property
    def value(self) -> str:
        return self._selected

    @value.setter
    def value(self, val: str) -> None:
        self._selected = val
        self.render()
        if self._is_open:
            self._update_item_states()

    @property
    def options(self) -> List[str]:
        return list(self._dropdown_items)

    @options.setter
    def options(self, new_opts: List[str]) -> None:
        self._dropdown_items = list(new_opts) if new_opts else []
        if self._selected not in self._dropdown_items:
            self._selected = self._dropdown_items[0] if self._dropdown_items else ""
        self.render()

    def set_options(self, options: List[str], selected: Optional[str] = None) -> None:
        """Update options list and optionally choose selected item."""
        self._dropdown_items = list(options) if options else []
        if selected and selected in self._dropdown_items:
            self._selected = selected
        elif self._dropdown_items:
            self._selected = self._dropdown_items[0]
        else:
            self._selected = ""
        self.render()

    def _handle_click(self, event) -> None:
        if self._is_disabled:
            return
        self._is_pressed = False
        try:
            self.focus_set()
        except Exception:
            pass
        self._toggle_popup(event)

    def _on_focus_in(self, event) -> None:
        self._is_focused = True
        self.render()

    def _on_focus_out(self, event) -> None:
        self._is_focused = False
        self.render()

    def _on_key_down(self, event) -> str:
        if not self._dropdown_items:
            return "break"
        idx = self._dropdown_items.index(self._selected) if self._selected in self._dropdown_items else -1
        new_idx = min(len(self._dropdown_items) - 1, idx + 1)
        self._select_option(self._dropdown_items[new_idx], notify=True, close=False)
        if self._is_open:
            self._scroll_item_into_view(new_idx)
        return "break"

    def _on_key_up(self, event) -> str:
        if not self._dropdown_items:
            return "break"
        idx = self._dropdown_items.index(self._selected) if self._selected in self._dropdown_items else 0
        new_idx = max(0, idx - 1)
        self._select_option(self._dropdown_items[new_idx], notify=True, close=False)
        if self._is_open:
            self._scroll_item_into_view(new_idx)
        return "break"

    def _on_key_home(self, event) -> str:
        if self._dropdown_items:
            self._select_option(self._dropdown_items[0], notify=True, close=False)
            if self._is_open:
                self._scroll_item_into_view(0)
        return "break"

    def _on_key_end(self, event) -> str:
        if self._dropdown_items:
            last_idx = len(self._dropdown_items) - 1
            self._select_option(self._dropdown_items[last_idx], notify=True, close=False)
            if self._is_open:
                self._scroll_item_into_view(last_idx)
        return "break"

    def _on_key_enter(self, event) -> str:
        if self._is_open:
            self._close_popup()
        else:
            self._open_popup()
        return "break"

    def _toggle_popup(self, event=None) -> None:
        if self._is_open:
            self._close_popup()
        else:
            self._open_popup()

    def _scroll_item_into_view(self, idx: int) -> None:
        if self._scroll_canvas and len(self._dropdown_items) > self._max_visible_items:
            total = len(self._dropdown_items)
            frac = idx / max(1, total - 1)
            self._scroll_canvas.yview_moveto(max(0.0, min(1.0, frac - 0.2)))

    def _open_popup(self) -> None:
        if self._is_open:
            return
        self._is_open = True
        self.render()

        self.update_idletasks()
        rx = self.winfo_rootx()
        ry = self.winfo_rooty()
        rw = self._widget_w
        rh = self._widget_h
        s = self._scale

        item_h = max(24, int(32 * s))
        total_items = len(self._dropdown_items)
        visible_count = min(total_items, self._max_visible_items)
        pop_pad = int(4 * s)
        pop_h = visible_count * item_h + pop_pad * 2 + int(4 * s)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        space_below = screen_h - (ry + rh + int(4 * s))

        # Auto-flip upward if not enough room below
        if space_below < pop_h and ry > pop_h:
            pop_y = ry - pop_h - int(4 * s)
        else:
            pop_y = ry + rh + int(4 * s)

        # Clamp Y to screen boundaries
        if pop_y < 0:
            pop_y = 0
        elif pop_y + pop_h > screen_h:
            pop_y = max(0, screen_h - pop_h - 4)

        # Clamp X to screen boundaries
        pop_x = max(0, rx)
        pop_w = rw
        if pop_x + pop_w > screen_w:
            pop_x = max(0, screen_w - pop_w - 4)

        pal = get_theme()
        toplevel = self.winfo_toplevel()

        border_col = pal.card_border
        popup_bg = pal.card_bg

        self._popup_win = tk.Toplevel(self)
        self._popup_win.wm_overrideredirect(True)
        try:
            self._popup_win.transient(toplevel)
        except Exception:
            pass
        self._popup_win.geometry(f"{pop_w}x{pop_h}+{pop_x}+{pop_y}")
        self._popup_win.configure(bg=border_col)

        # Border container frame for crisp 1.5px border
        border_frame = tk.Frame(self._popup_win, bg=border_col, padx=1, pady=1)
        border_frame.pack(fill="both", expand=True)

        inner_frame = tk.Frame(border_frame, bg=popup_bg)
        inner_frame.pack(fill="both", expand=True)

        self._item_widgets = []

        # If items exceed max_visible_items, use a scrollable canvas with high-contrast VectorScrollbar
        if total_items > self._max_visible_items:
            scrollbar_w = int(10 * s)
            content_w = max(10, pop_w - scrollbar_w - int(10 * s))

            canvas = tk.Canvas(
                inner_frame,
                bg=popup_bg,
                highlightthickness=0,
                bd=0,
                width=content_w,
                height=visible_count * item_h,
            )

            scrollbar = VectorScrollbar(
                inner_frame,
                command=canvas.yview,
                width=10,
                height=int((visible_count * item_h) / s),
                parent_bg=popup_bg,
            )
            canvas.configure(yscrollcommand=scrollbar.set)

            scrollbar.pack(side="right", fill="y", padx=(int(2 * s), int(4 * s)), pady=int(3 * s))
            canvas.pack(side="left", fill="both", expand=True, padx=(int(4 * s), int(2 * s)), pady=int(3 * s))
            self._scroll_canvas = canvas
            self._scrollbar = scrollbar

            scroll_frame = tk.Frame(canvas, bg=popup_bg)
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=content_w)

            def _on_frame_configure(e):
                canvas.configure(scrollregion=canvas.bbox("all"))

            scroll_frame.bind("<Configure>", _on_frame_configure)

            def _on_wheel(e):
                if sys.platform == "darwin":
                    canvas.yview_scroll(int(-1 * e.delta), "units")
                elif sys.platform.startswith("win"):
                    canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
                else:
                    if getattr(e, "num", None) == 4:
                        canvas.yview_scroll(-2, "units")
                    elif getattr(e, "num", None) == 5:
                        canvas.yview_scroll(2, "units")
                    elif hasattr(e, "delta") and e.delta:
                        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
                return "break"

            canvas.bind("<MouseWheel>", _on_wheel)
            canvas.bind("<Button-4>", _on_wheel)
            canvas.bind("<Button-5>", _on_wheel)

            item_w_logical = int(content_w / s)
            for opt in self._dropdown_items:
                it = DropdownItem(
                    scroll_frame,
                    text=opt,
                    is_selected=(opt == self._selected),
                    on_select=self._on_item_clicked,
                    width=item_w_logical,
                    height=30,
                    parent_bg=popup_bg,
                )
                it.pack(fill="x", pady=1)
                it.bind("<MouseWheel>", _on_wheel, add="+")
                it.bind("<Button-4>", _on_wheel, add="+")
                it.bind("<Button-5>", _on_wheel, add="+")
                self._item_widgets.append(it)

            # Scroll selected into view initially
            if self._selected in self._dropdown_items:
                sel_idx = self._dropdown_items.index(self._selected)
                self._scroll_item_into_view(sel_idx)
        else:
            self._scroll_canvas = None
            self._scrollbar = None
            item_w_logical = int(self._logical_w)
            for opt in self._dropdown_items:
                it = DropdownItem(
                    inner_frame,
                    text=opt,
                    is_selected=(opt == self._selected),
                    on_select=self._on_item_clicked,
                    width=item_w_logical - 6,
                    height=30,
                    parent_bg=popup_bg,
                )
                it.pack(fill="x", pady=1, padx=int(3 * s))
                self._item_widgets.append(it)

        # Global event listeners for rock-solid dismissal
        self._root_bind_id = toplevel.bind("<ButtonPress-1>", self._on_root_click, add="+")
        self._parent_bind_id = toplevel.bind("<Configure>", self._on_root_configure, add="+")
        self._escape_bind_id = toplevel.bind("<Escape>", lambda e: self._close_popup(), add="+")
        self._root_focus_bind_id = toplevel.bind("<FocusOut>", self._on_root_focus_out, add="+")

    def _on_root_click(self, event) -> None:
        if not self._is_open or not self._popup_win or not self._popup_win.winfo_exists():
            return
        px = event.x_root
        py = event.y_root

        # Check if click is inside the popup
        try:
            pop_x = self._popup_win.winfo_rootx()
            pop_y = self._popup_win.winfo_rooty()
            pop_w = self._popup_win.winfo_width()
            pop_h = self._popup_win.winfo_height()
            if pop_x <= px <= pop_x + pop_w and pop_y <= py <= pop_h + pop_y:
                return
        except Exception:
            pass

        # Check if click is on the trigger widget itself
        try:
            trig_x = self.winfo_rootx()
            trig_y = self.winfo_rooty()
            trig_w = self.winfo_width()
            trig_h = self.winfo_height()
            if trig_x <= px <= trig_x + trig_w and trig_y <= py <= trig_h + trig_y:
                return
        except Exception:
            pass

        # Otherwise clicked outside: close cleanly
        self._close_popup()

    def _on_root_configure(self, event) -> None:
        if self._is_open and event.widget == self.winfo_toplevel():
            self._close_popup()

    def _on_root_focus_out(self, event) -> None:
        if not self._is_open:
            return
        top = self.winfo_toplevel()
        if event.widget == top:
            try:
                if top.focus_displayof() is None:
                    self._close_popup()
            except Exception:
                pass

    def _close_popup(self) -> None:
        if not self._is_open and not self._popup_win:
            return
        self._is_open = False

        try:
            top = self.winfo_toplevel()
            if self._root_bind_id:
                top.unbind("<ButtonPress-1>", self._root_bind_id)
                self._root_bind_id = None
            if self._parent_bind_id:
                top.unbind("<Configure>", self._parent_bind_id)
                self._parent_bind_id = None
            if self._escape_bind_id:
                top.unbind("<Escape>", self._escape_bind_id)
                self._escape_bind_id = None
            if self._root_focus_bind_id:
                top.unbind("<FocusOut>", self._root_focus_bind_id)
                self._root_focus_bind_id = None
        except Exception:
            pass

        if self._popup_win:
            try:
                self._popup_win.destroy()
            except Exception:
                pass
            self._popup_win = None
        self._item_widgets = []
        self._scroll_canvas = None
        self._scrollbar = None
        self.render()

    def _on_item_clicked(self, opt: str) -> None:
        self._select_option(opt, notify=True, close=True)

    def _select_option(self, opt: str, notify: bool = True, close: bool = True) -> None:
        self._selected = opt
        if close:
            self._close_popup()
        else:
            self._update_item_states()
            self.render()

        if notify and self._on_select:
            try:
                self._on_select(opt)
            except Exception:
                pass

    def _update_item_states(self) -> None:
        for it in self._item_widgets:
            it.set_selected(it.text == self._selected)

    def _on_destroy(self, event=None) -> None:
        self._close_popup()
        super()._on_destroy(event)

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            pad = 2.0 * s
            w = max(1.0, float(self._widget_w) - pad * 2.0)
            h = max(1.0, float(self._widget_h) - pad * 2.0)
            r = 8.0 * s

            pal = get_theme()

            # Input surface background
            field_bg = pal.input_bg

            # Focus ring and border styling
            if self._is_open:
                border = pal.primary
                border_w = 2.0 * s
                field_bg = blend_color_hex(pal.input_bg, pal.primary, 0.08)
            elif self._is_focused:
                border = pal.primary
                border_w = 1.8 * s
            elif self._is_hovered:
                border = pal.primary_hover
                border_w = 1.6 * s
                field_bg = blend_color_hex(pal.input_bg, pal.primary, 0.05)
            else:
                border = pal.input_border
                border_w = 1.2 * s

            # Outer soft focus glow if focused or open
            if self._is_focused or self._is_open:
                glow_color = blend_color_hex(pal.primary, self._parent_bg, 0.45)
                self._surface.stroke_rounded_rect(
                    pad - 1.0 * s,
                    pad - 1.0 * s,
                    w + 2.0 * s,
                    h + 2.0 * s,
                    r + 1.0 * s,
                    r + 1.0 * s,
                    glow_color,
                    2.5 * s,
                )

            self._surface.fill_rounded_rect(pad, pad, w, h, r, r, field_bg)
            self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, border, border_w)

            # Draw selected text or placeholder with high contrast
            font_sz = 13.0 * s
            display_text = self._selected if self._selected else self._placeholder
            text_color = ("#ffffff" if pal.dark_mode else "#0f172a") if self._selected else pal.text_muted

            # Truncate text if needed to avoid overlapping chevron
            max_text_w = self._widget_w - pad * 2.0 - 44.0 * s
            clipped_text = truncate_text(display_text, max_text_w, font_sz, avg_char_width_ratio=0.58)

            self._surface.draw_text(
                clipped_text,
                pad + 12.0 * s,
                self._widget_h / 2.0 + (font_sz * 0.35),
                font_size=font_sz,
                font_family="sans-serif",
                color=text_color,
                align="left",
            )

            # Smooth vector chevron icon (pointing up if open, down if closed)
            chev_x = self._widget_w - pad - 16.0 * s
            chev_y = self._widget_h / 2.0
            chev_color = pal.primary if (self._is_open or self._is_hovered or self._is_focused) else ("#bac2de" if pal.dark_mode else "#64748b")
            draw_vector_chevron(self._surface, chev_x, chev_y, s, "up" if self._is_open else "down", chev_color, stroke_width=2.0 * s)

            self._surface.blit(self._photo)
        except Exception:
            pass


ModernDropdown = Dropdown
