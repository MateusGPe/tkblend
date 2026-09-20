"""
Feedback and status widgets for tkblend: ModernProgressBar, ModernSpinner, ModernBadge, ModernAvatar, ModernTooltip.
"""

from __future__ import annotations
import tkinter as tk
import math
import time
from typing import Optional, Callable, List, Tuple, Any

from tkblend.surface import Surface, ColorLike, LinearGradient, Path
from tkblend.widgets.base import ModernWidget
from tkblend.widgets.theme import Theme, ThemeManager


class ModernProgressBar(ModernWidget):
    """
    Antialiased smooth progress bar with gradient fill and rounded capsule geometry.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 16,
        value: float = 0.0,  # [0.0 - 100.0]
        track_color: Optional[ColorLike] = None,
        fill_color_start: Optional[ColorLike] = None,
        fill_color_end: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._value = max(0.0, min(100.0, float(value)))
        self._track_color = track_color if track_color is not None else t.track
        self._fill_start = fill_color_start if fill_color_start is not None else t.primary
        self._fill_end = fill_color_end if fill_color_end is not None else t.primary_hover
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window

        self._anim_val: float = self._value

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=self._parent_bg,
            theme=theme,
            **kwargs,
        )

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        new_val = max(0.0, min(100.0, float(val)))
        if self._value != new_val:
            self._value = new_val
            self.animate_property(
                start_val=self._anim_val,
                end_val=new_val,
                duration_ms=180,
                on_update=self._set_anim_val,
            )

    def _set_anim_val(self, val: float) -> None:
        self._anim_val = val

    def set_value(self, val: float) -> None:
        self.value = val

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        pad = 2.0
        r = (self._widget_h - pad * 2.0) / 2.0
        w = max(1.0, self._widget_w - pad * 2.0)
        h = max(1.0, self._widget_h - pad * 2.0)

        # Background track
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, self._track_color)

        # Progress fill
        if self._anim_val > 0.5:
            fill_w = max(r * 2.0, (self._anim_val / 100.0) * w)
            grad = LinearGradient(pad, pad, pad + fill_w, pad)
            grad.add_stop(0.0, self._fill_start)
            grad.add_stop(1.0, self._fill_end)
            self._surface.fill_rounded_rect(pad, pad, fill_w, h, r, r, grad)

        self._surface.blit(self._photo)


class ModernSpinner(ModernWidget):
    """
    Antialiased rotating circular loading spinner powered by Blend2D.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 36,
        color: Optional[ColorLike] = None,
        track_color: Optional[ColorLike] = None,
        line_width: float = 3.5,
        speed: float = 1.0,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._size = size
        self._color = color if color is not None else t.primary
        self._track_color = track_color if track_color is not None else "#ffffff15"
        self._line_w = line_width
        self._speed = speed
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window

        self._angle: float = 0.0
        self._is_spinning: bool = False
        self._spin_job: Optional[str] = None

        super().__init__(
            master=master,
            width=size,
            height=size,
            bg=self._parent_bg,
            theme=theme,
            **kwargs,
        )

        self.start()

    def start(self) -> None:
        if not self._is_spinning:
            self._is_spinning = True
            self._spin_step()

    def stop(self) -> None:
        self._is_spinning = False
        if self._spin_job:
            try:
                self.after_cancel(self._spin_job)
            except Exception:
                pass
            self._spin_job = None
        self.render()

    def _spin_step(self) -> None:
        if not self._is_spinning or not self.winfo_exists():
            return
        self._angle = (self._angle + 8.0 * self._speed) % 360.0
        self.render()
        self._spin_job = self.after(16, self._spin_step)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        r = max(2.0, (min(self._widget_w, self._widget_h) - self._line_w * 2.0) / 2.0)

        # Background track circle
        self._surface.stroke_circle(cx, cy, r, self._track_color, stroke_width=self._line_w)

        # Arc path for spinning indicator
        if self._is_spinning:
            p = Path()
            start_deg = self._angle
            sweep_deg = 100.0
            num_segments = 16
            for i in range(num_segments + 1):
                deg = start_deg + (sweep_deg * i / num_segments)
                rad = math.radians(deg)
                px = cx + r * math.cos(rad)
                py = cy + r * math.sin(rad)
                if i == 0:
                    p.move_to(px, py)
                else:
                    p.line_to(px, py)

            self._surface.stroke_path(p, self._color, stroke_width=self._line_w)

        self._surface.blit(self._photo)


