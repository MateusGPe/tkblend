"""
Unit tests for the Vector Data Table widget and uncropped shadow rendering.
"""

import pytest
import tkinter as tk
import tkblend as tb
from tkblend.widgets.table import Table, _FloatingCellEditor
from tkblend.widgets.card import Card
from tkblend.theme import set_theme, get_theme


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_table_basic_and_data_manipulation(tk_root):
    cols = [
        {"id": "id", "title": "ID", "width": 60, "align": "center"},
        {"id": "name", "title": "Name", "width": 120, "align": "left"},
        {"id": "score", "title": "Score", "width": 80, "align": "right"},
    ]
    data = [
        {"id": "1", "name": "Alice", "score": 95},
        {"id": "2", "name": "Bob", "score": 82},
    ]

    tbl = Table(tk_root, columns=cols, data=data, width=400, height=200)
    tbl.pack()
    tk_root.update_idletasks()

    assert tbl.row_count == 2
    assert tbl.column_count == 3
    assert tbl.get_cell_value(0, "name") == "Alice"
    assert tbl.get_cell_value(1, "score") == 82

    # Insert row
    tbl.insert_row({"id": "3", "name": "Charlie", "score": 90})
    assert tbl.row_count == 3
    assert tbl.get_cell_value(2, "name") == "Charlie"

    # Set cell value
    tbl.set_cell_value(1, "score", 88)
    assert tbl.get_cell_value(1, "score") == 88

    # Delete row
    tbl.delete_row(0)
    assert tbl.row_count == 2
    assert tbl.get_cell_value(0, "name") == "Bob"

    # Clear
    tbl.clear()
    assert tbl.row_count == 0


def test_table_sorting(tk_root):
    cols = ["id", "name", "val"]
    data = [
        {"id": 3, "name": "Charlie", "val": 30},
        {"id": 1, "name": "Alice", "val": 10},
        {"id": 2, "name": "Bob", "val": 20},
    ]

    tbl = Table(tk_root, columns=cols, data=data)
    tbl.pack()
    tk_root.update_idletasks()

    # Sort ascending by id
    tbl.sort_by(0, descending=False)
    filtered = tbl.get_filtered_data()
    assert filtered[0]["id"] == 1
    assert filtered[1]["id"] == 2
    assert filtered[2]["id"] == 3

    # Sort descending by id
    tbl.sort_by(0, descending=True)
    filtered = tbl.get_filtered_data()
    assert filtered[0]["id"] == 3
    assert filtered[1]["id"] == 2
    assert filtered[2]["id"] == 1


def test_table_filtering(tk_root):
    cols = ["id", "name", "city"]
    data = [
        {"id": 1, "name": "Alice", "city": "New York"},
        {"id": 2, "name": "Bob", "city": "London"},
        {"id": 3, "name": "Charlie", "city": "Paris"},
    ]

    tbl = Table(tk_root, columns=cols, data=data)
    tbl.pack()
    tk_root.update_idletasks()

    # Search string filter
    tbl.filter_by("London")
    assert len(tbl.get_filtered_data()) == 1
    assert tbl.get_filtered_data()[0]["name"] == "Bob"

    # Custom callable filter
    tbl.filter_by(lambda row: row["id"] > 1)
    assert len(tbl.get_filtered_data()) == 2

    # Clear filter
    tbl.clear_filter()
    assert len(tbl.get_filtered_data()) == 3


def test_table_pagination(tk_root):
    cols = ["id", "val"]
    data = [{"id": i, "val": f"Item {i}"} for i in range(25)]

    tbl = Table(tk_root, columns=cols, data=data, pagination=True, page_size=10)
    tbl.pack()
    tk_root.update_idletasks()

    assert tbl.get_total_pages() == 3
    assert tbl.get_current_page() == 0
    assert len(tbl._get_visible_data()) == 10

    # Next page
    tbl.next_page()
    assert tbl.get_current_page() == 1
    assert tbl._get_visible_data()[0]["id"] == 10

    # Prev page
    tbl.prev_page()
    assert tbl.get_current_page() == 0
    assert tbl._get_visible_data()[0]["id"] == 0

    # Set page size
    tbl.set_page_size(5)
    assert tbl.get_total_pages() == 5


