"""
Shared pure utility functions for tkblend vector widgets.

Contains drawing helpers, Tk variable tracing lifecycle utilities,
and layout calculations without mixins or complex inheritance.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any

from tkblend.surface import Surface, ColorLike
from tkblend.widgets.constants import (
    FOCUS_RING_WIDTH,
    FOCUS_RING_PADDING,
    FOCUS_RING_ROUND_OFFSET,
    TEXT_BASELINE_OFFSET_RATIO,
    ICON_BASELINE_OFFSET_RATIO,
)


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
