from __future__ import annotations

import sys
import tkinter as tk
from typing import Optional, Callable, Sequence, List, Any, Dict, Tuple, Union, Set
from tkblend.widgets.base import BaseControl
from tkblend.theme import Palette, to_tk_hex, get_theme
from tkblend.surface import Surface


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

        # Initialize BaseControl
        super().__init__(
            master=master,
            widget_class="",
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )

        # Ensure C++ controller does not intercept with static batch
        self.controller.widget_class = ""
        self._widget_class = ""
        self.clear_batch()
        self.controller.set_on_paint(self._render_table)

        # Mouse and keyboard event bindings on the vector widget frame
        self.bind("<Motion>", self._on_motion, add="+")
        self.bind("<Button-1>", self._on_button_press, add="+")
        self.bind("<B1-Motion>", self._on_drag, add="+")
        self.bind("<ButtonRelease-1>", self._on_button_release, add="+")
        self.bind("<Leave>", self._on_leave, add="+")
        self.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.bind("<Button-4>", self._on_mousewheel, add="+")
        self.bind("<Button-5>", self._on_mousewheel, add="+")
        self.bind("<Shift-MouseWheel>", self._on_shift_mousewheel, add="+")

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
        delta = -1 * int(event.delta / 120) if event.delta else 1
        total_content_w = sum(self._col_widths)
        viewport_w = self.winfo_width() - (self._scrollbar_w + 6)
        max_scroll_x = max(0.0, float(total_content_w - viewport_w))
        self._scroll_x = max(0.0, min(max_scroll_x, self._scroll_x + delta * 24.0))
        self.request_redraw()

    def _sort_by_column(self, col_idx: int) -> None:
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

    # -------------------------------------------------------------
    # Public Properties & Methods
    # -------------------------------------------------------------
    @property
    def columns(self) -> List[str]:
        return list(self._columns)

    @columns.setter
    def columns(self, cols: Sequence[str]) -> None:
        self._columns = list(cols)
        self._user_resized_cols = False
        self._last_calc_w = 0
        self.request_redraw()

    @property
    def data(self) -> List[List[Any]]:
        return [list(r) for r in self._data]

    @data.setter
    def data(self, rows: Sequence[Sequence[Any]]) -> None:
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
        self.request_redraw()
