"""
TextBox - Modern multiline text editor widget with pure Blend2D vector styling.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Union, Tuple, Any

from tkblend.surface import ColorLike
from tkblend.theme import (
    get_theme,
    Palette,
    add_theme_listener,
    remove_theme_listener,
    resolve_color_failsafe,
    to_tk_hex,
)
from tkblend.widgets.base import Widget, ScalingTracker
from tkblend.widgets.containers import Frame
from tkblend.widgets.scrollbar import VectorScrollbar


class Text(tk.Frame):
    """
    Modern multiline text editor widget featuring Blend2D rounded vector borders,
    elevation drop shadow, integrated vector scrollbar, placeholder support,
    and dynamic theme adaptation.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 260,
        height: int = 140,
        rx: float = 8.0,
        ry: float = 8.0,
        bg_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        elevation: float = 2.0,
        font: Optional[Union[str, Tuple[str, int], Tuple[str, int, str]]] = None,
        placeholder_text: Optional[str] = None,
        placeholder_color: Optional[ColorLike] = None,
        wrap: str = "word",
        scrollbar_width: int = 8,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._scale = ScalingTracker.get_scaling_factor(master)
        pal = get_theme()
        self._explicit_parent_bg = parent_bg
        self._parent_bg = parent_bg or Widget._resolve_default_bg(master, pal)
        self._rx = rx
        self._ry = ry
        self._bg_color = bg_color
        self._explicit_text_color = text_color
        self._explicit_placeholder_color = placeholder_color
        self._border_color = border_color
        self._border_width = border_width
        self._elevation = elevation
        self._placeholder_text = placeholder_text
        self._is_showing_placeholder = False

        font_size = max(9, int(11 * self._scale))
        self._font = font or ("sans-serif", font_size)

        super().__init__(
            master,
            width=max(1, int(width * self._scale)),
            height=max(1, int(height * self._scale)),
            background=self._parent_bg,
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        # Card container
        self._card = Frame(
            self,
            rx=self._rx,
            ry=self._ry,
            bg_color=self._bg_color or pal.input_bg,
            border_color=self._border_color or pal.input_border,
            border_width=self._border_width,
            elevation=self._elevation,
            parent_bg=self._parent_bg,
        )
        self._card.pack(fill="both", expand=True)

        inner_bg = self._card.bg_color
        txt_fg = self._explicit_text_color or pal.fg

        # Underpinning Tkinter Text
        self._text = tk.Text(
            self._card,
            background=to_tk_hex(inner_bg),
            foreground=to_tk_hex(txt_fg),
            font=self._font,
            wrap=wrap,
            borderwidth=0,
            highlightthickness=0,
            insertbackground=to_tk_hex(pal.primary),
            selectbackground=to_tk_hex(pal.primary),
            selectforeground=to_tk_hex(pal.primary_fg),
        )

        # Vector Scrollbar
        self._scrollbar = VectorScrollbar(
            self._card,
            command=self._text.yview,
            orientation="vertical",
            width=scrollbar_width,
            parent_bg=inner_bg,
        )
        self._text.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)
        self._text.pack(side="left", fill="both", expand=True, padx=(8, 4), pady=6)

        # Placeholder bindings
        if self._placeholder_text:
            self._show_placeholder()
            self._text.bind("<FocusIn>", self._on_focus_in, add="+")
            self._text.bind("<FocusOut>", self._on_focus_out, add="+")

        add_theme_listener(self._on_theme_changed)
        self.bind("<Destroy>", self._on_destroy, add="+")

    @property
    def bg_color(self) -> str:
        """Return the current interior background color."""
        return self._card.bg_color

    @property
    def text_widget(self) -> tk.Text:
        """Direct reference to underlying tk.Text."""
        return self._text

    def _show_placeholder(self) -> None:
        if not self.get("1.0", "end-1c"):
            self._is_showing_placeholder = True
            pal = get_theme()
            ph_col = self._explicit_placeholder_color or pal.secondary_fg
            self._text.insert("1.0", self._placeholder_text or "")
            self._text.configure(foreground=ph_col)

    def _clear_placeholder(self) -> None:
        if self._is_showing_placeholder:
            self._is_showing_placeholder = False
            self._text.delete("1.0", "end")
            pal = get_theme()
            txt_fg = self._explicit_text_color or pal.fg
            self._text.configure(foreground=txt_fg)

    def _on_focus_in(self, event) -> None:
        if self._is_showing_placeholder:
            self._clear_placeholder()

    def _on_focus_out(self, event) -> None:
        if not self.get("1.0", "end-1c"):
            self._show_placeholder()

    def insert(self, index: str, chars: str, *args) -> None:
        if self._is_showing_placeholder:
            self._clear_placeholder()
        self._text.insert(index, chars, *args)

    def get(self, index1: str = "1.0", index2: str = "end-1c") -> str:
        if self._is_showing_placeholder:
            return ""
        return self._text.get(index1, index2)

    def delete(self, index1: str = "1.0", index2: str = "end") -> None:
        self._text.delete(index1, index2)
        if self._placeholder_text and not self._text.focus_get() == self._text:
            self._show_placeholder()

    def clear(self) -> None:
        self.delete("1.0", "end")

    def set_text(self, text: str) -> None:
        self.delete("1.0", "end")
        self.insert("1.0", text)

    def see(self, index: str) -> None:
        self._text.see(index)

    def tag_config(self, tagName: str, **kwargs) -> Any:
        return self._text.tag_config(tagName, **kwargs)

    def tag_add(self, tagName: str, index1: str, *args) -> None:
        self._text.tag_add(tagName, index1, *args)

    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        resolved_bg = self._explicit_parent_bg or Widget._resolve_default_bg(self.master, palette)
        self._parent_bg = resolved_bg
        self.configure(background=self._parent_bg)

        if self._bg_color is None:
            self._card._bg_color = palette.input_bg
        if self._border_color is None:
            self._card._border_color = palette.input_border
        self._card.set_parent_bg(self._parent_bg)
        self._card.render()

        inner_bg = self._card.bg_color
        txt_fg = self._explicit_text_color or palette.fg
        self._text.configure(
            background=to_tk_hex(inner_bg),
            foreground=to_tk_hex(palette.secondary_fg if self._is_showing_placeholder else txt_fg),
            insertbackground=to_tk_hex(palette.primary),
            selectbackground=to_tk_hex(palette.primary),
            selectforeground=to_tk_hex(palette.primary_fg),
        )
        self._scrollbar.set_parent_bg(inner_bg)

    def render(self) -> None:
        """Render container card and vector scrollbar."""
        if hasattr(self, "_card") and self._card is not None:
            self._card.render()
        if hasattr(self, "_scrollbar") and self._scrollbar is not None:
            self._scrollbar.render()

    def _on_destroy(self, event) -> None:
        if event.widget == self:
            remove_theme_listener(self._on_theme_changed)


TextBox = Text

