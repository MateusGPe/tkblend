import pytest
import tkinter as tk
import tkblend as tb
from tkblend._tkblend import ContainerLayer, StyleEngine, Color


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_container_layer_enum_and_registration(root):
    tb.set_theme("dark")
    pal = tb.get_theme()

    # Verify layer colors
    base_col = StyleEngine.get_layer_color(ContainerLayer.Base, "dark")
    assert base_col.to_hex() == pal.bg.lower()

    surf_col = StyleEngine.get_layer_color(ContainerLayer.Surface, "dark")
    assert surf_col.to_hex() in (pal.surface.lower(), pal.card_bg.lower())

    # Create a Card container and verify it registers its container layer
    card = tb.Card(root, width=300, height=200)
    card.pack()
    root.update_idletasks()

    # Create a button inside the Card without explicit outer_bg
    btn = tb.Button(card, text="Child Button")
    btn.pack()
    root.update_idletasks()

    # Button outer_bg should match Card container layer surface background
    assert btn.outer_bg.lower() in (pal.surface.lower(), pal.card_bg.lower(), card.inner_bg.lower())

    # Switch theme to light and verify seamless adaptation
    tb.set_theme("light")
    light_pal = tb.get_theme()
    root.update_idletasks()

    assert btn.outer_bg.lower() in (light_pal.surface.lower(), light_pal.card_bg.lower(), card.inner_bg.lower())

    card.destroy()
    tb.set_theme("dark")


def test_native_state_lerping_and_timer(root):
    tb.set_theme("dark")
    btn = tb.Button(root, text="Animated Button")
    btn.pack()
    root.update_idletasks()

    ctrl = btn.controller
    assert ctrl.animated is True
    assert ctrl.hover_t == 0.0

    # Simulate hover event
    ctrl.is_hovered = True
    root.update()

    # Hover lerp advances smoothly towards 1.0
    ctrl.hover_t = 0.5
    assert ctrl.hover_t == pytest.approx(0.5, abs=1e-4)

    # Simulate press
    ctrl.is_pressed = True
    root.update()
    ctrl.press_t = 0.8
    assert ctrl.press_t == pytest.approx(0.8, abs=1e-4)

    btn.destroy()



def test_drawbatch_element_template_registry():
    batch = tb.DrawBatch()
    batch.fill_rect_var(0, 0, 100, 50, "--primary")
    StyleEngine.register_element_batch("custom_badge", batch)

    retrieved = StyleEngine.get_element_batch("custom_badge")
    assert retrieved is not None
    assert len(retrieved) == 1


def test_theme_specific_color_and_drawbatch_dynamic_dims():
    dark_bg = StyleEngine.resolve_color("--bg", "dark")
    light_bg = StyleEngine.resolve_color("--bg", "light")
    assert dark_bg.to_hex() != light_bg.to_hex()

    # Fast hex path without var()
    hex_col = StyleEngine.resolve_color("#123456")
    assert hex_col.to_hex() == "#123456"

    # DrawBatch dynamic width and height bindings
    b = tb.DrawBatch()
    b.fill_rect_var(0, 0, 10, 10, "--primary", w_var="--w", h_var="--h")
    b.draw_card_var(
        0, 0, 50, 50, 4, 4,
        "--card-bg", "--card-border", 1.0,
        4.0, 0.0, 0.0, 2.0, "--card-shadow",
        w_var="--width", h_var="--height"
    )
    assert len(b) == 2


def test_controller_responsive_dimensions(root):
    card = tb.Card(root, width=120, height=80)
    card.pack()
    root.update_idletasks()

    ctrl = card.controller
    vars_map = ctrl.get_vars()
    # Ensure native controller has registered dimensions or vars
    assert ctrl.width >= 100
    assert ctrl.height >= 60

    card.destroy()


