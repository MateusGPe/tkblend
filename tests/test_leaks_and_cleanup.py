"""
Tests for nanobind leak prevention, memoryview buffer safety, and clean widget lifecycle teardown.
"""

import gc
import tkinter as tk
import pytest
from tkblend._tkblend import (
    Color as NativeColor,
    Surface as NativeSurface,
    DrawBatch,
)
import tkblend as tb
from tkblend.theme import set_theme, get_theme, ThemeManager


@pytest.fixture
def root():
    try:
        r = tk.Tk()
        r.withdraw()
        yield r
        r.destroy()
    except tk.TclError:
        pytest.skip("Tkinter display not available")


def test_widget_lifecycle_leak_prevention(root):
    """Verify that repeatedly creating and destroying widgets leaves zero lingering surfaces or colors."""
    gc.collect()

    for _ in range(10):
        btn = tb.Button(root, text="Test")
        card = tb.Card(root, title="Card")
        badge = tb.Badge(root, text="Badge")
        inp = tb.TextInput(root, placeholder="Input")
        sw = tb.Switch(root)
        spin = tb.SpinBox(root)
        acc = tb.Accordion(root, title="Section")

        root.update_idletasks()

        btn.destroy()
        card.destroy()
        badge.destroy()
        inp.destroy()
        sw.destroy()
        spin.destroy()
        acc.destroy()

    del btn, card, badge, inp, sw, spin, acc
    gc.collect()

    surfaces_alive = [obj for obj in gc.get_objects() if isinstance(obj, NativeSurface)]
    colors_alive = [obj for obj in gc.get_objects() if isinstance(obj, NativeColor)]

    assert len(surfaces_alive) == 0
    assert len(colors_alive) == 0


def test_surface_buffer_memoryview_lifetime(root):
    """Verify that buffer memoryviews maintain parent surface lifetime without reference leaks."""
    surf = tb.Surface(120, 60)
    surf.clear("#3b82f6")
    surf.fill_circle(60, 30, 20, "#ffffff")

    buf = surf.get_buffer()
    assert len(buf) == 120 * 60 * 4
    # Modify buffer through memoryview
    buf[0] = 255

    del buf
    del surf
    gc.collect()

    surfaces_alive = [obj for obj in gc.get_objects() if isinstance(obj, NativeSurface)]
    assert len(surfaces_alive) == 0


def test_theme_manager_weak_listener_pruning(root):
    """Verify that ThemeManager does not retain destroyed or unreferenced widget callbacks."""
    tm = ThemeManager()
    initial_listeners_count = len(tm._listeners)

    def create_and_discard():
        btn = tb.Button(root, text="Transient")
        root.update_idletasks()
        return btn

    btn = create_and_discard()
    btn.destroy()
    del btn
    gc.collect()

    # Trigger notify to prune dead weak references
    tm.notify_listeners()

    # Dead listeners should be pruned
    assert len(tm._listeners) <= initial_listeners_count


def test_file_explorer_complete_teardown_zero_leaks():
    """Verify headless FileExplorerApp initialization and destruction leaves zero memory leaks."""
    gc.collect()

    r = tk.Tk()
    r.withdraw()

    from examples.file_explorer import FileExplorerApp
    app = FileExplorerApp(r)
    r.update_idletasks()

    app.toggle_theme()
    r.update_idletasks()

    r.destroy()
    del app, r
    gc.collect()

    surfaces_alive = [obj for obj in gc.get_objects() if isinstance(obj, NativeSurface)]
    colors_alive = [obj for obj in gc.get_objects() if isinstance(obj, NativeColor)]

    assert len(surfaces_alive) == 0
    assert len(colors_alive) == 0
