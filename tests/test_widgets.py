"""
Unit and integration tests for pure vector widgets in tkblend.widgets.
"""

import pytest
import tkinter as tk
from tkblend.widgets import (
    ScalingTracker,
    Widget,
    Frame,
    Card,
    LabelFrame,
    Labelframe,
    Button,
    Entry,
    TextInput,
    Checkbutton,
    Checkbox,
    Radiobutton,
    Radio,
    RadioGroup,
    Combobox,
    ComboBox,
    OptionMenu,
    Progressbar,
    ProgressBar,
    CircularProgress,
    Scale,
    Slider,
    RangeSlider,
    Spinbox,
    SpinBox,
    Label,
    Notebook,
    Tabview,
    Text,
    TextBox,
    Scrollbar,
    VectorScrollbar,
    Dropdown,
    DropdownItem,
    Badge,
    Avatar,
    Accordion,
    SegmentedControl,
    SegmentedButton,
    Switch,
    ToggleSwitch,
)
from tkblend.theme import set_theme, get_theme, DARK_PALETTE, LIGHT_PALETTE


@pytest.fixture
def root():
    try:
        r = tk.Tk()
        r.withdraw()
        yield r
        r.destroy()
    except tk.TclError:
        pytest.skip("Tkinter display not available")


def test_scaling_tracker(root):
    factor = ScalingTracker.get_scaling_factor(root)
    assert factor >= 0.5
    scaled = ScalingTracker.scale(100, root)
    assert isinstance(scaled, int)
    assert scaled > 0

    scaled_tuple = ScalingTracker.scale((10, 20), root)
    assert len(scaled_tuple) == 2


def test_button(root):
    clicked = []
    btn = Button(root, text="Click Me", command=lambda: clicked.append(1), variant="primary")
    btn.render()
    assert btn._text == "Click Me"
    btn.set_text("Updated")
    assert btn._text == "Updated"

    class MockEvent:
        def __init__(self, x=10, y=10):
            self.x = x
            self.y = y

    # Test press and release without leaving: state transitions cleanly
    btn._on_enter(MockEvent(10, 10))
    assert btn._is_hovered is True
    btn._on_press(MockEvent(10, 10))
    assert btn._is_pressed is True
    btn._on_release(MockEvent(10, 10))
    # Crucial fix verification: _is_pressed must be False after release even though mouse has not left
    assert btn._is_pressed is False
    assert btn._is_hovered is True
    assert clicked == [1]

    # Test keyboard activation
    btn._on_key_activate(None)
    assert btn._is_pressed is True
    # Run Tk scheduled after-callback to reset press and invoke command
    root.update_idletasks()
    root.after(150, lambda: None)
    import time
    time.sleep(0.12)
    root.update()
    assert btn._is_pressed is False
    assert len(clicked) == 2

    # Test focus handling
    btn._on_focus_in(None)
    assert btn._has_focus is True
    btn._on_focus_out(None)
    assert btn._has_focus is False
    btn.destroy()


def test_progress_bar(root):
    pb = ProgressBar(root, value=25.0)
    pb.render()
    assert pb.value == 25.0
    pb.set_value(75.0)
    assert pb.value == 75.0
    pb.set_value(150.0)  # Clamped to 100
    assert pb.value == 100.0
    pb.destroy()


def test_circular_progress(root):
    cp = CircularProgress(root, size=80, value=50.0)
    cp.render()
    assert cp.value == 50.0
    cp.set_value(80.0)
    assert cp.value == 80.0
    cp.destroy()


def test_slider(root):
    changed = []
    slider = Slider(root, min_val=0, max_val=100, value=30, on_change=lambda v: changed.append(v))
    slider.render()
    assert slider.value == 30.0
    slider.set_value(60.0)
    assert slider.value == 60.0
    slider.destroy()


def test_range_slider(root):
    rs = RangeSlider(root, min_val=0, max_val=100, low_val=10, high_val=90)
    rs.render()
    assert rs.range == (10.0, 90.0)
    rs.destroy()


def test_switch(root):
    set_theme("dark")
    toggled = []
    sw = Switch(root, is_on=False, on_toggle=lambda state: toggled.append(state))
    sw.render()
    assert sw.is_on is False
    assert sw._on_color == DARK_PALETTE.primary
    sw.toggle()
    assert sw.is_on is True
    assert toggled == [True]

    # Theme switch test
    set_theme("light")
    sw.render()
    assert get_theme().name == "light"
    set_theme("dark")

    sw.destroy()


def test_checkbox(root):
    cb = Checkbox(root, text="Remember Me", checked=False)
    cb.render()
    assert cb.checked is False
    cb.toggle()
    assert cb.checked is True
    cb.destroy()


