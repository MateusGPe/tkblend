# tkblend Documentation

Welcome to the **tkblend** documentation. **tkblend** is a 2D vector user interface and graphics library for Python Tkinter, powered by the **Blend2D** rasterizer and direct C++ blitting into Tk window drawables.

tkblend renders widgets independently of the standard TTK theme engine, providing antialiased vector controls, soft box-blur shadows, runtime theme switching across 18+ presets, and immediate-mode canvas rendering.

---

## Documentation Map

| Guide | Description |
| :--- | :--- |
| **[Getting Started](getting_started.md)** | Installation prerequisites, system dependencies, High-DPI setup, and building a first application. |
| **[Architecture & Rendering Pipeline](architecture.md)** | Low-level C++ blit pipeline, `Tk_PhotoPutBlock` integration, transparent frame handling, GIL management, and memory safety. |
| **[Widget Catalog](widgets.md)** | Catalog of built-in vector widgets (`Button`, `Card`, `Slider`, `RangeSlider`, `Switch`, `Table`, `TextBox`, etc.) with property references and code examples. |
| **[Theming Engine & Palettes](theming.md)** | Dynamic runtime theme switching, 18+ built-in presets, palette tokens, custom palettes, and container background cascading. |
| **[Canvas & Custom Vector Drawing](canvas_and_vector.md)** | Immediate-mode vector graphics with `NativeBlitCanvas` and `Surface`, gradients, Bézier paths, drop shadows, `DrawBatch`, and custom `BaseControl` authoring. |
| **[Caveats, Edge Cases & Troubleshooting](caveats_and_edge_cases.md)** | Architectural constraints, platform-specific differences (X11/Wayland/Windows/macOS), thread safety, font shaping, and widget layout gotchas with workarounds. |
| **[Examples Guide](examples.md)** | Descriptions and run commands for the interactive showcase applications included in the repository. |

---

## Key Concepts

* **Custom Vector Drawing**: Controls are rendered analytically via Blend2D instead of relying on fixed TTK bitmap layouts, allowing smooth scaling and customizable vector styling.
* **Direct C++ Buffer Blitting**: Renders pixel buffers directly in memory and transfers them to Tkinter display surfaces via native platform drawables or `Tk_PhotoPutBlock`, avoiding intermediate PIL conversions.
* **Display Scaling Support**: `ScalingTracker` calculates coordinate ratios on Windows, macOS, and Linux to adjust widget dimensions and stroke weights for High-DPI displays.
* **Theme Palettes**: Includes 18+ dark and light palettes (`Catppuccin Mocha`, `Tokyo Night`, `Cyberpunk`, `Dracula`, `Emerald Forest`, `Cinematic`, etc.) with runtime switching and background color inheritance.
* **Gradients and Shadows**: Built-in support for linear/radial gradients and multi-pass separable box-blur drop shadows.

---

## Quick Links

* **Repository Root**: [README.md](../README.md)
* **Examples Folder**: [examples/README.md](../examples/README.md)
* **License**: [MIT License](../LICENSE)
