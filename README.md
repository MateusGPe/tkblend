# tkblend

**tkblend** is a high-performance Blend2D pure vector graphics and modern UI component library for **Tkinter**. It renders hardware-grade, antialiased 2D vector graphics directly into Tkinter's native `tk.PhotoImage` display buffer using zero-copy `Tk_PhotoPutBlock` C++ blitting.

Built with zero TTK theme dependencies, **tkblend** provides a complete, modern suite of self-contained vector widgets (`Button`, `Slider`, `RangeSlider`, `Switch`, `ProgressBar`, `CircularProgress`, `Card`, `SegmentedControl`, `TextInput`, `Dropdown`, `SpinBox`, `Badge`, `Avatar`, `Accordion`), High-DPI coordinate scaling, dynamic pure-Python theme switching (Dark & Light modes), and a 60+ FPS immediate-mode canvas (`BlendCanvas`).

---

## Key Features

- ⚡ **Zero-Copy Direct Blit**: Blits raw 32-bit PRGB pixels straight to `tk.PhotoImage` via `Tk_PhotoPutBlock` with zero intermediate PIL copies or memory allocations.
- 🎨 **Pure Vector Modern Widgets**: 15+ rich vector widgets built strictly from scratch with Blend2D:
  - **Interactive**: `Button`, `Switch`, `Checkbox`, `Radio`, `RadioGroup`, `SegmentedControl`
  - **Inputs & Steppers**: `TextInput`, `Dropdown`, `SpinBox`
  - **Sliders & Gauges**: `Slider`, `RangeSlider`, `ProgressBar`, `CircularProgress`
  - **Containers & Display**: `Card`, `Frame`, `Badge`, `Avatar`, `Accordion`
- 🌓 **Dynamic Theme & Palette System**: Pure-Python `Palette` manager with built-in Dark (Catppuccin Mocha) and Light modes, dynamic live theme switching (`set_theme("dark" | "light")`), and automatic widget updates.
- 🖥️ **High-DPI Per-Monitor Awareness**: Integrated `ScalingTracker` handles automatic logical-to-physical pixel conversion across 1080p, 2K, 4K Retina, and mixed-DPI setups.
- 🚀 **High-Framerate 60+ FPS Canvas**: `BlendCanvas` widget with immediate-mode callbacks (`on_draw`), convenience drawing methods, and automatic resize management.
- 📐 **SIMD-Accelerated 2D Vector Engine**: Full Blend2D rasterization for lines, cubic beziers, circles, ellipses, rounded rectangles, and arbitrary paths.
- 🌈 **Modern Effects & Soft Shadows**: Multi-stop linear and radial gradients, fast 3-pass separable box-blur soft drop shadows, and modern card rendering.

---

## Installation

```bash
pip install tkblend
```

Requirements:
- Python 3.9+
- Standard Tkinter / Tcl/Tk 8.6+

---

## Quick Start: Modern Vector Widgets

```python
import tkinter as tk
from tkblend import (
    Button,
    Card,
    Slider,
    Switch,
    ProgressBar,
    CircularProgress,
    Badge,
    set_theme,
)

root = tk.Tk()
root.title("tkblend Vector UI")
root.geometry("480x600")
root.configure(bg="#1e1e2e")

# Elevated card container
card = Card(root, title="Hardware Metrics", width=420, height=520, parent_bg="#1e1e2e")
card.pack(padx=30, pady=30, fill="both", expand=True)

# Radial gauge & linear progress bar
gauge = CircularProgress(card, size=100, value=75.0, unit="%")
gauge.pack(pady=10)

pbar = ProgressBar(card, width=280, value=75.0)
pbar.pack(pady=10)

# Smooth slider updating both gauges
def on_slider(val):
    gauge.set_value(val)
    pbar.set_value(val)

slider = Slider(card, width=280, value=75.0, on_change=on_slider)
slider.pack(pady=10)

# Toggle switch and button
switch = Switch(card, is_on=True)
switch.pack(pady=10)

btn = Button(card, text="Toggle Theme", variant="primary", command=lambda: set_theme("light" if switch.is_on else "dark"))
btn.pack(pady=10)

root.mainloop()
```

---

## Quick Start: 60 FPS Vector Canvas

```python
import tkinter as tk
from tkblend import BlendCanvas, Surface, LinearGradient

root = tk.Tk()
root.title("tkblend Canvas")
root.geometry("600x400")

def on_draw(s: Surface):
    w, h = s.width, s.height
    s.clear("#181825")
    
    # Modern card with soft drop shadow
    s.draw_card(20, 20, w - 40, h - 40, rx=16, ry=16, bg_color="#1e1e2e", shadow_blur=16.0)
    
    # Dynamic multi-stop gradient
    grad = LinearGradient(40, 0, w - 40, 0)
    grad.add_stop(0.0, "#89b4fa").add_stop(0.5, "#cba6f7").add_stop(1.0, "#a6e3a1")
    
    # Antialiased text & shapes
    s.draw_text("⚡ Blend2D Vector Canvas", 44, 60, font_size=16, color="#cdd6f4")
    s.fill_rounded_rect(44, 90, w - 88, 8, 4, 4, grad)

canvas = BlendCanvas(root, width=600, height=400, on_draw=on_draw)
canvas.pack(fill="both", expand=True)

root.mainloop()
```

---

## Showcase Application

Run the comprehensive showcase application to see all 15+ vector widgets and high-framerate fluid canvas rendering in action:

```bash
uv run python examples/showcase_canvas_extended.py
```

---

## License

Apache-2.0
