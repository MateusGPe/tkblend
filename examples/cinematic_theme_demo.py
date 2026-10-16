#!/usr/bin/env python3
"""
Cinematic Theme Showcase
Demonstrating the blockbuster Teal & Orange aesthetic in tkblend.
Warm glowing amber interactive controls (switches, sliders, checkboxes, radios, focus)
paired with refined peacock teal primary actions and table selection.
"""

from __future__ import annotations

import sys
from pathlib import Path as FilePath
from typing import Optional, List
import tkinter as tk

# Ensure project root is in sys.path
PROJECT_ROOT = FilePath(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
    SearchEntry,
    get_theme,
    set_theme,
    cascade_bg_to_children,
    resolve_color_failsafe,
)


class CinematicDemoApp(tk.Tk):
    """
    Cinematic Theme Showcase application.
    Demonstrating the blockbuster Teal & Orange aesthetic in tkblend.
    """

    def __init__(self):
        super().__init__()
        self.title("tkblend — Cinematic Theme (Peacock Teal & Warm Amber)")
        self.geometry("1060x800")
        self.minsize(920, 680)

        tb.set_theme("cinematic")
        pal = tb.get_theme()
        self.configure(bg=pal.bg)

        self._all_rows: List[List[str]] = [
            ["Vector Blitter", "Active", "0.4 ms", "12.4 GB/s", "Blend2D C++"],
            ["Surface Registry", "Active", "0.1 ms", "38.2 GB/s", "Direct Memory"],
            ["Draw Engine", "Active", "0.6 ms", "8.9 GB/s", "Display List"],
            ["Native Controller", "Active", "0.2 ms", "16.1 GB/s", "X11 / Win32 Native"],
            ["Style Engine", "Active", "0.3 ms", "6.4 GB/s", "CSS Token Engine"],
        ]

        self._build_ui()
        tb.cascade_bg_to_children(self, pal.bg, palette=pal)

    def _build_ui(self):
        pal = tb.get_theme()

        # Header Title
        header = tk.Frame(self, bg=pal.bg)
        header.pack(fill="x", padx=24, pady=(16, 10))

        tk.Label(
            header,
            text="Cinematic Modern UI: Peacock Teal & Warm Amber",
            font=("sans-serif", 17, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Blockbuster color grade: pure flat tonal surfaces, zero borders & shadows, glowing warm amber focus & highlights.",
            font=("sans-serif", 9),
            fg=pal.fg_subtle,
            bg=pal.bg,
        ).pack(anchor="w", pady=(2, 0))

        # Main Scrollable Body
        scroller = ScrollableFrame(self, width=900, height=620)
        scroller.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        body = scroller.content

        # 2-Column Responsive Layout
        cols = tk.Frame(body, bg=pal.bg)
        cols.pack(fill="x", expand=True)

        col_left = tk.Frame(cols, bg=pal.bg)
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        col_right = tk.Frame(cols, bg=pal.bg)
        col_right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # ----------------------------------------------------------------------
        # Card 1: Buttons & Actions (Left)
        # ----------------------------------------------------------------------
        c_btn = Card(col_left, width=430, height=225, auto_height=True)
        c_btn.pack(fill="x", pady=(0, 12))

        c_btn_content = c_btn.content

        tk.Label(
            c_btn_content,
            text="Interactive Push Controls",
            font=("sans-serif", 11, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(0, 8))

        btn_row1 = tk.Frame(c_btn_content, bg=pal.card_bg)
        btn_row1.pack(fill="x", pady=(0, 4))

        b_pri = Button(btn_row1, text="Primary Teal", variant="primary", width=130, height=34, auto_fit=True)
        b_pri.pack(side="left", padx=(0, 6))

        b_acc = Button(btn_row1, text="Amber Accent", variant="accent", width=130, height=34, auto_fit=True)
        b_acc.pack(side="left", padx=4)

        b_sec = Button(btn_row1, text="Secondary", variant="secondary", width=120, height=34, auto_fit=True)
        b_sec.pack(side="left", padx=4)

        btn_row2 = tk.Frame(c_btn_content, bg=pal.card_bg)
        btn_row2.pack(fill="x", pady=(0, 8))

        b_out = Button(btn_row2, text="Tinted Teal", variant="outline", width=130, height=34, auto_fit=True)
        b_out.pack(side="left", padx=(0, 6))

        b_ghost = Button(btn_row2, text="Flat Ghost", variant="ghost", width=130, height=34, auto_fit=True)
        b_ghost.pack(side="left", padx=4)

        b_dang = Button(btn_row2, text="Destructive", variant="destructive", width=120, height=34, auto_fit=True)
        b_dang.pack(side="left", padx=4)

        # Segmented Button
        tk.Label(
            c_btn_content,
            text="Segmented Filter Pill",
            font=("sans-serif", 9, "bold"),
            fg=pal.fg_subtle,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(0, 4))

        seg = SegmentedButton(
            c_btn_content,
            values=["Analytics", "Telemetry", "Diagnostics"],
            default_value="Analytics",
            width=380,
            height=32,
        )
        seg.pack(anchor="w")

        # ----------------------------------------------------------------------
        # Card 2: Form Toggles & Switches (Right) - Warm Amber Interactive Controls
        # ----------------------------------------------------------------------
        c_toggle = Card(col_right, width=430, height=225, auto_height=True)
        c_toggle.pack(fill="x", pady=(0, 12))

        c_tog_content = c_toggle.content

        tk.Label(
            c_tog_content,
            text="Warm Amber Toggles & Selection Controls",
            font=("sans-serif", 11, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(0, 8))

        # Switches
        sw_row = tk.Frame(c_tog_content, bg=pal.card_bg)
        sw_row.pack(fill="x", pady=(0, 6))

        sw1 = Switch(sw_row, text="Hardware Blit", is_checked=True, width=170, height=26)
        sw1.pack(side="left")

        sw2 = Switch(sw_row, text="Ambient Bloom", is_checked=False, width=170, height=26)
        sw2.pack(side="left")

        # Checkboxes
        cb_row = tk.Frame(c_tog_content, bg=pal.card_bg)
        cb_row.pack(fill="x", pady=(0, 6))

        cb1 = Checkbox(cb_row, text="Vector Antialiasing", is_checked=True, width=170, height=24)
        cb1.pack(side="left")

        cb2 = Checkbox(cb_row, text="Zero-Copy Pipeline", is_checked=True, width=170, height=24)
        cb2.pack(side="left")

        # Radios with synchronized mutual exclusivity
        self.radio_var = tk.StringVar(value="60")
        radio_row = tk.Frame(c_tog_content, bg=pal.card_bg)
        radio_row.pack(fill="x", pady=(0, 4))

        r1 = Radio(radio_row, text="60 FPS", value="60", variable=self.radio_var, width=105, height=24)
        r1.pack(side="left")

        r2 = Radio(radio_row, text="120 FPS", value="120", variable=self.radio_var, width=105, height=24)
        r2.pack(side="left")

        r3 = Radio(radio_row, text="ProMotion", value="pro", variable=self.radio_var, width=105, height=24)
        r3.pack(side="left")

        # ----------------------------------------------------------------------
        # Card 3: Metrics, Sliders & Gauges (Left)
        # ----------------------------------------------------------------------
        c_metrics = Card(col_left, width=430, height=210, auto_height=True)
        c_metrics.pack(fill="x", pady=(0, 12))

        c_met_content = c_metrics.content

        tk.Label(
            c_met_content,
            text="Sliders, Gauges & Waveforms",
            font=("sans-serif", 11, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(0, 6))

        sl_row = tk.Frame(c_met_content, bg=pal.card_bg)
        sl_row.pack(fill="x", pady=(0, 4))

        tk.Label(sl_row, text="Throughput:", font=("sans-serif", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(side="left", padx=(0, 8))
        sl = Slider(sl_row, width=270, height=22, from_=0, to=100)
        sl.set(65.0)
        sl.pack(side="left")

        # Progress bar (Peacock Teal)
        tk.Label(c_met_content, text="Buffer Capacity — Teal Fill (84%):", font=("sans-serif", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w", pady=(2, 2))
        pb = Progressbar(c_met_content, width=370, height=6)
        pb.set(0.84)
        pb.pack(anchor="w", pady=(0, 6))

        # Sparkline
        tk.Label(c_met_content, text="Latency Waveform (ms):", font=("sans-serif", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w", pady=(2, 2))
        spark = Sparkline(c_met_content, data=[3.2, 4.1, 3.8, 5.0, 4.4, 3.1, 2.8, 3.5, 3.0], width=370, height=30)
        spark.pack(anchor="w")

        # ----------------------------------------------------------------------
        # Card 4: Inputs & Circular Progress (Right)
        # ----------------------------------------------------------------------
        c_inputs = Card(col_right, width=430, height=210, auto_height=True)
        c_inputs.pack(fill="x", pady=(0, 12))

        c_inp_content = c_inputs.content

        tk.Label(
            c_inp_content,
            text="Inputs & Circular Telemetry",
            font=("sans-serif", 11, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(0, 6))

        split_row = tk.Frame(c_inp_content, bg=pal.card_bg)
        split_row.pack(fill="both", expand=True)

        left_side = tk.Frame(split_row, bg=pal.card_bg)
        left_side.pack(side="left", fill="both", expand=True)

        combo = ComboBox(
            left_side,
            values=["Renderer: Blend2D", "Renderer: Direct2D", "Renderer: Vulkan"],
            value="Renderer: Blend2D",
            width=220,
            height=30,
        )
        combo.pack(anchor="w", pady=(0, 8))

        self._search = SearchEntry(
            left_side,
            placeholder="Filter components...",
            width=220,
            height=40,
        )
        self._search.pack(anchor="w")
        self._search._entry.bind("<KeyRelease>", self._on_filter_changed)

        # Circular Gauge (Warm Amber Accent)
        right_side = tk.Frame(split_row, bg=pal.card_bg)
        right_side.pack(side="right", padx=(10, 0))

        gauge = CircularProgress(
            right_side,
            size=92,
            value=78.0,
            title="GPU",
            show_value=True,
        )
        # Set warm amber accent color on circular progress
        gauge.set_var("--primary", pal.accent)
        gauge.pack()

        # ----------------------------------------------------------------------
        # Full-Width Card: High-Performance Data Table (Peacock Teal Selection)
        # ----------------------------------------------------------------------
        c_table = Card(body, width=880, height=295, auto_height=True)
        c_table.pack(fill="x", pady=(0, 12))

        c_tbl_content = c_table.content

        tk.Label(
            c_tbl_content,
            text="Hardware Pipeline Metrics",
            font=("sans-serif", 11, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        ).pack(anchor="w", pady=(0, 6))

        col_names = ["Module", "Status", "Latency", "Throughput", "Engine"]
        col_widths = [190, 130, 130, 160, 180]

        self._table = Table(
            c_tbl_content,
            columns=col_names,
            data=self._all_rows,
            column_widths=col_widths,
            width=840,
            height=215,
        )
        self._table.pack(fill="both", expand=True)

    def _on_filter_changed(self, _event=None) -> None:
        query = self._search.get().strip().lower()
        if not query:
            self._table.data = list(self._all_rows)
        else:
            filtered = [
                row for row in self._all_rows
                if any(query in str(cell).lower() for cell in row)
            ]
            self._table.data = filtered


if __name__ == "__main__":
    app = CinematicDemoApp()
    app.mainloop()
