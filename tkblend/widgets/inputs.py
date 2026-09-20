"""
Input widgets for tkblend: ModernEntry and ModernDropdown.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, List, Tuple, Any

from tkblend.surface import Surface, ColorLike, Path
from tkblend.widgets.theme import Theme, ThemeManager


class ModernEntry(tk.Frame):
    """
    Modern hybrid text entry widget with antialiased Blend2D border,
    focus ring glow, drop shadow, placeholder text, and embedded tk.Entry.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 40,
        placeholder: str = "",
        text: str = "",
        rx: Optional[float] = None,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        focus_border_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        placeholder_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        show: Optional[str] = None,
        is_password: bool = False,
        is_error: bool = False,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._theme = t
        self._widget_w = max(1, width)
        self._widget_h = max(1, height)
        self._rx = rx if rx is not None else t.radius_sm
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window
        self._bg_color = bg_color if bg_color is not None else t.bg_input
        self._border_color = border_color if border_color is not None else t.border
        self._focus_border_color = focus_border_color if focus_border_color is not None else t.border_focused
        self._text_color = text_color if text_color is not None else t.text
        self._placeholder_color = placeholder_color if placeholder_color is not None else t.placeholder
        self._font_size = font_size if font_size is not None else t.font_size_md
        self._font_family = font_family or t.font_family
        self._placeholder = placeholder
        self._is_focused = False
        self._is_error = is_error
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
        tk_font = (self._font_family, int(self._font_size))
        self._entry = tk.Entry(
            self,
            font=tk_font,
            fg=self._text_color,
            bg=self._bg_color,
            insertbackground=self._theme.primary,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            show=self._show,
        )
        self._entry.place(
            x=12,
            y=int((self._widget_h - self._font_size * 1.5) / 2),
            width=max(1, self._widget_w - 24),
            height=int(self._font_size * 1.5),
        )

        self._placeholder_active = False
        if text:
            self._entry.insert(0, text)
        elif self._placeholder:
            self._show_placeholder()

        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Configure>", self._on_configure)

        ThemeManager.subscribe(self._on_theme_changed)
        self.bind("<Destroy>", lambda e: ThemeManager.unsubscribe(self._on_theme_changed))

        self.after_idle(self.render)

    def _on_theme_changed(self, new_theme: Theme) -> None:
        if self.winfo_exists():
            self._theme = new_theme
            self._parent_bg = new_theme.bg_window
            self._bg_color = new_theme.bg_input
            self._border_color = new_theme.border
            self._focus_border_color = new_theme.border_focused
            self._text_color = new_theme.text
            self._placeholder_color = new_theme.placeholder
            self.configure(background=self._parent_bg)
            self._entry.configure(
                bg=self._bg_color,
                fg=self._placeholder_color if self._placeholder_active else self._text_color,
                insertbackground=new_theme.primary,
            )
            self.render()

    def _show_placeholder(self) -> None:
        self._placeholder_active = True
        self._entry.delete(0, tk.END)
        self._entry.insert(0, self._placeholder)
        self._entry.configure(fg=self._placeholder_color, show="")

    def _hide_placeholder(self) -> None:
        if self._placeholder_active:
            self._placeholder_active = False
            self._entry.delete(0, tk.END)
            self._entry.configure(fg=self._text_color, show=self._show)

    def _on_focus_in(self, event) -> None:
        self._is_focused = True
        if self._placeholder_active:
            self._hide_placeholder()
        self.render()

    def _on_focus_out(self, event) -> None:
        self._is_focused = False
        if not self._entry.get() and self._placeholder:
            self._show_placeholder()
        self.render()

    def _on_configure(self, event) -> None:
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        if new_w != self._widget_w or new_h != self._widget_h:
            self._widget_w = new_w
            self._widget_h = new_h
            self._photo.configure(width=self._widget_w, height=self._widget_h)
            self._surface.resize(self._widget_w, self._widget_h)
            self._entry.place_configure(
                x=12,
                y=int((self._widget_h - self._font_size * 1.5) / 2),
                width=max(1, self._widget_w - 24),
                height=int(self._font_size * 1.5),
            )
            self.render()

    def get(self) -> str:
        if self._placeholder_active:
            return ""
        return self._entry.get()

    def set_text(self, text: str) -> None:
        self._entry.delete(0, tk.END)
        if text:
            self._placeholder_active = False
            self._entry.configure(fg=self._text_color, show=self._show)
            self._entry.insert(0, text)
        elif self._placeholder and not self._is_focused:
            self._show_placeholder()

    @property
    def is_error(self) -> bool:
        return self._is_error

    @is_error.setter
    def is_error(self, val: bool) -> None:
        self._is_error = bool(val)
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        pad = 3.0
        w = max(1.0, self._widget_w - pad * 2.0)
        h = max(1.0, self._widget_h - pad * 2.0)

        # Border color based on focus / error state
        if self._is_error:
            b_col = self._theme.danger
            border_w = 1.8
            shadow_col = self._theme.danger
            shadow_blur = 6.0
        elif self._is_focused:
            b_col = self._focus_border_color
            border_w = 1.8
            shadow_col = self._theme.primary
            shadow_blur = 6.0
        else:
            b_col = self._border_color
            border_w = 1.0
            shadow_col = "#00000000"
            shadow_blur = 0.0

        # Draw card with focus glow shadow
        if self._is_focused or self._is_error:
            self._surface.draw_shadow(
                pad,
                pad,
                w,
                h,
                self._rx,
                self._rx,
                blur_radius=shadow_blur,
                offset_y=0.0,
                shadow_color=shadow_col if shadow_blur > 0 else "#00000000",
            )

        self._surface.fill_rounded_rect(pad, pad, w, h, self._rx, self._rx, self._bg_color)
        self._surface.stroke_rounded_rect(pad, pad, w, h, self._rx, self._rx, b_col, stroke_width=border_w)

        self._surface.blit(self._photo)


