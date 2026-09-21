"""
Modern UI widgets for Tkinter powered by tkblend's Blend2D vector engine.
"""

from tkblend.widgets.theme import (
    Theme,
    DARK_THEME,
    LIGHT_THEME,
    NORD_THEME,
    DRACULA_THEME,
    TOKYO_NIGHT_THEME,
    RampColor,
    ThemeManager,
    apply_ttk_theme,
    apply_theme,
    detect_system_theme,
    mix_colors,
    tint,
    shade,
    lighten_color,
    darken_color,
    relative_luminance,
    contrast_ratio,
    accent_on_color,
    is_dark_color,
    StyleBuilderTTK,
    DURABLE_STYLE_OPTIONS,
)

from tkblend.widgets.scaling import (
    ScalingTracker,
)

from tkblend.widgets.base import (
    ModernWidget,
    ease_out_cubic,
    ease_in_out_cubic,
    linear,
    _resolve_parent_bg,
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
    ModernLabel,
    ModernToast,
)

from tkblend.widgets.dialogs import (
    ModernDialog,
    show_alert,
)

__all__ = [
    "Theme",
    "DARK_THEME",
    "LIGHT_THEME",
    "NORD_THEME",
    "DRACULA_THEME",
    "TOKYO_NIGHT_THEME",
    "RampColor",
    "ThemeManager",
    "apply_ttk_theme",
    "apply_theme",
    "detect_system_theme",
    "mix_colors",
    "tint",
    "shade",
    "lighten_color",
    "darken_color",
    "relative_luminance",
    "contrast_ratio",
    "accent_on_color",
    "is_dark_color",
    "StyleBuilderTTK",
    "DURABLE_STYLE_OPTIONS",
    "ScalingTracker",
    "_resolve_parent_bg",
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
    "ModernLabel",
    "ModernToast",
    "ModernDialog",
    "show_alert",
]
