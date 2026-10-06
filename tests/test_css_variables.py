import pytest
from tkblend._tkblend import StyleEngine, Color, PseudoState
from tkblend.theme import set_theme, get_theme


def test_style_engine_color_variables():
    set_theme("dark")
    # Query default theme color variables
    primary = StyleEngine.resolve_color_var("var(--primary)")
    assert primary.a > 0

    # Custom variable registration
    StyleEngine.set_variable("--brand-accent", "#ff0055", "dark")
    accent = StyleEngine.resolve_color_var("var(--brand-accent)")
    assert accent.r == 255
    assert accent.g == 0
    assert accent.b == 85

    # Fallback when var is missing
    fallback_col = Color(10, 20, 30, 255)
    missing = StyleEngine.resolve_color_var("var(--non-existent-color)", fallback_col)
    assert missing.r == 10 and missing.g == 20 and missing.b == 30


def test_style_engine_scalar_and_curve_variables():
    set_theme("dark")
    # Register numeric/dimension variables
    StyleEngine.set_variable("--curve-size", "18.5", "dark")
    StyleEngine.set_variable("--border-width", "2.5px", "dark")

    val1 = StyleEngine.resolve_scalar("var(--curve-size)")
    assert abs(val1 - 18.5) < 1e-4

    val2 = StyleEngine.resolve_scalar("var(--border-width)")
    assert abs(val2 - 2.5) < 1e-4

    # Fallback
    val_fb = StyleEngine.resolve_scalar("var(--missing-dimension, 12.0)")
    assert abs(val_fb - 12.0) < 1e-4


def test_style_engine_string_variables():
    set_theme("dark")
    StyleEngine.set_variable("--button-label", '"Submit Application"', "dark")
    StyleEngine.set_variable("--font-heading", "Inter", "dark")

    label = StyleEngine.resolve_string("var(--button-label)")
    assert label == "Submit Application"

    font = StyleEngine.resolve_string("var(--font-heading)")
    assert font == "Inter"

    missing = StyleEngine.resolve_string("var(--missing-str)", fallback="Default Title")
    assert missing == "Default Title"


def test_style_engine_compound_class_resolution():
    css = """
    .btn-test {
        background: #123456;
        color: #ffffff;
        border-radius: 8px;
    }
    .elevated {
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4);
    }
    .btn-test:hover {
        background: #234567;
    }
    """
    StyleEngine.load_stylesheet(css)

    # Single class
    cs_norm = StyleEngine.resolve("widget", "btn-test", 0)
    assert cs_norm.border_radius == 8.0
    assert cs_norm.bg_color == Color.from_hex("#123456")

    # Multi-class compound selector
    cs_compound = StyleEngine.resolve("widget", "btn-test elevated", 0)
    assert cs_compound.border_radius == 8.0
    assert cs_compound.shadow_blur == 12.0
    assert cs_compound.shadow_offset_y == 4.0

    # Pseudo-state hover on compound classes
    cs_hover = StyleEngine.resolve("widget", "btn-test elevated", int(PseudoState.Hover))
    assert cs_hover.bg_color == Color.from_hex("#234567")
    assert cs_hover.shadow_blur == 12.0

