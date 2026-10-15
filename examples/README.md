# tkblend Showcase & Example Suite

This directory contains standalone example applications demonstrating various widgets and capabilities of **tkblend** — including vector controls, separable soft drop shadows, linear/radial gradients, CSS theming, and immediate-mode canvas drawing.

---

## Quick Start: Master Widget Showcase

To launch the interactive widget showcase with live theme hot-switching:

```bash
uv run python examples/showcase.py
```

<p align="center">
  <img src="../docs/assets/widget_matrix_theming.gif" alt="tkblend Showcase" width="860"/>
</p>

The showcase organizes widgets into functional tabs (`Buttons & Toggles`, `Sliders & Progress`, `Data & Inputs`, `Themes`) with property inspectors and runtime palette switching.

---

## Showcase Applications

### 1. [Master Widget Showcase](showcase.py) (`examples/showcase.py`)
* **Description**: Interactive widget matrix featuring buttons, switches, sliders, range sliders, progressbars, circular gauges, segmented buttons, textboxes, badges, and tables across built-in palettes.
```bash
uv run python examples/showcase.py
```

---

### 2. [Gradient Widgets Showcase](gradient_widgets.py) (`examples/gradient_widgets.py`)
* **Description**: Multi-stop linear and radial gradient styling across vector controls, dual-handle range sliders with dynamic gradient fills, live color pickers, and configurable drop shadows.
```bash
uv run python examples/gradient_widgets.py
```

---

### 3. [API Inspector & REST Client](api_inspector.py) (`examples/api_inspector.py`)
* **Description**: Desktop REST client demonstration showing non-blocking threaded HTTP requests, live status code badges, request history table with click-to-restore, response latency sparklines, JSON viewer, and offline mock mode.
```bash
uv run python examples/api_inspector.py
```

---

### 4. [Cinematic Theme Showcase](cinematic_theme_demo.py) (`examples/cinematic_theme_demo.py`)
* **Description**: Demonstration of the Peacock Teal (`#028090`) and Warm Amber (`#f4a261`) palette across vector cards, pills, badges, and responsive buttons.
```bash
uv run python examples/cinematic_theme_demo.py
```

---

### 5. [Vector Table Demo](table_demo.py) (`examples/table_demo.py`)
* **Description**: Vector data grid demonstration with drag-to-resize columns, click-to-sort headers, zebra striping, selection modes, inline cell editors, and antialiased capsule scrollbars.
```bash
uv run python examples/table_demo.py
```

---

## Documentation Reference

For architecture guides, widget references, and theming documentation, see the [Documentation Hub](../docs/README.md):
* [Getting Started Guide](../docs/getting_started.md)
* [Architecture & Rendering Pipeline](../docs/architecture.md)
* [Widget Catalog](../docs/widgets.md)
* [Theming Engine & Palettes](../docs/theming.md)
* [Canvas & Custom Vector Drawing](../docs/canvas_and_vector.md)
* [Caveats, Edge Cases & Troubleshooting](../docs/caveats_and_edge_cases.md)
