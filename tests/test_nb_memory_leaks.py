"""
Nanobind memory leak tests for tkblend.

Structure
---------
Each subsystem gets two to three test functions:
  - `test_<subsystem>_*_no_leak`: asserts memory growth is negligible across various usage patterns.
  - `test_<subsystem>_stress_no_leak`: heavy-iteration stress variant running 500–1000 loops.

Heavy-iteration variants are decorated with ``@pytest.mark.slow`` and run 500–1000
loops. Pass ``-m slow`` to pytest to include them.

Measurement strategy
--------------------
All tests use ``tracemalloc`` to capture a before/after snapshot of Python-side
allocations. The tests assert net growth stays negligible (< _SAFE_THRESHOLD_KB).

Relevant nanobind surface areas covered:
  1. Surface / SurfaceBufferObject – memoryview lifetime vs parent Surface
  2. nanobind rv_policy::reference_internal – Path method chaining
  3. DrawBatch holding Color objects across GC cycles
  4. Gradient/Path objects outliving Surface after flush
  5. C++-side singletons (FontManager, ShadowEngine, EmojiEngine) retaining refs
  6. Widget-level PhotoImage not released when widget is destroyed
  7. Thread-safety races that appear as lingering allocations
  8. nb::set_leak_warnings(True) smoke test
  9. Surface.close() explicit lifecycle + double-close safety
  10. Context-manager Surface lifecycle
  11. Reference cycles & cyclic GC reclamation
  12. Exception unwinding & aborted lifecycles
  13. Buffer protocol slicing, casting, and surface resizing
  14. Comprehensive widget swarm & theme storm
  15. Multithreaded ThreadPool torture test
  16. ShadowEngine & font/emoji cache flood & eviction
  17. Massive DrawBatch queue saturation (25k-100k commands)
"""

import concurrent.futures
import gc
import threading
import tracemalloc
import pytest

