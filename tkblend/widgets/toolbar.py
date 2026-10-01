"""
High-performance pure vector Toolbar container and action bar for tkblend.
Zero TTK dependencies. Supports horizontal/vertical orientation, floating/docked/flat styles,
and fluent builders for buttons, toggles, vector separators, spacers, and custom widgets.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, List, Union, Any

from tkblend.surface import Surface, ColorLike
from tkblend.theme import get_theme, Palette, add_theme_listener, remove_theme_listener, resolve_ancestor_bg
from tkblend.widgets.base import Widget, ScalingTracker, cascade_bg_to_children
from tkblend.widgets.button import Button
from tkblend.widgets.selection import Switch, Checkbutton


class ToolbarSeparator(Widget):
    """Sleek vertical or horizontal vector divider line for toolbars."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        orientation: str = "vertical",
        length: int = 20,
        thickness: int = 1,
        color: Optional[ColorLike] = None,
        bg: Optional[str] = None,
        **kwargs,
    ):
        self._orientation = orientation.lower()
        self._explicit_color = color
        self._thickness = thickness
        s = ScalingTracker.get_scaling_factor(master)

        if self._orientation == "vertical":
            w = max(4, int(8 * s))
            h = max(1, int(length * s))
        else:
            w = max(1, int(length * s))
            h = max(4, int(8 * s))

        super().__init__(
            master=master,
            width=w,
            height=h,
            bg=bg,
            resizable_width=(self._orientation != "vertical"),
            resizable_height=(self._orientation == "vertical"),
            **kwargs,
        )

    def render(self) -> None:
        if self._surface is None:
            return

        w = float(self._widget_w)
        h = float(self._widget_h)
        s = self._scale
        pal = get_theme()

        self._surface.clear(self._parent_bg)
        sep_col = self._explicit_color or (pal.card_border if hasattr(pal, "card_border") else "#334155")

        if self._orientation == "vertical":
            cx = w / 2.0
            self._surface.draw_line(cx, 2.0 * s, cx, h - 2.0 * s, sep_col, stroke_width=float(self._thickness) * s)
        else:
            cy = h / 2.0
            self._surface.draw_line(2.0 * s, cy, w - 2.0 * s, cy, sep_col, stroke_width=float(self._thickness) * s)

        self.end_render()


