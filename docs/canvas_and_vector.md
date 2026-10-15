# Canvas & Custom Vector Drawing

**tkblend** provides access to Blend2D's 2D vector rasterizer from Python Tkinter. You can draw immediate-mode graphics using `NativeBlitCanvas`, or author custom reusable UI controls by subclassing `BaseControl`.

---

## The `NativeBlitCanvas` Immediate-Mode Canvas

`NativeBlitCanvas` is a drawing widget backed by a C++ `NativeController`. Whenever a repaint is requested, it invokes an `on_paint(surf: Surface)` callback:

```python
import tkinter as tk
from tkblend import NativeBlitCanvas, Surface, LinearGradient

root = tk.Tk()
root.title("Blend2D Canvas")
root.geometry("640x480")

def draw_frame(surf: Surface):
    w, h = surf.width, surf.height
    
    # Clear canvas background
    surf.clear("#0f111a")
    
    # Multi-stop linear gradient
    grad = LinearGradient(0, 0, w, h)
    grad.add_stop(0.0, "#00c6ff")
    grad.add_stop(0.5, "#0072ff")
    grad.add_stop(1.0, "#7928ca")
    
    # Draw rounded vector card
    surf.fill_rounded_rect(40, 40, w - 80, h - 80, rx=20, ry=20, fill=grad)
    
    # Draw antialiased vector text
    surf.draw_text("Blend2D Vector Canvas", 70, 90, font_size=18, color="#ffffff")

canvas = NativeBlitCanvas(root, width=640, height=480, on_paint=draw_frame)
canvas.pack(fill="both", expand=True)

root.mainloop()
```

---

## Vector Drawing Primitives

### 1. Rectangles & Rounded Rectangles
```python
# Solid fill
surf.fill_rect(x=20, y=20, w=100, h=60, fill="#2b334a")

# Outline stroke
surf.stroke_rect(x=20, y=20, w=100, h=60, stroke="#61afef", stroke_width=2.0)

# Rounded rectangle with gradient or color
surf.fill_rounded_rect(x=140, y=20, w=120, h=60, rx=12, ry=12, fill="#98c379")
surf.stroke_rounded_rect(x=140, y=20, w=120, h=60, rx=12, ry=12, stroke="#e5c07b", stroke_width=1.5)
```

---

### 2. Circles, Ellipses & Arcs
```python
# Circle fill and outline
surf.fill_circle(cx=80, cy=150, r=40, fill="#e06c75")
surf.stroke_circle(cx=80, cy=150, r=40, stroke="#ffffff", stroke_width=2.0)

# Ellipse
surf.fill_ellipse(cx=220, cy=150, rx=60, ry=35, fill="#d19a66")

# Radial Arc (Gauge / Speedometer)
surf.stroke_arc(cx=350, cy=150, r=40, start_angle=-135.0, sweep_angle=270.0, stroke="#56b6c2", stroke_width=6.0)
```

---

### 3. Arbitrary Vector Paths & Bézier Curves
Construct complex 2D shapes with `Path`:

```python
from tkblend import Path

path = Path()
path.move_to(50, 250)
# Cubic Bézier curve: control point 1, control point 2, end point
path.cubic_to(120, 180, 200, 320, 280, 250)
# Quadratic Bézier curve
path.quad_to(320, 220, 360, 250)
path.close()

# Stroke or fill the custom path
surf.stroke_path(path, stroke="#c678dd", stroke_width=3.0)
```

---

## Gradients

### Linear Gradients
```python
from tkblend import LinearGradient, EXTEND_PAD, EXTEND_REPEAT, EXTEND_REFLECT

# Coordinates from (x0, y0) to (x1, y1)
grad = LinearGradient(0, 0, 300, 0)
grad.add_stop(0.0, "#ff007f")
grad.add_stop(0.5, "#7928ca")
grad.add_stop(1.0, "#00dfd8")
grad.set_extend_mode(EXTEND_PAD)

surf.fill_rounded_rect(20, 20, 300, 80, rx=10, ry=10, fill=grad)
```

