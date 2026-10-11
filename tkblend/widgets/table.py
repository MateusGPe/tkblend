from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Sequence, List, Any, Dict, Tuple
from tkblend.widgets.base import BaseControl
from tkblend.widgets.scrollable_frame import VectorScrollbar
from tkblend.theme import Palette, to_tk_hex, get_theme


class Table(BaseControl):
    """
    High-performance Material Design 3 vector data table.
    """

    WIDGET_CLASS = "table"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        columns: Optional[Sequence[str]] = None,
        data: Optional[Sequence[Sequence[Any]]] = None,
        command: Optional[Callable[[int, List[Any]], Any]] = None,
        width: int = 480,
        height: int = 240,
        row_height: int = 32,
        header_height: int = 38,
        **kwargs,
    ):
        self._columns = list(columns) if columns else ["Column 1", "Column 2", "Column 3"]
        self._data: List[List[Any]] = [list(r) for r in data] if data else []
        self._row_h = int(row_height)
        self._header_h = int(header_height)
        self._selected_row: Optional[int] = None
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
        fg_hex = to_tk_hex(pal.fg)
        border_hex = to_tk_hex(pal.card_border)
        primary_hex = to_tk_hex(pal.primary)

        # Viewport canvas for rows
        self._canvas = tk.Canvas(
            self,
            background=bg_hex,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
        )
        self._canvas.place(x=1, y=self._header_h, relwidth=1.0, relheight=1.0, width=-2, height=-(self._header_h + 1))

        # Header row frame
        self._header_frame = tk.Frame(self, background=bg_hex, height=self._header_h)
        self._header_frame.place(x=1, y=1, relwidth=1.0, height=self._header_h - 1, width=-2)

        self._build_header()
        self._render_rows()

        self._canvas.bind("<Button-1>", self._on_canvas_click)

    def _build_header(self) -> None:
        for w in self._header_frame.winfo_children():
            w.destroy()

        pal = self._palette
        bg_hex = to_tk_hex(pal.card_bg)
        fg_hex = to_tk_hex(pal.fg)

        col_count = max(1, len(self._columns))
        for col_idx, col_name in enumerate(self._columns):
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
                padx=10,
                cursor="hand2",
            )
            lbl.place(relx=col_idx / col_count, rely=0.0, relwidth=1.0 / col_count, relheight=1.0)
            lbl.bind("<Button-1>", lambda e, c=col_idx: self._on_header_click(c))

    def _render_rows(self) -> None:
        self._canvas.delete("all")
        if not self._data:
            return

        pal = self._palette
        bg_hex = to_tk_hex(pal.card_bg)
        fg_hex = to_tk_hex(pal.fg)
        sel_hex = to_tk_hex(pal.primary)
        border_hex = to_tk_hex(pal.card_border)
        alt_hex = to_tk_hex(pal.surface)

        w = self._canvas.winfo_width() or self._logical_w
        col_count = max(1, len(self._columns))
        col_w = w / col_count

        total_h = len(self._data) * self._row_h
        self._canvas.configure(scrollregion=(0, 0, w, total_h))

        for row_idx, row in enumerate(self._data):
            y1 = row_idx * self._row_h
            y2 = y1 + self._row_h
            is_selected = (self._selected_row == row_idx)

            fill_col = sel_hex if is_selected else (alt_hex if row_idx % 2 == 1 else bg_hex)
            self._canvas.create_rectangle(0, y1, w, y2, fill=fill_col, outline="", tags=f"row_{row_idx}")

            # Bottom row divider
            self._canvas.create_line(0, y2, w, y2, fill=border_hex, tags=f"row_{row_idx}")

            text_col = "#ffffff" if is_selected else fg_hex
            for col_idx, cell_val in enumerate(row[:col_count]):
                cx = col_idx * col_w + 10
                cy = y1 + self._row_h / 2
                self._canvas.create_text(
                    cx, cy,
                    text=str(cell_val),
                    anchor="w",
                    fill=text_col,
                    font=("sans-serif", 10),
                    tags=f"row_{row_idx}",
                )

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
            self._data.sort(key=lambda r: r[col_idx] if col_idx < len(r) else "", reverse=not self._sort_asc)
        except Exception:
            pass

        self._build_header()
        self._render_rows()

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
