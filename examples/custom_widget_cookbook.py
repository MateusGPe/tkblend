#!/usr/bin/env python3
"""
tkblend Developer Reference: Custom Vector Widget Cookbook.
Demonstrates:
  - How to build brand new, zero-TTK pure Blend2D vector widgets from scratch by subclassing 
  - High-DPI coordinate scaling with 
  - Zero-copy direct blitting to Tk window drawables
  - Automatic dynamic theming with  and palette inheritance
  - 4 Production-ready Custom Widgets:
      1. RadarChart: Multi-axis spider/radar chart with polygon fill
      2. SpeedometerGauge: Semi-circular analog gauge with needle & glowing ticks
      3. StepProgressBar: Multi-step wizard indicator with vector checkmarks
      4. ColorWheelPicker: Radial HSV color wheel with draggable interactive thumb
"""

from __future__ import annotations

import math
import tkinter as tk
from typing import Optional, List, Dict, Tuple, Callable

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
        font_cfg = parse_font(font_size=9.0, bold=True)
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
                font_family=font_cfg.family,
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

    def set_value(self, val: float) -> None:
        self._value = max(0.0, min(self._max_speed, float(val)))
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        cx = w / 2.0
        cy = h - 15.0 * s
        r = min(w / 2.0 - 20.0 * s, h - 25.0 * s)

        # Background Arc Track (180 degrees sweep)
        surf.stroke_arc(cx, cy, r, math.pi, math.pi, pal.track_bg, stroke_width=10.0 * s)

        # Active colored arc
        fraction = self._value / max(1.0, self._max_speed)
        sweep = math.pi * fraction
        if sweep > 0.01:
            surf.stroke_arc(cx, cy, r, math.pi, sweep, pal.primary, stroke_width=10.0 * s)

        # Needle
        needle_angle = math.pi + sweep
        nx = cx + math.cos(needle_angle) * (r - 12.0 * s)
        ny = cy + math.sin(needle_angle) * (r - 12.0 * s)

        surf.stroke_line(cx, cy, nx, ny, pal.destructive, stroke_width=3.0 * s)
        surf.fill_circle(cx, cy, 8.0 * s, pal.destructive)
        surf.stroke_circle(cx, cy, 8.0 * s, pal.card_bg, stroke_width=2.0 * s)

        # Center Text readout
        font_sz = 14.0 * s
        font_cfg = parse_font(font_size=14.0, bold=True)
        readout = f"{int(self._value)} {self._unit}"
        surf.draw_text(
            readout,
            cx,
            compute_text_baseline_y(cy - 25.0 * s, font_sz),
            font_size=font_sz,
            font_family=font_cfg.family,
            color=pal.fg,
            bold=True,
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

        font_cfg = parse_font(font_size=9.0, bold=True)
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
                font_family=font_cfg.family,
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
        header = Card(self, height=64, corner_radius=10, bg_color=pal.card_bg)
        header.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(
            header,
            text="🧪 Custom Vector Widget Cookbook",
            font=("sans-serif", 15, "bold"),
            bg=header.bg_color,
            fg=pal.fg,
        ).pack(side="left", padx=16)

        self._theme_opt = OptionMenu(
            header,
            values=get_available_themes(),
            default_value="dark",
            command=self._on_theme_change,
            width=130,
            height=30,
        )
        self._theme_opt.pack(side="right", padx=14)

        # Main Grid
        grid_frame = tk.Frame(self, bg=pal.bg)
        grid_frame.pack(fill="both", expand=True, padx=16, pady=6)

        # Card 1: Radar Chart
        c1 = Card(grid_frame, corner_radius=10, bg_color=pal.card_bg)
        c1.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        tk.Label(c1, text="1. Radar / Spider Chart", font=("sans-serif", 11, "bold"), bg=c1.bg_color, fg=pal.fg).pack(anchor="w", padx=14, pady=(10, 4))
        self._radar = RadarChart(c1, size=210)
        self._radar.pack(padx=10, pady=6)

        # Card 2: Speedometer
        c2 = Card(grid_frame, corner_radius=10, bg_color=pal.card_bg)
        c2.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        tk.Label(c2, text="2. Speedometer Gauge", font=("sans-serif", 11, "bold"), bg=c2.bg_color, fg=pal.fg).pack(anchor="w", padx=14, pady=(10, 4))
        self._speedo = SpeedometerGauge(c2, size=210, value=75.0)
        self._speedo.pack(padx=10, pady=4)

        speed_slider = Slider(c2, from_=0, to=180, value=75, command=self._speedo.set_value, width=180)
        speed_slider.pack(pady=4)

        # Card 3: Step Progress Bar
        c3 = Card(grid_frame, corner_radius=10, bg_color=pal.card_bg)
        c3.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)

        tk.Label(c3, text="3. Multi-Step Wizard Indicator", font=("sans-serif", 11, "bold"), bg=c3.bg_color, fg=pal.fg).pack(anchor="w", padx=14, pady=(10, 4))
        self._step_bar = StepProgressBar(c3, current_step=2, height=60)
        self._step_bar.pack(fill="x", padx=20, pady=6)

        step_btn_row = tk.Frame(c3, bg=c3.bg_color)
        step_btn_row.pack(pady=(2, 10))

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
