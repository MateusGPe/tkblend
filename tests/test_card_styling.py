"""
Tests for Card.* styles and card-child background synchronization.
"""

import pytest
import tkinter as tk
from tkinter import ttk
import tkblend


@pytest.fixture
def root():
    try:
        r = tk.Tk()
        r.withdraw()
        yield r
        r.destroy()
    except tk.TclError:
        pytest.skip("Tk display not available in environment")


def test_card_styles_registered(root):
    """Verify that Card.* styles are configured in the TTK theme engine."""
    tkblend.apply_theme(root, dark_mode=True)
    style = ttk.Style(master=root)
    pal = tkblend.get_theme_palette()

    # Verify Card.TFrame
    assert style.lookup("Card.TFrame", "background") == pal["card_bg"]

    # Verify Card.TLabel
    assert style.lookup("Card.TLabel", "background") == pal["card_bg"]

    # Verify Card.TCheckbutton
    assert style.lookup("Card.TCheckbutton", "background") == pal["card_bg"]

    # Verify Card.TRadiobutton
    assert style.lookup("Card.TRadiobutton", "background") == pal["card_bg"]


def test_is_inside_card(root):
    """Verify is_inside_card correctly distinguishes card containers from root widgets."""
    tkblend.apply_theme(root, dark_mode=True)

    header = ttk.Frame(root)
    header_lbl = ttk.Label(header, text="Root Header")
    assert not tkblend.is_inside_card(header)
    assert not tkblend.is_inside_card(header_lbl)

    card = ttk.Labelframe(root, text="Settings")
    card_row = ttk.Frame(card)
    card_lbl = ttk.Label(card_row, text="Nested Label")
    assert tkblend.is_inside_card(card_row)
    assert tkblend.is_inside_card(card_lbl)

    custom_card = ttk.Frame(root, style="Card.TFrame")
    inner_lbl = ttk.Label(custom_card, text="Card Frame Child")
    assert tkblend.is_inside_card(inner_lbl)


def test_sync_card_children_upgrades_default_styles(root):
    """Verify unstyled widgets in a Card/Labelframe are upgraded to Card.* styles."""
    card = ttk.Labelframe(root, text="Inputs")
    card.pack()

    row = ttk.Frame(card)
    row.pack()
    lbl = ttk.Label(row, text="Username:")
    lbl.pack()
    chk = ttk.Checkbutton(row, text="Remember")
    chk.pack()
    rb = ttk.Radiobutton(row, text="Option")
    rb.pack()

    # Custom styled widget should NOT be overridden
    custom_lbl = ttk.Label(row, text="Custom", style="Custom.TLabel")
    custom_lbl.pack()

    # Classic Tk widget
    tk_lbl = tk.Label(row, text="Classic")
    tk_lbl.pack()

    tkblend.apply_theme(root, dark_mode=True)

    assert row.cget("style") == "Card.TFrame"
    assert lbl.cget("style") == "Card.TLabel"
    assert chk.cget("style") == "Card.TCheckbutton"
    assert rb.cget("style") == "Card.TRadiobutton"
    assert custom_lbl.cget("style") == "Custom.TLabel"

    pal = tkblend.get_theme_palette()
    assert tk_lbl.cget("background") == pal["card_bg"]


def test_theme_mode_toggle_card_sync(root):
    """Verify switching themes updates card styling cleanly."""
    card = ttk.Labelframe(root, text="Panel")
    card.pack()
    row = ttk.Frame(card)
    row.pack()
    lbl = ttk.Label(row, text="Mode Test")
    lbl.pack()
    tk_frame = tk.Frame(row)
    tk_frame.pack()

    # Apply dark mode
    tkblend.apply_theme(root, dark_mode=True)
    dark_pal = tkblend.get_theme_palette()
    assert tk_frame.cget("background") == dark_pal["card_bg"]

    # Toggle to light mode
    tkblend.apply_theme(root, dark_mode=False)
    light_pal = tkblend.get_theme_palette()
    assert tk_frame.cget("background") == light_pal["card_bg"]
    assert dark_pal["card_bg"] != light_pal["card_bg"]
