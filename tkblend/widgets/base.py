"""
Base classes and display scaling infrastructure for tkblend vector widgets.
"""

from __future__ import annotations
import sys
import tkinter as tk
from math import floor, ceil
from typing import Optional, Union, List, Tuple, Any

from tkblend.surface import Surface
from tkblend.theme import (
    get_theme,
    Palette,
    add_theme_listener,
    remove_theme_listener,
    resolve_ancestor_bg,
    resolve_color_failsafe,
)


def _round_half_away(value: float) -> int:
    """Round halves away from zero without Banker's rounding bias."""
    if value >= 0:
        return floor(value + 0.5)
    return ceil(value - 0.5)


class ScalingTracker:
    """
    Manages process-level High-DPI awareness, Tk scaling factor tracking,
    and logical-to-physical pixel conversion for 4K / Retina displays.
    """

    _dpi_awareness_initialized: bool = False
    _user_widget_scaling: float = 1.0

    @classmethod
    def activate_high_dpi_awareness(cls) -> None:
        """Enable Per-Monitor High-DPI awareness where supported."""
        if cls._dpi_awareness_initialized:
            return

        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    import ctypes
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

        cls._dpi_awareness_initialized = True

    @classmethod
    def get_scaling_factor(cls, widget_or_window: Optional[tk.Misc] = None) -> float:
        """Calculate effective display scaling factor (1.0 = standard 96 DPI)."""
        if widget_or_window is None:
            return cls._user_widget_scaling

        try:
            ws = str(widget_or_window.tk.call("tk", "windowingsystem"))
            baseline = 1.0 if (ws == "aqua" and tk.TkVersion < 8.7) else (4.0 / 3.0)
            raw_scaling = float(widget_or_window.tk.call("tk", "scaling"))
            factor = raw_scaling / baseline
            quarter = round(factor * 4.0) / 4.0
            if abs(factor - quarter) <= 0.005:
                factor = quarter
            return max(0.5, factor * cls._user_widget_scaling)
        except Exception:
            return max(0.5, cls._user_widget_scaling)

    @classmethod
    def scale(cls, value: Union[int, float, List, Tuple], widget: Optional[tk.Misc] = None) -> Any:
        """Convert logical UI units to physical pixel values."""
        factor = cls.get_scaling_factor(widget)
        if factor == 1.0:
            if isinstance(value, (int, float)):
                return int(value)
            return value

        if isinstance(value, (int, float)):
            if value == 0:
                return 0
            return _round_half_away(float(value) * factor)
        elif isinstance(value, (tuple, list)):
            return [cls.scale(v, widget) for v in value]
        return value


# Auto-activate DPI awareness early
ScalingTracker.activate_high_dpi_awareness()


