"""
Unit and Integration Tests for ThemedEntry, FloatingScrollbar, ThemedText,
ThemedScrolledFrame, and Dynamic Theme Synchronization in tkblend.
"""

import tkinter as tk
from tkinter import ttk
import pytest
import tkblend


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    tkblend.apply_theme(r, dark_mode=True)
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_theme_palette_resolution(root):
    pal = tkblend.get_theme_palette()
    assert "bg" in pal
    assert "fg" in pal
    assert "input_bg" in pal
    assert "placeholder_fg" in pal
    assert "select_bg" in pal
    assert pal["input_bg"].startswith("#")


def test_themed_entry_placeholder_and_get(root):
    entry = tkblend.ThemedEntry(root, placeholder="Type username...")
    entry.pack()
    root.update()

    # Initial state should show placeholder, but get() returns empty string
    assert entry.get() == ""

    # Focus in hides placeholder
    entry.event_generate("<FocusIn>")
    root.update()
    assert entry.get() == ""

    # Inserting user text
    entry.insert(0, "mateus")
    assert entry.get() == "mateus"

    # Focus out with text preserves text
    entry.event_generate("<FocusOut>")
    root.update()
    assert entry.get() == "mateus"

    # Setting new text
    entry.set("new_user")
    assert entry.get() == "new_user"

    # Setting empty text restores placeholder on blur
    entry.set("")
    assert entry.get() == ""


def test_searchentry(root):
    search = tkblend.SearchEntry(root, placeholder="Search logs...")
    search.pack()
    root.update()
    assert search.get() == ""
    search.set("query")
    assert search.get() == "query"


def test_docked_scrollbar_geometry_and_tracking(root):
    text = tk.Text(root, wrap="none", height=5, width=20)
    text.pack(side="left", fill="both", expand=True)
    for i in range(50):
        text.insert("end", f"Line {i}\n")

    scroller = ttk.Scrollbar(root, orient="vertical", command=text.yview)
    text.configure(yscrollcommand=scroller.set)
    scroller.pack(side="right", fill="y", padx=(2, 4), pady=2)
    root.update()

    assert scroller.winfo_manager() == "pack"
    assert str(scroller.cget("orient")) == "vertical"

    # Set fractions and test get()
    scroller.set(0.2, 0.6)
    assert scroller.get() == (0.2, 0.6)

    # Test wheel scroll handling directly via text widget
    initial_yview = text.yview()
    text.yview_scroll(2, "units")
    root.update()
    new_yview = text.yview()
    assert new_yview != initial_yview


def test_themed_text_and_sync(root):
    themed_text = tkblend.ThemedText(root, height=6, width=30)
    themed_text.pack()
    root.update()

    assert themed_text.scrollbar.winfo_manager() == "pack"
    assert str(themed_text.scrollbar.cget("orient")) == "vertical"

    themed_text.insert("1.0", "Native Blend2D Theme Line 1\nLine 2\nLine 3\n")
    assert "Native Blend2D Theme" in themed_text.get("1.0", "end")

    # Switch to light mode
    tkblend.apply_theme(root, dark_mode=False)
    root.update()

    pal_light = tkblend.get_theme_palette()
    assert themed_text.text.cget("background") == pal_light["card_bg"]

    # Switch back to dark mode
    tkblend.apply_theme(root, dark_mode=True)
    root.update()

    pal_dark = tkblend.get_theme_palette()
    assert themed_text.text.cget("background") == pal_dark["card_bg"]


def test_themed_scrolled_frame(root):
    scrolled = tkblend.ThemedScrolledFrame(root, height=200, width=300)
    scrolled.pack(fill="both", expand=True)

    for i in range(20):
        btn = ttk.Button(scrolled.content, text=f"Item {i}")
        btn.pack(pady=4)

    root.update()
    assert scrolled.scrollbar.winfo_manager() == "pack"
    assert str(scrolled.scrollbar.cget("orient")) == "vertical"

    # Dynamic theme change
    tkblend.apply_theme(root, dark_mode=False)
    root.update()
    tkblend.apply_theme(root, dark_mode=True)
    root.update()


def test_sync_widget_colors(root):
    text_w = tk.Text(root)
    canvas_w = tk.Canvas(root)
    entry_w = tk.Entry(root)

    tkblend.apply_theme(root, dark_mode=True)
    tkblend.sync_widget_colors(text_w)
    tkblend.sync_widget_colors(canvas_w)
    tkblend.sync_widget_colors(entry_w)

    pal = tkblend.get_theme_palette()
    assert text_w.cget("background") == pal["card_bg"]
    assert canvas_w.cget("background") == pal["card_bg"]
    assert entry_w.cget("background") == pal["input_bg"]
