# ⚡ tkblend Showcase & Example Suite

Welcome to the **tkblend** showcase suite. These examples demonstrate the full power of pure Blend2D 2D vector rendering for Python Tkinter — delivering subpixel anti-aliasing, 3-pass separable soft drop shadows, multi-stop linear/radial gradients, dynamic theming, and 60+ FPS zero-copy blitting with **zero TTK dependencies**.

---

## 🕹️ Quick Start: Unified Showcase Hub

The easiest way to explore the entire suite is via the **Unified Showcase Hub**:

```bash
uv run python examples/hub.py
```

<p align="center">
  <img src="../docs/assets/widget_matrix_theming.gif" alt="tkblend Showcase Hub" width="860"/>
</p>

The Showcase Hub includes a modern sidebar allowing you to test every demo inside an embedded live viewport or pop out any demo into a dedicated standalone window with real-time theme switching.

---

## 🚀 Showcase Applications

---

### 1. [Unified Showcase Hub](file:///home/mateusgp/projects/tkblend/examples/hub.py) (`examples/hub.py`)
* **What it demonstrates**: Master interactive flagship hub with sidebar navigation, live embedded previews, standalone launcher, and runtime theme switcher across all 13+ presets.
```bash
uv run python examples/hub.py
```

---

### 2. [Analytics & Telemetry Dashboard](file:///home/mateusgp/projects/tkblend/examples/analytics_dashboard.py) (`examples/analytics_dashboard.py`)
* **What it demonstrates**: Production-grade SaaS and telemetry dashboard with live data streaming, circular gauges, sparklines, Bezier throughput curves, and incident data grids.
```bash
uv run python examples/analytics_dashboard.py
```

---

### 3. [Multimedia & Studio Workstation](file:///home/mateusgp/projects/tkblend/examples/multimedia_dashboard.py) (`examples/multimedia_dashboard.py`)
* **What it demonstrates**: Real-time 48-band audio spectrum analyzer (RTA), oscilloscope waveform, stereo VU meters with LED & gradient modes, playback transport controls, and session playlist manager.
```bash
uv run python examples/multimedia_dashboard.py
```

---

### 4. [Vector File Explorer](file:///home/mateusgp/projects/tkblend/examples/file_explorer.py) (`examples/file_explorer.py`)
* **What it demonstrates**: Full-featured 3-pane modern file manager with Quick Access favorites, path navigation entry, live search filtering, sortable file metadata table, and text/code snippet preview.
```bash
uv run python examples/file_explorer.py
```

---

### 5. [60 FPS Real-Time Engine Lab](file:///home/mateusgp/projects/tkblend/examples/realtime_visualizer.py) (`examples/realtime_visualizer.py`)
* **What it demonstrates**: Extreme rendering speed and zero-copy blitting stressing high frame rates across particle swarm physics, neon audio spectrum, and harmonic Lissajous curves.
```bash
uv run python examples/realtime_visualizer.py
```

---

### 6. [Custom Vector Widget Cookbook](file:///home/mateusgp/projects/tkblend/examples/custom_widget_cookbook.py) (`examples/custom_widget_cookbook.py`)
* **What it demonstrates**: Developer architectural reference guide for creating custom zero-TTK vector widgets by subclassing `BaseControl` (Radar Chart, Speedometer Gauge, Step Progress Bar).
```bash
uv run python examples/custom_widget_cookbook.py
```

---

### 7. [Icons & Advanced Typography Demo](file:///home/mateusgp/projects/tkblend/examples/icons_and_typography_demo.py) (`examples/icons_and_typography_demo.py`)
* **What it demonstrates**: Font Awesome 6 and Lucide vector icon integration, antialiased typography, text metrics, and code boxes.
```bash
uv run python examples/icons_and_typography_demo.py
```

---

### 8. [Canvas Studio & Vector Lab](file:///home/mateusgp/projects/tkblend/examples/canvas_studio.py) (`examples/canvas_studio.py`)
* **What it demonstrates**: Deep dive into `BlendCanvas` and `Surface` vector graphics capabilities with Bezier paths, multi-stop gradients, composition blend modes, and drop shadows.
```bash
uv run python examples/canvas_studio.py
```

---

## 🏗️ Architectural Highlights ("The New Ways")

* **Zero TTK Dependencies**: Pure `BaseControl` subclasses with native Blend2D zero-copy blitting directly into Tk window drawables.
* **Transparent Frame Protocol**: Seamless borderless container integration with zero background flickering (`super().__init__(..., background="")`).
* **Dynamic Theming (13+ Palettes)**: Instant runtime theme transitions with compound container `.bg_color` cascade recursion across `DARK`, `LIGHT`, `CATPPUCCIN_MOCHA`, `TOKYO_NIGHT`, `CYBERPUNK`, `DRACULA`, `EMERALD_FOREST`, `NORD`, `SUNSET_AMBER`, `MONOKAI_PRO`, `SOLARIZED_DARK`, and `SOLARIZED_LIGHT`.
* **High-DPI Coordinate Scaling**: DPI-aware layout, border, geometry, and font metrics via `ScalingTracker`.

