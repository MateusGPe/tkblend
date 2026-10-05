#!/usr/bin/env python3
"""
tkblend Multimedia & Studio Audio Telemetry Dashboard Showcase.
Demonstrates:
  - High-performance real-time vector audio spectrum visualizer (BlendCanvas)
  - Stereo VU meters and peak decibel telemetry with LED and gradient modes
  - Audio studio track playlist table with sorting and track duration
  - Pure BaseControl controls: Slider, CircularProgress / Dial, Button, Switch, Badge, Card
  - Dynamic runtime palette switching across 13+ themes
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
    Frame,
    ScrollableFrame,
    Button,
    Slider,
    CircularProgress,
    Gauge,
    Table,
    Switch,
    SegmentedButton,
    OptionMenu,
    Badge,
    Sparkline,
    BlendCanvas,
    LinearGradient,
    Path,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    ScalingTracker,
)


class AudioVisualizerCanvas(BlendCanvas):
    """Real-time vector audio spectrum visualizer and waveform oscillograph."""

    def __init__(self, master: tk.Misc, width: int = 580, height: int = 220, **kwargs):
        self._mode = "spectrum"  # 'spectrum' or 'wave'
        self._num_bars = 48
        self._bars: List[float] = [random.uniform(0.1, 0.9) for _ in range(self._num_bars)]
        self._peaks: List[float] = list(self._bars)
        self._phase = 0.0

        super().__init__(master, width=width, height=height, bg="card_bg", **kwargs)

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self.redraw()

    def update_audio(self) -> None:
        self._phase += 0.08
        for i in range(self._num_bars):
            # Harmonic frequency distribution
            f = (i + 1) / float(self._num_bars)
            amp = math.sin(self._phase * 2.0 + f * 10.0) * 0.4 + math.cos(self._phase * 1.5 + f * 4.0) * 0.3 + 0.35
            amp += random.uniform(-0.08, 0.08)
            val = max(0.05, min(0.98, amp))
            self._bars[i] = self._bars[i] * 0.4 + val * 0.6

            # Peak tracking
            if self._bars[i] > self._peaks[i]:
                self._peaks[i] = self._bars[i]
            else:
                self._peaks[i] = max(0.05, self._peaks[i] - 0.02)

        self.redraw()

    def _redraw(self) -> None:
        if self._surface is None:
            return

        pal = get_theme()
        s = ScalingTracker.get_scaling_factor(self)
        w = float(self._canvas_width)
        h = float(self._canvas_height)

        self._surface.clear(pal.card_bg)

        pad = 12.0 * s
        usable_w = w - pad * 2.0
        usable_h = h - pad * 2.0

        if self._mode == "spectrum":
            # Spectrum Analyzer Bars
            bar_w = max(2.0 * s, (usable_w / self._num_bars) - 2.5 * s)
            for i, val in enumerate(self._bars):
                x = pad + i * (bar_w + 2.5 * s)
                bar_h = val * usable_h
                y = (h - pad) - bar_h

                # Gradient bar fill
                grad = LinearGradient(x, y, x, h - pad)
                grad.add_stop(0.0, pal.primary)
                grad.add_stop(0.6, pal.secondary)
                grad.add_stop(1.0, pal.card_bg)
                self._surface.fill_rounded_rect(x, y, bar_w, bar_h, 2.0 * s, 2.0 * s, grad)

                # Peak cap
                peak_y = (h - pad) - self._peaks[i] * usable_h
                self._surface.fill_rounded_rect(x, peak_y, bar_w, 2.5 * s, 1.0 * s, 1.0 * s, pal.accent)

        else:
            # Oscilloscope Waveform
            pts = []
            cy = h / 2.0
            for i in range(self._num_bars):
                x = pad + (i / (self._num_bars - 1)) * usable_w
                val = (self._bars[i] - 0.5) * 2.0
                y = cy + val * (usable_h * 0.45)
                pts.append((x, y))

            path = Path()
            path.move_to(pts[0][0], pts[0][1])
            for i in range(1, len(pts)):
                path.line_to(pts[i][0], pts[i][1])

            # Glow line
            self._surface.stroke_path(path, pal.primary, stroke_width=2.5 * s)

            # Center grid line
            self._surface.stroke_line(pad, cy, w - pad, cy, pal.card_border, stroke_width=1.0 * s)


class VUMeterWidget(BlendCanvas):
    """Stereo LED / Gradient Volume Unit Meter."""

    def __init__(self, master: tk.Misc, width: int = 40, height: int = 180, **kwargs):
        self._val_l = 0.65
        self._val_r = 0.58
        super().__init__(master, width=width, height=height, bg="card_bg", **kwargs)

    def set_levels(self, l: float, r: float) -> None:
        self._val_l = max(0.0, min(1.0, float(l)))
        self._val_r = max(0.0, min(1.0, float(r)))
        self.redraw()

    def _redraw(self) -> None:
        if self._surface is None:
            return

        pal = get_theme()
        s = ScalingTracker.get_scaling_factor(self)
        w = float(self._canvas_width)
        h = float(self._canvas_height)

        self._surface.clear(pal.card_bg)

        pad = 6.0 * s
        ch_w = (w - pad * 3.0) / 2.0
        usable_h = h - pad * 2.0
        num_segments = 24
        seg_h = (usable_h / num_segments) - 1.5 * s

        for ch_idx, val in enumerate((self._val_l, self._val_r)):
            ch_x = pad + ch_idx * (ch_w + pad)
            active_segs = int(val * num_segments)

            for i in range(num_segments):
                seg_y = (h - pad) - (i + 1) * (seg_h + 1.5 * s)
                is_active = (i <= active_segs)

                if is_active:
                    frac = i / float(num_segments)
                    if frac > 0.85:
                        col = pal.destructive
                    elif frac > 0.65:
                        col = pal.warning
                    else:
                        col = pal.success
                else:
                    col = pal.track_bg

                self._surface.fill_rounded_rect(ch_x, seg_y, ch_w, seg_h, 1.5 * s, 1.5 * s, col)


class MultimediaDashboard(tk.Frame):
    """Studio Audio Telemetry & Multimedia Player Suite."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._is_playing = True
        self._timer_job: Optional[str] = None
        self._build_ui()
        self._start_playback_loop()

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Header Card
        header = Card(self, height=64, corner_radius=10, bg_color=pal.card_bg)
        header.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(
            header,
            text="🎧 BlendStudio Pro Audio Workstation",
            font=("sans-serif", 15, "bold"),
            bg=header.bg_color,
            fg=pal.fg,
        ).pack(side="left", padx=16)

        Badge(header, text="48 kHz / 24-bit PCM", variant="primary").pack(side="left", padx=4)

        # Theme Selector
        self._theme_opt = OptionMenu(
            header,
            values=get_available_themes(),
            default_value=pal.name,
            command=self._on_theme_change,
            width=130,
            height=30,
        )
        self._theme_opt.pack(side="right", padx=14)

        # Master Level & Mute
        self._mute_switch = Switch(header, is_on=False, text="Mute", width=75, height=26)
        self._mute_switch.pack(side="right", padx=8)

        # Main Central Grid
        mid_frame = tk.Frame(self, bg=pal.bg)
        mid_frame.pack(fill="both", expand=True, padx=16, pady=6)

        # Left Column: Visualizer & Player
        left_col = tk.Frame(mid_frame, bg=pal.bg)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # Visualizer Card
        viz_card = Card(left_col, height=270, corner_radius=10, bg_color=pal.card_bg)
        viz_card.pack(fill="both", expand=True, pady=(0, 6))

        viz_hdr = tk.Frame(viz_card, bg=viz_card.bg_color)
        viz_hdr.pack(fill="x", padx=14, pady=(10, 4))

        tk.Label(viz_hdr, text="Master Output Visualizer (RTA)", font=("sans-serif", 11, "bold"), bg=viz_card.bg_color, fg=pal.fg).pack(side="left")

        self._mode_seg = SegmentedButton(
            viz_hdr,
            values=["Spectrum", "Waveform"],
            selected_value="Spectrum",
            command=self._on_viz_mode_changed,
            height=26,
            width=160,
        )
        self._mode_seg.pack(side="right")

        # Visualizer Canvas + VU Meter Box
        viz_content = tk.Frame(viz_card, bg=viz_card.bg_color)
        viz_content.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        self._visualizer = AudioVisualizerCanvas(viz_content, height=190)
        self._visualizer.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._vu_meter = VUMeterWidget(viz_content, width=38, height=190)
        self._vu_meter.pack(side="right", fill="y")

        # Playback Transport Card
        player_card = Card(left_col, height=140, corner_radius=10, bg_color=pal.card_bg)
        player_card.pack(fill="x", pady=(6, 0))

        # Track Info Row
        track_row = tk.Frame(player_card, bg=player_card.bg_color)
        track_row.pack(fill="x", padx=16, pady=(10, 2))

        self._track_title = tk.Label(track_row, text="Cyberpunk Symphony - Neon Overdrive (Master Mix)", font=("sans-serif", 11, "bold"), bg=player_card.bg_color, fg=pal.fg)
        self._track_title.pack(side="left")

        self._time_lbl = tk.Label(track_row, text="02:34 / 04:18", font=("sans-serif", 10), bg=player_card.bg_color, fg=pal.text_muted)
        self._time_lbl.pack(side="right")

        # Timeline Slider
        self._timeline_slider = Slider(player_card, value=58.0, height=22)
        self._timeline_slider.pack(fill="x", padx=16, pady=2)

        # Controls Button Bar
        ctrl_bar = tk.Frame(player_card, bg=player_card.bg_color)
        ctrl_bar.pack(fill="x", padx=16, pady=(4, 10))

        btn_prev = Button(ctrl_bar, text="⏮ Prev", width=70, height=28)
        btn_prev.pack(side="left", padx=3)

        self._btn_play = Button(ctrl_bar, text="⏸ Pause", width=85, height=28, command=self._toggle_play)
        self._btn_play.pack(side="left", padx=3)

        btn_next = Button(ctrl_bar, text="Next ⏭", width=70, height=28)
        btn_next.pack(side="left", padx=3)

        # Volume Slider
        vol_box = tk.Frame(ctrl_bar, bg=player_card.bg_color)
        vol_box.pack(side="right", padx=4)
        tk.Label(vol_box, text="🔊 Vol:", font=("sans-serif", 10), bg=player_card.bg_color, fg=pal.text_muted).pack(side="left", padx=2)
        self._vol_slider = Slider(vol_box, value=82.0, width=110, height=22)
        self._vol_slider.pack(side="left", padx=2)

        # Right Column: DSP Channel Dials & Playlist
        right_col = tk.Frame(mid_frame, width=380, bg=pal.bg)
        right_col.pack(side="right", fill="both", padx=(6, 0))

        # Channel Dials Card
        dsp_card = Card(right_col, height=160, corner_radius=10, bg_color=pal.card_bg)
        dsp_card.pack(fill="x", pady=(0, 6))

        tk.Label(dsp_card, text="DSP Equalizer & Gain Stages", font=("sans-serif", 11, "bold"), bg=dsp_card.bg_color, fg=pal.fg).pack(padx=14, pady=(8, 2))

        dials_box = tk.Frame(dsp_card, bg=dsp_card.bg_color)
        dials_box.pack(fill="both", expand=True, padx=10, pady=(2, 8))

        self._dial_gain = CircularProgress(dials_box, size=75, value=78.0, title="Master Gain", unit="dB", stroke_width=6)
        self._dial_gain.pack(side="left", fill="both", expand=True)

        self._dial_low = CircularProgress(dials_box, size=75, value=62.0, title="Bass Boost", unit="Hz", stroke_width=6, fill_color=pal.secondary)
        self._dial_low.pack(side="left", fill="both", expand=True)

        self._dial_high = CircularProgress(dials_box, size=75, value=85.0, title="Treble Air", unit="kHz", stroke_width=6, fill_color=pal.accent)
        self._dial_high.pack(side="left", fill="both", expand=True)

        # Playlist Table Card
        pl_card = Card(right_col, corner_radius=10, bg_color=pal.card_bg)
        pl_card.pack(fill="both", expand=True, pady=(6, 0))

        tk.Label(pl_card, text="Session Playlist Queue", font=("sans-serif", 11, "bold"), bg=pl_card.bg_color, fg=pal.fg).pack(anchor="w", padx=14, pady=(8, 2))

        pl_cols = [
            {"name": "track", "title": "Title", "width": 140},
            {"name": "bpm", "title": "BPM", "width": 45},
            {"name": "key", "title": "Key", "width": 45},
            {"name": "duration", "title": "Time", "width": 50},
        ]

        pl_data = [
            {"track": "1. Neon Overdrive", "bpm": "128", "key": "F#m", "duration": "04:18"},
            {"track": "2. Solar Flare", "bpm": "132", "key": "Am", "duration": "03:45"},
            {"track": "3. Quantum Shift", "bpm": "124", "key": "Dm", "duration": "05:12"},
            {"track": "4. Midnight Echoes", "bpm": "110", "key": "Em", "duration": "04:02"},
            {"track": "5. Hyperdrive Bass", "bpm": "140", "key": "Gm", "duration": "03:29"},
            {"track": "6. Synthwave Horizon", "bpm": "126", "key": "C#m", "duration": "04:55"},
        ]

        self._pl_table = Table(pl_card, columns=pl_cols, data=pl_data, height=180)
        self._pl_table.pack(fill="both", expand=True, padx=8, pady=(2, 8))

        cascade_bg_to_children(self, pal.bg, palette=pal)

    def _on_theme_change(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg, palette=pal)
        self._visualizer.redraw()
        self._vu_meter.redraw()

    def _on_viz_mode_changed(self, mode_str: str) -> None:
        self._visualizer.set_mode(mode_str.lower())

    def _toggle_play(self) -> None:
        self._is_playing = not self._is_playing
        if self._is_playing:
            self._btn_play.text = "⏸ Pause"
            self._start_playback_loop()
        else:
            self._btn_play.text = "▶ Play"
            if self._timer_job:
                self.after_cancel(self._timer_job)
                self._timer_job = None

    def _start_playback_loop(self) -> None:
        if not self._is_playing:
            return

        self._visualizer.update_audio()

        # Update VU meters
        vl = max(0.1, min(0.98, random.uniform(0.4, 0.85)))
        vr = max(0.1, min(0.98, vl + random.uniform(-0.15, 0.15)))
        self._vu_meter.set_levels(vl, vr)

        self._timer_job = self.after(40, self._start_playback_loop)

    def destroy(self) -> None:
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None
        super().destroy()


def main():
    root = tk.Tk()
    root.title("tkblend - Multimedia Studio Suite")
    root.geometry("1060x700")
    root.minsize(880, 580)

    app = MultimediaDashboard(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
