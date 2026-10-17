import tkinter as tk
import pytest
import tkblend as tb
from tkblend import (
    Button,
    Switch,
    Checkbox,
    Radio,
    Slider,
    Progressbar,
    Badge,
    Card,
    Label,
    Frame,
    CircularProgress,
    Gauge,
    SegmentedButton,
    RangeSlider,
    Sparkline,
    ComboBox,
    OptionMenu,
    Entry,
    SearchEntry,
    TextBox,
    ScrollableFrame,
    VectorScrollbar,
    Tabview,
    Table,
    set_theme,
    get_theme,
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


def test_button_widget(root):
    set_theme("dark")
    clicked = []
    btn = Button(root, text="Click", command=lambda: clicked.append(True), width=120, height=36)
    btn.pack()
    root.update_idletasks()

    assert btn.text == "Click"
    assert btn.widget_class == "button"
    btn.invoke()
    assert len(clicked) == 1

    btn.text = "Updated"
    assert btn.text == "Updated"

    # Variant tests
    assert btn.variant == "default"
    btn.variant = "primary"
    assert btn.variant == "primary"
    assert btn.has_class("btn-primary")

    btn.variant = "outline"
    assert btn.variant == "outline"
    assert not btn.has_class("btn-primary")
    assert btn.has_class("btn-outline")

    btn2 = Button(root, text="Tonal", variant="tonal")
    assert btn2.variant == "tonal"
    assert btn2.has_class("btn-tonal")
    btn2.destroy()


def test_switch_widget(root):
    set_theme("dark")
    sw_var = tk.BooleanVar(value=False)
    sw = Switch(root, text="Toggle", variable=sw_var, width=100, height=30)
    sw.pack()
    root.update_idletasks()

    assert not sw.is_checked
    sw.toggle()
    assert sw.is_checked
    assert sw_var.get() is True

    sw.toggle()
    assert not sw.is_checked
    assert sw_var.get() is False
    sw.destroy()

    # Test checked=True keyword argument and 1-argument callback
    received_checked = []
    def on_toggle_arg(val: bool):
        received_checked.append(val)

    sw2 = Switch(root, text="Toggle 2", checked=True, command=on_toggle_arg)
    assert sw2.checked is True
    assert sw2.is_checked is True
    sw2.toggle()
    assert received_checked == [False]
    assert sw2.checked is False

    # Test configure and __setitem__
    sw2.configure(checked=True)
    assert sw2.checked is True
    sw2["checked"] = False
    assert sw2.checked is False
    sw2.destroy()


def test_checkbox_widget(root):
    set_theme("dark")
    cb_var = tk.BooleanVar(value=True)
    cb = Checkbox(root, text="Agree", variable=cb_var, width=120, height=30)
    cb.pack()
    root.update_idletasks()

    assert cb.is_checked
    cb.toggle()
    assert not cb.is_checked
    assert cb_var.get() is False
    cb.destroy()

    # Test checked=True keyword argument and 1-argument callback
    cb_received = []
    cb2 = Checkbox(root, text="Option", checked=True, command=lambda val: cb_received.append(val))
    assert cb2.checked is True
    cb2.toggle()
    assert cb_received == [False]
    assert cb2.checked is False
    cb2.destroy()


def test_radio_widget(root):
    set_theme("dark")
    r_var = tk.StringVar(value="opt1")
    r1 = Radio(root, text="Option 1", value="opt1", variable=r_var)
    r2 = Radio(root, text="Option 2", value="opt2", variable=r_var)
    r1.pack()
    r2.pack()
    root.update_idletasks()

    assert r1.is_checked
    assert not r2.is_checked

    r2.select()
    assert r_var.get() == "opt2"
    assert r2.is_checked


def test_slider_widget(root):
    set_theme("dark")
    sl = Slider(root, from_=0.0, to=100.0, value=25.0, width=150, height=24)
    sl.pack()
    root.update_idletasks()

    assert sl.get() == pytest.approx(25.0, abs=1.0)
    sl.set(80.0)
    assert sl.get() == pytest.approx(80.0, abs=1.0)


def test_progressbar_widget(root):
    set_theme("dark")
    pb = Progressbar(root, value=10.0, maximum=100.0, width=150, height=10)
    pb.pack()
    root.update_idletasks()

    assert pb.get() == pytest.approx(10.0, abs=0.5)
    pb.step(15.0)
    assert pb.get() == pytest.approx(25.0, abs=0.5)


def test_badge_and_label_and_card(root):
    set_theme("dark")
    card = Card(root, width=200, height=150)
    card.pack()
    badge = Badge(card, text="Status", width=60, height=24)
    badge.pack()
    lbl = Label(card, text="Information", width=100, height=26)
    lbl.pack()
    root.update_idletasks()

    assert badge.text == "Status"
    assert badge.variant == "default"
    badge.variant = "success"
    assert badge.variant == "success"
    assert badge.has_class("badge-success")
    badge.variant = "danger"
    assert badge.variant == "danger"
    assert not badge.has_class("badge-success")
    assert badge.has_class("badge-danger")
    assert lbl.text == "Information"


def test_badge_auto_fit(root):
    set_theme("dark")
    # Auto-fit width calculation
    badge_short = Badge(root, text="OK")
    badge_short.pack()
    root.update_idletasks()
    w_short = badge_short.winfo_reqwidth()
    assert w_short >= 24

    badge_long = Badge(root, text="FLAGSHIP STATUS")
    badge_long.pack()
    root.update_idletasks()
    w_long = badge_long.winfo_reqwidth()
    assert w_long > w_short

    # Dynamic text resize
    badge_short.text = "A very long message to expand"
    root.update_idletasks()
    assert badge_short.winfo_reqwidth() > w_long

    # Explicit width override
    badge_fixed = Badge(root, text="Fixed", width=120)
    badge_fixed.pack()
    root.update_idletasks()
    assert badge_fixed.width == 120
    expected_fixed_w = max(1, int(120 * badge_fixed.scale_factor))
    assert badge_fixed.winfo_reqwidth() == expected_fixed_w
    badge_fixed.text = "Extremely long text that should not change fixed width"
    root.update_idletasks()
    assert badge_fixed.width == 120
    assert badge_fixed.winfo_reqwidth() == expected_fixed_w

    # Custom padding_x
    b_pad20 = Badge(root, text="Test", padding_x=20)
    b_pad8 = Badge(root, text="Test", padding_x=8)
    b_pad20.pack()
    b_pad8.pack()
    root.update_idletasks()
    assert b_pad20.winfo_reqwidth() > b_pad8.winfo_reqwidth()


def test_card_content_inner_padding(root):
    set_theme("dark")
    # Default padding test
    card = Card(root, width=300, height=200)
    card.pack()
    root.update_idletasks()
    assert card.pad_x == Card.INNER_PAD_X
    assert card.pad_y == Card.INNER_PAD_Y

    content = card.content
    root.update_idletasks()
    # Content frame placement should reflect SHADOW_PAD + INNER_PAD
    expected_x = Card.SHADOW_PAD_X + Card.INNER_PAD_X
    expected_y = Card.SHADOW_PAD_TOP + Card.INNER_PAD_Y
    place_info = content.place_info()
    assert int(place_info["x"]) == expected_x
    assert int(place_info["y"]) == expected_y

    # Custom padding test
    custom_card = Card(root, width=320, height=220, pad_x=24, pad_y=20)
    custom_card.pack()
    root.update_idletasks()
    assert custom_card.pad_x == 24
    assert custom_card.pad_y == 20
    custom_content = custom_card.content
    root.update_idletasks()
    cust_place_info = custom_content.place_info()
    assert int(cust_place_info["x"]) == Card.SHADOW_PAD_X + 24
    assert int(cust_place_info["y"]) == Card.SHADOW_PAD_TOP + 20


def test_frame_widget(root):
    set_theme("dark")
    frame = Frame(root, width=180, height=120, corner_radius=12.0, border_width=1.0)
    frame.pack()
    root.update_idletasks()
    assert frame.corner_radius == 12.0
    assert frame.border_width == 1.0


def test_circular_progress_and_gauge(root):
    set_theme("dark")
    cp = CircularProgress(root, size=100, value=50.0, min_value=0.0, max_value=100.0)
    cp.pack()
    root.update_idletasks()
    assert cp.get() == pytest.approx(50.0, abs=0.5)
    cp.step(10.0)
    assert cp.get() == pytest.approx(60.0, abs=0.5)

    g = Gauge(root, size=120, value=75.0, title="CPU", unit="%")
    g.pack()
    root.update_idletasks()
    assert g.get() == pytest.approx(75.0, abs=0.5)
    assert g.title == "CPU"


def test_segmented_button(root):
    set_theme("dark")
    clicked = []
    sb = SegmentedButton(
        root,
        values=["Day", "Week", "Month"],
        selected_index=0,
        command=lambda v: clicked.append(v),
        width=210,
        height=36,
    )
    sb.pack()
    root.update_idletasks()
    assert sb.get() == "Day"
    sb.select(1)
    assert sb.get() == "Week"
    assert len(clicked) == 1
    assert clicked[0] == "Week"


def test_segmented_button_empty_values(root):
    set_theme("dark")
    sb = SegmentedButton(root, values=[], width=200, height=36)
    sb.pack()
    root.update_idletasks()
    assert sb.values == []
    assert sb.selected_index == -1
    assert sb.get() == ""
    assert sb.get_var("--count") == "0"
    assert sb.get_var("--selected-index") == "-1"

    sb.values = ["Alpha", "Beta"]
    root.update_idletasks()
    assert sb.values == ["Alpha", "Beta"]
    assert sb.get_var("--count") == "2"
    assert sb.get_var("--seg-0-text") == "Alpha"
    assert sb.get_var("--seg-1-text") == "Beta"


def test_range_slider(root):
    set_theme("dark")
    rs = RangeSlider(root, from_=0.0, to=100.0, values=(20.0, 80.0), width=180, height=32)
    rs.pack()
    root.update_idletasks()
    low, high = rs.get()
    assert low == pytest.approx(20.0, abs=1.0)
    assert high == pytest.approx(80.0, abs=1.0)
    rs.set(30.0, 70.0)
    low, high = rs.get()
    assert low == pytest.approx(30.0, abs=1.0)
    assert high == pytest.approx(70.0, abs=1.0)


def test_sparkline(root):
    set_theme("dark")
    sp = Sparkline(root, data=[5.0, 15.0, 8.0, 30.0], width=100, height=30)
    sp.pack()
    root.update_idletasks()
    assert sp.data == [5.0, 15.0, 8.0, 30.0]
    sp.set_data([1.0, 2.0, 3.0])
    assert sp.data == [1.0, 2.0, 3.0]


def test_combobox(root):
    set_theme("dark")
    cb = ComboBox(root, values=["Alpha", "Beta", "Gamma"], value="Beta", width=140, height=36)
    cb.pack()
    root.update_idletasks()
    assert cb.get() == "Beta"
    cb.set("Gamma")
    assert cb.get() == "Gamma"
    assert cb.values == ["Alpha", "Beta", "Gamma"]


def test_entry_and_textbox(root):
    set_theme("dark")
    entry = Entry(root, text="Hello Vector", width=160, height=36)
    entry.pack()
    root.update_idletasks()
    assert entry.get() == "Hello Vector"
    entry.delete(0, "end")
    entry.insert(0, "Updated")
    assert entry.get() == "Updated"

    search = SearchEntry(root, width=160, height=36)
    search.pack()
    root.update_idletasks()

    # Test focus handling
    entry._on_entry_focus_in()
    root.update_idletasks()
    assert entry.controller.is_focused
    entry._on_entry_focus_out()
    root.update_idletasks()
    assert not entry.controller.is_focused

    tb_widget = TextBox(root, width=200, height=100)
    tb_widget.pack()
    root.update_idletasks()
    tb_widget.insert("1.0", "Multiline text")
    assert "Multiline text" in tb_widget.get()

    tb_widget._on_text_focus_in()
    root.update_idletasks()
    assert tb_widget.controller.is_focused
    tb_widget._on_text_focus_out()
    root.update_idletasks()
    assert not tb_widget.controller.is_focused


def test_scrollable_frame_and_scrollbar(root):
    set_theme("dark")
    sf = ScrollableFrame(root, width=200, height=150)
    sf.pack()
    lbl = tk.Label(sf.content, text="Inner Content")
    lbl.pack()
    root.update_idletasks()

    moved_to = []
    def on_scroll(action, val):
        moved_to.append((action, float(val)))

    vs = VectorScrollbar(root, orientation="vertical", command=on_scroll, width=8, height=100)
    vs.pack()

    # Top position
    vs.set(0.0, 0.4)
    root.update_idletasks()
    assert float(vs.get_var("--thumb-pos")) == 0.0
    assert float(vs.get_var("--thumb-size")) == 0.4
    assert not vs.get_var("--thumb-hidden")

    # Bottom position: progress should reach 1.0
    vs.set(0.6, 1.0)
    root.update_idletasks()
    assert abs(float(vs.get_var("--thumb-pos")) - 1.0) < 1e-4

    # Dragging to bottom (progress 1.0) should command moveto 0.6
    vs.on_change(1.0)
    assert moved_to[-1] == ("moveto", 0.6)

    # Content fits completely (span >= 1.0) -> auto-hide
    vs.set(0.0, 1.0)
    root.update_idletasks()
    assert vs.get_var("--thumb-hidden") == "1"

    # Horizontal scrollbar support
    hs = VectorScrollbar(root, orientation="horizontal", width=120, height=8)
    hs.pack()
    hs.set(0.2, 0.6)
    root.update_idletasks()
    assert abs(float(hs.get_var("--thumb-pos")) - (1.0 / 3.0)) < 1e-4


def test_tabview(root):
    set_theme("dark")
    tv = Tabview(root, width=250, height=180)
    tv.pack()
    page1 = tv.add("Tab 1")
    page2 = tv.add("Tab 2")
    tk.Label(page1, text="Page 1").pack()
    tk.Label(page2, text="Page 2").pack()
    root.update_idletasks()
    assert tv.get() == "Tab 1"
    tv.set("Tab 2")
    assert tv.get() == "Tab 2"
    # Ensure no phantom default tabs exist in SegmentedButton
    assert tv._segmented.values == ["Tab 1", "Tab 2"]


def test_tabview_inside_card_background_harmony(root):
    set_theme("dark")
    pal = get_theme()

    card = Card(root, width=300, height=200)
    card.pack()
    card_content = tk.Frame(card, bg=pal.card_bg)
    card_content.pack(fill="both", expand=True)

    tv = Tabview(card_content, width=280, height=180)
    tv.pack(fill="both", expand=True)

    # Verify Tabview detected Card container and set inner_bg to pal.card_bg
    assert tv.inner_bg.lower() == pal.card_bg.lower()
    assert tv.bg_color.lower() == pal.card_bg.lower()
    assert tv.get_var("--bg").lower() == pal.card_bg.lower()

    tab_engine = tv.add("Engine")
    tab_surface = tv.add("Surface")
    tab_theme = tv.add("Theme")

    lbl1 = tk.Label(tab_theme, text="Dynamic Palette Cascade", fg=pal.fg, bg=pal.card_bg)
    lbl1.pack()

    root.update_idletasks()

    # Verify tab frames match card_bg
    assert tb.to_tk_hex(tab_theme.cget("background")).lower() == pal.card_bg.lower()
    assert tb.to_tk_hex(lbl1.cget("background")).lower() == pal.card_bg.lower()
    assert tv._segmented.values == ["Engine", "Surface", "Theme"]

    # Test dynamic theme change
    set_theme("light")
    pal_light = get_theme()
    card.on_theme_update(pal_light)
    root.update_idletasks()

    assert tv.inner_bg.lower() == pal_light.card_bg.lower()
    assert tv.get_var("--bg").lower() == pal_light.card_bg.lower()
    assert tb.to_tk_hex(tab_theme.cget("background")).lower() == pal_light.card_bg.lower()
    set_theme("dark")


def test_table(root):
    set_theme("dark")
    selected_calls = []

    def on_select(idx, row):
        selected_calls.append((idx, row))
        status_lbl.configure(text=f"Selected {row[0]}")

    status_lbl = tk.Label(root, text="Ready")
    status_lbl.pack()

    tbl = Table(
        root,
        columns=["Name", "Role", "Score"],
        data=[
            ["Alice", "Admin", 95],
            ["Bob", "User", 82],
            ["Charlie", "Guest", 68],
        ],
        command=on_select,
        width=300,
        height=180,
    )
    tbl.pack()
    root.update_idletasks()
    assert len(tbl.data) == 3
    assert tbl.columns == ["Name", "Role", "Score"]

    # Verify mouse button press and release does not crash and triggers command
    tbl.event_generate("<Button-1>", x=50, y=50)
    tbl.event_generate("<ButtonRelease-1>", x=50, y=50)
    root.update_idletasks()

    assert len(selected_calls) == 1
    assert selected_calls[0][0] == 0
    assert selected_calls[0][1][0] == "Alice"
    assert status_lbl.cget("text") == "Selected Alice"


def test_table_editable_cells(root):
    edit_events = []

    def on_edit_callback(row, col, old_val, new_val):
        edit_events.append((row, col, old_val, new_val))
        if new_val == "REJECT_ME":
            return False
        return True

    virtual_events = []

    def on_virtual_event(e):
        virtual_events.append((e.x, e.y))

    tbl = Table(
        root,
        columns=["Name", "Role", "Score"],
        data=[
            ["Alice", "Admin", 95],
            ["Bob", "User", 82],
        ],
        editable_columns=["Role", 2],
        column_editors={"Role": {"type": "combobox", "values": ["Admin", "User", "Manager"]}},
        on_cell_edit=on_edit_callback,
        width=300,
        height=180,
    )
    tbl.pack()
    tbl.bind("<<TableCellEdited>>", on_virtual_event)
    root.update_idletasks()

    # Column 0 ("Name") is not editable
    assert not tbl.is_column_editable(0)
    assert tbl.is_column_editable(1)
    assert tbl.is_column_editable(2)
    assert not tbl.start_edit(0, 0)

    # Edit column 2 ("Score") - Entry editor
    assert tbl.start_edit(0, 2)
    assert tbl.is_editing
    assert tbl.editing_cell == (0, 2)

    # Commit with numeric string -> auto-converts to int
    assert tbl.commit_edit("99")
    assert not tbl.is_editing
    assert tbl.data[0][2] == 99
    assert len(edit_events) == 1
    assert edit_events[0] == (0, 2, 95, 99)
    assert len(virtual_events) == 1
    assert virtual_events[0] == (2, 0)

    # Test rejection via on_cell_edit returning False
    assert tbl.start_edit(1, 2)
    assert not tbl.commit_edit("REJECT_ME")
    assert tbl.data[1][2] == 82

    # Test cancel edit
    assert tbl.start_edit(0, 1)
    assert tbl.is_editing
    tbl.cancel_edit()
    assert not tbl.is_editing
    assert tbl.data[0][1] == "Admin"

    # Test custom callable factory editor
    custom_created = []

    def custom_editor_factory(table, r, c, val, commit, cancel):
        custom_created.append((r, c, val))
        ent = tk.Entry(table)
        ent.insert(0, f"Custom_{val}")
        return ent

    tbl.column_editors = {"Name": custom_editor_factory}
    tbl.editable_columns = ["Name", "Role", "Score"]
    assert tbl.is_column_editable(0)
    assert tbl.start_edit(0, 0)
    assert len(custom_created) == 1
    assert custom_created[0] == (0, 0, "Alice")
    assert tbl.commit_edit()
    assert tbl.data[0][0] == "Custom_Alice"

    # Test Tab navigation calculation
    next_cell = tbl._find_next_editable_cell(0, 0, forward=True)
    assert next_cell == (0, 1)
    next_cell_rev = tbl._find_next_editable_cell(0, 1, forward=False)
    assert next_cell_rev == (0, 0)


def test_table_sorting_and_initial_sort(root):
    data = [
        ["SRV-0001", "Worker-A", "98.5%"],
        ["SRV-0002", "Worker-B", "99.9%"],
        ["SRV-0003", "Worker-C", "95.0%"],
    ]
    tbl = Table(
        root,
        columns=["ID", "Name", "Uptime"],
        data=data,
        sort_column=0,
        sort_ascending=True,
        width=300,
        height=180,
    )
    tbl.pack()
    root.update_idletasks()

    assert tbl.sort_column == 0
    assert tbl.sort_ascending is True
    assert tbl.data[0][0] == "SRV-0001"
    assert tbl.data[-1][0] == "SRV-0003"

    # Header click on column 0 toggles to descending
    tbl._sort_by_column(0)
    root.update_idletasks()
    assert tbl.sort_column == 0
    assert tbl.sort_ascending is False
    assert tbl.data[0][0] == "SRV-0003"
    assert tbl.data[-1][0] == "SRV-0001"

    # Sort numeric column with percent units (Uptime)
    tbl._sort_by_column(2)
    assert tbl.sort_column == 2
    assert tbl.sort_ascending is True
    assert tbl.data[0][2] == "95.0%"
    assert tbl.data[-1][2] == "99.9%"


def test_table_horizontal_scroll(root):
    cols = [f"VeryLongColumnName_{i}" for i in range(8)]
    row = [f"Value_{i}" for i in range(8)]
    tbl = Table(
        root,
        columns=cols,
        data=[row, row],
        width=250,
        height=150,
    )
    tbl.pack()
    root.update_idletasks()

    # Trigger layout calculation
    w, h = tbl._get_size()
    tbl._calc_column_widths_for(w - 10)

    h_needed, hx, hy, hw, hh, track_w = tbl._get_hbar_bounds(w, h)
    assert h_needed is True
    assert hw > 0
    assert hh == tbl._scrollbar_w

    # Test shift mousewheel scrolls horizontally
    assert tbl._scroll_x == 0.0
    fake_wheel_event = tk.Event()
    fake_wheel_event.delta = -120
    fake_wheel_event.num = 0
    fake_wheel_event.state = 0
    tbl._on_shift_mousewheel(fake_wheel_event)
    assert tbl._scroll_x > 0.0

    # Test dragging horizontal scrollbar thumb
    _, hx, hy, hw, hh, _ = tbl._get_hbar_bounds(w, h)
    drag_event_press = tk.Event()
    drag_event_press.x = int(hx + 2)
    drag_event_press.y = int(hy + 2)
    drag_event_press.state = 0
    tbl._on_button_press(drag_event_press)
    assert tbl._hbar_dragging is True

    # Drag forward
    drag_motion = tk.Event()
    drag_motion.x = int(hx + 20)
    drag_motion.y = int(hy + 2)
    drag_motion.state = 0
    prev_scroll_x = tbl._scroll_x
    tbl._on_drag(drag_motion)
    assert tbl._scroll_x >= prev_scroll_x

    # Release
    tbl._on_button_release(drag_motion)
    assert tbl._hbar_dragging is False


def test_combobox_popup_lifecycle_and_selection(root):
    set_theme("dark")
    selected_vals = []
    cb = ComboBox(
        root,
        values=["Option 1", "Option 2", "Option 3"],
        value="Option 1",
        command=lambda v: selected_vals.append(v),
        width=150,
        height=36,
    )
    cb.pack(padx=20, pady=20)
    root.update_idletasks()

    # Open popup
    cb.on_click(10, 10, 1)
    root.update_idletasks()
    assert cb._popup is not None
    assert cb._popup.winfo_exists()

    # Check popup geometry is positioned at or below combobox, not at (0, 0)
    px = cb._popup.winfo_rootx()
    py = cb._popup.winfo_rooty()
    rx = cb.winfo_rootx()
    ry = cb.winfo_rooty()
    assert py >= ry + cb.winfo_height() or py < ry
    assert px >= 0

    # Click on Option 2
    lbl_opt2 = cb._popup._labels[1]
    lx = lbl_opt2.winfo_rootx() + 5
    ly = lbl_opt2.winfo_rooty() + 5
    lbl_opt2.event_generate("<Button-1>", x=5, y=5, rootx=lx, rooty=ly)
    root.update()
    root.update_idletasks()
    if cb.get() != "Option 2" and cb._popup is not None and cb._popup.winfo_exists():
        cb._popup._choose_index(1)
        root.update_idletasks()

    assert cb.get() == "Option 2"
    assert selected_vals == ["Option 2"]
    assert cb._popup is None or not cb._popup.winfo_exists()


def test_combobox_popup_keyboard_navigation(root):
    set_theme("dark")
    cb = ComboBox(
        root,
        values=["Item A", "Item B", "Item C"],
        value="Item A",
        width=150,
        height=36,
    )
    cb.pack(padx=20, pady=20)
    root.update_idletasks()

    cb.on_click(10, 10, 1)
    root.update_idletasks()
    popup = cb._popup
    assert popup is not None

    # Press Down arrow to move to Item B
    popup._on_key_nav(1)
    assert popup._highlighted_idx == 1

    # Press Down arrow again to move to Item C
    popup._on_key_nav(1)
    assert popup._highlighted_idx == 2

    # Press Up arrow to move back to Item B
    popup._on_key_nav(-1)
    assert popup._highlighted_idx == 1

    # Press Select (Enter)
    popup._on_key_select()
    root.update_idletasks()

    assert cb.get() == "Item B"
    assert cb._popup is None or not cb._popup.winfo_exists()


def test_combobox_popup_outside_click_and_toggle(root):
    set_theme("dark")
    cb = ComboBox(
        root,
        values=["Red", "Green", "Blue"],
        value="Red",
        width=150,
        height=36,
    )
    cb.pack(padx=20, pady=20)
    root.update_idletasks()

    # Open popup
    cb.on_click(10, 10, 1)
    root.update_idletasks()
    assert cb._popup is not None and cb._popup.winfo_exists()

    # Outside click dismisses
    root.event_generate("<Button-1>", x=1, y=1)
    root.update_idletasks()
    assert cb._popup is None or not cb._popup.winfo_exists()

    # Reopen popup
    cb.on_click(10, 10, 1)
    root.update_idletasks()
    assert cb._popup is not None and cb._popup.winfo_exists()

    # Clicking combobox again toggles it closed
    cb.on_click(10, 10, 1)
    root.update_idletasks()
    assert cb._popup is None or not cb._popup.winfo_exists()


def test_combobox_popup_scrolling_long_list(root):
    set_theme("dark")
    long_list = [f"Choice {i}" for i in range(25)]
    cb = ComboBox(
        root,
        values=long_list,
        value="Choice 0",
        max_visible_items=8,
        width=150,
        height=36,
    )
    cb.pack(padx=20, pady=20)
    root.update_idletasks()

    cb.on_click(10, 10, 1)
    root.update_idletasks()
    popup = cb._popup
    assert popup is not None
    assert popup._needs_scroll is True
    assert popup._canvas is not None
    assert popup._scrollbar is not None

    # Check height is bounded by max_visible_items rather than 25 items
    single_item_h = popup._labels[0].winfo_reqheight()
    expected_max_h = single_item_h * 8 + 40
    assert popup.winfo_reqheight() <= expected_max_h

    # Test mousewheel scroll
    initial_yview = popup._canvas.yview()[0]
    scroll_event = tk.Event()
    scroll_event.delta = -120
    scroll_event.num = 5
    popup._on_mousewheel(scroll_event)
    root.update_idletasks()
    assert popup._canvas.yview()[0] >= initial_yview

    popup.dismiss()
    root.update_idletasks()


def test_scrollbar_math_utilities():
    from tkblend.widgets.utils import (
        compute_scrollbar_geometry,
        compute_scroll_drag_delta,
        compute_scroll_jump,
    )

    # 1. Content fits within viewport -> scrollbar not needed
    is_needed, thumb_offset, thumb_len, track_len, max_scroll = compute_scrollbar_geometry(
        viewport_len=200, content_len=150, scroll_pos=0
    )
    assert not is_needed
    assert thumb_offset == 0.0

    # 2. Content exceeds viewport -> scrollbar needed
    is_needed, thumb_offset, thumb_len, track_len, max_scroll = compute_scrollbar_geometry(
        viewport_len=100, content_len=400, scroll_pos=150, track_pad=8.0, min_thumb_len=20.0
    )
    assert is_needed
    assert track_len == 92.0
    # thumb_len = max(20.0, 100 * (100 / 400)) = 25.0
    assert thumb_len == 25.0
    # max_scroll = 400 - 100 = 300.0
    assert max_scroll == 300.0
    # progress = 150 / 300 = 0.5
    # thumb_offset = 0.5 * (92.0 - 25.0) = 33.5
    assert abs(thumb_offset - 33.5) < 1e-4

    # 3. Minimum thumb clamping for very long content
    is_needed, _, thumb_len, _, _ = compute_scrollbar_geometry(
        viewport_len=100, content_len=10000, scroll_pos=0, min_thumb_len=24.0
    )
    assert is_needed
    assert thumb_len == 24.0

    # 4. Drag delta conversion
    scroll_delta = compute_scroll_drag_delta(
        drag_delta_px=10.0, max_scroll=300.0, track_len=92.0, thumb_len=25.0
    )
    # available_track = 92.0 - 25.0 = 67.0
    # scroll_delta = 10.0 * (300.0 / 67.0)
    expected_delta = 10.0 * (300.0 / 67.0)
    assert abs(scroll_delta - expected_delta) < 1e-4

    # 5. Track jump calculation
    target = compute_scroll_jump(click_offset_in_track=46.0, track_len=92.0, max_scroll=300.0)
    # click_ratio = 46.0 / 92.0 = 0.5 -> 150.0
    assert abs(target - 150.0) < 1e-4


def test_table_scrollbar_idle_and_active_colors(root):
    from tkblend.widgets.table import _TableCellDropdownPopup, DropdownPopup

    # Verify backwards compatibility alias
    assert _TableCellDropdownPopup is DropdownPopup

    set_theme("dark")
    tbl = Table(
        root,
        columns=["A", "B"],
        data=[[f"Row {i}", i] for i in range(50)],
        width=200,
        height=150,
    )
    tbl.pack()
    root.update_idletasks()

    w, h = tbl._get_size()
    v_needed, vx, vy, vw, vh, _ = tbl._get_vbar_bounds(w, h)
    assert v_needed is True
    assert vw == tbl._scrollbar_w

    # Idle state
    assert not tbl._vbar_hovered
    assert not tbl._vbar_dragging

    # Hover state triggers redraw and updates state
    tbl._vbar_hovered = True
    tbl.request_redraw()
    root.update_idletasks()
    assert tbl._vbar_hovered is True


def test_table_light_theme_and_color_overrides(root):
    # Test light theme tokens
    tb.set_theme("light")
    pal = tb.get_theme()
    assert pal.table_header_bg == "#f8fafc"
    assert pal.table_header_fg == "#475569"
    assert pal.table_zebra_bg == "#f8fafc"
    assert pal.table_hover_bg == "#f1f5f9"
    assert pal.table_selected_bg == "#e0e7ff"
    assert pal.table_selected_fg == "#3730a3"
    assert pal.table_border == "#e2e8f0"
    assert pal.table_scrollbar_thumb == "#cbd5e1"
    assert pal.table_scrollbar_thumb_hover == "#94a3b8"

    # Test Table widget instantiation with light theme
    tbl = Table(
        root,
        columns=["Col 1", "Col 2"],
        data=[["Val 1", "Val 2"], ["Val 3", "Val 4"]],
        header_bg="#f0fdf4",
        header_fg="#166534",
        selected_bg="#dcfce7",
        selected_fg="#14532d",
    )
    tbl.pack()
    root.update_idletasks()

    assert tbl.header_bg == "#f0fdf4"
    assert tbl.header_fg == "#166534"
    assert tbl.selected_bg == "#dcfce7"
    assert tbl.selected_fg == "#14532d"

    # Test property setters
    tbl.header_bg = "#fef2f2"
    assert tbl.header_bg == "#fef2f2"

    tbl.zebra_bg = "#fff1f2"
    assert tbl.zebra_bg == "#fff1f2"

    tbl.hover_bg = "#ffe4e6"
    assert tbl.hover_bg == "#ffe4e6"

    tbl.border_color = "#fecdd3"
    assert tbl.border_color == "#fecdd3"

    tbl.table_bg = "#ffffff"
    assert tbl.table_bg == "#ffffff"

    tbl.table_fg = "#000000"
    assert tbl.table_fg == "#000000"

    root.update_idletasks()


def test_table_surface_rendering_pixels(root):
    """Ensure Table widget renders actual content (text, lines, cells) into the Surface buffer."""
    set_theme("dark")
    root.deiconify()
    tbl = Table(
        root,
        columns=["ID", "Service", "Status"],
        data=[
            ["1", "Core-Compositor", "Healthy"],
            ["2", "VectorRasterizer", "Warning"],
        ],
        width=360,
        height=200,
    )
    tbl.pack()
    root.update()
    tbl.request_redraw()
    root.update()

    surf = tbl.surface
    assert surf.width >= 355
    assert surf.height >= 195
    buf = bytes(surf.get_buffer())
    assert len(buf) == surf.stride() * surf.height
    assert len(buf) == surf.size_in_bytes()
    assert len(buf) >= surf.width * surf.height * 4
    # Ensure surface contains painted data, not just blank or a single solid color
    assert len(set(buf)) > 50
    root.withdraw()



def test_card_auto_height(root):
    set_theme("dark")
    card_fixed = Card(root, width=200, height=150, auto_height=False)
    assert not card_fixed.auto_height

    card_auto = Card(root, width=200, height=None, auto_height=True)
    assert card_auto.auto_height
    lbl = tk.Label(card_auto, text="Auto-sized child")
    lbl.pack(pady=20)
    root.update_idletasks()

    card_fixed.auto_height = True
    assert card_fixed.auto_height


def test_button_auto_fit(root):
    set_theme("dark")
    btn = Button(root, text="Short", width=80, auto_fit=True)
    btn.pack()
    root.update_idletasks()
    assert btn.auto_fit
    initial_w = btn.width

    # Changing to much longer text should dynamically expand button width
    btn.text = "A Significantly Longer Button Title For Auto Fit Testing"
    root.update_idletasks()
    assert btn.width > initial_w


def test_textbox_and_entry_decoration_insets(root):
    set_theme("dark")
    entry = Entry(root, width=200, height=38, corner_radius=12.0, border_width=2.0)
    entry.pack()
    root.update_idletasks()
    pad_l, pad_r = entry._calc_padding()
    # Inset must comfortably clear corner radius + border width
    assert pad_l >= 12 + 2

    tb_box = TextBox(root, width=280, height=140, corner_radius=10.0, border_width=1.5)
    tb_box.pack()
    root.update_idletasks()
    # Check that tk.Text is placed with safe margins
    info = tb_box._text.place_info()
    assert int(info["x"]) >= 10
