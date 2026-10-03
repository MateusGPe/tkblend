"""
Pure Blend2D Vector Data Table widget powered by BaseControl.
"""

from __future__ import annotations

import sys
import tkinter as tk
from typing import Optional, Callable, Dict, List, Any, Union, Tuple, Set

from tkblend.widgets.base import BaseControl
from tkblend.widgets.scrollable_frame import VectorScrollbar
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    blend_color_hex,
    to_tk_hex,
)
from tkblend.font import parse_font
from tkblend.widgets.constants import (
    DEFAULT_FONT_SIZE,
    CURSOR_HAND,
    CURSOR_DEFAULT,
)
from tkblend.widgets.utils import compute_text_baseline_y


class Table(BaseControl):
    """
    Modern vector data grid featuring sortable headers, alternating row colors,
    selection highlight, custom column widths, and integrated vector scrolling.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        columns: Optional[List[Union[str, Dict[str, Any]]]] = None,
        data: Optional[List[Any]] = None,
        command: Optional[Callable[[int, Any], None]] = None,
        on_select: Optional[Callable[[int, Any], None]] = None,
        row_height: int = 32,
        header_height: int = 34,
        corner_radius: float = 8.0,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        width: int = 500,
        height: int = 260,
        cursor: Optional[str] = None,
        **kwargs,
    ):
        self._row_height = int(row_height)
        self._header_height = int(header_height)
        self._corner_radius = float(corner_radius)
        self._custom_bg = bg_color
        self._custom_border = border_color
        self._border_width = float(border_width)
        self._command = command or on_select

        self._columns: List[Dict[str, Any]] = []
        self._data: List[Any] = []
        self._selected_indices: Set[int] = set()
        self._hovered_row: Optional[int] = None
        self._sort_col: Optional[int] = None
        self._sort_desc: bool = False
        self._scroll_offset_y: float = 0.0

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor or CURSOR_DEFAULT,
            takefocus=True,
            **kwargs,
        )

        # Vector scrollbar
        self._v_scrollbar = VectorScrollbar(
            self,
            orientation="vertical",
            width=8,
            command=self._on_scrollbar_move,
        )
        self._v_scrollbar.place(relx=1.0, y=self._header_height, relheight=1.0, x=-10, width=8, height=-self._header_height - 4)

        if columns:
            self.set_columns(columns)
        if data:
            self.set_data(data)

        self.bind("<Button-1>", self._on_click)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-4>", self._on_mousewheel)
        self.bind("<Button-5>", self._on_mousewheel)

    @property
    def bg_color(self) -> str:
        return resolve_color_failsafe(self._custom_bg or self._palette.card_bg, palette=self._palette)

    def set_columns(self, columns: List[Union[str, Dict[str, Any]]]) -> None:
        cols = []
        for col in columns:
            if isinstance(col, str):
                cols.append({"name": col, "title": col, "width": 100})
            elif isinstance(col, dict):
                cols.append({
                    "name": col.get("name", col.get("id", "")),
                    "title": col.get("title", col.get("name", "")),
                    "width": col.get("width", 100),
                })
        self._columns = cols
        self.request_redraw()

    def set_data(self, data: List[Any]) -> None:
        self._data = list(data)
        self._selected_indices.clear()
        self._scroll_offset_y = 0.0
        self._update_scrollbar()
        self.request_redraw()

    def insert_row(self, row: Any, index: Optional[int] = None) -> None:
        if index is None or index >= len(self._data):
            self._data.append(row)
        else:
            self._data.insert(index, row)
        self._update_scrollbar()
        self.request_redraw()

    def delete_row(self, index: int) -> None:
        if 0 <= index < len(self._data):
            self._data.pop(index)
            self._selected_indices.discard(index)
            self._update_scrollbar()
            self.request_redraw()

    def clear(self) -> None:
        self._data.clear()
        self._selected_indices.clear()
        self._scroll_offset_y = 0.0
        self._update_scrollbar()
        self.request_redraw()

    def get_selected_index(self) -> Optional[int]:
        return next(iter(self._selected_indices)) if self._selected_indices else None

    def get_selected_indices(self) -> List[int]:
        return sorted(list(self._selected_indices))

    def get_selected_row(self) -> Optional[Any]:
        idx = self.get_selected_index()
        return self._data[idx] if idx is not None and 0 <= idx < len(self._data) else None

    def set_selection(self, index: int) -> None:
        self._selected_indices = {index} if 0 <= index < len(self._data) else set()
        self.request_redraw()

    def clear_selection(self) -> None:
        self._selected_indices.clear()
        self.request_redraw()

    def sort_by(self, col_index: int, descending: Optional[bool] = None) -> None:
        if not (0 <= col_index < len(self._columns)):
            return
        if descending is None:
            if self._sort_col == col_index:
                self._sort_desc = not self._sort_desc
            else:
                self._sort_desc = False
        else:
            self._sort_desc = descending
        self._sort_col = col_index

        col_key = self._columns[col_index]["name"]

        def get_val(row):
            if isinstance(row, dict):
                return str(row.get(col_key, ""))
            elif isinstance(row, (list, tuple)) and col_index < len(row):
                return str(row[col_index])
            return ""

        self._data.sort(key=get_val, reverse=self._sort_desc)
        self.request_redraw()

    def _update_scrollbar(self) -> None:
        total_rows = len(self._data)
        visible_rows = max(1, int((self.winfo_height() - self._header_height) / max(1, self._row_height)))
        if total_rows <= visible_rows:
            self._v_scrollbar.set(0.0, 1.0)
        else:
            first = self._scroll_offset_y / max(1, total_rows)
            span = visible_rows / total_rows
            self._v_scrollbar.set(first, min(1.0, first + span))

    def _on_scrollbar_move(self, action: str, *args) -> None:
        if action == "moveto" and args:
            frac = float(args[0])
            total_rows = len(self._data)
            self._scroll_offset_y = max(0.0, min(float(total_rows - 1), frac * total_rows))
            self._update_scrollbar()
            self.request_redraw()

    def _on_mousewheel(self, event) -> None:
        total_rows = len(self._data)
        if event.num == 4 or event.delta > 0:
            self._scroll_offset_y = max(0.0, self._scroll_offset_y - 2.0)
        elif event.num == 5 or event.delta < 0:
            self._scroll_offset_y = min(max(0.0, float(total_rows - 3)), self._scroll_offset_y + 2.0)
        self._update_scrollbar()
        self.request_redraw()

    def _on_click(self, event) -> None:
        s = self._scale_factor
        hdr_h = self._header_height * s
        y = event.y

        # Header click -> sort
        if y <= hdr_h:
            x = event.x
            cur_x = 0.0
            total_col_w = sum(c["width"] for c in self._columns) * s
            usable_w = float(self.winfo_width()) - 16.0 * s
            scale_w = usable_w / max(1.0, total_col_w) if total_col_w > 0 else 1.0

            for idx, col in enumerate(self._columns):
                w = col["width"] * s * scale_w
                if cur_x <= x <= cur_x + w:
                    self.sort_by(idx)
                    break
                cur_x += w
            return

        # Row click
        row_h = self._row_height * s
        row_idx = int((y - hdr_h) / row_h + self._scroll_offset_y)
        if 0 <= row_idx < len(self._data):
            self.set_selection(row_idx)
            if self._command:
                try:
                    self._command(row_idx, self._data[row_idx])
                except Exception:
                    pass

    def _on_motion(self, event) -> None:
        s = self._scale_factor
        hdr_h = self._header_height * s
        y = event.y
        if y > hdr_h:
            row_h = self._row_height * s
            row_idx = int((y - hdr_h) / row_h + self._scroll_offset_y)
            if 0 <= row_idx < len(self._data):
                if row_idx != self._hovered_row:
                    self._hovered_row = row_idx
                    self.request_redraw()
                return
        if self._hovered_row is not None:
            self._hovered_row = None
            self.request_redraw()

    def _on_leave(self, event) -> None:
        if self._hovered_row is not None:
            self._hovered_row = None
            self.request_redraw()

    def on_theme_update(self, pal: Palette) -> None:
        if hasattr(self, "_v_scrollbar") and self._v_scrollbar.winfo_exists():
            self._v_scrollbar.set_parent_bg(self.bg_color)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        cr = self._corner_radius * s
        bg_col = resolve_color_failsafe(self._custom_bg or pal.card_bg, palette=pal)
        border_col = resolve_color_failsafe(self._custom_border or pal.card_border, palette=pal)
        hdr_bg = blend_color_hex(bg_col, pal.fg, 0.05)

        # 1. Main Table Background & Border
        surf.clear(self._resolved_parent_bg)
        surf.fill_rounded_rect(0.0, 0.0, w, h, cr, cr, bg_col)
        if self._border_width > 0.0:
            surf.stroke_rounded_rect(0.0, 0.0, w, h, cr, cr, border_col, stroke_width=self._border_width * s)

        # Column scaling
        total_col_w = sum(c.get("width", 100) for c in self._columns) * s
        usable_w = w - 16.0 * s
        scale_w = usable_w / max(1.0, total_col_w) if total_col_w > 0 else 1.0

        hdr_h = self._header_height * s
        font_cfg = parse_font(font_size=11.0, bold=True)
        hdr_font_sz = 11.0 * s

        # 2. Header
        surf.fill_rounded_rect(0.0, 0.0, w, hdr_h, cr, cr, hdr_bg)
        surf.stroke_line(0.0, hdr_h, w, hdr_h, border_col, stroke_width=1.0 * s)

        cur_x = 8.0 * s
        for idx, col in enumerate(self._columns):
            col_w = col.get("width", 100) * s * scale_w
            title = col.get("title", col.get("name", ""))

            # Header text
            text_y = compute_text_baseline_y(hdr_h / 2.0, hdr_font_sz)
            surf.draw_text(
                title,
                cur_x,
                text_y,
                font_size=hdr_font_sz,
                font_family=font_cfg.family,
                color=pal.fg,
                bold=True,
                align="left",
            )

            # Sort icon
            if self._sort_col == idx:
                icon_name = "chevron-down" if self._sort_desc else "chevron-up"
                surf.draw_icon(
                    icon_name,
                    cur_x + col_w - 14.0 * s,
                    hdr_h / 2.0 + 3.0 * s,
                    size=10.0 * s,
                    color=pal.primary,
                    align="center",
                )

            cur_x += col_w

        # 3. Rows
        row_h = self._row_height * s
        row_font_cfg = parse_font(font_size=11.0, bold=False)
        row_font_sz = 11.0 * s
        start_row = int(self._scroll_offset_y)

        for i in range(start_row, len(self._data)):
            row_y = hdr_h + (i - self._scroll_offset_y) * row_h
            if row_y + row_h > h:
                break

            is_selected = (i in self._selected_indices)
            is_hover = (i == self._hovered_row and not is_selected)

            # Row background
            if is_selected:
                surf.fill_rect(0.0, row_y, usable_w, row_h, blend_color_hex(pal.primary, bg_col, 0.25))
            elif is_hover:
                surf.fill_rect(0.0, row_y, usable_w, row_h, blend_color_hex(bg_col, pal.fg, 0.04))
            elif i % 2 == 1:
                surf.fill_rect(0.0, row_y, usable_w, row_h, blend_color_hex(bg_col, pal.fg, 0.02))

            # Row divider
            surf.stroke_line(0.0, row_y + row_h, usable_w, row_y + row_h, blend_color_hex(border_col, bg_col, 0.3), stroke_width=1.0 * s)

            # Row cells
            row_data = self._data[i]
            cur_x = 8.0 * s
            for col_idx, col in enumerate(self._columns):
                col_w = col.get("width", 100) * s * scale_w
                col_name = col.get("name", "")

                if isinstance(row_data, dict):
                    cell_val = str(row_data.get(col_name, ""))
                elif isinstance(row_data, (list, tuple)) and col_idx < len(row_data):
                    cell_val = str(row_data[col_idx])
                else:
                    cell_val = ""

                cell_y = compute_text_baseline_y(row_y + row_h / 2.0, row_font_sz)
                surf.draw_text(
                    cell_val,
                    cur_x,
                    cell_y,
                    font_size=row_font_sz,
                    font_family=row_font_cfg.family,
                    color=pal.fg if not is_selected else pal.primary,
                    bold=is_selected,
                    align="left",
                )
                cur_x += col_w
