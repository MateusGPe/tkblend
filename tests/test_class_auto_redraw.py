import tkinter as tk
import pytest
from tkblend.decorator import BlendDecorator
from tkblend.controller import NativeController
from tkblend._tkblend import StyleEngine, Color, PseudoState
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


def test_decorator_class_management(root):
    set_theme("dark")
    dec = BlendDecorator(root, width=200, height=50)

    # Initial state
    assert dec.classes == []
    assert dec.class_name == ""
    assert not dec.has_class("active")

    # Add class
    dec.add_class("btn-primary")
    assert dec.has_class("btn-primary")
    assert "btn-primary" in dec.classes
    assert dec.class_name == "btn-primary"

    # Add multiple classes
    dec.add_class("elevated")
    assert dec.classes == ["btn-primary", "elevated"]
    assert dec.class_name == "btn-primary elevated"

    # Toggle class
    dec.toggle_class("elevated")
    assert not dec.has_class("elevated")
    assert dec.classes == ["btn-primary"]

    dec.toggle_class("elevated")
    assert dec.has_class("elevated")

    # Remove class
    dec.remove_class("btn-primary")
    assert not dec.has_class("btn-primary")
    assert dec.classes == ["elevated"]

    # Assign class_name directly
    dec.class_name = "card warning pulse"
    assert dec.classes == ["card", "warning", "pulse"]
    assert dec.has_class("warning")


def test_decorator_local_variables(root):
    set_theme("dark")
    dec = BlendDecorator(root, width=200, height=50)

    # Set local scoped variable
    dec.set_var("--local-widget-radius", "24.0")
    dec.set_var("--custom-accent", "#00ffcc")

    assert dec.get_var("--local-widget-radius") == "24.0"
    assert dec.get_var("--custom-accent") == "#00ffcc"
    assert dec.vars["--local-widget-radius"] == "24.0"

    # Remove var
    dec.remove_var("--local-widget-radius")
    assert dec.get_var("--local-widget-radius") == ""

    # Clear vars
    dec.clear_vars()
    assert dec.vars == {}

    # Hierarchical fallback test (local widget vars > global theme vars)
    StyleEngine.set_variable("--test-hierarchy-var", "global-val", "dark")
    assert dec.get_var("--test-hierarchy-var") == "global-val"
    dec.set_var("--test-hierarchy-var", "local-override")
    assert dec.get_var("--test-hierarchy-var") == "local-override"
    dec.remove_var("--test-hierarchy-var")
    assert dec.get_var("--test-hierarchy-var") == "global-val"


def test_decorator_child_sync_on_class_change(root):
    css = """
    .btn-alert {
        background: #990000;
        color: #ffffff;
    }
    .btn-success {
        background: #008800;
        color: #ffff00;
    }
    """
    StyleEngine.load_stylesheet(css)

    dec = BlendDecorator(root, width=200, height=50)
    entry = tk.Entry(dec)
    dec.decorate(entry)
    root.update_idletasks()

    # Apply class
    dec.add_class("btn-alert")
    root.update_idletasks()
    assert entry.cget("background").lower() == "#990000"
    assert entry.cget("foreground").lower() == "#ffffff"

    # Switch class
    dec.classes = ["btn-success"]
    root.update_idletasks()
    assert entry.cget("background").lower() == "#008800"
    assert entry.cget("foreground").lower() == "#ffff00"


def test_native_controller_class_and_variables(root):
    frame = tk.Frame(root, width=100, height=50)
    frame.pack()
    root.update_idletasks()

    ctrl = NativeController(frame)
    ctrl.add_class("badge-primary")
    assert ctrl.has_class("badge-primary")
    assert ctrl.classes == ["badge-primary"]

    ctrl.set_var("--badge-radius", "10px")
    assert ctrl.get_var("--badge-radius") == "10px"

    ctrl.remove_class("badge-primary")
    assert not ctrl.has_class("badge-primary")
