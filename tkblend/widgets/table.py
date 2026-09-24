"""
Table - Full-featured vector data grid widget powered by Blend2D C++ rendering.
Features:
- High-performance vector rendering with zero TTK dependencies
- Column sorting, interactive drag-resizing, and auto-fitting
- Dual-axis vector scrollbars (vertical and horizontal)
- Multi-selection modes ('extended', 'single', 'multiple', 'none')
- Declarative cell types (text, badge/pill, progress bar, checkbox, icon) & custom callable renderers
- In-place cell editing with floating vector-styled editor and validation hooks
- Dynamic search/filter engine and built-in pagination
- Comprehensive keyboard navigation and clipboard export (Ctrl+C / TSV)
- High-DPI awareness and dynamic theme switching
"""

from __future__ import annotations
import logging
import sys
import tkinter as tk
from typing import Optional, Callable, Dict, List, Any, Union, Tuple, Set

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
from tkblend.widgets.drawing import (
    draw_vector_checkmark,
    draw_vector_chevron,
    truncate_text,
)

logger = logging.getLogger(__name__)


class _FloatingCellEditor(tk.Entry):
    """Floating Entry overlay for in-place cell editing within the Table."""

    def __init__(
        self,
        master: tk.Misc,
        table: Table,
        row_idx: int,
        col_idx: int,
        initial_value: str,
        x: int,
        y: int,
        width: int,
        height: int,
    ):
        pal = get_theme()
        super().__init__(
            master,
            font=("sans-serif", max(9, int(11 * table._scale))),
            bg=pal.surface,
            fg=pal.fg,
            insertbackground=pal.fg,
            selectbackground=pal.primary,
            selectforeground="#ffffff",
            relief="solid",
            highlightthickness=1,
            highlightbackground=pal.primary,
            highlightcolor=pal.primary,
            borderwidth=1,
        )
        self._table = table
        self._row_idx = row_idx
        self._col_idx = col_idx
        self._initial_value = initial_value
        self._is_committed = False

        self.insert(0, initial_value)
        self.select_range(0, tk.END)
        self.icursor(tk.END)

        self.place(x=x, y=y, width=width, height=height)
        self.focus_set()

        self.bind("<Return>", self._on_commit)
        self.bind("<KP_Enter>", self._on_commit)
        self.bind("<Escape>", self._on_cancel)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_commit(self, event=None) -> None:
        if self._is_committed:
            return
        self._is_committed = True
        new_val = self.get()
        self._destroy_and_callback(new_val, commit=True)

    def _on_cancel(self, event=None) -> None:
        if self._is_committed:
            return
        self._is_committed = True
        self._destroy_and_callback(self._initial_value, commit=False)

    def _on_focus_out(self, event=None) -> None:
        if not self._is_committed:
            self._is_committed = True
            new_val = self.get()
            self._destroy_and_callback(new_val, commit=True)

    def _destroy_and_callback(self, val: str, commit: bool) -> None:
        try:
            self.destroy()
        except Exception:
            pass
        self._table._on_editor_closed(self._row_idx, self._col_idx, self._initial_value, val, commit)


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
        # Mouse event bindings
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Double-Button-1>", self._on_double_click)

    def _get_divider_at_x(self, x: float, tolerance: float = 5.0) -> Optional[int]:
        """Return the column index if x is near the right divider edge of that column."""
        s = self._scale
        curr_x = -self._table._scroll_x
        for i, col in enumerate(self._table._columns):
            cw = col.get("width", 100) * s
            divider_x = curr_x + cw
            if abs(x - divider_x) <= tolerance * s:
                return i
            curr_x += cw
        return None

    def _on_mouse_move(self, event) -> None:
        s = self._scale
        hdr_h = self._table._header_height * s
        row_h = self._table._row_height * s

        # Check if hovering over header divider for resizing
        if event.y < hdr_h:
            divider_col = self._get_divider_at_x(event.x)
            if divider_col is not None and divider_col < len(self._table._columns):
                self.configure(cursor="sb_h_double_arrow")
            else:
                self.configure(cursor="")

            col_idx = self._table._get_col_at_x(event.x + self._table._scroll_x)
            if col_idx != self._table._hovered_col:
                self._table._hovered_col = col_idx
                self._table._hovered_row = None
                self.render()
        else:
            self.configure(cursor="")
            content_y = event.y - hdr_h + self._table._scroll_y
            row_idx = int(content_y // row_h)
            visible_rows = self._table._get_visible_data()
            if 0 <= row_idx < len(visible_rows):
                if row_idx != self._table._hovered_row:
                    self._table._hovered_row = row_idx
                    self._table._hovered_col = None
                    self.render()
            else:
                if self._table._hovered_row is not None:
                    self._table._hovered_row = None
                    self.render()

    def _on_mouse_leave(self, event) -> None:
        self.configure(cursor="")
        self._table._hovered_row = None
        self._table._hovered_col = None
        self.render()

    def _on_press(self, event) -> None:
        self.focus_set()
        s = self._scale
        hdr_h = self._table._header_height * s
        row_h = self._table._row_height * s

        if event.y < hdr_h:
            divider_col = self._get_divider_at_x(event.x)
            if divider_col is not None:
                # Start resizing column
                self._table._resizing_col = divider_col
                self._table._resize_start_x = event.x
                self._table._resize_orig_width = self._table._columns[divider_col].get("width", 100)
                return

            col_idx = self._table._get_col_at_x(event.x + self._table._scroll_x)
            if col_idx is not None:
                self._table._on_header_click(col_idx)
        else:
            content_y = event.y - hdr_h + self._table._scroll_y
            row_idx = int(content_y // row_h)
            visible_rows = self._table._get_visible_data()
            if 0 <= row_idx < len(visible_rows):
                col_idx = self._table._get_col_at_x(event.x + self._table._scroll_x)
                raw_idx = self._table._get_raw_index(row_idx)

                # Check if checkbox column clicked
                if col_idx is not None and 0 <= col_idx < len(self._table._columns):
                    col = self._table._columns[col_idx]
                    if col.get("type") == "checkbox":
                        col_id = col.get("id", str(col_idx))
                        curr_val = self._table.get_cell_value(raw_idx, col_id)
                        new_val = not bool(curr_val)
                        self._table.set_cell_value(raw_idx, col_id, new_val)
                        if self._table._on_cell_edit:
                            try:
                                self._table._on_cell_edit(raw_idx, col_id, curr_val, new_val)
                            except Exception as e:
                                logger.debug("on_cell_edit callback error: %s", e)
                        self.render()
                        return

                self._table._handle_row_click(raw_idx, event.state)

    def _on_drag(self, event) -> None:
        if self._table._resizing_col is not None:
            col_idx = self._table._resizing_col
            s = self._scale
            delta_px = (event.x - self._table._resize_start_x) / s
            col = self._table._columns[col_idx]
            min_w = col.get("min_width", 40)
            new_w = max(min_w, int(self._table._resize_orig_width + delta_px))
            col["width"] = new_w
            self._table._update_scroll_geometry()
            self.render()

    def _on_release(self, event) -> None:
        if self._table._resizing_col is not None:
            self._table._resizing_col = None
            self._table._update_scroll_geometry()
            self.render()

    def _on_double_click(self, event) -> None:
        s = self._scale
        hdr_h = self._table._header_height * s
        row_h = self._table._row_height * s

        if event.y < hdr_h:
            # Check divider double-click for auto-fit
            divider_col = self._get_divider_at_x(event.x)
            if divider_col is not None:
                self._table.auto_fit_column(divider_col)
                return
        else:
            content_y = event.y - hdr_h + self._table._scroll_y
            row_idx = int(content_y // row_h)
            visible_rows = self._table._get_visible_data()
            if 0 <= row_idx < len(visible_rows):
                raw_idx = self._table._get_raw_index(row_idx)
                col_idx = self._table._get_col_at_x(event.x + self._table._scroll_x)
                if col_idx is not None:
                    col = self._table._columns[col_idx]
                    if col.get("editable", False):
                        self._table._start_cell_edit(raw_idx, col_idx, row_idx)
                        return

                if self._table._on_double_click:
                    try:
                        self._table._on_double_click(raw_idx, self._table._data[raw_idx])
                    except Exception as e:
                        logger.debug("on_double_click error: %s", e)

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
            visible_data = self._table._get_visible_data()
            scroll_x = self._table._scroll_x
            scroll_y = self._table._scroll_y
            hdr_h = self._table._header_height * s
            row_h = self._table._row_height * s

            # 1. Render Visible Rows
            font_sz_row = max(9.0, 11.0 * s)
            visible_start_idx = max(0, int(scroll_y // row_h))
            visible_end_idx = min(len(visible_data), int((scroll_y + h - hdr_h) // row_h) + 2)

            for r_idx in range(visible_start_idx, visible_end_idx):
                row = visible_data[r_idx]
                raw_idx = self._table._get_raw_index(r_idx)
                ry = hdr_h + (r_idx * row_h) - scroll_y
                is_selected = raw_idx in self._table._selected_rows

                # Background & Selection Highlight
                if is_selected:
                    row_bg = blend_color_hex(pal.secondary, pal.primary, 0.22)
                    self._surface.fill_rect(0, ry, w, row_h, row_bg)
                    # Selected left accent bar
                    self._surface.fill_rect(0, ry, 3.5 * s, row_h, pal.primary)
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
                    col_type = col.get("type", "text")
                    renderer = col.get("renderer")

                    # Extract raw cell value
                    if isinstance(row, dict):
                        cell_raw_val = row.get(col_id, "")
                    elif isinstance(row, (list, tuple)) and c_idx < len(row):
                        cell_raw_val = row[c_idx]
                    else:
                        cell_raw_val = ""

                    if cell_x + cw > 0 and cell_x < w:
                        # 1. Custom Callable Renderer
                        if callable(renderer):
                            try:
                                renderer(
                                    self._surface,
                                    cell_x,
                                    ry,
                                    cw,
                                    row_h,
                                    cell_raw_val,
                                    is_selected,
                                    pal,
                                )
                            except Exception as e:
                                logger.debug("Custom renderer exception: %s", e)

                        # 2. Checkbox Type
                        elif col_type == "checkbox":
                            cb_sz = 14.0 * s
                            cb_px = cell_x + (cw - cb_sz) / 2.0
                            cb_py = ry + (row_h - cb_sz) / 2.0
                            val_bool = bool(cell_raw_val)
                            self._surface.stroke_rounded_rect(
                                cb_px, cb_py, cb_sz, cb_sz, 3.0 * s, 3.0 * s, pal.surface_border, stroke_width=1.2 * s
                            )
                            if val_bool:
                                self._surface.fill_rounded_rect(
                                    cb_px, cb_py, cb_sz, cb_sz, 3.0 * s, 3.0 * s, pal.primary
                                )
                                draw_vector_checkmark(
                                    self._surface, cb_px + cb_sz / 2.0, cb_py + cb_sz / 2.0, 0.8 * s, "#ffffff"
                                )

                        # 3. Badge / Pill Type
                        elif col_type in ("badge", "pill"):
                            badge_str = str(cell_raw_val)
                            badge_colors = col.get("badge_colors", {})
                            badge_bg = (
                                badge_colors.get(badge_str)
                                or col.get("badge_bg")
                                or pal.secondary
                            )
                            badge_fg = col.get("badge_fg", pal.fg)
                            b_h = min(20.0 * s, row_h - 10.0 * s)
                            b_font_sz = max(8.5, 9.5 * s)
                            b_w = max(40.0 * s, len(badge_str) * b_font_sz * 0.65 + 16.0 * s)
                            b_w = min(b_w, max(20.0 * s, cw - 16.0 * s))

                            if align == "center":
                                bx = cell_x + (cw - b_w) / 2.0
                            elif align == "right":
                                bx = cell_x + cw - b_w - 10.0 * s
                            else:
                                bx = cell_x + 10.0 * s

                            by = ry + (row_h - b_h) / 2.0
                            self._surface.fill_rounded_rect(bx, by, b_w, b_h, b_h / 2.0, b_h / 2.0, badge_bg)
                            self._surface.draw_text(
                                truncate_text(badge_str, b_w - 8.0 * s, b_font_sz),
                                bx + b_w / 2.0,
                                by + b_h / 2.0 + b_font_sz * 0.35,
                                font_size=b_font_sz,
                                font_family="sans-serif",
                                color=badge_fg,
                                align="center",
                            )

                        # 4. Progress Bar Type
                        elif col_type in ("progress", "progress_bar"):
                            try:
                                if isinstance(cell_raw_val, (int, float)):
                                    pct = float(cell_raw_val)
                                    if pct <= 1.0 and pct > 0:
                                        pct = pct * 100.0
                                else:
                                    pct = float(str(cell_raw_val).replace("%", "").strip())
                            except Exception:
                                pct = 0.0
                            pct = max(0.0, min(100.0, pct))
                            bar_h = 8.0 * s
                            bar_w = max(20.0 * s, cw - 46.0 * s)
                            bx = cell_x + 8.0 * s
                            by = ry + (row_h - bar_h) / 2.0

                            track_col = "#2a2a3e" if pal.dark_mode else "#e2e8f0"
                            self._surface.fill_rounded_rect(bx, by, bar_w, bar_h, bar_h / 2.0, bar_h / 2.0, track_col)
                            fill_w = (pct / 100.0) * bar_w
                            if fill_w > 0:
                                bar_color = col.get("bar_color", pal.primary)
                                self._surface.fill_rounded_rect(
                                    bx, by, fill_w, bar_h, bar_h / 2.0, bar_h / 2.0, bar_color
                                )

                            # Percentage text
                            txt_x = bx + bar_w + 6.0 * s
                            txt_y = ry + row_h / 2.0 + font_sz_row * 0.35
                            self._surface.draw_text(
                                f"{int(pct)}%",
                                txt_x,
                                txt_y,
                                font_size=max(8.0, 9.5 * s),
                                font_family="sans-serif",
                                color=pal.fg,
                                align="left",
                            )

                        # 5. Standard Formatted Text
                        else:
                            formatter = col.get("formatter")
                            if callable(formatter):
                                try:
                                    cell_val = formatter(cell_raw_val)
                                except Exception:
                                    cell_val = str(cell_raw_val)
                            else:
                                cell_val = str(cell_raw_val)

                            ty = ry + row_h / 2.0 + font_sz_row * 0.35
                            if align == "center":
                                tx = cell_x + cw / 2.0
                            elif align == "right":
                                tx = cell_x + cw - 10.0 * s
                            else:
                                tx = cell_x + 10.0 * s

                            txt_color = pal.primary if is_selected else pal.fg
                            display_cell = truncate_text(cell_val, max(10.0, cw - 18.0 * s), font_sz_row)
                            self._surface.draw_text(
                                display_cell,
                                tx,
                                ty,
                                font_size=font_sz_row,
                                font_family="sans-serif",
                                color=txt_color,
                                align=align,
                            )

                    cell_x += cw

            # 2. Sticky Header Background, Border & Header Columns
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
                    if self._table._hovered_col == i and self._table._resizing_col is None:
                        self._surface.fill_rect(max(0.0, curr_x), 0, cw, hdr_h - 1.0 * s, pal.secondary)

                    # Header text & checkbox
                    if col.get("type") == "checkbox":
                        # Draw header checkbox (select all indicator)
                        cb_size = 14.0 * s
                        cb_x = curr_x + (cw - cb_size) / 2.0
                        cb_y = (hdr_h - cb_size) / 2.0
                        all_checked = (
                            len(self._table._selected_rows) > 0
                            and len(self._table._selected_rows) == len(self._table._data)
                        )
                        self._surface.stroke_rounded_rect(
                            cb_x, cb_y, cb_size, cb_size, 3.0 * s, 3.0 * s, pal.surface_border, stroke_width=1.2 * s
                        )
                        if all_checked:
                            self._surface.fill_rounded_rect(
                                cb_x, cb_y, cb_size, cb_size, 3.0 * s, 3.0 * s, pal.primary
                            )
                            draw_vector_checkmark(
                                self._surface, cb_x + cb_size / 2.0, cb_y + cb_size / 2.0, 0.8 * s, "#ffffff"
                            )
                    else:
                        ty = hdr_h / 2.0 + font_sz_hdr * 0.35
                        if align == "center":
                            tx = curr_x + cw / 2.0
                        elif align == "right":
                            tx = curr_x + cw - 14.0 * s
                        else:
                            tx = curr_x + 10.0 * s

                        display_txt = truncate_text(title, max(10.0, cw - 28.0 * s), font_sz_hdr)
                        self._surface.draw_text(
                            display_txt,
                            tx,
                            ty,
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

                    # Column separator divider
                    self._surface.fill_rect(
                        curr_x + cw - 1.0 * s, 4.0 * s, 1.0 * s, hdr_h - 8.0 * s, pal.surface_border
                    )

                curr_x += cw

            self._surface.blit(self._photo)
        except Exception as e:
            logger.debug("Render failed in _TableViewSurface: %s", e, exc_info=True)


class Table(tk.Frame):
    """
    High-performance vector data table with sortable & resizable columns,
    dual-axis vector scrollbars, multi-selection, in-place cell editing,
    filtering, pagination, and keyboard navigation.
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
        select_mode: str = "extended",
        pagination: bool = False,
        page_size: Optional[int] = None,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        elevation: float = 4.0,
        on_select: Optional[Callable[..., None]] = None,
        on_double_click: Optional[Callable[[int, Any], None]] = None,
        on_cell_edit: Optional[Callable[[int, str, Any, Any], None]] = None,
        on_cell_validate: Optional[Callable[[int, str, Any, Any], bool]] = None,
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
        self._select_mode = select_mode  # "extended", "single", "multiple", "none"
        self._pagination = pagination or (page_size is not None)
        self._page_size = page_size or 20
        self._current_page = 0

        self._bg_color = bg_color
        self._border_color = border_color
        self._border_width = border_width
        self._elevation = elevation

        self._on_select = on_select
        self._on_double_click = on_double_click
        self._on_cell_edit = on_cell_edit
        self._on_cell_validate = on_cell_validate

        # State tracking
        self._selected_rows: Set[int] = set()
        self._anchor_row: Optional[int] = None
        self._focused_row: Optional[int] = None
        self._focused_col: int = 0
        self._hovered_row: Optional[int] = None
        self._hovered_col: Optional[int] = None
        self._sort_col: Optional[int] = None
        self._sort_desc: bool = False

        # Resizing state
        self._resizing_col: Optional[int] = None
        self._resize_start_x: float = 0.0
        self._resize_orig_width: float = 0.0

        # Filtering state
        self._filter_query: Optional[Union[str, Callable[[Any], bool]]] = None
        self._filtered_indices: List[int] = list(range(len(self._data)))

        # Scrolling offsets
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

        # Grid card content: row 0 = View + VScroll, row 1 = HScroll, row 2 = Pagination Bar
        self._card.grid_rowconfigure(0, weight=1)
        self._card.grid_columnconfigure(0, weight=1)

        # Vector Surface
        self._view = _TableViewSurface(
            self._card,
            table=self,
            parent_bg=self._card.bg_color,
        )
        self._view.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=(2, 0))

        # Vertical Scrollbar
        self._v_scrollbar = VectorScrollbar(
            self._card,
            command=self._on_vscroll,
            orientation="vertical",
            width=8,
            parent_bg=self._card.bg_color,
        )
        self._v_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 2), pady=(2, 0))

        # Horizontal Scrollbar
        self._h_scrollbar = VectorScrollbar(
            self._card,
            command=self._on_hscroll,
            orientation="horizontal",
            height=8,
            parent_bg=self._card.bg_color,
        )
        self._h_scrollbar.grid(row=1, column=0, sticky="ew", padx=(2, 0), pady=(0, 2))

        # Bottom Pagination Bar (if enabled)
        self._page_frame: Optional[tk.Frame] = None
        self._page_label: Optional[tk.Label] = None
        self._btn_prev: Optional[tk.Button] = None
        self._btn_next: Optional[tk.Button] = None
        if self._pagination:
            self._build_pagination_bar()

        # Keyboard & Wheel bindings
        self._view.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self._view.bind("<Shift-MouseWheel>", self._on_shift_mousewheel, add="+")
        self._view.bind("<Button-4>", self._on_mousewheel_linux, add="+")
        self._view.bind("<Button-5>", self._on_mousewheel_linux, add="+")
        self._view.bind("<Configure>", self._on_view_resize, add="+")

        self._view.bind("<Up>", self._on_key_up)
        self._view.bind("<Down>", self._on_key_down)
        self._view.bind("<Shift-Up>", self._on_key_shift_up)
        self._view.bind("<Shift-Down>", self._on_key_shift_down)
        self._view.bind("<Left>", self._on_key_left)
        self._view.bind("<Right>", self._on_key_right)
        self._view.bind("<Prior>", self._on_key_page_up)
        self._view.bind("<Next>", self._on_key_page_down)
        self._view.bind("<Home>", self._on_key_home)
        self._view.bind("<End>", self._on_key_end)
        self._view.bind("<Return>", self._on_key_return)
        self._view.bind("<Control-a>", self._on_key_select_all)
        self._view.bind("<Command-a>", self._on_key_select_all)
        self._view.bind("<Control-c>", self._on_key_copy)
        self._view.bind("<Command-c>", self._on_key_copy)

        add_theme_listener(self._on_theme_changed)
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._update_filtered_indices()
        self._update_scroll_geometry()

    @property
    def bg_color(self) -> str:
        """Return the current interior background color."""
        return self._card.bg_color

    @property
    def row_count(self) -> int:
        """Return the total number of rows in the table."""
        return len(self._data)


    def _build_pagination_bar(self) -> None:
        """Construct the pagination control bar."""
        pal = get_theme()
        s = self._scale
        self._page_frame = tk.Frame(
            self._card,
            bg=self._card.bg_color,
            height=int(28 * s),
        )
        self._page_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 4))

        self._btn_prev = tk.Button(
            self._page_frame,
            text="◀ Prev",
            command=self.prev_page,
            font=("sans-serif", max(8, int(9.5 * s))),
            bg=pal.secondary,
            fg=pal.fg,
            relief="flat",
            activebackground=pal.primary,
            activeforeground="#ffffff",
            padx=6,
            pady=1,
            cursor="hand2",
        )
        self._btn_prev.pack(side="left", padx=4)

        self._page_label = tk.Label(
            self._page_frame,
            text="",
            font=("sans-serif", max(8, int(9.5 * s))),
            bg=self._card.bg_color,
            fg=pal.fg,
        )
        self._page_label.pack(side="left", padx=8)

        self._btn_next = tk.Button(
            self._page_frame,
            text="Next ▶",
            command=self.next_page,
            font=("sans-serif", max(8, int(9.5 * s))),
            bg=pal.secondary,
            fg=pal.fg,
            relief="flat",
            activebackground=pal.primary,
            activeforeground="#ffffff",
            padx=6,
            pady=1,
            cursor="hand2",
        )
        self._btn_next.pack(side="left", padx=4)
        self._update_pagination_ui()

    def _update_pagination_ui(self) -> None:
        if not self._pagination or not self._page_frame:
            return
        total_p = self.get_total_pages()
        cur_p = self._current_page + 1
        total_rows = len(self._filtered_indices)
        if self._page_label:
            self._page_label.config(
                text=f"Page {cur_p} of {max(1, total_p)} ({total_rows} items)"
            )
        if self._btn_prev:
            self._btn_prev.config(state="normal" if self._current_page > 0 else "disabled")
        if self._btn_next:
            self._btn_next.config(state="normal" if cur_p < total_p else "disabled")

    # -------------------------------------------------------------
    # DATA & COLUMN MANAGEMENT
    # -------------------------------------------------------------
    def set_columns(self, columns: List[Dict[str, Any]]) -> None:
        """Set the table columns definition."""
        self._columns = list(columns)
        self._update_scroll_geometry()
        self._view.render()

    def set_data(self, data: List[Union[Dict[str, Any], List[Any], Tuple[Any, ...]]]) -> None:
        """Replace the entire dataset."""
        self._data = list(data)
        self._selected_rows.clear()
        self._anchor_row = None
        self._focused_row = None
        self._hovered_row = None
        self._current_page = 0
        self._update_filtered_indices()
        self._update_scroll_geometry()
        self._update_pagination_ui()
        self._view.render()

    def insert_row(
        self,
        row: Union[Dict[str, Any], List[Any], Tuple[Any, ...]],
        index: Optional[int] = None,
    ) -> None:
        """Insert a single row."""
        if index is None or index >= len(self._data):
            self._data.append(row)
        else:
            self._data.insert(index, row)
        self._update_filtered_indices()
        self._update_scroll_geometry()
        self._update_pagination_ui()
        self._view.render()

    def delete_row(self, index: int) -> None:
        """Delete row at specified raw dataset index."""
        if 0 <= index < len(self._data):
            self._data.pop(index)
            # Adjust selected rows
            new_sel = set()
            for r in self._selected_rows:
                if r < index:
                    new_sel.add(r)
                elif r > index:
                    new_sel.add(r - 1)
            self._selected_rows = new_sel
            self._update_filtered_indices()
            self._update_scroll_geometry()
            self._update_pagination_ui()
            self._view.render()

    def clear(self) -> None:
        """Clear all rows."""
        self._data.clear()
        self._selected_rows.clear()
        self._anchor_row = None
        self._focused_row = None
        self._update_filtered_indices()
        self._update_scroll_geometry()
        self._update_pagination_ui()
        self._view.render()

    def set_cell_value(self, row_index: int, col_id: str, value: Any) -> None:
        """Set cell value at specified raw row index and column ID."""
        if not (0 <= row_index < len(self._data)):
            return
        row = self._data[row_index]
        if isinstance(row, dict):
            row[col_id] = value
        elif isinstance(row, list):
            for i, c in enumerate(self._columns):
                if c.get("id") == col_id and i < len(row):
                    row[i] = value
                    break
        self._view.render()

    def get_cell_value(self, row_index: int, col_id: str) -> Any:
        """Retrieve cell value at specified row index and column ID."""
        if not (0 <= row_index < len(self._data)):
            return None
        row = self._data[row_index]
        if isinstance(row, dict):
            return row.get(col_id)
        elif isinstance(row, (list, tuple)):
            for i, c in enumerate(self._columns):
                if c.get("id") == col_id and i < len(row):
                    return row[i]
        return None

    # -------------------------------------------------------------
    # FILTERING & SEARCH
    # -------------------------------------------------------------
    def filter_by(self, query_or_func: Union[str, Callable[[Any], bool], None]) -> None:
        """
        Filter visible rows by substring query or predicate function.
        Pass None or empty string to clear the filter.
        """
        self._filter_query = query_or_func
        self._current_page = 0
        self._update_filtered_indices()
        self._update_scroll_geometry()
        self._update_pagination_ui()
        self._view.render()

    def clear_filter(self) -> None:
        """Clear active search filter."""
        self.filter_by(None)

    def _update_filtered_indices(self) -> None:
        """Recompute matching rows based on current filter."""
        if not self._filter_query:
            self._filtered_indices = list(range(len(self._data)))
            return

        indices = []
        if callable(self._filter_query):
            for i, row in enumerate(self._data):
                try:
                    if self._filter_query(row):
                        indices.append(i)
                except Exception:
                    pass
        else:
            q = str(self._filter_query).lower()
            for i, row in enumerate(self._data):
                match = False
                if isinstance(row, dict):
                    for v in row.values():
                        if q in str(v).lower():
                            match = True
                            break
                elif isinstance(row, (list, tuple)):
                    for v in row:
                        if q in str(v).lower():
                            match = True
                            break
                if match:
                    indices.append(i)

        self._filtered_indices = indices

    def get_filtered_data(self) -> List[Any]:
        """Return the list of all rows matching the active filter."""
        return [self._data[i] for i in self._filtered_indices]

    def _get_visible_data(self) -> List[Any]:
        """Return rows visible on the current page."""
        if not self._pagination:
            return [self._data[i] for i in self._filtered_indices]
        start = self._current_page * self._page_size
        end = start + self._page_size
        page_indices = self._filtered_indices[start:end]
        return [self._data[i] for i in page_indices]

    def _get_raw_index(self, visible_idx: int) -> int:
        """Convert a visible row index on the current view to its raw index in self._data."""
        if not self._pagination:
            if 0 <= visible_idx < len(self._filtered_indices):
                return self._filtered_indices[visible_idx]
            return visible_idx
        start = self._current_page * self._page_size
        actual_idx = start + visible_idx
        if 0 <= actual_idx < len(self._filtered_indices):
            return self._filtered_indices[actual_idx]
        return visible_idx

    # -------------------------------------------------------------
    # PAGINATION
    # -------------------------------------------------------------
    def get_total_pages(self) -> int:
        """Calculate total number of pages."""
        if not self._pagination or self._page_size <= 0:
            return 1
        return max(1, (len(self._filtered_indices) + self._page_size - 1) // self._page_size)

    def get_current_page(self) -> int:
        """Return current 0-indexed page."""
        return self._current_page

    def set_page(self, page_index: int) -> None:
        """Jump to specific page index."""
        max_pages = self.get_total_pages()
        self._current_page = max(0, min(max_pages - 1, page_index))
        self._scroll_y = 0.0
        self._update_scroll_geometry()
        self._update_pagination_ui()
        self._view.render()

    def next_page(self) -> None:
        """Advance to next page."""
        if self._current_page + 1 < self.get_total_pages():
            self.set_page(self._current_page + 1)

    def prev_page(self) -> None:
        """Go back to previous page."""
        if self._current_page > 0:
            self.set_page(self._current_page - 1)

    def set_page_size(self, size: Optional[int]) -> None:
        """Set page size and recompute pagination."""
        if size is None or size <= 0:
            self._pagination = False
            if self._page_frame:
                self._page_frame.grid_forget()
        else:
            self._pagination = True
            self._page_size = size
            if not self._page_frame:
                self._build_pagination_bar()
            else:
                self._page_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 4))
        self.set_page(0)

    # -------------------------------------------------------------
    # SELECTION MANAGEMENT
    # -------------------------------------------------------------
    def get_selected_index(self) -> Optional[int]:
        """Return index of first selected row, or None."""
        if not self._selected_rows:
            return None
        return min(self._selected_rows)

    def get_selected_indices(self) -> List[int]:
        """Return sorted list of all selected raw row indices."""
        return sorted(list(self._selected_rows))

    def get_selected_row(self) -> Optional[Any]:
        """Return data of first selected row, or None."""
        idx = self.get_selected_index()
        if idx is not None and 0 <= idx < len(self._data):
            return self._data[idx]
        return None

    def get_selected_rows(self) -> List[Any]:
        """Return list of data items for all selected rows."""
        return [self._data[i] for i in self.get_selected_indices() if 0 <= i < len(self._data)]

    def set_selection(self, indices: Union[int, List[int], Set[int], None]) -> None:
        """Set selection by raw data index or list of indices."""
        if indices is None:
            self._selected_rows.clear()
            self._anchor_row = None
        elif isinstance(indices, int):
            if 0 <= indices < len(self._data):
                self._selected_rows = {indices}
                self._anchor_row = indices
                self._focused_row = indices
        else:
            valid = {i for i in indices if 0 <= i < len(self._data)}
            self._selected_rows = valid
            if valid:
                self._anchor_row = min(valid)
                self._focused_row = min(valid)

        self._view.render()
        self._notify_select()

    def select_all(self) -> None:
        """Select all visible/filtered rows."""
        if self._select_mode in ("extended", "multiple"):
            self._selected_rows = set(self._filtered_indices)
            self._view.render()
            self._notify_select()

    def clear_selection(self) -> None:
        """Clear all selected rows."""
        self._selected_rows.clear()
        self._anchor_row = None
        self._view.render()
        self._notify_select()

    def _handle_row_click(self, raw_idx: int, modifier_state: int) -> None:
        """Handle click on a row with selection modifiers."""
        if self._select_mode == "none":
            return

        is_ctrl = bool(modifier_state & 0x0004) or bool(modifier_state & 0x0008)
        is_shift = bool(modifier_state & 0x0001)

        if self._select_mode == "single":
            self._selected_rows = {raw_idx}
            self._anchor_row = raw_idx
            self._focused_row = raw_idx
        elif self._select_mode == "multiple":
            if raw_idx in self._selected_rows:
                self._selected_rows.remove(raw_idx)
            else:
                self._selected_rows.add(raw_idx)
            self._anchor_row = raw_idx
            self._focused_row = raw_idx
        elif self._select_mode == "extended":
            if is_shift and self._anchor_row is not None:
                # Contiguous range selection between anchor and clicked row
                start = min(self._anchor_row, raw_idx)
                end = max(self._anchor_row, raw_idx)
                self._selected_rows = set(range(start, end + 1))
                self._focused_row = raw_idx
            elif is_ctrl:
                # Toggle clicked row
                if raw_idx in self._selected_rows:
                    self._selected_rows.remove(raw_idx)
                else:
                    self._selected_rows.add(raw_idx)
                self._anchor_row = raw_idx
                self._focused_row = raw_idx
            else:
                # Normal single click
                self._selected_rows = {raw_idx}
                self._anchor_row = raw_idx
                self._focused_row = raw_idx

        self._view.render()
        self._notify_select()

    def _notify_select(self) -> None:
        if self._on_select:
            indices = self.get_selected_indices()
            rows = self.get_selected_rows()
            single_idx = indices[0] if indices else None
            single_row = rows[0] if rows else None
            try:
                self._on_select(indices, rows)
            except TypeError:
                try:
                    self._on_select(single_idx, single_row)
                except TypeError:
                    self._on_select(single_row)

    # -------------------------------------------------------------
    # COLUMN RESIZING & AUTO-FIT
    # -------------------------------------------------------------
    def auto_fit_column(self, col_index: int) -> None:
        """Automatically adjust column width based on content and title length."""
        if not (0 <= col_index < len(self._columns)):
            return
        col = self._columns[col_index]
        col_id = col.get("id", str(col_index))
        title = col.get("title", "")
        max_chars = len(title)

        # Inspect cell strings
        for row in self._data:
            if isinstance(row, dict):
                v = str(row.get(col_id, ""))
            elif isinstance(row, (list, tuple)) and col_index < len(row):
                v = str(row[col_index])
            else:
                v = ""
            if len(v) > max_chars:
                max_chars = len(v)

        s = self._scale
        estimated_w = int(max_chars * 8.5 + 32.0)
        min_w = col.get("min_width", 40)
        col["width"] = max(min_w, estimated_w)
        self._update_scroll_geometry()
        self._view.render()

    def auto_fit_all_columns(self) -> None:
        """Auto-fit all columns to content."""
        for i in range(len(self._columns)):
            self.auto_fit_column(i)

    # -------------------------------------------------------------
    # SORTING
    # -------------------------------------------------------------
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
                num_val = float(str(val).replace("%", "").replace("$", "").replace(",", "").strip())
                return (0, num_val)
            except (ValueError, TypeError):
                return (1, str(val).lower())

        self._data.sort(key=sort_key, reverse=self._sort_desc)
        self._update_filtered_indices()
        self._view.render()

    def _on_header_click(self, col_index: int) -> None:
        col = self._columns[col_index]
        if col.get("type") == "checkbox":
            # Toggle Select All / None
            if len(self._selected_rows) == len(self._data):
                self.clear_selection()
            else:
                self.select_all()
        else:
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

    # -------------------------------------------------------------
    # IN-PLACE CELL EDITING
    # -------------------------------------------------------------
    def _start_cell_edit(self, raw_row_idx: int, col_idx: int, visible_row_idx: int) -> None:
        """Open floating Entry editor over cell."""
        if not (0 <= col_idx < len(self._columns)):
            return
        col = self._columns[col_idx]
        col_id = col.get("id", str(col_idx))
        current_val = str(self.get_cell_value(raw_row_idx, col_id) or "")

        s = self._scale
        hdr_h = self._header_height * s
        row_h = self._row_height * s

        # Calculate cell bounding box on screen
        col_x = -self._scroll_x
        for i in range(col_idx):
            col_x += self._columns[i].get("width", 100) * s
        cw = col.get("width", 100) * s
        ry = hdr_h + (visible_row_idx * row_h) - self._scroll_y

        _FloatingCellEditor(
            self._view,
            table=self,
            row_idx=raw_row_idx,
            col_idx=col_idx,
            initial_value=current_val,
            x=int(col_x + 2),
            y=int(ry + 2),
            width=max(10, int(cw - 4)),
            height=max(10, int(row_h - 4)),
        )

    def _on_editor_closed(
        self,
        raw_row_idx: int,
        col_idx: int,
        old_val: str,
        new_val: str,
        commit: bool,
    ) -> None:
        """Callback when floating editor closes."""
        if commit and new_val != old_val:
            col = self._columns[col_idx]
            col_id = col.get("id", str(col_idx))

            # Validation hook
            if self._on_cell_validate:
                try:
                    if not self._on_cell_validate(raw_row_idx, col_id, old_val, new_val):
                        self._view.render()
                        return
                except Exception as e:
                    logger.debug("on_cell_validate exception: %s", e)

            self.set_cell_value(raw_row_idx, col_id, new_val)
            if self._on_cell_edit:
                try:
                    self._on_cell_edit(raw_row_idx, col_id, old_val, new_val)
                except Exception as e:
                    logger.debug("on_cell_edit exception: %s", e)

        self._view.render()

    # -------------------------------------------------------------
    # SCROLLING & GEOMETRY
    # -------------------------------------------------------------
    def _on_vscroll(self, action: str, *args) -> None:
        s = self._scale
        row_h = self._row_height * s
        visible_rows = len(self._get_visible_data())
        total_h = visible_rows * row_h
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

    def _on_hscroll(self, action: str, *args) -> None:
        s = self._scale
        total_w = sum(c.get("width", 100) * s for c in self._columns)
        view_w = max(1.0, float(self._view._widget_w))

        if action == "moveto" and args:
            fraction = float(args[0])
            self._scroll_x = max(0.0, min(total_w - view_w, fraction * total_w))
        elif action == "scroll" and len(args) >= 2:
            amount = float(args[0])
            what = args[1]
            if what == "units":
                self._scroll_x = max(0.0, min(total_w - view_w, self._scroll_x + amount * 30.0 * s))
            elif what == "pages":
                self._scroll_x = max(0.0, min(total_w - view_w, self._scroll_x + amount * view_w))

        self._update_scroll_geometry()
        self._view.render()

    def _on_mousewheel(self, event) -> None:
        if event.state & 0x0001:  # Shift held -> horizontal scroll
            self._on_shift_mousewheel(event)
            return

        s = self._scale
        row_h = self._row_height * s
        visible_rows = len(self._get_visible_data())
        total_h = visible_rows * row_h
        view_h = max(1.0, float(self._view._widget_h - self._header_height * s))

        delta = event.delta
        step = -1 * (delta / 120.0 if sys.platform != "darwin" else delta) * row_h
        self._scroll_y = max(0.0, min(total_h - view_h, self._scroll_y + step))
        self._update_scroll_geometry()
        self._view.render()

    def _on_shift_mousewheel(self, event) -> None:
        s = self._scale
        total_w = sum(c.get("width", 100) * s for c in self._columns)
        view_w = max(1.0, float(self._view._widget_w))

        delta = event.delta
        step = -1 * (delta / 120.0 if sys.platform != "darwin" else delta) * 40.0 * s
        self._scroll_x = max(0.0, min(total_w - view_w, self._scroll_x + step))
        self._update_scroll_geometry()
        self._view.render()

    def _on_mousewheel_linux(self, event) -> None:
        s = self._scale
        row_h = self._row_height * s
        visible_rows = len(self._get_visible_data())
        total_h = visible_rows * row_h
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
        visible_rows = len(self._get_visible_data())
        total_h = max(1.0, visible_rows * row_h)
        view_h = max(1.0, float(self._view._widget_h - self._header_height * s))

        # Vertical Scrollbar Sync
        if total_h <= view_h:
            self._scroll_y = 0.0
            self._v_scrollbar.set(0.0, 1.0)
        else:
            self._scroll_y = max(0.0, min(total_h - view_h, self._scroll_y))
            first = self._scroll_y / total_h
            last = min(1.0, (self._scroll_y + view_h) / total_h)
            self._v_scrollbar.set(first, last)

        # Horizontal Scrollbar Sync
        total_w = max(1.0, sum(c.get("width", 100) * s for c in self._columns))
        view_w = max(1.0, float(self._view._widget_w))

        if total_w <= view_w:
            self._scroll_x = 0.0
            self._h_scrollbar.set(0.0, 1.0)
        else:
            self._scroll_x = max(0.0, min(total_w - view_w, self._scroll_x))
            first = self._scroll_x / total_w
            last = min(1.0, (self._scroll_x + view_w) / total_w)
            self._h_scrollbar.set(first, last)

    # -------------------------------------------------------------
    # KEYBOARD NAVIGATION & CLIPBOARD
    # -------------------------------------------------------------
    def _on_key_up(self, event) -> None:
        if not self._filtered_indices:
            return
        cur = self._focused_row if self._focused_row is not None else 0
        new_row = max(0, cur - 1)
        self.set_selection(new_row)
        self._ensure_row_visible(new_row)

    def _on_key_down(self, event) -> None:
        if not self._filtered_indices:
            return
        cur = self._focused_row if self._focused_row is not None else -1
        new_row = min(len(self._data) - 1, cur + 1)
        self.set_selection(new_row)
        self._ensure_row_visible(new_row)

    def _on_key_shift_up(self, event) -> None:
        if not self._filtered_indices:
            return
        cur = self._focused_row if self._focused_row is not None else 0
        new_row = max(0, cur - 1)
        self._focused_row = new_row
        if self._anchor_row is None:
            self._anchor_row = cur
        start = min(self._anchor_row, new_row)
        end = max(self._anchor_row, new_row)
        self._selected_rows = set(range(start, end + 1))
        self._view.render()
        self._notify_select()
        self._ensure_row_visible(new_row)

    def _on_key_shift_down(self, event) -> None:
        if not self._filtered_indices:
            return
        cur = self._focused_row if self._focused_row is not None else 0
        new_row = min(len(self._data) - 1, cur + 1)
        self._focused_row = new_row
        if self._anchor_row is None:
            self._anchor_row = cur
        start = min(self._anchor_row, new_row)
        end = max(self._anchor_row, new_row)
        self._selected_rows = set(range(start, end + 1))
        self._view.render()
        self._notify_select()
        self._ensure_row_visible(new_row)

    def _on_key_left(self, event) -> None:
        self._focused_col = max(0, self._focused_col - 1)

    def _on_key_right(self, event) -> None:
        self._focused_col = min(len(self._columns) - 1, self._focused_col + 1)

    def _on_key_home(self, event) -> None:
        if self._filtered_indices:
            self.set_selection(0)
            self._scroll_y = 0.0
            self._update_scroll_geometry()
            self._view.render()

    def _on_key_end(self, event) -> None:
        if self._filtered_indices:
            last = len(self._data) - 1
            self.set_selection(last)
            self._ensure_row_visible(last)

    def _on_key_page_up(self, event) -> None:
        self._on_vscroll("scroll", -1, "pages")

    def _on_key_page_down(self, event) -> None:
        self._on_vscroll("scroll", 1, "pages")

    def _on_key_return(self, event) -> None:
        if self._focused_row is not None and 0 <= self._focused_col < len(self._columns):
            col = self._columns[self._focused_col]
            if col.get("editable", False):
                # Calculate visible index
                vis_idx = 0
                for v_i, r_idx in enumerate(self._filtered_indices):
                    if r_idx == self._focused_row:
                        vis_idx = v_i
                        break
                self._start_cell_edit(self._focused_row, self._focused_col, vis_idx)

    def _on_key_select_all(self, event) -> None:
        self.select_all()
        return "break"

    def _on_key_copy(self, event) -> None:
        """Copy selected rows formatted as TSV to clipboard."""
        self.copy_to_clipboard()
        return "break"

    def copy_to_clipboard(self) -> None:
        """Format selected rows (or all if none selected) as TSV and copy to clipboard."""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            selected_rows = self._get_visible_data()

        lines = []
        # Header row
        lines.append("\t".join(c.get("title", "") for c in self._columns))
        # Data rows
        for row in selected_rows:
            row_vals = []
            for i, col in enumerate(self._columns):
                col_id = col.get("id", str(i))
                if isinstance(row, dict):
                    val = str(row.get(col_id, ""))
                elif isinstance(row, (list, tuple)) and i < len(row):
                    val = str(row[i])
                else:
                    val = ""
                row_vals.append(val)
            lines.append("\t".join(row_vals))

        tsv_text = "\n".join(lines)
        try:
            self.clipboard_clear()
            self.clipboard_append(tsv_text)
        except Exception as e:
            logger.debug("Clipboard copy failed: %s", e)

    def _ensure_row_visible(self, raw_row_idx: int) -> None:
        """Scroll viewport so that raw_row_idx is visible."""
        s = self._scale
        row_h = self._row_height * s
        hdr_h = self._header_height * s
        view_h = max(1.0, float(self._view._widget_h - hdr_h))

        # Find visible index
        try:
            vis_idx = self._filtered_indices.index(raw_row_idx)
        except ValueError:
            return

        row_top = vis_idx * row_h
        row_bottom = row_top + row_h

        if row_top < self._scroll_y:
            self._scroll_y = row_top
        elif row_bottom > self._scroll_y + view_h:
            self._scroll_y = row_bottom - view_h

        self._update_scroll_geometry()
        self._view.render()

    # -------------------------------------------------------------
    # THEME & CLEANUP
    # -------------------------------------------------------------
    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        resolved_bg = self._explicit_parent_bg or Widget._resolve_default_bg(self.master, palette)
        self._parent_bg = resolved_bg
        self.configure(background=self._parent_bg)
        if self._bg_color is None:
            self._card._bg_color = palette.card_bg
        if self._border_color is None:
            self._card._border_color = palette.card_border
        self._card.set_parent_bg(self._parent_bg)
        self._card.render()
        inner_bg = self._card.bg_color

        self._v_scrollbar.set_parent_bg(inner_bg)
        self._h_scrollbar.set_parent_bg(inner_bg)
        self._view.set_parent_bg(inner_bg)

        if self._page_frame:
            self._page_frame.config(bg=inner_bg)
            if self._page_label:
                self._page_label.config(bg=inner_bg, fg=palette.fg)
            if self._btn_prev:
                self._btn_prev.config(bg=palette.secondary, fg=palette.fg, activebackground=palette.primary)
            if self._btn_next:
                self._btn_next.config(bg=palette.secondary, fg=palette.fg, activebackground=palette.primary)

        self._view.render()

    def render(self) -> None:
        """Render the data table view surface and scrollbars."""
        if hasattr(self, "_view") and self._view is not None:
            self._view.render()
        if hasattr(self, "_card") and self._card is not None:
            self._card.render()

    def _on_destroy(self, event) -> None:
        if event.widget == self:
            remove_theme_listener(self._on_theme_changed)


Treeview = Table


