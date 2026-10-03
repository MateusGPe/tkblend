"""
Comprehensive tests for BlendDecorator and NativeDecorator subpackage.
Verifies pure surface rendering, passive child event hooks, double-buffered Pixmap presentation,
geometry negotiation without photo images, and theme synchronization.
"""

import pytest
import tkinter as tk
from tkinter import ttk

import tkblend as tb
from tkblend import BlendDecorator
from tkblend._tkblend import NativeDecorator, Color


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


class TestNativeDecorator:
    """Direct tests for C++ NativeDecorator nanobind bindings."""

    def test_native_decorator_lifecycle(self, tk_root):
        interp_addr = tk_root.tk.interpaddr()
        parent_path = tk_root._w
        widget_name = "test_native_dec_1"

        dec = NativeDecorator(interp_addr, parent_path, widget_name, 200, 45)
        assert dec.is_attached
        assert dec.path == f".{widget_name}"
        assert dec.child_path == ""
        assert not dec.is_focused
        assert not dec.is_hovered

        # Insets
        insets = dec.get_insets()
        assert len(insets) == 4
        assert all(x >= 0 for x in insets)

        # Style setters/getters
        dec.set_style(
            bg_color=Color(255, 255, 255, 255),
            border_color=Color(100, 100, 100, 255),
            border_width=2.0,
            rx=12.0,
            ry=12.0,
            shadow_blur=10.0,
            shadow_enabled=True,
            focus_ring_color=Color(0, 120, 215, 255),
            focus_ring_width=3.0,
        )

        assert dec.border_width == 2.0
        assert dec.rx == 12.0
        assert dec.ry == 12.0
        assert dec.shadow_blur == 10.0
        assert dec.shadow_enabled is True
        assert dec.focus_ring_width == 3.0

        # Geometry request
        dec.set_geometry_request(300, 60)
        dec.request_redraw()
        tk_root.update_idletasks()

    def test_native_child_attachment(self, tk_root):
        interp_addr = tk_root.tk.interpaddr()
        parent_path = tk_root._w
        widget_name = "test_native_dec_2"

        dec = NativeDecorator(interp_addr, parent_path, widget_name, 200, 45)
        child = tk.Entry(tk_root)
        child.pack()

        # Attach child
        success = dec.attach_child(child._w)
        assert success is True
        assert dec.child_path == child._w

        # State updates
        dec.set_focused(True)
        assert dec.is_focused is True
        dec.set_hovered(True)
        assert dec.is_hovered is True

        dec.set_focused(False)
        assert dec.is_focused is False

        # Detach
        dec.detach_child()
        assert dec.child_path == ""
        assert not dec.is_focused
        assert not dec.is_hovered

        child.destroy()


