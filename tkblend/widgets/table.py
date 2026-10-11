from __future__ import annotations

import sys
import tkinter as tk
from typing import Optional, Callable, Sequence, List, Any, Dict, Tuple, Union
from tkblend.widgets.base import BaseControl
from tkblend.widgets.scrollable_frame import VectorScrollbar
from tkblend.theme import Palette, to_tk_hex, get_theme


class Table(BaseControl):
    """
    High-performance Material Design 3 vector data table with synchronized columns,
    auto/proportional column layout, integrated VectorScrollbar, and row hover/selection.
    """

    WIDGET_CLASS = "table"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        columns: Optional[Sequence[str]] = None,
        data: Optional[Sequence[Sequence[Any]]] = None,
        command: Optional[Callable[[int, List[Any]], Any]] = None,
        column_widths: Optional[Sequence[Union[int, float]]] = None,
        width: int = 480,
        height: int = 240,
        row_height: int = 34,
        header_height: int = 38,
        scrollbar_width: int = 8,
        corner_radius: float = 8.0,
        **kwargs,
    ):
        self._columns = list(columns) if columns else ["Column 1", "Column 2", "Column 3"]
        self._data: List[List[Any]] = [list(r) for r in data] if data else []
        self._column_weights = list(column_widths) if column_widths else None
        self._row_h = int(row_height)
        self._header_h = int(header_height)
        self._scrollbar_w = int(scrollbar_width)
        self._corner_radius = float(corner_radius)
        self._selected_row: Optional[int] = None
        self._hovered_row: Optional[int] = None
        self._sort_col: Optional[int] = None
        self._sort_asc: bool = True
        self._command = command

        super().__init__(
            master=master,
            widget_class="table",
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )

        self.set_var("--header-height", str(self._header_h))

        pal = self._palette
        bg_hex = to_tk_hex(pal.card_bg)

        # Header frame at top
        self._header_frame = tk.Frame(self, background=bg_hex, height=self._header_h)
        self._header_frame.place(x=2, y=2, relwidth=1.0, height=self._header_h - 2, width=-4)

        # Canvas viewport for rows
        self._canvas = tk.Canvas(
            self,
            background=bg_hex,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
        )
        self._canvas.place(
            x=2,
            y=self._header_h + 1,
            relwidth=1.0,
            relheight=1.0,
            width=-(4 + self._scrollbar_w),
            height=-(self._header_h + 5),
        )

        # Vector Scrollbar for rows
        self._scrollbar = VectorScrollbar(
            self,
            orientation="vertical",
            command=self._canvas.yview,
            width=self._scrollbar_w,
            height=height,
        )
        self._scrollbar.place(
            relx=1.0,
            x=-(self._scrollbar_w + 3),
            y=self._header_h + 2,
            relheight=1.0,
            height=-(self._header_h + 6),
            width=self._scrollbar_w,
        )

        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # Event bindings
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<Button-1>", self._on_canvas_click)
        self._canvas.bind("<Motion>", self._on_canvas_motion)
        self._canvas.bind("<Leave>", self._on_canvas_leave)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind("<Button-4>", self._on_mousewheel)
        self._canvas.bind("<Button-5>", self._on_mousewheel)

        self._build_header()
        self._render_rows()

    def _calc_column_widths(self, available_w: int) -> List[int]:
        col_count = max(1, len(self._columns))
        if self._column_weights and len(self._column_weights) == col_count:
            total_w = sum(self._column_weights)
            if total_w > 0:
                widths = [max(40, int(available_w * (w / total_w))) for w in self._column_weights]
                diff = available_w - sum(widths)
                if diff != 0:
                    widths[-1] += diff
                return widths

        # Auto-compute proportional widths based on content lengths
        max_lens = [len(str(c)) for c in self._columns]
        for row in self._data:
            for i, cell in enumerate(row[:col_count]):
                max_lens[i] = max(max_lens[i], len(str(cell)))

        weights = [max(8, l) for l in max_lens]
        total_weight = sum(weights)
        if total_weight <= 0:
            total_weight = 1

        widths = [max(45, int(available_w * (w / total_weight))) for w in weights]
        diff = available_w - sum(widths)
        if diff != 0:
            max_idx = widths.index(max(widths))
            widths[max_idx] += diff
        return widths

    def _get_canvas_width(self) -> int:
        cw = self._canvas.winfo_width()
        if cw > 1:
            return cw
        parent_w = self.winfo_width()
        if parent_w > 1:
            return max(100, parent_w - 4 - self._scrollbar_w)
        return max(100, int(self._logical_w * self._scale_factor) - 4 - self._scrollbar_w)

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self._build_header()
        self._render_rows()

    def _build_header(self) -> None:
        for w in self._header_frame.winfo_children():
            w.destroy()

        pal = self._palette
        bg_hex = to_tk_hex(pal.card_bg)
        fg_hex = to_tk_hex(pal.fg)

        w = self._get_canvas_width()
        col_widths = self._calc_column_widths(w)

        curr_x = 0
        for col_idx, (col_name, col_w) in enumerate(zip(self._columns, col_widths)):
            sort_arrow = ""
            if self._sort_col == col_idx:
                sort_arrow = " ▲" if self._sort_asc else " ▼"

            lbl = tk.Label(
                self._header_frame,
                text=str(col_name) + sort_arrow,
                bg=bg_hex,
                fg=fg_hex,
                font=("sans-serif", 10, "bold"),
                anchor="w",
                padx=12,
                cursor="hand2",
            )
            lbl.place(x=curr_x, y=0, width=col_w, relheight=1.0)
            lbl.bind("<Button-1>", lambda e, c=col_idx: self._on_header_click(c))

            curr_x += col_w

    def _render_rows(self) -> None:
        self._canvas.delete("all")
        if not self._data:
            return

        pal = self._palette
        bg_hex = to_tk_hex(pal.card_bg)
        fg_hex = to_tk_hex(pal.fg)
        sel_hex = to_tk_hex(pal.primary)
        border_hex = to_tk_hex(pal.card_border)
        alt_hex = to_tk_hex(getattr(pal, "surface", pal.card_bg))
        hover_hex = to_tk_hex(getattr(pal, "card_hover", pal.surface))

        w = self._get_canvas_width()
        col_widths = self._calc_column_widths(w)

        total_h = len(self._data) * self._row_h
        self._canvas.configure(scrollregion=(0, 0, w, total_h))

        for row_idx, row in enumerate(self._data):
            y1 = row_idx * self._row_h
            y2 = y1 + self._row_h
            is_selected = (self._selected_row == row_idx)
            is_hovered = (self._hovered_row == row_idx and not is_selected)

            if is_selected:
                fill_col = sel_hex
                text_col = "#ffffff"
            elif is_hovered:
                fill_col = hover_hex
                text_col = fg_hex
            elif row_idx % 2 == 1:
                fill_col = alt_hex
                text_col = fg_hex
            else:
                fill_col = bg_hex
                text_col = fg_hex

            # Row background
            self._canvas.create_rectangle(0, y1, w, y2, fill=fill_col, outline="", tags=f"row_{row_idx}")

            # Bottom row divider
            self._canvas.create_line(0, y2, w, y2, fill=border_hex, tags=f"row_{row_idx}")

            # Cells
            curr_x = 0
            for col_idx, col_w in enumerate(col_widths):
                raw_val = str(row[col_idx]) if col_idx < len(row) else ""
                max_chars = max(4, int((col_w - 20) / 7.2))
                if len(raw_val) > max_chars:
                    cell_val = raw_val[:max_chars - 1] + "…"
                else:
                    cell_val = raw_val

                cx = curr_x + 12
                cy = y1 + self._row_h / 2
                self._canvas.create_text(
                    cx,
                    cy,
                    text=cell_val,
                    anchor="w",
                    fill=text_col,
                    font=("sans-serif", 10),
                    tags=f"row_{row_idx}",
                )
                curr_x += col_w

    def _on_canvas_motion(self, event: tk.Event) -> None:
        canvas_y = self._canvas.canvasy(event.y)
        row_idx = int(canvas_y // self._row_h)
        if 0 <= row_idx < len(self._data):
            if self._hovered_row != row_idx:
                self._hovered_row = row_idx
                self._render_rows()
        elif self._hovered_row is not None:
            self._hovered_row = None
            self._render_rows()

    def _on_canvas_leave(self, event: tk.Event) -> None:
        if self._hovered_row is not None:
            self._hovered_row = None
            self._render_rows()

    def _on_canvas_click(self, event: tk.Event) -> None:
        canvas_y = self._canvas.canvasy(event.y)
        row_idx = int(canvas_y // self._row_h)
        if 0 <= row_idx < len(self._data):
            self._selected_row = row_idx
            self._render_rows()
            if callable(self._command):
                try:
                    self._command(row_idx, self._data[row_idx])
                except Exception:
                    pass

    def _on_header_click(self, col_idx: int) -> None:
        if self._sort_col == col_idx:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col_idx
            self._sort_asc = True

        try:
            self._data.sort(key=lambda r: str(r[col_idx]) if col_idx < len(r) else "", reverse=not self._sort_asc)
        except Exception:
            pass

        self._build_header()
        self._render_rows()

    def _on_mousewheel(self, event: tk.Event) -> None:
        if sys.platform == "darwin":
            delta = -1 * event.delta
        elif event.num == 5:
            delta = 1
        elif event.num == 4:
            delta = -1
        else:
            delta = -1 * int(event.delta / 120)
        self._canvas.yview_scroll(delta, "units")

    @property
    def columns(self) -> List[str]:
        return list(self._columns)

    @columns.setter
    def columns(self, cols: Sequence[str]) -> None:
        self._columns = list(cols)
        self._build_header()
        self._render_rows()

    @property
    def data(self) -> List[List[Any]]:
        return [list(r) for r in self._data]

    @data.setter
    def data(self, rows: Sequence[Sequence[Any]]) -> None:
        self._data = [list(r) for r in rows]
        self._selected_row = None
        self._hovered_row = None
        self._render_rows()

    @property
    def selected_row(self) -> Optional[int]:
        return self._selected_row

    def get_selected(self) -> Optional[List[Any]]:
        if self._selected_row is not None and 0 <= self._selected_row < len(self._data):
            return list(self._data[self._selected_row])
        return None

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self._build_header()
        self._render_rows()

    def on_theme_update(self, pal: Palette) -> None:
        super().on_theme_update(pal)
        bg_hex = to_tk_hex(pal.card_bg)
        try:
            self._canvas.configure(background=bg_hex)
            self._header_frame.configure(background=bg_hex)
        except Exception:
            pass
        self._build_header()
        self._render_rows()
