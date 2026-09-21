"""
Feedback and status widgets for tkblend: ModernProgressBar, ModernSpinner,
ModernBadge, ModernAvatar, ModernTooltip, ModernLabel, and ModernToast.

Full .configure() / .cget() protocol, semantic variants, and Blend2D anti-aliased rendering.
"""

from __future__ import annotations
import tkinter as tk
import math
import time
from typing import Optional, Callable, List, Tuple, Any, Dict, Union

from tkblend.surface import Surface, ColorLike, LinearGradient, Path
from tkblend.widgets.base import ModernWidget
from tkblend.widgets.theme import Theme, ThemeManager
from tkblend.widgets.scaling import ScalingTracker


# ============================================================================
# ModernProgressBar
# ============================================================================

class ModernProgressBar(ModernWidget):
    """
    Antialiased smooth progress bar with gradient fill, rounded capsule geometry,
    indeterminate mode, semantic variants, and CustomTkinter / ttkbootstrap parity.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 240,
        height: int = 16,
        value: float = 0.0,
        mode: str = "determinate",  # "determinate" or "indeterminate"
        variant: str = "primary",  # "primary", "success", "danger", "warning", "info"
        track_color: Optional[ColorLike] = None,
        fill_color_start: Optional[ColorLike] = None,
        fill_color_end: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        self._value = max(0.0, min(100.0, float(value)))
        self._mode = mode
        self._variant = (variant or "primary").lower()
        self._custom_track_color = track_color
        self._custom_fill_start = fill_color_start
        self._custom_fill_end = fill_color_end
        self._anim_val: float = self._value
        self._indet_pos: float = 0.0
        self._indet_job: Optional[str] = None

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            theme=theme,
            **kwargs,
        )

        if self._mode == "indeterminate":
            self.start()

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        redraw = False
        if "value" in kwargs:
            self.value = float(kwargs.pop("value"))
            redraw = True
        if "mode" in kwargs:
            self._mode = str(kwargs.pop("mode")).lower()
            if self._mode == "indeterminate":
                self.start()
            else:
                self.stop()
            redraw = True
        if "variant" in kwargs:
            self._variant = str(kwargs.pop("variant")).lower()
            redraw = True
        if "track_color" in kwargs:
            self._custom_track_color = kwargs.pop("track_color")
            redraw = True
        if "fill_color_start" in kwargs or "progress_color" in kwargs:
            self._custom_fill_start = kwargs.pop("fill_color_start", None) or kwargs.pop("progress_color", None)
            redraw = True
        if "fill_color_end" in kwargs:
            self._custom_fill_end = kwargs.pop("fill_color_end")
            redraw = True
        return redraw

    def _cget_subclass(self, key: str) -> Optional[Any]:
        if key == "value":
            return self._value
        elif key == "mode":
            return self._mode
        elif key == "variant":
            return self._variant
        elif key == "track_color":
            return self._custom_track_color
        elif key in ("fill_color_start", "progress_color"):
            return self._custom_fill_start
        elif key == "fill_color_end":
            return self._custom_fill_end
        return None

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

    def set(self, val: float) -> None:
        self.value = val * 100.0 if val <= 1.0 else val

    def get(self) -> float:
        return self._value / 100.0

    def step(self, amount: float = 5.0) -> None:
        self.value = min(100.0, self._value + amount)

    def start(self) -> None:
        if self._indet_job is None:
            self._indet_step()

    def stop(self) -> None:
        if self._indet_job:
            try:
                self.after_cancel(self._indet_job)
            except Exception:
                pass
            self._indet_job = None
        self.render()

    def destroy(self) -> None:
        self.stop()
        super().destroy()

    def _on_destroy_event(self, event) -> None:
        if event.widget is self:
            self.stop()
        super()._on_destroy_event(event)

    def _indet_step(self) -> None:
        if self._mode != "indeterminate":
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self._indet_pos = (self._indet_pos + 0.03) % 1.5
        self.render()
        if self._mode == "indeterminate":
            self._indet_job = self.after(20, self._indet_step)

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        t = self._theme
        track_color = self._custom_track_color if self._custom_track_color is not None else t.track

        if self._custom_fill_start is not None:
            fill_start = self._custom_fill_start
            fill_end = self._custom_fill_end or fill_start
        else:
            base_col, hov_col, _, _ = t.get_variant_colors(self._variant)
            fill_start = base_col
            fill_end = hov_col

        pad = 2.0
        r = (self._widget_h - pad * 2.0) / 2.0
        w = max(1.0, self._widget_w - pad * 2.0)
        h = max(1.0, self._widget_h - pad * 2.0)

        self._surface.fill_rounded_rect(pad, pad, w, h, r, r, track_color)

        if self._mode == "indeterminate":
            block_w = w * 0.35
            start_x = pad + (self._indet_pos - 0.35) * w
            clamped_start = max(pad, min(pad + w - r, start_x))
            clamped_end = min(pad + w, start_x + block_w)
            if clamped_end > clamped_start:
                self._surface.fill_rounded_rect(clamped_start, pad, clamped_end - clamped_start, h, r, r, fill_start)
        else:
            if self._anim_val > 0.5:
                fill_w = max(r * 2.0, (self._anim_val / 100.0) * w)
                grad = LinearGradient(pad, pad, pad + fill_w, pad)
                grad.add_stop(0.0, fill_start)
                grad.add_stop(1.0, fill_end)
                self._surface.fill_rounded_rect(pad, pad, fill_w, h, r, r, grad)

        self._surface.blit(self._photo)


# ============================================================================
# ModernSpinner
# ============================================================================

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

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        redraw = False
        if "color" in kwargs:
            self._custom_color = kwargs.pop("color")
            redraw = True
        if "speed" in kwargs:
            self._speed = float(kwargs.pop("speed"))
        if "line_width" in kwargs:
            self._line_w = float(kwargs.pop("line_width"))
            redraw = True
        return redraw

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

    def destroy(self) -> None:
        self.stop()
        super().destroy()

    def _on_destroy_event(self, event) -> None:
        if event.widget is self:
            self.stop()
        super()._on_destroy_event(event)

    def _spin_step(self) -> None:
        if not self._is_spinning:
            return
        try:
            if not self.winfo_exists():
                self._is_spinning = False
                return
        except Exception:
            self._is_spinning = False
            return
        self._angle = (self._angle + 8.0 * self._speed) % 360.0
        self.render()
        if self._is_spinning:
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

        self._surface.stroke_circle(cx, cy, r, track_color, stroke_width=self._line_w)

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


# ============================================================================
# ModernBadge
# ============================================================================

class ModernBadge(ModernWidget):
    """
    Modern pill badge / chip with status indicators, semantic variants, or counter labels.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Badge",
        variant: str = "primary",
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
        self._variant = (variant or "primary").lower()
        self._dot = dot
        self._custom_font_size = font_size
        self._custom_font_family = font_family

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

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        redraw = False
        if "text" in kwargs:
            self.set_text(str(kwargs.pop("text")))
            redraw = True
        if "variant" in kwargs:
            self._variant = str(kwargs.pop("variant")).lower()
            redraw = True
        if "dot" in kwargs:
            self._dot = bool(kwargs.pop("dot"))
            redraw = True
        return redraw

    def _cget_subclass(self, key: str) -> Optional[Any]:
        if key == "text":
            return self._text
        elif key == "variant":
            return self._variant
        elif key == "dot":
            return self._dot
        return None

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
        elif self._variant == "info":
            bg = "#1e2f38" if t.name == "dark" else "#e0f2fe"
            text_c = t.info
            border_c = "#2563eb" if t.name == "dark" else "#bae6fd"
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


