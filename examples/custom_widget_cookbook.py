#!/usr/bin/env python3
"""
tkblend Developer Reference: Custom Vector Widget Cookbook.
Demonstrates:
  - How to build brand new, zero-TTK pure Blend2D vector widgets from scratch by subclassing `Widget`
  - High-DPI coordinate scaling with `ScalingTracker`
  - Zero-copy blitting to Tkinter `PhotoImage`
  - Automatic dynamic theming with `get_theme()` and palette inheritance
  - 4 Production-ready Custom Widgets:
      1. RadarChartWidget: Multi-axis spider/radar chart with polygon fill
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
    Widget,
    Card,
    Button,
    Slider,
    OptionMenu,
    Path,
    LinearGradient,
    RadialGradient,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    ScalingTracker,
)
from tkblend.widgets.drawing import draw_vector_checkmark


# ==============================================================================
# Custom Widget 1: Multi-Axis Radar / Spider Chart
# ==============================================================================
class RadarChartWidget(Widget):
    """Custom Blend2D multi-axis radar chart widget."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        categories: Optional[List[str]] = None,
        values: Optional[List[float]] = None,
        size: int = 240,
        color: Optional[str] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._categories = categories or ["Speed", "Power", "Defense", "Agility", "Stamina", "Magic"]
        self._values = values or [80.0, 95.0, 60.0, 85.0, 70.0, 90.0]
        self._explicit_color = color
        super().__init__(master=master, width=size, height=size, bg=parent_bg, **kwargs)

    def set_values(self, values: List[float]) -> None:
        self._values = list(values)
        self.render()

    def render(self) -> None:
        if self._surface is None or self._photo is None:
            return

        pal = get_theme()
        s = self._scale
        w = float(self._widget_w)
        h = float(self._widget_h)
        cx = w / 2.0
        cy = h / 2.0
        max_r = min(cx, cy) - 44.0 * s

        self._surface.clear(self._parent_bg)

        n = len(self._categories)
        if n < 3:
            return

        # 1. Concentric Grid Rings
        rings = 4
        for r_idx in range(1, rings + 1):
            r = (r_idx / rings) * max_r
            ring_path = Path()
            for i in range(n):
                ang = i * (2.0 * math.pi / n) - (math.pi / 2.0)
                px = cx + r * math.cos(ang)
                py = cy + r * math.sin(ang)
                if i == 0:
                    ring_path.move_to(px, py)
                else:
                    ring_path.line_to(px, py)
            ring_path.close()
            self._surface.stroke_path(ring_path, pal.surface_border, stroke_width=1.0 * s)

        # 2. Radial Axis Lines & Category Labels
        for i, cat in enumerate(self._categories):
            ang = i * (2.0 * math.pi / n) - (math.pi / 2.0)
            px = cx + max_r * math.cos(ang)
            py = cy + max_r * math.sin(ang)
            self._surface.draw_line(cx, cy, px, py, pal.surface_border, stroke_width=1.0 * s)

            # Draw Label
            lbl_r = max_r + 14.0 * s
            lx = cx + lbl_r * math.cos(ang)
            ly = cy + lbl_r * math.sin(ang)
            align = "center"
            if math.cos(ang) > 0.3:
                align = "left"
            elif math.cos(ang) < -0.3:
                align = "right"
            self._surface.draw_text(cat, lx, ly + 3.0 * s, font_size=8.5 * s, color=pal.fg_subtle, align=align)

        # 3. Value Polygon Fill & Stroke
        val_path = Path()
        col = self._explicit_color or pal.primary or "#3b82f6"
        for i, val in enumerate(self._values):
            norm = max(0.0, min(100.0, val)) / 100.0
            r = norm * max_r
            ang = i * (2.0 * math.pi / n) - (math.pi / 2.0)
            px = cx + r * math.cos(ang)
            py = cy + r * math.sin(ang)
            if i == 0:
                val_path.move_to(px, py)
            else:
                val_path.line_to(px, py)
        val_path.close()

        # Fill with semi-transparent tint
        fill_col = col + "44" if col.startswith("#") and len(col) == 7 else col
        self._surface.fill_path(val_path, fill_col)
        self._surface.stroke_path(val_path, col, stroke_width=2.5 * s)

        # Draw Points
        for i, val in enumerate(self._values):
            norm = max(0.0, min(100.0, val)) / 100.0
            r = norm * max_r
            ang = i * (2.0 * math.pi / n) - (math.pi / 2.0)
            px = cx + r * math.cos(ang)
            py = cy + r * math.sin(ang)
            self._surface.fill_circle(px, py, 4.0 * s, col)
            self._surface.stroke_circle(px, py, 4.0 * s, "#ffffff", stroke_width=1.5 * s)

        self._surface.blit(self._photo)


