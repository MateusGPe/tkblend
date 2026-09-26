"""
Blend2D Vector Paint Backend for tkblend.prismtk.
"""

from __future__ import annotations
import re
from typing import Optional, Any, Dict, Tuple
from tkblend.surface import Surface
from tkblend.prismtk.dom import Node
from tkblend.prismtk.state import interpolate_string, ReactiveState


def _parse_color_or_gradient(val: Any) -> Any:
    """Returns clean hex color or GradientLike object if applicable."""
    if not val:
        return None
    val_str = str(val).strip()
    return val_str


def _parse_box_shadow(shadow_str: str) -> Optional[Dict[str, Any]]:
    """
    Parses '0 4px 12px rgba(0,0,0,0.15)' -> {dx, dy, blur, color}
    """
    if not shadow_str:
        return None
    parts = shadow_str.strip().split()
    if len(parts) >= 4:
        try:
            dx = float(parts[0].replace("px", ""))
            dy = float(parts[1].replace("px", ""))
            blur = float(parts[2].replace("px", ""))
            color = " ".join(parts[3:])
            return {"dx": dx, "dy": dy, "blur": blur, "color": color}
        except ValueError:
            return None
    return None


def _parse_border(border_str: str) -> Tuple[float, str]:
    """
    Parses '1px solid #ff0000' -> (1.0, '#ff0000')
    """
    if not border_str:
        return (0.0, "#00000000")
    parts = border_str.strip().split()
    width = 1.0
    color = "#ffffff"
    for part in parts:
        if part.endswith("px") or part.replace(".", "", 1).isdigit():
            try:
                width = float(part.replace("px", ""))
            except ValueError:
                pass
        elif part.startswith("#") or part.startswith("rgb") or part.startswith("var"):
            color = part
    return (width, color)


def render_node(surface: Surface, node: Node, state: ReactiveState, scale: float = 1.0) -> None:
    """
    Renders a single Node and its children to the Blend2D Surface.
    """
    style = node.computed_style or {}
    
    # Absolute Physical Coordinates
    x = node.abs_x * scale
    y = node.abs_y * scale
    w = node.abs_width * scale
    h = node.abs_height * scale

    if w <= 0 or h <= 0:
        return

    # Visual Attributes
    bg = style.get("background") or style.get("background-color")
    border_str = style.get("border")
    radius = float(style.get("border-radius", 0.0)) * scale
    shadow_str = style.get("box-shadow")

    # 1. Box Shadow
    if shadow_str:
        s_data = _parse_box_shadow(shadow_str)
        if s_data:
            surface.draw_shadow(
                x=x,
                y=y,
                w=w,
                h=h,
                rx=radius,
                ry=radius,
                blur_radius=s_data["blur"] * scale,
                spread=0.0,
                offset_x=s_data["dx"] * scale,
                offset_y=s_data["dy"] * scale,
                shadow_color=s_data["color"],
            )

    # 2. Background Fill & Shape
    if bg:
        fill_color = _parse_color_or_gradient(bg)
        if node.tag == "circle":
            r = min(w, h) / 2.0
            surface.fill_circle(x + r, y + r, r, fill_color)
        elif radius > 0:
            surface.fill_rounded_rect(x, y, w, h, radius, radius, fill_color)
        else:
            surface.fill_rect(x, y, w, h, fill_color)

    # 3. Border Stroke
    if border_str:
        bw, b_color = _parse_border(border_str)
        b_stroke_w = bw * scale
        if b_stroke_w > 0:
            if node.tag == "circle":
                r = min(w, h) / 2.0
                surface.stroke_circle(x + r, y + r, r, b_color, stroke_width=b_stroke_w)
            elif radius > 0:
                surface.stroke_rounded_rect(x, y, w, h, radius, radius, b_color, stroke_width=b_stroke_w)
            else:
                surface.stroke_rect(x, y, w, h, b_color, stroke_width=b_stroke_w)

    # 4. Specific Tag Behaviors (Text, Progress, Button)
    text_val = node.text_content or node.attributes.get("text")
    if text_val:
        # Interpolate state variables in text
        rendered_text = interpolate_string(str(text_val), state)
        color = style.get("color", "#ffffff")
        font_size = float(style.get("font-size", 14.0)) * scale
        font_family = style.get("font-family", "Segoe UI, sans-serif")
        
        # Center or left-align
        text_align = style.get("text-align", "center" if node.tag in ("button", "text") else "left")
        
        tx = x + (w / 2.0 if text_align == "center" else 8.0 * scale)
        ty = y + (h / 2.0)
        
        surface.draw_text(
            text=rendered_text,
            x=tx,
            y=ty,
            color=color,
            font_size=font_size,
            font_family=font_family,
            align="center" if text_align == "center" else "left"
        )

    # Progress bar special rendering
    if node.tag == "progress":
        val_expr = node.attributes.get("value", 0.0)
        max_expr = node.attributes.get("max", 100.0)
        val = float(interpolate_string(str(val_expr), state) or 0.0)
        max_val = max(1.0, float(interpolate_string(str(max_expr), state) or 100.0))
        pct = max(0.0, min(1.0, val / max_val))
        
        bar_w = w * pct
        bar_color = style.get("color", "#3498db")
        if bar_w > 0:
            if radius > 0:
                surface.fill_rounded_rect(x, y, bar_w, h, radius, radius, bar_color)
            else:
                surface.fill_rect(x, y, bar_w, h, bar_color)

    # 5. Render Children
    for child in node.children:
        render_node(surface, child, state, scale)
