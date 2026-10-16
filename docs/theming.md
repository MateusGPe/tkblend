# Theming Engine & CSS Palettes

`tkblend` includes a theming architecture based on CSS custom properties. Styling rules, semantic tokens, and color palettes are parsed by `StyleEngine` into `Palette` objects, allowing runtime theme switching across the widget tree.

---

## Built-in Themes

`tkblend` includes 18 built-in palettes for dark and light modes:

| Theme Name | Mode | Description |
| :--- | :---: | :--- |
| `dark` | Dark | Default dark interface with slate backgrounds. |
| `light` | Light | Standard daylight interface. |
| `catppuccin_mocha` | Dark | Pastel dark palette based on Catppuccin Mocha. |
| `catppuccin_latte` | Light | Daylight pastel palette based on Catppuccin Latte. |
| `cinematic` | Dark | Teal (`#028090`) and Warm Amber (`#f4a261`) palette. |
| `tokyo_night` | Dark | Midnight indigo with purple and blue accents. |
| `cyberpunk` | Dark | Neon cyan, yellow, and magenta accents on a dark background. |
| `dracula` | Dark | Purple and dark navy background with pink and green accents. |
| `nord` | Dark | Arctic blue-gray palette. |
| `emerald_forest` / `emerald` | Dark | Deep forest green with mint highlights. |
| `sunset_amber` / `sunset` | Dark | Evening dark palette with warm amber accents. |
| `monokai_pro` / `monokai` | Dark | Dark charcoal background with multi-color accents. |
| `solarized_dark` | Dark | Low-contrast teal and cream palette. |
| `solarized_light` | Light | Low-contrast solarized daylight palette. |
| `ocean` | Dark | Deep navy blue with cyan highlights. |
| `slate` | Dark | Neutral zinc and cool gray tones. |

---

## Runtime Theme Switching

Themes can be changed dynamically without recreating widgets or restarting the application:

```python
from tkblend import set_theme, get_theme, get_available_themes

# List all available theme identifiers
print(get_available_themes())

# Switch theme at runtime
set_theme("catppuccin_mocha")

# Inspect the active Palette object
palette = get_theme()
print("Background:", palette.bg)
print("Card Background:", palette.card_bg)
print("Primary Accent:", palette.primary)
```

### OS Theme Synchronization
`tkblend` can listen for operating system dark/light mode preference changes:

```python
from tkblend import auto_theme, stop_auto_theme

# Synchronize with OS theme changes
auto_theme(dark_theme="catppuccin_mocha", light_theme="catppuccin_latte")
```

---

## Theme Token Reference

Widgets query colors from semantic tokens exposed by the `Palette` object:

| Token Property | CSS Variable | Description |
| :--- | :--- | :--- |
| `palette.bg` | `--bg` | Primary window / root container background. |
| `palette.fg` | `--fg` | Primary foreground text color. |
| `palette.primary` | `--primary` | Main interactive brand / accent color. |
| `palette.secondary` | `--secondary` | Secondary interactive color. |
| `palette.accent` | `--accent` | Highlight and indicator color. |
| `palette.card_bg` | `--card-bg` | Surface background fill for cards and containers. |
| `palette.card_border` | `--card-border` | Outline border for cards and panels. |
| `palette.input_bg` | `--input-bg` | Background fill for text fields and search entries. |
| `palette.track_bg` | `--track-bg` | Background track for sliders, progress bars, and switches. |
| `palette.thumb_color`| `--thumb-color`| Handle/knob color for sliders and switches. |
| `palette.selection_bg`| `--selection-bg`| Highlight color for selected rows or text. |
| `palette.success` | `--success` | Semantic green for confirmations and active states. |
| `palette.warning` | `--warning` | Semantic yellow/amber for warnings. |
| `palette.danger` | `--danger` | Semantic red for errors or destructive actions. |

### Table Component Tokens

The `Table` widget uses a standardized set of tokens defined across all built-in themes:

| Token Property | CSS Variable | Description |
| :--- | :--- | :--- |
| `palette.table_bg` | `--table-bg` | Table container surface background. |
| `palette.table_fg` | `--table-fg` | Primary table cell text foreground. |
| `palette.table_header_bg` | `--table-header-bg` | Column header bar background. |
| `palette.table_header_fg` | `--table-header-fg` | Column header title text foreground. |
| `palette.table_zebra_bg` | `--table-zebra-bg` | Alternating row stripe background. |
| `palette.table_hover_bg` | `--table-hover-bg` | Interactive row hover highlight. |
| `palette.table_selected_bg` | `--table-selected-bg` | Active row selection highlight. |
| `palette.table_selected_fg` | `--table-selected-fg` | Selected row text foreground. |
| `palette.table_border` | `--table-border` | Table outer border and row divider lines. |
| `palette.table_scrollbar_thumb` | `--table-scrollbar-thumb` | Embedded table scrollbar idle thumb. |
| `palette.table_scrollbar_thumb_hover` | `--table-scrollbar-thumb-hover` | Embedded table scrollbar active/hover thumb. |

---

## Container Background Cascading

When nesting widgets in Tkinter, child widgets often require knowledge of their parent container's background to avoid visual seams:

1. **Inner Surface Color**: Compound containers (`Card`, `ScrollableFrame`, `Tabview`, `Table`, `TextBox`, `Frame`) expose their active inner background via `.bg_color`.
2. **Cascading Notification**: When a container's theme updates, `cascade_bg_to_children(container, inner_bg)` traverses child widgets to update their backdrop color.
3. **Empty Background Attribute**: Vector controls set `background=""` so Tkinter does not fill a solid background over Blend2D's rendered pixels.

```python
from tkblend import Card, Button

card = Card(root, width=320, height=200)
card.pack()

# Widgets placed inside card.content receive the card's background color
btn = Button(card.content, text="Action")
btn.pack(pady=20)
```

---

## Defining Custom Themes

Custom themes can be registered from a CSS string or loaded from an external `.css` file:

### From a CSS String
```python
from tkblend import register_theme, set_theme

CUSTOM_CSS = """
:root {
    --bg: #0d0f18;
    --fg: #f0f4fc;
    --primary: #00ffcc;
    --secondary: #1a1e30;
    --accent: #ff007f;
    --card-bg: #141829;
    --card-border: #222944;
    --input-bg: #101424;
    --track-bg: #1c223a;
    --thumb-color: #00ffcc;
    --success: #00ff88;
    --warning: #ffcc00;
    --danger: #ff0055;
}
"""

# Register and apply the theme
register_theme("custom_neon", CUSTOM_CSS)
set_theme("custom_neon")
```

### From an External CSS File
```python
from tkblend import load_theme_file, set_theme

theme_name = load_theme_file("my_theme.css")
set_theme(theme_name)
```

---

> [!TIP]
> For details on container background color cascading (`resolve_ancestor_bg()`), pseudo-transparency corner blending, and registering custom vector drawings via `add_theme_listener()`, see the [Caveats, Edge Cases & Troubleshooting Guide](caveats_and_edge_cases.md).

