"""
Base classes and display scaling infrastructure for tkblend vector widgets.
"""

from __future__ import annotations
from collections.abc import Callable
import logging
import sys
import tkinter as tk
from math import floor, ceil
from typing import Optional, Union, List, Tuple, Any

logger = logging.getLogger(__name__)

from tkblend.surface import (
    Surface,
    ColorLike,
    SurfaceHandle,
    PseudoState,
    StyleEngine,
    ComputedStyle,
)
from tkblend.theme import (
    get_theme,
    Palette,
    add_theme_listener,
    remove_theme_listener,
    resolve_ancestor_bg,
    resolve_color_failsafe,
)
from tkblend.utils.window_shape import (
    apply_round_rect_shape,
    clear_window_shape,
    is_window_shaping_supported,
)


def _round_half_away(value: float) -> int:
    """Round halves away from zero without Banker's rounding bias."""
    if value >= 0:
        return floor(value + 0.5)
    return ceil(value - 0.5)


def _resolve_color(color: Optional[ColorLike], fallback: str, pal: Optional[Palette] = None) -> ColorLike:
    """Helper to resolve an optional color or palette fallback."""
    if color is None:
        return fallback
    if isinstance(color, str):
        return resolve_color_failsafe(color, fallback=fallback, palette=pal or get_theme())
    return color


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
            except Exception as e1:
                logger.debug("SetProcessDpiAwareness failed: %s; falling back to SetProcessDPIAware", e1)
                try:
                    import ctypes
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception as e2:
                    logger.debug("SetProcessDPIAware failed: %s", e2)

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
        except Exception as e:
            logger.debug("Failed querying Tk scaling factor on %r: %s", widget_or_window, e)
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
    Base vector widget rendering on a Blend2D SurfaceHandle with zero-copy blit
    to a backing Tkinter PhotoImage. Handles DPI scaling, resize, CSS-like pseudo states,
    and declarative style resolution.
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
        tag_name: str = "widget",
        class_name: str = "",
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
        self._handle = SurfaceHandle(self._widget_w, self._widget_h)
        self._surface = Surface(self._handle)

        self._state: int = int(PseudoState.Normal)
        self._tag_name: str = tag_name
        self._class_name: str = class_name

        if not hasattr(self, "_explicit_fg"):
            self._explicit_fg = None
        if not hasattr(self, "_explicit_border_color"):
            self._explicit_border_color = None
        if not hasattr(self, "_custom_rx"):
            self._custom_rx = None
        if not hasattr(self, "_custom_ry"):
            self._custom_ry = None
        if not hasattr(self, "_variant"):
            self._variant = ""
        if not hasattr(self, "_text"):
            self._text = kwargs.pop("text", "")
        if not hasattr(self, "_command"):
            self._command = kwargs.pop("command", None)
        if not hasattr(self, "_elevation"):
            self._elevation = 0.0

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

        self._theme_dirty = False

        # Register for theme notifications
        add_theme_listener(self._on_theme_changed)

        self.after_idle(lambda: self.render() if self.winfo_exists() else None)

    @property
    def surface_id(self) -> int:
        """64-bit handle ID of the native surface in SurfaceRegistry."""
        return self._handle.surface_id if self._handle is not None else 0

    @property
    def handle(self) -> SurfaceHandle:
        return self._handle

    @property
    def surface(self) -> Surface:
        return self._surface

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, val: int) -> None:
        self._state = int(val)
        self.render()

    @property
    def tag_name(self) -> str:
        return self._tag_name

    @tag_name.setter
    def tag_name(self, val: str) -> None:
        self._tag_name = str(val)
        self.render()

    @property
    def class_name(self) -> str:
        return self._class_name

    @class_name.setter
    def class_name(self, val: str) -> None:
        self._class_name = str(val)
        self.render()

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        self._text = str(val)
        self.render()

    def set_text(self, text: str) -> None:
        self.text = text

    @property
    def command(self) -> Optional[Callable]:
        return self._command

    @command.setter
    def command(self, cmd: Optional[Callable]) -> None:
        self._command = cmd

    @property
    def variant(self) -> str:
        return self._variant

    @variant.setter
    def variant(self, val: str) -> None:
        self._variant = str(val)
        self._class_name = f".{self._tag_name}-{self._variant}" if self._variant else ""
        self.render()

    def set_variant(self, variant: str) -> None:
        self.variant = variant

    @property
    def bootstyle(self) -> str:
        return self.variant

    @bootstyle.setter
    def bootstyle(self, val: str) -> None:
        self.variant = val

    def set_bootstyle(self, style: str) -> None:
        self.variant = style

    @property
    def corner_radius(self) -> float:
        return float(self._custom_rx / self._scale) if self._custom_rx is not None else 8.0

    @corner_radius.setter
    def corner_radius(self, radius: float) -> None:
        s = self._scale
        self._custom_rx = float(radius) * s
        self._custom_ry = float(radius) * s
        self.render()

    def set_corner_radius(self, radius: float) -> None:
        self.corner_radius = radius

    @property
    def bg_color(self) -> Optional[ColorLike]:
        return self._explicit_bg

    @bg_color.setter
    def bg_color(self, color: Optional[ColorLike]) -> None:
        self._explicit_bg = color
        self.render()

    def set_bg_color(self, color: ColorLike) -> None:
        self.bg_color = color

    @property
    def fg_color(self) -> Optional[ColorLike]:
        return self._explicit_fg

    @fg_color.setter
    def fg_color(self, color: Optional[ColorLike]) -> None:
        self._explicit_fg = color
        self.render()

    def set_fg_color(self, color: ColorLike) -> None:
        self.fg_color = color

    @property
    def border_color(self) -> Optional[ColorLike]:
        return self._explicit_border_color

    @border_color.setter
    def border_color(self, color: Optional[ColorLike]) -> None:
        self._explicit_border_color = color
        self.render()

    def set_border_color(self, color: ColorLike) -> None:
        self.border_color = color

    @property
    def text_color(self) -> Optional[ColorLike]:
        return self.fg_color

    @text_color.setter
    def text_color(self, color: Optional[ColorLike]) -> None:
        self.fg_color = color

    def set_text_color(self, color: ColorLike) -> None:
        self.text_color = color

    def set_state(self, state: str) -> None:
        self._is_disabled = (str(state).lower() == "disabled")
        self.render()

    def get_computed_style(
        self,
        tag_name: Optional[str] = None,
        class_name: Optional[str] = None,
        state: Optional[int] = None,
    ) -> ComputedStyle:
        """Resolve declarative CSS style for widget, scaling geometric values for display DPI and applying instance overrides."""
        tag = tag_name if tag_name is not None else self._tag_name
        cls_sel = class_name if class_name is not None else self._class_name
        if not cls_sel and self._variant:
            cls_sel = f".{tag}-{self._variant}" if not self._variant.startswith(".") else self._variant
        st = self._state if state is None else state
        style = StyleEngine.resolve(tag, cls_sel, st)
        s = self._scale

        if self._custom_font_override:
            style.font_size = float(self._font_config.size * s)
            style.font_family = self._font_config.family
            style.font_weight = self._font_config.weight
        else:
            style.font_size = float(style.font_size * s)

        if self._custom_rx is not None:
            style.border_radius = float(self._custom_rx)
        else:
            style.border_radius = float(style.border_radius * s)

        style.border_width = float(style.border_width * s)
        style.shadow_blur = float(style.shadow_blur * s)
        style.shadow_offset_x = float(style.shadow_offset_x * s)
        style.shadow_offset_y = float(style.shadow_offset_y * s)

        from tkblend.surface import parse_color
        if self._explicit_bg is not None:
            style.bg_color = parse_color(self._explicit_bg)
        if self._explicit_fg is not None:
            style.fg_color = parse_color(self._explicit_fg)
        if self._explicit_border_color is not None:
            style.border_color = parse_color(self._explicit_border_color)

        return style

    def begin_render(self, clear_color: Optional[ColorLike] = None) -> float:
        """Clear surface to solid parent background and return display scaling factor. Returns 0.0 if unmapped."""
        if getattr(self, "_surface", None) is None or getattr(self, "_handle", None) is None:
            raise RuntimeError("Surface is closed or None")
        if self._widget_w <= 1 or self._widget_h <= 1:
            return 0.0
        from tkblend.surface import parse_color
        bg = clear_color if clear_color is not None else self._parent_bg
        self._handle.clear(parse_color(bg))
        return self._scale

    def end_render(self) -> None:
        """Blit native surface directly to backing Tkinter PhotoImage."""
        if self.winfo_exists() and hasattr(self, "_photo") and self._photo is not None:
            self._handle.blit_to_photo(int(self.tk.interpaddr()), str(self._photo.name))

    def configure(self, **kwargs) -> Any:
        """Configure widget options dynamically with automatic re-render."""
        render_needed = False
        if "text" in kwargs:
            self._text = str(kwargs.pop("text"))
            render_needed = True
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "variant" in kwargs:
            self._variant = str(kwargs.pop("variant"))
            self._class_name = f".{self._tag_name}-{self._variant}" if self._variant else ""
            render_needed = True
        if "bootstyle" in kwargs:
            self._variant = str(kwargs.pop("bootstyle"))
            self._class_name = f".{self._tag_name}-{self._variant}" if self._variant else ""
            render_needed = True
        if "corner_radius" in kwargs:
            cr = kwargs.pop("corner_radius")
            s = self._scale
            self._custom_rx = float(cr) * s if cr is not None else None
            self._custom_ry = float(cr) * s if cr is not None else None
            render_needed = True
        if "bg_color" in kwargs:
            self._explicit_bg = kwargs.pop("bg_color")
            render_needed = True
        if "fg_color" in kwargs:
            self._explicit_fg = kwargs.pop("fg_color")
            render_needed = True
        if "text_color" in kwargs:
            self._explicit_fg = kwargs.pop("text_color")
            render_needed = True
        if "fg" in kwargs:
            self._explicit_fg = kwargs.pop("fg")
            render_needed = True
        if "foreground" in kwargs:
            self._explicit_fg = kwargs.pop("foreground")
            render_needed = True
        if "border_color" in kwargs:
            self._explicit_border_color = kwargs.pop("border_color")
            render_needed = True
        if "state" in kwargs:
            st = kwargs.pop("state")
            self._is_disabled = (str(st).lower() == "disabled")
            render_needed = True
        if "parent_bg" in kwargs:
            self.set_parent_bg(kwargs.pop("parent_bg"), render=False)
            render_needed = True
        if "font" in kwargs or "font_size" in kwargs or "font_family" in kwargs:
            from tkblend.font import parse_font
            self._custom_font_override = True
            self._font_config = parse_font(
                font=kwargs.pop("font", None),
                font_size=kwargs.pop("font_size", None),
                font_family=kwargs.pop("font_family", None),
                default_family=self._font_config.family,
                default_size=self._font_config.size,
            )
            self._on_font_changed()
            render_needed = True

        res = None
        if kwargs:
            res = super().configure(**kwargs)
        if render_needed:
            self.render()
        return res

    config = configure

    @property
    def _is_hovered(self) -> bool:
        return bool(self._state & int(PseudoState.Hover))

    @_is_hovered.setter
    def _is_hovered(self, val: bool) -> None:
        if val:
            self._state |= int(PseudoState.Hover)
        else:
            self._state &= ~int(PseudoState.Hover)

    @property
    def _is_pressed(self) -> bool:
        return bool(self._state & int(PseudoState.Active))

    @_is_pressed.setter
    def _is_pressed(self, val: bool) -> None:
        if val:
            self._state |= int(PseudoState.Active)
        else:
            self._state &= ~int(PseudoState.Active)

    @property
    def _is_disabled(self) -> bool:
        return bool(self._state & int(PseudoState.Disabled))

    @_is_disabled.setter
    def _is_disabled(self, val: bool) -> None:
        if val:
            self._state |= int(PseudoState.Disabled)
        else:
            self._state &= ~int(PseudoState.Disabled)

    @property
    def _has_focus(self) -> bool:
        return bool(self._state & int(PseudoState.Focused))

    @_has_focus.setter
    def _has_focus(self, val: bool) -> None:
        if val:
            self._state |= int(PseudoState.Focused)
        else:
            self._state &= ~int(PseudoState.Focused)

    @property
    def _is_checked(self) -> bool:
        return bool(self._state & int(PseudoState.Checked))

    @_is_checked.setter
    def _is_checked(self, val: bool) -> None:
        if val:
            self._state |= int(PseudoState.Checked)
        else:
            self._state &= ~int(PseudoState.Checked)

    @property
    def photo(self) -> tk.PhotoImage:
        return self._photo

    def get_effective_tk_font(self) -> Any:
        """Return the effective Tkinter font tuple/Font object scaled for current display DPI."""
        eff_fc = self._font_config.copy_with(size=self._font_config.size * self._scale)
        return eff_fc.to_tk_font()

    def _on_font_changed(self) -> None:
        """Hook called when font properties change."""
        pass

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
        self._on_font_changed()
        self.render()

    @property
    def font_size(self) -> float:
        return self._font_config.size

    @font_size.setter
    def font_size(self, size: float) -> None:
        self._custom_font_override = True
        self._font_config = self._font_config.copy_with(size=size)
        self._on_font_changed()
        self.render()

    @property
    def font_family(self) -> str:
        return self._font_config.family

    @font_family.setter
    def font_family(self, family: str) -> None:
        self._custom_font_override = True
        self._font_config = self._font_config.copy_with(family=family)
        self._on_font_changed()
        self.render()

    @property
    def font_config(self) -> Any:
        return self._font_config

    @font_config.setter
    def font_config(self, fc: Any) -> None:
        self.font = fc

    def _on_destroy(self, event=None) -> None:
        if event is not None:
            w = getattr(event, "widget", None)
            if w is not None and w != self and str(w) != str(self):
                return
        remove_theme_listener(self._on_theme_changed)
        if hasattr(self, "_var_sync") and self._var_sync is not None:
            try:
                self._var_sync.cleanup()
            except Exception:
                pass
        if hasattr(self, "_surface") and self._surface is not None:
            try:
                self._surface.close()
            except Exception:
                pass
            self._surface = None  # type: ignore
        if hasattr(self, "_handle") and self._handle is not None:
            try:
                self._handle.close()
            except Exception:
                pass
            self._handle = None  # type: ignore
        if hasattr(self, "_photo") and self._photo is not None:
            try:
                photo_name = str(self._photo.name)
                if self.winfo_exists():
                    self.configure(image="")
                if hasattr(self, "tk") and self.tk is not None:
                    self.tk.call("image", "delete", photo_name)
            except Exception:
                pass
            self._photo = None  # type: ignore

    def destroy(self) -> None:
        try:
            for child in list(getattr(self, "children", {}).values()):
                if hasattr(child, "destroy"):
                    try:
                        child.destroy()
                    except Exception:
                        pass
        except Exception:
            pass
        self._on_destroy()
        super().destroy()

    def __del__(self) -> None:
        try:
            self._on_destroy()
        except Exception:
            pass

    def set_parent_bg(self, bg: str, force: bool = False, render: bool = True) -> None:
        """Explicitly update the parent background and re-render."""
        resolved = resolve_color_failsafe(bg, master=self, fallback=self._parent_bg)
        self._parent_bg = resolved
        if force:
            self._explicit_bg = None
        try:
            self.configure(background=self._parent_bg)
        except Exception as e:
            logger.debug("Failed configuring Widget background to '%s': %s", self._parent_bg, e)
        if render:
            self.render()
        else:
            self._theme_dirty = True

    def _apply_theme_update(self, palette: Palette) -> None:
        """Execute scheduled theme render in non-blocking batch."""
        if not self.winfo_exists():
            return
        if not self._theme_dirty:
            return
        if self._explicit_bg is None:
            self._parent_bg = self._resolve_default_bg(getattr(self, "master", None), palette)
            try:
                self.configure(background=self._parent_bg)
            except Exception as e:
                logger.debug("Failed updating Widget background in _apply_theme_update on %r: %s", self, e)
        self._theme_dirty = False
        self.render()

    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        self._theme_dirty = True
        if self._explicit_bg is None:
            self._parent_bg = self._resolve_default_bg(getattr(self, "master", None), palette)
            try:
                self.configure(background=self._parent_bg)
            except Exception as e:
                logger.debug("Failed updating Widget background during theme change on %r: %s", self, e)
        from ..theme import ThemeManager
        ThemeManager().queue_render(self)

    def _on_configure(self, event) -> None:
        # Ignore unmapped / transient <= 1px geometry events during container layout recalculations
        if event.width <= 1 or event.height <= 1:
            return

        pref_w = max(1, int(self._logical_w * self._scale))
        pref_h = max(1, int(self._logical_h * self._scale))

        new_w = max(1, event.width) if self.resizable_width else pref_w
        new_h = (
            max(1, event.height)
            if self.resizable_height
            else pref_h
        )

        # Retain PhotoImage geometry requisition at >= preferred size so Tk
        # geometry managers (pack/grid) can recover full allocated space when parent containers expand.
        photo_w = max(pref_w, new_w)
        photo_h = max(pref_h, new_h)

        if (
            new_w != self._widget_w
            or new_h != self._widget_h
            or self._photo.cget("width") != photo_w
            or self._photo.cget("height") != photo_h
        ):
            self._widget_w = new_w
            self._widget_h = new_h
            self._photo.configure(width=photo_w, height=photo_h)
            if self._handle is not None:
                self._handle.resize(self._widget_w, self._widget_h)
            elif self._surface is not None:
                self._surface.resize(self._widget_w, self._widget_h)
            self.render()

    def _on_enter(self, event) -> None:
        if not self._is_disabled:
            self._state |= int(PseudoState.Hover)
            self._handle_enter(event)
            self.render()

    def _on_leave(self, event) -> None:
        if not self._is_disabled:
            self._state &= ~(int(PseudoState.Hover) | int(PseudoState.Active))
            self._handle_leave(event)
            self.render()

    def _on_press(self, event) -> None:
        if not self._is_disabled:
            self._state |= int(PseudoState.Active)
            self._handle_press(event)
            self.render()

    def _on_release(self, event) -> None:
        if not self._is_disabled:
            self._state &= ~int(PseudoState.Active)
            in_bounds = (0 <= event.x <= self._widget_w and 0 <= event.y <= self._widget_h)
            if in_bounds:
                self._handle_click(event)
            self._handle_release(event)
            self.render()

    def _on_focus_in(self, event) -> None:
        self._state |= int(PseudoState.Focused)
        self.render()

    def _on_focus_out(self, event) -> None:
        self._state &= ~int(PseudoState.Focused)
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
        if not self._is_disabled and self._command:
            self._command()

    def render(self) -> None:
        """Override in subclasses to draw custom vector UI."""
        s = self.begin_render()
        if s <= 0.0:
            return
        self.end_render()


