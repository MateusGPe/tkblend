# Widget Catalog

`tkblend` provides a suite of self-contained vector widgets. Each widget renders using Blend2D rasterization, scales across display DPI settings via `ScalingTracker`, and updates when the active theme palette changes.

---

## Widget Overview

| Category | Widget | Description |
| :--- | :--- | :--- |
| **Interactive Controls** | `Button` | Push button with hover/pressed states and color variants (`primary`, `secondary`, `success`, `danger`, `outline`). |
| | `Switch` | Toggle switch with animated thumb and optional text label. |
| | `Checkbox` | Vector checkbox with checkmark paths and hover/active states. |
| | `Radio` | Vector radio button linked via `tk.Variable`. |
| | `SegmentedButton` | Segmented button selector for mutually exclusive options. |
| **Numeric & Ranges** | `Slider` | Single-handle continuous slider with configurable bounds (`from_`, `to`). |
| | `RangeSlider` | Dual-handle continuous range slider (`low`, `high`) for selecting numeric intervals. |
| **Progress & Gauges** | `Progressbar` | Linear progress bar with rounded vector track and fill indicator. |
| | `CircularProgress` | Radial gauge / circular progress indicator with customizable sweep angle and unit label. |
| **Containers** | `Card` | Container with box-blur drop shadow and an inner `.content` frame. |
| | `Frame` | Vector container frame with background color cascading to child widgets. |
| | `ScrollableFrame` | Scrolling container with integrated vector scrollbar. |
| | `Tabview` | Tabbed container with segmented tab headers and page switching. |
| **Inputs & Pickers** | `Entry` | Single-line vector text input with placeholder support and focus borders. |
| | `SearchEntry` | Vector search box with search icon and clear button. |
| | `TextBox` | Multiline text editor with word wrapping and rounded border. |
| | `ComboBox` / `OptionMenu` | Dropdown picker with popup selection menu. |
| **Data & Metrics** | `Table` | Vector data grid with sortable columns, virtualized row rendering, and zebra striping. |
| | `Badge` | Pill-shaped status badge with variants (`default`, `primary`, `success`, `warning`, `danger`). |
| | `Label` | Vector-rendered text label with font, anchor alignment, and multiline auto-fit options. |
| | `Sparkline` | Compact trend line chart with area fill and Bézier curve smoothing. |

---

## Common Control API & Layout Contract

All interactive vector controls in `tkblend` inherit from `BaseControl`, providing a uniform API, standard Tkinter interoperability, and automated layout negotiation.

### 1. Universal Geometry & Layout Properties

Every control supports explicit sizing, boundary constraints, automated content measurement, and content anchoring:

| Property / Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `width` | `int \| None` | Widget default | Explicit logical pixel width. When omitted, the widget auto-fits to its content. |
| `height` | `int \| None` | Widget default | Explicit logical pixel height. When omitted, the widget auto-fits to its content. |
| `min_width` | `int \| None` | `None` | Minimum width constraint. Natural or requested width cannot shrink below this value. |
| `max_width` | `int \| None` | `None` | Maximum width constraint. Natural or requested width cannot expand beyond this value. |
| `min_height` | `int \| None` | `None` | Minimum height constraint. |
| `max_height` | `int \| None` | `None` | Maximum height constraint. |
| `auto_fit` | `bool` | `True` (if width is None) | When `True`, natural content size (text metrics + padding) determines geometry requests. |
| `anchor` | `str` | `"center"` or `"w"` | Internal content alignment within the surface: `"w"` (left), `"center"`, `"e"` (right). |
| `corner_radius` | `float \| None` | Theme default | Outer border corner radius in logical pixels. |
| `font` | `Any` | System sans-serif | Font descriptor (e.g. `("Inter", 12, "bold")` or `FontConfig`). |
| `text_overflow` | `str` | `"clip"` | Text truncation strategy: `"clip"` or `"ellipsis"`. |

```python
from tkblend import Button, Label, Switch

# Auto-fits to text length with boundary constraints
btn = Button(
    master,
    text="Confirm Transaction",
    min_width=120,
    max_width=240,
    anchor="center",
    corner_radius=8.0,
)
btn.pack(pady=6)

# Left-aligned switch inside an expanded column
sw = Switch(
    master,
    text="Background Sync",
    anchor="w",
)
sw.pack(fill="x", padx=12, pady=4)
```

### 2. State & Tkinter Interoperability

All widgets follow standard Tkinter conventions for state management, variable binding, and dynamic configuration:

