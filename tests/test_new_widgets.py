"""
Unit tests for new pure vector widgets:
Sparklines, Charts, ColorPicker/ColorWell, Volume/VUMeter, and Toolbar.
"""

import pytest
import tkinter as tk
import tkblend as tb
from tkblend import (
    Sparkline,
    LineChart,
    AreaChart,
    BarChart,
    PieChart,
    DonutChart,
    ColorPicker,
    ColorWell,
    VolumeControl,
    VolumeSlider,
    VUMeter,
    AudioMeter,
    Toolbar,
    ToolbarSeparator,
    get_theme,
    set_theme,
)


@pytest.fixture(scope="module")
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_sparkline_widget(root):
    data = [10, 25, 18, 42, 35, 60, 55, 80]
    sp = Sparkline(root, data=data, kind="line")
    sp.render()
    assert sp.data == [float(v) for v in data]

    # Test area mode
    sp.kind = "area"
    sp.render()

    # Test bar mode
    sp.kind = "bar"
    sp.render()

    # Test winloss mode
    sp.kind = "winloss"
    sp.data = [1, -1, 1, 0, 1, -1]
    sp.render()

    # Test push_data
    sp.push_data(1.0, max_points=10)
    assert len(sp.data) <= 10

    sp.destroy()


def test_chart_widgets(root):
    # LineChart
    lc = LineChart(root, data=[10, 20, 15, 30, 25], title="Network Traffic", smooth=True)
    lc.add_series("Upload", [5, 12, 8, 18, 14], color="#10b981")
    lc.push_data({"Series 1": 35.0, "Upload": 22.0})
    lc.render()
    lc.destroy()

    # AreaChart
    ac = AreaChart(root, data=[100, 200, 150, 300], title="Storage Usage")
    ac.render()
    ac.destroy()

    # BarChart
    bc = BarChart(root, data=[45, 80, 60, 95], categories=["Q1", "Q2", "Q3", "Q4"], show_values=True)
    bc.add_series("2025", [30, 65, 50, 75], color="#f59e0b")
    bc.render()
    bc.destroy()

    # PieChart & DonutChart
    pie = PieChart(root, data={"Chrome": 65, "Firefox": 20, "Safari": 10, "Edge": 5}, title="Browser Share")
    pie.render()
    pie.destroy()

    donut = DonutChart(root, data={"CPU": 45, "RAM": 35, "Disk": 20})
    donut.render()
    donut.destroy()


def test_color_picker_and_well(root):
    changed = []

    def on_color_change(c):
        changed.append(c)

    picker = ColorPicker(root, initial_color="#ef4444", on_change=on_color_change)
    picker.render()
    assert picker.get_color().startswith("#")
    
    picker.set_color("#10b981")
    assert len(changed) > 0
    assert picker.get_color() == "#10B981"
    picker.destroy()

    well = ColorWell(root, color="#3b82f6", on_change=on_color_change)
    well.render()
    assert well.color == "#3b82f6"
    well.destroy()


def test_volume_and_vu_meter(root):
    vol_changes = []

    def on_vol_change(v):
        vol_changes.append(v)

    vol = VolumeControl(root, value=80, on_change=on_vol_change)
    vol.render()
    assert vol.value == 80.0
    assert not vol.is_muted

    # Toggle Mute
    vol.toggle_mute()
    assert vol.is_muted
    assert vol.value == 0.0

    vol.toggle_mute()
    assert not vol.is_muted
    assert vol.value == 80.0

    vol.destroy()

    # VUMeter / AudioMeter
    vu = VUMeter(root, channels=2, mode="segmented")
    vu.set_levels(0.75, 0.60)
    vu.render()

    vu_grad = AudioMeter(root, channels=1, mode="gradient")
    vu_grad.set_levels(0.85)
    vu_grad.render()

    vu.destroy()
    vu_grad.destroy()


def test_toolbar(root):
    toolbar = Toolbar(root, orientation="horizontal", style="floating")
    
    b1 = toolbar.add_button("New", icon="+", command=lambda: None)
    b2 = toolbar.add_button("Save", icon="💾")
    sep = toolbar.add_separator()
    t1 = toolbar.add_toggle("Bold", initial=True)
    spacer = toolbar.add_spacer()
    well = toolbar.add_widget(ColorWell(toolbar, color="#10b981"))
    
    toolbar.pack()
    root.update_idletasks()

    assert len(toolbar._items) >= 5
    toolbar.destroy()


def test_theme_switch_adaptation(root):
    # Verify widgets gracefully re-render on theme switch
    sp = Sparkline(root, data=[10, 20, 30])
    chart = LineChart(root, data=[5, 15, 25])
    picker = ColorPicker(root)
    vol = VolumeControl(root)
    vu = VUMeter(root)
    tb_bar = Toolbar(root)

    set_theme("dark")
    set_theme("light")
    set_theme("dracula")

    sp.destroy()
    chart.destroy()
    picker.destroy()
    vol.destroy()
    vu.destroy()
    tb_bar.destroy()
