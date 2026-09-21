"""
Theming, design tokens, color math, and TTK style engine for tkblend modern UI widgets,
seamlessly interoperable with standard Tkinter and TTK controls.

Inspired by ttkbootstrap and CustomTkinter architectures, optimized for Blend2D vector rendering.
"""

from __future__ import annotations
import colorsys
import json
import os
import sys
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, field, asdict
from typing import Callable, Set, Dict, Union, Optional, List, Any, Tuple
from functools import lru_cache


# ============================================================================
# Color Math & Ramp Functions (Harvested and adapted from ttkbootstrap/bootstack)
# ============================================================================

_TINT_WEIGHTS = {
    50: 0.90,
    100: 0.80,
    150: 0.70,
    200: 0.60,
    250: 0.50,
    300: 0.40,
    350: 0.30,
    400: 0.20,
    450: 0.10,
}
_SHADE_WEIGHTS = {
    550: 0.10,
    600: 0.20,
    650: 0.30,
    700: 0.40,
    750: 0.50,
    800: 0.60,
    850: 0.70,
    900: 0.80,
    950: 0.90,
}
_RAMP_STOPS = frozenset(list(_TINT_WEIGHTS.keys()) + [500] + list(_SHADE_WEIGHTS.keys()))


def _hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Parse hex string (#RGB, #RRGGBB, #RRGGBBAA) into 0-255 RGB integers."""
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        return int(s[0] * 2, 16), int(s[1] * 2, 16), int(s[2] * 2, 16)
    elif len(s) == 6 or len(s) == 8:
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    return 0, 0, 0


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    """Format RGB integers to #RRGGBB hex string."""
    return f"#{max(0, min(255, int(r))):02x}{max(0, min(255, int(g))):02x}{max(0, min(255, int(b))):02x}"


def mix_colors(color1: str, color2: str, weight: float = 0.5) -> str:
    """Mix two colors; weight (0.0 to 1.0) is the fraction of color1."""
    r1, g1, b1 = _hex_to_rgb(color1)
    r2, g2, b2 = _hex_to_rgb(color2)
    w = max(0.0, min(1.0, float(weight)))
    r = round(r1 * w + r2 * (1.0 - w))
    g = round(g1 * w + g2 * (1.0 - w))
    b = round(b1 * w + b2 * (1.0 - w))
    return _rgb_to_hex(r, g, b)


def tint(color: str, weight: float = 0.2) -> str:
    """Mix `weight` of white into `color` (a lighter tint)."""
    return mix_colors("#ffffff", color, weight)


def shade(color: str, weight: float = 0.2) -> str:
    """Mix `weight` of black into `color` (a darker shade)."""
    return mix_colors("#000000", color, weight)


@lru_cache(maxsize=256)
def _build_color_ramp(anchor_hex: str) -> Dict[int, str]:
    """Generate a 50–950 tint/shade ramp for an anchor hex color."""
    anchor = _rgb_to_hex(*_hex_to_rgb(anchor_hex))
    ramp = {
        stop: mix_colors("#ffffff", anchor, target)
        for stop, target in _TINT_WEIGHTS.items()
    }
    ramp[500] = anchor
    ramp.update(
        {
            stop: mix_colors("#000000", anchor, target)
            for stop, target in _SHADE_WEIGHTS.items()
        }
    )
    return ramp


class RampColor(str):
    """
    A hex color string that also supports 50–950 tint/shade indexing.
    Acts as a normal string everywhere, but `color[300]` returns a lighter tint,
    `color[700]` returns a darker shade, etc.
    """

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int) and key in _RAMP_STOPS:
            return _build_color_ramp(str(self))[key]
        return super().__getitem__(key)


def as_ramp_color(value: Union[str, RampColor, Any]) -> Union[RampColor, Any]:
    """Wrap a color string as a `RampColor`."""
    if isinstance(value, str) and not isinstance(value, RampColor):
        return RampColor(value)
    return value


def relative_luminance(color: str) -> float:
    """Return WCAG relative luminance (0.0 to 1.0) for a hex color."""
    r_int, g_int, b_int = _hex_to_rgb(color)
    channels = [r_int / 255.0, g_int / 255.0, b_int / 255.0]

    def linearize(val: float) -> float:
        return val / 12.92 if val <= 0.03928 else ((val + 0.055) / 1.055) ** 2.4

    r, g, b = (linearize(c) for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color1: str, color2: str) -> float:
    """Return the WCAG contrast ratio (1.0 to 21.0) between two colors."""
    lum1 = relative_luminance(color1)
    lum2 = relative_luminance(color2)
    lighter, darker = max(lum1, lum2), min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def is_dark_color(color: str) -> bool:
    """Determine if a color is perceptually dark."""
    return relative_luminance(color) < 0.35