class TestBlendDecorator:
    """Tests for Python BlendDecorator facade widget."""

    def test_instantiation_and_properties(self, tk_root):
        dec = BlendDecorator(
            tk_root,
            width=240,
            height=48,
            rx=8.0,
            ry=8.0,
            bg_color="#FFFFFF",
            border_color="#CCCCCC",
            border_width=1.5,
            shadow_blur=6.0,
            shadow_enabled=True,
        )
        assert isinstance(dec, tk.Widget)
        assert dec.native is not None
        assert dec.native.is_attached

        insets = dec.insets
        assert len(insets) == 4
        assert insets[0] > 0 or insets[1] > 0

        assert not dec.is_focused
        assert not dec.is_hovered
        assert dec.child is None

        # Test state setters and redraw
        dec.set_hovered(True)
        assert dec.is_hovered is True
        dec.set_focused(True)
        assert dec.is_focused is True

        dec.redraw()
        dec.request_redraw()

        dec.is_hovered = False
        assert dec.is_hovered is False
        dec.is_focused = False
        assert dec.is_focused is False

        dec.destroy()

    def test_decorate_entry(self, tk_root):
        dec = BlendDecorator(tk_root, width=200, height=40, rx=10)
        dec.pack(padx=20, pady=20)

        entry = tk.Entry(dec)
        decorated_entry = dec.decorate(entry, padding=(10, 6, 10, 6))

        assert decorated_entry is entry
        assert dec.child is entry
        assert dec.native.child_path == entry._w

        # Check that Entry was made borderless
        assert str(entry.cget("relief")) == "flat"
        assert int(entry.cget("bd")) == 0

        tk_root.update_idletasks()
        tk_root.update()

        dec.detach()
        assert dec.child is None
        assert dec.native.child_path == ""

        dec.destroy()

    def test_decorate_ttk_widgets(self, tk_root):
        dec = BlendDecorator(tk_root, width=220, height=42)
        dec.grid(row=0, column=0, sticky="nsew")

        combo = ttk.Combobox(dec, values=["Option 1", "Option 2"])
        dec.decorate(combo, padding=8)

        assert dec.child is combo
        assert dec.native.child_path == combo._w

        tk_root.update_idletasks()
        dec.destroy()

    def test_configure_styles(self, tk_root):
        dec = BlendDecorator(tk_root, width=180, height=36)
        dec.pack()

        dec.configure(
            bg_color="#F8F9FA",
            hover_bg_color="#FFFFFF",
            focus_bg_color="#FFFFFF",
            border_color="#007ACC",
            border_focus_color="#005A9E",
            border_width=2.0,
            radius=14.0,
            shadow_color="#10000000",
            shadow_blur=12.0,
            shadow_offset_y=4.0,
            focus_ring_color="#0078D4",
            focus_ring_width=2.5,
            width=250,
            height=50,
        )

        assert dec.native.border_width == 2.0
        assert dec.native.rx == 14.0
        assert dec.native.ry == 14.0
        assert dec.native.shadow_blur == 12.0
        assert dec.native.shadow_offset_y == 4.0
        assert dec.native.focus_ring_width == 2.5

        tk_root.update_idletasks()
        dec.destroy()

    def test_theme_synchronization(self, tk_root):
        tb.set_theme("dark")
        dec = BlendDecorator(tk_root, width=200, height=45)
        dec.pack()
        tk_root.update_idletasks()

        # Switch theme
        tb.set_theme("light")
        tk_root.update_idletasks()

        tb.set_theme("dark")
        tk_root.update_idletasks()

        dec.destroy()

    def test_geometry_resiliency_and_resizing(self, tk_root):
        frame = tk.Frame(tk_root, width=400, height=300)
        frame.pack(fill="both", expand=True)

        dec = BlendDecorator(frame, width=200, height=45)
        dec.pack(fill="x", expand=True, padx=10, pady=10)

        entry = tk.Entry(dec)
        dec.decorate(entry, padding=(12, 8, 12, 8))

        tk_root.update_idletasks()
        tk_root.update()

        # Simulate parent resizing
        frame.configure(width=600, height=400)
        tk_root.update_idletasks()
        tk_root.update()

        # Ensure no exceptions and child is still placed
        assert dec.child is entry
        dec.destroy()

    def test_no_photoimage_used(self, tk_root):
        """Verify that BlendDecorator and NativeDecorator do NOT instantiate tk.PhotoImage."""
        # Record initial photo images
        initial_photos = list(tk_root.tk.call("image", "names"))

        dec = BlendDecorator(tk_root, width=200, height=45)
        dec.pack()
        entry = tk.Entry(dec)
        dec.decorate(entry)

        tk_root.update_idletasks()
        tk_root.update()

        photos_after = list(tk_root.tk.call("image", "names"))
        assert initial_photos == photos_after, "BlendDecorator must not create any tk.PhotoImage instances"

        dec.destroy()

    def test_child_window_shaping_and_clipping(self, tk_root):
        """Test clip_child, child_rx, child_ry properties and OS-level window shaping."""
        dec = BlendDecorator(
            tk_root,
            width=260,
            height=60,
            rx=16.0,
            ry=16.0,
            clip_child=True,
        )
        dec.pack()

        assert dec.clip_child is True
        assert dec.child_rx is None
        assert dec.child_ry is None

        # Decorate a frame/canvas container
        inner_frame = tk.Frame(dec, bg="#3b82f6")
        dec.decorate(inner_frame, padding=(0, 0, 0, 0))

        tk_root.update_idletasks()
        tk_root.update()

        # Update custom child radius
        dec.child_rx = 14.0
        dec.child_ry = 14.0
        assert dec.child_rx == 14.0
        assert dec.child_ry == 14.0

        tk_root.update_idletasks()
        tk_root.update()

        # Toggle clipping off and on via configure
        dec.configure(clip_child=False)
        assert dec.clip_child is False

        dec.configure(clip_child=True, child_rx=12.0)
        assert dec.clip_child is True
        assert dec.child_rx == 12.0

        tk_root.update_idletasks()
        tk_root.update()

        # Clean detach and destroy
        dec.detach()
        assert dec.child is None
        dec.destroy()

