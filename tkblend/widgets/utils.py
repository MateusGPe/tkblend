"""
Shared pure utility functions for tkblend vector widgets.

Contains drawing helpers, Tk variable tracing lifecycle utilities,
and layout calculations without mixins or complex inheritance.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any

from tkblend.surface import Surface, Path, ColorLike
from tkblend._tkblend import (
    compute_scrollbar_geometry as _native_compute_scrollbar_geometry,
    compute_scroll_drag_delta as _native_compute_scroll_drag_delta,
    compute_scroll_jump as _native_compute_scroll_jump,
    measure_text_bounds as _native_measure_text_bounds,
)
from tkblend.widgets.constants import (
    FOCUS_RING_WIDTH,
    FOCUS_RING_PADDING,
    FOCUS_RING_ROUND_OFFSET,
    TEXT_BASELINE_OFFSET_RATIO,
    ICON_BASELINE_OFFSET_RATIO,
)


def draw_vector_checkmark(
    surface: Surface,
    cx: float,
    cy: float,
    scale: float,
    color: ColorLike,
    stroke_width: Optional[float] = None,
) -> None:
    """Draw an antialiased vector checkmark centered around (cx, cy)."""
    s = scale
    sw = stroke_width if stroke_width is not None else 2.0 * s
    p = Path()
    p.move_to(cx - 4.5 * s, cy)
    p.line_to(cx - 1.5 * s, cy + 3.5 * s)
    p.line_to(cx + 4.5 * s, cy - 3.5 * s)
    surface.stroke_path(p, color, stroke_width=sw)


def draw_vector_chevron(
    surface: Surface,
    cx: float,
    cy: float,
    scale: float,
    direction: str,
    color: ColorLike,
    stroke_width: Optional[float] = None,
) -> None:
    """
    Draw a crisp vector chevron centered around (cx, cy).
    Direction can be 'up', 'down', 'left', or 'right'.
    """
    s = scale
    sw = stroke_width if stroke_width is not None else 2.0 * s
    p = Path()
    if direction == "up":
        p.move_to(cx - 4.5 * s, cy + 2.0 * s)
        p.line_to(cx, cy - 2.5 * s)
        p.line_to(cx + 4.5 * s, cy + 2.0 * s)
    elif direction == "right":
        p.move_to(cx - 2.5 * s, cy - 4.5 * s)
        p.line_to(cx + 2.0 * s, cy)
        p.line_to(cx - 2.5 * s, cy + 4.5 * s)
    elif direction == "left":
        p.move_to(cx + 2.5 * s, cy - 4.5 * s)
        p.line_to(cx - 2.0 * s, cy)
        p.line_to(cx + 2.5 * s, cy + 4.5 * s)
    else:  # default "down"
        p.move_to(cx - 4.5 * s, cy - 2.0 * s)
        p.line_to(cx, cy + 2.5 * s)
        p.line_to(cx + 4.5 * s, cy - 2.0 * s)

    surface.stroke_path(p, color, stroke_width=sw)


def draw_vector_minus(
    surface: Surface,
    cx: float,
    cy: float,
    arm: float,
    color: ColorLike,
    stroke_width: float = 1.8,
) -> None:
    """Draw a horizontal minus line centered around (cx, cy)."""
    surface.draw_line(cx - arm, cy, cx + arm, cy, color, stroke_width)


def draw_vector_plus(
    surface: Surface,
    cx: float,
    cy: float,
    arm: float,
    color: ColorLike,
    stroke_width: float = 1.8,
) -> None:
    """Draw a plus cross centered around (cx, cy)."""
    surface.draw_line(cx - arm, cy, cx + arm, cy, color, stroke_width)
    surface.draw_line(cx, cy - arm, cx, cy + arm, color, stroke_width)


def truncate_text(
    text: str,
    max_width: float,
    font_size: float,
    avg_char_width_ratio: float = 0.58,
) -> str:
    """Truncate text with ellipsis if estimated width exceeds max_width."""
    if not text:
        return ""
    char_est = max(5, int(max_width / max(1.0, (font_size * avg_char_width_ratio))))
    if len(text) > char_est:
        return text[: max(1, char_est - 3)] + "..."
    return text



def draw_focus_ring(
    surf: Surface,
    x: float,
    y: float,
    w: float,
    h: float,
    rx: float,
    ry: float,
    color: ColorLike,
    stroke_width: float = FOCUS_RING_WIDTH,
    padding: float = FOCUS_RING_PADDING,
    scale: float = 1.0,
) -> None:
    """
    Draw a standard rounded rectangle focus ring around the widget bounds.
    """
    pad_s = padding * scale
    sw_s = stroke_width * scale
    surf.stroke_rounded_rect(
        x - pad_s,
        y - pad_s,
        w + pad_s * 2.0,
        h + pad_s * 2.0,
        rx + pad_s,
        ry + pad_s,
        color,
        stroke_width=sw_s,
    )


def draw_circular_focus_ring(
    surf: Surface,
    cx: float,
    cy: float,
    radius: float,
    color: ColorLike,
    stroke_width: float = FOCUS_RING_WIDTH,
    offset: float = FOCUS_RING_ROUND_OFFSET,
    scale: float = 1.0,
) -> None:
    """
    Draw a circular focus ring around a circular widget (e.g. RadioButton, Slider thumb).
    """
    sw_s = stroke_width * scale
    surf.stroke_circle(
        cx,
        cy,
        radius + offset * scale,
        color,
        stroke_width=sw_s,
    )


def compute_text_baseline_y(
    center_y: float,
    scaled_font_size: float,
    ratio: float = TEXT_BASELINE_OFFSET_RATIO,
) -> float:
    """
    Compute vertical baseline Y coordinate for text rendering centered at `center_y`.
    """
    return center_y + scaled_font_size * ratio


def compute_icon_baseline_y(
    center_y: float,
    scaled_icon_size: float,
    ratio: float = ICON_BASELINE_OFFSET_RATIO,
) -> float:
    """
    Compute vertical baseline Y coordinate for vector icon rendering centered at `center_y`.
    """
    return center_y + scaled_icon_size * ratio


def bind_variable_trace(
    var: Optional[tk.Variable],
    callback: Callable[..., None],
) -> Optional[str]:
    """
    Safely attach a write trace to a Tkinter Variable across different Python/Tk versions.
    """
    if var is None:
        return None
    try:
        return var.trace_add("write", callback)
    except Exception:
        try:
            return var.trace("w", callback)
        except Exception:
            return None


def unbind_variable_trace(
    var: Optional[tk.Variable],
    trace_id: Optional[str],
) -> None:
    """
    Safely detach a write trace from a Tkinter Variable.
    """
    if var is None or trace_id is None:
        return
    try:
        var.trace_remove("write", trace_id)
    except Exception:
        try:
            var.trace_vdelete("w", trace_id)
        except Exception:
            pass


def compute_scrollbar_geometry(
    viewport_len: float,
    content_len: float,
    scroll_pos: float,
    track_pad: float = 8.0,
    min_thumb_len: float = 24.0,
    min_track_len: float = 10.0,
) -> tuple[bool, float, float, float, float]:
    """
    High-performance native helper for virtual/vector scrollbar layout.

    Calculates whether a scrollbar is required, the thumb position offset,
    the thumb size clamped to min_thumb_len, the track length, and the max scroll range.

    Returns:
        (is_needed, thumb_offset, thumb_len, track_len, max_scroll)
    """
    res = _native_compute_scrollbar_geometry(
        float(viewport_len),
        float(content_len),
        float(scroll_pos),
        float(track_pad),
        float(min_thumb_len),
        float(min_track_len),
    )
    return res.is_needed, res.thumb_offset, res.thumb_len, res.track_len, res.max_scroll


def compute_scroll_drag_delta(
    drag_delta_px: float,
    max_scroll: float,
    track_len: float,
    thumb_len: float,
) -> float:
    """
    Convert a mouse drag pixel delta on a scrollbar track into a content scroll delta.
    """
    return _native_compute_scroll_drag_delta(
        float(drag_delta_px),
        float(max_scroll),
        float(track_len),
        float(thumb_len),
    )


def compute_scroll_jump(
    click_offset_in_track: float,
    track_len: float,
    max_scroll: float,
) -> float:
    """
    Calculate target content scroll position from a direct jump click on the track.
    """
    return _native_compute_scroll_jump(
        float(click_offset_in_track),
        float(track_len),
        float(max_scroll),
    )


_MEASURE_SURFACE: Optional[Surface] = None


def get_measure_surface() -> Optional[Surface]:
    """Backwards-compatibility shim for legacy code."""
    global _MEASURE_SURFACE
    if _MEASURE_SURFACE is None:
        try:
            _MEASURE_SURFACE = Surface(1, 1)
        except Exception:
            _MEASURE_SURFACE = None
    return _MEASURE_SURFACE


def normalize_anchor(anchor: Optional[str]) -> str:
    """Normalize cardinal anchor strings ('w', 'center', 'e') or aliases ('left', 'c', 'right')."""
    if not anchor:
        return "center"
    a = str(anchor).lower().strip()
    if a in ("w", "left", "west"):
        return "w"
    elif a in ("e", "right", "east"):
        return "e"
    elif a in ("center", "c", "middle"):
        return "center"
    return "center"


def measure_text_dimensions(
    text: str,
    font_size: float = 13.0,
    font_family: str = "sans-serif",
    font_weight: int = 400,
    italic: bool = False,
    font: Any = None,
    pad_x: int = 0,
    pad_y: int = 0,
    min_w: int = 0,
    min_h: int = 0,
    line_spacing: float = 1.3,
) -> tuple[int, int]:
    """
    Measure natural bounding dimensions of text including multi-line strings.
    Powered by C++ TextLayoutEngine without allocating intermediate measurement surfaces.
    Safe to invoke before widget window creation and in headless environments.
    """
    if font is not None:
        from tkblend.font import parse_font
        cfg = parse_font(font)
        font_size = cfg.size
        font_family = cfg.family
        font_weight = cfg.effective_weight
        italic = cfg.italic

    tb = _native_measure_text_bounds(
        str(text or ""),
        float(font_size),
        str(font_family or "sans-serif"),
        int(font_weight),
        bool(italic),
        int(pad_x),
        int(pad_y),
        int(min_w),
        int(min_h),
        float(line_spacing),
    )
    return tb.width, tb.height


def invoke_callback(cb: Optional[Callable], *args: Any) -> Any:
    """
    Safely invoke a user command callback.
    Supports callbacks taking arguments (e.g. checked state or value) as well as 0-argument callbacks.
    """
    if cb is None or not callable(cb):
        return None
    try:
        import inspect
        sig = inspect.signature(cb)
        params = list(sig.parameters.values())
        has_varargs = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)
        if has_varargs:
            return cb(*args)
        pos_params = [
            p for p in params
            if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        if len(pos_params) == 0:
            return cb()
        return cb(*args[:len(pos_params)])
    except (ValueError, TypeError):
        try:
            return cb(*args)
        except TypeError:
            return cb()




