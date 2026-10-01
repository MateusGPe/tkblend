#!/usr/bin/env python3
"""
tkblend Showcase: Modern SaaS & System Telemetry Analytics Dashboard.
Demonstrates:
  - Zero-TTK pure Blend2D vector widgets (Card, CircularProgress, Table, Switch, SegmentedButton, etc.)
  - High-performance live BlendCanvas vector charts with multi-series Bezier curves and gradient fills
  - Dynamic runtime palette switching across 13+ themes
  - Real-time data streaming and animated gauge metrics
"""

from __future__ import annotations

import math
import random
import time
import tkinter as tk
from typing import Optional, List, Dict, Any

import tkblend as tb
from tkblend import (
    Card,
    CircularProgress,
    Table,
    Button,
    Switch,
    SegmentedButton,
    RangeSlider,
    Slider,
    OptionMenu,
    Badge,
    BlendCanvas,
    LinearGradient,
    Path,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    ScalingTracker,
)


class SparklineCanvas(BlendCanvas):
    """Mini vector sparkline chart rendered via Blend2D."""

    def __init__(self, master: tk.Misc, data: List[float], color: str = "#3b82f6", width: int = 100, height: int = 36, **kwargs):
        self._data = list(data)
        self._line_color = color
        super().__init__(master, width=width, height=height, bg="card_bg", **kwargs)

    def set_data(self, data: List[float]) -> None:
        self._data = list(data)
        self.redraw()

    def set_color(self, color: str) -> None:
        self._line_color = color
        self.redraw()

    def _redraw(self) -> None:
        if self._surface is None or len(self._data) < 2:
            return

        pal = get_theme()
        w = float(self._canvas_width)
        h = float(self._canvas_height)

        self._surface.clear(pal.card_bg)

        min_v = min(self._data)
        max_v = max(self._data)
        rng = max(1.0, max_v - min_v)

        pts = []
        n = len(self._data)
        for i, val in enumerate(self._data):
            x = (i / (n - 1)) * (w - 8.0) + 4.0
            norm = (val - min_v) / rng
            y = h - 6.0 - (norm * (h - 12.0))
            pts.append((x, y))

        # Fill gradient path
        path_fill = Path()
        path_fill.move_to(pts[0][0], h)
        path_fill.line_to(pts[0][0], pts[0][1])
        for i in range(1, len(pts)):
            xc = (pts[i - 1][0] + pts[i][0]) / 2.0
            yc = (pts[i - 1][1] + pts[i][1]) / 2.0
            path_fill.quad_to(pts[i - 1][0], pts[i - 1][1], xc, yc)
        path_fill.line_to(pts[-1][0], pts[-1][1])
        path_fill.line_to(pts[-1][0], h)
        path_fill.close()

        grad = LinearGradient(0, 0, 0, h)
        grad.add_stop(0.0, self._line_color + "44" if len(self._line_color) == 7 else self._line_color)
        grad.add_stop(1.0, self._line_color + "05" if len(self._line_color) == 7 else self._line_color)
        self._surface.fill_path(path_fill, grad)

        # Stroke curve
        path_stroke = Path()
        path_stroke.move_to(pts[0][0], pts[0][1])
        for i in range(1, len(pts)):
            xc = (pts[i - 1][0] + pts[i][0]) / 2.0
            yc = (pts[i - 1][1] + pts[i][1]) / 2.0
            path_stroke.quad_to(pts[i - 1][0], pts[i - 1][1], xc, yc)
        path_stroke.line_to(pts[-1][0], pts[-1][1])

        self._surface.stroke_path(path_stroke, self._line_color, stroke_width=2.0)
        self._surface.fill_circle(pts[-1][0], pts[-1][1], 3.0, self._line_color)


