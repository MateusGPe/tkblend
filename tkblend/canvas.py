"""
BlendCanvas widget - High-performance Blend2D drawing surface for Tkinter & ttkbootstrap.
Renders directly to native OS window without tk.Canvas or tk.PhotoImage.
"""

from __future__ import annotations
import logging
import tkinter as tk
from typing import Optional, Callable, Union, Any, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

from tkblend.frame import BlendFrame
from tkblend.surface import Surface, ColorLike, GradientLike, Path
from tkblend.theme import (
    resolve_theme_color,
    add_theme_listener,
    remove_theme_listener,
    is_inside_card,
)


class BlendCanvas(BlendFrame):
    """
    High-performance 2D vector drawing canvas powered by Blend2D with native OS window blitting.
    Seamlessly integrates with ttkbootstrap themes and bootstyles.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 300,
        height: int = 200,
        bg: Optional[str] = None,
        bootstyle: Optional[str] = None,
        on_draw: Optional[Callable[[Surface], None]] = None,
        auto_theme_redraw: bool = True,
        **kwargs,
    ):
        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=bg,
            bootstyle=bootstyle,
            on_draw=on_draw,
            auto_theme_redraw=auto_theme_redraw,
            **kwargs,
        )

    @property
    def photo(self) -> Optional[Any]:
        """Legacy photo property (now None since native blitting is used directly)."""
        return None

    @contextmanager
    def render(self, auto_blit: bool = True, auto_present: Optional[bool] = None):
        """
        Context manager for custom rendering blocks.
        Automatically presents changes upon block exit.
        """
        if self._surface is None or self._is_destroyed:
            raise RuntimeError("Cannot render on a destroyed BlendCanvas")
        yield self._surface
        should_present = auto_present if auto_present is not None else auto_blit
        if should_present and self._surface is not None:
            self._surface.present()

    # Convenience direct drawing delegation to self._surface with chaining support
    def clear(self, color: ColorLike = "#00000000", blit: bool = False, present: bool = False) -> BlendCanvas:
        if self._surface is not None:
            self._surface.clear(color)
            if blit or present:
                self._surface.present()
        return self

    def fill_rect(self, x: float, y: float, w: float, h: float, color: ColorLike, blit: bool = False, present: bool = False) -> BlendCanvas:
        if self._surface is not None:
            self._surface.fill_rect(x, y, w, h, color)
            if blit or present:
                self._surface.present()
        return self

    def stroke_rect(self, x: float, y: float, w: float, h: float, color: ColorLike, stroke_width: float = 1.0, blit: bool = False, present: bool = False) -> BlendCanvas:
        if self._surface is not None:
            self._surface.stroke_rect(x, y, w, h, color, stroke_width)
            if blit or present:
                self._surface.present()
        return self

    def fill_rounded_rect(self, x: float, y: float, w: float, h: float, rx: float, ry: float, color: ColorLike, blit: bool = False, present: bool = False) -> BlendCanvas:
        if self._surface is not None:
            self._surface.fill_rounded_rect(x, y, w, h, rx, ry, color)
            if blit or present:
                self._surface.present()
        return self

    def stroke_rounded_rect(self, x: float, y: float, w: float, h: float, rx: float, ry: float, color: ColorLike, stroke_width: float = 1.0, blit: bool = False, present: bool = False) -> BlendCanvas:
        if self._surface is not None:
            self._surface.stroke_rounded_rect(x, y, w, h, rx, ry, color, stroke_width)
            if blit or present:
                self._surface.present()
        return self

    def fill_circle(self, cx: float, cy: float, r: float, color: ColorLike, blit: bool = False, present: bool = False) -> BlendCanvas:
        if self._surface is not None:
            self._surface.fill_circle(cx, cy, r, color)
            if blit or present:
                self._surface.present()
        return self

    def stroke_circle(self, cx: float, cy: float, r: float, color: ColorLike, stroke_width: float = 1.0, blit: bool = False, present: bool = False) -> BlendCanvas:
        if self._surface is not None:
            self._surface.stroke_circle(cx, cy, r, color, stroke_width)
            if blit or present:
                self._surface.present()
        return self

    def draw_line(self, x1: float, y1: float, x2: float, y2: float, color: ColorLike, stroke_width: float = 1.0, blit: bool = False, present: bool = False) -> BlendCanvas:
        if self._surface is not None:
            self._surface.draw_line(x1, y1, x2, y2, color, stroke_width)
            if blit or present:
                self._surface.present()
        return self

    def draw_text(
        self,
        text: str,
        x: float,
        y: float,
        font_size: float = 14.0,
        font_family: str = "default",
        color: Optional[ColorLike] = None,
        align: int = 0,
        weight: int = 400,
        italic: bool = False,
        bold: bool = False,
        blit: bool = False,
        present: bool = False,
    ) -> BlendCanvas:
        if self._surface is not None:
            self._surface.draw_text(
                text=text,
                x=x,
                y=y,
                font_size=font_size,
                font_family=font_family,
                color=color,
                align=align,
                weight=weight,
                italic=italic,
                bold=bold,
            )
            if blit or present:
                self._surface.present()
        return self

    def draw_shadow(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float = 0.0,
        ry: float = 0.0,
        blur_radius: float = 10.0,
        spread: float = 0.0,
        offset_x: float = 0.0,
        offset_y: float = 4.0,
        shadow_color: Optional[ColorLike] = None,
        blit: bool = False,
        present: bool = False,
    ) -> BlendCanvas:
        if self._surface is not None:
            self._surface.draw_shadow_rounded_rect(
                x=x,
                y=y,
                w=w,
                h=h,
                rx=rx,
                ry=ry,
                blur_radius=blur_radius,
                spread=spread,
                offset_x=offset_x,
                offset_y=offset_y,
                shadow_color=shadow_color,
            )
            if blit or present:
                self._surface.present()
        return self

    def draw_card(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float = 0.0,
        ry: float = 0.0,
        bg_color: ColorLike = "#ffffff",
        border_color: Optional[ColorLike] = None,
        border_width: float = 0.0,
        shadow_blur: float = 0.0,
        shadow_spread: float = 0.0,
        shadow_offset_x: float = 0.0,
        shadow_offset_y: float = 0.0,
        shadow_color: Optional[ColorLike] = None,
        blit: bool = False,
        present: bool = False,
    ) -> BlendCanvas:
        if self._surface is not None:
            self._surface.draw_card(
                x=x,
                y=y,
                w=w,
                h=h,
                rx=rx,
                ry=ry,
                bg_color=bg_color,
                border_color=border_color,
                border_width=border_width,
                shadow_blur=shadow_blur,
                shadow_spread=shadow_spread,
                shadow_offset_x=shadow_offset_x,
                shadow_offset_y=shadow_offset_y,
                shadow_color=shadow_color,
            )
            if blit or present:
                self._surface.present()
        return self

    def draw_button(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float = 0.0,
        ry: float = 0.0,
        bg_color: ColorLike = "#3b82f6",
        border_color: Optional[ColorLike] = None,
        border_width: float = 0.0,
        fg_color: Optional[ColorLike] = None,
        text: str = "",
        font_size: float = 13.0,
        font_family: str = "default",
        weight: int = 400,
        italic: bool = False,
        bold: bool = False,
        shadow_blur: float = 0.0,
        shadow_offset_y: float = 0.0,
        shadow_color: Optional[ColorLike] = None,
        focus_ring_color: Optional[ColorLike] = None,
        focus_ring_width: float = 0.0,
        is_pressed: bool = False,
        blit: bool = False,
        present: bool = False,
    ) -> BlendCanvas:
        if self._surface is not None:
            self._surface.draw_button(
                x=x,
                y=y,
                w=w,
                h=h,
                rx=rx,
                ry=ry,
                bg_color=bg_color,
                border_color=border_color,
                border_width=border_width,
                fg_color=fg_color,
                text=text,
                font_size=font_size,
                font_family=font_family,
                weight=weight,
                italic=italic,
                bold=bold,
                shadow_blur=shadow_blur,
                shadow_offset_y=shadow_offset_y,
                shadow_color=shadow_color,
                focus_ring_color=focus_ring_color,
                focus_ring_width=focus_ring_width,
                is_pressed=is_pressed,
            )
            if blit or present:
                self._surface.present()
        return self
