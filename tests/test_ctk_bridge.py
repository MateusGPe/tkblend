"""
Unit and integration tests for tkblend.ctk Blend2D vector rendering bridge for CustomTkinter.
"""

import pytest
import tkinter as tk
import customtkinter
import tkblend.ctk as ctk
from tkblend.ctk.draw_engine import TkBlendDrawEngine
from tkblend.ctk.canvas import TkBlendCanvas
from tkblend.ctk.patcher import patch, unpatch, is_patched


@pytest.fixture(autouse=True)
def ensure_patched_and_cleanup():
    patch()
    yield
    # Keep patched for other tests or cleanup if needed


def test_patch_and_unpatch_lifecycle():
    assert is_patched()
    assert customtkinter.windows.widgets.core_rendering.DrawEngine is TkBlendDrawEngine
    assert customtkinter.windows.widgets.core_rendering.CTkCanvas is TkBlendCanvas

    unpatch()
    assert not is_patched()
    assert customtkinter.windows.widgets.core_rendering.DrawEngine is not TkBlendDrawEngine

    patch()
    assert is_patched()
    assert customtkinter.windows.widgets.core_rendering.DrawEngine is TkBlendDrawEngine


def test_ctk_button_surface_rendering():
    root = tk.Tk()
    root.withdraw()
    try:
        btn = ctk.CTkButton(
            root,
            text="Blend2D Button",
            corner_radius=12,
            border_width=2,
            fg_color="#3b82f6",
            border_color="#1d4ed8",
            hover_color="#2563eb",
            width=140,
            height=40,
        )
        btn.pack()
        root.update()

        canvas = btn._canvas
        assert isinstance(canvas, TkBlendCanvas)
        assert hasattr(canvas, "_blend_engine")
        assert canvas._blend_engine is not None
        assert isinstance(canvas._blend_engine, TkBlendDrawEngine)

        # Check surface dimensions
        engine = canvas._blend_engine
        assert engine._surface is not None
        assert engine._surface.width >= 140
        assert engine._surface.height >= 40
        assert engine._photo is not None

        # Test hover / color change
        btn._on_enter()
        root.update()
        assert engine.get_color("inner_parts") is not None
    finally:
        root.destroy()


def test_ctk_slider_surface_rendering():
    root = tk.Tk()
    root.withdraw()
    try:
        slider = ctk.CTkSlider(
            root,
            from_=0,
            to=100,
            width=200,
            height=20,
            progress_color="#10b981",
            button_color="#34d399",
            button_hover_color="#059669",
        )
        slider.set(50)
        slider.pack()
        root.update()

        engine = slider._canvas._blend_engine
        assert engine._shape_type == "slider"
        assert engine._surface is not None
        assert engine._surface.width >= 200

        # Change value and re-render
        slider.set(75)
        root.update()
        assert engine._params["slider_value"] == pytest.approx(0.75, abs=0.01)
    finally:
        root.destroy()


def test_ctk_progressbar_surface_rendering():
    root = tk.Tk()
    root.withdraw()
    try:
        pbar = ctk.CTkProgressBar(
            root,
            width=220,
            height=16,
            corner_radius=8,
            progress_color="#8b5cf6",
        )
        pbar.set(0.65)
        pbar.pack()
        root.update()

        engine = pbar._canvas._blend_engine
        assert engine._shape_type == "progress_bar"
        assert engine._surface is not None
        assert engine._surface.width >= 220
        assert engine._params["progress_value_2"] == pytest.approx(0.65, abs=0.01)
    finally:
        root.destroy()


def test_ctk_checkbox_and_switch_rendering():
    root = tk.Tk()
    root.withdraw()
    try:
        chk = ctk.CTkCheckbox(
            root,
            text="Enable Feature",
            checkmark_color="#ffffff",
            fg_color="#3b82f6",
        )
        chk.select()
        chk.pack()

        sw = ctk.CTkSwitch(
            root,
            text="Dark Mode",
            progress_color="#6366f1",
        )
        sw.select()
        sw.pack()
        root.update()

        chk_engine = chk._canvas._blend_engine
        assert chk_engine.is_tag_active("checkmark")
        assert chk_engine._params.get("checkmark_active") is True

        sw_engine = sw._canvas._blend_engine
        assert sw_engine._shape_type == "slider"
    finally:
        root.destroy()


