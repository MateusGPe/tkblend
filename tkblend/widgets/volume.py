"""
High-performance pure vector Volume and Audio Telemetry widgets for tkblend.
Zero TTK dependencies. Provides VolumeControl (interactive slider with dynamic mute/speaker icon)
and VUMeter / AudioMeter (real-time stereo/mono LED segmented and gradient peak level meters).
"""

from __future__ import annotations
import math
import tkinter as tk
from typing import Optional, Callable, Union, Tuple

from tkblend.surface import Surface, Path, LinearGradient, ColorLike, parse_color
from tkblend.theme import get_theme, Palette
from tkblend.widgets.base import Widget, ScalingTracker, _resolve_color


class VolumeControl(Widget):
    """
    Interactive volume slider with dynamic speaker icon (Muted/Low/Med/High),
    click-to-mute toggle, percentage readout, and responsive track dragging.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 220,
        height: int = 34,
        value: float = 75.0,
        min_val: float = 0.0,
        max_val: float = 100.0,
        show_value: bool = True,
        show_icon: bool = True,
        on_change: Optional[Callable[[float], None]] = None,
        command: Optional[Callable[[float], None]] = None,
        track_color: Optional[ColorLike] = None,
        active_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._min = float(min_val)
        self._max = float(max_val)
        self._value = max(self._min, min(self._max, float(value)))
        self._last_nonzero_value = self._value if self._value > 0 else 50.0
        self._is_muted = (self._value == 0.0)

        self._show_value = show_value
        self._show_icon = show_icon
        self._on_change = on_change or command
        self._explicit_track_color = track_color
        self._explicit_active_color = active_color

        self._is_dragging = False

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            tag_name="volume_control",
            **kwargs,
        )

        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

    # -------------------------------------------------------------------------
    # Properties & State
    # -------------------------------------------------------------------------

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self.set_value(val)

    def set_value(self, val: float) -> None:
        """Update volume level [min_val, max_val] and trigger redraw."""
        self._value = max(self._min, min(self._max, float(val)))
        if self._value > 0:
            self._last_nonzero_value = self._value
            self._is_muted = False
        else:
            self._is_muted = True
        self.render()
        if self._on_change:
            self._on_change(self._value)

    @property
    def is_muted(self) -> bool:
        return self._is_muted

    def toggle_mute(self) -> None:
        """Toggle mute state, restoring previous volume when unmuting."""
        if self._is_muted or self._value == 0.0:
            self._is_muted = False
            self.set_value(self._last_nonzero_value if self._last_nonzero_value > 0 else 50.0)
        else:
            self._last_nonzero_value = self._value
            self._is_muted = True
            self._value = 0.0
            self.render()
            if self._on_change:
                self._on_change(0.0)

    # -------------------------------------------------------------------------
    # Layout & Mouse Events
    # -------------------------------------------------------------------------

    def _get_layout(self) -> dict:
        w = float(self._widget_w)
        h = float(self._widget_h)
        s = self._scale

        icon_w = 32.0 * s if self._show_icon else 0.0
        val_w = 40.0 * s if self._show_value else 0.0

        track_pad_x = 8.0 * s
        track_x = icon_w + track_pad_x
        track_w = max(20.0 * s, w - track_x - val_w - track_pad_x)
        track_h = 6.0 * s
        track_y = (h - track_h) / 2.0

        return {
            "icon_rect": (0.0, 0.0, icon_w, h),
            "track_rect": (track_x, track_y, track_w, track_h),
            "val_rect": (w - val_w, 0.0, val_w, h),
        }

    def _on_mouse_down(self, event: tk.Event) -> None:
        mx = float(event.x) * self._scale
        my = float(event.y) * self._scale
        layout = self._get_layout()

        # Check Icon click (Mute toggle)
        if self._show_icon:
            ix, iy, iw, ih = layout["icon_rect"]
            if ix <= mx <= ix + iw and iy <= my <= iy + ih:
                self.toggle_mute()
                return

        # Check Track click / drag
        tx, _, tw, _ = layout["track_rect"]
        self._is_dragging = True
        self._update_value_from_mouse(mx, tx, tw)

    def _on_mouse_drag(self, event: tk.Event) -> None:
        if not self._is_dragging:
            return
        mx = float(event.x) * self._scale
        layout = self._get_layout()
        tx, _, tw, _ = layout["track_rect"]
        self._update_value_from_mouse(mx, tx, tw)

    def _on_mouse_up(self, _event: tk.Event) -> None:
        self._is_dragging = False

    def _update_value_from_mouse(self, mx: float, tx: float, tw: float) -> None:
        ratio = max(0.0, min(1.0, (mx - tx) / tw))
        new_val = self._min + ratio * (self._max - self._min)
        self.set_value(new_val)

    # -------------------------------------------------------------------------
    # Render Pipeline
    # -------------------------------------------------------------------------

    def render(self) -> None:
        if self._surface is None or self._photo is None:
            return

        w = float(self._widget_w)
        h = float(self._widget_h)
        s = self._scale
        pal = get_theme()

        self._surface.clear(self._parent_bg)

        layout = self._get_layout()
        accent = _resolve_color(self._explicit_active_color, pal.primary, pal)
        track_col = _resolve_color(self._explicit_track_color, pal.track_bg, pal)

        # 1. Render Dynamic Speaker Icon
        if self._show_icon:
            self._render_speaker_icon(s, h, pal)

        # 2. Render Track & Active Fill
        tx, ty, tw, th = layout["track_rect"]
        rx = th / 2.0
        self._surface.fill_rounded_rect(tx, ty, tw, th, rx, rx, track_col)

        rng = max(1.0, self._max - self._min)
        norm = (self._value - self._min) / rng
        active_w = norm * tw

        if active_w > 0:
            self._surface.fill_rounded_rect(tx, ty, active_w, th, rx, rx, accent)

        # Slider Knob
        knob_cx = tx + active_w
        knob_cy = ty + th / 2.0
        knob_r = 7.0 * s
        self._surface.fill_circle(knob_cx, knob_cy, knob_r, pal.thumb_color)
        self._surface.stroke_circle(knob_cx, knob_cy, knob_r, accent, stroke_width=2.0 * s)

        # 3. Render Value Readout Label
        if self._show_value:
            vx, vy, vw, vh = layout["val_rect"]
            pct = int(round(norm * 100.0))
            text = "MUTE" if self._is_muted or self._value == 0 else f"{pct}%"
            col = pal.danger if (self._is_muted or self._value == 0) else pal.fg
            self._surface.draw_text(
                text,
                vx + vw / 2.0,
                (h - 10.0 * s) / 2.0,
                font_size=9.5 * s,
                bold=True,
                color=col,
                align="center",
            )

        self._surface.blit(self._photo)

    def _render_speaker_icon(self, s: float, h: float, pal: Palette) -> None:
        cx = 16.0 * s
        cy = h / 2.0
        icon_col = pal.danger if (self._is_muted or self._value == 0) else pal.fg

        # Speaker Body & Cone
        p = Path()
        # Back rectangle
        p.move_to(cx - 9.0 * s, cy - 3.5 * s)
        p.line_to(cx - 5.5 * s, cy - 3.5 * s)
        # Flare to cone
        p.line_to(cx - 1.0 * s, cy - 7.5 * s)
        p.line_to(cx - 1.0 * s, cy + 7.5 * s)
        p.line_to(cx - 5.5 * s, cy + 3.5 * s)
        p.line_to(cx - 9.0 * s, cy + 3.5 * s)
        p.close()
        self._surface.fill_path(p, icon_col)

        # Sound Waves or Mute Cross
        rng = max(1.0, self._max - self._min)
        norm = self._value / rng

        if self._is_muted or self._value == 0:
            # Draw 'X' for mute
            self._surface.draw_line(cx + 3.0 * s, cy - 4.0 * s, cx + 9.0 * s, cy + 4.0 * s, icon_col, stroke_width=1.6 * s)
            self._surface.draw_line(cx + 9.0 * s, cy - 4.0 * s, cx + 3.0 * s, cy + 4.0 * s, icon_col, stroke_width=1.6 * s)
        else:
            # Wave 1 (Low)
            p1 = Path()
            p1.arc_to(cx - 1.0 * s, cy, 5.0 * s, 5.0 * s, -math.pi / 4.0, math.pi / 2.0)
            self._surface.stroke_path(p1, icon_col, stroke_width=1.5 * s)

            # Wave 2 (Medium)
            if norm > 0.33:
                p2 = Path()
                p2.arc_to(cx - 1.0 * s, cy, 8.5 * s, 8.5 * s, -math.pi / 3.5, math.pi / 1.75)
                self._surface.stroke_path(p2, icon_col, stroke_width=1.5 * s)

            # Wave 3 (High)
            if norm > 0.66:
                p3 = Path()
                p3.arc_to(cx - 1.0 * s, cy, 12.0 * s, 12.0 * s, -math.pi / 3.0, math.pi / 1.5)
                self._surface.stroke_path(p3, icon_col, stroke_width=1.5 * s)


# Alias
VolumeSlider = VolumeControl


class VUMeter(Widget):
    """
    Real-time Stereo or Mono Audio Level VU Meter.
    Supports LED segmented bars or smooth gradients with peak-hold indicators.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        channels: int = 2,  # 1 = Mono, 2 = Stereo
        mode: str = "segmented",  # 'segmented' or 'gradient'
        width: int = 180,
        height: int = 40,
        show_labels: bool = True,
        orientation: str = "horizontal",  # 'horizontal' or 'vertical'
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._channels = max(1, min(2, int(channels)))
        self._mode = mode.lower()
        self._show_labels = show_labels
        self._orientation = orientation.lower()

        self._left_level: float = 0.0
        self._right_level: float = 0.0
        self._peak_left: float = 0.0
        self._peak_right: float = 0.0

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            tag_name="vu_meter",
            **kwargs,
        )

    def set_levels(self, left: float, right: Optional[float] = None) -> None:
        """
        Update channel levels in range [0.0, 1.0].
        Automatically updates peak-hold indicators with decay.
        """
        self._left_level = max(0.0, min(1.0, float(left)))
        if self._channels == 2:
            self._right_level = max(0.0, min(1.0, float(right if right is not None else left)))
        else:
            self._right_level = self._left_level

        # Peak hold logic with physics decay
        self._peak_left = max(self._left_level, self._peak_left * 0.94)
        self._peak_right = max(self._right_level, self._peak_right * 0.94)

        self.render()

    def render(self) -> None:
        if self._surface is None or self._photo is None:
            return

        w = float(self._widget_w)
        h = float(self._widget_h)
        s = self._scale
        pal = get_theme()

        self._surface.clear(self._parent_bg)

        pad_x = 8.0 * s
        pad_y = 6.0 * s
        label_h = 12.0 * s if self._show_labels else 0.0

        meter_w = w - 2.0 * pad_x
        meter_h = h - 2.0 * pad_y - label_h

        # Labels top or bottom
        if self._show_labels:
            self._render_db_labels(pad_x, meter_w, s, pal)

        ch_gap = 4.0 * s
        ch_h = (meter_h - (self._channels - 1) * ch_gap) / self._channels

        # Render Left Channel
        y_left = pad_y + label_h
        self._render_channel_bar(pad_x, y_left, meter_w, ch_h, self._left_level, self._peak_left, s, pal)

        # Render Right Channel
        if self._channels == 2:
            y_right = y_left + ch_h + ch_gap
            self._render_channel_bar(pad_x, y_right, meter_w, ch_h, self._right_level, self._peak_right, s, pal)

        self._surface.blit(self._photo)

    def _render_db_labels(self, pad_x: float, meter_w: float, s: float, pal: Palette) -> None:
        # Tick marks at: -40dB (10%), -20dB (35%), -6dB (70%), 0dB (88%), +3dB (100%)
        ticks = [
            (0.10, "-40"),
            (0.35, "-20"),
            (0.70, "-6"),
            (0.88, "0"),
            (1.00, "+3"),
        ]
        label_col = pal.secondary if hasattr(pal, "secondary") else "#94a3b8"
        for pos, text in ticks:
            tx = pad_x + pos * meter_w
            self._surface.draw_text(text, tx, 2.0 * s, font_size=8.0 * s, color=label_col, align="center")

    def _render_channel_bar(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        level: float,
        peak: float,
        s: float,
        pal: Palette,
    ) -> None:
        rx = 2.0 * s
        bg_col = pal.track_bg

        if self._mode == "gradient":
            # Track bg
            self._surface.fill_rounded_rect(x, y, w, h, rx, rx, bg_col)
            active_w = level * w
            if active_w > 0:
                grad = LinearGradient(x, y, x + w, y)
                grad.add_stop(0.00, "#10b981")  # Green
                grad.add_stop(0.70, "#f59e0b")  # Yellow (-6dB)
                grad.add_stop(0.90, "#ef4444")  # Red (0dB)
                self._surface.fill_rounded_rect(x, y, active_w, h, rx, rx, grad)

            # Peak marker
            if peak > 0.02:
                px = x + min(w - 2.0 * s, peak * w)
                self._surface.fill_rect(px, y, 2.0 * s, h, "#ef4444" if peak >= 0.88 else "#ffffff")

        else:  # Segmented LED blocks
            num_segments = 24
            seg_gap = 1.5 * s
            seg_w = (w - (num_segments - 1) * seg_gap) / num_segments

            for idx in range(num_segments):
                sx = x + idx * (seg_w + seg_gap)
                seg_ratio = (idx + 1) / num_segments

                # Determine color zone
                if seg_ratio <= 0.70:
                    on_color = "#10b981"  # Safe Green
                    off_color = "#064e3b55"
                elif seg_ratio <= 0.88:
                    on_color = "#f59e0b"  # Warning Amber
                    off_color = "#78350f55"
                else:
                    on_color = "#ef4444"  # Clip Red
                    off_color = "#7f1d1d55"

                is_active = (seg_ratio <= level)
                is_peak = abs(seg_ratio - peak) < (1.0 / num_segments)

                col = on_color if is_active else (on_color if is_peak else off_color)
                self._surface.fill_rounded_rect(sx, y, seg_w, h, 1.0 * s, 1.0 * s, col)


# Alias
AudioMeter = VUMeter
