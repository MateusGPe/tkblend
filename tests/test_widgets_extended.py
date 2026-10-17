import sys
import pytest
import tkinter as tk
from tkblend.theme import set_theme
from tkblend.widgets import (
    Table,
    ScrollableFrame,
    VectorScrollbar,
    Slider,
    RangeSlider,
    Progressbar,
    CircularProgress,
    Gauge,
    SegmentedButton,
    Badge,
    Radio,
    Checkbox,
    Switch,
    ComboBox,
    OptionMenu,
    Entry,
    SearchEntry,
    TextBox,
    Button,
    Label,
    Frame,
    Tabview,
)


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


# ==============================================================================
# TABLE TESTS
# ==============================================================================

def test_table_full_lifecycle_and_interactions(root):
    set_theme("dark")
    cols = ["ID", "Name", "Score", "Revenue", "Progress"]
    data = [
        [1, "Alpha", 95, "$1,200", "80%"],
        [2, "Beta", 82, "$3,450", "45%"],
        [3, "Gamma", 98, "$850", "95%"],
        [4, "Delta", None, "$2,100", "60%"],
    ]

    clicked_events = []
    def on_click(row_or_rows, record_or_records):
        clicked_events.append((row_or_rows, record_or_records))

    tbl = Table(
        root,
        columns=cols,
        data=data,
        command=on_click,
        column_weights=[1, 2, 1, 1, 1],
        width=500,
        height=250,
        multi_select=True,
        zebra_striping=True,
    )
    tbl.pack()
    root.update_idletasks()

    assert tbl.inner_bg is not None
    assert tbl.bg_color == tbl.inner_bg
    assert tbl.columns == cols
    assert len(tbl.data) == 4
    assert tbl.multi_select is True
    assert tbl.zebra_striping is True

    # 1. Properties and Color Overrides
    tbl.sort_column = 1
    assert tbl.sort_column == 1
    tbl.sort_ascending = False
    assert tbl.sort_ascending is False
    tbl.command = on_click
    assert tbl.command is on_click

    tbl.table_bg = "#1e1e24"
    assert tbl.table_bg == "#1e1e24"
    tbl.table_fg = "#ffffff"
    assert tbl.table_fg == "#ffffff"
    tbl.header_bg = "#2a2a32"
    assert tbl.header_bg == "#2a2a32"
    tbl.header_fg = "#e0e0e0"
    assert tbl.header_fg == "#e0e0e0"
    tbl.zebra_bg = "#22222a"
    assert tbl.zebra_bg == "#22222a"
    tbl.hover_bg = "#333340"
    assert tbl.hover_bg == "#333340"
    tbl.selected_bg = "#4f46e5"
    assert tbl.selected_bg == "#4f46e5"
    tbl.selected_fg = "#ffffff"
    assert tbl.selected_fg == "#ffffff"
    tbl.border_color = "#444450"
    assert tbl.border_color == "#444450"

    # 2. Selection APIs
    assert tbl.selected_row is None
    assert tbl.selected_rows == []
    assert tbl.get_selected() is None
    assert tbl.get_selected_rows() == []

    tbl.selected_row = 1
    assert tbl.selected_row == 1
    assert tbl.selected_rows == [1]
    assert tbl.get_selected()[1] == "Beta"

    tbl.selected_rows = [0, 2]
    assert tbl.selected_rows == [0, 2]
    assert len(tbl.get_selected_rows()) == 2

    tbl.select_all()
    assert len(tbl.selected_rows) == 4

    tbl.clear_selection()
    assert tbl.selected_rows == []

    # 3. Sorting with diverse values (numbers, currencies, percentages, None)
    # Sort by Revenue (index 3)
    tbl._sort_by_column(3)
    root.update_idletasks()
    assert tbl.sort_column == 3
    assert tbl.sort_ascending is True

    # Sort again -> reverses order
    tbl._sort_by_column(3)
    root.update_idletasks()
    assert tbl.sort_ascending is False

    # Sort by column with None (Score, index 2)
    tbl._sort_by_column(2)
    root.update_idletasks()

    # Sort by Name (index 1, strings)
    tbl._sort_by_column(1)
    root.update_idletasks()

    # 4. Mouse motion, header divider detection, hover
    ev_motion_header = tk.Event()
    ev_motion_header.x = 80
    ev_motion_header.y = 15
    tbl._on_motion(ev_motion_header)

    ev_motion_body = tk.Event()
    ev_motion_body.x = 80
    ev_motion_body.y = 55
    tbl._on_motion(ev_motion_body)
    assert tbl._hovered_row is not None

    ev_leave = tk.Event()
    tbl._on_leave(ev_leave)
    assert tbl._hovered_row is None

    # 5. Row clicking (Single, Ctrl, Shift)
    ev_click = tk.Event()
    ev_click.x = 80
    ev_click.y = 55
    ev_click.state = 0
    tbl._on_button_press(ev_click)
    assert tbl.selected_row is not None

    # Ctrl click
    ev_ctrl_click = tk.Event()
    ev_ctrl_click.x = 80
    ev_ctrl_click.y = 85
    ev_ctrl_click.state = 0x0004
    tbl._on_button_press(ev_ctrl_click)
    assert len(tbl.selected_rows) >= 2

    # Shift click
    ev_shift_click = tk.Event()
    ev_shift_click.x = 80
    ev_shift_click.y = 115
    ev_shift_click.state = 0x0001
    tbl._on_button_press(ev_shift_click)
    assert len(tbl.selected_rows) >= 2

    # Column header sort click via _on_button_press
    ev_hdr_click = tk.Event()
    ev_hdr_click.x = 40
    ev_hdr_click.y = 15
    ev_hdr_click.state = 0
    tbl._on_button_press(ev_hdr_click)

    # 6. Mousewheel and Shift-Mousewheel scrolling
    ev_wheel = tk.Event()
    ev_wheel.delta = -120
    ev_wheel.num = None
    ev_wheel.state = 0
    tbl._on_mousewheel(ev_wheel)

    ev_shift_wheel = tk.Event()
    ev_shift_wheel.delta = -120
    ev_shift_wheel.num = None
    ev_shift_wheel.state = 0x0001
    tbl._on_mousewheel(ev_shift_wheel)
    tbl._on_shift_mousewheel(ev_shift_wheel)

    # Mouse release
    tbl._on_button_release(ev_click)

    # 7. Updating columns and data properties
    tbl.columns = ["ColA", "ColB"]
    assert tbl.columns == ["ColA", "ColB"]
    tbl.data = [["X1", "Y1"], ["X2", "Y2"]]
    assert len(tbl.data) == 2

    # Test multi_select setter disabling
    tbl.multi_select = False
    assert tbl.multi_select is False
    tbl.zebra_striping = False
    assert tbl.zebra_striping is False

    tbl._on_controller_click(10, 10, 1)