def test_table_selection(tk_root):
    cols = ["id", "name"]
    data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}, {"id": 3, "name": "C"}]

    tbl = Table(tk_root, columns=cols, data=data, select_mode="extended")
    tbl.pack()
    tk_root.update_idletasks()

    tbl.select_row(1)
    assert tbl.get_selected_index() == 1
    assert tbl.get_selected_indices() == [1]

    tbl.select_all()
    assert tbl.get_selected_indices() == [0, 1, 2]

    tbl.clear_selection()
    assert tbl.get_selected_index() is None
    assert tbl.get_selected_indices() == []


def test_table_export_tsv(tk_root):
    cols = ["id", "name"]
    data = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]

    tbl = Table(tk_root, columns=cols, data=data)
    tsv = tbl.export_tsv()
    assert "id\tname" in tsv
    assert "1\tAlice" in tsv
    assert "2\tBob" in tsv


def test_card_uncropped_shadow_insets(tk_root):
    card = Card(
        tk_root,
        width=200,
        height=150,
        shadow=True,
        shadow_blur=10.0,
        shadow_spread=2.0,
        shadow_offset_x=0.0,
        shadow_offset_y=4.0,
        shadow_insets=True,
    )
    card.pack()
    tk_root.update_idletasks()

    assert card.bg_color is not None
    # Force synchronous paint and blit to ensure no assert or crash
    card.paint_and_blit()


def test_table_theme_sync(tk_root):
    cols = ["id", "name"]
    data = [{"id": 1, "name": "Alice"}]
    tbl = Table(tk_root, columns=cols, data=data)
    tbl.pack()
    tk_root.update_idletasks()

    # Switch themes dynamically
    set_theme("light")
    tk_root.update_idletasks()
    assert get_theme().dark_mode is False

    set_theme("dark")
    tk_root.update_idletasks()
    assert get_theme().dark_mode is True

    tbl.paint_and_blit()


def test_table_column_pinning_and_visibility(tk_root):
    cols = [
        {"id": "id", "title": "ID", "width": 50},
        {"id": "name", "title": "Name", "width": 100},
        {"id": "city", "title": "City", "width": 100},
        {"id": "score", "title": "Score", "width": 80},
    ]
    data = [
        {"id": 1, "name": "Alice", "city": "NY", "score": 90},
        {"id": 2, "name": "Bob", "city": "LA", "score": 85},
    ]

    tbl = Table(tk_root, columns=cols, data=data, pinned_columns=1)
    tbl.pack()
    tk_root.update_idletasks()

    assert tbl.pinned_columns == 1
    assert tbl.is_column_visible("city") is True

    # Hide column
    tbl.hide_column("city")
    assert tbl.is_column_visible("city") is False
    assert len(tbl._get_visible_columns()) == 3

    # Show column
    tbl.show_column("city")
    assert tbl.is_column_visible("city") is True
    assert len(tbl._get_visible_columns()) == 4

    # Reorder column
    tbl._reorder_column(0, 2)
    assert tbl._columns[2]["id"] == "id"

    tbl.paint_and_blit()


def test_table_multi_column_sorting(tk_root):
    cols = ["group", "score", "name"]
    data = [
        {"group": "B", "score": 50, "name": "Eve"},
        {"group": "A", "score": 80, "name": "Alice"},
        {"group": "A", "score": 90, "name": "Bob"},
        {"group": "B", "score": 70, "name": "Dan"},
    ]

    tbl = Table(tk_root, columns=cols, data=data)
    tbl.pack()
    tk_root.update_idletasks()

    # Multi-sort: Group ASC, Score DESC
    tbl.sort_by(0, descending=False, multi=False)
    tbl.sort_by(1, descending=True, multi=True)

    filtered = tbl.get_filtered_data()
    # Group A: Bob (90), then Alice (80)
    assert filtered[0]["name"] == "Bob"
    assert filtered[1]["name"] == "Alice"
    # Group B: Dan (70), then Eve (50)
    assert filtered[2]["name"] == "Dan"
    assert filtered[3]["name"] == "Eve"

    # Reset sorting
    tbl.reset_sorting()
    assert len(tbl._sort_criteria) == 0


