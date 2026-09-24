"""
Tests for the fully-featured Table vector widget.
"""

import pytest
import tkinter as tk
import tkblend as tb


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_table_initialization_and_properties(root):
    cols = [
        {"id": "id", "title": "ID", "width": 60, "align": "center"},
        {"id": "name", "title": "Host Name", "width": 120, "editable": True},
        {"id": "status", "title": "Status", "width": 80, "type": "badge", "badge_colors": {"Active": "#10b981", "Offline": "#ef4444"}},
        {"id": "cpu", "title": "CPU %", "width": 90, "type": "progress"},
    ]
    data = [
        {"id": 1, "name": "node-01", "status": "Active", "cpu": "45.0%"},
        {"id": 2, "name": "node-02", "status": "Offline", "cpu": "12.5%"},
        {"id": 3, "name": "node-03", "status": "Active", "cpu": "89.0%"},
    ]
    table = tb.Table(root, columns=cols, data=data, select_mode="extended")
    root.update_idletasks()

    assert len(table._data) == 3
    assert len(table._columns) == 4
    assert table.bg_color is not None
    assert table.get_selected_index() is None


def test_table_sorting(root):
    cols = [
        {"id": "id", "title": "ID", "width": 50},
        {"id": "score", "title": "Score", "width": 60},
    ]
    data = [
        {"id": 1, "score": "95.5%"},
        {"id": 2, "score": "20.0%"},
        {"id": 3, "score": "80.0%"},
    ]
    table = tb.Table(root, columns=cols, data=data)

    # Sort score ascending
    table.sort_by(1, descending=False)
    assert table._data[0]["id"] == 2
    assert table._data[1]["id"] == 3
    assert table._data[2]["id"] == 1

    # Sort score descending
    table.sort_by(1, descending=True)
    assert table._data[0]["id"] == 1
    assert table._data[1]["id"] == 3
    assert table._data[2]["id"] == 2


def test_table_selection_modes(root):
    data = [{"id": i, "name": f"Item {i}"} for i in range(5)]
    table = tb.Table(root, data=data, select_mode="extended")

    # Single selection
    table.set_selection(2)
    assert table.get_selected_index() == 2
    assert table.get_selected_indices() == [2]
    assert table.get_selected_row()["name"] == "Item 2"
    assert len(table.get_selected_rows()) == 1

    # Multi selection
    table.set_selection([1, 3, 4])
    assert table.get_selected_indices() == [1, 3, 4]
    assert len(table.get_selected_rows()) == 3

    # Select all & clear
    table.select_all()
    assert len(table.get_selected_indices()) == 5
    table.clear_selection()
    assert table.get_selected_indices() == []


def test_table_filtering(root):
    data = [
        {"id": 1, "name": "Alpha Server", "region": "US-East"},
        {"id": 2, "name": "Beta Node", "region": "EU-West"},
        {"id": 3, "name": "Gamma Cluster", "region": "US-West"},
        {"id": 4, "name": "Alpha DB", "region": "AP-East"},
    ]
    table = tb.Table(root, data=data)
    assert len(table.get_filtered_data()) == 4

    # Substring filter
    table.filter_by("Alpha")
    filtered = table.get_filtered_data()
    assert len(filtered) == 2
    assert filtered[0]["name"] == "Alpha Server"
    assert filtered[1]["name"] == "Alpha DB"

    # Custom predicate filter
    table.filter_by(lambda row: "US" in row.get("region", ""))
    filtered = table.get_filtered_data()
    assert len(filtered) == 2
    assert filtered[0]["name"] == "Alpha Server"
    assert filtered[1]["name"] == "Gamma Cluster"

    # Clear filter
    table.clear_filter()
    assert len(table.get_filtered_data()) == 4