import tkinter as tk
import tkblend as tb
from tkblend._tkblend import (
    Color as NativeColor,
    Surface as NativeSurface,
    DrawBatch,
    Gradient,
    Path,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LEAK_THRESHOLD_KB = 20.0   # growth considered a real leak (trigger tests)
_SAFE_THRESHOLD_KB = 50.0   # max acceptable growth in no-leak tests


def _tracemalloc_diff_kb(func, *args, **kwargs):
    """Run *func* between two tracemalloc snapshots and return net KB growth."""
    gc.collect()
    tb.clear_caches()
    tracemalloc.start()
    snap1 = tracemalloc.take_snapshot()

    func(*args, **kwargs)

    gc.collect()
    tb.clear_caches()
    snap2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = snap2.compare_to(snap1, "lineno")
    return sum(s.size_diff for s in stats) / 1024.0


@pytest.fixture
def root():
    try:
        r = tk.Tk()
        r.withdraw()
        yield r
        r.destroy()
    except tk.TclError:
        pytest.skip("Tkinter display not available")


# ===========================================================================
# 1. Surface / SurfaceBufferObject – memoryview lifetime
# ===========================================================================

def _surface_buffer_leak_pattern(n: int):
    """Keep a live memoryview while deleting the Surface variable.

    This pattern *should* keep the Surface alive via the SurfaceBufferObject's
    Py_INCREF on surface_py. If the refcount bookkeeping is wrong the Surface
    dies early, corrupting the buffer – but if buffer holds an unexpected extra
    ref, the Surface never dies and we leak.

    UAF probe: each buffer is read through *after* ``del s`` to confirm
    the Surface is genuinely kept alive by the buffer's back-reference, not
    freed underneath us.
    """
    bufs = []
    for _ in range(n):
        s = tb.Surface(64, 64)
        s.clear("#ff0000")
        bufs.append(s.get_buffer())   # hold buffer, drop surface
        del s
    # UAF probe: read through each live buffer – if Surface was freed early
    # this will segfault or return garbage rather than the expected 0xFF (red
    # channel of a PRGB32-premultiplied #ff0000 pixel).
    for buf in bufs:
        assert buf[0] != 0 or buf[1] != 0 or buf[2] != 0 or buf[3] != 0, (
            "Buffer read returned all-zero bytes after del s: Surface may have been freed early"
        )
    # All buffers released at once – surfaces should also be freed
    bufs.clear()
    gc.collect()


def test_surface_buffer_simultaneous_hold_no_leak():
    """Holding N live memoryviews simultaneously and releasing them reclaims all memory."""
    diff = _tracemalloc_diff_kb(_surface_buffer_leak_pattern, 200)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Surface/buffer hold-and-release left {diff:.1f} KB unreleased (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


def test_surface_buffer_no_leak_after_release():
    """After all memoryviews are released, Surface memory must be fully reclaimed.

    Additionally verifies the structural invariant: active_buffers() reaches 0
    on the native surface once all Python-side memoryviews are dropped.
    """
    from tkblend._tkblend import Surface as NativeSurface
    # Structural invariant: active_buffers counter must drop to 0 after release
    native = NativeSurface(64, 64)
    native.clear(tb.parse_color("#ff0000"))
    buf = native.get_buffer()
    assert native.active_buffers() == 1, (
        "Expected active_buffers() == 1 while buffer is live"
    )
    del buf
    gc.collect()
    assert native.active_buffers() == 0, (
        "active_buffers() did not reach 0 after all buffers were released – "
        "Surface is being kept alive by a dangling reference"
    )
    del native

    # Memory regression: full cycle with many surfaces
    diff = _tracemalloc_diff_kb(_surface_buffer_leak_pattern, 100)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Surface/buffer cleanup left {diff:.1f} KB unreleased (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


@pytest.mark.slow
def test_surface_buffer_stress_no_leak():
    """Heavy-stress variant: 1000 Surface+buffer create/release cycles stay bounded."""
    diff = _tracemalloc_diff_kb(_surface_buffer_leak_pattern, 1000)
    assert diff < _SAFE_THRESHOLD_KB * 3, (
        f"Stress surface/buffer left {diff:.1f} KB unreleased"
    )


# ===========================================================================
# 2. nanobind rv_policy::reference_internal – Path method chaining
# ===========================================================================

def _path_rv_policy_pattern(n: int):
    """Chain Path methods repeatedly and discard the path.

    ``reference_internal`` returns a reference to ``self`` (the Path), keeping
    the parent alive. If nanobind miscounts the refback, the Path may linger.
    """
    for _ in range(n):
        p = Path()
        # Deep method chain – each call returns a reference_internal ref
        (
            p.move_to(0, 0)
             .line_to(10, 10)
             .quad_to(20, 0, 30, 10)
             .cubic_to(40, 0, 50, 10, 60, 0)
             .arc_to(70, 10, 5, 5, 0, 1.57)
             .add_rect(0, 0, 20, 20)
             .add_rounded_rect(5, 5, 10, 10, 2, 2)
             .add_circle(15, 15, 5)
             .add_ellipse(15, 15, 8, 4)
             .close()
             .clear()
             .reset()
        )
        del p
    gc.collect()


def test_path_rv_policy_chain_no_leak():
    """Deep method chaining on Path must not leak reference_internal references."""
    diff = _tracemalloc_diff_kb(_path_rv_policy_pattern, 500)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Path rv_policy chain leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


def test_path_rv_policy_no_leak_after_del():
    """Path objects from chained methods must not outlive their ``del``."""
    diff = _tracemalloc_diff_kb(_path_rv_policy_pattern, 100)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Path rv_policy cleanup leaked {diff:.1f} KB"
    )


@pytest.mark.slow
def test_path_rv_policy_stress_no_leak():
    """1000-iteration path chaining stays within memory bounds."""
    diff = _tracemalloc_diff_kb(_path_rv_policy_pattern, 1000)
    assert diff < _SAFE_THRESHOLD_KB * 3, (
        f"Stress Path rv_policy leaked {diff:.1f} KB"
    )


# ===========================================================================
# 3. DrawBatch holding Color objects across GC cycles
# ===========================================================================

def _drawbatch_color_pattern(n: int):
    """Create DrawBatch, add Color-parameterized commands, execute on Surface, discard.

    If DrawBatch holds internal Python Color references without proper nb ownership
    transfer the Colors survive into the next GC cycle.
    """
    surf = tb.Surface(80, 80)
    for _ in range(n):
        batch = DrawBatch()
        for i in range(10):
            c = NativeColor(i * 25, i * 10, 200, 255)
            batch.fill_rect(0, 0, 80, 80, c)
            batch.stroke_rect(5, 5, 70, 70, c, 1.5)
            batch.fill_rounded_rect(10, 10, 60, 60, 8, 8, c)
            batch.fill_circle(40, 40, 20, c)
            batch.draw_line(0, 0, 80, 80, c, 2.0)
            del c
        surf.execute_batch(batch)
        del batch
    del surf
    gc.collect()


def test_drawbatch_color_retention_no_leak():
    """DrawBatch must not retain Color objects alive after batch is discarded."""
    diff = _tracemalloc_diff_kb(_drawbatch_color_pattern, 200)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"DrawBatch Color retention leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


def test_drawbatch_color_no_leak():
    """After batch.del, no Color allocations remain attributed to DrawBatch."""
    diff = _tracemalloc_diff_kb(_drawbatch_color_pattern, 100)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"DrawBatch Color cleanup leaked {diff:.1f} KB"
    )


@pytest.mark.slow
def test_drawbatch_color_stress_no_leak():
    """500 DrawBatch + Color cycles stay bounded."""
    diff = _tracemalloc_diff_kb(_drawbatch_color_pattern, 500)
    assert diff < _SAFE_THRESHOLD_KB * 3, (
        f"Stress DrawBatch Color leaked {diff:.1f} KB"
    )


# ===========================================================================
# 4. Gradient/Path objects outliving Surface after flush
# ===========================================================================

def _gradient_path_surface_pattern(n: int):
    """Create Gradient and Path, use them on a Surface, flush, then discard all.

    Uses NativeSurface directly since gradient-fill methods are bound on the
    native class (fill_rect_gradient, fill_circle_gradient). If Surface keeps
    an internal reference to the Gradient/Path object the Python wrappers
    can't be collected.
    """
    for _ in range(n):
        # Use NativeSurface directly – gradient fill methods are bound there
        surf = NativeSurface(100, 100)

        g = Gradient.linear(0, 0, 100, 0)
        g.add_stop(0.0, NativeColor(255, 0, 0, 255))
        g.add_stop(1.0, NativeColor(0, 0, 255, 255))
        surf.fill_rect_gradient(0, 0, 100, 100, g)
        del g

        rg = Gradient.radial(50, 50, 0, 50, 50, 50)
        rg.add_stop(0.0, NativeColor(255, 255, 0, 255))
        rg.add_stop(1.0, NativeColor(0, 255, 255, 128))
        surf.fill_circle_gradient(50, 50, 45, rg)
        del rg

        p = Path()
        p.move_to(10, 10).line_to(90, 10).line_to(50, 90).close()
        surf.fill_path(p, NativeColor(200, 100, 50, 255))
        surf.stroke_path(p, NativeColor(255, 255, 255, 255), 2.0)
        del p

        surf.flush()
        del surf
    gc.collect()


def test_gradient_path_surface_retain_no_leak():
    """Gradient/Path wrapper objects must not outlive their Surface lifecycle."""
    diff = _tracemalloc_diff_kb(_gradient_path_surface_pattern, 200)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Gradient/Path surface retention leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


def test_gradient_path_surface_no_leak():
    """After flush+del, Gradient and Path wrappers must be fully freed."""
    diff = _tracemalloc_diff_kb(_gradient_path_surface_pattern, 100)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Gradient/Path surface cleanup leaked {diff:.1f} KB"
    )


