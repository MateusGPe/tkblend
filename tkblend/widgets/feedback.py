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
        self._value = max(0.0, min(100.0, float(value)))
        self._custom_track_color = track_color
        self._custom_fill_start = fill_color_start
        self._custom_fill_end = fill_color_end
        self._anim_val: float = self._value

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
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

        t = self._theme
        track_color = self._custom_track_color if self._custom_track_color is not None else t.track
        fill_start = self._custom_fill_start if self._custom_fill_start is not None else t.primary
        fill_end = self._custom_fill_end if self._custom_fill_end is not None else t.primary_hover

        pad = 2.0
        r = (self._widget_h - pad * 2.0) / 2.0
        w = max(1.0, self._widget_w - pad * 2.0)
        h = max(1.0, self._widget_h - pad * 2.0)

        # Background track
        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, track_color)

        # Progress fill
        if self._anim_val > 0.5:
            fill_w = max(r * 2.0, (self._anim_val / 100.0) * w)
            grad = LinearGradient(pad, pad, pad + fill_w, pad)
            grad.add_stop(0.0, fill_start)
            grad.add_stop(1.0, fill_end)
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
        self._size = size
        self._custom_color = color
        self._custom_track_color = track_color
        self._line_w = line_width
        self._speed = speed

        self._angle: float = 0.0
        self._is_spinning: bool = False
        self._spin_job: Optional[str] = None

        super().__init__(
            master=master,
            width=size,
            height=size,
            bg=parent_bg,
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

        t = self._theme
        color = self._custom_color if self._custom_color is not None else t.primary
        default_track = "#ffffff15" if t.name == "dark" else "#00000015"
        track_color = self._custom_track_color if self._custom_track_color is not None else default_track

        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        r = max(2.0, (min(self._widget_w, self._widget_h) - self._line_w * 2.0) / 2.0)

        # Background track circle
        self._surface.stroke_circle(cx, cy, r, track_color, stroke_width=self._line_w)

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

            self._surface.stroke_path(p, color, stroke_width=self._line_w)

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
        self._custom_font_size = font_size
        self._custom_font_family = font_family

        # Calculate appropriate width
        font_s = font_size if font_size is not None else t.font_size_xs
        char_w = font_s * 0.65
        calc_w = int(len(text) * char_w + (32 if dot else 20))
        width = max(36, calc_w)

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            theme=theme,
            **kwargs,
        )

    def set_text(self, text: str) -> None:
        self._text = text
        t = self._theme
        font_s = self._custom_font_size if self._custom_font_size is not None else t.font_size_xs
        char_w = font_s * 0.65
        calc_w = int(len(text) * char_w + (32 if self._dot else 20))
        self.resize(max(36, calc_w), self._requested_h)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        t = self._theme
        font_size = self._custom_font_size if self._custom_font_size is not None else t.font_size_xs
        font_family = self._custom_font_family or t.font_family

        # Variant colors
        if self._variant == "success":
            bg = "#1e3a2b" if t.name == "dark" else "#d1fae5"
            text_c = t.success
            border_c = "#2e6f47" if t.name == "dark" else "#a7f3d0"
        elif self._variant == "warning":
            bg = "#3d2e18" if t.name == "dark" else "#fef3c7"
            text_c = t.warning
            border_c = "#7c5923" if t.name == "dark" else "#fde68a"
        elif self._variant == "danger":
            bg = "#3e1c24" if t.name == "dark" else "#fee2e2"
            text_c = t.danger
            border_c = "#7e2a39" if t.name == "dark" else "#fca5a5"
        elif self._variant == "neutral":
            bg = t.secondary
            text_c = t.text_muted
            border_c = t.border
        else:  # primary
            bg = "#1e293b" if t.name == "dark" else "#dbeafe"
            text_c = t.primary
            border_c = "#3b82f6" if t.name == "dark" else "#93c5fd"

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

        text_y = self._widget_h / 2.0 + (font_size * 0.35)
        self._surface.draw_text(
            self._text,
            x=text_start_x,
            y=text_y,
            font_size=font_size,
            font_family=font_family,
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
        self._text = text[:2].upper()
        self._size = size
        self._custom_bg_color = bg_color
        self._custom_text_color = text_color
        self._status = status

        super().__init__(
            master=master,
            width=size,
            height=size,
            bg=parent_bg,
            theme=theme,
            **kwargs,
        )

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        t = self._theme
        bg_col = self._custom_bg_color if self._custom_bg_color is not None else t.primary
        text_col = self._custom_text_color if self._custom_text_color is not None else t.primary_text

        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        r = (self._size - 4.0) / 2.0

        # Avatar circle + subtle border
        self._surface.fill_circle(cx, cy, r, bg_col)
        self._surface.stroke_circle(cx, cy, r, "#ffffff33", stroke_width=1.5)

        # Monogram text
        font_s = r * 0.85
        text_y = cy + (font_s * 0.35)
        self._surface.draw_text(
            self._text,
            x=cx,
            y=text_y,
            font_size=font_s,
            font_family=t.font_family,
            color=text_col,
            align="center",
        )

        # Status indicator dot
        if self._status:
            stat_color = (
                t.success
                if self._status == "online"
                else t.danger
                if self._status == "busy"
                else t.warning
                if self._status == "away"
                else t.text_disabled
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
        self._custom_theme = theme
        self._tip_window: Optional[tk.Toplevel] = None
        self._scheduled_id: Optional[str] = None

        self._widget.bind("<Enter>", self._on_enter)
        self._widget.bind("<Leave>", self._on_leave)
        self._widget.bind("<ButtonPress>", self._on_leave)

    @property
    def _theme(self) -> Theme:
        return self._custom_theme or ThemeManager.get_theme()

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

        t = self._theme
        x = self._widget.winfo_rootx() + (self._widget.winfo_width() // 2)
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6

        self._tip_window = tk.Toplevel(self._widget)
        self._tip_window.wm_overrideredirect(True)
        self._tip_window.wm_attributes("-topmost", True)
        self._tip_window.geometry(f"+{x}+{y}")
        self._tip_window.configure(bg=t.border)

        lbl = tk.Label(
            self._tip_window,
            text=self._text,
            font=(t.font_family, int(t.font_size_xs)),
            fg=t.text,
            bg=t.bg_card,
            padx=10,
            pady=6,
            relief="solid",
            borderwidth=1,
            highlightthickness=0,
        )
        lbl.pack()


class ModernLabel(ModernWidget):
    """
    Antialiased vector text label with semantic variants, auto-theming, and custom styling.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        variant: str = "default",  # "default", "muted", "heading", "subheading", "accent", "danger", "success", "warning"
        color: Optional[ColorLike] = None,
        font_size: Optional[float] = None,
        font_family: Optional[str] = None,
        align: str = "left",  # "left", "center", "right"
        bold: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        self._text = str(text)
        self._variant = variant.lower()
        self._custom_color = color
        self._custom_font_size = font_size
        self._custom_font_family = font_family
        self._align = align
        self._bold = bold

        t = theme or ThemeManager.get_theme()
        if font_size is not None:
            f_size = font_size
        elif self._variant == "heading":
            f_size = t.font_size_lg
        elif self._variant == "subheading":
            f_size = t.font_size_xs
        else:
            f_size = t.font_size_md

        calc_w = width if width is not None else max(10, int(len(self._text) * f_size * 0.65) + 12)
        calc_h = height if height is not None else int(f_size * 1.8) + 4

        super().__init__(
            master=master,
            width=calc_w,
            height=calc_h,
            bg=parent_bg,
            theme=theme,
            **kwargs,
        )

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        self._text = str(val)
        self.render()

    def set_text(self, val: str) -> None:
        self.text = val

    def _resolve_text_color(self) -> ColorLike:
        if self._custom_color is not None:
            return self._custom_color
        t = self._theme
        if self._variant in ("muted", "subheading"):
            return t.text_muted
        elif self._variant in ("heading", "accent"):
            return t.primary
        elif self._variant == "danger":
            return t.danger
        elif self._variant == "success":
            return t.success
        elif self._variant == "warning":
            return t.warning
        return t.text

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        t = self._theme
        font_size = self._custom_font_size
        if font_size is None:
            if self._variant == "heading":
                font_size = t.font_size_lg
            elif self._variant == "subheading":
                font_size = t.font_size_xs
            else:
                font_size = t.font_size_md

        font_family = self._custom_font_family or t.font_family
        color = self._resolve_text_color()

        if self._align == "center":
            tx = self._widget_w / 2.0
        elif self._align == "right":
            tx = self._widget_w - 4.0
        else:
            tx = 4.0

        ty = self._widget_h / 2.0 + (font_size * 0.35)

        self._surface.draw_text(
            self._text,
            x=tx,
            y=ty,
            font_size=font_size,
            font_family=font_family,
            color=color,
            align=self._align,
        )
        self._surface.blit(self._photo)

