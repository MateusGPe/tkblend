"""
Automated headless execution tests for surviving tkblend example applications.
Ensures Canvas Studio, Decorator Showcase, and CTK Showcase can be initialized
and interacted with without runtime errors.
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
from canvas_studio import CanvasStudio
from decorator_showcase import DecoratorShowcase
from ctk_showcase import CTKBridgeInfoFrame, _HAS_CTK


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


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


def test_decorator_showcase_lifecycle(root):
    app = DecoratorShowcase(root)
    root.update_idletasks()
    app._on_radius_changed(16.0)
    app._on_border_w_changed(2.0)
    app._on_blur_changed(14.0)
    app._on_offset_y_changed(4.0)
    app._on_focus_ring_w_changed(3.0)
    app._on_toggle_shadows(False)
    app._on_toggle_shadows(True)
    app._on_change_theme("nord")
    app._on_change_theme("tokyo-night")
    root.update_idletasks()
    app.destroy()


def test_ctk_bridge_fallback_lifecycle(root):
    frame = CTKBridgeInfoFrame(root)
    frame.pack()
    root.update_idletasks()
    frame.destroy()
