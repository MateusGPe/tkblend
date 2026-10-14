"""
Thread-safety stress tests for the native tkblend layer.

Scope: Tk/UI calls stay on the main thread; worker threads may drive Surfaces,
SurfaceHandles and the StyleEngine/font caches concurrently. These tests hammer
those paths from many OS threads and assert:

* no crash / use-after-free (the process survives),
* no deadlock (every worker joins within a timeout),
* only *expected* Python exceptions (closed/invalid surface) are raised.

Lock hierarchy under test (outermost first):  GIL  ->  controller mutex_  ->
Surface mutex_ / engine mutexes  ->  SurfaceRegistry mutex_ (leaf).
"""

import gc
import threading
import time

import pytest

import tkblend as tb
from tkblend._tkblend import (
    Color,
    DrawBatch,
    DrawEngine,
    NativeWidgetController,
    StyleEngine,
    Surface,
    SurfaceHandle,
    SurfaceRegistry,
    clear_shadow_cache,
    set_shadow_cache_limits,
)

BG = Color(24, 24, 37, 255)
BLUE = Color(137, 180, 250, 255)
WHITE = Color(255, 255, 255, 255)
BLACK = Color(0, 0, 0, 255)
RED = Color(255, 0, 0, 255)

JOIN_TIMEOUT = 60.0
EXPECTED = (RuntimeError, ValueError)


def _run_threads(targets, timeout=JOIN_TIMEOUT):
    """Start all targets simultaneously, assert none deadlocked."""
    barrier = threading.Barrier(len(targets))
    errors = []

    def wrap(fn):
        def run():
            barrier.wait()
            try:
                fn()
            except EXPECTED:
                pass
            except BaseException as exc:  # noqa: BLE001 - surfaced to the test
                errors.append(exc)
        return run

    threads = [threading.Thread(target=wrap(t), daemon=True) for t in targets]
    for t in threads:
        t.start()
    deadline = time.monotonic() + timeout
    for t in threads:
        t.join(max(0.0, deadline - time.monotonic()))
    stuck = [t for t in threads if t.is_alive()]
    assert not stuck, f"{len(stuck)} worker thread(s) deadlocked"
    assert not errors, f"unexpected errors: {errors[:3]!r}"


@pytest.fixture
def clean_gc():
    gc.collect()
    yield
    gc.collect()


class TestSurfaceHandleLifetimeRaces:
    def test_draw_while_handle_destroyed(self, clean_gc):
        """Drawing on a handle another thread closes must never use freed memory."""
        for _ in range(25):
            handle = SurfaceHandle(160, 60)

            def drawer():
                for i in range(200):
                    handle.clear(BG)
                    handle.fill_rounded_rect(4, 4, 150, 50, 8, 8, BLUE)
                    handle.draw_text("race", 10, 30, 12, "default", WHITE)
                    handle.flush()

            def closer():
                time.sleep(0.001)
                handle.close()

            _run_threads([drawer, drawer, drawer, closer])

    def test_registry_create_destroy_storm(self, clean_gc):
        baseline = SurfaceRegistry.instance().active_surface_count()

        def churn():
            for _ in range(100):
                h = SurfaceHandle(32, 32)
                h.clear(BLACK)
                h.close()

        _run_threads([churn] * 8)
        assert SurfaceRegistry.instance().active_surface_count() == baseline

    def test_buffer_view_outlives_handle_close(self, clean_gc):
        """A live memoryview pins the surface; closing the handle must not free pixels."""
        handle = SurfaceHandle(64, 64)
        handle.clear(RED)
        mv = memoryview(handle.get_buffer())
        try:
            handle.close()  # refuses to close surface while view is active
        except EXPECTED:
            pass
        # Pixels must remain readable (no use-after-free).
        assert len(mv) >= 64 * 64 * 4
        _ = mv[0], mv[len(mv) - 1]
        del mv
        gc.collect()


