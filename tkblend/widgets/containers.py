"""
Modern container widgets: Frame, Card, and Accordion with Blend2D vector styling.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional

from tkblend.surface import Surface, ColorLike, Path
from tkblend.theme import (
    get_theme,
    Palette,
    add_theme_listener,
    remove_theme_listener,
    resolve_color_failsafe,
)
from tkblend.widgets.base import Widget, ScalingTracker, cascade_bg_to_children
from tkblend.widgets.drawing import draw_vector_chevron


class Frame(tk.Frame):
    """
    Modern container with dynamic corner radius, customizable border,
    and soft elevation drop shadow.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 200,
        height: int = 150,
        rx: float = 16.0,
        ry: float = 16.0,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        elevation: float = 8.0,
        shadow_color: Optional[ColorLike] = None,
        shadow_offset_y: float = 4.0,
        padding: Optional[float] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._scale = ScalingTracker.get_scaling_factor(master)
        pal = get_theme()
        self._explicit_parent_bg = parent_bg
        self._parent_bg = parent_bg or Widget._resolve_default_bg(master, pal)
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

        self._widget_w = max(1, int(width * self._scale))
        self._widget_h = max(1, int(height * self._scale))
        self._rx = rx * self._scale
        self._ry = ry * self._scale
        self._explicit_bg_color = bg_color
        self._explicit_border_color = border_color
        self._explicit_shadow_color = shadow_color
        self._bg_color = bg_color or pal.card_bg
        self._border_color = border_color or pal.card_border
        self._border_width = max(1.0, border_width * self._scale)
        self._elevation = elevation * self._scale
        self._shadow_color = shadow_color or pal.shadow_color
        self._shadow_offset_y = shadow_offset_y * self._scale
        self._explicit_padding = padding
        self._padding = (padding * self._scale) if padding is not None else None
        self._current_pad = 0.0

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

        self.bind("<Configure>", self._on_configure)
        self.bind("<Destroy>", self._on_destroy)
        add_theme_listener(self._on_theme_changed)
        self.after_idle(self.render)

    def _on_destroy(self, event) -> None:
        remove_theme_listener(self._on_theme_changed)

    def set_parent_bg(self, bg: str, force: bool = False) -> None:
        """Update parent background and re-render container."""
        self._parent_bg = resolve_color_failsafe(bg, master=self, fallback=self._parent_bg)
        if force:
            self._explicit_parent_bg = None
        try:
            self.configure(background=self._parent_bg)
            if hasattr(self, "_bg_label") and self._bg_label.winfo_exists():
                self._bg_label.configure(background=self._parent_bg)
        except Exception:
            pass
        self.render()

    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        if self._explicit_parent_bg is None:
            self._parent_bg = Widget._resolve_default_bg(getattr(self, "master", None), palette)
        if self._explicit_bg_color is None:
            self._bg_color = palette.card_bg
        if self._explicit_border_color is None:
            self._border_color = palette.card_border
        if self._explicit_shadow_color is None:
            self._shadow_color = palette.shadow_color

        try:
            self.configure(background=self._parent_bg)
            if hasattr(self, "_bg_label") and self._bg_label.winfo_exists():
                self._bg_label.configure(background=self._parent_bg)
        except Exception:
            pass
        self.render()
        cascade_bg_to_children(self, str(self._bg_color))

    def _on_configure(self, event) -> None:
        if event.width <= 1 or event.height <= 1:
            return
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        if new_w != self._widget_w or new_h != self._widget_h:
            self._widget_w = new_w
            self._widget_h = new_h
            self._photo.configure(width=self._widget_w, height=self._widget_h)
            self._surface.resize(self._widget_w, self._widget_h)
            self.render()

    def set_background(self, bg_color: ColorLike, force: bool = False) -> None:
        resolved = resolve_color_failsafe(bg_color, master=self, fallback=str(self._bg_color))
        self._bg_color = resolved
        if force:
            self._explicit_bg_color = None
        self.render()
        cascade_bg_to_children(self, str(self._bg_color))

    @property
    def padding(self) -> float:
        if self._explicit_padding is not None:
            return float(self._explicit_padding)
        return float(self._current_pad / self._scale) if self._scale > 0 else 0.0

    @padding.setter
    def padding(self, value: Optional[float]) -> None:
        self._explicit_padding = value
        self._padding = (value * self._scale) if value is not None else None
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        if self._padding is not None:
            pad = max(0.0, self._padding)
        else:
            pad = max(8.0 * self._scale, self._elevation * 0.8)
        self._current_pad = pad
        draw_x = pad
        draw_y = pad
        draw_w = max(1.0, self._widget_w - pad * 2.0)
        draw_h = max(1.0, self._widget_h - pad * 2.0)

        if self._elevation > 0.0 and pad > 0.0:
            max_blur = pad * 0.6
            safe_blur = min(self._elevation * 0.8, max_blur)
            safe_offset_y = min(self._shadow_offset_y, pad * 0.2, safe_blur * 0.4)
        else:
            safe_blur = 0.0
            safe_offset_y = 0.0

        self._surface.draw_card(
            x=draw_x,
            y=draw_y,
            w=draw_w,
            h=draw_h,
            rx=self._rx,
            ry=self._ry,
            bg_color=self._bg_color,
            border_color=self._border_color,
            border_width=self._border_width,
            shadow_blur=safe_blur,
            shadow_spread=0.0,
            shadow_offset_x=0.0,
            shadow_offset_y=safe_offset_y,
            shadow_color=self._shadow_color,
        )
        self._surface.blit(self._photo)


