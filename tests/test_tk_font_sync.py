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
    Button,
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


def test_text_input_and_spinbox_font_resolution(root):
    from tkblend import TextInput, SpinBox
    
    # Default font matches tkblend default family
    inp = TextInput(root, placeholder="Test")
    spin = SpinBox(root)
    inp.pack()
    spin.pack()

    default_fam = extract_font_family("default")
    assert inp.font_family == "default"
    assert inp.font_size == 12.0
    
    inp_tk_font = str(inp._entry.cget("font"))
    assert default_fam.lower() in inp_tk_font.lower()

    spin_tk_font = str(spin._entry.cget("font"))
    assert default_fam.lower() in spin_tk_font.lower()


def test_text_input_and_spinbox_custom_font_properties(root):
    from tkblend import TextInput, SpinBox

    inp = TextInput(root, font=("Arial", 16, "bold"))
    spin = SpinBox(root, font=("Times", 14, "italic"))
    inp.pack()
    spin.pack()

    assert inp.font.family == "Arial"
    assert inp.font.size == 16.0
    assert inp.font.bold is True
    assert "Arial" in str(inp._entry.cget("font"))
    assert_scaled_font_size(inp, 16)

    # Property mutation on TextInput
    inp.font_size = 18.0
    assert inp.font_size == 18.0
    assert_scaled_font_size(inp, 18)

    inp.font_family = "Courier"
    assert inp.font_family == "Courier"
    assert "Courier" in str(inp._entry.cget("font"))

    inp.configure(font=("Helvetica", 13))
    assert inp.font_family == "Helvetica"
    assert inp.font_size == 13.0
    assert "Helvetica" in str(inp._entry.cget("font"))

    # Property mutation on SpinBox
    spin.font_size = 20.0
    assert spin.font_size == 20.0
    assert_scaled_font_size(spin, 20)

    spin.font_family = "Georgia"
    assert spin.font_family == "Georgia"
    assert "Georgia" in str(spin._entry.cget("font"))


def test_sync_tk_fonts_with_text_input_and_spinbox(root):
    from tkblend import TextInput, SpinBox

    inp_auto = TextInput(root)
    inp_custom = TextInput(root, font=("Courier", 15))
    spin_auto = SpinBox(root)
    spin_custom = SpinBox(root, font=("Georgia", 18))

    inp_auto.pack()
    inp_custom.pack()
    spin_auto.pack()
    spin_custom.pack()

    sync_tk_fonts(root, font=("Helvetica", 14, "bold"), preserve_overrides=True)

    # Auto widgets updated
    assert "Helvetica" in str(inp_auto._entry.cget("font"))
    assert "Helvetica" in str(spin_auto._entry.cget("font"))

    # Custom widgets preserved
    assert "Courier" in str(inp_custom._entry.cget("font"))
    assert_scaled_font_size(inp_custom, 15)
    assert "Georgia" in str(spin_custom._entry.cget("font"))
    assert_scaled_font_size(spin_custom, 18)

