#!/usr/bin/env python3
"""
Teal & Orange Theme Showcase
Demonstrating the refined borderless, flat, Material UI (M3) modern theme in tkblend.
"""

import tkinter as tk
import tkblend as tb
from tkblend import (
    Button,
    Card,
    Checkbox,
    CircularProgress,
    ComboBox,
    Frame,
    Label,
    Progressbar,
    Radio,
    RangeSlider,
    ScrollableFrame,
    SegmentedButton,
    Slider,
    Sparkline,
    Switch,
    Table,
    TextBox,
)


class TealOrangeDemoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("tkblend — Teal & Orange Modern Flat Theme")
        self.geometry("980x760")
        self.minsize(860, 640)

        # Apply the new teal_orange theme
        tb.set_theme("teal_orange")
        pal = tb.get_theme()
        self.configure(bg=pal.bg)

        self._build_ui()
        tb.cascade_bg_to_children(self, pal.bg)

    def _build_ui(self):
        pal = tb.get_theme()

        # Header Title
        header = tk.Frame(self, bg=pal.bg)
        header.pack(fill="x", padx=28, pady=(20, 10))

        tk.Label(
            header,
            text="Material Flat UI: Teal & Orange",
            font=("sans-serif", 18, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Refined borderless surfaces, tonal layers, smooth rounded radii, and ambient elevation.",
            font=("sans-serif", 10),
            fg=pal.fg_subtle,
            bg=pal.bg,
        ).pack(anchor="w", pady=(2, 0))

        # Main Scrollable Body
        scroller = ScrollableFrame(self, width=920, height=640)
        scroller.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        body = scroller.content

        # 2-Column Responsive Layout
        cols = tk.Frame(body, bg=pal.bg)
        cols.pack(fill="x", expand=True)

        col_left = tk.Frame(cols, bg=pal.bg)
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        col_right = tk.Frame(cols, bg=pal.bg)
        col_right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # ----------------------------------------------------------------------
        # Card 1: Buttons & Actions (Left)
        # ----------------------------------------------------------------------
        c_btn = Card(col_left, width=440, height=280)
        c_btn.pack(fill="x", pady=(0, 14))

        c_btn_content = tk.Frame(c_btn, bg=pal.card_bg)
        c_btn_content.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(
            c_btn_content,
            text="Interactive Push Controls",
            font=("sans-serif", 12, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(0, 12))

        btn_row1 = tk.Frame(c_btn_content, bg=pal.card_bg)
        btn_row1.pack(fill="x", pady=4)

        b_pri = Button(btn_row1, text="Primary Teal", variant="primary", width=130, height=36)
        b_pri.pack(side="left", padx=(0, 8))

        b_acc = Button(btn_row1, text="Accent Orange", variant="accent", width=130, height=36)
        b_acc.pack(side="left", padx=4)

        b_sec = Button(btn_row1, text="Secondary", variant="secondary", width=120, height=36)
        b_sec.pack(side="left", padx=4)

        btn_row2 = tk.Frame(c_btn_content, bg=pal.card_bg)
        btn_row2.pack(fill="x", pady=8)

        b_out = Button(btn_row2, text="Outline Teal", variant="outline", width=130, height=36)
        b_out.pack(side="left", padx=(0, 8))

        b_ghost = Button(btn_row2, text="Flat Ghost", variant="ghost", width=130, height=36)
        b_ghost.pack(side="left", padx=4)

        b_dang = Button(btn_row2, text="Destructive", variant="destructive", width=120, height=36)
        b_dang.pack(side="left", padx=4)

        # Segmented Button
        tk.Label(
            c_btn_content,
            text="Segmented Filter Pill",
            font=("sans-serif", 10, "bold"),
            fg=pal.fg_subtle,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(12, 6))

        seg = SegmentedButton(
            c_btn_content,
            values=["Analytics", "Telemetry", "Diagnostics"],
            default_value="Analytics",
            width=390,
            height=34,
        )
        seg.pack(anchor="w")

        # ----------------------------------------------------------------------
        # Card 2: Form Toggles & Switches (Right)
        # ----------------------------------------------------------------------
        c_toggle = Card(col_right, width=440, height=280)
        c_toggle.pack(fill="x", pady=(0, 14))

        c_tog_content = tk.Frame(c_toggle, bg=pal.card_bg)
        c_tog_content.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(
            c_tog_content,
            text="Selection Controls & Toggles",
            font=("sans-serif", 12, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(0, 12))

        # Switches
        sw_row = tk.Frame(c_tog_content, bg=pal.card_bg)
        sw_row.pack(fill="x", pady=4)

        sw1 = Switch(sw_row, text="Hardware Blit", is_checked=True, width=180, height=26)
        sw1.pack(side="left")

        sw2 = Switch(sw_row, text="Ambient Bloom", is_checked=False, width=180, height=26)
        sw2.pack(side="left")

        # Checkboxes
        cb_row = tk.Frame(c_tog_content, bg=pal.card_bg)
        cb_row.pack(fill="x", pady=8)

        cb1 = Checkbox(cb_row, text="Vector Antialiasing", is_checked=True, width=180, height=24)
        cb1.pack(side="left")

        cb2 = Checkbox(cb_row, text="Zero-Copy Pipeline", is_checked=True, width=180, height=24)
        cb2.pack(side="left")

        # Radios
        self.radio_var = tk.StringVar(value="60")
        radio_row = tk.Frame(c_tog_content, bg=pal.card_bg)
        radio_row.pack(fill="x", pady=8)

        r1 = Radio(radio_row, text="60 FPS", value="60", variable=self.radio_var, width=110, height=24)
        r1.pack(side="left")

        r2 = Radio(radio_row, text="120 FPS", value="120", variable=self.radio_var, width=110, height=24)
        r2.pack(side="left")

        r3 = Radio(radio_row, text="ProMotion", value="pro", variable=self.radio_var, width=110, height=24)
        r3.pack(side="left")

        # ----------------------------------------------------------------------
        # Card 3: Metrics, Sliders & Gauges (Left)
        # ----------------------------------------------------------------------
        c_metrics = Card(col_left, width=440, height=260)
        c_metrics.pack(fill="x", pady=(0, 14))

        c_met_content = tk.Frame(c_metrics, bg=pal.card_bg)
        c_met_content.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(
            c_met_content,
            text="Sliders, Gauges & Sparklines",
            font=("sans-serif", 12, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(0, 10))

        sl_row = tk.Frame(c_met_content, bg=pal.card_bg)
        sl_row.pack(fill="x", pady=4)

        tk.Label(sl_row, text="Throughput:", font=("sans-serif", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(side="left", padx=(0, 8))
        sl = Slider(sl_row, width=280, height=24, from_=0, to=100, number_of_steps=100)
        sl.set(65.0)
        sl.pack(side="left")

        # Progress bar
        tk.Label(c_met_content, text="Buffer Capacity (84%):", font=("sans-serif", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w", pady=(8, 2))
        pb = Progressbar(c_met_content, width=380, height=6)
        pb.set(0.84)
        pb.pack(anchor="w", pady=(0, 10))

        # Sparkline
        tk.Label(c_met_content, text="Latency Waveform (ms):", font=("sans-serif", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w", pady=(2, 2))
        spark = Sparkline(c_met_content, data=[3.2, 4.1, 3.8, 5.0, 4.4, 3.1, 2.8, 3.5, 3.0], width=380, height=34)
        spark.pack(anchor="w")

        # ----------------------------------------------------------------------
        # Card 4: Inputs & Circular Progress (Right)
        # ----------------------------------------------------------------------
        c_inputs = Card(col_right, width=440, height=260)
        c_inputs.pack(fill="x", pady=(0, 14))

        c_inp_content = tk.Frame(c_inputs, bg=pal.card_bg)
        c_inp_content.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(
            c_inp_content,
            text="Inputs & Circular Telemetry",
            font=("sans-serif", 12, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(0, 10))

        split_row = tk.Frame(c_inp_content, bg=pal.card_bg)
        split_row.pack(fill="both", expand=True)

        left_side = tk.Frame(split_row, bg=pal.card_bg)
        left_side.pack(side="left", fill="both", expand=True)

        combo = ComboBox(
            left_side,
            values=["Renderer: Blend2D", "Renderer: Direct2D", "Renderer: Vulkan"],
            value="Renderer: Blend2D",
            width=230,
            height=34,
        )
        combo.pack(anchor="w", pady=(0, 8))

        search = TextBox(
            left_side,
            placeholder_text="Filter components...",
            width=230,
            height=34,
        )
        search.pack(anchor="w")

        # Circular Gauge
        right_side = tk.Frame(split_row, bg=pal.card_bg)
        right_side.pack(side="right", padx=(10, 0))

        gauge = CircularProgress(
            right_side,
            size=100,
            value=78.0,
            title="GPU 78%",
            color=pal.accent,  # Vibrant orange accent
            show_value=True,
        )
        gauge.pack()

        # ----------------------------------------------------------------------
        # Full-Width Card: High-Performance Data Table
        # ----------------------------------------------------------------------
        c_table = Card(body, width=900, height=240)
        c_table.pack(fill="x", pady=(0, 14))

        c_tbl_content = tk.Frame(c_table, bg=pal.card_bg)
        c_tbl_content.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(
            c_tbl_content,
            text="Hardware Pipeline Metrics",
            font=("sans-serif", 12, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(0, 8))

        columns = [
            {"id": "mod", "name": "Module", "width": 180, "align": "left"},
            {"id": "stat", "name": "Status", "width": 140, "align": "center"},
            {"id": "lat", "name": "Latency", "width": 140, "align": "right"},
            {"id": "thru", "name": "Throughput", "width": 160, "align": "right"},
            {"id": "eng", "name": "Engine", "width": 160, "align": "left"},
        ]

        rows = [
            ["Vector Blitter", "Active", "0.4 ms", "12.4 GB/s", "Blend2D C++"],
            ["Surface Registry", "Active", "0.1 ms", "38.2 GB/s", "Direct Memory"],
            ["Draw Engine", "Active", "0.6 ms", "8.9 GB/s", "Display List"],
            ["Native Controller", "Active", "0.2 ms", "16.1 GB/s", "X11 / Win32 Native"],
            ["Style Engine", "Active", "0.3 ms", "6.4 GB/s", "CSS Token Engine"],
        ]

        tbl = Table(
            c_tbl_content,
            columns=columns,
            rows=rows,
            width=860,
            height=140,
        )
        tbl.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = TealOrangeDemoApp()
    app.mainloop()
