import tkinter as tk
import pytest
from tkblend._tkblend import DrawBatch, StyleEngine, Color, Surface as _NativeSurface
from tkblend.surface import Surface
from tkblend.decorator import BlendDecorator
from tkblend.controller import NativeController
from tkblend.widgets.base import BaseControl
from tkblend.theme import set_theme


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_draw_batch_variable_execution_on_surface():
    set_theme("dark")
    surf = Surface(width=100, height=100)

    batch = DrawBatch()
    # Queue operations bound to dynamic variables
    batch.clear_var("var(--bg-color)", fallback=Color(0, 0, 0, 255))
    batch.fill_rounded_rect_var(
        10, 10, 80, 80, 8, 8,
        c_var="var(--card-fill)",
        rx_var="var(--curve-radius)",
        fallback=Color(255, 0, 0, 255)
    )

    # 1. Execute with local_vars
    local_vars = {
        "--bg-color": "#112233",
        "--card-fill": "#445566",
        "--curve-radius": "16.0",
    }
    surf.execute_batch(batch, local_vars=local_vars)
    surf.flush()
    # Successfully rendered without error


def test_decorator_bind_batch_zero_python(root):
    set_theme("dark")
    dec = BlendDecorator(root, width=150, height=60)
    root.update_idletasks()

    # Create C++ DrawBatch
    batch = DrawBatch()
    batch.clear_var("var(--parent-bg)", fallback=Color(0, 0, 0, 0))
    batch.fill_rounded_rect_var(
        5, 5, 140, 50, 12, 12,
        c_var="var(--accent-col)",
        rx_var="var(--card-rx)",
        fallback=Color(0, 128, 255, 255)
    )

    # Bind batch to decorator
    dec.bind_batch(batch)
    assert dec.has_batch

    # Set local variables and redraw
    dec.set_var("--accent-col", "#ff0088")
    dec.set_var("--card-rx", "20.0")
    root.update_idletasks()

    # Clear batch returns to default
    dec.clear_batch()
    assert not dec.has_batch


def test_base_control_batch_binding(root):
    set_theme("dark")
    control = BaseControl(root, width=120, height=40)
    control.pack()
    root.update_idletasks()

    batch = DrawBatch()
    batch.fill_rounded_rect(0, 0, 120, 40, 6, 6, Color(100, 150, 200, 255))

    control.bind_batch(batch)
    assert control.has_batch

    root.update_idletasks()
    control.clear_batch()
    assert not control.has_batch
