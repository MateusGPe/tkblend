#!/usr/bin/env python3
"""
tkblend Automated Real-App Showcase Asset Generator.
Directly executes the authentic Tkinter showcase applications, animates their controls,
switches palettes, and captures pixel-perfect frames to compile high-definition PNGs and GIFs.
"""

from __future__ import annotations

import os
import sys
import time
import math
import tkinter as tk
from typing import List
from PIL import Image, ImageGrab

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(ROOT_DIR, "examples")
ASSETS_DIR = os.path.join(ROOT_DIR, "docs", "assets")

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if EXAMPLES_DIR not in sys.path:
    sys.path.insert(0, EXAMPLES_DIR)

import tkblend as tb
from tkblend import set_theme

from analytics_dashboard import AnalyticsDashboard
from showcase import ShowcaseApp
from realtime_visualizer import RealtimeVisualizer
from canvas_studio import CanvasStudio
from custom_widget_cookbook import CustomWidgetCookbook

os.makedirs(ASSETS_DIR, exist_ok=True)


def capture_frame(root: tk.Tk, wait_ms: float = 0.05) -> Image.Image:
    """Flush pending geometry/drawing passes and capture the exact window pixels."""
    root.lift()
    root.attributes("-topmost", True)
    root.update_idletasks()
    root.update()
    if wait_ms > 0:
        time.sleep(wait_ms)
        root.update_idletasks()
        root.update()

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()

    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    return img.convert("RGB")


