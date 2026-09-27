"""
Modern container widgets: Frame, Card, and Accordion with Blend2D vector styling.
"""

from __future__ import annotations
import logging
import tkinter as tk
from typing import Optional

from tkblend.surface import ColorLike
from tkblend.theme import (
    get_theme,
    Palette,
    add_theme_listener,
    remove_theme_listener,
    resolve_color_failsafe,
)
from tkblend.utils.window_shape import is_window_shaping_supported
from tkblend.widgets.base import (
    Widget,
    ScalingTracker,
    ContainerBase,
    cascade_bg_to_children,
)
from tkblend.widgets.drawing import draw_vector_chevron

logger = logging.getLogger(__name__)


class Frame(ContainerBase):
    """
    Modern container with dynamic corner radius, customizable border,
    and soft elevation drop shadow.
    """
    pass


class Card(Frame):
    """
    Card container with elevation drop shadow, header title support,
    and automatic safe margin computation.
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
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, val: str) -> None:
        self._title = val
        self._update_body_geometry()
        self.render()

    @property
    def safe_insets_px(self) -> tuple[int, int, int, int]:
        """Return (left, top, right, bottom) safe inner margins in scaled pixels for Card."""
        s = self._scale
        pad = self._current_pad if self._current_pad > 0 else (self._padding if self._padding is not None else max(8.0 * s, self._elevation * 0.8))
        inset_x = int(pad + max(self._border_width + (self._rx * 0.35), 14.0 * s))
        bottom_inset = int(pad + max(self._border_width + (self._ry * 0.35) + 4.0 * s, 14.0 * s))
        if self._title:
            top_inset = int(pad + 44.0 * s)
        else:
            top_inset = int(pad + max(self._border_width + (self._ry * 0.35) + 4.0 * s, 14.0 * s))
        return (inset_x, top_inset, inset_x, bottom_inset)

    @property
    def content_bounds(self) -> tuple[int, int, int, int]:
        """Return (x, y, width, height) of the printable inner rectangle in scaled pixels for Card."""
        s = self._scale
        pad = self._current_pad if self._current_pad > 0 else (self._padding if self._padding is not None else max(8.0 * s, self._elevation * 0.8))
        if self._clip_children and is_window_shaping_supported():
            left = int(pad + self._border_width)
            right = left
            bottom = int(pad + self._border_width)
            top = int(pad + 40.0 * s) if self._title else int(pad + self._border_width)
            w = max(1, self._widget_w - left - right)
            h = max(1, self._widget_h - top - bottom)
            return (left, top, w, h)
        left, top, right, bottom = self.safe_insets_px
        w = max(1, self._widget_w - left - right)
        h = max(1, self._widget_h - top - bottom)
        return (left, top, w, h)

    @property
    def content(self) -> Card:
        """Alias returning self for direct packing into Card."""
        return self

    def render(self) -> None:
        super().render()
        if self._title and self._widget_w > 1 and self._widget_h > 1:
            try:
                pad = self._current_pad
                pal = get_theme()
                font_sz = 14.0 * self._scale
                text_x = pad + 16.0 * self._scale
                text_y = pad + 24.0 * self._scale
                self._surface.draw_text(
                    self._title,
                    x=text_x,
                    y=text_y,
                    font_size=font_sz,
                    font_family="sans-serif",
                    color=pal.fg,
                )
                # Divider line below title
                line_y = pad + 36.0 * self._scale
                max_line_w = max(text_x + 10.0, self._widget_w - pad - 16.0 * self._scale)
                if max_line_w > text_x:
                    self._surface.draw_line(
                        text_x,
                        line_y,
                        max_line_w,
                        line_y,
                        stroke=pal.card_border,
                        stroke_width=1.0,
                    )
                self._surface.blit(self._photo)
            except Exception as e:
                logger.debug("Render failed in Card title overlay: %s", e, exc_info=True)


class _AccordionHeader(Widget):
    """Backing vector surface for Accordion header."""

    def __init__(self, accordion: "Accordion", master: tk.Misc, width: int, height: int, bg: Optional[str] = None):
        import weakref
        self._accordion_ref = weakref.ref(accordion)
        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=bg,
            cursor="hand2",
            resizable_height=False,
        )

    @property
    def _accordion(self) -> Optional["Accordion"]:
        return self._accordion_ref() if hasattr(self, "_accordion_ref") else None

    def _on_theme_changed(self, palette: Palette) -> None:
        super()._on_theme_changed(palette)
        acc = self._accordion
        if acc is not None and hasattr(acc, "winfo_exists") and acc.winfo_exists():
            try:
                acc._content.configure(bg=palette.surface)
                cascade_bg_to_children(acc._content, palette.surface)
            except Exception as e:
                logger.debug("Failed updating Accordion content background in _AccordionHeader: %s", e)

    def render(self) -> None:
        acc = self._accordion
        if acc is not None:
            acc._render_header()


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

    def _on_destroy(self, event=None) -> None:
        remove_theme_listener(self._on_theme_changed)

    def destroy(self) -> None:
        remove_theme_listener(self._on_theme_changed)
        if hasattr(self, "_header") and self._header is not None:
            try:
                self._header.destroy()
            except Exception as e:
                logger.debug("Failed destroying Accordion header: %s", e)
            self._header = None  # type: ignore
        super().destroy()

    def set_parent_bg(self, bg: str, force: bool = False, render: bool = True) -> None:
        """Update parent background and re-render."""
        self._parent_bg = resolve_color_failsafe(bg, master=self, fallback=self._parent_bg)
        if force:
            self._explicit_parent_bg = None
        try:
            self.configure(bg=self._parent_bg)
        except Exception as e:
            logger.debug("Failed configuring Accordion background to '%s': %s", self._parent_bg, e)
        if hasattr(self, "_header"):
            self._header.set_parent_bg(self._parent_bg, force=force, render=render)
        if render:
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
                cascade_bg_to_children(self._content, palette.surface, render=False, palette=palette)
        except Exception as e:
            logger.debug("Failed updating Accordion background during theme change: %s", e)
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
        if self._header._widget_w <= 1 or self._header._widget_h <= 1:
            return
        try:
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
        except Exception as e:
            logger.debug("Render failed in Accordion header: %s", e, exc_info=True)

    def render(self) -> None:
        """Render backing vector accordion header."""
        self._render_header()


LabelFrame = Card
Labelframe = Card
