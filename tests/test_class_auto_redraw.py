import tkinter as tk
import pytest
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


def test_native_controller_class_management(root):
    set_theme("dark")
    frame = tk.Frame(root, width=200, height=50)
    frame.pack()
    root.update_idletasks()
    ctrl = NativeController(frame)

    # Initial state
    assert ctrl.classes == []
    assert ctrl.class_name == ""
    assert not ctrl.has_class("active")

    # Add class
    ctrl.add_class("btn-primary")
    assert ctrl.has_class("btn-primary")
    assert "btn-primary" in ctrl.classes
    assert ctrl.class_name == "btn-primary"

    # Add multiple classes
    ctrl.add_class("elevated")
    assert ctrl.classes == ["btn-primary", "elevated"]
    assert ctrl.class_name == "btn-primary elevated"

    # Toggle class
    ctrl.toggle_class("elevated")
    assert not ctrl.has_class("elevated")
    assert ctrl.classes == ["btn-primary"]

    ctrl.toggle_class("elevated")
    assert ctrl.has_class("elevated")

    # Remove class
    ctrl.remove_class("btn-primary")
    assert not ctrl.has_class("btn-primary")
    assert ctrl.classes == ["elevated"]

    # Assign class_name directly
    ctrl.class_name = "card warning pulse"
    assert ctrl.classes == ["card", "warning", "pulse"]
    assert ctrl.has_class("warning")


def test_native_controller_local_variables(root):
    set_theme("dark")
    frame = tk.Frame(root, width=200, height=50)
    frame.pack()
    root.update_idletasks()
    ctrl = NativeController(frame)

    # Set local scoped variable
    ctrl.set_var("--local-widget-radius", "24.0")
    ctrl.set_var("--custom-accent", "#00ffcc")

    assert ctrl.get_var("--local-widget-radius") == "24.0"
    assert ctrl.get_var("--custom-accent") == "#00ffcc"
    assert ctrl.vars["--local-widget-radius"] == "24.0"

    # Remove var
    ctrl.remove_var("--local-widget-radius")
    assert ctrl.get_var("--local-widget-radius") == ""

    # Clear vars
    ctrl.clear_vars()
    assert ctrl.vars == {}

    # Hierarchical fallback test (local widget vars > global theme vars)
    StyleEngine.set_variable("--test-hierarchy-var", "global-val", "dark")
    assert ctrl.get_var("--test-hierarchy-var") == "global-val"
    ctrl.set_var("--test-hierarchy-var", "local-override")
    assert ctrl.get_var("--test-hierarchy-var") == "local-override"
    ctrl.remove_var("--test-hierarchy-var")
    assert ctrl.get_var("--test-hierarchy-var") == "global-val"
