"""
Pure Blend2D Vector Button powered by NativeController.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Callable, Any, Union

from tkblend.widgets.base import BaseControl
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    resolve_color_failsafe,
    blend_color_hex,
)
from tkblend.font import FontConfig, parse_font
from tkblend.icons import Icons


class Button(BaseControl):
    """
    Modern vector button with smooth elevation shadow, rounded corners,
    vector icons, focus ring, and state transition animations.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        text: str = "Button",
        command: Optional[Callable[[], None]] = None,
        icon: Optional[str] = None,
        icon_family: str = "fa-solid",
        icon_size: Optional[float] = None,
        width: int = 120,
        height: int = 36,
        corner_radius: float = 8.0,
        bg_color: Optional[ColorLike] = None,
        hover_color: Optional[ColorLike] = None,
        pressed_color: Optional[ColorLike] = None,
        disabled_color: Optional[ColorLike] = None,
        fg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 0.0,
        font: Optional[Any] = None,
        font_size: Optional[float] = None,
        bold: Optional[bool] = True,
        italic: Optional[bool] = False,
        shadow: bool = True,
        shadow_blur: float = 6.0,
        shadow_offset_y: float = 2.0,
        shadow_color: Optional[ColorLike] = None,
        focus_ring: bool = True,
        focus_ring_color: Optional[ColorLike] = None,
        focus_ring_width: float = 2.0,
        animated: bool = True,
        cursor: str = "hand2",
        state: str = "normal",
        **kwargs,
    ):
        self._text = str(text)
        self._command = command
        self._icon = icon
        self._icon_family = icon_family
        self._icon_size = icon_size
        self._corner_radius = float(corner_radius)

        self._custom_bg_color = bg_color
        self._custom_hover_color = hover_color
        self._custom_pressed_color = pressed_color
        self._custom_disabled_color = disabled_color
        self._custom_fg_color = fg_color
        self._custom_border_color = border_color
        self._border_width = float(border_width)

        self._font_spec = font
        self._font_size = font_size
        self._bold = bold
        self._italic = italic

        self._shadow = shadow
        self._shadow_blur = float(shadow_blur)
        self._shadow_offset_y = float(shadow_offset_y)
        self._custom_shadow_color = shadow_color

        self._focus_ring = focus_ring
        self._custom_focus_ring_color = focus_ring_color
        self._focus_ring_width = float(focus_ring_width)

        self._animated = animated
        self._hover_t = 0.0
        self._press_t = 0.0

        super().__init__(
            master=master,
            width=width,
            height=height,
            cursor=cursor,
            state=state,
            takefocus=True,
            **kwargs,
        )

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        self._text = str(val)
        self.request_redraw()

    @property
    def icon(self) -> Optional[str]:
        return self._icon

    @icon.setter
    def icon(self, val: Optional[str]) -> None:
        self._icon = val
        self.request_redraw()

    @property
    def command(self) -> Optional[Callable[[], None]]:
        return self._command

    @command.setter
    def command(self, cmd: Optional[Callable[[], None]]) -> None:
        self._command = cmd

    def invoke(self) -> None:
        """Programmatically invoke button command."""
        if not self.is_disabled and self._command is not None:
            self._command()

    def on_click(self, x: int, y: int, button: int) -> None:
        if button == 1:
            self.invoke()

    def on_key_press(self, event: tk.Event) -> None:
        if event.keysym in ("Return", "space"):
            self.animate_property("press", self._press_t, 1.0, duration_ms=40, on_update=self._set_press_t)
            self.invoke()

    def on_key_release(self, event: tk.Event) -> None:
        if event.keysym in ("Return", "space"):
            self.animate_property("press", self._press_t, 0.0, duration_ms=80, on_update=self._set_press_t)

    def on_state_changed(self, new_state: int, old_state: int) -> None:
        if self._animated:
            target_hover = 1.0 if self.is_hovered else 0.0
            target_press = 1.0 if self.is_pressed else 0.0
            if not self.is_disabled:
                self.animate_property("hover", self._hover_t, target_hover, duration_ms=120, on_update=self._set_hover_t)
                self.animate_property("press", self._press_t, target_press, duration_ms=60, on_update=self._set_press_t)
        else:
            self._hover_t = 1.0 if self.is_hovered else 0.0
            self._press_t = 1.0 if self.is_pressed else 0.0
            self.request_redraw()

    def _set_hover_t(self, val: float) -> None:
        self._hover_t = val

    def _set_press_t(self, val: float) -> None:
        self._press_t = val

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        rx = self._corner_radius * s
        ry = rx

        # Resolve Colors
        base_bg = resolve_color_failsafe(self._custom_bg_color or pal.primary, palette=pal)
        hover_bg = resolve_color_failsafe(self._custom_hover_color or pal.primary_hover, palette=pal)
        press_bg = resolve_color_failsafe(self._custom_pressed_color or pal.primary_active, palette=pal)
        disabled_bg = resolve_color_failsafe(self._custom_disabled_color or pal.surface, palette=pal)
        fg_col = resolve_color_failsafe(self._custom_fg_color or pal.primary_fg, palette=pal)

        if self.is_disabled:
            curr_bg = disabled_bg
            fg_col = resolve_color_failsafe(pal.text_muted, palette=pal)
            press_offset = 0.0
            shadow_blur = 0.0
        else:
            curr_bg = base_bg
            if self._hover_t > 0.0:
                curr_bg = blend_color_hex(curr_bg, hover_bg, self._hover_t) or curr_bg
            if self._press_t > 0.0:
                curr_bg = blend_color_hex(curr_bg, press_bg, self._press_t) or curr_bg

            press_offset = (1.5 * s) * self._press_t
            shadow_blur = self._shadow_blur * s * (1.0 - 0.5 * self._press_t) if self._shadow else 0.0

        # Draw drop shadow
        if self._shadow and shadow_blur > 0.0 and not self.is_disabled:
            sh_col = resolve_color_failsafe(self._custom_shadow_color or pal.shadow_color, palette=pal)
            sh_y = self._shadow_offset_y * s * (1.0 - 0.4 * self._press_t)
            surf.draw_shadow(
                0.0,
                sh_y + press_offset,
                w,
                h - press_offset,
                rx,
                ry,
                blur_radius=shadow_blur,
                shadow_color=sh_col,
            )

        # Draw rounded button background
        btn_y = press_offset
        btn_h = h - press_offset
        surf.fill_rounded_rect(0.0, btn_y, w, btn_h, rx, ry, curr_bg)

        # Draw border
        bw = self._border_width * s
        if bw > 0.0:
            bc = resolve_color_failsafe(self._custom_border_color or pal.card_border, palette=pal)
            surf.stroke_rounded_rect(0.0, btn_y, w, btn_h, rx, ry, bc, stroke_width=bw)

        # Draw focus ring
        if self._focus_ring and self.is_focused and not self.is_disabled:
            fr_col = resolve_color_failsafe(self._custom_focus_ring_color or pal.input_focus, palette=pal)
            frw = self._focus_ring_width * s
            surf.stroke_rounded_rect(
                -1.5 * s,
                btn_y - 1.5 * s,
                w + 3.0 * s,
                btn_h + 3.0 * s,
                rx + 1.5 * s,
                ry + 1.5 * s,
                fr_col,
                stroke_width=frw,
            )

        # Typography and Icon Layout
        font_cfg = parse_font(
            font=self._font_spec,
            font_size=self._font_size or 13.0,
            bold=self._bold,
            italic=self._italic,
        )
        scaled_font_size = float(font_cfg.size) * s

        has_text = bool(self._text)
        has_icon = bool(self._icon)

        center_y = btn_y + btn_h / 2.0

        if has_icon and has_text:
            icon_sz = (self._icon_size or (font_cfg.size * 1.1)) * s
            spacing = 8.0 * s
            text_metrics = surf.measure_text(
                self._text,
                font_size=scaled_font_size,
                font_family=font_cfg.family,
                bold=font_cfg.bold,
                italic=font_cfg.italic,
                weight=font_cfg.weight,
            )
            total_content_w = icon_sz + spacing + text_metrics.width
            start_x = (w - total_content_w) / 2.0

            # Draw Icon
            surf.draw_icon(
                self._icon,
                start_x,
                center_y - icon_sz / 2.0,
                size=icon_sz,
                color=fg_col,
                family=self._icon_family,
                align="left",
            )

            # Draw Text
            text_x = start_x + icon_sz + spacing
            text_y = center_y + scaled_font_size * 0.35
            surf.draw_text(
                self._text,
                text_x,
                text_y,
                font_size=scaled_font_size,
                font_family=font_cfg.family,
                color=fg_col,
                bold=font_cfg.bold,
                italic=font_cfg.italic,
                weight=font_cfg.weight,
                align="left",
            )
        elif has_icon:
            icon_sz = (self._icon_size or (min(w, h) * 0.45))
            surf.draw_icon(
                self._icon,
                w / 2.0,
                center_y - icon_sz / 2.0,
                size=icon_sz,
                color=fg_col,
                family=self._icon_family,
                align="center",
            )
        elif has_text:
            text_y = center_y + scaled_font_size * 0.35
            surf.draw_text(
                self._text,
                w / 2.0,
                text_y,
                font_size=scaled_font_size,
                font_family=font_cfg.family,
                color=fg_col,
                bold=font_cfg.bold,
                italic=font_cfg.italic,
                weight=font_cfg.weight,
                align="center",
            )

    def configure(self, cnf=None, **kwargs):
        if cnf is None and not kwargs:
            return super().configure()
        if cnf:
            kwargs.update(cnf)

        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "icon" in kwargs:
            self._icon = kwargs.pop("icon")
        if "icon_size" in kwargs:
            self._icon_size = kwargs.pop("icon_size")
        if "corner_radius" in kwargs:
            self._corner_radius = float(kwargs.pop("corner_radius"))
        if "bg_color" in kwargs or "fg_color" in kwargs or "hover_color" in kwargs:
            if "bg_color" in kwargs:
                self._custom_bg_color = kwargs.pop("bg_color")
            if "hover_color" in kwargs:
                self._custom_hover_color = kwargs.pop("hover_color")
            if "fg_color" in kwargs:
                self._custom_fg_color = kwargs.pop("fg_color")
        self.request_redraw()
        return super().configure(**kwargs)
