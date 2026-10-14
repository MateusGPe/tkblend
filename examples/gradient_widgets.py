#!/usr/bin/env python3
"""
Custom Vector Widgets with C++ DrawBatch Gradients Showcase.
Demonstrates building high-performance, pure Blend2D vector widgets using
C++ DrawBatch display lists, multi-stop linear/radial gradients, and zero TTK dependencies.
"""

from __future__ import annotations

import math
import tkinter as tk
from typing import Optional, Callable, Any, Sequence, Tuple, Union

import tkblend as tb
from tkblend import (
    BaseControl,
    LinearGradient,
    RadialGradient,
    DrawBatch,
    Color,
    Badge,
    Switch,
    get_theme,
    set_theme,
    Palette,
)
from tkblend._tkblend import ControllerPseudoState


# =============================================================================
# Gradient Color Presets
# =============================================================================

GRADIENT_PRESETS = {
    "cyberpunk": [
        (0.0, "#ff007f"),
        (0.5, "#7928ca"),
        (1.0, "#00f0ff"),
    ],
    "sunset": [
        (0.0, "#f97316"),
        (0.5, "#ec4899"),
        (1.0, "#8b5cf6"),
    ],
    "ocean": [
        (0.0, "#06b6d4"),
        (0.5, "#3b82f6"),
        (1.0, "#6366f1"),
    ],
    "emerald": [
        (0.0, "#10b981"),
        (0.5, "#059669"),
        (1.0, "#047857"),
    ],
    "aurora": [
        (0.0, "#a855f7"),
        (0.5, "#ec4899"),
        (1.0, "#f43f5e"),
    ],
    "amber": [
        (0.0, "#f59e0b"),
        (0.5, "#d97706"),
        (1.0, "#b45309"),
    ],
    "card_dark": [
        (0.0, "#272530"),
        (0.5, "#201e28"),
        (1.0, "#191820"),
    ],
    "card_light": [
        (0.0, "#ffffff"),
        (0.5, "#f8fafc"),
        (1.0, "#f1f5f9"),
    ],
}


def _create_linear_gradient(
    stops: Sequence[Tuple[float, str]],
    x0: float = 0.0,
    y0: float = 0.0,
    x1: float = 1.0,
    y1: float = 0.0,
) -> LinearGradient:
    """Helper to construct a LinearGradient from stops."""
    grad = LinearGradient(x0, y0, x1, y1)
    for offset, color in stops:
        grad.add_stop(offset, color)
    return grad


def _get_preset_glow_color(stops: Sequence[Tuple[float, str]], alpha: int = 70) -> Color:
    """Extract vibrant primary accent color from stops and return Color with specified alpha."""
    try:
        idx = 0 if len(stops) <= 2 else len(stops) // 2
        hex_col = stops[idx][1]
        c = hex_col.lstrip("#")
        if len(c) == 6:
            r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
            return Color(r, g, b, alpha)
    except Exception:
        pass
    return Color(99, 102, 241, alpha)


# =============================================================================
# Custom Widget 1: GradientButton
# =============================================================================

