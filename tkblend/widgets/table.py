"""
Table - Full-featured vector data grid widget powered by Blend2D C++ rendering.
"""

from __future__ import annotations
import sys
import tkinter as tk
from typing import Optional, Callable, Dict, List, Any, Union, Tuple

from tkblend.surface import ColorLike
from tkblend.theme import (
    get_theme,
    Palette,
    add_theme_listener,
    remove_theme_listener,
    blend_color_hex,
)
from tkblend.widgets.base import Widget, ScalingTracker
from tkblend.widgets.containers import Frame
from tkblend.widgets.scrollbar import VectorScrollbar
from tkblend.widgets.drawing import draw_vector_chevron, truncate_text


class _TableViewSurface(Widget):
    """Internal Blend2D surface rendering headers and rows for Table."""

    def __init__(
        self,
        master: tk.Misc,
        table: Table,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._table = table
        super().__init__(
            master=master,
            width=300,
            height=200,
            bg=parent_bg,
            **kwargs,
        )
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<ButtonPress-1>", self._on_press)

    def _on_mouse_move(self, event) -> None:
        s = self._scale
        hdr_h = self._table._header_height * s
        row_h = self._table._row_height * s

        # Check if hovering header or rows
        if event.y < hdr_h:
            # Hover header column
            col_idx = self._table._get_col_at_x(event.x + self._table._scroll_x)
            if col_idx != self._table._hovered_col:
                self._table._hovered_col = col_idx
                self._table._hovered_row = None
                self.render()
        else:
            # Hover row
            content_y = event.y - hdr_h + self._table._scroll_y
            row_idx = int(content_y // row_h)
            if 0 <= row_idx < len(self._table._data):
                if row_idx != self._table._hovered_row:
                    self._table._hovered_row = row_idx
                    self._table._hovered_col = None
                    self.render()
            else:
                if self._table._hovered_row is not None:
                    self._table._hovered_row = None
                    self.render()

    def _on_mouse_leave(self, event) -> None:
        self._table._hovered_row = None
        self._table._hovered_col = None
        self.render()

    def _on_press(self, event) -> None:
        s = self._scale
        hdr_h = self._table._header_height * s
        row_h = self._table._row_height * s

        if event.y < hdr_h:
            col_idx = self._table._get_col_at_x(event.x + self._table._scroll_x)
            if col_idx is not None:
                self._table._on_header_click(col_idx)
        else:
            content_y = event.y - hdr_h + self._table._scroll_y
            row_idx = int(content_y // row_h)
            if 0 <= row_idx < len(self._table._data):
                self._table.set_selection(row_idx)

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            self._surface.clear(self._parent_bg)
            s = self._scale
            w = float(self._widget_w)
            h = float(self._widget_h)
            pal = get_theme()

            cols = self._table._columns
            data = self._table._data
            scroll_x = self._table._scroll_x
            scroll_y = self._table._scroll_y
            hdr_h = self._table._header_height * s
            row_h = self._table._row_height * s

            # Calculate total content width
            total_content_w = sum(c.get("width", 100) * s for c in cols)
            draw_w = max(w, total_content_w)

            # 1. Header Background & Border
            self._surface.fill_rect(0, 0, w, hdr_h, pal.surface)
            self._surface.fill_rect(0, hdr_h - 1.0 * s, w, 1.0 * s, pal.surface_border)

            # Draw Header Columns
            curr_x = -scroll_x
            font_sz_hdr = max(9.0, 11.0 * s)
            for i, col in enumerate(cols):
                cw = col.get("width", 100) * s
                title = col.get("title", f"Col {i}")
                align = col.get("align", "left")

                if curr_x + cw > 0 and curr_x < w:
                    # Hover on column header
                    if self._table._hovered_col == i:
                        self._surface.fill_rect(max(0.0, curr_x), 0, cw, hdr_h - 1.0 * s, pal.secondary)

                    # Text
                    ty = hdr_h / 2.0 + font_sz_hdr * 0.35
                    if align == "center":
                        tx = curr_x + cw / 2.0
                    elif align == "right":
                        tx = curr_x + cw - 12.0 * s
                    else:
                        tx = curr_x + 10.0 * s

                    display_txt = truncate_text(title, max(10.0, cw - 28.0 * s), font_sz_hdr)
                    self._surface.draw_text(
                        display_txt, tx, ty,
                        font_size=font_sz_hdr,
                        font_family="sans-serif",
                        color=pal.fg,
                        align=align,
                    )

                    # Sort chevron if sorted by this column
                    if self._table._sort_col == i:
                        chev_dir = "down" if self._table._sort_desc else "up"
                        draw_vector_chevron(
                            self._surface,
                            curr_x + cw - 12.0 * s,
                            hdr_h / 2.0,
                            scale=0.9 * s,
                            direction=chev_dir,
                            color=pal.primary,
                            stroke_width=1.6 * s,
                        )

                    # Column separator
                    self._surface.fill_rect(curr_x + cw - 1.0 * s, 4.0 * s, 1.0 * s, hdr_h - 8.0 * s, pal.surface_border)

                curr_x += cw

            # 2. Render Visible Rows
            font_sz_row = max(9.0, 11.0 * s)
            visible_start_idx = max(0, int(scroll_y // row_h))
            visible_end_idx = min(len(data), int((scroll_y + h - hdr_h) // row_h) + 2)

            for r_idx in range(visible_start_idx, visible_end_idx):
                row = data[r_idx]
                ry = hdr_h + (r_idx * row_h) - scroll_y

                # Background & Selection
                if r_idx == self._table._selected_row:
                    row_bg = blend_color_hex(pal.secondary, pal.primary, 0.25)
                    self._surface.fill_rect(0, ry, w, row_h, row_bg)
                    # Selected left accent bar
                    self._surface.fill_rect(0, ry, 3.0 * s, row_h, pal.primary)
                elif r_idx == self._table._hovered_row:
                    self._surface.fill_rect(0, ry, w, row_h, pal.secondary)
                else:
                    stripe_bg = pal.card_bg if (r_idx % 2 == 0) else pal.surface
                    self._surface.fill_rect(0, ry, w, row_h, stripe_bg)

                # Row bottom divider
                self._surface.fill_rect(0, ry + row_h - 1.0 * s, w, 1.0 * s, pal.surface_border)

                # Draw Cells
                cell_x = -scroll_x
                for c_idx, col in enumerate(cols):
                    cw = col.get("width", 100) * s
                    align = col.get("align", "left")
                    col_id = col.get("id", str(c_idx))

                    # Extract cell text
                    if isinstance(row, dict):
                        cell_val = str(row.get(col_id, ""))
                    elif isinstance(row, (list, tuple)) and c_idx < len(row):
                        cell_val = str(row[c_idx])
                    else:
                        cell_val = ""

                    if cell_x + cw > 0 and cell_x < w:
                        ty = ry + row_h / 2.0 + font_sz_row * 0.35
                        if align == "center":
                            tx = cell_x + cw / 2.0
                        elif align == "right":
                            tx = cell_x + cw - 10.0 * s
                        else:
                            tx = cell_x + 10.0 * s

                        txt_color = pal.primary if r_idx == self._table._selected_row else pal.fg
                        display_cell = truncate_text(cell_val, max(10.0, cw - 18.0 * s), font_sz_row)
                        self._surface.draw_text(
                            display_cell, tx, ty,
                            font_size=font_sz_row,
                            font_family="sans-serif",
                            color=txt_color,
                            align=align,
                        )

                    cell_x += cw

            self._surface.blit(self._photo)
        except Exception:
            pass


class Table(tk.Frame):
    """
    High-performance vector data table with sortable columns, alternating stripes,
    row hover/selection, and integrated Blend2D vector scrollbars.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        columns: Optional[List[Dict[str, Any]]] = None,
        data: Optional[List[Union[Dict[str, Any], List[Any], Tuple[Any, ...]]]] = None,
        width: int = 400,
        height: int = 240,
        header_height: int = 34,
        row_height: int = 32,
        rx: float = 8.0,
        ry: float = 8.0,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        elevation: float = 4.0,
        on_select: Optional[Callable[[int, Any], None]] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._scale = ScalingTracker.get_scaling_factor(master)
        pal = get_theme()
        self._explicit_parent_bg = parent_bg
        self._parent_bg = parent_bg or Widget._resolve_default_bg(master, pal)
        self._columns = list(columns) if columns else [
            {"id": "col1", "title": "Column 1", "width": 120, "align": "left"},
            {"id": "col2", "title": "Column 2", "width": 140, "align": "left"},
        ]
        self._data = list(data) if data else []
        self._header_height = header_height
        self._row_height = row_height
        self._rx = rx
        self._ry = ry
        self._bg_color = bg_color
        self._border_color = border_color
        self._border_width = border_width
        self._elevation = elevation
        self._on_select = on_select

        self._selected_row: Optional[int] = None
        self._hovered_row: Optional[int] = None
        self._hovered_col: Optional[int] = None
        self._sort_col: Optional[int] = None
        self._sort_desc: bool = False

        self._scroll_x: float = 0.0
        self._scroll_y: float = 0.0

        super().__init__(
            master,
            width=max(1, int(width * self._scale)),
            height=max(1, int(height * self._scale)),
            background=self._parent_bg,
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )

        # Card container
        self._card = Frame(
            self,
            rx=self._rx,
            ry=self._ry,
            bg_color=self._bg_color or pal.card_bg,
            border_color=self._border_color or pal.card_border,
            border_width=self._border_width,
            elevation=self._elevation,
            parent_bg=self._parent_bg,
        )
        self._card.pack(fill="both", expand=True)

        # Vertical Scrollbar
        self._v_scrollbar = VectorScrollbar(
            self._card,
            command=self._on_vscroll,
            orientation="vertical",
            width=8,
            parent_bg=self._card.bg_color,
        )
        self._v_scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=2)

        # Vector Surface
        self._view = _TableViewSurface(
            self._card,
            table=self,
            parent_bg=self._card.bg_color,
        )
        self._view.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        # Wheel bindings
        self._view.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self._view.bind("<Button-4>", self._on_mousewheel_linux, add="+")
        self._view.bind("<Button-5>", self._on_mousewheel_linux, add="+")
        self._view.bind("<Configure>", self._on_view_resize, add="+")

        add_theme_listener(self._on_theme_changed)
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._update_scroll_geometry()

    def set_columns(self, columns: List[Dict[str, Any]]) -> None:
        """Set the table columns definition."""
        self._columns = list(columns)
        self._view.render()

    def set_data(self, data: List[Union[Dict[str, Any], List[Any], Tuple[Any, ...]]]) -> None:
        """Replace the entire dataset."""
        self._data = list(data)
        self._selected_row = None
        self._hovered_row = None
        self._update_scroll_geometry()
        self._view.render()

    def insert_row(self, row: Union[Dict[str, Any], List[Any], Tuple[Any, ...]], index: Optional[int] = None) -> None:
        """Insert a single row."""
        if index is None or index >= len(self._data):
            self._data.append(row)
        else:
            self._data.insert(index, row)
        self._update_scroll_geometry()
        self._view.render()

    def delete_row(self, index: int) -> None:
        """Delete row at specified index."""
        if 0 <= index < len(self._data):
            self._data.pop(index)
            if self._selected_row == index:
                self._selected_row = None
            elif self._selected_row is not None and self._selected_row > index:
                self._selected_row -= 1
            self._update_scroll_geometry()
            self._view.render()

    def clear(self) -> None:
        """Clear all rows."""
        self._data.clear()
        self._selected_row = None
        self._update_scroll_geometry()
        self._view.render()

    def get_selected_index(self) -> Optional[int]:
        """Return the index of the currently selected row, or None."""
        return self._selected_row

    def get_selected_row(self) -> Optional[Any]:
        """Return the data item of the currently selected row, or None."""
        if self._selected_row is not None and 0 <= self._selected_row < len(self._data):
            return self._data[self._selected_row]
        return None

    def set_selection(self, index: Optional[int]) -> None:
        """Select row by index."""
        if index is None or (0 <= index < len(self._data)):
            self._selected_row = index
            self._view.render()
            if self._on_select and self._selected_row is not None:
                row_val = self._data[self._selected_row]
                try:
                    self._on_select(self._selected_row, row_val)
                except TypeError:
                    self._on_select(row_val)

    def sort_by(self, col_index: int, descending: Optional[bool] = None) -> None:
        """Sort data rows by specified column."""
        if not (0 <= col_index < len(self._columns)):
            return
        col = self._columns[col_index]
        col_id = col.get("id", str(col_index))

        if descending is None:
            if self._sort_col == col_index:
                self._sort_desc = not self._sort_desc
            else:
                self._sort_desc = False
        else:
            self._sort_desc = descending
        self._sort_col = col_index

        def sort_key(row):
            if isinstance(row, dict):
                val = row.get(col_id, "")
            elif isinstance(row, (list, tuple)) and col_index < len(row):
                val = row[col_index]
            else:
                val = ""
            try:
                return (0, float(val))
            except (ValueError, TypeError):
                return (1, str(val).lower())

        self._data.sort(key=sort_key, reverse=self._sort_desc)
        self._view.render()

    def _on_header_click(self, col_index: int) -> None:
        self.sort_by(col_index)

    def _get_col_at_x(self, x: float) -> Optional[int]:
        s = self._scale
        curr_x = 0.0
        for i, col in enumerate(self._columns):
            cw = col.get("width", 100) * s
            if curr_x <= x <= curr_x + cw:
                return i
            curr_x += cw
        return None

    def _on_vscroll(self, action: str, *args) -> None:
        s = self._scale
        row_h = self._row_height * s
        total_h = len(self._data) * row_h
        view_h = max(1.0, float(self._view._widget_h - self._header_height * s))

        if action == "moveto" and args:
            fraction = float(args[0])
            self._scroll_y = max(0.0, min(total_h - view_h, fraction * total_h))
        elif action == "scroll" and len(args) >= 2:
            amount = float(args[0])
            what = args[1]
            if what == "units":
                self._scroll_y = max(0.0, min(total_h - view_h, self._scroll_y + amount * row_h))
            elif what == "pages":
                self._scroll_y = max(0.0, min(total_h - view_h, self._scroll_y + amount * view_h))

        self._update_scroll_geometry()
        self._view.render()

    def _on_mousewheel(self, event) -> None:
        s = self._scale
        row_h = self._row_height * s
        total_h = len(self._data) * row_h
        view_h = max(1.0, float(self._view._widget_h - self._header_height * s))

        delta = event.delta
        step = -1 * (delta / 120.0 if sys.platform != "darwin" else delta) * row_h
        self._scroll_y = max(0.0, min(total_h - view_h, self._scroll_y + step))
        self._update_scroll_geometry()
        self._view.render()

    def _on_mousewheel_linux(self, event) -> None:
        s = self._scale
        row_h = self._row_height * s
        total_h = len(self._data) * row_h
        view_h = max(1.0, float(self._view._widget_h - self._header_height * s))

        step = -row_h if event.num == 4 else row_h
        self._scroll_y = max(0.0, min(total_h - view_h, self._scroll_y + step))
        self._update_scroll_geometry()
        self._view.render()

    def _on_view_resize(self, event) -> None:
        self._update_scroll_geometry()

    def _update_scroll_geometry(self) -> None:
        s = self._scale
        row_h = self._row_height * s
        total_h = max(1.0, len(self._data) * row_h)
        view_h = max(1.0, float(self._view._widget_h - self._header_height * s))

        if total_h <= view_h:
            self._scroll_y = 0.0
            self._v_scrollbar.set(0.0, 1.0)
        else:
            first = self._scroll_y / total_h
            last = min(1.0, (self._scroll_y + view_h) / total_h)
            self._v_scrollbar.set(first, last)

    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        resolved_bg = self._explicit_parent_bg or Widget._resolve_default_bg(self.master, palette)
        self._parent_bg = resolved_bg
        self.configure(background=self._parent_bg)
        self._card.configure(background=self._parent_bg)
        self._view._parent_bg = self._card.bg_color
        self._view.render()

    def _on_destroy(self, event) -> None:
        if event.widget == self:
            remove_theme_listener(self._on_theme_changed)


ModernTable = Table