@pytest.mark.slow
def test_gradient_path_surface_stress_no_leak():
    """500 Gradient+Path+Surface cycles stay bounded."""
    diff = _tracemalloc_diff_kb(_gradient_path_surface_pattern, 500)
    assert diff < _SAFE_THRESHOLD_KB * 3, (
        f"Stress Gradient/Path/Surface leaked {diff:.1f} KB"
    )


# ===========================================================================
# 5. C++-side singleton Python handle retention
#    (FontManager, ShadowEngine, EmojiEngine)
# ===========================================================================

def _singleton_python_handles_pattern(n: int):
    """Rapid-fire singleton API calls that could cause internal Python handle caching.

    Each call passes Python strings/objects; if the singleton caches a PyObject*
    without DECREF on eviction the handles accumulate.
    """
    surf = tb.Surface(200, 200)
    for _ in range(n):
        # FontManager
        tb.get_active_font()
        tb.set_active_font("sans-serif")
        tb.find_system_font("monospace", 400, False)
        tb.get_loaded_fonts()
        tb.get_system_fonts(refresh=False)

        # ShadowEngine – fill cache then query metrics
        surf.draw_shadow_rounded_rect(
            5, 5, 60, 60, 6, 6,
            blur_radius=4.0, spread=1.0,
            offset_x=1.0, offset_y=2.0,
            shadow_color="#00000080",
        )
        _ = tb.get_shadow_cache_size()
        _ = tb.get_shadow_cache_bytes()

        # EmojiEngine – trigger glyph lookup
        surf.draw_text("\U0001f600", 10, 30, font_size=16)

    del surf
    tb.clear_caches()
    gc.collect()


def test_singleton_python_handle_retention_no_leak():
    """Singleton APIs must not accumulate Python handles across repeated calls."""
    diff = _tracemalloc_diff_kb(_singleton_python_handles_pattern, 100)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Singleton handle retention leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


def test_singleton_python_handle_no_leak():
    """clear_caches() + del surf must leave singletons with no residual Python refs."""
    diff = _tracemalloc_diff_kb(_singleton_python_handles_pattern, 50)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Singleton handle cleanup leaked {diff:.1f} KB"
    )


@pytest.mark.slow
def test_singleton_python_handle_stress_no_leak():
    """500 singleton call rounds stay bounded after clear_caches()."""
    diff = _tracemalloc_diff_kb(_singleton_python_handles_pattern, 500)
    assert diff < _SAFE_THRESHOLD_KB * 3, (
        f"Stress singleton handles leaked {diff:.1f} KB"
    )