class GradientButton(BaseControl):
    """
    Push button powered by C++ DrawBatch with multi-stop linear gradients,
    dynamic state transitions (normal, hover, pressed), and soft drop shadows.
    """

    SHADOW_PAD_X: float = 8.0
    SHADOW_PAD_TOP: float = 5.0
    SHADOW_PAD_BOTTOM: float = 9.0

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "",
        preset: str = "cyberpunk",
        stops: Optional[Sequence[Tuple[float, str]]] = None,
        command: Optional[Callable[..., Any]] = None,
        width: int = 136,
        height: int = 42,
        radius: float = 10.0,
        **kwargs,
    ):
        self._text = str(text)
        self._preset = preset
        self._stops = list(stops) if stops else list(GRADIENT_PRESETS.get(preset, GRADIENT_PRESETS["cyberpunk"]))
        self._radius = float(radius)
        self._command = command

        super().__init__(
            master=master,
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )
        self._update_vars(width, height)
        self._rebuild_batches()

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        self._text = str(val)
        self.set_var("--text", self._text)
        self.request_redraw()

    def set_stops(self, stops: Sequence[Tuple[float, str]]) -> None:
        self._stops = list(stops)
        self._rebuild_batches()
        self.request_redraw()

    def _get_glow_color(self, is_light: bool, hover: bool = False) -> Color:
        alpha = (75 if hover else 45) if is_light else (115 if hover else 75)
        return _get_preset_glow_color(self._stops, alpha=alpha)

    def _rebuild_batches(self) -> None:
        """Create normal, hover, and pressed DrawBatches with unclipped soft glow shadows."""
        r = self._radius
        pal = get_theme()
        is_light = pal.name.lower() == "light"
        bx = self.SHADOW_PAD_X
        by = self.SHADOW_PAD_TOP

        # 1. Normal State Batch
        norm_grad = _create_linear_gradient(self._stops, 0.0, 0.0, 1.0, 1.0)
        norm_batch = DrawBatch()
        norm_batch.clear_var("--parent-bg")
        # Soft vibrant glow drop shadow
        norm_shadow_col = self._get_glow_color(is_light, hover=False)
        norm_batch.draw_shadow_rounded_rect_var(
            bx, by, 0.0, 0.0, r, r,
            5.5, 0.0, 0.0, 2.0,
            "--btn-shadow", "", "", "",
            norm_shadow_col, "--w_btn", "--h_btn"
        )
        # Gradient body
        norm_batch.fill_rounded_rect_gradient(
            bx, by, 0.0, 0.0, r, r,
            norm_grad, bbox_relative=True,
            w_var="--w_btn", h_var="--h_btn"
        )
        # Subtle top highlight sheen
        sheen_grad = LinearGradient(0.0, 0.0, 0.0, 1.0)
        sheen_grad.add_stop(0.0, (255, 255, 255, 60))
        sheen_grad.add_stop(1.0, (255, 255, 255, 0))
        norm_batch.fill_rounded_rect_gradient(
            bx, by, 0.0, 0.0, r, r,
            sheen_grad, bbox_relative=True,
            w_var="--w_btn", h_var="--h_btn"
        )
        # Button text centered dynamically via C++ variables
        norm_batch.draw_text_var(
            "", 0.0, 0.0, 13.0, "sans-serif",
            "--btn-fg", "--text", "--font-size",
            Color(255, 255, 255), 1, 600, False,
            "--text-x", "--text-y"
        )
        self._normal_batch = norm_batch

        # 2. Hover State Batch (brighter stops & intensified neon glow)
        hover_stops = [(offset, self._brighten_color(col, 1.15)) for offset, col in self._stops]
        hover_grad = _create_linear_gradient(hover_stops, 0.0, 0.0, 1.0, 1.0)
        hover_batch = DrawBatch()
        hover_batch.clear_var("--parent-bg")
        hover_shadow_col = self._get_glow_color(is_light, hover=True)
        hover_batch.draw_shadow_rounded_rect_var(
            bx, by, 0.0, 0.0, r, r,
            7.5, 0.5, 0.0, 2.5,
            "--btn-shadow-hover", "", "", "",
            hover_shadow_col, "--w_btn", "--h_btn"
        )
        hover_batch.fill_rounded_rect_gradient(
            bx, by, 0.0, 0.0, r, r,
            hover_grad, bbox_relative=True,
            w_var="--w_btn", h_var="--h_btn"
        )
        hover_batch.fill_rounded_rect_gradient(
            bx, by, 0.0, 0.0, r, r,
            sheen_grad, bbox_relative=True,
            w_var="--w_btn", h_var="--h_btn"
        )
        hover_batch.draw_text_var(
            "", 0.0, 0.0, 13.0, "sans-serif",
            "--btn-fg", "--text", "--font-size",
            Color(255, 255, 255), 1, 650, False,
            "--text-x", "--text-y"
        )
        self._hover_batch = hover_batch

        # 3. Pressed State Batch (inset feel, shifted text)
        pressed_stops = [(offset, self._brighten_color(col, 0.85)) for offset, col in self._stops]
        pressed_grad = _create_linear_gradient(pressed_stops, 0.0, 0.0, 1.0, 1.0)
        pressed_batch = DrawBatch()
        pressed_batch.clear_var("--parent-bg")
        pressed_batch.fill_rounded_rect_gradient(
            bx, by + 1.0, 0.0, 0.0, r, r,
            pressed_grad, bbox_relative=True,
            w_var="--w_btn", h_var="--h_btn"
        )
        pressed_batch.draw_text_var(
            "", 0.0, 0.0, 13.0, "sans-serif",
            "--btn-fg", "--text", "--font-size",
            Color(240, 240, 240), 1, 600, False,
            "--text-x", "--text-y-pressed"
        )
        self._pressed_batch = pressed_batch

        # Initial binding
        self.bind_batch(self._normal_batch)

    def on_state_changed(self, new_state: int, old_state: int) -> None:
        """Dynamically switch C++ DrawBatch based on controller pseudo-state."""
        if (new_state & ControllerPseudoState.StatePressed) != 0:
            self.bind_batch(self._pressed_batch)
        elif (new_state & ControllerPseudoState.StateHovered) != 0:
            self.bind_batch(self._hover_batch)
        else:
            self.bind_batch(self._normal_batch)

    def on_theme_update(self, pal: Palette) -> None:
        self._rebuild_batches()

    def on_resize(self, width: int, height: int) -> None:
        self._update_vars(width, height)

    def _update_vars(self, w: int, h: int) -> None:
        bw = max(10, w - int(2 * self.SHADOW_PAD_X))
        bh = max(10, h - int(self.SHADOW_PAD_TOP + self.SHADOW_PAD_BOTTOM))
        bx = self.SHADOW_PAD_X
        by = self.SHADOW_PAD_TOP
        self.set_var("--w_btn", str(bw))
        self.set_var("--h_btn", str(bh))
        self.set_var("--text", self._text)
        self.set_var("--text-x", str(bx + bw / 2.0))
        self.set_var("--text-y", str(by + bh / 2.0 + 13.0 * 0.35))
        self.set_var("--text-y-pressed", str(by + bh / 2.0 + 13.0 * 0.35 + 1.0))
        self.set_var("--btn-fg", "#ffffff")

    def paint_and_blit(self) -> None:
        w = self.winfo_width()
        h = self.winfo_height()
        self._update_vars(w, h)
        super().paint_and_blit()

    @staticmethod
    def _brighten_color(hex_str: str, factor: float) -> str:
        """Quick hex color brightness adjuster."""
        try:
            c = hex_str.lstrip("#")
            if len(c) == 6:
                r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
                r = min(255, int(r * factor))
                g = min(255, int(g * factor))
                b = min(255, int(b * factor))
                return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            pass
        return hex_str


# =============================================================================
# Custom Widget 2: GradientCard
# =============================================================================

