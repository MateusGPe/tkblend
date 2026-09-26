# tkblend Next-Generation Example Suite

Welcome to the **tkblend** showcase suite. These examples demonstrate the full power of pure Blend2D 2D vector rendering for Python Tkinter — delivering subpixel anti-aliasing, soft drop shadows, multi-stop linear/radial gradients, dynamic theming, and 60+ FPS zero-copy blits with **zero TTK dependencies**.

---

## Quick Start: Launch the Showcase Hub

The easiest way to explore all showcases is via the **Unified Showcase Hub**:

```bash
python examples/hub.py
```

The Showcase Hub includes a modern sidebar allowing you to test every demo inside an embedded live viewport or pop out any demo into a dedicated standalone window.

---

## Showcase Applications Overview

### 1. [Analytics Dashboard](file:///home/mateusgp/projects/tkblend/examples/analytics_dashboard.py) (`examples/analytics_dashboard.py`)
* **What it demonstrates**: Production-grade SaaS and telemetry dashboard.
* **Features**:
  * Real-time hardware gauges with `CircularProgress` (CPU %, RAM %, GPU %).
  * Smooth anti-aliased Bézier area chart with transparent gradient fills and interactive hover tooltips.
  * Sortable incident log data grid with `Table`, status `Badge`s, and `Avatar`s.
  * Live metrics streaming and diagnostics controls with `SegmentedButton` and `Switch`.

```bash
python examples/analytics_dashboard.py
```

---

### 2. [Widget Catalog & Playground](file:///home/mateusgp/projects/tkblend/examples/widget_gallery.py) (`examples/widget_gallery.py`)
* **What it demonstrates**: Complete interactive showroom of all 20+ zero-TTK vector widgets.
* **Features**:
  * **Buttons & Badges**: Primary, Secondary, Outline, Danger, Success, Badges, Avatars.
  * **Inputs & Forms**: `TextInput`, `SpinBox`, `ComboBox`, `OptionMenu`, `Checkbox`, `RadioGroup`, `Switch`.
  * **Selectors & Sliders**: `Slider`, `RangeSlider`, `SegmentedButton`, `SegmentedControl`.
  * **Indicators & Gauges**: `ProgressBar`, `CircularProgress`.
  * **Containers & Layouts**: `Card`, `Accordion`, `ScrollableFrame`, `Tabview`.
  * **Data**: `Table` with sorting and column resizing.
  * **Live Property Inspector**: Real-time slider adjustments for corner radius (`rx`/`ry`), shadow elevation blur, and disabled states.

```bash
python examples/widget_gallery.py
```

---

### 3. [Creative Canvas & Vector Studio](file:///home/mateusgp/projects/tkblend/examples/canvas_studio.py) (`examples/canvas_studio.py`)
* **What it demonstrates**: Deep dive into `BlendCanvas` and `Surface` vector graphics capabilities.
* **Features**:
  * **Paths & Curves**: Cubic Bézier ribbons, quadratic arcs, star polygons, and SVG-like vector icons.
  * **Gradients & Extends**: 3-stop linear gradients, radial focal gradients, and extend modes (`EXTEND_PAD`, `EXTEND_REPEAT`, `EXTEND_REFLECT`).
  * **Composition Blend Modes**: Channel math visualization (`COMP_OP_MULTIPLY`, `SCREEN`, `OVERLAY`, `XOR`, `PLUS`, etc.).
  * **Drop Shadows & Glow**: Interactive sliders for shadow blur, spread, offset X/Y, and alpha.
  * **Interactive Freehand Scratchpad**: Smooth vector drawing canvas with brush size and color palette.

```bash
python examples/canvas_studio.py
```

---

### 4. [60 FPS Real-Time Visualizer](file:///home/mateusgp/projects/tkblend/examples/realtime_visualizer.py) (`examples/realtime_visualizer.py`)
* **What it demonstrates**: Raw rendering speed and zero-copy blit performance.
* **Features**:
  * **Particle Swarm**: 200+ particle physics simulation with cursor gravity wells, collision bounces, and speed-colored trails.
  * **Neon Audio Spectrum**: 32-band audio equalizer with peak hold meters and reflections.
  * **Harmonic Lissajous**: Phase-modulated oscilloscope curves.
  * **Live Performance Telemetry**: Real-time FPS counter and sub-millisecond render latency tracking.

```bash
python examples/realtime_visualizer.py
```

---

### 5. [Custom Vector Widget Cookbook](file:///home/mateusgp/projects/tkblend/examples/custom_widget_cookbook.py) (`examples/custom_widget_cookbook.py`)
* **What it demonstrates**: Developer architectural guide for creating custom vector widgets by subclassing `Widget`.
* **Included Reference Widgets**:
  1. `RadarChartWidget`: Multi-axis spider chart with polygon fill.
  2. `SpeedometerGauge`: Semi-circular analog/digital vector dial with glowing needle.
  3. `StepProgressBar`: Multi-step breadcrumb wizard with vector checkmarks.
  4. `ColorWheelPicker`: Radial HSV color wheel with draggable thumb.

```bash
python examples/custom_widget_cookbook.py
```

---

### 6. [CustomTkinter Bridge](file:///home/mateusgp/projects/tkblend/examples/ctk_showcase.py) (`examples/ctk_showcase.py`)
* **What it demonstrates**: Drop-in vector acceleration for CustomTkinter applications using `tkblend.ctk`.
* **Features**:
  * Intercepts CTk canvas drawing and replaces it with Blend2D JIT rendering.
  * Eliminates jagged corners and software rasterization artifacts.

```bash
python examples/ctk_showcase.py
```

---

## Architectural Highlights

* **Zero TTK Dependencies**: Completely independent of `ttk.Style` and Tcl/Tk theme engines.
* **Direct Zero-Copy Blitting**: Pixel buffers transfer directly from C++ memory into `tk.PhotoImage` using `Tk_PhotoPutBlock`.
* **Dynamic Theming (13+ Palettes)**: Runtime switching between `DARK`, `LIGHT`, `CATPPUCCIN_MOCHA`, `TOKYO_NIGHT`, `CYBERPUNK`, `DRACULA`, `EMERALD_FOREST`, `NORD`, `SUNSET_AMBER`, `MONOKAI_PRO`, `SOLARIZED_DARK`, and `SOLARIZED_LIGHT`.
* **High-DPI Coordinate Scaling**: DPI-aware layout, border, and font rendering via `ScalingTracker`.