* **State**: Standard `state="normal"` or `state="disabled"` strings, accompanied by the `is_disabled` boolean property. Disabled controls update their cursor, skip click callbacks, and render using disabled theme tokens.
* **Tkinter Variables**: Pass Tkinter variables directly via `variable=var` (`StringVar`, `BooleanVar`, `IntVar`, `DoubleVar`). Changes synchronize two-way between the vector widget and the variable with automatic trace cleanup on destruction.
* **Dynamic Configuration**: Configure properties at runtime via `.configure(key=value)`, `.config(key=value)`, dict assignment (`widget["text"] = "New"`), or direct property setters (`widget.text = "New"`).
* **Property Retrieval**: Inspect properties using `.cget("key")`, dict lookup (`widget["text"]`), or direct property reads (`widget.text`).

```python
import tkinter as tk
from tkblend import Checkbox, Button

checked_var = tk.BooleanVar(value=True)

chk = Checkbox(
    master,
    text="Enable Developer Diagnostics",
    variable=checked_var,
    state="normal",
)
chk.pack(pady=4)

# Dynamic updates via property setters or .configure()
chk.configure(text="Diagnostics Active", state="disabled")
assert chk.is_disabled is True

# Dict-style access
chk["state"] = "normal"
print("Checkbox anchor:", chk.cget("anchor"))
```

### 3. Responsive Pack and Grid Behavior

tkblend controls participate seamlessly in Tkinter geometry managers (`pack` and `grid`):

* **Auto-Fit by Default**: When no explicit width is passed, controls request exactly the geometry needed to render their text, icons, and padding without truncation.
* **Responsive Expansion (`fill="x"` / `sticky="ew"`)**: When expanded by a layout manager to fill extra space, the Blend2D surface resizes to the allocated bounds while `anchor` cleanly positions the vector contents (left, center, or right) across the expanded surface.
* **Dynamic Content Mutation**: Changing a widget's text dynamically (`lbl.text = "Much longer text..."`) recalculates the natural bounding box and triggers Tkinter geometry propagation automatically.

```python
from tkblend import Frame, Button, Label

row = Frame(master)
row.pack(fill="x", padx=16, pady=8)

# Left-anchored title that fills available horizontal space
title = Label(row, text="System Performance", anchor="w", font=("sans-serif", 14, "bold"))
title.pack(side="left", fill="x", expand=True)

# Right-anchored action button with clamped width
action = Button(row, text="Refresh", anchor="center", min_width=90, max_width=140)
action.pack(side="right")
```

---

## Interactive Controls

### 1. Button
Push button supporting multiple visual variants, auto-fit or explicit dimensions, anchors, and click callbacks.

```python
from tkblend import Button

# Auto-fitting button with min/max bounds and anchor alignment
btn = Button(
    master,
    text="Confirm Action",
    variant="primary",   # default, primary, secondary, success, danger, outline
    anchor="center",     # "w", "center", "e"
    min_width=120,
    max_width=220,
    corner_radius=8.0,
    command=lambda: print("Clicked!"),
)
btn.pack(pady=8)

# Update text and state dynamically
btn.text = "Processing..."
btn.state = "disabled"   # disables clicks and updates cursor/styling
```

---

### 2. Switch
Toggle switch with vector rounded track, animated thumb, optional text label, and `tk.Variable` binding.

```python
import tkinter as tk
from tkblend import Switch

switch_var = tk.BooleanVar(value=True)

def on_toggle():
    print("Switch state:", switch.is_checked)

switch = Switch(
    master,
    text="Enable Notifications",
    variable=switch_var,
    anchor="w",
    command=on_toggle,
)
switch.pack(fill="x", padx=12, pady=6)

# Programmatic toggle
switch.toggle()
assert switch_var.get() is False
```

---

### 3. Checkbox & Radio
Vector checkboxes and radio button groups linked to Tkinter variables with auto-sized labels and anchor alignment.

```python
import tkinter as tk
from tkblend import Checkbox, Radio

# Checkbox with two-way variable synchronization
chk_var = tk.BooleanVar(value=False)
chk = Checkbox(
    master,
    text="Remember session credentials",
    variable=chk_var,
    anchor="w",
)
chk.pack(fill="x", padx=12, pady=4)

# Radio Group with shared StringVar
radio_var = tk.StringVar(value="medium")
r1 = Radio(master, text="Low Priority", value="low", variable=radio_var, anchor="w")
r2 = Radio(master, text="Medium Priority", value="medium", variable=radio_var, anchor="w")
r3 = Radio(master, text="High Priority", value="high", variable=radio_var, anchor="w")
r1.pack(fill="x", padx=12, pady=2)
r2.pack(fill="x", padx=12, pady=2)
r3.pack(fill="x", padx=12, pady=2)

# Check active selection
assert r2.is_selected is True
```