# ==============================================================================
# Custom Widget 2: Semi-Circular Speedometer Analog Gauge
# ==============================================================================
class SpeedometerGauge(Widget):
    """Custom analog speedometer dial with ticks and glowing vector needle."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        min_value: float = 0.0,
        max_value: float = 160.0,
        value: float = 65.0,
        unit: str = "km/h",
        size: int = 220,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._min_v = min_value
        self._max_v = max_value
        self._value = value
        self._unit = unit
        super().__init__(master=master, width=size, height=int(size * 0.85), bg=parent_bg, **kwargs)

    def set_value(self, val: float) -> None:
        self._value = max(self._min_v, min(self._max_v, float(val)))
        self.render()

    def render(self) -> None:
        if self._surface is None or self._photo is None:
            return

        pal = get_theme()
        s = self._scale
        w = float(self._widget_w)
        h = float(self._widget_h)
        cx = w / 2.0

        self._surface.clear(self._parent_bg)

        # Gauge arc parameters (144 deg to 396 deg / -144 to 36 deg relative)
        start_rad = math.pi * 0.8
        end_rad = math.pi * 2.2
        span_rad = end_rad - start_rad

        # Calculate radius and center so top/bottom ticks and hub are completely unclipped
        max_tick_extra = 12.0 * s
        pad = 14.0 * s
        vert_factor = 1.0 + math.sin(0.8 * math.pi)  # ~1.5878
        max_r_from_h = (h - 2.0 * pad) / vert_factor - max_tick_extra
        max_r_from_w = (w / 2.0) - pad - max_tick_extra
        r = max(10.0, min(max_r_from_h, max_r_from_w))
        cy = pad + (r + max_tick_extra)

        # 1. Track Arc
        track_path = Path()
        track_path.arc_to(cx, cy, r, r, start_rad, span_rad)
        self._surface.stroke_path(track_path, pal.track_bg, stroke_width=10.0 * s)

        # 2. Value Active Arc
        norm = (self._value - self._min_v) / max(1.0, self._max_v - self._min_v)
        val_path = Path()
        val_path.arc_to(cx, cy, r, r, start_rad, span_rad * norm)

        val_col = pal.accent if norm > 0.8 else (pal.primary if norm > 0.4 else pal.secondary)
        self._surface.stroke_path(val_path, val_col, stroke_width=10.0 * s)

        # 3. Ticks
        ticks = 8
        for i in range(ticks + 1):
            t_norm = i / ticks
            t_rad = start_rad + span_rad * t_norm
            x1 = cx + (r - 12.0 * s) * math.cos(t_rad)
            y1 = cy + (r - 12.0 * s) * math.sin(t_rad)
            x2 = cx + (r + 12.0 * s) * math.cos(t_rad)
            y2 = cy + (r + 12.0 * s) * math.sin(t_rad)
            self._surface.draw_line(x1, y1, x2, y2, pal.surface_border, stroke_width=1.5 * s)

        # 4. Needle Pointer
        cur_rad = start_rad + span_rad * norm
        nx = cx + (r - 16.0 * s) * math.cos(cur_rad)
        ny = cy + (r - 16.0 * s) * math.sin(cur_rad)
        self._surface.draw_line(cx, cy, nx, ny, val_col, stroke_width=3.0 * s)

        # Center Hub
        self._surface.fill_circle(cx, cy, 10.0 * s, pal.card_bg)
        self._surface.stroke_circle(cx, cy, 10.0 * s, val_col, stroke_width=2.5 * s)
        self._surface.fill_circle(cx, cy, 4.0 * s, "#ffffff")

        # 5. Value Text Readout
        self._surface.draw_text(f"{int(self._value)}", cx, cy - 24.0 * s, font_size=16.0 * s, color=pal.fg, align="center")
        self._surface.draw_text(self._unit, cx, cy - 10.0 * s, font_size=8.0 * s, color=pal.fg_subtle, align="center")

        self._surface.blit(self._photo)


# ==============================================================================
# Custom Widget 3: Multi-Step Breadcrumb Progress Wizard
# ==============================================================================
class StepProgressBar(Widget):
    """Custom multi-step wizard progress indicator."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        steps: Optional[List[str]] = None,
        current_step: int = 1,
        width: int = 500,
        height: int = 60,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._steps = steps or ["Account", "Profile", "Payment", "Review", "Complete"]
        self._current_step = current_step
        super().__init__(master=master, width=width, height=height, bg=parent_bg, **kwargs)

    def set_step(self, step_idx: int) -> None:
        self._current_step = max(0, min(len(self._steps) - 1, step_idx))
        self.render()

    def render(self) -> None:
        if self._surface is None or self._photo is None:
            return

        pal = get_theme()
        s = self._scale
        w = float(self._widget_w)
        h = float(self._widget_h)
        cy = 22.0 * s
        n = len(self._steps)

        self._surface.clear(self._parent_bg)

        pad_x = 40.0 * s
        step_w = (w - pad_x * 2.0) / max(1, n - 1)

        # 1. Background Connector Line
        self._surface.draw_line(pad_x, cy, w - pad_x, cy, pal.track_bg, stroke_width=4.0 * s)

        # 2. Active Connector Line
        if self._current_step > 0:
            active_w = pad_x + self._current_step * step_w
            self._surface.draw_line(pad_x, cy, active_w, cy, pal.primary, stroke_width=4.0 * s)

        # 3. Step Nodes
        node_r = 13.0 * s
        for i, step_name in enumerate(self._steps):
            nx = pad_x + i * step_w
            if i < self._current_step:
                # Completed Step
                self._surface.fill_circle(nx, cy, node_r, pal.success)
                draw_vector_checkmark(self._surface, nx, cy, 0.9 * s, "#ffffff")
            elif i == self._current_step:
                # Active Current Step
                self._surface.fill_circle(nx, cy, node_r, pal.primary)
                self._surface.stroke_circle(nx, cy, node_r + 3.0 * s, pal.primary, stroke_width=2.0 * s)
                self._surface.draw_text(str(i + 1), nx, cy + 4.0 * s, font_size=10.0 * s, color="#ffffff", align="center")
            else:
                # Pending Step
                self._surface.fill_circle(nx, cy, node_r, pal.card_bg)
                self._surface.stroke_circle(nx, cy, node_r, pal.track_bg, stroke_width=2.0 * s)
                self._surface.draw_text(str(i + 1), nx, cy + 4.0 * s, font_size=10.0 * s, color=pal.fg_subtle, align="center")

            # Step Label Text
            lbl_col = pal.fg if i <= self._current_step else pal.fg_subtle
            self._surface.draw_text(step_name, nx, cy + 22.0 * s, font_size=8.5 * s, color=lbl_col, align="center")

        self._surface.blit(self._photo)


