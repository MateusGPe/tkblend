"""
Tests for new vector widgets: Tabview, ScrollableFrame, TextBox, Table, ComboBox, OptionMenu, SegmentedButton, VectorIcon, IconLabel.
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


def test_tabview(root):
    tabview = tb.Tabview(root, width=300, height=200)
    tab1 = tabview.add("Overview")
    tab2 = tabview.add("Settings")
    assert tabview.get() == "Overview"
    assert tabview.tab("Overview") == tab1
    assert tabview.tab("Settings") == tab2

    tabview.set("Settings")
    assert tabview.get() == "Settings"

    tabview.delete("Overview")
    assert tabview.get() == "Settings"
    assert "Overview" not in tabview._tabs


def test_scrollable_frame(root):
    sf = tb.ScrollableFrame(root, width=200, height=200, orientation="vertical")
    inner = sf.scrollable_frame
    btn = tb.Button(inner, text="Scroll Child")
    btn.pack()
    root.update_idletasks()
    assert sf.winfo_exists()


def test_textbox(root):
    tb_widget = tb.TextBox(root, placeholder_text="Type something...")
    assert tb_widget.get() == ""
    tb_widget.insert("1.0", "Hello Blend2D")
    assert "Hello Blend2D" in tb_widget.get()
    tb_widget.clear()
    assert tb_widget.get() == ""


def test_option_menu(root):
    opt = tb.OptionMenu(root, values=["Alpha", "Beta", "Gamma"], selected_value="Alpha")
    assert opt.get() == "Alpha"
    opt.set("Beta")
    assert opt.get() == "Beta"
    opt.configure_values(["X", "Y", "Z"])
    assert opt.get() == "X"


def test_combobox(root):
    cb = tb.ComboBox(root, values=["Option A", "Option B"])
    assert cb.get() == "Option A"
    cb.set("Custom Typed Value")
    assert cb.get() == "Custom Typed Value"


def test_segmented_button(root):
    sb = tb.SegmentedButton(root, values=["Day", "Week", "Month"])
    assert sb.get() == "Day"
    sb.set("Week")
    assert sb.get() == "Week"


def test_table(root):
    cols = [
        {"id": "id", "title": "ID", "width": 50},
        {"id": "name", "title": "Name", "width": 100},
        {"id": "score", "title": "Score", "width": 60},
    ]
    data = [
        {"id": 1, "name": "Alice", "score": 95},
        {"id": 2, "name": "Bob", "score": 82},
        {"id": 3, "name": "Charlie", "score": 90},
    ]
    table = tb.Table(root, columns=cols, data=data)
    assert len(table._data) == 3

    # Sorting
    table.sort_by(2, descending=True)  # Sort by score desc
    assert table._data[0]["name"] == "Alice"
    assert table._data[1]["name"] == "Charlie"
    assert table._data[2]["name"] == "Bob"

    # Selection
    table.set_selection(1)
    assert table.get_selected_index() == 1
    assert table.get_selected_row()["name"] == "Charlie"

    # Insert & Delete
    table.insert_row({"id": 4, "name": "Dave", "score": 88})
    assert len(table._data) == 4
    table.delete_row(0)
    assert len(table._data) == 3


def test_vector_icons_and_labels(root):
    icon = tb.VectorIcon(root, icon_name="checkmark")
    icon.icon_name = "chevron_down"
    assert icon.icon_name == "chevron_down"

    lbl = tb.IconLabel(root, text="Status", icon="dot")
    lbl.set_text("Updated Status")
    assert lbl._text == "Updated Status"


def test_option_menu_and_combobox_popup_lifecycle(root):
    root.deiconify()
    root.geometry("400x400+100+100")
    root.update_idletasks()

    opt = tb.OptionMenu(root, values=["Option 1", "Option 2"])
    opt.pack()
    cb = tb.ComboBox(root, values=["Choice A", "Choice B"])
    cb.pack()
    root.update_idletasks()

    # Open OptionMenu popup
    opt._open_popup()
    assert opt._is_open is True
    assert opt._popup is not None
    assert opt._popup.winfo_exists()
    assert opt._popup.winfo_viewable()
    opt._close_popup()
    assert opt._is_open is False
    assert opt._popup is None

    # Open ComboBox popup
    cb._open_popup()
    assert cb._is_open is True
    assert cb._popup is not None
    assert cb._popup.winfo_exists()
    assert cb._popup.winfo_viewable()
    cb._close_popup()
    assert cb._is_open is False
    assert cb._popup is None
