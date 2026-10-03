---
name: blend2d-vector-widgets
description: Architecture guide and reference patterns for developing pure Blend2D surface-based vector widgets in tkblend with zero TTK dependencies.
---

# Blend2D Vector Widgets Architecture & Development Guide

This skill provides the architectural foundation, development workflow, and widget design patterns for `tkblend`'s pure surface-based vector UI components.

## Core Architectural Principles

1. **Zero TTK Dependencies**:
   - `tkblend` does not use the Tcl/Tk TTK theme engine (`Ttk_RegisterElement`, `Ttk_RegisterTheme`, `ttk.Style`).
   - All interactive components are self-contained vector widgets powered by Blend2D C++ rendering directly into Tk window drawables via zero-copy blitting without intermediate `PhotoImage` allocations.

2. **DPI-Aware Coordinate Scaling**:
   - Always route dimensions and layout coordinates through `ScalingTracker`:
     ```python
     scale = ScalingTracker.get_scaling_factor(master)
     widget_w = int(logical_w * scale)
     widget_h = int(logical_h * scale)
     ```
   - Auto-activates process-level high-DPI awareness on Windows and detects scaling factors on macOS / Linux.

3. **BaseControl & NativeController Lifecycle (`tkblend.widgets.BaseControl`)**:
   - Subclass `BaseControl`, which wraps `tk.Frame` with an integrated `NativeWidgetController` for zero-copy direct drawable blitting.
   - **Transparent Frame Protocol**: Always initialize `super().__init__(..., background="")` so Tk's internal `DisplayFrame` has `framePtr->border == NULL` and does not erase Blend2D vector surfaces on Expose/Configure events.
   - Implement `render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None`:
     1. Vector shapes, paths, text, or drop shadows are drawn into `surf`.
     2. Background clearing is handled via `surf.clear(self._resolved_parent_bg)`.
   - Request redraws via `self.request_redraw()`, which schedules non-blocking idle execution through `self.after_idle(self._execute_idle_redraw)`.
   - **Direct C++ Hardware Blits on Expose / MapNotify**: `NativeWidgetController` handles X11 `Expose`, `MapNotify`, and `VisibilityNotify` events by immediately executing `blit_active_surface()` in C++ from the backing surface buffer.

4. **Dynamic Theming with `tkblend.theme`**:
   - Query `get_theme()` for semantic colors: `bg`, `fg`, `primary`, `secondary`, `accent`, `card_bg`, `card_border`, `track_bg`, `thumb_color`.
   - `BaseControl` automatically registers with `add_theme_listener` and re-renders on `set_theme("light" | "dark")`.
   - **Avoid Static Color Locking**: Do not pass explicit theme colors in constructors unless a permanent user override is intended. Let child widgets dynamically inherit background via `_resolve_default_bg(master, palette)`.
   - **Compound Container Protocol (`.bg_color`)**: Any compound container (`ScrollableFrame`, `Tabview`, `Table`, `TextBox`, `Frame`, `Card`) must expose a `.bg_color` property returning its active inner surface fill color so `cascade_bg_to_children()` can properly recurse.
   - **Subcomponent Cascade in `_on_theme_changed`**:
     Compound widgets must update their internal frames, canvas viewports, and vector scrollbars with `set_parent_bg()` and call `cascade_bg_to_children(self, inner_bg)`.
   - **Startup UI Palette Injection**:
     Call `self._on_theme_changed(pal)` or `tb.cascade_bg_to_children(self, pal.bg)` right after `_build_ui()` so standard helper `tk.Frame`s adapt immediately to theme card colors on first launch.

## Developing a Native Vector Widget

Follow this template for creating custom vector components with `BaseControl`:

```python
import tkinter as tk
from typing import Optional
from tkblend.widgets import BaseControl
from tkblend.theme import Palette, get_theme
from tkblend.surface import Surface, ColorLike

class CustomGauge(BaseControl):
    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 100,
        value: float = 50.0,
        color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._value = value
        self._color = color
        super().__init__(master=master, width=size, height=size, parent_bg=parent_bg, **kwargs)

    def set_value(self, val: float) -> None:
        self._value = max(0.0, min(100.0, float(val)))
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        cx = width / 2.0
        cy = height / 2.0
        r = min(cx, cy) - 6.0 * s
        
        # Draw track and progress
        active_color = self._color or pal.primary
        surf.stroke_circle(cx, cy, r, pal.track_bg, stroke_width=6.0 * s)
        surf.fill_circle(cx, cy, r * (self._value / 100.0), active_color)
```

## C++ Native Extension Concurrency & Memory Safety

1. **GIL Management & Event Loop Thread Safety**:
   - Never invoke raw `PyGILState_Ensure()` / `PyGILState_Release()` during `_tkinter` `Tcl_Eval` execution; use `nb::gil_scoped_acquire` in C++ event callbacks.
   - Python-initiated redraws must be scheduled via `widget.after_idle()`.
   - `Surface::resize()` runs under `nb::call_guard<nb::gil_scoped_release>()`.
   - All buffer acquisitions (`SurfaceBufferObject`, `Surface::get_buffer()`) must register via `Surface::acquire_buffer_view()` / `Surface::release_buffer_view()` under `Surface::mutex_`.
   - `active_buffers_` acts as a guard preventing resize and subsequent use-after-free while active memoryviews exist.

2. **Display List & Direct Drawing Parity**:
   - Every operation in `DrawBatch` (`DrawOp`) must maintain 1:1 parity with direct `Surface` calls (including all shadow blur, spread, offset-x, offset-y, and color arguments).
   - Any new high-level drawing primitive added to `Surface` must also be added with identical arguments to `DrawBatch`.

3. **Cross-Platform Native Hygiene**:
   - Objective-C++ sources (macOS window shaping) must be pinned to `-fobjc-arc` and treat native view handles as borrowed references.
   - Dynamic asset and font resolution must never use hardcoded user paths; dynamic `$HOME` / `$WINDIR` lookups must be used.
   - Global native types (e.g. `SurfaceBufferType`) must be initialized via `std::call_once` or module init.