# ==============================================================================
# Custom Widget 4: Radial HSV Color Wheel Picker
# ==============================================================================
class ColorWheelPicker(Widget):
    """Custom radial HSV color wheel picker with draggable selector thumb."""

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 180,
        on_color_changed: Optional[Callable[[str], None]] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._on_color_changed = on_color_changed
        self._hue = 0.6  # 0.0 - 1.0
        self._sat = 0.8  # 0.0 - 1.0
        super().__init__(master=master, width=size, height=size, bg=parent_bg, **kwargs)
        self.bind("<ButtonPress-1>", self._on_mouse)
        self.bind("<B1-Motion>", self._on_mouse)

    def _on_mouse(self, event) -> None:
        s = self._scale
        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        r_max = (min(cx, cy) - 10.0 * s)

        dx = event.x - cx
        dy = event.y - cy
        dist = math.hypot(dx, dy)
        self._sat = max(0.0, min(1.0, dist / r_max))
        ang = math.atan2(dy, dx)
        if ang < 0:
            ang += 2.0 * math.pi
        self._hue = ang / (2.0 * math.pi)

        self.render()
        if self._on_color_changed:
            self._on_color_changed(self.get_hex())

    def get_hex(self) -> str:
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(self._hue, self._sat, 1.0)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    def render(self) -> None:
        if self._surface is None or self._photo is None:
            return

        pal = get_theme()
        s = self._scale
        w = float(self._widget_w)
        h = float(self._widget_h)
        cx = w / 2.0
        cy = h / 2.0
        r_max = min(cx, cy) - 10.0 * s

        self._surface.clear(self._parent_bg)

        # Draw Color Wheel Segments
        segments = 36
        import colorsys
        for i in range(segments):
            h_val = i / segments
            r_c, g_c, b_c = colorsys.hsv_to_rgb(h_val, 1.0, 1.0)
            hex_c = f"#{int(r_c * 255):02x}{int(g_c * 255):02x}{int(b_c * 255):02x}"
            ang1 = i * (2.0 * math.pi / segments)
            ang2 = (i + 1) * (2.0 * math.pi / segments)

            seg_path = Path()
            seg_path.move_to(cx, cy)
            seg_path.arc_to(cx, cy, r_max, r_max, ang1, ang2 - ang1)
            seg_path.close()
            self._surface.fill_path(seg_path, hex_c)

        # Center White Glow Fade
        white_fade = RadialGradient(cx, cy, r_max)
        white_fade.add_stop(0.0, "#ffffffff")
        white_fade.add_stop(1.0, "#ffffff00")
        self._surface.fill_circle(cx, cy, r_max, white_fade)

        # Draggable Thumb
        thumb_ang = self._hue * 2.0 * math.pi
        thumb_r = self._sat * r_max
        tx = cx + thumb_r * math.cos(thumb_ang)
        ty = cy + thumb_r * math.sin(thumb_ang)

        self._surface.fill_circle(tx, ty, 8.0 * s, self.get_hex())
        self._surface.stroke_circle(tx, ty, 8.0 * s, "#ffffff", stroke_width=2.5 * s)

        self._surface.blit(self._photo)


