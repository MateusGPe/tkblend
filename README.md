# tkblend

**tkblend** is a high-performance Blend2D vector graphics addon for **ttkbootstrap** and **Tkinter**. It blits antialiased 2D vector graphics directly into Tkinter's native `tk.PhotoImage` display buffer using zero-copy `Tk_PhotoPutBlock` C++ blitting.

Designed as a lightweight, super-fast graphics addon, **tkblend** gives you hardware-grade 2D rendering, soft shadows, antialiased beziers/curves, multi-stop gradients, and custom canvas widgets (`BlendCanvas`) that automatically synchronize with `ttkbootstrap` themes and bootstyles.

---

## Key Features

- ⚡ **Zero-Copy Direct Blit**: Blits raw 32-bit PRGB pixels straight to `tk.PhotoImage` via `Tk_PhotoPutBlock` with zero intermediate PIL copies or memory allocations.
- 🎨 **Seamless ttkbootstrap Integration**: Pass `ttkbootstrap` color tokens (`"primary"`, `"success"`, `"info"`, `"dark"`, `"bg"`, `"border"`, etc.) directly to any drawing command. Automatically updates when themes switch!
- 🚀 **High-Framerate 60+ FPS Canvas**: `BlendCanvas` widget with immediate-mode callbacks (`on_draw`), convenience drawing methods, and automatic resize/DPI management.
- 📐 **SIMD-Accelerated 2D Vector Engine**: Full Blend2D rasterization for lines, cubic beziers, circles, ellipses, rounded rectangles, and arbitrary paths.
- 🌈 **Modern Effects & Soft Shadows**: Multi-stop linear and radial gradients, $O(1)$ soft drop shadows, and modern card rendering.
- 🔤 **Subpixel Typography**: Antialiased subpixel text layout using Blend2D's native font engine.

---

## Installation

```bash
# Core package
pip install tkblend

# With ttkbootstrap support
pip install "tkblend[ttkbootstrap]"
```

---

## Quick Start with ttkbootstrap

```python
import ttkbootstrap as tb
from tkblend import BlendCanvas, LinearGradient

# Create ttkbootstrap window
app = tb.Window(title="tkblend + ttkbootstrap", themename="darkly", size=(800, 600))

# Define drawing callback
def draw_dashboard(surface):
    w, h = surface.width, surface.height
    
    # 1. Clear with theme background
    surface.clear("bg")
    
    # 2. Modern card with soft drop shadow
    surface.draw_card(
        20, 20, w - 40, h - 40,
        rx=16, ry=16,
        bg_color="dark",
        border_color="border",
        border_width=1.0,
        shadow_blur=16.0,
        shadow_color="#00000055"
    )
    
    # 3. Dynamic multi-stop gradient
    grad = LinearGradient(40, 0, w - 40, 0)
    grad.add_stop(0.0, "primary").add_stop(0.5, "info").add_stop(1.0, "success")
    
    # 4. Antialiased shapes & text
    surface.draw_text("⚡ tkblend Graphics Engine", 44, 55, font_size=16, color="primary")
    surface.fill_rounded_rect(44, 80, w - 88, 8, 4, 4, grad)

# Create BlendCanvas widget
canvas = BlendCanvas(app, width=760, height=560, on_draw=draw_dashboard)
canvas.pack(fill="both", expand=True, padx=20, pady=20)

app.mainloop()
```

---

## Standalone Tkinter Usage

`tkblend` has zero mandatory runtime dependencies beyond standard Python and Tkinter:

```python
import tkinter as tk
from tkblend import BlendCanvas, Surface

root = tk.Tk()
root.geometry("400x300")

def on_draw(s: Surface):
    s.clear("#181825")
    s.draw_card(20, 20, 360, 260, rx=12, ry=12, bg_color="#1e1e2e", shadow_blur=10.0)
    s.fill_circle(200, 150, 50, "#89b4fa")
    s.draw_text("Pure Tkinter + Blend2D", 200, 150, font_size=14, color="#ffffff", align="center")

canvas = BlendCanvas(root, width=400, height=300, on_draw=on_draw)
canvas.pack(fill="both", expand=True)

root.mainloop()
```

---

## Interactive Showcase & Benchmarks

Run the live 60 FPS interactive showcase:
```bash
uv run python examples/showcase.py
```

Run headless and interactive blit benchmarks:
```bash
uv run python examples/benchmark.py
```

---

## Running Tests

```bash
uv run pytest
```

---

## License

MIT License.
