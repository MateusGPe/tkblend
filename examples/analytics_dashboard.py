#!/usr/bin/env python3
"""
tkblend Showcase: Modern SaaS & System Telemetry Analytics Dashboard.
Demonstrates:
  - Zero-TTK pure Blend2D vector widgets (Card, CircularProgress, Table, Switch, SegmentedButton, etc.)
  - High-performance live NativeBlitCanvas vector charts with multi-series Bezier curves and gradient fills
  - Dynamic runtime palette switching across 13+ themes
  - Real-time data streaming and animated gauge metrics
"""

from __future__ import annotations

import math
import random
import sys
import tkinter as tk
from pathlib import Path as FilePath
from typing import Optional, List, Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = FilePath(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkblend as tb
from tkblend import (
    Card,
    CircularProgress,
    Table,
    Button,
    Switch,
    SegmentedButton,
    OptionMenu,
    Badge,
    Sparkline,
    NativeBlitCanvas,
    Surface,
    LinearGradient,
    Path,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    ScalingTracker,
)


class TelemetryChart(NativeBlitCanvas):
    """High-performance multi-series vector telemetry chart with Bezier curves."""

    def __init__(self, master: tk.Misc, width: int = 600, height: int = 240, **kwargs):
        self._max_pts = 35
        self._data_primary: List[float] = [
            50.0 + 20.0 * math.sin(i * 0.3) + random.uniform(-4, 4) for i in range(self._max_pts)
        ]
        self._data_secondary: List[float] = [
            35.0 + 15.0 * math.cos(i * 0.25) + random.uniform(-3, 3) for i in range(self._max_pts)
        ]
        self._hover_x: Optional[float] = None
        self._hover_idx: Optional[int] = None

        super().__init__(master, width=width, height=height, on_paint=self._paint, **kwargs)
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)

    def _on_mouse_move(self, event: tk.Event) -> None:
        self._hover_x = float(event.x)
        s = ScalingTracker.get_scaling_factor(self)
        pad_l = 45.0 * s
        pad_r = 15.0 * s
        w = max(1.0, float(self.winfo_width()) - pad_l - pad_r)
        rel_x = max(0.0, min(w, event.x - pad_l))
        self._hover_idx = int(round((rel_x / w) * (len(self._data_primary) - 1)))
        self.request_redraw()

    def _on_mouse_leave(self, _event: tk.Event) -> None:
        self._hover_x = None
        self._hover_idx = None
        self.request_redraw()

    def push_data(self, val1: float, val2: float) -> None:
        self._data_primary.append(val1)
        if len(self._data_primary) > self._max_pts:
            self._data_primary.pop(0)

        self._data_secondary.append(val2)
        if len(self._data_secondary) > self._max_pts:
            self._data_secondary.pop(0)

        self.request_redraw()

    def _paint(self, surf: Surface) -> None:
        if len(self._data_primary) < 2:
            return

        pal = get_theme()
        s = ScalingTracker.get_scaling_factor(self)
        w = float(surf.width)
        h = float(surf.height)

        surf.clear(pal.card_bg)

        pad_l = 45.0 * s
        pad_r = 15.0 * s
        pad_t = 20.0 * s
        pad_b = 30.0 * s

        plot_w = max(10.0, w - pad_l - pad_r)
        plot_h = max(10.0, h - pad_t - pad_b)

        # 1. Grid lines and Y-axis labels
        grid_lines = 4
        for i in range(grid_lines + 1):
            y_val = pad_t + (plot_h / grid_lines) * i
            surf.stroke_line(pad_l, y_val, w - pad_r, y_val, pal.card_border, stroke_width=1.0 * s)
            lbl_val = int(100 - (100 / grid_lines) * i)
            surf.draw_text(
                f"{lbl_val}%",
                pad_l - 8.0 * s,
                y_val + 3.0 * s,
                font_size=9.0 * s,
                color=pal.text_muted,
                align="right",
            )

        # Helper to compute points
        def get_points(series: List[float]) -> List[tuple[float, float]]:
            pts = []
            n = len(series)
            for idx, val in enumerate(series):
                x = pad_l + (idx / max(1, n - 1)) * plot_w
                norm_y = max(0.0, min(100.0, val)) / 100.0
                y = (pad_t + plot_h) - norm_y * plot_h
                pts.append((x, y))
            return pts

        pts1 = get_points(self._data_primary)
        pts2 = get_points(self._data_secondary)

        # 2. Draw Area and Curves
        bottom_y = pad_t + plot_h
        self._draw_area_and_curve(surf, pts2, pal.secondary, bottom_y, s)
        self._draw_area_and_curve(surf, pts1, pal.primary, bottom_y, s)

        # 3. Hover indicator
        if self._hover_idx is not None and 0 <= self._hover_idx < len(pts1):
            hx1, hy1 = pts1[self._hover_idx]
            hx2, hy2 = pts2[self._hover_idx]

            surf.stroke_line(hx1, pad_t, hx1, bottom_y, pal.primary, stroke_width=1.0 * s)
            surf.fill_circle(hx1, hy1, 4.5 * s, pal.primary)
            surf.stroke_circle(hx1, hy1, 4.5 * s, pal.card_bg, stroke_width=1.5 * s)
            surf.fill_circle(hx2, hy2, 4.0 * s, pal.secondary)
            surf.stroke_circle(hx2, hy2, 4.0 * s, pal.card_bg, stroke_width=1.5 * s)

            val1 = self._data_primary[self._hover_idx]
            val2 = self._data_secondary[self._hover_idx]
            tip_text = f"In: {val1:.1f}% | Out: {val2:.1f}%"
            tip_w = 120.0 * s
            tip_h = 22.0 * s
            tip_x = max(pad_l, min(w - pad_r - tip_w, hx1 - tip_w / 2.0))
            tip_y = max(pad_t, min(bottom_y - tip_h - 10.0 * s, hy1 - tip_h - 8.0 * s))

            surf.fill_rounded_rect(tip_x, tip_y, tip_w, tip_h, 4.0 * s, 4.0 * s, pal.bg)
            surf.stroke_rounded_rect(tip_x, tip_y, tip_w, tip_h, 4.0 * s, 4.0 * s, pal.card_border, stroke_width=1.0 * s)
            surf.draw_text(
                tip_text,
                tip_x + tip_w / 2.0,
                tip_y + tip_h / 2.0 + 3.0 * s,
                font_size=9.0 * s,
                color=pal.fg,
                align="center",
            )

    def _draw_area_and_curve(self, surf: Surface, pts: List[tuple[float, float]], color: str, bottom_y: float, s: float) -> None:
        if len(pts) < 2:
            return

        # Build smooth Bezier path
        path = Path()
        path.move_to(pts[0][0], pts[0][1])
        for i in range(len(pts) - 1):
            p0 = pts[max(0, i - 1)]
            p1 = pts[i]
            p2 = pts[i + 1]
            p3 = pts[min(len(pts) - 1, i + 2)]

            cp1x = p1[0] + (p2[0] - p0[0]) / 6.0
            cp1y = p1[1] + (p2[1] - p0[1]) / 6.0
            cp2x = p2[0] - (p3[0] - p1[0]) / 6.0
            cp2y = p2[1] - (p3[1] - p1[1]) / 6.0
            path.cubic_to(cp1x, cp1y, cp2x, cp2y, p2[0], p2[1])

        # Area gradient fill
        area_path = Path()
        area_path.move_to(pts[0][0], bottom_y)
        area_path.line_to(pts[0][0], pts[0][1])
        for i in range(len(pts) - 1):
            p0 = pts[max(0, i - 1)]
            p1 = pts[i]
            p2 = pts[i + 1]
            p3 = pts[min(len(pts) - 1, i + 2)]

            cp1x = p1[0] + (p2[0] - p0[0]) / 6.0
            cp1y = p1[1] + (p2[1] - p0[1]) / 6.0
            cp2x = p2[0] - (p3[0] - p1[0]) / 6.0
            cp2y = p2[1] - (p3[1] - p1[1]) / 6.0
            area_path.cubic_to(cp1x, cp1y, cp2x, cp2y, p2[0], p2[1])
        area_path.line_to(pts[-1][0], bottom_y)
        area_path.close()

        min_y = min(p[1] for p in pts)
        grad = LinearGradient(0, min_y, 0, bottom_y)
        grad.add_stop(0.0, color, alpha=0.35)
        grad.add_stop(1.0, color, alpha=0.0)
        surf.fill_path(area_path, grad)

        # Stroke curve
        surf.stroke_path(path, color, stroke_width=2.5 * s)