class GradientCard(BaseControl):
    """
    Modern container card with a smooth multi-stop gradient backdrop,
    soft unclipped drop shadow, automatic content container, and dynamic theme responsiveness.
    """

    SHADOW_PAD_X: float = 14.0
    SHADOW_PAD_TOP: float = 10.0
    SHADOW_PAD_BOTTOM: float = 18.0
    CONTENT_PAD_X: float = 12.0
    CONTENT_PAD_Y: float = 10.0

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        preset: str = "ocean",
        stops: Optional[Sequence[Tuple[float, str]]] = None,
        radius: float = 14.0,
        subtle: bool = False,
        width: int = 280,
        height: int = 160,
        **kwargs,
    ):
        self._radius = float(radius)
        self._subtle = subtle
        self._preset = preset
        self._custom_stops = list(stops) if stops else None
        self._content: Optional[tk.Frame] = None

        super().__init__(
            master=master,
            width=width,
            height=height,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._update_geometry(width, height)
        self._update_gradient_batch()

    @property
    def content(self) -> tk.Frame:
        """Lazy inner content container frame positioned safely inside the card's rounded surface."""
        if self._content is None:
            self._content = tk.Frame(self, background=self.bg_color)
            self._content.place(
                x=int(self.SHADOW_PAD_X + self.CONTENT_PAD_X),
                y=int(self.SHADOW_PAD_TOP + self.CONTENT_PAD_Y),
                relwidth=1.0,
                relheight=1.0,
                width=-int(2 * (self.SHADOW_PAD_X + self.CONTENT_PAD_X)),
                height=-int(self.SHADOW_PAD_TOP + self.SHADOW_PAD_BOTTOM + 2 * self.CONTENT_PAD_Y),
            )
        return self._content

    @property
    def bg_color(self) -> str:
        """Compound container protocol: returns active card fill."""
        if self._subtle:
            pal = get_theme()
            is_dark = pal.name.lower() != "light"
            return "#201e28" if is_dark else "#f8fafc"
        return "#1b1924"

    def _get_active_stops(self) -> Sequence[Tuple[float, str]]:
        if self._custom_stops:
            return self._custom_stops
        if self._subtle:
            pal = get_theme()
            is_dark = pal.name.lower() != "light"
            return GRADIENT_PRESETS["card_dark"] if is_dark else GRADIENT_PRESETS["card_light"]
        return GRADIENT_PRESETS.get(self._preset, GRADIENT_PRESETS["ocean"])

    def _update_gradient_batch(self) -> None:
        r = self._radius
        pal = get_theme()
        is_light = pal.name.lower() == "light"
        bx = self.SHADOW_PAD_X
        by = self.SHADOW_PAD_TOP

        batch = DrawBatch()
        batch.clear_var("--parent-bg")

        # 1. Soft unclipped drop shadow
        if self._subtle:
            # Elegant neutral elevation shadow
            shadow_col = Color(0, 0, 0, 22) if is_light else Color(0, 0, 0, 50)
        else:
            # Vibrant glow for colorful cards
            shadow_col = _get_preset_glow_color(self._get_active_stops(), alpha=45 if is_light else 70)

        batch.draw_shadow_rounded_rect_var(
            bx, by, 0.0, 0.0, r, r,
            11.0, 0.0, 0.0, 4.0,
            "--card-shadow", "", "", "",
            shadow_col, "--w_card", "--h_card"
        )

        # 2. Card surface fill
        if self._subtle:
            # Exact solid card fill seamlessly matching inner frame background
            fill_col = Color(248, 250, 252) if is_light else Color(32, 30, 40)
            batch.fill_rounded_rect_var(
                bx, by, 0.0, 0.0, r, r,
                "--card-fill", "", "",
                fill_col, "--w_card", "--h_card"
            )
        else:
            stops = self._get_active_stops()
            grad = _create_linear_gradient(stops, 0.0, 0.0, 1.0, 1.0)
            batch.fill_rounded_rect_gradient(
                bx, by, 0.0, 0.0, r, r,
                grad, bbox_relative=True,
                w_var="--w_card", h_var="--h_card"
            )

        # 3. Delicate inner border / highlight
        if is_light and self._subtle:
            border_col = Color(0, 0, 0, 22)
        elif self._subtle:
            border_col = Color(255, 255, 255, 45)
        else:
            border_col = Color(255, 255, 255, 60)
        batch.stroke_rounded_rect_var(
            bx, by, 0.0, 0.0, r, r,
            "--card-border", 1.0, "", "", "",
            border_col, "--w_card", "--h_card"
        )

        self.bind_batch(batch)

    def _update_geometry(self, width: int, height: int) -> None:
        bw = max(10, width - int(2 * self.SHADOW_PAD_X))
        bh = max(10, height - int(self.SHADOW_PAD_TOP + self.SHADOW_PAD_BOTTOM))
        self.set_var("--w_card", str(bw))
        self.set_var("--h_card", str(bh))

    def on_resize(self, width: int, height: int) -> None:
        self._update_geometry(width, height)
        if self._content is not None:
            usable_w = max(100, width - int(2 * (self.SHADOW_PAD_X + self.CONTENT_PAD_X) + 16))
            for child in self._content.winfo_children():
                if isinstance(child, tk.Label):
                    try:
                        cur_wrap = int(child.cget("wraplength"))
                        if cur_wrap > 0:
                            child.configure(wraplength=usable_w)
                    except Exception:
                        pass

    def paint_and_blit(self) -> None:
        w = self.winfo_width()
        h = self.winfo_height()
        self._update_geometry(w, h)
        super().paint_and_blit()

    def on_theme_update(self, pal: Palette) -> None:
        self._update_gradient_batch()
        if self._content is not None:
            try:
                self._content.configure(background=self.bg_color)
            except Exception:
                pass
            tb.cascade_bg_to_children(self._content, self.bg_color, palette=pal)
        self.request_redraw()


# =============================================================================
# Custom Widget 3: GradientMetricCard
# =============================================================================

class GradientMetricCard(BaseControl):
    """
    Dedicated metric display card rendered with pure Blend2D / DrawBatch vector graphics.
    Draws multi-stop gradients, vibrant neon drop shadows, highlight sheen, and
    title/value/subtitle text directly onto the surface canvas with full alpha transparency.
    """

    SHADOW_PAD_X: float = 12.0
    SHADOW_PAD_TOP: float = 8.0
    SHADOW_PAD_BOTTOM: float = 14.0

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: str = "",
        value: str = "",
        subtitle: str = "",
        preset: str = "cyberpunk",
        stops: Optional[Sequence[Tuple[float, str]]] = None,
        radius: float = 12.0,
        width: int = 210,
        height: int = 135,
        **kwargs,
    ):
        self._title = str(title)
        self._value_text = str(value)
        self._subtitle = str(subtitle)
        self._preset = preset
        self._stops = list(stops) if stops else list(GRADIENT_PRESETS.get(preset, GRADIENT_PRESETS["cyberpunk"]))
        self._radius = float(radius)

        super().__init__(
            master=master,
            width=width,
            height=height,
            takefocus=False,
            **kwargs,
        )
        self.set_var("--title", self._title)
        self.set_var("--val", self._value_text)
        self.set_var("--sub", self._subtitle)
        self.set_var("--title-fg", "#ffffff")
        self.set_var("--val-fg", "#ffffff")
        self.set_var("--sub-fg", "#e0e7ff")
        self._update_geometry(width, height)
        self._rebuild_batch()

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, val: str) -> None:
        self._title = str(val)
        self.set_var("--title", self._title)
        self.request_redraw()

    @property
    def value(self) -> str:
        return self._value_text

    @value.setter
    def value(self, val: str) -> None:
        self._value_text = str(val)
        self.set_var("--val", self._value_text)
        self.request_redraw()

    @property
    def subtitle(self) -> str:
        return self._subtitle

    @subtitle.setter
    def subtitle(self, val: str) -> None:
        self._subtitle = str(val)
        self.set_var("--sub", self._subtitle)
        self.request_redraw()

    def set_stops(self, stops: Sequence[Tuple[float, str]]) -> None:
        self._stops = list(stops)
        self._rebuild_batch()
        self.request_redraw()

    def _update_geometry(self, width: int, height: int) -> None:
        bw = max(10, width - int(2 * self.SHADOW_PAD_X))
        bh = max(10, height - int(self.SHADOW_PAD_TOP + self.SHADOW_PAD_BOTTOM))
        self.set_var("--w_card", str(bw))
        self.set_var("--h_card", str(bh))

    def _rebuild_batch(self) -> None:
        r = self._radius
        bx = self.SHADOW_PAD_X
        by = self.SHADOW_PAD_TOP
        grad = _create_linear_gradient(self._stops, 0.0, 0.0, 1.0, 1.0)
        pal = get_theme()
        is_light = pal.name.lower() == "light"

        batch = DrawBatch()
        batch.clear_var("--parent-bg")

        # 1. Soft unclipped vibrant ambient glow shadow
        shadow_col = _get_preset_glow_color(self._stops, alpha=50 if is_light else 85)
        batch.draw_shadow_rounded_rect_var(
            bx, by, 0.0, 0.0, r, r,
            9.0, 0.0, 0.0, 3.0,
            "--card-shadow", "", "", "",
            shadow_col, "--w_card", "--h_card"
        )

        # 2. Vibrant multi-stop linear gradient fill across entire card
        batch.fill_rounded_rect_gradient(
            bx, by, 0.0, 0.0, r, r,
            grad, bbox_relative=True,
            w_var="--w_card", h_var="--h_card"
        )

        # 3. Glass sheen highlight
        sheen_grad = LinearGradient(0.0, 0.0, 0.0, 1.0)
        sheen_grad.add_stop(0.0, (255, 255, 255, 60))
        sheen_grad.add_stop(1.0, (255, 255, 255, 0))
        batch.fill_rounded_rect_gradient(
            bx, by, 0.0, 0.0, r, r,
            sheen_grad, bbox_relative=True,
            w_var="--w_card", h_var="--h_card"
        )

        # 4. Delicate inner border
        batch.stroke_rounded_rect_var(
            bx, by, 0.0, 0.0, r, r,
            "--card-border", 1.0, "", "", "",
            Color(255, 255, 255, 60), "--w_card", "--h_card"
        )

        # 5. Direct text rendering with transparent blending safe within card body
        batch.draw_text_var(
            "", bx + 16.0, by + 24.0, 9.5, "sans-serif",
            "--title-fg", "--title", "--title-size",
            Color(255, 255, 255, 240), 0, 700, False
        )
        batch.draw_text_var(
            "", bx + 16.0, by + 64.0, 22.0, "sans-serif",
            "--val-fg", "--val", "--val-size",
            Color(255, 255, 255, 255), 0, 700, False
        )
        batch.draw_text_var(
            "", bx + 16.0, by + 94.0, 9.5, "sans-serif",
            "--sub-fg", "--sub", "--sub-size",
            Color(224, 231, 255, 230), 0, 400, False
        )

        self.bind_batch(batch)

    def on_resize(self, width: int, height: int) -> None:
        self._update_geometry(width, height)

    def paint_and_blit(self) -> None:
        w = self.winfo_width()
        h = self.winfo_height()
        self._update_geometry(w, h)
        super().paint_and_blit()

    def on_theme_update(self, pal: Palette) -> None:
        self._rebuild_batch()
        self.request_redraw()


