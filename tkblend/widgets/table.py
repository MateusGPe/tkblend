from __future__ import annotations

import sys
import tkinter as tk
from typing import Optional, Callable, Sequence, List, Any, Dict, Tuple, Union, Set
from tkblend.widgets.base import BaseControl
from tkblend.theme import Palette, to_tk_hex, get_theme
from tkblend.surface import Surface


class _TableCellDropdownPopup(tk.Toplevel):
    """Floating Material Design 3 vector styled dropdown list for Table cell editing."""

    def __init__(
        self,
        table: Table,
        cell_x: int,
        cell_y: int,
        cell_w: int,
        cell_h: int,
        values: Sequence[str],
        current_value: str,
        on_select: Callable[[str], None],
        on_dismiss: Optional[Callable[[], None]] = None,
    ):
        super().__init__(table)
        self._table = table
        self._on_select = on_select
        self._on_dismiss = on_dismiss
        self._values = list(values)
        self._current_value = current_value
        self._selected = False

        self.overrideredirect(True)
        self.attributes("-topmost", True)

        pal = table._palette
        bg_hex = to_tk_hex(getattr(pal, "card_bg", "#25232a"))
        border_hex = to_tk_hex(getattr(pal, "card_border", "#49454f"))
        fg_hex = to_tk_hex(getattr(pal, "fg", "#e6e0e9"))
        primary_hex = to_tk_hex(getattr(pal, "primary", "#8b5cf6"))
        hover_hex = to_tk_hex(getattr(pal, "surface", "#2f2d38"))

        self.configure(bg=border_hex, padx=1, pady=1)

        container = tk.Frame(self, bg=bg_hex)
        container.pack(fill="both", expand=True)

        for val in self._values:
            is_active = (val == current_value)
            item_fg = primary_hex if is_active else fg_hex
            item_font = ("sans-serif", 10, "bold" if is_active else "normal")
            lbl = tk.Label(
                container,
                text=str(val),
                bg=bg_hex,
                fg=item_fg,
                font=item_font,
                anchor="w",
                padx=10,
                pady=6,
                cursor="hand2",
            )
            lbl.pack(fill="x")

            def _make_callbacks(v: str, label_widget: tk.Label):
                def _on_enter(e):
                    label_widget.configure(bg=hover_hex)

                def _on_leave(e):
                    label_widget.configure(bg=bg_hex)

                def _on_click(e):
                    self._selected = True
                    self.dismiss()
                    self._on_select(v)

                label_widget.bind("<Enter>", _on_enter)
                label_widget.bind("<Leave>", _on_leave)
                label_widget.bind("<Button-1>", _on_click)

            _make_callbacks(val, lbl)

        # Position below the cell
        self.update_idletasks()
        rx = table.winfo_rootx() + cell_x
        ry = table.winfo_rooty() + cell_y + cell_h + 1
        rw = max(cell_w, self.winfo_reqwidth(), 100)
        rh = self.winfo_reqheight()
        self.geometry(f"{rw}x{rh}+{rx}+{ry}")

        self.bind("<Escape>", lambda e: self.dismiss())
        self.bind("<FocusOut>", lambda e: self.dismiss())
        self.focus_set()

    def dismiss(self) -> None:
        try:
            self.destroy()
        except Exception:
            pass
        if not self._selected and callable(self._on_dismiss):
            try:
                self._on_dismiss()
            except Exception:
                pass


