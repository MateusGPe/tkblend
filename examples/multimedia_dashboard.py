#!/usr/bin/env python3
"""
tkblend Multimedia & Studio Telemetry Dashboard Showcase.
Demonstrates:
  - Sparklines (Line, Area, Bar, Win/Loss)
  - Real-time Multi-Series Charts (LineChart, AreaChart, BarChart, DonutChart)
  - Color Controls (ColorPicker, ColorWell, ask_color dialog)
  - Audio Suite (VolumeControl, Stereo VUMeter with LED & gradient modes)
  - Toolbars (Action bar, Toggle tools, Separators, Spacers)
  - Dynamic Runtime Palette Switching
"""

from __future__ import annotations
import math
import random
import time
import tkinter as tk
from typing import Optional

import tkblend as tb
from tkblend import (
    Card,
    Frame,
    ScrollableFrame,
    Button,
    Sparkline,
    LineChart,
    AreaChart,
    BarChart,
    PieChart,
    DonutChart,
    ColorPicker,
    ColorWell,
    ask_color,
    VolumeControl,
    VUMeter,
    AudioMeter,
    Toolbar,
    ToolbarSeparator,
    Switch,
    SegmentedButton,
    OptionMenu,
    Badge,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
)


class MultimediaDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("tkblend Studio & Telemetry Suite")
        self.geometry("1180x820")
        self.minsize(980, 680)

        # Apply dark theme by default
        set_theme("dark")
        pal = get_theme()
        self.configure(bg=pal.bg)

        self._build_ui()
        self._start_telemetry_loop()

    def _build_ui(self):
        pal = get_theme()

        # =====================================================================
        # TOP DOCKED TOOLBAR & HEADER
        # =====================================================================
        top_bar = Toolbar(self, orientation="horizontal", style="docked", padding=6)
        top_bar.pack(fill="x", padx=16, pady=(12, 6))

        top_bar.add_button("📊 Studio Suite", variant="ghost")
        top_bar.add_separator()

        # Mode toggles
        top_bar.add_toggle("🔴 Live Stream", initial=True, command=self._on_toggle_stream)
        top_bar.add_toggle("🔊 Audio Master", initial=True, command=self._on_toggle_audio)
        top_bar.add_separator()

        # Theme selector dropdown
        theme_names = get_available_themes()
        self._theme_opt = OptionMenu(
            top_bar,
            values=theme_names,
            default_value="dark",
            command=self._on_theme_changed,
            width=130,
        )
        top_bar.add_widget(self._theme_opt)

        top_bar.add_spacer()

        # Color Well in toolbar
        self._accent_well = ColorWell(
            top_bar,
            color=pal.primary,
            on_change=self._on_accent_color_changed,
            width=36,
            height=28,
        )
        top_bar.add_widget(self._accent_well)

        top_bar.add_button(
            "🎨 Custom Dialog",
            variant="outline",
            command=self._open_color_dialog,
        )

        # =====================================================================
        # MAIN CONTENT AREA
        # =====================================================================
        content_container = tk.Frame(self, bg=pal.bg)
        content_container.pack(fill="both", expand=True, padx=16, pady=(4, 14))

        # ---------------------------------------------------------------------
        # ROW 1: STAT CARDS WITH EMBEDDED SPARKLINES
        # ---------------------------------------------------------------------
        stats_row = tk.Frame(content_container, bg=pal.bg)
        stats_row.pack(fill="x", pady=(0, 10))

        # Card 1: Revenue (Line Sparkline)
        c1 = Card(stats_row, height=115, rx=12, ry=12, elevation=4)
        c1.pack(side="left", fill="both", expand=True, padx=(0, 6))
        tb.Label(c1.body, text="Total Revenue", font_size=10, color="text_muted", height=18).pack(anchor="w", padx=12, pady=(8, 0))
        tb.Label(c1.body, text="$128,450", font_size=18, bold=True, height=26).pack(anchor="w", padx=12, pady=(0, 2))
        self._sp_line = Sparkline(c1.body, data=[32, 45, 40, 58, 62, 75, 70, 88, 92, 105], kind="line", color="#3b82f6", height=32)
        self._sp_line.pack(fill="x", padx=12, pady=(0, 6))

        # Card 2: Active Users (Area Sparkline)
        c2 = Card(stats_row, height=115, rx=12, ry=12, elevation=4)
        c2.pack(side="left", fill="both", expand=True, padx=6)
        tb.Label(c2.body, text="Active Users", font_size=10, color="text_muted", height=18).pack(anchor="w", padx=12, pady=(8, 0))
        tb.Label(c2.body, text="42,890", font_size=18, bold=True, height=26).pack(anchor="w", padx=12, pady=(0, 2))
        self._sp_area = Sparkline(c2.body, data=[18, 24, 30, 28, 45, 52, 60, 58, 70, 85], kind="area", color="#10b981", height=32)
        self._sp_area.pack(fill="x", padx=12, pady=(0, 6))

        # Card 3: Server Load (Bar Sparkline)
        c3 = Card(stats_row, height=115, rx=12, ry=12, elevation=4)
        c3.pack(side="left", fill="both", expand=True, padx=6)
        tb.Label(c3.body, text="Server Capacity", font_size=10, color="text_muted", height=18).pack(anchor="w", padx=12, pady=(8, 0))
        tb.Label(c3.body, text="78.4 %", font_size=18, bold=True, height=26).pack(anchor="w", padx=12, pady=(0, 2))
        self._sp_bar = Sparkline(c3.body, data=[40, 65, 55, 80, 70, 90, 85, 60, 78], kind="bar", color="#f59e0b", height=32)
        self._sp_bar.pack(fill="x", padx=12, pady=(0, 6))

        # Card 4: Daily Win/Loss Sparkline
        c4 = Card(stats_row, height=115, rx=12, ry=12, elevation=4)
        c4.pack(side="left", fill="both", expand=True, padx=(6, 0))
        tb.Label(c4.body, text="Deployment Health", font_size=10, color="text_muted", height=18).pack(anchor="w", padx=12, pady=(8, 0))
        tb.Label(c4.body, text="96.2 %", font_size=18, bold=True, height=26).pack(anchor="w", padx=12, pady=(0, 2))
        self._sp_winloss = Sparkline(c4.body, data=[1, 1, -1, 1, 1, 1, 0, 1, -1, 1, 1], kind="winloss", height=32)
        self._sp_winloss.pack(fill="x", padx=12, pady=(0, 6))

        # ---------------------------------------------------------------------
        # ROW 2: REAL-TIME CHARTS & AUDIO METERS
        # ---------------------------------------------------------------------
        charts_row = tk.Frame(content_container, bg=pal.bg)
        charts_row.pack(fill="both", expand=True)

        # Left Column: Multi-Series LineChart & BarChart
        left_col = tk.Frame(charts_row, bg=pal.bg)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 8))

        card_live = Card(left_col, rx=12, ry=12, elevation=4)
        card_live.pack(fill="both", expand=True, pady=(0, 6))
        self._live_chart = LineChart(
            card_live.body,
            title="Real-Time Network Telemetry (KB/s)",
            smooth=True,
            fill_area=True,
        )
        self._live_chart.add_series("Inbound", [random.uniform(40, 80) for _ in range(25)], color="#3b82f6")
        self._live_chart.add_series("Outbound", [random.uniform(20, 50) for _ in range(25)], color="#10b981")
        self._live_chart.pack(fill="both", expand=True, padx=6, pady=6)

        card_bar = Card(left_col, rx=12, ry=12, elevation=4)
        card_bar.pack(fill="both", expand=True, pady=(6, 0))
        self._bar_chart = BarChart(
            card_bar.body,
            title="Quarterly Regional Distribution",
            categories=["NA", "EU", "APAC", "LATAM"],
            show_values=True,
        )
        self._bar_chart.add_series("2025", [45, 60, 35, 25], color="#6366f1")
        self._bar_chart.add_series("2026", [58, 72, 48, 38], color="#06b6d4")
        self._bar_chart.pack(fill="both", expand=True, padx=6, pady=6)

        # Right Column: Donut Chart, Color Picker Panel & Audio VU Controls
        right_col = tk.Frame(charts_row, bg=pal.bg, width=350)
        right_col.pack(side="right", fill="both", expand=False, padx=(8, 0))
        right_col.pack_propagate(False)

        # Audio Studio Control Card
        card_audio = Card(right_col, height=270, rx=12, ry=12, elevation=4)
        card_audio.pack(fill="x", pady=(0, 6))
        tb.Label(card_audio.body, text="Audio Studio Monitor", font_size=11, bold=True, height=20).pack(anchor="w", padx=12, pady=(8, 4))

        self._vol_slider = VolumeControl(card_audio.body, value=80, on_change=self._on_volume_changed)
        self._vol_slider.pack(fill="x", padx=12, pady=4)

        tb.Label(card_audio.body, text="Master Output (Stereo LED)", font_size=9, color="text_muted", height=16).pack(anchor="w", padx=12, pady=(6, 2))
        self._vu_meter_led = VUMeter(card_audio.body, channels=2, mode="segmented", height=34)
        self._vu_meter_led.pack(fill="x", padx=12, pady=2)

        tb.Label(card_audio.body, text="Monitor Bus (Gradient Peak)", font_size=9, color="text_muted", height=16).pack(anchor="w", padx=12, pady=(6, 2))
        self._vu_meter_grad = VUMeter(card_audio.body, channels=1, mode="gradient", height=22)
        self._vu_meter_grad.pack(fill="x", padx=12, pady=(2, 8))

        # Donut Chart & Color Swatches Card
        card_donut = Card(right_col, rx=12, ry=12, elevation=4)
        card_donut.pack(fill="both", expand=True, pady=(6, 0))
        self._donut_chart = DonutChart(
            card_donut.body,
            data={"Compute": 45, "Storage": 28, "Network": 18, "Memory": 9},
            title="Cluster Resource Allocation",
        )
        self._donut_chart.pack(fill="both", expand=True, padx=6, pady=6)

    def _on_toggle_stream(self, active: bool):
        self._stream_active = active

    def _on_toggle_audio(self, active: bool):
        self._audio_active = active

    def _on_volume_changed(self, vol: float):
        pass

    def _on_accent_color_changed(self, color: str):
        self._sp_line.color = color
        self._sp_area.color = color

    def _open_color_dialog(self):
        new_color = ask_color(initial_color=self._accent_well.color, parent=self)
        if new_color:
            self._accent_well.color = new_color
            self._on_accent_color_changed(new_color)

    def _on_theme_changed(self, theme_name: str):
        set_theme(theme_name)
        pal = get_theme()
        self.configure(bg=pal.bg)
        self._accent_well.color = pal.primary
        cascade_bg_to_children(self, pal.bg)

    def _start_telemetry_loop(self):
        self._stream_active = True
        self._audio_active = True
        self._step = 0

        def update():
            if not self.winfo_exists():
                return

            self._step += 1

            # 1. Update Live Chart & Sparklines
            if self._stream_active:
                in_val = 50.0 + 25.0 * math.sin(self._step * 0.2) + random.uniform(-10, 10)
                out_val = 30.0 + 15.0 * math.cos(self._step * 0.15) + random.uniform(-6, 6)
                self._live_chart.push_data({"Inbound": max(5, in_val), "Outbound": max(2, out_val)})
                self._sp_line.push_data(in_val, max_points=20)
                self._sp_area.push_data(out_val, max_points=20)

            # 2. Update VU Meter levels
            if self._audio_active:
                master_vol = self._vol_slider.value / 100.0
                base_l = (0.5 + 0.35 * math.sin(self._step * 0.4) + random.uniform(-0.1, 0.15)) * master_vol
                base_r = (0.5 + 0.35 * math.cos(self._step * 0.35) + random.uniform(-0.1, 0.15)) * master_vol
                self._vu_meter_led.set_levels(max(0.0, min(1.0, base_l)), max(0.0, min(1.0, base_r)))
                self._vu_meter_grad.set_levels(max(0.0, min(1.0, (base_l + base_r) / 2.0)))

            self.after(80, update)

        self.after(100, update)


if __name__ == "__main__":
    app = MultimediaDashboard()
    app.mainloop()

