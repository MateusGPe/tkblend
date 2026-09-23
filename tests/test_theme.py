"""
Tests for tkblend.theme: Palette, ThemeManager, dynamic switching, and color utilities.
"""

import pytest
import tkinter as tk
from tkblend.theme import (
    Palette,
    DARK_PALETTE,
    LIGHT_PALETTE,
    ThemeManager,
    get_theme,
    get_palette,
    set_theme,
    set_dark_mode,
    add_theme_listener,
    remove_theme_listener,
    resolve_theme_color,
    resolve_color_failsafe,
    resolve_ancestor_bg,
    apply_theme,
    inject_theme,
    blend_color_hex,
    adjust_brightness,
    is_inside_card,
    is_ttkbootstrap_installed,
)
from tkblend.widgets import Button, Card, Frame, TextInput


@pytest.fixture
def root():
    try:
        r = tk.Tk()
        r.withdraw()
        yield r
        r.destroy()
    except tk.TclError:
        pytest.skip("Tkinter display not available")


def test_builtin_palettes():
    assert DARK_PALETTE.dark_mode is True
    assert LIGHT_PALETTE.dark_mode is False
    assert DARK_PALETTE.bg.startswith("#")
    assert LIGHT_PALETTE.bg.startswith("#")
    assert DARK_PALETTE.primary.startswith("#")
    assert LIGHT_PALETTE.primary.startswith("#")


def test_theme_switching():
    # Switch to light
    set_theme("light")
    assert get_theme().name == "light"
    assert get_palette().dark_mode is False

    # Switch to dark
    set_theme("dark")
    assert get_theme().name == "dark"
    assert get_palette().dark_mode is True

    # Switch via set_dark_mode
    set_dark_mode(False)
    assert get_theme().name == "light"
    set_dark_mode(True)
    assert get_theme().name == "dark"


def test_theme_listeners():
    received = []

    def on_change(palette: Palette):
        received.append(palette.name)

    add_theme_listener(on_change)
    set_theme("light")
    assert received == ["light"]

    set_theme("dark")
    assert received == ["light", "dark"]

    remove_theme_listener(on_change)
    set_theme("light")
    assert received == ["light", "dark"]  # Not notified after removal

    # Reset back to dark
    set_theme("dark")


def test_resolve_theme_color():
    # Semantic token resolution
    set_theme("dark")
    resolved_primary = resolve_theme_color("primary")
    assert resolved_primary == DARK_PALETTE.primary

    # Hex resolution
    assert resolve_theme_color("#123") == "#112233"
    assert resolve_theme_color("#112233") == "#112233"

    # Hex resolution with alpha
    resolved_alpha = resolve_theme_color("#112233", alpha=0.5)
    assert resolved_alpha.startswith("#112233")
    assert len(resolved_alpha) == 9  # #RRGGBBAA

    # Named colors
    assert resolve_theme_color("white") == "#ffffff"
    assert resolve_theme_color("black") == "#000000"


def test_color_math():
    # blend_color_hex
    c = blend_color_hex("#000000", "#ffffff", 0.5)
    assert c.lower() == "#7f7f7f"
    assert blend_color_hex("#000000", "#ffffff", 0.0) == "#000000"
    assert blend_color_hex("#000000", "#ffffff", 1.0) == "#ffffff"

    # adjust_brightness
    darker = adjust_brightness("#ffffff", 0.5)
    assert darker.lower() == "#7f7f7f"


def test_ttk_bridge_helpers():
    assert is_ttkbootstrap_installed() is False
    assert is_inside_card(None) is False