class VariableSync:
    """
    Controller providing standard, robust synchronization with Tkinter variables
    (StringVar, IntVar, DoubleVar, BooleanVar) including tracing, type safety,
    re-entrancy suppression, and automatic cleanup.
    """

    def __init__(
        self,
        variable: Optional[Any] = None,
        initial_value: Any = None,
        on_change: Optional[Callable[[Any], None]] = None,
        type_caster: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        self._variable: Optional[Any] = None
        self._trace_id: Optional[str] = None
        self._on_change: Optional[Callable[[Any], None]] = on_change
        self._type_caster: Optional[Callable[[Any], Any]] = type_caster
        self._current_value: Any = initial_value
        self._suppress_trace: bool = False

        if variable is not None:
            self.set_variable(variable, initial_value=initial_value)
        else:
            self._current_value = initial_value

    @property
    def variable(self) -> Optional[Any]:
        return self._variable

    @variable.setter
    def variable(self, new_var: Optional[Any]) -> None:
        self.set_variable(new_var)

    @property
    def has_variable(self) -> bool:
        return self._variable is not None

    def get(self) -> Any:
        if self._variable is not None:
            try:
                raw = self._variable.get()
                self._current_value = self._type_caster(raw) if self._type_caster else raw
            except Exception as e:
                logger.debug("Failed reading variable value: %s", e)
        return self._current_value

    def set(self, val: Any) -> None:
        self._current_value = self._type_caster(val) if self._type_caster else val
        if self._variable is not None:
            self._suppress_trace = True
            try:
                self._variable.set(val)
            except Exception as e:
                logger.debug("Failed setting synced variable: %s", e)
            finally:
                self._suppress_trace = False

    def set_variable(self, variable: Optional[Any], initial_value: Any = None) -> Any:
        self.cleanup()
        self._variable = variable
        if initial_value is not None:
            self._current_value = initial_value

        if self._variable is not None:
            try:
                raw = self._variable.get()
                self._current_value = self._type_caster(raw) if self._type_caster else raw
            except Exception as e:
                logger.debug("Failed reading initial variable value: %s", e)
                if self._current_value is not None:
                    try:
                        self._variable.set(self._current_value)
                    except Exception:
                        pass
            try:
                self._trace_id = self._variable.trace_add("write", self._on_trace_write)
            except Exception as e:
                logger.debug("Failed adding trace to variable: %s", e)
        return self._current_value

    def _on_trace_write(self, *args) -> None:
        if self._suppress_trace:
            return
        if self._variable is not None and self._on_change is not None:
            try:
                raw = self._variable.get()
                val = self._type_caster(raw) if self._type_caster else raw
                self._current_value = val
                self._on_change(val)
            except Exception as e:
                logger.debug("Failed reading synced variable in trace: %s", e)

    def cleanup(self) -> None:
        if self._variable is not None and self._trace_id is not None:
            try:
                self._variable.trace_remove("write", self._trace_id)
            except Exception:
                pass
            self._trace_id = None


class ContainerBase(tk.Frame):
    """
    Base container widget for Blend2D vector surfaces (Frame, Card, etc.).
    Manages backing vector Surface, PhotoImage, inner body frame, OS-level window shaping,
    safe margin calculation, and automatic theme & background cascade.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 200,
        height: int = 150,
        rx: float = 16.0,
        ry: float = 16.0,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        elevation: float = 8.0,
        shadow_color: Optional[ColorLike] = None,
        shadow_offset_y: float = 4.0,
        padding: Optional[float] = None,
        parent_bg: Optional[str] = None,
        clip_children: bool = True,
        **kwargs,
    ):
        self._logical_w = max(1, width)
        self._logical_h = max(1, height)
        self._scale = ScalingTracker.get_scaling_factor(master)
        pal = get_theme()
        self._explicit_parent_bg = parent_bg
        self._parent_bg = parent_bg or Widget._resolve_default_bg(master, pal)
        super().__init__(
            master,
            width=max(1, int(self._logical_w * self._scale)),
            height=max(1, int(self._logical_h * self._scale)),
            background=self._parent_bg,
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._widget_w = max(1, int(self._logical_w * self._scale))
        self._widget_h = max(1, int(self._logical_h * self._scale))
        self._rx = rx * self._scale
        self._ry = ry * self._scale
        self._clip_children = clip_children
        self._explicit_bg_color = bg_color
        self._explicit_border_color = border_color
        self._explicit_shadow_color = shadow_color
        self._bg_color = bg_color or pal.card_bg
        self._border_color = border_color or pal.card_border
        self._border_width = max(1.0, border_width * self._scale)
        self._elevation = elevation * self._scale
        self._shadow_color = shadow_color or pal.shadow_color
        self._shadow_offset_y = shadow_offset_y * self._scale
        self._explicit_padding = padding
        self._padding = (padding * self._scale) if padding is not None else None
        self._current_pad = (padding * self._scale) if padding is not None else max(8.0 * self._scale, self._elevation * 0.8)

        self._photo = tk.PhotoImage(master=self, width=self._widget_w, height=self._widget_h)
        self._handle = SurfaceHandle(self._widget_w, self._widget_h)
        self._surface = Surface(self._handle)

        self._bg_label = tk.Label(
            self,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            background=self._parent_bg,
        )
        self._bg_label.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._bg_label.lower()

        self.bind("<Configure>", self._on_configure)
        self.bind("<Destroy>", self._on_destroy)
        add_theme_listener(self._on_theme_changed)
        self.after_idle(lambda: self.render() if self.winfo_exists() else None)

    @property
    def surface_id(self) -> int:
        """64-bit handle ID of the native surface in SurfaceRegistry."""
        return self._handle.surface_id if self._handle is not None else 0

    @property
    def handle(self) -> SurfaceHandle:
        return self._handle

    @property
    def surface(self) -> Surface:
        return self._surface

    def _on_destroy(self, event=None) -> None:
        if event is not None:
            w = getattr(event, "widget", None)
            if w is not None and w != self and str(w) != str(self):
                return
        remove_theme_listener(self._on_theme_changed)
        if hasattr(self, "_surface") and self._surface is not None:
            try:
                self._surface.close()
            except Exception:
                pass
            self._surface = None  # type: ignore
        if hasattr(self, "_handle") and self._handle is not None:
            try:
                self._handle.close()
            except Exception:
                pass
            self._handle = None  # type: ignore
        if hasattr(self, "_photo") and self._photo is not None:
            try:
                photo_name = str(self._photo.name)
                if hasattr(self, "_bg_label") and self._bg_label is not None and self._bg_label.winfo_exists():
                    self._bg_label.configure(image="")
                if hasattr(self, "tk") and self.tk is not None:
                    self.tk.call("image", "delete", photo_name)
            except Exception:
                pass
            self._photo = None  # type: ignore

    def destroy(self) -> None:
        try:
            for child in list(getattr(self, "children", {}).values()):
                if hasattr(child, "destroy"):
                    try:
                        child.destroy()
                    except Exception:
                        pass
        except Exception:
            pass
        self._on_destroy()
        super().destroy()

    def __del__(self) -> None:
        try:
            self._on_destroy()
        except Exception:
            pass

    @property
    def clip_children(self) -> bool:
        """Whether OS-level rounded corner clipping is enabled on inner content frames."""
        return self._clip_children

    @clip_children.setter
    def clip_children(self, val: bool) -> None:
        self._clip_children = bool(val)
        self._update_body_geometry()

    @property
    def safe_insets(self) -> tuple[float, float, float, float]:
        """Return (left, top, right, bottom) safe inner margins in logical units."""
        s = self._scale if self._scale > 0 else 1.0
        l_px, t_px, r_px, b_px = self.safe_insets_px
        return (l_px / s, t_px / s, r_px / s, b_px / s)

    @property
    def safe_insets_px(self) -> tuple[int, int, int, int]:
        """Return (left, top, right, bottom) safe inner margins in scaled pixels."""
        s = self._scale
        pad = self._current_pad if self._current_pad > 0 else (self._padding if self._padding is not None else max(8.0 * s, self._elevation * 0.8))
        inset_x = int(pad + self._border_width + (self._rx * 0.25))
        inset_y = int(pad + self._border_width + (self._ry * 0.25))
        return (inset_x, inset_y, inset_x, inset_y)

    @property
    def content_bounds(self) -> tuple[int, int, int, int]:
        """Return (x, y, width, height) of the printable inner rectangle in scaled pixels."""
        s = self._scale
        pad = self._current_pad if self._current_pad > 0 else (self._padding if self._padding is not None else max(8.0 * s, self._elevation * 0.8))
        if self._clip_children and is_window_shaping_supported():
            left = int(pad + self._border_width)
            top = int(pad + self._border_width)
            right = left
            bottom = top
            w = max(1, self._widget_w - left - right)
            h = max(1, self._widget_h - top - bottom)
            return (left, top, w, h)
        left, top, right, bottom = self.safe_insets_px
        w = max(1, self._widget_w - left - right)
        h = max(1, self._widget_h - top - bottom)
        return (left, top, w, h)

    @property
    def bg_color(self) -> str:
        """Return the current background/fill color of the container."""
        pal = get_theme()
        return str(self._bg_color or pal.card_bg)

    @property
    def body(self) -> tk.Frame:
        """
        Inner content frame automatically bounded within safe insets or clipped to container shape.
        Lazily created on first access and placed within the container's inner margins.
        """
        if not hasattr(self, "_body_frame") or not self._body_frame.winfo_exists():
            pal = get_theme()
            self._body_frame = tk.Frame(
                self,
                background=self._bg_color or pal.card_bg,
                borderwidth=0,
                highlightthickness=0,
            )
            self._update_body_geometry()
        return self._body_frame

    def _update_body_geometry(self) -> None:
        if hasattr(self, "_body_frame") and self._body_frame.winfo_exists():
            x, y, w, h = self.content_bounds
            self._body_frame.place(x=x, y=y, width=w, height=h)
            if self._clip_children and is_window_shaping_supported():
                inner_rx = max(0.0, self._rx - self._border_width)
                inner_ry = max(0.0, self._ry - self._border_width)
                self.after_idle(lambda: apply_round_rect_shape(self._body_frame, w, h, inner_rx, inner_ry))
            else:
                self.after_idle(lambda: clear_window_shape(self._body_frame))

    def create_content_frame(self, **kwargs) -> tk.Frame:
        """Helper to create an inner tk.Frame styled with the container's surface background and bounds."""
        bg = kwargs.pop("bg", kwargs.pop("background", self._bg_color))
        frame = tk.Frame(self, bg=bg, **kwargs)
        x, y, w, h = self.content_bounds
        frame.place(x=x, y=y, width=w, height=h)
        if self._clip_children and is_window_shaping_supported():
            inner_rx = max(0.0, self._rx - self._border_width)
            inner_ry = max(0.0, self._ry - self._border_width)
            self.after_idle(lambda: apply_round_rect_shape(frame, w, h, inner_rx, inner_ry))
        return frame

    def set_parent_bg(self, bg: str, force: bool = False, render: bool = True) -> None:
        """Update parent background and re-render container."""
        self._parent_bg = resolve_color_failsafe(bg, master=self, fallback=self._parent_bg)
        if force:
            self._explicit_parent_bg = None
        try:
            self.configure(background=self._parent_bg)
            if hasattr(self, "_bg_label") and self._bg_label.winfo_exists():
                self._bg_label.configure(background=self._parent_bg)
        except Exception as e:
            logger.debug("Failed configuring container background to '%s': %s", self._parent_bg, e)
        if render:
            self.render()

    def _on_theme_changed(self, palette: Palette) -> None:
        if not self.winfo_exists():
            return
        if self._explicit_parent_bg is None:
            self._parent_bg = Widget._resolve_default_bg(getattr(self, "master", None), palette)
        if self._explicit_bg_color is None:
            self._bg_color = palette.card_bg
        if self._explicit_border_color is None:
            self._border_color = palette.card_border
        if self._explicit_shadow_color is None:
            self._shadow_color = palette.shadow_color

        try:
            self.configure(background=self._parent_bg)
            if hasattr(self, "_bg_label") and self._bg_label.winfo_exists():
                self._bg_label.configure(background=self._parent_bg)
            if hasattr(self, "_body_frame") and self._body_frame.winfo_exists():
                self._body_frame.configure(background=self._bg_color)
        except Exception as e:
            logger.debug("Failed updating container colors during theme change: %s", e)
        self.render()
        cascade_bg_to_children(self, str(self._bg_color), preserve_overrides=True, render=False)

    def _on_configure(self, event) -> None:
        if event.width <= 1 or event.height <= 1:
            return
        pref_w = max(1, int(self._logical_w * self._scale))
        pref_h = max(1, int(self._logical_h * self._scale))
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        photo_w = max(pref_w, new_w)
        photo_h = max(pref_h, new_h)
        if (
            new_w != self._widget_w
            or new_h != self._widget_h
            or (self._photo is not None and (self._photo.cget("width") != photo_w or self._photo.cget("height") != photo_h))
        ):
            self._widget_w = new_w
            self._widget_h = new_h
            try:
                if self._photo is not None:
                    self._photo.configure(width=photo_w, height=photo_h)
                if self._surface is not None:
                    self._surface.resize(self._widget_w, self._widget_h)
            except Exception as e:
                logger.debug("Failed resizing container surface (%sx%s): %s", self._widget_w, self._widget_h, e)
            self._update_body_geometry()
            self.render()

    def set_background(self, bg_color: ColorLike, force: bool = False) -> None:
        resolved = resolve_color_failsafe(bg_color, master=self, fallback=str(self._bg_color))
        self._bg_color = resolved
        if force:
            self._explicit_bg_color = None
        if hasattr(self, "_body_frame") and self._body_frame.winfo_exists():
            try:
                self._body_frame.configure(background=self._bg_color)
            except Exception as e:
                logger.debug("Failed configuring container _body_frame background: %s", e)
        self.render()
        cascade_bg_to_children(self, str(self._bg_color))

    @property
    def padding(self) -> float:
        if self._explicit_padding is not None:
            return float(self._explicit_padding)
        return float(self._current_pad / self._scale) if self._scale > 0 else 0.0

    @padding.setter
    def padding(self, value: Optional[float]) -> None:
        self._explicit_padding = value
        self._padding = (value * self._scale) if value is not None else None
        self._current_pad = (value * self._scale) if value is not None else max(8.0 * self._scale, self._elevation * 0.8)
        self._update_body_geometry()
        self.render()

    def render(self) -> None:
        if self._widget_w <= 1 or self._widget_h <= 1:
            return
        try:
            from tkblend.surface import parse_color
            self._handle.clear(parse_color(self._parent_bg))
            if self._padding is not None:
                pad = max(0.0, self._padding)
            else:
                pad = max(8.0 * self._scale, self._elevation * 0.8)
            self._current_pad = pad
            draw_x = pad
            draw_y = pad
            draw_w = max(1.0, self._widget_w - pad * 2.0)
            draw_h = max(1.0, self._widget_h - pad * 2.0)

            if draw_w <= 1.0 or draw_h <= 1.0:
                self._handle.blit_to_photo(int(self.tk.interpaddr()), str(self._photo.name))
                return

            style = StyleEngine.resolve("card", "", 0)
            if self._explicit_bg_color is not None:
                style.bg_color = parse_color(self._explicit_bg_color)
            elif self._bg_color is not None:
                style.bg_color = parse_color(self._bg_color)

            if self._explicit_border_color is not None:
                style.border_color = parse_color(self._explicit_border_color)
            elif self._border_color is not None:
                style.border_color = parse_color(self._border_color)

            style.border_width = float(self._border_width)
            style.border_radius = float(self._rx)

            if self._elevation > 0.0 and pad > 0.0:
                max_blur = pad * 0.6
                style.shadow_blur = float(min(self._elevation * 0.8, max_blur))
                style.shadow_offset_y = float(min(self._shadow_offset_y, pad * 0.2, style.shadow_blur * 0.4))
                if self._explicit_shadow_color is not None:
                    style.shadow_color = parse_color(self._explicit_shadow_color)
                elif self._shadow_color is not None:
                    style.shadow_color = parse_color(self._shadow_color)
            else:
                style.shadow_blur = 0.0
                style.shadow_offset_y = 0.0

            self._handle.render_box(
                float(draw_x),
                float(draw_y),
                float(draw_w),
                float(draw_h),
                style,
                "",
                1,
            )
            self._handle.blit_to_photo(int(self.tk.interpaddr()), str(self._photo.name))
        except Exception as e:
            logger.debug("Render failed in ContainerBase: %s", e, exc_info=True)


def cascade_bg_to_children(
    container: Any,
    bg: str,
    preserve_overrides: bool = True,
    render: bool = False,
) -> None:
    """Recursively propagate background color down through child widgets."""
    if not hasattr(container, "winfo_children"):
        return
    try:
        children = container.winfo_children()
    except Exception as e:
        logger.debug("Failed getting winfo_children in cascade_bg_to_children for %r: %s", container, e)
        return

    for child in children:
        try:
            if not child.winfo_exists():
                continue
        except Exception as e:
            logger.debug("Error checking winfo_exists in cascade_bg_to_children for %r: %s", child, e)
            continue

        # Skip the internal backing surface label of Card / Frame
        if getattr(container, "_bg_label", None) is child:
            continue

        # If child is a container with its own bg_color (Card, Frame, ScrollableFrame, Tabview, Table, TextBox):
        if hasattr(child, "bg_color") and not callable(getattr(child, "bg_color", None)):
            if hasattr(child, "set_parent_bg"):
                try:
                    child.set_parent_bg(bg, render=render)
                except Exception as e:
                    logger.debug("Failed setting parent_bg on child container %r: %s", child, e)
            inner_bg = str(child.bg_color)
            cascade_bg_to_children(child, inner_bg, preserve_overrides=preserve_overrides, render=render)
            continue

        # If it's a vector Widget or has set_parent_bg:
        if hasattr(child, "set_parent_bg"):
            if preserve_overrides and getattr(child, "_explicit_bg", None) is not None:
                continue
            try:
                child.set_parent_bg(bg, render=render)
            except Exception as e:
                logger.debug("Failed setting parent_bg on child widget %r: %s", child, e)
            continue

        # Standard container (e.g. tk.Frame, tk.Canvas, tk.Label): update its background and recurse
        if hasattr(child, "configure"):
            try:
                if isinstance(child, tk.Label):
                    pal = get_theme()
                    child.configure(background=bg, foreground=pal.text_muted)
                else:
                    child.configure(background=bg)
            except Exception as e:
                try:
                    child.configure(background=bg)
                except Exception:
                    pass
        cascade_bg_to_children(child, bg, preserve_overrides=preserve_overrides, render=render)