class TestSharedSurfaceRaces:
    def test_resize_draw_flush_interleave(self, clean_gc):
        surf = tb.Surface(100, 100)

        def drawer():
            for i in range(300):
                surf.clear("#101010")
                surf.fill_rect(0, 0, 50, 50, "#ffffff")
                surf.flush()

        def resizer():
            for i in range(150):
                surf.resize(100 + (i % 7) * 10, 100 + (i % 5) * 10)

        _run_threads([drawer, drawer, resizer, resizer])
        surf.close()

    def test_measure_text_font_cache(self, clean_gc):
        surf = tb.Surface(10, 10)

        def measure():
            for i in range(300):
                surf.measure_text(f"Hello {i}", 10 + (i % 6), "default")

        _run_threads([measure] * 8)
        surf.close()


class TestStyleEngineRaces:
    def test_theme_switch_and_resolve(self, clean_gc):
        themes = list(StyleEngine.get_available_themes()) or [StyleEngine.get_theme()]
        original = StyleEngine.get_theme()

        def switcher():
            for i in range(200):
                StyleEngine.set_theme(themes[i % len(themes)])

        def resolver():
            for i in range(400):
                StyleEngine.resolve("button", "", i % 8)
                StyleEngine.resolve_color("var(--primary)", "")

        def variables():
            for i in range(200):
                StyleEngine.set_variable(f"--t{i % 5}", "#112233", "")
                StyleEngine.get_variable(f"--t{i % 5}", "")

        try:
            _run_threads([switcher, resolver, resolver, variables])
        finally:
            StyleEngine.set_theme(original)

    def test_stylesheet_reload_vs_resolve(self, clean_gc):
        css = ".tsafe { background: #123456; color: #ffffff; }"

        def loader():
            for _ in range(100):
                StyleEngine.load_stylesheet(css)
                StyleEngine.clear_cache()

        def resolver():
            for _ in range(300):
                StyleEngine.resolve("button", "tsafe", 0)

        _run_threads([loader, resolver, resolver])


class TestExternalSurfaceOwnership:
    def test_bind_surface_keeps_surface_alive_then_releases(self, clean_gc):
        import sys
        from tkblend._tkblend import NativeWidgetController, Surface

        ctrl = NativeWidgetController()
        surf = Surface(40, 40)
        before = sys.getrefcount(surf)
        ctrl.bind_surface(surf)
        # The controller now holds its own strong reference to the Surface.
        assert sys.getrefcount(surf) == before + 1

        ctrl.unbind_surface()
        assert sys.getrefcount(surf) == before

        ctrl.bind_surface(surf)
        ctrl.detach()  # detach must drop the reference too
        assert sys.getrefcount(surf) == before

    def test_state_callback_flag_tracks_set_and_clear(self, clean_gc):
        from tkblend._tkblend import NativeWidgetController

        ctrl = NativeWidgetController()
        seen = []
        ctrl.set_on_state_changed(lambda new, old: seen.append((new, old)))
        ctrl.is_hovered = True
        ctrl.clear_on_state_changed()
        ctrl.is_hovered = False  # no callback: must not fire or crash
        assert len(seen) == 1
        ctrl.detach()


