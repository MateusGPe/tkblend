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
from tkblend._tkblend import Color, StyleEngine, SurfaceHandle, SurfaceRegistry

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
