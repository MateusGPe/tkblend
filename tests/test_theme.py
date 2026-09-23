"""
Tests for tkblend.theme: Palette, ThemeManager, dynamic switching, and color utilities.
"""

import pytest
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
    blend_color_hex,
    adjust_brightness,
    is_inside_card,
    is_ttkbootstrap_installed,
)


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