class TestControllerGILAndCallbackHarness:
    """Harness tests verifying GIL and NativeWidgetController recursive_mutex interactions."""

    def test_state_callback_concurrent_invocation_and_replacement(self, clean_gc):
        """Worker threads churn state changes while callbacks are dynamically swapped/cleared."""
        ctrl = NativeWidgetController()
        seen = []

        def worker_state(tid):
            for i in range(120):
                ctrl.state = (i + tid) & 0x1F
                ctrl.is_hovered = bool(i & 1)
                ctrl.is_pressed = bool(i & 2)

        def worker_cb_churn():
            for _ in range(80):
                ctrl.set_on_state_changed(lambda new_s, old_s: seen.append((new_s, old_s)))
                time.sleep(0.0005)
                ctrl.clear_on_state_changed()

        def worker_reader():
            for _ in range(150):
                _ = ctrl.state, ctrl.is_hovered, ctrl.is_pressed

        _run_threads([lambda: worker_state(1), lambda: worker_state(2), worker_cb_churn, worker_reader])
        ctrl.clear_on_state_changed()
        ctrl.detach()

    def test_reentrant_state_callback_under_contention(self, clean_gc):
        """State callback re-enters the controller while holding the GIL."""
        ctrl = NativeWidgetController()
        reentrant_calls = []

        def on_state(new_s, old_s):
            # Re-entrant calls into ctrl while holding the GIL:
            ctrl.set_var("last_state", str(new_s))
            val = ctrl.get_var("last_state")
            ctrl.add_class(f"s-{new_s % 4}")
            ctrl.request_redraw()
            reentrant_calls.append((new_s, val))

        ctrl.set_on_state_changed(on_state)

        def worker_driver(offset):
            for i in range(120):
                ctrl.state = (i + offset) & 0x1F

        def worker_var_mutator():
            for i in range(120):
                ctrl.set_var("worker_key", f"val_{i}")
                _ = ctrl.get_var("worker_key")

        _run_threads([lambda: worker_driver(0), lambda: worker_driver(10), worker_var_mutator])
        ctrl.clear_on_state_changed()
        ctrl.detach()
        assert len(reentrant_calls) > 0

    def test_on_paint_vs_state_callback_interleave(self, clean_gc):
        """Paint callback (GIL -> mutex_) interleaves with set_state (mutex_ -> GIL)."""
        ctrl = NativeWidgetController()
        paint_counts = [0]
        state_counts = [0]

        def paint_cb(surf):
            paint_counts[0] += 1
            surf.fill_rect(0, 0, 10, 10, RED)
            surf.flush()

        def state_cb(new_s, old_s):
            state_counts[0] += 1

        ctrl.set_on_paint(paint_cb)
        ctrl.set_on_state_changed(state_cb)

        def painter():
            for _ in range(80):
                ctrl.paint_and_blit()

        def stater():
            for i in range(80):
                ctrl.state = i % 16

        _run_threads([painter, painter, stater, stater])
        ctrl.clear_on_paint()
        ctrl.clear_on_state_changed()
        ctrl.detach()
        assert paint_counts[0] > 0
        assert state_counts[0] > 0

    def test_all_callbacks_concurrent_lifecycle_storm(self, clean_gc):
        """Concurrently sets, replaces, and clears all callback slots while state updates."""
        ctrl = NativeWidgetController()

        def cber_paint():
            for i in range(80):
                ctrl.set_on_paint(lambda s: None)
                if i % 3 == 0:
                    ctrl.clear_on_paint()

        def cber_click():
            for i in range(80):
                ctrl.set_on_click(lambda x, y, b: None)
                if i % 3 == 0:
                    ctrl.clear_on_click()

        def cber_resize():
            for i in range(80):
                ctrl.set_on_resize(lambda w, h: None)
                if i % 3 == 0:
                    ctrl.clear_on_resize()

        def cber_change():
            for i in range(80):
                ctrl.set_on_change(lambda val: None)
                if i % 3 == 0:
                    ctrl.clear_on_change()

        def cber_state():
            for i in range(80):
                ctrl.set_on_state_changed(lambda n, o: None)
                if i % 3 == 0:
                    ctrl.clear_on_state_changed()

        def worker():
            for i in range(80):
                ctrl.state = i % 8
                ctrl.paint_and_blit()

        _run_threads([cber_paint, cber_click, cber_resize, cber_change, cber_state, worker])
        ctrl.detach()


class TestControllerSurfaceBindingAndDeferredPy:
    """Verifies DeferredPy correctly releases Python Surface references outside controller mutex."""

    def test_surface_binding_churn_while_drawing_and_collecting(self, clean_gc):
        ctrl = NativeWidgetController()
        surfs = [Surface(32, 32) for _ in range(4)]
        handles = [SurfaceHandle(32, 32) for _ in range(4)]

        def binder_surfs():
            for i in range(80):
                ctrl.bind_surface(surfs[i % len(surfs)])
                if i % 3 == 0:
                    ctrl.unbind_surface()

        def binder_handles():
            for i in range(80):
                ctrl.bind_surface_handle(handles[i % len(handles)])
                if i % 3 == 0:
                    ctrl.unbind_surface()

        def drawer():
            for i in range(80):
                s = surfs[i % len(surfs)]
                s.clear(BLACK)
                s.fill_rect(0, 0, 10, 10, WHITE)
                s.flush()

        def gc_runner():
            for _ in range(15):
                gc.collect()
                time.sleep(0.001)

        _run_threads([binder_surfs, binder_handles, drawer, gc_runner])
        ctrl.detach()
        for h in handles:
            h.close()
        for s in surfs:
            s.close()

    def test_controller_blit_surface_concurrency(self, clean_gc):
        ctrl = NativeWidgetController()
        surf = Surface(40, 40)
        handle = SurfaceHandle(40, 40)

        def blit_worker():
            for _ in range(80):
                ctrl.blit_surface(surf)
                ctrl.blit_handle(handle)

        def drawer():
            for i in range(80):
                surf.clear(RED)
                handle.clear(BLUE)

        _run_threads([blit_worker, blit_worker, drawer, drawer])
        ctrl.detach()
        handle.close()
        surf.close()