def test_table_cell_editing_comprehensive(root):
    set_theme("dark")
    cols = ["Item", "Category", "Quantity", "Custom"]
    data = [
        ["Apple", "Fruit", 10, "A1"],
        ["Banana", "Fruit", 20, "B2"],
        ["Carrot", "Vegetable", 15, "C3"],
    ]

    edit_history = []
    def on_edit(row, col, old_val, new_val):
        edit_history.append((row, col, old_val, new_val))

    tbl = Table(
        root,
        columns=cols,
        data=data,
        editable_columns=[0, 1, 2, 3],
        column_editors={
            1: "combobox",
            3: lambda master, r, c, val, commit, cancel: Entry(master, text=str(val)),
        },
        on_cell_edit=on_edit,
        width=450,
        height=220,
    )
    tbl.pack()
    root.update_idletasks()

    assert tbl.editable_columns == [0, 1, 2, 3]
    assert 1 in tbl.column_editors
    assert tbl.is_column_editable(0) is True
    assert tbl.is_column_editable(1) is True
    assert tbl.is_column_editable(99) is False

    # 1. Start editing text cell (row 0, col 0)
    started = tbl._start_cell_edit(0, 0)
    assert started is True
    assert tbl.is_editing is True
    assert tbl.editing_cell == (0, 0)

    # Commit edit
    if tbl._active_editor_widget is not None:
        tbl._active_editor_widget.delete(0, "end")
        tbl._active_editor_widget.insert(0, "Honeycrisp Apple")
    tbl._commit_cell_edit()
    assert tbl.is_editing is False
    assert tbl.data[0][0] == "Honeycrisp Apple"
    assert len(edit_history) == 1

    # 2. Start editing combobox cell (row 0, col 1)
    started_cb = tbl._start_cell_edit(0, 1)
    assert started_cb is True
    assert tbl.is_editing is True
    tbl._commit_cell_edit()

    # 3. Start editing custom editor cell (row 0, col 3)
    started_custom = tbl._start_cell_edit(0, 3)
    assert started_custom is True
    tbl._dismiss_active_editor()
    assert tbl.is_editing is False

    # 4. Keyboard navigation in editor (Escape and Tab)
    tbl._start_cell_edit(1, 0)
    tbl._cancel_cell_edit()
    assert tbl.is_editing is False

    tbl._start_cell_edit(1, 0)
    tbl._navigate_cell_edit(forward=True, new_val="Advance")
    root.update_idletasks()
    assert tbl.editing_cell == (1, 1)
    tbl._navigate_cell_edit(forward=False)
    root.update_idletasks()
    assert tbl.editing_cell == (1, 0)
    tbl._dismiss_active_editor()

    # Double click cell editing trigger
    ev_double = tk.Event()
    ev_double.x = 60
    ev_double.y = 55
    tbl._on_double_click(ev_double)
    if tbl.is_editing:
        tbl._dismiss_active_editor()