def test_ctk_optionmenu_and_combobox():
    root = tk.Tk()
    root.withdraw()
    try:
        opt = ctk.CTkOptionMenu(
            root,
            values=["Alpha", "Beta", "Gamma"],
            fg_color="#1e293b",
            button_color="#334155",
        )
        opt.pack()
        root.update()

        engine = opt._canvas._blend_engine
        assert engine._shape_type == "vertical_split"
        assert engine.is_tag_active("dropdown_arrow")
    finally:
        root.destroy()


def test_ctk_frame_and_label():
    root = tk.Tk()
    root.withdraw()
    try:
        frame = ctk.CTkFrame(root, width=300, height=200, corner_radius=16, border_width=1)
        frame.pack()
        lbl = ctk.CTkLabel(frame, text="Hello Blend2D CTk", corner_radius=6)
        lbl.pack(padx=10, pady=10)
        root.update()

        f_engine = frame._canvas._blend_engine
        assert f_engine._shape_type == "rounded_rect"
        assert f_engine._surface is not None
    finally:
        root.destroy()


def test_ctk_scrollbar():
    root = tk.Tk()
    root.withdraw()
    try:
        sb = ctk.CTkScrollbar(root, orientation="vertical")
        sb.set(0.2, 0.6)
        sb.pack()
        root.update()

        engine = sb._canvas._blend_engine
        assert engine._shape_type == "scrollbar"
        assert engine._params["start_value"] == pytest.approx(0.2, abs=0.01)
        assert engine._params["end_value"] == pytest.approx(0.6, abs=0.01)
    finally:
        root.destroy()


def test_ctk_segmented_button():
    root = tk.Tk()
    root.withdraw()
    try:
        seg = ctk.CTkSegmentedButton(root, values=["A", "B", "C"])
        seg.set("B")
        seg.pack()
        root.update()

        for btn in seg._buttons_dict.values():
            engine = btn._canvas._blend_engine
            assert isinstance(engine, TkBlendDrawEngine)
            assert engine._surface is not None
    finally:
        root.destroy()


def test_ctk_entry():
    root = tk.Tk()
    root.withdraw()
    try:
        entry = ctk.CTkEntry(root, placeholder_text="Type...")
        entry.pack()
        root.update()

        engine = entry._canvas._blend_engine
        assert engine._shape_type == "rounded_rect"
        assert engine._surface is not None
    finally:
        root.destroy()


def test_ctk_radiobutton():
    root = tk.Tk()
    root.withdraw()
    try:
        rb = ctk.CTkRadioButton(root, text="Choice 1")
        rb.select()
        rb.pack()
        root.update()

        engine = rb._canvas._blend_engine
        assert engine._shape_type == "rounded_rect"
        assert engine._surface is not None
    finally:
        root.destroy()


def test_ctk_indeterminate_progressbar():
    root = tk.Tk()
    root.withdraw()
    try:
        pbar = ctk.CTkProgressBar(root, mode="indeterminate")
        pbar.start()
        pbar.step()
        pbar.pack()
        root.update()

        engine = pbar._canvas._blend_engine
        assert engine._shape_type == "progress_bar"
        assert engine._surface is not None
    finally:
        root.destroy()


def test_nested_frame_background_resolution():
    root = tk.Tk()
    root.withdraw()
    try:
        outer = ctk.CTkFrame(root, fg_color="#1a1a1a")
        outer.pack()
        inner = ctk.CTkFrame(outer, fg_color="#2b2b2b")
        inner.pack()
        btn = ctk.CTkButton(inner, text="Nested")
        btn.pack()
        root.update()

        engine = btn._canvas._blend_engine
        bg = engine._resolve_bg_color()
        assert bg == "#2b2b2b"
    finally:
        root.destroy()

