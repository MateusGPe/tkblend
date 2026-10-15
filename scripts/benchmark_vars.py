"""
Benchmark script measuring performance of variable resolution, batch compilation,
and NativeWidgetController paint paths.
"""

import time
import tkinter as tk
import tkblend as tb
from tkblend._tkblend import DrawEngine, DrawBatch, NativeWidgetController


def run_benchmark():
    print("=" * 70)
    print("TKBLEND VARIABLE RESOLUTION & COMPILATION BENCHMARK")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. DrawEngine.create_control_batch for representative controls
    # -------------------------------------------------------------
    controls = ["button", "slider", "switch", "card"]
    sample_vars = {
        "--btn-pad-x": "6.0",
        "--btn-pad-top": "3.0",
        "--btn-pad-bottom": "7.0",
        "--btn-radius": "10.0",
        "--btn-border-width": "1.5",
        "--thumb-pos": "0.65",
        "--thumb-x": "45.0",
        "--thumb-y": "15.0",
        "--active-w": "45.0",
        "--progress": "0.75",
        "--progress-w": "120.0",
        "--parent-bg": "#1e1e2e",
        "--accent": "#3b82f6",
        "--hover-t": "1.0",
        "--press-t": "0.0",
        "--focus-t": "0.5",
    }

    iterations_create = 20000
    print(f"\n[1. DrawEngine.create_control_batch ({iterations_create:,} iterations per control)]")
    for ctrl_cls in controls:
        t0 = time.perf_counter()
        for _ in range(iterations_create):
            _ = DrawEngine.create_control_batch(ctrl_cls, 0, 150.0, 36.0, sample_vars)
        elapsed = time.perf_counter() - t0
        rate = iterations_create / elapsed
        print(f"  {ctrl_cls.capitalize():<10}: {elapsed * 1000:7.2f} ms ({rate:9,.0f} ops/sec)")

    # -------------------------------------------------------------
    # 2. DrawBatch.compile with local variable lookup
    # -------------------------------------------------------------
    iterations_compile = 30000
    print(f"\n[2. DrawBatch.compile with Variable Lookup ({iterations_compile:,} iterations per control)]")
    for ctrl_cls in controls:
        batch = DrawEngine.create_control_batch(ctrl_cls, 0, 150.0, 36.0, sample_vars)
        t0 = time.perf_counter()
        for _ in range(iterations_compile):
            _ = batch.compile(sample_vars)
        elapsed = time.perf_counter() - t0
        rate = iterations_compile / elapsed
        print(f"  {ctrl_cls.capitalize():<10}: {elapsed * 1000:7.2f} ms ({rate:9,.0f} ops/sec)")

    # -------------------------------------------------------------
    # 3. NativeWidgetController: Cold paint (cache invalidated) vs Warm paint (cached batch)
    # -------------------------------------------------------------
    root = tk.Tk()
    root.withdraw()

    frame = tk.Frame(root, width=160, height=40)
    frame.pack()
    root.update_idletasks()

    ctrl = NativeWidgetController()
    attached = ctrl.attach(root.tk.interpaddr(), frame._w)
    if not attached:
        print("  Warning: could not attach NativeWidgetController to frame.")
    else:
        ctrl.widget_class = "button"
        for k, v in sample_vars.items():
            ctrl.set_var(k, v)

        # Warm-up
        ctrl.paint_and_blit()

        # Warm/Steady-state paint (fast_compiled_ready path)
        iterations_warm = 20000
        t0 = time.perf_counter()
        for _ in range(iterations_warm):
            ctrl.paint_and_blit()
        elapsed_warm = time.perf_counter() - t0
        rate_warm = iterations_warm / elapsed_warm
        print(f"\n[3. NativeWidgetController Warm Paint / Steady-State ({iterations_warm:,} calls)]")
        print(f"  Steady-state Paint: {elapsed_warm * 1000:7.2f} ms ({rate_warm:9,.0f} fps)")

        # Cold paint (force cache invalidation every frame to test vars_copy copy + compilation)
        iterations_cold = 5000
        t0 = time.perf_counter()
        for i in range(iterations_cold):
            ctrl.set_var("--hover-t", "0.5")  # invalidates cached_compiled_batch_
            ctrl.paint_and_blit()
        elapsed_cold = time.perf_counter() - t0
        rate_cold = iterations_cold / elapsed_cold
        print(f"\n[4. NativeWidgetController Cold Paint / Cache Invalidation ({iterations_cold:,} calls)]")
        print(f"  Cold Recompile Paint: {elapsed_cold * 1000:7.2f} ms ({rate_cold:9,.0f} fps)")

    try:
        root.destroy()
    except Exception:
        pass

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_benchmark()
