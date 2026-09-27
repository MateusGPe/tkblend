"""
High-performance pure vector UI widgets powered by Blend2D and Tkinter PhotoImage.
Zero TTK theme dependencies. Antialiased vector rendering, High-DPI coordinate scaling,
and dynamic theming support.

Standard Tk/ttk drop-in widget naming with backward-compatible aliases and modern components.
"""

from tkblend.theme import blend_color_hex

from tkblend.widgets.base import (
    ScalingTracker,
    Widget,
    VariableSync,
    _round_half_away,
    cascade_bg_to_children,
)
from tkblend.widgets.drawing import (
    draw_vector_checkmark,
    draw_vector_chevron,
    draw_vector_plus,
    draw_vector_minus,
    truncate_text,
)
from tkblend.widgets.containers import (
    Frame,
    Card,
    LabelFrame,
    Labelframe,
    Accordion,
    _AccordionHeader,
)
from tkblend.widgets.button import (
    Button,
)
from tkblend.widgets.progress import (
    Progressbar,
    ProgressBar,
    CircularProgress,
)
from tkblend.widgets.sliders import (
    Scale,
    Slider,
    RangeSlider,
)
from tkblend.widgets.selection import (
    Checkbutton,
    Checkbox,
    Radiobutton,
    Radio,
    RadioGroup,
    Switch,
    ToggleSwitch,
    SegmentedControl,
    SegmentedButton,
)
from tkblend.widgets.inputs import (
    Entry,
    TextInput,
    Spinbox,
    SpinBox,
    _TextInputBackground,
)
from tkblend.widgets.scrollbar import (
    Scrollbar,
    VectorScrollbar,
)
from tkblend.widgets.dropdown import (
    Dropdown,
    DropdownItem,
)
from tkblend.widgets.display import (
    Label,
    Badge,
    Avatar,
)
from tkblend.widgets.tabview import (
    Notebook,
    Tabview,
)
from tkblend.widgets.scrollable import (
    ScrollableFrame,
)
from tkblend.widgets.textbox import (
    Text,
    TextBox,
)
from tkblend.widgets.combobox import (
    Combobox,
    ComboBox,
    OptionMenu,
)
from tkblend.widgets.table import (
    Table,
    Treeview,
)
from tkblend.widgets.image import (
    VectorIcon,
    IconLabel,
    VectorImage,
)
from tkblend.widgets.sparkline import (
    Sparkline,
)
from tkblend.widgets.chart import (
    BaseChart,
    LineChart,
    AreaChart,
    BarChart,
    PieChart,
    DonutChart,
)
from tkblend.widgets.color_picker import (
    ColorPicker,
    ColorWell,
    ask_color,
)
from tkblend.widgets.volume import (
    VolumeControl,
    VolumeSlider,
    VUMeter,
    AudioMeter,
)
from tkblend.widgets.toolbar import (
    Toolbar,
    ToolbarSeparator,
)

__all__ = [
    # Base & Infrastructure
    "ScalingTracker",
    "Widget",
    "VariableSync",
    "cascade_bg_to_children",
    "blend_color_hex",
    # Standard Tk/ttk Canonical Widgets
    "Button",
    "Entry",
    "Checkbutton",
    "Radiobutton",
    "Combobox",
    "Progressbar",
    "Scale",
    "Spinbox",
    "Label",
    "LabelFrame",
    "Labelframe",
    "Notebook",
    "Text",
    "Scrollbar",
    "Frame",
    "Treeview",
    # Backward-Compatible Legacy Aliases
    "TextInput",
    "Checkbox",
    "Radio",
    "ComboBox",
    "ProgressBar",
    "Slider",
    "SpinBox",
    "Tabview",
    "TextBox",
    "Table",
    "VectorScrollbar",
    # Modern Vector Extended Components
    "Card",
    "Switch",
    "ToggleSwitch",
    "RadioGroup",
    "SegmentedControl",
    "SegmentedButton",
    "RangeSlider",
    "CircularProgress",
    "Dropdown",
    "DropdownItem",
    "OptionMenu",
    "Badge",
    "Avatar",
    "Accordion",
    "ScrollableFrame",
    "VectorIcon",
    "IconLabel",
    "VectorImage",
    # Data Visualization & Media Controls
    "Sparkline",
    "BaseChart",
    "LineChart",
    "AreaChart",
    "BarChart",
    "PieChart",
    "DonutChart",
    "ColorPicker",
    "ColorWell",
    "ask_color",
    "VolumeControl",
    "VolumeSlider",
    "VUMeter",
    "AudioMeter",
    "Toolbar",
    "ToolbarSeparator",
    # Drawing Utilities
    "draw_vector_checkmark",
    "draw_vector_chevron",
    "draw_vector_plus",
    "draw_vector_minus",
    "truncate_text",
]