class ModernBadge(ModernWidget):
    """
    Modern pill badge / chip with status indicators or counter labels.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Badge",
        variant: str = "primary",  # "primary", "success", "warning", "danger", "neutral"
        dot: bool = False,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        height: int = 24,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._text = text
        self._variant = variant
        self._dot = dot
        self._font_size = font_size if font_size is not None else t.font_size_xs
        self._font_family = font_family or t.font_family
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window

        # Calculate appropriate width
        char_w = self._font_size * 0.65
        calc_w = int(len(text) * char_w + (32 if dot else 20))
        width = max(36, calc_w)

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=self._parent_bg,
            theme=theme,
            **kwargs,
        )

    def set_text(self, text: str) -> None:
        self._text = text
        char_w = self._font_size * 0.65
        calc_w = int(len(text) * char_w + (32 if self._dot else 20))
        self._widget_w = max(36, calc_w)
        self._photo.configure(width=self._widget_w, height=self._widget_h)
        self._surface.resize(self._widget_w, self._widget_h)
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        # Variant colors
        if self._variant == "success":
            bg = "#1e3a2b"
            text_c = self._theme.success
            border_c = "#2e6f47"
        elif self._variant == "warning":
            bg = "#3d2e18"
            text_c = self._theme.warning
            border_c = "#7c5923"
        elif self._variant == "danger":
            bg = "#3e1c24"
            text_c = self._theme.danger
            border_c = "#7e2a39"
        elif self._variant == "neutral":
            bg = self._theme.secondary
            text_c = self._theme.text_muted
            border_c = self._theme.border
        else:  # primary
            bg = "#1e293b"
            text_c = self._theme.primary
            border_c = "#3b82f6"

        pad = 2.0
        w = self._widget_w - pad * 2.0
        h = self._widget_h - pad * 2.0
        r = h / 2.0

        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, bg)
        self._surface.stroke_rounded_rect(pad, pad, w, h, r, r, border_c, stroke_width=1.0)

        # Draw dot if present
        text_start_x = pad + 10.0
        if self._dot:
            dot_cx = pad + 8.0
            dot_cy = self._widget_h / 2.0
            self._surface.fill_circle(dot_cx, dot_cy, 3.0, text_c)
            text_start_x += 10.0

        text_y = self._widget_h / 2.0 + (self._font_size * 0.35)
        self._surface.draw_text(
            self._text,
            x=text_start_x,
            y=text_y,
            font_size=self._font_size,
            font_family=self._font_family,
            color=text_c,
            align="left",
        )

        self._surface.blit(self._photo)


class ModernAvatar(ModernWidget):
    """
    Antialiased circular avatar widget displaying initials monogram or custom image with status badge.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "JD",
        size: int = 44,
        bg_color: Optional[ColorLike] = None,
        text_color: Optional[ColorLike] = None,
        status: Optional[str] = None,  # "online", "busy", "away", "offline"
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._text = text[:2].upper()
        self._size = size
        self._bg_color = bg_color if bg_color is not None else t.primary
        self._text_color = text_color if text_color is not None else t.primary_text
        self._status = status
        self._parent_bg = parent_bg if parent_bg is not None else t.bg_window

        super().__init__(
            master=master,
            width=size,
            height=size,
            bg=self._parent_bg,
            theme=theme,
            **kwargs,
        )

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        r = (self._size - 4.0) / 2.0

        # Avatar circle + subtle border
        self._surface.fill_circle(cx, cy, r, self._bg_color)
        self._surface.stroke_circle(cx, cy, r, "#ffffff33", stroke_width=1.5)

        # Monogram text
        font_s = r * 0.85
        text_y = cy + (font_s * 0.35)
        self._surface.draw_text(
            self._text,
            x=cx,
            y=text_y,
            font_size=font_s,
            font_family=self._theme.font_family,
            color=self._text_color,
            align="center",
        )

        # Status indicator dot
        if self._status:
            stat_color = (
                self._theme.success
                if self._status == "online"
                else self._theme.danger
                if self._status == "busy"
                else self._theme.warning
                if self._status == "away"
                else self._theme.text_disabled
            )
            stat_r = r * 0.28
            stat_cx = cx + r * 0.7
            stat_cy = cy + r * 0.7
            # Ring cut
            self._surface.fill_circle(stat_cx, stat_cy, stat_r + 1.5, self._parent_bg)
            self._surface.fill_circle(stat_cx, stat_cy, stat_r, stat_color)

        self._surface.blit(self._photo)


class ModernTooltip:
    """
    Floating modern tooltip with rounded corner and drop shadow attached to any widget.
    """

    def __init__(
        self,
        widget: tk.Widget,
        text: str = "",
        delay_ms: int = 400,
        theme: Optional[Theme] = None,
    ):
        self._widget = widget
        self._text = text
        self._delay_ms = delay_ms
        self._theme = theme or ThemeManager.get_theme()
        self._tip_window: Optional[tk.Toplevel] = None
        self._scheduled_id: Optional[str] = None

        self._widget.bind("<Enter>", self._on_enter)
        self._widget.bind("<Leave>", self._on_leave)
        self._widget.bind("<ButtonPress>", self._on_leave)

    def _on_enter(self, event) -> None:
        self._scheduled_id = self._widget.after(self._delay_ms, self._show_tip)

    def _on_leave(self, event=None) -> None:
        if self._scheduled_id:
            try:
                self._widget.after_cancel(self._scheduled_id)
            except Exception:
                pass
            self._scheduled_id = None
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None

    def _show_tip(self) -> None:
        if not self._widget.winfo_exists() or not self._text:
            return

        x = self._widget.winfo_rootx() + (self._widget.winfo_width() // 2)
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6

        self._tip_window = tk.Toplevel(self._widget)
        self._tip_window.wm_overrideredirect(True)
        self._tip_window.wm_attributes("-topmost", True)
        self._tip_window.geometry(f"+{x}+{y}")

        lbl = tk.Label(
            self._tip_window,
            text=self._text,
            font=(self._theme.font_family, int(self._theme.font_size_xs)),
            fg=self._theme.text,
            bg=self._theme.bg_card,
            padx=10,
            pady=6,
            relief="solid",
            borderwidth=1,
        )
        lbl.pack()
