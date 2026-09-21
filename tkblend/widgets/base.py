"""
Base classes, DPI scaling integration, and animation utilities for tkblend modern UI widgets.
Harvested and adapted from CustomTkinter CTkBaseClass and ttkbootstrap style engine.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import math
import time
from typing import Optional, Callable, Union, Any, Dict, Set

from tkblend.surface import Surface, ColorLike
from tkblend.widgets.theme import Theme, ThemeManager
from tkblend.widgets.scaling import ScalingTracker


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
            if hasattr(cur, "_bg_color") and cur._bg_color:
                return str(cur._bg_color)
            if hasattr(cur, "_custom_bg_color") and cur._custom_bg_color:
                return str(cur._custom_bg_color)
            if hasattr(cur, "_card_bg") and cur._card_bg:
                return str(cur._card_bg)
            if hasattr(cur, "_parent_bg") and cur._parent_bg:
                return str(cur._parent_bg)

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
    Provides full .configure() / .cget() / dict subscripting parity with CustomTkinter & Tkinter,
    Per-Monitor DPI scaling, reactive parent background tracking, and vector blitting.
    """

    # Custom attributes supported by tkblend widgets
    _valid_base_attributes: Set[str] = {
        "width", "height", "bg", "bg_color", "theme", "state", "cursor"
    }

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 120,
        height: int = 40,
        bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        ScalingTracker.activate_high_dpi_awareness()
        self._theme = theme or ThemeManager.get_theme()
        self._scale_factor = ScalingTracker.get_scaling_factor(master)
        
        self._requested_w = max(1, width)
        self._requested_h = max(1, height)
        self._widget_w = max(1, ScalingTracker.scale(width, master))
        self._widget_h = max(1, ScalingTracker.scale(height, master))
        self._custom_parent_bg = bg
        self._parent_bg = _resolve_parent_bg(master, self._custom_parent_bg, self._theme)
        self._bg_window = self._parent_bg

        # Zero-allocation direct PhotoImage + Blend2D Surface
        self._photo = tk.PhotoImage(master=master, width=self._widget_w, height=self._widget_h)
        self._surface = Surface(self._widget_w, self._widget_h)

        self._is_hovered = False
        self._is_pressed = False
        self._is_focused = False
        self._is_disabled = False
        self._anim_timer_id: Optional[str] = None
        self._state = "normal"

        # Separate native Tkinter Label options from custom options
        tk_kwargs = {}
        for k in ("cursor", "takefocus"):
            if k in kwargs:
                tk_kwargs[k] = kwargs.pop(k)

        super().__init__(
            master,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            background=self._bg_window,
            **tk_kwargs,
        )

        # Hook master's configure to dynamically react when container background changes (CTk pattern)
        if self.master is not None and isinstance(self.master, (tk.Tk, tk.Toplevel, tk.Frame, tk.LabelFrame, ttk.Frame, ttk.LabelFrame)):
            if not hasattr(self.master, "_tkblend_hooked"):
                orig_config = self.master.configure

                def _master_config_wrapper(*args, **mkwargs):
                    res = orig_config(*args, **mkwargs)
                    if "bg" in mkwargs or "background" in mkwargs:
                        for child in self.master.winfo_children():
                            if hasattr(child, "resolve_parent_bg"):
                                child.resolve_parent_bg()
                    return res

                self.master.configure = _master_config_wrapper
                self.master.config = _master_config_wrapper
                self.master._tkblend_hooked = True

        ThemeManager.subscribe(self._on_theme_changed)

        self.bind("<Configure>", self._on_configure)
        self.bind("<Map>", self._on_map)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Destroy>", self._on_destroy_event)

        # Process any remaining kwargs through configure()
        if kwargs:
            self.configure(**kwargs)

        self.after_idle(self.render)

    # ------------------------------------------------------------------------
    # Protocol: configure(), cget(), __getitem__, __setitem__
    # ------------------------------------------------------------------------

    def configure(self, **kwargs) -> Any:
        """
        Configure widget options (e.g., text, bg_color, corner_radius, state, command).
        Automatically triggers redraw if visual attributes change.
        """
        if not kwargs:
            # Return full configuration dict for standard Tk compatibility
            return {
                "width": self._requested_w,
                "height": self._requested_h,
                "bg_color": self._custom_parent_bg,
                "state": self._state,
            }

        require_render = False

        if "width" in kwargs:
            w = kwargs.pop("width")
            self._requested_w = max(1, int(w))
            self._widget_w = max(1, ScalingTracker.scale(self._requested_w, self.master))
            require_render = True

        if "height" in kwargs:
            h = kwargs.pop("height")
            self._requested_h = max(1, int(h))
            self._widget_h = max(1, ScalingTracker.scale(self._requested_h, self.master))
            require_render = True

        if "bg" in kwargs or "bg_color" in kwargs:
            self._custom_parent_bg = kwargs.pop("bg", None) or kwargs.pop("bg_color", None)
            self.resolve_parent_bg()
            require_render = True

        if "theme" in kwargs:
            self._theme = kwargs.pop("theme")
            self.resolve_parent_bg()
            require_render = True

        if "state" in kwargs:
            st = kwargs.pop("state")
            self._state = str(st).lower()
            self._is_disabled = (self._state == "disabled")
            require_render = True

        # Delegate remaining subclass-specific options
        subclass_handled = self._configure_subclass(kwargs)
        if subclass_handled:
            require_render = True

        # Forward standard Tk attributes
        tk_keys = {k: v for k, v in kwargs.items() if k in ("cursor", "takefocus")}
        if tk_keys:
            super().configure(**tk_keys)

        if require_render and self.winfo_exists():
            if self._surface.width != self._widget_w or self._surface.height != self._widget_h:
                self._photo.configure(width=self._widget_w, height=self._widget_h)
                self._surface.resize(self._widget_w, self._widget_h)
            self.render()

    def config(self, **kwargs) -> Any:
        """Alias for configure()."""
        return self.configure(**kwargs)

    def cget(self, key: str) -> Any:
        """Query widget configuration attribute."""
        if key == "width":
            return self._requested_w
        elif key == "height":
            return self._requested_h
        elif key in ("bg", "bg_color"):
            return self._custom_parent_bg
        elif key == "theme":
            return self._theme
        elif key == "state":
            return self._state
        elif key in ("cursor", "takefocus"):
            return super().cget(key)
        
        # Check subclass cget
        val = self._cget_subclass(key)
        if val is not None:
            return val
        raise KeyError(f"Unknown attribute '{key}' for {self.__class__.__name__}")

    def __getitem__(self, key: str) -> Any:
        return self.cget(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.configure(**{key: value})

    def _configure_subclass(self, kwargs: Dict[str, Any]) -> bool:
        """Override in subclasses to handle specific attributes. Return True if redraw required."""
        return False

    def _cget_subclass(self, key: str) -> Optional[Any]:
        """Override in subclasses to return specific attribute values."""
        return None

    # ------------------------------------------------------------------------
    # Sizing & Layout
    # ------------------------------------------------------------------------

    def resize(self, width: int, height: int) -> None:
        """Explicitly update the widget's requested dimensions and resize the rendering surface."""
        self._requested_w = max(1, width)
        self._requested_h = max(1, height)
        self._widget_w = max(1, ScalingTracker.scale(self._requested_w, self.master))
        self._widget_h = max(1, ScalingTracker.scale(self._requested_h, self.master))
        self._photo.configure(width=self._widget_w, height=self._widget_h)
        self._surface.resize(self._widget_w, self._widget_h)
        self.render()

    @property
    def theme(self) -> Theme:
        return self._theme

    @theme.setter
    def theme(self, val: Theme) -> None:
        self.configure(theme=val)

    def resolve_parent_bg(self) -> str:
        """Dynamically re-evaluate parent background color."""
        self._parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, self._theme)
        self._bg_window = self._parent_bg
        try:
            super().configure(background=self._bg_window)
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
        self.configure(state="disabled" if val else "normal")

    # ------------------------------------------------------------------------
    # Events & Lifecycle
    # ------------------------------------------------------------------------

    def _on_map(self, event) -> None:
        new_parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, self._theme)
        if new_parent_bg != self._parent_bg:
            self._parent_bg = new_parent_bg
            self._bg_window = new_parent_bg
            try:
                super().configure(background=self._bg_window)
            except Exception:
                pass
            self.render()

    def _on_theme_changed(self, new_theme: Theme) -> None:
        if self.winfo_exists():
            self._theme = new_theme
            self._parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, new_theme)
            self._bg_window = self._parent_bg
            try:
                super().configure(background=self._bg_window)
            except Exception:
                pass
            self.render()

    def _on_configure(self, event) -> None:
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        if new_w != self._widget_w or new_h != self._widget_h:
            self._widget_w = new_w
            self._widget_h = new_h
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
        """Smoothly interpolate a float property over duration_ms using 60fps frame timer."""
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
        """Override in subclasses to draw vector UI with Blend2D."""
        self._surface.clear(self._parent_bg)
        self._surface.blit(self._photo)
