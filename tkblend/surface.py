"""
High-level Surface and BlendCanvas abstractions for tkblend.
"""

from __future__ import annotations
import tkinter as tk
from typing import Union, Tuple, Optional, Callable, Sequence, Any
from contextlib import contextmanager

from tkblend._tkblend import (  # type: ignore
    Color as _NativeColor,
    Gradient as _NativeGradient,
    Path as _NativePath,
    Surface as _NativeSurface,
    COMP_OP_SRC_OVER,
    EXTEND_PAD,
    EXTEND_REPEAT,
    EXTEND_REFLECT,
)

ColorLike = Union[str, int, Tuple[int, int, int], Tuple[int, int, int, int], _NativeColor]


def parse_color(c: ColorLike) -> _NativeColor:
    """Convert any color representation into a native Color object."""
    if isinstance(c, _NativeColor):
        return c
    if isinstance(c, str):
        return _NativeColor.from_hex(c)
    if isinstance(c, int):
        return _NativeColor.from_u32(c)
    if isinstance(c, (tuple, list)):
        if len(c) == 3:
            return _NativeColor(int(c[0]), int(c[1]), int(c[2]), 255)
        elif len(c) == 4:
            return _NativeColor(int(c[0]), int(c[1]), int(c[2]), int(c[3]))
    raise ValueError(f"Cannot parse color from value: {c!r}")


class LinearGradient:
    """Helper class to build linear gradients with stops."""
    def __init__(self, x0: float, y0: float, x1: float, y1: float):
        self._gradient = _NativeGradient.linear(x0, y0, x1, y1)

    def add_stop(self, offset: float, color: ColorLike) -> LinearGradient:
        self._gradient.add_stop(offset, parse_color(color))
        return self

    def set_extend_mode(self, mode: int) -> LinearGradient:
        self._gradient.set_extend_mode(mode)
        return self

    @property
    def native(self) -> _NativeGradient:
        return self._gradient


class RadialGradient:
    """Helper class to build radial gradients with stops."""
    def __init__(self, x0: float, y0: float, r0: float, x1: float, y1: float, r1: float):
        self._gradient = _NativeGradient.radial(x0, y0, r0, x1, y1, r1)

    def add_stop(self, offset: float, color: ColorLike) -> RadialGradient:
        self._gradient.add_stop(offset, parse_color(color))
        return self

    def set_extend_mode(self, mode: int) -> RadialGradient:
        self._gradient.set_extend_mode(mode)
        return self

    @property
    def native(self) -> _NativeGradient:
        return self._gradient


GradientLike = Union[LinearGradient, RadialGradient, _NativeGradient]


def _unwrap_gradient(g: GradientLike) -> _NativeGradient:
    if isinstance(g, (LinearGradient, RadialGradient)):
        return g.native
    return g


