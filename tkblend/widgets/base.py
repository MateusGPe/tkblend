"""
Base classes and animation utilities for tkblend modern UI widgets.
"""

from __future__ import annotations
import tkinter as tk
import math
import time
from typing import Optional, Callable, Union, Any

from tkblend.surface import Surface, ColorLike
from tkblend.widgets.theme import Theme, ThemeManager


def ease_out_cubic(t: float) -> float:
    return 1.0 - math.pow(1.0 - t, 3)


def ease_in_out_cubic(t: float) -> float:
    return 4.0 * t * t * t if t < 0.5 else 1.0 - math.pow(-2.0 * t + 2.0, 3) / 2.0


def linear(t: float) -> float:
    return t


def _resolve_parent_bg(widget: Optional[tk.Misc], explicit_parent_bg: Optional[str], theme: Theme) -> str:
    """
    Intelligently resolve the effective background color of a widget's parent or container.
    """
    if explicit_parent_bg is not None and explicit_parent_bg != "":
        return explicit_parent_bg

    if widget is None:
        return theme.bg_window

    cur = widget
    while cur is not None:
        try:
            # Check if parent container defines a custom background attribute
            if hasattr(cur, "_bg_color") and cur._bg_color:
                return str(cur._bg_color)
            if hasattr(cur, "_custom_bg_color") and cur._custom_bg_color:
                return str(cur._custom_bg_color)
            if hasattr(cur, "_card_bg") and cur._card_bg:
                return str(cur._card_bg)
            if hasattr(cur, "_parent_bg") and cur._parent_bg:
                return str(cur._parent_bg)

            # Query Tkinter widget bg/background config
            c = cur.cget("background") or cur.cget("bg")
            if c and c != "" and not str(c).startswith("System"):
                return str(c)
        except Exception:
            pass

        cur = getattr(cur, "master", None)

    return theme.bg_window


