"""
High-level Blend2D Surface, Gradients, and Vector Path abstractions for tkblend.
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
    DrawBatch,
    TextMetrics,
    EasingType,
    ease,
    spring,
    COMP_OP_SRC_OVER,
    EXTEND_PAD,
    EXTEND_REPEAT,
    EXTEND_REFLECT,
    clear_all_caches,
    clear_font_cache,
    clear_shadow_cache,
    clear_emoji_cache,
    get_shadow_cache_size,
    get_shadow_cache_bytes,
    set_shadow_cache_limits,
)
from tkblend.theme import resolve_theme_color

ColorLike = Union[str, int, Tuple[int, int, int], Tuple[int, int, int, int], _NativeColor]


def clear_caches() -> None:
    """Purge all C++ and engine caches (shadows, fonts, emojis) to reclaim memory immediately."""
    clear_all_caches()


def parse_color(c: ColorLike, alpha: Optional[Union[float, int]] = None) -> _NativeColor:
    """Convert any color representation or ttkbootstrap token into a native Color object."""
    if isinstance(c, _NativeColor):
        return c
    if isinstance(c, str):
        resolved = resolve_theme_color(c, alpha=alpha)
        return _NativeColor.from_hex(resolved)
    if isinstance(c, int):
        return _NativeColor.from_u32(c)
    if isinstance(c, (tuple, list)):
        if len(c) == 3:
            a = int(alpha * 255) if alpha is not None and alpha <= 1.0 else (int(alpha) if alpha is not None else 255)
            return _NativeColor(int(c[0]), int(c[1]), int(c[2]), a)
        elif len(c) == 4:
            a = int(c[3])
            if alpha is not None:
                a = int(alpha * 255) if alpha <= 1.0 else int(alpha)
            return _NativeColor(int(c[0]), int(c[1]), int(c[2]), a)
    raise ValueError(f"Cannot parse color from value: {c!r}")


class LinearGradient:
    """Helper class to build linear gradients with stops."""
    def __init__(self, x0: float, y0: float, x1: float, y1: float):
        self._gradient = _NativeGradient.linear(x0, y0, x1, y1)

    def add_stop(self, offset: float, color: ColorLike, alpha: Optional[float] = None) -> LinearGradient:
        self._gradient.add_stop(offset, parse_color(color, alpha=alpha))
        return self

    def set_extend_mode(self, mode: int) -> LinearGradient:
        self._gradient.set_extend_mode(mode)
        return self

    @property
    def native(self) -> _NativeGradient:
        return self._gradient


class RadialGradient:
    """Helper class to build radial gradients with stops.

    Can be constructed either with:
    - Center and radius: RadialGradient(cx, cy, r)
    - Two circles (focal & outer): RadialGradient(x0, y0, r0, x1, y1, r1)
    """
    def __init__(
        self,
        x0: float,
        y0: float,
        r0_or_r: float,
        x1: Optional[float] = None,
        y1: Optional[float] = None,
        r1: Optional[float] = None,
    ):
        if x1 is None or y1 is None or r1 is None:
            # RadialGradient(cx, cy, r) centered at (x0, y0) with radius r0_or_r
            self._gradient = _NativeGradient.radial(x0, y0, 0.0, x0, y0, r0_or_r)
        else:
            self._gradient = _NativeGradient.radial(x0, y0, r0_or_r, x1, y1, r1)

    def add_stop(self, offset: float, color: ColorLike, alpha: Optional[float] = None) -> RadialGradient:
        self._gradient.add_stop(offset, parse_color(color, alpha=alpha))
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
        self._surface = _NativeSurface(max(1, int(width)), max(1, int(height)))

    def __enter__(self) -> Surface:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            if hasattr(self, "_surface") and self._surface is not None and not self._surface.is_closed:
                self._surface.close()
        except Exception:
            pass

    @property
    def is_closed(self) -> bool:
        """Return whether the native Blend2D surface has been explicitly closed."""
        return self._surface.is_closed if self._surface is not None else True

    def close(self) -> None:
        """Explicitly release native Blend2D context and pixel buffers immediately."""
        if hasattr(self, "_surface") and self._surface is not None and not self._surface.is_closed:
            self._surface.close()

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
        self._surface.resize(max(1, int(width)), max(1, int(height)))

    def clear(self, color: ColorLike = "#00000000") -> None:
        """Clear the surface with a solid color."""
        self._surface.clear(parse_color(color))

    def clear_rect(self, x: float, y: float, w: float, h: float) -> None:
        """Clear a rectangular region to transparent."""
        self._surface.clear_rect(float(x), float(y), float(w), float(h))

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
        self._surface.translate(float(tx), float(ty))

    def scale(self, sx: float, sy: float) -> None:
        """Scale the coordinate matrix."""
        self._surface.scale(float(sx), float(sy))

    def rotate(self, angle_rad: float) -> None:
        """Rotate coordinates by angle in radians."""
        self._surface.rotate(float(angle_rad))

    def clip_rect(self, x: float, y: float, w: float, h: float) -> None:
        """Clip rendering to a rectangle."""
        self._surface.clip_rect(float(x), float(y), float(w), float(h))

    def clip_rounded_rect(self, x: float, y: float, w: float, h: float, rx: float, ry: float) -> None:
        """Clip rendering to a rounded rectangle."""
        self._surface.clip_rounded_rect(float(x), float(y), float(w), float(h), float(rx), float(ry))

    def reset_clip(self) -> None:
        """Reset clipping area."""
        self._surface.reset_clip()

    def set_comp_op(self, comp_op: int) -> None:
        """Set composition operator."""
        self._surface.set_comp_op(comp_op)

    def set_global_alpha(self, alpha: float) -> None:
        """Set global alpha multiplier [0.0 - 1.0]."""
        self._surface.set_global_alpha(float(alpha))

    # Rectangles
    def fill_rect(self, x: float, y: float, w: float, h: float, fill: Union[ColorLike, GradientLike]) -> None:
        """Fill a rectangle with a color or gradient."""
        if isinstance(fill, (LinearGradient, RadialGradient, _NativeGradient)):
            self._surface.fill_rect_gradient(float(x), float(y), float(w), float(h), _unwrap_gradient(fill))
        else:
            self._surface.fill_rect(float(x), float(y), float(w), float(h), parse_color(fill))

    def stroke_rect(self, x: float, y: float, w: float, h: float, stroke: ColorLike, stroke_width: float = 1.0) -> None:
        """Draw rectangle outline."""
        self._surface.stroke_rect(float(x), float(y), float(w), float(h), parse_color(stroke), float(stroke_width))

    def fill_rounded_rect(
        self, x: float, y: float, w: float, h: float, rx: float, ry: float, fill: Union[ColorLike, GradientLike]
    ) -> None:
        """Fill a rounded rectangle with color or gradient."""
        if isinstance(fill, (LinearGradient, RadialGradient, _NativeGradient)):
            self._surface.fill_rounded_rect_gradient(float(x), float(y), float(w), float(h), float(rx), float(ry), _unwrap_gradient(fill))
        else:
            self._surface.fill_rounded_rect(float(x), float(y), float(w), float(h), float(rx), float(ry), parse_color(fill))

    def stroke_rounded_rect(
        self, x: float, y: float, w: float, h: float, rx: float, ry: float, stroke: ColorLike, stroke_width: float = 1.0
    ) -> None:
        """Draw rounded rectangle outline."""
        self._surface.stroke_rounded_rect(float(x), float(y), float(w), float(h), float(rx), float(ry), parse_color(stroke), float(stroke_width))

    # Circles & Ellipses
    def fill_circle(self, cx: float, cy: float, r: float, fill: Union[ColorLike, GradientLike]) -> None:
        """Fill circle."""
        if isinstance(fill, (LinearGradient, RadialGradient, _NativeGradient)):
            self._surface.fill_circle_gradient(float(cx), float(cy), float(r), _unwrap_gradient(fill))
        else:
            self._surface.fill_circle(float(cx), float(cy), float(r), parse_color(fill))

    def stroke_circle(self, cx: float, cy: float, r: float, stroke: ColorLike, stroke_width: float = 1.0) -> None:
        """Stroke circle outline."""
        self._surface.stroke_circle(float(cx), float(cy), float(r), parse_color(stroke), float(stroke_width))

    def fill_ellipse(self, cx: float, cy: float, rx: float, ry: float, fill: ColorLike) -> None:
        """Fill ellipse."""
        self._surface.fill_ellipse(float(cx), float(cy), float(rx), float(ry), parse_color(fill))

    def stroke_ellipse(self, cx: float, cy: float, rx: float, ry: float, stroke: ColorLike, stroke_width: float = 1.0) -> None:
        """Stroke ellipse outline."""
        self._surface.stroke_ellipse(float(cx), float(cy), float(rx), float(ry), parse_color(stroke), float(stroke_width))

    # Lines & Paths
    def draw_line(self, x1: float, y1: float, x2: float, y2: float, stroke: ColorLike, stroke_width: float = 1.0) -> None:
        """Draw a line between two points."""
        self._surface.draw_line(float(x1), float(y1), float(x2), float(y2), parse_color(stroke), float(stroke_width))

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
        self._surface.stroke_path(native_path, parse_color(stroke), float(stroke_width))

    # Typography & Metrics
    def measure_text(
        self,
        text: str,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        font: Union[FontConfig, Tuple[Any, ...], str, None] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        weight: Optional[Union[int, str]] = None,
    ) -> TextMetrics:
        """Measure text metrics (width, height, ascent, descent, advance_x) natively."""
        from tkblend.font import parse_font
        cfg = parse_font(
            font=font,
            font_size=font_size,
            font_family=font_family,
            bold=bold,
            italic=italic,
            weight=weight,
            default_family="default",
            default_size=14.0,
        )
        return self._surface.measure_text(
            text,
            float(cfg.size),
            cfg.family,
            cfg.weight,
            cfg.italic,
            cfg.bold,
        )

    def break_lines(
        self,
        text: str,
        max_width: float,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        font: Union[FontConfig, Tuple[Any, ...], str, None] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        weight: Optional[Union[int, str]] = None,
        truncate_ellipsis: bool = False,
        max_lines: int = 0,
    ) -> list[str]:
        """Wrap text into lines fitting within max_width natively using Blend2D."""
        from tkblend.font import parse_font
        cfg = parse_font(
            font=font,
            font_size=font_size,
            font_family=font_family,
            bold=bold,
            italic=italic,
            weight=weight,
            default_family="default",
            default_size=14.0,
        )
        return self._surface.break_lines(
            text,
            float(max_width),
            float(cfg.size),
            cfg.family,
            cfg.weight,
            cfg.italic,
            cfg.bold,
            bool(truncate_ellipsis),
            int(max_lines),
        )

    def draw_text(
        self,
        text: str,
        x: float,
        y: float,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        color: ColorLike = "#ffffff",
        align: str = "left",  # "left", "center", "right"
        font: Union[FontConfig, Tuple[Any, ...], str, None] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        weight: Optional[Union[int, str]] = None,
    ) -> None:
        """
        Draw antialiased subpixel text using Blend2D's native font engine.
        Supports weight, bold, italic, font tuples, and string descriptions.
        Align can be 'left' (0), 'center' (1), or 'right' (2).
        """
        from tkblend.font import parse_font
        cfg = parse_font(
            font=font,
            font_size=font_size,
            font_family=font_family,
            bold=bold,
            italic=italic,
            weight=weight,
            default_family="default",
            default_size=14.0,
        )

        align_code = 0
        if align == "center":
            align_code = 1
        elif align == "right":
            align_code = 2

        parsed_col = parse_color(color)
        if "\n" in text:
            lines = text.split("\n")
            line_height = float(cfg.size) * 1.35
            for line_idx, line_str in enumerate(lines):
                if line_str:
                    self._surface.draw_text(
                        line_str,
                        float(x),
                        float(y + line_idx * line_height),
                        float(cfg.size),
                        cfg.family,
                        parsed_col,
                        align_code,
                        cfg.weight,
                        cfg.italic,
                        cfg.bold,
                    )
            return

        self._surface.draw_text(
            text,
            float(x),
            float(y),
            float(cfg.size),
            cfg.family,
            parsed_col,
            align_code,
            cfg.weight,
            cfg.italic,
            cfg.bold,
        )

    def draw_text_wrapped(
        self,
        text: str,
        x: float,
        y: float,
        max_width: float,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        color: ColorLike = "#ffffff",
        align: str = "left",
        font: Union[FontConfig, Tuple[Any, ...], str, None] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        weight: Optional[Union[int, str]] = None,
        line_height_factor: float = 1.25,
        truncate_ellipsis: bool = False,
        max_lines: int = 0,
    ) -> None:
        """Draw multi-line wrapped text with word wrapping and optional ellipsis truncation in C++."""
        from tkblend.font import parse_font
        cfg = parse_font(
            font=font,
            font_size=font_size,
            font_family=font_family,
            bold=bold,
            italic=italic,
            weight=weight,
            default_family="default",
            default_size=14.0,
        )
        align_code = 1 if align == "center" else (2 if align == "right" else 0)
        self._surface.draw_text_wrapped(
            text,
            float(x),
            float(y),
            float(max_width),
            float(cfg.size),
            cfg.family,
            parse_color(color),
            align_code,
            cfg.weight,
            cfg.italic,
            cfg.bold,
            float(line_height_factor),
            bool(truncate_ellipsis),
            int(max_lines),
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
            float(x), float(y), float(w), float(h), float(rx), float(ry),
            float(blur_radius), float(spread), float(offset_x), float(offset_y),
            parse_color(shadow_color)
        )

    draw_shadow_rounded_rect = draw_shadow

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
            float(x), float(y), float(w), float(h), float(rx), float(ry),
            parse_color(bg_color),
            parse_color(border_color),
            float(border_width),
            float(shadow_blur),
            float(shadow_spread),
            float(shadow_offset_x),
            float(shadow_offset_y),
            parse_color(shadow_color),
        )

    def fill_shadowed_rounded_rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float = 12.0,
        ry: float = 12.0,
        fill: ColorLike = "#1e1e2e",
        border: ColorLike = "#00000000",
        border_width: float = 0.0,
        shadow_blur: float = 12.0,
        shadow_spread: float = 0.0,
        shadow_offset_x: float = 0.0,
        shadow_offset_y: float = 4.0,
        shadow_color: ColorLike = "#00000055",
        **kwargs,
    ) -> None:
        """Alias for draw_card with fill/border parameter naming."""
        bg = kwargs.get("bg_color", fill)
        bc = kwargs.get("border_color", border)
        bw = kwargs.get("border_width", border_width)
        self.draw_card(
            x, y, w, h, rx, ry,
            bg_color=bg,
            border_color=bc,
            border_width=bw,
            shadow_blur=shadow_blur,
            shadow_spread=shadow_spread,
            shadow_offset_x=shadow_offset_x,
            shadow_offset_y=shadow_offset_y,
            shadow_color=shadow_color,
        )

    # Compound Widget Rendering Primitives (C++)
    def draw_button(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float = 10.0,
        ry: float = 10.0,
        bg_color: ColorLike = "#3b82f6",
        border_color: ColorLike = "#00000000",
        border_width: float = 0.0,
        fg_color: ColorLike = "#ffffff",
        text: str = "",
        font: Union[FontConfig, Tuple[Any, ...], str, None] = None,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
        weight: Optional[Union[int, str]] = None,
        shadow_blur: float = 0.0,
        shadow_offset_y: float = 0.0,
        shadow_color: ColorLike = "#00000000",
        focus_ring_color: ColorLike = "#00000000",
        focus_ring_width: float = 0.0,
        is_pressed: bool = False,
    ) -> None:
        """Draw complete modern vector button with shadow, container, border, focus ring, and text in one native call."""
        from tkblend.font import parse_font
        cfg = parse_font(
            font=font,
            font_size=font_size,
            font_family=font_family,
            bold=bold,
            italic=italic,
            weight=weight,
            default_family="default",
            default_size=13.0,
        )
        self._surface.draw_button(
            float(x), float(y), float(w), float(h),
            float(rx), float(ry),
            parse_color(bg_color),
            parse_color(border_color),
            float(border_width),
            parse_color(fg_color),
            str(text),
            float(cfg.size),
            cfg.family,
            cfg.weight,
            cfg.italic,
            cfg.bold,
            float(shadow_blur),
            float(shadow_offset_y),
            parse_color(shadow_color),
            parse_color(focus_ring_color),
            float(focus_ring_width),
            bool(is_pressed),
        )

    def draw_switch(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        track_color: ColorLike = "#3b82f6",
        thumb_color: ColorLike = "#ffffff",
        thumb_border_color: ColorLike = "#00000000",
        progress_t: float = 0.0,
        is_hovered: bool = False,
        focus_ring_color: ColorLike = "#00000000",
        focus_ring_width: float = 0.0,
    ) -> None:
        """Draw sliding toggle switch with track, shadow, thumb, and focus ring in one native call."""
        self._surface.draw_switch(
            float(x), float(y), float(w), float(h),
            parse_color(track_color),
            parse_color(thumb_color),
            parse_color(thumb_border_color),
            float(progress_t),
            bool(is_hovered),
            parse_color(focus_ring_color),
            float(focus_ring_width),
        )

    def draw_slider(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        track_bg: ColorLike = "#e2e8f0",
        active_bg: ColorLike = "#3b82f6",
        thumb_color: ColorLike = "#ffffff",
        thumb_border_color: ColorLike = "#00000000",
        value_t: float = 0.0,
        track_thickness: float = 4.0,
        thumb_radius: float = 8.0,
        is_hovered: bool = False,
        is_dragging: bool = False,
        focus_ring_color: ColorLike = "#00000000",
        focus_ring_width: float = 0.0,
    ) -> None:
        """Draw slider with track, active fill, thumb shadow, grip, and focus ring in one native call."""
        self._surface.draw_slider(
            float(x), float(y), float(w), float(h),
            parse_color(track_bg),
            parse_color(active_bg),
            parse_color(thumb_color),
            parse_color(thumb_border_color),
            float(value_t),
            float(track_thickness),
            float(thumb_radius),
            bool(is_hovered),
            bool(is_dragging),
            parse_color(focus_ring_color),
            float(focus_ring_width),
        )

    def draw_progress_bar(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float = 6.0,
        ry: float = 6.0,
        track_bg: ColorLike = "#e2e8f0",
        bar_bg: ColorLike = "#3b82f6",
        progress_t: float = 0.0,
        is_indeterminate: bool = False,
        phase_offset: float = 0.0,
    ) -> None:
        """Draw progress bar with track and progress strip / glowing indeterminate pill in one native call."""
        self._surface.draw_progress_bar(
            float(x), float(y), float(w), float(h),
            float(rx), float(ry),
            parse_color(track_bg),
            parse_color(bar_bg),
            float(progress_t),
            bool(is_indeterminate),
            float(phase_offset),
        )

    def draw_checkbox(
        self,
        x: float,
        y: float,
        size: float = 20.0,
        rx: float = 4.0,
        ry: float = 4.0,
        box_bg: ColorLike = "#3b82f6",
        border_color: ColorLike = "#00000000",
        border_width: float = 0.0,
        check_color: ColorLike = "#ffffff",
        is_checked: bool = False,
        is_hovered: bool = False,
        focus_ring_color: ColorLike = "#00000000",
        focus_ring_width: float = 0.0,
    ) -> None:
        """Draw checkbox with rounded container, border, focus ring, and checkmark path in one native call."""
        self._surface.draw_checkbox(
            float(x), float(y), float(size),
            float(rx), float(ry),
            parse_color(box_bg),
            parse_color(border_color),
            float(border_width),
            parse_color(check_color),
            bool(is_checked),
            bool(is_hovered),
            parse_color(focus_ring_color),
            float(focus_ring_width),
        )

    def execute_batch(self, batch: DrawBatch) -> None:
        """Execute a recorded DrawBatch display list with zero GIL overhead."""
        self._surface.execute_batch(batch)

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
        self._surface.blit_to_photo(interp_addr, photo_name, int(dst_x), int(dst_y))

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
        self._path.move_to(float(x), float(y))
        return self

    def line_to(self, x: float, y: float) -> Path:
        self._path.line_to(float(x), float(y))
        return self

    def quad_to(self, x1: float, y1: float, x2: float, y2: float) -> Path:
        self._path.quad_to(float(x1), float(y1), float(x2), float(y2))
        return self

    def cubic_to(self, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float) -> Path:
        self._path.cubic_to(float(x1), float(y1), float(x2), float(y2), float(x3), float(y3))
        return self

    def arc_to(self, cx: float, cy: float, rx: float, ry: float, start_angle: float, sweep_angle: float) -> Path:
        self._path.arc_to(float(cx), float(cy), float(rx), float(ry), float(start_angle), float(sweep_angle))
        return self

    def add_rect(self, x: float, y: float, w: float, h: float) -> Path:
        self._path.add_rect(float(x), float(y), float(w), float(h))
        return self

    def add_rounded_rect(self, x: float, y: float, w: float, h: float, rx: float, ry: float) -> Path:
        self._path.add_rounded_rect(float(x), float(y), float(w), float(h), float(rx), float(ry))
        return self

    def add_circle(self, cx: float, cy: float, r: float) -> Path:
        self._path.add_circle(float(cx), float(cy), float(r))
        return self

    def add_ellipse(self, cx: float, cy: float, rx: float, ry: float) -> Path:
        self._path.add_ellipse(float(cx), float(cy), float(rx), float(ry))
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


# Lazy import for BlendCanvas to avoid circular dependency
def __getattr__(name: str):
    if name == "BlendCanvas":
        from tkblend.canvas import BlendCanvas
        return BlendCanvas
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
