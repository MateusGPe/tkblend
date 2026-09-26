"""
tkblend Performance and Framerate Benchmark.
Measures vector rendering throughput, shadow generation, and Tk_PhotoPutBlock blit framerates.
"""

import time
import math
import random
import tkinter as tk
from tkblend import Surface, Color, LinearGradient, RadialGradient, Path


def run_headless_benchmark():
    print("=" * 60)
    print(" tkblend Headless Rendering Benchmark")
    print("=" * 60)

    # 1. 1080p Frame Render & Draw Primitives
    w, h = 1920, 1080
    surf = Surface(w, h)

    iterations = 200
    start_t = time.perf_counter()
    for i in range(iterations):
        surf.clear("#11111b")

        # Background gradient
        grad = LinearGradient(0, 0, w, h)
        grad.add_stop(0.0, "#1e1e2e")
        grad.add_stop(1.0, "#181825")
        surf.fill_rect(0, 0, w, h, grad)

        # Draw 100 complex shapes per frame
        for j in range(100):
            x = (j * 37) % (w - 200)
            y = (j * 23) % (h - 200)
            rx = (j % 16) + 4
            surf.draw_card(
                x, y, 180, 120, rx, rx,
                bg_color="#313244",
                border_color="#89b4fa",
                border_width=1.5,
                shadow_blur=12.0,
                shadow_color="#00000044"
            )

        surf.flush()

    elapsed = time.perf_counter() - start_t
    fps = iterations / elapsed
    print(f"[1080p Complex Scene] {iterations} frames in {elapsed:.3f}s -> {fps:.1f} FPS ({elapsed/iterations*1000:.2f} ms/frame)")

    # 2. Path & Curve Drawing Throughput
    iterations = 500
    p = Path()
    for i in range(100):
        t = i * 0.1
        cx = 960 + 400 * math.cos(t)
        cy = 540 + 300 * math.sin(t * 1.5)
        if i == 0:
            p.move_to(cx, cy)
        else:
            p.cubic_to(cx - 20, cy - 20, cx + 20, cy + 20, cx, cy)

    start_t = time.perf_counter()
    for _ in range(iterations):
        surf.stroke_path(p, "#f38ba8", stroke_width=3.0)
        surf.flush()
    elapsed = time.perf_counter() - start_t
    print(f"[Cubic Bezier Paths]  {iterations} complex strokes in {elapsed:.3f}s -> {iterations/elapsed:.1f} strokes/s")

    # 3. Soft Drop Shadow Generation & Cache Performance
    iterations = 1000
    start_t = time.perf_counter()
    for i in range(iterations):
        surf.draw_shadow(100, 100, 400, 250, 20, 20, blur_radius=24.0, shadow_color="#00000088")
        surf.flush()
    elapsed = time.perf_counter() - start_t
    print(f"[Cached 24px Blur Shadows] {iterations} renders in {elapsed:.3f}s -> {iterations/elapsed:.1f} ops/s ({elapsed/iterations*1000:.3f} ms/op)")


def run_tkinter_blit_benchmark():
    print("\n" + "=" * 60)
    print(" tkblend Tk_PhotoPutBlock Direct Blit Benchmark")
    print("=" * 60)

    root = tk.Tk()
    root.title("tkblend Blit Benchmark")
    root.geometry("1280x720")

    w, h = 1280, 720
    photo = tk.PhotoImage(master=root, width=w, height=h)
    label = tk.Label(root, image=photo, borderwidth=0)
    label.pack(fill="both", expand=True)

    surf = Surface(w, h)

    frames = 0
    start_t = time.perf_counter()
    duration = 3.0  # run for 3 seconds

    def update_frame():
        nonlocal frames, start_t
        t = time.perf_counter() - start_t
        if t >= duration:
            fps = frames / t
            print(f"[1280x720 Direct Tkinter Blit] {frames} frames in {t:.3f}s -> {fps:.1f} FPS ({t/frames*1000:.2f} ms/frame)")
            root.destroy()
            return

        # Render dynamic scene
        surf.clear("#11111b")

        # Rotating gradient
        cx, cy = w / 2, h / 2
        rad_grad = RadialGradient(cx + 100 * math.cos(t * 2), cy + 100 * math.sin(t * 2), 10, cx, cy, 500)
        rad_grad.add_stop(0.0, "#89b4fa")
        rad_grad.add_stop(0.5, "#cba6f7")
        rad_grad.add_stop(1.0, "#11111b")
        surf.fill_rect(0, 0, w, h, rad_grad)

        # Dynamic floating cards
        for k in range(12):
            angle = t * 1.5 + k * (2 * math.pi / 12)
            card_x = cx + math.cos(angle) * 350 - 60
            card_y = cy + math.sin(angle) * 200 - 40
            surf.draw_card(
                card_x, card_y, 120, 80, 14, 14,
                bg_color="#181825ee",
                border_color="#ffffff44",
                border_width=1.5,
                shadow_blur=16.0,
                shadow_color="#00000066"
            )

        surf.draw_text(f"Real-Time Tkinter Blit: {frames / max(0.001, t):.1f} FPS", 40, 60, font_size=24, color="#ffffff")
        
        # Direct blit to PhotoImage
        surf.blit(photo)
        frames += 1

        root.after(1, update_frame)

    root.after(10, update_frame)
    root.mainloop()


if __name__ == "__main__":
    run_headless_benchmark()
    try:
        run_tkinter_blit_benchmark()
    except Exception as e:
        print(f"Interactive benchmark skipped (display unavailable or error: {e})")