def lighten_color(color: str, percent: float = 0.1) -> str:
    """Lighten a color by increasing HLS lightness."""
    r, g, b = _hex_to_rgb(color)
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    l = min(1.0, l + (1.0 - l) * percent)
    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return _rgb_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))


def darken_color(color: str, percent: float = 0.1) -> str:
    """Darken a color by reducing HLS lightness."""
    r, g, b = _hex_to_rgb(color)
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    l = max(0.0, l * (1.0 - percent))
    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return _rgb_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))


def accent_on_color(surface: str) -> str:
    """
    Return a legible text foreground (#ffffff or #11111b) for a given surface color.
    Prefers white on saturated colors while ensuring accessibility on light fills.
    """
    if contrast_ratio("#ffffff", surface) >= 3.0:
        return "#ffffff"
    r, g, b = _hex_to_rgb(surface)
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    hue_deg = int(h * 360)
    warm = 20 <= hue_deg <= 100
    if s >= 0.45 and not warm and contrast_ratio("#ffffff", surface) >= 2.2:
        return "#ffffff"
    return "#11111b"


# ============================================================================
# Theme Class and Token Definitions
# ============================================================================

@dataclass
class Theme:
    """
    Design tokens and semantic colors for modern widgets and standard Tk/ttk controls.
    """
    name: str = "dark"
    is_dark: bool = True

    # Backgrounds & Surfaces
    bg_window: str = "#11111b"
    bg_surface: str = "#1e1e2e"
    bg_surface_alt: str = "#181825"
    bg_card: str = "#181825"
    bg_input: str = "#181825"
    bg_hover: str = "#313244"
    bg_active: str = "#45475a"
    surface_raised: str = "#262638"
    surface_overlay: str = "#181825"

    # Borders & Dividers
    border: str = "#313244"
    border_subtle: str = "#262638"
    border_focused: str = "#89b4fa"
    border_width: float = 1.0

    # Semantic Accents
    primary: str = "#89b4fa"
    primary_hover: str = "#b4befe"
    primary_press: str = "#74c7ec"
    primary_text: str = "#11111b"

    secondary: str = "#313244"
    secondary_hover: str = "#45475a"
    secondary_press: str = "#585b70"
    secondary_text: str = "#cdd6f4"

    success: str = "#a6e3a1"
    success_hover: str = "#bbf2b6"
    success_press: str = "#94d38f"
    success_text: str = "#11111b"

    warning: str = "#f9e2af"
    warning_hover: str = "#fbecc8"
    warning_press: str = "#ebd4a0"
    warning_text: str = "#11111b"

    danger: str = "#f38ba8"
    danger_hover: str = "#f8a5bc"
    danger_press: str = "#e07895"
    danger_text: str = "#11111b"

    info: str = "#89dceb"
    info_hover: str = "#a6e7f2"
    info_press: str = "#74cbdb"
    info_text: str = "#11111b"

    # Foreground Typography
    text: str = "#cdd6f4"
    text_muted: str = "#a6adc8"
    text_disabled: str = "#6c7086"
    placeholder: str = "#6c7086"
    accent_text: str = "#89b4fa"

    # Interactive elements & Scrollbars
    track: str = "#313244"
    knob: str = "#ffffff"
    shadow_color: str = "#00000066"
    selection_bg: str = "#89b4fa"
    selection_fg: str = "#11111b"
    scrollbar_thumb: str = "#45475a"
    scrollbar_thumb_hover: str = "#585b70"
    scrollbar_track: str = "#181825"

    # Typography scales
    font_family: str = "sans-serif"
    font_size_xs: float = 10.0
    font_size_sm: float = 12.0
    font_size_md: float = 14.0
    font_size_lg: float = 16.0
    font_size_xl: float = 20.0
    font_size_2xl: float = 24.0

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

    def __post_init__(self):
        # Auto-wrap accent and surface colors with RampColor for convenient tint/shade indexing
        for attr in ("primary", "secondary", "success", "warning", "danger", "info",
                     "bg_window", "bg_surface", "bg_card", "bg_input", "border", "text"):
            val = getattr(self, attr, None)
            if isinstance(val, str) and not isinstance(val, RampColor):
                setattr(self, attr, RampColor(val))

    def get_color(self, role: str) -> str:
        """Get color by role or attribute name with graceful fallback."""
        return str(getattr(self, role, self.primary))

    def get_variant_colors(self, variant: str) -> Tuple[str, str, str, str]:
        """
        Return (normal_bg, hover_bg, press_bg, text_color) for a semantic variant.
        Supported variants: primary, secondary, success, danger, warning, info, outline, ghost.
        """
        v = (variant or "primary").lower()
        if v == "secondary":
            return self.secondary, self.secondary_hover, self.secondary_press, self.secondary_text
        elif v == "success":
            return self.success, self.success_hover, self.success_press, self.success_text
        elif v == "danger":
            return self.danger, self.danger_hover, self.danger_press, self.danger_text
        elif v == "warning":
            return self.warning, self.warning_hover, self.warning_press, self.warning_text
        elif v == "info":
            return self.info, self.info_hover, self.info_press, self.info_text
        elif v == "outline":
            return "transparent", self.bg_hover, self.bg_active, self.primary
        elif v == "ghost":
            return "transparent", self.bg_hover, self.bg_active, self.text
        # Default to primary
        return self.primary, self.primary_hover, self.primary_press, self.primary_text

    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Theme:
        """Create a Theme instance from dictionary."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# ============================================================================
# Built-in Theme Presets
# ============================================================================

DARK_THEME = Theme(
    name="dark",
    is_dark=True,
    bg_window="#11111b",
    bg_surface="#1e1e2e",
    bg_surface_alt="#181825",
    bg_card="#181825",
    bg_input="#181825",
    bg_hover="#313244",
    bg_active="#45475a",
    surface_raised="#262638",
    surface_overlay="#181825",
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
    success_hover="#bbf2b6",
    success_press="#94d38f",
    success_text="#11111b",
    warning="#f9e2af",
    warning_hover="#fbecc8",
    warning_press="#ebd4a0",
    warning_text="#11111b",
    danger="#f38ba8",
    danger_hover="#f8a5bc",
    danger_press="#e07895",
    danger_text="#11111b",
    info="#89dceb",
    info_hover="#a6e7f2",
    info_press="#74cbdb",
    info_text="#11111b",
    text="#cdd6f4",
    text_muted="#a6adc8",
    text_disabled="#6c7086",
    placeholder="#6c7086",
    accent_text="#89b4fa",
    track="#313244",
    knob="#ffffff",
    shadow_color="#00000066",
    selection_bg="#89b4fa",
    selection_fg="#11111b",
    scrollbar_thumb="#45475a",
    scrollbar_thumb_hover="#585b70",
    scrollbar_track="#181825",
)

LIGHT_THEME = Theme(
    name="light",
    is_dark=False,
    bg_window="#eff1f5",
    bg_surface="#ffffff",
    bg_surface_alt="#e6e9ef",
    bg_card="#ffffff",
    bg_input="#ffffff",
    bg_hover="#dce0e8",
    bg_active="#ccd0da",
    surface_raised="#e6e9ef",
    surface_overlay="#ffffff",
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
    success_hover="#5cb83c",
    success_press="#358424",
    success_text="#ffffff",
    warning="#df8e1d",
    warning_hover="#f0a535",
    warning_press="#be7918",
    warning_text="#ffffff",
    danger="#d20f39",
    danger_hover="#e6395c",
    danger_press="#b00d30",
    danger_text="#ffffff",
    info="#209fb5",
    info_hover="#34b4ca",
    info_press="#1b8598",
    info_text="#ffffff",
    text="#4c4f69",
    text_muted="#6c6f85",
    text_disabled="#9ca0b0",
    placeholder="#9ca0b0",
    accent_text="#1e66f5",
    track="#dce0e8",
    knob="#ffffff",
    shadow_color="#00000022",
    selection_bg="#1e66f5",
    selection_fg="#ffffff",
    scrollbar_thumb="#ccd0da",
    scrollbar_thumb_hover="#bcc0cc",
    scrollbar_track="#e6e9ef",
)

NORD_THEME = Theme(
    name="nord",
    is_dark=True,
    bg_window="#2e3440",
    bg_surface="#3b4252",
    bg_surface_alt="#2e3440",
    bg_card="#3b4252",
    bg_input="#2e3440",
    bg_hover="#434c5e",
    bg_active="#4c566a",
    surface_raised="#434c5e",
    surface_overlay="#2e3440",
    border="#434c5e",
    border_subtle="#3b4252",
    border_focused="#88c0d0",
    primary="#88c0d0",
    primary_hover="#8fbcbb",
    primary_press="#81a1c1",
    primary_text="#2e3440",
    secondary="#4c566a",
    secondary_hover="#5e6a82",
    secondary_press="#434c5e",
    secondary_text="#eceff4",
    success="#a3be8c",
    success_hover="#b5d19e",
    success_press="#91ac7a",
    success_text="#2e3440",
    warning="#ebcb8b",
    warning_hover="#f4db9f",
    warning_press="#dfbc75",
    warning_text="#2e3440",
    danger="#bf616a",
    danger_hover="#d0757e",
    danger_press="#ab5059",
    danger_text="#ffffff",
    info="#5e81ac",
    info_hover="#7295bf",
    info_press="#4c6f99",
    info_text="#ffffff",
    text="#eceff4",
    text_muted="#d8dee9",
    text_disabled="#4c566a",
    placeholder="#4c566a",
    accent_text="#88c0d0",
    track="#3b4252",
    knob="#eceff4",
    shadow_color="#00000055",
    selection_bg="#88c0d0",
    selection_fg="#2e3440",
    scrollbar_thumb="#4c566a",
    scrollbar_thumb_hover="#5e6a82",
    scrollbar_track="#2e3440",
)

DRACULA_THEME = Theme(
    name="dracula",
    is_dark=True,
    bg_window="#282a36",
    bg_surface="#44475a",
    bg_surface_alt="#21222c",
    bg_card="#343746",
    bg_input="#21222c",
    bg_hover="#6272a4",
    bg_active="#505b82",
    surface_raised="#44475a",
    surface_overlay="#21222c",
    border="#6272a4",
    border_subtle="#44475a",
    border_focused="#bd93f9",
    primary="#bd93f9",
    primary_hover="#caa6fa",
    primary_press="#ab7af5",
    primary_text="#282a36",
    secondary="#44475a",
    secondary_hover="#6272a4",
    secondary_press="#383a4c",
    secondary_text="#f8f8f2",
    success="#50fa7b",
    success_hover="#69fb8d",
    success_press="#38e865",
    success_text="#282a36",
    warning="#f1fa8c",
    warning_hover="#f4fb9f",
    warning_press="#e3ed70",
    warning_text="#282a36",
    danger="#ff5555",
    danger_hover="#ff6e6e",
    danger_press="#ea4040",
    danger_text="#ffffff",
    info="#8be9fd",
    info_hover="#a2effe",
    info_press="#6eddfa",
    info_text="#282a36",
    text="#f8f8f2",
    text_muted="#bfbfbf",
    text_disabled="#6272a4",
    placeholder="#6272a4",
    accent_text="#bd93f9",
    track="#44475a",
    knob="#f8f8f2",
    shadow_color="#00000077",
    selection_bg="#bd93f9",
    selection_fg="#282a36",
    scrollbar_thumb="#6272a4",
    scrollbar_thumb_hover="#7385be",
    scrollbar_track="#21222c",
)

TOKYO_NIGHT_THEME = Theme(
    name="tokyo-night",
    is_dark=True,
    bg_window="#1a1b26",
    bg_surface="#24283b",
    bg_surface_alt="#1f2335",
    bg_card="#24283b",
    bg_input="#1f2335",
    bg_hover="#414868",
    bg_active="#565f89",
    surface_raised="#2f354e",
    surface_overlay="#1f2335",
    border="#414868",
    border_subtle="#2f354e",
    border_focused="#7aa2f7",
    primary="#7aa2f7",
    primary_hover="#8fb3f9",
    primary_press="#638ee6",
    primary_text="#1a1b26",
    secondary="#414868",
    secondary_hover="#565f89",
    secondary_press="#343a54",
    secondary_text="#c0caf5",
    success="#9ece6a",
    success_hover="#aedf7b",
    success_press="#8cbe58",
    success_text="#1a1b26",
    warning="#e0af68",
    warning_hover="#e8be7d",
    warning_press="#cca056",
    warning_text="#1a1b26",
    danger="#f7768e",
    danger_hover="#f98e9f",
    danger_press="#e66079",
    danger_text="#ffffff",
    info="#7dcfff",
    info_hover="#96daff",
    info_press="#64c2f6",
    info_text="#1a1b26",
    text="#c0caf5",
    text_muted="#9aa5ce",
    text_disabled="#565f89",
    placeholder="#565f89",
    accent_text="#7aa2f7",
    track="#2f354e",
    knob="#c0caf5",
    shadow_color="#00000066",
    selection_bg="#7aa2f7",
    selection_fg="#1a1b26",
    scrollbar_thumb="#414868",
    scrollbar_thumb_hover="#565f89",
    scrollbar_track="#1f2335",
)


# ============================================================================
# OS Theme Detection
# ============================================================================

def detect_system_theme() -> str:
    """
    Detect whether the host OS is in dark mode or light mode.
    Falls back gracefully to 'dark'.
    """
    try:
        import darkdetect  # type: ignore
        detected = darkdetect.theme()
        if detected and str(detected).lower() in ("dark", "light"):
            return str(detected).lower()
    except Exception:
        pass

    # Linux GTK/Freedesktop schema query fallback
    if sys.platform.startswith("linux"):
        try:
            import subprocess
            out = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if "dark" in out.stdout.lower():
                return "dark"
            elif "light" in out.stdout.lower():
                return "light"
        except Exception:
            pass

    return "dark"


# ============================================================================
# TTK Style Builder with Durable User Options Layer (Adapted from ttkbootstrap)
# ============================================================================

DURABLE_STYLE_OPTIONS = frozenset({
    "padding",
    "borderwidth",
    "focusthickness",
    "thickness",
    "rowheight",
    "sashthickness",
    "gripcount",
    "tabmargins",
    "arrowsize",
    "anchor",
    "font",
    "relief",
    "justify",
    "insertwidth",
    "indicatormargin",
    "indicatorsize",
})


class StyleBuilderTTK:
    """
    Configures standard ttk.Style to match design tokens, supporting semantic styles
    (e.g., 'primary.TButton', 'danger.TButton', 'success.Horizontal.TProgressbar')
    and preserving durable user configuration across theme switches.
    """

    def __init__(self, style: Optional[ttk.Style] = None, master: Optional[tk.Misc] = None):
        self._style = style
        self._master = master
        self._user_options: Dict[str, Dict[str, Any]] = {}

    @property
    def style(self) -> ttk.Style:
        if self._style is None:
            self._style = ttk.Style(master=self._master)
        return self._style

    def set_user_option(self, style_name: str, **kwargs) -> None:
        """Record a user customization option that must survive theme changes."""
        filtered = {k: v for k, v in kwargs.items() if k in DURABLE_STYLE_OPTIONS}
        if filtered:
            if style_name not in self._user_options:
                self._user_options[style_name] = {}
            self._user_options[style_name].update(filtered)

    def apply(self, theme: Theme, master: Optional[tk.Misc] = None) -> Optional[ttk.Style]:
        target_master = master or self._master or getattr(tk, "_default_root", None)
        if self._style is None:
            if target_master is None:
                return None
            try:
                self._style = ttk.Style(master=target_master)
            except Exception:
                return None
        elif master is not None and master != self._master:
            try:
                self._style = ttk.Style(master=master)
                self._master = master
            except Exception:
                pass

        style = self._style

        # Ensure 'clam' base engine is selected for clean flat vector colors
        try:
            available_themes = style.theme_names()
            if "clam" in available_themes and style.theme_use() != "clam":
                style.theme_use("clam")
        except Exception:
            pass

        # Global style defaults
        style.configure(
            ".",
            background=theme.bg_window,
            foreground=theme.text,
            troughcolor=theme.track,
            focuscolor=theme.border_focused,
            bordercolor=theme.border,
            darkcolor=theme.bg_surface,
            lightcolor=theme.bg_surface_alt,
            selectbackground=theme.selection_bg,
            selectforeground=theme.selection_fg,
            font=(theme.font_family, int(theme.font_size_md)),
        )

        # Frames & LabelFrames
        style.configure("TFrame", background=theme.bg_card)
        style.configure("Window.TFrame", background=theme.bg_window)
        style.configure("Surface.TFrame", background=theme.bg_surface)
        style.configure("Card.TFrame", background=theme.bg_card)
        style.configure(
            "TLabelframe",
            background=theme.bg_card,
            bordercolor=theme.border,
            darkcolor=theme.border,
            lightcolor=theme.border,
        )
        style.configure(
            "TLabelframe.Label",
            background=theme.bg_card,
            foreground=theme.text,
            font=(theme.font_family, int(theme.font_size_sm), "bold"),
        )

        # Labels
        style.configure("TLabel", background=theme.bg_card, foreground=theme.text)
        style.configure("Muted.TLabel", background=theme.bg_card, foreground=theme.text_muted)
        style.configure("Heading.TLabel", background=theme.bg_card, foreground=theme.primary, font=(theme.font_family, int(theme.font_size_lg), "bold"))
        style.configure("Title.TLabel", background=theme.bg_card, foreground=theme.text, font=(theme.font_family, int(theme.font_size_xl), "bold"))

        # Base TButton
        style.configure(
            "TButton",
            background=theme.secondary,
            foreground=theme.secondary_text,
            bordercolor=theme.border,
            focuscolor=theme.border_focused,
            lightcolor=theme.secondary_hover,
            darkcolor=theme.secondary_press,
            padding=(12, 6),
        )
        style.map(
            "TButton",
            background=[("pressed", theme.secondary_press), ("active", theme.secondary_hover), ("disabled", theme.bg_surface)],
            foreground=[("disabled", theme.text_disabled)],
        )

        # Semantic Button Styles
        for var_name, normal, hover, press, fg in [
            ("primary", theme.primary, theme.primary_hover, theme.primary_press, theme.primary_text),
            ("secondary", theme.secondary, theme.secondary_hover, theme.secondary_press, theme.secondary_text),
            ("success", theme.success, theme.success_hover, theme.success_press, theme.success_text),
            ("warning", theme.warning, theme.warning_hover, theme.warning_press, theme.warning_text),
            ("danger", theme.danger, theme.danger_hover, theme.danger_press, theme.danger_text),
            ("info", theme.info, theme.info_hover, theme.info_press, theme.info_text),
        ]:
            s_name = f"{var_name}.TButton"
            style.configure(
                s_name,
                background=normal,
                foreground=fg,
                bordercolor=normal,
                focuscolor=hover,
                lightcolor=hover,
                darkcolor=press,
                padding=(12, 6),
            )
            style.map(
                s_name,
                background=[("pressed", press), ("active", hover), ("disabled", theme.bg_surface)],
                foreground=[("disabled", theme.text_disabled)],
            )

            # Outline variants
            out_name = f"outline.{var_name}.TButton"
            style.configure(
                out_name,
                background=theme.bg_card,
                foreground=normal,
                bordercolor=normal,
                focuscolor=normal,
                padding=(12, 6),
            )
            style.map(
                out_name,
                background=[("pressed", press), ("active", normal), ("disabled", theme.bg_card)],
                foreground=[("pressed", fg), ("active", fg), ("disabled", theme.text_disabled)],
            )

        # TEntry
        style.configure(
            "TEntry",
            fieldbackground=theme.bg_input,
            foreground=theme.text,
            insertcolor=theme.primary,
            bordercolor=theme.border,
            lightcolor=theme.border_focused,
            darkcolor=theme.border,
            padding=6,
        )
        style.map("TEntry", bordercolor=[("focus", theme.border_focused)])

        # TCombobox
        style.configure(
            "TCombobox",
            fieldbackground=theme.bg_input,
            background=theme.secondary,
            foreground=theme.text,
            arrowcolor=theme.text,
            bordercolor=theme.border,
            padding=6,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", theme.bg_input)],
            background=[("active", theme.secondary_hover)],
            bordercolor=[("focus", theme.border_focused)],
        )

        # Progressbars
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor=theme.track,
            background=theme.primary,
            bordercolor=theme.track,
            darkcolor=theme.primary,
            lightcolor=theme.primary,
            thickness=8,
        )
        for var_name, col in [
            ("primary", theme.primary),
            ("success", theme.success),
            ("warning", theme.warning),
            ("danger", theme.danger),
            ("info", theme.info),
        ]:
            style.configure(f"{var_name}.Horizontal.TProgressbar", background=col, darkcolor=col, lightcolor=col)

        # Checkbutton & Radiobutton
        style.configure("TCheckbutton", background=theme.bg_card, foreground=theme.text, indicatorbackground=theme.bg_input, indicatorforeground=theme.primary)
        style.map("TCheckbutton", indicatorcolor=[("selected", theme.primary), ("active", theme.bg_hover)])
        style.configure("TRadiobutton", background=theme.bg_card, foreground=theme.text, indicatorbackground=theme.bg_input)
        style.map("TRadiobutton", indicatorcolor=[("selected", theme.primary), ("active", theme.bg_hover)])

        # TNotebook
        style.configure("TNotebook", background=theme.bg_surface, tabmargins=[2, 5, 2, 0])
        style.configure(
            "TNotebook.Tab",
            background=theme.bg_surface_alt,
            foreground=theme.text_muted,
            padding=[14, 6],
            bordercolor=theme.border,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", theme.bg_card), ("active", theme.bg_hover)],
            foreground=[("selected", theme.primary), ("active", theme.text)],
        )

        # Treeview
        style.configure(
            "Treeview",
            background=theme.bg_input,
            foreground=theme.text,
            fieldbackground=theme.bg_input,
            bordercolor=theme.border,
            rowheight=28,
        )
        style.map(
            "Treeview",
            background=[("selected", theme.selection_bg)],
            foreground=[("selected", theme.selection_fg)],
        )
        style.configure(
            "Treeview.Heading",
            background=theme.bg_surface,
            foreground=theme.text,
            bordercolor=theme.border,
            padding=[8, 4],
            font=(theme.font_family, int(theme.font_size_sm), "bold"),
        )
        style.map("Treeview.Heading", background=[("active", theme.bg_hover)])

        # Replay durable user options that were set on specific styles
        for s_name, opts in self._user_options.items():
            try:
                style.configure(s_name, **opts)
            except Exception:
                pass

        return style


def apply_ttk_theme(theme: Theme, style: Optional[ttk.Style] = None, master: Optional[tk.Misc] = None) -> Optional[ttk.Style]:
    """Configure ttk.Style to seamlessly match the specified Theme tokens."""
    if style is None and master is None and getattr(tk, "_default_root", None) is None:
        return None
    builder = StyleBuilderTTK(style=style, master=master)
    return builder.apply(theme, master=master)


# ============================================================================
# Ancestral Background Resolution & Dynamic Theme Application
# ============================================================================

def _find_ancestral_bg(widget: tk.Misc, theme: Theme) -> str:
    """Find effective contextual background for a standard Tk widget."""
    cur = getattr(widget, "master", None)
    while cur is not None:
        try:
            if hasattr(cur, "_title") and (hasattr(cur, "_surface") or hasattr(cur, "surface")):
                if hasattr(cur, "_custom_bg_color") and cur._custom_bg_color is not None:
                    return str(cur._custom_bg_color)
                return theme.bg_card

            master = getattr(cur, "master", None)
            if master is not None and hasattr(master, "content") and master.content is cur:
                if hasattr(master, "_custom_bg_color") and master._custom_bg_color is not None:
                    return str(master._custom_bg_color)
                return theme.bg_card

            if hasattr(cur, "_bg_color"):
                if hasattr(cur, "_custom_bg_color") and cur._custom_bg_color is not None:
                    return str(cur._custom_bg_color)
                return theme.bg_surface

            if hasattr(cur, "_custom_parent_bg") and cur._custom_parent_bg:
                return str(cur._custom_parent_bg)
        except Exception:
            pass
        cur = getattr(cur, "master", None)
    return theme.bg_window


def apply_theme(root_or_widget: tk.Misc, theme: Optional[Theme] = None, recurse: bool = True) -> None:
    """
    Recursively apply theme styling to a Tk/ttk widget hierarchy with context awareness.
    """
    t = theme or ThemeManager.get_theme()
    if not root_or_widget.winfo_exists():
        return

    try:
        apply_ttk_theme(t, master=root_or_widget)
    except Exception:
        pass

    def _apply_node(widget: tk.Misc):
        if not widget.winfo_exists():
            return

        is_modern = hasattr(widget, "surface") or hasattr(widget, "_surface") or hasattr(widget, "_photo")

        if is_modern:
            if hasattr(widget, "_on_theme_changed"):
                try:
                    widget._on_theme_changed(t)
                except Exception:
                    pass
        else:
            w_class = widget.winfo_class()
            ctx_bg = _find_ancestral_bg(widget, t)

            try:
                if w_class in ("Tk", "Toplevel"):
                    widget.configure(bg=t.bg_window)
                elif w_class == "Frame":
                    widget.configure(bg=ctx_bg)
                elif w_class == "Label":
                    widget.configure(bg=ctx_bg, fg=t.text)
                elif w_class == "Button":
                    widget.configure(
                        bg=t.secondary,
                        fg=t.secondary_text,
                        activebackground=t.secondary_hover,
                        activeforeground=t.secondary_text,
                        relief="flat",
                        highlightthickness=0,
                    )
                elif w_class in ("Entry", "Text"):
                    widget.configure(
                        bg=t.bg_input,
                        fg=t.text,
                        insertbackground=t.primary,
                        selectbackground=t.selection_bg,
                        selectforeground=t.selection_fg,
                        highlightcolor=t.border_focused,
                        highlightbackground=t.border,
                        relief="flat",
                    )
                elif w_class == "Listbox":
                    widget.configure(
                        bg=t.bg_input,
                        fg=t.text,
                        selectbackground=t.selection_bg,
                        selectforeground=t.selection_fg,
                        highlightcolor=t.border_focused,
                        highlightbackground=t.border,
                    )
                elif w_class == "Canvas":
                    widget.configure(bg=ctx_bg, highlightthickness=0)
                elif w_class == "Scrollbar":
                    widget.configure(
                        bg=t.scrollbar_thumb,
                        troughcolor=t.scrollbar_track,
                        activebackground=t.scrollbar_thumb_hover,
                        highlightthickness=0,
                    )
            except Exception:
                pass

        if recurse:
            for child in widget.winfo_children():
                try:
                    _apply_node(child)
                except Exception:
                    pass

    _apply_node(root_or_widget)


# ============================================================================
# Theme Manager Singleton
# ============================================================================

class _ThemeManager:
    """
    Global theme manager singleton managing registered themes, listeners,
    JSON loading/exporting, and automatic root window live synchronization.
    """

    def __init__(self):
        self._current_theme: Theme = DARK_THEME
        self._registry: Dict[str, Theme] = {
            "dark": DARK_THEME,
            "light": LIGHT_THEME,
            "nord": NORD_THEME,
            "dracula": DRACULA_THEME,
            "tokyo-night": TOKYO_NIGHT_THEME,
        }
        self._listeners: Set[Callable[[Theme], None]] = set()
        self._bound_roots: Set[tk.Misc] = set()
        self.animations_enabled: bool = True
        self.builder = StyleBuilderTTK()

    @property
    def theme(self) -> Theme:
        return self._current_theme

    def get_theme(self) -> Theme:
        return self._current_theme

    def register_theme(self, name: str, theme: Theme) -> None:
        """Register a custom theme preset."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Theme name must be a non-empty string.")
        if not isinstance(theme, Theme):
            raise TypeError(f"Expected Theme instance, got {type(theme)}")
        self._registry[name.lower()] = theme

    def unregister_theme(self, name: str) -> None:
        """Unregister a theme preset."""
        key = name.lower()
        if key in ("dark", "light"):
            raise ValueError(f"Cannot unregister builtin theme: {name}")
        self._registry.pop(key, None)

    def get_registered_themes(self) -> Dict[str, Theme]:
        """Return a copy of registered themes dictionary."""
        return dict(self._registry)

    def set_theme(self, theme: Union[Theme, str]) -> None:
        """Switch active theme and notify all listeners and bound windows."""
        if isinstance(theme, str):
            key = theme.lower()
            if key in self._registry:
                self._current_theme = self._registry[key]
            else:
                raise ValueError(f"Unknown theme name: {theme}. Registered themes: {list(self._registry.keys())}")
        elif isinstance(theme, Theme):
            self._current_theme = theme
        else:
            raise TypeError(f"Expected Theme or str, got {type(theme)}")

        # Configure ttk styles across bound roots or active default root
        for root in list(self._bound_roots):
            try:
                if root.winfo_exists():
                    self.builder.apply(self._current_theme, master=root)
            except Exception:
                pass
        if getattr(tk, "_default_root", None) is not None:
            try:
                self.builder.apply(self._current_theme, master=tk._default_root)
            except Exception:
                pass

        # Update bound root windows
        dead_roots = set()
        for root in list(self._bound_roots):
            try:
                if root.winfo_exists():
                    apply_theme(root, theme=self._current_theme, recurse=True)
                else:
                    dead_roots.add(root)
            except Exception:
                dead_roots.add(root)
        self._bound_roots.difference_update(dead_roots)

        # Notify all registered widget listeners
        for listener in list(self._listeners):
            try:
                listener(self._current_theme)
            except Exception:
                pass

    def toggle_theme(self) -> Theme:
        """Toggle between light and dark themes."""
        if self._current_theme.name == "dark":
            self.set_theme(LIGHT_THEME)
        else:
            self.set_theme(DARK_THEME)
        return self._current_theme

    def load_theme_json(self, filepath: str) -> Theme:
        """Load and register a theme definition from a JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        theme = Theme.from_dict(data)
        self.register_theme(theme.name, theme)
        return theme

    def export_theme_json(self, theme: Union[Theme, str], filepath: str) -> None:
        """Export a theme definition to a JSON file."""
        t = self._registry[theme.lower()] if isinstance(theme, str) else theme
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(t.to_dict(), f, indent=2)

    def bind_root(self, root: tk.Misc) -> None:
        """
        Bind a root or toplevel window for automatic live synchronization on theme change.
        """
        self._bound_roots.add(root)
        if root.winfo_exists():
            try:
                self.builder.apply(self._current_theme, master=root)
            except Exception:
                pass
            apply_theme(root, theme=self._current_theme, recurse=True)

    def unbind_root(self, root: tk.Misc) -> None:
        """Unbind a root window from automatic theme updates."""
        self._bound_roots.discard(root)

    def subscribe(self, listener: Callable[[Theme], None]) -> None:
        """Subscribe a callback to theme changes."""
        self._listeners.add(listener)

    def unsubscribe(self, listener: Callable[[Theme], None]) -> None:
        """Unsubscribe a callback from theme changes."""
        self._listeners.discard(listener)

    def detect_and_apply_system_theme(self) -> str:
        """Detect OS theme and apply it."""
        sys_theme = detect_system_theme()
        if sys_theme in self._registry:
            self.set_theme(sys_theme)
        return sys_theme


ThemeManager = _ThemeManager()
