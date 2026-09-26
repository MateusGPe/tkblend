"""
CSS Flexbox and Box Model Layout Solver for tkblend.prismtk.
"""

from __future__ import annotations
from typing import Optional, List, Tuple
from tkblend.prismtk.dom import Node


def _parse_box_dim(val: any, parent_size: float) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if val_str.endswith("%"):
        try:
            pct = float(val_str[:-1].strip())
            return (pct / 100.0) * parent_size
        except ValueError:
            return None
    if val_str.endswith("px"):
        try:
            return float(val_str[:-2].strip())
        except ValueError:
            return None
    try:
        return float(val_str)
    except ValueError:
        return None


def _parse_edge_insets(val: any) -> Tuple[float, float, float, float]:
    """Returns (top, right, bottom, left)"""
    if val is None:
        return (0.0, 0.0, 0.0, 0.0)
    if isinstance(val, (int, float)):
        v = float(val)
        return (v, v, v, v)
    parts = [float(p.replace("px", "").strip()) for p in str(val).split() if p.strip()]
    if len(parts) == 1:
        return (parts[0], parts[0], parts[0], parts[0])
    elif len(parts) == 2:
        return (parts[0], parts[1], parts[0], parts[1])
    elif len(parts) == 4:
        return (parts[0], parts[1], parts[2], parts[3])
    return (0.0, 0.0, 0.0, 0.0)


def compute_layout(node: Node, container_w: float, container_h: float, origin_x: float = 0.0, origin_y: float = 0.0) -> None:
    """
    Recursively computes layout boxes (x, y, w, h) for a Node and its children.
    """
    style = node.computed_style or {}
    
    # Padding & Margin
    pad_top, pad_right, pad_bottom, pad_left = _parse_edge_insets(style.get("padding"))
    mar_top, mar_right, mar_bottom, mar_left = _parse_edge_insets(style.get("margin"))

    # Dimension resolution
    specified_w = _parse_box_dim(style.get("width"), container_w)
    specified_h = _parse_box_dim(style.get("height"), container_h)

    # Defaults: if root, match container; if child, default to 100% or auto
    node.layout_width = specified_w if specified_w is not None else max(0.0, container_w - mar_left - mar_right)
    node.layout_height = specified_h if specified_h is not None else max(0.0, container_h - mar_top - mar_bottom)

    # Absolute Screen Bounds
    node.abs_x = origin_x + mar_left
    node.abs_y = origin_y + mar_top
    node.abs_width = node.layout_width
    node.abs_height = node.layout_height

    if not node.children:
        return

    # Inner Content Area for Children
    inner_x = node.abs_x + pad_left
    inner_y = node.abs_y + pad_top
    inner_w = max(0.0, node.layout_width - pad_left - pad_right)
    inner_h = max(0.0, node.layout_height - pad_top - pad_bottom)

    # Flex Layout
    flex_dir = str(style.get("flex-direction", "column")).lower()
    justify = str(style.get("justify-content", "flex-start")).lower()
    align_items = str(style.get("align-items", "stretch")).lower()
    gap = float(style.get("gap", 0.0))

    is_row = (flex_dir == "row")

    # Step 1: Pre-calculate child intrinsic or specified sizes
    child_sizes: List[Tuple[float, float]] = []
    total_main_size = 0.0

    for child in node.children:
        c_style = child.computed_style or {}
        cw = _parse_box_dim(c_style.get("width"), inner_w)
        ch = _parse_box_dim(c_style.get("height"), inner_h)
        
        # Default auto child dimensions
        resolved_cw = cw if cw is not None else (inner_w if not is_row else 40.0)
        resolved_ch = ch if ch is not None else (30.0 if not is_row else inner_h)

        child_sizes.append((resolved_cw, resolved_ch))
        total_main_size += (resolved_cw if is_row else resolved_ch)

    if len(node.children) > 1:
        total_main_size += gap * (len(node.children) - 1)

    # Step 2: Main-axis positioning (Justify-content)
    curr_main = 0.0
    spacing = gap
    main_avail = inner_w if is_row else inner_h

    if justify == "center":
        curr_main = max(0.0, (main_avail - total_main_size) / 2.0)
    elif justify == "flex-end":
        curr_main = max(0.0, main_avail - total_main_size)
    elif justify == "space-between" and len(node.children) > 1:
        remaining = max(0.0, main_avail - (total_main_size - gap * (len(node.children) - 1)))
        spacing = remaining / (len(node.children) - 1)

    # Step 3: Position each child
    for i, child in enumerate(node.children):
        cw, ch = child_sizes[i]

        # Cross-axis positioning (Align-items)
        cross_avail = inner_h if is_row else inner_w
        curr_cross = 0.0
        
        if is_row:
            if align_items == "center":
                curr_cross = (cross_avail - ch) / 2.0
            elif align_items == "flex-end":
                curr_cross = cross_avail - ch
            elif align_items == "stretch" and _parse_box_dim(child.computed_style.get("height"), inner_h) is None:
                ch = cross_avail

            child_x = inner_x + curr_main
            child_y = inner_y + curr_cross
            curr_main += cw + spacing
        else:
            if align_items == "center":
                curr_cross = (cross_avail - cw) / 2.0
            elif align_items == "flex-end":
                curr_cross = cross_avail - cw
            elif align_items == "stretch" and _parse_box_dim(child.computed_style.get("width"), inner_w) is None:
                cw = cross_avail

            child_x = inner_x + curr_cross
            child_y = inner_y + curr_main
            curr_main += ch + spacing

        # Recurse layout for child
        compute_layout(child, cw, ch, child_x, child_y)