ModernFrame = Frame


class Card(Frame):
    """
    Card container with elevation drop shadow and optional header title.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: str = "",
        width: int = 280,
        height: int = 180,
        rx: float = 16.0,
        ry: float = 16.0,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        elevation: float = 10.0,
        shadow_color: Optional[ColorLike] = None,
        shadow_offset_y: float = 4.0,
        padding: Optional[float] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        pal = get_theme()
        super().__init__(
            master=master,
            width=width,
            height=height,
            rx=rx,
            ry=ry,
            bg_color=bg_color,
            border_color=border_color,
            border_width=border_width,
            elevation=elevation,
            shadow_color=shadow_color,
            shadow_offset_y=shadow_offset_y,
            padding=padding,
            parent_bg=parent_bg,
            **kwargs,
        )
        self._title = title

    @property
    def content(self) -> Card:
        """Alias returning self for direct packing into Card."""
        return self

    def create_content_frame(self, **kwargs) -> tk.Frame:
        """Helper to create an inner tk.Frame styled with the card's surface background."""
        bg = kwargs.pop("bg", kwargs.pop("background", self._bg_color))
        return tk.Frame(self, bg=bg, **kwargs)

    def render(self) -> None:
        super().render()
        if self._title:
            pad = self._current_pad
            pal = get_theme()
            self._surface.draw_text(
                self._title,
                x=pad + 16.0 * self._scale,
                y=pad + 26.0 * self._scale,
                font_size=14.0 * self._scale,
                font_family="sans-serif",
                color=pal.fg,
            )
            # Divider line below title
            line_y = pad + 36.0 * self._scale
            self._surface.draw_line(
                pad + 16.0 * self._scale,
                line_y,
                self._widget_w - pad - 16.0 * self._scale,
                line_y,
                stroke=pal.card_border,
                stroke_width=1.0,
            )
            self._surface.blit(self._photo)


ModernCard = Card


class _AccordionHeader(Widget):
    """Backing vector surface for Accordion header."""

    def __init__(self, accordion: "Accordion", master: tk.Misc, width: int, height: int, bg: Optional[str] = None):
        self._accordion = accordion
        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=bg,
            cursor="hand2",
            resizable_height=False,
        )

    def _on_theme_changed(self, palette: Palette) -> None:
        super()._on_theme_changed(palette)
        if hasattr(self, "_accordion") and self._accordion.winfo_exists():
            try:
                self._accordion._content.configure(bg=palette.surface)
                cascade_bg_to_children(self._accordion._content, palette.surface)
            except Exception:
                pass

    def render(self) -> None:
        if hasattr(self, "_accordion"):
            self._accordion._render_header()