def test_radio_and_group(root):
    group = RadioGroup()
    r1 = Radio(root, text="Option 1", value="opt1", group=group)
    r2 = Radio(root, text="Option 2", value="opt2", group=group)
    r1.render()
    r2.render()

    assert group.value == "opt1"
    assert r1.selected is True
    assert r2.selected is False

    group.select("opt2")
    assert group.value == "opt2"
    assert r1.selected is False
    assert r2.selected is True

    r1.destroy()
    r2.destroy()
    group.destroy()


def test_radio_background_inheritance(root):
    set_theme("dark")
    dark_pal = get_theme()

    card = Card(root, width=300, height=200)
    card.pack()
    root.update_idletasks()

    # 1. Logical group controller mode (Radio widgets inside Card, group is headless)
    logical_group = RadioGroup()
    r1 = Radio(card, text="Radio 1", value="r1", group=logical_group)
    r2 = Radio(card, text="Radio 2", value="r2", group=logical_group)
    r1.render()
    r2.render()

    assert r1._parent_bg == dark_pal.card_bg
    assert r2._parent_bg == dark_pal.card_bg

    # Switch theme: child radios must resolve to card_bg, NOT root bg
    set_theme("light")
    light_pal = get_theme()
    assert r1._parent_bg == light_pal.card_bg
    assert r2._parent_bg == light_pal.card_bg

    r1.destroy()
    r2.destroy()
    logical_group.destroy()

    # 2. Container mode (RadioGroup is packed inside Card with options)
    set_theme("dark")
    dark_pal = get_theme()
    container_group = RadioGroup(card, options=["Alpha", "Beta"], selected="Alpha")
    container_group.pack()
    root.update_idletasks()

    assert container_group._parent_bg == dark_pal.card_bg
    for child_radio in container_group._radios:
        assert child_radio._parent_bg == dark_pal.card_bg

    set_theme("light")
    light_pal = get_theme()
    assert container_group._parent_bg == light_pal.card_bg
    for child_radio in container_group._radios:
        assert child_radio._parent_bg == light_pal.card_bg

    container_group.destroy()
    card.destroy()


def test_segmented_control(root):
    seg = SegmentedControl(root, values=["Tab A", "Tab B", "Tab C"], selected_index=0)
    seg.render()
    assert seg.selected_index == 0
    seg.selected_index = 2
    assert seg.selected_index == 2
    seg.destroy()


def test_text_input(root):
    inp = TextInput(root, placeholder="Type here...", width=240, height=38)
    inp.pack()
    root.update_idletasks()

    # Placeholder active initially: get() returns empty string, entry has placeholder
    assert inp.get() == ""
    assert inp._placeholder_active is True
    assert inp._entry.get() == "Type here..."

    # Ensure background widget rendered on idle
    assert inp._bg_widget.winfo_exists()

    # Focus in clears placeholder
    inp._on_focus_in(None)
    assert inp._placeholder_active is False
    assert inp.get() == ""

    # Setting text
    inp.set("Hello tkblend")
    assert inp.get() == "Hello tkblend"
    assert inp._placeholder_active is False

    # Clear button click
    s = inp._scale
    class DummyEvent:
        x = int(inp._bg_widget._widget_w - 20.0 * s)
        y = int(inp._bg_widget._widget_h / 2.0)
    inp._on_bg_click(DummyEvent())
    assert inp.get() == ""

    # Focus out with empty text restores placeholder
    inp._on_focus_out(None)
    assert inp._placeholder_active is True
    assert inp.get() == ""
    assert inp._entry.get() == "Type here..."

    inp.destroy()


def test_dropdown(root):
    selected_log = []

    def on_sel(val):
        selected_log.append(val)

    # Basic initialization and callbacks
    dd = Dropdown(root, options=["First", "Second", "Third"], selected="First", on_select=on_sel)
    dd.render()
    assert dd.value == "First"
    assert dd.options == ["First", "Second", "Third"]

    # Select option programmatically
    dd._select_option("Second")
    assert dd.value == "Second"
    assert selected_log == ["Second"]

    # Set value property
    dd.value = "Third"
    assert dd.value == "Third"

    # Set options method
    dd.set_options(["Alpha", "Beta", "Gamma"], selected="Beta")
    assert dd.options == ["Alpha", "Beta", "Gamma"]
    assert dd.value == "Beta"

    # Keyboard navigation tests
    dd._on_key_down(None)
    assert dd.value == "Gamma"
    dd._on_key_up(None)
    assert dd.value == "Beta"
    dd._on_key_home(None)
    assert dd.value == "Alpha"
    dd._on_key_end(None)
    assert dd.value == "Gamma"

    # Open popup
    dd._open_popup()
    assert dd._is_open is True
    assert dd._popup_win is not None
    assert len(dd._item_widgets) == 3

    # Click an item in open popup
    dd._on_item_clicked("Beta")
    assert dd.value == "Beta"
    assert dd._is_open is False
    assert dd._popup_win is None

    # Test long options list (scrollable container with VectorScrollbar)
    long_opts = [f"Item {i}" for i in range(15)]
    dd.set_options(long_opts, selected="Item 0")
    dd._open_popup()
    assert dd._is_open is True
    assert dd._scroll_canvas is not None
    assert dd._scrollbar is not None
    assert len(dd._item_widgets) == 15

    # Test keyboard navigation when open
    dd._on_key_down(None)
    assert dd.value == "Item 1"

    # Close popup via Escape or toggle
    dd._on_key_enter(None)
    assert dd._is_open is False

    # Standalone DropdownItem test
    item = DropdownItem(root, text="Standalone", is_selected=True, on_select=on_sel)
    item.render()
    assert item.text == "Standalone"
    assert item.is_selected is True
    item.set_selected(False)
    assert item.is_selected is False
    item._handle_click(None)
    assert selected_log[-1] == "Standalone"
    item.destroy()

    dd.destroy()