class Surface:
    """
    High-performance Blend2D Vector Surface with direct Tkinter blitting.
    """

    def __init__(self, width: int, height: int):
        self._surface = _NativeSurface(max(1, width), max(1, height))

    @property
    def width(self) -> int:
        return self._surface.width

    @property
    def height(self) -> int:
        return self._surface.height

    @property
    def native(self) -> _NativeSurface:
        return self._surface

    def resize(self, width: int, height: int) -> None:
        """Resize the surface backing image."""
        self._surface.resize(max(1, width), max(1, height))

    def clear(self, color: ColorLike = "#00000000") -> None:
        """Clear the surface with a solid color."""
        self._surface.clear(parse_color(color))

    def clear_rect(self, x: float, y: float, w: float, h: float) -> None:
        """Clear a rectangular region to transparent."""
        self._surface.clear_rect(x, y, w, h)

    def save(self) -> None:
        """Save the context state (transformations, clipping)."""
        self._surface.save()

    def restore(self) -> None:
        """Restore the previous context state."""
        self._surface.restore()

    @contextmanager
    def saved(self):
        """Context manager for saving and restoring transformation state."""
        self.save()
        try:
            yield self
        finally:
            self.restore()

    def reset_transform(self) -> None:
        """Reset transformations to identity."""
        self._surface.reset_transform()

    def translate(self, tx: float, ty: float) -> None:
        """Translate the coordinate matrix."""
        self._surface.translate(tx, ty)

    def scale(self, sx: float, sy: float) -> None:
        """Scale the coordinate matrix."""
        self._surface.scale(sx, sy)

    def rotate(self, angle_rad: float) -> None:
        """Rotate coordinates by angle in radians."""
        self._surface.rotate(angle_rad)

    def clip_rect(self, x: float, y: float, w: float, h: float) -> None:
        """Clip rendering to a rectangle."""
        self._surface.clip_rect(x, y, w, h)

    def clip_rounded_rect(self, x: float, y: float, w: float, h: float, rx: float, ry: float) -> None:
        """Clip rendering to a rounded rectangle."""
        self._surface.clip_rounded_rect(x, y, w, h, rx, ry)

    def reset_clip(self) -> None:
        """Reset clipping area."""
        self._surface.reset_clip()

    def set_comp_op(self, comp_op: int) -> None:
        """Set composition operator."""
        self._surface.set_comp_op(comp_op)

    def set_global_alpha(self, alpha: float) -> None:
        """Set global alpha multiplier [0.0 - 1.0]."""
        self._surface.set_global_alpha(alpha)

    # Rectangles
    def fill_rect(self, x: float, y: float, w: float, h: float, fill: Union[ColorLike, GradientLike]) -> None:
        """Fill a rectangle with a color or gradient."""
        if isinstance(fill, (LinearGradient, RadialGradient, _NativeGradient)):
            self._surface.fill_rect_gradient(x, y, w, h, _unwrap_gradient(fill))
        else:
            self._surface.fill_rect(x, y, w, h, parse_color(fill))

    def stroke_rect(self, x: float, y: float, w: float, h: float, stroke: ColorLike, stroke_width: float = 1.0) -> None:
        """Draw rectangle outline."""
        self._surface.stroke_rect(x, y, w, h, parse_color(stroke), stroke_width)

    def fill_rounded_rect(
        self, x: float, y: float, w: float, h: float, rx: float, ry: float, fill: Union[ColorLike, GradientLike]
    ) -> None:
        """Fill a rounded rectangle with color or gradient."""
        if isinstance(fill, (LinearGradient, RadialGradient, _NativeGradient)):
            self._surface.fill_rounded_rect_gradient(x, y, w, h, rx, ry, _unwrap_gradient(fill))
        else:
            self._surface.fill_rounded_rect(x, y, w, h, rx, ry, parse_color(fill))

    def stroke_rounded_rect(
        self, x: float, y: float, w: float, h: float, rx: float, ry: float, stroke: ColorLike, stroke_width: float = 1.0
    ) -> None:
        """Draw rounded rectangle outline."""
        self._surface.stroke_rounded_rect(x, y, w, h, rx, ry, parse_color(stroke), stroke_width)

    # Circles & Ellipses
    def fill_circle(self, cx: float, cy: float, r: float, fill: Union[ColorLike, GradientLike]) -> None:
        """Fill circle."""
        if isinstance(fill, (LinearGradient, RadialGradient, _NativeGradient)):
            self._surface.fill_circle_gradient(cx, cy, r, _unwrap_gradient(fill))
        else:
            self._surface.fill_circle(cx, cy, r, parse_color(fill))

    def stroke_circle(self, cx: float, cy: float, r: float, stroke: ColorLike, stroke_width: float = 1.0) -> None:
        """Stroke circle outline."""
        self._surface.stroke_circle(cx, cy, r, parse_color(stroke), stroke_width)

    def fill_ellipse(self, cx: float, cy: float, rx: float, ry: float, fill: ColorLike) -> None:
        """Fill ellipse."""
        self._surface.fill_ellipse(cx, cy, rx, ry, parse_color(fill))

    def stroke_ellipse(self, cx: float, cy: float, rx: float, ry: float, stroke: ColorLike, stroke_width: float = 1.0) -> None:
        """Stroke ellipse outline."""
        self._surface.stroke_ellipse(cx, cy, rx, ry, parse_color(stroke), stroke_width)

    # Lines & Paths
    def draw_line(self, x1: float, y1: float, x2: float, y2: float, stroke: ColorLike, stroke_width: float = 1.0) -> None:
        """Draw a line between two points."""
        self._surface.draw_line(x1, y1, x2, y2, parse_color(stroke), stroke_width)

    def fill_path(self, path: Union[Path, _NativePath], fill: Union[ColorLike, GradientLike]) -> None:
        """Fill a path with color or gradient."""
        native_path = path.native if isinstance(path, Path) else path
        if isinstance(fill, (LinearGradient, RadialGradient, _NativeGradient)):
            self._surface.fill_path_gradient(native_path, _unwrap_gradient(fill))
        else:
            self._surface.fill_path(native_path, parse_color(fill))

    def stroke_path(self, path: Union[Path, _NativePath], stroke: ColorLike, stroke_width: float = 1.0) -> None:
        """Stroke path outline."""
        native_path = path.native if isinstance(path, Path) else path
        self._surface.stroke_path(native_path, parse_color(stroke), stroke_width)

    # Typography
    def draw_text(
        self,
        text: str,
        x: float,
        y: float,
        font_size: float = 14.0,
        font_family: str = "sans-serif",
        color: ColorLike = "#ffffff",
        align: str = "left",  # "left", "center", "right"
    ) -> None:
        """
        Draw antialiased subpixel text using Blend2D's native font engine.
        Align can be 'left' (0), 'center' (1), or 'right' (2).
        """
        align_code = 0
        if align == "center":
            align_code = 1
        elif align == "right":
            align_code = 2

        self._surface.draw_text(
            text,
            float(x),
            float(y),
            float(font_size),
            font_family,
            parse_color(color),
            align_code,
        )

    # Shadows & Cards
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
    ) -> None:
        """
        Draw high-performance $O(1)$ soft drop shadow for rounded rectangle geometry.
        """
        self._surface.draw_shadow_rounded_rect(
            x, y, w, h, rx, ry, blur_radius, spread, offset_x, offset_y, parse_color(shadow_color)
        )

    def draw_card(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float = 12.0,
        ry: float = 12.0,
        bg_color: ColorLike = "#1e1e2e",
        border_color: ColorLike = "#00000000",
        border_width: float = 0.0,
        shadow_blur: float = 12.0,
        shadow_spread: float = 0.0,
        shadow_offset_x: float = 0.0,
        shadow_offset_y: float = 4.0,
        shadow_color: ColorLike = "#00000055",
    ) -> None:
        """
        Draw a modern card with soft drop shadow, rounded background, and border in one call.
        """
        self._surface.draw_card(
            x, y, w, h, rx, ry,
            parse_color(bg_color),
            parse_color(border_color),
            border_width,
            shadow_blur,
            shadow_spread,
            shadow_offset_x,
            shadow_offset_y,
            parse_color(shadow_color),
        )

    def flush(self) -> None:
        """Synchronize and flush all queued Blend2D rendering operations."""
        self._surface.flush()

    def blit(self, photo: tk.PhotoImage, dst_x: int = 0, dst_y: int = 0) -> None:
        """
        Directly blit the surface pixel buffer to a Tkinter PhotoImage using Tk_PhotoPutBlock.
        Zero Python copies, zero allocations.
        """
        interp_addr = int(photo.tk.interpaddr())
        photo_name = str(photo.name)
        self._surface.blit_to_photo(interp_addr, photo_name, dst_x, dst_y)

    def get_buffer(self) -> Any:
        """Return a direct zero-copy ndarray/buffer of raw PRGB32 pixels."""
        return self._surface.get_buffer()