# ==============================================================================
# SCROLLABLE FRAME & VECTOR SCROLLBAR TESTS
# ==============================================================================

def test_scrollable_frame_comprehensive(root):
    set_theme("dark")
    sf = ScrollableFrame(root, width=250, height=180, scrollbar_width=10)
    sf.pack()
    root.update_idletasks()

    # Add enough content to trigger scrolling
    labels = []
    for i in range(25):
        lbl = tk.Label(sf.content, text=f"Item Row #{i}", height=2)
        lbl.pack(fill="x")
        labels.append(lbl)
    root.update_idletasks()

    assert sf.content is not None
    assert sf.scrollbar is not None

    # Hover enter / leave
    sf._on_mouse_enter()
    assert sf._is_hovered_for_scroll is True

    # Mouse wheel event scrolling
    ev_wheel_down = tk.Event()
    ev_wheel_down.delta = -120
    ev_wheel_down.num = 0
    sf._on_mousewheel(ev_wheel_down)

    ev_wheel_up = tk.Event()
    ev_wheel_up.delta = 120
    ev_wheel_up.num = 0
    sf._on_mousewheel(ev_wheel_up)

    # Button-4 and Button-5 simulation for Linux
    ev_b4 = tk.Event()
    ev_b4.delta = 0
    ev_b4.num = 4
    sf._on_mousewheel(ev_b4)

    ev_b5 = tk.Event()
    ev_b5.delta = 0
    ev_b5.num = 5
    sf._on_mousewheel(ev_b5)

    # Step smooth scroll execution
    sf._step_smooth_scroll()

    # Scrollbar move callback with active animation timer
    sf._anim_timer = 9999
    sf._on_scrollbar_move("moveto", 0.5)
    assert sf._anim_timer is None

    # Hover leave
    sf._on_mouse_leave()

    # Theme update
    from tkblend.theme import get_theme
    sf.on_theme_update(get_theme())

    # Destroy with active animation timer
    sf._anim_timer = 9999
    sf.destroy()


def test_vector_scrollbar_api_coverage(root):
    set_theme("dark")
    actions = []
    vs = VectorScrollbar(root, orientation="vertical", command=lambda *a: actions.append(a))
    vs.pack()
    root.update_idletasks()

    # Initial get
    f, l = vs.get()
    assert f == pytest.approx(0.0, abs=0.01)

    # Invalid string parameters to set and on_change
    vs.set("bad", "input")
    vs.on_change("bad_float")

    # Command exception handling
    vs_err = VectorScrollbar(root, command=lambda *a: 1 / 0)
    vs_err.on_change(0.5)
    vs_err.destroy()

    # Set normal range
    vs.set(0.1, 0.5)
    f, l = vs.get()
    assert f == pytest.approx(0.1, abs=0.05)

    # on_change
    vs.on_change(0.5)
    assert len(actions) > 0

    # Auto-hide span >= 0.999
    vs.set(0.0, 1.0)
    assert vs.get_var("--thumb-hidden") == "1"

    vs.destroy()



# ==============================================================================
# SLIDER AND RANGE SLIDER TESTS
# ==============================================================================

def test_slider_full_coverage(root):
    set_theme("dark")
    cmd_calls = []
    var = tk.DoubleVar(value=20.0)

    sl = Slider(
        root,
        from_=10.0,
        to=110.0,
        value=20.0,
        variable=var,
        command=lambda v: cmd_calls.append(v),
    )
    sl.pack()
    root.update_idletasks()

    assert sl.from_ == 10.0
    assert sl.to == 110.0
    assert sl.get() == pytest.approx(20.0, abs=0.5)

    # Set properties
    sl.from_ = 0.0
    sl.to = 200.0
    sl.value = 50.0
    assert sl.value == pytest.approx(50.0, abs=0.5)
    assert var.get() == pytest.approx(50.0, abs=0.5)

    # Variable write trace
    var.set(100.0)
    root.update_idletasks()
    assert sl.get() == pytest.approx(100.0, abs=0.5)

    # on_change hook (native C++ dispatch)
    sl.on_change(0.75)
    assert cmd_calls[-1] == pytest.approx(150.0, abs=0.5)

    # Zero span edge case
    sl.to = sl.from_
    sl.set(10.0)

    sl.destroy()