def test_vector_scrollbar(root):
    scroll_cmds = []

    def on_scroll(*args):
        scroll_cmds.append(args)

    vs = VectorScrollbar(root, command=on_scroll, width=10, height=150)
    vs.render()
    assert vs._first == 0.0
    assert vs._last == 1.0

    # Protocol set(first, last)
    vs.set(0.2, 0.6)
    assert vs._first == 0.2
    assert vs._last == 0.6

    # Test track click paging
    class MockEvent:
        def __init__(self, y):
            self.y = y

    # Click below thumb -> page down
    vs._on_press(MockEvent(y=140))
    assert scroll_cmds[-1] == ("scroll", 1, "pages")

    # Click above thumb -> page up
    vs._on_press(MockEvent(y=10))
    assert scroll_cmds[-1] == ("scroll", -1, "pages")

    vs.destroy()


def test_spinbox(root):
    changes = []
    sb = SpinBox(root, min_val=0, max_val=10, value=5, step=1, on_change=lambda v: changes.append(v))
    sb.render()
    assert sb.value == 5
    assert sb._entry.get() == "5"

    class MockEvent:
        def __init__(self, x=10, y=10):
            self.x = x
            self.y = y

    minus_x, plus_x, btn_y, btn_w, btn_h, _ = sb._button_geometry()
    cy = btn_y + btn_h / 2.0

    # Test stepping via buttons
    # Minus button click
    sb._handle_press(MockEvent(x=minus_x + btn_w / 2.0, y=cy))
    assert sb.value == 4
    assert sb._pressed_btn == "minus"
    sb._handle_release(MockEvent(x=minus_x + btn_w / 2.0, y=cy))
    assert sb._pressed_btn is None

    # Plus button click
    sb._handle_press(MockEvent(x=plus_x + btn_w / 2.0, y=cy))
    assert sb.value == 5
    sb._handle_release(MockEvent(x=plus_x + btn_w / 2.0, y=cy))

    # Test keyboard navigation Up/Down
    sb._on_entry_up(None)
    assert sb.value == 6
    assert sb._entry.get() == "6"
    sb._on_entry_down(None)
    assert sb.value == 5
    assert sb._entry.get() == "5"

    # Test text entry direct typing and commit
    sb._entry.delete(0, "end")
    sb._entry.insert(0, "9")
    sb._on_entry_commit(None)
    assert sb.value == 9

    # Test clamping on entry commit
    sb._entry.delete(0, "end")
    sb._entry.insert(0, "999")
    sb._on_entry_commit(None)
    assert sb.value == 10
    assert sb._entry.get() == "10"

    sb._entry.delete(0, "end")
    sb._entry.insert(0, "-50")
    sb._on_entry_commit(None)
    assert sb.value == 0
    assert sb._entry.get() == "0"

    # Test button hover detection
    sb._on_mouse_motion(MockEvent(x=minus_x + btn_w / 2.0, y=cy))
    assert sb._hovered_btn == "minus"
    sb._on_mouse_motion(MockEvent(x=plus_x + btn_w / 2.0, y=cy))
    assert sb._hovered_btn == "plus"
    sb._handle_leave(MockEvent(x=-1, y=-1))
    assert sb._hovered_btn is None

    # Test auto-repeat trigger and cancellation
    sb._start_repeat(1)
    assert sb._repeat_timer is not None
    sb._cancel_repeat()
    assert sb._repeat_timer is None

    sb.destroy()


def test_badge(root):
    badge = Badge(root, text="Active", variant="success", dot=True)
    badge.render()
    assert badge._text == "Active"
    badge.set_text("Pending")
    assert badge._text == "Pending"
    badge.destroy()


def test_avatar(root):
    av = Avatar(root, initials="BL", status="online", size=48)
    av.render()
    assert av._initials == "BL"
    av.destroy()