class TestControllerClassesAndVariablesStorm:
    """Heavy multi-threaded mutation of CSS classes and local variables on NativeWidgetController."""

    def test_concurrent_classes_and_vars_heavy_mutation(self, clean_gc):
        ctrl = NativeWidgetController()

        def class_mutator():
            for i in range(120):
                name = f"theme-{i % 6}"
                ctrl.add_class(name)
                ctrl.toggle_class(f"flag-{i % 3}")
                _ = ctrl.has_class(name)
                _ = ctrl.classes
                _ = ctrl.class_name
                if i % 4 == 0:
                    ctrl.remove_class(name)

        def var_mutator():
            for i in range(120):
                k = f"--var-{i % 8}"
                v = f"#{i:06x}"
                ctrl.set_var(k, v)
                _ = ctrl.get_var(k)
                _ = ctrl.get_vars()
                if i % 5 == 0:
                    ctrl.remove_var(k)

        _run_threads([class_mutator, class_mutator, var_mutator, var_mutator])
        ctrl.detach()


class TestBufferProtocolGILAndMutexSafety:
    """Buffer protocol memoryviews vs Surface resize, close, and concurrent drawing."""

    def test_concurrent_buffer_views_block_resize_and_close(self, clean_gc):
        surf = Surface(40, 40)
        views_active = threading.Event()
        stop_event = threading.Event()
        resize_blocked = []

        def buffer_holder():
            mv = memoryview(surf.get_buffer())
            assert len(mv) == 40 * 40 * 4
            views_active.set()
            while not stop_event.is_set():
                mv[0] = 128
                _ = mv[len(mv) - 1]
                time.sleep(0.001)
            del mv

        def resizer():
            views_active.wait()
            for i in range(50):
                try:
                    surf.resize(40 + (i % 5) * 4, 40 + (i % 5) * 4)
                except RuntimeError as e:
                    resize_blocked.append(str(e))
                time.sleep(0.001)

        t_holder = threading.Thread(target=buffer_holder)
        t_resizer = threading.Thread(target=resizer)
        t_holder.start()
        t_resizer.start()

        t_resizer.join(timeout=JOIN_TIMEOUT)
        stop_event.set()
        t_holder.join(timeout=JOIN_TIMEOUT)
        gc.collect()

        assert len(resize_blocked) > 0
        assert all("active buffer views" in msg for msg in resize_blocked)

        # After views released, resize must succeed
        surf.resize(60, 60)
        assert surf.width == 60
        assert surf.height == 60
        surf.close()

    def test_multiple_concurrent_buffer_views_and_drawing(self, clean_gc):
        surf = Surface(50, 50)

        def view_worker(tid):
            for _ in range(40):
                mv = memoryview(surf.get_buffer())
                assert len(mv) == 50 * 50 * 4
                mv[tid * 10] = tid
                del mv

        def draw_worker():
            for i in range(40):
                surf.clear(BG)
                surf.fill_rect(0, 0, 20, 20, BLUE)
                surf.flush()

        _run_threads([lambda: view_worker(0), lambda: view_worker(1), draw_worker, draw_worker])
        gc.collect()
        surf.close()


