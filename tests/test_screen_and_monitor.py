"""
Robust tests for multi-monitor support and screen work-area handling in tkblend.
Covers:
- get_monitor_work_area Win32 ctypes integration, fallbacks, and error boundaries.
- ComboBox dropdown popup positioning, clamping, auto-flipping, and scrolling
  across primary, secondary-left, secondary-right, secondary-top, and constrained monitors.
"""

from __future__ import annotations

import sys
import pytest
import tkinter as tk
from unittest.mock import patch, MagicMock

from tkblend.utils.screen import get_monitor_work_area
import tkblend.utils.screen as screen_module
from tkblend.widgets.combobox import ComboBox, DropdownPopup


@pytest.fixture
def tk_root():
    """Provides a Tk root instance safely cleaned up after each test."""
    try:
        r = tk.Tk()
        r.geometry("400x300+100+100")
        r.update_idletasks()
        yield r
        try:
            r.destroy()
        except Exception:
            pass
    except tk.TclError:
        pytest.skip("Tkinter display not available")


# ============================================================================
# get_monitor_work_area Unit Tests
# ============================================================================

def test_get_monitor_work_area_live_system(tk_root):
    """Test get_monitor_work_area on the live operating system."""
    rect = get_monitor_work_area(100, 100, tk_root)
    assert isinstance(rect, tuple)
    assert len(rect) == 4
    left, top, right, bottom = rect
    assert isinstance(left, int)
    assert isinstance(top, int)
    assert isinstance(right, int)
    assert isinstance(bottom, int)
    assert right > left
    assert bottom > top

    # Widget None should still return valid bounds via default root or fallback
    rect_no_widget = get_monitor_work_area(100, 100, None)
    assert isinstance(rect_no_widget, tuple)
    assert len(rect_no_widget) == 4
    assert rect_no_widget[2] > rect_no_widget[0]
    assert rect_no_widget[3] > rect_no_widget[1]


def test_get_monitor_work_area_extreme_coords(tk_root):
    """Test get_monitor_work_area with extreme positive, negative, and float coordinates."""
    for pt in [(-5000, 100), (10000, 5000), (0, -3000), (150.7, 220.4)]:
        rect = get_monitor_work_area(pt[0], pt[1], tk_root)
        assert len(rect) == 4
        assert rect[2] > rect[0]
        assert rect[3] > rect[1]


def test_get_monitor_work_area_fallback_virtual_root(monkeypatch):
    """Test fallback when Win32 ctypes is unavailable and Tk virtual root exists."""
    monkeypatch.setattr(screen_module, "_user32", None)

    mock_widget = MagicMock(spec=tk.Misc)
    mock_widget.winfo_vrootx.return_value = -1920
    mock_widget.winfo_vrooty.return_value = 0
    mock_widget.winfo_vrootwidth.return_value = 3840
    mock_widget.winfo_vrootheight.return_value = 1080

    rect = get_monitor_work_area(0, 0, mock_widget)
    assert rect == (-1920, 0, -1920 + 3840, 1080)


def test_get_monitor_work_area_fallback_screen_dimensions(monkeypatch):
    """Test fallback when virtual root returns 0 and screenwidth/height are used."""
    monkeypatch.setattr(screen_module, "_user32", None)

    mock_widget = MagicMock(spec=tk.Misc)
    mock_widget.winfo_vrootx.return_value = 0
    mock_widget.winfo_vrooty.return_value = 0
    mock_widget.winfo_vrootwidth.return_value = 0
    mock_widget.winfo_vrootheight.return_value = 0
    mock_widget.winfo_screenwidth.return_value = 1600
    mock_widget.winfo_screenheight.return_value = 900

    rect = get_monitor_work_area(0, 0, mock_widget)
    assert rect == (0, 0, 1600, 900)


def test_get_monitor_work_area_fallback_absolute_default(monkeypatch):
    """Test final fallback (0, 0, 1024, 768) when no widget and no Tk root exist."""
    monkeypatch.setattr(screen_module, "_user32", None)
    monkeypatch.setattr(tk, "_default_root", None)

    rect = get_monitor_work_area(0, 0, None)
    assert rect == (0, 0, 1024, 768)


# ============================================================================
# ComboBox Multi-Monitor Geometry & Clamping Tests
# ============================================================================