class TelemetryChart(BlendCanvas):
    """High-performance multi-series vector telemetry chart with smooth Bézier curves."""

    def __init__(self, master: tk.Misc, width: int = 600, height: int = 240, **kwargs):
        self._series1: List[float] = [random.uniform(20, 65) for _ in range(30)]
        self._series2: List[float] = [random.uniform(10, 45) for _ in range(30)]
        self._hover_idx: Optional[int] = None
        super().__init__(master, width=width, height=height, bg="card_bg", **kwargs)
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)

    def _on_mouse_move(self, event) -> None:
        w = float(self._canvas_width)
        pad_l = 45.0
        pad_r = 20.0
        plot_w = max(1.0, w - pad_l - pad_r)
        if pad_l <= event.x <= w - pad_r:
            rel_x = (event.x - pad_l) / plot_w
            n = len(self._series1)
            idx = int(round(rel_x * (n - 1)))
            self._hover_idx = max(0, min(n - 1, idx))
            self.redraw()
        else:
            if self._hover_idx is not None:
                self._hover_idx = None
                self.redraw()

    def _on_mouse_leave(self, _event) -> None:
        if self._hover_idx is not None:
            self._hover_idx = None
            self.redraw()

    def push_data(self, val1: float, val2: float) -> None:
        self._series1.pop(0)
        self._series1.append(val1)
        self._series2.pop(0)
        self._series2.append(val2)
        self.redraw()

    def _redraw(self) -> None:
        if self._surface is None:
            return

        pal = get_theme()
        w = float(self._canvas_width)
        h = float(self._canvas_height)

        self._surface.clear(pal.card_bg)

        pad_l = 45.0
        pad_r = 20.0
        pad_t = 30.0
        pad_b = 30.0
        plot_w = max(1.0, w - pad_l - pad_r)
        plot_h = max(1.0, h - pad_t - pad_b)

        # Draw grid lines & Y-axis labels
        grid_lines = 4
        for i in range(grid_lines + 1):
            y = pad_t + (i / grid_lines) * plot_h
            val_lbl = int(100 - (i / grid_lines) * 100)
            self._surface.draw_line(pad_l, y, w - pad_r, y, pal.surface_border, stroke_width=1.0)
            self._surface.draw_text(
                f"{val_lbl}k",
                pad_l - 8.0,
                y + 4.0,
                font_size=10.0,
                color=pal.fg_subtle,
                align="right",
            )

        # Chart curves calculation
        def get_points(series: List[float]) -> List[tuple[float, float]]:
            pts = []
            n = len(series)
            for idx, val in enumerate(series):
                px = pad_l + (idx / (n - 1)) * plot_w
                py = pad_t + (1.0 - max(0.0, min(100.0, val)) / 100.0) * plot_h
                pts.append((px, py))
            return pts

        pts1 = get_points(self._series1)
        pts2 = get_points(self._series2)

        # Draw Series 2 (Secondary / Cyan)
        self._draw_area_and_curve(pts2, pal.secondary or "#06b6d4", pad_t + plot_h)
        # Draw Series 1 (Primary / Violet or Blue)
        self._draw_area_and_curve(pts1, pal.primary or "#3b82f6", pad_t + plot_h)

        # Draw Header Legend
        self._surface.fill_circle(pad_l + 10.0, 14.0, 4.0, pal.primary or "#3b82f6")
        self._surface.draw_text("Network In (MB/s)", pad_l + 20.0, 18.0, font_size=11.0, color=pal.fg, align="left")

        self._surface.fill_circle(pad_l + 160.0, 14.0, 4.0, pal.secondary or "#06b6d4")
        self._surface.draw_text("Network Out (MB/s)", pad_l + 170.0, 18.0, font_size=11.0, color=pal.fg, align="left")

        # Hover Tooltip Crosshair
        if self._hover_idx is not None and 0 <= self._hover_idx < len(pts1):
            hx = pts1[self._hover_idx][0]
            self._surface.draw_line(hx, pad_t, hx, pad_t + plot_h, pal.accent or pal.primary, stroke_width=1.5)

            # Draw glowing circles at intersection
            for pts, col, val in [(pts1, pal.primary, self._series1[self._hover_idx]), (pts2, pal.secondary, self._series2[self._hover_idx])]:
                hy = pts[self._hover_idx][1]
                self._surface.fill_circle(hx, hy, 5.0, col)
                self._surface.stroke_circle(hx, hy, 7.0, "#ffffff", stroke_width=1.5)

            # Floating Tooltip Box
            tt_w = 90.0
            tt_h = 44.0
            tt_x = min(w - pad_r - tt_w, max(pad_l, hx - tt_w / 2.0))
            tt_y = pad_t + 6.0
            self._surface.fill_rounded_rect(tt_x, tt_y, tt_w, tt_h, 6.0, 6.0, pal.card_bg)
            self._surface.stroke_rounded_rect(tt_x, tt_y, tt_w, tt_h, 6.0, 6.0, pal.card_border, stroke_width=1.0)
            self._surface.draw_text(f"In:  {self._series1[self._hover_idx]:.1f} MB/s", tt_x + 8.0, tt_y + 16.0, font_size=10.0, color=pal.primary)
            self._surface.draw_text(f"Out: {self._series2[self._hover_idx]:.1f} MB/s", tt_x + 8.0, tt_y + 32.0, font_size=10.0, color=pal.secondary)

    def _draw_area_and_curve(self, pts: List[tuple[float, float]], color: str, bottom_y: float) -> None:
        if len(pts) < 2:
            return

        # Smooth Area Fill
        area_path = Path()
        area_path.move_to(pts[0][0], bottom_y)
        area_path.line_to(pts[0][0], pts[0][1])
        for i in range(1, len(pts)):
            xc = (pts[i - 1][0] + pts[i][0]) / 2.0
            yc = (pts[i - 1][1] + pts[i][1]) / 2.0
            area_path.quad_to(pts[i - 1][0], pts[i - 1][1], xc, yc)
        area_path.line_to(pts[-1][0], pts[-1][1])
        area_path.line_to(pts[-1][0], bottom_y)
        area_path.close()

        grad = LinearGradient(0, pts[0][1], 0, bottom_y)
        hex_col = color if color.startswith("#") and len(color) == 7 else "#3b82f6"
        grad.add_stop(0.0, hex_col + "40")
        grad.add_stop(1.0, hex_col + "00")
        self._surface.fill_path(area_path, grad)

        # Smooth Stroke
        curve_path = Path()
        curve_path.move_to(pts[0][0], pts[0][1])
        for i in range(1, len(pts)):
            xc = (pts[i - 1][0] + pts[i][0]) / 2.0
            yc = (pts[i - 1][1] + pts[i][1]) / 2.0
            curve_path.quad_to(pts[i - 1][0], pts[i - 1][1], xc, yc)
        curve_path.line_to(pts[-1][0], pts[-1][1])
        self._surface.stroke_path(curve_path, color, stroke_width=2.5)


