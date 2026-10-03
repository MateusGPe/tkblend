"""
Comprehensive tests for NativeWidgetController and NativeController.
Verifies native window attachment, dual-mode surface binding, direct Blit presentation,
event/state tracking, and GIL-safe callbacks.
"""

import pytest
import tkinter as tk

import tkblend as tb
from tkblend import NativeController, NativeWidgetController, ControllerPseudoState, NativeBlitCanvas, Color
from tkblend.surface import Surface


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


class TestNativeWidgetController:
    """Direct tests for C++ NativeWidgetController nanobind bindings."""

    def test_lifecycle_and_defaults(self):
        c = NativeWidgetController()
        assert not c.is_attached
        assert c.widget_path == ""
        assert c.width >= 1
        assert c.height >= 1
        assert not c.has_bound_surface
        assert c.bound_surface_id == 0

        # State flags
        assert not c.is_hovered
        assert not c.is_pressed
        assert not c.is_focused
        assert not c.is_disabled
        assert not c.is_checked
        assert c.state == ControllerPseudoState.Normal

        # Internal surface access
        surf = c.surface
        assert surf is not None
        assert surf.width >= 1

    def test_attachment_to_tk_widget(self, tk_root):
        frame = tk.Frame(tk_root, width=150, height=80)
        frame.pack()
        tk_root.update_idletasks()

        c = NativeWidgetController()
        interp_addr = tk_root.tk.interpaddr()
        widget_path = frame._w

        attached = c.attach(interp_addr, widget_path)
        assert attached
        assert c.is_attached
        assert c.widget_path == widget_path

        c.set_geometry_request(200, 100)
        c.detach()
        assert not c.is_attached
        assert c.widget_path == ""

    def test_state_management(self):
        c = NativeWidgetController()
        changes = []
        c.set_on_state_changed(lambda cur, old: changes.append((cur, old)))

        c.is_hovered = True
        assert c.is_hovered
        assert (c.state & ControllerPseudoState.Hover) != 0

        c.is_pressed = True
        assert c.is_pressed
        assert (c.state & ControllerPseudoState.Active) != 0

        c.is_focused = True
        assert c.is_focused
        assert (c.state & ControllerPseudoState.Focused) != 0

        c.is_disabled = True
        assert c.is_disabled
        assert (c.state & ControllerPseudoState.Disabled) != 0

        c.is_checked = True
        assert c.is_checked
        assert (c.state & ControllerPseudoState.Checked) != 0

        assert len(changes) == 5

        c.clear_on_state_changed()
        c.is_hovered = False
        assert not c.is_hovered
        assert len(changes) == 5  # No more callback

    def test_dual_mode_surface_binding(self):
        c = NativeWidgetController()
        assert not c.has_bound_surface

        # Bind external surface
        ext_surf = Surface(80, 40)
        c.bind_surface(ext_surf.native)
        assert c.has_bound_surface

        # Unbind reverts to internal surface
        c.unbind_surface()
        assert not c.has_bound_surface

    def test_on_paint_callback(self, tk_root):
        frame = tk.Frame(tk_root, width=100, height=50)
        frame.pack()
        tk_root.update_idletasks()

        c = NativeWidgetController()
        c.attach(tk_root.tk.interpaddr(), frame._w)

        painted = []
        def _paint(surf):
            painted.append((surf.width, surf.height))
            surf.clear(Color(255, 0, 0, 255))

        c.set_on_paint(_paint)
        c.paint_and_blit()
        assert len(painted) == 1

        c.clear_on_paint()
        c.paint_and_blit()
        assert len(painted) == 1  # Not invoked after clear


class TestNativeController:
    """High-level Python NativeController tests."""

    def test_python_controller_wrapper(self, tk_root):
        frame = tk.Frame(tk_root, width=160, height=90)
        frame.pack()
        tk_root.update_idletasks()

        paint_calls = []
        def on_paint(surface: Surface):
            paint_calls.append(surface)
            surface.clear("blue")
            surface.fill_rounded_rect(5, 5, 50, 40, 4, 4, "white")

        state_calls = []
        def on_state(cur, old):
            state_calls.append((cur, old))

        ctrl = NativeController(
            frame,
            on_paint=on_paint,
            on_state_changed=on_state,
        )

        assert ctrl.is_attached
        assert ctrl.widget is frame
        assert ctrl.surface is not None

        # State manipulation
        ctrl.is_hovered = True
        assert ctrl.is_hovered
        assert len(state_calls) == 1

        ctrl.is_pressed = True
        assert ctrl.is_pressed
        assert len(state_calls) == 2

        # Redraw
        ctrl.paint_and_blit()
        assert len(paint_calls) >= 1

        # Surface binding
        ext = Surface(60, 60)
        ctrl.bind_surface(ext)
        assert ctrl.has_bound_surface
        ctrl.unbind_surface()
        assert not ctrl.has_bound_surface

        ctrl.detach()
        assert not ctrl.is_attached

    def test_native_blit_canvas(self, tk_root):
        drawn = []
        def on_paint(surface: Surface):
            drawn.append(surface.width)
            surface.clear("purple")

        canvas = NativeBlitCanvas(tk_root, width=120, height=80, on_paint=on_paint)
        canvas.pack()
        tk_root.update_idletasks()

        assert canvas.controller.is_attached
        canvas.paint_and_blit()
        assert len(drawn) >= 1