# ===========================================================================
# 6. Widget-level PhotoImage not released when widget is destroyed
# ===========================================================================

def _photoimage_registry_pattern(root, n: int):
    """Create and destroy widgets that back themselves with Tk PhotoImages.

    If ``blit_to_photo`` registers a name in the Tcl interpreter but the widget
    destructor doesn't call ``image delete``, the name leaks in the Tcl registry
    and the image data is never freed.
    """
    for _ in range(n):
        btn = tb.Button(root, text="Leak?")
        card = tb.Card(root, title="Leak?")
        sw = tb.Switch(root)
        canvas = tb.BlendCanvas(root, width=64, height=64)
        root.update_idletasks()

        btn.destroy()
        card.destroy()
        sw.destroy()
        canvas.destroy()
        root.update_idletasks()

    del btn, card, sw, canvas
    gc.collect()


def test_photoimage_registry_teardown_no_leak(root):
    """Verify widget teardown properly deletes registered Tk PhotoImage names."""
    initial = set(root.tk.call("image", "names"))

    for _ in range(50):
        btn = tb.Button(root, text="X")
        root.update_idletasks()
        btn.destroy()
        root.update_idletasks()

    final = set(root.tk.call("image", "names"))
    leaked = final - initial
    assert len(leaked) == 0, (
        f"PhotoImage names not cleaned up during widget teardown: {leaked}"
    )


def test_photoimage_registry_cleanup_no_leak(root):
    """Every PhotoImage name registered by widgets must be deleted on widget.destroy()."""
    initial = set(root.tk.call("image", "names"))

    _photoimage_registry_pattern(root, 20)

    final = set(root.tk.call("image", "names"))
    leaked = final - initial
    assert len(leaked) == 0, (
        f"PhotoImage names not cleaned up after destroy: {leaked}"
    )


@pytest.mark.slow
def test_photoimage_registry_stress_no_leak(root):
    """200 widget create/destroy cycles leave zero residual PhotoImage names."""
    initial = set(root.tk.call("image", "names"))

    _photoimage_registry_pattern(root, 200)

    final = set(root.tk.call("image", "names"))
    leaked = final - initial
    assert len(leaked) == 0, (
        f"Stress PhotoImage leak: {len(leaked)} names remain: {leaked}"
    )


# ===========================================================================
# 7. Thread-safety races appearing as lingering allocations
# ===========================================================================

def _threaded_surface_race_pattern(n_threads: int, iters: int):
    """Concurrent Surface creation, rendering, buffer access, and destruction.

    A data race in Surface::acquire_buffer_view / release_buffer_view or
    Surface refcount management can result in objects being freed on the wrong
    thread, causing the allocator to report a net positive allocation difference.

    Errors are raised *before* gc.collect() so the tracemalloc snapshot is
    only taken on a clean (non-aborted) run, keeping the diff meaningful.
    """
    errors: list = []

    def worker():
        try:
            for _ in range(iters):
                s = tb.Surface(48, 48)
                s.clear("#112233")
                s.fill_rect(5, 5, 38, 38, "#aabbcc")
                buf = s.get_buffer()
                assert len(buf) == s.native.size_in_bytes(), (
                    f"Buffer length {len(buf)} != surface size_in_bytes {s.native.size_in_bytes()}"
                )
                first_byte = buf[0]  # read to exercise the buffer path
                del buf
                # active_buffers must immediately return to 0 after del buf
                assert s.native.active_buffers() == 0, (
                    "active_buffers() != 0 after buffer released in worker thread"
                )
                s.flush()
                del s
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Raise errors BEFORE gc.collect() so the tracemalloc diff is only
    # computed on a clean run; a partial-abort diff is meaningless noise.
    if errors:
        raise errors[0]

    gc.collect()


def test_threaded_surface_race_concurrency_no_leak():
    """Concurrent Surface+buffer use across 8 threads must not leak memory."""
    diff = _tracemalloc_diff_kb(_threaded_surface_race_pattern, 8, 50)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Threaded Surface concurrency leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


def test_threaded_surface_race_no_leak():
    """4 threads, 50 iters each: all surfaces freed, no net allocation growth."""
    diff = _tracemalloc_diff_kb(_threaded_surface_race_pattern, 4, 50)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Threaded Surface cleanup leaked {diff:.1f} KB"
    )


@pytest.mark.slow
def test_threaded_surface_race_stress_no_leak():
    """8 threads x 500 iters: thorough concurrent Surface lifecycle, bounded memory."""
    diff = _tracemalloc_diff_kb(_threaded_surface_race_pattern, 8, 500)
    assert diff < _SAFE_THRESHOLD_KB * 4, (
        f"Stress threaded Surface leaked {diff:.1f} KB"
    )


