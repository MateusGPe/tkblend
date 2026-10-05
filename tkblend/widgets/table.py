"""
Pure Blend2D Vector Data Table widget powered by BaseControl.

Features:
- High-performance vector rendering with zero TTK dependencies
- Multi-column sorting with multi-tier sort badges, drag-and-drop column reordering, auto-fitting, and column hiding/visibility
- Fixed / pinned / frozen columns during horizontal scrolling
- Dual-axis vector scrollbars (vertical and horizontal)
- Multi-selection modes ('extended', 'single', 'multiple', 'none') and selection units ('row', 'cell')
- Active cell focus indicator rectangle and rectangular range selection
- Declarative cell types (text, badge/pill, progress bar, checkbox) & custom callable renderers
- In-place cell editing with floating vector-styled text editor, dropdown/select editor, and numeric editor with validation
- Dynamic row & cell styling hooks for conditional formatting
- Right-click context menus for header and body with custom extension hooks
- Dynamic search/filter engine and built-in pagination
- Comprehensive keyboard navigation and clipboard export (CSV / TSV / Ctrl+C)
- High-DPI awareness and dynamic theme switching
"""

from __future__ import annotations
import csv
import io
import logging
import sys
import tkinter as tk
from typing import Optional, Callable, Dict, List, Any, Union, Tuple, Set

from tkblend.widgets.base import BaseControl, ScalingTracker
from tkblend.widgets.scrollable_frame import VectorScrollbar
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    get_theme,
    add_theme_listener,
    remove_theme_listener,
    resolve_color_failsafe,
    blend_color_hex,
    get_contrast_color,
    to_tk_hex,
    cascade_bg_to_children,
)
from tkblend.widgets.constants import (
    DEFAULT_FONT_SIZE,
    CURSOR_HAND,
    CURSOR_DEFAULT,
)
from tkblend.widgets.utils import (
    compute_text_baseline_y,
    draw_vector_checkmark,
    draw_vector_chevron,
    truncate_text,
)

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# IN-PLACE EDITORS
# -------------------------------------------------------------------------