def test_range_slider_full_coverage(root):
    set_theme("dark")
    cmd_calls = []

    rsl = RangeSlider(
        root,
        from_=0.0,
        to=100.0,
        lower_value=20.0,
        upper_value=80.0,
        command=lambda vals: cmd_calls.append(vals),
    )
    rsl.pack()
    root.update_idletasks()

    assert rsl.from_ == 0.0
    assert rsl.to == 100.0
    low, high = rsl.get()
    assert low == pytest.approx(20.0, abs=0.5)
    assert high == pytest.approx(80.0, abs=0.5)

    # Setters
    rsl.from_ = 10.0
    rsl.to = 200.0
    rsl.lower_value = 30.0
    rsl.upper_value = 150.0
    assert rsl.lower_value == pytest.approx(30.0, abs=0.5)
    assert rsl.upper_value == pytest.approx(150.0, abs=0.5)

    # Inverted values handling
    rsl.set(120.0, 40.0)
    l, h = rsl.get()
    assert l <= h

    # Zero span edge case
    rsl.to = rsl.from_
    rsl.set(10.0, 10.0)

    # on_change hook
    rsl.from_ = 0.0
    rsl.to = 100.0
    rsl.on_change((0.2, 0.8))
    assert len(cmd_calls) > 0
    assert cmd_calls[-1][0] == pytest.approx(20.0, abs=0.5)
    assert cmd_calls[-1][1] == pytest.approx(80.0, abs=0.5)

    rsl.destroy()


# ==============================================================================
# PROGRESSBAR, CIRCULAR PROGRESS & GAUGE TESTS
# ==============================================================================

def test_progressbar_full_coverage(root):
    set_theme("dark")
    var = tk.DoubleVar(value=25.0)
    pb = Progressbar(root, value=25.0, maximum=100.0, variable=var)
    pb.pack()
    root.update_idletasks()

    assert pb.get() == pytest.approx(25.0, abs=0.5)
    assert pb.maximum == 100.0

    # Step wrapping
    pb.maximum = 50.0
    pb.set(45.0)
    pb.step(10.0)
    assert pb.get() < 45.0

    # Variable change
    var.set(30.0)
    root.update_idletasks()
    assert pb.get() == pytest.approx(30.0, abs=0.5)

    pb.destroy()


def test_circular_progress_and_gauge_full_coverage(root):
    set_theme("dark")
    var = tk.DoubleVar(value=40.0)
    cp = CircularProgress(
        root,
        value=40.0,
        min_value=0.0,
        max_value=100.0,
        title="Battery",
        variable=var,
        show_value=True,
    )
    cp.pack()
    root.update_idletasks()

    assert cp.title == "Battery"
    assert cp.value == pytest.approx(40.0, abs=0.5)

    cp.title = "Power"
    assert cp.title == "Power"
    cp.title = None
    assert cp.title is None

    cp.step(15.0)
    assert cp.get() == pytest.approx(55.0, abs=0.5)

    var.set(70.0)
    root.update_idletasks()
    assert cp.get() == pytest.approx(70.0, abs=0.5)

    cp.destroy()

    # Gauge
    gg = Gauge(root, value=60.0, min_value=0.0, max_value=120.0, title="RPM", unit="k")
    gg.pack()
    root.update_idletasks()
    assert gg.get() == pytest.approx(60.0, abs=0.5)
    gg.step(10.0)
    assert gg.get() == pytest.approx(70.0, abs=0.5)
    gg.destroy()


# ==============================================================================
# SEGMENTED BUTTON TESTS
# ==============================================================================

def test_segmented_button_full_coverage(root):
    set_theme("dark")
    cmd_calls = []
    var = tk.StringVar(value="Two")

    sb = SegmentedButton(
        root,
        values=["One", "Two", "Three"],
        value="Two",
        variable=var,
        command=lambda v: cmd_calls.append(v),
    )
    sb.pack()
    root.update_idletasks()

    assert sb.values == ["One", "Two", "Three"]
    assert sb.selected_index == 1
    assert sb.selected_value == "Two"
    assert sb.get() == "Two"

    # Selection by value
    sb.set("Three")
    assert sb.selected_index == 2
    assert var.get() == "Three"

    # Selection by index
    sb.selected_index = 0
    assert sb.selected_value == "One"

    # on_change hook
    sb.on_change(2)
    assert sb.selected_value == "Three"

    # Dynamic values update
    sb.values = ["A", "B"]
    assert sb.values == ["A", "B"]

    # Empty values
    sb.values = []
    assert sb.selected_index == -1
    assert sb.selected_value == ""

    sb.destroy()


# ==============================================================================
# BADGE TESTS
# ==============================================================================

def test_badge_extended_coverage(root):
    set_theme("dark")
    bg = Badge(root, text="Verified", variant="success", padding_x=10)
    bg.pack()
    root.update_idletasks()

    assert bg.text == "Verified"
    assert bg.variant == "success"
    assert bg.padding_x == 10

    # Variant switching
    bg.variant = "warning"
    assert bg.variant == "warning"
    bg.variant = "default"
    assert bg.variant == "default"

    bg.padding_x = 12
    assert bg.padding_x == 12

    bg.set_text("Updated")
    assert bg.text == "Updated"

    bg.destroy()


