"""
Automated headless execution tests for all tkblend example applications.
Ensures every showcase UI, canvas mode, button action, and custom widget can be
initialized and interacted with without runtime errors or exceptions.
"""

from __future__ import annotations
import os
import sys
import tkinter as tk
import pytest

# Ensure the project root and examples directory are importable
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
examples_dir = os.path.join(project_dir, "examples")
if examples_dir not in sys.path:
    sys.path.insert(0, examples_dir)

import tkblend as tb
from analytics_dashboard import AnalyticsDashboard
from canvas_studio import CanvasStudio
from custom_widget_cookbook import CustomWidgetCookbook, RadarChartWidget, SpeedometerGauge, StepProgressBar, ColorWheelPicker
from realtime_visualizer import RealtimeVisualizer
from widget_gallery import WidgetGallery
from hub import ShowcaseHub
from file_explorer import FileExplorerApp


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_analytics_dashboard_lifecycle(root):
    dash = AnalyticsDashboard(root)
    dash.pack()
    root.update_idletasks()

    # Test actions
    dash._flush_cache()
    dash._run_audit()
    dash._toggle_streaming()
    dash._toggle_streaming()
    dash._on_change_theme("light")
    dash._on_change_theme("dark")
    root.update_idletasks()
    dash.destroy()


def test_canvas_studio_lifecycle(root):
    studio = CanvasStudio(root)
    studio.pack()
    root.update_idletasks()

    modes = ["Paths & Curves", "Gradients & Extends", "Composition Modes", "Shadows & Glow", "Freehand Scratchpad"]
    for m in modes:
        studio._set_mode(m)
        root.update_idletasks()

    studio._set_comp_mode("SCREEN")
    studio._set_blur(20.0)
    studio._set_spread(5.0)
    studio._set_offset_y(8.0)
    studio._clear_scratchpad()
    studio._on_theme_changed("ocean")
    root.update_idletasks()
    studio.destroy()


def test_custom_widget_cookbook_lifecycle(root):
    cb = CustomWidgetCookbook(root)
    cb.pack()
    root.update_idletasks()

    cb._next_step()
    cb._prev_step()
    cb._randomize_radar()
    cb._on_wheel_color("#ef4444")
    cb._on_theme_changed("monokai")
    root.update_idletasks()
    cb.destroy()


def test_realtime_visualizer_lifecycle(root):
    vis = RealtimeVisualizer(root)
    vis.pack()
    root.update_idletasks()

    modes = ["Particle Swarm", "Audio Spectrum", "Harmonic Lissajous"]
    for m in modes:
        vis._set_mode(m)
        vis._render_frame()
        root.update_idletasks()

    vis._set_particle_count(100)
    vis._set_gravity(1.5)
    vis._set_trail_length(8)
    vis._set_freq_x(5.0)
    vis._set_freq_y(6.0)
    vis._on_theme_changed("sunset")
    root.update_idletasks()
    vis.destroy()


def test_widget_gallery_lifecycle(root):
    gallery = WidgetGallery(root)
    gallery.pack()
    root.update_idletasks()

    gallery._update_sample_props(16.0)
    gallery._toggle_disabled(True)
    gallery._toggle_disabled(False)
    gallery._randomize_sample()
    gallery._on_theme_changed("nord")
    root.update_idletasks()
    gallery.destroy()


def test_showcase_hub_navigation(root):
    hub = ShowcaseHub(root)
    hub.pack()
    root.update_idletasks()

    app_ids = ["dashboard", "gallery", "canvas", "visualizer", "cookbook", "ctk"]
    for aid in app_ids:
        hub._load_view(aid)
        root.update_idletasks()

    hub._on_theme_changed("emerald")
    root.update_idletasks()
    hub.destroy()


def test_file_explorer_app_lifecycle(root):
    app = FileExplorerApp(root)
    root.update_idletasks()
    app._on_theme_selected("nord")
    app.toggle_theme()
    root.update_idletasks()
    app.destroy()
