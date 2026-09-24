"""
VectorImage, VectorIcon, and IconLabel widgets with pure Blend2D vector scaling & tinting.
"""

from __future__ import annotations
import logging
import tkinter as tk
from typing import Optional, Union, Tuple, Any

from tkblend.surface import Surface, ColorLike
from tkblend.theme import (
    get_theme,
    Palette,
    add_theme_listener,
    remove_theme_listener,
    resolve_color_failsafe,
)
from tkblend.widgets.base import Widget, ScalingTracker
from tkblend.widgets.drawing import (
    draw_vector_checkmark,
    draw_vector_chevron,
    draw_vector_plus,
    draw_vector_minus,
)

logger = logging.getLogger(__name__)


class VectorIcon(Widget):
    """
    Renders pure vector geometric icons (chevron, checkmark, plus, minus, circle, star, info)
    with dynamic color tinting and High-DPI scaling.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        icon_name: str = "checkmark",
        size: int = 24,
        color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._icon_name = icon_name
        self._explicit_color = color
        self._size = size
        super().__init__(master=master, width=size, height=size, bg=parent_bg, **kwargs)

    @property
    def icon_name(self) -> str:
        return self._icon_name

    @icon_name.setter
    def icon_name(self, name: str) -> None:
        self._icon_name = name
        self.render()

    def set_color(self, color: ColorLike) -> None:
        self._explicit_color = color
        self.render()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            w = float(self._widget_w)
            h = float(self._widget_h)
            cx = w / 2.0
            cy = h / 2.0
            pal = get_theme()
            col = self._explicit_color or pal.primary

            icon_scale = min(w, h) / (24.0 * s) * s

            if self._icon_name == "checkmark":
                draw_vector_checkmark(self._surface, cx, cy, scale=icon_scale * 1.6, color=col, stroke_width=2.2 * s)
            elif self._icon_name in ("chevron_down", "chevron_up", "chevron_left", "chevron_right"):
                direction = self._icon_name.split("_")[-1]
                draw_vector_chevron(self._surface, cx, cy, scale=icon_scale * 1.5, direction=direction, color=col, stroke_width=2.2 * s)
            elif self._icon_name == "plus":
                draw_vector_plus(self._surface, cx, cy, arm=6.0 * icon_scale, color=col, stroke_width=2.2 * s)
            elif self._icon_name == "minus":
                draw_vector_minus(self._surface, cx, cy, arm=6.0 * icon_scale, color=col, stroke_width=2.2 * s)
            elif self._icon_name == "dot":
                self._surface.fill_circle(cx, cy, 4.0 * icon_scale, col)
            elif self._icon_name == "circle":
                self._surface.stroke_circle(cx, cy, 6.0 * icon_scale, col, stroke_width=2.0 * s)
            else:
                self._surface.fill_circle(cx, cy, 4.0 * icon_scale, col)

            self._surface.blit(self._photo)
        except Exception as e:
            logger.debug("Render failed in VectorIcon: %s", e, exc_info=True)


class IconLabel(Widget):
    """
    Compound widget combining a vector icon alongside a text label.
    Automatically computes appropriate width when none is explicitly specified.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        icon: str = "dot",
        width: Optional[int] = None,
        height: int = 32,
        font_size: int = 12,
        icon_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._text = text
        self._icon = icon
        self._font_size = font_size
        self._explicit_icon_color = icon_color
        self._explicit_text_color = text_color
        self._auto_width = (width is None)

        if width is None:
            width = self._calc_auto_width(text, font_size)

        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

    @staticmethod
    def _calc_auto_width(text: str, font_size: int) -> int:
        return max(50, int(len(text) * font_size * 0.72 + 36))

    def set_text(self, text: str) -> None:
        self._text = text
        if self._auto_width:
            new_w = self._calc_auto_width(text, self._font_size)
            if new_w != self._logical_w:
                self._logical_w = new_w
                self._widget_w = max(1, int(new_w * self._scale))
                if self._photo and self._surface:
                    self._photo.configure(width=self._widget_w, height=self._widget_h)
                    self._surface.resize(self._widget_w, self._widget_h)
        self.render()

    def set_icon(self, icon: str) -> None:
        self._icon = icon
        self.render()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            w = float(self._widget_w)
            h = float(self._widget_h)
            pal = get_theme()
            icon_col = self._explicit_icon_color or pal.primary
            txt_col = self._explicit_text_color or pal.fg

            # Draw icon on the left
            icon_x = 10.0 * s
            icon_y = h / 2.0

            if self._icon == "checkmark":
                draw_vector_checkmark(self._surface, icon_x, icon_y, scale=1.3 * s, color=icon_col, stroke_width=2.0 * s)
            elif self._icon == "plus":
                draw_vector_plus(self._surface, icon_x, icon_y, arm=4.5 * s, color=icon_col, stroke_width=2.0 * s)
            elif self._icon == "minus":
                draw_vector_minus(self._surface, icon_x, icon_y, arm=4.5 * s, color=icon_col, stroke_width=2.0 * s)
            elif self._icon in ("chevron_down", "chevron_up", "chevron_left", "chevron_right"):
                direction = self._icon.split("_")[-1]
                draw_vector_chevron(self._surface, icon_x, icon_y, scale=1.2 * s, direction=direction, color=icon_col, stroke_width=2.0 * s)
            elif self._icon == "dot":
                self._surface.fill_circle(icon_x, icon_y, 3.5 * s, icon_col)
            else:
                self._surface.fill_circle(icon_x, icon_y, 3.5 * s, icon_col)

            # Draw text
            fsz = self._font_size * s
            text_x = icon_x + 12.0 * s
            text_y = h / 2.0 + (fsz * 0.35)
            self._surface.draw_text(
                self._text, text_x, text_y,
                font_size=fsz,
                font_family="sans-serif",
                color=txt_col,
                align="left",
            )

            self._surface.blit(self._photo)
        except Exception as e:
            logger.debug("Render failed in IconLabel: %s", e, exc_info=True)


class VectorImage(Widget):
    """
    Displays raster or Blend2D images with high DPI scaling and optional rounded corners.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        image: Optional[Image] = None,
        width: int = 100,
        height: int = 100,
        rx: float = 0.0,
        ry: float = 0.0,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._image = image
        self._rx = rx
        self._ry = ry
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

    def set_image(self, image: Optional[Image]) -> None:
        self._image = image
        self.render()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            w = float(self._widget_w)
            h = float(self._widget_h)

            if self._image is not None:
                self._surface.blit_image(self._image, 0, 0, w, h)

            self._surface.blit(self._photo)
        except Exception as e:
            logger.debug("Render failed in VectorImage: %s", e, exc_info=True)