# ============================================================================
# ModernAvatar
# ============================================================================

class ModernAvatar(ModernWidget):
    """
    Circular user avatar with monogram initials and status badge indicator.
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

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        redraw = False
        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))[:2].upper()
            redraw = True
        if "status" in kwargs:
            self._status = kwargs.pop("status")
            redraw = True
        if "bg_color" in kwargs:
            self._custom_bg_color = kwargs.pop("bg_color")
            redraw = True
        if "text_color" in kwargs:
            self._custom_text_color = kwargs.pop("text_color")
            redraw = True
        return redraw

    def _cget_subclass(self, key: str) -> Optional[Any]:
        if key == "text":
            return self._text
        elif key == "status":
            return self._status
        elif key == "bg_color":
            return self._custom_bg_color
        elif key == "text_color":
            return self._custom_text_color
        return None

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        t = self._theme
        bg_col = self._custom_bg_color if self._custom_bg_color is not None else t.primary
        text_col = self._custom_text_color if self._custom_text_color is not None else t.primary_text

        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        r = (min(self._widget_w, self._widget_h) - 4.0) / 2.0

        self._surface.fill_circle(cx, cy, r, bg_col)
        self._surface.stroke_circle(cx, cy, r, "#ffffff33", stroke_width=1.5)

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
            self._surface.fill_circle(stat_cx, stat_cy, stat_r + 1.5, self._parent_bg)
            self._surface.fill_circle(stat_cx, stat_cy, stat_r, stat_color)

        self._surface.blit(self._photo)


# ============================================================================
# ModernLabel
# ============================================================================

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
        align: str = "left",
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

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        redraw = False
        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
            redraw = True
        if "variant" in kwargs:
            self._variant = str(kwargs.pop("variant")).lower()
            redraw = True
        if "color" in kwargs or "text_color" in kwargs or "fg_color" in kwargs:
            self._custom_color = kwargs.pop("color", None) or kwargs.pop("text_color", None) or kwargs.pop("fg_color", None)
            redraw = True
        if "font_size" in kwargs:
            self._custom_font_size = kwargs.pop("font_size")
            redraw = True
        if "align" in kwargs:
            self._align = kwargs.pop("align")
            redraw = True
        return redraw

    def _cget_subclass(self, key: str) -> Optional[Any]:
        if key == "text":
            return self._text
        elif key == "variant":
            return self._variant
        elif key in ("color", "text_color", "fg_color"):
            return self._custom_color
        elif key == "font_size":
            return self._custom_font_size
        elif key == "align":
            return self._align
        return None

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        self.configure(text=val)

    def set_text(self, val: str) -> None:
        self.configure(text=val)

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


# ============================================================================
# ModernTooltip & ModernToast
# ============================================================================

class ModernTooltip:
    """
    Floating tooltip helper for any Tkinter/tkblend widget with soft elevation shadow.
    """

    def __init__(
        self,
        widget: tk.Misc,
        text: str,
        delay_ms: int = 400,
        theme: Optional[Theme] = None,
    ):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._theme = theme or ThemeManager.get_theme()
        self._tip_window: Optional[tk.Toplevel] = None
        self._timer_id: Optional[str] = None

        self.widget.bind("<Enter>", self._schedule)
        self.widget.bind("<Leave>", self._hide)
        self.widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, event=None):
        self._cancel()
        self._timer_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self):
        if self._timer_id:
            try:
                self.widget.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None

    def _show(self):
        if self._tip_window or not self.text:
            return

        t = self._theme
        x = self.widget.winfo_rootx() + int(self.widget.winfo_width() / 2)
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6

        self._tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        tw.geometry(f"+{x}+{y}")

        lbl = tk.Label(
            tw,
            text=self.text,
            background=t.bg_surface_alt,
            foreground=t.text,
            font=(t.font_family, int(t.font_size_xs)),
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=4,
        )
        lbl.pack()

    def _hide(self, event=None):
        self._cancel()
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None

    def _show_tip(self):
        self._show()

    def _on_leave(self, event=None):
        self._hide(event)

    def _on_enter(self, event=None):
        self._schedule(event)


class ModernToast:
    """
    Floating banner toast notification with auto-dismiss timer.
    """

    @classmethod
    def show(
        cls,
        root: tk.Misc,
        message: str,
        title: str = "Notification",
        variant: str = "info",
        duration_ms: int = 3000,
        theme: Optional[Theme] = None,
    ) -> tk.Toplevel:
        t = theme or ThemeManager.get_theme()
        toast = tk.Toplevel(root)
        toast.wm_overrideredirect(True)
        toast.wm_attributes("-topmost", True)

        card = tk.Frame(toast, bg=t.bg_card, highlightbackground=t.primary, highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        if title:
            lbl_title = tk.Label(
                card,
                text=title,
                font=(t.font_family, int(t.font_size_sm), "bold"),
                fg=t.primary,
                bg=t.bg_card,
                anchor="w",
            )
            lbl_title.pack(fill=tk.X, padx=12, pady=(8, 2))

        lbl_msg = tk.Label(
            card,
            text=message,
            font=(t.font_family, int(t.font_size_xs)),
            fg=t.text,
            bg=t.bg_card,
            anchor="w",
        )
        lbl_msg.pack(fill=tk.X, padx=12, pady=(2, 8))

        root_w = root.winfo_width() if root.winfo_width() > 1 else 600
        rx = root.winfo_rootx() + root_w - 280
        ry = root.winfo_rooty() + 40
        toast.geometry(f"260x70+{rx}+{ry}")

        root.after(duration_ms, lambda: toast.destroy() if toast.winfo_exists() else None)
        return toast
