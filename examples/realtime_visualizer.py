#!/usr/bin/env python3
"""
tkblend Showcase: High-Performance 60 FPS Real-time Visualizer & Physics Simulator.
Demonstrates:
  - Raw Blend2D rendering speed and zero-copy direct blitting via NativeBlitCanvas
  - Smooth 60 FPS animation loop with sub-millisecond per-frame draw times
  - 3 simulation modes:
      1. Particle Swarm with gravity wells, velocities, and speed-colored trails
      2. Neon Audio Spectrum Equalizer with peak hold meters and reflections
      3. Harmonic Lissajous Oscilloscope with live phase modulation
  - Real-time FPS counter, render latency telemetry, and interactive physics sliders
"""

from __future__ import annotations

import math
import random
import sys
import time
import tkinter as tk
from pathlib import Path as FilePath
from typing import Optional, List, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = FilePath(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkblend as tb
from tkblend import (
    NativeBlitCanvas,
    Surface,
    LinearGradient,
    RadialGradient,
    Path,
    Card,
    Button,
    Slider,
    CircularProgress,
    SegmentedButton,
    OptionMenu,
    Switch,
    Badge,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    resolve_color_failsafe,
    ScalingTracker,
)


class Particle:
    """Single particle in the 2D physics simulation."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(-2.5, 2.5)
        self.radius = random.uniform(2.5, 5.0)
        self.history: List[Tuple[float, float]] = []


class RealtimeVisualizer(tk.Frame):
    """High-performance real-time vector visualizer stressing 60 FPS Blend2D rendering."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)

        self._mode = "particles"  # 'particles', 'spectrum', 'lissajous'
        self._is_animating = True
        self._anim_job: Optional[str] = None

        # Physics & Simulation state
        self._particle_count = 120
        self._gravity_strength = 1.0
        self._speed_multiplier = 1.0
        self._particles: List[Particle] = []
        self._mouse_attractor: Optional[Tuple[float, float]] = None

        # Spectrum state
        self._spectrum_bars = 48
        self._spectrum_vals: List[float] = [0.0] * self._spectrum_bars
        self._spectrum_peaks: List[float] = [0.0] * self._spectrum_bars

        # Lissajous state
        self._phase_a = 0.0
        self._phase_b = 0.0
        self._freq_x = 3.0
        self._freq_y = 4.0
        self._lissajous_ratios = [(3.0, 4.0), (5.0, 4.0), (5.0, 6.0), (2.0, 3.0), (3.0, 5.0), (7.0, 8.0)]
        self._ratio_idx = 0

        # FPS & Telemetry
        self._fps = 60.0
        self._render_time_ms = 0.5
        self._last_time = time.perf_counter()
        self._frame_count = 0
        self._fps_timer = time.perf_counter()

        self._build_ui()
        self._init_particles()
        self._start_loop()

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Header Bar Card
        header = Card(self, height=68)
        header.pack(fill="x", padx=16, pady=(16, 8))

        hdr_inner = tk.Frame(header, bg=pal.card_bg)
        hdr_inner.pack(fill="both", expand=True, padx=18, pady=(10, 14))

        tk.Label(
            hdr_inner,
            text="⚡ 60 FPS Real-time Engine & Physics Lab",
            font=("sans-serif", 15, "bold"),
            bg=pal.card_bg,
            fg=pal.fg,
        ).pack(side="left")

        self._fps_badge = Badge(hdr_inner, text="60 FPS | 0.4 ms", variant="success", dot=True)
        self._fps_badge.pack(side="left", padx=12)

        # Theme OptionMenu
        self._theme_opt = OptionMenu(
            hdr_inner,
            values=sorted(get_available_themes()),
            current_value=pal.name,
            command=self._on_theme_change,
            width=140,
            height=30,
        )
        self._theme_opt.pack(side="right", padx=(8, 0))

        # Pause / Play Switch
        self._anim_switch = Switch(hdr_inner, text="Active", is_checked=True, command=self._toggle_animation, width=80, height=26)
        self._anim_switch.pack(side="right", padx=8)

        # Main Central Section
        mid_frame = tk.Frame(self, bg=pal.bg)
        mid_frame.pack(fill="both", expand=True, padx=16, pady=6)

        # Left Column: Canvas Viewport Card
        canvas_card = Card(mid_frame)
        canvas_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        canvas_inner = tk.Frame(canvas_card, bg=pal.card_bg)
        canvas_inner.pack(fill="both", expand=True, padx=18, pady=16)

        c_hdr = tk.Frame(canvas_inner, bg=pal.card_bg)
        c_hdr.pack(fill="x", pady=(2, 4))

        tk.Label(c_hdr, text="Simulation Viewport", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(side="left")

        self._mode_seg = SegmentedButton(
            c_hdr,
            values=["Particles", "Spectrum", "Lissajous"],
            selected_value="Particles",
            command=self._on_mode_change,
            height=30,
            width=280,
        )
        self._mode_seg.pack(side="right")

        # NativeBlitCanvas
        self._canvas = NativeBlitCanvas(canvas_inner, height=440, on_paint=self._paint_canvas)
        self._canvas.pack(fill="both", expand=True, pady=(2, 6))

        self._canvas.bind("<Motion>", self._on_canvas_motion)
        self._canvas.bind("<Leave>", self._on_canvas_leave)

        # Right Column: Controls & Telemetry
        ctrl_card = Card(mid_frame, width=340)
        ctrl_card.pack(side="right", fill="both", padx=(6, 0))

        ctrl_inner = tk.Frame(ctrl_card, bg=pal.card_bg)
        ctrl_inner.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(ctrl_inner, text="Engine Telemetry", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=(2, 6))

        # Real-time Gauges Row
        gauge_row = tk.Frame(ctrl_inner, bg=pal.card_bg)
        gauge_row.pack(fill="x", pady=(0, 10))

        self._gauge_fps = CircularProgress(gauge_row, size=85, value=60.0, max_value=120.0, title="Framerate", unit="FPS", stroke_width=6)
        self._gauge_fps.pack(side="left", fill="both", expand=True)

        self._gauge_load = CircularProgress(gauge_row, size=85, value=4.5, max_value=100.0, title="Frame Cost", unit="%", stroke_width=6)
        self._gauge_load.pack(side="left", fill="both", expand=True)

        # Mode-dependent Controls
        self._lbl_params = tk.Label(ctrl_inner, text="Physics & Parameters", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg)
        self._lbl_params.pack(anchor="w", pady=(8, 4))

        # Speed slider
        self._lbl_s1 = tk.Label(ctrl_inner, text="Speed Multiplier:", font=("sans-serif", 9), bg=pal.card_bg, fg=pal.text_muted)
        self._lbl_s1.pack(anchor="w")
        self._slider_speed = Slider(ctrl_inner, from_=0.1, to=3.0, value=1.0, command=self._on_speed_changed, height=22)
        self._slider_speed.pack(fill="x", pady=(2, 6))

        # Secondary parameter slider
        self._lbl_s2 = tk.Label(ctrl_inner, text="Particle Swarm Density:", font=("sans-serif", 9), bg=pal.card_bg, fg=pal.text_muted)
        self._lbl_s2.pack(anchor="w")
        self._slider_count = Slider(ctrl_inner, from_=20.0, to=300.0, value=120.0, command=self._on_count_changed, height=22)
        self._slider_count.pack(fill="x", pady=(2, 6))

        # Tertiary parameter slider
        self._lbl_s3 = tk.Label(ctrl_inner, text="Gravity Well Pull:", font=("sans-serif", 9), bg=pal.card_bg, fg=pal.text_muted)
        self._lbl_s3.pack(anchor="w")
        self._slider_grav = Slider(ctrl_inner, from_=0.0, to=3.0, value=1.0, command=self._on_gravity_changed, height=22)
        self._slider_grav.pack(fill="x", pady=(2, 10))

        # Action Buttons
        self._btn_act1 = Button(ctrl_inner, text="💥 Blast Particle Field", command=self._on_action1, height=34, auto_fit=True)
        self._btn_act1.pack(fill="x", pady=4)

        self._btn_act2 = Button(ctrl_inner, text="🔄 Reset Simulation", command=self._on_action2, height=34, auto_fit=True)
        self._btn_act2.pack(fill="x", pady=4)

        cascade_bg_to_children(self, pal.bg, palette=pal)

    def _init_particles(self) -> None:
        w = max(100.0, float(self._canvas.winfo_width() or 600))
        h = max(100.0, float(self._canvas.winfo_height() or 400))
        self._particles = [
            Particle(random.uniform(20, w - 20), random.uniform(20, h - 20))
            for _ in range(self._particle_count)
        ]

    def _on_speed_changed(self, val: float) -> None:
        self._speed_multiplier = float(val)

    def _on_count_changed(self, val: float) -> None:
        if self._mode == "particles":
            self._particle_count = int(val)
            self._init_particles()
        elif self._mode == "spectrum":
            self._spectrum_bars = max(16, min(64, int(val)))
            self._spectrum_vals = [0.0] * self._spectrum_bars
            self._spectrum_peaks = [0.0] * self._spectrum_bars
        elif self._mode == "lissajous":
            self._freq_x = max(1.0, round(float(val)))

    def _on_gravity_changed(self, val: float) -> None:
        if self._mode == "particles":
            self._gravity_strength = float(val)
        elif self._mode == "lissajous":
            self._freq_y = max(1.0, round(float(val)))

    def _on_action1(self) -> None:
        if self._mode == "particles":
            self._blast_particles()
        elif self._mode == "spectrum":
            for i in range(len(self._spectrum_vals)):
                self._spectrum_vals[i] = random.uniform(0.7, 1.0)
                self._spectrum_peaks[i] = max(self._spectrum_peaks[i], self._spectrum_vals[i])
        elif self._mode == "lissajous":
            self._ratio_idx = (self._ratio_idx + 1) % len(self._lissajous_ratios)
            self._freq_x, self._freq_y = self._lissajous_ratios[self._ratio_idx]
            self._slider_count.set(self._freq_x)
            self._slider_grav.set(self._freq_y)

    def _on_action2(self) -> None:
        if self._mode == "particles":
            self._init_particles()
        elif self._mode == "spectrum":
            self._spectrum_peaks = [0.0] * self._spectrum_bars
        elif self._mode == "lissajous":
            self._phase_a = 0.0
            self._phase_b = 0.0

    def _blast_particles(self) -> None:
        w = float(self._canvas.winfo_width() or 600)
        h = float(self._canvas.winfo_height() or 400)
        cx, cy = w / 2.0, h / 2.0
        for p in self._particles:
            dx = p.x - cx
            dy = p.y - cy
            dist = max(1.0, math.sqrt(dx * dx + dy * dy))
            p.vx = (dx / dist) * random.uniform(8.0, 16.0)
            p.vy = (dy / dist) * random.uniform(8.0, 16.0)

    def _on_mode_change(self, mode_str: str) -> None:
        self._mode = mode_str.lower()
        if self._mode == "particles":
            self._lbl_params.configure(text="Physics & Parameters")
            self._lbl_s1.configure(text="Speed Multiplier:")
            self._lbl_s2.configure(text="Particle Swarm Density:")
            self._lbl_s3.configure(text="Gravity Well Pull:")
            self._slider_speed.from_ = 0.1
            self._slider_speed.to = 3.0
            self._slider_speed.set(self._speed_multiplier)
            self._slider_count.from_ = 20.0
            self._slider_count.to = 300.0
            self._slider_count.set(float(self._particle_count))
            self._slider_grav.from_ = 0.0
            self._slider_grav.to = 3.0
            self._slider_grav.set(self._gravity_strength)
            self._btn_act1.text = "💥 Blast Particle Field"
            self._btn_act2.text = "🔄 Reset Simulation"
        elif self._mode == "spectrum":
            self._lbl_params.configure(text="Spectrum & EQ Parameters")
            self._lbl_s1.configure(text="Animation Pace:")
            self._lbl_s2.configure(text="Frequency Band Count:")
            self._lbl_s3.configure(text="Peak Sensitivity:")
            self._slider_speed.from_ = 0.2
            self._slider_speed.to = 3.0
            self._slider_speed.set(self._speed_multiplier)
            self._slider_count.from_ = 16.0
            self._slider_count.to = 64.0
            self._slider_count.set(float(self._spectrum_bars))
            self._slider_grav.from_ = 0.5
            self._slider_grav.to = 2.5
            self._slider_grav.set(1.0)
            self._btn_act1.text = "⚡ Surge Equalizer"
            self._btn_act2.text = "🔄 Reset Peaks"
        elif self._mode == "lissajous":
            self._lbl_params.configure(text="Harmonic Oscilloscope")
            self._lbl_s1.configure(text="Phase Modulation Speed:")
            self._lbl_s2.configure(text="Harmonic Frequency X:")
            self._lbl_s3.configure(text="Harmonic Frequency Y:")
            self._slider_speed.from_ = 0.1
            self._slider_speed.to = 3.0
            self._slider_speed.set(self._speed_multiplier)
            self._slider_count.from_ = 1.0
            self._slider_count.to = 9.0
            self._slider_count.set(self._freq_x)
            self._slider_grav.from_ = 1.0
            self._slider_grav.to = 9.0
            self._slider_grav.set(self._freq_y)
            self._btn_act1.text = "🎛️ Shift Harmonic Ratio"
            self._btn_act2.text = "🔄 Reset Phase Modulation"
        self._canvas.request_redraw()

    def _toggle_animation(self, is_on: bool = True) -> None:
        self._is_animating = self._anim_switch.is_checked
        if self._is_animating:
            self._start_loop()
        else:
            if self._anim_job:
                self.after_cancel(self._anim_job)
                self._anim_job = None

    def _on_canvas_motion(self, event: tk.Event) -> None:
        self._mouse_attractor = (float(event.x), float(event.y))

    def _on_canvas_leave(self, _event: tk.Event) -> None:
        self._mouse_attractor = None

    def _start_loop(self) -> None:
        if not self._is_animating:
            return

        t0 = time.perf_counter()
        self._canvas.paint_and_blit()
        t1 = time.perf_counter()

        self._render_time_ms = (t1 - t0) * 1000.0

        # Update FPS
        self._frame_count += 1
        now = time.perf_counter()
        if now - self._fps_timer >= 0.5:
            self._fps = self._frame_count / max(1e-4, (now - self._fps_timer))
            self._frame_count = 0
            self._fps_timer = now
            self._fps_badge.text = f"{self._fps:.0f} FPS | {self._render_time_ms:.1f} ms"
            self._gauge_fps.value = min(120.0, self._fps)
            self._gauge_load.value = min(100.0, max(2.0, (self._render_time_ms / 16.6) * 100.0))

        self._anim_job = self.after(16, self._start_loop)

    def _paint_canvas(self, surf: Surface) -> None:
        pal = get_theme()
        s = ScalingTracker.get_scaling_factor(self)
        w = float(surf.width)
        h = float(surf.height)
        if w <= 1.0 or h <= 1.0:
            return

        surf.clear(pal.card_bg)

        if self._mode == "particles":
            # 1. Particles Swarm Simulation
            cx = self._mouse_attractor[0] if self._mouse_attractor else w / 2.0
            cy = self._mouse_attractor[1] if self._mouse_attractor else h / 2.0

            # Attractor glow circle
            surf.fill_circle(cx, cy, 8.0 * s, pal.primary)
            surf.stroke_circle(cx, cy, 14.0 * s, pal.primary, stroke_width=1.5 * s)

            for p in self._particles:
                dx = cx - p.x
                dy = cy - p.y
                dist_sq = max(100.0, dx * dx + dy * dy)
                force = (400.0 / dist_sq) * self._gravity_strength * self._speed_multiplier
                dist = math.sqrt(dist_sq)

                p.vx += (dx / dist) * force
                p.vy += (dy / dist) * force

                p.vx *= 0.985
                p.vy *= 0.985

                p.x += p.vx * self._speed_multiplier
                p.y += p.vy * self._speed_multiplier

                if p.x < p.radius:
                    p.x = p.radius
                    p.vx *= -0.8
                elif p.x > w - p.radius:
                    p.x = w - p.radius
                    p.vx *= -0.8

                if p.y < p.radius:
                    p.y = p.radius
                    p.vy *= -0.8
                elif p.y > h - p.radius:
                    p.y = h - p.radius
                    p.vy *= -0.8

                p.history.append((p.x, p.y))
                if len(p.history) > 6:
                    p.history.pop(0)

                if len(p.history) >= 2:
                    p_path = Path()
                    p_path.move_to(p.history[0][0], p.history[0][1])
                    for hx, hy in p.history[1:]:
                        p_path.line_to(hx, hy)
                    surf.stroke_path(p_path, pal.secondary, stroke_width=1.5 * s)

                speed = math.sqrt(p.vx * p.vx + p.vy * p.vy)
                col = pal.accent if speed > 4.0 else (pal.primary if speed > 2.0 else pal.fg)
                surf.fill_circle(p.x, p.y, p.radius * s, col)

        elif self._mode == "spectrum":
            # 2. Neon Audio Spectrum
            pad = 16.0 * s
            usable_w = max(10.0, w - pad * 2.0)
            usable_h = max(10.0, h - pad * 2.0)
            bar_w = max(2.0, (usable_w / self._spectrum_bars) - 3.0 * s)

            self._phase_a += 0.06
            for i in range(self._spectrum_bars):
                f = (i + 1) / float(self._spectrum_bars)
                target = max(
                    0.05,
                    min(
                        0.95,
                        math.sin(self._phase_a * 1.5 + f * 8.0) * 0.4
                        + math.cos(self._phase_a + f * 3.0) * 0.3
                        + 0.35
                        + random.uniform(-0.06, 0.06),
                    ),
                )
                self._spectrum_vals[i] = self._spectrum_vals[i] * 0.4 + target * 0.6

                if self._spectrum_vals[i] > self._spectrum_peaks[i]:
                    self._spectrum_peaks[i] = self._spectrum_vals[i]
                else:
                    self._spectrum_peaks[i] = max(0.05, self._spectrum_peaks[i] - 0.015)

                x = pad + i * (bar_w + 3.0 * s)
                bar_h = self._spectrum_vals[i] * usable_h
                y = (h - pad) - bar_h

                grad = LinearGradient(x, y, x, h - pad)
                grad.add_stop(0.0, pal.primary)
                grad.add_stop(0.6, pal.secondary)
                grad.add_stop(1.0, pal.card_bg)
                surf.fill_rounded_rect(x, y, bar_w, bar_h, 2.0 * s, 2.0 * s, grad)

                peak_y = (h - pad) - self._spectrum_peaks[i] * usable_h
                surf.fill_rounded_rect(x, peak_y, bar_w, 2.0 * s, 1.0 * s, 1.0 * s, pal.accent)

        else:
            # 3. Harmonic Lissajous Oscilloscope
            speed = self._speed_multiplier
            self._phase_a += 0.024 * speed
            cx, cy = w / 2.0, h / 2.0
            rx = (w / 2.0) - 75.0 * s
            ry = (h / 2.0) - 65.0 * s

            # Oscilloscope circular grid / reticle lines
            grid_col = resolve_color_failsafe(pal.border, alpha=0.45)
            surf.stroke_circle(cx, cy, min(rx, ry) * 0.35, grid_col, stroke_width=1.0 * s)
            surf.stroke_circle(cx, cy, min(rx, ry) * 0.70, grid_col, stroke_width=1.0 * s)
            surf.stroke_line(cx - rx - 15.0 * s, cy, cx + rx + 15.0 * s, cy, grid_col, stroke_width=1.0 * s)
            surf.stroke_line(cx, cy - ry - 15.0 * s, cx, cy + ry + 15.0 * s, grid_col, stroke_width=1.0 * s)

            steps = 320
            path = Path()
            head_x, head_y = cx, cy
            for i in range(steps + 1):
                t = (i / steps) * math.tau
                lx = cx + math.sin(t * self._freq_x + self._phase_a) * rx
                ly = cy + math.sin(t * self._freq_y) * ry
                if i == 0:
                    path.move_to(lx, ly)
                else:
                    path.line_to(lx, ly)
                if i == steps:
                    head_x, head_y = lx, ly
            path.close()

            # Outer neon glow pass
            glow_col = resolve_color_failsafe(pal.primary, alpha=0.35)
            surf.stroke_path(path, glow_col, stroke_width=6.0 * s)
            # Main crisp beam
            surf.stroke_path(path, pal.primary, stroke_width=2.4 * s)

            # Secondary harmonic wave (with phase delta and frequency offset)
            inner_path = Path()
            sec_freq_x = self._freq_x + 1.0 if self._freq_x < 6.0 else self._freq_x - 1.0
            sec_freq_y = self._freq_y - 1.0 if self._freq_y > 2.0 else self._freq_y + 1.0
            for i in range(steps + 1):
                t = (i / steps) * math.tau
                lx = cx + math.sin(t * sec_freq_x + self._phase_a * 1.3 + math.pi / 4) * (rx * 0.72)
                ly = cy + math.sin(t * sec_freq_y) * (ry * 0.72)
                if i == 0:
                    inner_path.move_to(lx, ly)
                else:
                    inner_path.line_to(lx, ly)
            inner_path.close()

            glow_sec = resolve_color_failsafe(pal.secondary, alpha=0.35)
            surf.stroke_path(inner_path, glow_sec, stroke_width=4.5 * s)
            surf.stroke_path(inner_path, pal.secondary, stroke_width=1.6 * s)

            # Glowing electron tracer head
            head_glow = resolve_color_failsafe(pal.accent, alpha=0.45)
            surf.fill_circle(head_x, head_y, 4.5 * s, pal.accent)
            surf.stroke_circle(head_x, head_y, 9.5 * s, head_glow, stroke_width=2.0 * s)

    def _on_theme_change(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg, palette=pal)
        self._canvas.request_redraw()
        self._gauge_fps.request_redraw()
        self._gauge_load.request_redraw()

    def destroy(self) -> None:
        if self._anim_job:
            self.after_cancel(self._anim_job)
            self._anim_job = None
        super().destroy()


def main():
    root = tk.Tk()
    root.title("tkblend - 60 FPS Real-time Engine Lab")
    root.geometry("1080x720")
    root.minsize(920, 600)

    app = RealtimeVisualizer(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
