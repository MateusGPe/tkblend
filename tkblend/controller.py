"""
Native Blend2D Widget Controller for Tkinter.
Provides high-performance direct blitting and native event sinking for Python-driven rendering.
"""

from __future__ import annotations

import tkinter as tk
import weakref
from typing import Optional, Callable, Any, Union

from tkblend._tkblend import (
    NativeWidgetController as _NativeWidgetController,
    ControllerPseudoState,
    Surface as _NativeSurface,
    SurfaceHandle as _NativeSurfaceHandle,
    Color as _NativeColor,
)
from tkblend.surface import Surface, ColorLike, parse_color
from tkblend.utils.tcl_interp import extract_interp_address


class NativeController:
    """
    High-performance native blitter and event sink for Tkinter widgets.

    Attaches to an existing Tk widget, intercepts native X11/Tk events
    (Expose, Configure, Map, Destroy, Enter/Leave, Focus, ButtonPress/Release),
    manages interactive pseudo-states (Hover, Pressed, Focused), and blits
    Blend2D Surface pixel buffers directly to the Tk window drawable without
    requiring intermediate PhotoImage allocations.
    """

    def __init__(
        self,
        widget: Optional[tk.Misc] = None,
        on_paint: Optional[Callable[[Surface], None]] = None,
        on_state_changed: Optional[Callable[[int, int], None]] = None,
        on_click: Optional[Callable[[int, int, int], None]] = None,
        on_resize: Optional[Callable[[int, int], None]] = None,
        auto_hover: bool = True,
        auto_press: bool = True,
        auto_focus: bool = True,
        parent_bg: Optional[ColorLike] = None,
    ):
        self._native = _NativeWidgetController()
        self._widget_ref: Optional[weakref.ref[tk.Misc]] = None
        self._surface_wrapper: Optional[Surface] = None

        self._on_paint_user = on_paint
        self._on_state_changed_user = on_state_changed
        self._on_click_user = on_click
        self._on_resize_user = on_resize

        self.auto_hover = auto_hover
        self.auto_press = auto_press
        self.auto_focus = auto_focus

        if parent_bg is not None:
            self.parent_bg = parent_bg

        if on_paint is not None:
            self.set_on_paint(on_paint)
        if on_state_changed is not None:
            self.set_on_state_changed(on_state_changed)
        if on_click is not None:
            self.set_on_click(on_click)
        if on_resize is not None:
            self.set_on_resize(on_resize)

        if widget is not None:
            self.attach(widget)

    def attach(self, widget: tk.Misc) -> bool:
        """Attach controller to an existing Tk widget."""
        self._widget_ref = weakref.ref(widget)
        interp_addr = extract_interp_address(widget)
        widget_path = getattr(widget, "_w", str(widget))
        return self._native.attach(interp_addr, widget_path)

    def detach(self) -> None:
        """Detach controller and stop intercepting native events."""
        self._native.detach()
        self._widget_ref = None
        self._surface_wrapper = None

    @property
    def is_attached(self) -> bool:
        return self._native.is_attached

    @property
    def widget(self) -> Optional[tk.Misc]:
        return self._widget_ref() if self._widget_ref is not None else None

    @property
    def widget_path(self) -> str:
        return self._native.widget_path

    @property
    def width(self) -> int:
        return self._native.width

    @property
    def height(self) -> int:
        return self._native.height

    @property
    def surface(self) -> Surface:
        """Access the internal managed Surface."""
        raw_surf = self._native.surface
        if self._surface_wrapper is None or self._surface_wrapper._surface is not raw_surf:
            self._surface_wrapper = Surface(raw_surf, borrowed=True)
        return self._surface_wrapper

    @property
    def has_bound_surface(self) -> bool:
        return self._native.has_bound_surface

    @property
    def bound_surface_id(self) -> int:
        return self._native.bound_surface_id

    def bind_surface(self, surface: Union[Surface, _NativeSurface, _NativeSurfaceHandle, int]) -> None:
        """Bind an external Surface, SurfaceHandle, or surface ID for blitting."""
        if isinstance(surface, Surface):
            self._native.bind_surface(surface.native)
        elif isinstance(surface, _NativeSurface):
            self._native.bind_surface(surface)
        elif isinstance(surface, _NativeSurfaceHandle):
            self._native.bind_surface_handle(surface)
        elif isinstance(surface, int):
            self._native.bind_surface_id(surface)
        else:
            raise TypeError(f"Unsupported surface type: {type(surface)}")

    def unbind_surface(self) -> None:
        """Unbind external surface and revert to internal managed Surface."""
        self._native.unbind_surface()

    def blit_surface(self, surface: Union[Surface, _NativeSurface]) -> None:
        """Immediately blit given surface to the attached widget drawable."""
        if isinstance(surface, Surface):
            self._native.blit_surface(surface.native)
        elif isinstance(surface, _NativeSurface):
            self._native.blit_surface(surface)
        else:
            raise TypeError(f"Unsupported surface type: {type(surface)}")

    def blit_handle(self, handle: _NativeSurfaceHandle) -> None:
        """Immediately blit given SurfaceHandle to the attached widget drawable."""
        self._native.blit_handle(handle)

    def request_redraw(self) -> None:
        """Schedule an idle redraw via Tcl_DoWhenIdle."""
        self._native.request_redraw()

    def paint_and_blit(self) -> None:
        """Synchronously execute on_paint (if any) and blit to the widget."""
        self._native.paint_and_blit()

    def set_geometry_request(self, width: int, height: int) -> None:
        """Request geometric dimensions from Tk geometry manager."""
        self._native.set_geometry_request(int(width), int(height))

    # State properties
    @property
    def state(self) -> int:
        return self._native.state

    @state.setter
    def state(self, val: int) -> None:
        self._native.state = int(val)

    @property
    def is_hovered(self) -> bool:
        return self._native.is_hovered

    @is_hovered.setter
    def is_hovered(self, val: bool) -> None:
        self._native.is_hovered = bool(val)

    @property
    def is_pressed(self) -> bool:
        return self._native.is_pressed

    @is_pressed.setter
    def is_pressed(self, val: bool) -> None:
        self._native.is_pressed = bool(val)

    @property
    def is_focused(self) -> bool:
        return self._native.is_focused

    @is_focused.setter
    def is_focused(self, val: bool) -> None:
        self._native.is_focused = bool(val)

    @property
    def is_disabled(self) -> bool:
        return self._native.is_disabled

    @is_disabled.setter
    def is_disabled(self, val: bool) -> None:
        self._native.is_disabled = bool(val)

    @property
    def is_checked(self) -> bool:
        return self._native.is_checked

    @is_checked.setter
    def is_checked(self, val: bool) -> None:
        self._native.is_checked = bool(val)

    @property
    def auto_hover(self) -> bool:
        return self._native.auto_hover

    @auto_hover.setter
    def auto_hover(self, val: bool) -> None:
        self._native.auto_hover = bool(val)

    @property
    def auto_press(self) -> bool:
        return self._native.auto_press

    @auto_press.setter
    def auto_press(self, val: bool) -> None:
        self._native.auto_press = bool(val)

    @property
    def auto_focus(self) -> bool:
        return self._native.auto_focus

    @auto_focus.setter
    def auto_focus(self, val: bool) -> None:
        self._native.auto_focus = bool(val)

    @property
    def parent_bg(self) -> _NativeColor:
        return self._native.parent_bg

    @parent_bg.setter
    def parent_bg(self, color: ColorLike) -> None:
        parsed = parse_color(color)
        self._native.parent_bg = parsed

    # Python Callbacks with Weak References to prevent cycles
    def set_on_paint(self, callback: Callable[[Surface], None]) -> None:
        self._on_paint_user = callback
        if hasattr(callback, "__self__"):
            obj_ref = weakref.ref(callback.__self__)
            func = callback.__func__
            def _thunk(raw_surf):
                obj = obj_ref()
                if obj is not None:
                    surf = Surface(raw_surf, borrowed=True)
                    func(obj, surf)
        else:
            try:
                cb_ref = weakref.ref(callback)
                def _thunk(raw_surf):
                    cb = cb_ref()
                    if cb is not None:
                        surf = Surface(raw_surf, borrowed=True)
                        cb(surf)
            except TypeError:
                def _thunk(raw_surf):
                    surf = Surface(raw_surf, borrowed=True)
                    callback(surf)
        self._native.set_on_paint(_thunk)

    def clear_on_paint(self) -> None:
        self._on_paint_user = None
        self._native.clear_on_paint()

    def set_on_state_changed(self, callback: Callable[[int, int], None]) -> None:
        self._on_state_changed_user = callback
        if hasattr(callback, "__self__"):
            obj_ref = weakref.ref(callback.__self__)
            func = callback.__func__
            def _thunk(new_state: int, old_state: int):
                obj = obj_ref()
                if obj is not None:
                    func(obj, new_state, old_state)
        else:
            try:
                cb_ref = weakref.ref(callback)
                def _thunk(new_state: int, old_state: int):
                    cb = cb_ref()
                    if cb is not None:
                        cb(new_state, old_state)
            except TypeError:
                _thunk = callback
        self._native.set_on_state_changed(_thunk)

    def clear_on_state_changed(self) -> None:
        self._on_state_changed_user = None
        self._native.clear_on_state_changed()

    def set_on_click(self, callback: Callable[[int, int, int], None]) -> None:
        self._on_click_user = callback
        if hasattr(callback, "__self__"):
            obj_ref = weakref.ref(callback.__self__)
            func = callback.__func__
            def _thunk(x: int, y: int, button: int):
                obj = obj_ref()
                if obj is not None:
                    func(obj, x, y, button)
        else:
            try:
                cb_ref = weakref.ref(callback)
                def _thunk(x: int, y: int, button: int):
                    cb = cb_ref()
                    if cb is not None:
                        cb(x, y, button)
            except TypeError:
                _thunk = callback
        self._native.set_on_click(_thunk)

    def clear_on_click(self) -> None:
        self._on_click_user = None
        self._native.clear_on_click()

    def set_on_resize(self, callback: Callable[[int, int], None]) -> None:
        self._on_resize_user = callback
        if hasattr(callback, "__self__"):
            obj_ref = weakref.ref(callback.__self__)
            func = callback.__func__
            def _thunk(width: int, height: int):
                obj = obj_ref()
                if obj is not None:
                    func(obj, width, height)
        else:
            try:
                cb_ref = weakref.ref(callback)
                def _thunk(width: int, height: int):
                    cb = cb_ref()
                    if cb is not None:
                        cb(width, height)
            except TypeError:
                _thunk = callback
        self._native.set_on_resize(_thunk)

    def clear_on_resize(self) -> None:
        self._on_resize_user = None
        self._native.clear_on_resize()


class NativeBlitCanvas(tk.Frame):
    """
    Convenience Frame widget with an integrated NativeController for direct vector blitting.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 200,
        height: int = 100,
        on_paint: Optional[Callable[[Surface], None]] = None,
        **kwargs,
    ):
        super().__init__(master, width=width, height=height, **kwargs)
        self.controller = NativeController(self, on_paint=on_paint)
        self.controller.set_geometry_request(width, height)

    @property
    def surface(self) -> Surface:
        return self.controller.surface

    def request_redraw(self) -> None:
        self.controller.request_redraw()

    def paint_and_blit(self) -> None:
        self.controller.paint_and_blit()
