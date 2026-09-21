"""
Input widgets for tkblend: ModernEntry and ModernDropdown (OptionMenu).
Full .configure() / .cget() protocol, placeholder text, focus glow shadows,
and cross-platform DPI scaling.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, List, Tuple, Any, Dict, Union

from tkblend.surface import Surface, ColorLike, Path
from tkblend.widgets.base import _resolve_parent_bg
from tkblend.widgets.theme import Theme, ThemeManager
from tkblend.widgets.scaling import ScalingTracker


# ============================================================================
# ModernEntry
# ============================================================================

class ModernEntry(tk.Frame):
    """
    Modern hybrid text entry widget with antialiased Blend2D border,
    focus ring glow, drop shadow, placeholder text, embedded tk.Entry,
    and complete .configure() / .cget() / dict subscripting parity.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 40,
        placeholder: str = "",
        placeholder_text: Optional[str] = None,
        text: str = "",
        rx: Optional[float] = None,
        corner_radius: Optional[float] = None,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        focus_border_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        fg_color: Optional[ColorLike] = None,
        placeholder_color: Optional[ColorLike] = None,
        placeholder_text_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        show: Optional[str] = None,
        is_password: bool = False,
        is_error: bool = False,
        state: str = "normal",
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._theme = t
        self._requested_w = max(1, width)
        self._requested_h = max(1, height)
        self._widget_w = max(1, ScalingTracker.scale(self._requested_w, master))
        self._widget_h = max(1, ScalingTracker.scale(self._requested_h, master))
        self._custom_rx = corner_radius if corner_radius is not None else rx
        self._custom_parent_bg = parent_bg
        self._parent_bg = _resolve_parent_bg(master, self._custom_parent_bg, self._theme)
        self._custom_bg_color = bg_color
        self._custom_border_color = border_color
        self._custom_focus_border_color = focus_border_color
        self._custom_text_color = text_color or fg_color
        self._custom_placeholder_color = placeholder_color or placeholder_text_color
        self._custom_font_size = font_size
        self._custom_font_family = font_family
        self._placeholder = placeholder_text if placeholder_text is not None else placeholder
        self._is_focused = False
        self._is_error = is_error
        self._state = state
        self._show = "*" if is_password else (show or "")

        super().__init__(
            master,
            width=self._widget_w,
            height=self._widget_h,
            background=self._parent_bg,
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        # Blend2D Background Label
        self._photo = tk.PhotoImage(master=self, width=self._widget_w, height=self._widget_h)
        self._surface = Surface(self._widget_w, self._widget_h)
        self._bg_label = tk.Label(
            self,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            background=self._parent_bg,
        )
        self._bg_label.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._bg_label.lower()

        # Native tk.Entry embedded inside
        font_size_val = self._custom_font_size if self._custom_font_size is not None else t.font_size_md
        font_family_val = self._custom_font_family or t.font_family
        tk_font = (font_family_val, int(font_size_val))
        bg_col = self._custom_bg_color if self._custom_bg_color is not None else t.bg_input
        text_col = self._custom_text_color if self._custom_text_color is not None else t.text

        self._entry = tk.Entry(
            self,
            font=tk_font,
            fg=text_col,
            bg=bg_col,
            insertbackground=t.primary,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            show=self._show,
            state=self._state,
        )
        self._entry.place(
            x=12,
            y=int((self._widget_h - font_size_val * 1.5) / 2),
            width=max(1, self._widget_w - 24),
            height=int(font_size_val * 1.5),
        )

        self._placeholder_active = False
        if text:
            self._entry.insert(0, text)
        elif self._placeholder:
            self._show_placeholder()

        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Configure>", self._on_configure)
        self.bind("<Map>", self._on_map)

        ThemeManager.subscribe(self._on_theme_changed)
        self.bind("<Destroy>", lambda e: ThemeManager.unsubscribe(self._on_theme_changed))

        self.after_idle(self.render)

    # ------------------------------------------------------------------------
    # Protocol: configure(), cget(), __getitem__, __setitem__
    # ------------------------------------------------------------------------

    def configure(self, **kwargs) -> Any:
        if not kwargs:
            return {
                "width": self._requested_w,
                "height": self._requested_h,
                "placeholder": self._placeholder,
                "state": self._state,
                "is_error": self._is_error,
            }

        redraw = False
        if "text" in kwargs:
            self.set_text(kwargs.pop("text"))
        if "placeholder" in kwargs or "placeholder_text" in kwargs:
            self._placeholder = kwargs.pop("placeholder", None) or kwargs.pop("placeholder_text", None) or ""
            if not self._entry.get() or self._placeholder_active:
                self._show_placeholder()
        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._entry.configure(state=self._state)
            redraw = True
        if "is_error" in kwargs:
            self._is_error = bool(kwargs.pop("is_error"))
            redraw = True
        if "corner_radius" in kwargs or "rx" in kwargs:
            self._custom_rx = kwargs.pop("corner_radius", None) or kwargs.pop("rx", None)
            redraw = True
        if "bg_color" in kwargs:
            self._custom_bg_color = kwargs.pop("bg_color")
            self._entry.configure(bg=self._custom_bg_color)
            redraw = True
        if "border_color" in kwargs:
            self._custom_border_color = kwargs.pop("border_color")
            redraw = True
        if "focus_border_color" in kwargs:
            self._custom_focus_border_color = kwargs.pop("focus_border_color")
            redraw = True
        if "text_color" in kwargs or "fg_color" in kwargs:
            self._custom_text_color = kwargs.pop("text_color", None) or kwargs.pop("fg_color", None)
            if not self._placeholder_active:
                self._entry.configure(fg=self._custom_text_color)
        if "placeholder_color" in kwargs or "placeholder_text_color" in kwargs:
            self._custom_placeholder_color = kwargs.pop("placeholder_color", None) or kwargs.pop("placeholder_text_color", None)
            if self._placeholder_active:
                self._entry.configure(fg=self._custom_placeholder_color)
        if "show" in kwargs:
            self._show = kwargs.pop("show")
            self._entry.configure(show=self._show)
        if "font_size" in kwargs:
            self._custom_font_size = kwargs.pop("font_size")
            font_size_val = self._custom_font_size
            font_family_val = self._custom_font_family or self._theme.font_family
            self._entry.configure(font=(font_family_val, int(font_size_val)))
            self._entry.place_configure(
                y=int((self._widget_h - font_size_val * 1.5) / 2),
                height=int(font_size_val * 1.5),
            )
            redraw = True

        if redraw and self.winfo_exists():
            self.render()

    def config(self, **kwargs) -> Any:
        return self.configure(**kwargs)

    def cget(self, key: str) -> Any:
        if key == "width":
            return self._requested_w
        elif key == "height":
            return self._requested_h
        elif key in ("placeholder", "placeholder_text"):
            return self._placeholder
        elif key == "state":
            return self._state
        elif key == "is_error":
            return self._is_error
        elif key in ("corner_radius", "rx"):
            return self._custom_rx
        elif key == "bg_color":
            return self._custom_bg_color
        elif key in ("text_color", "fg_color"):
            return self._custom_text_color
        elif key == "text":
            return self.get()
        return self._entry.cget(key)

    def __getitem__(self, key: str) -> Any:
        return self.cget(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.configure(**{key: value})

    # Delegated Entry Methods
    def get(self) -> str:
        if self._placeholder_active:
            return ""
        return self._entry.get()

    def set_text(self, text: str) -> None:
        self._entry.delete(0, tk.END)
        text_col = self._custom_text_color if self._custom_text_color is not None else self._theme.text
        if text:
            self._placeholder_active = False
            self._entry.configure(fg=text_col, show=self._show)
            self._entry.insert(0, text)
        elif self._placeholder and not self._is_focused:
            self._show_placeholder()

    def insert(self, index: Any, string: str) -> None:
        self._hide_placeholder()
        self._entry.insert(index, string)

    def delete(self, first: Any, last: Optional[Any] = None) -> None:
        self._entry.delete(first, last)
        if not self._entry.get() and not self._is_focused:
            self._show_placeholder()

    def focus(self) -> None:
        self._entry.focus_set()

    def select_range(self, start: int, end: int) -> None:
        self._entry.select_range(start, end)

    def icursor(self, index: int) -> None:
        self._entry.icursor(index)

    @property
    def is_error(self) -> bool:
        return self._is_error

    @is_error.setter
    def is_error(self, val: bool) -> None:
        self.configure(is_error=bool(val))

    def _show_placeholder(self) -> None:
        self._placeholder_active = True
        self._entry.delete(0, tk.END)
        place_col = self._custom_placeholder_color if self._custom_placeholder_color is not None else self._theme.placeholder
        self._entry.configure(fg=place_col, show="")
        self._entry.insert(0, self._placeholder)

    def _hide_placeholder(self) -> None:
        if self._placeholder_active:
            self._placeholder_active = False
            self._entry.delete(0, tk.END)
            text_col = self._custom_text_color if self._custom_text_color is not None else self._theme.text
            self._entry.configure(fg=text_col, show=self._show)

    def _on_focus_in(self, event) -> None:
        self._is_focused = True
        self._hide_placeholder()
        self.render()

    def _on_focus_out(self, event) -> None:
        self._is_focused = False
        if not self._entry.get():
            self._show_placeholder()
        self.render()

    def _on_map(self, event) -> None:
        new_parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, self._theme)
        if new_parent_bg != self._parent_bg:
            self._parent_bg = new_parent_bg
            try:
                super().configure(background=self._parent_bg)
                self._bg_label.configure(background=self._parent_bg)
            except Exception:
                pass
            self.render()

    def _on_theme_changed(self, new_theme: Theme) -> None:
        if self.winfo_exists():
            self._theme = new_theme
            self._parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, new_theme)
            try:
                super().configure(background=self._parent_bg)
                self._bg_label.configure(background=self._parent_bg)
            except Exception:
                pass

            bg_col = self._custom_bg_color if self._custom_bg_color is not None else new_theme.bg_input
            text_col = self._custom_text_color if self._custom_text_color is not None else new_theme.text
            place_col = self._custom_placeholder_color if self._custom_placeholder_color is not None else new_theme.placeholder

            self._entry.configure(
                bg=bg_col,
                fg=place_col if self._placeholder_active else text_col,
                insertbackground=new_theme.primary,
                selectbackground=new_theme.selection_bg,
                selectforeground=new_theme.selection_fg,
            )
            self.render()

    def _on_configure(self, event) -> None:
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        if new_w != self._widget_w or new_h != self._widget_h:
            self._widget_w = new_w
            self._widget_h = new_h
            self._photo.configure(width=self._widget_w, height=self._widget_h)
            self._surface.resize(self._widget_w, self._widget_h)
            font_size_val = self._custom_font_size if self._custom_font_size is not None else self._theme.font_size_md
            self._entry.place_configure(
                width=max(1, self._widget_w - 24),
                y=int((self._widget_h - font_size_val * 1.5) / 2),
            )
            self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        t = self._theme
        rx = self._custom_rx if self._custom_rx is not None else t.radius_sm
        bg_col = self._custom_bg_color if self._custom_bg_color is not None else t.bg_input
        border_col = self._custom_border_color if self._custom_border_color is not None else t.border
        focus_border_col = self._custom_focus_border_color if self._custom_focus_border_color is not None else t.border_focused

        pad = 3.0
        w = max(1.0, self._widget_w - pad * 2.0)
        h = max(1.0, self._widget_h - pad * 2.0)

        if self._is_error:
            b_col = t.danger
            border_w = 1.8
            shadow_col = t.danger
            shadow_blur = 6.0
        elif self._is_focused:
            b_col = focus_border_col
            border_w = 1.8
            shadow_col = t.primary
            shadow_blur = 6.0
        else:
            b_col = border_col
            border_w = 1.0
            shadow_col = "#00000000"
            shadow_blur = 0.0

        if self._is_focused or self._is_error:
            self._surface.draw_shadow(
                pad,
                pad,
                w,
                h,
                rx,
                rx,
                blur_radius=shadow_blur,
                offset_y=0.0,
                shadow_color=shadow_col if shadow_blur > 0 else "#00000000",
            )

        self._surface.fill_rounded_rect(pad, pad, w, h, rx, rx, bg_col)
        self._surface.stroke_rounded_rect(pad, pad, w, h, rx, rx, b_col, stroke_width=border_w)

        self._surface.blit(self._photo)