# ==============================================================================
# RADIO, CHECKBOX & SWITCH TESTS
# ==============================================================================

def test_radio_extended_coverage(root):
    set_theme("dark")
    var = tk.StringVar(value="opt1")
    cmd_calls = []

    r1 = Radio(root, text="Option 1", value="opt1", variable=var, command=lambda v: cmd_calls.append(v))
    r2 = Radio(root, text="Option 2", value="opt2", variable=var, command=lambda v: cmd_calls.append(v))
    r1.pack()
    r2.pack()
    root.update_idletasks()

    assert r1.is_checked is True
    assert r2.is_checked is False

    r2.select()
    assert var.get() == "opt2"
    assert r1.is_checked is False
    assert r2.is_checked is True
    assert "opt2" in cmd_calls

    # Variable change
    var.set("opt1")
    root.update_idletasks()
    assert r1.is_checked is True
    assert r2.is_checked is False

    # on_change hook
    r2.on_change(True)
    assert var.get() == "opt2"

    r1.destroy()
    r2.destroy()


def test_checkbox_and_switch_extended_coverage(root):
    set_theme("dark")
    cmd_calls = []
    var = tk.BooleanVar(value=True)

    cb = Checkbox(root, text="Accept Terms", variable=var, command=lambda v: cmd_calls.append(v))
    cb.pack()
    root.update_idletasks()

    assert cb.is_checked is True
    assert cb.checked is True

    cb.toggle()
    assert cb.is_checked is False
    assert var.get() is False

    cb.on_change(True)
    assert cb.is_checked is True

    cb.destroy()

    sw_calls = []
    sw_var = tk.BooleanVar(value=False)
    sw = Switch(root, text="Dark Mode", variable=sw_var, checked=False, command=lambda v: sw_calls.append(v))
    sw.pack()
    root.update_idletasks()

    sw.on_change(True)
    assert sw_calls == [True]
    assert sw_var.get() is True
    assert sw.is_checked is True
    sw.toggle()
    assert sw.is_checked is False
    sw.destroy()


# ==============================================================================
# TEXTBOX AND ENTRY TESTS
# ==============================================================================

def test_entry_and_textbox_extended_coverage(root):
    set_theme("dark")
    var = tk.StringVar(value="Initial")

    ent = Entry(root, placeholder="Type something...", text="Initial", variable=var, auto_fit=True)
    ent.pack()
    root.update_idletasks()

    assert ent.text == "Initial"
    assert ent.get() == "Initial"

    # Placeholder display on clear
    ent.delete(0, "end")
    assert ent.placeholder == "Type something..."

    ent.insert(0, "New Value")
    assert ent.text == "New Value"
    assert var.get() == "New Value"

    ent.placeholder = "Enter keyword..."
    assert ent.placeholder == "Enter keyword..."

    ent.set("Reset Text")
    assert ent.get() == "Reset Text"

    # Focus in/out hooks
    ent._on_entry_focus_in()
    ent._on_entry_focus_out()

    ent.destroy()

    # TextBox
    tb = TextBox(root, width=250, height=120)
    tb.pack()
    root.update_idletasks()

    tb.insert("1.0", "Hello\nWorld")
    content = tb.get("1.0", "end-1c")
    assert "Hello" in content

    tb.delete("1.0", "end")
    assert tb.get("1.0", "end-1c") == ""

    tb._on_container_click()
    tb._on_text_focus_in()
    tb._on_text_focus_out()

    tb.destroy()


# ==============================================================================
# COMBOBOX TESTS
# ==============================================================================

