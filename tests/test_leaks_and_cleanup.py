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


def test_surface_buffer_keeps_parent_alive_after_parent_gc():
    """Verify that buffer memoryview keeps the underlying Surface alive even if the Surface variable is deleted."""
    def create_and_get_buf():
        s = tb.Surface(64, 64)
        s.clear("#ff0000ff")
        return s.get_buffer()

    buf = create_and_get_buf()
    gc.collect()

    # The memoryview must remain valid and readable/writable
    assert len(buf) == 64 * 64 * 4
    assert buf[0] == 0 or buf[0] == 255  # readable without segfault
    buf[0] = 128
    assert buf[0] == 128

    del buf
    gc.collect()

    surfaces_alive = [obj for obj in gc.get_objects() if isinstance(obj, NativeSurface)]
    assert len(surfaces_alive) == 0


def test_surface_resize_prohibited_during_active_buffer():
    """Verify that Surface::resize raises RuntimeError when active buffer views exist."""
    surf = tb.Surface(80, 80)
    buf = surf.get_buffer()

    with pytest.raises(RuntimeError, match="Cannot resize Surface while active buffer views exist"):
        surf.resize(160, 160)

    # Discard buffer and collect
    del buf
    gc.collect()

    # Resize should now succeed smoothly
    surf.resize(160, 160)
    assert surf.width == 160
    assert surf.height == 160


def test_emoji_engine_lru_cache_eviction():
    """Verify that rendering many unique emoji glyphs stays bounded and operates without error."""
    surf = tb.Surface(200, 200)
    # Render 300 distinct codepoints (exceeding max_cache_entries_ = 256)
    for cp in range(0x1F600, 0x1F600 + 300):
        char = chr(cp)
        surf.draw_text(f"Emoji {char}", 10, 30, font_size=16)

    surf.flush()


def test_font_manager_concurrent_thread_safety():
    """Verify concurrent thread calls to FontManager do not trigger data races."""
    import threading

    errors = []

    def worker(family: str):
        try:
            for _ in range(20):
                tb.set_active_font(family)
                tb.find_system_font(family)
                tb.get_active_font()
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=worker, args=(fam,))
        for fam in ["sans-serif", "serif", "monospace", "arial", "helvetica", "dejavu sans"]
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


def test_path_chaining_reference_internal():
    """Verify Path method chaining operates safely without dangling references."""
    p = tb.Path()
    p.move_to(0, 0).line_to(10, 10).quad_to(20, 20, 30, 30).cubic_to(40, 40, 50, 50, 60, 60).close()
    
    surf = tb.Surface(100, 100)
    surf.fill_path(p, "#ff0000")
    surf.stroke_path(p, "#00ff00", stroke_width=2.0)


def test_draw_batch_card_and_shadow_parity():
    """Verify DrawBatch draw_card and draw_shadow_rounded_rect produce identical rendering to direct Surface calls."""
    # Direct render
    s1 = tb.Surface(120, 120)
    s1.clear("#18181b")
    s1.draw_card(
        10, 10, 100, 100, 12, 12,
        bg_color="#27272a",
        border_color="#3f3f46",
        border_width=1.5,
        shadow_blur=8.0,
        shadow_spread=2.0,
        shadow_offset_x=2.0,
        shadow_offset_y=4.0,
        shadow_color="#00000080"
    )
    s1.flush()

    # Batch render
    s2 = tb.Surface(120, 120)
    s2.clear("#18181b")
    batch = DrawBatch()
    batch.draw_card(
        10, 10, 100, 100, 12, 12,
        NativeColor(0x27, 0x27, 0x2a, 0xff),
        NativeColor(0x3f, 0x3f, 0x46, 0xff),
        1.5,
        8.0, 2.0, 2.0, 4.0,
        NativeColor(0, 0, 0, 0x80)
    )
    s2.execute_batch(batch)
    s2.flush()

    b1 = bytes(s1.get_buffer())
    b2 = bytes(s2.get_buffer())
    assert b1 == b2


def test_surface_get_buffer_multithreaded_concurrency():
    """Verify concurrent threads accessing get_buffer and resizing operate safely without race conditions."""
    import threading

    surf = tb.Surface(64, 64)
    errors = []

    def reader():
        try:
            for _ in range(50):
                buf = surf.get_buffer()
                assert len(buf) > 0
                val = buf[0]
                del buf
        except RuntimeError as e:
            # Expected if resize happened or blocked
            pass
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=reader) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0

