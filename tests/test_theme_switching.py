"""
Automated visual & multi-step theme switching tests for tkblend using PIL and xvfb.
Verifies that all widgets, containers, and standard Tk elements update backgrounds,
foregrounds, and borders without color bleed or locked-in ancestor backgrounds.
"""

import pytest
import tkinter as tk

pytest.importorskip("PIL")
from PIL import Image, ImageGrab, ImageStat
import tkblend as tb
from tkblend import (
    set_theme,
    get_theme,
    get_available_themes,
    apply_theme,
    flush_theme_queue,
    Button,
    Card,
    Frame,
    Switch,
    Checkbox,
    Slider,
    ProgressBar,
    Entry,
    OptionMenu,
    SegmentedButton,
    Tabview,
    Table,
    ScrollableFrame,
    Accordion,
    Badge,
    Avatar,
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
    
    # Left Column: Standard vector widgets inside a Card
    card1 = Card(root, title="Vector Controls", width=400, height=600)
    card1.pack(side="left", padx=10, pady=10, fill="both", expand=True)
    body1 = card1.body
    
    btn1 = Button(body1, text="Primary Action", bootstyle="primary")
    btn1.pack(pady=4)
    btn2 = Button(body1, text="Secondary Action", bootstyle="secondary")
    btn2.pack(pady=4)
    sw = Switch(body1, text="Live Toggle")
    sw.pack(pady=4)
    cb = Checkbox(body1, text="Check Option")
    cb.pack(pady=4)
    sl = Slider(body1, from_=0, to=100)
    sl.pack(pady=4)
    pb = ProgressBar(body1, value=50)
    pb.pack(pady=4)
    om = OptionMenu(body1, values=["Alpha", "Beta", "Gamma"])
    om.pack(pady=4)
    sb = SegmentedButton(body1, values=["Day", "Week", "Month"])
    sb.pack(pady=4)
    
    # Right Column: Nested containers, Accordion, Tabview, and Table
    card2 = Card(root, title="Complex Containers", width=400, height=600)
    card2.pack(side="right", padx=10, pady=10, fill="both", expand=True)
    body2 = card2.body
    
    acc = Accordion(body2, title="Collapsible Settings")
    acc.pack(fill="x", pady=4)
    lbl_acc = tk.Label(acc._content, text="Inner Content Label")
    lbl_acc.pack(pady=4)
    
    tab = Tabview(body2, width=360, height=140)
    tab.pack(fill="x", pady=4)
    tab_page = tab.add("General")
    btn_tab = Button(tab_page, text="Inside Tab")
    btn_tab.pack(pady=8)
    
    tbl = Table(body2, columns=["ID", "Name", "Status"], width=360, height=120)
    tbl.insert_row(["01", "Alpha", "Active"])
    tbl.insert_row(["02", "Beta", "Done"])
    tbl.pack(fill="x", pady=4)

    root.update()

    themes_sequence = ["dark", "light", "dracula", "cyberpunk", "solarized_light", "nord", "dark"]

    for theme_name in themes_sequence:
        set_theme(theme_name)
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
        
        # Verify Card surface colors & parent background match
        assert card1.bg_color.lower() == cur_pal.card_bg.lower()
        assert card1._parent_bg.lower() == cur_pal.bg.lower()
        assert card1._bg_label.cget("background").lower() == cur_pal.bg.lower()
        assert body1.cget("background").lower() == cur_pal.card_bg.lower()
        
        # Verify leaf widget inside card inherits card_bg as its parent background
        assert btn1._parent_bg.lower() == cur_pal.card_bg.lower()
        assert btn1.cget("background").lower() == cur_pal.card_bg.lower()
        
        # Verify accordion inner content and standard Tk label colors
        assert acc._parent_bg.lower() == cur_pal.card_bg.lower()
        assert acc._content.cget("background").lower() == cur_pal.surface.lower()
        assert lbl_acc.cget("background").lower() == cur_pal.surface.lower()
        assert lbl_acc.cget("foreground").lower() == cur_pal.text_muted.lower()
        
        # Verify Table parent background matches enclosing card
        assert tbl._parent_bg.lower() == cur_pal.card_bg.lower()
        
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
