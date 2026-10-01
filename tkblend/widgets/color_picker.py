"""
High-performance pure vector Color Picker and ColorWell widgets for tkblend.
Zero TTK dependencies. Provides interactive 2D HSV gradient picker, Hue spectrum slider,
Alpha slider, RGB/HEX text inputs, preset palette swatches, and popup ColorWell button.
"""

from __future__ import annotations
import colorsys
import tkinter as tk
from typing import Optional, Callable, List, Tuple, Union

from tkblend.surface import Surface, Path, LinearGradient, ColorLike, parse_color
from tkblend.theme import get_theme, Palette
from tkblend.widgets.base import Widget, ScalingTracker, _resolve_color
from tkblend.widgets.containers import Card, Frame
from tkblend.widgets.button import Button
from tkblend.widgets.inputs import Entry


PRESET_SWATCHES = [
    "#ef4444", "#f97316", "#f59e0b", "#10b981", "#06b6d4", "#3b82f6",
    "#6366f1", "#8b5cf6", "#ec4899", "#64748b", "#ffffff", "#000000",
]


def _rgb_to_hex(r: int, g: int, b: int, a: float = 1.0) -> str:
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    if a < 1.0:
        a_int = max(0, min(255, int(a * 255)))
        return f"#{r:02x}{g:02x}{b:02x}{a_int:02x}"
    return f"#{r:02x}{g:02x}{b:02x}"


def _hex_to_rgb(hex_str: str) -> Tuple[int, int, int, float]:
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c * 2 for c in hex_clean])
    if len(hex_clean) == 6:
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        return r, g, b, 1.0
    elif len(hex_clean) == 8:
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        a = int(hex_clean[6:8], 16) / 255.0
        return r, g, b, a
    return 59, 130, 246, 1.0  # fallback blue