class Accordion(tk.Frame):
    """
    Expandable / collapsible card container with animated rotating chevron arrow.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: str = "Collapsible Section",
        width: int = 280,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._scale = ScalingTracker.get_scaling_factor(master)
        s = self._scale
        pal = get_theme()
        self._explicit_parent_bg = parent_bg
        self._parent_bg = parent_bg or Widget._resolve_default_bg(master, pal)
        super().__init__(
            master,
            width=max(1, int(width * s)),
            bg=self._parent_bg,
            **kwargs,
        )
        self._is_open = False
        self._title = title

        self._header = _AccordionHeader(self, master=self, width=width, height=38, bg=self._parent_bg)
        self._header.pack(fill="x")
        self._header.bind("<ButtonRelease-1>", self._toggle)

        self._content = tk.Frame(self, bg=pal.surface, padx=int(12 * s), pady=int(10 * s))
        self.bind("<Destroy>", self._on_destroy)
        add_theme_listener(self._on_theme_changed)
        self._render_header()

    def _on_destroy(self, event) -> None:
        remove_theme_listener(self._on_theme_changed)

    def set_parent_bg(self, bg: str, force: bool = False) -> None:
        """Update parent background and re-render."""
        self._parent_bg = resolve_color_failsafe(bg, master=self, fallback=self._parent_bg)
        if force:
            self._explicit_parent_bg = None
        try:
            self.configure(bg=self._parent_bg)
        except Exception:
            pass
        if hasattr(self, "_header"):
            self._header.set_parent_bg(self._parent_bg, force=force)
        self._render_header()

    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        if self._explicit_parent_bg is None:
            self._parent_bg = Widget._resolve_default_bg(getattr(self, "master", None), palette)
        try:
            self.configure(bg=self._parent_bg)
            if hasattr(self, "_content") and self._content.winfo_exists():
                self._content.configure(bg=palette.surface)
                cascade_bg_to_children(self._content, palette.surface)
        except Exception:
            pass
        self._render_header()

    @property
    def content_frame(self) -> tk.Frame:
        return self._content

    def _toggle(self, event) -> None:
        self._is_open = not self._is_open
        if self._is_open:
            self._content.pack(fill="both", expand=True, padx=int(4 * self._scale), pady=(0, int(4 * self._scale)))
        else:
            self._content.pack_forget()
        self._header.render()

    def _render_header(self) -> None:
        surf = self._header.surface
        surf.clear(self._parent_bg)
        s = self._scale
        pad = 2.0 * s
        w = max(1.0, self._header._widget_w - pad * 2.0)
        h = max(1.0, self._header._widget_h - pad * 2.0)
        r = 8.0 * s

        pal = get_theme()
        is_hovered = getattr(self._header, "_is_hovered", False)
        is_pressed = getattr(self._header, "_is_pressed", False)

        if is_pressed:
            header_bg = pal.secondary_active
            border_col = pal.primary
            chev_col = pal.primary_active
        elif is_hovered:
            header_bg = pal.card_bg
            border_col = pal.primary_hover
            chev_col = pal.primary_hover
        else:
            header_bg = pal.surface
            border_col = pal.card_border
            chev_col = pal.primary

        surf.fill_rounded_rect(pad, pad, w, h, r, r, header_bg)
        surf.stroke_rounded_rect(pad, pad, w, h, r, r, border_col, 1.2 * s if (is_hovered or is_pressed) else 1.0 * s)

        chev_x = pad + 16.0 * s
        chev_y = self._header._widget_h / 2.0
        draw_vector_chevron(surf, chev_x, chev_y, s, "down" if self._is_open else "right", chev_col, stroke_width=1.8 * s)

        font_sz = 13.0 * s
        surf.draw_text(
            self._title,
            chev_x + 14.0 * s,
            self._header._widget_h / 2.0 + (font_sz * 0.35),
            font_size=font_sz,
            font_family="sans-serif",
            color=pal.fg,
            align="left",
        )
        surf.blit(self._header.photo)


ModernAccordion = Accordion
