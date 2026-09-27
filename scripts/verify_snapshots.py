"""
Visual snapshot verification script running under Xvfb using PIL/tk/tkblend.
Renders all core widgets and example layouts to test for rendering artifacts,
black boxes, misalignments, and theme transitions.
"""
import os
import sys
import time
import tkinter as tk
from PIL import ImageGrab, Image

from tkblend import (
    Button,
    Badge,
    Avatar,
    TextInput,
    SpinBox,
    Switch,
    Checkbutton,
    Radiobutton,
    SegmentedControl,
    Progressbar,
    CircularProgress,
    Slider,
    RangeSlider,
    Frame,
    Card,
    Dropdown,
    set_theme,
    get_theme,
)

def destroy_hierarchy(widget):
    for child in list(getattr(widget, "children", {}).values()):
        destroy_hierarchy(child)
    if hasattr(widget, "destroy"):
        try:
            widget.destroy()
        except Exception:
            pass

def run_visual_tests():
    root = tk.Tk()
    root.geometry("1000x800+50+50")
    root.title("Visual Snapshot Verification")

    def build_test_ui():
        # Clear root recursively
        for child in list(root.winfo_children()):
            destroy_hierarchy(child)

        pal = get_theme()
        root.configure(bg=pal.bg)

        card = Card(root, title="Controls & Inputs Gallery", width=920, height=720)
        card.pack(padx=20, pady=20, fill="both", expand=True)

        body = card.body

        # Row 1: Buttons and Badges
        r1 = tk.Frame(body, bg=card.bg_color)
        r1.pack(fill="x", pady=5)
        b1 = Button(r1, text="Primary", variant="primary")
        b1.pack(side="left", padx=5)
        b2 = Button(r1, text="Secondary", variant="secondary")
        b2.pack(side="left", padx=5)
        b3 = Button(r1, text="Destructive", variant="destructive")
        b3.pack(side="left", padx=5)
        b4 = Button(r1, text="Outline", variant="outline")
        b4.pack(side="left", padx=5)
        b5 = Button(r1, text="Ghost", variant="ghost")
        b5.pack(side="left", padx=5)
        badge = Badge(r1, text="Active", variant="success")
        badge.pack(side="left", padx=10)
        avatar = Avatar(r1, text="JD", size=36)
        avatar.pack(side="left", padx=5)

        # Row 2: Inputs & Selection
        r2 = tk.Frame(body, bg=card.bg_color)
        r2.pack(fill="x", pady=10)
        inp = TextInput(r2, placeholder="Type something...", width=180)
        inp.pack(side="left", padx=5)
        spin = SpinBox(r2, from_=0, to=100, width=100)
        spin.pack(side="left", padx=5)
        sw = Switch(r2, text="Dark Mode", is_on=True)
        sw.pack(side="left", padx=10)
        cb = Checkbutton(r2, text="Remember Me", is_checked=True)
        cb.pack(side="left", padx=10)
        rb = Radiobutton(r2, text="Option 1", is_selected=True)
        rb.pack(side="left", padx=10)

        # Row 3: Segmented Control & Sliders
        r3 = tk.Frame(body, bg=card.bg_color)
        r3.pack(fill="x", pady=10)
        seg = SegmentedControl(r3, items=["Overview", "Analytics", "Settings", "Reports"], width=360)
        seg.pack(side="left", padx=5)
        sl = Slider(r3, from_=0, to=100, value=65, width=180)
        sl.pack(side="left", padx=15)
        rsl = RangeSlider(r3, from_=0, to=100, low_val=20, high_val=80, width=180)
        rsl.pack(side="left", padx=15)

        # Row 4: Progress & Gauges
        r4 = tk.Frame(body, bg=card.bg_color)
        r4.pack(fill="x", pady=10)
        pb = Progressbar(r4, value=75, width=250)
        pb.pack(side="left", padx=5)
        cp = CircularProgress(r4, value=68, size=80, thickness=8.0)
        cp.pack(side="left", padx=20)
        dd = Dropdown(r4, options=["Option A", "Option B", "Option C"], width=160)
        dd.pack(side="left", padx=15)

    os.makedirs("artifacts/snapshots", exist_ok=True)

    # 1. Test Dark Theme
    set_theme("dark")
    build_test_ui()
    root.update_idletasks()
    root.update()
    time.sleep(0.1)
    root.update()

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()
    shot_dark = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    shot_dark.save("artifacts/snapshots/dark_theme.png")
    print(f"Captured dark theme screenshot: size={shot_dark.size}")

    # 2. Test Light Theme
    set_theme("light")
    build_test_ui()
    root.update_idletasks()
    root.update()
    time.sleep(0.1)
    root.update()

    shot_light = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    shot_light.save("artifacts/snapshots/light_theme.png")
    print(f"Captured light theme screenshot: size={shot_light.size}")

    # Inspect images with PIL for rendering validity
    assert shot_dark.size == (w, h), f"Dark screenshot size mismatch: {shot_dark.size} vs {(w, h)}"
    assert shot_light.size == (w, h), f"Light screenshot size mismatch: {shot_light.size} vs {(w, h)}"

    # Sample central pixels to ensure light theme isn't completely black
    light_pixels = list(shot_light.getdata())
    avg_light_brightness = sum(sum(p[:3]) / 3 for p in light_pixels) / len(light_pixels)
    dark_pixels = list(shot_dark.getdata())
    avg_dark_brightness = sum(sum(p[:3]) / 3 for p in dark_pixels) / len(dark_pixels)

    print(f"Average Light Theme Brightness: {avg_light_brightness:.1f}/255")
    print(f"Average Dark Theme Brightness: {avg_dark_brightness:.1f}/255")
    assert avg_light_brightness > 150.0, "Light theme is too dark / rendered black!"
    assert avg_dark_brightness < 100.0, "Dark theme is too bright!"

    # Clean teardown
    destroy_hierarchy(root)
    del shot_dark, shot_light

if __name__ == "__main__":
    from tkblend import clear_caches
    run_visual_tests()
    import gc
    gc.collect()
    clear_caches()
    print("Snapshot verification PASSED successfully!")