def test_table_pagination(root):
    data = [{"id": i, "val": f"v{i}"} for i in range(25)]
    table = tb.Table(root, data=data, pagination=True, page_size=10)

    assert table.get_total_pages() == 3
    assert table.get_current_page() == 0
    assert len(table._get_visible_data()) == 10

    table.next_page()
    assert table.get_current_page() == 1
    assert table._get_visible_data()[0]["id"] == 10

    table.next_page()
    assert table.get_current_page() == 2
    assert len(table._get_visible_data()) == 5

    table.prev_page()
    assert table.get_current_page() == 1

    table.set_page(0)
    assert table.get_current_page() == 0


def test_table_column_resizing_and_autofit(root):
    cols = [
        {"id": "short", "title": "S", "width": 50, "min_width": 30},
        {"id": "long", "title": "A Very Long Description Column Header", "width": 50},
    ]
    data = [
        {"short": "a", "long": "Short"},
        {"short": "b", "long": "This is a significantly longer string value that needs auto-fit space"},
    ]
    table = tb.Table(root, columns=cols, data=data)

    table.auto_fit_column(1)
    # Width of column 1 should expand beyond 50
    assert table._columns[1]["width"] > 100

    table.auto_fit_all_columns()
    assert table._columns[0]["width"] >= 30


def test_table_cell_value_and_edit_callback(root):
    edited = []

    def on_cell_edit(row_idx, col_id, old_v, new_v):
        edited.append((row_idx, col_id, old_v, new_v))

    cols = [
        {"id": "name", "title": "Name", "editable": True},
        {"id": "active", "title": "Active", "type": "checkbox"},
    ]
    data = [
        {"name": "Alice", "active": True},
        {"name": "Bob", "active": False},
    ]
    table = tb.Table(root, columns=cols, data=data, on_cell_edit=on_cell_edit)

    # Set and get cell value
    table.set_cell_value(0, "name", "Alicia")
    assert table.get_cell_value(0, "name") == "Alicia"

    # In-place editor closed simulate
    table._on_editor_closed(1, 0, "Bob", "Robert", commit=True)
    assert table.get_cell_value(1, "name") == "Robert"
    assert len(edited) == 1
    assert edited[0] == (1, "name", "Bob", "Robert")


def test_table_custom_callable_renderer(root):
    rendered_calls = []

    def my_renderer(surface, x, y, w, h, val, is_sel, theme):
        rendered_calls.append((x, y, w, h, val))

    cols = [
        {"id": "custom", "title": "Custom", "renderer": my_renderer},
    ]
    data = [
        {"custom": "test_render"},
    ]
    table = tb.Table(root, columns=cols, data=data, width=300, height=200)
    root.update_idletasks()
    table._view.render()

    assert len(rendered_calls) >= 1
    assert rendered_calls[0][4] == "test_render"


def test_table_clipboard_tsv_generation(root):
    cols = [
        {"id": "id", "title": "ID"},
        {"id": "name", "title": "Name"},
    ]
    data = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
    ]
    table = tb.Table(root, columns=cols, data=data)
    table.set_selection(0)
    # Clipboard call should format selected row without crashing
    table.copy_to_clipboard()


def test_table_scrolling_and_sticky_header(root):
    cols = [
        {"id": "id", "title": "ID", "width": 60},
        {"id": "name", "title": "Name", "width": 120},
    ]
    data = [{"id": i, "name": f"Item {i}"} for i in range(100)]
    table = tb.Table(root, columns=cols, data=data, width=300, height=200)
    root.update_idletasks()

    # Scroll to the bottom end
    table._on_vscroll("moveto", "1.0")
    assert table._scroll_y > 0
    # Rendering should succeed without exception
    table._view.render()



def test_treeview_alias(root):
    assert tb.Treeview is tb.Table
    tv = tb.Treeview(root, columns=[{"id": "id", "title": "ID"}, {"id": "name", "title": "Name"}], data=[[1, "Alice"], [2, "Bob"]])
    tv.render()
    assert tv.row_count == 2
    tv.destroy()