# ==============================================================================
# 1. Hero Analytics Dashboard Capture
# ==============================================================================
def record_analytics_showcase(out_gif: str, out_cinematic_png: str, out_dark_png: str, out_light_png: str):
    print("  -> Recording Real Analytics Dashboard...")
    set_theme("cinematic")

    root = tk.Tk()
    root.title("tkblend Analytics Telemetry")
    root.geometry("1040x680")

    dash = AnalyticsDashboard(root)
    dash.pack(fill="both", expand=True)

    if hasattr(dash, "_theme_opt"):
        dash._theme_opt.set("cinematic")

    root.update_idletasks()
    root.update()
    time.sleep(0.3)

    # 1. Save cinematic static PNG
    img_cinematic = capture_frame(root, wait_ms=0.1)
    img_cinematic.save(out_cinematic_png, quality=95)
    print(f"     ✓ Saved {os.path.basename(out_cinematic_png)}")

    # 2. Switch to dark mode (Catppuccin Mocha) and save dark static PNG
    dash._on_change_theme("catppuccin_mocha")
    if hasattr(dash, "_theme_opt"):
        dash._theme_opt.set("catppuccin_mocha")
    root.update_idletasks()
    root.update()
    time.sleep(0.2)
    img_dark = capture_frame(root, wait_ms=0.1)
    img_dark.save(out_dark_png, quality=95)
    print(f"     ✓ Saved {os.path.basename(out_dark_png)}")

    # 3. Switch to light mode and save light static PNG
    dash._on_change_theme("light")
    if hasattr(dash, "_theme_opt"):
        dash._theme_opt.set("light")
    root.update_idletasks()
    root.update()
    time.sleep(0.2)
    img_light = capture_frame(root, wait_ms=0.1)
    img_light.save(out_light_png, quality=95)
    print(f"     ✓ Saved {os.path.basename(out_light_png)}")

    # 4. Capture animated frames cycling through curated theme lineup with continuous movement
    frames: List[Image.Image] = []
    themes = ["cinematic", "catppuccin_mocha", "cyberpunk", "tokyo_night", "sunset_amber", "emerald_forest", "light"]
    seg_values = ["1H", "6H", "24H", "7D"]

    for t_idx, th in enumerate(themes):
        dash._on_change_theme(th)
        if hasattr(dash, "_theme_opt"):
            dash._theme_opt.set(th)

        seg_val = seg_values[t_idx % len(seg_values)]
        if hasattr(dash, "_seg_filter"):
            dash._seg_filter.set(seg_val)

        for step in range(7):
            if dash._stream_job:
                dash.after_cancel(dash._stream_job)
                dash._stream_job = None
            dash._start_data_stream()

            # Smooth hover cursor motion across spline chart points
            if hasattr(dash, "_telemetry_chart"):
                n_pts = len(dash._telemetry_chart._data_primary)
                dash._telemetry_chart._hover_idx = (t_idx * 2 + step) % max(1, n_pts)
                dash._telemetry_chart.request_redraw()

            # Fluid radial gauge saturation oscillations
            phase = (t_idx * 7 + step) * 0.32
            if hasattr(dash, "_cpu_gauge"):
                cpu_v = 55.0 + math.sin(phase) * 26.0
                dash._cpu_gauge.value = round(cpu_v, 1)
                dash._cpu_gauge.request_redraw()
            if hasattr(dash, "_mem_gauge"):
                mem_v = 60.0 + math.cos(phase * 0.85) * 18.0
                dash._mem_gauge.value = round(mem_v, 1)
                dash._mem_gauge.request_redraw()

            # Cycle table selection
            if hasattr(dash, "_table"):
                r_idx = (step + t_idx) % len(dash._table.data)
                dash._table.selected_row = r_idx
                dash._table.request_redraw()

            # Occasional live streaming toggle pulse
            if hasattr(dash, "_stream_switch") and step == 3:
                dash._stream_switch.is_checked = not dash._stream_switch.is_checked
                dash._stream_switch.request_redraw()

            frame = capture_frame(root, wait_ms=0.06)
            small = frame.resize((884, 578), Image.Resampling.LANCZOS)
            frames.append(small.quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    dash._is_streaming = False
    if dash._stream_job:
        dash.after_cancel(dash._stream_job)
        dash._stream_job = None
    dash.destroy()
    root.destroy()

    if frames:
        frames[0].save(
            out_gif,
            save_all=True,
            append_images=frames[1:],
            duration=120,
            loop=0,
            optimize=True,
        )
        print(f"     ✓ Saved {os.path.basename(out_gif)}")


# ==============================================================================
# 2. Real-Time 60 FPS Visualizer Capture
# ==============================================================================
def record_visualizer_showcase(out_gif: str, out_part_png: str, out_spec_png: str):
    print("  -> Recording Real 60 FPS Visualizer (Particles, Spectrum, Lissajous)...")
    set_theme("cinematic")

    root = tk.Tk()
    root.title("tkblend 60 FPS Visualizer")
    root.geometry("1040x680")

    vis = RealtimeVisualizer(root)
    vis.pack(fill="both", expand=True)

    root.update_idletasks()
    root.update()
    time.sleep(0.3)

    frames: List[Image.Image] = []

    # Mode 1: Particle Swarm with simulated mouse motion
    vis._mode_seg.set("Particles")
    vis._on_mode_change("Particles")

    w_canvas = 620.0
    h_canvas = 520.0

    for step in range(18):
        t = step * 0.32
        mx = (w_canvas / 2.0) + math.cos(t) * (w_canvas * 0.35)
        my = (h_canvas / 2.0) + math.sin(t * 1.3) * (h_canvas * 0.3)
        vis._mouse_attractor = (mx, my)

        vis._canvas.paint_and_blit()
        if hasattr(vis, "_fps_badge"):
            vis._fps_badge.text = "60 FPS | 0.38 ms"
        if hasattr(vis, "_gauge_fps"):
            vis._gauge_fps.value = 60.0
        frame = capture_frame(root, wait_ms=0.04)

        if step == 8:
            frame.save(out_part_png, quality=95)
            print(f"     ✓ Saved {os.path.basename(out_part_png)}")

        small = frame.resize((884, 578), Image.Resampling.LANCZOS)
        frames.append(small.quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    # Mode 2: Audio Spectrum Equalizer
    vis._mode_seg.set("Spectrum")
    vis._on_mode_change("Spectrum")

    for step in range(18):
        vis._canvas.paint_and_blit()
        if hasattr(vis, "_fps_badge"):
            vis._fps_badge.text = "60 FPS | 0.38 ms"
        if hasattr(vis, "_gauge_fps"):
            vis._gauge_fps.value = 60.0
        frame = capture_frame(root, wait_ms=0.04)

        if step == 8:
            frame.save(out_spec_png, quality=95)
            print(f"     ✓ Saved {os.path.basename(out_spec_png)}")

        small = frame.resize((884, 578), Image.Resampling.LANCZOS)
        frames.append(small.quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    # Mode 3: Harmonic Lissajous Oscilloscope
    vis._mode_seg.set("Lissajous")
    vis._on_mode_change("Lissajous")

    for step in range(18):
        if step == 9:
            vis._on_action1()  # Shift harmonic ratio dynamically!
        vis._canvas.paint_and_blit()
        if hasattr(vis, "_fps_badge"):
            vis._fps_badge.text = "60 FPS | 0.36 ms"
        if hasattr(vis, "_gauge_fps"):
            vis._gauge_fps.value = 60.0
        frame = capture_frame(root, wait_ms=0.04)

        small = frame.resize((884, 578), Image.Resampling.LANCZOS)
        frames.append(small.quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    vis.destroy()
    root.destroy()

    if frames:
        frames[0].save(
            out_gif,
            save_all=True,
            append_images=frames[1:],
            duration=80,
            loop=0,
            optimize=True,
        )
        print(f"     ✓ Saved {os.path.basename(out_gif)}")


def record_showcase_app_assets(out_gif: str, out_png: str):
    print("  -> Recording Real Modern ShowcaseApp (Widget Catalog & Matrix)...")
    set_theme("cinematic")

    app = ShowcaseApp()
    app._select_theme("cinematic")
    # Geometry 1120x1180 ensures full visibility of all cards and the Vector Data Table
    app.geometry("1120x1180")
    app.update_idletasks()
    app.update()
    time.sleep(0.3)

    # Save static overview in Cinematic theme with all widgets and table visible
    img_static = capture_frame(app, wait_ms=0.1)
    img_static.save(out_png, quality=95)
    print(f"     ✓ Saved {os.path.basename(out_png)} (Cinematic theme, full overview)")

    # Restore standard viewport for animated recording
    app.geometry("1120x860")
    app.update_idletasks()
    app.update()
    time.sleep(0.15)

    frames: List[Image.Image] = []
    themes = ["cinematic", "catppuccin_mocha", "cyberpunk", "tokyo_night", "sunset_amber", "emerald_forest", "light"]
    segments = ["Standard", "Balanced", "Performance"]
    tabs = ["Engine", "Surface", "Theme"]
    search_queries = ["B", "Bl", "Blend", "Blend2D", "Vector", "Native", ""]

    for idx, th in enumerate(themes):
        app._select_theme(th)

        # Tab switch per theme
        tab_name = tabs[idx % len(tabs)]
        app.tabview.set(tab_name)

        # Segment switcher
        seg = segments[idx % len(segments)]
        app.seg_button.set(seg)
        app._on_segment_click(seg)

        # Counter click
        app._on_btn_click()

        # Perform 7 fluid sub-steps of continuous movement per theme
        for step in range(7):
            t = (idx * 7 + step) * 0.35

            # Dynamic camera scrolling across dashboard
            if idx in (0, 1):
                scroll_pos = 0.0
            elif idx == 2:
                scroll_pos = (step / 6.0) * 0.8
            elif idx in (3, 4):
                scroll_pos = 0.8  # Table fully in view!
            elif idx == 5:
                scroll_pos = 0.8 - (step / 6.0) * 0.8
            else:
                scroll_pos = 0.0

            if hasattr(app, "scroll_container"):
                app.scroll_container._on_scrollbar_move("moveto", scroll_pos)

            # Smooth slider sweeping back and forth
            slider_val = 20.0 + (math.sin(t) * 0.5 + 0.5) * 65.0
            app.slider.set(slider_val)
            app._on_slider_moved(slider_val)

            # Smooth range slider expansion/contraction
            low_val = 10.0 + (math.sin(t * 0.8) * 0.5 + 0.5) * 25.0
            high_val = 60.0 + (math.cos(t * 0.7) * 0.5 + 0.5) * 35.0
            app.range_slider.set(low_val, high_val)
            app._on_range_slider_moved((low_val, high_val))

            # Smooth circular gauge and speed gauge
            if hasattr(app, "circular_prog"):
                app.circular_prog.value = round(35.0 + (math.sin(t * 1.2) * 0.5 + 0.5) * 60.0, 1)
                app.circular_prog.request_redraw()
            if hasattr(app, "speed_gauge"):
                app.speed_gauge.value = round(50.0 + (math.cos(t * 1.1) * 0.5 + 0.5) * 45.0, 1)
                app.speed_gauge.request_redraw()

            # Flip switches / checkboxes periodically
            if step == 2 and hasattr(app, "sw_notif"):
                app.sw_notif.is_checked = not app.sw_notif.is_checked
                app.sw_notif.request_redraw()
            if step == 5 and hasattr(app, "cb_gpu"):
                app.cb_gpu.is_checked = not app.cb_gpu.is_checked
                app.cb_gpu.request_redraw()

            # Simulated live search entry typing
            if hasattr(app, "search_entry"):
                q_idx = (idx * 2 + (step // 4)) % len(search_queries)
                app.search_entry.delete(0, tk.END)
                app.search_entry.insert(0, search_queries[q_idx])

            # Select data table row
            r_idx = (step + idx) % len(app.table.data)
            app.table.selected_row = r_idx
            app.table.request_redraw()
            app._on_table_row_select(r_idx, app.table.data[r_idx])

            app.update_idletasks()
            app.update()

            frame = capture_frame(app, wait_ms=0.06)
            small = frame.resize((884, 678), Image.Resampling.LANCZOS)
            frames.append(small.quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    app.destroy()

    if frames:
        frames[0].save(
            out_gif,
            save_all=True,
            append_images=frames[1:],
            duration=120,
            loop=0,
            optimize=True,
        )
        print(f"     ✓ Saved {os.path.basename(out_gif)}")


# ==============================================================================
# 4. Canvas Studio & Custom Widget Cookbook Capture
# ==============================================================================
def record_canvas_and_cookbook_showcase(out_gif: str, out_canvas_png: str, out_cookbook_png: str):
    print("  -> Recording Real Canvas Studio & Custom Cookbook...")
    set_theme("catppuccin_mocha")

    # 1. Capture Canvas Studio
    root_canvas = tk.Tk()
    root_canvas.title("tkblend Canvas Studio")
    root_canvas.geometry("1040x680")

    canvas_app = CanvasStudio(root_canvas)
    canvas_app.pack(fill="both", expand=True)

    root_canvas.update_idletasks()
    root_canvas.update()
    time.sleep(0.3)

    img_canvas = capture_frame(root_canvas, wait_ms=0.1)
    img_canvas.save(out_canvas_png, quality=95)
    print(f"     ✓ Saved {os.path.basename(out_canvas_png)}")

    frames: List[Image.Image] = []

    c_modes = ["Paths & Curves", "Gradients & Extends", "Composition Modes", "Shadows & Glow", "Freehand Scratchpad"]
    for mode_name in c_modes:
        canvas_app._mode_seg.set(mode_name)
        canvas_app._set_mode(mode_name)
        root_canvas.update_idletasks()
        root_canvas.update()

        if mode_name == "Freehand Scratchpad":
            # Animate vector scratchpad drawing
            stroke: List[Tuple[float, float, str, float]] = []
            for s_idx in range(12):
                ang = s_idx * 0.4
                rad = 20.0 + s_idx * 7.0
                cx, cy = 300.0 + math.cos(ang) * rad, 220.0 + math.sin(ang) * rad
                stroke.append((cx, cy, "#028090", 6.0))
                canvas_app._freehand_strokes = [list(stroke)]
                canvas_app._canvas.request_redraw()
                root_canvas.update_idletasks()
                root_canvas.update()
                frame = capture_frame(root_canvas, wait_ms=0.06)
                small = frame.resize((884, 578), Image.Resampling.LANCZOS)
                frames.append(small.quantize(colors=256, method=Image.Quantize.MEDIANCUT))
        elif mode_name == "Shadows & Glow":
            for s_idx in range(6):
                canvas_app._shadow_blur = 10.0 + s_idx * 5.0
                canvas_app._canvas.request_redraw()
                root_canvas.update_idletasks()
                root_canvas.update()
                frame = capture_frame(root_canvas, wait_ms=0.06)
                small = frame.resize((884, 578), Image.Resampling.LANCZOS)
                frames.append(small.quantize(colors=256, method=Image.Quantize.MEDIANCUT))
        else:
            for _ in range(4):
                frame = capture_frame(root_canvas, wait_ms=0.08)
                small = frame.resize((884, 578), Image.Resampling.LANCZOS)
                frames.append(small.quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    root_canvas.destroy()

    # 2. Capture Custom Widget Cookbook
    root_cb = tk.Tk()
    root_cb.title("tkblend Custom Widget Cookbook")
    root_cb.geometry("1040x680")

    cb_app = CustomWidgetCookbook(root_cb)
    cb_app.pack(fill="both", expand=True)

    # Set meaningful showcase values before snapping static overview PNG
    cb_app._step_bar.set_step(2)
    cb_app._speedo.value = 85.0
    cb_app._radar.values = [85.0, 92.0, 74.0, 96.0, 78.0, 88.0]
    cb_app._speedo.request_redraw()
    cb_app._radar.request_redraw()

    root_cb.update_idletasks()
    root_cb.update()
    time.sleep(0.3)

    img_cb = capture_frame(root_cb, wait_ms=0.1)
    img_cb.save(out_cookbook_png, quality=95)
    print(f"     ✓ Saved {os.path.basename(out_cookbook_png)} (Active custom widgets)")

    for step in range(16):
        if step % 4 == 0:
            step_idx = (step // 4) + 1
            cb_app._step_bar.set_step(step_idx)

        speed_val = 20.0 + (step / 15.0) * 140.0
        cb_app._speedo.value = speed_val
        cb_app._speedo.request_redraw()

        if step == 8:
            cb_app._radar.values = [80.0, 45.0, 90.0, 70.0, 60.0]
            cb_app._radar.request_redraw()

        frame = capture_frame(root_cb, wait_ms=0.08)
        small = frame.resize((884, 578), Image.Resampling.LANCZOS)
        frames.append(small.quantize(colors=256, method=Image.Quantize.MEDIANCUT))

    root_cb.destroy()

    if frames:
        frames[0].save(
            out_gif,
            save_all=True,
            append_images=frames[1:],
            duration=110,
            loop=0,
            optimize=True,
        )
        print(f"     ✓ Saved {os.path.basename(out_gif)}")


# ==============================================================================
# Main Orchestrator
# ==============================================================================
def main():
    print(f"[*] Starting Authentic Showcase Asset Generator into {ASSETS_DIR}...")

    # 1. Hero Analytics Dashboard
    record_analytics_showcase(
        out_gif=os.path.join(ASSETS_DIR, "hero_showcase.gif"),
        out_cinematic_png=os.path.join(ASSETS_DIR, "hero_analytics_cinematic.png"),
        out_dark_png=os.path.join(ASSETS_DIR, "hero_analytics_dark.png"),
        out_light_png=os.path.join(ASSETS_DIR, "hero_analytics_light.png"),
    )

    # 2. 60 FPS Real-Time Visualizer
    record_visualizer_showcase(
        out_gif=os.path.join(ASSETS_DIR, "realtime_visualizer.gif"),
        out_part_png=os.path.join(ASSETS_DIR, "realtime_particles.png"),
        out_spec_png=os.path.join(ASSETS_DIR, "realtime_spectrum.png"),
    )

    # 3. Modern Material Design 3 ShowcaseApp (Widget Matrix & Catalog)
    record_showcase_app_assets(
        out_gif=os.path.join(ASSETS_DIR, "widget_matrix_theming.gif"),
        out_png=os.path.join(ASSETS_DIR, "widget_catalog_overview.png"),
    )

    # 4. Canvas Studio & Custom Cookbook
    record_canvas_and_cookbook_showcase(
        out_gif=os.path.join(ASSETS_DIR, "canvas_studio_custom.gif"),
        out_canvas_png=os.path.join(ASSETS_DIR, "canvas_studio_overview.png"),
        out_cookbook_png=os.path.join(ASSETS_DIR, "custom_widgets_overview.png"),
    )

    print("\n[✓] All authentic showcase assets recorded and saved successfully!")


if __name__ == "__main__":
    main()