class AnalyticsDashboard(tk.Frame):
    """Modern SaaS and System Telemetry Analytics Dashboard."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._is_streaming = True
        self._stream_job: Optional[str] = None
        self._build_ui()
        self._start_data_stream()

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Top Header Bar Card
        header_card = Card(self, height=68)
        header_card.pack(fill="x", padx=16, pady=(16, 8))

        hdr_content = tk.Frame(header_card, bg=pal.card_bg)
        hdr_content.pack(fill="both", expand=True, padx=18, pady=(10, 14))

        title_lbl = tk.Label(
            hdr_content,
            text="⚡ HyperScale Telemetry Analytics",
            font=("sans-serif", 15, "bold"),
            bg=pal.card_bg,
            fg=pal.fg,
        )
        title_lbl.pack(side="left", pady=4)

        # Live Status badge
        self._status_badge = Badge(hdr_content, text="LIVE STREAM", variant="success", dot=True)
        self._status_badge.pack(side="left", padx=10)

        # Theme Selector
        theme_names = sorted(get_available_themes())
        self._theme_opt = OptionMenu(
            hdr_content,
            values=theme_names,
            current_value=pal.name,
            command=self._on_change_theme,
            width=140,
            height=30,
        )
        self._theme_opt.pack(side="right", padx=(8, 0))

        # Streaming Toggle
        self._stream_switch = Switch(
            hdr_content,
            is_checked=True,
            command=self._toggle_streaming,
            width=48,
            height=26,
        )
        self._stream_switch.pack(side="right", padx=8)

        lbl_stream = tk.Label(hdr_content, text="Live Sync:", font=("sans-serif", 10), bg=pal.card_bg, fg=pal.text_muted)
        lbl_stream.pack(side="right", padx=(8, 2))

        # KPI Metrics Row
        kpi_frame = tk.Frame(self, bg=pal.bg)
        kpi_frame.pack(fill="x", padx=16, pady=6)

        kpis = [
            ("Total Requests", "4.82 M", "+12.4%", "primary", [40.0, 48.0, 55.0, 62.0, 70.0, 68.0, 78.0, 85.0, 92.0]),
            ("Avg Latency", "18.4 ms", "-3.2%", "success", [32.0, 28.0, 26.0, 24.0, 22.0, 20.0, 19.0, 18.0, 18.0]),
            ("Memory Usage", "68.2 %", "+1.1%", "warning", [50.0, 52.0, 55.0, 60.0, 64.0, 66.0, 68.0, 67.0, 68.0]),
            ("Error Rate", "0.004 %", "-0.01%", "secondary", [12.0, 10.0, 8.0, 6.0, 5.0, 4.0, 4.0, 3.0, 4.0]),
        ]

        self._kpi_sparklines: List[Sparkline] = []
        for i, (name, val, diff, variant, spark_data) in enumerate(kpis):
            card = Card(kpi_frame, height=105)
            card.pack(side="left", fill="both", expand=True, padx=4 if i > 0 else (0, 4))

            inner = tk.Frame(card, bg=pal.card_bg)
            inner.pack(fill="both", expand=True, padx=16, pady=14)

            top_box = tk.Frame(inner, bg=pal.card_bg)
            top_box.pack(fill="x", pady=(2, 2))

            lbl_name = tk.Label(top_box, text=name, font=("sans-serif", 9), bg=pal.card_bg, fg=pal.text_muted)
            lbl_name.pack(side="left")

            badge = Badge(top_box, text=diff, variant="success" if ("+" in diff and "Req" in name) or ("-" in diff and "Lat" in name) else "primary", height=18, font_size=8)
            badge.pack(side="right")

            bot_box = tk.Frame(inner, bg=pal.card_bg)
            bot_box.pack(fill="both", expand=True, pady=(2, 4))

            lbl_val = tk.Label(bot_box, text=val, font=("sans-serif", 14, "bold"), bg=pal.card_bg, fg=pal.fg)
            lbl_val.pack(side="left", anchor="w")

            sp = Sparkline(bot_box, data=spark_data, width=80, height=28)
            sp.pack(side="right")
            self._kpi_sparklines.append(sp)

        # Middle Section: Chart + Radial Gauges
        mid_frame = tk.Frame(self, bg=pal.bg)
        mid_frame.pack(fill="both", expand=True, padx=16, pady=6)

        # Left: Main Chart Card
        chart_card = Card(mid_frame)
        chart_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        chart_inner = tk.Frame(chart_card, bg=pal.card_bg)
        chart_inner.pack(fill="both", expand=True, padx=18, pady=16)

        chart_hdr = tk.Frame(chart_inner, bg=pal.card_bg)
        chart_hdr.pack(fill="x", pady=(4, 4))

        tk.Label(chart_hdr, text="Network Throughput & IOPS", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(side="left")

        self._seg_filter = SegmentedButton(
            chart_hdr,
            values=["1H", "6H", "24H", "7D"],
            selected_value="1H",
            height=26,
            width=180,
        )
        self._seg_filter.pack(side="right")

        self._telemetry_chart = TelemetryChart(chart_inner, height=190)
        self._telemetry_chart.pack(fill="both", expand=True, pady=(2, 6))

        # Right: Gauges Card
        gauge_card = Card(mid_frame, width=250)
        gauge_card.pack(side="right", fill="y", padx=(6, 0))

        gauge_inner = tk.Frame(gauge_card, bg=pal.card_bg)
        gauge_inner.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(gauge_inner, text="Resource Saturation", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(pady=(4, 6))

        self._cpu_gauge = CircularProgress(gauge_inner, size=95, value=72.0, title="CPU Load", unit="%")
        self._cpu_gauge.pack(side="top", pady=4)

        self._mem_gauge = CircularProgress(gauge_inner, size=95, value=64.0, title="RAM Swap", unit="%")
        self._mem_gauge.pack(side="top", pady=4)

        # Bottom Section: Event Telemetry Table
        tbl_card = Card(self, height=185)
        tbl_card.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        tbl_inner = tk.Frame(tbl_card, bg=pal.card_bg)
        tbl_inner.pack(fill="both", expand=True, padx=18, pady=14)

        tbl_hdr = tk.Frame(tbl_inner, bg=pal.card_bg)
        tbl_hdr.pack(fill="x", pady=(4, 4))

        tk.Label(tbl_hdr, text="Live Node Cluster Telemetry & Incidents", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(side="left")

        btn_flush = Button(tbl_hdr, text="Flush Cache", width=90, height=24, command=self._flush_cache)
        btn_flush.pack(side="right", padx=4)

        btn_audit = Button(tbl_hdr, text="Run Audit", width=80, height=24, command=self._run_audit)
        btn_audit.pack(side="right", padx=4)

        table_cols = ["Node ID", "Region", "Status", "Load Index", "QPS Stream", "Uptime"]
        table_data = [
            ["worker-us-01", "us-east", "HEALTHY", "34.2%", "18,400", "99.99%"],
            ["worker-us-02", "us-west", "HEALTHY", "42.8%", "24,120", "99.98%"],
            ["worker-eu-01", "eu-central", "HEALTHY", "51.6%", "19,850", "100.0%"],
            ["worker-ap-01", "ap-east", "OPTIMAL", "28.4%", "12,300", "99.95%"],
            ["ingress-edge-1", "global", "HEALTHY", "62.1%", "74,900", "99.99%"],
        ]

        self._table = Table(tbl_inner, columns=table_cols, data=table_data, height=120)
        self._table.pack(fill="both", expand=True, pady=(2, 4))

        cascade_bg_to_children(self, pal.bg, palette=pal)

    def _on_change_theme(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg, palette=pal)
        self._telemetry_chart.request_redraw()
        for sp in self._kpi_sparklines:
            sp.request_redraw()
        self._cpu_gauge.request_redraw()
        self._mem_gauge.request_redraw()
        self._table.request_redraw()

    def _toggle_streaming(self, is_on: bool = True) -> None:
        self._is_streaming = self._stream_switch.is_checked
        if self._is_streaming:
            self._status_badge.text = "LIVE STREAM"
            self._status_badge.variant = "success"
            self._start_data_stream()
        else:
            self._status_badge.text = "PAUSED"
            self._status_badge.variant = "warning"
            if self._stream_job:
                self.after_cancel(self._stream_job)
                self._stream_job = None

    def _flush_cache(self) -> None:
        new_row = ["cache-evict-01", "cluster", "EVICTED", "12.0%", "0", "100.0%"]
        self._table.data = [new_row] + self._table.data

    def _run_audit(self) -> None:
        self._cpu_gauge.value = min(100.0, self._cpu_gauge.value + 5.0)
        self._mem_gauge.value = min(100.0, self._mem_gauge.value + 3.0)

    def _start_data_stream(self) -> None:
        if not self._is_streaming:
            return

        # Push random telemetry tick
        last1 = self._telemetry_chart._data_primary[-1]
        last2 = self._telemetry_chart._data_secondary[-1]

        v1 = max(10.0, min(95.0, last1 + random.uniform(-6.0, 6.0)))
        v2 = max(10.0, min(90.0, last2 + random.uniform(-5.0, 5.0)))
        self._telemetry_chart.push_data(v1, v2)

        # Update gauges
        self._cpu_gauge.value = max(15.0, min(98.0, self._cpu_gauge.value + random.uniform(-2.0, 2.0)))
        self._mem_gauge.value = max(20.0, min(95.0, self._mem_gauge.value + random.uniform(-1.5, 1.5)))

        # Update sparklines
        for sp in self._kpi_sparklines:
            d = sp.data
            d.append(max(5.0, min(100.0, d[-1] + random.uniform(-4.0, 4.0))))
            if len(d) > 15:
                d.pop(0)
            sp.data = d

        self._stream_job = self.after(350, self._start_data_stream)

    def destroy(self) -> None:
        if self._stream_job:
            self.after_cancel(self._stream_job)
            self._stream_job = None
        super().destroy()


def main():
    root = tk.Tk()
    root.title("tkblend - Modern Analytics Dashboard")
    root.geometry("980x720")
    root.minsize(800, 600)

    app = AnalyticsDashboard(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