def test_combobox_popup_normal_below(tk_root, monkeypatch):
    """Dropdown fits below anchor with margin and gap."""
    # Mock primary monitor work area (0, 0, 1920, 1040)
    monkeypatch.setattr(
        "tkblend.widgets.combobox.get_monitor_work_area",
        lambda x, y, master: (0, 0, 1920, 1040),
    )

    cb = ComboBox(tk_root, values=["A", "B", "C"], width=150, height=36)
    cb.pack(padx=50, pady=50)
    tk_root.update_idletasks()

    cb.on_click(10, 10, 1)
    tk_root.update_idletasks()

    popup = cb._popup
    assert popup is not None
    assert popup.winfo_exists()

    rx, ry, rw, rh = cb.winfo_rootx(), cb.winfo_rooty(), cb.winfo_width(), cb.winfo_height()
    px, py, pw, ph = popup._popup_rect

    # Placed right below anchor with 2px gap
    assert py == ry + rh + 2
    assert px == rx
    assert py + ph <= 1040 - 4
    popup.dismiss()


def test_combobox_popup_autoflip_above(tk_root, monkeypatch):
    """Dropdown auto-flips above anchor when vertical space below is insufficient."""
    # Anchor near bottom of monitor
    monkeypatch.setattr(
        "tkblend.widgets.combobox.get_monitor_work_area",
        lambda x, y, master: (0, 0, 1920, 1000),
    )

    cb = ComboBox(tk_root, values=[f"Item {i}" for i in range(12)], width=150, height=36)
    cb.place(x=100, y=850)
    tk_root.update_idletasks()

    # Force simulated root position near bottom
    cb.winfo_rootx = lambda: 100
    cb.winfo_rooty = lambda: 850

    cb.on_click(10, 10, 1)
    tk_root.update_idletasks()

    popup = cb._popup
    assert popup is not None
    px, py, pw, ph = popup._popup_rect

    # Flipped above: popup bottom is at anchor_ry - 2 (leaving 2px gap above anchor)
    assert py + ph == 850 - 2
    assert py >= 0 + 4
    popup.dismiss()


def test_combobox_popup_secondary_monitor_left(tk_root, monkeypatch):
    """Dropdown on a secondary monitor to the left (negative coordinates) stays negative."""
    # Secondary monitor: left = -1920, top = 0, right = 0, bottom = 1040
    monkeypatch.setattr(
        "tkblend.widgets.combobox.get_monitor_work_area",
        lambda x, y, master: (-1920, 0, 0, 1040),
    )

    cb = ComboBox(tk_root, values=["One", "Two", "Three"], width=150, height=36)
    cb.pack()
    tk_root.update_idletasks()

    # Simulate anchor positioned at x = -500, y = 300 on the left monitor
    cb.winfo_rootx = lambda: -500
    cb.winfo_rooty = lambda: 300

    cb.on_click(10, 10, 1)
    tk_root.update_idletasks()

    popup = cb._popup
    assert popup is not None
    px, py, pw, ph = popup._popup_rect

    # Must be on the left monitor (negative X), NOT clamped to >= 0
    assert px == -500
    assert px + pw <= 0 - 4
    assert px >= -1920 + 4
    assert py == 300 + cb.winfo_height() + 2
    popup.dismiss()


def test_combobox_popup_secondary_monitor_left_right_edge(tk_root, monkeypatch):
    """Dropdown near the right boundary of the left monitor (x ≈ 0) clamps to stay on the left monitor."""
    monkeypatch.setattr(
        "tkblend.widgets.combobox.get_monitor_work_area",
        lambda x, y, master: (-1920, 0, 0, 1040),
    )

    cb = ComboBox(tk_root, values=["Alpha", "Beta", "Gamma"], width=200, height=36)
    cb.pack()
    tk_root.update_idletasks()

    # Anchor at x = -50 on left monitor; popup width 200 would otherwise cross into x > 0
    cb.winfo_rootx = lambda: -50
    cb.winfo_rooty = lambda: 200

    cb.on_click(10, 10, 1)
    tk_root.update_idletasks()

    popup = cb._popup
    assert popup is not None
    px, py, pw, ph = popup._popup_rect

    # Must be clamped so right edge does not exceed mon_right - 4 (-4)
    assert px + pw <= -4
    assert px >= -1920 + 4
    popup.dismiss()


def test_combobox_popup_secondary_monitor_left_left_edge(tk_root, monkeypatch):
    """Dropdown near the extreme left boundary of the left monitor clamps to mon_left + margin."""
    monkeypatch.setattr(
        "tkblend.widgets.combobox.get_monitor_work_area",
        lambda x, y, master: (-1920, 0, 0, 1040),
    )

    cb = ComboBox(tk_root, values=["Alpha", "Beta"], width=200, height=36)
    cb.pack()
    tk_root.update_idletasks()

    # Anchor at -1930 (beyond left boundary)
    cb.winfo_rootx = lambda: -1930
    cb.winfo_rooty = lambda: 200

    cb.on_click(10, 10, 1)
    tk_root.update_idletasks()

    popup = cb._popup
    assert popup is not None
    px, py, pw, ph = popup._popup_rect

    # Clamped to -1920 + margin (-1916)
    assert px == -1916
    popup.dismiss()


