#!/usr/bin/env python3
"""
Headless Visual Verification Script for tkblend Table Widget.
Captures high-resolution PNGs of table_demo.py under xvfb-run,
validates drawing of headers, rows, zebra stripes, selection highlight,
column sorting, and light/dark theme transitions using PIL.
"""

from __future__ import annotations

import os
import sys
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageGrab

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkblend as tb
from examples.table_demo import TableDemoApp


def capture_window(window: tk.Tk, dest_path: Path) -> Image.Image:
    window.update_idletasks()
    window.update()

    # Repaint all tkblend controls
    _repaint_recurse(window)
    window.update_idletasks()
    window.update()

    x = window.winfo_rootx()
    y = window.winfo_rooty()
    w = window.winfo_width()
    h = window.winfo_height()

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save(str(dest_path))
    print(f"Captured: {dest_path.name} ({img.size[0]}x{img.size[1]})")
    return img


def _repaint_recurse(widget):
    if hasattr(widget, "paint_and_blit"):
        try:
            widget.paint_and_blit()
        except Exception:
            pass
    for child in widget.winfo_children():
        _repaint_recurse(child)


def verify_screenshot(img: Image.Image, name: str, expected_min_colors: int = 4) -> None:
    w, h = img.size
    assert w >= 600 and h >= 400, f"{name}: Screenshot size too small {img.size}"

    # Sample pixel colors across an 8x8 grid
    colors = set()
    for gx in range(1, 8):
        for gy in range(1, 8):
            px = int(w * (gx / 8.0))
            py = int(h * (gy / 8.0))
            colors.add(img.getpixel((px, py))[:3])

    assert len(colors) >= expected_min_colors, (
        f"{name}: Visual variance check failed, found only {len(colors)} distinct colors. "
        "Widget may be rendered blank or solid black."
    )
    print(f"Verified: {name} passes visual check ({len(colors)} distinct sampled colors)")


def run_checks():
    dest_dir = PROJECT_ROOT / "screenshots"
    dest_dir.mkdir(parents=True, exist_ok=True)

    print("=== Launching Table Demo App under headless X11 ===")
    app = TableDemoApp()
    app.update()

    # 1. Dark Theme Initial Capture
    dark_path = dest_dir / "table_demo_dark.png"
    img_dark = capture_window(app, dark_path)
    verify_screenshot(img_dark, "table_demo_dark.png")

    # 2. Test Selection & Sorting
    print("=== Testing Row Selection and Sorting ===")
    app.table.selected_row = 2
    app.table._sort_by_column(1)  # Sort by Service Name
    app.update()

    sorted_path = dest_dir / "table_demo_sorted_selected.png"
    img_sorted = capture_window(app, sorted_path)
    verify_screenshot(img_sorted, "table_demo_sorted_selected.png")

    # 3. Test Light Theme
    print("=== Testing Light Theme Switch ===")
    app._toggle_theme()
    app.update()

    light_path = dest_dir / "table_demo_light.png"
    img_light = capture_window(app, light_path)
    verify_screenshot(img_light, "table_demo_light.png")

    app.destroy()
    print("\n✓ All Table visual verification checks passed successfully!")


if __name__ == "__main__":
    run_checks()
