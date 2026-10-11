#!/usr/bin/env python3
"""
Headless Screenshot & Visual Verification Script
Captures showcase.py and individual controls under xvfb-run using PIL.ImageGrab,
saves high-resolution PNGs to screenshots/, and verifies pixel buffers.
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
from examples.showcase import ShowcaseApp


def capture_window(window: tk.Tk, dest_path: Path) -> Image.Image:
    window.update_idletasks()
    window.update()

    # Repaint all tkblend controls
    for w in window.winfo_children():
        _repaint_recurse(w)
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


def verify_image(img: Image.Image, name: str):
    w, h = img.size
    assert w > 100 and h > 100, f"{name}: image too small {img.size}"

    # Sample colors across image
    colors = set()
    for sx in [w // 4, w // 2, 3 * w // 4]:
        for sy in [h // 4, h // 2, 3 * h // 4]:
            colors.add(img.getpixel((sx, sy))[:3])

    # Ensure it's not a single solid color or black screen
    assert len(colors) >= 2, f"{name}: image appears blank or single solid color"
    print(f"Verified: {name} passes visual variance check ({len(colors)} distinct sampled colors)")


def main():
    dest_dir = PROJECT_ROOT / "screenshots"
    dest_dir.mkdir(parents=True, exist_ok=True)

    print("=== Launching Showcase in Dark Mode ===")
    app = ShowcaseApp()
    app.update()

    # 1. Dark Theme Capture
    dark_path = dest_dir / "showcase_dark.png"
    img_dark = capture_window(app, dark_path)
    verify_image(img_dark, "showcase_dark.png")

    # 2. Toggle to Light Theme
    print("=== Toggling to Light Mode ===")
    app._select_theme("light")
    app.update()

    light_path = dest_dir / "showcase_light.png"
    img_light = capture_window(app, light_path)
    verify_image(img_light, "showcase_light.png")

    # 3. Simulate Live Interactions
    print("=== Simulating Live Interactions (clicks, slider drag, radio selection) ===")
    app.btn_counter.on_click(0, 0, 1)
    app.btn_counter.on_click(0, 0, 1)
    app.btn_counter.on_click(0, 0, 1)
    app.slider.set(85.0)
    app._on_slider_moved(85.0)
    app.sw_notif.is_checked = True
    app.sw_notif.request_redraw()
    app.table.selected_row = 1
    app.update()

    interactive_path = dest_dir / "showcase_interactive.png"
    img_inter = capture_window(app, interactive_path)
    verify_image(img_inter, "showcase_interactive.png")

    app.destroy()
    print(f"\nAll screenshots exported successfully to {dest_dir}")


if __name__ == "__main__":
    main()
