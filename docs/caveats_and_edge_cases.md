# Caveats, Edge Cases & Troubleshooting

This document provides a technical catalog of architectural constraints, platform-specific differences, and widget-level edge cases in **tkblend**, structured as **Symptom**, **Root Cause**, and **Workaround / Best Practice**.

---

## 📑 Table of Contents

1. [Platform & Windowing Subsystems](#1-platform--windowing-subsystems)
   - [Unmapped Window IDs on Linux / Wayland](#unmapped-window-ids-on-linux--wayland)
   - [Cross-Platform Mouse Wheel Delta Normalization](#cross-platform-mouse-wheel-delta-normalization)
   - [High-DPI Per-Monitor Awareness on Windows](#high-dpi-per-monitor-awareness-on-windows)
   - [macOS Cocoa Blitting Limitations](#macos-cocoa-blitting-limitations)
2. [Lifecycle, Threading & Memory Management](#2-lifecycle-threading--memory-management)
   - [Tkinter Main Thread UI Concurrency](#tkinter-main-thread-ui-concurrency)
   - [Buffer View Locking During Window Resizes](#buffer-view-locking-during-window-resizes)
   - [Widget Destruction and Native Controller Unbinding](#widget-destruction-and-native-controller-unbinding)
3. [Vector Rendering, Fonts & Alpha Blending](#3-vector-rendering-fonts--alpha-blending)
   - [Pseudo-Transparency vs True Window Alpha](#pseudo-transparency-vs-true-window-alpha)
   - [Complex Script Shaping & HarfBuzz Absence](#complex-script-shaping--harfbuzz-absence)
   - [Glyph Fallback Modes for Missing Characters](#glyph-fallback-modes-for-missing-characters)
4. [Widget-Specific Gotchas](#4-widget-specific-gotchas)
   - [Card Layout: Packing Directly into Card vs Card.content](#card-layout-packing-directly-into-card-vs-cardcontent)
   - [Slider Label Width Shift at Boundary Values](#slider-label-width-shift-at-boundary-values)
   - [Slider Zero-Range Edge Case (min == max)](#slider-zero-range-edge-case-min--max)
   - [Dynamic Theme Propagation to Custom Vector Items](#dynamic-theme-propagation-to-custom-vector-items)

---

## 1. Platform & Windowing Subsystems

### Unmapped Window IDs on Linux / Wayland

* **Symptom**: Calling native controller blits or low-level X11 surface hooks immediately after widget creation produces a `BadWindow` protocol error or a null window identifier (`winfo_id() == 0`).
* **Root Cause**: On X11 and XWayland, Tk allocates native window handles lazily. A widget's underlying window handle does not exist until the window is mapped and displayed on screen by the window manager.
* **Workaround / Best Practice**: Call `root.update_idletasks()` or listen for the `<Map>` event before invoking operations that require a valid OS window handle:

```python
import tkinter as tk
from tkblend import NativeController

root = tk.Tk()
canvas = tk.Canvas(root, width=400, height=300)
canvas.pack()

# Force Tk to process geometry management and allocate OS window ID
root.update_idletasks()

# Safe to acquire winfo_id() now
controller = NativeController(canvas.winfo_id())
```

---

### Cross-Platform Mouse Wheel Delta Normalization

* **Symptom**: Scrolling a `ScrollableFrame` or `Table` works smoothly on Windows, moves in reverse or jumps erratically on macOS, or fails to respond at all on Linux X11.
* **Root Cause**: Different OS platforms report mouse wheel movements differently in Tkinter:
  - **Windows**: Dispatches `<MouseWheel>` with `event.delta` multiples of `±120`.
  - **macOS**: Dispatches `<MouseWheel>` with `event.delta` values typically around `±1` or `±5` (with inverted signs depending on natural scrolling settings).
  - **Linux (X11)**: Does not use `event.delta`; instead, it fires discrete `<Button-4>` (scroll up) and `<Button-5>` (scroll down) events.
* **Workaround / Best Practice**: Normalize scroll events using the unified handler pattern implemented in tkblend widgets:

```python
def handle_scroll(widget, event):
    if event.num == 4:
        # Linux scroll up
        delta = -1
    elif event.num == 5:
        # Linux scroll down
        delta = 1
    elif hasattr(event, "delta") and event.delta != 0:
        # Windows / macOS
        delta = -int(event.delta / 120) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1)
    else:
        return
    widget.yview_scroll(delta, "units")

# Universal binding pattern:
widget.bind("<MouseWheel>", lambda e: handle_scroll(widget, e))
widget.bind("<Button-4>", lambda e: handle_scroll(widget, e))
widget.bind("<Button-5>", lambda e: handle_scroll(widget, e))
```

---

### High-DPI Per-Monitor Awareness on Windows

* **Symptom**: Vector widgets appear tiny, blurry, or misaligned on high-DPI displays (such as 4K monitors or 150% scaling laptops) under Windows.
* **Root Cause**: By default, Python executables on Windows run without DPI awareness unless explicitly declared in an application manifest or configured at process startup. Windows applies bitmap scaling ("DPI virtualization") which degrades subpixel vector sharpness.
* **Workaround / Best Practice**: Declare per-monitor DPI awareness before creating the root Tk instance:

```python
import sys
import tkinter as tk

if sys.platform == "win32":
    try:
        import ctypes
        # Set per-monitor DPI awareness (v2)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

root = tk.Tk()
# tkblend ScalingTracker will now automatically read true physical display metrics
```

---

### macOS Cocoa Blitting Limitations

* **Symptom**: Direct native blitting onto a Cocoa `NSView` does not support direct X11 shared memory protocols.
* **Root Cause**: macOS uses a display server architecture (Quartz / Metal / Cocoa) that restricts uncoordinated direct memory writes into child window views.
* **Workaround / Best Practice**: tkblend automatically switches to `Tk_PhotoPutBlock` blitting mode when direct drawable blitting is unsupported on the platform. The vector rasterization still runs via Blend2D in C++ without PIL intermediate buffers, retaining smooth subpixel quality.

---

## 2. Lifecycle, Threading & Memory Management

### Tkinter Main Thread UI Concurrency

* **Symptom**: Calling `widget.update()`, altering vector parameters, or triggering repaints from a background thread causes crashes, random segmentation faults, or `Tcl_AsyncDelete` errors.
* **Root Cause**: Tcl/Tk is inherently single-threaded. Although Blend2D path rasterization releases the Python GIL during heavy rendering passes, all Tkinter widget interactions and geometry allocations must be executed on the thread running the Tk main event loop.
* **Workaround / Best Practice**: Offload compute or IO tasks to background worker threads, and schedule widget updates onto the main thread using `root.after()`:

```python
import threading
import time
import tkinter as tk
from tkblend import Progressbar

root = tk.Tk()
pbar = Progressbar(root, width=300, height=12)
pbar.pack(pady=20)

def worker_task():
    # Long-running background computation
    for i in range(101):
        # Dispatch UI update safely to the Tk event loop
        root.after(0, pbar.set, float(i))
        time.sleep(0.02)

threading.Thread(target=worker_task, daemon=True).start()
root.mainloop()
```

---

### Buffer View Locking During Window Resizes

* **Symptom**: `Surface::resize()` blocks or raises an exception if an active buffer view is being held by an external consumer (such as a NumPy or PyTorch image transfer).
* **Root Cause**: To prevent dangling pointers and race conditions, `Surface.acquire_buffer_view()` increments an atomic reference counter protected by a mutex. Reallocating the backing pixel buffer while another thread holds a raw pointer is prohibited.
* **Workaround / Best Practice**: Always use the buffer view within a controlled scope and release it promptly:

```python
from tkblend import Surface

surface = Surface(800, 600)

# Recommended: Release view immediately after copying or processing
view_info = surface.acquire_buffer_view()
try:
    # Process or copy raw memory bytes
    raw_bytes = bytes(view_info.ptr[:view_info.size])
finally:
    surface.release_buffer_view()

# Now safe for surface.resize() or window resize events
```

---

### Widget Destruction and Native Controller Unbinding

* **Symptom**: Closing a top-level window or dynamically destroying a tkblend widget intermittently raises native memory access violations during event delivery.
* **Root Cause**: If a widget's underlying `Tk_Window` is destroyed while a `NativeController` hook or draw timer is still active, the native event loop may attempt to dispatch events to an invalidated handle.
* **Workaround / Best Practice**: Always clean up timers and call widget destroy handlers properly. In custom widgets subclassing `BaseControl`, `destroy()` unbinds the native controller automatically:

```python
from tkblend.widgets.base import BaseControl

class CustomVectorWidget(BaseControl):
    def destroy(self):
        # BaseControl handles native controller unbinding and timer cancellation
        super().destroy()
```

---

## 3. Vector Rendering, Fonts & Alpha Blending

### Pseudo-Transparency vs True Window Alpha

* **Symptom**: Rounded corners of a `Card` or vector button show unexpected dark or bright square artifacts instead of blending into the parent background.
* **Root Cause**: Standard Tkinter does not support true per-pixel alpha channels across overlapping native window borders. Vector widgets achieve rounded corners via **pseudo-transparency**: blending anti-aliased edge pixels against the detected background color of their parent widget (`resolve_ancestor_bg()`).
* **Workaround / Best Practice**: When placing vector widgets inside a container with a custom background, ensure the container's background is explicitly configured or inherited:

```python
import tkinter as tk
from tkblend import Card, Button

root = tk.Tk()
root.configure(bg="#1e1e24")

# Card automatically samples parent bg "#1e1e24" to blend shadow and rounded edges
card = Card(root, width=320, height=180)
card.pack(padx=20, pady=20)

# When placing custom Tkinter frames inside, match the background
content_frame = tk.Frame(card.content, bg=card.get_color("card-bg"))
content_frame.pack(fill="both", expand=True)
```

---

### Complex Script Shaping & HarfBuzz Absence

* **Symptom**: Arabic text, complex Indic scripts (Devanagari, Tamil), or connected emoji clusters display with disconnected or incorrectly ordered glyphs.
* **Root Cause**: Blend2D includes a high-performance vector font engine with OpenType kerning and glyph metrics, but does not embed a full complex text shaping engine (such as HarfBuzz). Right-to-left (RTL) ligature contextual substitution is not supported natively.
* **Workaround / Best Practice**: For applications requiring complex non-Latin scripts or bidirectional text, use standard Tkinter `Label` widgets (which utilize the OS native text shaping engine) embedded within `Card.content`.

---

### Glyph Fallback Modes for Missing Characters

* **Symptom**: Characters missing from the active font display as empty rectangles ("tofu") or trigger runtime warnings in the console.
* **Root Cause**: Blend2D requires glyph outlines to rasterize vector text. When a character is absent from the configured font, the fallback engine resolves replacement characters based on the active fallback mode.
* **Workaround / Best Practice**: Configure the glyph fallback mode via `set_glyph_fallback_mode()` or register a custom character mapper:

```python
from tkblend.font import set_glyph_fallback_mode, register_glyph_fallback_hook

# Choose fallback policy: "silent" (clean UI), "warn" (log missing glyphs), or "strict"
set_glyph_fallback_mode("silent")

# Optional: Register a custom mapper for special symbols or emojis
def emoji_fallback(char: str):
    if char == "⚡":
        return "[*]"
    return None

register_glyph_fallback_hook(emoji_fallback)
```

---

## 4. Widget-Specific Gotchas

### Card Layout: Packing Directly into Card vs Card.content

* **Symptom**: Child widgets placed inside a `Card` overwrite the card's rounded borders, obscure the drop shadow, or break the internal padding.
* **Root Cause**: `Card` is a composite container composed of an underlying vector drawing canvas (which draws the box-blur shadow and rounded background) and an internal positioning frame (`card.content`).
* **Workaround / Best Practice**: Always place child widgets into `card.content`, never directly into `card`:

```python
from tkblend import Card, Button, Label

card = Card(root, width=300, height=200)
card.pack(padx=16, pady=16)

# ❌ INCORRECT: btn = Button(card, text="Click")
# ✅ CORRECT: Place children inside card.content
lbl = Label(card.content, text="Profile", font=("sans-serif", 13, "bold"))
lbl.pack(pady=(12, 6))

btn = Button(card.content, text="Save Changes")
btn.pack(pady=6)
```

---

### Slider Label Width Shift at Boundary Values

* **Symptom**: Dragging a slider to `0%` or `100%` causes the slider track or adjacent controls to visibly jump horizontally.
* **Root Cause**: If the accompanying text label displaying the numerical percentage does not have a fixed character `width`, strings of varying length (`0%` [2 chars] vs `100%` [4 chars]) cause the layout manager (`pack(side="right")` or `grid()`) to resize the label, shifting the slider.
* **Workaround / Best Practice**: Assign a fixed character `width` to value labels beside vector sliders:

```python
import tkinter as tk
from tkblend import Slider, Label

row = tk.Frame(root)
row.pack(fill="x", padx=16, pady=8)

# Fixed width of 5 characters prevents layout jitter
val_lbl = Label(row, text="50%", width=5, anchor="e")
val_lbl.pack(side="right")

slider = Slider(row, value=50, command=lambda v: val_lbl.configure(text=f"{int(v)}%"))
slider.pack(side="left", fill="x", expand=True)
```

---

### Slider Zero-Range Edge Case (min == max)

* **Symptom**: Setting `min_value` equal to `max_value` on a `Slider` or `RangeSlider` causes a division-by-zero error or renders the thumb off-screen.
* **Root Cause**: Slider coordinate mapping calculates thumb position using `(value - min_value) / (max_value - min_value)`. When `min_value == max_value`, the interval length is zero.
* **Workaround / Best Practice**: Validate that `max_value > min_value` before updating slider boundaries:

```python
def update_slider_limits(slider, new_min: float, new_max: float):
    # Guard against invalid or collapsed intervals
    if new_max <= new_min:
        new_max = new_min + 1.0  # Safe minimum delta
    slider.configure(min_value=new_min, max_value=new_max)
```

---

### Dynamic Theme Propagation to Custom Vector Items

* **Symptom**: Calling `set_theme("dark")` updates built-in tkblend widgets, but custom Blend2D canvas drawings retain their old hardcoded colors.
* **Root Cause**: Built-in widgets subscribe to theme notifications via `add_theme_listener()`. Custom vector drawing code must also listen for theme change events to invalidate and repaint its display list.
* **Workaround / Best Practice**: Register custom canvas redraw callbacks with `add_theme_listener`:

```python
from tkblend import add_theme_listener, get_theme

def on_theme_change(new_theme_name: str):
    palette = get_theme()
    # Update custom drawing colors and trigger repaint
    redraw_custom_graphics(palette)

add_theme_listener(on_theme_change)
```
