"""
Tests for external CSS theme file loading, custom themes, and soft shadow rendering.
"""

import os
import tempfile
from pathlib import Path
import pytest
import tkinter as tk

import tkblend
from tkblend import (
    StyleEngine,
    get_theme,
    set_theme,
    get_available_themes,
    register_theme,
    load_theme_file,
    load_theme_dir,
    THEME_PRESETS,
    Palette,
    BlendDecorator,
    get_contrast_color,
    SLATE_PALETTE,
)


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_builtin_theme_files_loaded():
    """Verify all built-in CSS themes are found and registered."""
    themes = get_available_themes()
    expected = [
        "dark", "light", "dracula", "nord", "tokyo_night",
        "catppuccin_mocha", "catppuccin_latte", "cyberpunk",
        "emerald_forest", "sunset_amber", "monokai_pro",
        "solarized_dark", "solarized_light", "ocean",
        "emerald", "sunset", "monokai",
    ]
    for exp in expected:
        assert exp in themes, f"Expected theme '{exp}' in available themes: {themes}"
        assert exp in THEME_PRESETS, f"Expected theme '{exp}' in THEME_PRESETS"


def test_theme_switching_all_presets():
    """Test that set_theme() smoothly switches across all restored presets."""
    for theme_name in [
        "dracula", "nord", "tokyo_night", "catppuccin_mocha", "catppuccin_latte",
        "cyberpunk", "emerald_forest", "sunset_amber", "monokai_pro",
        "solarized_dark", "solarized_light", "ocean", "emerald", "sunset", "monokai",
        "dark", "light"
    ]:
        set_theme(theme_name)
        pal = get_theme()
        assert pal.name == theme_name
        assert pal.bg.startswith("#")
        assert pal.fg.startswith("#")
        assert pal.primary.startswith("#")


def test_custom_theme_file_loading(tmp_path):
    """Test loading a custom .css theme file from disk."""
    custom_css = """
/* Neon Matrix Theme */
:root {
  --bg: #001100;
  --fg: #00ff66;
  --surface: #002200;
  --surface-border: #004400;
  --card-bg: #003300;
  --card-border: #00ff66;
  --primary: #00ff66;
  --primary-hover: #33ff88;
  --primary-active: #00cc55;
  --primary-fg: #001100;
  --secondary: #004400;
  --secondary-hover: #006600;
  --secondary-active: #002200;
  --secondary-fg: #00ff66;
  --text-muted: #009944;
  --fg-subtle: #009944;
  --shadow: rgba(0, 255, 102, 0.4);
  --shadow-color: rgba(0, 255, 102, 0.4);
  --accent: #00ffcc;
  --success: #00ff66;
  --warning: #ffff00;
  --destructive: #ff0033;
  --danger: #ff0033;
  --input-bg: #002200;
  --input-border: #00ff66;
  --input-focus: #00ffcc;
  --track-bg: #003300;
  --thumb-color: #00ff66;
}

button {
  background: var(--surface);
  color: var(--fg);
  border: 1px solid var(--card-border);
  border-radius: 6px;
  box-shadow: 0 2px 8px var(--shadow);
}
"""
    theme_file = tmp_path / "neon_matrix.css"
    theme_file.write_text(custom_css, encoding="utf-8")

    name = load_theme_file(theme_file)
    assert name == "neon_matrix"
    assert "neon_matrix" in get_available_themes()

    set_theme("neon_matrix")
    pal = get_theme()
    assert pal.name == "neon_matrix"
    assert pal.bg == "#001100"
    assert pal.fg == "#00ff66"
    assert pal.primary == "#00ff66"


def test_custom_theme_dir_loading(tmp_path):
    """Test loading multiple themes from a directory."""
    theme1 = tmp_path / "theme_alpha.css"
    theme1.write_text(":root { --bg: #111111; --fg: #ffffff; --primary: #ff0000; }", encoding="utf-8")
    theme2 = tmp_path / "theme_beta.css"
    theme2.write_text(":root { --bg: #222222; --fg: #eeeeee; --primary: #00ff00; }", encoding="utf-8")

    loaded = load_theme_dir(tmp_path)
    assert "theme_alpha" in loaded
    assert "theme_beta" in loaded

    set_theme("theme_alpha")
    assert get_theme().bg == "#111111"
    set_theme("theme_beta")
    assert get_theme().bg == "#222222"


def test_soft_shadow_rendering(tk_root):
    """Verify BlendDecorator renders with soft Gaussian elevation shadows without clipping."""
    set_theme("dark")
    card = BlendDecorator(tk_root, width=300, height=200, shadow_blur=12.0, shadow_enabled=True)
    card.update_idletasks()
    assert card.winfo_reqwidth() > 0
    assert card.winfo_reqheight() > 0
    card.destroy()


def test_theme_aliases_and_slate():
    """Verify theme aliases (forest, neon) and slate theme work properly."""
    set_theme("forest")
    assert get_theme().bg == THEME_PRESETS["emerald_forest"].bg

    set_theme("neon")
    assert get_theme().bg == THEME_PRESETS["cyberpunk"].bg

    set_theme("slate")
    assert get_theme().bg == "#0f172a"
    assert get_theme().primary == "#38bdf8"
    assert "slate" in THEME_PRESETS


def test_get_contrast_color():
    """Verify get_contrast_color returns white on dark/saturated colors and dark on light colors."""
    assert get_contrast_color("#000000") == "#ffffff"
    assert get_contrast_color("#100e14") == "#ffffff"
    assert get_contrast_color("#10b981") == "#ffffff"  # Emerald green
    assert get_contrast_color("#ef4444") == "#ffffff"  # Red
    assert get_contrast_color("#8b5cf6") == "#ffffff"  # Vivid purple
    assert get_contrast_color("#ffffff") == "#0f172a"  # White
    assert get_contrast_color("#f8f9fa") == "#0f172a"  # Light gray
    assert get_contrast_color("#fbbf24") == "#0f172a"  # Amber/yellow