class Toolbar(tk.Frame):
    """
    Vector Toolbar container supporting horizontal/vertical layout,
    floating/docked styles, and fluent item addition methods.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        orientation: str = "horizontal",  # 'horizontal' or 'vertical'
        style: str = "floating",  # 'floating', 'docked', 'flat'
        padding: int = 4,
        corner_radius: float = 8.0,
        bg_color: Optional[str] = None,
        **kwargs,
    ):
        self._orientation = orientation.lower()
        self._style = style.lower()
        self._padding = padding
        self._corner_radius = corner_radius
        self._explicit_bg = bg_color
        self._items: List[tk.Widget] = []

        pal = get_theme()
        eff_bg = self._resolve_bg(pal, master=master)

        super().__init__(
            master,
            bg=eff_bg,
            padx=int(padding * ScalingTracker.get_scaling_factor(master)),
            pady=int(padding * ScalingTracker.get_scaling_factor(master)),
            highlightthickness=0,
            borderwidth=0,
            **kwargs,
        )

        add_theme_listener(self._on_theme_changed)

    def _resolve_bg(self, pal: Palette, master: Optional[tk.Misc] = None) -> str:
        if self._explicit_bg:
            return self._explicit_bg
        if self._style in ("floating", "docked"):
            return pal.card_bg if hasattr(pal, "card_bg") else "#1e293b"
        else:  # flat
            target_master = master if master is not None else getattr(self, "master", None)
            return resolve_ancestor_bg(target_master, pal)

    @property
    def bg_color(self) -> str:
        """Expose inner background color for compound children propagation."""
        return self._resolve_bg(get_theme())

    def _on_theme_changed(self, pal: Palette) -> None:
        eff_bg = self._resolve_bg(pal)
        self.configure(bg=eff_bg)
        for item in self._items:
            if isinstance(item, tk.Frame) and not hasattr(item, "render"):
                try:
                    item.configure(bg=eff_bg)
                except Exception:
                    pass
        cascade_bg_to_children(self, eff_bg)

    def destroy(self) -> None:
        remove_theme_listener(self._on_theme_changed)
        super().destroy()

    # -------------------------------------------------------------------------
    # Fluent Item Builders
    # -------------------------------------------------------------------------

    def add_button(
        self,
        text: str = "",
        command: Optional[Callable[[], None]] = None,
        icon: Optional[str] = None,
        variant: str = "ghost",
        width: Optional[int] = None,
        height: int = 32,
        **kwargs,
    ) -> Button:
        """Add an action button to the toolbar."""
        display_text = f"{icon} {text}".strip() if icon else text
        calc_w = width if width is not None else max(36, len(display_text) * 9 + 20)
        btn = Button(
            self,
            text=display_text,
            command=command,
            variant=variant,
            width=calc_w,
            height=height,
            **kwargs,
        )
        self._pack_item(btn)
        return btn

    def add_toggle(
        self,
        text: str = "",
        command: Optional[Callable[[bool], None]] = None,
        variable: Optional[tk.BooleanVar] = None,
        initial: bool = False,
        variant: str = "outline",
        width: Optional[int] = None,
        height: int = 32,
        **kwargs,
    ) -> Button:
        """Add a stateful toggle button to the toolbar."""
        var = variable if variable is not None else tk.BooleanVar(value=initial)

        def on_toggle():
            new_val = not var.get()
            var.set(new_val)
            btn.variant = "primary" if new_val else variant
            if command:
                command(new_val)

        calc_w = width if width is not None else max(36, len(text) * 9 + 20)
        init_variant = "primary" if var.get() else variant
        btn = Button(
            self,
            text=text,
            command=on_toggle,
            variant=init_variant,
            width=calc_w,
            height=height,
            **kwargs,
        )
        btn._toggle_var = var  # type: ignore
        self._pack_item(btn)
        return btn

    def add_separator(self, length: int = 20) -> ToolbarSeparator:
        """Add a crisp vector divider line to the toolbar."""
        sep_orient = "vertical" if self._orientation == "horizontal" else "horizontal"
        sep = ToolbarSeparator(
            self,
            orientation=sep_orient,
            length=length,
        )
        self._pack_item(sep, padx=4)
        return sep

    def add_spacer(self) -> tk.Frame:
        """Add an expandable spring spacer to push items apart."""
        spacer = tk.Frame(self, bg=self.bg_color, width=1, height=1)
        if self._orientation == "horizontal":
            spacer.pack(side="left", fill="x", expand=True)
        else:
            spacer.pack(side="top", fill="y", expand=True)
        self._items.append(spacer)
        return spacer

    def add_widget(self, widget: tk.Widget, stretch: bool = False, **pack_kwargs) -> tk.Widget:
        """Add any custom widget (e.g. ColorWell, VolumeControl, Entry) to the toolbar."""
        self._pack_item(widget, stretch=stretch, **pack_kwargs)
        return widget

    def _pack_item(self, widget: tk.Widget, stretch: bool = False, **pack_kwargs) -> None:
        self._items.append(widget)
        if self._orientation == "horizontal":
            pack_kwargs.setdefault("side", "left")
            pack_kwargs.setdefault("padx", 2)
            pack_kwargs.setdefault("pady", 2)
            if stretch:
                pack_kwargs.setdefault("fill", "x")
                pack_kwargs.setdefault("expand", True)
        else:
            pack_kwargs.setdefault("side", "top")
            pack_kwargs.setdefault("padx", 2)
            pack_kwargs.setdefault("pady", 2)
            if stretch:
                pack_kwargs.setdefault("fill", "y")
                pack_kwargs.setdefault("expand", True)

        widget.pack(**pack_kwargs)

    def clear_items(self) -> None:
        """Remove and destroy all items in toolbar."""
        for item in self._items:
            item.destroy()
        self._items.clear()
