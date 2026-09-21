"""
tkblend + ttkbootstrap Modern Showcase
Demonstrates high-performance Blend2D vector graphics, real-time 60 FPS animation,
glowing gauges, dynamic cards, and seamless ttkbootstrap theme integration.
"""

import math
import time
import tkinter as tk
from tkinter import ttk

try:
    import ttkbootstrap as tb
    HAS_TTKBOOTSTRAP = True
except ImportError:
    HAS_TTKBOOTSTRAP = False

from tkblend import (
    BlendCanvas,
    Surface,
    LinearGradient,
    RadialGradient,
    Path,
    resolve_theme_color,
    is_ttkbootstrap_installed,
)


class ShowcaseApp:
    def __init__(self):
        if HAS_TTKBOOTSTRAP:
            self.root = tb.Window(
                title="tkblend + ttkbootstrap Showcase",
                themename="darkly",
                size=(1050, 720),
                resizable=(True, True),
            )
            self.style = tb.Style.get_instance()
        else:
            self.root = tk.Tk()
            self.root.title("tkblend Showcase (Standard Tk)")
            self.root.geometry("1050x720")
            self.style = None

        self.root.minsize(800, 600)

        # State variables
        self.running = True
        self.phase = 0.0
        self.speed = 0.05
        self.frequency = 3.0
        self.gauge_val = 65.0
        self.gauge_target = 75.0
        self.fps = 0.0
        self._frame_count = 0
        self._last_time = time.perf_counter()

        self._build_ui()
        self._animate()

    def _build_ui(self):
        # Top Header & Controls Bar
        header = ttk.Frame(self.root, padding=16)
        header.pack(fill=tk.X)

        title_lbl = ttk.Label(
            header,
            text="⚡ tkblend + ttkbootstrap Graphics Engine",
            font=("sans-serif", 18, "bold"),
        )
        title_lbl.pack(side=tk.LEFT)

        # Theme Switcher (if ttkbootstrap available)
        if HAS_TTKBOOTSTRAP and self.style:
            all_themes = list(self.style.theme_names())
            current_theme = self.style.theme_use()
            self.theme_var = tk.StringVar(value=current_theme)

            theme_frame = ttk.Frame(header)
            theme_frame.pack(side=tk.RIGHT)

            ttk.Label(theme_frame, text="Theme:", font=("sans-serif", 10)).pack(side=tk.LEFT, padx=6)
            cb = ttk.Combobox(
                theme_frame,
                textvariable=self.theme_var,
                values=all_themes,
                state="readonly",
                width=16,
            )
            cb.pack(side=tk.LEFT)
            cb.bind("<<ComboboxSelected>>", self._on_theme_select)


        # Control Toolbar
        toolbar = ttk.Frame(self.root, padding=(16, 0, 16, 12))
        toolbar.pack(fill=tk.X)

        self.btn_toggle = ttk.Button(toolbar, text="⏸ Pause", command=self._toggle_anim, width=10)
        self.btn_toggle.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(toolbar, text="Speed:").pack(side=tk.LEFT, padx=4)
        self.speed_slider = ttk.Scale(toolbar, from_=0.01, to=0.15, value=0.05, command=self._on_speed)
        self.speed_slider.pack(side=tk.LEFT, padx=(0, 16), fill=tk.X)

        ttk.Label(toolbar, text="Gauge Target:").pack(side=tk.LEFT, padx=4)
        self.gauge_slider = ttk.Scale(toolbar, from_=0.0, to=100.0, value=75.0, command=self._on_gauge)
        self.gauge_slider.pack(side=tk.LEFT, padx=(0, 16), fill=tk.X)

        self.lbl_fps = ttk.Label(toolbar, text="FPS: --", font=("sans-serif", 10, "bold"))
        self.lbl_fps.pack(side=tk.RIGHT)

        # Main Graphic Grid Layout
        main_frame = ttk.Frame(self.root, padding=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # 1. Main Oscilloscope / Wave Visualizer Canvas
        self.canvas_wave = BlendCanvas(
            main_frame,
            width=580,
            height=300,
            on_draw=self._draw_wave,
        )
        self.canvas_wave.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        # 2. Glowing Radial Gauge Canvas
        self.canvas_gauge = BlendCanvas(
            main_frame,
            width=380,
            height=300,
            on_draw=self._draw_gauge,
        )
        self.canvas_gauge.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        # 3. Dynamic Vector Geometry & Card Canvas
        self.canvas_vector = BlendCanvas(
            main_frame,
            width=580,
            height=260,
            on_draw=self._draw_vectors,
        )
        self.canvas_vector.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

        # 4. Multi-Stop Gradient Glassmorphism Canvas
        self.canvas_glass = BlendCanvas(
            main_frame,
            width=380,
            height=260,
            on_draw=self._draw_glass,
        )
        self.canvas_glass.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)

    def _on_theme_select(self, event=None):
        if HAS_TTKBOOTSTRAP and self.style:
            new_theme = self.theme_var.get()
            self.style.theme_use(new_theme)

    def _toggle_anim(self):
        self.running = not self.running
        self.btn_toggle.configure(text="▶ Resume" if not self.running else "⏸ Pause")

    def _on_speed(self, val):
        self.speed = float(val)

    def _on_gauge(self, val):
        self.gauge_target = float(val)

    # -------------------------------------------------------------------------
    # Canvas Draw Callbacks (Blend2D Accelerated)
    # -------------------------------------------------------------------------

    def _draw_wave(self, s: Surface):
        w, h = s.width, s.height

        # Card container with soft shadow
        s.clear("bg")
        s.draw_card(
            12, 12, w - 24, h - 24,
            rx=16, ry=16,
            bg_color="dark",
            border_color="border",
            border_width=1.0,
            shadow_blur=16.0,
            shadow_color="#00000055"
        )

        # Card Header
        s.draw_text("⚡ Real-time Vector Signal Analyzer", 32, 42, font_size=16, color="primary")
        s.draw_text("Blend2D Bezier Interpolation (Direct Blit)", 32, 62, font_size=11, color="secondary")

        # Grid lines
        grid_top = 80
        grid_bot = h - 35
        grid_h = grid_bot - grid_top

        for i in range(5):
            gy = grid_top + (grid_h * i / 4.0)
            s.draw_line(32, gy, w - 32, gy, stroke="border", stroke_width=0.8)

        # Animated Wave 1 (Filled Area Gradient + Crisp Stroke)
        area_p = Path()
        wave_p = Path()
        mid_y = grid_top + grid_h / 2.0
        area_p.move_to(32, grid_bot)

        steps = 60
        dx = (w - 64) / steps
        for i in range(steps + 1):
            x = 32 + i * dx
            norm_x = i / float(steps)
            y = mid_y + math.sin(norm_x * 4 * math.pi + self.phase) * (grid_h * 0.35) * math.sin(norm_x * math.pi)
            if i == 0:
                wave_p.move_to(x, y)
            else:
                wave_p.line_to(x, y)
            area_p.line_to(x, y)

        area_p.line_to(w - 32, grid_bot)
        area_p.close()

        # Fill area under curve with vertical gradient
        grad = LinearGradient(32, grid_top, 32, grid_bot)
        grad.add_stop(0.0, "primary/0.45").add_stop(1.0, "dark/0.0")
        s.fill_path(area_p, grad)

        # Stroke the wave curve
        s.stroke_path(wave_p, "primary", stroke_width=3.0)

        # Animated Wave 2 (Secondary phase)
        wave_p2 = Path()
        for i in range(steps + 1):
            x = 32 + i * dx
            norm_x = i / float(steps)
            y = mid_y + math.cos(norm_x * 6 * math.pi - self.phase * 1.5) * (grid_h * 0.22)
            if i == 0:
                wave_p2.move_to(x, y)
            else:
                wave_p2.line_to(x, y)

        s.stroke_path(wave_p2, "warning", stroke_width=2.0)

    def _draw_gauge(self, s: Surface):
        w, h = s.width, s.height

        s.clear("bg")
        s.draw_card(
            12, 12, w - 24, h - 24,
            rx=16, ry=16,
            bg_color="dark",
            border_color="border",
            border_width=1.0,
            shadow_blur=16.0,
            shadow_color="#00000055"
        )

        s.draw_text("Radial Arc Meter", 32, 42, font_size=16, color="info")

        cx = w / 2.0
        cy = h / 2.0 + 15
        radius = min(w, h) * 0.32

        # Background track arc
        start_angle = math.radians(135)
        sweep_angle = math.radians(270)

        track_p = Path()
        track_p.arc_to(cx, cy, radius, radius, start_angle, sweep_angle)
        s.stroke_path(track_p, stroke="secondary", stroke_width=14.0)

        # Active progress arc
        pct = max(0.0, min(100.0, self.gauge_val)) / 100.0
        active_sweep = sweep_angle * pct

        if active_sweep > 0.01:
            active_p = Path()
            active_p.arc_to(cx, cy, radius, radius, start_angle, active_sweep)
            s.stroke_path(active_p, "primary", stroke_width=14.0)


        # Center Value & Unit
        val_str = f"{self.gauge_val:.1f}%"
        s.draw_text(val_str, cx, cy - 5, font_size=26, font_family="sans-serif", color="fg", align="center")
        s.draw_text("SYSTEM LOAD", cx, cy + 24, font_size=10, color="secondary", align="center")

    def _draw_vectors(self, s: Surface):
        w, h = s.width, s.height

        s.clear("bg")
        s.draw_card(
            12, 12, w - 24, h - 24,
            rx=16, ry=16,
            bg_color="dark",
            border_color="border",
            border_width=1.0,
            shadow_blur=16.0,
            shadow_color="#00000055"
        )

        s.draw_text("Antialiased Vector Primitives", 32, 42, font_size=16, color="success")

        # Rotating Star Geometry
        star_cx = 90.0
        star_cy = h / 2.0 + 10
        star_p = Path()
        points = 5
        outer_r = 45.0
        inner_r = 20.0

        for i in range(points * 2):
            r = outer_r if i % 2 == 0 else inner_r
            angle = i * math.pi / points + self.phase
            px = star_cx + r * math.cos(angle)
            py = star_cy + r * math.sin(angle)
            if i == 0:
                star_p.move_to(px, py)
            else:
                star_p.line_to(px, py)
        star_p.close()

        star_grad = RadialGradient(star_cx, star_cy, 0, star_cx, star_cy, outer_r)
        star_grad.add_stop(0.0, "warning").add_stop(1.0, "danger")
        s.fill_path(star_p, star_grad)
        s.stroke_path(star_p, "light", stroke_width=1.5)

        # Rounded Badges & Progress
        bx = 180.0
        by = 80.0
        bw = w - bx - 32

        s.draw_text("Direct Tk_PhotoPutBlock Blitting", bx, by + 12, font_size=13, color="fg")
        s.fill_rounded_rect(bx, by + 24, bw, 12, 6, 6, "border")
        fill_w = bw * (0.5 + 0.45 * math.sin(self.phase * 0.8))
        s.fill_rounded_rect(bx, by + 24, fill_w, 12, 6, 6, "primary")

        # Pill Tags
        pill_y = by + 56
        tags = [("Blend2D", "primary"), ("Tk_PhotoPutBlock", "success"), ("Zero-Copy", "info"), ("60 FPS", "warning")]
        curr_x = bx
        for tag_text, tag_color in tags:
            tag_w = len(tag_text) * 9 + 18
            s.fill_rounded_rect(curr_x, pill_y, tag_w, 24, 12, 12, tag_color)
            s.draw_text(tag_text, curr_x + tag_w / 2.0, pill_y + 16, font_size=10, color="dark", align="center")
            curr_x += tag_w + 10

    def _draw_glass(self, s: Surface):
        w, h = s.width, s.height

        s.clear("bg")
        s.draw_card(
            12, 12, w - 24, h - 24,
            rx=16, ry=16,
            bg_color="dark",
            border_color="border",
            border_width=1.0,
            shadow_blur=16.0,
            shadow_color="#00000055"
        )

        s.draw_text("Multi-Stop Gradients", 32, 42, font_size=16, color="warning")

        # Animated multi-color mesh / gradient block
        gw = w - 64
        gh = h - 90
        gx = 32.0
        gy = 65.0

        rad = RadialGradient(gx + gw * 0.5, gy + gh * 0.5, 0, gx + gw * 0.5, gy + gh * 0.5, gw * 0.6)
        rad.add_stop(0.0, "primary").add_stop(0.4, "info").add_stop(0.8, "success").add_stop(1.0, "dark")
        s.fill_rounded_rect(gx, gy, gw, gh, 12, 12, rad)
        s.stroke_rounded_rect(gx, gy, gw, gh, 12, 12, "light", 1.0)

        # Concentric glowing rings
        for r_step in range(1, 4):
            ring_r = 18.0 * r_step + math.sin(self.phase + r_step) * 6.0
            s.stroke_circle(gx + gw * 0.5, gy + gh * 0.5, ring_r, "light", stroke_width=1.5)

    def _animate(self):
        if self.running:
            self.phase += self.speed
            # Smooth gauge ease towards target
            self.gauge_val += (self.gauge_target - self.gauge_val) * 0.08

            # Redraw all canvases
            self.canvas_wave.redraw()
            self.canvas_gauge.redraw()
            self.canvas_vector.redraw()
            self.canvas_glass.redraw()

            # Calculate FPS
            self._frame_count += 1
            now = time.perf_counter()
            dt = now - self._last_time
            if dt >= 0.5:
                self.fps = self._frame_count / dt
                self.lbl_fps.configure(text=f"FPS: {self.fps:.1f}")
                self._frame_count = 0
                self._last_time = now

        self.root.after(16, self._animate)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = ShowcaseApp()
    app.run()
