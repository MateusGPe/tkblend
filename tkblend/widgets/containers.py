"""
Modern container widgets: Frame, Card, and Accordion with Blend2D vector styling.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional

from tkblend.surface import Surface, ColorLike, Path
from tkblend.theme import get_theme, Palette
from tkblend.widgets.base import Widget, ScalingTracker
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
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._scale = ScalingTracker.get_scaling_factor(master)
        pal = get_theme()
        self._parent_bg = parent_bg or pal.bg
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
        self._bg_color = bg_color or pal.card_bg
        self._border_color = border_color or pal.card_border
        self._border_width = max(1.0, border_width * self._scale)
        self._elevation = elevation * self._scale
        self._shadow_color = shadow_color or pal.shadow_color
        self._shadow_offset_y = shadow_offset_y * self._scale

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
        self.after_idle(self.render)

    def _on_configure(self, event) -> None:
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        if new_w != self._widget_w or new_h != self._widget_h:
            self._widget_w = new_w
            self._widget_h = new_h
            self._photo.configure(width=self._widget_w, height=self._widget_h)
            self._surface.resize(self._widget_w, self._widget_h)
            self.render()

    def set_background(self, bg_color: ColorLike) -> None:
        self._bg_color = bg_color
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        pad = max(4.0 * self._scale, self._elevation * 0.8)
        draw_x = pad
        draw_y = pad
        draw_w = max(1.0, self._widget_w - pad * 2.0)
        draw_h = max(1.0, self._widget_h - pad * 2.0)

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
            shadow_blur=self._elevation * 1.5,
            shadow_spread=0.0,
            shadow_offset_x=0.0,
            shadow_offset_y=self._shadow_offset_y,
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
            bg_color=bg_color or pal.surface,
            border_color=border_color or pal.card_border,
            border_width=border_width,
            elevation=elevation,
            shadow_color=shadow_color or pal.shadow_color,
            parent_bg=parent_bg or pal.bg,
            **kwargs,
        )
        self._title = title

    def render(self) -> None:
        super().render()
        if self._title:
            pad = max(4.0 * self._scale, self._elevation * 0.8)
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
        super().__init__(master=master, width=width, height=height, bg=bg, cursor="hand2")

    def _on_theme_changed(self, palette: Palette) -> None:
        super()._on_theme_changed(palette)
        if hasattr(self, "_accordion") and self._accordion.winfo_exists():
            try:
                self._accordion._content.configure(bg=palette.surface)
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
        self._parent_bg = parent_bg or pal.bg
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
