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
| | `Label` | Vector-rendered text label with font and color options. |
| | `Sparkline` | Compact trend line chart with area fill and Bézier curve smoothing. |

---

## Interactive Controls

### 1. Button
Push button supporting multiple visual variants and click callbacks.

```python
from tkblend import Button

# Standard primary button
btn = Button(
    master,
    text="Confirm Action",
    variant="primary",   # default, primary, secondary, success, danger, outline
    command=lambda: print("Clicked!"),
    width=140,
    height=36,
)
btn.pack(pady=8)

# Update text dynamically
btn.text = "Processing..."
```

---

### 2. Switch
Toggle switch with optional text label and state change callback.

```python
from tkblend import Switch

def on_toggle():
    print("Switch state:", switch.is_checked)

switch = Switch(
    master,
    text="Enable Notifications",
    is_checked=True,
    command=on_toggle,
)
switch.pack(pady=8)

# Programmatic toggle
switch.toggle()
```

---

### 3. Checkbox & Radio
Vector checkboxes and radio button groups linked to Tkinter variables.

```python
import tkinter as tk
from tkblend import Checkbox, Radio

# Checkbox
chk = Checkbox(master, text="Remember session credentials", is_checked=False)
chk.pack(pady=4)

# Radio Group
radio_var = tk.StringVar(value="medium")
r1 = Radio(master, text="Low Priority", value="low", variable=radio_var)
r2 = Radio(master, text="Medium Priority", value="medium", variable=radio_var)
r3 = Radio(master, text="High Priority", value="high", variable=radio_var)
r1.pack(pady=2)
r2.pack(pady=2)
r3.pack(pady=2)
```

---

### 4. SegmentedButton
Segmented button selector for choosing from a list of options.

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
Text input fields with placeholder text support and focus borders.

```python
from tkblend import Entry, SearchEntry

# Standard entry with placeholder
entry = Entry(master, placeholder="Enter username...", width=260)
entry.pack(pady=8)

# Search entry with search icon
search = SearchEntry(master, placeholder="Search logs...", width=260)
search.pack(pady=8)
```

---

### 13. TextBox
Multiline text editor.

```python
from tkblend import TextBox

text_box = TextBox(master, width=340, height=160, font=("sans-serif", 10))
text_box.pack(pady=10)
```

---

### 14. ComboBox & OptionMenu
Dropdown picker with vector popup menu.

```python
from tkblend import ComboBox

def on_selection(choice):
    print("User picked:", choice)

combo = ComboBox(
    master,
    values=["Option A", "Option B", "Option C"],
    selected="Option A",
    command=on_selection,
    width=220,
)
combo.pack(pady=10)
```

---

## Data & Metrics

### 15. Table
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

### 16. Badge & Sparkline
Status badges and compact trend lines.

```python
from tkblend import Badge, Sparkline

# Badges with semantic variants
b1 = Badge(master, text="CONNECTED", variant="success")
b2 = Badge(master, text="WARNING", variant="warning")
b3 = Badge(master, text="OFFLINE", variant="danger")
b1.pack(side="left", padx=4)
b2.pack(side="left", padx=4)
b3.pack(side="left", padx=4)

# Sparkline trend graph
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