---

### 4. SegmentedButton
Segmented button selector for mutually exclusive options with animated selection indicator.

```python
from tkblend import SegmentedButton

def on_segment_changed(selected_value):
    print("Selected mode:", selected_value)

seg = SegmentedButton(
    master,
    values=["Daily", "Weekly", "Monthly", "Yearly"],
    selected="Weekly",
    command=on_segment_changed,
    width=320,
    height=36,
)
seg.pack(pady=12)

# Programmatic value selection
seg.set("Monthly")
```

---

## Numeric & Range Controls

### 5. Slider
Continuous single-handle slider with bounded values.

```python
from tkblend import Slider

def on_slider_change(val: float):
    print(f"Current value: {val:.1f}")

slider = Slider(
    master,
    from_=0.0,
    to=100.0,
    value=50.0,
    width=280,
    height=30,
    command=on_slider_change,
)
slider.pack(pady=10)

# Set value programmatically
slider.set(75.0)
```

---

### 6. RangeSlider
Dual-handle continuous range slider for selecting minimum and maximum intervals.

```python
from tkblend import RangeSlider

def on_range_change(range_tuple):
    low, high = range_tuple
    print(f"Selected range: [{low:.1f}, {high:.1f}]")

range_slider = RangeSlider(
    master,
    from_=0.0,
    to=1000.0,
    values=(150.0, 850.0),
    width=320,
    height=36,
    command=on_range_change,
)
range_slider.pack(pady=10)

# Retrieve current interval
low, high = range_slider.get()
```

---

## Progress & Gauges

### 7. Progressbar
Linear progress bar with rounded vector track.

```python
from tkblend import Progressbar

pbar = Progressbar(master, width=280, height=10, value=65.0, maximum=100.0)
pbar.pack(pady=8)

# Set progress
pbar.set(85.0)
```

---

### 8. CircularProgress (Gauge)
Radial gauge and circular progress indicator with configurable sweep angle and unit text.

```python
from tkblend import CircularProgress

gauge = CircularProgress(
    master,
    size=120,
    value=78.5,
    min_value=0.0,
    max_value=100.0,
    unit="%",
    title="CPU Load",
    stroke_width=9.0,
    start_angle=-90.0,
    sweep_angle=360.0,
)
gauge.pack(pady=10)

# Update gauge
gauge.set_value(92.0)
```

---

## Containers & Layout

### 9. Card
Card container with a multi-pass box-blur drop shadow.

> [!NOTE]
> Child widgets should be placed into `card.content`, an internal frame positioned inside the card's rounded borders and padding.

```python
from tkblend import Card, Label, Button

card = Card(master, width=360, height=220)
card.pack(padx=20, pady=20)

lbl = Label(card.content, text="Card Content", font=("sans-serif", 13, "bold"))
lbl.pack(pady=(16, 8))

btn = Button(card.content, text="Perform Action", variant="primary")
btn.pack(pady=8)
```

---

### 10. ScrollableFrame
Scrollable container with an integrated vector scrollbar.

```python
from tkblend import ScrollableFrame, Button

scroll_container = ScrollableFrame(master, width=300, height=250)
scroll_container.pack(fill="both", expand=True, padx=16, pady=16)

# Populate scroll container
for i in range(25):
    btn = Button(scroll_container, text=f"Item #{i + 1}", width=240)
    btn.pack(pady=4)
```

---

### 11. Tabview
Multi-tab container with segmented headers.

```python
from tkblend import Tabview, Label

tabview = Tabview(master, width=400, height=260)
tabview.pack(fill="both", expand=True, padx=16, pady=16)

# Create tabs
tab_general = tabview.add("General")
tab_network = tabview.add("Network")
tab_security = tabview.add("Security")

Label(tab_general, text="General Settings").pack(pady=20)
Label(tab_network, text="Network Configuration").pack(pady=20)
Label(tab_security, text="Security & Encryption").pack(pady=20)
```

---

## Inputs & Pickers

### 12. Entry & SearchEntry
Vector single-line text input fields with placeholder text support, focus rings, and `tk.Variable` binding.

```python
import tkinter as tk
from tkblend import Entry, SearchEntry

username_var = tk.StringVar(value="")

# Standard entry with placeholder and variable binding
entry = Entry(
    master,
    placeholder="Enter username...",
    variable=username_var,
    min_width=200,
)
entry.pack(fill="x", padx=16, pady=6)

# Search entry with built-in search icon and clear button
search = SearchEntry(
    master,
    placeholder="Search logs...",
    min_width=240,
)
search.pack(fill="x", padx=16, pady=6)
```

