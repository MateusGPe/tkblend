# Getting Started with tkblend

This guide walks you through setting up **tkblend**, reviewing system requirements, and creating your first application using custom vector widgets.

---

## System Requirements

### Python & Platforms
* **Python**: 3.9, 3.10, 3.11, 3.12, or 3.13
* **Platforms**:
  * **Linux**: x86_64, aarch64 (glibc 2.28+)
  * **macOS**: Apple Silicon (M1+) & Intel x86_64 (macOS 11.0+)
  * **Windows**: x64 / x86 (Windows 10 / 11)

### System Packages
Standard Tcl/Tk 8.6+ development headers and libraries are required:
* **Ubuntu / Debian**:
  ```bash
  sudo apt-get update && sudo apt-get install -y python3-tk tk-dev
  ```
* **Fedora / RHEL**:
  ```bash
  sudo dnf install -y python3-tkinter tk-devel
  ```
* **macOS / Windows**:
  Standard Python installers from [python.org](https://python.org) or Homebrew provide Tkinter automatically.

---

## Installation

### Building from Source

tkblend contains C++ extensions compiled against Blend2D using `nanobind` and `scikit-build-core`. A C++17 or C++20 compatible compiler, CMake (>= 3.20), and Ninja are required for compilation:

```bash
# Clone the repository with submodules
git clone --recursive https://github.com/mateusgp/tsurf.git tkblend
cd tkblend

# Install build dependencies and build editable package using uv
uv pip install -e .
```

Alternatively, using standard `pip`:
```bash
pip install -e .
```

To verify the installation:
```bash
python -c "import tkblend; print(f'tkblend version: {tkblend.__version__}')"
```

---

## Display Scaling (High-DPI)

On high-resolution displays (e.g. 2K, 4K Retina, or mixed multi-monitor setups), standard Tkinter windows may require scaling adjustments.

`tkblend` provides `ScalingTracker` to query system scaling factors on Windows, macOS, and Linux:

```python
import tkinter as tk
from tkblend import ScalingTracker

root = tk.Tk()
scale = ScalingTracker.get_scaling_factor(root)
print(f"Active monitor scaling factor: {scale}x")
```

Built-in `tkblend` widgets (`Button`, `Card`, `Slider`, `Table`, etc.) automatically query scaling factors to adjust stroke widths, corner radii, and padding.

---

## Example: Basic Vector Application

Below is a complete, standalone script demonstrating a card container, slider, radial gauge, toggle switch, and theme switcher:

```python
import tkinter as tk
from tkblend import (
    Card,
    Button,
    Slider,
    Switch,
    Progressbar,
    CircularProgress,
    Badge,
    set_theme,
    get_theme,
)

def main():
    root = tk.Tk()
    root.title("tkblend Example")
    root.geometry("480x640")
    root.configure(bg="#181825")

    # Set initial theme palette
    set_theme("catppuccin_mocha")

    # Container card with drop shadow
    card = Card(root, width=420, height=560)
    card.pack(padx=24, pady=24, fill="both", expand=True)

    # Status badge
    badge = Badge(card.content, text="Ready", variant="success")
    badge.pack(pady=(4, 12))

    # Radial progress indicator
    gauge = CircularProgress(card.content, size=120, value=65.0, unit="%")
    gauge.pack(pady=10)

    # Linear progress bar
    pbar = Progressbar(card.content, width=320, value=65.0)
    pbar.pack(pady=8)

    # Slider linked to both indicators
    def on_slider_moved(val):
        gauge.set_value(val)
        pbar.set(val)

    slider = Slider(card.content, width=320, value=65.0, command=on_slider_moved)
    slider.pack(pady=10)

    # Toggle switch
    switch = Switch(card.content, text="High Contrast Mode", is_checked=True)
    switch.pack(pady=12)

    # Theme toggle button
    is_dark = True
    def toggle_theme():
        nonlocal is_dark
        is_dark = not is_dark
        new_theme = "catppuccin_mocha" if is_dark else "light"
        set_theme(new_theme)
        root.configure(bg=get_theme().bg)

    btn = Button(
        card.content,
        text="Toggle Theme (Dark / Light)",
        variant="primary",
        command=toggle_theme,
    )
    btn.pack(pady=12)

    root.mainloop()

if __name__ == "__main__":
    main()
```

---

## Next Steps

* **[Architecture & Rendering Pipeline](architecture.md)**: Details on the C++ blit pipeline, memory safety, and GIL handling.
* **[Widget Catalog](widgets.md)**: Catalog of built-in vector widgets with property tables and usage patterns.
* **[Theming Engine & Palettes](theming.md)**: Guide to palette tokens and defining custom themes.
* **[Canvas & Custom Vector Drawing](canvas_and_vector.md)**: Instructions for custom immediate-mode drawing with `NativeBlitCanvas`.
* **[Examples Guide](examples.md)**: Overview of runnable sample programs.
