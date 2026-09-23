"""
Shared vector drawing primitives and geometry utilities for tkblend widgets.
Encapsulates common rendering shapes (checkmarks, chevrons, steppers, text truncation)
following DRY and KISS principles.
"""

from __future__ import annotations
from typing import Optional
from tkblend.surface import Surface, Path, ColorLike


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
    char_est = max(5, int(max_width / (font_size * avg_char_width_ratio)))
    if len(text) > char_est:
        return text[: max(1, char_est - 3)] + "..."
    return text