class _FloatingCellEditor(tk.Entry):
    """Floating Entry overlay for in-place text cell editing within the Table."""

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
        s = ScalingTracker.get_scaling_factor(master)
        super().__init__(
            master,
            font=("sans-serif", max(9, int(11 * s))),
            bg=to_tk_hex(pal.card_bg),
            fg=to_tk_hex(pal.fg),
            insertbackground=to_tk_hex(pal.fg),
            selectbackground=to_tk_hex(pal.primary),
            selectforeground="#ffffff",
            relief="solid",
            highlightthickness=1,
            highlightbackground=to_tk_hex(pal.primary),
            highlightcolor=to_tk_hex(pal.primary),
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


class _NumericCellEditor(tk.Entry):
    """Floating numeric editor with min/max bounds and Up/Down arrow increments."""

    def __init__(
        self,
        master: tk.Misc,
        table: Table,
        row_idx: int,
        col_idx: int,
        initial_value: Any,
        x: int,
        y: int,
        width: int,
        height: int,
        step: float = 1.0,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ):
        pal = get_theme()
        s = ScalingTracker.get_scaling_factor(master)
        super().__init__(
            master,
            font=("sans-serif", max(9, int(11 * s))),
            bg=to_tk_hex(pal.card_bg),
            fg=to_tk_hex(pal.fg),
            insertbackground=to_tk_hex(pal.fg),
            selectbackground=to_tk_hex(pal.primary),
            selectforeground="#ffffff",
            relief="solid",
            highlightthickness=1,
            highlightbackground=to_tk_hex(pal.primary),
            highlightcolor=to_tk_hex(pal.primary),
            borderwidth=1,
        )
        self._table = table
        self._row_idx = row_idx
        self._col_idx = col_idx
        self._initial_value = str(initial_value)
        self._step = step
        self._min_val = min_val
        self._max_val = max_val
        self._is_committed = False

        self.insert(0, str(initial_value))
        self.select_range(0, tk.END)
        self.icursor(tk.END)

        self.place(x=x, y=y, width=width, height=height)
        self.focus_set()

        self.bind("<Return>", self._on_commit)
        self.bind("<KP_Enter>", self._on_commit)
        self.bind("<Escape>", self._on_cancel)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Up>", self._on_step_up)
        self.bind("<Down>", self._on_step_down)

    def _get_current_numeric(self) -> float:
        try:
            return float(self.get())
        except (ValueError, TypeError):
            return 0.0

    def _on_step_up(self, event=None) -> str:
        curr = self._get_current_numeric() + self._step
        if self._max_val is not None:
            curr = min(self._max_val, curr)
        val_str = f"{curr:g}"
        self.delete(0, tk.END)
        self.insert(0, val_str)
        self.select_range(0, tk.END)
        return "break"

    def _on_step_down(self, event=None) -> str:
        curr = self._get_current_numeric() - self._step
        if self._min_val is not None:
            curr = max(self._min_val, curr)
        val_str = f"{curr:g}"
        self.delete(0, tk.END)
        self.insert(0, val_str)
        self.select_range(0, tk.END)
        return "break"

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


class _DropdownCellEditor(tk.Frame):
    """Floating Dropdown / Option selector overlay for categorical cell editing."""

    def __init__(
        self,
        master: tk.Misc,
        table: Table,
        row_idx: int,
        col_idx: int,
        initial_value: str,
        options: List[str],
        x: int,
        y: int,
        width: int,
        height: int,
    ):
        pal = get_theme()
        s = ScalingTracker.get_scaling_factor(master)
        super().__init__(
            master,
            bg=to_tk_hex(pal.card_bg),
            highlightthickness=1,
            highlightbackground=to_tk_hex(pal.primary),
            highlightcolor=to_tk_hex(pal.primary),
        )
        self._table = table
        self._row_idx = row_idx
        self._col_idx = col_idx
        self._initial_value = initial_value
        self._dropdown_options = list(options)
        self._is_committed = False

        # Entry top
        self._entry = tk.Entry(
            self,
            font=("sans-serif", max(9, int(11 * s))),
            bg=to_tk_hex(pal.card_bg),
            fg=to_tk_hex(pal.fg),
            insertbackground=to_tk_hex(pal.fg),
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )
        self._entry.pack(side="top", fill="x", padx=3, pady=2)
        self._entry.insert(0, initial_value)
        self._entry.select_range(0, tk.END)

        # Listbox for options
        list_h = min(6, max(2, len(self._dropdown_options)))
        self._listbox = tk.Listbox(
            self,
            height=list_h,
            font=("sans-serif", max(9, int(10.5 * s))),
            bg=to_tk_hex(pal.surface),
            fg=to_tk_hex(pal.fg),
            selectbackground=to_tk_hex(pal.primary),
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )
        self._listbox.pack(side="top", fill="both", expand=True)

        for opt in self._dropdown_options:
            self._listbox.insert(tk.END, str(opt))

        if initial_value in self._dropdown_options:
            idx = self._dropdown_options.index(initial_value)
            self._listbox.selection_set(idx)
            self._listbox.see(idx)

        total_h = height + list_h * int(20 * s) + 6
        self.place(x=x, y=y, width=max(width, int(120 * s)), height=total_h)
        self._entry.focus_set()

        self._entry.bind("<Return>", self._on_commit)
        self._entry.bind("<Escape>", self._on_cancel)
        self._entry.bind("<Down>", self._on_focus_list)
        self._entry.bind("<FocusOut>", self._on_focus_out)

        self._listbox.bind("<ButtonRelease-1>", self._on_list_select)
        self._listbox.bind("<Return>", self._on_list_select)
        self._listbox.bind("<Escape>", self._on_cancel)
        self._listbox.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_list(self, event=None) -> str:
        self._listbox.focus_set()
        if not self._listbox.curselection() and self._dropdown_options:
            self._listbox.selection_set(0)
        return "break"

    def _on_list_select(self, event=None) -> None:
        sel = self._listbox.curselection()
        if sel:
            val = self._dropdown_options[sel[0]]
            self._destroy_and_callback(val, commit=True)

    def _on_commit(self, event=None) -> None:
        if self._is_committed:
            return
        self._is_committed = True
        new_val = self._entry.get()
        self._destroy_and_callback(new_val, commit=True)

    def _on_cancel(self, event=None) -> None:
        if self._is_committed:
            return
        self._is_committed = True
        self._destroy_and_callback(self._initial_value, commit=False)

    def _on_focus_out(self, event=None) -> None:
        self.after(80, self._check_focus_loss)

    def _check_focus_loss(self) -> None:
        if self._is_committed:
            return
        foc = self.focus_get()
        if foc not in (self, self._entry, self._listbox):
            self._is_committed = True
            new_val = self._entry.get()
            self._destroy_and_callback(new_val, commit=True)

    def _destroy_and_callback(self, val: str, commit: bool) -> None:
        try:
            self.destroy()
        except Exception:
            pass
        self._table._on_editor_closed(self._row_idx, self._col_idx, self._initial_value, val, commit)


# -------------------------------------------------------------------------
# TABLE VECTOR VIEW SURFACE
# -------------------------------------------------------------------------

class _TableViewSurface(BaseControl):
    """Internal Blend2D vector surface rendering table headers, pinned columns, and virtualized rows."""

    def __init__(
        self,
        master: tk.Misc,
        table: Table,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._table = table
        self._press_header_x: float = 0.0
        self._press_header_col_idx: Optional[int] = None
        self._header_pressed: bool = False

        super().__init__(
            master=master,
            width=300,
            height=200,
            parent_bg=parent_bg,
            cursor=CURSOR_DEFAULT,
            takefocus=True,
            **kwargs,
        )

        # Mouse and keyboard event bindings
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Double-Button-1>", self._on_double_click)

        # Context Menu bindings
        self.bind("<Button-3>", self._on_context_menu_event)
        self.bind("<Control-Button-1>", self._on_context_menu_event)

    @property
    def _scale(self) -> float:
        return self._scale_factor

    def _get_divider_at_x(self, x: float, tolerance: float = 8.0) -> Optional[int]:
        """Return raw column index if x is near the right divider edge of that column."""
        s = self._scale_factor
        vis_cols = self._table._get_visible_columns()
        pinned_n = min(self._table._pinned_columns, len(vis_cols))
        pinned_w = sum(c.get("width", 100) * s for c in vis_cols[:pinned_n])

        # 1. Pinned columns dividers
        curr_x = 0.0
        for i in range(pinned_n):
            col = vis_cols[i]
            cw = col.get("width", 100) * s
            divider_x = curr_x + cw
            if abs(x - divider_x) <= tolerance * s:
                return self._table._get_col_raw_index(col)
            curr_x += cw

        # 2. Unpinned columns dividers
        curr_x = pinned_w - self._table._scroll_x
        for i in range(pinned_n, len(vis_cols)):
            col = vis_cols[i]
            cw = col.get("width", 100) * s
            divider_x = curr_x + cw
            if x >= (pinned_w - tolerance * s) and abs(x - divider_x) <= tolerance * s:
                return self._table._get_col_raw_index(col)
            curr_x += cw

        return None

    def _on_mouse_move(self, event) -> None:
        s = self._scale
        hdr_h = self._table._header_height * s
        row_h = self._table._row_height * s

        if self._table._resizing_col is not None:
            self.configure(cursor="sb_h_double_arrow")
            return

        if event.y < hdr_h:
            divider_col = self._get_divider_at_x(event.x)
            if divider_col is not None and divider_col < len(self._table._columns):
                self.configure(cursor="sb_h_double_arrow")
            else:
                self.configure(cursor="")

            col_idx = self._table._get_col_at_x(event.x)
            if col_idx != self._table._hovered_col:
                self._table._hovered_col = col_idx
                self._table._hovered_row = None
                self.request_redraw()
        else:
            self.configure(cursor="")

            content_y = event.y - hdr_h + self._table._scroll_y
            row_idx = int(content_y // row_h)
            visible_rows = self._table._get_visible_data()
            if 0 <= row_idx < len(visible_rows):
                if row_idx != self._table._hovered_row:
                    self._table._hovered_row = row_idx
                    self._table._hovered_col = None
                    self.request_redraw()
            else:
                if self._table._hovered_row is not None:
                    self._table._hovered_row = None
                    self.request_redraw()

    def _on_mouse_leave(self, event) -> None:
        if self._table._resizing_col is None:
            self.configure(cursor="")
        self._table._hovered_row = None
        self._table._hovered_col = None
        self.request_redraw()

    def _on_press(self, event) -> None:
        self.focus_set()
        s = self._scale
        hdr_h = self._table._header_height * s
        row_h = self._table._row_height * s

        if event.y < hdr_h:
            divider_col = self._get_divider_at_x(event.x)
            if divider_col is not None:
                self._table._resizing_col = divider_col
                self._table._resize_start_x = float(event.x)
                self._table._resize_orig_width = float(self._table._columns[divider_col].get("width", 100))
                self._header_pressed = False
                self.configure(cursor="sb_h_double_arrow")
                return

            col_idx = self._table._get_col_at_x(event.x)
            if col_idx is not None:
                self._press_header_x = float(event.x)
                self._press_header_col_idx = col_idx
                self._header_pressed = True
        else:
            content_y = event.y - hdr_h + self._table._scroll_y
            row_idx = int(content_y // row_h)
            visible_rows = self._table._get_visible_data()
            if 0 <= row_idx < len(visible_rows):
                col_idx = self._table._get_col_at_x(event.x)
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
                        self.request_redraw()
                        return

                self._table._handle_item_click(raw_idx, col_idx if col_idx is not None else 0, event.state)

    def _on_drag(self, event) -> None:
        s = self._scale
        if self._table._resizing_col is not None:
            self.configure(cursor="sb_h_double_arrow")
            col_idx = self._table._resizing_col
            delta_px = (event.x - self._table._resize_start_x) / s
            col = self._table._columns[col_idx]
            min_w = col.get("min_width", 30)
            new_w = max(min_w, int(self._table._resize_orig_width + delta_px))
            col["width"] = new_w
            self._table._update_scroll_geometry()
            self.request_redraw()
            return

        # Check column reordering drag
        if self._header_pressed and self._press_header_col_idx is not None:
            if abs(event.x - self._press_header_x) > 6 * s:
                self._table._dragging_col_idx = self._press_header_col_idx
                # Calculate insertion target
                target_col, target_x = self._table._get_reorder_target_at_x(event.x)
                self._table._drag_target_col_idx = target_col
                self._table._drag_target_x = target_x
                self.request_redraw()

    def _on_release(self, event) -> None:
        if self._table._resizing_col is not None:
            self._table._resizing_col = None
            self._table._update_scroll_geometry()
            s = self._scale
            hdr_h = self._table._header_height * s
            if event.y < hdr_h and self._get_divider_at_x(event.x) is not None:
                self.configure(cursor="sb_h_double_arrow")
            else:
                self.configure(cursor="")
            self.request_redraw()
            return

        if self._table._dragging_col_idx is not None:
            src_idx = self._table._dragging_col_idx
            dst_idx = self._table._drag_target_col_idx
            self._table._dragging_col_idx = None
            self._table._drag_target_col_idx = None
            self._table._drag_target_x = None
            self._header_pressed = False

            if dst_idx is not None and src_idx != dst_idx:
                self._table._reorder_column(src_idx, dst_idx)
            self.request_redraw()
            return

        if self._header_pressed and self._press_header_col_idx is not None:
            self._header_pressed = False
            is_shift = bool(event.state & 0x0001)
            self._table._on_header_click(self._press_header_col_idx, multi_sort=is_shift)

    def _on_double_click(self, event) -> None:
        s = self._scale
        hdr_h = self._table._header_height * s
        row_h = self._table._row_height * s

        if event.y < hdr_h:
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
                col_idx = self._table._get_col_at_x(event.x)
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

    def _on_context_menu_event(self, event) -> None:
        self.focus_set()
        s = self._scale
        hdr_h = self._table._header_height * s
        if event.y < hdr_h:
            col_idx = self._table._get_col_at_x(event.x)
            self._table._show_header_context_menu(event.x_root, event.y_root, col_idx)
        else:
            content_y = event.y - hdr_h + self._table._scroll_y
            row_idx = int(content_y // (self._table._row_height * s))
            col_idx = self._table._get_col_at_x(event.x)
            raw_idx = self._table._get_raw_index(row_idx) if 0 <= row_idx < len(self._table._get_visible_data()) else None
            self._table._show_body_context_menu(event.x_root, event.y_root, raw_idx, col_idx)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        if width <= 1 or height <= 1:
            return
        try:
            surf.clear(self.outer_bg)
            s = scale
            w = float(width)
            h = float(height)

            vis_cols = self._table._get_visible_columns()
            pinned_n = min(self._table._pinned_columns, len(vis_cols))
            pinned_cols = vis_cols[:pinned_n]
            unpinned_cols = vis_cols[pinned_n:]

            pinned_w = sum(c.get("width", 100) * s for c in pinned_cols)
            visible_data = self._table._get_visible_data()
            scroll_x = self._table._scroll_x
            scroll_y = self._table._scroll_y
            hdr_h = self._table._header_height * s
            row_h = self._table._row_height * s

            # -------------------------------------------------------------
            # 1. Render Visible Rows (Virtualized)
            # -------------------------------------------------------------
            font_sz_row = max(9.0, 11.0 * s)
            visible_start_idx = max(0, int(scroll_y // row_h))
            visible_end_idx = min(len(visible_data), int((scroll_y + h - hdr_h) // row_h) + 2)

            for r_idx in range(visible_start_idx, visible_end_idx):
                row = visible_data[r_idx]
                raw_idx = self._table._get_raw_index(r_idx)
                ry = hdr_h + (r_idx * row_h) - scroll_y
                is_row_selected = (
                    self._table._select_unit == "row" and raw_idx in self._table._selected_rows
                )

                # Custom Row Styler
                custom_row_style = None
                if self._table._row_styler:
                    try:
                        custom_row_style = self._table._row_styler(raw_idx, row)
                    except Exception as e:
                        logger.debug("row_styler error: %s", e)

                # Row Background & Selection Highlight
                if is_row_selected:
                    row_bg = blend_color_hex(pal.secondary, pal.primary, 0.22) or pal.primary
                    surf.fill_rect(0, ry, w, row_h, row_bg)
                    # Accent selection bar on left edge
                    surf.fill_rect(0, ry, 3.5 * s, row_h, pal.primary)
                elif r_idx == self._table._hovered_row:
                    stripe_bg = pal.card_bg if (r_idx % 2 == 0) else pal.surface
                    hover_bg = blend_color_hex(stripe_bg, pal.primary, 0.14) or blend_color_hex(stripe_bg, pal.fg, 0.08) or stripe_bg
                    surf.fill_rect(0, ry, w, row_h, hover_bg)
                else:
                    if custom_row_style and "bg" in custom_row_style:
                        surf.fill_rect(0, ry, w, row_h, custom_row_style["bg"])
                    else:
                        stripe_bg = pal.card_bg if (r_idx % 2 == 0) else pal.surface
                        surf.fill_rect(0, ry, w, row_h, stripe_bg)

                # Row bottom divider line
                surf.fill_rect(0, ry + row_h - 1.0 * s, w, 1.0 * s, pal.surface_border)

                # Helper to render a cell
                def render_cell(c_idx: int, col: Dict[str, Any], cx: float, cw: float):
                    col_id = col.get("id", str(c_idx))
                    col_type = col.get("type", "text")
                    align = col.get("align", "left")
                    renderer = col.get("renderer")

                    # Cell Selection
                    is_cell_selected = is_row_selected or (
                        self._table._select_unit == "cell" and (raw_idx, c_idx) in self._table._selected_cells
                    )

                    # Custom Cell Styler
                    custom_cell_style = None
                    if self._table._cell_styler:
                        try:
                            custom_cell_style = self._table._cell_styler(raw_idx, col_id, self._table.get_cell_value(raw_idx, col_id))
                        except Exception as e:
                            logger.debug("cell_styler error: %s", e)

                    cell_sel_bg = blend_color_hex(pal.secondary, pal.primary, 0.28) or pal.primary
                    if is_cell_selected and self._table._select_unit == "cell":
                        surf.fill_rect(cx, ry, cw, row_h - 1.0 * s, cell_sel_bg)
                    elif custom_cell_style and "bg" in custom_cell_style:
                        surf.fill_rect(cx, ry, cw, row_h - 1.0 * s, custom_cell_style["bg"])

                    # Extract raw cell value
                    if isinstance(row, dict):
                        cell_raw_val = row.get(
                            col_id,
                            row.get(
                                col.get("name"),
                                row.get(
                                    col.get("title"),
                                    row.get(col.get("key"), ""),
                                ),
                            ),
                        )
                    elif isinstance(row, (list, tuple)) and c_idx < len(row):
                        cell_raw_val = row[c_idx]
                    else:
                        cell_raw_val = ""

                    # 1. Custom Callable Renderer
                    if callable(renderer):
                        try:
                            renderer(
                                surf,
                                cx,
                                ry,
                                cw,
                                row_h,
                                cell_raw_val,
                                is_cell_selected,
                                pal,
                            )
                        except Exception as e:
                            logger.debug("Custom renderer exception: %s", e)

                    # 2. Checkbox Type
                    elif col_type == "checkbox":
                        cb_sz = 14.0 * s
                        cb_px = cx + (cw - cb_sz) / 2.0
                        cb_py = ry + (row_h - cb_sz) / 2.0
                        val_bool = bool(cell_raw_val)
                        surf.stroke_rounded_rect(
                            cb_px, cb_py, cb_sz, cb_sz, 3.0 * s, 3.0 * s, pal.surface_border, stroke_width=1.2 * s
                        )
                        if val_bool:
                            surf.fill_rounded_rect(
                                cb_px, cb_py, cb_sz, cb_sz, 3.0 * s, 3.0 * s, pal.primary
                            )
                            draw_vector_checkmark(
                                surf, cb_px + cb_sz / 2.0, cb_py + cb_sz / 2.0, 0.8 * s, "#ffffff"
                            )

                    # 3. Badge / Pill Type
                    elif col_type in ("badge", "pill"):
                        badge_str = str(cell_raw_val)
                        badge_colors = col.get("badge_colors", {})
                        badge_bg = (
                            (custom_cell_style.get("badge_bg") if custom_cell_style else None)
                            or badge_colors.get(badge_str)
                            or col.get("badge_bg")
                            or pal.secondary
                        )
                        badge_fg = (
                            (custom_cell_style.get("badge_fg") if custom_cell_style else None)
                            or col.get("badge_fg", pal.fg)
                        )
                        b_h = min(20.0 * s, row_h - 10.0 * s)
                        b_font_sz = max(8.5, 9.5 * s)
                        b_w = max(40.0 * s, len(badge_str) * b_font_sz * 0.65 + 16.0 * s)
                        b_w = min(b_w, max(20.0 * s, cw - 16.0 * s))

                        if align == "center":
                            bx = cx + (cw - b_w) / 2.0
                        elif align == "right":
                            bx = cx + cw - b_w - 10.0 * s
                        else:
                            bx = cx + 10.0 * s

                        by = ry + (row_h - b_h) / 2.0
                        surf.fill_rounded_rect(bx, by, b_w, b_h, b_h / 2.0, b_h / 2.0, badge_bg)
                        surf.draw_text(
                            truncate_text(badge_str, b_w - 8.0 * s, b_font_sz),
                            bx + b_w / 2.0,
                            compute_text_baseline_y(by + b_h / 2.0, b_font_sz),
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
                                if 0 < pct <= 1.0:
                                    pct = pct * 100.0
                            else:
                                pct = float(str(cell_raw_val).replace("%", "").strip())
                        except Exception:
                            pct = 0.0
                        pct = max(0.0, min(100.0, pct))
                        bar_h = 8.0 * s
                        bar_w = max(20.0 * s, cw - 46.0 * s)
                        bx = cx + 8.0 * s
                        by = ry + (row_h - bar_h) / 2.0

                        track_col = "#2a2a3e" if pal.dark_mode else "#e2e8f0"
                        surf.fill_rounded_rect(bx, by, bar_w, bar_h, bar_h / 2.0, bar_h / 2.0, track_col)
                        fill_w = (pct / 100.0) * bar_w
                        if fill_w > 0:
                            bar_color = col.get("bar_color", pal.primary)
                            surf.fill_rounded_rect(
                                bx, by, fill_w, bar_h, bar_h / 2.0, bar_h / 2.0, bar_color
                            )

                        # Percentage text
                        txt_x = bx + bar_w + 6.0 * s
                        txt_y = compute_text_baseline_y(ry + row_h / 2.0, max(8.0, 9.5 * s))
                        surf.draw_text(
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

                        ty = compute_text_baseline_y(ry + row_h / 2.0, font_sz_row)
                        if align == "center":
                            tx = cx + cw / 2.0
                        elif align == "right":
                            tx = cx + cw - 10.0 * s
                        else:
                            tx = cx + 10.0 * s

                        if is_cell_selected:
                            sel_bg = (
                                cell_sel_bg
                                if (self._table._select_unit == "cell" and (raw_idx, c_idx) in self._table._selected_cells)
                                else row_bg
                            )
                            default_sel_fg = get_contrast_color(
                                sel_bg,
                                light_fg="#ffffff",
                                dark_fg="#0f172a",
                                palette=pal,
                            )
                            txt_color = (
                                (custom_cell_style.get("fg") if custom_cell_style else None)
                                or (custom_row_style.get("fg") if custom_row_style else None)
                                or default_sel_fg
                            )
                        else:
                            txt_color = (
                                (custom_cell_style.get("fg") if custom_cell_style else None)
                                or (custom_row_style.get("fg") if custom_row_style else None)
                                or pal.fg
                            )
                        display_cell = truncate_text(cell_val, max(10.0, cw - 18.0 * s), font_sz_row)
                        surf.draw_text(
                            display_cell,
                            tx,
                            ty,
                            font_size=font_sz_row,
                            font_family="sans-serif",
                            color=txt_color,
                            align=align,
                        )

                # A. Render Unpinned Columns (Scrollable)
                cell_x = pinned_w - scroll_x
                for col in unpinned_cols:
                    raw_c_idx = self._table._columns.index(col)
                    cw = col.get("width", 100) * s
                    if cell_x + cw > pinned_w and cell_x < w:
                        render_cell(raw_c_idx, col, cell_x, cw)
                    cell_x += cw

                # B. Render Pinned Columns (Fixed at Left)
                pinned_cx = 0.0
                for col in pinned_cols:
                    raw_c_idx = self._table._columns.index(col)
                    cw = col.get("width", 100) * s
                    # Fill background of pinned cell to occlude scrolled content
                    if not is_row_selected:
                        if custom_row_style and "bg" in custom_row_style:
                            p_bg = custom_row_style["bg"]
                        elif r_idx == self._table._hovered_row:
                            stripe_bg = pal.card_bg if (r_idx % 2 == 0) else pal.surface
                            p_bg = blend_color_hex(stripe_bg, pal.primary, 0.14) or stripe_bg
                        else:
                            p_bg = pal.card_bg if (r_idx % 2 == 0) else pal.surface
                        surf.fill_rect(pinned_cx, ry, cw, row_h - 1.0 * s, p_bg)
                    render_cell(raw_c_idx, col, pinned_cx, cw)
                    pinned_cx += cw

            # -------------------------------------------------------------
            # 2. Pinned Columns Vertical Divider / Shadow Line
            # -------------------------------------------------------------
            if pinned_w > 0:
                surf.fill_rect(pinned_w - 1.0 * s, 0, 1.5 * s, h, pal.surface_border)

            # -------------------------------------------------------------
            # 3. Active Cell Focus Rectangle Highlight
            # -------------------------------------------------------------
            if (
                self._table._focused_row is not None
                and self._table._focused_col is not None
                and 0 <= self._table._focused_row < len(visible_data)
            ):
                f_raw = self._table._get_raw_index(self._table._focused_row)
                f_col_idx = self._table._focused_col
                if 0 <= f_col_idx < len(self._table._columns):
                    f_col = self._table._columns[f_col_idx]
                    if f_col.get("visible", True) is not False:
                        fcx, fcw = self._table._get_col_x_and_width(f_col_idx)
                        fcy = hdr_h + (self._table._focused_row * row_h) - scroll_y
                        if fcx + fcw > (pinned_w if f_col_idx >= pinned_n else 0) and fcx < w:
                            surf.stroke_rounded_rect(
                                fcx + 1.0 * s,
                                fcy + 1.0 * s,
                                fcw - 2.0 * s,
                                row_h - 2.0 * s,
                                2.0 * s,
                                2.0 * s,
                                pal.primary,
                                stroke_width=1.8 * s,
                            )

            # -------------------------------------------------------------
            # 4. Sticky Header Background, Columns, Multi-Sort & Indicators
            # -------------------------------------------------------------
            surf.fill_rect(0, 0, w, hdr_h, pal.surface)
            surf.fill_rect(0, hdr_h - 1.0 * s, w, 1.0 * s, pal.surface_border)

            font_sz_hdr = max(9.0, 11.0 * s)

            def render_header_col(col: Dict[str, Any], cx: float, cw: float):
                raw_c_idx = self._table._columns.index(col)
                align = col.get("align", "left")
                title = (
                    col.get("title")
                    or col.get("name")
                    or col.get("header")
                    or col.get("heading")
                    or col.get("label")
                    or col.get("text")
                    or col.get("id", f"Col {raw_c_idx}")
                )

                # Hover on column header
                if self._table._hovered_col == raw_c_idx and self._table._resizing_col is None:
                    surf.fill_rect(max(0.0, cx), 0, cw, hdr_h - 1.0 * s, pal.secondary)

                # Header Checkbox
                if col.get("type") == "checkbox":
                    cb_size = 14.0 * s
                    cb_x = cx + (cw - cb_size) / 2.0
                    cb_y = (hdr_h - cb_size) / 2.0
                    all_checked = (
                        len(self._table._selected_rows) > 0
                        and len(self._table._selected_rows) == len(self._table._data)
                    )
                    surf.stroke_rounded_rect(
                        cb_x, cb_y, cb_size, cb_size, 3.0 * s, 3.0 * s, pal.surface_border, stroke_width=1.2 * s
                    )
                    if all_checked:
                        surf.fill_rounded_rect(
                            cb_x, cb_y, cb_size, cb_size, 3.0 * s, 3.0 * s, pal.primary
                        )
                        draw_vector_checkmark(
                            surf, cb_x + cb_size / 2.0, cb_y + cb_size / 2.0, 0.8 * s, "#ffffff"
                        )
                else:
                    ty = compute_text_baseline_y(hdr_h / 2.0, font_sz_hdr)
                    if align == "center":
                        tx = cx + cw / 2.0
                    elif align == "right":
                        tx = cx + cw - 16.0 * s
                    else:
                        tx = cx + 10.0 * s

                    display_txt = truncate_text(title, max(10.0, cw - 32.0 * s), font_sz_hdr)
                    surf.draw_text(
                        display_txt,
                        tx,
                        ty,
                        font_size=font_sz_hdr,
                        font_family="sans-serif",
                        color=pal.fg,
                        align=align,
                    )

                    # Multi-sort badge / indicator
                    sort_info = self._table._get_sort_info_for_column(raw_c_idx)
                    if sort_info is not None:
                        rank, is_desc = sort_info
                        chev_dir = "down" if is_desc else "up"
                        # If multi-column sorting active, show order rank number
                        if len(self._table._sort_criteria) > 1:
                            badge_txt = f"{rank}{'▼' if is_desc else '▲'}"
                            surf.draw_text(
                                badge_txt,
                                cx + cw - 16.0 * s,
                                ty,
                                font_size=max(8.0, 9.0 * s),
                                font_family="sans-serif",
                                color=pal.primary,
                                align="right",
                            )
                        else:
                            draw_vector_chevron(
                                surf,
                                cx + cw - 12.0 * s,
                                hdr_h / 2.0,
                                scale=0.9 * s,
                                direction=chev_dir,
                                color=pal.primary,
                                stroke_width=1.6 * s,
                            )

                # Column separator divider
                surf.fill_rect(
                    cx + cw - 1.0 * s, 4.0 * s, 1.0 * s, hdr_h - 8.0 * s, pal.surface_border
                )

            # A. Render Unpinned Headers
            curr_x = pinned_w - scroll_x
            for col in unpinned_cols:
                cw = col.get("width", 100) * s
                if curr_x + cw > pinned_w and curr_x < w:
                    render_header_col(col, curr_x, cw)
                curr_x += cw

            # B. Render Pinned Headers (Fixed at Left)
            pinned_hx = 0.0
            for col in pinned_cols:
                cw = col.get("width", 100) * s
                surf.fill_rect(pinned_hx, 0, cw, hdr_h - 1.0 * s, pal.surface)
                render_header_col(col, pinned_hx, cw)
                pinned_hx += cw

            # Divider between pinned header and unpinned header
            if pinned_w > 0:
                surf.fill_rect(pinned_w - 1.0 * s, 0, 1.5 * s, hdr_h, pal.surface_border)

            # -------------------------------------------------------------
            # 5. Drag-and-Drop Column Reordering Drop Indicator
            # -------------------------------------------------------------
            if (
                self._table._dragging_col_idx is not None
                and self._table._drag_target_x is not None
            ):
                ix = self._table._drag_target_x
                # Visual insertion line
                surf.fill_rect(ix - 1.5 * s, 0, 3.0 * s, hdr_h, pal.primary)
                # Drop indicator top/bottom triangles
                surf.fill_rect(ix - 4.0 * s, 0, 8.0 * s, 3.0 * s, pal.primary)
                surf.fill_rect(ix - 4.0 * s, hdr_h - 3.0 * s, 8.0 * s, 3.0 * s, pal.primary)

        except Exception as e:
            logger.debug("Render failed in _TableViewSurface: %s", e, exc_info=True)


# -------------------------------------------------------------------------
# MAIN TABLE WIDGET
# -------------------------------------------------------------------------

class Table(tk.Frame):
    """
    High-performance pure Blend2D vector data table with multi-column sorting,
    drag-and-drop column reordering, frozen/pinned columns, column visibility toggling,
    dual-axis vector scrollbars, multi-selection (row or cell units), active cell focus rectangle,
    rich in-place editors (text, dropdown, numeric), dynamic styling hooks,
    right-click context menus, filtering, pagination, and TSV/CSV clipboard export.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        columns: Optional[List[Union[str, Dict[str, Any]]]] = None,
        data: Optional[List[Union[Dict[str, Any], List[Any], Tuple[Any, ...]]]] = None,
        width: int = 500,
        height: int = 260,
        header_height: int = 34,
        row_height: int = 32,
        select_mode: str = "extended",
        select_unit: str = "row",
        pinned_columns: int = 0,
        pagination: bool = False,
        page_size: Optional[int] = None,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        on_select: Optional[Callable[..., None]] = None,
        on_double_click: Optional[Callable[[int, Any], None]] = None,
        on_cell_edit: Optional[Callable[[int, str, Any, Any], None]] = None,
        on_cell_validate: Optional[Callable[[int, str, Any, Any], bool]] = None,
        on_column_reorder: Optional[Callable[[int, int], None]] = None,
        on_context_menu: Optional[Callable[[Optional[int], Optional[str], tk.Menu], None]] = None,
        row_styler: Optional[Callable[[int, Any], Optional[Dict[str, Any]]]] = None,
        cell_styler: Optional[Callable[[int, str, Any], Optional[Dict[str, Any]]]] = None,
        command: Optional[Callable[..., None]] = None,
        inner_bg: Optional[str] = None,
        outer_bg: Optional[str] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._scale = ScalingTracker.get_scaling_factor(master)
        pal = get_theme()
        self._explicit_outer_bg = outer_bg if outer_bg is not None else parent_bg
        self._explicit_inner_bg = inner_bg if inner_bg is not None else bg_color
        self._explicit_parent_bg = self._explicit_outer_bg
        self._parent_bg = self._explicit_outer_bg or pal.bg
        self._bg_color = self._explicit_inner_bg
        self._columns = self._normalize_columns(columns)
        self._data = list(data) if data else []
        self._header_height = header_height
        self._row_height = row_height
        self._select_mode = select_mode  # "extended", "single", "multiple", "none"
        self._select_unit = select_unit  # "row", "cell"
        self._pinned_columns = max(0, pinned_columns)
        self._pagination = pagination or (page_size is not None)
        self._page_size = page_size or 20
        self._current_page = 0

        self._border_color = border_color
        self._border_width = border_width

        self._on_select = on_select or command
        self._on_double_click = on_double_click
        self._on_cell_edit = on_cell_edit
        self._on_cell_validate = on_cell_validate
        self._on_column_reorder = on_column_reorder
        self._on_context_menu = on_context_menu
        self._row_styler = row_styler
        self._cell_styler = cell_styler

        # Selection state
        self._selected_rows: Set[int] = set()
        self._selected_cells: Set[Tuple[int, int]] = set()  # (raw_row_idx, raw_col_idx)
        self._anchor_row: Optional[int] = None
        self._anchor_col: Optional[int] = None
        self._focused_row: Optional[int] = None
        self._focused_col: Optional[int] = 0
        self._hovered_row: Optional[int] = None
        self._hovered_col: Optional[int] = None

        # Sorting state: list of (col_idx, descending_bool)
        self._sort_criteria: List[Tuple[int, bool]] = []

        # Resizing state
        self._resizing_col: Optional[int] = None
        self._resize_start_x: float = 0.0
        self._resize_orig_width: float = 0.0

        # Column drag-and-drop reordering state
        self._dragging_col_idx: Optional[int] = None
        self._drag_target_col_idx: Optional[int] = None
        self._drag_target_x: Optional[float] = None

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
            background=to_tk_hex(self.bg_color),
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )

        # Configure Grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Vector Surface
        self._view = _TableViewSurface(
            self,
            table=self,
            parent_bg=self.bg_color,
        )
        self._view.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # Vertical Scrollbar
        self._v_scrollbar = VectorScrollbar(
            self,
            command=self._on_vscroll,
            orientation="vertical",
            width=8,
            parent_bg=self.bg_color,
        )
        self._v_scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 2), pady=0)

        # Horizontal Scrollbar
        self._h_scrollbar = VectorScrollbar(
            self,
            command=self._on_hscroll,
            orientation="horizontal",
            height=8,
            parent_bg=self.bg_color,
        )
        self._h_scrollbar.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 2))

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
        self._view.bind("<Shift-Left>", self._on_key_shift_left)
        self._view.bind("<Shift-Right>", self._on_key_shift_right)
        self._view.bind("<Prior>", self._on_key_page_up)
        self._view.bind("<Next>", self._on_key_page_down)
        self._view.bind("<Home>", self._on_key_home)
        self._view.bind("<End>", self._on_key_end)
        self._view.bind("<Return>", self._on_key_return)
        self._view.bind("<F2>", self._on_key_return)
        self._view.bind("<Control-a>", self._on_key_select_all)
        self._view.bind("<Command-a>", self._on_key_select_all)
        self._view.bind("<Control-c>", self._on_key_copy)
        self._view.bind("<Command-c>", self._on_key_copy)

        add_theme_listener(self._on_theme_changed)
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._update_filtered_indices()
        self._update_scroll_geometry()

    @property
    def inner_bg(self) -> str:
        """Return the current interior background color."""
        pal = get_theme()
        return resolve_color_failsafe(self._bg_color or pal.card_bg, palette=pal)

    @property
    def outer_bg(self) -> str:
        """Return the current parent/outer background color."""
        pal = get_theme()
        return resolve_color_failsafe(self._parent_bg or pal.bg, palette=pal)

    @property
    def bg_color(self) -> str:
        """Alias for inner_bg."""
        return self.inner_bg

    @property
    def parent_bg(self) -> str:
        """Alias for outer_bg."""
        return self.outer_bg

    @property
    def row_count(self) -> int:
        """Return the total number of rows in the table."""
        return len(self._data)

    @property
    def column_count(self) -> int:
        """Return the total number of columns in the table."""
        return len(self._columns)

    @property
    def select_unit(self) -> str:
        return self._select_unit

    @select_unit.setter
    def select_unit(self, unit: str) -> None:
        if unit in ("row", "cell"):
            self._select_unit = unit
            self._view.request_redraw()

    @property
    def pinned_columns(self) -> int:
        return self._pinned_columns

    @pinned_columns.setter
    def pinned_columns(self, count: int) -> None:
        self.set_pinned_column_count(count)

    def set_pinned_column_count(self, count: int) -> None:
        """Set the number of pinned/frozen columns on the left."""
        self._pinned_columns = max(0, int(count))
        self._update_scroll_geometry()
        self._view.request_redraw()

    @property
    def _sort_col(self) -> Optional[int]:
        """Backward-compatible access to primary sort column index."""
        return self._sort_criteria[0][0] if self._sort_criteria else None

    @_sort_col.setter
    def _sort_col(self, col: Optional[int]) -> None:
        if col is None:
            self._sort_criteria.clear()
        else:
            self._sort_criteria = [(col, self._sort_desc)]

    @property
    def _sort_desc(self) -> bool:
        """Backward-compatible access to primary sort direction."""
        return self._sort_criteria[0][1] if self._sort_criteria else False

    @_sort_desc.setter
    def _sort_desc(self, desc: bool) -> None:
        if self._sort_criteria:
            self._sort_criteria[0] = (self._sort_criteria[0][0], desc)
        elif self._sort_col is not None:
            self._sort_criteria = [(self._sort_col, desc)]

    def _get_sort_info_for_column(self, col_idx: int) -> Optional[Tuple[int, bool]]:
        """Return (1-based rank, is_desc) if column is sorted, else None."""
        for i, (c, desc) in enumerate(self._sort_criteria):
            if c == col_idx:
                return (i + 1, desc)
        return None

    def _get_visible_columns(self) -> List[Dict[str, Any]]:
        """Return list of columns that are currently visible."""
        return [c for c in self._columns if c.get("visible", True) is not False]

    def _build_pagination_bar(self) -> None:
        """Construct the pagination control bar."""
        pal = get_theme()
        s = self._scale
        self._page_frame = tk.Frame(
            self,
            bg=to_tk_hex(self.bg_color),
            height=int(28 * s),
        )
        self._page_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=(0, 4))

        self._btn_prev = tk.Button(
            self._page_frame,
            text="◀ Prev",
            command=self.prev_page,
            font=("sans-serif", max(8, int(9.5 * s))),
            bg=to_tk_hex(pal.secondary),
            fg=to_tk_hex(pal.fg),
            relief="flat",
            activebackground=to_tk_hex(pal.primary),
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
            bg=to_tk_hex(self.bg_color),
            fg=to_tk_hex(pal.fg),
        )
        self._page_label.pack(side="left", padx=8)

        self._btn_next = tk.Button(
            self._page_frame,
            text="Next ▶",
            command=self.next_page,
            font=("sans-serif", max(8, int(9.5 * s))),
            bg=to_tk_hex(pal.secondary),
            fg=to_tk_hex(pal.fg),
            relief="flat",
            activebackground=to_tk_hex(pal.primary),
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

    @classmethod
    def _normalize_columns(cls, columns: Optional[List[Union[Dict[str, Any], str]]]) -> List[Dict[str, Any]]:
        if not columns:
            return [
                {"id": "col1", "title": "Column 1", "width": 120, "align": "left", "visible": True},
                {"id": "col2", "title": "Column 2", "width": 140, "align": "left", "visible": True},
            ]
        norm: List[Dict[str, Any]] = []
        for i, col in enumerate(columns):
            if isinstance(col, str):
                norm.append({"id": col, "title": col, "width": 100, "align": "left", "visible": True})
            elif isinstance(col, dict):
                c = dict(col)
                title = (
                    c.get("title")
                    or c.get("name")
                    or c.get("header")
                    or c.get("heading")
                    or c.get("label")
                    or c.get("text")
                )
                if title is None:
                    title = c.get("id", f"Col {i}")
                c["title"] = str(title)
                if "id" not in c:
                    c["id"] = str(c.get("name") or c.get("key") or f"col_{i}")
                if "width" not in c:
                    c["width"] = 100
                if "align" not in c:
                    c["align"] = "left"
                if "visible" not in c:
                    c["visible"] = True
                norm.append(c)
            else:
                norm.append({"id": f"col_{i}", "title": str(col), "width": 100, "align": "left", "visible": True})
        return norm

    # -------------------------------------------------------------
    # DATA & COLUMN MANAGEMENT
    # -------------------------------------------------------------
    def set_columns(self, columns: List[Union[Dict[str, Any], str]]) -> None:
        """Set the table columns definition."""
        self._columns = self._normalize_columns(columns)
        self._sort_criteria.clear()
        self._update_scroll_geometry()
        self._view.request_redraw()

    def set_data(self, data: List[Union[Dict[str, Any], List[Any], Tuple[Any, ...]]]) -> None:
        """Replace the entire dataset."""
        self._data = list(data)
        self._selected_rows.clear()
        self._selected_cells.clear()
        self._anchor_row = None
        self._anchor_col = None
        self._focused_row = None
        self._hovered_row = None
        self._current_page = 0
        self._update_filtered_indices()
        self._update_scroll_geometry()
        self._update_pagination_ui()
        self._view.request_redraw()

    def insert_row(
        self,
        row: Optional[Any] = None,
        index: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Insert a single row."""
        target_row: Any = None
        target_index: Optional[int] = index

        if "data" in kwargs:
            target_row = kwargs["data"]
        elif "row" in kwargs:
            target_row = kwargs["row"]

        if isinstance(row, int) and target_row is None and not args:
            target_index = row
        elif isinstance(row, int) and args:
            target_index = row
            target_row = args[0]
        elif row is not None and target_row is None:
            if isinstance(row, (dict, list, tuple, str)):
                target_row = row
                if args and isinstance(args[0], int) and target_index is None:
                    target_index = args[0]
            else:
                target_row = row

        if target_row is None:
            target_row = {}

        if target_index is None or target_index >= len(self._data):
            self._data.append(target_row)
        else:
            self._data.insert(max(0, target_index), target_row)

        self._update_filtered_indices()
        self._update_scroll_geometry()
        self._update_pagination_ui()
        self._view.request_redraw()

    def delete_row(self, index: int) -> None:
        """Delete a row by index."""
        if 0 <= index < len(self._data):
            self._data.pop(index)
            self._selected_rows.discard(index)
            self._selected_rows = {i if i < index else i - 1 for i in self._selected_rows}
            self._selected_cells = {(r if r < index else r - 1, c) for r, c in self._selected_cells if r != index}
            self._update_filtered_indices()
            self._update_scroll_geometry()
            self._update_pagination_ui()
            self._view.request_redraw()

    def clear(self) -> None:
        """Clear all rows."""
        self._data.clear()
        self._selected_rows.clear()
        self._selected_cells.clear()
        self._anchor_row = None
        self._anchor_col = None
        self._focused_row = None
        self._hovered_row = None
        self._current_page = 0
        self._update_filtered_indices()
        self._update_scroll_geometry()
        self._update_pagination_ui()
        self._view.request_redraw()

    def set_cell_value(self, row_index: int, col_id: str, value: Any) -> None:
        """Set a specific cell value."""
        if 0 <= row_index < len(self._data):
            row = self._data[row_index]
            if isinstance(row, dict):
                row[col_id] = value
            elif isinstance(row, list):
                col_idx = self._get_col_index_by_id(col_id)
                if col_idx is not None and col_idx < len(row):
                    row[col_idx] = value
            self._view.request_redraw()

    def get_cell_value(self, row_index: int, col_id: str) -> Any:
        """Get a specific cell value."""
        if 0 <= row_index < len(self._data):
            row = self._data[row_index]
            if isinstance(row, dict):
                return row.get(col_id, "")
            elif isinstance(row, (list, tuple)):
                col_idx = self._get_col_index_by_id(col_id)
                if col_idx is not None and col_idx < len(row):
                    return row[col_idx]
        return ""

    def _get_col_raw_index(self, col: Dict[str, Any]) -> int:
        for i, c in enumerate(self._columns):
            if c is col:
                return i
        try:
            return self._columns.index(col)
        except ValueError:
            return 0

    def _get_col_index_by_id(self, col_id: str) -> Optional[int]:
        for i, c in enumerate(self._columns):
            if c.get("id") == col_id or c.get("name") == col_id or c.get("title") == col_id:
                return i
        return None

    # -------------------------------------------------------------
    # COLUMN VISIBILITY & REORDERING
    # -------------------------------------------------------------
    def set_column_visibility(self, col_identifier: Union[int, str], visible: bool) -> None:
        """Show or hide a column by ID or index."""
        col_idx = self._get_col_index_by_id(col_identifier) if isinstance(col_identifier, str) else col_identifier
        if col_idx is not None and 0 <= col_idx < len(self._columns):
            self._columns[col_idx]["visible"] = bool(visible)
            self._update_scroll_geometry()
            self._view.request_redraw()

    def hide_column(self, col_identifier: Union[int, str]) -> None:
        """Hide a column."""
        self.set_column_visibility(col_identifier, False)

    def show_column(self, col_identifier: Union[int, str]) -> None:
        """Show a previously hidden column."""
        self.set_column_visibility(col_identifier, True)

    def is_column_visible(self, col_identifier: Union[int, str]) -> bool:
        """Check if column is visible."""
        col_idx = self._get_col_index_by_id(col_identifier) if isinstance(col_identifier, str) else col_identifier
        if col_idx is not None and 0 <= col_idx < len(self._columns):
            return self._columns[col_idx].get("visible", True) is not False
        return False

    def _reorder_column(self, src_idx: int, dst_idx: int) -> None:
        """Move column from src_idx to dst_idx in self._columns."""
        if 0 <= src_idx < len(self._columns) and 0 <= dst_idx < len(self._columns):
            col = self._columns.pop(src_idx)
            self._columns.insert(dst_idx, col)
            self._update_scroll_geometry()
            if self._on_column_reorder:
                try:
                    self._on_column_reorder(src_idx, dst_idx)
                except Exception as e:
                    logger.debug("on_column_reorder error: %s", e)
            self._view.request_redraw()

    def _get_reorder_target_at_x(self, x: float) -> Tuple[int, float]:
        """Compute target insertion column index and visual x coordinate."""
        s = self._scale
        vis_cols = self._get_visible_columns()
        pinned_n = min(self._pinned_columns, len(vis_cols))
        pinned_w = sum(c.get("width", 100) * s for c in vis_cols[:pinned_n])

        curr_x = 0.0
        for i in range(pinned_n):
            col = vis_cols[i]
            cw = col.get("width", 100) * s
            mid = curr_x + cw / 2.0
            if x < mid:
                return (self._columns.index(col), curr_x)
            curr_x += cw

        curr_x = pinned_w - self._scroll_x
        for i in range(pinned_n, len(vis_cols)):
            col = vis_cols[i]
            cw = col.get("width", 100) * s
            mid = curr_x + cw / 2.0
            if x < mid:
                return (self._columns.index(col), max(pinned_w, curr_x))
            curr_x += cw

        last_col = vis_cols[-1] if vis_cols else self._columns[-1]
        return (self._columns.index(last_col), curr_x)

    # -------------------------------------------------------------
    # FILTERING & SEARCH
    # -------------------------------------------------------------
    def filter_by(self, query_or_func: Union[str, Callable[[Any], bool], None]) -> None:
        """Filter table rows by search string or custom predicate function."""
        self._filter_query = query_or_func
        self._current_page = 0
        self._update_filtered_indices()
        self._update_scroll_geometry()
        self._update_pagination_ui()
        self._view.request_redraw()

    def clear_filter(self) -> None:
        """Clear active search / filter query."""
        self.filter_by(None)

    def _update_filtered_indices(self) -> None:
        if self._filter_query is None:
            self._filtered_indices = list(range(len(self._data)))
        elif callable(self._filter_query):
            self._filtered_indices = [
                i for i, row in enumerate(self._data) if self._filter_query(row)
            ]
        elif isinstance(self._filter_query, str):
            q = self._filter_query.strip().lower()
            if not q:
                self._filtered_indices = list(range(len(self._data)))
            else:
                filtered: List[int] = []
                for i, row in enumerate(self._data):
                    if isinstance(row, dict):
                        match = any(q in str(v).lower() for v in row.values())
                    elif isinstance(row, (list, tuple)):
                        match = any(q in str(v).lower() for v in row)
                    else:
                        match = q in str(row).lower()
                    if match:
                        filtered.append(i)
                self._filtered_indices = filtered

        if self._sort_criteria:
            self._apply_sort()

    def get_filtered_data(self) -> List[Any]:
        """Return list of rows currently matching filter."""
        return [self._data[i] for i in self._filtered_indices if i < len(self._data)]

    def _get_visible_data(self) -> List[Any]:
        filtered = self.get_filtered_data()
        if not self._pagination:
            return filtered
        start = self._current_page * self._page_size
        end = start + self._page_size
        return filtered[start:end]

    def _get_raw_index(self, visible_idx: int) -> int:
        filtered = self._filtered_indices
        if not self._pagination:
            if 0 <= visible_idx < len(filtered):
                return filtered[visible_idx]
            return visible_idx
        start = self._current_page * self._page_size
        actual_filtered_idx = start + visible_idx
        if 0 <= actual_filtered_idx < len(filtered):
            return filtered[actual_filtered_idx]
        return actual_filtered_idx

    # -------------------------------------------------------------
    # PAGINATION
    # -------------------------------------------------------------
    def get_total_pages(self) -> int:
        if not self._pagination or self._page_size <= 0:
            return 1
        total_rows = len(self._filtered_indices)
        return max(1, (total_rows + self._page_size - 1) // self._page_size)

    def get_current_page(self) -> int:
        return self._current_page

    def set_page(self, page_idx: int) -> None:
        total = self.get_total_pages()
        self._current_page = max(0, min(total - 1, page_idx))
        self._scroll_y = 0.0
        self._update_scroll_geometry()
        self._update_pagination_ui()
        self._view.request_redraw()

    def next_page(self) -> None:
        self.set_page(self._current_page + 1)

    def prev_page(self) -> None:
        self.set_page(self._current_page - 1)

    def set_page_size(self, size: int) -> None:
        self._page_size = max(1, size)
        self.set_page(0)

    # -------------------------------------------------------------
    # MULTI-COLUMN SORTING
    # -------------------------------------------------------------
    def _on_header_click(self, col_idx: int, multi_sort: bool = False) -> None:
        col = self._columns[col_idx]
        if col.get("type") == "checkbox":
            if len(self._selected_rows) == len(self._data) and len(self._data) > 0:
                self.clear_selection()
            else:
                self.select_all()
            return

        if multi_sort:
            found_idx = -1
            for i, (c, desc) in enumerate(self._sort_criteria):
                if c == col_idx:
                    found_idx = i
                    break

            if found_idx >= 0:
                cur_col, cur_desc = self._sort_criteria[found_idx]
                if not cur_desc:
                    self._sort_criteria[found_idx] = (cur_col, True)
                else:
                    self._sort_criteria.pop(found_idx)
            else:
                self._sort_criteria.append((col_idx, False))
        else:
            if len(self._sort_criteria) == 1 and self._sort_criteria[0][0] == col_idx:
                if not self._sort_criteria[0][1]:
                    self._sort_criteria = [(col_idx, True)]
                else:
                    self._sort_criteria.clear()
            else:
                self._sort_criteria = [(col_idx, False)]

        self._apply_sort()

    def sort_by(
        self,
        col_identifier: Union[int, str],
        descending: Optional[bool] = None,
        multi: bool = False,
    ) -> None:
        """Programmatically sort table by column name or index."""
        col_idx = self._get_col_index_by_id(col_identifier) if isinstance(col_identifier, str) else col_identifier
        if col_idx is None or not (0 <= col_idx < len(self._columns)):
            return

        is_desc = bool(descending) if descending is not None else False
        if multi:
            self._sort_criteria = [(c, d) for c, d in self._sort_criteria if c != col_idx]
            self._sort_criteria.append((col_idx, is_desc))
        else:
            self._sort_criteria = [(col_idx, is_desc)]

        self._apply_sort()

    def reset_sorting(self) -> None:
        """Clear all active sort criteria and revert to original data order."""
        self._sort_criteria.clear()
        self._update_filtered_indices()
        self._view.request_redraw()

    def _apply_sort(self) -> None:
        if not self._sort_criteria:
            self._update_filtered_indices()
            self._view.request_redraw()
            return

        from functools import cmp_to_key

        def compare_rows(r1: int, r2: int) -> int:
            if r1 >= len(self._data) or r2 >= len(self._data):
                return 0
            row1 = self._data[r1]
            row2 = self._data[r2]

            for col_idx, desc in self._sort_criteria:
                if col_idx >= len(self._columns):
                    continue
                col = self._columns[col_idx]
                col_id = col.get("id", str(col_idx))
                key_name = col.get("name", col_id)

                val1 = ""
                if isinstance(row1, dict):
                    val1 = row1.get(col_id, row1.get(key_name, ""))
                elif isinstance(row1, (list, tuple)) and col_idx < len(row1):
                    val1 = row1[col_idx]

                val2 = ""
                if isinstance(row2, dict):
                    val2 = row2.get(col_id, row2.get(key_name, ""))
                elif isinstance(row2, (list, tuple)) and col_idx < len(row2):
                    val2 = row2[col_idx]

                if val1 == val2:
                    continue

                try:
                    n1 = float(str(val1).replace("%", "").strip())
                    n2 = float(str(val2).replace("%", "").strip())
                    res = (n1 > n2) - (n1 < n2)
                except Exception:
                    s1 = str(val1).lower()
                    s2 = str(val2).lower()
                    res = (s1 > s2) - (s1 < s2)

                if res != 0:
                    return -res if desc else res

            return 0

        self._filtered_indices.sort(key=cmp_to_key(compare_rows))
        self._view.request_redraw()

    # -------------------------------------------------------------
    # AUTO-FIT COLUMNS
    # -------------------------------------------------------------
    def auto_fit_column(self, col_idx: int) -> None:
        """Auto-size column width to fit its longest content string."""
        if not (0 <= col_idx < len(self._columns)):
            return
        col = self._columns[col_idx]
        col_id = col.get("id", str(col_idx))
        title = col.get("title", f"Col {col_idx}")

        max_len = len(str(title))
        for row in self._data:
            if isinstance(row, dict):
                v = str(row.get(col_id, row.get(col.get("name", ""), "")))
            elif isinstance(row, (list, tuple)) and col_idx < len(row):
                v = str(row[col_idx])
            else:
                v = ""
            if len(v) > max_len:
                max_len = len(v)

        calc_w = max(50, int(max_len * 9.5 + 36))
        col["width"] = calc_w
        self._update_scroll_geometry()
        self._view.request_redraw()

    def auto_fit_all_columns(self) -> None:
        """Auto-fit all column widths."""
        for i in range(len(self._columns)):
            self.auto_fit_column(i)

    # -------------------------------------------------------------
    # SELECTION ENGINE
    # -------------------------------------------------------------
    def _handle_item_click(self, raw_row_idx: int, col_idx: int, state: int) -> None:
        if self._select_mode == "none":
            return

        is_shift = bool(state & 0x0001)
        is_ctrl = bool(state & 0x0004 or state & 0x0008)

        if self._select_unit == "cell":
            if self._select_mode == "single":
                self._selected_cells = {(raw_row_idx, col_idx)}
                self._anchor_row = raw_row_idx
                self._anchor_col = col_idx
            elif self._select_mode == "multiple":
                if (raw_row_idx, col_idx) in self._selected_cells:
                    self._selected_cells.remove((raw_row_idx, col_idx))
                else:
                    self._selected_cells.add((raw_row_idx, col_idx))
                self._anchor_row = raw_row_idx
                self._anchor_col = col_idx
            else:  # "extended"
                if is_shift and self._anchor_row is not None and self._anchor_col is not None:
                    min_r, max_r = min(self._anchor_row, raw_row_idx), max(self._anchor_row, raw_row_idx)
                    min_c, max_c = min(self._anchor_col, col_idx), max(self._anchor_col, col_idx)
                    self._selected_cells = {(r, c) for r in range(min_r, max_r + 1) for c in range(min_c, max_c + 1)}
                elif is_ctrl:
                    if (raw_row_idx, col_idx) in self._selected_cells:
                        self._selected_cells.remove((raw_row_idx, col_idx))
                    else:
                        self._selected_cells.add((raw_row_idx, col_idx))
                    self._anchor_row = raw_row_idx
                    self._anchor_col = col_idx
                else:
                    self._selected_cells = {(raw_row_idx, col_idx)}
                    self._anchor_row = raw_row_idx
                    self._anchor_col = col_idx
        else:
            if self._select_mode == "single":
                self._selected_rows = {raw_row_idx}
                self._anchor_row = raw_row_idx
            elif self._select_mode == "multiple":
                if raw_row_idx in self._selected_rows:
                    self._selected_rows.remove(raw_row_idx)
                else:
                    self._selected_rows.add(raw_row_idx)
                self._anchor_row = raw_row_idx
            else:  # "extended"
                if is_shift and self._anchor_row is not None:
                    start_i = min(self._anchor_row, raw_row_idx)
                    end_i = max(self._anchor_row, raw_row_idx)
                    self._selected_rows = set(range(start_i, end_i + 1))
                elif is_ctrl:
                    if raw_row_idx in self._selected_rows:
                        self._selected_rows.remove(raw_row_idx)
                    else:
                        self._selected_rows.add(raw_row_idx)
                    self._anchor_row = raw_row_idx
                else:
                    self._selected_rows = {raw_row_idx}
                    self._anchor_row = raw_row_idx

        # Calculate visible row index for focused position
        try:
            vis_row_idx = self._get_visible_data().index(self._data[raw_row_idx])
        except (ValueError, IndexError):
            vis_row_idx = 0
        self._focused_row = vis_row_idx
        self._focused_col = col_idx

        if self._on_select:
            try:
                selected_data = [self._data[i] for i in self._selected_rows if i < len(self._data)]
                self._on_select(raw_row_idx, selected_data)
            except Exception as e:
                logger.debug("on_select error: %s", e)

        self._view.request_redraw()

    def get_selected_indices(self) -> List[int]:
        """Return list of selected raw row indices."""
        return sorted(list(self._selected_rows))

    def get_selected_index(self) -> Optional[int]:
        """Return the first selected raw row index or None."""
        return next(iter(self._selected_rows)) if self._selected_rows else None

    def get_selected_rows(self) -> List[Any]:
        """Return list of selected row data items."""
        return [self._data[i] for i in self.get_selected_indices() if i < len(self._data)]

    def get_selected_cells(self) -> List[Tuple[int, int]]:
        """Return list of selected (row_index, col_index) tuples."""
        return sorted(list(self._selected_cells))

    def select_row(self, index: int, append: bool = False) -> None:
        """Select a row by index."""
        if 0 <= index < len(self._data):
            if not append or self._select_mode == "single":
                self._selected_rows.clear()
            self._selected_rows.add(index)
            self._anchor_row = index
            try:
                self._focused_row = self._get_visible_data().index(self._data[index])
            except (ValueError, IndexError):
                self._focused_row = 0
            self._view.request_redraw()

    def set_selection(self, index: int) -> None:
        """Set single row selection (alias to select_row)."""
        self.select_row(index, append=False)

    def deselect_row(self, index: int) -> None:
        """Deselect a row by index."""
        self._selected_rows.discard(index)
        self._view.request_redraw()

    def select_cell(self, row_idx: int, col_idx: int, append: bool = False) -> None:
        """Select a single cell."""
        if 0 <= row_idx < len(self._data) and 0 <= col_idx < len(self._columns):
            if not append:
                self._selected_cells.clear()
            self._selected_cells.add((row_idx, col_idx))
            self._anchor_row = row_idx
            self._anchor_col = col_idx
            try:
                self._focused_row = self._get_visible_data().index(self._data[row_idx])
            except (ValueError, IndexError):
                self._focused_row = 0
            self._focused_col = col_idx
            self._view.request_redraw()

    def select_all(self) -> None:
        """Select all table rows or cells."""
        if self._select_mode in ("extended", "multiple"):
            self._selected_rows = set(range(len(self._data)))
            if self._select_unit == "cell":
                self._selected_cells = {
                    (r, c) for r in range(len(self._data)) for c in range(len(self._columns))
                }
            self._view.request_redraw()

    def clear_selection(self) -> None:
        """Clear all selections."""
        self._selected_rows.clear()
        self._selected_cells.clear()
        self._anchor_row = None
        self._anchor_col = None
        self._focused_row = None
        self._view.request_redraw()

    def paint_and_blit(self) -> None:
        """Force immediate synchronous repaint and blit."""
        self._view.paint_and_blit()
        self._v_scrollbar.paint_and_blit()
        self._h_scrollbar.paint_and_blit()

    # -------------------------------------------------------------
    # IN-PLACE CELL EDITING
    # -------------------------------------------------------------
    def _start_cell_edit(self, raw_idx: int, col_idx: int, visible_row_idx: int) -> None:
        col = self._columns[col_idx]
        col_id = col.get("id", str(col_idx))
        curr_val = self.get_cell_value(raw_idx, col_id)

        s = self._scale
        hdr_h = self._header_height * s
        row_h = self._row_height * s

        cx, cw = self._get_col_x_and_width(col_idx)
        cell_y = hdr_h + (visible_row_idx * row_h) - self._scroll_y

        editor_type = col.get("editor", "text")
        options = col.get("editor_options") or col.get("options")

        if editor_type == "select" or options:
            _DropdownCellEditor(
                self._view,
                table=self,
                row_idx=raw_idx,
                col_idx=col_idx,
                initial_value=str(curr_val),
                options=options or [],
                x=int(cx + 2 * s),
                y=int(cell_y + 2 * s),
                width=int(cw - 4 * s),
                height=int(row_h - 4 * s),
            )
        elif editor_type == "number":
            _NumericCellEditor(
                self._view,
                table=self,
                row_idx=raw_idx,
                col_idx=col_idx,
                initial_value=curr_val,
                x=int(cx + 2 * s),
                y=int(cell_y + 2 * s),
                width=int(cw - 4 * s),
                height=int(row_h - 4 * s),
                step=col.get("step", 1.0),
                min_val=col.get("min_val"),
                max_val=col.get("max_val"),
            )
        else:
            _FloatingCellEditor(
                self._view,
                table=self,
                row_idx=raw_idx,
                col_idx=col_idx,
                initial_value=str(curr_val),
                x=int(cx + 2 * s),
                y=int(cell_y + 2 * s),
                width=int(cw - 4 * s),
                height=int(row_h - 4 * s),
            )

    def _on_editor_closed(
        self,
        row_idx: int,
        col_idx: int,
        orig_val: str,
        new_val: str,
        commit: bool,
    ) -> None:
        if not commit or new_val == orig_val:
            self._view.focus_set()
            self._view.request_redraw()
            return

        col = self._columns[col_idx]
        col_id = col.get("id", str(col_idx))

        if self._on_cell_validate:
            try:
                valid = self._on_cell_validate(row_idx, col_id, orig_val, new_val)
                if not valid:
                    self._view.focus_set()
                    self._view.request_redraw()
                    return
            except Exception as e:
                logger.debug("Validation error: %s", e)

        self.set_cell_value(row_idx, col_id, new_val)
        if self._on_cell_edit:
            try:
                self._on_cell_edit(row_idx, col_id, orig_val, new_val)
            except Exception as e:
                logger.debug("on_cell_edit callback error: %s", e)

        self._view.focus_set()
        self._view.request_redraw()

    # -------------------------------------------------------------
    # CONTEXT MENUS
    # -------------------------------------------------------------
    def _show_header_context_menu(self, x_root: int, y_root: int, col_idx: Optional[int]) -> None:
        """Display right-click context menu on column header."""
        pal = get_theme()
        menu = tk.Menu(self, tearoff=0, bg=to_tk_hex(pal.card_bg), fg=to_tk_hex(pal.fg), activebackground=to_tk_hex(pal.primary), activeforeground="#ffffff")

        if col_idx is not None and 0 <= col_idx < len(self._columns):
            col = self._columns[col_idx]
            col_id = col.get("id", str(col_idx))
            menu.add_command(label=f"Auto-fit '{col.get('title', col_id)}'", command=lambda: self.auto_fit_column(col_idx))

        menu.add_command(label="Auto-fit All Columns", command=self.auto_fit_all_columns)
        menu.add_separator()

        if col_idx is not None and 0 <= col_idx < len(self._columns):
            col = self._columns[col_idx]
            col_id = col.get("id", str(col_idx))
            menu.add_command(label="Hide Column", command=lambda: self.hide_column(col_id))

        # Hidden columns submenu
        hidden_cols = [c for c in self._columns if c.get("visible", True) is False]
        if hidden_cols:
            unhide_menu = tk.Menu(menu, tearoff=0, bg=to_tk_hex(pal.card_bg), fg=to_tk_hex(pal.fg), activebackground=to_tk_hex(pal.primary), activeforeground="#ffffff")
            for hc in hidden_cols:
                hc_id = hc.get("id", "")
                unhide_menu.add_command(label=hc.get("title", hc_id), command=lambda cid=hc_id: self.show_column(cid))
            menu.add_cascade(label="Unhide Column", menu=unhide_menu)

        menu.add_separator()
        menu.add_command(label="Reset Sorting", command=self.reset_sorting)

        if self._on_context_menu:
            try:
                col_id_str = self._columns[col_idx].get("id") if col_idx is not None and 0 <= col_idx < len(self._columns) else None
                self._on_context_menu(None, col_id_str, menu)
            except Exception as e:
                logger.debug("on_context_menu header hook error: %s", e)

        menu.tk_popup(x_root, y_root)

    def _show_body_context_menu(self, x_root: int, y_root: int, raw_row_idx: Optional[int], col_idx: Optional[int]) -> None:
        """Display right-click context menu on table body."""
        pal = get_theme()
        menu = tk.Menu(self, tearoff=0, bg=to_tk_hex(pal.card_bg), fg=to_tk_hex(pal.fg), activebackground=to_tk_hex(pal.primary), activeforeground="#ffffff")

        menu.add_command(label="Copy (TSV)", command=lambda: self.copy_to_clipboard(fmt="tsv"))
        menu.add_command(label="Copy (CSV)", command=lambda: self.copy_to_clipboard(fmt="csv"))
        menu.add_separator()
        menu.add_command(label="Select All", command=self.select_all)
        menu.add_command(label="Clear Selection", command=self.clear_selection)

        if self._on_context_menu:
            try:
                col_id_str = self._columns[col_idx].get("id") if col_idx is not None and 0 <= col_idx < len(self._columns) else None
                self._on_context_menu(raw_row_idx, col_id_str, menu)
            except Exception as e:
                logger.debug("on_context_menu body hook error: %s", e)

        menu.tk_popup(x_root, y_root)

    # -------------------------------------------------------------
    # EXPORT & CLIPBOARD
    # -------------------------------------------------------------
    def export_csv(self, selected_only: bool = False, delimiter: str = ",") -> str:
        """Export table contents as CSV formatted text (RFC 4180)."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter, lineterminator="\n")

        vis_cols = self._get_visible_columns()
        headers = [c.get("title", c.get("id", "")) for c in vis_cols]
        writer.writerow(headers)

        if selected_only and self._select_unit == "cell" and self._selected_cells:
            # Rectangular cell export
            sel_rows = sorted(list({r for r, c in self._selected_cells if r < len(self._data)}))
            for r_idx in sel_rows:
                row_item = self._data[r_idx]
                row_vals = []
                for c in vis_cols:
                    raw_c_idx = self._columns.index(c)
                    if (r_idx, raw_c_idx) in self._selected_cells:
                        cid = c.get("id", str(raw_c_idx))
                        v = self.get_cell_value(r_idx, cid)
                    else:
                        v = ""
                    row_vals.append(str(v))
                writer.writerow(row_vals)
        else:
            rows_to_export = self.get_selected_rows() if selected_only and self._selected_rows else self.get_filtered_data()
            for r in rows_to_export:
                row_vals = []
                for c in vis_cols:
                    cid = c.get("id")
                    if isinstance(r, dict):
                        v = str(r.get(cid, r.get(c.get("name", ""), "")))
                    elif isinstance(r, (list, tuple)):
                        raw_c = self._columns.index(c)
                        v = str(r[raw_c]) if raw_c < len(r) else ""
                    else:
                        v = ""
                    row_vals.append(v)
                writer.writerow(row_vals)

        return output.getvalue()

    def export_tsv(self, selected_only: bool = False) -> str:
        """Export table contents as TSV formatted text."""
        return self.export_csv(selected_only=selected_only, delimiter="\t")

    def copy_to_clipboard(self, fmt: str = "tsv") -> None:
        """Copy selected rows/cells (or table if none selected) to clipboard."""
        is_sel = bool(self._selected_cells) if self._select_unit == "cell" else bool(self._selected_rows)
        exported = self.export_csv(selected_only=is_sel) if fmt == "csv" else self.export_tsv(selected_only=is_sel)
        self.clipboard_clear()
        self.clipboard_append(exported)

    # -------------------------------------------------------------
    # SCROLLING ENGINE & GEOMETRY
    # -------------------------------------------------------------
    def _get_col_x_and_width(self, col_idx: int) -> Tuple[float, float]:
        """Return (x, width) for column in view surface coordinate space."""
        s = self._scale
        vis_cols = self._get_visible_columns()
        pinned_n = min(self._pinned_columns, len(vis_cols))
        pinned_w = sum(c.get("width", 100) * s for c in vis_cols[:pinned_n])

        if col_idx < len(self._columns):
            target_col = self._columns[col_idx]
            # Check if in pinned
            if target_col in vis_cols[:pinned_n]:
                cx = 0.0
                for c in vis_cols[:pinned_n]:
                    cw = c.get("width", 100) * s
                    if c is target_col:
                        return (cx, cw)
                    cx += cw
            elif target_col in vis_cols[pinned_n:]:
                cx = pinned_w - self._scroll_x
                for c in vis_cols[pinned_n:]:
                    cw = c.get("width", 100) * s
                    if c is target_col:
                        return (cx, cw)
                    cx += cw

        return (0.0, 100.0 * s)

    def _get_col_at_x(self, x: float) -> Optional[int]:
        s = self._scale
        vis_cols = self._get_visible_columns()
        pinned_n = min(self._pinned_columns, len(vis_cols))
        pinned_w = sum(c.get("width", 100) * s for c in vis_cols[:pinned_n])

        if x < pinned_w:
            curr_x = 0.0
            for col in vis_cols[:pinned_n]:
                cw = col.get("width", 100) * s
                if curr_x <= x <= curr_x + cw:
                    return self._columns.index(col)
                curr_x += cw
        else:
            curr_x = pinned_w - self._scroll_x
            for col in vis_cols[pinned_n:]:
                cw = col.get("width", 100) * s
                if curr_x <= x <= curr_x + cw:
                    return self._columns.index(col)
                curr_x += cw

        return None

    def _get_total_content_width(self) -> float:
        s = self._scale
        vis_cols = self._get_visible_columns()
        return sum(c.get("width", 100) * s for c in vis_cols)

    def _get_total_content_height(self) -> float:
        s = self._scale
        visible_rows = self._get_visible_data()
        return len(visible_rows) * self._row_height * s

    def _update_scroll_geometry(self) -> None:
        s = self._scale
        vw = max(1.0, float(self._view.winfo_width() or (300 * s)))
        vh = max(1.0, float(self._view.winfo_height() or (200 * s)) - self._header_height * s)

        vis_cols = self._get_visible_columns()
        pinned_n = min(self._pinned_columns, len(vis_cols))
        pinned_w = sum(c.get("width", 100) * s for c in vis_cols[:pinned_n])
        unpinned_w = sum(c.get("width", 100) * s for c in vis_cols[pinned_n:])

        th = self._get_total_content_height()

        # Update VScrollbar fractions
        if th <= vh:
            self._scroll_y = 0.0
            self._v_scrollbar.set_fraction(0.0, 1.0)
        else:
            max_sy = th - vh
            self._scroll_y = max(0.0, min(max_sy, self._scroll_y))
            top_frac = self._scroll_y / th
            bottom_frac = (self._scroll_y + vh) / th
            self._v_scrollbar.set_fraction(top_frac, bottom_frac)

        # Update HScrollbar fractions for unpinned scrollable area
        scrollable_vw = max(1.0, vw - pinned_w)
        if unpinned_w <= scrollable_vw:
            self._scroll_x = 0.0
            self._h_scrollbar.set_fraction(0.0, 1.0)
        else:
            max_sx = unpinned_w - scrollable_vw
            self._scroll_x = max(0.0, min(max_sx, self._scroll_x))
            left_frac = self._scroll_x / unpinned_w
            right_frac = (self._scroll_x + scrollable_vw) / unpinned_w
            self._h_scrollbar.set_fraction(left_frac, right_frac)

    def _on_vscroll(self, *args) -> None:
        if not args:
            return
        if len(args) > 1 and args[0] == "moveto":
            fraction = float(args[1])
        else:
            try:
                fraction = float(args[0])
            except (ValueError, TypeError):
                return
        s = self._scale
        vh = max(1.0, float(self._view.winfo_height() or (200 * s)) - self._header_height * s)
        th = self._get_total_content_height()
        if th > vh:
            self._scroll_y = max(0.0, min(th - vh, fraction * th))
            self._update_scroll_geometry()
            self._view.request_redraw()

    def _on_hscroll(self, *args) -> None:
        if not args:
            return
        if len(args) > 1 and args[0] == "moveto":
            fraction = float(args[1])
        else:
            try:
                fraction = float(args[0])
            except (ValueError, TypeError):
                return
        s = self._scale
        vw = max(1.0, float(self._view.winfo_width() or (300 * s)))
        vis_cols = self._get_visible_columns()
        pinned_n = min(self._pinned_columns, len(vis_cols))
        pinned_w = sum(c.get("width", 100) * s for c in vis_cols[:pinned_n])
        unpinned_w = sum(c.get("width", 100) * s for c in vis_cols[pinned_n:])
        scrollable_vw = max(1.0, vw - pinned_w)

        if unpinned_w > scrollable_vw:
            self._scroll_x = max(0.0, min(unpinned_w - scrollable_vw, fraction * unpinned_w))
            self._update_scroll_geometry()
            self._view.request_redraw()

    def _on_mousewheel(self, event) -> None:
        s = self._scale
        delta = -1.0 * (event.delta / 120.0) if event.delta else 0.0
        step = self._row_height * s * 2.0 * delta
        self._scroll_y += step
        self._update_scroll_geometry()
        self._view.request_redraw()

    def _on_shift_mousewheel(self, event) -> None:
        s = self._scale
        delta = -1.0 * (event.delta / 120.0) if event.delta else 0.0
        step = 40.0 * s * delta
        self._scroll_x += step
        self._update_scroll_geometry()
        self._view.request_redraw()

    def _on_mousewheel_linux(self, event) -> None:
        s = self._scale
        delta = -1.0 if event.num == 4 else 1.0
        step = self._row_height * s * 2.0 * delta
        self._scroll_y += step
        self._update_scroll_geometry()
        self._view.request_redraw()

    def _on_view_resize(self, event) -> None:
        self._update_scroll_geometry()
        self._view.request_redraw()

    # -------------------------------------------------------------
    # KEYBOARD NAVIGATION
    # -------------------------------------------------------------
    def _on_key_up(self, event) -> None:
        if self._focused_row is None:
            self.select_row(0)
        elif self._focused_row > 0:
            new_foc = self._focused_row - 1
            raw_idx = self._get_raw_index(new_foc)
            if self._select_unit == "cell":
                self.select_cell(raw_idx, self._focused_col or 0)
            else:
                self.select_row(raw_idx)

    def _on_key_down(self, event) -> None:
        visible_data = self._get_visible_data()
        if self._focused_row is None:
            self.select_row(0)
        elif self._focused_row < len(visible_data) - 1:
            new_foc = self._focused_row + 1
            raw_idx = self._get_raw_index(new_foc)
            if self._select_unit == "cell":
                self.select_cell(raw_idx, self._focused_col or 0)
            else:
                self.select_row(raw_idx)

    def _on_key_left(self, event) -> None:
        if self._focused_col is not None and self._focused_col > 0:
            self._focused_col -= 1
            if self._select_unit == "cell" and self._focused_row is not None:
                raw_idx = self._get_raw_index(self._focused_row)
                self.select_cell(raw_idx, self._focused_col)
            self._view.request_redraw()
        else:
            self._scroll_x = max(0.0, self._scroll_x - 30.0 * self._scale)
            self._update_scroll_geometry()
            self._view.request_redraw()

    def _on_key_right(self, event) -> None:
        if self._focused_col is not None and self._focused_col < len(self._columns) - 1:
            self._focused_col += 1
            if self._select_unit == "cell" and self._focused_row is not None:
                raw_idx = self._get_raw_index(self._focused_row)
                self.select_cell(raw_idx, self._focused_col)
            self._view.request_redraw()
        else:
            self._scroll_x += 30.0 * self._scale
            self._update_scroll_geometry()
            self._view.request_redraw()

    def _on_key_shift_up(self, event) -> None:
        if self._select_mode == "extended" and self._focused_row is not None and self._focused_row > 0:
            self._focused_row -= 1
            raw_idx = self._get_raw_index(self._focused_row)
            if self._anchor_row is None:
                self._anchor_row = raw_idx
            if self._select_unit == "cell":
                min_r, max_r = min(self._anchor_row, raw_idx), max(self._anchor_row, raw_idx)
                col = self._focused_col or 0
                anc_c = self._anchor_col if self._anchor_col is not None else col
                min_c, max_c = min(anc_c, col), max(anc_c, col)
                self._selected_cells = {(r, c) for r in range(min_r, max_r + 1) for c in range(min_c, max_c + 1)}
            else:
                start_i = min(self._anchor_row, raw_idx)
                end_i = max(self._anchor_row, raw_idx)
                self._selected_rows = set(range(start_i, end_i + 1))
            self._view.request_redraw()

    def _on_key_shift_down(self, event) -> None:
        visible_data = self._get_visible_data()
        if self._select_mode == "extended" and self._focused_row is not None and self._focused_row < len(visible_data) - 1:
            self._focused_row += 1
            raw_idx = self._get_raw_index(self._focused_row)
            if self._anchor_row is None:
                self._anchor_row = raw_idx
            if self._select_unit == "cell":
                min_r, max_r = min(self._anchor_row, raw_idx), max(self._anchor_row, raw_idx)
                col = self._focused_col or 0
                anc_c = self._anchor_col if self._anchor_col is not None else col
                min_c, max_c = min(anc_c, col), max(anc_c, col)
                self._selected_cells = {(r, c) for r in range(min_r, max_r + 1) for c in range(min_c, max_c + 1)}
            else:
                start_i = min(self._anchor_row, raw_idx)
                end_i = max(self._anchor_row, raw_idx)
                self._selected_rows = set(range(start_i, end_i + 1))
            self._view.request_redraw()

    def _on_key_shift_left(self, event) -> None:
        if self._select_unit == "cell" and self._focused_col is not None and self._focused_col > 0:
            self._focused_col -= 1
            if self._focused_row is not None:
                raw_idx = self._get_raw_index(self._focused_row)
                if self._anchor_row is None:
                    self._anchor_row = raw_idx
                if self._anchor_col is None:
                    self._anchor_col = self._focused_col + 1
                min_r, max_r = min(self._anchor_row, raw_idx), max(self._anchor_row, raw_idx)
                min_c, max_c = min(self._anchor_col, self._focused_col), max(self._anchor_col, self._focused_col)
                self._selected_cells = {(r, c) for r in range(min_r, max_r + 1) for c in range(min_c, max_c + 1)}
                self._view.request_redraw()

    def _on_key_shift_right(self, event) -> None:
        if self._select_unit == "cell" and self._focused_col is not None and self._focused_col < len(self._columns) - 1:
            self._focused_col += 1
            if self._focused_row is not None:
                raw_idx = self._get_raw_index(self._focused_row)
                if self._anchor_row is None:
                    self._anchor_row = raw_idx
                if self._anchor_col is None:
                    self._anchor_col = self._focused_col - 1
                min_r, max_r = min(self._anchor_row, raw_idx), max(self._anchor_row, raw_idx)
                min_c, max_c = min(self._anchor_col, self._focused_col), max(self._anchor_col, self._focused_col)
                self._selected_cells = {(r, c) for r in range(min_r, max_r + 1) for c in range(min_c, max_c + 1)}
                self._view.request_redraw()

    def _on_key_page_up(self, event) -> None:
        if self._pagination:
            self.prev_page()
        else:
            s = self._scale
            vh = max(1.0, float(self._view.winfo_height() or (200 * s)) - self._header_height * s)
            self._scroll_y = max(0.0, self._scroll_y - vh)
            self._update_scroll_geometry()
            self._view.request_redraw()

    def _on_key_page_down(self, event) -> None:
        if self._pagination:
            self.next_page()
        else:
            s = self._scale
            vh = max(1.0, float(self._view.winfo_height() or (200 * s)) - self._header_height * s)
            self._scroll_y += vh
            self._update_scroll_geometry()
            self._view.request_redraw()

    def _on_key_home(self, event) -> None:
        self.select_row(0)
        self._scroll_y = 0.0
        self._update_scroll_geometry()
        self._view.request_redraw()

    def _on_key_end(self, event) -> None:
        if self._data:
            self.select_row(len(self._data) - 1)
            self._update_scroll_geometry()
            self._view.request_redraw()

    def _on_key_return(self, event) -> None:
        if self._focused_row is not None and 0 <= self._focused_row < len(self._get_visible_data()):
            raw_idx = self._get_raw_index(self._focused_row)
            target_col_idx = self._focused_col if self._focused_col is not None else 0
            # If current column is editable, edit it; else find first editable column
            if not self._columns[target_col_idx].get("editable", False):
                for i, c in enumerate(self._columns):
                    if c.get("editable", False):
                        target_col_idx = i
                        break
            if self._columns[target_col_idx].get("editable", False):
                self._start_cell_edit(raw_idx, target_col_idx, self._focused_row)

    def _on_key_select_all(self, event) -> str:
        self.select_all()
        return "break"

    def _on_key_copy(self, event) -> str:
        self.copy_to_clipboard()
        return "break"

    # -------------------------------------------------------------
    # THEME SYNCHRONIZATION
    # -------------------------------------------------------------
    def _on_theme_changed(self, pal: Palette) -> None:
        resolved_inner = self.inner_bg
        try:
            self.configure(background=to_tk_hex(resolved_inner))
        except Exception:
            pass
        self._view.set_outer_bg(resolved_inner, render=False)
        self._v_scrollbar.set_outer_bg(resolved_inner, render=False)
        self._h_scrollbar.set_outer_bg(resolved_inner, render=False)
        if self._page_frame:
            try:
                self._page_frame.configure(background=to_tk_hex(resolved_inner))
                if self._page_label:
                    self._page_label.configure(background=to_tk_hex(resolved_inner), foreground=to_tk_hex(pal.fg))
                if self._btn_prev:
                    self._btn_prev.configure(bg=to_tk_hex(pal.secondary), fg=to_tk_hex(pal.fg), activebackground=to_tk_hex(pal.primary))
                if self._btn_next:
                    self._btn_next.configure(bg=to_tk_hex(pal.secondary), fg=to_tk_hex(pal.fg), activebackground=to_tk_hex(pal.primary))
            except Exception:
                pass
        self._view.request_redraw()

    def set_outer_bg(self, bg_color: str, render: bool = True, explicit: bool = True) -> None:
        """Update outer parent background color."""
        self._parent_bg = bg_color
        if explicit:
            self._explicit_outer_bg = bg_color
            self._explicit_parent_bg = bg_color

    def set_parent_bg(self, bg_color: str, render: bool = True, explicit: bool = True) -> None:
        """Deprecated alias for set_outer_bg."""
        self.set_outer_bg(bg_color, render=render, explicit=explicit)

    def set_inner_bg(self, bg_color: str, render: bool = True, explicit: bool = True) -> None:
        """Update inner table background color."""
        self._bg_color = bg_color
        if explicit:
            self._explicit_inner_bg = bg_color
        resolved_inner = self.inner_bg
        try:
            self.configure(background=to_tk_hex(resolved_inner))
        except Exception:
            pass
        self._view.set_outer_bg(resolved_inner, render=render)
        self._v_scrollbar.set_outer_bg(resolved_inner, render=render)
        self._h_scrollbar.set_outer_bg(resolved_inner, render=render)

    def set_bg_color(self, bg_color: str, render: bool = True, explicit: bool = True) -> None:
        """Alias for set_inner_bg."""
        self.set_inner_bg(bg_color, render=render, explicit=explicit)

    def _on_destroy(self, event) -> None:
        remove_theme_listener(self._on_theme_changed)
