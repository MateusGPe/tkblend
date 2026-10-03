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
                # Query Tk scaling (72 points per inch standard base)
                scale = float(widget.tk.call("tk", "scaling"))
                factor = scale / 1.3333333333333333
                if factor > 0.1:
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
        width: int = 100,
        height: int = 30,
        parent_bg: Optional[ColorLike] = None,
        cursor: Optional[str] = None,
        takefocus: bool = True,
        state: str = "normal",
        **kwargs,
    ):
        self._logical_w = int(width)
        self._logical_h = int(height)
        self._explicit_parent_bg = parent_bg
        self._state_str = state
        self._takefocus = takefocus
        self._cursor_pref = cursor
        self._active_animations: Dict[str, Tuple[int, Any]] = {}
        self._scale_factor = ScalingTracker.get_scaling_factor(master)
        self._idle_redraw_id: Optional[str] = None

        # Resolve initial theme palette & background
        self._palette = get_theme()
        resolved_bg = (
            resolve_color_failsafe(parent_bg, palette=self._palette)
            if parent_bg is not None
            else resolve_ancestor_bg(master, self._palette)
        )
        self._resolved_parent_bg = resolved_bg
        tk_bg = to_tk_hex(resolved_bg, fallback="#100e14" if self._palette.dark_mode else "#ffffff")

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
            cursor=cursor or "",
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
            parent_bg=self._resolved_parent_bg,
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
    def bg_color(self) -> str:
        """Expose background color for container recursion protocols."""
        return self._resolved_parent_bg

    def set_parent_bg(self, color: ColorLike, render: bool = True) -> None:
        """Update parent container background color."""
        self._explicit_parent_bg = color
        resolved = resolve_color_failsafe(color, palette=self._palette)
        self._resolved_parent_bg = resolved
        self._controller.parent_bg = resolved
        if render:
            self.request_redraw()

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
        surf = self._controller.surface
        w = surf.width
        h = surf.height
        if w <= 1 or h <= 1:
            return
        surf.clear(self._resolved_parent_bg)
        scale = self.scale_factor
        self.render(surf, self._palette, w, h, scale)
        self._controller.blit_surface(surf)

    # Controller Callbacks
    def _on_controller_paint(self, surf: Surface) -> None:
        w = surf.width
        h = surf.height
        if w <= 1 or h <= 1:
            return
        surf.clear(self._resolved_parent_bg)
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
        if self._explicit_parent_bg is None:
            self._resolved_parent_bg = resolve_ancestor_bg(self.master, pal)
            self._controller.parent_bg = self._resolved_parent_bg
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
            self.request_redraw()

    def _on_tk_map(self, event: tk.Event) -> None:
        if event.widget is self:
            self.request_redraw()

    def _on_tk_destroy(self, event: tk.Event) -> None:
        if event.widget is self:
            if self._idle_redraw_id is not None:
                try:
                    self.after_cancel(self._idle_redraw_id)
                except Exception:
                    pass
                self._idle_redraw_id = None
            remove_theme_listener(self._on_theme_changed)
            self._cancel_all_animations()
            if hasattr(self, "_controller"):
                self._controller.clear_on_paint()
                self._controller.clear_on_state_changed()
                self._controller.clear_on_click()
                self._controller.clear_on_resize()
                if self._controller.is_attached:
                    self._controller.detach()

    def _update_cursor(self) -> None:
        if self.is_disabled:
            try:
                self.configure(cursor="")
            except Exception:
                pass
        else:
            try:
                self.configure(cursor=self._cursor_pref or "")
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
        if "bg" in kwargs or "background" in kwargs:
            bg_val = kwargs.pop("bg", kwargs.pop("background", None))
            if bg_val is not None:
                self.set_parent_bg(bg_val)

        if kwargs:
            return super().configure(**kwargs)
        return None

    config = configure

    def cget(self, key: str) -> Any:
        if key == "state":
            return self._state_str
        if key == "width":
            return self._logical_w
        if key == "height":
            return self._logical_h
        if key in ("bg", "background"):
            return self._resolved_parent_bg
        if key == "cursor":
            return self._cursor_pref
        return super().cget(key)

    __getitem__ = cget
