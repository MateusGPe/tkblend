#!/usr/bin/env python3
"""
tkblend Developer Reference: Custom Vector Widget Cookbook.
Demonstrates:
  - How to build brand new, zero-TTK pure Blend2D vector widgets from scratch by subclassing BaseControl
  - High-DPI coordinate scaling with ScalingTracker
  - Zero-copy direct blitting to Tk window drawables
  - Automatic dynamic theming with get_theme() and palette inheritance
  - 3 Production-ready Custom Widgets:
      1. RadarChart: Multi-axis spider/radar chart with polygon fill
      2. SpeedometerGauge: Semi-circular analog gauge with needle & glowing ticks
      3. StepProgressBar: Multi-step wizard indicator with vector checkmarks
"""

from __future__ import annotations

import math
import sys
import tkinter as tk
from pathlib import Path as FilePath
from typing import Optional, List, Dict, Tuple, Callable

# Ensure project root is in sys.path
PROJECT_ROOT = FilePath(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkblend as tb
from tkblend import (
    BaseControl,
    Card,
    Button,
    Slider,
    OptionMenu,
    Surface,
    Path,
    LinearGradient,
    RadialGradient,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    ScalingTracker,
)
from tkblend.theme import Palette, resolve_color_failsafe, blend_color_hex
from tkblend.font import parse_font
from tkblend.widgets.utils import compute_text_baseline_y


# ==============================================================================
# Custom Widget 1: Multi-Axis Radar / Spider Chart
# ==============================================================================
class RadarChart(BaseControl):
    """Custom Blend2D multi-axis radar chart widget powered by BaseControl."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        categories: Optional[List[str]] = None,
        values: Optional[List[float]] = None,
        size: int = 240,
        color: Optional[str] = None,
        **kwargs,
    ):
        self._categories = categories or ["Speed", "Power", "Defense", "Agility", "Stamina", "Magic"]
        self._values = values or [80.0, 95.0, 60.0, 85.0, 70.0, 90.0]
        self._color = color
        super().__init__(master=master, width=size, height=size, takefocus=False, **kwargs)
        self.controller.set_on_paint(self._paint_wrapper)

    def _paint_wrapper(self, surf: Surface) -> None:
        pal = get_theme()
        scale = ScalingTracker.get_scaling_factor(self)
        surf.clear(self.outer_bg)
        self.render(surf, pal, surf.width, surf.height, scale)

    def set_values(self, vals: List[float]) -> None:
        self._values = list(vals)
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        cx = w / 2.0
        cy = h / 2.0
        r = min(cx, cy) - 25.0 * s
        n = len(self._categories)
        if n < 3:
            return

        col = resolve_color_failsafe(self._color or pal.primary, palette=pal)
        border_col = resolve_color_failsafe(pal.card_border, palette=pal)

        # 1. Concentric Web Rings
        rings = 4
        for ring in range(1, rings + 1):
            ring_r = r * (ring / float(rings))
            ring_path = Path()
            for i in range(n):
                angle = (i / float(n)) * 2.0 * math.pi - (math.pi / 2.0)
                px = cx + math.cos(angle) * ring_r
                py = cy + math.sin(angle) * ring_r
                if i == 0:
                    ring_path.move_to(px, py)
                else:
                    ring_path.line_to(px, py)
            ring_path.close()
            surf.stroke_path(ring_path, border_col, stroke_width=1.0 * s)

        # 2. Spoke Lines and Labels
        font_sz = 9.0 * s
        for i in range(n):
            angle = (i / float(n)) * 2.0 * math.pi - (math.pi / 2.0)
            px = cx + math.cos(angle) * r
            py = cy + math.sin(angle) * r
            surf.stroke_line(cx, cy, px, py, border_col, stroke_width=1.0 * s)

            # Category Text Label
            lx = cx + math.cos(angle) * (r + 14.0 * s)
            ly = cy + math.sin(angle) * (r + 14.0 * s)
            surf.draw_text(
                self._categories[i],
                lx,
                compute_text_baseline_y(ly, font_sz),
                font_size=font_sz,
                color=pal.text_muted,
                bold=True,
                align="center",
            )

        # 3. Data Polygon
        poly_path = Path()
        data_pts = []
        for i in range(n):
            val = self._values[i] if i < len(self._values) else 50.0
            val_r = r * (max(0.0, min(100.0, val)) / 100.0)
            angle = (i / float(n)) * 2.0 * math.pi - (math.pi / 2.0)
            px = cx + math.cos(angle) * val_r
            py = cy + math.sin(angle) * val_r
            data_pts.append((px, py))
            if i == 0:
                poly_path.move_to(px, py)
            else:
                poly_path.line_to(px, py)
        poly_path.close()

        # Fill and stroke
        surf.fill_path(poly_path, blend_color_hex(col, "#00000000", 0.35))
        surf.stroke_path(poly_path, col, stroke_width=2.5 * s)

        # Vertex Dots
        for px, py in data_pts:
            surf.fill_circle(px, py, 4.0 * s, col)
            surf.stroke_circle(px, py, 4.0 * s, pal.card_bg, stroke_width=1.5 * s)


# ==============================================================================
# Custom Widget 2: Speedometer Analog Gauge
# ==============================================================================
class SpeedometerGauge(BaseControl):
    """Analog speedometer dial with needle pointer and tick marks."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 240,
        value: float = 65.0,
        max_speed: float = 180.0,
        unit: str = "km/h",
        **kwargs,
    ):
        self._value = value
        self._max_speed = max_speed
        self._unit = unit
        super().__init__(master=master, width=size, height=int(size * 0.75), takefocus=False, **kwargs)
        self.controller.set_on_paint(self._paint_wrapper)

    def _paint_wrapper(self, surf: Surface) -> None:
        pal = get_theme()
        scale = ScalingTracker.get_scaling_factor(self)
        surf.clear(self.outer_bg)
        self.render(surf, pal, surf.width, surf.height, scale)

    def set_value(self, val: float) -> None:
        self._value = max(0.0, min(self._max_speed, float(val)))
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        cx = w / 2.0
        cy = h - 22.0 * s
        r = min(w / 2.0 - 24.0 * s, h - 34.0 * s)
        if r <= 10.0:
            return

        # Track thickness
        track_w = 8.0 * s

        # Background Arc Track (Semi-circle: -180 deg to 0 deg in radians)
        surf.stroke_arc(cx, cy, r, -math.pi, math.pi, pal.track_bg, stroke_width=track_w)

        # Redline Warning Arc (top speed zone, last 20% of scale)
        redline_val = self._max_speed * 0.8
        redline_start_ang = -math.pi + math.pi * (redline_val / self._max_speed)
        redline_sweep = math.pi - math.pi * (redline_val / self._max_speed)
        danger_col = resolve_color_failsafe(pal.danger, palette=pal, fallback="#ef4444")
        surf.stroke_arc(cx, cy, r, redline_start_ang, redline_sweep, danger_col, stroke_width=track_w)

        # Active Progress Arc
        fraction = min(1.0, max(0.0, self._value / max(1.0, self._max_speed)))
        active_sweep = math.pi * fraction
        if active_sweep > 0.01:
            primary_col = resolve_color_failsafe(pal.primary, palette=pal, fallback="#3b82f6")
            surf.stroke_arc(cx, cy, r, -math.pi, active_sweep, primary_col, stroke_width=track_w)

        # Tick marks & dial numbers
        major_step = 30 if self._max_speed <= 180 else 40
        num_major = int(self._max_speed // major_step)
        muted_col = resolve_color_failsafe(pal.text_muted, palette=pal, fallback="#71717a")
        fg_col = resolve_color_failsafe(pal.fg, palette=pal, fallback="#e4e4e7")

        for val in range(0, int(self._max_speed) + 1, 10):
            tf = val / self._max_speed
            ang = -math.pi + math.pi * tf
            is_major = (val % major_step == 0)
            inner_r = r - (16.0 if is_major else 10.0) * s
            outer_r = r - 5.0 * s

            x1 = cx + math.cos(ang) * inner_r
            y1 = cy + math.sin(ang) * inner_r
            x2 = cx + math.cos(ang) * outer_r
            y2 = cy + math.sin(ang) * outer_r

            tick_col = danger_col if val >= redline_val else (fg_col if is_major else muted_col)
            surf.stroke_line(x1, y1, x2, y2, tick_col, stroke_width=(2.0 if is_major else 1.0) * s)

            # Major numeric scale label
            if is_major:
                lbl_r = r - 26.0 * s
                lx = cx + math.cos(ang) * lbl_r
                ly = cy + math.sin(ang) * lbl_r
                font_sz = 8.5 * s
                surf.draw_text(
                    str(val),
                    lx,
                    compute_text_baseline_y(ly, font_sz),
                    font_size=font_sz,
                    color=tick_col,
                    align="center",
                )

        # Needle pointer with counterweight
        needle_ang = -math.pi + active_sweep
        tip_r = r - 12.0 * s
        nx = cx + math.cos(needle_ang) * tip_r
        ny = cy + math.sin(needle_ang) * tip_r
        bx = cx - math.cos(needle_ang) * (12.0 * s)
        by = cy - math.sin(needle_ang) * (12.0 * s)

        needle_col = danger_col
        surf.stroke_line(bx, by, nx, ny, needle_col, stroke_width=3.0 * s)

        # Center Pivot Hub
        surf.fill_circle(cx, cy, 7.0 * s, needle_col)
        card_bg_col = resolve_color_failsafe(pal.card_bg, palette=pal, fallback="#1e1e2e")
        surf.fill_circle(cx, cy, 3.5 * s, card_bg_col)

        # Center Text readout
        readout_font_sz = 14.0 * s
        unit_font_sz = 9.0 * s
        readout = f"{int(round(self._value))}"
        surf.draw_text(
            readout,
            cx,
            compute_text_baseline_y(cy - 24.0 * s, readout_font_sz),
            font_size=readout_font_sz,
            color=fg_col,
            bold=True,
            align="center",
        )
        surf.draw_text(
            self._unit,
            cx,
            compute_text_baseline_y(cy - 12.0 * s, unit_font_sz),
            font_size=unit_font_sz,
            color=muted_col,
            align="center",
        )


# ==============================================================================
# Custom Widget 3: Step Progress Bar
# ==============================================================================
class StepProgressBar(BaseControl):
    """Multi-step wizard indicator with connected vector nodes."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        steps: Optional[List[str]] = None,
        current_step: int = 1,
        width: int = 400,
        height: int = 54,
        **kwargs,
    ):
        self._steps = steps or ["Account", "Profile", "Billing", "Review"]
        self._current = current_step
        super().__init__(master=master, width=width, height=height, takefocus=False, **kwargs)
        self.controller.set_on_paint(self._paint_wrapper)

    def _paint_wrapper(self, surf: Surface) -> None:
        pal = get_theme()
        scale = ScalingTracker.get_scaling_factor(self)
        surf.clear(self.outer_bg)
        self.render(surf, pal, surf.width, surf.height, scale)

    def set_step(self, step_idx: int) -> None:
        self._current = max(0, min(len(self._steps) - 1, step_idx))
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        n = len(self._steps)
        if n < 2:
            return

        pad_x = 35.0 * s
        node_y = 18.0 * s
        node_r = 12.0 * s
        usable_w = w - pad_x * 2.0
        step_w = usable_w / (n - 1)

        # Connecting track
        surf.stroke_line(pad_x, node_y, w - pad_x, node_y, pal.track_bg, stroke_width=3.0 * s)

        # Completed line
        if self._current > 0:
            comp_x = pad_x + self._current * step_w
            surf.stroke_line(pad_x, node_y, comp_x, node_y, pal.primary, stroke_width=3.0 * s)

        lbl_font_sz = 9.0 * s

        # Step Nodes
        for i, name in enumerate(self._steps):
            nx = pad_x + i * step_w
            is_done = (i < self._current)
            is_curr = (i == self._current)

            if is_done or is_curr:
                surf.fill_circle(nx, node_y, node_r, pal.primary)
                surf.stroke_circle(nx, node_y, node_r, pal.card_bg, stroke_width=2.0 * s)
                node_num = "✓" if is_done else str(i + 1)
                surf.draw_text(
                    node_num,
                    nx,
                    compute_text_baseline_y(node_y, 10.0 * s),
                    font_size=10.0 * s,
                    color="#FFFFFF",
                    bold=True,
                    align="center",
                )
            else:
                surf.fill_circle(nx, node_y, node_r, pal.track_bg)
                surf.stroke_circle(nx, node_y, node_r, pal.card_border, stroke_width=1.5 * s)
                surf.draw_text(
                    str(i + 1),
                    nx,
                    compute_text_baseline_y(node_y, 10.0 * s),
                    font_size=10.0 * s,
                    color=pal.text_muted,
                    bold=True,
                    align="center",
                )

            # Step Label text
            lbl_y = compute_text_baseline_y(node_y + node_r + 14.0 * s, lbl_font_sz)
            surf.draw_text(
                name,
                nx,
                lbl_y,
                font_size=lbl_font_sz,
                color=pal.fg if (is_done or is_curr) else pal.text_muted,
                bold=is_curr,
                align="center",
            )


# ==============================================================================
# Custom Widget Cookbook Showcase App
# ==============================================================================
class CustomWidgetCookbook(tk.Frame):
    """Interactive demo for developer custom widgets."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Header Card
        header = Card(self, height=68)
        header.pack(fill="x", padx=16, pady=(16, 8))

        hdr_inner = tk.Frame(header, bg=pal.card_bg)
        hdr_inner.pack(fill="both", expand=True, padx=18, pady=(10, 14))

        tk.Label(
            hdr_inner,
            text="🧪 Custom Vector Widget Cookbook",
            font=("sans-serif", 15, "bold"),
            bg=pal.card_bg,
            fg=pal.fg,
        ).pack(side="left")

        self._theme_opt = OptionMenu(
            hdr_inner,
            values=sorted(get_available_themes()),
            current_value=pal.name,
            command=self._on_theme_change,
            width=130,
            height=30,
        )
        self._theme_opt.pack(side="right")

        # Main Grid
        grid_frame = tk.Frame(self, bg=pal.bg)
        grid_frame.pack(fill="both", expand=True, padx=16, pady=6)

        # Card 1: Radar Chart
        c1 = Card(grid_frame)
        c1.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        c1_inner = tk.Frame(c1, bg=pal.card_bg)
        c1_inner.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(c1_inner, text="1. Radar / Spider Chart", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=(4, 4))
        self._radar = RadarChart(c1_inner, size=210)
        self._radar.pack(padx=10, pady=6)

        # Card 2: Speedometer
        c2 = Card(grid_frame)
        c2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        c2_inner = tk.Frame(c2, bg=pal.card_bg)
        c2_inner.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(c2_inner, text="2. Speedometer Gauge", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=(4, 4))
        self._speedo = SpeedometerGauge(c2_inner, size=210, value=75.0)
        self._speedo.pack(padx=10, pady=4)

        speed_slider = Slider(c2_inner, from_=0, to=180, value=75, command=self._speedo.set_value, width=180)
        speed_slider.pack(pady=4)

        # Card 3: Step Progress Bar
        c3 = Card(grid_frame)
        c3.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)

        c3_inner = tk.Frame(c3, bg=pal.card_bg)
        c3_inner.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(c3_inner, text="3. Multi-Step Wizard Indicator", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=(4, 4))
        self._step_bar = StepProgressBar(c3_inner, current_step=2, height=60)
        self._step_bar.pack(fill="x", padx=20, pady=6)

        step_btn_row = tk.Frame(c3_inner, bg=pal.card_bg)
        step_btn_row.pack(pady=(2, 8))

        Button(step_btn_row, text="◀ Prev Step", width=95, height=28, command=lambda: self._step_bar.set_step(self._step_bar._current - 1)).pack(side="left", padx=4)
        Button(step_btn_row, text="Next Step ▶", width=95, height=28, command=lambda: self._step_bar.set_step(self._step_bar._current + 1)).pack(side="left", padx=4)

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)
        grid_frame.rowconfigure(0, weight=1)
        grid_frame.rowconfigure(1, weight=1)

        cascade_bg_to_children(self, pal.bg, palette=pal)

    def _on_theme_change(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg, palette=pal)
        self._radar.request_redraw()
        self._speedo.request_redraw()
        self._step_bar.request_redraw()


def main():
    root = tk.Tk()
    root.title("tkblend - Custom Widget Cookbook")
    root.geometry("880x640")
    root.minsize(740, 520)

    app = CustomWidgetCookbook(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