def test_combobox_extended_coverage(root):
    set_theme("dark")
    cmd_calls = []
    combo = ComboBox(
        root,
        values=["Python", "C++", "Rust", "Go"],
        value="Python",
        command=lambda v: cmd_calls.append(v),
    )
    combo.pack()
    root.update_idletasks()

    assert combo.get() == "Python"
    assert combo.values == ["Python", "C++", "Rust", "Go"]

    # Open popup
    combo.on_click(10, 10, 1)
    root.update_idletasks()
    assert combo._popup is not None

    # Keyboard interactions on popup
    combo._popup._on_key_nav(1)
    assert combo._popup._highlighted_idx >= 0
    combo._popup._on_key_nav(-1)
    combo._popup._on_key_select()

    # Check updated selection
    assert combo.get() == "Python"

    # Close popup
    if combo._popup is not None:
        combo._popup.dismiss()
    assert combo._popup is None

    # Properties
    combo.values = ["Alpha", "Beta"]
    assert combo.values == ["Alpha", "Beta"]
    combo.value = "Beta"
    assert combo.value == "Beta"
    assert combo.get() == "Beta"
    combo.command = lambda v: None
    combo.state = "disabled"
    assert combo.is_disabled is True
    combo.on_click(10, 10, 1)  # should return early
    assert combo._popup is None
    combo.destroy()

    # Test popup scrolling with long list
    combo2 = ComboBox(root, values=[f"Option {i}" for i in range(30)], max_visible_items=5)
    combo2.pack()
    root.update_idletasks()
    combo2.on_click(10, 10, 1)
    root.update_idletasks()
    pop = combo2._popup
    assert pop is not None
    assert pop._needs_scroll is True

    # Mousewheel scrolling
    ev_mw = tk.Event()
    ev_mw.delta = -120
    pop._on_mousewheel(ev_mw)

    ev_mw_up = tk.Event()
    ev_mw_up.delta = 120
    pop._on_mousewheel(ev_mw_up)

    ev_b4 = tk.Event()
    ev_b4.num = 4
    pop._on_mousewheel(ev_b4)

    ev_b5 = tk.Event()
    ev_b5.num = 5
    pop._on_mousewheel(ev_b5)

    # Scrollbar move
    pop._on_scrollbar_move("moveto", 0.5)
    pop._on_scrollbar_move("scroll", 2, "units")

    # Item highlight with scroll
    pop._set_highlight(3, scroll_into_view=True)
    assert pop._highlighted_idx == 3

    # Mousewheel scrolling with small delta
    ev_mw_small = tk.Event()
    ev_mw_small.delta = 1
    pop._on_mousewheel(ev_mw_small)

    ev_mw_small_neg = tk.Event()
    ev_mw_small_neg.delta = -1
    pop._on_mousewheel(ev_mw_small_neg)

    # Master configure dismiss
    ev_m_conf = tk.Event()
    ev_m_conf.widget = pop._toplevel_master
    pop._on_master_configure(ev_m_conf)
    assert combo2._popup is None

    # Toggle open/close via anchor click
    combo2.on_click(10, 10, 1)
    assert combo2._popup is not None
    combo2.on_click(10, 10, 1)
    assert combo2._popup is None

    # Values setter updates
    combo2.values = ["Updated 1", "Updated 2"]
    assert combo2.values == ["Updated 1", "Updated 2"]
    combo2.value = "Updated 2"
    assert combo2.value == "Updated 2"

    combo2.destroy()



# ==============================================================================
# BUTTON, LABEL, FRAME, TABVIEW, SEARCHENTRY EXTENDED TESTS
# ==============================================================================

def test_button_label_frame_tabview_extended(root):
    set_theme("dark")

    # 1. Button
    invoked = []
    btn = Button(root, text="Action", command=lambda: invoked.append(True))
    btn.pack()
    root.update_idletasks()

    assert btn.padding_x >= 0
    assert btn.padding_y >= 0
    btn.padding_x = 16
    assert btn.padding_x == 16
    btn.padding_y = 8
    assert btn.padding_y == 8

    btn.variant = "danger"
    assert btn.variant == "danger"
    btn.variant = "default"
    assert btn.variant == "default"

    btn.invoke()
    assert len(invoked) == 1
    btn.destroy()

    # 2. Label
    lbl = Label(root, text="Info Label", variant="default")
    lbl.pack()
    root.update_idletasks()

    assert lbl.padding_x >= 0
    assert lbl.padding_y >= 0
    lbl.padding_x = 10
    assert lbl.padding_x == 10
    lbl.padding_y = 6
    assert lbl.padding_y == 6

    lbl.variant = "warning"
    assert lbl.variant == "warning"
    lbl.variant = "default"
    assert lbl.variant == "default"
    lbl.destroy()

    # 3. Frame
    frm = Frame(root, width=200, height=150, corner_radius=10.0, border_width=1.0)
    frm.pack()
    root.update_idletasks()

    assert frm.corner_radius == 10.0
    assert frm.border_width == 1.0
    frm.corner_radius = 16.0
    assert frm.corner_radius == 16.0
    frm.border_width = 2.0
    assert frm.border_width == 2.0

    frm.set_inner_bg("#2b2b36")
    assert frm.inner_bg.startswith("#")
    frm.destroy()

    # 4. Tabview
    tv = Tabview(root, width=300, height=200)
    tv.pack()
    root.update_idletasks()

    p1 = tv.add("First")
    p2 = tv.add("Second")
    # Duplicate add returns existing frame
    p1_dup = tv.add("First")
    assert p1 is p1_dup

    assert tv.get() == "First"
    tv.set("Second")
    assert tv.get() == "Second"

    tv._on_segment_changed("First")
    assert tv.get() == "First"

    tv.bg_color = "#202028"
    assert tv.bg_color.startswith("#")
    tv.destroy()

    # 5. SearchEntry
    se = SearchEntry(root, placeholder="Search documentation...")
    se.pack()
    root.update_idletasks()

    pad_l, pad_r = se._calc_padding()
    assert pad_l > pad_r  # Left padding is wider to clear the search magnifying glass icon
    se.text = "Query string"
    assert se.text == "Query string"
    se.destroy()