class ColorPicker(Widget):
    """
    Pure vector Color Picker panel with 2D Saturation/Value gradient canvas,
    Hue spectrum slider, Alpha slider, preset palette swatches, and HEX/RGB controls.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        initial_color: str = "#3b82f6",
        width: int = 240,
        height: int = 290,
        show_alpha: bool = True,
        show_swatches: bool = True,
        on_change: Optional[Callable[[str], None]] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._show_alpha = show_alpha
        self._show_swatches = show_swatches
        self._on_change = on_change

        # Color state in HSV + Alpha [0.0 - 1.0]
        r, g, b, a = _hex_to_rgb(initial_color)
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self._h = h
        self._s = s
        self._v = v
        self._a = a

        self._active_drag_target: Optional[str] = None  # 'sv', 'hue', 'alpha'

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            tag_name="color_picker",
            **kwargs,
        )

        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

    # -------------------------------------------------------------------------
    # Color Value Properties
    # -------------------------------------------------------------------------

    def get_color(self) -> str:
        """Return color as uppercase HEX string (e.g. #3B82F6 or #3B82F6FF)."""
        r, g, b = colorsys.hsv_to_rgb(self._h, self._s, self._v)
        return _rgb_to_hex(int(r * 255), int(g * 255), int(b * 255), self._a).upper()

    def get_rgb(self) -> Tuple[int, int, int]:
        """Return current RGB tuple (0-255)."""
        r, g, b = colorsys.hsv_to_rgb(self._h, self._s, self._v)
        return int(r * 255), int(g * 255), int(b * 255)

    def get_rgba(self) -> Tuple[int, int, int, float]:
        """Return current RGBA tuple (0-255, 0-255, 0-255, 0.0-1.0)."""
        r, g, b = self.get_rgb()
        return r, g, b, self._a

    def set_color(self, hex_or_rgb: Union[str, Tuple[int, int, int]]) -> None:
        """Update active color and trigger redraw."""
        if isinstance(hex_or_rgb, str):
            r, g, b, a = _hex_to_rgb(hex_or_rgb)
        else:
            r, g, b = hex_or_rgb[:3]
            a = hex_or_rgb[3] if len(hex_or_rgb) > 3 else 1.0

        self._h, self._s, self._v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self._a = a
        self.render()
        if self._on_change:
            self._on_change(self.get_color())

    # -------------------------------------------------------------------------
    # Geometry Layout Calculations
    # -------------------------------------------------------------------------

    def _get_layout(self) -> dict:
        w = float(self._widget_w)
        h = float(self._widget_h)
        s = self._scale

        pad = 10.0 * s
        sv_size = w - 2.0 * pad

        sv_rect = (pad, pad, sv_size, 130.0 * s)
        hue_rect = (pad, sv_rect[1] + sv_rect[3] + 10.0 * s, sv_size, 14.0 * s)

        next_y = hue_rect[1] + hue_rect[3] + 8.0 * s
        alpha_rect = None
        if self._show_alpha:
            alpha_rect = (pad, next_y, sv_size, 14.0 * s)
            next_y += alpha_rect[3] + 8.0 * s

        swatch_rect = (pad, next_y, 40.0 * s, 24.0 * s)
        hex_rect = (pad + 48.0 * s, next_y, sv_size - 48.0 * s, 24.0 * s)
        next_y += swatch_rect[3] + 10.0 * s

        swatches_y = next_y if self._show_swatches else None

        return {
            "pad": pad,
            "sv": sv_rect,
            "hue": hue_rect,
            "alpha": alpha_rect,
            "swatch": swatch_rect,
            "hex": hex_rect,
            "swatches_y": swatches_y,
            "swatch_size": 14.0 * s,
            "swatch_gap": 5.0 * s,
        }

    # -------------------------------------------------------------------------
    # Mouse Interaction
    # -------------------------------------------------------------------------

    def _on_mouse_down(self, event: tk.Event) -> None:
        mx = float(event.x) * self._scale
        my = float(event.y) * self._scale
        layout = self._get_layout()

        # Check SV box
        sv = layout["sv"]
        if sv[0] <= mx <= sv[0] + sv[2] and sv[1] <= my <= sv[1] + sv[3]:
            self._active_drag_target = "sv"
            self._update_sv_from_mouse(mx, my, sv)
            return

        # Check Hue bar
        hue = layout["hue"]
        if hue[0] <= mx <= hue[0] + hue[2] and hue[1] <= my <= hue[1] + hue[3]:
            self._active_drag_target = "hue"
            self._update_hue_from_mouse(mx, hue)
            return

        # Check Alpha bar
        alpha = layout["alpha"]
        if alpha and alpha[0] <= mx <= alpha[0] + alpha[2] and alpha[1] <= my <= alpha[1] + alpha[3]:
            self._active_drag_target = "alpha"
            self._update_alpha_from_mouse(mx, alpha)
            return

        # Check Preset Swatches
        if layout["swatches_y"] is not None:
            sy = layout["swatches_y"]
            gap = layout["swatch_gap"]
            size = layout["swatch_size"]
            pad = layout["pad"]
            for idx, hex_col in enumerate(PRESET_SWATCHES):
                col_x = pad + (idx % 6) * (size + gap + 10.0 * self._scale)
                row_y = sy + (idx // 6) * (size + gap + 4.0 * self._scale)
                if col_x <= mx <= col_x + size and row_y <= my <= row_y + size:
                    self.set_color(hex_col)
                    return

    def _on_mouse_drag(self, event: tk.Event) -> None:
        if not self._active_drag_target:
            return
        mx = float(event.x) * self._scale
        my = float(event.y) * self._scale
        layout = self._get_layout()

        if self._active_drag_target == "sv":
            self._update_sv_from_mouse(mx, my, layout["sv"])
        elif self._active_drag_target == "hue":
            self._update_hue_from_mouse(mx, layout["hue"])
        elif self._active_drag_target == "alpha" and layout["alpha"]:
            self._update_alpha_from_mouse(mx, layout["alpha"])

    def _on_mouse_up(self, _event: tk.Event) -> None:
        self._active_drag_target = None

    def _update_sv_from_mouse(self, mx: float, my: float, rect: Tuple[float, float, float, float]) -> None:
        x, y, w, h = rect
        self._s = max(0.0, min(1.0, (mx - x) / w))
        self._v = max(0.0, min(1.0, 1.0 - (my - y) / h))
        self.render()
        if self._on_change:
            self._on_change(self.get_color())

    def _update_hue_from_mouse(self, mx: float, rect: Tuple[float, float, float, float]) -> None:
        x, _, w, _ = rect
        self._h = max(0.0, min(1.0, (mx - x) / w))
        self.render()
        if self._on_change:
            self._on_change(self.get_color())

    def _update_alpha_from_mouse(self, mx: float, rect: Tuple[float, float, float, float]) -> None:
        x, _, w, _ = rect
        self._a = max(0.0, min(1.0, (mx - x) / w))
        self.render()
        if self._on_change:
            self._on_change(self.get_color())

    # -------------------------------------------------------------------------
    # Render Pipeline
    # -------------------------------------------------------------------------

    def render(self) -> None:
        if self._surface is None:
            return

        w = float(self._widget_w)
        h = float(self._widget_h)
        s = self._scale
        pal = get_theme()

        self._surface.clear(self._parent_bg)

        layout = self._get_layout()

        # 1. Render Saturation/Value Box
        sv_x, sv_y, sv_w, sv_h = layout["sv"]
        pure_hue_r, pure_hue_g, pure_hue_b = colorsys.hsv_to_rgb(self._h, 1.0, 1.0)
        pure_hue_hex = _rgb_to_hex(int(pure_hue_r * 255), int(pure_hue_g * 255), int(pure_hue_b * 255))

        # Base Hue Fill
        self._surface.fill_rounded_rect(sv_x, sv_y, sv_w, sv_h, 6.0 * s, 6.0 * s, pure_hue_hex)

        # Horizontal White to Transparent Gradient (Saturation)
        grad_sat = LinearGradient(sv_x, sv_y, sv_x + sv_w, sv_y)
        grad_sat.add_stop(0.0, "#ffffff", alpha=1.0)
        grad_sat.add_stop(1.0, "#ffffff", alpha=0.0)
        self._surface.fill_rounded_rect(sv_x, sv_y, sv_w, sv_h, 6.0 * s, 6.0 * s, grad_sat)

        # Vertical Transparent to Black Gradient (Value)
        grad_val = LinearGradient(sv_x, sv_y, sv_x, sv_y + sv_h)
        grad_val.add_stop(0.0, "#000000", alpha=0.0)
        grad_val.add_stop(1.0, "#000000", alpha=1.0)
        self._surface.fill_rounded_rect(sv_x, sv_y, sv_w, sv_h, 6.0 * s, 6.0 * s, grad_val)

        # SV Reticle (Circle indicator)
        rx = sv_x + self._s * sv_w
        ry = sv_y + (1.0 - self._v) * sv_h
        self._surface.stroke_circle(rx, ry, 6.0 * s, "#ffffff", stroke_width=2.0 * s)
        self._surface.stroke_circle(rx, ry, 7.0 * s, "#000000", stroke_width=1.0 * s)

        # Border for SV Box
        border_col = pal.card_border if hasattr(pal, "card_border") else "#475569"
        self._surface.stroke_rounded_rect(sv_x, sv_y, sv_w, sv_h, 6.0 * s, 6.0 * s, border_col, stroke_width=1.0 * s)

        # 2. Render Hue Spectrum Slider
        hx, hy, hw, hh = layout["hue"]
        hue_grad = LinearGradient(hx, hy, hx + hw, hy)
        hue_stops = [
            (0.00, "#ff0000"),
            (0.17, "#ffff00"),
            (0.33, "#00ff00"),
            (0.50, "#00ffff"),
            (0.67, "#0000ff"),
            (0.83, "#ff00ff"),
            (1.00, "#ff0000"),
        ]
        for offset, col in hue_stops:
            hue_grad.add_stop(offset, col)

        self._surface.fill_rounded_rect(hx, hy, hw, hh, hh / 2.0, hh / 2.0, hue_grad)
        self._surface.stroke_rounded_rect(hx, hy, hw, hh, hh / 2.0, hh / 2.0, border_col, stroke_width=1.0 * s)

        # Hue Thumb
        htx = hx + self._h * hw
        self._surface.fill_circle(htx, hy + hh / 2.0, hh / 2.0 + 1.0 * s, "#ffffff")
        self._surface.stroke_circle(htx, hy + hh / 2.0, hh / 2.0 + 1.0 * s, "#334155", stroke_width=1.5 * s)

        # 3. Render Alpha Slider (if enabled)
        if layout["alpha"]:
            ax, ay, aw, ah = layout["alpha"]
            curr_hex = self.get_color()[:7]

            alpha_grad = LinearGradient(ax, ay, ax + aw, ay)
            alpha_grad.add_stop(0.0, curr_hex, alpha=0.0)
            alpha_grad.add_stop(1.0, curr_hex, alpha=1.0)

            self._surface.fill_rounded_rect(ax, ay, aw, ah, ah / 2.0, ah / 2.0, alpha_grad)
            self._surface.stroke_rounded_rect(ax, ay, aw, ah, ah / 2.0, ah / 2.0, border_col, stroke_width=1.0 * s)

            # Alpha Thumb
            atx = ax + self._a * aw
            self._surface.fill_circle(atx, ay + ah / 2.0, ah / 2.0 + 1.0 * s, "#ffffff")
            self._surface.stroke_circle(atx, ay + ah / 2.0, ah / 2.0 + 1.0 * s, "#334155", stroke_width=1.5 * s)

        # 4. Swatch & Hex Badge
        sw_x, sw_y, sw_w, sw_h = layout["swatch"]
        hex_x, hex_y, hex_w, hex_h = layout["hex"]
        curr_col = self.get_color()

        # Swatch fill
        self._surface.fill_rounded_rect(sw_x, sw_y, sw_w, sw_h, 6.0 * s, 6.0 * s, curr_col)
        self._surface.stroke_rounded_rect(sw_x, sw_y, sw_w, sw_h, 6.0 * s, 6.0 * s, border_col, stroke_width=1.0 * s)

        # Hex info box
        input_bg = pal.card_bg if hasattr(pal, "card_bg") else "#1e293b"
        self._surface.fill_rounded_rect(hex_x, hex_y, hex_w, hex_h, 6.0 * s, 6.0 * s, input_bg)
        self._surface.stroke_rounded_rect(hex_x, hex_y, hex_w, hex_h, 6.0 * s, 6.0 * s, border_col, stroke_width=1.0 * s)
        font_sz = 10.5 * s
        text_y = hex_y + (hex_h / 2.0) + (font_sz * 0.35)
        self._surface.draw_text(
            curr_col,
            hex_x + hex_w / 2.0,
            text_y,
            font_size=font_sz,
            bold=True,
            color=pal.fg,
            align="center",
        )

        # 5. Preset Palette Swatches
        if layout["swatches_y"] is not None:
            sy = layout["swatches_y"]
            gap = layout["swatch_gap"]
            size = layout["swatch_size"]
            pad = layout["pad"]
            for idx, hex_col in enumerate(PRESET_SWATCHES):
                col_x = pad + (idx % 6) * (size + gap + 10.0 * s)
                row_y = sy + (idx // 6) * (size + gap + 4.0 * s)
                self._surface.fill_rounded_rect(col_x, row_y, size, size, 3.0 * s, 3.0 * s, hex_col)
                self._surface.stroke_rounded_rect(col_x, row_y, size, size, 3.0 * s, 3.0 * s, border_col, stroke_width=0.8 * s)

        self.end_render()


class ColorWell(Widget):
    """
    Compact button displaying a color swatch that opens a ColorPicker popup on click.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        color: str = "#3b82f6",
        width: int = 44,
        height: int = 32,
        on_change: Optional[Callable[[str], None]] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._color = color
        self._on_change = on_change
        self._popup: Optional[tk.Toplevel] = None
        self._root_bind_id: Optional[str] = None

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            tag_name="color_well",
            **kwargs,
        )

        self.bind("<Button-1>", self._on_click)

    @property
    def color(self) -> str:
        return self._color

    @color.setter
    def color(self, val: str) -> None:
        self._color = val
        self.render()

    def _on_click(self, _event: tk.Event) -> None:
        if self._popup and self._popup.winfo_exists():
            self._close_popup()
        else:
            self.open_picker()

    def _close_popup(self) -> None:
        top = self.winfo_toplevel()
        if self._root_bind_id and top and top.winfo_exists():
            try:
                top.unbind("<ButtonPress-1>", self._root_bind_id)
            except Exception:
                pass
            self._root_bind_id = None

        if self._popup and self._popup.winfo_exists():
            try:
                self._popup.destroy()
            except Exception:
                pass
        self._popup = None

    def _on_root_click(self, event: tk.Event) -> None:
        if not self._popup or not self._popup.winfo_exists():
            return

        px = event.x_root
        py = event.y_root

        # Check if click is inside the popup
        try:
            pop_x = self._popup.winfo_rootx()
            pop_y = self._popup.winfo_rooty()
            pop_w = self._popup.winfo_width()
            pop_h = self._popup.winfo_height()
            if pop_x <= px <= pop_x + pop_w and pop_y <= py <= pop_y + pop_h:
                return
        except Exception:
            pass

        # Check if click is on the trigger widget itself
        try:
            trig_x = self.winfo_rootx()
            trig_y = self.winfo_rooty()
            trig_w = self.winfo_width()
            trig_h = self.winfo_height()
            if trig_x <= px <= trig_x + trig_w and trig_y <= py <= trig_h + trig_y:
                return
        except Exception:
            pass

        # Clicked outside: close popup cleanly
        self._close_popup()

    def _on_destroy(self, event=None) -> None:
        self._close_popup()
        super()._on_destroy(event)

    def open_picker(self) -> None:
        """Open popup ColorPicker floating window."""
        self._close_popup()

        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)

        # Position below well
        root_x = self.winfo_rootx()
        root_y = self.winfo_rooty() + self.winfo_height() + 4

        # Card container inside popup
        picker_w = 250
        picker_h = 280
        card = Card(self._popup, width=picker_w + 24, height=picker_h + 24, rx=12, ry=12, elevation=6)
        card.pack(fill="both", expand=True)

        def on_pick(c: str) -> None:
            self._color = c
            self.render()
            if self._on_change:
                self._on_change(c)

        picker = ColorPicker(
            card.body,
            initial_color=self._color,
            width=picker_w,
            height=picker_h,
            on_change=on_pick,
            parent_bg=card.bg_color,
        )
        picker.pack(fill="both", expand=True)

        self._popup.geometry(f"+{root_x}+{root_y}")
        top = self.winfo_toplevel()
        if top and top.winfo_exists():
            self._root_bind_id = top.bind("<ButtonPress-1>", self._on_root_click, add="+")

    def render(self) -> None:
        if self._surface is None:
            return

        w = float(self._widget_w)
        h = float(self._widget_h)
        s = self._scale
        pal = get_theme()

        self._surface.clear(self._parent_bg)

        # Button card border & fill
        border_col = pal.card_border if hasattr(pal, "card_border") else "#475569"
        rx = 6.0 * s
        self._surface.fill_rounded_rect(1.0 * s, 1.0 * s, w - 2.0 * s, h - 2.0 * s, rx, rx, pal.card_bg)
        self._surface.stroke_rounded_rect(1.0 * s, 1.0 * s, w - 2.0 * s, h - 2.0 * s, rx, rx, border_col, stroke_width=1.0 * s)

        # Inner color swatch pill
        pad = 5.0 * s
        sw_w = w - 2.0 * pad
        sw_h = h - 2.0 * pad
        self._surface.fill_rounded_rect(pad, pad, sw_w, sw_h, 4.0 * s, 4.0 * s, self._color)
        self._surface.stroke_rounded_rect(pad, pad, sw_w, sw_h, 4.0 * s, 4.0 * s, "#00000033", stroke_width=1.0 * s)

        self.end_render()


def ask_color(
    initial_color: str = "#3b82f6",
    parent: Optional[tk.Misc] = None,
    title: str = "Select Color",
) -> Optional[str]:
    """Modal Blend2D color selection dialog."""
    root = parent or tk._default_root
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    selected_color = {"val": initial_color, "confirmed": False}

    picker_w = 260
    picker_h = 280
    card = Card(dialog, width=picker_w + 32, height=picker_h + 76, rx=14, ry=14, elevation=6)
    card.pack(fill="both", expand=True, padx=8, pady=8)

    def on_change(c: str) -> None:
        selected_color["val"] = c

    picker = ColorPicker(
        card.body,
        initial_color=initial_color,
        width=picker_w,
        height=picker_h,
        on_change=on_change,
        parent_bg=card.bg_color,
    )
    picker.pack(fill="both", expand=True, padx=4, pady=(4, 0))

    btn_frame = tk.Frame(card.body, bg=card.bg_color)
    btn_frame.pack(fill="x", padx=4, pady=(8, 4))

    def on_ok() -> None:
        selected_color["confirmed"] = True
        dialog.destroy()

    def on_cancel() -> None:
        dialog.destroy()

    Button(btn_frame, text="Cancel", command=on_cancel, variant="secondary", width=80).pack(side="right", padx=4)
    Button(btn_frame, text="OK", command=on_ok, variant="primary", width=80).pack(side="right", padx=4)

    dialog.wait_window(dialog)
    return selected_color["val"] if selected_color["confirmed"] else None
