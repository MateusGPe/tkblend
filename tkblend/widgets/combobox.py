"""
ComboBox and OptionMenu widgets with pure Blend2D vector styling.
"""

from __future__ import annotations
import logging
import sys
import tkinter as tk
from typing import Optional, Callable, List, Union, Any

from tkblend.surface import ColorLike
from tkblend.theme import (
    get_theme,
    Palette,
    add_theme_listener,
    remove_theme_listener,
    blend_color_hex,
)
from tkblend.widgets.base import Widget, ScalingTracker, VariableSyncMixin
from tkblend.widgets.dropdown import Dropdown, DropdownItem
from tkblend.widgets.drawing import draw_vector_chevron, truncate_text

logger = logging.getLogger(__name__)


class OptionMenu(Widget, VariableSyncMixin):
    """
    Modern OptionMenu selector widget: A button displaying the active selection
    with a vector dropdown chevron and a floating Blend2D popup menu.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        values: Optional[List[str]] = None,
        selected_value: Optional[str] = None,
        command: Optional[Callable[[str], None]] = None,
        variable: Optional[Any] = None,
        width: Optional[int] = None,
        height: int = 34,
        rx: float = 8.0,
        ry: float = 8.0,
        bg_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        elevation: float = 2.0,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._values = list(values) if values else ["Option 1", "Option 2"]
        default_val = selected_value or (self._values[0] if self._values else "")
        self._selected = self._init_variable_sync(
            variable=variable,
            initial_value=default_val,
            on_variable_change=self._on_var_changed,
            type_caster=str,
        )
        self._command = command
        self._rx = rx
        self._ry = ry
        self._explicit_bg_color = bg_color
        self._explicit_text_color = text_color
        self._explicit_border_color = border_color
        self._border_width = border_width
        self._elevation = elevation
        self._is_open = False
        self._popup: Optional[tk.Toplevel] = None
        self._root_bind_id: Optional[str] = None
        self._root_cfg_bind_id: Optional[str] = None

        if width is None:
            max_len = max((len(str(v)) for v in self._values), default=10)
            width = max(110, int(max_len * 9 + 44))

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            **kwargs,
        )

        self.bind("<ButtonRelease-1>", self._on_click)

    def _on_var_changed(self, new_val: str) -> None:
        if new_val != self._selected:
            self._selected = new_val
            self.render()

    def set(self, value: str) -> None:
        """Set the active selected value."""
        self._selected = str(value)
        self._set_synced_value(self._selected)
        self.render()

    def get(self) -> str:
        """Return the current selected value."""
        return self._selected

    def destroy(self) -> None:
        self._cleanup_variable_sync()
        super().destroy()

    def configure_values(self, values: List[str]) -> None:
        """Update the available options."""
        self._values = list(values)
        if self._selected not in self._values and self._values:
            self.set(self._values[0])
        else:
            self.render()

    def _on_click(self, event) -> None:
        if self._is_disabled:
            return
        self._toggle_popup()

    def _toggle_popup(self) -> None:
        if self._is_open and self._popup and self._popup.winfo_exists():
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self) -> None:
        if not self._values:
            return
        self._is_open = True
        self.render()

        root = self.winfo_toplevel()
        popup = tk.Toplevel(self)
        popup.withdraw()
        popup.overrideredirect(True)
        try:
            popup.transient(root)
        except Exception as e:
            logger.debug("Failed setting transient root for OptionMenu popup: %s", e)
        try:
            popup.attributes("-topmost", True)
        except Exception as e:
            logger.debug("Failed setting topmost attribute for OptionMenu popup: %s", e)
        self._popup = popup

        self.update_idletasks()
        rx = self.winfo_rootx()
        ry = self.winfo_rooty()
        rw = self.winfo_width()
        rh = self.winfo_height()
        s = self._scale
        pw = max(rw, int(140 * s))

        pal = get_theme()
        popup.configure(background=pal.card_border)

        # Popup frame container
        frame = tk.Frame(popup, background=pal.card_bg, highlightthickness=1, highlightbackground=pal.card_border)
        frame.pack(fill="both", expand=True)

        for val in self._values:
            item = DropdownItem(
                frame,
                text=val,
                is_selected=(val == self._selected),
                on_select=lambda v=val: self._on_item_selected(v),
                width=int(pw / s),
                height=30,
                parent_bg=pal.card_bg,
            )
            item.pack(fill="x", padx=2, pady=1)

        popup.update_idletasks()
        ph = popup.winfo_reqheight()

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        space_below = screen_h - (ry + rh + 4)

        if space_below < ph and ry > ph:
            pop_y = max(0, ry - ph - 4)
        else:
            pop_y = ry + rh + 4

        if pop_y + ph > screen_h:
            pop_y = max(0, screen_h - ph - 4)

        pop_x = max(0, rx)
        if pop_x + pw > screen_w:
            pop_x = max(0, screen_w - pw - 4)

        popup.geometry(f"{pw}x{ph}+{pop_x}+{pop_y}")
        popup.deiconify()
        popup.lift()

        # Auto-close hooks
        def on_global_click(e):
            if popup.winfo_exists():
                try:
                    px, py = popup.winfo_rootx(), popup.winfo_rooty()
                    pw_val, ph_val = popup.winfo_width(), popup.winfo_height()
                    if px <= e.x_root <= px + pw_val and py <= e.y_root <= py + ph_val:
                        return
                    sx, sy = self.winfo_rootx(), self.winfo_rooty()
                    sw, sh = self.winfo_width(), self.winfo_height()
                    if sx <= e.x_root <= sx + sw and sy <= e.y_root <= sy + sh:
                        return
                except Exception as e:
                    logger.debug("Failed checking coordinates in OptionMenu on_global_click: %s", e)
                self._close_popup()

        def on_root_configure(e):
            if self._is_open and e.widget == root:
                self._close_popup()

        self._root_bind_id = root.bind("<ButtonPress-1>", on_global_click, add="+")
        self._root_cfg_bind_id = root.bind("<Configure>", on_root_configure, add="+")

    def _close_popup(self) -> None:
        self._is_open = False
        if self._root_bind_id:
            try:
                self.winfo_toplevel().unbind("<ButtonPress-1>", self._root_bind_id)
            except Exception as e:
                logger.debug("Failed unbinding global click in OptionMenu: %s", e)
            self._root_bind_id = None
        if self._root_cfg_bind_id:
            try:
                self.winfo_toplevel().unbind("<Configure>", self._root_cfg_bind_id)
            except Exception as e:
                logger.debug("Failed unbinding root configure in OptionMenu: %s", e)
            self._root_cfg_bind_id = None
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
            self._popup = None
        self.render()

    def _on_item_selected(self, val: str) -> None:
        self._close_popup()
        self.set(val)
        if self._command:
            try:
                self._command(val)
            except TypeError:
                self._command()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            pad = 2.0 * s
            w = max(1.0, self._widget_w - pad * 2.0)
            h = max(1.0, self._widget_h - pad * 2.0)
            r = min(self._rx * s, h / 2.0)

            pal = get_theme()
            bg_col = self._explicit_bg_color or (pal.button_hover if self._is_hovered else pal.surface)
            txt_col = self._explicit_text_color or pal.fg
            brd_col = self._explicit_border_color or (pal.primary if self._is_open or self._is_hovered else pal.surface_border)

            # Drop shadow if elevated
            if self._elevation > 0:
                safe_blur = min(self._elevation * s, pad * 0.8)
                self._surface.draw_shadow(pad, pad, w, h, r, r, blur_radius=safe_blur, shadow_color=pal.shadow_color)

            # Button background & border
            self._surface.fill_rounded_rect(pad, pad, w, h, r, r, bg_col)
            if self._border_width > 0:
                self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, brd_col, self._border_width * s)

            # Text
            font_sz = max(9.0, 12.0 * s)
            text_x = pad + 12.0 * s
            text_y = pad + h / 2.0 + (font_sz * 0.35)
            max_txt_w = w - 34.0 * s
            display_text = truncate_text(self._selected, max_txt_w, font_sz)
            self._surface.draw_text(display_text, text_x, text_y, font_size=font_sz, font_family="sans-serif", color=txt_col, align="left")

            # Chevron
            chev_x = pad + w - 16.0 * s
            chev_y = pad + h / 2.0
            chev_dir = "up" if self._is_open else "down"
            draw_vector_chevron(self._surface, chev_x, chev_y, scale=1.0 * s, direction=chev_dir, color=pal.secondary_fg, stroke_width=1.8 * s)

            self._surface.blit(self._photo)
        except Exception as e:
            logger.debug("Render failed in OptionMenu: %s", e, exc_info=True)


class Combobox(tk.Frame):
    """
    Modern ComboBox widget: Single-line editable text input paired with
    a Blend2D vector dropdown button and popup list.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        values: Optional[List[str]] = None,
        command: Optional[Callable[[str], None]] = None,
        variable: Optional[Any] = None,
        width: int = 180,
        height: int = 34,
        rx: float = 8.0,
        ry: float = 8.0,
        bg_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        state: str = "normal",  # "normal" or "readonly"
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._scale = ScalingTracker.get_scaling_factor(master)
        pal = get_theme()
        self._explicit_parent_bg = parent_bg
        self._parent_bg = parent_bg or Widget._resolve_default_bg(master, pal)
        self._values = list(values) if values else []
        self._command = command
        self._variable = variable
        self._rx = rx
        self._ry = ry
        self._bg_color = bg_color
        self._text_color = text_color
        self._border_color = border_color
        self._border_width = border_width
        self._state = state
        self._is_open = False
        self._popup: Optional[tk.Toplevel] = None
        self._root_bind_id: Optional[str] = None
        self._root_cfg_bind_id: Optional[str] = None

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

        # Card container with crisp border
        self._card = tk.Frame(
            self,
            background=pal.input_bg,
            highlightthickness=1,
            highlightbackground=pal.input_border,
            highlightcolor=pal.primary,
        )
        self._card.pack(fill="both", expand=True)

        # Inner text entry
        font_sz = max(9, int(11 * self._scale))
        self._entry = tk.Entry(
            self._card,
            background=pal.input_bg,
            foreground=pal.fg,
            font=("sans-serif", font_sz),
            borderwidth=0,
            highlightthickness=0,
            insertbackground=pal.primary,
            textvariable=self._variable,
            state="readonly" if self._state == "readonly" else "normal",
        )
        self._entry.pack(side="left", fill="both", expand=True, padx=(10, 2), pady=4)

        # Dropdown arrow button
        self._btn = Widget(
            self._card,
            width=28,
            height=30,
            bg=pal.input_bg,
        )
        self._btn.render = self._render_button
        self._btn.bind("<ButtonRelease-1>", self._on_btn_click)
        self._btn.pack(side="right", fill="y", padx=(0, 2), pady=2)

        if self._values and not self.get():
            self.set(self._values[0])

        add_theme_listener(self._on_theme_changed)
        self.bind("<Destroy>", self._on_destroy, add="+")

    def _render_button(self) -> None:
        if self._btn._widget_w <= 1 or self._btn._widget_h <= 1:
            return
        try:
            pal = get_theme()
            self._btn._surface.clear(pal.input_bg)
            s = self._btn._scale
            w = float(self._btn._widget_w)
            h = float(self._btn._widget_h)

            # Hover highlight
            if self._btn._is_hovered:
                self._btn._surface.fill_rounded_rect(2.0, 2.0, w - 4.0, h - 4.0, 4.0 * s, 4.0 * s, pal.secondary)

            chev_dir = "up" if self._is_open else "down"
            draw_vector_chevron(
                self._btn._surface,
                w / 2.0,
                h / 2.0,
                scale=1.0 * s,
                direction=chev_dir,
                color=pal.fg,
                stroke_width=1.6 * s,
            )
            self._btn._surface.blit(self._btn._photo)
        except Exception as e:
            logger.debug("Render failed in ComboBox button: %s", e, exc_info=True)

    def _on_btn_click(self, event) -> None:
        if self._is_open:
            self._close_popup()
        else:
            self._open_popup()

    def _open_popup(self) -> None:
        if not self._values:
            return
        self._is_open = True
        self._btn.render()

        root = self.winfo_toplevel()
        popup = tk.Toplevel(self)
        popup.withdraw()
        popup.overrideredirect(True)
        try:
            popup.transient(root)
        except Exception as e:
            logger.debug("Failed setting transient root for ComboBox popup: %s", e)
        try:
            popup.attributes("-topmost", True)
        except Exception as e:
            logger.debug("Failed setting topmost attribute for ComboBox popup: %s", e)
        self._popup = popup

        self.update_idletasks()
        rx = self.winfo_rootx()
        ry = self.winfo_rooty()
        rw = self.winfo_width()
        rh = self.winfo_height()
        s = self._scale
        pw = max(rw, int(140 * s))

        pal = get_theme()
        popup.configure(background=pal.card_border)

        frame = tk.Frame(popup, background=pal.card_bg, highlightthickness=1, highlightbackground=pal.card_border)
        frame.pack(fill="both", expand=True)

        for val in self._values:
            item = DropdownItem(
                frame,
                text=val,
                is_selected=(val == self.get()),
                on_select=lambda v=val: self._on_item_selected(v),
                width=int(pw / s),
                height=28,
                parent_bg=pal.card_bg,
            )
            item.pack(fill="x", padx=2, pady=1)

        popup.update_idletasks()
        ph = popup.winfo_reqheight()

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        space_below = screen_h - (ry + rh + 2)

        if space_below < ph and ry > ph:
            pop_y = max(0, ry - ph - 2)
        else:
            pop_y = ry + rh + 2

        if pop_y + ph > screen_h:
            pop_y = max(0, screen_h - ph - 4)

        pop_x = max(0, rx)
        if pop_x + pw > screen_w:
            pop_x = max(0, screen_w - pw - 4)

        popup.geometry(f"{pw}x{ph}+{pop_x}+{pop_y}")
        popup.deiconify()
        popup.lift()

        def on_global_click(e):
            if popup.winfo_exists():
                try:
                    px, py = popup.winfo_rootx(), popup.winfo_rooty()
                    pw_val, ph_val = popup.winfo_width(), popup.winfo_height()
                    if px <= e.x_root <= px + pw_val and py <= e.y_root <= py + ph_val:
                        return
                    sx, sy = self.winfo_rootx(), self.winfo_rooty()
                    sw, sh = self.winfo_width(), self.winfo_height()
                    if sx <= e.x_root <= sx + sw and sy <= e.y_root <= sy + sh:
                        return
                except Exception as e:
                    logger.debug("Failed checking coordinates in ComboBox on_global_click: %s", e)
                self._close_popup()

        def on_root_configure(e):
            if self._is_open and e.widget == root:
                self._close_popup()

        self._root_bind_id = root.bind("<ButtonPress-1>", on_global_click, add="+")
        self._root_cfg_bind_id = root.bind("<Configure>", on_root_configure, add="+")

    def _close_popup(self) -> None:
        self._is_open = False
        if self._root_bind_id:
            try:
                self.winfo_toplevel().unbind("<ButtonPress-1>", self._root_bind_id)
            except Exception as e:
                logger.debug("Failed unbinding global click in ComboBox: %s", e)
            self._root_bind_id = None
        if self._root_cfg_bind_id:
            try:
                self.winfo_toplevel().unbind("<Configure>", self._root_cfg_bind_id)
            except Exception as e:
                logger.debug("Failed unbinding root configure in ComboBox: %s", e)
            self._root_cfg_bind_id = None
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
            self._popup = None
        self._btn.render()

    def _on_item_selected(self, val: str) -> None:
        self._close_popup()
        self.set(val)
        if self._command:
            try:
                self._command(val)
            except TypeError:
                self._command()

    def set(self, value: str) -> None:
        """Set the current text in the entry."""
        if self._state == "readonly":
            self._entry.configure(state="normal")
            self._entry.delete(0, "end")
            self._entry.insert(0, str(value))
            self._entry.configure(state="readonly")
        else:
            self._entry.delete(0, "end")
            self._entry.insert(0, str(value))

    def get(self) -> str:
        """Get the current text."""
        return self._entry.get()

    def configure_values(self, values: List[str]) -> None:
        self._values = list(values)

    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        resolved_bg = self._explicit_parent_bg or Widget._resolve_default_bg(self.master, palette)
        self._parent_bg = resolved_bg
        self.configure(background=self._parent_bg)
        self._card.configure(
            background=palette.input_bg,
            highlightbackground=palette.input_border,
            highlightcolor=palette.primary,
        )
        self._entry.configure(
            background=palette.input_bg,
            foreground=palette.fg,
            insertbackground=palette.primary,
            selectbackground=palette.primary,
            selectforeground=palette.primary_fg,
        )
        self._btn.set_parent_bg(palette.input_bg)

    def _on_destroy(self, event) -> None:
        if event.widget == self:
            remove_theme_listener(self._on_theme_changed)




ComboBox = Combobox
