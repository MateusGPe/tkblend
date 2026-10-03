"""
Pure Blend2D Vector Entry and TextBox controls powered by BaseControl.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any, Union, Tuple

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    blend_color_hex,
    to_tk_hex,
    cascade_bg_to_children,
)
from tkblend.font import parse_font
from tkblend.widgets.constants import (
    DEFAULT_FONT_SIZE,
    CURSOR_IBEAM,
    CURSOR_DEFAULT,
)


class Entry(BaseControl):
    """
    Modern vector single-line text entry with glowing focus border,
    placeholder text, leading/trailing icon, and clean typography.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        placeholder: str = "",
        placeholder_text: Optional[str] = None,
        text: str = "",
        textvariable: Optional[tk.StringVar] = None,
        font: Optional[Any] = None,
        font_size: float = 11.0,
        fg_color: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        corner_radius: float = 6.0,
        icon: Optional[str] = None,
        show: Optional[str] = None,
        width: int = 220,
        height: int = 34,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._placeholder = placeholder_text if placeholder_text is not None else placeholder
        self._custom_fg = fg_color
        self._custom_bg = bg_color
        self._custom_border = border_color
        self._border_width = float(border_width)
        self._corner_radius = float(corner_radius)
        self._font_spec = font
        self._font_size = float(font_size)
        self._icon = icon
        self._is_focused = False

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or CURSOR_IBEAM,
            takefocus=False,
            **kwargs,
        )

        # Embedded native tk.Entry
        font_cfg = parse_font(font=self._font_spec, font_size=self._font_size)
        self._entry = tk.Entry(
            self,
            textvariable=textvariable,
            font=(font_cfg.family, int(self._font_size)),
            bd=0,
            highlightthickness=0,
            relief="flat",
            show=show,
        )
        if text:
            self._entry.insert(0, text)

        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<KeyRelease>", self._on_key_release)

        self._place_inner_entry()
        self._sync_colors()

    @property
    def bg_color(self) -> str:
        return resolve_color_failsafe(self._custom_bg or self._palette.input_bg, palette=self._palette)

    def _place_inner_entry(self) -> None:
        s = self._scale_factor
        pad_x = int((32.0 if self._icon else 12.0) * s)
        pad_y = int(6.0 * s)
        self._entry.place(
            x=pad_x,
            y=pad_y,
            relwidth=1.0,
            relheight=1.0,
            width=-pad_x - int(12.0 * s),
            height=-pad_y * 2,
        )

    def _on_focus_in(self, event) -> None:
        self._is_focused = True
        self.request_redraw()

    def _on_focus_out(self, event) -> None:
        self._is_focused = False
        self.request_redraw()

    def _on_key_release(self, event) -> None:
        self.request_redraw()

    def _sync_colors(self) -> None:
        pal = self._palette
        bg = resolve_color_failsafe(self._custom_bg or pal.input_bg, palette=pal)
        fg = resolve_color_failsafe(self._custom_fg or pal.fg, palette=pal)
        insert_bg = resolve_color_failsafe(pal.primary, palette=pal)
        self._entry.configure(
            background=to_tk_hex(bg),
            foreground=to_tk_hex(fg),
            insertbackground=to_tk_hex(insert_bg),
        )

    def on_theme_update(self, pal: Palette) -> None:
        self._sync_colors()

    def get(self) -> str:
        return self._entry.get()

    def insert(self, index, string: str) -> None:
        self._entry.insert(index, string)
        self.request_redraw()

    def delete(self, first, last=None) -> None:
        self._entry.delete(first, last)
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        cr = self._corner_radius * s
        bg_col = resolve_color_failsafe(self._custom_bg or pal.input_bg, palette=pal)
        border_col = resolve_color_failsafe(
            self._custom_border or (pal.primary if self._is_focused else pal.border),
            palette=pal,
        )

        # Clear parent background
        surf.clear(self._resolved_parent_bg)

        # Rounded background & border
        surf.fill_rounded_rect(0.0, 0.0, w, h, cr, cr, bg_col)
        bw = (2.0 if self._is_focused else self._border_width) * s
        if bw > 0.0:
            surf.stroke_rounded_rect(0.0, 0.0, w, h, cr, cr, border_col, stroke_width=bw)

        # Leading Icon
        if self._icon:
            icon_sz = 14.0 * s
            surf.draw_icon(
                self._icon,
                14.0 * s,
                h / 2.0 + 4.0 * s,
                size=icon_sz,
                color=pal.primary if self._is_focused else pal.text_muted,
                align="center",
            )

        # Placeholder text if entry is empty and not focused
        if not self._entry.get() and self._placeholder:
            font_cfg = parse_font(font=self._font_spec, font_size=self._font_size)
            font_sz = self._font_size * s
            start_x = (32.0 if self._icon else 12.0) * s
            text_y = h / 2.0 + font_sz * 0.35
            surf.draw_text(
                self._placeholder,
                start_x,
                text_y,
                font_size=font_sz,
                font_family=font_cfg.family,
                color=pal.text_muted,
                align="left",
            )


