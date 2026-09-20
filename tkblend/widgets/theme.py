"""
Theming and design token management for tkblend modern UI widgets.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Set, Union, Optional


@dataclass
class Theme:
    """
    Design tokens and semantic colors for modern widgets.
    """
    name: str = "dark"

    # Backgrounds & Surfaces
    bg_window: str = "#11111b"
    bg_surface: str = "#1e1e2e"
    bg_surface_alt: str = "#181825"
    bg_card: str = "#181825"
    bg_input: str = "#181825"
    bg_hover: str = "#313244"
    bg_active: str = "#45475a"

    # Borders & Dividers
    border: str = "#313244"
    border_subtle: str = "#262638"
    border_focused: str = "#89b4fa"
    border_width: float = 1.0

    # Primary / Accent
    primary: str = "#89b4fa"
    primary_hover: str = "#b4befe"
    primary_press: str = "#74c7ec"
    primary_text: str = "#11111b"

    # Secondary / Neutral Actions
    secondary: str = "#313244"
    secondary_hover: str = "#45475a"
    secondary_press: str = "#585b70"
    secondary_text: str = "#cdd6f4"

    # Status / Semantics
    success: str = "#a6e3a1"
    warning: str = "#f9e2af"
    danger: str = "#f38ba8"
    info: str = "#89dceb"

    # Foreground Typography
    text: str = "#cdd6f4"
    text_muted: str = "#a6adc8"
    text_disabled: str = "#6c7086"
    placeholder: str = "#6c7086"

    # Interactive elements
    track: str = "#313244"
    knob: str = "#ffffff"
    shadow_color: str = "#00000066"

    # Typography scales
    font_family: str = "sans-serif"
    font_size_xs: float = 10.0
    font_size_sm: float = 12.0
    font_size_md: float = 14.0
    font_size_lg: float = 16.0
    font_size_xl: float = 20.0

    # Corner radii
    radius_xs: float = 4.0
    radius_sm: float = 8.0
    radius_md: float = 12.0
    radius_lg: float = 16.0
    radius_full: float = 999.0

    # Elevation & Shadows
    elevation_none: float = 0.0
    elevation_sm: float = 4.0
    elevation_md: float = 8.0
    elevation_lg: float = 14.0


DARK_THEME = Theme(
    name="dark",
    bg_window="#11111b",
    bg_surface="#1e1e2e",
    bg_surface_alt="#181825",
    bg_card="#181825",
    bg_input="#181825",
    bg_hover="#313244",
    bg_active="#45475a",
    border="#313244",
    border_subtle="#262638",
    border_focused="#89b4fa",
    border_width=1.0,
    primary="#89b4fa",
    primary_hover="#b4befe",
    primary_press="#74c7ec",
    primary_text="#11111b",
    secondary="#313244",
    secondary_hover="#45475a",
    secondary_press="#585b70",
    secondary_text="#cdd6f4",
    success="#a6e3a1",
    warning="#f9e2af",
    danger="#f38ba8",
    info="#89dceb",
    text="#cdd6f4",
    text_muted="#a6adc8",
    text_disabled="#6c7086",
    placeholder="#6c7086",
    track="#313244",
    knob="#ffffff",
    shadow_color="#00000066",
)

LIGHT_THEME = Theme(
    name="light",
    bg_window="#eff1f5",
    bg_surface="#ffffff",
    bg_surface_alt="#e6e9ef",
    bg_card="#ffffff",
    bg_input="#ffffff",
    bg_hover="#dce0e8",
    bg_active="#ccd0da",
    border="#ccd0da",
    border_subtle="#bcc0cc",
    border_focused="#1e66f5",
    border_width=1.0,
    primary="#1e66f5",
    primary_hover="#7287fd",
    primary_press="#04a5e5",
    primary_text="#ffffff",
    secondary="#e6e9ef",
    secondary_hover="#dce0e8",
    secondary_press="#bcc0cc",
    secondary_text="#4c4f69",
    success="#40a02b",
    warning="#df8e1d",
    danger="#d20f39",
    info="#209fb5",
    text="#4c4f69",
    text_muted="#6c6f85",
    text_disabled="#9ca0b0",
    placeholder="#9ca0b0",
    track="#dce0e8",
    knob="#ffffff",
    shadow_color="#00000022",
)


class _ThemeManager:
    """
    Global theme manager singleton.
    """

    def __init__(self):
        self._current_theme: Theme = DARK_THEME
        self._listeners: Set[Callable[[Theme], None]] = set()
        self.animations_enabled: bool = True

    @property
    def theme(self) -> Theme:
        return self._current_theme

    def get_theme(self) -> Theme:
        return self._current_theme

    def set_theme(self, theme: Union[Theme, str]) -> None:
        if isinstance(theme, str):
            if theme.lower() == "light":
                self._current_theme = LIGHT_THEME
            elif theme.lower() == "dark":
                self._current_theme = DARK_THEME
            else:
                raise ValueError(f"Unknown theme name: {theme}")
        elif isinstance(theme, Theme):
            self._current_theme = theme
        else:
            raise TypeError(f"Expected Theme or str, got {type(theme)}")

        # Notify all registered widgets
        for listener in list(self._listeners):
            try:
                listener(self._current_theme)
            except Exception:
                pass

    def toggle_theme(self) -> Theme:
        if self._current_theme.name == "dark":
            self.set_theme(LIGHT_THEME)
        else:
            self.set_theme(DARK_THEME)
        return self._current_theme

    def subscribe(self, listener: Callable[[Theme], None]) -> None:
        self._listeners.add(listener)

    def unsubscribe(self, listener: Callable[[Theme], None]) -> None:
        self._listeners.discard(listener)


ThemeManager = _ThemeManager()