def test_accordion(root):
    acc = Accordion(root, title="Advanced Settings", width=250)
    acc.pack()
    root.update_idletasks()

    assert acc._is_open is False
    assert isinstance(acc.content_frame, tk.Frame)
    assert acc._header.winfo_exists()

    # Toggle open
    acc._toggle(None)
    assert acc._is_open is True

    # Toggle closed
    acc._toggle(None)
    assert acc._is_open is False

    # Hover rendering
    acc._header._is_hovered = True
    acc._header.render()
    acc._header._is_hovered = False
    acc._header.render()

    acc.destroy()


def test_frame_and_card(root):
    frame = Frame(root, width=200, height=120)
    frame.render()
    card = Card(root, title="Analytics Card", width=240, height=160)
    card.render()
    assert card.content is card
    cf = card.create_content_frame()
    assert cf.master is card
    cf.destroy()
    frame.destroy()
    card.destroy()


def test_widget_hierarchy_bg_resolution(root):
    set_theme("dark")
    card = Card(root, title="Test Card")
    # Button directly inside card
    btn = Button(card, text="Direct")
    assert btn._parent_bg == card._bg_color

    # Button inside a child tk.Frame inside card
    subframe = tk.Frame(card)
    btn_nested = Button(subframe, text="Nested")
    assert btn_nested._parent_bg == card._bg_color

    # Switch theme to light and verify both adapt
    set_theme("light")
    root.update_idletasks()
    assert btn._parent_bg == LIGHT_PALETTE.card_bg
    assert btn_nested._parent_bg == LIGHT_PALETTE.card_bg

    # Switch back to dark
    set_theme("dark")
    root.update_idletasks()
    assert btn._parent_bg == DARK_PALETTE.card_bg
    assert btn_nested._parent_bg == DARK_PALETTE.card_bg

    btn.destroy()
    btn_nested.destroy()
    subframe.destroy()
    card.destroy()


def test_theme_switch_redraw(root):
    btn = Button(root, text="Themed")
    btn.render()
    card = Card(root, title="Card")
    frame = Frame(root)
    sw = Switch(root)
    seg = SegmentedControl(root, values=["A", "B"])

    # Switch to light
    set_theme("light")
    root.update_idletasks()
    assert btn._get_variant_colors("primary")["bg"] == LIGHT_PALETTE.primary
    assert card._bg_color == LIGHT_PALETTE.card_bg
    assert frame._bg_color == LIGHT_PALETTE.card_bg

    # Switch back to dark
    set_theme("dark")
    root.update_idletasks()
    assert btn._get_variant_colors("primary")["bg"] == DARK_PALETTE.primary
    assert card._bg_color == DARK_PALETTE.card_bg
    assert frame._bg_color == DARK_PALETTE.card_bg

    btn.destroy()
    card.destroy()
    frame.destroy()
    sw.destroy()
    seg.destroy()


def test_deep_mixed_hierarchy_bg_resolution(root):
    import tkinter.ttk as ttk
    set_theme("dark")

    # Card (tkblend) -> tk.Frame (standard Tk) -> ttk.Frame (ttk container) -> tkblend widgets
    card = Card(root, title="Compound Card")
    tk_frame = tk.Frame(card)
    ttk_frame = ttk.Frame(tk_frame)

    btn = Button(ttk_frame, text="Deep Button")
    inp = TextInput(ttk_frame, placeholder="Deep Input")
    slider = Slider(ttk_frame, value=50)

    root.update_idletasks()
    # All deep children should resolve to the enclosing Card's background
    assert btn._parent_bg == card._bg_color
    assert inp._parent_bg == card._bg_color
    assert slider._parent_bg == card._bg_color

    # Switch theme to light and verify all deep descendants update
    set_theme("light")
    root.update_idletasks()
    assert btn._parent_bg == LIGHT_PALETTE.card_bg
    assert inp._parent_bg == LIGHT_PALETTE.card_bg
    assert slider._parent_bg == LIGHT_PALETTE.card_bg

    # Switch back to dark
    set_theme("dark")
    root.update_idletasks()
    assert btn._parent_bg == DARK_PALETTE.card_bg
    assert inp._parent_bg == DARK_PALETTE.card_bg
    assert slider._parent_bg == DARK_PALETTE.card_bg

    btn.destroy()
    inp.destroy()
    slider.destroy()
    ttk_frame.destroy()
    tk_frame.destroy()
    card.destroy()


def test_accordion_geometry_under_theme_switch_and_fill_x(root):
    set_theme("dark")
    card = Card(root, title="Card Container", width=400, height=300)
    card.pack()
    acc = Accordion(card, title="Test Accordion", width=350)
    acc.pack(fill="x")
    root.update()

    scale = acc._scale
    expected_h = max(1, int(38 * scale))
    assert acc._header._widget_h == expected_h

    # Trigger theme switch to light: container background updates must not collapse header height
    set_theme("light")
    root.update_idletasks()
    assert acc._header._widget_h == expected_h
    assert acc._header.winfo_reqheight() == expected_h

    # Trigger theme switch back to dark
    set_theme("dark")
    root.update_idletasks()
    assert acc._header._widget_h == expected_h
    assert acc._header.winfo_reqheight() == expected_h

    card.destroy()


