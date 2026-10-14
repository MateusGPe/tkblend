"""
Base class for pure Blend2D vector widgets powered by NativeController and DrawEngine.
Zero TTK dependencies, zero PhotoImage allocations.
"""

from __future__ import annotations

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
    TK_SCALING_MIN_THRESHOLD,
    DEFAULT_BASE_WIDTH,
    DEFAULT_BASE_HEIGHT,
    FALLBACK_DARK_BG,
    FALLBACK_LIGHT_BG,
    STATE_NORMAL,
    STATE_DISABLED,
    CURSOR_DEFAULT,
)


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

                # 2. Query standard Tk scaling (72 points per inch standard base -> 96 / 72 = 1.333)
                scale = float(widget.tk.call("tk", "scaling"))
                factor = scale / TK_SCALING_BASE
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

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        widget_class: Optional[str] = None,
        width: int = DEFAULT_BASE_WIDTH,
        height: int = DEFAULT_BASE_HEIGHT,
        inner_bg: Optional[ColorLike] = None,
        outer_bg: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        cursor: Optional[str] = None,
        takefocus: bool = True,
        state: str = STATE_NORMAL,
        command: Optional[Callable[..., Any]] = None,
        **kwargs,
    ):
        self._logical_w = int(width)
        self._logical_h = int(height)
        self._master_ref = master
        self._widget_class = str(widget_class or getattr(self, "WIDGET_CLASS", ""))
        self._command = command
        self._explicit_outer_bg = outer_bg if outer_bg is not None else parent_bg
        self._explicit_inner_bg = inner_bg if inner_bg is not None else bg_color
        self._explicit_parent_bg = self._explicit_outer_bg
        self._state_str = state
        self._takefocus = takefocus
        self._cursor_pref = cursor
        self._scale_factor = ScalingTracker.get_scaling_factor(master)

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

        # Compute initial scaled geometry
        scale = self._scale_factor
        init_w = max(1, int(self._logical_w * scale))
        init_h = max(1, int(self._logical_h * scale))

        tk_frame_options = {
            "class", "colormap", "container", "cursor", "height",
            "highlightbackground", "highlightcolor", "highlightthickness",
            "padx", "pady", "relief", "takefocus", "visual", "width"
        }
        frame_kwargs = {k: v for k, v in kwargs.items() if k in tk_frame_options}
        extra_kwargs = {k: v for k, v in kwargs.items() if k not in tk_frame_options}

        super().__init__(
            master=master,
            width=init_w,
            height=init_h,
            background="",
            takefocus=1 if takefocus else 0,
            cursor=cursor or CURSOR_DEFAULT,
            **frame_kwargs,
        )

        if extra_kwargs:
            self.configure(**extra_kwargs)

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
        self._controller.set_geometry_request(init_w, init_h)

        if self._widget_class == "card":
            self._controller.container_layer = ContainerLayer.Surface

        if self._state_str == "disabled":
            self._controller.is_disabled = True

        # Register dynamic theme updates
        add_theme_listener(self._on_theme_changed)

        # Event bindings
        self.bind("<Destroy>", self._on_tk_destroy, add="+")

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

    def set_geometry_request(self, width: int, height: int) -> None:
        """Set logical dimensions and request geometry update."""
        self._logical_w = int(width)
        self._logical_h = int(height)
        scale = self.scale_factor
        pw = max(1, int(self._logical_w * scale))
        ph = max(1, int(self._logical_h * scale))
        self._controller.set_geometry_request(pw, ph)
        try:
            super().configure(width=pw, height=ph)
        except Exception:
            pass
        self.request_redraw()

    # Container layer management
    @property
    def container_layer(self) -> int:
        return self._controller.container_layer

    @container_layer.setter
    def container_layer(self, layer: Any) -> None:
        self._controller.container_layer = layer

    def set_container_layer(self, layer: Any) -> BaseControl:
        self._controller.set_container_layer(layer)
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

    def _on_controller_resize(self, width: int, height: int) -> None:
        self.on_resize(width, height)

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

    def destroy(self) -> None:
        """Safely release native controller, bindings and listeners."""
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
            self.is_disabled = (kwargs.pop("state") == "disabled")
        if "command" in kwargs:
            self._command = kwargs.pop("command")
        if "widget_class" in kwargs:
            self.widget_class = kwargs.pop("widget_class")
        if "width" in kwargs and "height" in kwargs:
            self.set_geometry_request(kwargs.pop("width"), kwargs.pop("height"))
        elif "width" in kwargs:
            self.set_geometry_request(kwargs.pop("width"), self._logical_h)
        elif "height" in kwargs:
            self.set_geometry_request(self._logical_w, kwargs.pop("height"))
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
        if key == "width":
            return self._logical_w
        if key == "height":
            return self._logical_h
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