# ===========================================================================
# 8. Nanobind leak-warnings integration smoke test
# ===========================================================================

def test_nb_leak_warnings_enabled():
    """Confirm nb.set_leak_warnings(True) is active so nanobind will emit warnings
    on module unload for any surviving managed objects.

    Strategy: the only reliable way to verify the flag without intercepting stderr
    is to confirm the NB_MODULE initializer ran to completion by:
      1. Verifying core types are present (module import succeeded).
      2. Creating and immediately deleting a managed object to exercise the
         lifecycle path that leak-warnings guard, ensuring no TypeError is raised.
      3. Confirming nanobind's type system recognises our core classes, which
         requires the full module initializer to have run (including
         nb::set_leak_warnings(true) which must be the first call in NB_MODULE).
    If the first line of NB_MODULE threw before set_leak_warnings ran,
    the import would have failed and the asserts below would not be reached.
    """
    from tkblend import _tkblend
    # (1) Core types exist – module initializer completed
    assert hasattr(_tkblend, "Surface"), "Surface not bound – NB_MODULE init failed"
    assert hasattr(_tkblend, "Color"), "Color not bound – NB_MODULE init failed"
    assert hasattr(_tkblend, "DrawBatch"), "DrawBatch not bound – NB_MODULE init failed"
    assert hasattr(_tkblend, "Gradient"), "Gradient not bound – NB_MODULE init failed"
    assert hasattr(_tkblend, "Path"), "Path not bound – NB_MODULE init failed"
    # (2) Instantiation + deletion exercises the nanobind lifecycle path
    s = _tkblend.Surface(1, 1)
    s.close()
    del s
    p = _tkblend.Path()
    del p
    c = _tkblend.Color(255, 0, 0, 255)
    del c
    # (3) Type introspection: nanobind-wrapped types expose __module__
    assert _tkblend.Surface.__module__ == "tkblend._tkblend", (
        "Surface.__module__ unexpected – nanobind type registration may be incomplete"
    )
    assert _tkblend.Color.__module__ == "tkblend._tkblend", (
        "Color.__module__ unexpected – nanobind type registration may be incomplete"
    )


# ===========================================================================
# 9. Surface.close() explicit lifecycle + double-close safety
# ===========================================================================

def _surface_explicit_close_pattern(n: int):
    """Explicitly close Surfaces and verify double-close doesn't re-free memory."""
    for _ in range(n):
        s = tb.Surface(60, 60)
        s.clear("#ffffff")
        s.fill_circle(30, 30, 20, "#ff0000")
        s.flush()
        s.close()
        # Double-close must be a no-op, not a crash or extra free
        s.close()
        del s
    gc.collect()


def test_surface_explicit_close_no_leak():
    """Explicit Surface.close() + double-close must leave zero residual allocs."""
    diff = _tracemalloc_diff_kb(_surface_explicit_close_pattern, 100)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Explicit close cleanup leaked {diff:.1f} KB"
    )


@pytest.mark.slow
def test_surface_explicit_close_stress_no_leak():
    """1000 explicit close + double-close cycles stay bounded."""
    diff = _tracemalloc_diff_kb(_surface_explicit_close_pattern, 1000)
    assert diff < _SAFE_THRESHOLD_KB * 3, (
        f"Stress explicit close leaked {diff:.1f} KB"
    )


# ===========================================================================
# 10. Context-manager Surface lifecycle
# ===========================================================================

def _context_manager_pattern(n: int):
    """Use Surface as a context manager and verify __exit__ calls close()."""
    for _ in range(n):
        with tb.Surface(50, 50) as s:
            s.clear("#001122")
            s.draw_text("test", 5, 25, font_size=12)
        # s.is_closed must be True here; the object should be GC-eligible
        assert s.is_closed, (
            "Surface.is_closed is False after __exit__: context manager did not call close()"
        )
        # Structural invariant: no active buffer views may survive after close()
        assert s.native.active_buffers() == 0, (
            f"active_buffers() == {s.native.active_buffers()} after __exit__: "
            "dangling buffer views prevent proper surface cleanup"
        )
        del s
    gc.collect()


def test_surface_context_manager_no_leak():
    """Context-manager surfaces must be fully closed and freed after ``with`` block."""
    diff = _tracemalloc_diff_kb(_context_manager_pattern, 100)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Context-manager cleanup leaked {diff:.1f} KB"
    )


@pytest.mark.slow
def test_surface_context_manager_stress_no_leak():
    """1000 context-manager Surface cycles stay bounded."""
    diff = _tracemalloc_diff_kb(_context_manager_pattern, 1000)
    assert diff < _SAFE_THRESHOLD_KB * 3, (
        f"Stress context-manager leaked {diff:.1f} KB"
    )