def test_widget_transient_configure_guard(root):
    btn = Button(root, text="Guard Test", width=120, height=40)
    btn.pack()
    root.update()

    init_w = btn._widget_w
    init_h = btn._widget_h

    # Simulate transient unmapped/intermediate geometry events with <= 1 dimensions
    class DummyEvent:
        width = 1
        height = 1

    btn._on_configure(DummyEvent())
    assert btn._widget_w == init_w
    assert btn._widget_h == init_h

    btn.destroy()


def test_progress_bar_and_circular_gauge_dynamic_theme_switching(root):
    set_theme("dark")
    root.update_idletasks()

    pb_default = ProgressBar(root, value=30.0)
    pb_custom = ProgressBar(root, value=30.0, track_color="#112233", fill_color_start="#445566")
    cp_default = CircularProgress(root, value=50.0)
    cp_semantic = CircularProgress(root, value=50.0, fill_color="accent")
    cp_custom = CircularProgress(root, value=50.0, track_color="#aabbcc")

    root.update_idletasks()

    # Initial dark theme verification
    assert pb_default.track_color == DARK_PALETTE.track_bg
    assert pb_default._fill_start == DARK_PALETTE.primary
    assert pb_custom.track_color == "#112233"
    assert pb_custom._fill_start == "#445566"
    assert cp_default.track_color == DARK_PALETTE.track_bg
    assert cp_default.fill_color == DARK_PALETTE.primary
    assert cp_semantic.fill_color == DARK_PALETTE.accent
    assert cp_custom.track_color == "#aabbcc"

    # Switch to light theme
    set_theme("light")
    root.update_idletasks()

    assert pb_default.track_color == LIGHT_PALETTE.track_bg
    assert pb_default._fill_start == LIGHT_PALETTE.primary
    assert pb_custom.track_color == "#112233"
    assert pb_custom._fill_start == "#445566"
    assert cp_default.track_color == LIGHT_PALETTE.track_bg
    assert cp_default.fill_color == LIGHT_PALETTE.primary
    assert cp_semantic.fill_color == LIGHT_PALETTE.accent
    assert cp_custom.track_color == "#aabbcc"

    # Switch back to dark theme
    set_theme("dark")
    root.update_idletasks()

    assert pb_default.track_color == DARK_PALETTE.track_bg
    assert cp_default.track_color == DARK_PALETTE.track_bg
    assert cp_semantic.fill_color == DARK_PALETTE.accent

    pb_default.destroy()
    pb_custom.destroy()
    cp_default.destroy()
    cp_semantic.destroy()
    cp_custom.destroy()


def test_slider_and_range_slider_dynamic_theme_switching(root):
    set_theme("dark")
    root.update_idletasks()

    slider_default = Slider(root, value=40.0)
    slider_semantic = Slider(root, value=40.0, active_track_color="accent")
    slider_custom = Slider(root, value=40.0, track_color="#334455", knob_color="#667788")

    rs_default = RangeSlider(root, low_val=20.0, high_val=80.0)
    rs_semantic = RangeSlider(root, low_val=20.0, high_val=80.0, active_color="warning")
    rs_custom = RangeSlider(root, low_val=20.0, high_val=80.0, knob_color="#fedcba")

    root.update_idletasks()

    # Initial dark theme verification
    assert slider_default.track_color == DARK_PALETTE.track_bg
    assert slider_default.active_track_color == DARK_PALETTE.primary
    assert slider_default.knob_color == DARK_PALETTE.thumb_color
    assert slider_semantic.active_track_color == DARK_PALETTE.accent
    assert slider_custom.track_color == "#334455"
    assert slider_custom.knob_color == "#667788"

    assert rs_default.track_color == DARK_PALETTE.track_bg
    assert rs_default.active_color == DARK_PALETTE.success
    assert rs_default.knob_color == DARK_PALETTE.thumb_color
    assert rs_semantic.active_color == DARK_PALETTE.warning
    assert rs_custom.knob_color == "#fedcba"

    # Switch to light theme
    set_theme("light")
    root.update_idletasks()

    assert slider_default.track_color == LIGHT_PALETTE.track_bg
    assert slider_default.active_track_color == LIGHT_PALETTE.primary
    assert slider_default.knob_color == LIGHT_PALETTE.thumb_color
    assert slider_semantic.active_track_color == LIGHT_PALETTE.accent
    assert slider_custom.track_color == "#334455"
    assert slider_custom.knob_color == "#667788"

    assert rs_default.track_color == LIGHT_PALETTE.track_bg
    assert rs_default.active_color == LIGHT_PALETTE.success
    assert rs_default.knob_color == LIGHT_PALETTE.thumb_color
    assert rs_semantic.active_color == LIGHT_PALETTE.warning
    assert rs_custom.knob_color == "#fedcba"

    # Switch back to dark theme
    set_theme("dark")
    root.update_idletasks()

    assert slider_default.track_color == DARK_PALETTE.track_bg
    assert rs_default.track_color == DARK_PALETTE.track_bg

    slider_default.destroy()
    slider_semantic.destroy()
    slider_custom.destroy()
    rs_default.destroy()
    rs_semantic.destroy()
    rs_custom.destroy()


