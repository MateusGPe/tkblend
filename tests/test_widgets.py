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
    Dropdown,
    ModernDropdown,
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
    inp = TextInput(root, placeholder="Type here...")
    inp.set("Hello tkblend")
    assert inp.get() == "Hello tkblend"
    inp.destroy()


def test_dropdown(root):
    dd = Dropdown(root, options=["First", "Second", "Third"], selected="First")
    dd.render()
    assert dd.value == "First"
    dd._select_option("Second")
    assert dd.value == "Second"
    dd.destroy()


def test_spinbox(root):
    sb = SpinBox(root, min_val=0, max_val=10, value=5, step=1)
    sb.render()
    assert sb.value == 5
    sb.value += 1
    assert sb.value == 6
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
    assert acc._is_open is False
    assert isinstance(acc.content_frame, tk.Frame)
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