class Path:
    """Wrapper around Blend2D vector Path."""
    def __init__(self):
        self._path = _NativePath()

    @property
    def native(self) -> _NativePath:
        return self._path

    def move_to(self, x: float, y: float) -> Path:
        self._path.move_to(x, y)
        return self

    def line_to(self, x: float, y: float) -> Path:
        self._path.line_to(x, y)
        return self

    def quad_to(self, x1: float, y1: float, x2: float, y2: float) -> Path:
        self._path.quad_to(x1, y1, x2, y2)
        return self

    def cubic_to(self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> Path:
        self._path.cubic_to(x1, y1, x2, y2, x3, y3)
        return self

    def arc_to(self, cx: float, cy: float, rx: float, ry: float, start_angle: float, sweep_angle: float) -> Path:
        self._path.arc_to(cx, cy, rx, ry, start_angle, sweep_angle)
        return self

    def add_rect(self, x: float, y: float, w: float, h: float) -> Path:
        self._path.add_rect(x, y, w, h)
        return self

    def add_rounded_rect(self, x: float, y: float, w: float, h: float, rx: float, ry: float) -> Path:
        self._path.add_rounded_rect(x, y, w, h, rx, ry)
        return self

    def add_circle(self, cx: float, cy: float, r: float) -> Path:
        self._path.add_circle(cx, cy, r)
        return self

    def add_ellipse(self, cx: float, cy: float, rx: float, ry: float) -> Path:
        self._path.add_ellipse(cx, cy, rx, ry)
        return self

    def close(self) -> Path:
        self._path.close()
        return self

    def clear(self) -> Path:
        self._path.clear()
        return self

    def reset(self) -> Path:
        self._path.reset()
        return self


class BlendCanvas(tk.Label):
    """
    Tkinter widget backed by a Blend2D Surface and PhotoImage with automatic resize synchronization.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 300,
        height: int = 200,
        bg: str = "#1e1e2e",
        on_draw: Optional[Callable[[Surface], None]] = None,
        **kwargs,
    ):
        self._canvas_width = max(1, width)
        self._canvas_height = max(1, height)
        self._on_draw = on_draw
        self._bg_color = bg

        # Create backing PhotoImage & Surface
        self._photo = tk.PhotoImage(master=master, width=self._canvas_width, height=self._canvas_height)
        self._surface = Surface(self._canvas_width, self._canvas_height)

        super().__init__(
            master,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            background=bg,
            **kwargs,
        )

        self.bind("<Configure>", self._on_configure)
        self.after_idle(self.redraw)

    @property
    def surface(self) -> Surface:
        return self._surface

    @property
    def photo(self) -> tk.PhotoImage:
        return self._photo

    def set_draw_callback(self, callback: Callable[[Surface], None]) -> None:
        """Set or update the custom draw callback."""
        self._on_draw = callback
        self.redraw()

    def _on_configure(self, event) -> None:
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        if new_w != self._canvas_width or new_h != self._canvas_height:
            self._canvas_width = new_w
            self._canvas_height = new_h
            self._photo.configure(width=self._canvas_width, height=self._canvas_height)
            self._surface.resize(self._canvas_width, self._canvas_height)
            self.redraw()

    def redraw(self) -> None:
        """Trigger a render pass and blit to PhotoImage."""
        if self._on_draw:
            self._on_draw(self._surface)
        self._surface.blit(self._photo)