def test_frame_and_card_padding_and_shadow_budget(root):
    # 1. Frame with default padding and elevation
    frame = Frame(root, width=200, height=120, elevation=8.0)
    frame.render()
    assert frame._current_pad >= 8.0
    assert frame.padding == frame._current_pad / frame._scale

    # 2. Frame with explicit padding
    frame_padded = Frame(root, width=200, height=120, elevation=12.0, padding=16.0)
    frame_padded.render()
    assert frame_padded.padding == 16.0
    assert frame_padded._current_pad == 16.0 * frame_padded._scale

    # 3. Dynamic padding property setter
    frame_padded.padding = 20.0
    assert frame_padded.padding == 20.0
    assert frame_padded._current_pad == 20.0 * frame_padded._scale

    # 4. Zero padding disables shadow cleanly
    frame_zero = Frame(root, width=200, height=120, padding=0.0)
    frame_zero.render()
    assert frame_zero.padding == 0.0
    assert frame_zero._current_pad == 0.0

    # 5. Card with explicit padding
    card = Card(root, title="Padded Card", width=250, height=180, elevation=10.0, padding=14.0)
    card.render()
    assert card.padding == 14.0
    assert card._current_pad == 14.0 * card._scale

    frame.destroy()
    frame_padded.destroy()
    frame_zero.destroy()
    card.destroy()


def test_widget_unclipped_shadow_rendering(root):
    # Verify widgets rendering shadows execute without errors under padding-budget inference
    btn = Button(root, text="Elevated", elevation=5.0)
    btn.render()

    sw = Switch(root)
    sw.render()

    seg = SegmentedControl(root, values=["A", "B", "C"])
    seg.render()

    slider = Slider(root, min_val=0, max_val=100, value=50)
    slider.render()

    rslider = RangeSlider(root, min_val=0, max_val=100, low_val=25, high_val=75)
    rslider.render()

    btn.destroy()
    sw.destroy()
    seg.destroy()
    slider.destroy()
    rslider.destroy()


def test_container_safe_insets_and_body(root):
    from tkblend.utils.window_shape import (
        is_window_shaping_supported,
        apply_round_rect_shape,
        clear_window_shape,
    )

    # 1. Frame safe insets (unclipped / fallback mode)
    frame = Frame(root, width=200, height=150, elevation=8.0, rx=16.0, ry=16.0, clip_children=False)
    frame.render()
    l, t, r, b = frame.safe_insets
    assert l > 0 and t > 0 and r > 0 and b > 0
    bx, by, bw, bh = frame.content_bounds
    assert bw > 0 and bh > 0
    assert bx == frame.safe_insets_px[0]
    assert by == frame.safe_insets_px[1]

    # 2. Card safe insets without title vs with title
    card_no_title = Card(root, title="", width=280, height=180, clip_children=False)
    card_no_title.render()
    _, t_no_title, _, _ = card_no_title.safe_insets

    card_with_title = Card(root, title="Stats Overview", width=280, height=180, clip_children=False)
    card_with_title.render()
    _, t_with_title, _, _ = card_with_title.safe_insets
    # Title adds header and divider clearance
    assert t_with_title > t_no_title

    # 3. Card body inner content frame
    body = card_with_title.body
    assert isinstance(body, tk.Frame)
    assert body.master is card_with_title

    # 4. Verify geometric corner clearance in unclipped mode
    l_px, t_px, r_px, b_px = card_no_title.safe_insets_px
    assert l_px >= card_no_title._current_pad + 14.0 * card_no_title._scale
    assert b_px >= card_no_title._current_pad + 14.0 * card_no_title._scale
    cx, cy, cw, ch = card_no_title.content_bounds
    assert cx >= l_px
    assert cy >= t_px
    assert cx + cw <= card_no_title._widget_w - r_px
    assert cy + ch <= card_no_title._widget_h - b_px

    # 5. Clipped mode and C++ native window shaping
    clipped_frame = Frame(root, width=200, height=150, clip_children=True)
    clipped_frame.render()
    body_frame = clipped_frame.body
    root.update()
    
    if is_window_shaping_supported():
        # High-level facade
        sh_res = apply_round_rect_shape(body_frame, 150, 100, 12.0, 12.0)
        assert sh_res is True
        cl_res = clear_window_shape(body_frame)
        assert cl_res is True

        # Native C++ module tests
        from tkblend import _tkblend
        if hasattr(_tkblend, "apply_round_rect_shape"):
            wid = body_frame.winfo_id()
            assert _tkblend.is_window_shaping_supported() is True
            assert _tkblend.apply_round_rect_shape(wid, 150, 100, 12.0, 12.0) is True
            assert _tkblend.clear_window_shape(wid) is True

    frame.destroy()
    card_no_title.destroy()
    card_with_title.destroy()
    clipped_frame.destroy()


