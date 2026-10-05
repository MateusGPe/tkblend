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
from tkblend import BlendDecorator


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
    assert c.lower() in ("#7f7f7f", "#808080")
    assert blend_color_hex("#000000", "#ffffff", 0.0) == "#000000"
    assert blend_color_hex("#000000", "#ffffff", 1.0) == "#ffffff"

    # adjust_brightness
    darker = adjust_brightness("#ffffff", 0.5)
    assert darker.lower() in ("#7f7f7f", "#808080")


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

    # Inside a BlendDecorator card container
    card = BlendDecorator(root, bg_color="#332244")
    assert resolve_ancestor_bg(card) == "#332244"

    # Inside a tk.Frame that is inside the BlendDecorator
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
    dec = BlendDecorator(root)

    cleanup = apply_theme(root, "dark")
    root.update_idletasks()

    assert f.cget("background") == DARK_PALETTE.bg
    assert lbl.cget("background") == DARK_PALETTE.bg
    assert cvs.cget("background") == DARK_PALETTE.bg

    # Switch theme to light and verify all standard Tk and tkblend widgets auto-sync
    set_theme("light")
    root.update_idletasks()

    assert f.cget("background") == LIGHT_PALETTE.bg
    assert lbl.cget("background") == LIGHT_PALETTE.bg
    assert cvs.cget("background") == LIGHT_PALETTE.bg

    # Cleanup listener
    cleanup()

    # Reset back to dark
    set_theme("dark")
    f.destroy()
    lbl.destroy()
    cvs.destroy()
    dec.destroy()


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
    card = BlendDecorator(root, bg_color="#112233")
    subframe = tk.Frame(card)
    lbl = tk.Label(subframe, text="Inside Decorator")

    root.update_idletasks()
    assert resolve_ancestor_bg(subframe) == "#112233"
    assert resolve_ancestor_bg(lbl) == "#112233"

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


def test_to_tk_hex():
    from tkblend.theme import to_tk_hex, to_tk_color
    assert to_tk_hex("#ff007f88") == "#ff007f"
    assert to_tk_hex("#aabbcc") == "#aabbcc"
    assert to_tk_hex("#fff") == "#ffffff"
    assert to_tk_hex("#ffff") == "#ffffff"
    assert to_tk_hex("rgba(255, 0, 127, 0.5)") == "#ff007f"
    assert to_tk_hex("rgb(10, 20, 30)") == "#0a141e"
    assert to_tk_color("#12345678") == "#123456"


def test_cascade_bg_preserves_card_hierarchy_and_contrast(root):
    from tkblend.widgets.card import Card
    from tkblend.theme import cascade_bg_to_children, get_theme, to_tk_hex, get_contrast_color
    set_theme("dark")
    pal = get_theme()

    card = Card(root, width=300, height=200)
    frame = tk.Frame(card)
    lbl_title = tk.Label(frame, text="Header Title", font=("sans-serif", 12, "bold"))
    lbl_desc = tk.Label(frame, text="Description", font=("sans-serif", 9))

    cascade_bg_to_children(card, card.bg_color, palette=pal)
    root.update_idletasks()

    # Verify frame and labels inherit card_bg and have high contrast
    assert frame.cget("background").lower() == to_tk_hex(pal.card_bg).lower()
    assert lbl_title.cget("background").lower() == to_tk_hex(pal.card_bg).lower()
    # Foreground must have high contrast against card_bg
    assert get_contrast_color(lbl_title.cget("background")) != get_contrast_color(lbl_title.cget("foreground"))

    # Switch theme to light and verify cascade
    set_theme("light")
    new_pal = get_theme()
    cascade_bg_to_children(card, card.bg_color, palette=new_pal)
    root.update_idletasks()

    assert frame.cget("background").lower() == to_tk_hex(new_pal.card_bg).lower()
    assert lbl_title.cget("background").lower() == to_tk_hex(new_pal.card_bg).lower()
    assert lbl_title.cget("foreground").lower() == to_tk_hex(new_pal.fg).lower()
    assert get_contrast_color(lbl_title.cget("background")) != get_contrast_color(lbl_title.cget("foreground"))

    card.destroy()


def test_combobox_syncs_with_global_theme(root):
    from tkblend.widgets.combobox import OptionMenu
    from tkblend.theme import get_available_themes, set_theme, get_theme

    set_theme("dark")
    themes = get_available_themes()
    assert "light" in themes
    assert "dark" in themes

    opt = OptionMenu(root, values=themes, default_value="dark")
    assert opt.get() == "dark"

    # Global theme switch
    set_theme("light")
    root.update_idletasks()
    assert opt.get() == "light"

    set_theme("cyberpunk")
    root.update_idletasks()
    assert opt.get() == "cyberpunk"

    # Reset
    set_theme("dark")
    opt.destroy()


def test_contrast_across_all_registered_presets():
    from tkblend.theme import THEME_PRESETS, get_contrast_color, set_theme, get_theme
    for name, pal in THEME_PRESETS.items():
        set_theme(name)
        active = get_theme()
        # Ensure card_bg and bg have high contrast text
        fg_card = get_contrast_color(active.card_bg)
        fg_bg = get_contrast_color(active.bg)
        fg_primary = get_contrast_color(active.primary)

        assert fg_card in ("#ffffff", "#0f172a")
        assert fg_bg in ("#ffffff", "#0f172a")
        assert fg_primary in ("#ffffff", "#0f172a")

    set_theme("dark")