---

### 13. TextBox
Multiline text editor with word wrapping, themeable background, and clipboard integration.

```python
from tkblend import TextBox

text_box = TextBox(
    master,
    width=340,
    height=160,
    font=("sans-serif", 10),
    corner_radius=8.0,
)
text_box.pack(pady=10)

# Modify content programmatically
text_box.set("Initial system configuration text...")
content = text_box.get()
```

---

### 14. ComboBox & OptionMenu
Dropdown picker with vector popup menu and selection callbacks.

```python
import tkinter as tk
from tkblend import ComboBox

selected_choice = tk.StringVar(value="Option A")

def on_selection(choice):
    print("User picked:", choice)

combo = ComboBox(
    master,
    values=["Option A", "Option B", "Option C"],
    selected="Option A",
    variable=selected_choice,
    command=on_selection,
    anchor="w",
    min_width=180,
)
combo.pack(pady=10)
```

---

## Data & Metrics

### 15. Label
Vector-rendered text label with font styling, multi-line auto-fit, and anchor alignment.

```python
from tkblend import Label

# Auto-fits horizontally and vertically to multi-line strings
lbl = Label(
    master,
    text="Service Cluster: EU-West\nStatus: Operational",
    anchor="w",                       # "w" (left), "center", "e" (right)
    font=("sans-serif", 11, "bold"),
    min_width=160,
)
lbl.pack(fill="x", padx=16, pady=8)

# Dynamic text change re-measures dimensions and updates geometry
lbl.text = "Service Cluster: EU-West\nStatus: Maintenance Scheduled"
```

---

### 16. Badge
Pill-shaped semantic status badge with auto-fitting width and corner radius constraints.

```python
from tkblend import Badge

b1 = Badge(master, text="CONNECTED", variant="success", anchor="center")
b2 = Badge(master, text="WARNING", variant="warning", anchor="center")
b3 = Badge(master, text="OFFLINE", variant="danger", anchor="center")
b1.pack(side="left", padx=4)
b2.pack(side="left", padx=4)
b3.pack(side="left", padx=4)

# Dynamic text mutation
b1.text = "SYNCED"
```

---

### 17. Table
Vector data grid with sortable column headers, virtualized row rendering, and zebra striping.

```python
from tkblend import Table

columns = ["ID", "Service", "Status", "Latency", "Throughput"]
data = [
    [101, "Auth Gateway", "Operational", "1.2 ms", "4,820 req/s"],
    [102, "Billing Core", "Operational", "3.4 ms", "1,290 req/s"],
    [103, "Search Cluster", "Degraded", "28.5 ms", "8,940 req/s"],
    [104, "Notification Bus", "Operational", "0.8 ms", "6,150 req/s"],
    [105, "Cache Sentinel", "Operational", "0.4 ms", "14,300 req/s"],
]

table = Table(
    master,
    columns=columns,
    data=data,
    width=560,
    height=240,
    zebra_striping=True,
    multi_select=True,
)
table.pack(fill="both", expand=True, padx=16, pady=16)
```

---

### 18. Sparkline
Compact trend line chart with Bézier curve smoothing and optional area gradient fill.

```python
from tkblend import Sparkline

points = [12, 19, 3, 5, 2, 3, 20, 33, 23, 40, 38, 55]
sparkline = Sparkline(master, data=points, width=160, height=36)
sparkline.pack(pady=8)
```

---

## Widget Edge Cases & Best Practices

When building complex forms and dashboards with vector widgets, keep the following edge cases in mind:

* **Card Hierarchy**: Always pack or grid children into `card.content` rather than the `Card` instance itself, ensuring child controls do not overwrite rounded border radii or drop shadow margins.
* **Slider Boundary Layout**: When displaying live percentage labels next to a `Slider` or `RangeSlider`, assign a fixed character `width` (e.g. `width=5`) to prevent adjacent layout shifts caused by varying string lengths (`0%` vs `100%`).
* **Table & Frame Mousewheel**: Scrolling on Linux fires `<Button-4>`/`<Button-5>` while Windows and macOS dispatch `<MouseWheel>` with different magnitude and sign conventions. Built-in widgets normalize these automatically.
* **Zero Interval Guards**: Ensure `max_value > min_value` when reconfiguring slider intervals dynamically to prevent division-by-zero boundary mapping.

> [!TIP]
> For code patterns and technical explanations of all widget edge cases, consult the [Caveats, Edge Cases & Troubleshooting Guide](caveats_and_edge_cases.md).