def test_resolve_color_failsafe(root):
    set_theme("dark")
    # None, empty, invalid types fallback safely
    assert resolve_color_failsafe(None) == DARK_PALETTE.bg
    assert resolve_color_failsafe("") == DARK_PALETTE.bg
    assert resolve_color_failsafe(12345, fallback="#aabbcc") == "#aabbcc"

    # Hex formats
    assert resolve_color_failsafe("#abc") == "#aabbcc"
    assert resolve_color_failsafe("#112233") == "#112233"
    assert resolve_color_failsafe("#11223344") == "#11223344"
    assert resolve_color_failsafe("#112233", alpha=0.5).startswith("#112233")

    # Semantic tokens
    assert resolve_color_failsafe("primary") == DARK_PALETTE.primary
    assert resolve_color_failsafe("card-bg") == DARK_PALETTE.card_bg
    assert resolve_color_failsafe("surface") == DARK_PALETTE.surface

    # Named web colors
    assert resolve_color_failsafe("white") == "#ffffff"
    assert resolve_color_failsafe("black") == "#000000"
    assert resolve_color_failsafe("red") == "#ff0000"

    # Tk system / X11 color name via winfo_rgb
    converted = resolve_color_failsafe("gray85", master=root)
    assert converted.startswith("#")
    assert len(converted) == 7

    # Non-existent color name safely returns fallback
    assert resolve_color_failsafe("not_a_real_color_xyz", fallback="#334455") == "#334455"


def test_resolve_ancestor_bg(root):
    set_theme("dark")
    # None master returns palette.bg
    assert resolve_ancestor_bg(None) == DARK_PALETTE.bg

    # Inside a Card container
    card = Card(root, title="Resolver Test", bg_color="#332244")
    assert resolve_ancestor_bg(card) == "#332244"

    # Inside a tk.Frame that is inside the Card
    subframe = tk.Frame(card)
    assert resolve_ancestor_bg(subframe) == "#332244"

    # Inside a standard Tk container outside of any Card
    plain_frame = tk.Frame(root, bg="#556677")
    assert resolve_ancestor_bg(plain_frame) == "#556677"

    # Nested inside plain Tk frame
    inner_plain = tk.Frame(plain_frame)
    # The nearest ancestor with bg is plain_frame
    assert resolve_ancestor_bg(inner_plain) in ("#556677", resolve_color_failsafe(inner_plain.cget("background")))

    inner_plain.destroy()
    plain_frame.destroy()
    subframe.destroy()
    card.destroy()


def test_apply_theme_and_dynamic_injection(root):
    set_theme("dark")
    f = tk.Frame(root)
    lbl = tk.Label(root, text="Hello")
    cvs = tk.Canvas(root)
    btn = Button(root, text="Vector Btn")

    cleanup = apply_theme(root, "dark")
    root.update_idletasks()

    assert f.cget("background") == DARK_PALETTE.bg
    assert lbl.cget("background") == DARK_PALETTE.bg
    assert cvs.cget("background") == DARK_PALETTE.bg
    assert btn._parent_bg == DARK_PALETTE.bg

    # Switch theme to light and verify all standard Tk and tkblend widgets auto-sync
    set_theme("light")
    root.update_idletasks()

    assert f.cget("background") == LIGHT_PALETTE.bg
    assert lbl.cget("background") == LIGHT_PALETTE.bg
    assert cvs.cget("background") == LIGHT_PALETTE.bg
    assert btn._parent_bg == LIGHT_PALETTE.bg

    # Cleanup listener
    cleanup()

    # Reset back to dark
    set_theme("dark")
    f.destroy()
    lbl.destroy()
    cvs.destroy()
    btn.destroy()


def test_apply_theme_preserve_overrides(root):
    set_theme("dark")
    f_custom = tk.Frame(root, bg="#ff0000")
    f_default = tk.Frame(root)

    # Apply with preserve_overrides=True (default)
    cleanup = apply_theme(root, "dark", preserve_overrides=True)
    root.update_idletasks()

    assert f_custom.cget("background") == "#ff0000"
    assert f_default.cget("background") == DARK_PALETTE.bg

    # Switch theme to light
    set_theme("light")
    root.update_idletasks()

    # Custom background is preserved
    assert f_custom.cget("background") == "#ff0000"
    # Default frame adapted to new light theme
    assert f_default.cget("background") == LIGHT_PALETTE.bg

    # Now apply with preserve_overrides=False (forced)
    apply_theme(root, "light", preserve_overrides=False)
    root.update_idletasks()
    assert f_custom.cget("background") == LIGHT_PALETTE.bg

    cleanup()
    set_theme("dark")
    f_custom.destroy()
    f_default.destroy()


