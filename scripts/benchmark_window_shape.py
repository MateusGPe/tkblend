"""
Comprehensive benchmark comparing window shape clipping performance vs unclipped containers.
Measures:
1. Micro-benchmark: apply_round_rect_shape raw latency across dimensions and radii.
2. Widget churn: Batch creation and initialization of containers with and without clip_children.
3. Dynamic resizing: High-frequency resize loop simulating window resizing / animation.
4. Profiling breakdown: X11 connection overhead vs rectangle generation vs shape masking.
"""

import time
import os
import sys
import tkinter as tk

from tkblend.utils.window_shape import (
    apply_round_rect_shape,
    clear_window_shape,
    is_window_shaping_supported,
)
try:
    from tkblend import _tkblend
except ImportError:
    _tkblend = None


def benchmark_micro_shaping(root: tk.Tk, iterations: int = 1000):
    print("=" * 70)
    print(" 1. MICRO-BENCHMARK: apply_round_rect_shape raw latency")
    print("=" * 70)

    if not is_window_shaping_supported():
        print("  [WARN] Window shaping is NOT supported on this platform/environment.")
        return

    frame = tk.Frame(root, width=400, height=300, bg="#202020")
    frame.place(x=10, y=10, width=400, height=300)
    root.update()
    wid = frame.winfo_id()

    test_cases = [
        ("Small (200x100, r=8)", 200, 100, 8.0, 8.0),
        ("Medium (400x300, r=16)", 400, 300, 16.0, 16.0),
        ("Large (800x600, r=24)", 800, 600, 24.0, 24.0),
        ("HD (1920x1080, r=32)", 1920, 1080, 32.0, 32.0),
    ]

    for name, w, h, rx, ry in test_cases:
        # Measure Python wrapper
        t0 = time.perf_counter()
        for _ in range(iterations):
            apply_round_rect_shape(frame, w, h, rx, ry)
        t_py = time.perf_counter() - t0

        # Measure direct C++ binding
        t0 = time.perf_counter()
        if _tkblend is not None and hasattr(_tkblend, "apply_round_rect_shape"):
            for _ in range(iterations):
                _tkblend.apply_round_rect_shape(wid, w, h, rx, ry)
            t_cpp = time.perf_counter() - t0
        else:
            t_cpp = t_py

        us_per_call = (t_cpp / iterations) * 1_000_000
        calls_per_sec = iterations / t_cpp

        print(f"  {name:26} : {t_cpp*1000:7.2f} ms total | {us_per_call:6.1f} µs/call | {calls_per_sec:9,.0f} calls/s")

    # Clear shape
    t0 = time.perf_counter()
    for _ in range(iterations):
        clear_window_shape(frame)
    t_clear = time.perf_counter() - t0
    print(f"  {'clear_window_shape':26} : {t_clear*1000:7.2f} ms total | {(t_clear/iterations)*1_000_000:6.1f} µs/call | {iterations/t_clear:9,.0f} calls/s")
    frame.destroy()