def test_text_input_and_spinbox_dynamic_bounds_and_resize(root):
    # 1. TextInput dynamic font metrics update
    inp = TextInput(root, placeholder="Type here...", width=200, height=36)
    inp.pack()
    root.update()

    init_entry_h = inp._entry.winfo_reqheight()
    # Change to larger font
    inp.font_size = 20.0
    root.update()
    larger_entry_h = inp._entry.winfo_reqheight()
    assert larger_entry_h >= init_entry_h

    # 2. SpinBox entry geometry bounds
    spin = SpinBox(root, min_val=0, max_val=100, value=25, width=150, height=36)
    spin.pack()
    root.update()

    # Entry width must leave room for stepper buttons
    entry_w = int(spin._entry.place_info()["width"])
    assert entry_w > 0
    assert entry_w < spin._widget_w - 40

    # 3. SpinBox font change adjusts geometry
    spin.font_size = 18.0
    root.update()

    inp.destroy()
    spin.destroy()


def test_dropdown_screen_edge_clamping(root):
    dd = Dropdown(root, options=["Alpha", "Beta", "Gamma"], width=160, height=34)
    dd.pack()
    root.update()

    # Open popup and verify it mounts within screen bounds
    dd._open_popup()
    assert dd._popup_win is not None
    assert dd._popup_win.winfo_exists()

    pop_geom = dd._popup_win.geometry()
    assert "x" in pop_geom and "+" in pop_geom

    dd._close_popup()
    assert dd._popup_win is None
    dd.destroy()


def test_zero_dimension_and_extreme_resize_robustness(root):
    # Ensure all widgets render safely without crashes even under 1x1 or extreme sizes
    widgets = [
        Button(root, text="B", width=1, height=1),
        ProgressBar(root, width=1, height=1),
        CircularProgress(root, size=1),
        Slider(root, width=1, height=1),
        RangeSlider(root, width=1, height=1),
        Switch(root, width=1, height=1),
        Checkbox(root, width=1, height=1),
        Radio(root, width=1, height=1),
        SegmentedControl(root, width=1, height=1),
        TextInput(root, width=1, height=1),
        SpinBox(root, width=1, height=1),
        Dropdown(root, width=1, height=1),
        Badge(root, width=1, height=1),
        Avatar(root, size=1),
        VectorScrollbar(root, width=1, height=1),
        Frame(root, width=1, height=1),
        Card(root, width=1, height=1),
        Accordion(root, width=1),
    ]

    for w in widgets:
        w.render()

    for w in widgets:
        w.destroy()


def test_switch_variable_and_command(root):
    var = tk.BooleanVar(value=True)
    called = []
    sw = Switch(root, variable=var, command=lambda val=None: called.append(val))
    sw.pack()
    root.update()
    assert sw.is_on is True

    # Test toggling via method
    sw.toggle()
    assert sw.is_on is False
    assert var.get() is False
    assert len(called) == 1

    # Test updating variable
    var.set(True)
    assert sw.is_on is True

    sw.destroy()


def test_segmented_control_command(root):
    selected_vals = []
    seg = SegmentedControl(
        root,
        values=["List", "Grid", "Icons"],
        command=lambda val: selected_vals.append(val),
    )
    seg.pack()
    root.update()

    # Simulate selecting index 1
    seg._handle_click(type("Event", (), {"x": int(seg._widget_w * 0.5)})())
    assert seg.selected_index == 1
    assert "Grid" in selected_vals
    seg.destroy()


def test_text_input_bind_forwarding(root):
    root.deiconify()
    events = []
    inp = TextInput(root, placeholder="Type here...")
    inp.pack()
    inp.bind("<<CustomEvent>>", lambda e: events.append("custom"))
    root.update()

    inp.event_generate("<<CustomEvent>>")
    root.update()
    assert "custom" in events
    root.withdraw()
    inp.destroy()


def test_badge_variant_and_text(root):
    b = Badge(root, text="Initial", variant="primary")
    b.pack()
    root.update()
    assert b.text == "Initial"
    assert b.variant == "primary"

    b.set_text("Updated")
    b.set_variant("success")
    assert b.text == "Updated"
    assert b.variant == "success"
    b.destroy()


