"""
Benchmark script comparing granular Python-to-C++ calls vs native C++ compound and batch drawing.
"""

import time
import tkinter as tk
from tkblend.surface import Surface, LinearGradient, DrawBatch
from tkblend._tkblend import Color, EasingType, ease, spring


def benchmark_button_rendering(iterations: int = 10000):
    surface = Surface(120, 40)
    bg_col = Color(59, 130, 246, 255)
    fg_col = Color(255, 255, 255, 255)
    border_col = Color(29, 78, 216, 255)
    shadow_col = Color(0, 0, 0, 40)

    # 1. Measure Compound Primitive (Single C++ call)
    t0 = time.perf_counter()
    for _ in range(iterations):
        surface.draw_button(
            x=5, y=5, w=110, h=30, rx=8, ry=8,
            bg_color=bg_col,
            border_color=border_col,
            border_width=1.0,
            fg_color=fg_col,
            text="Button",
            font_size=13.0,
            shadow_blur=4.0,
            shadow_offset_y=2.0,
            shadow_color=shadow_col,
        )
    t_compound = time.perf_counter() - t0

    # 2. Measure Granular (Multiple Python-to-C++ calls)
    t0 = time.perf_counter()
    for _ in range(iterations):
        surface.clear("#1e1e2e")
        surface.draw_shadow(5, 7, 110, 30, 8, 8, blur_radius=4.0, shadow_color=shadow_col)
        surface.fill_rounded_rect(5, 5, 110, 30, 8, 8, bg_col)
        surface.stroke_rounded_rect(5, 5, 110, 30, 8, 8, border_col, 1.0)
        surface.draw_text("Button", 60, 24, font_size=13.0, color=fg_col, align="center")
    t_granular = time.perf_counter() - t0

    print(f"\n[Benchmark: Button Rendering ({iterations:,} frames)]")
    print(f"  Granular Multi-Call Python->C++: {t_granular * 1000:.2f} ms ({iterations / t_granular:,.0f} fps)")
    print(f"  Native Compound C++ Primitive:   {t_compound * 1000:.2f} ms ({iterations / t_compound:,.0f} fps)")
    print(f"  Speedup: {t_granular / t_compound:.2f}x faster")


def benchmark_batch_rendering(iterations: int = 5000):
    surface = Surface(300, 200)
    batch = DrawBatch()
    batch.clear(Color(30, 30, 46, 255))
    for i in range(10):
        batch.fill_rounded_rect(10 + i * 25, 20, 20, 150, 4, 4, Color(50 + i * 20, 100, 200, 255))
        batch.stroke_rounded_rect(10 + i * 25, 20, 20, 150, 4, 4, Color(255, 255, 255, 100), 1.0)

    # 1. Execute via Display List DrawBatch
    t0 = time.perf_counter()
    for _ in range(iterations):
        surface.execute_batch(batch)
    t_batch = time.perf_counter() - t0

    # 2. Execute Granular via Python loop
    t0 = time.perf_counter()
    for _ in range(iterations):
        surface.clear(Color(30, 30, 46, 255))
        for i in range(10):
            surface.fill_rounded_rect(10 + i * 25, 20, 20, 150, 4, 4, Color(50 + i * 20, 100, 200, 255))
            surface.stroke_rounded_rect(10 + i * 25, 20, 20, 150, 4, 4, Color(255, 255, 255, 100), 1.0)
    t_granular = time.perf_counter() - t0

    print(f"\n[Benchmark: 20-Op Scene Graph ({iterations:,} frames)]")
    print(f"  Granular Python Loop: {t_granular * 1000:.2f} ms ({iterations / t_granular:,.0f} fps)")
    print(f"  DrawBatch Replay:     {t_batch * 1000:.2f} ms ({iterations / t_batch:,.0f} fps)")
    print(f"  Speedup: {t_granular / t_batch:.2f}x faster")


def benchmark_color_math(iterations: int = 50000):
    c1 = Color(100, 150, 200, 255)
    c2 = Color(240, 80, 120, 255)

    t0 = time.perf_counter()
    for i in range(iterations):
        _ = c1.lerp(c2, 0.5)
        _ = c1.lighten(1.2)
        _ = c2.darken(0.8)
    t_c = time.perf_counter() - t0

    print(f"\n[Benchmark: Color Math ({iterations:,} ops)]")
    print(f"  Native C++ Color Arithmetic: {t_c * 1000:.2f} ms ({iterations * 3 / t_c:,.0f} ops/sec)")


if __name__ == "__main__":
    benchmark_button_rendering(10000)
    benchmark_batch_rendering(5000)
    benchmark_color_math(50000)