def test_table_cell_selection_and_csv_export(tk_root):
    cols = ["c1", "c2", "c3"]
    data = [
        {"c1": "A1", "c2": "B1", "c3": "C1"},
        {"c1": "A2", "c2": "B2", "c3": "C2"},
        {"c1": "A3", "c2": "B3", "c3": "C3"},
    ]

    tbl = Table(tk_root, columns=cols, data=data, select_unit="cell")
    tbl.pack()
    tk_root.update_idletasks()

    assert tbl.select_unit == "cell"
    tbl.select_cell(0, 1)
    assert tbl.get_selected_cells() == [(0, 1)]

    # Select all cells
    tbl.select_all()
    assert len(tbl.get_selected_cells()) == 9

    # CSV Export
    csv_out = tbl.export_csv()
    assert "c1,c2,c3" in csv_out
    assert "A1,B1,C1" in csv_out

    # Copy to clipboard
    tbl.copy_to_clipboard(fmt="csv")
    tbl.copy_to_clipboard(fmt="tsv")

    tbl.paint_and_blit()


def test_table_styling_hooks_and_rich_editors(tk_root):
    cols = [
        {"id": "id", "title": "ID", "editable": True, "editor": "number", "min_val": 1, "max_val": 100, "step": 1},
        {"id": "category", "title": "Category", "editable": True, "editor": "select", "options": ["Tech", "Finance", "Health"]},
        {"id": "val", "title": "Value", "type": "badge"},
    ]
    data = [
        {"id": 10, "category": "Tech", "val": "Active"},
        {"id": 20, "category": "Finance", "val": "Pending"},
    ]

    def row_styler(r_idx, row):
        return {"bg": "#222233", "fg": "#ffffff"}

    def cell_styler(r_idx, col_id, val):
        if col_id == "val" and val == "Active":
            return {"badge_bg": "#10b981", "badge_fg": "#ffffff"}
        return None

    tbl = Table(
        tk_root,
        columns=cols,
        data=data,
        row_styler=row_styler,
        cell_styler=cell_styler,
    )
    tbl.pack()
    tk_root.update_idletasks()

    # Trigger cell editors
    tbl._start_cell_edit(0, 0, 0)
    tbl._on_editor_closed(0, 0, "10", "15", commit=True)
    assert tbl.get_cell_value(0, "id") == "15"

    tbl._start_cell_edit(0, 1, 0)
    tbl._on_editor_closed(0, 1, "Tech", "Finance", commit=True)
    assert tbl.get_cell_value(0, "category") == "Finance"

    tbl.paint_and_blit()


def test_table_column_interactive_resize(tk_root):
    cols = [
        {"id": "c1", "title": "Col 1", "width": 80},
        {"id": "c2", "title": "Col 2", "width": 100},
    ]
    data = [{"c1": "val1", "c2": "val2"}]

    tbl = Table(tk_root, columns=cols, data=data, width=300, height=200)
    tbl.pack()
    tk_root.update_idletasks()

    view = tbl._view
    s = view._scale_factor

    # 1. Divider hit detection
    divider_idx = view._get_divider_at_x(80.0 * s, tolerance=8.0)
    assert divider_idx == 0

    # 2. Simulate mouse press on divider
    class MockEvent:
        def __init__(self, x, y, state=0):
            self.x = x
            self.y = y
            self.state = state

    press_evt = MockEvent(x=int(80 * s), y=int(10 * s))
    view._on_press(press_evt)
    assert tbl._resizing_col == 0

    # 3. Simulate drag to expand column width by 40px
    drag_evt = MockEvent(x=int(120 * s), y=int(10 * s))
    view._on_drag(drag_evt)
    assert tbl._columns[0]["width"] == 120

    # 4. Simulate release
    release_evt = MockEvent(x=int(120 * s), y=int(10 * s))
    view._on_release(release_evt)
    assert tbl._resizing_col is None
    assert tbl._columns[0]["width"] == 120

    # 5. Auto-fit column double click simulation
    dbl_evt = MockEvent(x=int(120 * s), y=int(10 * s))
    view._on_double_click(dbl_evt)
    assert tbl._columns[0]["width"] > 30

    tbl.paint_and_blit()
    tbl.destroy()


def test_table_selection_contrast_and_theming(tk_root):
    cols = [{"id": "c1", "title": "Node"}, {"id": "c2", "title": "Status"}]
    data = [{"c1": "worker-01", "c2": "HEALTHY"}, {"c1": "worker-02", "c2": "BUSY"}]

    tbl = Table(tk_root, columns=cols, data=data, width=300, height=150)
    tbl.pack()
    tk_root.update_idletasks()

    # Select row 0
    tbl.select_row(0)
    assert 0 in tbl._selected_rows

    # Verify rendering under dark theme
    set_theme("dark")
    tbl.paint_and_blit()

    # Verify rendering under light theme
    set_theme("light")
    tbl.paint_and_blit()

    # Reset
    set_theme("dark")
    tbl.destroy()



