"""
Unit and integration tests for pure vector widgets in tkblend.widgets.
"""

import pytest
import tkinter as tk
from tkblend.widgets import (
    ScalingTracker,
    Widget,
    ModernWidget,
    Frame,
    ModernFrame,
    Card,
    ModernCard,
    Button,
    ModernButton,
    ProgressBar,
    ModernProgressBar,
    CircularProgress,
    ModernCircularProgress,
    Slider,
    ModernSlider,
    RangeSlider,
    ModernRangeSlider,
    Switch,
    ModernSwitch,
    ToggleSwitch,
    Checkbox,
    ModernCheckbox,
    Radio,
    ModernRadio,
    RadioGroup,
    ModernRadioGroup,
    SegmentedControl,
    ModernSegmentedControl,
    TextInput,
    ModernTextInput,
    VectorScrollbar,
    Scrollbar,
    Dropdown,
    ModernDropdown,
    DropdownItem,
    SpinBox,
    ModernSpinBox,
    Badge,
    ModernBadge,
    Avatar,
    ModernAvatar,
    Accordion,
    ModernAccordion,
)
from tkblend.theme import set_theme


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

    # Alias check
    m_btn = ModernButton(root, text="Modern", variant="accent")
    m_btn.render()
    btn.destroy()
    m_btn.destroy()


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
    toggled = []
    sw = Switch(root, is_on=False, on_toggle=lambda state: toggled.append(state))
    sw.render()
    assert sw.is_on is False
    sw.toggle()
    assert sw.is_on is True
    assert toggled == [True]
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
    frame.destroy()
    card.destroy()


def test_theme_switch_redraw(root):
    btn = Button(root, text="Themed")
    btn.render()
    # Trigger theme switch - verifies listeners don't crash
    set_theme("light")
    btn.render()
    set_theme("dark")
    btn.render()
    btn.destroy()