class Widget(tk.Label):
    """
    Base vector widget rendering on a Blend2D Surface with zero-copy blit
    to a backing Tkinter PhotoImage. Handles DPI scaling, resize, mouse states,
    and dynamic theme notifications.
    """

    @classmethod
    def _resolve_default_bg(cls, master: Optional[tk.Misc], palette: Palette) -> str:
        """Resolve background color from ancestor hierarchy (Card/Frame inner bg, Tk container bg, or palette.bg)."""
        return resolve_ancestor_bg(master, palette)

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 120,
        height: int = 40,
        bg: Optional[str] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._logical_w = max(1, width)
        self._logical_h = max(1, height)
        self._scale = ScalingTracker.get_scaling_factor(master)

        self._widget_w = max(1, int(self._logical_w * self._scale))
        self._widget_h = max(1, int(self._logical_h * self._scale))
        eff_bg = parent_bg if parent_bg is not None else bg
        self._explicit_bg = eff_bg
        self._parent_bg = eff_bg if eff_bg is not None else self._resolve_default_bg(master, get_theme())

        self._photo = tk.PhotoImage(master=master, width=self._widget_w, height=self._widget_h)
        self._surface = Surface(self._widget_w, self._widget_h)

        self._is_hovered = False
        self._is_pressed = False
        self._is_disabled = False
        self._has_focus = False

        self.resizable_width: bool = kwargs.pop("resizable_width", True)
        self.resizable_height: bool = kwargs.pop("resizable_height", True)

        # Typography configuration caching
        font_spec = kwargs.pop("font", None)
        font_size = kwargs.pop("font_size", None)
        font_family = kwargs.pop("font_family", None)
        bold = kwargs.pop("bold", None)
        italic = kwargs.pop("italic", None)
        weight = kwargs.pop("weight", None)

        self._custom_font_override: bool = any(
            x is not None for x in (font_spec, font_size, font_family, bold, italic, weight)
        )

        from tkblend.font import parse_font
        self._font_config = parse_font(
            font=font_spec,
            font_size=font_size,
            font_family=font_family,
            bold=bold,
            italic=italic,
            weight=weight,
            default_family="default",
            default_size=12.0,
        )

        super().__init__(
            master,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            background=self._parent_bg,
            **kwargs,
        )

        self.bind("<Configure>", self._on_configure)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Destroy>", self._on_destroy)

        # Register for theme notifications
        add_theme_listener(self._on_theme_changed)

        self.after_idle(self.render)

    @property
    def surface(self) -> Surface:
        return self._surface

    @property
    def photo(self) -> tk.PhotoImage:
        return self._photo

    @property
    def font(self) -> Any:
        return self._font_config

    @font.setter
    def font(self, val: Any) -> None:
        from tkblend.font import parse_font
        self._custom_font_override = True
        self._font_config = parse_font(
            font=val,
            default_family=self._font_config.family,
            default_size=self._font_config.size,
        )
        self.render()

    @property
    def font_size(self) -> float:
        return self._font_config.size

    @font_size.setter
    def font_size(self, size: float) -> None:
        self._custom_font_override = True
        self._font_config = self._font_config.copy_with(size=size)
        self.render()

    @property
    def font_family(self) -> str:
        return self._font_config.family

    @font_family.setter
    def font_family(self, family: str) -> None:
        self._custom_font_override = True
        self._font_config = self._font_config.copy_with(family=family)
        self.render()

    @property
    def font_config(self) -> Any:
        return self._font_config

    @font_config.setter
    def font_config(self, fc: Any) -> None:
        self.font = fc

    def _on_destroy(self, event) -> None:
        remove_theme_listener(self._on_theme_changed)

    def set_parent_bg(self, bg: str, force: bool = False) -> None:
        """Explicitly update the parent background and re-render."""
        resolved = resolve_color_failsafe(bg, master=self, fallback=self._parent_bg)
        self._parent_bg = resolved
        if force:
            self._explicit_bg = None
        try:
            self.configure(background=self._parent_bg)
        except Exception:
            pass
        self.render()

    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        if self._explicit_bg is None:
            self._parent_bg = self._resolve_default_bg(getattr(self, "master", None), palette)
            try:
                self.configure(background=self._parent_bg)
            except Exception:
                pass
        self.render()

    def _on_configure(self, event) -> None:
        # Ignore unmapped / transient <= 1px geometry events during container layout recalculations
        if event.width <= 1 or event.height <= 1:
            return

        new_w = max(1, event.width) if self.resizable_width else self._widget_w
        new_h = (
            max(1, event.height)
            if self.resizable_height
            else max(1, int(self._logical_h * self._scale))
        )
        if new_w != self._widget_w or new_h != self._widget_h:
            self._widget_w = new_w
            self._widget_h = new_h
            self._photo.configure(width=self._widget_w, height=self._widget_h)
            self._surface.resize(self._widget_w, self._widget_h)
            self.render()

    def _on_enter(self, event) -> None:
        if not self._is_disabled:
            self._is_hovered = True
            self._handle_enter(event)
            self.render()

    def _on_leave(self, event) -> None:
        if not self._is_disabled:
            self._is_hovered = False
            self._is_pressed = False
            self._handle_leave(event)
            self.render()

    def _on_press(self, event) -> None:
        if not self._is_disabled:
            self._is_pressed = True
            self._handle_press(event)
            self.render()

    def _on_release(self, event) -> None:
        if not self._is_disabled:
            self._is_pressed = False
            in_bounds = (0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h)
            if in_bounds:
                self._handle_click(event)
            self._handle_release(event)
            self.render()

    def _on_focus_in(self, event) -> None:
        self._has_focus = True
        self.render()

    def _on_focus_out(self, event) -> None:
        self._has_focus = False
        self.render()

    def _handle_enter(self, event) -> None:
        pass

    def _handle_leave(self, event) -> None:
        pass

    def _handle_press(self, event) -> None:
        pass

    def _handle_release(self, event) -> None:
        pass

    def _handle_click(self, event) -> None:
        pass

    def render(self) -> None:
        """Override in subclasses to draw custom vector UI."""
        self._surface.clear(self._parent_bg)
        self._surface.blit(self._photo)


ModernWidget = Widget


def cascade_bg_to_children(container: Any, bg: str, preserve_overrides: bool = True) -> None:
    """Recursively propagate background color down through child widgets."""
    if not hasattr(container, "winfo_children"):
        return
    try:
        children = container.winfo_children()
    except Exception:
        return

    for child in children:
        try:
            if not child.winfo_exists():
                continue
        except Exception:
            continue

        # Skip the internal backing surface label of Card / Frame
        if getattr(container, "_bg_label", None) is child:
            continue

        # If it's a vector Widget or has set_parent_bg:
        if hasattr(child, "set_parent_bg"):
            if preserve_overrides and getattr(child, "_explicit_bg", None) is not None:
                continue
            try:
                child.set_parent_bg(bg)
            except Exception:
                pass
            continue

        # If child is a Frame/Card with its own _bg_color:
        if hasattr(child, "_bg_color"):
            if hasattr(child, "set_parent_bg"):
                try:
                    child.set_parent_bg(bg)
                except Exception:
                    pass
            continue

        # Standard container (e.g. tk.Frame, tk.Canvas): update its background and recurse
        if hasattr(child, "configure"):
            try:
                child.configure(background=bg)
            except Exception:
                pass
        cascade_bg_to_children(child, bg, preserve_overrides=preserve_overrides)