### Radial Gradients
```python
from tkblend import RadialGradient

# Center (cx, cy) and radius r
radial = RadialGradient(150, 150, 80)
radial.add_stop(0.0, "#ffffff")
radial.add_stop(0.7, "#0072ff")
radial.add_stop(1.0, "#00000000")  # Transparent fade

surf.fill_circle(150, 150, 80, fill=radial)
```

---

## Soft Drop Shadows

Blend2D supports multi-pass separable box-blur drop shadows:

```python
# Render a card with a drop shadow
surf.draw_card(
    x=40,
    y=40,
    w=280,
    h=160,
    rx=14,
    ry=14,
    bg_color="#1e1e2e",
    shadow_blur=16.0,
    shadow_spread=0.0,
    shadow_offset_x=0.0,
    shadow_offset_y=6.0,
    shadow_opacity=0.35,
)
```

---

## Display Lists with `DrawBatch`

For scenarios where drawing commands should be recorded once and replayed directly in C++ without Python interpreter overhead on damage/expose events:

```python
from tkblend import DrawBatch

batch = DrawBatch()
batch.fill_rounded_rect(10, 10, 200, 40, 8, 8, "#2e3440")
batch.draw_text("Pre-compiled C++ Vector Batch", 20, 34, font_size=12, color="#eceff4")

# Compile into an immutable native memory structure
compiled_batch = batch.compile()

# Bind directly to NativeController for native replay
canvas.controller.bind_batch(compiled_batch)
```

---

## Authoring Custom Vector Widgets (`BaseControl`)

To create reusable custom widgets, subclass `BaseControl`. It provides DPI scaling, event tracking, theme updates, and background transparency management.

### Example: Speedometer Gauge

```python
import tkinter as tk
from typing import Optional
from tkblend import BaseControl, Palette, Surface, ColorLike

class Speedometer(BaseControl):
    """Custom vector speedometer dial."""

    WIDGET_CLASS = "speedometer"

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 140,
        value: float = 45.0,
        max_value: float = 120.0,
        unit: str = "KM/H",
        **kwargs,
    ):
        self._value = float(value)
        self._max_value = float(max_value)
        self._unit = unit

        super().__init__(
            master=master,
            width=size,
            height=size,
            takefocus=False,
            **kwargs,
        )

    def set_value(self, val: float):
        self._value = max(0.0, min(self._max_value, float(val)))
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float):
        cx = width / 2.0
        cy = height / 2.0
        radius = min(cx, cy) - 12.0 * scale
        
        # 1. Clear background to parent container fill
        surf.clear(self.inner_bg)
        
        # 2. Draw background gauge track (240 degree sweep)
        start_angle = 150.0
        max_sweep = 240.0
        surf.stroke_arc(cx, cy, radius, start_angle, max_sweep, stroke=pal.track_bg, stroke_width=10.0 * scale)
        
        # 3. Draw active speed progress arc
        ratio = self._value / self._max_value
        active_sweep = max_sweep * ratio
        surf.stroke_arc(cx, cy, radius, start_angle, active_sweep, stroke=pal.primary, stroke_width=10.0 * scale)
        
        # 4. Draw central speed readout
        surf.draw_text(f"{int(self._value)}", cx - 18 * scale, cy + 6 * scale, font_size=int(22 * scale), color=pal.fg)
        surf.draw_text(self._unit, cx - 14 * scale, cy + 24 * scale, font_size=int(10 * scale), color=pal.fg_subtle)
```

---

> [!TIP]
> For details on handling pseudo-transparency, font fallback modes for missing glyphs, and buffer view locking safety during surface resizes, see the [Caveats, Edge Cases & Troubleshooting Guide](caveats_and_edge_cases.md).

