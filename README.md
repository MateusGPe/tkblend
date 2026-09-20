# tkblend

**tkblend** is a high-performance, standalone Python package that embeds **Blend2D** directly into Python and Tkinter. It blits anti-aliased 2D vector graphics directly into Tkinter's native `tk.PhotoImage` display buffer using `Tk_PhotoPutBlock`.

## Features
- **Zero-Allocation Direct Blit**: Directly writes raw 32-bit PRGB pixel scanlines to Tkinter's native `tk.PhotoImage` buffer with zero intermediate PIL copies or Tk Canvas overhead.
- **SIMD-Accelerated 2D Vector Engine**: Full Blend2D rasterization for lines, cubic beziers, circles, ellipses, rounded rectangles, and arbitrary paths.
- **Modern Effects**: Multi-stop linear and radial gradients, $O(1)$ 3-pass separable box/Gaussian blurs, soft drop shadows, and glassmorphic card rendering.
- **Native Typography**: Subpixel-antialiased text layout using Blend2D font engine with automatic cross-platform system font discovery.
- **Modern Tkinter Widgets**: Drop-in widgets (`ModernFrame`, `ModernButton`, `ModernCard`, `ModernProgressBar`, `ModernSlider`, `ModernSwitch`) with smooth hover/press animations and soft elevation shadows.
- **High-Framerate Canvas**: `BlendCanvas` for real-time 60+ FPS vector graphics and custom interactive visual scenes.

## Installation

```bash
pip install .
```

## Quick Start

```python
import tkinter as tk
from tkblend import Surface, Color, Gradient, ModernButton, ModernCard

root = tk.Tk()
root.title("tkblend Demo")
root.geometry("600x400")

card = ModernCard(root, width=320, height=220, rx=16, ry=16,
                  bg_color="#1e1e2e", border_color="#313244",
                  shadow_blur=16.0, shadow_color="#00000088")
card.pack(pady=40)

btn = ModernButton(card, text="Click Me", width=140, height=44,
                   bg_color="#89b4fa", hover_color="#b4befe", text_color="#11111b")
btn.pack(pady=60)

root.mainloop()
```

## Development & Testing

### 1. Build Extension Locally
```bash
# Using python script
python scripts/build.py

# Or using shell script (Linux/macOS)
./scripts/build.sh
```

### 2. Run Test Suite
```bash
# Automatically handles headless displays (xvfb) on Linux
python scripts/run_tests.py -v

# Or via pytest directly
pytest -v
```

### 3. Build Distributions (sdist & wheels)
```bash
# Build both source distribution and binary wheel into dist/
python scripts/build_dist.py

# Build sdist only
python scripts/build_dist.py --sdist-only

# Build wheel only
python scripts/build_dist.py --wheel-only
```

## GitHub Release & CI/CD

This repository includes automated GitHub Actions pipelines:

1. **Continuous Integration (`.github/workflows/ci.yml`)**:
   - Runs unit tests on every `push` and `pull_request` across Ubuntu, macOS (Intel & Apple Silicon), and Windows with Python 3.9–3.13.
2. **Release Workflow (`.github/workflows/release.yml`)**:
   - Automatically builds pure source distributions (`sdist`) and multi-platform native wheels (Linux x86_64/aarch64, macOS x86_64/arm64, Windows AMD64) using `cibuildwheel`.
   - Creates a GitHub Release and attaches all distribution archives when a version tag is pushed:

```bash
git tag v0.1.0
git push origin v0.1.0
```

