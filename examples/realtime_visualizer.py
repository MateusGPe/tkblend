#!/usr/bin/env python3
"""
tkblend Showcase: High-Performance 60 FPS Real-time Visualizer & Physics Simulator.
Demonstrates:
  - Raw Blend2D rendering speed and zero-copy blitting into Tkinter PhotoImage buffers
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
import time
import tkinter as tk
from typing import Optional, List, Tuple

import tkblend as tb
from tkblend import (
    BlendCanvas,
    Surface,
    LinearGradient,
    RadialGradient,
    Path,
    Card,
    Button,
    Slider,
    SegmentedButton,
    OptionMenu,
    Switch,
    Badge,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
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
        self._is_running = True
        self._mode = "Particle Swarm"
        self._particle_count = 180
        self._particles: List[Particle] = []
        self._mouse_pos: Optional[Tuple[float, float]] = None
        self._gravity_strength = 0.8
        self._trail_length = 6

        # Spectrum state
        self._spectrum_bands = 32
        self._spectrum_vals = [random.uniform(0.1, 0.8) for _ in range(self._spectrum_bands)]
        self._spectrum_peaks = list(self._spectrum_vals)

        # Lissajous state
        self._freq_x = 3.0
        self._freq_y = 4.0
        self._phase = 0.0

        # Performance telemetry
        self._frame_count = 0
        self._last_time = time.perf_counter()
        self._fps = 60.0
        self._render_time_ms = 0.5
        self._timer_id: Optional[str] = None

        self._init_particles()
        self._build_ui()
        self._start_animation_loop()

    def _init_particles(self) -> None:
        self._particles = [Particle(random.uniform(50, 550), random.uniform(50, 450)) for _ in range(self._particle_count)]

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Header Bar
        hdr = tk.Frame(self, background=pal.bg)
        hdr.pack(fill="x", padx=20, pady=(16, 8))

        tbox = tk.Frame(hdr, background=pal.bg)
        tbox.pack(side="left")

        tk.Label(tbox, text="Real-Time 60 FPS Visualizer", font=("Segoe UI", 18, "bold"), fg=pal.fg, bg=pal.bg).pack(anchor="w")
        tk.Label(tbox, text="Stress-testing Blend2D zero-copy blits with live physics and animations", font=("Segoe UI", 10), fg=pal.fg_subtle, bg=pal.bg).pack(anchor="w")

        cbox = tk.Frame(hdr, background=pal.bg)
        cbox.pack(side="right")

        # Telemetry Badges
        self._fps_badge = Badge(cbox, text="FPS: 60.0", color=pal.success, text_color="#ffffff", height=24)
        self._fps_badge.pack(side="left", padx=6)

        self._ms_badge = Badge(cbox, text="Render: 0.8 ms", color=pal.primary, text_color="#ffffff", height=24)
        self._ms_badge.pack(side="left", padx=6)

        OptionMenu(
            cbox,
            values=list(get_available_themes()),
            default_value="dark",
            command=self._on_theme_changed,
            width=140,
            height=32,
        ).pack(side="left", padx=6)

        # Mode Selection Bar
        mode_bar = tk.Frame(self, background=pal.bg)
        mode_bar.pack(fill="x", padx=20, pady=6)

        SegmentedButton(
            mode_bar,
            values=["Particle Swarm", "Audio Spectrum", "Harmonic Lissajous"],
            default_value="Particle Swarm",
            command=self._set_mode,
            width=480,
            height=32,
        ).pack(side="left")

        self._play_btn = Button(mode_bar, text="Pause Animation", width=140, height=32, command=self._toggle_running)
        self._play_btn.pack(side="right")

        # Main Workspace: Left Canvas + Right Controls
        workspace = tk.Frame(self, background=pal.bg)
        workspace.pack(fill="both", expand=True, padx=20, pady=(6, 16))

        # Main Canvas Card
        canvas_card = Card(workspace, width=640, height=540, rx=14, ry=14, elevation=6)
        canvas_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        c_body = canvas_card.body
        self._canvas = BlendCanvas(c_body, width=620, height=520, bg="card_bg")
        self._canvas.pack(fill="both", expand=True, padx=6, pady=6)

        # Mouse tracking for particle gravity well
        self._canvas.bind("<Motion>", self._on_mouse_move)
        self._canvas.bind("<Leave>", self._on_mouse_leave)

        # Right Telemetry & Controls Panel Card
        ctrl_card = Card(workspace, title="Simulation Controls", width=260, height=540, rx=14, ry=14, elevation=6)
        ctrl_card.pack(side="right", fill="y", padx=(6, 0))
        self._setup_ctrl_panel(ctrl_card.body)

        cascade_bg_to_children(self, pal.bg)

    def _setup_ctrl_panel(self, container: tk.Frame) -> None:
        pal = get_theme()

        p_box = tk.Frame(container, background=pal.card_bg)
        p_box.pack(fill="both", expand=True, padx=12, pady=8)

        # Particle Count Slider
        tk.Label(p_box, text="Particle Count (50 - 400):", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w")
        self._count_slider = Slider(p_box, from_=50, to=400, value=self._particle_count, width=220, height=22, command=self._set_particle_count)
        self._count_slider.pack(fill="x", pady=(2, 8))

        # Gravity Slider
        tk.Label(p_box, text="Gravity Well Attraction:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w")
        Slider(p_box, from_=0, to=2.0, value=self._gravity_strength, width=220, height=22, command=self._set_gravity).pack(fill="x", pady=(2, 8))

        # Trail Length Slider
        tk.Label(p_box, text="Motion Trail Decay:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w")
        Slider(p_box, from_=1, to=15, value=self._trail_length, width=220, height=22, command=self._set_trail_length).pack(fill="x", pady=(2, 8))

        # Lissajous Frequency Controls
        tk.Label(p_box, text="Oscilloscope Freq X:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w", pady=(6, 0))
        Slider(p_box, from_=1, to=10, value=self._freq_x, width=220, height=22, command=self._set_freq_x).pack(fill="x", pady=(2, 8))

        tk.Label(p_box, text="Oscilloscope Freq Y:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w", pady=(2, 0))
        Slider(p_box, from_=1, to=10, value=self._freq_y, width=220, height=22, command=self._set_freq_y).pack(fill="x", pady=(2, 8))

        Button(p_box, text="Reset Simulation", width=220, height=32, bootstyle="secondary", command=self._init_particles).pack(pady=12)

    def _set_mode(self, mode: str) -> None:
        self._mode = mode

    def _toggle_running(self) -> None:
        self._is_running = not self._is_running
        self._play_btn.set_text("Resume Animation" if not self._is_running else "Pause Animation")

    def _set_particle_count(self, val: float) -> None:
        self._particle_count = int(val)
        self._init_particles()

    def _set_gravity(self, val: float) -> None:
        self._gravity_strength = float(val)

    def _set_trail_length(self, val: float) -> None:
        self._trail_length = int(val)

    def _set_freq_x(self, val: float) -> None:
        self._freq_x = float(val)

    def _set_freq_y(self, val: float) -> None:
        self._freq_y = float(val)

    def _on_mouse_move(self, event) -> None:
        self._mouse_pos = (float(event.x), float(event.y))

    def _on_mouse_leave(self, _event) -> None:
        self._mouse_pos = None

    def _start_animation_loop(self) -> None:
        if self._is_running:
            t0 = time.perf_counter()
            self._render_frame()
            t1 = time.perf_counter()

            self._render_time_ms = (t1 - t0) * 1000.0
            self._frame_count += 1
            if self._frame_count % 15 == 0:
                dt = t1 - self._last_time
                if dt > 0:
                    self._fps = 15.0 / dt
                self._last_time = t1
                self._fps_badge.set_text(f"FPS: {self._fps:.1f}")
                self._ms_badge.set_text(f"Render: {self._render_time_ms:.2f} ms")

        # Target ~60 FPS (16ms interval)
        self._timer_id = self.after(16, self._start_animation_loop)

    def _render_frame(self) -> None:
        surf = self._canvas.surface
        if surf is None:
            return

        pal = get_theme()
        w = float(self._canvas.canvas_width)
        h = float(self._canvas.canvas_height)

        surf.clear(pal.card_bg)

        if self._mode == "Particle Swarm":
            self._render_particles(surf, w, h, pal)
        elif self._mode == "Audio Spectrum":
            self._render_spectrum(surf, w, h, pal)
        elif self._mode == "Harmonic Lissajous":
            self._render_lissajous(surf, w, h, pal)

        surf.blit(self._canvas.photo)

    def _render_particles(self, surf: Surface, w: float, h: float, pal) -> None:
        # Update physics
        mx, my = self._mouse_pos if self._mouse_pos else (w / 2.0, h / 2.0)

        for p in self._particles:
            if self._mouse_pos:
                dx = mx - p.x
                dy = my - p.y
                dist = math.hypot(dx, dy)
                if dist > 5.0:
                    force = self._gravity_strength * 12.0 / max(30.0, dist)
                    p.vx += (dx / dist) * force
                    p.vy += (dy / dist) * force

            # Speed damping
            p.vx *= 0.98
            p.vy *= 0.98

            p.x += p.vx
            p.y += p.vy

            # Bounds bounce
            if p.x < 10.0:
                p.x = 10.0
                p.vx = abs(p.vx) * 0.9
            elif p.x > w - 10.0:
                p.x = w - 10.0
                p.vx = -abs(p.vx) * 0.9

            if p.y < 10.0:
                p.y = 10.0
                p.vy = abs(p.vy) * 0.9
            elif p.y > h - 10.0:
                p.y = h - 10.0
                p.vy = -abs(p.vy) * 0.9

            p.history.append((p.x, p.y))
            if len(p.history) > self._trail_length:
                p.history.pop(0)

            # Draw particle trail
            if len(p.history) >= 2:
                tp = Path()
                tp.move_to(p.history[0][0], p.history[0][1])
                for pt in p.history[1:]:
                    tp.line_to(pt[0], pt[1])
                surf.stroke_path(tp, pal.secondary + "44" if len(pal.secondary) == 7 else pal.secondary, stroke_width=1.5)

            # Draw glowing head
            spd = math.hypot(p.vx, p.vy)
            col = pal.accent if spd > 3.0 else (pal.primary if spd > 1.5 else pal.secondary)
            surf.fill_circle(p.x, p.y, p.radius, col)

        # Draw gravity well cursor target
        if self._mouse_pos:
            surf.stroke_circle(mx, my, 18.0, pal.accent, stroke_width=2.0)
            surf.fill_circle(mx, my, 4.0, "#ffffff")

    def _render_spectrum(self, surf: Surface, w: float, h: float, pal) -> None:
        pad_x = 40.0
        pad_y = 60.0
        avail_w = w - pad_x * 2
        avail_h = h - pad_y * 2
        bw = (avail_w / self._spectrum_bands) - 4.0

        for i in range(self._spectrum_bands):
            # Dynamic simulated jitter
            target = math.sin(time.perf_counter() * 3.0 + i * 0.3) * 0.4 + 0.5
            target += random.uniform(-0.15, 0.15)
            target = max(0.05, min(0.95, target))

            self._spectrum_vals[i] += (target - self._spectrum_vals[i]) * 0.25

            # Peak hold decay
            if self._spectrum_vals[i] > self._spectrum_peaks[i]:
                self._spectrum_peaks[i] = self._spectrum_vals[i]
            else:
                self._spectrum_peaks[i] = max(0.05, self._spectrum_peaks[i] - 0.008)

            bx = pad_x + i * (bw + 4.0)
            bar_h = self._spectrum_vals[i] * avail_h
            by = pad_y + avail_h - bar_h

            # Equalizer Bar Gradient
            bg_grad = LinearGradient(bx, by, bx, pad_y + avail_h)
            bg_grad.add_stop(0.0, pal.accent or "#ec4899")
            bg_grad.add_stop(0.5, pal.primary or "#3b82f6")
            bg_grad.add_stop(1.0, pal.secondary or "#06b6d4")
            surf.fill_rounded_rect(bx, by, bw, bar_h, 3.0, 3.0, bg_grad)

            # Peak Indicator Line
            peak_y = pad_y + avail_h - (self._spectrum_peaks[i] * avail_h)
            surf.fill_rect(bx, peak_y, bw, 2.0, "#ffffff")

        surf.draw_text("32-Band Neon Audio Spectrum & Peak Hold", pad_x, 30.0, font_size=12.0, color=pal.fg)

    def _render_lissajous(self, surf: Surface, w: float, h: float, pal) -> None:
        cx, cy = w / 2.0, h / 2.0
        rx = min(w, h) * 0.4
        ry = rx

        self._phase += 0.03

        pts = []
        samples = 300
        for i in range(samples):
            t = (i / samples) * 2.0 * math.pi
            x = cx + rx * math.sin(self._freq_x * t + self._phase)
            y = cy + ry * math.sin(self._freq_y * t)
            pts.append((x, y))

        if pts:
            lp = Path()
            lp.move_to(pts[0][0], pts[0][1])
            for pt in pts[1:]:
                lp.line_to(pt[0], pt[1])
            lp.close()

            surf.stroke_path(lp, pal.primary or "#3b82f6", stroke_width=3.0)

            # Glowing inner harmonic
            surf.stroke_path(lp, "#ffffff", stroke_width=1.0)

        surf.draw_text(f"Lissajous Curve ({self._freq_x:.1f} : {self._freq_y:.1f})", 30.0, 30.0, font_size=12.0, color=pal.fg)

    def _on_theme_changed(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg)

    def destroy(self) -> None:
        if self._timer_id:
            try:
                self.after_cancel(self._timer_id)
            except Exception:
                pass
        super().destroy()


def main():
    root = tk.Tk()
    root.title("tkblend 60 FPS Real-Time Vector Visualizer")
    root.geometry("1020x720")
    root.minsize(900, 600)

    ScalingTracker.activate_high_dpi_awareness()
    set_theme("dark")

    vis = RealtimeVisualizer(root)
    vis.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
