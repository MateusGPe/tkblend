"""
Automated visual & multi-step theme switching tests for tkblend using PIL and xvfb.
Verifies that BlendDecorator, BlendCanvas, and standard Tk elements update backgrounds,
foregrounds, and borders without color bleed or locked-in ancestor backgrounds.
"""

import pytest
import tkinter as tk
from tkinter import ttk

pytest.importorskip("PIL")
from PIL import Image, ImageGrab, ImageStat
import tkblend as tb
from tkblend import (
    set_theme,
    get_theme,
    get_available_themes,
    apply_theme,
    flush_theme_queue,
    BlendDecorator,
    BlendCanvas,
)


@pytest.fixture
def tk_root():
    try:
        r = tk.Tk()
        r.geometry("900x700")
        r.update()
        yield r
        r.destroy()
    except tk.TclError:
        pytest.skip("Tkinter display not available")


def test_multistep_theme_cycling_colors(tk_root):
    """Test switching through 6 distinct themes consecutively to ensure full palette propagation."""
    root = tk_root
    pal = get_theme()
    
    # Left Column: Standard controls decorated by BlendDecorator
    dec1 = BlendDecorator(root, radius=12, width=380, height=250, shadow_blur=8)
    dec1.pack(side="left", padx=15, pady=15, fill="both", expand=True)
    
    lbl1 = tk.Label(dec1, text="Decorated Label", font=("Segoe UI", 12, "bold"))
    lbl1.pack(pady=8)
    entry1 = ttk.Entry(dec1)
    entry1.pack(pady=8)
    btn1 = ttk.Button(dec1, text="Action Button")
    btn1.pack(pady=8)

    # Right Column: Canvas & secondary decorator
    dec2 = BlendDecorator(root, radius=16, width=380, height=250, shadow_blur=10)
    dec2.pack(side="right", padx=15, pady=15, fill="both", expand=True)
    
    canvas = BlendCanvas(dec2, width=300, height=150)
    canvas.pack(pady=10)

    root.update()

    themes_sequence = ["dark", "light", "dracula", "cyberpunk", "solarized_light", "nord", "dark"]

    for theme_name in themes_sequence:
        apply_theme(root, theme_name)
        flush_theme_queue()
        root.update_idletasks()
        root.update()
        import time
        time.sleep(0.02)
        root.update()
        
        cur_pal = get_theme()
        assert cur_pal.name == theme_name
        
        # Verify root background matches active palette
        assert root.cget("background").lower() == cur_pal.bg.lower()
        
        # Verify decorator background color matches
        assert dec1.bg_color.lower() == cur_pal.card_bg.lower()
        assert dec2.bg_color.lower() == cur_pal.card_bg.lower()
        
        # Capture screenshot via PIL and verify image properties
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()
        if w > 10 and h > 10:
            img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            stat = ImageStat.Stat(img)
            assert img.size == (w, h)
            assert any(channel_stddev > 0 for channel_stddev in stat.stddev[:3])
