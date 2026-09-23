"""
High-performance pure vector UI widgets powered by Blend2D and Tkinter PhotoImage.
Zero TTK theme dependencies. Antialiased vector rendering, High-DPI coordinate scaling,
and dynamic theming support.
"""

from tkblend.theme import blend_color_hex

from tkblend.widgets.base import (
    ScalingTracker,
    Widget,
    ModernWidget,
    _round_half_away,
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
    ModernFrame,
    Card,
    ModernCard,
    Accordion,
    ModernAccordion,
    _AccordionHeader,
)
from tkblend.widgets.button import (
    Button,
    ModernButton,
)
from tkblend.widgets.progress import (
    ProgressBar,
    ModernProgressBar,
    CircularProgress,
    ModernCircularProgress,
)
from tkblend.widgets.sliders import (
    Slider,
    ModernSlider,
    RangeSlider,
    ModernRangeSlider,
)
from tkblend.widgets.selection import (
    Switch,
    ModernSwitch,
    ToggleSwitch,
    Checkbox,
    ModernCheckbox,
    Radio,
    ModernRadio,
    RadioGroup,
    ModernRadioGroup,
    SegmentedControl,
    ModernSegmentedControl,
)
from tkblend.widgets.inputs import (
    TextInput,
    ModernTextInput,
    SpinBox,
    ModernSpinBox,
    _TextInputBackground,
)
from tkblend.widgets.scrollbar import (
    VectorScrollbar,
    ModernScrollbar,
    Scrollbar,
)
from tkblend.widgets.dropdown import (
    Dropdown,
    ModernDropdown,
    DropdownItem,
)
from tkblend.widgets.display import (
    Badge,
    ModernBadge,
    Avatar,
    ModernAvatar,
)

__all__ = [
    "ScalingTracker",
    "Widget",
    "ModernWidget",
    "Frame",
    "ModernFrame",
    "Card",
    "ModernCard",
    "Button",
    "ModernButton",
    "ProgressBar",
    "ModernProgressBar",
    "CircularProgress",
    "ModernCircularProgress",
    "Slider",
    "ModernSlider",
    "RangeSlider",
    "ModernRangeSlider",
    "Switch",
    "ModernSwitch",
    "ToggleSwitch",
    "Checkbox",
    "ModernCheckbox",
    "Radio",
    "ModernRadio",
    "RadioGroup",
    "ModernRadioGroup",
    "SegmentedControl",
    "ModernSegmentedControl",
    "TextInput",
    "ModernTextInput",
    "VectorScrollbar",
    "ModernScrollbar",
    "Scrollbar",
    "Dropdown",
    "ModernDropdown",
    "DropdownItem",
    "SpinBox",
    "ModernSpinBox",
    "Badge",
    "ModernBadge",
    "Avatar",
    "ModernAvatar",
    "Accordion",
    "ModernAccordion",
    "blend_color_hex",
    # Geometry and drawing utilities
    "draw_vector_checkmark",
    "draw_vector_chevron",
    "draw_vector_plus",
    "draw_vector_minus",
    "truncate_text",
]