# =============================================================================
# Custom Widget 3: GradientProgressBar
# =============================================================================

class GradientProgressBar(BaseControl):
    """
    High-performance progress bar with a multi-stop gradient indicator bar,
    subtle track background, and smooth variable updates.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        value: float = 0.65,
        preset: str = "cyberpunk",
        stops: Optional[Sequence[Tuple[float, str]]] = None,
        width: int = 240,
        height: int = 14,
        radius: float = 7.0,
        **kwargs,
    ):
        self._value = max(0.0, min(1.0, float(value)))
        self._radius = float(radius)
        self._preset = preset
        self._stops = list(stops) if stops else list(GRADIENT_PRESETS.get(preset, GRADIENT_PRESETS["cyberpunk"]))

        super().__init__(
            master=master,
            width=width,
            height=height,
            **kwargs,
        )
        self.set_var("--w_pb", str(width))
        self.set_var("--h_pb", str(height))
        self.set_var("--w_bar", str(float(width) * self._value))
        self._rebuild_batch()

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = max(0.0, min(1.0, float(val)))
        w = max(10, self.winfo_width()) if self.winfo_width() > 1 else max(10, self._logical_w)
        self.set_var("--w_bar", str(float(w) * self._value))
        self.request_redraw()

    def set_stops(self, stops: Sequence[Tuple[float, str]]) -> None:
        self._stops = list(stops)
        self._rebuild_batch()
        self.request_redraw()

    def _rebuild_batch(self) -> None:
        r = self._radius
        bar_grad = _create_linear_gradient(self._stops, 0.0, 0.0, 1.0, 0.0)
        pal = get_theme()
        is_light = pal.name.lower() == "light"
        track_bg = Color(225, 228, 235, 200) if is_light else Color(30, 28, 36, 180)
        track_border = Color(0, 0, 0, 30) if is_light else Color(255, 255, 255, 20)

        batch = DrawBatch()
        batch.clear_var("--parent-bg")

        # 1. Background Track
        batch.fill_rounded_rect_var(
            0.0, 0.0, 0.0, 0.0, r, r,
            "--track-bg", "", "",
            track_bg, "--w_pb", "--h_pb"
        )
        batch.stroke_rounded_rect_var(
            0.0, 0.0, 0.0, 0.0, r, r,
            "--track-border", 1.0, "", "", "",
            track_border, "--w_pb", "--h_pb"
        )

        # 2. Active Indicator Gradient Bar
        batch.fill_rounded_rect_gradient(
            0.0, 0.0, 0.0, 0.0, r, r,
            bar_grad, bbox_relative=True,
            w_var="--w_bar", h_var="--h_pb"
        )

        # 3. Top Gloss Sheen
        gloss_grad = LinearGradient(0.0, 0.0, 0.0, 1.0)
        gloss_grad.add_stop(0.0, (255, 255, 255, 80))
        gloss_grad.add_stop(1.0, (255, 255, 255, 0))
        batch.fill_rounded_rect_gradient(
            0.0, 0.0, 0.0, 0.0, r, r,
            gloss_grad, bbox_relative=True,
            w_var="--w_bar", h_var="--h_pb"
        )

        self.bind_batch(batch)

    def on_theme_update(self, pal: Palette) -> None:
        self._rebuild_batch()
        self.request_redraw()

    def on_resize(self, width: int, height: int) -> None:
        self._logical_w = width
        w = max(10, width)
        h = max(6, height)
        self.set_var("--w_pb", str(w))
        self.set_var("--h_pb", str(h))
        self.set_var("--w_bar", str(float(w) * self._value))

    def paint_and_blit(self) -> None:
        w = max(10, self.winfo_width())
        h = max(6, self.winfo_height())
        bar_w = max(0.0, min(float(w), float(w) * self._value))
        self.set_var("--w_pb", str(w))
        self.set_var("--h_pb", str(h))
        self.set_var("--w_bar", str(bar_w))
        super().paint_and_blit()


# =============================================================================
# Custom Widget 4: GradientSlider
# =============================================================================

class GradientSlider(BaseControl):
    """
    Slider widget with a multi-stop color spectrum/gradient track,
    reactive vector thumb, and dynamic value callbacks.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        from_: float = 0.0,
        to: float = 100.0,
        value: float = 50.0,
        preset: str = "sunset",
        stops: Optional[Sequence[Tuple[float, str]]] = None,
        command: Optional[Callable[[float], None]] = None,
        width: int = 240,
        height: int = 32,
        **kwargs,
    ):
        self._from = float(from_)
        self._to = float(to)
        self._value = float(value)
        self._preset = preset
        self._stops = list(stops) if stops else list(GRADIENT_PRESETS.get(preset, GRADIENT_PRESETS["sunset"]))

        super().__init__(
            master=master,
            width=width,
            height=height,
            command=command,
            cursor="hand2",
            **kwargs,
        )
        self._command = command
        self._bind_mouse_events()
        self._rebuild_batch()
        self._sync_thumb_pos()

    def _sync_thumb_pos(self, current_w: Optional[float] = None) -> None:
        pad = 16.0
        if current_w is not None and current_w > 1:
            w = max(pad * 2.0 + 1.0, float(current_w))
        else:
            w = max(pad * 2.0 + 1.0, float(self.winfo_width()) if self.winfo_width() > 1 else float(self._logical_w))
        usable = max(1.0, w - 2.0 * pad)
        span = max(1e-6, abs(self._to - self._from))
        t = max(0.0, min(1.0, (self._value - self._from) / span))
        thumb_x = pad + t * usable
        self.set_var("--w_track", str(usable))
        self.set_var("--thumb-x", str(thumb_x))
        self.set_var("--thumb-ring", "#ffffff")
        self.set_var("--thumb-center", "#6366f1")

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = max(min(self._from, self._to), min(max(self._from, self._to), float(val)))
        self._sync_thumb_pos()
        self.request_redraw()

    def _bind_mouse_events(self) -> None:
        self.bind("<Button-1>", self._on_mouse_drag)
        self.bind("<B1-Motion>", self._on_mouse_drag)

    def _on_mouse_drag(self, event: tk.Event) -> None:
        pad = 16.0
        w = max(pad * 2.0 + 1.0, float(self.winfo_width()) if self.winfo_width() > 1 else float(self._logical_w))
        usable = max(1.0, w - 2.0 * pad)
        x = max(0.0, min(usable, float(event.x) - pad))
        t = x / usable
        self._value = self._from + t * (self._to - self._from)
        self._sync_thumb_pos()
        self.request_redraw()
        if callable(self._command):
            try:
                self._command(self._value)
            except Exception:
                pass

    def _rebuild_batch(self) -> None:
        track_grad = _create_linear_gradient(self._stops, 0.0, 0.0, 1.0, 0.0)

        batch = DrawBatch()
        batch.clear_var("--parent-bg")

        # 1. Gradient Track (height 8px, rounded 4px)
        batch.fill_rounded_rect_gradient(
            16.0, 12.0, 0.0, 8.0, 4.0, 4.0,
            track_grad, bbox_relative=True,
            w_var="--w_track"
        )
        # Track stroke
        batch.stroke_rounded_rect_var(
            16.0, 12.0, 0.0, 8.0, 4.0, 4.0,
            "--track-border", 1.0, "", "", "",
            Color(255, 255, 255, 30), "--w_track"
        )

        # 2. Multi-layer soft thumb drop shadow
        batch.fill_circle_var(0.0, 16.5, 11.5, "--thumb-shadow-outer", "", Color(0, 0, 0, 18), "--thumb-x")
        batch.fill_circle_var(0.0, 16.0, 9.5, "--thumb-shadow-mid", "", Color(0, 0, 0, 35), "--thumb-x")
        batch.fill_circle_var(0.0, 15.5, 8.0, "--thumb-shadow-core", "", Color(0, 0, 0, 45), "--thumb-x")

        # 3. Outer Thumb Ring
        batch.fill_circle_var(0.0, 16.0, 8.0, "--thumb-ring", "", Color(255, 255, 255), "--thumb-x")
        # 4. Inner Thumb Center
        batch.fill_circle_var(0.0, 16.0, 4.5, "--thumb-center", "", Color(99, 102, 241), "--thumb-x")

        self.bind_batch(batch)

    def on_theme_update(self, pal: Palette) -> None:
        self._rebuild_batch()
        self.request_redraw()

    def on_resize(self, width: int, height: int) -> None:
        self._logical_w = width
        self._sync_thumb_pos(width)

    def paint_and_blit(self) -> None:
        self._sync_thumb_pos()
        super().paint_and_blit()

    def render(self, surf: tb.Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        """Fallback rendering if batch needs precise thumb coordinates."""
        s = scale
        surf.clear(self.resolved_parent_bg)

        pad = 16.0 * s
        track_h = 8.0 * s
        track_y = (height - track_h) / 2.0
        track_w = max(1.0, width - 2.0 * pad)

        # 1. Gradient Track
        grad = _create_linear_gradient(self._stops, pad, track_y, pad + track_w, track_y)
        surf.fill_rounded_rect(pad, track_y, track_w, track_h, 4.0 * s, 4.0 * s, grad)
        surf.stroke_rounded_rect(pad, track_y, track_w, track_h, 4.0 * s, 4.0 * s, Color(255, 255, 255, 35), 1.0 * s)

        # 2. Thumb Handle
        span = max(1e-6, self._to - self._from)
        t = max(0.0, min(1.0, (self._value - self._from) / span))
        thumb_x = pad + t * track_w
        thumb_y = height / 2.0

        # Thumb soft drop shadow
        surf.draw_shadow_rounded_rect(
            thumb_x - 8.5 * s, thumb_y - 8.5 * s + 1.5 * s,
            17.0 * s, 17.0 * s, 8.5 * s, 8.5 * s,
            3.5 * s, 0.0, 0.0, 1.5 * s, Color(0, 0, 0, 50)
        )
        # Thumb outer white body
        surf.fill_circle(thumb_x, thumb_y, 8.0 * s, Color(255, 255, 255))
        # Thumb inner color
        thumb_accent = Color(99, 102, 241)
        surf.fill_circle(thumb_x, thumb_y, 4.5 * s, thumb_accent)


# =============================================================================
# Main Showcase Application
# =============================================================================

class GradientShowcaseApp(tk.Tk):
    """Interactive demo application for pure Blend2D custom gradient widgets."""

    def __init__(self):
        super().__init__()
        self.title("tkblend - Custom Gradient Widgets Showcase")
        self.geometry("980x760")
        self.minsize(860, 680)

        set_theme("dark")
        self._current_theme = "dark"
        self.configure(bg=get_theme().bg)

        self._action_counter = 0
        self._build_ui()
        self._apply_theme_recursive(self, get_theme())

    def _build_ui(self) -> None:
        pal = get_theme()

        # -------------------------------------------------------------
        # 1. Header Frame
        # -------------------------------------------------------------
        header = tk.Frame(self, bg=pal.bg)
        header.pack(fill="x", padx=32, pady=(24, 16))

        title_box = tk.Frame(header, bg=pal.bg)
        title_box.pack(side="left", fill="y")

        title_lbl = tk.Label(
            title_box,
            text="Gradient Widgets Display Lists",
            font=("sans-serif", 18, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        )
        title_lbl.pack(side="left")

        version_badge = Badge(title_box, text="C++ DrawBatch", width=120, height=26)
        version_badge.pack(side="left", padx=12)

        # Theme toggle
        self.theme_switch = Switch(
            header,
            text="Dark Theme",
            is_checked=True,
            command=self._on_theme_toggle,
            width=135,
            height=30,
        )
        self.theme_switch.pack(side="right")

        # -------------------------------------------------------------
        # 2. Main Grid Container
        # -------------------------------------------------------------
        main_container = tk.Frame(self, bg=pal.bg)
        main_container.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        col_left = tk.Frame(main_container, bg=pal.bg)
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        col_right = tk.Frame(main_container, bg=pal.bg)
        col_right.pack(side="right", fill="both", expand=True, padx=(12, 0))

        # -------------------------------------------------------------
        # Left Column - Card 1: Interactive Gradient Buttons
        # -------------------------------------------------------------
        self.btn_card = GradientCard(col_left, preset="card_dark", subtle=True, width=440, height=315)
        self.btn_card.pack(fill="x", pady=(0, 16))

        card1_inner = self.btn_card.content

        lbl1 = tk.Label(
            card1_inner,
            text="Interactive Vector Push Buttons",
            font=("sans-serif", 14, "bold"),
            fg=pal.fg,
            bg=self.btn_card.bg_color,
        )
        lbl1.pack(anchor="w", pady=(0, 4))

        sub1 = tk.Label(
            card1_inner,
            text="State-dependent display lists with hover sheens and soft drop shadows",
            font=("sans-serif", 10),
            fg=pal.secondary,
            bg=self.btn_card.bg_color,
            wraplength=380,
            justify="left",
        )
        sub1.pack(anchor="w", pady=(0, 12))

        row_buttons = tk.Frame(card1_inner, bg=self.btn_card.bg_color)
        row_buttons.pack(fill="x", pady=2)

        self.btn_cyber = GradientButton(
            row_buttons,
            text="Cyberpunk",
            preset="cyberpunk",
            command=lambda: self._on_btn_click("Cyberpunk"),
            width=122,
            height=50,
        )
        self.btn_cyber.pack(side="left", padx=(0, 10))

        self.btn_sunset = GradientButton(
            row_buttons,
            text="Sunset",
            preset="sunset",
            command=lambda: self._on_btn_click("Sunset"),
            width=122,
            height=50,
        )
        self.btn_sunset.pack(side="left", padx=(0, 10))

        self.btn_ocean = GradientButton(
            row_buttons,
            text="Ocean",
            preset="ocean",
            command=lambda: self._on_btn_click("Ocean"),
            width=122,
            height=50,
        )
        self.btn_ocean.pack(side="left")

        row_buttons2 = tk.Frame(card1_inner, bg=self.btn_card.bg_color)
        row_buttons2.pack(fill="x", pady=(8, 6))

        self.btn_emerald = GradientButton(
            row_buttons2,
            text="Emerald Glow",
            preset="emerald",
            command=lambda: self._on_btn_click("Emerald"),
            width=132,
            height=50,
        )
        self.btn_emerald.pack(side="left", padx=(0, 10))

        self.btn_aurora = GradientButton(
            row_buttons2,
            text="Aurora Neon",
            preset="aurora",
            command=lambda: self._on_btn_click("Aurora"),
            width=132,
            height=50,
        )
        self.btn_aurora.pack(side="left")

        self.status_lbl = tk.Label(
            card1_inner,
            text="Click any button to trigger state animation and counter",
            font=("sans-serif", 10, "italic"),
            fg=pal.secondary,
            bg=self.btn_card.bg_color,
        )
        self.status_lbl.pack(anchor="w", pady=(8, 0))

        # -------------------------------------------------------------
        # Left Column - Card 2: Gradient Sliders & Range Controls
        # -------------------------------------------------------------
        self.slider_card = GradientCard(col_left, preset="card_dark", subtle=True, width=440, height=265)
        self.slider_card.pack(fill="x")

        card2_inner = self.slider_card.content

        lbl2 = tk.Label(
            card2_inner,
            text="Multi-Stop Gradient Sliders",
            font=("sans-serif", 14, "bold"),
            fg=pal.fg,
            bg=self.slider_card.bg_color,
        )
        lbl2.pack(anchor="w", pady=(0, 4))

        sub2 = tk.Label(
            card2_inner,
            text="Drag handle to dynamically adjust values and sync progress bars",
            font=("sans-serif", 10),
            fg=pal.secondary,
            bg=self.slider_card.bg_color,
            wraplength=380,
            justify="left",
        )
        sub2.pack(anchor="w", pady=(0, 12))

        # Slider 1: Sunset
        s1_row = tk.Frame(card2_inner, bg=self.slider_card.bg_color)
        s1_row.pack(fill="x", pady=4)
        tk.Label(s1_row, text="Intensity", font=("sans-serif", 10, "bold"), fg=pal.fg, bg=self.slider_card.bg_color, width=10, anchor="w").pack(side="left")
        self.s1_val_lbl = tk.Label(s1_row, text="65%", font=("sans-serif", 10), fg=pal.fg, bg=self.slider_card.bg_color)
        self.s1_val_lbl.pack(side="right", padx=(8, 0))
        self.slider1 = GradientSlider(s1_row, from_=0, to=100, value=65, preset="sunset", command=self._on_slider1_change, width=280)
        self.slider1.pack(side="left", fill="x", expand=True, padx=8)

        # Slider 2: Ocean
        s2_row = tk.Frame(card2_inner, bg=self.slider_card.bg_color)
        s2_row.pack(fill="x", pady=6)
        tk.Label(s2_row, text="Frequency", font=("sans-serif", 10, "bold"), fg=pal.fg, bg=self.slider_card.bg_color, width=10, anchor="w").pack(side="left")
        self.s2_val_lbl = tk.Label(s2_row, text="40%", font=("sans-serif", 10), fg=pal.fg, bg=self.slider_card.bg_color)
        self.s2_val_lbl.pack(side="right", padx=(8, 0))
        self.slider2 = GradientSlider(s2_row, from_=0, to=100, value=40, preset="ocean", command=self._on_slider2_change, width=280)
        self.slider2.pack(side="left", fill="x", expand=True, padx=8)

        # -------------------------------------------------------------
        # Right Column - Card 3: Gradient Metric Cards
        # -------------------------------------------------------------
        metrics_grid = tk.Frame(col_right, bg=pal.bg)
        metrics_grid.pack(fill="x", pady=(0, 16))

        # Vibrant Card A: Throughput
        self.mcard1 = GradientMetricCard(
            metrics_grid,
            title="THROUGHPUT",
            value="1,420 fps",
            subtitle="Zero-copy direct blit",
            preset="cyberpunk",
            radius=12,
            width=210,
            height=135,
        )
        self.mcard1.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Vibrant Card B: Buffer Memory
        self.mcard2 = GradientMetricCard(
            metrics_grid,
            title="BUFFER MEMORY",
            value="0.00 KB",
            subtitle="Zero residual leak",
            preset="ocean",
            radius=12,
            width=210,
            height=135,
        )
        self.mcard2.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # -------------------------------------------------------------
        # Right Column - Card 4: Gradient Progress Bars & Gauges
        # -------------------------------------------------------------
        self.prog_card = GradientCard(col_right, preset="card_dark", subtle=True, width=440, height=355)
        self.prog_card.pack(fill="both", expand=True)

        card4_inner = self.prog_card.content

        lbl4 = tk.Label(
            card4_inner,
            text="Dynamic Gradient Progress Bars",
            font=("sans-serif", 14, "bold"),
            fg=pal.fg,
            bg=self.prog_card.bg_color,
        )
        lbl4.pack(anchor="w", pady=(0, 4))

        sub4 = tk.Label(
            card4_inner,
            text="Linear shader display lists adapting dynamically to value changes",
            font=("sans-serif", 10),
            fg=pal.secondary,
            bg=self.prog_card.bg_color,
            wraplength=380,
            justify="left",
        )
        sub4.pack(anchor="w", pady=(0, 16))

        # Progress 1: Cyberpunk
        p1_box = tk.Frame(card4_inner, bg=self.prog_card.bg_color)
        p1_box.pack(fill="x", pady=6)
        tk.Label(p1_box, text="Cyberpunk Progress", font=("sans-serif", 10, "bold"), fg=pal.fg, bg=self.prog_card.bg_color).pack(anchor="w", pady=(0, 4))
        self.prog1 = GradientProgressBar(p1_box, value=0.65, preset="cyberpunk", width=380, height=16)
        self.prog1.pack(fill="x")

        # Progress 2: Sunset
        p2_box = tk.Frame(card4_inner, bg=self.prog_card.bg_color)
        p2_box.pack(fill="x", pady=10)
        tk.Label(p2_box, text="Sunset Spectrum", font=("sans-serif", 10, "bold"), fg=pal.fg, bg=self.prog_card.bg_color).pack(anchor="w", pady=(0, 4))
        self.prog2 = GradientProgressBar(p2_box, value=0.40, preset="sunset", width=380, height=16)
        self.prog2.pack(fill="x")

        # Progress 3: Emerald
        p3_box = tk.Frame(card4_inner, bg=self.prog_card.bg_color)
        p3_box.pack(fill="x", pady=6)
        tk.Label(p3_box, text="Emerald Buffer Status", font=("sans-serif", 10, "bold"), fg=pal.fg, bg=self.prog_card.bg_color).pack(anchor="w", pady=(0, 4))
        self.prog3 = GradientProgressBar(p3_box, value=0.88, preset="emerald", width=380, height=16)
        self.prog3.pack(fill="x")

        # Interactive animate button
        anim_row = tk.Frame(card4_inner, bg=self.prog_card.bg_color)
        anim_row.pack(fill="x", pady=(16, 0))

        self.anim_btn = GradientButton(
            anim_row,
            text="Pulse Wave Animation",
            preset="aurora",
            command=self._toggle_wave_animation,
            width=180,
            height=36,
        )
        self.anim_btn.pack(side="left")

        self._animating = False
        self._anim_phase = 0.0

    def _on_btn_click(self, name: str) -> None:
        self._action_counter += 1
        self.status_lbl.configure(text=f"Activated [{name}] button (Total interactions: {self._action_counter})")
        # Pulse progress 1 slightly
        curr = self.prog1.value
        self.prog1.value = 0.1 if curr > 0.9 else curr + 0.15

    def _on_slider1_change(self, val: float) -> None:
        t = val / 100.0
        self.s1_val_lbl.configure(text=f"{int(val)}%")
        self.prog1.value = t
        self.mcard1.value = f"{int(800 + val * 12):,} fps"

    def _on_slider2_change(self, val: float) -> None:
        t = val / 100.0
        self.s2_val_lbl.configure(text=f"{int(val)}%")
        self.prog2.value = t

    def _toggle_wave_animation(self) -> None:
        self._animating = not self._animating
        if self._animating:
            self.anim_btn.text = "Stop Animation"
            self._run_wave_step()
        else:
            self.anim_btn.text = "Pulse Wave Animation"

    def _run_wave_step(self) -> None:
        if not self._animating:
            return
        self._anim_phase += 0.08
        v1 = (math.sin(self._anim_phase) + 1.0) / 2.0
        v2 = (math.cos(self._anim_phase * 0.8) + 1.0) / 2.0
        v3 = (math.sin(self._anim_phase * 1.2 + 1.0) + 1.0) / 2.0

        self.prog1.value = v1
        self.prog2.value = v2
        self.prog3.value = v3

        self.slider1.value = v1 * 100.0
        self.s1_val_lbl.configure(text=f"{int(v1 * 100.0)}%")
        self.slider2.value = v2 * 100.0
        self.s2_val_lbl.configure(text=f"{int(v2 * 100.0)}%")

        self.after(30, self._run_wave_step)

    def _on_theme_toggle(self) -> None:
        is_dark = self.theme_switch.is_checked
        new_theme = "dark" if is_dark else "light"
        if new_theme == self._current_theme:
            return
        self._current_theme = new_theme
        set_theme(new_theme)
        pal = get_theme()

        self.configure(bg=pal.bg)
        self.theme_switch.text = "Dark Theme" if is_dark else "Light Theme"

        # Cascade background colors to frames and labels
        self._apply_theme_recursive(self, pal)

    def _apply_theme_recursive(self, widget: tk.Misc, pal: Palette) -> None:
        try:
            # Let custom widgets handle their own themes
            if isinstance(widget, GradientCard):
                widget.on_theme_update(pal)
                for child in widget.winfo_children():
                    self._apply_theme_inner(child, pal, widget.bg_color)
                return
            if isinstance(widget, BaseControl):
                widget.on_theme_update(pal)
                return

            if isinstance(widget, tk.Frame):
                widget.configure(bg=pal.bg)
            elif isinstance(widget, tk.Label):
                widget.configure(bg=pal.bg, fg=pal.fg)

            for child in widget.winfo_children():
                self._apply_theme_recursive(child, pal)
        except Exception:
            pass

    def _apply_theme_inner(self, widget: tk.Misc, pal: Palette, card_bg: str) -> None:
        try:
            if isinstance(widget, BaseControl):
                widget.set_parent_bg(card_bg)
                widget.on_theme_update(pal)
                widget.request_redraw()
                return
            if isinstance(widget, tk.Frame):
                widget.configure(bg=card_bg)
            elif isinstance(widget, tk.Label):
                if getattr(widget, "_preserve_fg", False):
                    widget.configure(bg=card_bg)
                else:
                    widget.configure(bg=card_bg, fg=pal.fg)

            for child in widget.winfo_children():
                self._apply_theme_inner(child, pal, card_bg)
        except Exception:
            pass


def main():
    app = GradientShowcaseApp()
    app.mainloop()


if __name__ == "__main__":
    main()
