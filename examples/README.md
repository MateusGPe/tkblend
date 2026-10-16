# ⚡ tkblend Showcase & Example Suite

This directory contains standalone example applications demonstrating various widgets and capabilities of **tkblend** — including pure Blend2D vector controls, separable soft drop shadows, linear/radial gradients, dynamic CSS theming, immediate-mode canvas drawing, real-time physics, audio visualizers, and productivity tools with **zero TTK dependencies**.

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

### 1. [Unified Showcase Hub](hub.py) (`examples/hub.py`)
* **Description**: Master interactive flagship hub with sidebar navigation, live embedded previews, standalone launcher, and runtime theme switcher across all built-in presets.
```bash
uv run python examples/hub.py
```

---

### 2. [Analytics & Telemetry Dashboard](analytics_dashboard.py) (`examples/analytics_dashboard.py`)
* **Description**: Production-grade SaaS and telemetry dashboard with live data streaming, circular gauges, sparklines, Bezier throughput curves, and incident data grids.
```bash
uv run python examples/analytics_dashboard.py
```

---

### 3. [Multimedia & Studio Workstation](multimedia_dashboard.py) (`examples/multimedia_dashboard.py`)
* **Description**: Real-time 48-band audio spectrum analyzer (RTA), oscilloscope waveform, stereo VU meters with LED & gradient modes, playback transport controls, and session playlist manager.
```bash
uv run python examples/multimedia_dashboard.py
```

---

### 4. [Vector File Explorer](file_explorer.py) (`examples/file_explorer.py`)
* **Description**: Full-featured 3-pane modern file manager with Quick Access favorites, path navigation entry, live search filtering, sortable file metadata table, and text/code snippet preview.
```bash
uv run python examples/file_explorer.py
```

---

### 5. [60 FPS Real-Time Engine Lab](realtime_visualizer.py) (`examples/realtime_visualizer.py`)
* **Description**: Extreme rendering speed and zero-copy blitting stressing high frame rates across particle swarm physics, neon audio spectrum, and harmonic Lissajous curves.
```bash
uv run python examples/realtime_visualizer.py
```

---

### 6. [Canvas Studio & Vector Lab](canvas_studio.py) (`examples/canvas_studio.py`)
* **Description**: Deep dive into `NativeBlitCanvas` and `Surface` vector graphics capabilities with Bezier paths, multi-stop gradients, composition blend modes, drop shadows, and freehand drawing scratchpad.
```bash
uv run python examples/canvas_studio.py
```

---

### 7. [Custom Vector Widget Cookbook](custom_widget_cookbook.py) (`examples/custom_widget_cookbook.py`)
* **Description**: Developer architectural reference guide for creating custom zero-TTK vector widgets by subclassing `BaseControl` (Radar Chart, Speedometer Gauge, Step Progress Bar).
```bash
uv run python examples/custom_widget_cookbook.py
```

---

### 8. [Icons & Advanced Typography Demo](icons_and_typography_demo.py) (`examples/icons_and_typography_demo.py`)
* **Description**: Font Awesome 6 and Lucide vector icon integration, antialiased typography, text metrics, and code boxes.
```bash
uv run python examples/icons_and_typography_demo.py
```

---

### 9. [Master Widget Showcase](showcase.py) (`examples/showcase.py`)
* **Description**: Interactive widget matrix featuring buttons, switches, sliders, range sliders, progressbars, circular gauges, segmented buttons, textboxes, badges, and tables across built-in palettes.
```bash
uv run python examples/showcase.py
```

---

### 10. [Gradient Widgets Showcase](gradient_widgets.py) (`examples/gradient_widgets.py`)
* **Description**: Multi-stop linear and radial gradient styling across vector controls, dual-handle range sliders with dynamic gradient fills, live color pickers, and configurable drop shadows.
```bash
uv run python examples/gradient_widgets.py
```

---

### 11. [API Inspector & REST Client](api_inspector.py) (`examples/api_inspector.py`)
* **Description**: Desktop REST client demonstration showing non-blocking threaded HTTP requests, live status code badges, request history table with click-to-restore, response latency sparklines, JSON viewer, and offline mock mode.
```bash
uv run python examples/api_inspector.py
```

---

### 12. [Vector Table Demo](table_demo.py) (`examples/table_demo.py`)
* **Description**: Vector data grid demonstration with drag-to-resize columns, click-to-sort headers, zebra striping, selection modes, inline cell editors, and antialiased capsule scrollbars.
```bash
uv run python examples/table_demo.py
```

---

### 13. [Cinematic Theme Showcase](cinematic_theme_demo.py) (`examples/cinematic_theme_demo.py`)
* **Description**: Demonstration of the Peacock Teal (`#028090`) and Warm Amber (`#f4a261`) palette across vector cards, pills, badges, and responsive buttons.
```bash
uv run python examples/cinematic_theme_demo.py
```

---

## 🏗️ Architectural Highlights

* **Zero TTK Dependencies**: Pure `BaseControl` subclasses with native Blend2D zero-copy blitting directly into Tk window drawables.
* **Transparent Frame Protocol**: Seamless borderless container integration with zero background flickering (`super().__init__(..., background="")`).
* **Immediate-Mode Graphics (`NativeBlitCanvas`)**: High-performance immediate-mode painting backed by C++ `NativeController`.
* **Dynamic Theming**: Instant runtime theme transitions with compound container `.bg_color` cascade recursion across built-in palettes (`dark`, `light`, `catppuccin_mocha`, `tokyo_night`, `cyberpunk`, `dracula`, `nord`, etc.).
* **High-DPI Coordinate Scaling**: DPI-aware layout, border, geometry, and font metrics via `ScalingTracker`.

---

## Documentation Reference

For architecture guides, widget references, and theming documentation, see the [Documentation Hub](../docs/README.md):
* [Getting Started Guide](../docs/getting_started.md)
* [Architecture & Rendering Pipeline](../docs/architecture.md)
* [Widget Catalog](../docs/widgets.md)
* [Theming Engine & Palettes](../docs/theming.md)
* [Canvas & Custom Vector Drawing](../docs/canvas_and_vector.md)
* [Caveats, Edge Cases & Troubleshooting](../docs/caveats_and_edge_cases.md)
