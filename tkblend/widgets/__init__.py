"""
Modern UI widgets for Tkinter powered by tkblend's Blend2D vector engine.
"""

from tkblend.widgets.theme import (
    Theme,
    DARK_THEME,
    LIGHT_THEME,
    ThemeManager,
)

from tkblend.widgets.base import (
    ModernWidget,
    ease_out_cubic,
    ease_in_out_cubic,
    linear,
)

from tkblend.widgets.controls import (
    ModernButton,
    ModernCheckbox,
    ModernRadioButton,
    ModernRadioGroup,
    ModernSwitch,
    ModernSlider,
    ModernSegmentedControl,
)

from tkblend.widgets.inputs import (
    ModernEntry,
    ModernDropdown,
)

from tkblend.widgets.containers import (
    ModernFrame,
    ModernCard,
    ModernAccordion,
    ModernAccordionItem,
    ModernScrollableFrame,
)

from tkblend.widgets.feedback import (
    ModernProgressBar,
    ModernSpinner,
    ModernBadge,
    ModernAvatar,
    ModernTooltip,
)

from tkblend.widgets.dialogs import (
    ModernDialog,
    show_alert,
)

__all__ = [
    "Theme",
    "DARK_THEME",
    "LIGHT_THEME",
    "ThemeManager",
    "ModernWidget",
    "ModernButton",
    "ModernCheckbox",
    "ModernRadioButton",
    "ModernRadioGroup",
    "ModernSwitch",
    "ModernSlider",
    "ModernSegmentedControl",
    "ModernEntry",
    "ModernDropdown",
    "ModernFrame",
    "ModernCard",
    "ModernAccordion",
    "ModernAccordionItem",
    "ModernScrollableFrame",
    "ModernProgressBar",
    "ModernSpinner",
    "ModernBadge",
    "ModernAvatar",
    "ModernTooltip",
    "ModernDialog",
    "show_alert",
]