def test_dynamic_container_bg_cascade(root):
    set_theme("dark")
    card = Card(root, title="Dynamic Cascade")
    subframe = tk.Frame(card)
    btn = Button(subframe, text="Click")
    inp = TextInput(subframe, placeholder="Type")

    root.update_idletasks()
    assert btn._parent_bg == card._bg_color
    assert inp._parent_bg == card._bg_color

    # Dynamically change card's surface background
    card.set_background("#112233")
    root.update_idletasks()

    assert btn._parent_bg == "#112233"
    assert inp._parent_bg == "#112233"

    # Switch theme to light
    set_theme("light")
    root.update_idletasks()

    assert btn._parent_bg == "#ffffff"
    assert inp._parent_bg == "#ffffff"

    set_theme("dark")
    inp.destroy()
    btn.destroy()
    subframe.destroy()
    card.destroy()


def test_theme_manager_priority_listeners():
    from tkblend.theme import ThemeManager
    tm = ThemeManager()
    events = []

    def priority_cb(pal):
        events.append("priority")

    def standard_cb(pal):
        events.append("standard")

    tm.add_priority_listener(priority_cb)
    tm.add_listener(standard_cb)

    set_theme("light")
    assert events == ["priority", "standard"]

    set_theme("dark")
    assert events == ["priority", "standard", "priority", "standard"]

    tm.remove_priority_listener(priority_cb)
    tm.remove_listener(standard_cb)


def test_resolve_ancestor_bg_previous_palette_translation(root):
    # Setup standard Tk frame with dark bg
    set_theme("dark")
    f = tk.Frame(root, bg=DARK_PALETTE.bg)
    assert resolve_ancestor_bg(f) == DARK_PALETTE.bg

    # Switch theme to light: even before f is reconfigured, resolve_ancestor_bg should translate
    set_theme("light")
    assert resolve_ancestor_bg(f) == LIGHT_PALETTE.bg

    # Card background translation
    f_card = tk.Frame(root, bg=LIGHT_PALETTE.card_bg)
    set_theme("dark")
    assert resolve_ancestor_bg(f_card) == DARK_PALETTE.card_bg

    f.destroy()
    f_card.destroy()


def test_apply_theme_context_aware_card_and_accordion(root):
    from tkblend.widgets.containers import Accordion
    set_theme("dark")

    # Hierarchy: root -> card -> inner_frame -> acc -> acc_inner_label
    card = Card(root, title="Card")
    inner_frame = tk.Frame(card)
    inner_frame.pack()
    acc = Accordion(inner_frame, title="Acc")
    acc.pack()
    lbl = tk.Label(acc.content_frame, text="Inside Acc")
    lbl.pack()

    cleanup = apply_theme(root, recursive=True)
    root.update_idletasks()

    assert card._bg_label.cget("background") == DARK_PALETTE.bg
    assert card._bg_color == DARK_PALETTE.card_bg
    assert inner_frame.cget("background") == DARK_PALETTE.card_bg
    assert acc._parent_bg == DARK_PALETTE.card_bg
    assert acc.content_frame.cget("background") == DARK_PALETTE.surface
    assert lbl.cget("background") == DARK_PALETTE.surface

    # Switch to light
    set_theme("light")
    root.update_idletasks()

    assert card._bg_label.cget("background") == LIGHT_PALETTE.bg
    assert card._bg_color == LIGHT_PALETTE.card_bg
    assert inner_frame.cget("background") == LIGHT_PALETTE.card_bg
    assert acc._parent_bg == LIGHT_PALETTE.card_bg
    assert acc.content_frame.cget("background") == LIGHT_PALETTE.surface
    assert lbl.cget("background") == LIGHT_PALETTE.surface

    cleanup()
    set_theme("dark")
    card.destroy()