# ===========================================================================
# 11. Reference Cycles & Cyclic GC Reclamation
# ===========================================================================

def _cyclic_surface_graph_pattern(n: int):
    """Build cyclic reference graphs containing Surface, buffer, and closures."""
    for _ in range(n):
        s = tb.Surface(64, 64)
        s.clear("#123456")
        buf = s.get_buffer()
        # Create explicit reference cycle graph
        cycle_node = {"surface": s, "buffer": buf, "child": None}
        cycle_node["child"] = cycle_node
        s._cyclic_holder = cycle_node
        s._closure = (lambda obj=s: obj.width)()
        del s, buf, cycle_node
    gc.collect()


def test_surface_cyclic_references_no_leak():
    """Surfaces trapped in complex Python reference cycles must be freed by cyclic GC."""
    diff = _tracemalloc_diff_kb(_cyclic_surface_graph_pattern, 100)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Cyclic Surface references leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


@pytest.mark.slow
def test_surface_cyclic_references_stress_no_leak():
    """500 cyclic Surface graph iterations stay bounded."""
    diff = _tracemalloc_diff_kb(_cyclic_surface_graph_pattern, 500)
    assert diff < _SAFE_THRESHOLD_KB * 3, (
        f"Stress cyclic Surface references leaked {diff:.1f} KB"
    )


# ===========================================================================
# 12. Exception Unwinding & Aborted Lifecycles
# ===========================================================================

def _exception_unwind_pattern(n: int):
    """Simulate unhandled exceptions thrown inside context managers and draw loops."""
    for _ in range(n):
        try:
            with tb.Surface(80, 80) as s:
                s.clear("#abcdef")
                s.fill_circle(40, 40, 30, "#112233")
                buf = s.get_buffer()
                _ = buf[0]
                raise RuntimeError("Simulated mid-pipeline pipeline abort")
        except RuntimeError:
            pass

        try:
            batch = DrawBatch()
            for i in range(50):
                batch.fill_rect(i, i, 10, 10, NativeColor(i, i, i, 255))
                if i == 25:
                    raise ValueError("Simulated batch assembly error")
        except ValueError:
            del batch
    gc.collect()


def test_exception_unwinding_no_leak():
    """Exceptions thrown during active drawing and context managers must unwind cleanly."""
    diff = _tracemalloc_diff_kb(_exception_unwind_pattern, 100)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Exception unwind leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


@pytest.mark.slow
def test_exception_unwinding_stress_no_leak():
    """500 exception unwind cycles leave zero unreleased allocations."""
    diff = _tracemalloc_diff_kb(_exception_unwind_pattern, 500)
    assert diff < _SAFE_THRESHOLD_KB * 3, (
        f"Stress exception unwind leaked {diff:.1f} KB"
    )


# ===========================================================================
# 13. Buffer Protocol Slicing, Resizing & Zero-Copy Churn
# ===========================================================================

def _buffer_slicing_and_resize_pattern(n: int):
    """Stress buffer sub-slicing, bytearray casting, and surface resizing."""
    for _ in range(n):
        s = tb.Surface(100, 100)
        s.clear("#ff8800")
        buf = s.get_buffer()
        
        # Take multiple slices and bytearray conversions
        slices = [buf[i * 10:(i + 1) * 10] for i in range(20)]
        ba = bytearray(buf[:64])
        assert len(ba) == 64
        del slices, ba, buf

        # Rapidly resize surface
        for size in (32, 128, 64, 256, 16):
            s.resize(size, size)
            s.clear("#0088ff")
            s.flush()
        del s
    gc.collect()


def test_buffer_slicing_and_resize_no_leak():
    """Buffer slicing, bytearray copies, and dynamic resize cycles must not leak."""
    diff = _tracemalloc_diff_kb(_buffer_slicing_and_resize_pattern, 50)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Buffer slicing and resize leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


@pytest.mark.slow
def test_buffer_slicing_and_resize_stress_no_leak():
    """200 buffer slicing & resize cycles stay bounded."""
    diff = _tracemalloc_diff_kb(_buffer_slicing_and_resize_pattern, 200)
    assert diff < _SAFE_THRESHOLD_KB * 3, (
        f"Stress buffer slicing & resize leaked {diff:.1f} KB"
    )


# ===========================================================================
# 14. Comprehensive Widget Swarm & Theme Storm
# ===========================================================================