def test_table_scrollbar_interactions_and_drag(root):
    set_theme("dark")
    cols = ["Col A", "Col B", "Col C", "Col D", "Col E"]
    # Many rows and columns to force both vertical and horizontal scrollbars
    data = [[f"R{r}C{c} Value" for c in range(5)] for r in range(40)]

    tbl = Table(
        root,
        columns=cols,
        data=data,
        width=300,
        height=200,
    )
    tbl.pack()
    root.update_idletasks()

    w, h = tbl._get_size()
    v_needed, vx, vy, vw, vh, track_h = tbl._get_vbar_bounds(w, h)
    h_needed, hx, hy, hw, hh, track_w = tbl._get_hbar_bounds(w, h)

    assert v_needed is True

    # 1. Drag vertical scrollbar
    ev_v_press = tk.Event()
    ev_v_press.x = int(w - 6)
    ev_v_press.y = int(vy + 10)
    tbl._on_button_press(ev_v_press)
    assert tbl._vbar_dragging is True

    ev_v_drag = tk.Event()
    ev_v_drag.x = int(w - 6)
    ev_v_drag.y = int(vy + 30)
    tbl._on_drag(ev_v_drag)
    assert tbl._scroll_y > 0

    tbl._on_button_release(ev_v_drag)
    assert tbl._vbar_dragging is False

    # 2. Track click (jump) vertical
    ev_v_jump = tk.Event()
    ev_v_jump.x = int(w - 6)
    ev_v_jump.y = int(h - 20)  # past the thumb
    tbl._on_button_press(ev_v_jump)

    # 3. Drag horizontal scrollbar if needed
    if h_needed:
        ev_h_press = tk.Event()
        ev_h_press.x = int(hx + 5)
        ev_h_press.y = int(h - 6)
        tbl._on_button_press(ev_h_press)

        ev_h_drag = tk.Event()
        ev_h_drag.x = int(hx + 25)
        ev_h_drag.y = int(h - 6)
        tbl._on_drag(ev_h_drag)

        tbl._on_button_release(ev_h_drag)

    # 4. Column resize drag
    tbl._calc_column_widths_for(w)
    ev_divider_press = tk.Event()
    ev_divider_press.x = 80
    ev_divider_press.y = 15
    tbl._resizing_col_idx = 0
    tbl._resize_start_x = 80
    tbl._resize_start_w = 80

    ev_divider_drag = tk.Event()
    ev_divider_drag.x = 120
    tbl._on_drag(ev_divider_drag)
    assert tbl._col_widths[0] == 120

    tbl._on_button_release(ev_divider_drag)
    assert tbl._resizing_col_idx is None

    tbl.destroy()