class TestShadowEngineLRUStress:
    """Stress tests ShadowEngine LRU cache and multi-threaded 3-pass box blur."""

    def test_concurrent_shadow_rendering_and_cache_clearing(self, clean_gc):
        surf = Surface(80, 80)
        clear_shadow_cache()

        def drawer():
            for i in range(60):
                blur = 2.0 + (i % 7) * 1.5
                spread = (i % 3) * 1.0
                surf.draw_shadow_rounded_rect(
                    5, 5, 50, 40, 6, 6,
                    blur, spread, 0.0, 2.0,
                    Color(0, 0, 0, 100),
                )
                surf.flush()

        def cache_churner():
            for i in range(40):
                if i % 2 == 0:
                    clear_shadow_cache()
                else:
                    set_shadow_cache_limits(10 + (i % 20), 512 * 1024)
                time.sleep(0.001)

        _run_threads([drawer, drawer, drawer, cache_churner])
        surf.close()
        clear_shadow_cache()


class TestDrawEngineBatchRegistryConcurrency:
    """Stress tests DrawEngine recursive mutex during concurrent registration, lookup, and reset."""

    def test_concurrent_batch_registration_and_lookup(self, clean_gc):
        def registrar(prefix):
            for i in range(80):
                b = DrawBatch()
                b.fill_rect(0, 0, 20, 20, RED)
                cls_name = f"btn_{prefix}_{i % 5}"
                DrawEngine.register_batch(cls_name, i % 4, b)
                if i % 3 == 0:
                    DrawEngine.unregister_batch(cls_name, i % 4)

        def reader():
            for i in range(120):
                cls_name = f"btn_A_{i % 5}"
                _ = DrawEngine.get_batch(cls_name, i % 4)
                _ = DrawEngine.has_batch(cls_name, i % 4)

        def resetter():
            for _ in range(8):
                time.sleep(0.002)
                DrawEngine.reset_defaults()

        _run_threads([lambda: registrar("A"), lambda: registrar("B"), reader, resetter])
        DrawEngine.reset_defaults()


class TestFloodAndLoadHarness:
    """High-concurrency flood tests hammering surfaces, controllers, and registries."""

    def test_high_concurrency_surface_flood_16_threads(self, clean_gc):
        """16 worker threads concurrently rendering to private surfaces and a shared surface."""
        shared_surf = Surface(120, 120)

        def worker(tid):
            local_surf = Surface(32, 32)
            for i in range(70):
                local_surf.clear(Color(tid * 10, i % 256, 100, 255))
                local_surf.fill_rect(0, 0, 15, 15, WHITE)
                local_surf.flush()
                if i % 4 == 0:
                    shared_surf.fill_rect(tid * 6, (i % 20) * 5, 10, 10, BLUE)
                    shared_surf.flush()
            local_surf.close()

        _run_threads([lambda tid=t: worker(tid) for t in range(16)])
        shared_surf.close()

    def test_controller_event_and_state_flood_16_threads(self, clean_gc):
        """16 threads flood state transitions on a single NativeWidgetController."""
        ctrl = NativeWidgetController()
        seen = []
        ctrl.set_on_state_changed(lambda n, o: seen.append((n, o)))

        def flipper(tid):
            for i in range(80):
                ctrl.state = (i + tid) & 0x1F
                ctrl.is_hovered = bool(i & 1)
                ctrl.is_pressed = bool(i & 2)
                ctrl.is_focused = bool(i & 4)
                ctrl.is_checked = bool(i & 8)

        _run_threads([lambda tid=t: flipper(tid) for t in range(16)])
        ctrl.clear_on_state_changed()
        ctrl.detach()
        assert len(seen) > 0

    def test_surface_registry_burst_storm_16_threads(self, clean_gc):
        """16 threads creating, pinning, drawing, and closing SurfaceHandles simultaneously."""
        def handle_worker(tid):
            for _ in range(40):
                h = SurfaceHandle(24, 24)
                h.clear(BLACK)
                h.fill_rect(0, 0, 10, 10, RED)
                h.flush()
                _ = h.width, h.height, h.surface_id
                h.close()

        _run_threads([lambda tid=t: handle_worker(tid) for t in range(16)])