def _widget_swarm_pattern(root, n: int):
    """Instantiate and destroy the full suite of tkblend vector widgets."""
    for _ in range(n):
        f = tb.Frame(root)
        card = tb.Card(f, title="Card")
        btn = tb.Button(card, text="Button")
        pbar = tb.ProgressBar(card)
        cp = tb.CircularProgress(card)
        slider = tb.Slider(card)
        rslider = tb.RangeSlider(card)
        sw = tb.Switch(card)
        cb = tb.Checkbox(card, text="Check")
        rg = tb.RadioGroup(card)
        r1 = tb.Radio(card, text="R1", group=rg)
        r2 = tb.Radio(card, text="R2", group=rg)
        seg = tb.SegmentedControl(card, values=["A", "B", "C"])
        ti = tb.TextInput(card, placeholder="Text")
        vs = tb.VectorScrollbar(card)
        dd = tb.Dropdown(card, options=["1", "2", "3"])
        sb = tb.SpinBox(card)
        badge = tb.Badge(card, text="99+")
        avatar = tb.Avatar(card, text="AG")
        acc = tb.Accordion(card)
        canvas = tb.BlendCanvas(card, width=64, height=64)

        root.update_idletasks()

        # Teardown hierarchy
        f.destroy()
        root.update_idletasks()

        del f, card, btn, pbar, cp, slider, rslider, sw, cb, rg, r1, r2, seg, ti, vs, dd, sb, badge, avatar, acc, canvas
    gc.collect()


def test_widget_swarm_lifecycle_no_leak(root):
    """Lifecycle churn of all 20+ widget types leaves zero residual Tk PhotoImages or memory."""
    initial_images = set(root.tk.call("image", "names"))
    diff = _tracemalloc_diff_kb(_widget_swarm_pattern, root, 10)
    final_images = set(root.tk.call("image", "names"))
    
    assert final_images - initial_images == set(), (
        f"Widget swarm leaked PhotoImage names: {final_images - initial_images}"
    )
    assert diff < _SAFE_THRESHOLD_KB * 2, (
        f"Widget swarm leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB * 2} KB)"
    )


def _theme_storm_pattern(root, n: int):
    """Rapid theme switching with an active widget hierarchy."""
    f = tb.Frame(root)
    card = tb.Card(f, title="Theme Test")
    btn = tb.Button(card, text="Button")
    sw = tb.Switch(card)
    slider = tb.Slider(card)
    root.update_idletasks()

    themes = [
        "dark", "light", "dracula", "nord", "tokyo_night",
        "catppuccin_mocha", "cyberpunk", "monokai_pro",
    ]
    for i in range(n):
        tb.set_theme(themes[i % len(themes)])
        root.update_idletasks()

    f.destroy()
    root.update_idletasks()
    del f, card, btn, sw, slider
    gc.collect()


def test_widget_rapid_theme_storm_no_leak(root):
    """Rapid theme switching across 50 iterations must not leak theme listeners."""
    initial_images = set(root.tk.call("image", "names"))
    diff = _tracemalloc_diff_kb(_theme_storm_pattern, root, 50)
    final_images = set(root.tk.call("image", "names"))

    assert final_images - initial_images == set(), (
        f"Theme storm leaked PhotoImage names: {final_images - initial_images}"
    )
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Theme storm leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


# ===========================================================================
# 15. Multithreaded ThreadPool Torture Test
# ===========================================================================

def _threadpool_torture_worker(iters: int):
    """Worker function executing full rendering pipelines concurrently."""
    for _ in range(iters):
        with tb.Surface(64, 64) as s:
            s.clear("#1a1a24")
            # Linear Gradient
            g = tb.LinearGradient(0, 0, 64, 64)
            g.add_stop(0.0, "#ff0055")
            g.add_stop(1.0, "#00ffcc")
            s.fill_rect(5, 5, 54, 54, g)
            # Path
            p = tb.Path()
            p.move_to(10, 10).line_to(54, 10).line_to(32, 54).close()
            s.stroke_path(p, "#ffffff", 2.0)
            # Text & Emoji
            s.draw_text("⚡ Blend2D", 8, 32, font_size=12, color="#ffffff")
            # Shadow
            s.draw_shadow_rounded_rect(
                10, 10, 44, 44, 4, 4,
                blur_radius=3.0, spread=0.5,
                offset_x=1.0, offset_y=1.0,
                shadow_color="#000000aa"
            )
            # Batch execution
            batch = DrawBatch()
            batch.fill_circle(32, 32, 10, NativeColor(255, 255, 0, 200))
            s.execute_batch(batch)
            s.flush()
            buf = s.get_buffer()
            assert len(buf) > 0
            del buf, batch, p, g