def test_file_explorer_initialization(root):
    from examples.file_explorer import FileExplorerApp
    app = FileExplorerApp(root)
    root.update()
    assert app.current_dir.exists()
    assert len(app.current_items) > 0
    assert app.path_entry.get() == str(app.current_dir)

    # Test sorting
    app._sort_table_by("size")
    assert app.sort_column == "size"

    # Test search filter
    app.search_entry.set("py")
    app._on_search_changed(None)
    root.update()

    # Test view mode switch
    app._on_view_mode_changed("Grid")
    root.update()
    app._on_view_mode_changed("Details")
    root.update()

    # Test toggle theme
    app.toggle_theme()
    root.update()
    app.toggle_theme()
    root.update()






def test_tk_standard_names_and_aliases(root):
    # Verify standard Tk class parity and backward-compatible aliases
    assert TextInput is Entry
    assert Checkbox is Checkbutton
    assert Radio is Radiobutton
    assert ComboBox is Combobox
    assert ProgressBar is Progressbar
    assert Slider is Scale
    assert SpinBox is Spinbox
    assert Tabview is Notebook
    assert TextBox is Text
    assert LabelFrame is Card
    assert Labelframe is Card
    assert VectorScrollbar is Scrollbar

    # Verify Label instantiation and rendering
    lbl = Label(root, text="Pure Vector Label", font_size=14, align="center")
    lbl.render()
    assert lbl.text == "Pure Vector Label"
    lbl.set_text("Updated Label")
    assert lbl.text == "Updated Label"
    lbl.destroy()

    # Verify Entry instantiation with standard name
    ent = Entry(root, placeholder="Type here...")
    ent.render()
    ent.insert("0", "Test text")
    assert ent.get() == "Test text"
    ent.destroy()

    # Verify Checkbutton instantiation with standard name
    cb = Checkbutton(root, text="Check Me")
    cb.render()
    assert cb.get() is False
    cb.set(True)
    assert cb.get() is True
    cb.destroy()

    # Verify Radiobutton instantiation with standard name
    rb = Radiobutton(root, text="Option A", value="A")
    rb.render()
    rb.destroy()

    # Verify Progressbar instantiation with standard name
    pb = Progressbar(root, value=40.0)
    pb.render()
    assert pb.value == 40.0
    pb.destroy()

    # Verify Scale instantiation with standard name
    sc = Scale(root, from_=0, to=100, value=50)
    sc.render()
    assert sc.get() == 50
    sc.destroy()

    # Verify Notebook instantiation with standard name
    nb = Notebook(root)
    t1 = nb.add("Tab 1")
    assert "Tab 1" in nb.tabs()
    nb.render()
    nb.destroy()

    # Verify Text instantiation with standard name
    tx = Text(root, width=200, height=100)
    tx.render()
    tx.destroy()


def test_widget_resize_ratchet_recovery_and_space_restoration(root):
    """Test that widgets shrink gracefully when compressed and fully recover their space when expanded."""
    from tkblend.widgets import Button, ProgressBar

    root.deiconify()
    root.geometry("600x200")
    root.update_idletasks()
    root.update()

    # Container with multiple packed widgets side-by-side
    container = tk.Frame(root)
    container.pack(fill="x", expand=True, padx=10, pady=10)

    b1 = Button(container, text="Btn 1", width=100, height=36)
    b1.pack(side="left", padx=5)
    b2 = Button(container, text="Btn 2", width=100, height=36)
    b2.pack(side="left", padx=5)
    b3 = Button(container, text="Btn 3", width=100, height=36)
    b3.pack(side="left", padx=5)

    prog = ProgressBar(container, value=50, width=150, height=20)
    prog.pack(side="left", fill="x", expand=True, padx=5)

    root.update_idletasks()
    root.update()

    init_b1_w = b1.winfo_width()
    init_b2_w = b2.winfo_width()
    init_b3_w = b3.winfo_width()
    init_prog_w = prog.winfo_width()

    assert init_b1_w >= 100
    assert init_b2_w >= 100
    assert init_b3_w >= 100
    assert init_prog_w >= 150

    # Shrink window drastically to squeeze widgets
    root.geometry("200x200")
    root.update_idletasks()
    root.update()

    shrunk_b2_w = b2.winfo_width()
    assert shrunk_b2_w < init_b2_w

    # Expand window back to original size
    root.geometry("600x200")
    root.update_idletasks()
    root.update()

    # Verify that buttons and progress bar fully recovered their space
    assert b1.winfo_width() == init_b1_w
    assert b2.winfo_width() == init_b2_w
    assert b3.winfo_width() == init_b3_w
    assert prog.winfo_width() == init_prog_w

    root.update_idletasks()
    container.destroy()
    root.withdraw()


