"""
Tests for Tkinter and TTK font synchronization across tkblend.
"""

import pytest
import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk
import tkblend
from tkblend import (
    FontConfig,
    parse_font,
    extract_font_family,
    sync_tk_fonts,
    apply_theme,
    set_theme,
    get_theme,
)


@pytest.fixture
def root():
    try:
        r = tk.Tk()
        r.withdraw()
        yield r
        r.destroy()
    except tk.TclError:
        pytest.skip("Tkinter display not available")


def assert_scaled_font_size(widget, requested_size):
    actual_size = tkfont.Font(root=widget, font=widget._entry.cget("font")).cget("size")
    assert actual_size == round(requested_size * widget._scale)


def test_extract_font_family():
    # Test simple families
    assert extract_font_family("Helvetica") == "Helvetica"
    assert extract_font_family("Arial") == "Arial"
    assert extract_font_family("Segoe UI") == "Segoe UI"

    # Test file paths
    assert extract_font_family("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf") == "DejaVuSans"
    assert extract_font_family("C:\\Windows\\Fonts\\segoeui.ttf") == "segoeui"
    assert extract_font_family("/fonts/Inter-Regular.otf") == "Inter"
    assert extract_font_family("/fonts/FiraCode_SemiBold.ttf") == "FiraCode"

    # Test default
    fam = extract_font_family("default")
    assert isinstance(fam, str) and len(fam) > 0


def test_fontconfig_to_tk_font(root):
    fc = FontConfig(family="Helvetica", size=14, bold=True, italic=False)
    
    # Without root widget
    tk_tuple = fc.to_tk_font()
    assert tk_tuple == ("Helvetica", 14, "bold")

    fc_italic = FontConfig(family="Arial", size=12, bold=False, italic=True)
    assert fc_italic.to_tk_font() == ("Arial", 12, "italic")

    # With root widget -> returns tkfont.Font
    tk_font = fc.to_tk_font(root)
    assert isinstance(tk_font, tkfont.Font)
    assert tk_font.cget("family") == "Helvetica"
    assert tk_font.cget("size") == 14
    assert tk_font.cget("weight") == "bold"


def test_sync_tk_fonts_named_fonts(root):
    fc = FontConfig(family="Helvetica", size=15, bold=True, italic=False)
    sync_tk_fonts(root, font=fc)

    default_f = tkfont.nametofont("TkDefaultFont")
    assert default_f.cget("family") == "Helvetica"
    assert default_f.cget("size") == 15
    assert default_f.cget("weight") == "bold"

    heading_f = tkfont.nametofont("TkHeadingFont")
    assert heading_f.cget("family") == "Helvetica"
    assert heading_f.cget("size") >= 15
    assert heading_f.cget("weight") == "bold"


def test_sync_tk_fonts_ttk_style(root):
    fc = FontConfig(family="Helvetica", size=13, bold=False, italic=False)
    sync_tk_fonts(root, font=fc)

    style = ttk.Style()
    root_font = style.lookup(".", "font")
    assert "Helvetica" in str(root_font) or ("Helvetica", 13) == root_font or ("Helvetica", 13, "normal") == root_font


def test_sync_tk_fonts_classic_widgets(root):
    frame = tk.Frame(root)
    lbl = tk.Label(frame, text="Hello World")
    btn = tk.Button(frame, text="Click")
    lbl.pack()
    btn.pack()
    frame.pack()

    sync_tk_fonts(root, font=("Helvetica", 16, "bold"))

    lbl_font = str(lbl.cget("font")).lower()
    assert "helvetica" in lbl_font
    assert "16" in lbl_font


def test_sync_tk_fonts_preserve_overrides(root):
    lbl_auto = tk.Label(root, text="Auto")
    lbl_custom = tk.Label(root, text="Custom", font=("Courier", 20, "italic"))
    lbl_custom._tkblend_custom_font_override = True

    lbl_auto.pack()
    lbl_custom.pack()

    sync_tk_fonts(root, font=("Helvetica", 12), preserve_overrides=True)

    auto_font = str(lbl_auto.cget("font")).lower()
    custom_font = str(lbl_custom.cget("font")).lower()

    assert "helvetica" in auto_font
    assert "courier" in custom_font
    assert "20" in custom_font


def test_apply_theme_with_font_sync(root):
    frame = tk.Frame(root)
    lbl = tk.Label(frame, text="Themed Label")
    lbl.pack()
    frame.pack()

    cleanup = apply_theme(root, font=("Helvetica", 14, "bold"), sync_fonts=True)

    default_f = tkfont.nametofont("TkDefaultFont")
    assert default_f.cget("family") == "Helvetica"
    assert default_f.cget("size") == 14

    lbl_font = str(lbl.cget("font")).lower()
    assert "helvetica" in lbl_font

    cleanup()