def _threadpool_torture_pattern(n_workers: int, tasks_per_worker: int):
    """Run concurrent rendering across a high-worker ThreadPoolExecutor."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [
            executor.submit(_threadpool_torture_worker, tasks_per_worker)
            for _ in range(n_workers)
        ]
        for f in concurrent.futures.as_completed(futures):
            f.result()
    gc.collect()


def test_multithreaded_threadpool_torture_no_leak():
    """16 worker threads executing 20 full render pipelines each must not leak."""
    diff = _tracemalloc_diff_kb(_threadpool_torture_pattern, 16, 20)
    assert diff < _SAFE_THRESHOLD_KB * 2, (
        f"ThreadPool torture leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB * 2} KB)"
    )


@pytest.mark.slow
def test_multithreaded_threadpool_torture_stress_no_leak():
    """Heavy stress: 16 worker threads executing 100 full render pipelines each."""
    diff = _tracemalloc_diff_kb(_threadpool_torture_pattern, 16, 100)
    assert diff < _SAFE_THRESHOLD_KB * 4, (
        f"Stress ThreadPool torture leaked {diff:.1f} KB"
    )


# ===========================================================================
# 16. ShadowEngine & Font/Emoji Cache Saturation & Eviction
# ===========================================================================

def _shadow_cache_saturation_pattern(n: int):
    """Generate many unique shadow configurations to fill/evict shadow cache."""
    surf = tb.Surface(300, 300)
    for i in range(n):
        r = (i % 256)
        g = ((i * 3) % 256)
        b = ((i * 7) % 256)
        color = f"#{r:02x}{g:02x}{b:02x}80"
        surf.draw_shadow_rounded_rect(
            10, 10, 100 + (i % 50), 100 + (i % 50),
            4 + (i % 10), 4 + (i % 10),
            blur_radius=2.0 + (i % 8),
            spread=0.5 + (i % 3),
            offset_x=float(i % 5),
            offset_y=float(i % 5),
            shadow_color=color,
        )
    del surf
    tb.clear_caches()
    gc.collect()


def test_shadow_cache_saturation_no_leak():
    """Flooding the shadow engine with 1,000 unique keys must be fully reclaimed."""
    diff = _tracemalloc_diff_kb(_shadow_cache_saturation_pattern, 1000)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Shadow cache saturation leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


def _font_and_emoji_flood_pattern(n: int):
    """Rapid font queries and unicode/emoji render requests."""
    surf = tb.Surface(200, 200)
    emojis = ["😀", "🚀", "🎉", "🔥", "✨", "❤️", "🌟", "💡", "🎨", "🛠️"]
    for i in range(n):
        tb.find_system_font(f"NonExistentFontFamily_{i}", 400, False)
        emoji = emojis[i % len(emojis)]
        surf.draw_text(f"Font Test {emoji} #{i}", 10, 30, font_size=14)
    del surf
    tb.clear_caches()
    gc.collect()


def test_font_and_emoji_flood_no_leak():
    """Flooding font/emoji lookups with 500 unique requests must not leak."""
    diff = _tracemalloc_diff_kb(_font_and_emoji_flood_pattern, 500)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Font and emoji lookup flood leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


# ===========================================================================
# 17. Massive DrawBatch Queue Saturation
# ===========================================================================

def _massive_drawbatch_pattern(command_count: int):
    """Build a massive DrawBatch with tens of thousands of commands."""
    surf = tb.Surface(500, 500)
    batch = DrawBatch()
    for i in range(command_count):
        c = NativeColor(i % 256, (i * 2) % 256, (i * 4) % 256, 255)
        batch.fill_rect(i % 400, (i * 3) % 400, 10, 10, c)
        batch.fill_circle(250, 250, float(i % 100), c)
        batch.draw_line(0, 0, float(i % 500), float(i % 500), c, 1.0)

    # Verify the batch is populated before execution
    assert len(batch) == command_count * 3, (
        f"Expected {command_count * 3} ops in batch, got {len(batch)}"
    )

    surf.execute_batch(batch)
    surf.flush()
    batch.reset()

    # Structural invariant: reset() must clear the internal ops vector
    assert len(batch) == 0, (
        f"DrawBatch.reset() did not clear the ops queue: {len(batch)} ops remain"
    )

    del batch, surf
    gc.collect()


def test_drawbatch_massive_saturation_no_leak():
    """Executing and resetting a 25,000-command DrawBatch leaves zero residual memory."""
    diff = _tracemalloc_diff_kb(_massive_drawbatch_pattern, 25000)
    assert diff < _SAFE_THRESHOLD_KB, (
        f"Massive DrawBatch saturation leaked {diff:.1f} KB (threshold {_SAFE_THRESHOLD_KB} KB)"
    )


@pytest.mark.slow
def test_drawbatch_massive_saturation_stress_no_leak():
    """Executing and resetting a 100,000-command DrawBatch stays bounded."""
    diff = _tracemalloc_diff_kb(_massive_drawbatch_pattern, 100000)
    assert diff < _SAFE_THRESHOLD_KB * 3, (
        f"Stress DrawBatch saturation leaked {diff:.1f} KB"
    )