# ============================================================================
# ModernDropdown (OptionMenu / Combobox)
# ============================================================================

class ModernDropdown(tk.Frame):
    """
    Modern hybrid dropdown select widget with animated chevron, popup menu,
    and CustomTkinter CTkOptionMenu / CTkComboBox compatibility.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        options: Optional[List[str]] = None,
        values: Optional[List[str]] = None,
        selected_index: int = 0,
        on_select: Optional[Callable[[int, str], None]] = None,
        command: Optional[Callable[[str], None]] = None,
        width: int = 200,
        height: int = 40,
        rx: Optional[float] = None,
        corner_radius: Optional[float] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._theme = t
        self._custom_parent_bg = parent_bg
        self._parent_bg = _resolve_parent_bg(master, self._custom_parent_bg, self._theme)

        self._requested_w = max(1, width)
        self._requested_h = max(1, height)
        self._widget_w = max(1, ScalingTracker.scale(self._requested_w, master))
        self._widget_h = max(1, ScalingTracker.scale(self._requested_h, master))
        self._custom_rx = corner_radius if corner_radius is not None else rx

        super().__init__(
            master,
            width=self._widget_w,
            height=self._widget_h,
            background=self._parent_bg,
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )
        self.pack_propagate(False)

        self._dropdown_options = values or options or ["Option 1", "Option 2"]
        self._selected_index = max(0, min(len(self._dropdown_options) - 1, selected_index)) if self._dropdown_options else 0
        self._on_select = on_select
        self._command = command
        self._is_open = False
        self._is_hovered = False
        self._popup_window: Optional[tk.Toplevel] = None

        self._photo = tk.PhotoImage(master=self, width=self._widget_w, height=self._widget_h)
        self._surface = Surface(self._widget_w, self._widget_h)

        self._label = tk.Label(
            self,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            background=self._parent_bg,
        )
        self._label.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        self._label.bind("<ButtonRelease-1>", self._on_toggle_open)
        self._label.bind("<Enter>", lambda e: self._set_hovered(True))
        self._label.bind("<Leave>", lambda e: self._set_hovered(False))
        self.bind("<Configure>", self._on_configure)
        self.bind("<Map>", self._on_map)

        ThemeManager.subscribe(self._on_theme_changed)
        self.bind("<Destroy>", lambda e: ThemeManager.unsubscribe(self._on_theme_changed))

        self.after_idle(self.render)

    # ------------------------------------------------------------------------
    # Protocol: configure(), cget(), __getitem__, __setitem__
    # ------------------------------------------------------------------------

    def configure(self, **kwargs) -> Any:
        if not kwargs:
            return {
                "values": self._dropdown_options,
                "selected_index": self._selected_index,
                "selected_value": self.selected_value,
            }

        redraw = False
        if "options" in kwargs or "values" in kwargs:
            self._dropdown_options = kwargs.pop("options", None) or kwargs.pop("values", None) or []
            self._selected_index = max(0, min(len(self._dropdown_options) - 1, self._selected_index)) if self._dropdown_options else 0
            redraw = True
        if "selected_index" in kwargs:
            self._selected_index = max(0, min(len(self._dropdown_options) - 1, int(kwargs.pop("selected_index"))))
            redraw = True
        if "on_select" in kwargs:
            self._on_select = kwargs.pop("on_select")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "corner_radius" in kwargs or "rx" in kwargs:
            self._custom_rx = kwargs.pop("corner_radius", None) or kwargs.pop("rx", None)
            redraw = True

        if redraw and self.winfo_exists():
            self.render()

    def config(self, **kwargs) -> Any:
        return self.configure(**kwargs)

    def cget(self, key: str) -> Any:
        if key in ("options", "values"):
            return self._dropdown_options
        elif key == "selected_index":
            return self._selected_index
        elif key == "selected_value":
            return self.selected_value
        elif key in ("corner_radius", "rx"):
            return self._custom_rx
        return None

    def __getitem__(self, key: str) -> Any:
        return self.cget(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.configure(**{key: value})

    def get(self) -> str:
        return self.selected_value

    def set(self, value: str) -> None:
        if value in self._dropdown_options:
            self._selected_index = self._dropdown_options.index(value)
            self.render()

    @property
    def selected_value(self) -> str:
        if self._dropdown_options and 0 <= self._selected_index < len(self._dropdown_options):
            return self._dropdown_options[self._selected_index]
        return ""

    def _set_hovered(self, val: bool) -> None:
        self._is_hovered = val
        self.render()

    def _on_map(self, event) -> None:
        new_parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, self._theme)
        if new_parent_bg != self._parent_bg:
            self._parent_bg = new_parent_bg
            try:
                super().configure(background=self._parent_bg)
                self._label.configure(background=self._parent_bg)
            except Exception:
                pass
            self.render()

    def _on_theme_changed(self, new_theme: Theme) -> None:
        if self.winfo_exists():
            self._theme = new_theme
            self._parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, new_theme)
            try:
                super().configure(background=self._parent_bg)
                self._label.configure(background=self._parent_bg)
            except Exception:
                pass
            self.render()

    def _on_configure(self, event) -> None:
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        if new_w != self._widget_w or new_h != self._widget_h:
            self._widget_w = new_w
            self._widget_h = new_h
            self._photo.configure(width=self._widget_w, height=self._widget_h)
            self._surface.resize(self._widget_w, self._widget_h)
            self.render()

    def _on_toggle_open(self, event) -> None:
        if self._is_open:
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self) -> None:
        if not self._dropdown_options:
            return
        self._is_open = True
        self.render()

        self._popup_window = tk.Toplevel(self)
        self._popup_window.wm_overrideredirect(True)
        self._popup_window.wm_attributes("-topmost", True)
        self._popup_window.configure(background=self._theme.border)

        root_x = self.winfo_rootx()
        root_y = self.winfo_rooty() + self._widget_h + 4
        item_h = 32
        pop_h = min(240, len(self._dropdown_options) * item_h + 8)

        self._popup_window.geometry(f"{self._widget_w}x{pop_h}+{root_x}+{root_y}")

        list_frame = tk.Frame(self._popup_window, bg=self._theme.bg_card)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        for i, opt in enumerate(self._dropdown_options):
            lbl = tk.Label(
                list_frame,
                text=opt,
                font=(self._theme.font_family, int(self._theme.font_size_sm)),
                fg=self._theme.primary if i == self._selected_index else self._theme.text,
                bg=self._theme.bg_hover if i == self._selected_index else self._theme.bg_card,
                anchor="w",
                padx=12,
                pady=6,
            )
            lbl.pack(fill=tk.X)
            lbl.bind("<Button-1>", lambda e, idx=i: self._select_item(idx))
            lbl.bind("<Enter>", lambda e, l=lbl: l.configure(bg=self._theme.bg_hover))
            lbl.bind(
                "<Leave>",
                lambda e, l=lbl, idx=i: l.configure(
                    bg=self._theme.bg_hover if idx == self._selected_index else self._theme.bg_card
                ),
            )

        self._popup_window.bind("<FocusOut>", lambda e: self._close_popup())
        self._popup_window.bind("<Escape>", lambda e: self._close_popup())
        self._popup_window.focus_set()

    def _close_popup(self) -> None:
        self._is_open = False
        if self._popup_window and self._popup_window.winfo_exists():
            self._popup_window.destroy()
            self._popup_window = None
        self.render()

    def _select_item(self, idx: int) -> None:
        self._selected_index = idx
        self._close_popup()
        if 0 <= idx < len(self._dropdown_options):
            val = self._dropdown_options[idx]
            if self._on_select:
                self._on_select(idx, val)
            if self._command:
                self._command(val)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        t = self._theme
        rx = self._custom_rx if self._custom_rx is not None else t.radius_sm

        pad = 2.0
        w = max(1.0, self._widget_w - pad * 2.0)
        h = max(1.0, self._widget_h - pad * 2.0)

        bg = t.bg_hover if self._is_hovered else t.bg_input
        border_col = t.primary if self._is_open else t.border

        self._surface.fill_rounded_rect(pad, pad, w, h, rx, rx, bg)
        self._surface.stroke_rounded_rect(pad, pad, w, h, rx, rx, border_col, stroke_width=1.0)

        text_val = self.selected_value
        text_y = self._widget_h / 2.0 + (t.font_size_md * 0.35)
        self._surface.draw_text(
            text_val,
            x=12.0,
            y=text_y,
            font_size=t.font_size_md,
            font_family=t.font_family,
            color=t.text,
            align="left",
        )

        chev_cx = self._widget_w - 18.0
        chev_cy = self._widget_h / 2.0
        p = Path()
        if self._is_open:
            p.move_to(chev_cx - 4.0, chev_cy + 2.0)
            p.line_to(chev_cx, chev_cy - 2.0)
            p.line_to(chev_cx + 4.0, chev_cy + 2.0)
        else:
            p.move_to(chev_cx - 4.0, chev_cy - 2.0)
            p.line_to(chev_cx, chev_cy + 2.0)
            p.line_to(chev_cx + 4.0, chev_cy - 2.0)

        self._surface.stroke_path(p, t.text_muted, stroke_width=1.8)
        self._surface.blit(self._photo)