class Table(BaseControl):
    """
    High-performance pure Blend2D Material Design 3 vector data table.
    Features:
      - Pure Blend2D surface rendering (zero TTK, zero Canvas, zero child widget overhead)
      - Interactive drag-to-resize column dividers
      - Click-to-sort columns with vector sort indicators (▲ / ▼)
      - Responsive proportional auto-fit column layout
      - Virtualized row rendering for large datasets
      - Configurable Single-select and Multi-select modes (Ctrl / Shift + Click)
      - Integrated anti-aliased vector scrollbars with capsule thumbs
      - Alternating zebra striping, hover effects, and theme reactivity
    """

    WIDGET_CLASS = "table"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        columns: Optional[Sequence[str]] = None,
        data: Optional[Sequence[Sequence[Any]]] = None,
        command: Optional[Callable[..., Any]] = None,
        column_widths: Optional[Sequence[Union[int, float]]] = None,
        width: int = 480,
        height: int = 240,
        row_height: int = 34,
        header_height: int = 38,
        scrollbar_width: int = 7,
        corner_radius: float = 8.0,
        zebra_striping: bool = True,
        multi_select: bool = False,
        editable_columns: Optional[Sequence[Union[int, str]]] = None,
        column_editors: Optional[Dict[Union[int, str], Any]] = None,
        on_cell_edit: Optional[Callable[[int, int, Any, Any], Optional[bool]]] = None,
        **kwargs,
    ):
        self._columns: List[str] = list(columns) if columns else ["Column 1", "Column 2", "Column 3"]
        self._data: List[List[Any]] = [list(r) for r in data] if data else []
        self._column_weights = list(column_widths) if column_widths else None
        self._col_widths: List[int] = []
        self._user_resized_cols: bool = False
        self._last_calc_w: int = 0

        self._row_h: int = int(row_height)
        self._header_h: int = int(header_height)
        self._scrollbar_w: int = int(scrollbar_width)
        self._corner_radius: float = float(corner_radius)
        self._zebra_striping: bool = bool(zebra_striping)
        self._multi_select: bool = bool(multi_select)

        # In-place cell editing configuration and state
        self._editable_columns: Optional[List[Union[int, str]]] = (
            list(editable_columns) if editable_columns is not None else None
        )
        self._column_editors: Dict[Union[int, str], Any] = dict(column_editors) if column_editors else {}
        self._on_cell_edit = on_cell_edit
        self._active_editor: Optional[tk.Widget] = None
        self._active_editor_widget: Optional[tk.Widget] = None
        self._editing_cell: Optional[Tuple[int, int]] = None

        self._selected_rows: Set[int] = set()
        self._last_clicked_row: Optional[int] = None
        self._hovered_row: Optional[int] = None
        self._sort_col: Optional[int] = None
        self._sort_asc: bool = True
        self._command = command

        # Scroll positions (in pixels)
        self._scroll_y: float = 0.0
        self._scroll_x: float = 0.0

        # Scrollbar interaction states
        self._vbar_dragging: bool = False
        self._vbar_drag_y: int = 0
        self._vbar_drag_start_scroll: float = 0.0
        self._vbar_hovered: bool = False

        self._hbar_dragging: bool = False
        self._hbar_drag_x: int = 0
        self._hbar_drag_start_scroll: float = 0.0
        self._hbar_hovered: bool = False

        # Column resize drag state
        self._hovered_divider_idx: Optional[int] = None
        self._resizing_col_idx: Optional[int] = None
        self._resize_start_x: int = 0
        self._resize_start_w: int = 0

        # Initialize BaseControl without command so BaseControl's button-click
        # handler does not intercept Table's row selection callback.
        super().__init__(
            master=master,
            widget_class="",
            width=width,
            height=height,
            command=None,
            cursor="hand2",
            **kwargs,
        )

        self._command = command

        # Ensure C++ controller does not intercept with static batch, auto-press, or button clicks
        self.controller.widget_class = ""
        self._widget_class = ""
        self.controller.auto_press = False
        self.controller.clear_on_click()
        self.clear_batch()
        self.controller.set_on_paint(self._render_table)

        # Mouse and keyboard event bindings on the vector widget frame
        self.bind("<Motion>", self._on_motion, add="+")
        self.bind("<Button-1>", self._on_button_press, add="+")
        self.bind("<Double-Button-1>", self._on_double_click, add="+")
        self.bind("<Return>", self._on_key_edit, add="+")
        self.bind("<F2>", self._on_key_edit, add="+")
        self.bind("<B1-Motion>", self._on_drag, add="+")
        self.bind("<ButtonRelease-1>", self._on_button_release, add="+")
        self.bind("<Leave>", self._on_leave, add="+")
        self.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.bind("<Button-4>", self._on_mousewheel, add="+")
        self.bind("<Button-5>", self._on_mousewheel, add="+")
        self.bind("<Shift-MouseWheel>", self._on_shift_mousewheel, add="+")
        self.bind("<Configure>", self._on_configure, add="+")

    @property
    def inner_bg(self) -> str:
        """Expose inner card background for child container cascades."""
        return getattr(self._palette, "card_bg", "#25232a")

    @property
    def bg_color(self) -> str:
        """Alias for container background protocols."""
        return self.inner_bg

    def _calc_column_widths_for(self, available_w: int) -> None:
        col_count = max(1, len(self._columns))

        if self._column_weights and len(self._column_weights) == col_count:
            total_w = sum(self._column_weights)
            if total_w > 0:
                widths = [max(50, int(available_w * (w / total_w))) for w in self._column_weights]
                diff = available_w - sum(widths)
                if diff != 0:
                    widths[-1] = max(50, widths[-1] + diff)
                self._col_widths = widths
                return

        # Content-based weights with comfortable min-widths
        max_lens = [max(len(str(c)), 6) for c in self._columns]
        for row in self._data:
            for i, cell in enumerate(row[:col_count]):
                max_lens[i] = max(max_lens[i], min(len(str(cell)), 32))

        # Base minimum comfortable width per column
        base_mins = [max(60, int(l * 7.5) + 24) for l in max_lens]
        sum_mins = sum(base_mins)

        if available_w >= sum_mins:
            # Distribute remaining width proportionally
            extra = available_w - sum_mins
            widths = [base_mins[i] + int(extra * (base_mins[i] / sum_mins)) for i in range(col_count)]
            diff = available_w - sum(widths)
            if diff != 0:
                widths[-1] += diff
        else:
            # Scale down proportionally to fill available_w
            scale = available_w / max(1, sum_mins)
            widths = [max(45, int(bm * scale)) for bm in base_mins]
            diff = available_w - sum(widths)
            if diff != 0:
                widths[-1] += diff

        self._col_widths = widths

    def _find_column_divider(self, x: int) -> Optional[int]:
        """Check if x is within resize tolerance of any column separator."""
        curr_x = -self._scroll_x
        for i in range(len(self._col_widths) - 1):
            curr_x += self._col_widths[i]
            if abs(x - curr_x) <= 6:
                return i
        return None

    def _get_vbar_bounds(self, w: int, h: int) -> Tuple[bool, float, float, float, float, float]:
        total_content_h = len(self._data) * self._row_h
        viewport_h = h - self._header_h - 2
        v_needed = total_content_h > viewport_h
        if not v_needed or viewport_h <= 0 or total_content_h <= 0:
            return False, 0.0, 0.0, 0.0, 0.0, 0.0

        track_h = max(10.0, float(viewport_h - 8))
        thumb_h = max(24.0, float(viewport_h * (viewport_h / total_content_h)))
        max_scroll = max(1.0, float(total_content_h - viewport_h))
        progress = max(0.0, min(1.0, self._scroll_y / max_scroll))
        thumb_y = self._header_h + 4.0 + progress * (track_h - thumb_h)
        thumb_x = w - self._scrollbar_w - 4.0
        return True, thumb_x, thumb_y, float(self._scrollbar_w), thumb_h, track_h

    def _get_hbar_bounds(self, w: int, h: int) -> Tuple[bool, float, float, float, float, float]:
        total_content_w = sum(self._col_widths) if self._col_widths else w
        viewport_w = w - (self._scrollbar_w + 6)
        h_needed = self._user_resized_cols and (total_content_w > (viewport_w + 4))
        if not h_needed or viewport_w <= 0 or total_content_w <= 0:
            return False, 0.0, 0.0, 0.0, 0.0, 0.0

        track_w = max(10.0, float(viewport_w - 8))
        thumb_w = max(24.0, float(viewport_w * (viewport_w / total_content_w)))
        max_scroll = max(1.0, float(total_content_w - viewport_w))
        progress = max(0.0, min(1.0, self._scroll_x / max_scroll))
        thumb_x = 4.0 + progress * (track_w - thumb_w)
        thumb_y = h - self._scrollbar_w - 4.0
        return True, thumb_x, thumb_y, thumb_w, float(self._scrollbar_w), track_w

    def _on_motion(self, event: tk.Event) -> None:
        if self._resizing_col_idx is not None or self._vbar_dragging or self._hbar_dragging:
            return

        w = self.winfo_width()
        h = self.winfo_height()

        # Check scrollbar hover
        v_needed, vx, vy, vw, vh, _ = self._get_vbar_bounds(w, h)
        if v_needed and (event.x >= w - self._scrollbar_w - 8) and (event.y >= self._header_h):
            if not self._vbar_hovered:
                self._vbar_hovered = True
                self.request_redraw()
            return
        elif self._vbar_hovered:
            self._vbar_hovered = False
            self.request_redraw()

        if event.y <= self._header_h:
            # Inside header: check for column divider hover
            divider_idx = self._find_column_divider(event.x)
            if divider_idx is not None:
                self.configure(cursor="sb_h_double_arrow")
                self._hovered_divider_idx = divider_idx
            else:
                self.configure(cursor="hand2")
                self._hovered_divider_idx = None

            if self._hovered_row is not None:
                self._hovered_row = None
                self.request_redraw()
        else:
            # Inside body: row hover
            if self._hovered_divider_idx is not None:
                self.configure(cursor="hand2")
                self._hovered_divider_idx = None

            row_idx = int((event.y - self._header_h + self._scroll_y) // self._row_h)
            if 0 <= row_idx < len(self._data):
                if self._hovered_row != row_idx:
                    self._hovered_row = row_idx
                    self.request_redraw()
            elif self._hovered_row is not None:
                self._hovered_row = None
                self.request_redraw()

    def _on_button_press(self, event: tk.Event) -> None:
        if self._active_editor:
            self._commit_cell_edit()

        w = self.winfo_width()
        h = self.winfo_height()

        # Check vertical scrollbar interaction
        v_needed, vx, vy, vw, vh, track_h = self._get_vbar_bounds(w, h)
        if v_needed and event.x >= w - self._scrollbar_w - 8 and event.y >= self._header_h:
            total_content_h = len(self._data) * self._row_h
            viewport_h = h - self._header_h - 2
            max_scroll = max(1.0, float(total_content_h - viewport_h))

            if vy <= event.y <= vy + vh:
                # Dragging thumb
                self._vbar_dragging = True
                self._vbar_drag_y = event.y
                self._vbar_drag_start_scroll = self._scroll_y
            else:
                # Jump click on track
                click_ratio = max(0.0, min(1.0, (event.y - self._header_h - 4) / max(1.0, track_h)))
                self._scroll_y = max(0.0, min(max_scroll, click_ratio * max_scroll))
                self.request_redraw()
            return

        # Check header interaction
        if event.y <= self._header_h:
            divider_idx = self._find_column_divider(event.x)
            if divider_idx is not None:
                # Begin dragging column divider
                self._resizing_col_idx = divider_idx
                self._resize_start_x = event.x
                self._resize_start_w = self._col_widths[divider_idx]
                return

            # Header column click: Sort
            curr_x = -self._scroll_x
            for col_idx, col_w in enumerate(self._col_widths):
                if curr_x <= event.x < curr_x + col_w:
                    self._sort_by_column(col_idx)
                    break
                curr_x += col_w
        else:
            # Body row click
            row_idx = int((event.y - self._header_h + self._scroll_y) // self._row_h)
            if 0 <= row_idx < len(self._data):
                is_ctrl = bool(event.state & 0x0004 or event.state & 0x0008)
                is_shift = bool(event.state & 0x0001)

                if self._multi_select:
                    if is_ctrl:
                        if row_idx in self._selected_rows:
                            self._selected_rows.remove(row_idx)
                        else:
                            self._selected_rows.add(row_idx)
                    elif is_shift and self._last_clicked_row is not None:
                        start_idx = min(self._last_clicked_row, row_idx)
                        end_idx = max(self._last_clicked_row, row_idx)
                        self._selected_rows = set(range(start_idx, end_idx + 1))
                    else:
                        self._selected_rows = {row_idx}
                else:
                    self._selected_rows = {row_idx}

                self._last_clicked_row = row_idx
                self.request_redraw()

                if callable(self._command):
                    try:
                        if self._multi_select:
                            sel_indices = sorted(self._selected_rows)
                            sel_records = [self._data[i] for i in sel_indices]
                            self._command(sel_indices, sel_records)
                        else:
                            self._command(row_idx, self._data[row_idx])
                    except Exception:
                        pass

    def _on_drag(self, event: tk.Event) -> None:
        if self._vbar_dragging:
            w = self.winfo_width()
            h = self.winfo_height()
            _, _, _, _, vh, track_h = self._get_vbar_bounds(w, h)
            total_content_h = len(self._data) * self._row_h
            viewport_h = h - self._header_h - 2
            max_scroll = max(1.0, float(total_content_h - viewport_h))
            available_track = max(1.0, track_h - vh)

            delta_y = event.y - self._vbar_drag_y
            scroll_delta = delta_y * (max_scroll / available_track)
            self._scroll_y = max(0.0, min(max_scroll, self._vbar_drag_start_scroll + scroll_delta))
            self.request_redraw()
            return

        if self._resizing_col_idx is not None:
            delta = event.x - self._resize_start_x
            new_w = max(40, self._resize_start_w + delta)
            self._col_widths[self._resizing_col_idx] = new_w
            self._user_resized_cols = True
            self.request_redraw()

    def _on_button_release(self, event: tk.Event) -> None:
        if self._vbar_dragging:
            self._vbar_dragging = False
        if self._resizing_col_idx is not None:
            self._resizing_col_idx = None
            self.request_redraw()

    def _on_leave(self, event: tk.Event) -> None:
        if self._hovered_row is not None or self._hovered_divider_idx is not None or self._vbar_hovered:
            self._hovered_row = None
            self._hovered_divider_idx = None
            self._vbar_hovered = False
            self.request_redraw()

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self._active_editor:
            self._commit_cell_edit()

        if sys.platform == "darwin":
            delta = -1 * event.delta
        elif event.num == 5:
            delta = 1
        elif event.num == 4:
            delta = -1
        else:
            delta = -1 * int(event.delta / 120)

        # Check if Shift is held down -> horizontal scroll
        if event.state & 0x0001:
            total_content_w = sum(self._col_widths)
            viewport_w = self.winfo_width() - (self._scrollbar_w + 6)
            max_scroll_x = max(0.0, float(total_content_w - viewport_w))
            self._scroll_x = max(0.0, min(max_scroll_x, self._scroll_x + delta * 24.0))
        else:
            total_content_h = len(self._data) * self._row_h
            viewport_h = self.winfo_height() - self._header_h - 2
            max_scroll_y = max(0.0, float(total_content_h - viewport_h))
            self._scroll_y = max(0.0, min(max_scroll_y, self._scroll_y + delta * (self._row_h * 1.5)))

        self.request_redraw()

    def _on_shift_mousewheel(self, event: tk.Event) -> None:
        if self._active_editor:
            self._commit_cell_edit()

        delta = -1 * int(event.delta / 120) if event.delta else 1
        total_content_w = sum(self._col_widths)
        viewport_w = self.winfo_width() - (self._scrollbar_w + 6)
        max_scroll_x = max(0.0, float(total_content_w - viewport_w))
        self._scroll_x = max(0.0, min(max_scroll_x, self._scroll_x + delta * 24.0))
        self.request_redraw()

    def _sort_by_column(self, col_idx: int) -> None:
        if self._active_editor:
            self._dismiss_active_editor()

        if self._sort_col == col_idx:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col_idx
            self._sort_asc = True

        # Preserve active selected records across sorting
        prev_selected_data = [self._data[i] for i in self._selected_rows if 0 <= i < len(self._data)]

        def _sort_val(row: List[Any]) -> Tuple[int, Any]:
            if col_idx >= len(row):
                return (1, "")
            val = row[col_idx]
            try:
                return (0, float(val))
            except (ValueError, TypeError):
                return (1, str(val).lower())

        try:
            self._data.sort(key=_sort_val, reverse=not self._sort_asc)
        except Exception:
            pass

        if prev_selected_data:
            new_sel = set()
            for item in prev_selected_data:
                for idx, r in enumerate(self._data):
                    if r == item:
                        new_sel.add(idx)
                        break
            self._selected_rows = new_sel

        self._hovered_row = None
        self.request_redraw()

    def is_column_editable(self, col_idx: int) -> bool:
        """Return True if the column at col_idx can be edited."""
        if not (0 <= col_idx < len(self._columns)):
            return False
        col_name = self._columns[col_idx]
        if self._editable_columns is not None:
            return (col_idx in self._editable_columns) or (col_name in self._editable_columns)
        if self._column_editors:
            return (col_idx in self._column_editors) or (col_name in self._column_editors)
        return False

    def _get_column_editor_config(self, col_idx: int) -> Any:
        col_name = self._columns[col_idx] if 0 <= col_idx < len(self._columns) else ""
        if self._column_editors:
            if col_idx in self._column_editors:
                return self._column_editors[col_idx]
            if col_name in self._column_editors:
                return self._column_editors[col_name]
        return "entry"

    def _get_cell_at(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        if y <= self._header_h or y >= self.winfo_height():
            return None

        w = self.winfo_width()
        h = self.winfo_height()
        v_needed, _, _, _, _, _ = self._get_vbar_bounds(w, h)
        if v_needed and x >= w - self._scrollbar_w - 8:
            return None

        row_idx = int((y - self._header_h + self._scroll_y) // self._row_h)
        if not (0 <= row_idx < len(self._data)):
            return None

        curr_x = -self._scroll_x
        for col_idx, col_w in enumerate(self._col_widths):
            if curr_x <= x < curr_x + col_w:
                return row_idx, col_idx
            curr_x += col_w
        return None

    def _get_cell_bounds(self, row_idx: int, col_idx: int) -> Optional[Tuple[int, int, int, int]]:
        if not (0 <= row_idx < len(self._data)) or not (0 <= col_idx < len(self._columns)):
            return None
        if not self._col_widths or col_idx >= len(self._col_widths):
            return None

        col_x = int(-self._scroll_x + sum(self._col_widths[:col_idx]))
        row_y = int(self._header_h + row_idx * self._row_h - self._scroll_y)
        col_w = int(self._col_widths[col_idx])
        row_h = int(self._row_h)
        return col_x, row_y, col_w, row_h

    def _find_next_editable_cell(self, row_idx: int, col_idx: int, forward: bool = True) -> Optional[Tuple[int, int]]:
        num_rows = len(self._data)
        num_cols = len(self._columns)
        if num_rows == 0 or num_cols == 0:
            return None

        step = 1 if forward else -1
        curr_r = row_idx
        curr_c = col_idx + step

        for _ in range(num_rows * num_cols):
            if curr_c >= num_cols:
                curr_c = 0
                curr_r += 1
            elif curr_c < 0:
                curr_c = num_cols - 1
                curr_r -= 1

            if not (0 <= curr_r < num_rows):
                break

            if self.is_column_editable(curr_c):
                return curr_r, curr_c

            curr_c += step

        return None

    def _start_cell_edit(self, row_idx: int, col_idx: int) -> bool:
        if not (0 <= row_idx < len(self._data)) or not (0 <= col_idx < len(self._columns)):
            return False
        if not self.is_column_editable(col_idx):
            return False

        if self._active_editor:
            if self._editing_cell == (row_idx, col_idx):
                return True
            if not self._commit_cell_edit():
                return False

        # Ensure column widths are calculated
        if not self._col_widths:
            w = self.winfo_width()
            available_w = max(50, w - (self._scrollbar_w + 10))
            self._calc_column_widths_for(available_w)

        # Scroll cell into view if needed
        viewport_h = max(1, self.winfo_height() - self._header_h - 2)
        row_top = row_idx * self._row_h
        row_bottom = (row_idx + 1) * self._row_h
        needs_redraw = False

        if row_top < self._scroll_y:
            self._scroll_y = float(row_top)
            needs_redraw = True
        elif row_bottom > self._scroll_y + viewport_h:
            self._scroll_y = max(0.0, float(row_bottom - viewport_h))
            needs_redraw = True

        col_left = sum(self._col_widths[:col_idx])
        col_right = col_left + self._col_widths[col_idx]
        viewport_w = max(1, self.winfo_width() - (self._scrollbar_w + 6))
        if col_left < self._scroll_x:
            self._scroll_x = float(col_left)
            needs_redraw = True
        elif col_right > self._scroll_x + viewport_w:
            self._scroll_x = max(0.0, float(col_right - viewport_w))
            needs_redraw = True

        if needs_redraw:
            self.request_redraw()
            self.update_idletasks()

        bounds = self._get_cell_bounds(row_idx, col_idx)
        if not bounds:
            return False

        cell_x, cell_y, cell_w, cell_h = bounds
        place_x = max(1, cell_x + 1)
        place_y = max(self._header_h + 1, cell_y + 1)
        place_w = max(10, cell_w - 2)
        place_h = max(10, cell_h - 2)

        current_val = self._data[row_idx][col_idx] if col_idx < len(self._data[row_idx]) else ""
        cfg = self._get_column_editor_config(col_idx)

        pal = self._palette
        bg_hex = to_tk_hex(getattr(pal, "input_bg", "#1c1b1f"))
        fg_hex = to_tk_hex(getattr(pal, "fg", "#e6e0e9"))
        primary_hex = to_tk_hex(getattr(pal, "primary", "#8b5cf6"))

        self._editing_cell = (row_idx, col_idx)

        # 1. Custom callable factory
        if callable(cfg):
            custom_widget = cfg(
                self,
                row_idx,
                col_idx,
                current_val,
                lambda v=None: self._commit_cell_edit(v),
                self._cancel_cell_edit,
            )
            if custom_widget:
                custom_widget.place(x=place_x, y=place_y, width=place_w, height=place_h)
                self._active_editor = custom_widget
                self._active_editor_widget = custom_widget
                try:
                    custom_widget.focus_set()
                except Exception:
                    pass
                return True
            return False

        # 2. Combobox editor
        is_combobox = False
        cb_values: List[str] = []
        if isinstance(cfg, dict) and cfg.get("type") == "combobox":
            is_combobox = True
            cb_values = [str(v) for v in cfg.get("values", [])]
        elif isinstance(cfg, (tuple, list)) and len(cfg) >= 2 and cfg[0] == "combobox":
            is_combobox = True
            cb_values = [str(v) for v in cfg[1]]
        elif cfg == "combobox":
            is_combobox = True
            for r in self._data:
                if col_idx < len(r):
                    val_str = str(r[col_idx])
                    if val_str and val_str not in cb_values:
                        cb_values.append(val_str)

        if is_combobox:
            editor_frame = tk.Frame(self, bg=primary_hex, padx=1, pady=1)
            container = tk.Frame(editor_frame, bg=bg_hex)
            container.pack(fill="both", expand=True)

            lbl_text = tk.Label(
                container,
                text=str(current_val),
                bg=bg_hex,
                fg=fg_hex,
                font=("sans-serif", 10),
                anchor="w",
                padx=6,
            )
            lbl_text.pack(side="left", fill="both", expand=True)
            lbl_arrow = tk.Label(container, text="▼", bg=bg_hex, fg=primary_hex, font=("sans-serif", 8), padx=6)
            lbl_arrow.pack(side="right")

            editor_frame.place(x=place_x, y=place_y, width=place_w, height=place_h)
            self._active_editor = editor_frame
            self._active_editor_widget = None

            self.update_idletasks()

            _TableCellDropdownPopup(
                table=self,
                cell_x=place_x,
                cell_y=place_y,
                cell_w=place_w,
                cell_h=place_h,
                values=cb_values,
                current_value=str(current_val),
                on_select=lambda v: self._commit_cell_edit(v),
                on_dismiss=lambda: self._cancel_cell_edit(),
            )
            return True

        # 3. Default Entry editor
        editor_frame = tk.Frame(self, bg=primary_hex, padx=1, pady=1)
        entry = tk.Entry(
            editor_frame,
            bg=bg_hex,
            fg=fg_hex,
            insertbackground=fg_hex,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            font=("sans-serif", 10),
        )
        entry.pack(fill="both", expand=True)
        entry.insert(0, str(current_val))
        entry.select_range(0, tk.END)

        def _on_enter(e):
            self._commit_cell_edit(entry.get())
            return "break"

        def _on_escape(e):
            self._cancel_cell_edit()
            return "break"

        def _on_tab(e):
            self._navigate_cell_edit(forward=True, new_val=entry.get())
            return "break"

        def _on_shift_tab(e):
            self._navigate_cell_edit(forward=False, new_val=entry.get())
            return "break"

        def _on_blur(e):
            if self._editing_cell == (row_idx, col_idx):
                self.after(50, lambda: self._commit_cell_edit(entry.get()) if self._editing_cell == (row_idx, col_idx) else None)

        entry.bind("<Return>", _on_enter)
        entry.bind("<KP_Enter>", _on_enter)
        entry.bind("<Escape>", _on_escape)
        entry.bind("<Tab>", _on_tab)
        entry.bind("<Shift-Tab>", _on_shift_tab)
        entry.bind("<ISO_Left_Tab>", _on_shift_tab)
        entry.bind("<FocusOut>", _on_blur)

        editor_frame.place(x=place_x, y=place_y, width=place_w, height=place_h)
        self._active_editor = editor_frame
        self._active_editor_widget = entry
        entry.focus_set()
        return True

    def _commit_cell_edit(self, new_val: Any = None) -> bool:
        if self._active_editor is None or self._editing_cell is None:
            return True

        row_idx, col_idx = self._editing_cell
        if not (0 <= row_idx < len(self._data)):
            self._dismiss_active_editor()
            return True

        old_val = self._data[row_idx][col_idx] if col_idx < len(self._data[row_idx]) else None

        if new_val is None:
            editor = self._active_editor_widget or self._active_editor
            if isinstance(editor, tk.Entry):
                new_val = editor.get()
            elif hasattr(editor, "get"):
                try:
                    new_val = editor.get()
                except Exception:
                    new_val = str(old_val)
            else:
                new_val = str(old_val)

        # Preserve numeric types if old_val was numeric
        if isinstance(old_val, int) and not isinstance(old_val, bool):
            try:
                new_val = int(new_val)
            except (ValueError, TypeError):
                pass
        elif isinstance(old_val, float):
            try:
                new_val = float(new_val)
            except (ValueError, TypeError):
                pass

        # Validation callback
        if callable(self._on_cell_edit):
            try:
                res = self._on_cell_edit(row_idx, col_idx, old_val, new_val)
                if res is False:
                    self._dismiss_active_editor()
                    self.request_redraw()
                    return False
            except Exception:
                self._dismiss_active_editor()
                self.request_redraw()
                return False

        # Apply in-place mutation
        if col_idx < len(self._data[row_idx]):
            self._data[row_idx][col_idx] = new_val
        else:
            while len(self._data[row_idx]) < col_idx:
                self._data[row_idx].append("")
            self._data[row_idx].append(new_val)

        self._dismiss_active_editor()
        self.request_redraw()

        try:
            self.event_generate("<<TableCellEdited>>", x=col_idx, y=row_idx)
        except Exception:
            pass

        return True

    def _cancel_cell_edit(self) -> None:
        self._dismiss_active_editor()
        self.request_redraw()

    def _dismiss_active_editor(self) -> None:
        if self._active_editor is not None:
            try:
                self._active_editor.place_forget()
                self._active_editor.destroy()
            except Exception:
                pass
        self._active_editor = None
        self._active_editor_widget = None
        self._editing_cell = None

    def _navigate_cell_edit(self, forward: bool = True, new_val: Any = None) -> None:
        if self._editing_cell is None:
            return
        curr_r, curr_c = self._editing_cell
        if not self._commit_cell_edit(new_val):
            return

        next_cell = self._find_next_editable_cell(curr_r, curr_c, forward=forward)
        if next_cell:
            self.after_idle(lambda: self._start_cell_edit(*next_cell))

    def _on_double_click(self, event: tk.Event) -> None:
        cell = self._get_cell_at(event.x, event.y)
        if cell:
            r, c = cell
            if self.is_column_editable(c):
                self._start_cell_edit(r, c)

    def _on_key_edit(self, event: tk.Event) -> None:
        if self._active_editor:
            return
        row_idx = self._last_clicked_row
        if row_idx is None and self._selected_rows:
            row_idx = next(iter(self._selected_rows))
        if row_idx is not None and 0 <= row_idx < len(self._data):
            for col_idx in range(len(self._columns)):
                if self.is_column_editable(col_idx):
                    self._start_cell_edit(row_idx, col_idx)
                    break

    def _on_configure(self, event: tk.Event) -> None:
        if self._active_editor and self._editing_cell:
            bounds = self._get_cell_bounds(*self._editing_cell)
            if bounds:
                cell_x, cell_y, cell_w, cell_h = bounds
                self._active_editor.place(
                    x=max(1, cell_x + 1),
                    y=max(self._header_h + 1, cell_y + 1),
                    width=max(10, cell_w - 2),
                    height=max(10, cell_h - 2),
                )

    def start_edit(self, row_idx: int, col_idx: int) -> bool:
        """Programmatically activate cell editing for the specified cell."""
        return self._start_cell_edit(row_idx, col_idx)

    def commit_edit(self, new_val: Any = None) -> bool:
        """Programmatically commit the active cell edit."""
        return self._commit_cell_edit(new_val)

    def cancel_edit(self) -> None:
        """Programmatically cancel and dismiss the active cell edit."""
        self._cancel_cell_edit()

    def _render_table(self, surf: Surface) -> None:
        """Pure Blend2D surface rendering hook."""
        w = surf.width
        h = surf.height
        if w <= 4 or h <= 4:
            return

        pal = self._palette
        card_bg = getattr(pal, "card_bg", "#25232a")
        card_border = getattr(pal, "card_border", "#49454f")
        fg = getattr(pal, "fg", "#e6e0e9")
        primary = getattr(pal, "primary", "#8b5cf6")
        surface_col = getattr(pal, "surface", "#2f2d38")
        hover_col = getattr(pal, "card_hover", "#383542")

        total_content_h = len(self._data) * self._row_h
        viewport_h = max(0, h - self._header_h - 2)
        v_needed = total_content_h > viewport_h

        available_w = w - 4
        if v_needed:
            available_w -= (self._scrollbar_w + 6)

        # Recalculate column widths proportionally if width changed and user hasn't resized
        if (not self._user_resized_cols) and (available_w != self._last_calc_w or not self._col_widths):
            self._calc_column_widths_for(available_w)
            self._last_calc_w = available_w

        # Clamp scroll ranges
        max_scroll_y = max(0.0, float(total_content_h - viewport_h))
        self._scroll_y = max(0.0, min(max_scroll_y, self._scroll_y))

        total_content_w = sum(self._col_widths) if self._col_widths else available_w
        max_scroll_x = max(0.0, float(total_content_w - available_w))
        self._scroll_x = max(0.0, min(max_scroll_x, self._scroll_x))

        # 1. Fill base card background with smooth rounded corners
        surf.fill_rounded_rect(0, 0, w, h, self._corner_radius, self._corner_radius, card_bg)

        # 2. Clip all table content to the rounded card boundary
        surf.save()
        surf.clip_rounded_rect(0, 0, w, h, self._corner_radius, self._corner_radius)

        # 3. Draw Header Background & Separators
        surf.fill_rect(0, 0, w, self._header_h, card_bg)
        surf.draw_line(0, self._header_h, w, self._header_h, card_border, 1.0)

        # Header Columns
        curr_x = -self._scroll_x
        for col_idx, col_name in enumerate(self._columns):
            col_w = self._col_widths[col_idx] if col_idx < len(self._col_widths) else 100

            # Draw header cell with clipping
            surf.save()
            surf.clip_rect(max(0, curr_x + 2), 0, max(0, col_w - 4), self._header_h)

            header_text = str(col_name)
            sort_arrow = ""
            if self._sort_col == col_idx:
                sort_arrow = " ▲" if self._sort_asc else " ▼"
            full_header = header_text + sort_arrow

            max_h_chars = max(3, int((col_w - 18) / 7.2))
            display_header = full_header[:max_h_chars - 1] + "…" if len(full_header) > max_h_chars else full_header

            # Header text baseline calculation
            ty = self._header_h / 2.0 + 4.0
            surf.draw_text(
                display_header,
                curr_x + 10,
                ty,
                font_size=11.0,
                color=fg,
                weight=600,
            )
            surf.restore()

            # Column vertical separator
            surf.draw_line(curr_x + col_w, 6, curr_x + col_w, self._header_h - 6, card_border, 0.75)
            curr_x += col_w

        # 4. Virtualized Row Rendering
        surf.save()
        surf.clip_rect(0, self._header_h + 1, available_w, viewport_h)

        first_row = max(0, int(self._scroll_y // self._row_h))
        last_row = min(len(self._data), int((self._scroll_y + viewport_h) // self._row_h) + 1)

        for row_idx in range(first_row, last_row):
            row = self._data[row_idx]
            row_y = self._header_h + row_idx * self._row_h - self._scroll_y
            is_selected = row_idx in self._selected_rows
            is_hovered = (self._hovered_row == row_idx and not is_selected)

            # Row fill color
            if is_selected:
                row_fill = primary
                text_col = "#ffffff"
            elif is_hovered:
                row_fill = hover_col
                text_col = fg
            elif self._zebra_striping and (row_idx % 2 == 1):
                row_fill = surface_col
                text_col = fg
            else:
                row_fill = card_bg
                text_col = fg

            # Draw row background
            surf.fill_rect(0, row_y, available_w, self._row_h, row_fill)

            # Bottom row divider
            surf.draw_line(0, row_y + self._row_h, available_w, row_y + self._row_h, card_border, 0.5)

            # Draw cell text
            cell_x = -self._scroll_x
            for col_idx, col_w in enumerate(self._col_widths):
                if col_idx < len(row):
                    raw_val = str(row[col_idx])
                else:
                    raw_val = ""

                # Clip text cleanly inside the cell bounds
                surf.save()
                surf.clip_rect(max(0, cell_x + 2), row_y, max(0, col_w - 4), self._row_h)

                # Truncate with ellipsis if text exceeds column width
                max_chars = max(3, int((col_w - 18) / 6.8))
                display_val = raw_val[:max_chars - 1] + "…" if len(raw_val) > max_chars else raw_val

                cy = row_y + self._row_h / 2.0 + 3.5
                surf.draw_text(
                    display_val,
                    cell_x + 10,
                    cy,
                    font_size=10.0,
                    color=text_col,
                    weight=400,
                )
                surf.restore()

                cell_x += col_w

        surf.restore()  # End body clip

        # 5. Draw Pure Blend2D Scrollbar
        if v_needed:
            has_vbar, vx, vy, vw, vh, _ = self._get_vbar_bounds(w, h)
            if has_vbar:
                bar_color = primary if (self._vbar_hovered or self._vbar_dragging) else primary
                surf.fill_rounded_rect(vx, vy, vw, vh, vw / 2.0, vw / 2.0, bar_color)

        surf.restore()  # End card clip

        # 6. Stroke outer rounded card border
        surf.stroke_rounded_rect(0.5, 0.5, w - 1.0, h - 1.0, self._corner_radius, self._corner_radius, card_border, 1.0)

    def _on_controller_click(self, x: int, y: int, button: int) -> None:
        """No-op: Table manages cell, row, and scrollbar clicks internally."""
        pass

    @property
    def command(self) -> Optional[Callable[..., Any]]:
        return self._command

    @command.setter
    def command(self, cmd: Optional[Callable[..., Any]]) -> None:
        self._command = cmd

    @property
    def columns(self) -> List[str]:
        return list(self._columns)

    @columns.setter
    def columns(self, cols: Sequence[str]) -> None:
        if self._active_editor:
            self._dismiss_active_editor()
        self._columns = list(cols)
        self._user_resized_cols = False
        self._last_calc_w = 0
        self.request_redraw()

    @property
    def data(self) -> List[List[Any]]:
        return [list(r) for r in self._data]

    @data.setter
    def data(self, rows: Sequence[Sequence[Any]]) -> None:
        if self._active_editor:
            self._dismiss_active_editor()
        self._data = [list(r) for r in rows]
        self._selected_rows.clear()
        self._hovered_row = None
        self._last_clicked_row = None
        self._last_calc_w = 0
        self.request_redraw()

    @property
    def selected_row(self) -> Optional[int]:
        if not self._selected_rows:
            return None
        return next(iter(sorted(self._selected_rows)))

    @selected_row.setter
    def selected_row(self, idx: Optional[int]) -> None:
        if idx is None or idx < 0 or idx >= len(self._data):
            self._selected_rows.clear()
        else:
            self._selected_rows = {int(idx)}
        self.request_redraw()

    @property
    def selected_rows(self) -> List[int]:
        return sorted(self._selected_rows)

    @selected_rows.setter
    def selected_rows(self, indices: Sequence[int]) -> None:
        self._selected_rows = {i for i in indices if 0 <= i < len(self._data)}
        self.request_redraw()

    @property
    def multi_select(self) -> bool:
        return self._multi_select

    @multi_select.setter
    def multi_select(self, enabled: bool) -> None:
        self._multi_select = bool(enabled)
        if not enabled and len(self._selected_rows) > 1:
            first = next(iter(sorted(self._selected_rows)))
            self._selected_rows = {first}
            self.request_redraw()

    @property
    def zebra_striping(self) -> bool:
        return self._zebra_striping

    @zebra_striping.setter
    def zebra_striping(self, enabled: bool) -> None:
        self._zebra_striping = bool(enabled)
        self.request_redraw()

    @property
    def is_editing(self) -> bool:
        """Return True if a cell editor overlay is currently active."""
        return self._active_editor is not None and self._editing_cell is not None

    @property
    def editing_cell(self) -> Optional[Tuple[int, int]]:
        """Return (row_idx, col_idx) of the cell currently being edited, or None."""
        return self._editing_cell

    @property
    def editable_columns(self) -> Optional[List[Union[int, str]]]:
        return list(self._editable_columns) if self._editable_columns is not None else None

    @editable_columns.setter
    def editable_columns(self, cols: Optional[Sequence[Union[int, str]]]) -> None:
        self._editable_columns = list(cols) if cols is not None else None

    @property
    def column_editors(self) -> Dict[Union[int, str], Any]:
        return dict(self._column_editors)

    @column_editors.setter
    def column_editors(self, editors: Optional[Dict[Union[int, str], Any]]) -> None:
        self._column_editors = dict(editors) if editors else {}

    @property
    def on_cell_edit(self) -> Optional[Callable[..., Any]]:
        return self._on_cell_edit

    @on_cell_edit.setter
    def on_cell_edit(self, callback: Optional[Callable[..., Any]]) -> None:
        self._on_cell_edit = callback

    def get_selected(self) -> Optional[List[Any]]:
        first = self.selected_row
        if first is not None and 0 <= first < len(self._data):
            return list(self._data[first])
        return None

    def get_selected_rows(self) -> List[List[Any]]:
        return [list(self._data[i]) for i in sorted(self._selected_rows) if 0 <= i < len(self._data)]

    def clear_selection(self) -> None:
        self._selected_rows.clear()
        self.request_redraw()

    def select_all(self) -> None:
        if self._multi_select:
            self._selected_rows = set(range(len(self._data)))
            self.request_redraw()

    def _on_theme_changed(self, pal: Palette) -> None:
        super()._on_theme_changed(pal)
        if self._active_editor:
            self._commit_cell_edit()
        self.request_redraw()