class ModernWidget(tk.Label):
    """
    Base class for interactive Blend2D vector-drawn Tkinter widgets.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 120,
        height: int = 40,
        bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        self._theme = theme or ThemeManager.get_theme()
        self._requested_w = max(1, width)
        self._requested_h = max(1, height)
        self._widget_w = self._requested_w
        self._widget_h = self._requested_h
        self._custom_parent_bg = bg
        self._parent_bg = _resolve_parent_bg(master, self._custom_parent_bg, self._theme)
        self._bg_window = self._parent_bg

        self._photo = tk.PhotoImage(master=master, width=self._widget_w, height=self._widget_h)
        self._surface = Surface(self._widget_w, self._widget_h)

        self._is_hovered = False
        self._is_pressed = False
        self._is_focused = False
        self._is_disabled = False
        self._anim_timer_id: Optional[str] = None

        super().__init__(
            master,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            background=self._bg_window,
            **kwargs,
        )

        ThemeManager.subscribe(self._on_theme_changed)

        self.bind("<Configure>", self._on_configure)
        self.bind("<Map>", self._on_map)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Destroy>", self._on_destroy_event)

        self.after_idle(self.render)

    def resize(self, width: int, height: int) -> None:
        """
        Explicitly update the widget's requested dimensions and resize the rendering surface.
        """
        self._requested_w = max(1, width)
        self._requested_h = max(1, height)
        self._widget_w = self._requested_w
        self._widget_h = self._requested_h
        self._photo.configure(width=self._widget_w, height=self._widget_h)
        self._surface.resize(self._widget_w, self._widget_h)
        self.render()

    @property
    def theme(self) -> Theme:
        return self._theme

    @theme.setter
    def theme(self, val: Theme) -> None:
        self._theme = val
        self._parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, self._theme)
        self._bg_window = self._parent_bg
        try:
            self.configure(background=self._bg_window)
        except Exception:
            pass
        self.render()

    def resolve_parent_bg(self) -> str:
        """Dynamically re-evaluate parent background color."""
        self._parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, self._theme)
        self._bg_window = self._parent_bg
        try:
            self.configure(background=self._bg_window)
        except Exception:
            pass
        return self._parent_bg

    @property
    def surface(self) -> Surface:
        return self._surface

    @property
    def photo(self) -> tk.PhotoImage:
        return self._photo

    @property
    def is_disabled(self) -> bool:
        return self._is_disabled

    @is_disabled.setter
    def is_disabled(self, val: bool) -> None:
        self._is_disabled = bool(val)
        self.render()

    def _on_map(self, event) -> None:
        new_parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, self._theme)
        if new_parent_bg != self._parent_bg:
            self._parent_bg = new_parent_bg
            self._bg_window = new_parent_bg
            try:
                self.configure(background=self._bg_window)
            except Exception:
                pass
            self.render()

    def _on_theme_changed(self, new_theme: Theme) -> None:
        if self.winfo_exists():
            self._theme = new_theme
            self._parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, new_theme)
            self._bg_window = self._parent_bg
            try:
                self.configure(background=self._bg_window)
            except Exception:
                pass
            self.render()

    def _on_configure(self, event) -> None:
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        if new_w != self._widget_w or new_h != self._widget_h:
            self._widget_w = new_w
            self._widget_h = new_h
            # Preserve requested dimensions on the PhotoImage so transient packing constraints
            # do not collapse the widget's intrinsic requested size in Tkinter.
            photo_w = max(self._requested_w, new_w)
            photo_h = max(self._requested_h, new_h)
            if self._photo.width() != photo_w or self._photo.height() != photo_h:
                self._photo.configure(width=photo_w, height=photo_h)
            self._surface.resize(self._widget_w, self._widget_h)
            self.render()

    def _on_enter(self, event) -> None:
        if not self._is_disabled:
            self._is_hovered = True
            self.render()

    def _on_leave(self, event) -> None:
        if not self._is_disabled:
            self._is_hovered = False
            self._is_pressed = False
            self.render()

    def _on_press(self, event) -> None:
        if not self._is_disabled:
            self._is_pressed = True
            self.render()

    def _on_release(self, event) -> None:
        if not self._is_disabled:
            self._is_pressed = False
            self.render()

    def _on_destroy_event(self, event) -> None:
        ThemeManager.unsubscribe(self._on_theme_changed)
        if self._anim_timer_id:
            try:
                self.after_cancel(self._anim_timer_id)
            except Exception:
                pass
            self._anim_timer_id = None

    def animate_property(
        self,
        start_val: float,
        end_val: float,
        duration_ms: int = 200,
        on_update: Optional[Callable[[float], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
        easing: str = "ease_out",
    ) -> None:
        """
        Smoothly interpolate a float property over duration_ms using request-animation-frame style timer.
        """
        if not ThemeManager.animations_enabled or duration_ms <= 0:
            if on_update:
                on_update(end_val)
            if on_complete:
                on_complete()
            self.render()
            return

        if self._anim_timer_id:
            try:
                self.after_cancel(self._anim_timer_id)
            except Exception:
                pass
            self._anim_timer_id = None

        ease_fn = ease_out_cubic if easing == "ease_out" else ease_in_out_cubic if easing == "ease_in_out" else linear
        start_time = time.perf_counter()

        def _step():
            if not self.winfo_exists():
                return
            elapsed = (time.perf_counter() - start_time) * 1000.0
            t = min(1.0, elapsed / duration_ms)
            cur = start_val + (end_val - start_val) * ease_fn(t)

            if on_update:
                on_update(cur)
            self.render()

            if t < 1.0:
                self._anim_timer_id = self.after(16, _step)
            else:
                self._anim_timer_id = None
                if on_complete:
                    on_complete()

        _step()

    def render(self) -> None:
        """Override in subclasses to draw vector UI."""
        self._surface.clear(self._parent_bg)
        self._surface.blit(self._photo)