def test_table_extended_apis_and_events(root):
    data = [
        ["1", "Alice", 100.5, "$20"],
        ["2", "Bob", 50.2, "$10"],
        ["3", "Charlie", 75.0, "$15"],
    ]
    tbl = Table(
        root,
        columns=["ID", "Name", "Score", "Price"],
        data=data,
        multi_select=True,
        column_weights=[1, 2, 1, 1],
        column_editors={"Name": "entry", "Score": "entry"},
    )
    tbl.pack(fill="both", expand=True)
    root.update_idletasks()

    # Column weights calculation
    tbl._calc_column_widths_for(500)
    assert len(tbl._col_widths) == 4

    # Color overrides
    tbl.table_bg = "#112233"
    assert tbl.table_bg == "#112233"
    tbl.table_fg = "#ffffff"
    assert tbl.table_fg == "#ffffff"
    tbl.header_bg = "#223344"
    assert tbl.header_bg == "#223344"
    tbl.header_fg = "#ffffaa"
    assert tbl.header_fg == "#ffffaa"
    tbl.zebra_bg = "#152535"
    assert tbl.zebra_bg == "#152535"
    tbl.hover_bg = "#253545"
    assert tbl.hover_bg == "#253545"
    tbl.selected_bg = "#354555"
    assert tbl.selected_bg == "#354555"
    tbl.selected_fg = "#ffffbb"
    assert tbl.selected_fg == "#ffffbb"
    tbl.border_color = "#455565"
    assert tbl.border_color == "#455565"

    # on_cell_edit callback
    edits = []
    tbl.on_cell_edit = lambda r, c, o, n: edits.append((r, c, o, n))
    assert tbl.on_cell_edit is not None

    # Selection methods
    tbl.selected_row = 0
    assert tbl.get_selected() == ["1", "Alice", 100.5, "$20"]
    tbl.select_all()
    assert len(tbl.get_selected_rows()) == 3
    # Turn off multi_select with multiple selected (covers lines 1215-1216)
    tbl.multi_select = False
    assert len(tbl.selected_rows) == 1
    # Clear selection via selected_row = None (covers line 1193)
    tbl.selected_row = None
    assert tbl.selected_row is None
    tbl.multi_select = True
    tbl.select_all()
    tbl.clear_selection()
    assert tbl.get_selected() is None
    assert tbl.get_selected_rows() == []

    # Header clicks for sorting
    w, h = tbl._get_size()
    curr_x = 10
    for col_idx in range(len(tbl._columns)):
        ev = tk.Event()
        ev.x = curr_x
        ev.y = int(tbl._header_h // 2)
        tbl._on_button_press(ev)
        # Click again to reverse sort
        tbl._on_button_press(ev)
        curr_x += tbl._col_widths[col_idx]

    # Mousewheel scrolling (Linux buttons 4/5, Darwin delta, Shift)
    ev_mw = tk.Event()
    ev_mw.delta = -120
    ev_mw.state = 0
    tbl._on_mousewheel(ev_mw)

    ev_mw_shift = tk.Event()
    ev_mw_shift.delta = 120
    ev_mw_shift.state = 0x0001
    tbl._on_mousewheel(ev_mw_shift)

    ev_mw_linux5 = tk.Event()
    ev_mw_linux5.num = 5
    ev_mw_linux5.state = 0
    tbl._on_mousewheel(ev_mw_linux5)

    ev_mw_linux4 = tk.Event()
    ev_mw_linux4.num = 4
    ev_mw_linux4.state = 0
    tbl._on_mousewheel(ev_mw_linux4)

    # Shift mousewheel
    tbl._on_shift_mousewheel(ev_mw_linux5)
    tbl._on_shift_mousewheel(ev_mw_linux4)

    # Double click to edit
    ev_dc = tk.Event()
    ev_dc.x = tbl._col_widths[0] + 15
    ev_dc.y = int(tbl._header_h + tbl._row_h // 2)
    tbl._on_double_click(ev_dc)

    # Test key bindings in active editor
    if tbl._active_editor_widget:
        # Enter commits
        tbl._active_editor_widget.event_generate("<Return>")

    # Float cell edit & commit
    tbl.start_edit(0, 2)
    tbl._commit_cell_edit("150.75")
    assert tbl._data[0][2] == pytest.approx(150.75)

    # Validation rejection
    tbl.on_cell_edit = lambda r, c, o, n: False
    tbl.start_edit(0, 1)
    res = tbl._commit_cell_edit("RejectedName")
    assert res is False

    # Validation exception handling
    tbl.on_cell_edit = lambda r, c, o, n: 1 / 0
    tbl.start_edit(0, 1)
    res = tbl._commit_cell_edit("ErrorName")
    assert res is False
    tbl.on_cell_edit = None

    # Cancel edit
    tbl.start_edit(0, 1)
    tbl._cancel_cell_edit()
    assert tbl._active_editor is None

    # Navigate cell edit forward and backward
    tbl.start_edit(0, 1)
    tbl._navigate_cell_edit(forward=True, new_val="NextCellVal")
    tbl.start_edit(0, 1)
    tbl._navigate_cell_edit(forward=False, new_val="PrevCellVal")

    # Trigger theme change with active editor
    tbl.start_edit(0, 1)
    from tkblend.theme import get_palette
    tbl._on_theme_changed(get_palette())

    # Configure event
    tbl.start_edit(0, 1)
    ev_cfg = tk.Event()
    tbl._on_configure(ev_cfg)

    # Key edit when no editor is currently active
    tbl._dismiss_active_editor()
    tbl._last_clicked_row = 1
    tbl._on_key_edit(tk.Event())
    assert tbl._active_editor is not None

    tbl.destroy()



def test_textbox_and_entry_advanced_methods(root):
    from tkblend.theme import get_palette
    # 1. Disabled entry & property access
    entry_dis = Entry(root, placeholder="Type here...", state="disabled")
    entry_dis.pack()
    root.update_idletasks()
    assert entry_dis.entry is not None
    assert entry_dis.entry_widget is not None

    entry_dis.configure(state="normal")
    assert not entry_dis.is_disabled
    entry_dis.configure(state="disabled")
    assert entry_dis.is_disabled
    entry_dis.configure(font=("Helvetica", 13, "bold"))

    entry_dis._on_entry_key_release(None)
    entry_dis.on_theme_update(get_palette())
    entry_dis.destroy()

    # 2. Disabled TextBox & property access
    tb_dis = TextBox(root, state="disabled")
    tb_dis.pack()
    root.update_idletasks()
    assert tb_dis.text_widget is not None

    tb_dis.configure(state="normal")
    assert not tb_dis.is_disabled
    tb_dis.configure(state="disabled")
    assert tb_dis.is_disabled
    tb_dis.configure(font=("Helvetica", 14))

    tb_dis._on_container_click(None)
    tb_dis.on_theme_update(get_palette())
    tb_dis.destroy()