def benchmark_widget_churn(root: tk.Tk, count: int = 50):
    print("\n" + "=" * 70)
    print(f" 2. WIDGET CHURN BENCHMARK: Instantiating {count} Cards")
    print("=" * 70)

    # A. With shape clipping enabled
    t0 = time.perf_counter()
    frames_clipped = []
    for i in range(count):
        f = tk.Frame(root, width=250, height=120, bg="#202020")
        f.place(x=(i % 5) * 50, y=(i // 5) * 30)
        apply_round_rect_shape(f, 250, 120, 16, 16)
        frames_clipped.append(f)
    root.update()
    t_clipped = time.perf_counter() - t0

    for f in frames_clipped:
        f.destroy()
    root.update()

    # B. Without shape clipping
    t0 = time.perf_counter()
    frames_unclipped = []
    for i in range(count):
        f = tk.Frame(root, width=250, height=120, bg="#202020")
        f.place(x=(i % 5) * 50, y=(i // 5) * 30)
        frames_unclipped.append(f)
    root.update()
    t_unclipped = time.perf_counter() - t0

    for f in frames_unclipped:
        f.destroy()
    root.update()

    diff_ms = (t_clipped - t_unclipped) * 1000
    overhead_pct = ((t_clipped - t_unclipped) / t_unclipped) * 100 if t_unclipped > 0 else 0

    print(f"  Clipped   (clip_children=True)  : {t_clipped * 1000:7.2f} ms ({(t_clipped/count)*1000:.2f} ms/card)")
    print(f"  Unclipped (clip_children=False) : {t_unclipped * 1000:7.2f} ms ({(t_unclipped/count)*1000:.2f} ms/card)")
    print(f"  Overhead due to shaping         : {diff_ms:+7.2f} ms ({overhead_pct:+.1f}%)")


def benchmark_dynamic_resizing(root: tk.Tk, iterations: int = 200):
    print("\n" + "=" * 70)
    print(f" 3. DYNAMIC RESIZING / CONFIGURE BENCHMARK: {iterations} resize cycles")
    print("=" * 70)

    # Test Card resizing with clip_children=True vs clip_children=False
    card_clipped = Card(root, width=300, height=200, rx=20, ry=20, clip_children=True)
    card_clipped.place(x=20, y=20)
    _ = card_clipped.body
    root.update()

    t0 = time.perf_counter()
    for i in range(iterations):
        w = 300 + (i % 100)
        h = 200 + (i % 80)
        card_clipped.place(width=w, height=h)
        root.update()
    t_resize_clipped = time.perf_counter() - t0
    card_clipped.destroy()
    root.update()

    card_unclipped = Card(root, width=300, height=200, rx=20, ry=20, clip_children=False)
    card_unclipped.place(x=20, y=20, width=300, height=200)
    _ = card_unclipped.body
    root.update()

    t0 = time.perf_counter()
    for i in range(iterations):
        w = 300 + (i % 100)
        h = 200 + (i % 80)
        card_unclipped.place(width=w, height=h)
        root.update()
    t_resize_unclipped = time.perf_counter() - t0
    card_unclipped.destroy()
    root.update()

    fps_clipped = iterations / t_resize_clipped if t_resize_clipped > 0 else 0
    fps_unclipped = iterations / t_resize_unclipped if t_resize_unclipped > 0 else 0
    diff_ms = (t_resize_clipped - t_resize_unclipped) * 1000
    overhead_pct = ((t_resize_clipped - t_resize_unclipped) / t_resize_unclipped) * 100 if t_resize_unclipped > 0 else 0

    print(f"  Clipped   (clip_children=True)  : {t_resize_clipped * 1000:7.2f} ms | {fps_clipped:6.1f} FPS | {(t_resize_clipped/iterations)*1000:.3f} ms/frame")
    print(f"  Unclipped (clip_children=False) : {t_resize_unclipped * 1000:7.2f} ms | {fps_unclipped:6.1f} FPS | {(t_resize_unclipped/iterations)*1000:.3f} ms/frame")
    print(f"  Resize Overhead                 : {diff_ms:+7.2f} ms ({overhead_pct:+.1f}%)")


def run_all_benchmarks():
    print("Starting tkblend Window Shape Performance Benchmark...")
    print(f"Python: {sys.version.split()[0]} | Platform: {sys.platform}")
    root = tk.Tk()
    root.title("tkblend Window Shape Benchmark")
    root.geometry("600x400")
    root.withdraw()  # keep window off-screen to avoid visual disturbance

    try:
        benchmark_micro_shaping(root, iterations=1000)
        benchmark_widget_churn(root, count=60)
        benchmark_dynamic_resizing(root, iterations=250)
    finally:
        root.destroy()
    print("\n" + "=" * 70)
    print(" Benchmark completed.")
    print("=" * 70)


if __name__ == "__main__":
    run_all_benchmarks()