class TestFuzzAndBoundaryInputs:
    """Fuzz testing with non-finite coordinates, boundary values, malformed inputs, and unicode."""

    def test_geometry_coordinate_fuzzing(self, clean_gc):
        """Fuzzing draw calls with NaN, +/-Inf, sub-pixel, huge, and negative coordinates."""
        surf = Surface(100, 100)
        fuzz_values = [
            0.0, -0.0, 1.0, -1.0, 1e-6, -1e-6, 1e6, -1e6,
            float("inf"), float("-inf"), float("nan"),
        ]

        for x in fuzz_values:
            for y in [0.0, -10.0, float("nan")]:
                try:
                    surf.fill_rect(x, y, 50, 50, RED)
                except Exception:
                    pass
                try:
                    surf.fill_rounded_rect(x, y, 50, 50, 5, 5, BLUE)
                except Exception:
                    pass
                try:
                    surf.clear_rect(x, y, 20, 20)
                except Exception:
                    pass
                try:
                    surf.draw_shadow_rounded_rect(x, y, 50, 50, 5, 5, 2.0, 0.0, 0.0, 0.0, BLACK)
                except Exception:
                    pass

        surf.flush()
        surf.close()

    def test_surface_resize_boundary_fuzzing(self, clean_gc):
        """Resizing surfaces with boundary, zero, and negative dimensions."""
        surf = Surface(50, 50)
        boundary_sizes = [
            (0, 0), (-10, -20), (1, 1), (0, 50), (50, 0),
            (300, 300), (1, 800), (800, 1),
        ]
        for w, h in boundary_sizes:
            surf.resize(w, h)
            assert surf.width >= 1
            assert surf.height >= 1
            surf.clear(RED)
            surf.flush()
        surf.close()

    def test_text_rendering_unicode_and_length_fuzzing(self, clean_gc):
        """Fuzzing text measurement and drawing with huge strings, unicode, and extreme sizes."""
        surf = Surface(100, 100)
        fuzz_strings = [
            "",
            "x" * 15000,
            "Hello \U0001F600 \U0001F680 \U0001F4BB",
            "\u200b\u200c\u200d\ufeff",  # zero-width chars
            "Arabic: \u0627\u0644\u0639\u0631\u0628\u064a\u0629 Hebrew: \u05e2\u05d1\u05e8\u05d9\u05ea",
            "Line1\nLine2\r\nLine3\tTabbed",
            "\x00\x01\x02\x03",
        ]
        font_sizes = [0.0, -1.0, 0.001, 12.0, 500.0, float("nan"), float("inf")]
        families = ["", "default", "sans-serif", "nonexistent_font_xyz", "Symbols \u2665"]

        for st in fuzz_strings:
            for sz in font_sizes:
                for fam in families:
                    try:
                        surf.measure_text(st, sz, fam)
                    except Exception:
                        pass
                    try:
                        surf.draw_text(st, 10, 10, sz, fam, WHITE)
                    except Exception:
                        pass

        surf.flush()
        surf.close()

    def test_css_stylesheet_parser_fuzzing(self, clean_gc):
        """Fuzzing StyleEngine stylesheet parser with malformed and adversarial payloads."""
        malformed_payloads = [
            "",
            " { { { } } } ",
            ".btn { background: ; color: #; }",
            ".bad { :::: ;;;; }",
            "/* unclosed comment .foo { color: red; }",
            ".large { " + ("margin: 1px; " * 800) + "}",
            "::::invalid-selector:::: { border: 1px solid green; }",
            "@keyframes invalid { from { } to { } }",
        ]
        for css in malformed_payloads:
            try:
                StyleEngine.load_stylesheet(css)
                StyleEngine.clear_cache()
                _ = StyleEngine.resolve("button", "btn", 0)
            except Exception:
                pass

    def test_color_hex_fuzzing(self, clean_gc):
        """Fuzzing Color.from_hex with malformed, empty, and out-of-range strings."""
        bad_hex_inputs = [
            "", "#", "#1", "#12", "#12345", "#xyz", "#123456789",
            "invalid_color", "rgb(nan, inf)", "   #fff   ", "#ff\x00ff",
        ]
        for bad in bad_hex_inputs:
            c = Color.from_hex(bad)
            assert isinstance(c.r, int)
            assert isinstance(c.g, int)
            assert isinstance(c.b, int)
            assert isinstance(c.a, int)


