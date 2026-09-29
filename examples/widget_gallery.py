#!/usr/bin/env python3
"""
tkblend Showcase: Comprehensive Zero-TTK Vector Widget Gallery & Playground.
Demonstrates:
  - Full catalog of all 20+ pure Blend2D vector widgets
  - Dynamic interactive property tweaking (corner radius, elevation, borders, disabled states)
  - Seamless runtime palette switching across 13+ themes
  - Clean nested container architecture and zero-copy rendering
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, List, Dict, Any

import tkblend as tb
from tkblend import (
    Button,
    Card,
    Frame,
    Entry,
    TextInput,
    Spinbox,
    SpinBox,
    Combobox,
    ComboBox,
    OptionMenu,
    Dropdown,
    Checkbox,
    Checkbutton,
    Radio,
    Radiobutton,
    RadioGroup,
    Switch,
    ToggleSwitch,
    SegmentedButton,
    SegmentedControl,
    Slider,
    Scale,
    RangeSlider,
    ProgressBar,
    CircularProgress,
    Badge,
    Avatar,
    Label,
    IconLabel,
    VectorIcon,
    VectorImage,
    Accordion,
    ScrollableFrame,
    Tabview,
    Table,
    TextBox,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    ScalingTracker,
)


class WidgetGallery(tk.Frame):
    """Complete visual catalog and interactive playground for all tkblend vector widgets."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._disabled_state = False
        self._build_ui()

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Header Bar
        hdr = tk.Frame(self, background=pal.bg)
        hdr.pack(fill="x", padx=20, pady=(16, 10))

        tbox = tk.Frame(hdr, background=pal.bg)
        tbox.pack(side="left")

        tk.Label(tbox, text="tkblend Widget Catalog & Playground", font=("Segoe UI", 18, "bold"), fg=pal.fg, bg=pal.bg).pack(anchor="w")
        tk.Label(tbox, text="Explore, interact with, and test all 20+ pure Blend2D vector widgets", font=("Segoe UI", 10), fg=pal.fg_subtle, bg=pal.bg).pack(anchor="w")

        cbox = tk.Frame(hdr, background=pal.bg)
        cbox.pack(side="right")

        tk.Label(cbox, text="Theme:", font=("Segoe UI", 10), fg=pal.fg_subtle, bg=pal.bg).pack(side="left", padx=(8, 4))
        self._theme_opt = OptionMenu(
            cbox,
            values=list(get_available_themes()),
            default_value="dark",
            command=self._on_theme_changed,
            width=140,
            height=32,
        )
        self._theme_opt.pack(side="left", padx=6)

        # Main Layout: Left Tabs + Right Live Inspector
        main_box = tk.Frame(self, background=pal.bg)
        main_box.pack(fill="both", expand=True, padx=20, pady=(4, 16))

        # Left: Main Tabview
        self._tabview = Tabview(main_box, width=640, height=560, rx=14, ry=14, elevation=6)
        self._tabview.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self._setup_buttons_tab()
        self._setup_inputs_tab()
        self._setup_sliders_tab()
        self._setup_indicators_tab()
        self._setup_containers_tab()
        self._setup_table_tab()

        # Right: Interactive Inspector Card
        insp_card = Card(main_box, title="Live Widget Inspector", width=280, height=560, rx=14, ry=14, elevation=6)
        insp_card.pack(side="right", fill="y", padx=(6, 0))
        self._setup_inspector(insp_card.body)

        cascade_bg_to_children(self, pal.bg)

    def _setup_buttons_tab(self) -> None:
        tab = self._tabview.add("Buttons & Badges")
        body = tab.body
        pal = get_theme()

        scr = ScrollableFrame(body, width=580, height=480)
        scr.pack(fill="both", expand=True, padx=4, pady=4)
        c = scr.content

        # Button Variants Card
        b_card = Card(c, title="Modern Button Styles", width=560, height=130, elevation=4)
        b_card.pack(fill="x", pady=6)
        b_body = b_card.body

        row1 = tk.Frame(b_body, background=b_card.bg_color)
        row1.pack(fill="x", padx=12, pady=8)

        btn_primary = Button(row1, text="Primary Button", width=125, height=32, bootstyle="primary")
        btn_primary.pack(side="left", padx=4)

        btn_sec = Button(row1, text="Secondary", width=110, height=32, bootstyle="secondary")
        btn_sec.pack(side="left", padx=4)

        btn_succ = Button(row1, text="Success", width=100, height=32, bootstyle="success")
        btn_succ.pack(side="left", padx=4)

        btn_dang = Button(row1, text="Danger", width=100, height=32, bootstyle="danger")
        btn_dang.pack(side="left", padx=4)

        btn_out = Button(row1, text="Outline", width=100, height=32, bootstyle="outline-primary")
        btn_out.pack(side="left", padx=4)

        # Badges Card
        bdg_card = Card(c, title="Status Badges & Chips", width=560, height=100, elevation=4)
        bdg_card.pack(fill="x", pady=6)
        bdg_body = bdg_card.body

        row2 = tk.Frame(bdg_body, background=bdg_card.bg_color)
        row2.pack(fill="x", padx=12, pady=8)

        Badge(row2, text="ACTIVE", color=pal.success, height=22).pack(side="left", padx=6)
        Badge(row2, text="PENDING", color=pal.warning, text_color="#000000", height=22).pack(side="left", padx=6)
        Badge(row2, text="ERROR", color=pal.danger, height=22).pack(side="left", padx=6)
        Badge(row2, text="PRO FEATURE", color=pal.accent, height=22).pack(side="left", padx=6)
        Badge(row2, text="v0.3.0", color=pal.surface_border, text_color=pal.fg, height=22).pack(side="left", padx=6)

        # Avatars Card
        av_card = Card(c, title="Vector Avatars & Profiles", width=560, height=110, elevation=4)
        av_card.pack(fill="x", pady=6)
        av_body = av_card.body

        row3 = tk.Frame(av_body, background=av_card.bg_color)
        row3.pack(fill="x", padx=12, pady=8)

        Avatar(row3, text="MG", size=44, bg_color=pal.primary).pack(side="left", padx=8)
        Avatar(row3, text="AI", size=44, bg_color=pal.accent).pack(side="left", padx=8)
        Avatar(row3, text="TK", size=44, bg_color=pal.secondary).pack(side="left", padx=8)
        Avatar(row3, text="BL", size=44, bg_color=pal.success).pack(side="left", padx=8)

    def _setup_inputs_tab(self) -> None:
        tab = self._tabview.add("Inputs & Forms")
        body = tab.body
        pal = get_theme()

        scr = ScrollableFrame(body, width=580, height=480)
        scr.pack(fill="both", expand=True, padx=4, pady=4)
        c = scr.content

        # Text Inputs Card
        in_card = Card(c, title="Text Fields & Entry", width=560, height=130, elevation=4)
        in_card.pack(fill="x", pady=6)
        in_body = in_card.body

        i_row = tk.Frame(in_body, background=in_card.bg_color)
        i_row.pack(fill="x", padx=12, pady=6)

        tk.Label(i_row, text="Standard Entry:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=in_card.bg_color).pack(anchor="w")
        e1 = Entry(i_row, placeholder_text="Enter your email...", width=320, height=32)
        e1.pack(anchor="w", pady=(2, 6))

        # SpinBox & Pickers
        pick_card = Card(c, title="SpinBox, OptionMenu & ComboBox", width=560, height=130, elevation=4)
        pick_card.pack(fill="x", pady=6)
        p_body = pick_card.body

        p_row = tk.Frame(p_body, background=pick_card.bg_color)
        p_row.pack(fill="x", padx=12, pady=8)

        # Spinbox
        sb_col = tk.Frame(p_row, background=pick_card.bg_color)
        sb_col.pack(side="left", padx=8)
        tk.Label(sb_col, text="Spinbox (1-100):", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pick_card.bg_color).pack(anchor="w")
        Spinbox(sb_col, from_=1, to=100, value=25, width=120, height=32).pack(pady=2)

        # OptionMenu
        om_col = tk.Frame(p_row, background=pick_card.bg_color)
        om_col.pack(side="left", padx=8)
        tk.Label(om_col, text="OptionMenu:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pick_card.bg_color).pack(anchor="w")
        OptionMenu(om_col, values=["Production", "Staging", "Development"], default_value="Production", width=140, height=32).pack(pady=2)

        # Combobox
        cb_col = tk.Frame(p_row, background=pick_card.bg_color)
        cb_col.pack(side="left", padx=8)
        tk.Label(cb_col, text="ComboBox:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pick_card.bg_color).pack(anchor="w")
        Combobox(cb_col, values=["Fast (Blend2D)", "GPU Direct", "Hardware Sync"], width=150, height=32).pack(pady=2)

        # Toggles & Radios
        sel_card = Card(c, title="Checkboxes, Radio Buttons & Switches", width=560, height=130, elevation=4)
        sel_card.pack(fill="x", pady=6)
        s_body = sel_card.body

        s_row = tk.Frame(s_body, background=sel_card.bg_color)
        s_row.pack(fill="x", padx=12, pady=6)

        # Checkboxes
        c_col = tk.Frame(s_row, background=sel_card.bg_color)
        c_col.pack(side="left", padx=8)
        Checkbox(c_col, text="Enable Hardware Accel", is_checked=True).pack(anchor="w", pady=2)
        Checkbox(c_col, text="Subpixel Anti-Aliasing", is_checked=True).pack(anchor="w", pady=2)

        # Radios
        r_col = tk.Frame(s_row, background=sel_card.bg_color)
        r_col.pack(side="left", padx=16)
        rg = RadioGroup(r_col, options=["RGB 32-bit", "ARGB Premul", "Grayscale 8-bit"], default_value="RGB 32-bit")
        rg.pack(anchor="w")

        # Switches
        sw_col = tk.Frame(s_row, background=sel_card.bg_color)
        sw_col.pack(side="left", padx=16)
        tk.Label(sw_col, text="Zero-Copy Blit:", font=("Segoe UI", 9), fg=pal.fg, bg=sel_card.bg_color).pack(anchor="w")
        Switch(sw_col, is_on=True, width=44, height=24).pack(anchor="w", pady=2)

    def _setup_sliders_tab(self) -> None:
        tab = self._tabview.add("Selectors & Sliders")
        body = tab.body
        pal = get_theme()

        scr = ScrollableFrame(body, width=580, height=480)
        scr.pack(fill="both", expand=True, padx=4, pady=4)
        c = scr.content

        # Continuous Sliders
        sl_card = Card(c, title="Sliders & Continuous Scales", width=560, height=140, elevation=4)
        sl_card.pack(fill="x", pady=6)
        sl_body = sl_card.body

        sl_box = tk.Frame(sl_body, background=sl_card.bg_color)
        sl_box.pack(fill="x", padx=14, pady=8)

        tk.Label(sl_box, text="Primary Value Slider (0-100):", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=sl_card.bg_color).pack(anchor="w")
        self._live_slider = Slider(sl_box, from_=0, to=100, value=65, width=480, height=24)
        self._live_slider.pack(fill="x", pady=(2, 8))

        # RangeSlider
        rng_card = Card(c, title="Dual-Thumb RangeSlider", width=560, height=110, elevation=4)
        rng_card.pack(fill="x", pady=6)
        rng_body = rng_card.body

        rng_box = tk.Frame(rng_body, background=rng_card.bg_color)
        rng_box.pack(fill="x", padx=14, pady=8)

        tk.Label(rng_box, text="Range Filter (Min / Max):", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=rng_card.bg_color).pack(anchor="w")
        RangeSlider(rng_box, from_=0, to=100, low_value=20, high_value=80, width=480, height=24).pack(fill="x", pady=4)

        # Segmented Buttons
        seg_card = Card(c, title="Segmented Controls & Segmented Buttons", width=560, height=120, elevation=4)
        seg_card.pack(fill="x", pady=6)
        seg_body = seg_card.body

        seg_box = tk.Frame(seg_body, background=seg_card.bg_color)
        seg_box.pack(fill="x", padx=14, pady=8)

        tk.Label(seg_box, text="Segmented Switcher:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=seg_card.bg_color).pack(anchor="w")
        SegmentedButton(seg_box, values=["Daily", "Weekly", "Monthly", "Yearly", "All Time"], default_value="Monthly", width=480, height=32).pack(pady=4)

    def _setup_indicators_tab(self) -> None:
        tab = self._tabview.add("Indicators & Gauges")
        body = tab.body
        pal = get_theme()

        scr = ScrollableFrame(body, width=580, height=480)
        scr.pack(fill="both", expand=True, padx=4, pady=4)
        c = scr.content

        # Circular Progress Gauges
        cg_card = Card(c, title="Blend2D Circular Gauges", width=560, height=150, elevation=4)
        cg_card.pack(fill="x", pady=6)
        cg_body = cg_card.body

        cg_row = tk.Frame(cg_body, background=cg_card.bg_color)
        cg_row.pack(fill="x", padx=16, pady=8)

        for name, val, col in [("Memory", 82, pal.primary), ("Storage", 45, pal.secondary), ("Bandwidth", 90, pal.accent), ("Security", 100, pal.success)]:
            box = tk.Frame(cg_row, background=cg_card.bg_color)
            box.pack(side="left", fill="both", expand=True)
            CircularProgress(box, size=72, stroke_width=7, value=val, color=col).pack(pady=2)
            tk.Label(box, text=f"{name}\n{val}%", font=("Segoe UI", 9, "bold"), fg=pal.fg, bg=cg_card.bg_color).pack()

        # Linear Progress Bars
        pb_card = Card(c, title="Linear Progress Bars", width=560, height=120, elevation=4)
        pb_card.pack(fill="x", pady=6)
        pb_body = pb_card.body

        pb_box = tk.Frame(pb_body, background=pb_card.bg_color)
        pb_box.pack(fill="x", padx=14, pady=8)

        ProgressBar(pb_box, value=75, bootstyle="primary", width=480, height=12).pack(fill="x", pady=4)
        ProgressBar(pb_box, value=40, bootstyle="success", width=480, height=12).pack(fill="x", pady=4)
        ProgressBar(pb_box, value=90, bootstyle="accent", width=480, height=12).pack(fill="x", pady=4)

    def _setup_containers_tab(self) -> None:
        tab = self._tabview.add("Containers")
        body = tab.body
        pal = get_theme()

        scr = ScrollableFrame(body, width=580, height=480)
        scr.pack(fill="both", expand=True, padx=4, pady=4)
        # c = scr.content

        # # Accordion Card
        # acc_card = Card(c, title="Vector Accordion Component", width=560, height=280, elevation=4)
        # acc_card.pack(fill="both", expand=True, pady=6)
        acc_body = scr.content

        acc1 = Accordion(acc_body, title="1. Core Blend2D Architecture", width=520)
        acc1.pack(fill="x", padx=8, pady=3)
        tk.Label(
            acc1.content_frame,
            text="Blend2D is a high-performance 2D vector graphics engine utilizing JIT code generation\nand zero-copy blits directly to Tkinter PhotoImage buffers.",
            font=("Segoe UI", 9),
            fg=pal.fg,
            bg=pal.surface,
            justify="left",
        ).pack(anchor="w", padx=8, pady=4)

        acc2 = Accordion(acc_body, title="2. Zero TTK Theme Dependencies", width=520)
        acc2.pack(fill="x", padx=8, pady=3)
        tk.Label(
            acc2.content_frame,
            text="tkblend eliminates Tcl/Tk TTK theme engine limitations, providing crisp subpixel\nantialiasing, custom drop shadows, gradients, and full High-DPI scaling.",
            font=("Segoe UI", 9),
            fg=pal.fg,
            bg=pal.surface,
            justify="left",
        ).pack(anchor="w", padx=8, pady=4)

        acc3 = Accordion(acc_body, title="3. High-DPI & Dynamic Scaling", width=520)
        acc3.pack(fill="x", padx=8, pady=3)
        tk.Label(
            acc3.content_frame,
            text="All coordinate geometry, fonts, and borders automatically scale through ScalingTracker\nwith process-level DPI awareness.",
            font=("Segoe UI", 9),
            fg=pal.fg,
            bg=pal.surface,
            justify="left",
        ).pack(anchor="w", padx=8, pady=4)

    def _setup_table_tab(self) -> None:
        tab = self._tabview.add("Data Table")
        body = tab.body

        cols = [
            {"id": "id", "name": "ID", "width": 60, "align": "center"},
            {"id": "name", "name": "Package Name", "width": 160, "align": "left"},
            {"id": "version", "name": "Version", "width": 90, "align": "center"},
            {"id": "license", "name": "License", "width": 90, "align": "center"},
            {"id": "status", "name": "Status", "width": 100, "align": "center"},
        ]
        data = [
            {"id": "01", "name": "tkblend", "version": "0.3.0", "license": "BSL 1.1", "status": "Stable"},
            {"id": "02", "name": "blend2d", "version": "0.11.4", "license": "Zlib", "status": "Optimized"},
            {"id": "03", "name": "nanobind", "version": "2.4.0", "license": "BSD-3", "status": "Active"},
            {"id": "04", "name": "tkinter", "version": "8.6.14", "license": "Tcl/Tk", "status": "Builtin"},
            {"id": "05", "name": "python", "version": "3.12.3", "license": "PSF", "status": "Runtime"},
        ]

        tbl = Table(body, columns=cols, data=data, height=380, row_height=32, header_height=34, elevation=4)
        tbl.pack(fill="both", expand=True, padx=8, pady=8)

    def _setup_inspector(self, container: tk.Frame) -> None:
        pal = get_theme()

        p_box = tk.Frame(container, background=pal.card_bg)
        p_box.pack(fill="both", expand=True, padx=12, pady=8)

        # Preview Widget Box
        tk.Label(p_box, text="Live Preview Target:", font=("Segoe UI", 9, "bold"), fg=pal.fg, bg=pal.card_bg).pack(anchor="w")
        self._sample_btn = Button(p_box, text="Interactive Button", width=180, height=36, rx=12, ry=12)
        self._sample_btn.pack(pady=(6, 16))

        # Corner Radius Slider
        tk.Label(p_box, text="Corner Radius (rx/ry):", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w")
        self._rx_slider = Slider(p_box, from_=0, to=30, value=12, width=220, height=22, command=self._update_sample_props)
        self._rx_slider.pack(fill="x", pady=(2, 10))

        # Elevation / Shadow Slider
        tk.Label(p_box, text="Elevation Shadow Blur:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w")
        self._elev_slider = Slider(p_box, from_=0, to=20, value=6, width=220, height=22, command=self._update_sample_props)
        self._elev_slider.pack(fill="x", pady=(2, 10))

        # Disabled State Switch
        dis_row = tk.Frame(p_box, background=pal.card_bg)
        dis_row.pack(fill="x", pady=(6, 12))
        tk.Label(dis_row, text="Disabled State:", font=("Segoe UI", 9), fg=pal.fg, bg=pal.card_bg).pack(side="left")
        self._dis_sw = Switch(dis_row, is_on=False, width=44, height=24, command=self._toggle_disabled)
        self._dis_sw.pack(side="right")

        # Action Buttons
        Button(p_box, text="Randomize Colors", width=220, height=30, bootstyle="secondary", command=self._randomize_sample).pack(pady=4)

    def _update_sample_props(self, _val: Optional[float] = None) -> None:
        rx = float(self._rx_slider.get_value())
        elev = float(self._elev_slider.get_value())
        self._sample_btn.set_corner_radius(rx)
        self._sample_btn._elevation = elev * self._sample_btn._scale
        self._sample_btn.render()

    def _toggle_disabled(self, is_on: bool) -> None:
        self._disabled_state = is_on
        self._sample_btn.set_state("disabled" if is_on else "normal")

    def _randomize_sample(self) -> None:
        pal = get_theme()
        import random
        cols = [pal.primary, pal.secondary, pal.accent, pal.success, pal.danger, pal.warning]
        chosen = random.choice(cols)
        self._sample_btn.set_bg_color(chosen)

    def _on_theme_changed(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg)


def main():
    root = tk.Tk()
    root.title("tkblend Zero-TTK Vector Widget Gallery & Playground")
    root.geometry("1020x720")
    root.minsize(900, 600)

    ScalingTracker.activate_high_dpi_awareness()
    set_theme("dark")

    gallery = WidgetGallery(root)
    gallery.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