def test_combobox_popup_secondary_monitor_top(tk_root, monkeypatch):
    """Dropdown on a secondary monitor positioned above the primary monitor (negative Y)."""
    # Top monitor: left = 0, top = -1080, right = 1920, bottom = 0
    monkeypatch.setattr(
        "tkblend.widgets.combobox.get_monitor_work_area",
        lambda x, y, master: (0, -1080, 1920, 0),
    )

    cb = ComboBox(tk_root, values=["Item 1", "Item 2"], width=150, height=36)
    cb.pack()
    tk_root.update_idletasks()

    # Anchor at y = -400 on top monitor
    cb.winfo_rootx = lambda: 300
    cb.winfo_rooty = lambda: -400

    cb.on_click(10, 10, 1)
    tk_root.update_idletasks()

    popup = cb._popup
    assert popup is not None
    px, py, pw, ph = popup._popup_rect

    # Must be negative Y on top monitor, NOT forced to >= 0
    assert py == -400 + cb.winfo_height() + 2
    assert py + ph <= 0 - 4
    assert py >= -1080 + 4
    popup.dismiss()


def test_combobox_popup_secondary_monitor_right(tk_root, monkeypatch):
    """Dropdown on a secondary monitor positioned to the right (x in [1920, 3840])."""
    monkeypatch.setattr(
        "tkblend.widgets.combobox.get_monitor_work_area",
        lambda x, y, master: (1920, 0, 3840, 1080),
    )

    cb = ComboBox(tk_root, values=["A", "B", "C"], width=150, height=36)
    cb.pack()
    tk_root.update_idletasks()

    cb.winfo_rootx = lambda: 3750
    cb.winfo_rooty = lambda: 300

    cb.on_click(10, 10, 1)
    tk_root.update_idletasks()

    popup = cb._popup
    assert popup is not None
    px, py, pw, ph = popup._popup_rect

    # Clamped to right edge of monitor 2 (3840 - 4 = 3836)
    assert px + pw <= 3836
    assert px >= 1920 + 4
    popup.dismiss()


def test_combobox_popup_height_clamping_and_scroll_update(tk_root, monkeypatch):
    """Dropdown in a vertically constrained monitor clamps height and updates canvas."""
    # Constrained monitor height: only 200px tall
    monkeypatch.setattr(
        "tkblend.widgets.combobox.get_monitor_work_area",
        lambda x, y, master: (0, 0, 1920, 200),
    )

    cb = ComboBox(tk_root, values=[f"Entry {i}" for i in range(30)], width=160, height=36)
    cb.pack()
    tk_root.update_idletasks()

    cb.winfo_rootx = lambda: 100
    cb.winfo_rooty = lambda: 50

    cb.on_click(10, 10, 1)
    tk_root.update_idletasks()

    popup = cb._popup
    assert popup is not None
    px, py, pw, ph = popup._popup_rect

    # Entire popup must fit within [4, 196]
    assert py >= 4
    assert py + ph <= 196
    # Canvas height must be synced
    if popup._canvas is not None:
        c_h = int(popup._canvas.cget("height"))
        assert c_h <= ph
    popup.dismiss()


def test_combobox_popup_width_clamping(tk_root, monkeypatch):
    """Dropdown wider than monitor work area width clamps to max available width."""
    # Very narrow monitor: width 150px
    monkeypatch.setattr(
        "tkblend.widgets.combobox.get_monitor_work_area",
        lambda x, y, master: (0, 0, 150, 800),
    )

    cb = ComboBox(
        tk_root,
        values=["Super extremely long item name that exceeds narrow monitor width"],
        width=300,
        height=36,
    )
    cb.pack()
    tk_root.update_idletasks()

    cb.winfo_rootx = lambda: 20
    cb.winfo_rooty = lambda: 50

    cb.on_click(10, 10, 1)
    tk_root.update_idletasks()

    popup = cb._popup
    assert popup is not None
    px, py, pw, ph = popup._popup_rect

    # Width clamped within monitor bounds
    assert pw <= (150 - 2 * 4)
    assert px >= 4
    assert px + pw <= 150 - 4
    popup.dismiss()
