---
name: blend2d-vector-widgets
description: Architecture guide and reference patterns for developing pure Blend2D surface-based vector widgets in tkblend with zero TTK dependencies.
---

# Blend2D Vector Widgets Architecture & Development Guide

This skill provides the architectural foundation, development workflow, and widget design patterns for `tkblend`'s pure surface-based vector UI components.

## Core Architectural Principles

1. **Zero TTK Dependencies**:
   - `tkblend` does not use the Tcl/Tk TTK theme engine (`Ttk_RegisterElement`, `Ttk_RegisterTheme`, `ttk.Style`).
   - All interactive components are self-contained vector widgets powered by Blend2D C++ rendering directly into Tkinter `tk.PhotoImage` buffers using zero-copy `Tk_PhotoPutBlock`.

2. **DPI-Aware Coordinate Scaling**:
   - Always route dimensions and layout coordinates through `ScalingTracker`:
     ```python
     scale = ScalingTracker.get_scaling_factor(master)
     widget_w = int(logical_w * scale)
     widget_h = int(logical_h * scale)
     ```
   - Auto-activates process-level high-DPI awareness on Windows and detects scaling factors on macOS / Linux.

3. **ModernWidget Lifecycle (`tkblend.widgets.Widget`)**:
   - Subclass `Widget` (or `ModernWidget`), which wraps `tk.Label` with a backing `tk.PhotoImage` and `Surface`.
   - Implement `render(self) -> None`:
     1. Clear the surface with background (`self._surface.clear(self._parent_bg)`).
     2. Draw vector shapes, paths, gradients, text, or drop shadows (`self._surface.fill_rounded_rect(...)`, `self._surface.draw_text(...)`, etc.).
     3. Blit to the backing photo image: `self._surface.blit(self._photo)`.
   - Event bindings (`<Enter>`, `<Leave>`, `<ButtonPress-1>`, `<ButtonRelease-1>`) manage hover/press states and call `self.render()`.
   - Window resize (`<Configure>`) resizes both the backing `tk.PhotoImage` and `Surface`.

4. **Dynamic Theming with `tkblend.theme`**:
   - Query `get_theme()` for semantic colors: `bg`, `fg`, `primary`, `secondary`, `accent`, `card_bg`, `card_border`, `track_bg`, `thumb_color`.
   - Widgets automatically register with `add_theme_listener` and re-render on `set_theme("light" | "dark")`.
   - **Avoid Static Color Locking**: Do not pass explicit theme colors (like `parent_bg=parent.bg_color` or `bg_color=pal.card_bg`) in constructors unless a permanent user override is intended. Let child widgets dynamically inherit background via `_resolve_default_bg(master, palette)`.
   - **Compound Container Protocol (`.bg_color`)**: Any compound container (`ScrollableFrame`, `Tabview`, `Table`, `TextBox`, `Frame`, `Card`) must expose a `.bg_color` property returning its active inner surface fill color so `cascade_bg_to_children()` can properly recurse.
   - **Subcomponent Cascade in `_on_theme_changed`**:
     Compound widgets must update their internal frames, canvas viewports, and vector scrollbars with `set_parent_bg()` and call `cascade_bg_to_children(self, inner_bg)`.
   - **Startup UI Palette Injection**:
     Call `self._on_theme_changed(pal)` or `tb.cascade_bg_to_children(self, pal.bg)` right after `_build_ui()` so standard helper `tk.Frame`s adapt immediately to theme card colors on first launch.

## Developing a New Vector Widget

Follow this template for creating custom vector components:

```python
import tkinter as tk
from typing import Optional, Callable
from tkblend.widgets import Widget, ScalingTracker
from tkblend.theme import get_theme
from tkblend.surface import ColorLike

class CustomGauge(Widget):
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
        pal = get_theme()
        self._color = color or pal.primary
        super().__init__(master=master, width=size, height=size, bg=parent_bg, **kwargs)

    def set_value(self, val: float) -> None:
        self._value = max(0.0, min(100.0, float(val)))
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)
        s = self._scale
        cx = self._widget_w / 2.0
        cy = self._widget_h / 2.0
        r = min(cx, cy) - 6.0 * s
        
        # Draw track and progress
        pal = get_theme()
        self._surface.stroke_circle(cx, cy, r, pal.track_bg, stroke_width=6.0 * s)
        self._surface.fill_circle(cx, cy, r * (self._value / 100.0), self._color)
        
        # Zero-copy blit to PhotoImage
        self._surface.blit(self._photo)
```