class TestLockInversionAndContention:
    """Stress tests verifying absence of ABBA deadlocks across multiple controllers and callbacks."""

    def test_dual_controller_cross_callback_no_deadlock(self, clean_gc):
        """Two controllers whose callbacks cross-reference each other under concurrent worker threads."""
        ctrl_a = NativeWidgetController()
        ctrl_b = NativeWidgetController()
        calls_a = []
        calls_b = []

        def on_a(new_s, old_s):
            calls_a.append(new_s)
            ctrl_b.set_var("from_a", str(new_s))
            _ = ctrl_b.get_var("from_a")

        def on_b(new_s, old_s):
            calls_b.append(new_s)
            ctrl_a.set_var("from_b", str(new_s))
            _ = ctrl_a.get_var("from_b")

        ctrl_a.set_on_state_changed(on_a)
        ctrl_b.set_on_state_changed(on_b)

        def driver_a():
            for i in range(80):
                ctrl_a.state = i % 8

        def driver_b():
            for i in range(80):
                ctrl_b.state = i % 8

        _run_threads([driver_a, driver_a, driver_b, driver_b])
        ctrl_a.clear_on_state_changed()
        ctrl_b.clear_on_state_changed()
        ctrl_a.detach()
        ctrl_b.detach()
        assert len(calls_a) > 0
        assert len(calls_b) > 0

    def test_callback_raising_python_exceptions(self, clean_gc):
        """Callbacks raising unhandled Python exceptions do not corrupt mutexes or crash the engine."""
        ctrl = NativeWidgetController()

        def throwing_callback(new_s, old_s):
            if new_s % 2 == 0:
                raise ValueError("Test error from callback")
            if new_s % 3 == 0:
                raise RuntimeError("Runtime error from callback")
            raise ZeroDivisionError("Math error from callback")

        ctrl.set_on_state_changed(throwing_callback)

        def driver(tid):
            for i in range(70):
                ctrl.state = (i + tid) & 0xF

        _run_threads([lambda: driver(1), lambda: driver(2), lambda: driver(3)])
        ctrl.clear_on_state_changed()
        ctrl.detach()


class TestBufferProtocolEdgeCases:
    """Edge cases for zero-copy buffer protocol views, minimal sizes, and cyclic GC."""

    def test_buffer_view_minimal_1x1(self, clean_gc):
        """1x1 surface buffer view byte manipulation, stride verification, length checking."""
        surf = Surface(1, 1)
        surf.clear(RED)
        surf.flush()

        mv = memoryview(surf.get_buffer())
        assert len(mv) == 4  # 1 * 1 * 4 bytes for PRGB32
        assert mv.readonly is False
        # Read and modify pixel values
        mv[0] = 42
        assert mv[0] == 42
        del mv
        gc.collect()

        surf.resize(2, 2)
        assert surf.width == 2
        assert surf.height == 2
        surf.close()

    def test_buffer_view_cyclic_gc_recovery(self, clean_gc):
        """Circular references involving memoryview and Surface are recovered by cyclic GC."""
        surf = Surface(20, 20)
        mv = memoryview(surf.get_buffer())

        class Holder:
            pass

        h1 = Holder()
        h2 = Holder()
        h1.mv = mv
        h1.surf = surf
        h1.other = h2
        h2.other = h1

        del h1, h2, mv
        gc.collect()

        # The cyclic reference must be broken and buffer view released, allowing close
        surf.close()

    def test_closed_surface_handle_all_methods_throw(self, clean_gc):
        """Closed SurfaceHandle predictably raises RuntimeError on all operations."""
        h = SurfaceHandle(30, 30)
        h.close()

        operations = [
            lambda: h.clear(BLACK),
            lambda: h.clear_rect(0, 0, 10, 10),
            lambda: h.fill_rect(0, 0, 10, 10, RED),
            lambda: h.resize(40, 40),
            lambda: h.flush(),
            lambda: h.get_buffer(),
        ]
        for op in operations:
            try:
                op()
                assert False, "Expected RuntimeError on closed SurfaceHandle"
            except RuntimeError as e:
                assert any(k in str(e).lower() for k in ("invalid", "destroyed", "closed"))