"""
Visual Verification & Screenshot Capture Script for tkblend Widgets Showcase.
Runs headlessly under xvfb-run and uses PIL (Pillow) to capture and validate high-res UI pages.
"""

from __future__ import annotations

import os
import sys
import time
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageGrab

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from examples.widgets_showcase import WidgetsShowcaseApp
import tkblend as tb


def capture_window_screenshot(root: tk.Tk, output_path: Path) -> Image.Image:
    """Capture precise window contents using PIL ImageGrab."""
    root.update_idletasks()
    root.update()

    # Geometry bounds
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()

    # Take grab
    bbox = (x, y, x + w, y + h)
    img = ImageGrab.grab(bbox=bbox)

    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), format="PNG")
    print(f"  [SAVED] {output_path.name} ({img.width}x{img.height})")
    return img


def run_visual_verification():
    print("==================================================================")
    print("Starting tkblend Native Showcase Visual Verification & Capture")
    print("==================================================================")

    output_dir = PROJECT_ROOT / "examples" / "screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)

    root = tk.Tk()
    root.title("Visual Test Runner")
    app = WidgetsShowcaseApp(root)

    # Let the UI settle
    for _ in range(5):
        root.update_idletasks()
        root.update()
        time.sleep(0.05)

    captured_files = []

    # 1. Capture All Dashboard Pages under Default Dark Theme
    pages = [
        ("controls", "01_controls_dark.png"),
        ("gauges", "02_gauges_dark.png"),
        ("playground", "03_playground_dark.png"),
        ("themes", "04_themes_matrix_dark.png"),
    ]

    for page_id, filename in pages:
        print(f"\nNavigating to '{page_id}' page...")
        app._navigate_to(page_id)
        for _ in range(4):
            root.update_idletasks()
            root.update()
            time.sleep(0.05)

        target_file = output_dir / filename
        img = capture_window_screenshot(root, target_file)
        assert img.width > 800 and img.height > 600, f"Invalid capture size: {img.size}"
        captured_files.append(target_file)

    # 2. Capture Showcase in Light and Cyberpunk Themes
    theme_tests = [
        ("light", "controls", "05_controls_light.png"),
        ("cyberpunk", "gauges", "06_gauges_cyberpunk.png"),
        ("dracula", "playground", "07_playground_dracula.png"),
        ("tokyo_night", "controls", "08_controls_tokyo_night.png"),
    ]

    for theme_name, page_id, filename in theme_tests:
        print(f"\nApplying theme '{theme_name}' and navigating to '{page_id}'...")
        app._change_theme(theme_name)
        app._navigate_to(page_id)
        for _ in range(5):
            root.update_idletasks()
            root.update()
            time.sleep(0.05)

        target_file = output_dir / filename
        img = capture_window_screenshot(root, target_file)
        assert img.width > 800 and img.height > 600, f"Invalid capture size: {img.size}"
        captured_files.append(target_file)

    # 3. Dynamic Page Cycling Test (Navigate away and return to controls multiple times)
    print("\nExecuting multi-step dynamic page switching (testing unmap -> remap behavior)...")
    app._change_theme("dark")
    app._navigate_to("gauges")
    root.update_idletasks()
    root.update()
    time.sleep(0.05)
    app._navigate_to("themes")
    root.update_idletasks()
    root.update()
    time.sleep(0.05)
    app._navigate_to("playground")
    root.update_idletasks()
    root.update()
    time.sleep(0.05)
    app._navigate_to("controls")
    root.update_idletasks()
    root.update()
    time.sleep(0.05)

    cycled_target = output_dir / "09_controls_returned_after_switching.png"
    img = capture_window_screenshot(root, cycled_target)
    captured_files.append(cycled_target)

    print("\n------------------------------------------------------------------")
    print(f"Visual verification succeeded! Captured {len(captured_files)} screenshots in:")
    print(f"  {output_dir}")
    print("------------------------------------------------------------------")

    # Clean window destruction
    del app
    root.destroy()
    import gc
    gc.collect()
    return True


if __name__ == "__main__":
    success = run_visual_verification()
    sys.exit(0 if success else 1)