class SearchEntry(Entry):
    """Specialized Entry pre-configured with a search icon."""

    def __init__(self, master: Optional[tk.Misc] = None, placeholder: str = "Search...", **kwargs):
        super().__init__(master=master, placeholder=placeholder, icon="search", **kwargs)


class TextBox(BaseControl):
    """
    Modern multiline text area with rounded vector container,
    dynamic theming, and focus border.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 280,
        height: int = 140,
        font: Optional[Any] = None,
        font_size: float = 11.0,
        fg_color: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        corner_radius: float = 8.0,
        wrap: str = "word",
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._custom_fg = fg_color
        self._custom_bg = bg_color
        self._custom_border = border_color
        self._border_width = float(border_width)
        self._corner_radius = float(corner_radius)
        self._font_spec = font
        self._font_size = float(font_size)
        self._is_focused = False

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=False,
            **kwargs,
        )

        font_cfg = parse_font(font=self._font_spec, font_size=self._font_size)
        self._text_widget = tk.Text(
            self,
            font=(font_cfg.family, int(self._font_size)),
            bd=0,
            highlightthickness=0,
            relief="flat",
            wrap=wrap,
        )

        self._text_widget.bind("<FocusIn>", self._on_focus_in)
        self._text_widget.bind("<FocusOut>", self._on_focus_out)

        self._place_inner_text()
        self._sync_colors()

    @property
    def bg_color(self) -> str:
        return resolve_color_failsafe(self._custom_bg or self._palette.input_bg, palette=self._palette)

    def _place_inner_text(self) -> None:
        s = self._scale_factor
        pad = int(8.0 * s)
        self._text_widget.place(
            x=pad,
            y=pad,
            relwidth=1.0,
            relheight=1.0,
            width=-pad * 2,
            height=-pad * 2,
        )

    def _on_focus_in(self, event) -> None:
        self._is_focused = True
        self.request_redraw()

    def _on_focus_out(self, event) -> None:
        self._is_focused = False
        self.request_redraw()

    def _sync_colors(self) -> None:
        pal = self._palette
        bg = resolve_color_failsafe(self._custom_bg or pal.input_bg, palette=pal)
        fg = resolve_color_failsafe(self._custom_fg or pal.fg, palette=pal)
        insert_bg = resolve_color_failsafe(pal.primary, palette=pal)
        self._text_widget.configure(
            background=to_tk_hex(bg),
            foreground=to_tk_hex(fg),
            insertbackground=to_tk_hex(insert_bg),
        )

    def on_theme_update(self, pal: Palette) -> None:
        self._sync_colors()

    def get(self, index1="1.0", index2="end-1c") -> str:
        return self._text_widget.get(index1, index2)

    def insert(self, index, chars: str, *args) -> None:
        self._text_widget.insert(index, chars, *args)

    def delete(self, index1, index2=None) -> None:
        self._text_widget.delete(index1, index2)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        cr = self._corner_radius * s
        bg_col = resolve_color_failsafe(self._custom_bg or pal.input_bg, palette=pal)
        border_col = resolve_color_failsafe(
            self._custom_border or (pal.primary if self._is_focused else pal.border),
            palette=pal,
        )

        surf.clear(self._resolved_parent_bg)
        surf.fill_rounded_rect(0.0, 0.0, w, h, cr, cr, bg_col)
        bw = (2.0 if self._is_focused else self._border_width) * s
        if bw > 0.0:
            surf.stroke_rounded_rect(0.0, 0.0, w, h, cr, cr, border_col, stroke_width=bw)


# Aliases
Text = TextBox
