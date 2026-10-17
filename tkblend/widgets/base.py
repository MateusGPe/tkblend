"""
Base class for pure Blend2D vector widgets powered by NativeController and DrawEngine.
Zero TTK dependencies, zero PhotoImage allocations.
"""

from __future__ import annotations

import sys
import tkinter as tk
from typing import Optional, Callable, Any, Union, Dict, Sequence

from tkblend._tkblend import (
    ControllerPseudoState,
    ContainerLayer,
    StyleEngine,
    DrawEngine,
    DrawBatch,
)

from tkblend.controller import NativeController
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.theme import (
    Palette,
    get_theme,
    add_theme_listener,
    remove_theme_listener,
    resolve_ancestor_bg,
    resolve_color_failsafe,
    to_tk_hex,
)
from tkblend.widgets.constants import (
    TK_SCALING_BASE,
    TK_SCALING_BASE_DARWIN,
    TK_SCALING_MIN_THRESHOLD,
    DEFAULT_BASE_WIDTH,
    DEFAULT_BASE_HEIGHT,
    FALLBACK_DARK_BG,
    FALLBACK_LIGHT_BG,
    STATE_NORMAL,
    STATE_DISABLED,
    CURSOR_DEFAULT,
)
from tkblend.font import parse_font, FontConfig
from tkblend.widgets.utils import normalize_anchor, measure_text_dimensions


class ScalingTracker:
    """Detects and tracks system/window scaling factors across OS platforms."""

    _cached_factor: Optional[float] = None

    @classmethod
    def get_scaling_factor(cls, widget: Optional[tk.Misc] = None) -> float:
        if cls._cached_factor is not None:
            return cls._cached_factor

        if widget is None:
            try:
                widget = getattr(tk, "_default_root", None)
            except Exception:
                pass

        if widget is not None:
            try:
                # 1. Tk 9.0+ scaling percentage check (::tk::scalingPct e.g. 100, 150, 200)
                try:
                    exists_pct = widget.tk.eval("info exists ::tk::scalingPct")
                    if str(exists_pct) == "1":
                        pct_val = widget.tk.getvar("::tk::scalingPct")
                        if pct_val:
                            pct_float = float(pct_val)
                            if pct_float > 10.0:
                                factor = pct_float / 100.0
                                if factor > TK_SCALING_MIN_THRESHOLD:
                                    cls._cached_factor = factor
                                    return factor
                except Exception:
                    pass

                # 2. Query standard Tk scaling (72 points per inch standard base -> 96 / 72 = 1.333 on Windows/X11, 72 / 72 = 1.0 on Aqua)
                scale = float(widget.tk.call("tk", "scaling"))
                base = TK_SCALING_BASE_DARWIN if sys.platform == "darwin" else TK_SCALING_BASE
                factor = scale / base
                if abs(factor - 1.0) < 0.005:
                    factor = 1.0
                if factor > TK_SCALING_MIN_THRESHOLD:
                    cls._cached_factor = factor
                    return factor
            except Exception:
                pass

        return 1.0