class AnalyticsDashboard(tk.Frame):
    """Production-grade telemetry & analytics dashboard showcase using pure Blend2D widgets."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._is_streaming = True
        self._timer_id: Optional[str] = None
        self._build_ui()
        self._start_data_stream()

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Top Header Bar
        hdr_frame = tk.Frame(self, background=pal.bg)
        hdr_frame.pack(fill="x", padx=24, pady=(18, 12))

        title_box = tk.Frame(hdr_frame, background=pal.bg)
        title_box.pack(side="left")

        app_title = tk.Label(
            title_box,
            text="Nexus Telemetry",
            font=("Segoe UI", 18, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        )
        app_title.pack(anchor="w")

        app_subtitle = tk.Label(
            title_box,
            text="Real-time multi-cluster performance & incident feed",
            font=("Segoe UI", 10),
            fg=pal.fg_subtle,
            bg=pal.bg,
        )
        app_subtitle.pack(anchor="w")

        # Top Right Controls
        ctrl_box = tk.Frame(hdr_frame, background=pal.bg)
        ctrl_box.pack(side="right")

        self._clock_lbl = tk.Label(
            ctrl_box,
            text=time.strftime("%H:%M:%S UTC"),
            font=("Segoe UI", 11, "bold"),
            fg=pal.fg,
            bg=pal.bg,
            padx=12,
        )
        self._clock_lbl.pack(side="left", padx=8)

        theme_lbl = tk.Label(ctrl_box, text="Theme:", font=("Segoe UI", 10), fg=pal.fg_subtle, bg=pal.bg)
        theme_lbl.pack(side="left", padx=(8, 4))

        themes = list(get_available_themes())
        self._theme_opt = OptionMenu(
            ctrl_box,
            values=themes,
            default_value="dark",
            command=self._on_change_theme,
            width=140,
            height=32,
        )
        self._theme_opt.pack(side="left", padx=6)

        self._live_btn = Button(
            ctrl_box,
            text="Streaming: ON",
            width=120,
            height=32,
            command=self._toggle_streaming,
        )
        self._live_btn.pack(side="left", padx=6)

        # KPI Metric Summary Cards Grid
        kpi_row = tk.Frame(self, background=pal.bg)
        kpi_row.pack(fill="x", padx=24, pady=8)

        self._kpi_cards: List[Card] = []
        self._sparklines: List[SparklineCanvas] = []

        kpi_data = [
            ("Active Instances", "1,428", "+12.4%", pal.success or "#10b981", [30, 42, 55, 48, 62, 75, 88]),
            ("Req / Second", "84.6k", "+5.2%", pal.primary or "#3b82f6", [60, 58, 65, 72, 70, 80, 84]),
            ("P99 Latency", "18.4 ms", "-3.1%", pal.accent or "#8b5cf6", [40, 35, 30, 28, 25, 20, 18]),
            ("Error Budget", "99.98%", "Healthy", pal.success or "#10b981", [99, 99, 100, 99, 100, 100, 100]),
        ]

        for title, val, delta, col, spark_vals in kpi_data:
            c = Card(kpi_row, width=220, height=95, rx=12, ry=12, elevation=6)
            c.pack(side="left", fill="both", expand=True, padx=6)
            self._kpi_cards.append(c)

            body = c.body
            c_top = tk.Frame(body, background=c.bg_color)
            c_top.pack(fill="x", padx=12, pady=(10, 2))

            t_lbl = tk.Label(c_top, text=title, font=("Segoe UI", 9), fg=pal.fg_subtle, bg=c.bg_color)
            t_lbl.pack(side="left")

            b = Badge(c_top, text=delta, color=col, text_color="#ffffff", height=18)
            b.pack(side="right")

            c_bot = tk.Frame(body, background=c.bg_color)
            c_bot.pack(fill="both", expand=True, padx=12, pady=(2, 8))

            v_lbl = tk.Label(c_bot, text=val, font=("Segoe UI", 16, "bold"), fg=pal.fg, bg=c.bg_color)
            v_lbl.pack(side="left")

            sp = SparklineCanvas(c_bot, data=spark_vals, color=col, width=80, height=28)
            sp.pack(side="right")
            self._sparklines.append(sp)

        # Middle Content Row (Telemetry Gauges + Live Vector Chart)
        mid_row = tk.Frame(self, background=pal.bg)
        mid_row.pack(fill="both", expand=True, padx=24, pady=8)

        # System Hardware Gauges Card
        gauge_card = Card(mid_row, title="System Telemetry", width=280, height=240, rx=12, ry=12, elevation=6)
        gauge_card.pack(side="left", fill="y", padx=(6, 8))

        g_body = gauge_card.body
        g_row = tk.Frame(g_body, background=gauge_card.bg_color)
        g_row.pack(fill="both", expand=True, padx=10, pady=6)

        # CPU Gauge
        cpu_box = tk.Frame(g_row, background=gauge_card.bg_color)
        cpu_box.pack(side="left", fill="both", expand=True)
        self._cpu_gauge = CircularProgress(cpu_box, size=76, stroke_width=7, value=58, color=pal.primary)
        self._cpu_gauge.pack(pady=(4, 2))
        self._cpu_lbl = tk.Label(cpu_box, text="CPU\n58%", font=("Segoe UI", 9, "bold"), fg=pal.fg, bg=gauge_card.bg_color)
        self._cpu_lbl.pack()

        # RAM Gauge
        ram_box = tk.Frame(g_row, background=gauge_card.bg_color)
        ram_box.pack(side="left", fill="both", expand=True)
        self._ram_gauge = CircularProgress(ram_box, size=76, stroke_width=7, value=74, color=pal.secondary)
        self._ram_gauge.pack(pady=(4, 2))
        self._ram_lbl = tk.Label(ram_box, text="RAM\n74%", font=("Segoe UI", 9, "bold"), fg=pal.fg, bg=gauge_card.bg_color)
        self._ram_lbl.pack()

        # GPU / Disk Gauge
        gpu_box = tk.Frame(g_row, background=gauge_card.bg_color)
        gpu_box.pack(side="left", fill="both", expand=True)
        self._gpu_gauge = CircularProgress(gpu_box, size=76, stroke_width=7, value=42, color=pal.accent)
        self._gpu_gauge.pack(pady=(4, 2))
        self._gpu_lbl = tk.Label(gpu_box, text="GPU\n42%", font=("Segoe UI", 9, "bold"), fg=pal.fg, bg=gauge_card.bg_color)
        self._gpu_lbl.pack()

        # Gauge Status Footer
        g_footer = tk.Frame(g_body, background=gauge_card.bg_color)
        g_footer.pack(fill="x", padx=12, pady=(0, 10))
        tk.Label(g_footer, text="Cluster: prod-us-east-1", font=("Segoe UI", 8), fg=pal.fg_subtle, bg=gauge_card.bg_color).pack(side="left")
        Badge(g_footer, text="OPTIMAL", color=pal.success, height=18).pack(side="right")

        # Telemetry Chart Card
        chart_card = Card(mid_row, title="Network Throughput & IO", width=620, height=240, rx=12, ry=12, elevation=6)
        chart_card.pack(side="left", fill="both", expand=True, padx=(8, 6))

        ch_body = chart_card.body
        self._chart = TelemetryChart(ch_body, width=580, height=170)
        self._chart.pack(fill="both", expand=True, padx=6, pady=4)

        # Bottom Row: Incident Feed Table & Quick Action Controls
        bot_row = tk.Frame(self, background=pal.bg)
        bot_row.pack(fill="both", expand=True, padx=24, pady=(8, 18))

        # Incident / Event Table
        tbl_card = Card(bot_row, title="Recent Cluster Events & Incidents", width=580, height=220, rx=12, ry=12, elevation=6)
        tbl_card.pack(side="left", fill="both", expand=True, padx=(6, 8))

        tbl_body = tbl_card.body
        table_columns = [
            {"id": "time", "name": "Time", "width": 85, "align": "left"},
            {"id": "level", "name": "Level", "width": 80, "align": "center"},
            {"id": "service", "name": "Service", "width": 120, "align": "left"},
            {"id": "event", "name": "Event Description", "width": 260, "align": "left"},
            {"id": "latency", "name": "Latency", "width": 75, "align": "right"},
        ]
        table_rows = [
            {"time": "15:24:02", "level": "INFO", "service": "auth-gateway", "event": "OIDC Token refreshed cleanly", "latency": "12 ms"},
            {"time": "15:23:48", "level": "WARN", "service": "ingestion-worker-4", "event": "Kafka Consumer rebalancing partition 2", "latency": "48 ms"},
            {"time": "15:23:15", "level": "INFO", "service": "vector-search", "event": "HNSW index compaction completed", "latency": "14 ms"},
            {"time": "15:22:50", "level": "INFO", "service": "billing-api", "event": "Stripe webhook 200 OK acknowledged", "latency": "18 ms"},
            {"time": "15:22:11", "level": "CRIT", "service": "node-pool-c", "event": "Node memory pressure above 85%", "latency": "112 ms"},
        ]
        self._table = Table(
            tbl_body,
            columns=table_columns,
            data=table_rows,
            height=160,
            row_height=28,
            header_height=30,
            elevation=0,
        )
        self._table.pack(fill="both", expand=True, padx=6, pady=4)

        # Quick Control Card
        ctrl_card = Card(bot_row, title="Diagnostics & Policies", width=320, height=220, rx=12, ry=12, elevation=6)
        ctrl_card.pack(side="right", fill="y", padx=(8, 6))

        c_body = ctrl_card.body
        seg_box = tk.Frame(c_body, background=ctrl_card.bg_color)
        seg_box.pack(fill="x", padx=12, pady=(4, 8))

        self._seg_btn = SegmentedButton(
            seg_box,
            values=["15m", "1h", "24h", "7d"],
            default_value="1h",
            width=270,
            height=28,
        )
        self._seg_btn.pack()

        sw_row = tk.Frame(c_body, background=ctrl_card.bg_color)
        sw_row.pack(fill="x", padx=12, pady=4)
        tk.Label(sw_row, text="Auto-Heal Nodes", font=("Segoe UI", 9), fg=pal.fg, bg=ctrl_card.bg_color).pack(side="left")
        self._sw_heal = Switch(sw_row, width=44, height=24, is_on=True)
        self._sw_heal.pack(side="right")

        sw_row2 = tk.Frame(c_body, background=ctrl_card.bg_color)
        sw_row2.pack(fill="x", padx=12, pady=4)
        tk.Label(sw_row2, text="Dynamic Rate-Limiting", font=("Segoe UI", 9), fg=pal.fg, bg=ctrl_card.bg_color).pack(side="left")
        self._sw_rate = Switch(sw_row2, width=44, height=24, is_on=False)
        self._sw_rate.pack(side="right")

        btn_row = tk.Frame(c_body, background=ctrl_card.bg_color)
        btn_row.pack(fill="x", padx=12, pady=(8, 10))

        self._btn_flush = Button(btn_row, text="Flush Cache", width=125, height=28, command=self._flush_cache)
        self._btn_flush.pack(side="left", padx=(0, 4))

        self._btn_audit = Button(btn_row, text="Run Audit", width=125, height=28, command=self._run_audit)
        self._btn_audit.pack(side="right", padx=(4, 0))

        cascade_bg_to_children(self, pal.bg)

    def _on_change_theme(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg)

    def _toggle_streaming(self) -> None:
        self._is_streaming = not self._is_streaming
        txt = "Streaming: ON" if self._is_streaming else "Streaming: PAUSED"
        self._live_btn.set_text(txt)

    def _flush_cache(self) -> None:
        tb.clear_all_caches()
        self._table.insert_row(0, {
            "time": time.strftime("%H:%M:%S"),
            "level": "INFO",
            "service": "cache-mgr",
            "event": "Blend2D font & surface caches cleared",
            "latency": "2 ms",
        })

    def _run_audit(self) -> None:
        self._table.insert_row(0, {
            "time": time.strftime("%H:%M:%S"),
            "level": "WARN",
            "service": "security-bot",
            "event": "Cluster node compliance check in progress",
            "latency": "35 ms",
        })

    def _start_data_stream(self) -> None:
        if self._is_streaming:
            self._clock_lbl.configure(text=time.strftime("%H:%M:%S UTC"))

            # Jitter gauge metrics
            cpu = max(10, min(95, int(self._cpu_gauge._value + random.uniform(-4, 4))))
            ram = max(40, min(90, int(self._ram_gauge._value + random.uniform(-2, 2))))
            gpu = max(15, min(80, int(self._gpu_gauge._value + random.uniform(-5, 5))))

            self._cpu_gauge.set_value(cpu)
            self._cpu_lbl.configure(text=f"CPU\n{cpu}%")
            self._ram_gauge.set_value(ram)
            self._ram_lbl.configure(text=f"RAM\n{ram}%")
            self._gpu_gauge.set_value(gpu)
            self._gpu_lbl.configure(text=f"GPU\n{gpu}%")

            # Push live telemetry chart data
            v1 = max(10.0, min(95.0, self._chart._series1[-1] + random.uniform(-8.0, 8.0)))
            v2 = max(5.0, min(85.0, self._chart._series2[-1] + random.uniform(-6.0, 6.0)))
            self._chart.push_data(v1, v2)

        if self._is_streaming:
            self._timer_id = self.after(1000, self._start_data_stream)

    def destroy(self) -> None:
        self._is_streaming = False
        if self._timer_id:
            try:
                self.after_cancel(self._timer_id)
                self._timer_id = None
            except Exception:
                pass
        super().destroy()


def main():
    root = tk.Tk()
    root.title("tkblend Telemetry & Analytics Dashboard")
    root.geometry("1020x720")
    root.minsize(880, 600)

    ScalingTracker.activate_high_dpi_awareness()
    set_theme("dark")

    app = AnalyticsDashboard(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