class ModernDropdown(tk.Frame):
    """
    Modern hybrid dropdown select widget with animated chevron and custom popup list.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        options: Optional[List[str]] = None,
        selected_index: int = 0,
        on_select: Optional[Callable[[int, str], None]] = None,
        width: int = 200,
        height: int = 40,
        rx: Optional[float] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        p_bg = parent_bg if parent_bg is not None else t.bg_window
        super().__init__(
            master,
            width=width,
            height=height,
            background=p_bg,
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )
        self.pack_propagate(False)

        self._theme = t
        self._dropdown_options = options or ["Option 1", "Option 2"]
        self._selected_index = max(0, min(len(self._dropdown_options) - 1, selected_index)) if self._dropdown_options else 0
        self._on_select = on_select
        self._widget_w = max(1, width)
        self._widget_h = max(1, height)
        self._rx = rx if rx is not None else t.radius_sm
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window
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

        ThemeManager.subscribe(self._on_theme_changed)
        self.bind("<Destroy>", lambda e: ThemeManager.unsubscribe(self._on_theme_changed))

        self.after_idle(self.render)

    def _set_hovered(self, val: bool) -> None:
        self._is_hovered = val
        self.render()

    def _on_theme_changed(self, new_theme: Theme) -> None:
        if self.winfo_exists():
            self._theme = new_theme
            self._parent_bg = new_theme.bg_window
            self.configure(background=self._parent_bg)
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

    @property
    def selected_value(self) -> str:
        if self._dropdown_options and 0 <= self._selected_index < len(self._dropdown_options):
            return self._dropdown_options[self._selected_index]
        return ""

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

        # Create floating toplevel popup
        self._popup_window = tk.Toplevel(self)
        self._popup_window.wm_overrideredirect(True)
        self._popup_window.wm_attributes("-topmost", True)
        self._popup_window.configure(background=self._theme.border)

        root_x = self.winfo_rootx()
        root_y = self.winfo_rooty() + self._widget_h + 4
        item_h = 32
        pop_h = min(240, len(self._dropdown_options) * item_h + 8)

        self._popup_window.geometry(f"{self._widget_w}x{pop_h}+{root_x}+{root_y}")

        # List frame
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
        if self._on_select and 0 <= idx < len(self._dropdown_options):
            self._on_select(idx, self._dropdown_options[idx])

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        pad = 2.0
        w = max(1.0, self._widget_w - pad * 2.0)
        h = max(1.0, self._widget_h - pad * 2.0)

        bg = self._theme.bg_hover if self._is_hovered else self._theme.bg_input
        border_col = self._theme.primary if self._is_open else self._theme.border

        self._surface.fill_rounded_rect(pad, pad, w, h, self._rx, self._rx, bg)
        self._surface.stroke_rounded_rect(pad, pad, w, h, self._rx, self._rx, border_col, stroke_width=1.0)

        # Draw selected text
        text_val = self.selected_value
        text_y = self._widget_h / 2.0 + (self._theme.font_size_md * 0.35)
        self._surface.draw_text(
            text_val,
            x=12.0,
            y=text_y,
            font_size=self._theme.font_size_md,
            font_family=self._theme.font_family,
            color=self._theme.text,
            align="left",
        )

        # Draw chevron arrow
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

        self._surface.stroke_path(p, self._theme.text_muted, stroke_width=1.8)
        self._surface.blit(self._photo)
