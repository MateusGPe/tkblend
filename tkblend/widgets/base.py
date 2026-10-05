"""
Base class for pure Blend2D vector widgets powered by NativeController.
Zero TTK dependencies, zero PhotoImage allocations.
"""

from __future__ import annotations

import math
import sys
import tkinter as tk
from typing import Optional, Callable, Any, Union, Dict, Tuple

from tkblend._tkblend import (
    ControllerPseudoState,
    ease,
    spring,
    EasingType,
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
from tkblend.font import FontConfig, parse_font
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
from tkblend.widgets.utils import bind_variable_trace, unbind_variable_trace


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
    Subclasses tk.Frame and delegates rendering and event sinking to NativeController.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = DEFAULT_BASE_WIDTH,
        height: int = DEFAULT_BASE_HEIGHT,
        inner_bg: Optional[ColorLike] = None,
        outer_bg: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        bg_color: Optional[ColorLike] = None,
        cursor: Optional[str] = None,
        takefocus: bool = True,
        state: str = STATE_NORMAL,
        **kwargs,
    ):
        self._logical_w = int(width)
        self._logical_h = int(height)
        self._explicit_outer_bg = outer_bg if outer_bg is not None else parent_bg
        self._explicit_inner_bg = inner_bg if inner_bg is not None else bg_color
        self._explicit_parent_bg = self._explicit_outer_bg
        self._state_str = state
        self._takefocus = takefocus
        self._cursor_pref = cursor
        self._active_animations: Dict[str, Tuple[int, Any]] = {}
        self._scale_factor = ScalingTracker.get_scaling_factor(master)
        self._idle_redraw_id: Optional[str] = None

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
        tk_bg = to_tk_hex(resolved_outer, fallback=FALLBACK_DARK_BG if self._palette.dark_mode else FALLBACK_LIGHT_BG)

        # Compute initial scaled geometry
        scale = self._scale_factor
        init_w = max(1, int(self._logical_w * scale))
        init_h = max(1, int(self._logical_h * scale))

        super().__init__(
            master=master,
            width=init_w,
            height=init_h,
            background="",
            takefocus=1 if takefocus else 0,
            cursor=cursor or CURSOR_DEFAULT,
            **kwargs,
        )

        # Prevent frame geometry propagation from children
        self.pack_propagate(False)
        self.grid_propagate(False)

        # Attach NativeController
        self._controller = NativeController(
            widget=self,
            auto_hover=False,
            auto_press=False,
            auto_focus=False,
            parent_bg=self._resolved_outer_bg,
        )
        self._controller.set_geometry_request(init_w, init_h)

        if self._state_str == "disabled":
            self._controller.is_disabled = True

        # Register dynamic theme updates
        add_theme_listener(self._on_theme_changed)

        # Event bindings
        self.bind("<Enter>", self._on_tk_enter, add="+")
        self.bind("<Leave>", self._on_tk_leave, add="+")
        self.bind("<ButtonPress-1>", self._on_tk_button_press, add="+")
        self.bind("<ButtonRelease-1>", self._on_tk_button_release, add="+")
        self.bind("<FocusIn>", self._on_tk_focus_in, add="+")
        self.bind("<FocusOut>", self._on_tk_focus_out, add="+")
        self.bind("<KeyPress>", self._on_key_press, add="+")
        self.bind("<KeyRelease>", self._on_key_release, add="+")
        self.bind("<Configure>", self._on_tk_configure, add="+")
        self.bind("<Map>", self._on_tk_map, add="+")
        self.bind("<Destroy>", self._on_tk_destroy, add="+")

    def _default_inner_bg(self, pal: Palette) -> str:
        """Subclasses can override to define their default semantic theme inner color."""
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
        """Return the active outer (parent container) background color."""
        return self._resolved_outer_bg

    @outer_bg.setter
    def outer_bg(self, color: ColorLike) -> None:
        self.set_outer_bg(color, render=True, explicit=True)

    @property
    def parent_bg(self) -> str:
        """Deprecated alias for outer_bg."""
        return self._resolved_outer_bg

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

    def set_outer_bg(self, color: ColorLike, render: bool = True, explicit: bool = False) -> None:
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

    def set_parent_bg(self, color: ColorLike, render: bool = True, explicit: bool = False) -> None:
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

    def request_redraw(self) -> None:
        """Request idle redraw of widget surface."""
        if not self.winfo_exists():
            return
        if self._idle_redraw_id is not None:
            return
        try:
            self._idle_redraw_id = self.after_idle(self._execute_idle_redraw)
        except Exception:
            self._idle_redraw_id = None
            self.paint_and_blit()

    def _execute_idle_redraw(self) -> None:
        self._idle_redraw_id = None
        self.paint_and_blit()

    def paint_and_blit(self) -> None:
        """Synchronously render and blit to widget."""
        if not hasattr(self, "_controller") or not self._controller.is_attached:
            return
        if not self.winfo_exists():
            return
        surf = self._controller.surface
        try:
            cur_w = self.winfo_width()
            cur_h = self.winfo_height()
            if cur_w > 1 and cur_h > 1 and (surf.width != cur_w or surf.height != cur_h):
                surf.resize(cur_w, cur_h)
        except Exception:
            pass
        w = surf.width
        h = surf.height
        if w <= 1 or h <= 1:
            return
        surf.clear(self._resolved_outer_bg)
        scale = self.scale_factor
        self.render(surf, self._palette, w, h, scale)
        if self.winfo_ismapped():
            self._controller.blit_surface(surf)

    # Controller Callbacks
    def _on_controller_paint(self, surf: Surface) -> None:
        if not self.winfo_exists() or not self.winfo_ismapped():
            return
        try:
            cur_w = self.winfo_width()
            cur_h = self.winfo_height()
            if cur_w > 1 and cur_h > 1 and (surf.width != cur_w or surf.height != cur_h):
                surf.resize(cur_w, cur_h)
        except Exception:
            pass
        w = surf.width
        h = surf.height
        if w <= 1 or h <= 1:
            return
        surf.clear(self._resolved_outer_bg)
        scale = self.scale_factor
        self.render(surf, self._palette, w, h, scale)

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        """Subclasses override this method to render vector graphics."""
        pass

    def _on_controller_state_changed(self, new_state: int, old_state: int) -> None:
        self.on_state_changed(new_state, old_state)
        self.request_redraw()

    def on_state_changed(self, new_state: int, old_state: int) -> None:
        """Hook called when hover, active, or focused state changes."""
        pass

    def _on_controller_click(self, x: int, y: int, button: int) -> None:
        if not self.is_disabled:
            self.on_click(x, y, button)

    def on_click(self, x: int, y: int, button: int) -> None:
        """Hook called on mouse button release."""
        pass

    def _on_controller_resize(self, width: int, height: int) -> None:
        self.on_resize(width, height)
        self.request_redraw()

    def on_resize(self, width: int, height: int) -> None:
        """Hook called on widget geometry resize."""
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

        self.on_theme_update(pal)
        self.request_redraw()

    def on_theme_update(self, pal: Palette) -> None:
        """Subclasses can override to update color caches on theme change."""
        pass

    # Mouse, Focus & Key Interaction Callbacks
    def _on_tk_enter(self, event: tk.Event) -> None:
        if not self.is_disabled:
            self._controller.is_hovered = True
            self.on_state_changed(self._controller.state, self._controller.state)
            self.request_redraw()

    def _on_tk_leave(self, event: tk.Event) -> None:
        if not self.is_disabled:
            self._controller.is_hovered = False
            self._controller.is_pressed = False
            self.on_state_changed(self._controller.state, self._controller.state)
            self.request_redraw()

    def _on_tk_button_press(self, event: tk.Event) -> None:
        if not self.is_disabled and event.num == 1:
            self._controller.is_pressed = True
            self.on_state_changed(self._controller.state, self._controller.state)
            self.request_redraw()

    def _on_tk_button_release(self, event: tk.Event) -> None:
        if not self.is_disabled and event.num == 1:
            was_pressed = self._controller.is_pressed
            self._controller.is_pressed = False
            self.on_state_changed(self._controller.state, self._controller.state)
            self.request_redraw()
            if was_pressed:
                self.on_click(event.x, event.y, event.num)

    def _on_tk_focus_in(self, event: tk.Event) -> None:
        if not self.is_disabled:
            self._controller.is_focused = True
            self.on_state_changed(self._controller.state, self._controller.state)
            self.request_redraw()

    def _on_tk_focus_out(self, event: tk.Event) -> None:
        self._controller.is_focused = False
        self.on_state_changed(self._controller.state, self._controller.state)
        self.request_redraw()

    def _on_key_press(self, event: tk.Event) -> None:
        if not self.is_disabled:
            self.on_key_press(event)

    def on_key_press(self, event: tk.Event) -> None:
        """Subclasses override for keyboard interaction (Space, Return, Arrows)."""
        pass

    def _on_key_release(self, event: tk.Event) -> None:
        if not self.is_disabled:
            self.on_key_release(event)

    def on_key_release(self, event: tk.Event) -> None:
        pass

    def _on_tk_configure(self, event: tk.Event) -> None:
        if event.widget is self:
            if hasattr(self, "_controller") and self._controller.is_attached:
                surf = self._controller.surface
                if event.width > 1 and event.height > 1 and (surf.width != event.width or surf.height != event.height):
                    surf.resize(event.width, event.height)
                self.on_resize(event.width, event.height)
            self.request_redraw()

    def _on_tk_map(self, event: tk.Event) -> None:
        if event.widget is self:
            self.request_redraw()

    def _on_tk_destroy(self, event: Optional[tk.Event] = None) -> None:
        if event is None or event.widget is self or str(getattr(event, "widget", "")) == str(self):
            if self._idle_redraw_id is not None:
                try:
                    self.after_cancel(self._idle_redraw_id)
                except Exception:
                    pass
                self._idle_redraw_id = None
            try:
                remove_theme_listener(self._on_theme_changed)
            except Exception:
                pass
            self._cancel_all_animations()
            if hasattr(self, "stop") and callable(self.stop):
                try:
                    self.stop()
                except Exception:
                    pass
            if hasattr(self, "_var_trace_id") and hasattr(self, "_variable"):
                try:
                    unbind_variable_trace(self._variable, self._var_trace_id)
                except Exception:
                    pass
                self._var_trace_id = None
                self._variable = None
            if hasattr(self, "_controller"):
                self._controller.clear_on_paint()
                self._controller.clear_on_state_changed()
                self._controller.clear_on_click()
                self._controller.clear_on_resize()
                if self._controller.is_attached:
                    self._controller.detach()

    def destroy(self) -> None:
        """Safely release native controller, bindings, animations and listeners."""
        self._on_tk_destroy(None)
        super().destroy()

    def _update_cursor(self) -> None:
        cur = "" if self.is_disabled else (self._cursor_pref or "")
        try:
            super().configure(cursor=cur)
        except Exception:
            pass

    # Smooth Property Animation Helper
    def animate_property(
        self,
        name: str,
        start_val: float,
        end_val: float,
        duration_ms: int = 150,
        fps: int = 60,
        easing: str = "ease_out",
        on_update: Optional[Callable[[float], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Animate a float property from start_val to end_val with smooth easing curves.
        """
        self.cancel_animation(name)
        if duration_ms <= 0 or math.isclose(start_val, end_val, abs_tol=1e-5):
            if on_update:
                on_update(end_val)
            self.request_redraw()
            if on_complete:
                on_complete()
            return

        total_frames = max(2, int((duration_ms / 1000.0) * fps))
        step_delay_ms = max(10, int(1000 / fps))
        current_frame = 0

        ease_map = {
            "ease_in": EasingType.QuadIn,
            "ease_out": EasingType.QuadOut,
            "ease_in_out": EasingType.QuadInOut,
            "ease_out_cubic": EasingType.CubicOut,
            "linear": EasingType.Linear,
        }
        ease_type = ease_map.get(easing, EasingType.QuadOut)

        def _step():
            nonlocal current_frame
            if not self.winfo_exists():
                return

            current_frame += 1
            progress = min(1.0, current_frame / float(total_frames))
            t = ease(ease_type, progress)
            val = start_val + (end_val - start_val) * t

            if on_update:
                on_update(val)
            self.request_redraw()

            if progress < 1.0:
                timer_id = self.after(step_delay_ms, _step)
                self._active_animations[name] = (timer_id, _step)
            else:
                self._active_animations.pop(name, None)
                if on_complete:
                    on_complete()

        timer_id = self.after(step_delay_ms, _step)
        self._active_animations[name] = (timer_id, _step)

    def cancel_animation(self, name: str) -> None:
        if name in self._active_animations:
            timer_id, _ = self._active_animations.pop(name)
            try:
                self.after_cancel(timer_id)
            except Exception:
                pass

    def _cancel_all_animations(self) -> None:
        for name in list(self._active_animations.keys()):
            self.cancel_animation(name)

    def _apply_configure_option(self, key: str, val: Any) -> bool:
        """Apply a single configuration option to this widget."""
        # 1. Custom subclass handler hook if defined
        if hasattr(self, "_handle_custom_config") and callable(self._handle_custom_config):
            if self._handle_custom_config(key, val):
                return True

        # 2. Check property setters on class
        cls_attr = getattr(type(self), key, None)
        if isinstance(cls_attr, property) and cls_attr.fset is not None:
            setattr(self, key, val)
            return True

        # 3. Handle standard/common vector widget properties
        if key == "text" and hasattr(self, "_text"):
            self._text = str(val) if val is not None else ""
            return True
        if key == "command" and hasattr(self, "_command"):
            self._command = val
            return True
        if key == "icon" and hasattr(self, "_icon"):
            self._icon = val
            return True
        if key == "icon_family" and hasattr(self, "_icon_family"):
            self._icon_family = str(val)
            return True
        if key == "icon_size" and hasattr(self, "_icon_size"):
            self._icon_size = float(val) if val is not None else None
            return True
        if key in ("corner_radius", "radius") and hasattr(self, "_corner_radius"):
            self._corner_radius = float(val)
            return True
        if key == "border_width" and hasattr(self, "_border_width"):
            self._border_width = float(val)
            return True
        if key == "border_color":
            if hasattr(self, "_custom_border_color"):
                self._custom_border_color = val
                return True
            if hasattr(self, "_custom_border"):
                self._custom_border = val
                return True
            if hasattr(self, "_border_color"):
                self._border_color = val
                return True
        if key in ("bg_color", "inner_bg"):
            self.set_inner_bg(val, render=False, explicit=True)
            return True
        if key in ("outer_bg", "parent_bg", "bg", "background"):
            self.set_outer_bg(val, render=False, explicit=True)
            return True
        if key == "fg_color":
            if hasattr(self, "_custom_fg_color"):
                self._custom_fg_color = val
                return True
            if hasattr(self, "_custom_fg"):
                self._custom_fg = val
                return True
            if hasattr(self, "_custom_text_color"):
                self._custom_text_color = val
                return True
            if hasattr(self, "_fg_color"):
                self._fg_color = val
                return True
        if key == "hover_color" and hasattr(self, "_custom_hover_color"):
            self._custom_hover_color = val
            return True
        if key == "pressed_color" and hasattr(self, "_custom_pressed_color"):
            self._custom_pressed_color = val
            return True
        if key == "disabled_color" and hasattr(self, "_custom_disabled_color"):
            self._custom_disabled_color = val
            return True
        if key == "track_color":
            if hasattr(self, "_custom_track_color"):
                self._custom_track_color = val
                return True
            if hasattr(self, "_custom_track"):
                self._custom_track = val
                return True
        if key == "active_color":
            if hasattr(self, "_custom_active_color"):
                self._custom_active_color = val
                return True
            if hasattr(self, "_custom_active"):
                self._custom_active = val
                return True
        if key == "thumb_color":
            if hasattr(self, "_custom_thumb_color"):
                self._custom_thumb_color = val
                return True
            if hasattr(self, "_custom_thumb"):
                self._custom_thumb = val
                return True
        if key == "thumb_border_color" and hasattr(self, "_custom_thumb_border"):
            self._custom_thumb_border = val
            return True
        if key == "thumb_radius" and hasattr(self, "_thumb_radius"):
            self._thumb_radius = float(val)
            return True
        if key == "track_thickness" and hasattr(self, "_track_thickness"):
            self._track_thickness = float(val)
            return True
        if key == "shadow" and hasattr(self, "_shadow"):
            self._shadow = bool(val)
            return True
        if key == "shadow_blur" and hasattr(self, "_shadow_blur"):
            self._shadow_blur = float(val)
            return True
        if key == "shadow_spread" and hasattr(self, "_shadow_spread"):
            self._shadow_spread = float(val)
            return True
        if key == "shadow_offset_x" and hasattr(self, "_shadow_offset_x"):
            self._shadow_offset_x = float(val)
            return True
        if key == "shadow_offset_y" and hasattr(self, "_shadow_offset_y"):
            self._shadow_offset_y = float(val)
            return True
        if key == "shadow_color" and hasattr(self, "_custom_shadow_color"):
            self._custom_shadow_color = val
            return True
        if key == "focus_ring" and hasattr(self, "_focus_ring"):
            self._focus_ring = bool(val)
            return True
        if key == "focus_ring_color" and hasattr(self, "_custom_focus_ring_color"):
            self._custom_focus_ring_color = val
            return True
        if key == "focus_ring_width" and hasattr(self, "_focus_ring_width"):
            self._focus_ring_width = float(val)
            return True
        if key == "animated" and hasattr(self, "_animated"):
            self._animated = bool(val)
            return True
        if key in ("from_", "from") and hasattr(self, "_from"):
            self._from = float(val)
            return True
        if key == "to" and hasattr(self, "_to"):
            self._to = float(val)
            return True
        if key == "number_of_steps" and hasattr(self, "_number_of_steps"):
            self._number_of_steps = val
            return True
        if key == "value":
            if hasattr(self, "set") and callable(self.set):
                try:
                    self.set(val)
                    return True
                except Exception:
                    pass
            if hasattr(self, "_value"):
                self._value = val
                return True
        if key == "variable":
            if hasattr(self, "_variable"):
                if hasattr(self, "_var_trace_id") and self._var_trace_id is not None and self._variable is not None:
                    unbind_variable_trace(self._variable, self._var_trace_id)
                self._variable = val
                if self._variable is not None:
                    try:
                        new_val = self._variable.get()
                        if hasattr(self, "set") and callable(self.set):
                            self.set(new_val)
                        elif hasattr(self, "_value"):
                            self._value = new_val
                    except Exception:
                        pass
                    if hasattr(self, "_on_variable_write") and callable(self._on_variable_write):
                        self._var_trace_id = bind_variable_trace(self._variable, self._on_variable_write)
                else:
                    self._var_trace_id = None
                return True
        if key in ("font", "font_size", "font_family", "bold", "italic", "weight"):
            if hasattr(self, f"_{key}"):
                setattr(self, f"_{key}", val)
            if hasattr(self, "_font_spec") and key == "font":
                self._font_spec = val
            if hasattr(self, "_font_cfg"):
                f_spec = getattr(self, "_font_spec", None) or getattr(self, "_font", None)
                f_sz = getattr(self, "_font_size", None)
                f_b = getattr(self, "_bold", None)
                f_i = getattr(self, "_italic", None)
                self._font_cfg = parse_font(font=f_spec, font_size=f_sz, bold=f_b, italic=f_i)
            return True

        # 4. Generic attribute reflection fallback
        if hasattr(self, f"_{key}"):
            setattr(self, f"_{key}", val)
            return True
        if hasattr(self, f"_custom_{key}"):
            setattr(self, f"_custom_{key}", val)
            return True

        return False

    # Standard Tkinter compatibility overrides
    def configure(self, cnf=None, **kwargs):
        if cnf is None and not kwargs:
            return super().configure()
        if cnf:
            kwargs.update(cnf)

        if "state" in kwargs:
            self.is_disabled = (kwargs.pop("state") == "disabled")
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

        keys_to_remove = []
        for key, val in kwargs.items():
            if self._apply_configure_option(key, val):
                keys_to_remove.append(key)

        for k in keys_to_remove:
            kwargs.pop(k, None)

        self.request_redraw()

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
        if key in ("corner_radius", "radius") and hasattr(self, "_corner_radius"):
            return self._corner_radius
        if key == "text" and hasattr(self, "_text"):
            return self._text
        if key == "value":
            if hasattr(self, "get") and callable(self.get):
                return self.get()
            if hasattr(self, "_value"):
                return self._value

        cls_attr = getattr(type(self), key, None)
        if isinstance(cls_attr, property) and cls_attr.fget is not None:
            return getattr(self, key)

        if hasattr(self, f"_{key}"):
            return getattr(self, f"_{key}")
        if hasattr(self, f"_custom_{key}"):
            return getattr(self, f"_custom_{key}")

        try:
            return super().cget(key)
        except Exception:
            return None

    __getitem__ = cget
