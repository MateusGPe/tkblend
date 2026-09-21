"""
Comprehensive Tests for Native TTK Theme Engine with Blend2D.
"""

import pytest
import tkinter as tk
from tkinter import ttk
import tkblend


@pytest.fixture
def root():
    try:
        r = tk.Tk()
        r.withdraw()  # Run headless without creating visible desktop window
        yield r
        r.destroy()
    except tk.TclError:
        pytest.skip("Tk display not available in environment")


class TestTtkThemeEngine:
    def test_theme_registration_and_apply(self, root):
        theme_name = tkblend.apply_theme(root, dark_mode=True)
        assert theme_name == "tkblend"
        
        style = ttk.Style(master=root)
        assert style.theme_use() == "tkblend"

    def test_theme_widgets_creation_and_render(self, root):
        tkblend.apply_theme(root, dark_mode=True)

        frame = ttk.Frame(root)
        frame.pack(fill="both", expand=True)

        btn_primary = ttk.Button(frame, text="Primary Action", style="Accent.TButton")
        btn_primary.pack(padx=5, pady=5)

        btn = ttk.Button(frame, text="Click Me", style="TButton")
        btn.pack(padx=5, pady=5)

        entry = ttk.Entry(frame)
        entry.insert(0, "Sample text")
        entry.pack(padx=5, pady=5)

        check_var = tk.BooleanVar(value=True)
        check = ttk.Checkbutton(frame, text="Enable Feature", variable=check_var)
        check.pack(padx=5, pady=5)

        radio_var = tk.StringVar(value="opt1")
        radio1 = ttk.Radiobutton(frame, text="Option 1", value="opt1", variable=radio_var)
        radio2 = ttk.Radiobutton(frame, text="Option 2", value="opt2", variable=radio_var)
        radio1.pack(padx=5, pady=2)
        radio2.pack(padx=5, pady=2)

        # Horizontal and vertical progressbars
        pbar_h = ttk.Progressbar(frame, orient="horizontal", value=65, maximum=100)
        pbar_h.pack(fill="x", padx=5, pady=5)

        pbar_v = ttk.Progressbar(frame, orient="vertical", value=40, maximum=100)
        pbar_v.pack(fill="y", padx=5, pady=5)

        # Horizontal and vertical scrollbars
        scroll_h = ttk.Scrollbar(frame, orient="horizontal")
        scroll_h.pack(fill="x", padx=5, pady=5)

        scroll_v = ttk.Scrollbar(frame, orient="vertical")
        scroll_v.pack(fill="y", padx=5, pady=5)

        btn_destruct = ttk.Button(frame, text="Danger", style="Destructive.TButton")
        btn_destruct.pack(padx=5, pady=5)

        btn_sec = ttk.Button(frame, text="Secondary", style="Secondary.TButton")
        btn_sec.pack(padx=5, pady=5)

        # Scale (Slider)
        scale_h = ttk.Scale(frame, from_=0, to=100, orient="horizontal")
        scale_h.pack(fill="x", padx=5, pady=5)

        # Combobox & Spinbox
        combo = ttk.Combobox(frame, values=["Item 1", "Item 2"])
        combo.current(0)
        combo.pack(padx=5, pady=5)

        spin = ttk.Spinbox(frame, from_=1, to=10)
        spin.set(5)
        spin.pack(padx=5, pady=5)

        # Labelframe and Notebook
        nb = ttk.Notebook(frame)
        nb.pack(fill="both", expand=True, padx=5, pady=5)
        tab1 = ttk.Frame(nb)
        tab2 = ttk.Frame(nb)
        nb.add(tab1, text="Tab 1")
        nb.add(tab2, text="Tab 2")

        lf = ttk.Labelframe(tab1, text="Group 1")
        lf.pack(fill="both", expand=True, padx=5, pady=5)
        ttk.Label(lf, text="Inside Labelframe").pack(padx=5, pady=5)

        # Trigger layout and drawing passes in Tk
        root.update_idletasks()
        root.update()

    def test_widget_state_transitions(self, root):
        tkblend.apply_theme(root, dark_mode=True)

        btn = ttk.Button(root, text="State Button")
        btn.pack()

        # Normal -> Active/Hover -> Pressed -> Disabled -> Focus
        states_to_test = [
            ["active"],
            ["pressed"],
            ["disabled"],
            ["!disabled", "focus"],
            ["!focus"]
        ]

        for s in states_to_test:
            btn.state(s)
            root.update_idletasks()

        entry = ttk.Entry(root)
        entry.pack()
        for s in [["focus"], ["readonly"], ["disabled"], ["!disabled"]]:
            entry.state(s)
            root.update_idletasks()

        check = ttk.Checkbutton(root, text="Check States")
        check.pack()
        for s in [["selected"], ["!selected"], ["active", "selected"], ["disabled"]]:
            check.state(s)
            root.update_idletasks()

        radio = ttk.Radiobutton(root, text="Radio States")
        radio.pack()
        for s in [["selected"], ["!selected"], ["active", "selected"], ["disabled"]]:
            radio.state(s)
            root.update_idletasks()

    def test_theme_mode_switching_and_custom_config(self, root):
        # Switch to Light Mode
        theme = tkblend.apply_theme(
            root,
            dark_mode=False,
            button_radius=10.0,
            entry_radius=8.0,
            enable_shadows=True,
            shadow_blur=4.0
        )
        assert theme == "tkblend"
        
        cfg = tkblend.get_theme_config()
        assert cfg is not None
        assert cfg.dark_mode is False
        assert cfg.button_radius == 10.0
        assert cfg.entry_radius == 8.0

        btn = ttk.Button(root, text="Light Button")
        btn.pack()
        root.update_idletasks()

        # Switch back to Dark Mode
        tkblend.set_dark_mode(True)
        tkblend.apply_theme(root, dark_mode=True)
        cfg_dark = tkblend.get_theme_config()
        assert cfg_dark.dark_mode is True

    def test_zero_dimensions_resilience(self, root):
        tkblend.apply_theme(root, dark_mode=True)

        # Create collapsed zero-size frame containing widgets
        zero_frame = ttk.Frame(root, width=0, height=0)
        zero_frame.pack_propagate(False)
        zero_frame.pack()

        btn = ttk.Button(zero_frame, text="Hidden Button")
        btn.place(x=0, y=0, width=0, height=0)

        entry = ttk.Entry(zero_frame)
        entry.place(x=0, y=0, width=0, height=0)

        pbar = ttk.Progressbar(zero_frame)
        pbar.place(x=0, y=0, width=0, height=0)

        # Should safely abort blit callback without crash or Blend2D error
        root.update_idletasks()
        root.update()

    def test_theme_config_object(self):
        cfg = tkblend.ThemeConfig()
        cfg.button_radius = 12.0
        cfg.entry_radius = 10.0
        cfg.check_radius = 6.0
        cfg.pbar_radius = 8.0
        cfg.scrollbar_radius = 5.0
        cfg.focus_ring_width = 3.0
        cfg.enable_shadows = False
        cfg.shadow_blur = 10.0
        cfg.shadow_spread = 2.0
        cfg.shadow_offset_y = 5.0
        cfg.shadow_color = 0x80000000

        tkblend.set_theme_config(cfg)

        active_cfg = tkblend.get_theme_config()
        assert active_cfg.button_radius == 12.0
        assert active_cfg.entry_radius == 10.0
        assert active_cfg.check_radius == 6.0
        assert active_cfg.pbar_radius == 8.0
        assert active_cfg.scrollbar_radius == 5.0
        assert active_cfg.focus_ring_width == 3.0
        assert active_cfg.enable_shadows is False
        assert active_cfg.shadow_blur == 10.0
        assert active_cfg.shadow_spread == 2.0
        assert active_cfg.shadow_offset_y == 5.0
        assert active_cfg.shadow_color == 0x80000000

        # Factory methods
        dark_cfg = tkblend.ThemeConfig.create_dark()
        assert dark_cfg.dark_mode is True

        light_cfg = tkblend.ThemeConfig.create_light()
        assert light_cfg.dark_mode is False