# ==============================================================================
# Cookbook Showcase Window
# ==============================================================================
class CustomWidgetCookbook(tk.Frame):
    """Interactive showroom for custom user-created Blend2D vector widgets."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Header Bar
        hdr = tk.Frame(self, background=pal.bg)
        hdr.pack(fill="x", padx=20, pady=(16, 8))

        tbox = tk.Frame(hdr, background=pal.bg)
        tbox.pack(side="left")

        tk.Label(tbox, text="Custom Vector Widget Cookbook", font=("Segoe UI", 18, "bold"), fg=pal.fg, bg=pal.bg).pack(anchor="w")
        tk.Label(tbox, text="Learn how to build bespoke Blend2D vector components with zero TTK dependencies", font=("Segoe UI", 10), fg=pal.fg_subtle, bg=pal.bg).pack(anchor="w")

        cbox = tk.Frame(hdr, background=pal.bg)
        cbox.pack(side="right")

        tk.Label(cbox, text="Theme:", font=("Segoe UI", 10), fg=pal.fg_subtle, bg=pal.bg).pack(side="left", padx=(8, 4))
        OptionMenu(
            cbox,
            values=list(get_available_themes()),
            default_value="dark",
            command=self._on_theme_changed,
            width=140,
            height=32,
        ).pack(side="left", padx=6)

        # Top Wizard Row (StepProgressBar)
        wiz_card = Card(self, title="Step 1: Multi-Step Wizard Indicator (`StepProgressBar`)", width=960, height=120, rx=14, ry=14, elevation=6)
        wiz_card.pack(fill="x", padx=20, pady=8)

        w_body = wiz_card.body
        self._wizard = StepProgressBar(w_body, current_step=1, width=640, height=54)
        self._wizard.pack(side="left", padx=16, pady=4)

        w_ctrl = tk.Frame(w_body, background=wiz_card.bg_color)
        w_ctrl.pack(side="right", padx=16)

        Button(w_ctrl, text="← Prev Step", width=95, height=30, bootstyle="secondary", command=self._prev_step).pack(side="left", padx=4)
        Button(w_ctrl, text="Next Step →", width=95, height=30, bootstyle="primary", command=self._next_step).pack(side="left", padx=4)

        # Grid of Custom Widgets (Radar + Speedometer + ColorWheel)
        grid_row = tk.Frame(self, background=pal.bg)
        grid_row.pack(fill="both", expand=True, padx=20, pady=(6, 16))

        # 1. Radar Chart Card
        radar_card = Card(grid_row, title="Radar / Spider Chart", width=310, height=380, rx=14, ry=14, elevation=6)
        radar_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        r_body = radar_card.body
        self._radar = RadarChartWidget(r_body, size=230)
        self._radar.pack(pady=4)

        Button(r_body, text="Randomize Stats", width=180, height=30, command=self._randomize_radar).pack(pady=6)

        # 2. Speedometer Card
        speedo_card = Card(grid_row, title="Speedometer Gauge", width=310, height=380, rx=14, ry=14, elevation=6)
        speedo_card.pack(side="left", fill="both", expand=True, padx=4)

        s_body = speedo_card.body
        self._speedo = SpeedometerGauge(s_body, value=85.0, size=230)
        self._speedo.pack(pady=4)

        tk.Label(s_body, text="Speed Dial Slider:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=speedo_card.bg_color).pack(anchor="w", padx=24)
        Slider(s_body, from_=0, to=160, value=85, width=220, height=22, command=self._speedo.set_value).pack(pady=4)

        # 3. ColorWheel Card
        wheel_card = Card(grid_row, title="Radial Color Wheel", width=310, height=380, rx=14, ry=14, elevation=6)
        wheel_card.pack(side="left", fill="both", expand=True, padx=(8, 0))

        c_body = wheel_card.body
        self._wheel = ColorWheelPicker(c_body, size=200, on_color_changed=self._on_wheel_color)
        self._wheel.pack(pady=4)

        self._color_preview = tk.Label(c_body, text="Selected: #3b82f6", font=("Segoe UI", 10, "bold"), fg="#3b82f6", bg=wheel_card.bg_color)
        self._color_preview.pack(pady=6)

        cascade_bg_to_children(self, pal.bg)

    def _prev_step(self) -> None:
        self._wizard.set_step(self._wizard._current_step - 1)

    def _next_step(self) -> None:
        self._wizard.set_step(self._wizard._current_step + 1)

    def _randomize_radar(self) -> None:
        import random
        new_vals = [random.uniform(40, 100) for _ in range(6)]
        self._radar.set_values(new_vals)

    def _on_wheel_color(self, hex_val: str) -> None:
        self._color_preview.configure(text=f"Selected: {hex_val}", fg=hex_val)

    def _on_theme_changed(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg)


def main():
    root = tk.Tk()
    root.title("tkblend Custom Vector Widget Cookbook")
    root.geometry("1020x720")
    root.minsize(900, 600)

    ScalingTracker.activate_high_dpi_awareness()
    set_theme("dark")

    app = CustomWidgetCookbook(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
