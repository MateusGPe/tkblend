import tkinter as tk
import pytest
from tkblend import (
    DrawEngine,
    DrawBatch,
    Color,
    BaseControl,
    set_theme,
    ControllerPseudoState,
)


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_draw_engine_built_in_registrations():
    classes = DrawEngine.get_registered_classes()
    assert "button" in classes
    assert "checkbox" in classes
    assert "radio" in classes
    assert "switch" in classes
    assert "slider" in classes
    assert "progressbar" in classes
    assert "badge" in classes
    assert "card" in classes
    assert "frame" in classes
    assert "label" in classes
    assert "entry" in classes
    assert "textbox_frame" in classes
    assert "table_header" in classes
    assert "table_cell" in classes
    assert "table_row" in classes


def test_draw_engine_batch_lookup_and_fallback():
    # Button has a default batch (mask 0)
    b_default = DrawEngine.get_batch("button", 0)
    assert b_default is not None
    assert len(b_default) > 0

    # Looking up an unregistered state on button should fallback to default batch
    b_hover = DrawEngine.get_batch("button", ControllerPseudoState.Hover)
    assert b_hover is not None

    # Checkbox has both unchecked (0) and checked batches
    b_cb_normal = DrawEngine.get_batch("checkbox", 0)
    b_cb_checked = DrawEngine.get_batch("checkbox", ControllerPseudoState.Checked)
    assert b_cb_normal is not None
    assert b_cb_checked is not None
    assert len(b_cb_normal) > 0
    assert len(b_cb_checked) > 0


def test_draw_engine_custom_registration_and_override():
    custom_batch = DrawBatch()
    custom_batch.clear(Color(255, 0, 128))
    custom_batch.fill_rect(0, 0, 50, 50, Color(0, 255, 0))

    DrawEngine.register_batch("custom_box", 0, custom_batch)
    assert DrawEngine.has_batch("custom_box", 0)

    retrieved = DrawEngine.get_batch("custom_box", 0)
    assert retrieved is not None
    assert len(retrieved) == 2

    # Unregister
    DrawEngine.unregister_batch("custom_box", 0)
    assert not DrawEngine.has_batch("custom_box", 0)


def test_widget_draw_engine_button_auto_draw(root):
    set_theme("dark")
    btn = BaseControl(root, widget_class="button", width=120, height=36)
    btn.add_class("button")
    btn.pack()
    root.update_idletasks()

    assert btn.controller.widget_class == "button"
    assert btn.has_class("button")
    assert btn.has_batch

    # Focus update via C++
    btn.controller.is_focused = True
    assert btn.is_focused
    root.update_idletasks()

    btn.controller.is_focused = False
    assert not btn.is_focused
    root.update_idletasks()


def test_widget_draw_engine_switch_toggle(root):
    set_theme("dark")
    sw = BaseControl(root, widget_class="switch", width=50, height=26)
    sw.add_class("switch")
    sw.pack()
    root.update_idletasks()

    assert sw.controller.widget_class == "switch"
    assert not sw.is_checked

    # Native toggle through on_change
    sw.controller.is_checked = True
    sw.add_class("checked")
    root.update_idletasks()
    assert sw.is_checked
    assert sw.has_class("checked")

    sw.controller.is_checked = False
    sw.remove_class("checked")
    root.update_idletasks()
    assert not sw.is_checked
    assert not sw.has_class("checked")


def test_widget_draw_engine_slider_native_interaction(root):
    set_theme("dark")
    changed_val = []

    class TestSlider(BaseControl):
        def on_change(self, val):
            changed_val.append(val)

    sl = TestSlider(root, widget_class="slider", width=140, height=24)
    sl.add_class("slider")
    sl.pack()
    root.update_idletasks()

    assert sl.controller.widget_class == "slider"
    assert sl.has_batch

    # Simulate native thumb pos change
    sl.on_change(0.75)
    root.update_idletasks()
    assert len(changed_val) == 1
    assert changed_val[-1] == pytest.approx(0.75, rel=1e-2)


def test_widget_draw_engine_checkbox_toggle(root):
    set_theme("dark")
    cb = BaseControl(root, widget_class="checkbox", width=22, height=22)
    cb.add_class("checkbox")
    cb.pack()
    root.update_idletasks()

    assert cb.controller.widget_class == "checkbox"
    assert not cb.is_checked

    cb.is_checked = True
    cb.add_class("checked")
    root.update_idletasks()
    assert cb.is_checked
    assert cb.has_class("checked")
