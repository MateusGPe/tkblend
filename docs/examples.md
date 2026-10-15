# Showcase & Examples Guide

The `examples/` directory contains runnable sample applications demonstrating various capabilities of `tkblend`.

---

## Running the Examples

All examples can be launched directly using `uv` or standard Python:

```bash
# 1. Master Widget Showcase
uv run python examples/showcase.py

# 2. Gradient Widgets Showcase
uv run python examples/gradient_widgets.py

# 3. REST Client & API Inspector
uv run python examples/api_inspector.py

# 4. Cinematic Theme Showcase
uv run python examples/cinematic_theme_demo.py

# 5. Vector Table Demo
uv run python examples/table_demo.py
```

---

## Example Walkthroughs

### 1. Master Widget Showcase (`examples/showcase.py`)
* **File**: [examples/showcase.py](../examples/showcase.py)
* **What it demonstrates**:
  * An interactive matrix of built-in widgets organized into functional tabs.
  * Runtime theme switching across all 18 built-in palettes without restarting the application.
  * Controls including Buttons, Switches, Checkboxes, Radio Groups, Sliders, Circular Gauges, Progressbars, Badges, and TextBoxes.
  * High-DPI coordinate scaling and responsive layouts.

---

### 2. Gradient Widgets Showcase (`examples/gradient_widgets.py`)
* **File**: [examples/gradient_widgets.py](../examples/gradient_widgets.py)
* **What it demonstrates**:
  * Multi-stop linear and radial gradient shaders applied to buttons, sliders, progress bars, and card containers.
  * Dual-handle `RangeSlider` intervals linked to gradient progress indicators.
  * Live color pickers and property adjusters.
  * Separable soft drop shadows with configurable blur radius and opacity.

---

### 3. API Inspector (`examples/api_inspector.py`)
* **File**: [examples/api_inspector.py](../examples/api_inspector.py)
* **What it demonstrates**:
  * Demonstrates how to run asynchronous work using Python threads alongside tkblend widgets.
  * **Background HTTP Requests**: Dispatches network requests in background threads, reporting progress and results back to the main UI thread.
  * **Request History Table**: A vector table recording past requests, status codes, latency, and payloads.
  * **Status Code Badges**: Color-coded pill badges for HTTP status codes (`200 OK`, `404 Not Found`, `500 Error`).
  * **Response Latency Sparklines**: Sparkline trend graphs tracking latency across consecutive requests.
  * **Offline Mock Mode**: Enables local testing without network connectivity.

---

### 4. Cinematic Theme Demo (`examples/cinematic_theme_demo.py`)
* **File**: [examples/cinematic_theme_demo.py](../examples/cinematic_theme_demo.py)
* **What it demonstrates**:
  * Demonstration of the Peacock Teal (`#028090`) and Warm Amber (`#f4a261`) palette.
  * Card containers with subtle border contrasts, badges, and responsive buttons.
  * Clean dark-mode interface styling using custom theme tokens.

---

### 5. Vector Table Demo (`examples/table_demo.py`)
* **File**: [examples/table_demo.py](../examples/table_demo.py)
* **What it demonstrates**:
  * Vector data grid with virtualized row rendering.
  * Column dividers with interactive drag-to-resize behavior.
  * Click-to-sort columns with vector sorting indicators (`▲` / `▼`).
  * Alternating zebra striping, hover highlights, and row selection modes.
  * Inline cell editing with popups and dropdown selectors.
  * Antialiased capsule scrollbars.