class BaseControl(tk.Frame):
    """
    High-performance base control for Blend2D vector widgets.
    Subclasses tk.Frame and delegates rendering and event handling to NativeController and DrawEngine.
    """

    WIDGET_CLASS: str = ""
    DEFAULT_ANCHOR: str = "center"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        widget_class: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
        auto_fit: Optional[bool] = None,
        anchor: Optional[str] = None,
        corner_radius: Optional[float] = None,
        font: Any = None,
        text_overflow: str = "clip",
        inner_bg: Optional[ColorLike] = None,
        outer_bg: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        cursor: Optional[str] = None,
        takefocus: bool = True,
        state: str = STATE_NORMAL,
        command: Optional[Callable[..., Any]] = None,
        variable: Optional[tk.Variable] = None,
        **kwargs,
    ):
        self._master_ref = master
        self._widget_class = str(widget_class or getattr(self, "WIDGET_CLASS", ""))
        self._command = command
        self._variable = variable
        self._explicit_outer_bg = outer_bg if outer_bg is not None else parent_bg
        self._explicit_inner_bg = inner_bg if inner_bg is not None else bg_color
        self._explicit_parent_bg = self._explicit_outer_bg
        self._state_str = state
        self._takefocus = takefocus
        self._cursor_pref = cursor
        self._scale_factor = ScalingTracker.get_scaling_factor(master)

        # Dimension constraints (logical pixels)
        self._explicit_width = int(width) if width is not None else getattr(self, "_explicit_width", None)
        self._explicit_height = int(height) if height is not None else getattr(self, "_explicit_height", None)
        self._min_width = int(min_width) if min_width is not None else getattr(self, "_min_width", None)
        self._max_width = int(max_width) if max_width is not None else getattr(self, "_max_width", None)
        self._min_height = int(min_height) if min_height is not None else getattr(self, "_min_height", None)
        self._max_height = int(max_height) if max_height is not None else getattr(self, "_max_height", None)
        if auto_fit is not None:
            self._auto_fit = bool(auto_fit)
        elif hasattr(self, "_auto_fit") and self._auto_fit is not None:
            pass
        else:
            self._auto_fit = (width is None)
        self._anchor = normalize_anchor(anchor or getattr(self, "_anchor", getattr(self, "DEFAULT_ANCHOR", "center")))
        self._corner_radius = float(corner_radius) if corner_radius is not None else getattr(self, "_corner_radius", None)
        self._text_overflow = text_overflow or getattr(self, "_text_overflow", "clip")

        # Font configuration
        self._font_config: FontConfig = parse_font(font) if font is not None else getattr(self, "_font_config", parse_font(None))

        # Resolve initial theme palette & backgrounds
        self._palette = get_theme()
        resolved_outer = (
            resolve_color_failsafe(self._explicit_outer_bg, palette=self._palette)
            if self._explicit_outer_bg is not None
            else resolve_ancestor_bg(master, self._palette)
        )
        self._resolved_outer_bg = resolved_outer
        self._resolved_parent_bg = resolved_outer

        resolved_inner = (
            resolve_color_failsafe(self._explicit_inner_bg, palette=self._palette)
            if self._explicit_inner_bg is not None
            else self._default_inner_bg(self._palette)
        )
        self._resolved_inner_bg = resolved_inner

        self._logical_w = self._explicit_width or 100
        self._logical_h = self._explicit_height or 36

        tk_frame_options = {
            "class", "colormap", "container", "cursor", "height",
            "highlightbackground", "highlightcolor", "highlightthickness",
            "padx", "pady", "relief", "takefocus", "visual", "width"
        }
        frame_kwargs = {k: v for k, v in kwargs.items() if k in tk_frame_options}
        extra_kwargs = {k: v for k, v in kwargs.items() if k not in tk_frame_options}

        super().__init__(
            master=master,
            width=1,
            height=1,
            background="",
            takefocus=1 if takefocus else 0,
            cursor=cursor or CURSOR_DEFAULT,
            **frame_kwargs,
        )

        # Prevent frame geometry propagation from children
        self.pack_propagate(False)
        self.grid_propagate(False)

        # Attach NativeController
        self._controller = NativeController(
            widget=self,
            auto_hover=True,
            auto_press=True,
            auto_focus=True,
            parent_bg=self._resolved_outer_bg,
            widget_class=self._widget_class,
            on_state_changed=self._on_controller_state_changed,
            on_click=self._on_controller_click,
            on_resize=self._on_controller_resize,
            on_change=self._on_controller_change,
        )

        if self._anchor:
            self.set_var("--anchor", self._anchor)
        if self._corner_radius is not None:
            self.set_var("--rx", str(self._corner_radius))
            self.set_var("--ry", str(self._corner_radius))
        if font is not None:
            self.set_var("--font-family", self._font_config.family)
            self.set_var("--font-size", str(self._font_config.size))
            self.set_var("--font-weight", str(self._font_config.effective_weight))

        if self._widget_class == "card":
            self._controller.container_layer = ContainerLayer.Surface

        if self._state_str == "disabled":
            self._controller.is_disabled = True

        if extra_kwargs:
            self.configure(**extra_kwargs)

        # Compute initial target dimensions now that controller and properties are configured
        target_w, target_h = self._compute_target_size()
        self.set_geometry_request(target_w, target_h)

        # Register dynamic theme updates
        add_theme_listener(self._on_theme_changed)

        # Event bindings
        self.bind("<Destroy>", self._on_tk_destroy, add="+")
        self.bind("<Configure>", self._on_tk_configure, add="+")

    def _default_inner_bg(self, pal: Palette) -> str:
        """Subclasses can override to define their default semantic theme inner color."""
        if getattr(self, "_widget_class", "") == "card":
            return pal.card_bg
        return pal.bg

    @property
    def controller(self) -> NativeController:
        return self._controller

    @property
    def surface(self) -> Surface:
        return self._controller.surface

    @property
    def scale_factor(self) -> float:
        return self._scale_factor

    @property
    def widget_class(self) -> str:
        return self._controller.widget_class

    @widget_class.setter
    def widget_class(self, val: str) -> None:
        self._widget_class = str(val)
        self._controller.widget_class = str(val)

    @property
    def is_disabled(self) -> bool:
        return self._controller.is_disabled or self._state_str == "disabled"

    @is_disabled.setter
    def is_disabled(self, disabled: bool) -> None:
        self._controller.is_disabled = bool(disabled)
        self._state_str = "disabled" if disabled else "normal"
        self._update_cursor()
        self.request_redraw()

    @property
    def is_hovered(self) -> bool:
        return self._controller.is_hovered and not self.is_disabled

    @property
    def is_pressed(self) -> bool:
        return self._controller.is_pressed and not self.is_disabled

    @property
    def is_focused(self) -> bool:
        return self._controller.is_focused and not self.is_disabled

    @property
    def is_checked(self) -> bool:
        return self._controller.is_checked

    @is_checked.setter
    def is_checked(self, checked: bool) -> None:
        self._controller.is_checked = bool(checked)
        self.request_redraw()

    @property
    def checked(self) -> bool:
        return self.is_checked

    @checked.setter
    def checked(self, checked: bool) -> None:
        self.is_checked = checked

    @property
    def outer_bg(self) -> str:
        """Return the active outer (parent container) background color from C++ or theme."""
        if self._explicit_outer_bg is not None:
            return resolve_color_failsafe(self._explicit_outer_bg, palette=self._palette)
        if hasattr(self, "_controller") and self._controller.is_attached:
            try:
                col = self._controller.resolve_parent_bg()
                if col.a > 0 or col.r > 0 or col.g > 0 or col.b > 0:
                    return col.to_hex(include_alpha=False)
            except Exception:
                pass
        return self._resolved_outer_bg or self._palette.bg

    @outer_bg.setter
    def outer_bg(self, color: ColorLike) -> None:
        self.set_outer_bg(color, render=True, explicit=True)

    @property
    def parent_bg(self) -> str:
        """Deprecated alias for outer_bg."""
        return self.outer_bg

    @parent_bg.setter
    def parent_bg(self, color: ColorLike) -> None:
        self.set_outer_bg(color, render=True, explicit=True)

    @property
    def inner_bg(self) -> str:
        """Return the active inner surface/fill background color."""
        if self._explicit_inner_bg is not None:
            return resolve_color_failsafe(self._explicit_inner_bg, palette=self._palette)
        if self._resolved_inner_bg is not None:
            return self._resolved_inner_bg
        return self._default_inner_bg(self._palette)

    @inner_bg.setter
    def inner_bg(self, color: ColorLike) -> None:
        self.set_inner_bg(color, render=True, explicit=True)

    @property
    def bg_color(self) -> str:
        """Alias for inner_bg used in container background protocols."""
        return self.inner_bg

    @bg_color.setter
    def bg_color(self, color: ColorLike) -> None:
        self.set_inner_bg(color, render=True, explicit=True)

    def set_outer_bg(self, color: ColorLike, render: bool = True, explicit: bool = True) -> None:
        """Update outer (parent container) background color."""
        if explicit:
            self._explicit_outer_bg = color
            self._explicit_parent_bg = color
        resolved = resolve_color_failsafe(color, palette=self._palette)
        self._resolved_outer_bg = resolved
        self._resolved_parent_bg = resolved
        self._controller.parent_bg = resolved
        if render:
            self.request_redraw()

    def set_parent_bg(self, color: ColorLike, render: bool = True, explicit: bool = True) -> None:
        """Deprecated alias for set_outer_bg."""
        self.set_outer_bg(color, render=render, explicit=explicit)

    def set_inner_bg(self, color: ColorLike, render: bool = True, explicit: bool = True) -> None:
        """Update inner fill background color."""
        if explicit:
            self._explicit_inner_bg = color
        resolved = resolve_color_failsafe(color, palette=self._palette)
        self._resolved_inner_bg = resolved
        if render:
            self.request_redraw()

    def set_bg_color(self, color: ColorLike, render: bool = True, explicit: bool = True) -> None:
        """Alias for set_inner_bg."""
        self.set_inner_bg(color, render=render, explicit=explicit)

    def _get_content_size(self) -> tuple[int, int]:
        """Subclasses can override to measure and return natural (content_w, content_h)."""
        return (
            self._explicit_width or DEFAULT_BASE_WIDTH,
            self._explicit_height or DEFAULT_BASE_HEIGHT,
        )

    def _compute_target_size(self) -> tuple[int, int]:
        content_w, content_h = self._get_content_size()

        # Width calculation
        if self._auto_fit or self._explicit_width is None:
            w = content_w
            if self._explicit_width is not None:
                w = max(self._explicit_width, w)
        else:
            w = self._explicit_width

        if self._min_width is not None:
            w = max(self._min_width, w)
        if self._max_width is not None:
            w = min(self._max_width, w)

        # Height calculation
        if self._auto_fit or self._explicit_height is None:
            h = content_h
            if self._explicit_height is not None:
                h = max(self._explicit_height, h)
        else:
            h = self._explicit_height

        if self._min_height is not None:
            h = max(self._min_height, h)
        if self._max_height is not None:
            h = min(self._max_height, h)

        return max(1, int(w)), max(1, int(h))

    def _recalculate_natural_size(self) -> None:
        """Recalculate content dimensions and update geometry request if changed."""
        target_w, target_h = self._compute_target_size()
        if target_w != self._logical_w or target_h != self._logical_h:
            self.set_geometry_request(target_w, target_h)

    def set_geometry_request(self, width: int, height: int) -> None:
        """Set logical dimensions and request geometry update."""
        self._logical_w = int(width)
        self._logical_h = int(height)
        scale = self.scale_factor
        pw = max(1, int(round(self._logical_w * scale)))
        ph = max(1, int(round(self._logical_h * scale)))
        if hasattr(self, "_controller") and self._controller.is_attached:
            self._controller.set_geometry_request(pw, ph)
        try:
            super().configure(width=pw, height=ph)
        except Exception:
            pass
        self.request_redraw()

    @property
    def width(self) -> int:
        return self._logical_w

    @width.setter
    def width(self, val: Optional[int]) -> None:
        self._explicit_width = int(val) if val is not None else None
        self._recalculate_natural_size()

    @property
    def height(self) -> int:
        return self._logical_h

    @height.setter
    def height(self, val: Optional[int]) -> None:
        self._explicit_height = int(val) if val is not None else None
        self._recalculate_natural_size()

    @property
    def min_width(self) -> Optional[int]:
        return self._min_width

    @min_width.setter
    def min_width(self, val: Optional[int]) -> None:
        self._min_width = int(val) if val is not None else None
        self._recalculate_natural_size()

    @property
    def max_width(self) -> Optional[int]:
        return self._max_width

    @max_width.setter
    def max_width(self, val: Optional[int]) -> None:
        self._max_width = int(val) if val is not None else None
        self._recalculate_natural_size()

    @property
    def min_height(self) -> Optional[int]:
        return self._min_height

    @min_height.setter
    def min_height(self, val: Optional[int]) -> None:
        self._min_height = int(val) if val is not None else None
        self._recalculate_natural_size()

    @property
    def max_height(self) -> Optional[int]:
        return self._max_height

    @max_height.setter
    def max_height(self, val: Optional[int]) -> None:
        self._max_height = int(val) if val is not None else None
        self._recalculate_natural_size()

    @property
    def auto_fit(self) -> bool:
        return self._auto_fit

    @auto_fit.setter
    def auto_fit(self, val: bool) -> None:
        self._auto_fit = bool(val)
        self._recalculate_natural_size()

    @property
    def anchor(self) -> str:
        return self._anchor

    @anchor.setter
    def anchor(self, val: str) -> None:
        self._anchor = normalize_anchor(val)
        self.set_var("--anchor", self._anchor)
        self.request_redraw()

    @property
    def corner_radius(self) -> Optional[float]:
        return self._corner_radius

    @corner_radius.setter
    def corner_radius(self, val: Optional[float]) -> None:
        self._corner_radius = float(val) if val is not None else None
        if val is not None:
            self.set_var("--rx", str(val))
            self.set_var("--ry", str(val))
        else:
            self.remove_var("--rx")
            self.remove_var("--ry")
        self.request_redraw()

    @property
    def font(self) -> FontConfig:
        return self._font_config

    @font.setter
    def font(self, val: Any) -> None:
        self._font_config = parse_font(val)
        self.set_var("--font-family", self._font_config.family)
        self.set_var("--font-size", str(self._font_config.size))
        self.set_var("--font-weight", str(self._font_config.effective_weight))
        self._recalculate_natural_size()
        self.request_redraw()

    @property
    def text_overflow(self) -> str:
        return self._text_overflow

    @text_overflow.setter
    def text_overflow(self, val: str) -> None:
        self._text_overflow = str(val or "clip").lower()
        self.set_var("--text-overflow", self._text_overflow)
        self.request_redraw()

    @property
    def state(self) -> str:
        return self._state_str

    @state.setter
    def state(self, val: str) -> None:
        val_str = str(val or "normal").lower()
        self.is_disabled = (val_str == "disabled")

    @property
    def command(self) -> Optional[Callable[..., Any]]:
        return self._command

    @command.setter
    def command(self, cmd: Optional[Callable[..., Any]]) -> None:
        self._command = cmd

    @property
    def variable(self) -> Optional[tk.Variable]:
        return self._variable

    @variable.setter
    def variable(self, var: Optional[tk.Variable]) -> None:
        self._variable = var

    # Container layer management
    @property
    def container_layer(self) -> int:
        return self._controller.container_layer

    @container_layer.setter
    def container_layer(self, layer: Any) -> None:
        self._controller.container_layer = layer

    def set_container_layer(self, layer: Any) -> BaseControl:
        self.container_layer = layer
        return self

    # CSS Class Management
    def add_class(self, name: str) -> BaseControl:
        """Add a CSS class and trigger auto-redraw."""
        self._controller.add_class(name)
        return self

    def remove_class(self, name: str) -> BaseControl:
        """Remove a CSS class and trigger auto-redraw."""
        self._controller.remove_class(name)
        return self

    def toggle_class(self, name: str) -> BaseControl:
        """Toggle a CSS class on the control."""
        self._controller.toggle_class(name)
        return self

    def has_class(self, name: str) -> bool:
        """Return True if the control has the specified CSS class."""
        return self._controller.has_class(name)

    @property
    def classes(self) -> list[str]:
        """List of active CSS classes."""
        return self._controller.classes

    @classes.setter
    def classes(self, val: Sequence[str]) -> None:
        self._controller.classes = val

    @property
    def class_name(self) -> str:
        """Space-separated string of active CSS classes."""
        return self._controller.class_name

    @class_name.setter
    def class_name(self, val: str) -> None:
        self._controller.class_name = val

    # Dynamic Variable Management
    def set_var(self, key: str, value: Any) -> BaseControl:
        """Set a local scoped variable and trigger auto-redraw."""
        self._controller.set_var(key, value)
        return self

    def get_var(self, key: str, default: Optional[str] = None) -> str:
        """Get the value of a scoped or global variable."""
        return self._controller.get_var(key, default)

    def get_color(self, var_name: str, fallback: Optional[str] = None) -> str:
        """Resolve a CSS color variable (scoped to widget or global theme)."""
        key = var_name if var_name.startswith("--") else f"--{var_name}"
        local_val = self._controller.get_var(key)
        if not local_val and not var_name.startswith("--"):
            local_val = self._controller.get_var(var_name)
        if local_val:
            return resolve_color_failsafe(local_val, fallback=fallback, palette=self._palette)

        val = StyleEngine.get_variable(key, self._palette.name)
        if not val and not var_name.startswith("--"):
            val = StyleEngine.get_variable(var_name, self._palette.name)
        if val:
            return resolve_color_failsafe(val, fallback=fallback, palette=self._palette)

        return fallback or getattr(self._palette, var_name.replace("-", "_"), "#000000")

    def remove_var(self, key: str) -> BaseControl:
        """Remove a locally scoped variable override."""
        self._controller.remove_var(key)
        return self

    def clear_vars(self) -> BaseControl:
        """Clear all locally scoped variable overrides."""
        self._controller.clear_vars()
        return self

    @property
    def vars(self) -> dict[str, str]:
        """Dictionary of all local variable overrides."""
        return self._controller.vars

    @vars.setter
    def vars(self, d: dict[str, Any]) -> None:
        self._controller.vars = d

    # DrawBatch Binding
    def bind_batch(self, batch: Any) -> BaseControl:
        """Bind an explicit C++ DrawBatch display list."""
        self._controller.bind_batch(batch)
        return self

    def clear_batch(self) -> BaseControl:
        """Clear any bound DrawBatch and return to class-level DrawEngine lookup."""
        self._controller.clear_batch()
        return self

    @property
    def has_batch(self) -> bool:
        """Return True if a C++ DrawBatch is actively bound or registered for this class."""
        if self._controller.has_batch:
            return True
        if self._controller.widget_class:
            return DrawEngine.has_batch(self._controller.widget_class, self._controller.state)
        return False

    def request_redraw(self) -> None:
        """Request native redraw through C++ NativeController."""
        if hasattr(self, "_controller") and self._controller.is_attached:
            self._controller.request_redraw()

    def paint_and_blit(self) -> None:
        """Synchronously render and blit to widget through C++ NativeController."""
        if hasattr(self, "_controller") and self._controller.is_attached:
            self._controller.paint_and_blit()

    # Controller Callbacks
    def _on_controller_state_changed(self, new_state: int, old_state: int) -> None:
        self.on_state_changed(new_state, old_state)

    def on_state_changed(self, new_state: int, old_state: int) -> None:
        """Hook called when hover, active, or focused state changes."""
        pass

    def _on_controller_click(self, x: int, y: int, button: int) -> None:
        if not self.is_disabled:
            if callable(self._command) and self._widget_class not in ("switch", "checkbox", "radio", "slider"):
                try:
                    self._command()
                except Exception:
                    pass
            self.on_click(x, y, button)

    def on_click(self, x: int, y: int, button: int) -> None:
        """Hook called on mouse button release."""
        pass

    def _on_tk_configure(self, event: tk.Event) -> None:
        if event.widget == self:
            w = int(event.width)
            h = int(event.height)
            if w > 0 and h > 0 and (w != getattr(self, "_last_conf_w", None) or h != getattr(self, "_last_conf_h", None)):
                self._last_conf_w = w
                self._last_conf_h = h
                self.on_resize(w, h)

    def _on_controller_resize(self, width: int, height: int) -> None:
        pass

    def on_resize(self, width: int, height: int) -> None:
        """Hook called on widget geometry resize."""
        pass

    def _on_controller_change(self, val: Any) -> None:
        if not self.is_disabled:
            self.on_change(val)

    def on_change(self, val: Any) -> None:
        """Hook called when native widget value/state changes in C++ (slider drag, switch toggle, etc.)."""
        pass

    # Theme lifecycle
    def _on_theme_changed(self, pal: Palette) -> None:
        self._palette = pal
        if self._explicit_outer_bg is None:
            self._resolved_outer_bg = resolve_ancestor_bg(self.master, pal)
        else:
            self._resolved_outer_bg = resolve_color_failsafe(self._explicit_outer_bg, palette=pal)
        self._resolved_parent_bg = self._resolved_outer_bg
        self._controller.parent_bg = self._resolved_outer_bg

        if self._explicit_inner_bg is None:
            self._resolved_inner_bg = self._default_inner_bg(pal)
        else:
            self._resolved_inner_bg = resolve_color_failsafe(self._explicit_inner_bg, palette=pal)

        if hasattr(self, "_controller") and hasattr(self._controller, "invalidate_cached_batch"):
            self._controller.invalidate_cached_batch()

        self.on_theme_update(pal)
        self.request_redraw()

    def on_theme_update(self, pal: Palette) -> None:
        """Subclasses can override to update color variables on theme change."""
        pass

    def _on_tk_destroy(self, event: Optional[tk.Event] = None) -> None:
        if event is None or event.widget is self or str(getattr(event, "widget", "")) == str(self):
            try:
                remove_theme_listener(self._on_theme_changed)
            except Exception:
                pass
            if hasattr(self, "_controller"):
                self._controller.clear_on_state_changed()
                self._controller.clear_on_click()
                self._controller.clear_on_resize()
                if self._controller.is_attached:
                    self._controller.detach()

    def _init_variable(self, var: Optional[tk.Variable], callback: Callable[..., None]) -> None:
        """Bind a change listener to a Tk variable and keep trace ID for clean teardown."""
        from tkblend.widgets.utils import bind_variable_trace
        self._var_trace_id: Optional[str] = None
        if var is not None:
            self._var_trace_id = bind_variable_trace(var, callback)

    def _sync_variable_out(self, val: Any) -> None:
        """Safely push widget state changes to the bound Tk variable."""
        if self._variable is not None:
            try:
                self._variable.set(val)
            except Exception:
                pass

    def destroy(self) -> None:
        """Safely release native controller, bindings and listeners."""
        from tkblend.widgets.utils import unbind_variable_trace
        if self._variable is not None and getattr(self, "_var_trace_id", None) is not None:
            unbind_variable_trace(self._variable, self._var_trace_id)
            self._var_trace_id = None
        self._on_tk_destroy(None)
        super().destroy()

    def _update_cursor(self) -> None:
        cur = "" if self.is_disabled else (self._cursor_pref or "")
        try:
            super().configure(cursor=cur)
        except Exception:
            pass

    # Standard Tkinter configure / cget
    def configure(self, cnf=None, **kwargs):
        if cnf is None and not kwargs:
            return super().configure()
        if cnf:
            kwargs.update(cnf)

        if "state" in kwargs:
            self.state = kwargs.pop("state")
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if "variable" in kwargs:
            self.variable = kwargs.pop("variable")
        if "widget_class" in kwargs:
            self.widget_class = kwargs.pop("widget_class")
        if "anchor" in kwargs:
            self.anchor = kwargs.pop("anchor")
        if "corner_radius" in kwargs:
            self.corner_radius = kwargs.pop("corner_radius")
        if "font" in kwargs:
            self.font = kwargs.pop("font")
        if "auto_fit" in kwargs:
            self.auto_fit = kwargs.pop("auto_fit")
        if "min_width" in kwargs:
            self.min_width = kwargs.pop("min_width")
        if "max_width" in kwargs:
            self.max_width = kwargs.pop("max_width")
        if "min_height" in kwargs:
            self.min_height = kwargs.pop("min_height")
        if "max_height" in kwargs:
            self.max_height = kwargs.pop("max_height")
        if "width" in kwargs:
            self.width = kwargs.pop("width")
        if "height" in kwargs:
            self.height = kwargs.pop("height")
        if "text_overflow" in kwargs:
            self.text_overflow = kwargs.pop("text_overflow")
        if "value" in kwargs:
            val = kwargs.pop("value")
            if hasattr(self, "value"):
                self.value = val
            elif hasattr(self, "set"):
                self.set(val)
        if "values" in kwargs:
            vals = kwargs.pop("values")
            if hasattr(self, "values"):
                self.values = vals
        if "cursor" in kwargs:
            self._cursor_pref = kwargs.pop("cursor")
            self._update_cursor()
        if "outer_bg" in kwargs:
            self.set_outer_bg(kwargs.pop("outer_bg"), explicit=True)
        if "parent_bg" in kwargs:
            self.set_outer_bg(kwargs.pop("parent_bg"), explicit=True)
        if "inner_bg" in kwargs:
            self.set_inner_bg(kwargs.pop("inner_bg"), explicit=True)
        if "bg_color" in kwargs:
            self.set_inner_bg(kwargs.pop("bg_color"), explicit=True)
        if "bg" in kwargs or "background" in kwargs:
            bg_val = kwargs.pop("bg", kwargs.pop("background", None))
            if bg_val is not None:
                self.set_outer_bg(bg_val, explicit=True)
        if "text" in kwargs:
            txt_val = kwargs.pop("text")
            if hasattr(self, "text"):
                self.text = txt_val
            else:
                self.set_var("--text", str(txt_val))
                self._recalculate_natural_size()

        for key in list(kwargs.keys()):
            prop = getattr(type(self), key, None)
            if isinstance(prop, property) and prop.fset is not None:
                setattr(self, key, kwargs.pop(key))

        if kwargs:
            valid_tk_keys = ("takefocus", "highlightbackground", "highlightcolor", "highlightthickness", "padx", "pady")
            tk_kwargs = {k: v for k, v in kwargs.items() if k in valid_tk_keys}
            if tk_kwargs:
                return super().configure(**tk_kwargs)
        return None

    config = configure

    def cget(self, key: str) -> Any:
        if key == "state":
            return self._state_str
        if key == "widget_class":
            return self.widget_class
        if key == "command":
            return self._command
        if key == "variable":
            return self._variable
        if key == "width":
            return self._logical_w
        if key == "height":
            return self._logical_h
        if key == "min_width":
            return self._min_width
        if key == "max_width":
            return self._max_width
        if key == "min_height":
            return self._min_height
        if key == "max_height":
            return self._max_height
        if key == "auto_fit":
            return self._auto_fit
        if key == "anchor":
            return self._anchor
        if key == "corner_radius":
            return self._corner_radius
        if key == "font":
            return self._font_config
        if key == "text_overflow":
            return self._text_overflow
        if key in ("outer_bg", "parent_bg"):
            return self._resolved_outer_bg
        if key in ("inner_bg", "bg_color"):
            return self.inner_bg
        if key in ("bg", "background"):
            return self._resolved_outer_bg
        if key == "cursor":
            return self._cursor_pref

        cls_attr = getattr(type(self), key, None)
        if isinstance(cls_attr, property) and cls_attr.fget is not None:
            return getattr(self, key)

        if hasattr(self, f"_{key}"):
            return getattr(self, f"_{key}")

        try:
            return super().cget(key)
        except Exception:
            return None

    __getitem__ = cget

    def __setitem__(self, key: str, value: Any) -> None:
        self.configure(**{key: value})
