"""
BlendCanvas widget - High-performance Blend2D drawing surface for Tkinter & ttkbootstrap.
"""

from __future__ import annotations
import logging
import tkinter as tk
from typing import Optional, Callable, Union, Any, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

from tkblend.surface import Surface, ColorLike, GradientLike, Path
from tkblend.theme import (
    resolve_theme_color,
    bind_theme_changed,
    is_ttkbootstrap_installed,
    is_inside_card,
)


class BlendCanvas(tk.Label):
    """
    High-performance 2D vector drawing canvas powered by Blend2D and direct Tk_PhotoPutBlock blitting.
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
        self._logical_w = max(1, int(width))
        self._logical_h = max(1, int(height))
        self._canvas_width = self._logical_w
        self._canvas_height = self._logical_h
        self._on_draw = on_draw
        self._bootstyle = bootstyle
        self._auto_theme_redraw = auto_theme_redraw

        # Resolve initial background color
        if bg is not None:
            self._bg_color = bg
        elif bootstyle is not None:
            self._bg_color = bootstyle
        else:
            self._bg_color = "bg"

        # Check if nested inside card for initial bg
        bg_token = self._bg_color
        if bg_token in ("bg", "card_bg") and is_inside_card(master if master is not None else self):
            bg_token = "card_bg"

        resolved_bg = resolve_theme_color(bg_token)
        if resolved_bg.startswith("#") and len(resolved_bg) == 9:
            # Tkinter Label background requires 6-digit hex (#rrggbb)
            resolved_bg = resolved_bg[:7]

        # Backing PhotoImage and Blend2D Surface
        self._photo = tk.PhotoImage(master=master, width=self._canvas_width, height=self._canvas_height)
        self._surface = Surface(self._canvas_width, self._canvas_height)

        super().__init__(
            master,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            background=resolved_bg,
            **kwargs,
        )

        self.bind("<Configure>", self._on_configure)
        self.bind("<Destroy>", self._on_destroy_event, add="+")

        if self._auto_theme_redraw:
            bind_theme_changed(self, self._on_theme_changed)

        self.after_idle(self.redraw)

    @property
    def surface(self) -> Optional[Surface]:
        """Access the underlying Blend2D Surface object."""
        return self._surface

    @property
    def photo(self) -> Optional[tk.PhotoImage]:
        """Access the backing Tkinter PhotoImage."""
        return self._photo

    @property
    def canvas_width(self) -> int:
        return self._canvas_width

    @property
    def canvas_height(self) -> int:
        return self._canvas_height

    def set_draw_callback(self, callback: Optional[Callable[[Surface], None]], redraw_now: bool = True) -> None:
        """Set or update the custom rendering callback function."""
        self._on_draw = callback
        if redraw_now:
            self.redraw()

    @contextmanager
    def render(self, auto_blit: bool = True):
        """
        Context manager for custom rendering blocks.
        Automatically blits changes upon block exit if auto_blit is True.
        """
        if self._surface is None:
            raise RuntimeError("Cannot render on a destroyed BlendCanvas")
        yield self._surface
        if auto_blit and self._photo is not None and self._surface is not None:
            self._surface.blit(self._photo)

    def redraw(self) -> None:
        """Execute the draw callback or subclass _redraw and blit the result to the screen."""
        if not self.winfo_exists():
            return
        if self._on_draw is not None and self._surface is not None and self._photo is not None:
            self._on_draw(self._surface)
            self._surface.blit(self._photo)
        elif hasattr(self, "_redraw") and callable(getattr(self, "_redraw")):
            # Delegate to specialized subclass redraw (e.g. Badge, ToggleSwitch)
            self._redraw()
        elif self._surface is not None and self._photo is not None:
            self._surface.blit(self._photo)

    def _on_configure(self, event) -> None:
        # Ignore unmapped / transient 1x1 geometry events from hidden notebook tabs
        if event.width <= 1 or event.height <= 1:
            return
        if self._surface is None or self._photo is None:
            return

        min_w = getattr(self, "_preferred_width", getattr(self, "_logical_w", 1))
        min_h = getattr(self, "_preferred_height", getattr(self, "_logical_h", 1))

        target_w = max(1, event.width)
        target_h = max(1, event.height)
        photo_w = max(min_w, target_w)
        photo_h = max(min_h, target_h)

        if (
            target_w != self._canvas_width
            or target_h != self._canvas_height
            or self._photo.cget("width") != photo_w
            or self._photo.cget("height") != photo_h
        ):
            self._canvas_width = target_w
            self._canvas_height = target_h
            self._photo.configure(width=photo_w, height=photo_h)
            self._surface.resize(self._canvas_width, self._canvas_height)
            self.redraw()

    def _on_theme_changed(self) -> None:
        """Handle ttkbootstrap theme change event."""
        if not self.winfo_exists():
            return
        bg_token = self._bg_color
        if bg_token in ("bg", "card_bg"):
            bg_token = "card_bg" if is_inside_card(self) else "bg"
        resolved_bg = resolve_theme_color(bg_token)
        if resolved_bg.startswith("#") and len(resolved_bg) == 9:
            resolved_bg = resolved_bg[:7]
        try:
            self.configure(background=resolved_bg)
        except Exception as e:
            logger.debug("Failed configuring canvas background: %s", e)
        self.redraw()

    def _on_destroy_event(self, event=None) -> None:
        """Proactively release native Surface and Photo when Tk destroys the widget."""
        if event is not None and getattr(event, "widget", None) != self:
            return
        self._on_draw = None

        # Clean up theme listener
        cb = getattr(self, "_tkblend_theme_cb", None)
        if cb is not None:
            try:
                from tkblend.theme import remove_theme_listener
                remove_theme_listener(cb)
            except Exception:
                pass
            self._tkblend_theme_cb = None

        # Explicitly close Surface backing Blend2D context and buffer
        if hasattr(self, "_surface") and self._surface is not None:
            try:
                self._surface.close()
            except Exception:
                pass
            self._surface = None

        # Explicitly delete PhotoImage from Tcl/Tk image registry
        if hasattr(self, "_photo") and self._photo is not None:
            try:
                photo_name = str(self._photo.name)
                if self.winfo_exists():
                    self.configure(image="")
                if hasattr(self, "tk") and self.tk is not None:
                    self.tk.call("image", "delete", photo_name)
            except Exception:
                pass
            self._photo = None

    def destroy(self) -> None:
        """Clean up surface, backing photo, and callbacks cleanly on widget destruction."""
        self._on_destroy_event()
        super().destroy()

    # -------------------------------------------------------------------------
    # High-level Drawing Convenience Methods
    # -------------------------------------------------------------------------

    def clear(self, color: ColorLike = "#00000000", blit: bool = False) -> BlendCanvas:
        """Clear canvas with solid color or theme token."""
        self._surface.clear(color)
        if blit:
            self._surface.blit(self._photo)
        return self

    def fill_rect(self, x: float, y: float, w: float, h: float, fill: Union[ColorLike, GradientLike], blit: bool = False) -> BlendCanvas:
        self._surface.fill_rect(x, y, w, h, fill)
        if blit:
            self._surface.blit(self._photo)
        return self

    def stroke_rect(self, x: float, y: float, w: float, h: float, stroke: ColorLike, stroke_width: float = 1.0, blit: bool = False) -> BlendCanvas:
        self._surface.stroke_rect(x, y, w, h, stroke, stroke_width)
        if blit:
            self._surface.blit(self._photo)
        return self

    def fill_rounded_rect(self, x: float, y: float, w: float, h: float, rx: float, ry: float, fill: Union[ColorLike, GradientLike], blit: bool = False) -> BlendCanvas:
        self._surface.fill_rounded_rect(x, y, w, h, rx, ry, fill)
        if blit:
            self._surface.blit(self._photo)
        return self

    def stroke_rounded_rect(self, x: float, y: float, w: float, h: float, rx: float, ry: float, stroke: ColorLike, stroke_width: float = 1.0, blit: bool = False) -> BlendCanvas:
        self._surface.stroke_rounded_rect(x, y, w, h, rx, ry, stroke, stroke_width)
        if blit:
            self._surface.blit(self._photo)
        return self

    def fill_circle(self, cx: float, cy: float, r: float, fill: Union[ColorLike, GradientLike], blit: bool = False) -> BlendCanvas:
        self._surface.fill_circle(cx, cy, r, fill)
        if blit:
            self._surface.blit(self._photo)
        return self

    def stroke_circle(self, cx: float, cy: float, r: float, stroke: ColorLike, stroke_width: float = 1.0, blit: bool = False) -> BlendCanvas:
        self._surface.stroke_circle(cx, cy, r, stroke, stroke_width)
        if blit:
            self._surface.blit(self._photo)
        return self

    def draw_line(self, x1: float, y1: float, x2: float, y2: float, stroke: ColorLike, stroke_width: float = 1.0, blit: bool = False) -> BlendCanvas:
        self._surface.draw_line(x1, y1, x2, y2, stroke, stroke_width)
        if blit:
            self._surface.blit(self._photo)
        return self

    def draw_text(
        self,
        text: str,
        x: float,
        y: float,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        color: ColorLike = "#ffffff",
        align: str = "left",
        font: Any = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        weight: Optional[Union[int, str]] = None,
        blit: bool = False,
    ) -> BlendCanvas:
        self._surface.draw_text(
            text=text,
            x=x,
            y=y,
            font_size=font_size,
            font_family=font_family,
            color=color,
            align=align,
            font=font,
            bold=bold,
            italic=italic,
            weight=weight,
        )
        if blit:
            self._surface.blit(self._photo)
        return self

    def draw_shadow(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float,
        ry: float,
        blur_radius: float = 10.0,
        spread: float = 0.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        shadow_color: ColorLike = "#00000066",
        blit: bool = False,
    ) -> BlendCanvas:
        self._surface.draw_shadow(x, y, w, h, rx, ry, blur_radius, spread, offset_x, offset_y, shadow_color)
        if blit:
            self._surface.blit(self._photo)
        return self

    def draw_card(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float = 12.0,
        ry: float = 12.0,
        bg_color: ColorLike = "bg",
        border_color: ColorLike = "#00000000",
        border_width: float = 0.0,
        shadow_blur: float = 12.0,
        shadow_spread: float = 0.0,
        shadow_offset_x: float = 0.0,
        shadow_offset_y: float = 4.0,
        shadow_color: ColorLike = "#00000044",
        blit: bool = False,
    ) -> BlendCanvas:
        self._surface.draw_card(
            x, y, w, h, rx, ry,
            bg_color, border_color, border_width,
            shadow_blur, shadow_spread, shadow_offset_x, shadow_offset_y, shadow_color
        )
        if blit:
            self._surface.blit(self._photo)
        return self
