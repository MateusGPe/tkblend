"""
Pure-Python vector theme and color palette management for tkblend.
Provides semantic colors, built-in Dark and Light themes, and dynamic theme change notification.
"""

from __future__ import annotations
import inspect
import logging
import threading
import weakref
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Callable, Optional, Union, Tuple, List

logger = logging.getLogger(__name__)


def _format_alpha(alpha: Optional[Union[float, int]]) -> str:
    if alpha is None:
        return ""
    a_int = int(alpha * 255) if isinstance(alpha, float) and alpha <= 1.0 else int(alpha)
    a_int = max(0, min(255, a_int))
    return f"{a_int:02x}"


def resolve_color_failsafe(
    color: Any,
    master: Optional[Any] = None,
    fallback: Optional[str] = None,
    alpha: Optional[Union[float, int]] = None,
    palette: Optional[Palette] = None,
) -> str:
    """
    Fail-safe color resolution supporting:
    - Hex strings (#RGB, #RRGGBB, #RRGGBBAA)
    - Semantic palette tokens (e.g. 'primary', 'bg', 'card_bg')
    - Named web colors ('white', 'black', 'gray', etc.)
    - Tk system color names ('SystemButtonFace', 'SystemWindow', 'gray85', etc.) converted via winfo_rgb
    - Fallback color (defaults to active palette.bg) if lookup or parse fails.
    """
    active_pal = palette or get_theme()
    default_bg = fallback or active_pal.bg

    if color is None:
        return default_bg

    if not isinstance(color, str):
        try:
            color = str(color)
        except Exception as e:
            logger.debug("Failed converting color object to string: %s", e, exc_info=True)
            return default_bg

    c_clean = color.strip()
    if not c_clean:
        return default_bg

    # Check semantic token in active palette
    pal_obj = active_pal
    token = c_clean.lower().replace("-", "_")
    synonyms = {
        "dark": "bg",
        "light": "bg",
        "background": "bg",
        "foreground": "fg",
        "card": "card_bg",
        "border": "card_border",
    }
    if token in synonyms:
        token = synonyms[token]

    if hasattr(pal_obj, token):
        val = getattr(pal_obj, token)
        if isinstance(val, str) and val.startswith("#"):
            c_clean = val

    if c_clean.startswith("#"):
        hex_val = c_clean.lstrip("#")
        if len(hex_val) == 3:
            hex_val = "".join(ch + ch for ch in hex_val)
        if len(hex_val) == 6:
            if alpha is not None:
                return f"#{hex_val}{_format_alpha(alpha)}"
            return f"#{hex_val}"
        elif len(hex_val) == 8:
            if alpha is not None:
                return f"#{hex_val[:6]}{_format_alpha(alpha)}"
            return f"#{hex_val}"
        elif len(hex_val) in (4, 5, 7):
            pass

    # Common named colors map
    named_map = {
        "transparent": "#00000000",
        "white": "#ffffff",
        "black": "#000000",
        "red": "#ff0000",
        "green": "#00ff00",
        "blue": "#0000ff",
        "yellow": "#ffff00",
        "cyan": "#00ffff",
        "magenta": "#ff00ff",
        "gray": "#808080",
        "grey": "#808080",
        "silver": "#c0c0c0",
        "maroon": "#800000",
        "olive": "#808000",
        "lime": "#00ff00",
        "aqua": "#00ffff",
        "teal": "#008080",
        "navy": "#000080",
        "purple": "#800080",
        "orange": "#ffa500",
    }
    low = c_clean.lower()
    if low in named_map:
        base = named_map[low]
        if alpha is not None and len(base) == 7:
            return f"{base}{_format_alpha(alpha)}"
        return base

    # Try Tkinter winfo_rgb to convert system or X11 color names (e.g. 'SystemButtonFace', 'gray85')
    win = master
    if win is None:
        try:
            import tkinter as tk
            win = getattr(tk, "_default_root", None)
        except Exception as e:
            logger.debug("Failed checking tk._default_root for color conversion: %s", e)

    if win is not None and hasattr(win, "winfo_rgb"):
        try:
            r16, g16, b16 = win.winfo_rgb(c_clean)
            r8, g8, b8 = (r16 >> 8) & 0xFF, (g16 >> 8) & 0xFF, (b16 >> 8) & 0xFF
            hex_str = f"#{r8:02x}{g8:02x}{b8:02x}"
            if alpha is not None:
                return f"{hex_str}{_format_alpha(alpha)}"
            return hex_str
        except Exception as e:
            logger.debug("winfo_rgb failed for color '%s': %s", c_clean, e)

    # Fallback if unresolvable
    return default_bg


def resolve_theme_color(c: str, alpha: Optional[Union[float, int]] = None) -> str:
    """
    Resolve a hex code, named color, or semantic palette token (e.g. 'primary', 'bg', 'card_bg')
    into a valid #RRGGBB or #RRGGBBAA hex string.
    """
    return resolve_color_failsafe(c, alpha=alpha)


def blend_color_hex(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex color strings at factor t (0.0 to 1.0)."""
    if t <= 0.0:
        return c1
    if t >= 1.0:
        return c2
    try:
        from tkblend._tkblend import Color
        col1 = Color.from_hex(c1)
        col2 = Color.from_hex(c2)
        res = col1.lerp(col2, float(t))
        if col1.a < 255 or col2.a < 255:
            return f"#{res.r:02x}{res.g:02x}{res.b:02x}{res.a:02x}"
        return f"#{res.r:02x}{res.g:02x}{res.b:02x}"
    except Exception as e:
        logger.warning("Failed blending colors '%s' and '%s': %s", c1, c2, e)
        return c1 if t < 0.5 else c2


def adjust_brightness(hex_code: str, factor: float) -> str:
    """Lighten (> 1.0) or darken (< 1.0) a hex color."""
    try:
        from tkblend._tkblend import Color
        col = Color.from_hex(hex_code)
        if factor >= 1.0:
            res = col.lighten(float(factor))
        else:
            res = col.darken(float(factor))
        if col.a < 255:
            return f"#{res.r:02x}{res.g:02x}{res.b:02x}{res.a:02x}"
        return f"#{res.r:02x}{res.g:02x}{res.b:02x}"
    except Exception as e:
        logger.warning("Failed adjusting brightness for '%s' by factor %s: %s", hex_code, factor, e)
        return hex_code


@dataclass
class Palette:
    """Semantic color palette definition for vector widgets."""
    name: str = "dark"
    dark_mode: bool = True

    # Canvas & Window background
    bg: str = "#100e14"
    fg: str = "#e6e0e9"
    text_muted: str = "#cac4d0"

    # Surface & Containers
    card_bg: str = "#25232a"
    card_border: str = "#49454f"
    surface: str = "#1d1b20"
    surface_border: str = "#36343b"

    # Primary brand accent
    primary: str = "#d0bcff"
    primary_hover: str = "#e8def8"
    primary_active: str = "#b69df8"
    primary_fg: str = "#381e72"

    # Secondary action
    secondary: str = "#4a4458"
    secondary_hover: str = "#585168"
    secondary_active: str = "#332d41"
    secondary_fg: str = "#e8def8"

    # Status & Accent colors
    accent: str = "#efb8c8"
    success: str = "#85d697"
    warning: str = "#ffb877"
    destructive: str = "#ffb4ab"

    # Inputs & Controls
    input_bg: str = "#1d1b20"
    input_border: str = "#49454f"
    input_focus: str = "#d0bcff"
    track_bg: str = "#36343b"
    thumb_color: str = "#d0bcff"
    shadow_color: str = "#00000055"


DARK_PALETTE = Palette(
    name="dark",
    dark_mode=True,
    bg="#100e14",
    fg="#e6e0e9",
    text_muted="#cac4d0",
    card_bg="#25232a",
    card_border="#49454f",
    surface="#1d1b20",
    surface_border="#36343b",
    primary="#d0bcff",
    primary_hover="#e8def8",
    primary_active="#b69df8",
    primary_fg="#381e72",
    secondary="#4a4458",
    secondary_hover="#585168",
    secondary_active="#332d41",
    secondary_fg="#e8def8",
    accent="#efb8c8",
    success="#85d697",
    warning="#ffb877",
    destructive="#ffb4ab",
    input_bg="#1d1b20",
    input_border="#49454f",
    input_focus="#d0bcff",
    track_bg="#36343b",
    thumb_color="#d0bcff",
    shadow_color="#00000055",
)

LIGHT_PALETTE = Palette(
    name="light",
    dark_mode=False,
    bg="#f8f4fa",
    fg="#1d1b20",
    text_muted="#49454f",
    card_bg="#ffffff",
    card_border="#cac4d0",
    surface="#f0eaf4",
    surface_border="#e7e0ec",
    primary="#6750a4",
    primary_hover="#7f67be",
    primary_active="#533d8b",
    primary_fg="#ffffff",
    secondary="#e8def8",
    secondary_hover="#ded3ee",
    secondary_active="#cbbcdb",
    secondary_fg="#1d192b",
    accent="#7d5260",
    success="#2e6c43",
    warning="#8f4c00",
    destructive="#ba1a1a",
    input_bg="#ffffff",
    input_border="#79747e",
    input_focus="#6750a4",
    track_bg="#e7e0ec",
    thumb_color="#6750a4",
    shadow_color="#00000010",
)

DRACULA_PALETTE = Palette(
    name="dracula",
    dark_mode=True,
    bg="#282a36",
    fg="#f8f8f2",
    text_muted="#6272a4",
    card_bg="#343746",
    card_border="#44475a",
    surface="#21222c",
    surface_border="#44475a",
    primary="#bd93f9",
    primary_hover="#caa6fc",
    primary_active="#a777f5",
    primary_fg="#282a36",
    secondary="#6272a4",
    secondary_hover="#7283b5",
    secondary_active="#526190",
    secondary_fg="#f8f8f2",
    accent="#ff79c6",
    success="#50fa7b",
    warning="#ffb86c",
    destructive="#ff5555",
    input_bg="#21222c",
    input_border="#6272a4",
    input_focus="#bd93f9",
    track_bg="#44475a",
    thumb_color="#bd93f9",
    shadow_color="#00000060",
)

NORD_PALETTE = Palette(
    name="nord",
    dark_mode=True,
    bg="#2e3440",
    fg="#eceff4",
    text_muted="#d8dee9",
    card_bg="#434c5e",
    card_border="#4c566a",
    surface="#3b4252",
    surface_border="#4c566a",
    primary="#88c0d0",
    primary_hover="#8fbcbb",
    primary_active="#81a1c1",
    primary_fg="#2e3440",
    secondary="#4c566a",
    secondary_hover="#5b677e",
    secondary_active="#3f4756",
    secondary_fg="#eceff4",
    accent="#81a1c1",
    success="#a3be8c",
    warning="#ebcb8b",
    destructive="#bf616a",
    input_bg="#3b4252",
    input_border="#4c566a",
    input_focus="#88c0d0",
    track_bg="#4c566a",
    thumb_color="#88c0d0",
    shadow_color="#00000050",
)

TOKYO_NIGHT_PALETTE = Palette(
    name="tokyo_night",
    dark_mode=True,
    bg="#1a1b26",
    fg="#c0caf5",
    text_muted="#7aa2f7",
    card_bg="#24283b",
    card_border="#414868",
    surface="#16161e",
    surface_border="#292e42",
    primary="#7aa2f7",
    primary_hover="#89b4fa",
    primary_active="#628be0",
    primary_fg="#15161e",
    secondary="#414868",
    secondary_hover="#565f89",
    secondary_active="#343b58",
    secondary_fg="#c0caf5",
    accent="#bb9af7",
    success="#9ece6a",
    warning="#e0af68",
    destructive="#f7768e",
    input_bg="#16161e",
    input_border="#414868",
    input_focus="#7aa2f7",
    track_bg="#292e42",
    thumb_color="#7aa2f7",
    shadow_color="#00000066",
)

CATPPUCCIN_MOCHA_PALETTE = Palette(
    name="catppuccin_mocha",
    dark_mode=True,
    bg="#1e1e2e",
    fg="#cdd6f4",
    text_muted="#a6adc8",
    card_bg="#313244",
    card_border="#45475a",
    surface="#181825",
    surface_border="#313244",
    primary="#cba6f7",
    primary_hover="#d5b4fc",
    primary_active="#b485ee",
    primary_fg="#11111b",
    secondary="#45475a",
    secondary_hover="#585b70",
    secondary_active="#313244",
    secondary_fg="#cdd6f4",
    accent="#f5c2e7",
    success="#a6e3a1",
    warning="#f9e2af",
    destructive="#f38ba8",
    input_bg="#181825",
    input_border="#45475a",
    input_focus="#cba6f7",
    track_bg="#313244",
    thumb_color="#cba6f7",
    shadow_color="#00000066",
)

CATPPUCCIN_LATTE_PALETTE = Palette(
    name="catppuccin_latte",
    dark_mode=False,
    bg="#eff1f5",
    fg="#4c4f69",
    text_muted="#6c6f85",
    card_bg="#ffffff",
    card_border="#ccd0da",
    surface="#e6e9ef",
    surface_border="#ccd0da",
    primary="#8839ef",
    primary_hover="#9a52f4",
    primary_active="#7222df",
    primary_fg="#ffffff",
    secondary="#ccd0da",
    secondary_hover="#bcc0cc",
    secondary_active="#acb0be",
    secondary_fg="#4c4f69",
    accent="#ea76cb",
    success="#40a02b",
    warning="#df8e1d",
    destructive="#d20f39",
    input_bg="#ffffff",
    input_border="#bcc0cc",
    input_focus="#8839ef",
    track_bg="#dce0e8",
    thumb_color="#8839ef",
    shadow_color="#00000010",
)

CYBERPUNK_PALETTE = Palette(
    name="cyberpunk",
    dark_mode=True,
    bg="#0d0b18",
    fg="#00f0ff",
    text_muted="#9b72cf",
    card_bg="#1e1938",
    card_border="#ff007f",
    surface="#151226",
    surface_border="#2c2250",
    primary="#ff007f",
    primary_hover="#ff3399",
    primary_active="#d9006c",
    primary_fg="#ffffff",
    secondary="#2c2250",
    secondary_hover="#3d306b",
    secondary_active="#20183b",
    secondary_fg="#00f0ff",
    accent="#ffe600",
    success="#00ff9f",
    warning="#ff8c00",
    destructive="#ff0055",
    input_bg="#151226",
    input_border="#ff007f88",
    input_focus="#00f0ff",
    track_bg="#2b214a",
    thumb_color="#00f0ff",
    shadow_color="#ff007f33",
)

EMERALD_FOREST_PALETTE = Palette(
    name="emerald_forest",
    dark_mode=True,
    bg="#0b1914",
    fg="#e1f5ec",
    text_muted="#84bfa6",
    card_bg="#19332a",
    card_border="#295243",
    surface="#12251e",
    surface_border="#1f4235",
    primary="#10b981",
    primary_hover="#34d399",
    primary_active="#059669",
    primary_fg="#062319",
    secondary="#24493b",
    secondary_hover="#2f5e4c",
    secondary_active="#19352a",
    secondary_fg="#e1f5ec",
    accent="#38bdf8",
    success="#34d399",
    warning="#fbbf24",
    destructive="#f87171",
    input_bg="#12251e",
    input_border="#295243",
    input_focus="#10b981",
    track_bg="#1e3c31",
    thumb_color="#10b981",
    shadow_color="#00000060",
)

SUNSET_AMBER_PALETTE = Palette(
    name="sunset_amber",
    dark_mode=True,
    bg="#1a120c",
    fg="#faedd9",
    text_muted="#c7a58b",
    card_bg="#36261a",
    card_border="#543b29",
    surface="#261b12",
    surface_border="#422f20",
    primary="#f59e0b",
    primary_hover="#fbbf24",
    primary_active="#d97706",
    primary_fg="#261404",
    secondary="#453222",
    secondary_hover="#5a412d",
    secondary_active="#332417",
    secondary_fg="#faedd9",
    accent="#f43f5e",
    success="#10b981",
    warning="#f59e0b",
    destructive="#ef4444",
    input_bg="#261b12",
    input_border="#543b29",
    input_focus="#f59e0b",
    track_bg="#3d2a1c",
    thumb_color="#f59e0b",
    shadow_color="#00000060",
)

MONOKAI_PRO_PALETTE = Palette(
    name="monokai_pro",
    dark_mode=True,
    bg="#2d2a2e",
    fg="#fcfcfa",
    text_muted="#939293",
    card_bg="#3a373b",
    card_border="#504d51",
    surface="#221f22",
    surface_border="#403d41",
    primary="#ffd866",
    primary_hover="#ffe085",
    primary_active="#e6be47",
    primary_fg="#2d2a2e",
    secondary="#504d51",
    secondary_hover="#625f63",
    secondary_active="#3f3c40",
    secondary_fg="#fcfcfa",
    accent="#78dce8",
    success="#a9dc76",
    warning="#fc9867",
    destructive="#ff6188",
    input_bg="#221f22",
    input_border="#504d51",
    input_focus="#ffd866",
    track_bg="#403d41",
    thumb_color="#ffd866",
    shadow_color="#00000060",
)

SOLARIZED_DARK_PALETTE = Palette(
    name="solarized_dark",
    dark_mode=True,
    bg="#002b36",
    fg="#93a1a1",
    text_muted="#657b83",
    card_bg="#0d4351",
    card_border="#586e75",
    surface="#073642",
    surface_border="#1a4d5a",
    primary="#268bd2",
    primary_hover="#3ea2e8",
    primary_active="#1b74b3",
    primary_fg="#fdf6e3",
    secondary="#586e75",
    secondary_hover="#6c848d",
    secondary_active="#47595f",
    secondary_fg="#fdf6e3",
    accent="#2aa198",
    success="#859900",
    warning="#b58900",
    destructive="#dc322f",
    input_bg="#073642",
    input_border="#586e75",
    input_focus="#268bd2",
    track_bg="#0e4b5a",
    thumb_color="#268bd2",
    shadow_color="#00000060",
)

SOLARIZED_LIGHT_PALETTE = Palette(
    name="solarized_light",
    dark_mode=False,
    bg="#fdf6e3",
    fg="#586e75",
    text_muted="#657b83",
    card_bg="#ffffff",
    card_border="#93a1a1",
    surface="#eee8d5",
    surface_border="#d5cdb8",
    primary="#268bd2",
    primary_hover="#3ea2e8",
    primary_active="#1b74b3",
    primary_fg="#ffffff",
    secondary="#eee8d5",
    secondary_hover="#dfd8c2",
    secondary_active="#cec7b0",
    secondary_fg="#586e75",
    accent="#2aa198",
    success="#859900",
    warning="#b58900",
    destructive="#dc322f",
    input_bg="#ffffff",
    input_border="#93a1a1",
    input_focus="#268bd2",
    track_bg="#e4dec9",
    thumb_color="#268bd2",
    shadow_color="#00000010",
)

THEME_PRESETS: Dict[str, Palette] = {
    "dark": DARK_PALETTE,
    "light": LIGHT_PALETTE,
    "dracula": DRACULA_PALETTE,
    "nord": NORD_PALETTE,
    "tokyo_night": TOKYO_NIGHT_PALETTE,
    "catppuccin_mocha": CATPPUCCIN_MOCHA_PALETTE,
    "catppuccin_latte": CATPPUCCIN_LATTE_PALETTE,
    "cyberpunk": CYBERPUNK_PALETTE,
    "emerald_forest": EMERALD_FOREST_PALETTE,
    "sunset_amber": SUNSET_AMBER_PALETTE,
    "monokai_pro": MONOKAI_PRO_PALETTE,
    "solarized_dark": SOLARIZED_DARK_PALETTE,
    "solarized_light": SOLARIZED_LIGHT_PALETTE,
}


def get_available_themes() -> List[str]:
    """Return list of all registered theme names."""
    return list(ThemeManager().palettes.keys())


def _wrap_listener(callback: Callable[[Palette], None]) -> Any:
    try:
        if inspect.ismethod(callback):
            return weakref.WeakMethod(callback)
        return weakref.ref(callback)
    except TypeError as e:
        logger.debug("Cannot weakly reference callback %r (using strong ref): %s", callback, e)
        return callback


def _unwrap_listener(ref: Any) -> Optional[Callable[[Palette], None]]:
    if isinstance(ref, (weakref.ref, weakref.WeakMethod)):
        return ref()
    return ref


class ThemeManager:
    """Central singleton managing the active theme palette and listeners."""
    _instance: Optional[ThemeManager] = None

    def __new__(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._palettes = dict(THEME_PRESETS)
            cls._instance._current_palette = DARK_PALETTE
            cls._instance._previous_palette: Optional[Palette] = None
            cls._instance._listeners = []
            cls._instance._priority_listeners = []
        return cls._instance

    @property
    def palettes(self) -> Dict[str, Palette]:
        return dict(self._palettes)

    @property
    def current(self) -> Palette:
        return self._current_palette

    @property
    def previous(self) -> Optional[Palette]:
        return self._previous_palette

    def register_palette(self, name: str, palette: Palette) -> None:
        self._palettes[name.lower()] = palette

    def set_theme(self, theme_or_palette: Union[str, Palette]) -> None:
        old_pal = self._current_palette
        if isinstance(theme_or_palette, Palette):
            self._current_palette = theme_or_palette
        elif isinstance(theme_or_palette, str):
            key = theme_or_palette.lower()
            if key in ("system", "auto"):
                mode = detect_system_theme(fallback="dark")
                self._current_palette = DARK_PALETTE if mode == "dark" else LIGHT_PALETTE
            elif key in self._palettes:
                self._current_palette = self._palettes[key]
            elif key in ("true", "1", "dark"):
                self._current_palette = DARK_PALETTE
            elif key in ("false", "0", "light"):
                self._current_palette = LIGHT_PALETTE
            else:
                raise ValueError(f"Unknown theme '{theme_or_palette}'. Available: {list(self._palettes.keys()) + ['system', 'auto']}")
        self._previous_palette = old_pal
        self.notify_listeners()

    def get_palette(self) -> Palette:
        return self._current_palette

    def add_listener(self, callback: Callable[[Palette], None], priority: bool = False) -> None:
        target_list = self._priority_listeners if priority else self._listeners
        for ref in list(target_list):
            unwrapped = _unwrap_listener(ref)
            if unwrapped is None:
                try:
                    target_list.remove(ref)
                except ValueError:
                    pass
            elif unwrapped == callback:
                return
        target_list.append(_wrap_listener(callback))

    def add_priority_listener(self, callback: Callable[[Palette], None]) -> None:
        self.add_listener(callback, priority=True)

    def remove_listener(self, callback: Callable[[Palette], None]) -> None:
        for target_list in (self._priority_listeners, self._listeners):
            for ref in list(target_list):
                unwrapped = _unwrap_listener(ref)
                if unwrapped is None or unwrapped == callback:
                    try:
                        target_list.remove(ref)
                    except ValueError:
                        pass

    def remove_priority_listener(self, callback: Callable[[Palette], None]) -> None:
        for ref in list(self._priority_listeners):
            unwrapped = _unwrap_listener(ref)
            if unwrapped is None or unwrapped == callback:
                try:
                    self._priority_listeners.remove(ref)
                except ValueError:
                    pass

    def notify_listeners(self) -> None:
        # Priority listeners (e.g. root hierarchy apply_theme) execute FIRST top-down
        for ref in list(self._priority_listeners):
            cb = _unwrap_listener(ref)
            if cb is None:
                try:
                    self._priority_listeners.remove(ref)
                except ValueError:
                    pass
            else:
                try:
                    cb(self._current_palette)
                except Exception as e:
                    logger.error("Error executing priority theme listener %r: %s", cb, e, exc_info=True)
        # Standard listeners execute next
        for ref in list(self._listeners):
            cb = _unwrap_listener(ref)
            if cb is None:
                try:
                    self._listeners.remove(ref)
                except ValueError:
                    pass
            else:
                try:
                    cb(self._current_palette)
                except Exception as e:
                    logger.error("Error executing theme listener %r: %s", cb, e, exc_info=True)


# Global singleton and module-level convenience functions
_theme_manager = ThemeManager()
_auto_theme_thread: Optional[threading.Thread] = None
_auto_theme_active: bool = False


def detect_system_theme(fallback: str = "dark") -> str:
    """
    Detect the host OS dark/light mode preference using darkdetect if available.
    Returns 'dark' or 'light'. If detection is unsupported or fails, returns fallback.
    """
    try:
        import darkdetect  # type: ignore
        theme_name = darkdetect.theme()
        if theme_name:
            theme_str = str(theme_name).strip().lower()
            if "dark" in theme_str:
                return "dark"
            elif "light" in theme_str:
                return "light"

        is_dark = darkdetect.isDark()
        if is_dark is True:
            return "dark"
        elif is_dark is False:
            return "light"
    except Exception as e:
        logger.debug("System dark theme detection via darkdetect failed or not available: %s", e)
    return fallback


def is_system_dark(fallback: bool = True) -> bool:
    """Return True if the host OS is currently in dark mode."""
    detected = detect_system_theme(fallback="dark" if fallback else "light")
    return detected == "dark"


def auto_theme(
    root: Optional[Any] = None,
    dark: Union[str, Palette] = "dark",
    light: Union[str, Palette] = "light",
    listen: bool = True,
) -> Callable[[], None]:
    """
    Automatically detect and apply the system theme (Dark or Light).
    Optionally listens for dynamic OS theme changes in the background.

    Args:
        root: Optional Tk root or widget. If provided, theme changes triggered
              by the OS listener are safely dispatched via root.after(0, ...),
              and the listener is automatically stopped when root is destroyed.
        dark: Palette name or Palette object to use for dark mode (defaults to 'dark').
        light: Palette name or Palette object to use for light mode (defaults to 'light').
        listen: If True and darkdetect is available, spawns a background thread to
                listen for live OS theme changes.

    Returns:
        cleanup: Callable that stops the OS theme listener when invoked.
    """
    global _auto_theme_thread, _auto_theme_active

    def _resolve_and_apply(mode: str) -> None:
        target = dark if mode.lower() == "dark" else light
        set_theme(target)

    # Initial detection & apply
    detected = detect_system_theme(fallback="dark")
    _resolve_and_apply(detected)

    if not listen:
        return stop_auto_theme

    # Stop any previous listener
    stop_auto_theme()

    try:
        import darkdetect  # type: ignore
        if not hasattr(darkdetect, "listener"):
            return stop_auto_theme
    except Exception as e:
        logger.debug("darkdetect listener is not available: %s", e)
        return stop_auto_theme

    _auto_theme_active = True

    def _on_os_change(os_theme: str) -> None:
        if not _auto_theme_active:
            return
        mode = "dark" if (os_theme and "dark" in str(os_theme).lower()) else "light"
        if root is not None and hasattr(root, "after") and hasattr(root, "winfo_exists"):
            try:
                if root.winfo_exists():
                    root.after(0, lambda: _resolve_and_apply(mode) if _auto_theme_active else None)
                else:
                    stop_auto_theme()
            except Exception as e:
                logger.debug("Error querying root during auto_theme OS change callback: %s", e)
                _resolve_and_apply(mode)
        else:
            _resolve_and_apply(mode)

    def _worker() -> None:
        try:
            import darkdetect  # type: ignore
            darkdetect.listener(_on_os_change)
        except Exception as e:
            logger.debug("darkdetect listener worker encountered exception or terminated: %s", e)

    t = threading.Thread(target=_worker, name="tkblend-darkdetect-listener", daemon=True)
    _auto_theme_thread = t
    t.start()

    if root is not None and hasattr(root, "bind"):
        def _on_root_destroy(event: Any) -> None:
            if getattr(event, "widget", None) == root:
                stop_auto_theme()
        try:
            root.bind("<Destroy>", _on_root_destroy, add="+")
        except Exception as e:
            logger.debug("Failed binding root <Destroy> event in auto_theme: %s", e)

    return stop_auto_theme


def stop_auto_theme() -> None:
    """Stop any active OS system theme change listener."""
    global _auto_theme_active, _auto_theme_thread
    _auto_theme_active = False
    _auto_theme_thread = None


def get_theme() -> Palette:
    """Return the active Palette."""
    return _theme_manager.current

def get_palette() -> Palette:
    """Return the active Palette."""
    return _theme_manager.current

def set_theme(theme_or_palette: Union[str, Palette]) -> None:
    """Switch active theme ('dark', 'light', 'system', 'auto', or custom Palette)."""
    _theme_manager.set_theme(theme_or_palette)

def set_dark_mode(dark: bool) -> None:
    """Set dark mode on or off."""
    set_theme("dark" if dark else "light")

def add_theme_listener(callback: Callable[[Palette], None], priority: bool = False) -> None:
    """Register a callback for theme changes."""
    _theme_manager.add_listener(callback, priority=priority)

def remove_theme_listener(callback: Any) -> None:
    """Unregister a theme callback."""
    if hasattr(callback, "_tkblend_theme_cb"):
        _theme_manager.remove_listener(getattr(callback, "_tkblend_theme_cb"))
    _theme_manager.remove_listener(callback)

def bind_theme_changed(widget: Any, callback: Callable[[], None]) -> None:
    """Bind a widget callback to theme change events with auto-cleanup."""
    def _theme_cb(palette: Palette) -> None:
        if hasattr(widget, "winfo_exists"):
            try:
                if not widget.winfo_exists():
                    remove_theme_listener(_theme_cb)
                    return
            except Exception:
                remove_theme_listener(_theme_cb)
                return
        try:
            callback()
        except Exception as e:
            logger.debug("Error running theme callback on widget: %s", e)

    if widget is not None:
        try:
            widget._tkblend_theme_cb = _theme_cb
        except Exception:
            pass
    add_theme_listener(_theme_cb)

def is_inside_card(widget: Any) -> bool:
    """Check if a widget is inside a Card or Frame container."""
    curr = widget
    while curr:
        cls_name = getattr(curr, "__class__", type(None)).__name__
        if "Card" in cls_name or "Frame" in cls_name:
            return True
        curr = getattr(curr, "master", None)
    return False

def is_ttkbootstrap_installed() -> bool:
    """Pure vector toolkit has zero ttk dependencies."""
    return False


def resolve_ancestor_bg(
    master: Optional[Any],
    palette: Optional[Palette] = None,
    max_depth: int = 50,
) -> str:
    """
    Robust top-down ancestor background discovery:
    1. Checks for enclosing tkblend containers (Card, Frame, Accordion) via `_bg_color`.
    2. Interrogates tkblend widget explicit backgrounds via `_explicit_bg` / `_explicit_parent_bg`.
    3. Interrogates standard Tk container background via `.cget('background')` or `.cget('bg')`.
    4. Interrogates ttk container background via `ttk.Style().lookup(...)`.
    5. Falls back to active palette.bg.
    Uses winfo_rgb conversion so system color names (SystemButtonFace, etc.) are converted to #RRGGBB.
    """
    pal = palette or get_theme()
    if master is None:
        return pal.bg

    # Pass 1: Enclosing tkblend container surface (_bg_color on Card/Frame)
    curr = master
    visited = set()
    depth = 0
    while curr is not None and depth < max_depth:
        curr_id = id(curr)
        if curr_id in visited:
            break
        visited.add(curr_id)
        depth += 1

        if hasattr(curr, "_bg_color") and getattr(curr, "_bg_color", None):
            res = resolve_color_failsafe(curr._bg_color, master=curr, fallback=None)
            if res:
                return res
        curr = getattr(curr, "master", None)

    # Pass 2: No tkblend container surface found.
    # Interrogate explicit bg, standard Tk container background, or ttk style.
    curr = master
    visited = set()
    depth = 0
    while curr is not None and depth < max_depth:
        curr_id = id(curr)
        if curr_id in visited:
            break
        visited.add(curr_id)
        depth += 1

        # Check explicit bg set on a tkblend widget ancestor
        for attr in ("_explicit_bg", "_explicit_parent_bg"):
            if hasattr(curr, attr) and getattr(curr, attr, None):
                res = resolve_color_failsafe(getattr(curr, attr), master=curr, fallback=None)
                if res:
                    return res

        # Check standard Tk container background
        if hasattr(curr, "cget"):
            for opt in ("background", "bg"):
                try:
                    m_bg = curr.cget(opt)
                    if m_bg and str(m_bg).strip() not in ("", "None"):
                        res = resolve_color_failsafe(m_bg, master=curr, fallback=None)
                        if res:
                            prev = _theme_manager.previous
                            if prev is not None:
                                r_low = res.lower()
                                if r_low == prev.bg.lower():
                                    return pal.bg
                                elif r_low == prev.card_bg.lower():
                                    return pal.card_bg
                                elif r_low == prev.surface.lower():
                                    return pal.surface
                            return res
                except Exception as e:
                    logger.debug("Ancestor widget %r cget('%s') failed: %s", curr, opt, e)

        # Check ttk container style background
        if hasattr(curr, "winfo_class"):
            try:
                import tkinter.ttk as ttk
                style = ttk.Style()
                style_name = ""
                if hasattr(curr, "cget"):
                    try:
                        style_name = curr.cget("style")
                    except Exception as e:
                        logger.debug("Failed getting ttk style attribute from %r: %s", curr, e)
                if not style_name:
                    style_name = curr.winfo_class()
                ttk_bg = style.lookup(style_name, "background")
                if ttk_bg and str(ttk_bg).strip() not in ("", "None"):
                    res = resolve_color_failsafe(ttk_bg, master=curr, fallback=None)
                    if res:
                        return res
            except Exception as e:
                logger.debug("Failed checking ttk style background on %r: %s", curr, e)

        curr = getattr(curr, "master", None)

    return pal.bg


def apply_theme(
    root: Any,
    palette: Optional[Union[str, Palette]] = None,
    preserve_overrides: bool = True,
    recursive: bool = True,
    dark_mode: Optional[bool] = None,
    font: Optional[Any] = None,
    sync_fonts: bool = True,
    auto_detect: bool = False,
    **kwargs: Any,
) -> Callable[[], None]:
    """
    Inject theme into a Tk / Toplevel / Frame hierarchy, styling standard
    Tk widgets (Tk, Toplevel, Frame, Label, Canvas), ttk.Style elements, and tkblend widgets.

    Registers an auto-synchronizing priority listener on ThemeManager so subsequent `set_theme()`
    calls automatically re-style the hierarchy top-down.

    Args:
        root: The Tk root, Toplevel, or container widget to theme.
        palette: Optional specific Palette or theme name. If None, uses active theme.
        preserve_overrides: If True (default), widgets with custom explicit backgrounds
                            or fonts are preserved during theme changes. If False, overrides all.
        recursive: If True (default), traverses all child widgets recursively.
        dark_mode: Optional boolean shorthand to switch dark mode.
        font: Optional font configuration, family name, tuple, or FontConfig.
        sync_fonts: If True (default), synchronizes standard Tk and TTK fonts with tkblend typography.
        auto_detect: If True, automatically detects OS theme and starts continuous OS change listening.
        **kwargs: Extra options accepted for backward compatibility.

    Returns:
        A cleanup function to unregister the theme listener.
    """
    import tkinter as tk
    from .font import sync_tk_fonts

    if auto_detect:
        auto_theme(root=root, listen=True)
    elif dark_mode is not None:
        set_dark_mode(dark_mode)
    elif palette is not None:
        if isinstance(palette, str):
            set_theme(palette)
        elif isinstance(palette, Palette):
            set_theme(palette)

    initial_root_bg = ""
    if hasattr(root, "cget"):
        try:
            initial_root_bg = root.cget("background")
        except Exception as e:
            logger.debug("Failed querying initial root background: %s", e)
    prev_injected = getattr(root, "_tkblend_injected_bg", None)

    def _style_ttk(pal: Palette) -> None:
        try:
            import tkinter.ttk as ttk
            style = ttk.Style()
            style.configure(".", background=pal.bg, foreground=pal.fg)
            style.configure("TFrame", background=pal.bg)
            style.configure("TLabel", background=pal.bg, foreground=pal.fg)
            style.configure("TLabelframe", background=pal.bg, foreground=pal.fg)
            style.configure("TLabelframe.Label", background=pal.bg, foreground=pal.fg)
            style.configure("TNotebook", background=pal.bg)
            style.configure("TNotebook.Tab", background=pal.card_bg, foreground=pal.fg)
            style.map("TNotebook.Tab", background=[("selected", pal.primary), ("active", pal.card_border)])
        except Exception as e:
            logger.debug("Failed configuring ttk default styles: %s", e)

    def _check_preserve(w: Any, pal: Palette) -> bool:
        """Return True if background should be updated, False if preserved."""
        if not preserve_overrides:
            if hasattr(w, "_tkblend_custom_override"):
                w._tkblend_custom_override = False
            return True

        if getattr(w, "_tkblend_custom_override", False):
            return False

        try:
            curr_bg = w.cget("background")
            prev = _theme_manager.previous
            prev_colors = ()
            if prev is not None:
                prev_colors = (prev.bg.lower(), prev.card_bg.lower(), prev.surface.lower())
            curr_low = curr_bg.lower() if isinstance(curr_bg, str) else ""

            if curr_low in prev_colors or curr_bg in (initial_root_bg, prev_injected, pal.bg, pal.card_bg, pal.surface):
                return True

            if hasattr(w, "_tkblend_injected_bg"):
                if curr_bg != w._tkblend_injected_bg and curr_low not in prev_colors:
                    w._tkblend_custom_override = True
                    return False
            else:
                w._tkblend_custom_override = True
                return False
        except Exception as e:
            logger.debug("Error checking preserve override on %r: %s", w, e)
        return True

    def _apply_hierarchy(target: Any, pal: Palette, container_bg: Optional[str] = None) -> None:
        if not hasattr(target, "winfo_exists"):
            return
        try:
            if not target.winfo_exists():
                return
        except Exception as e:
            logger.debug("Error checking winfo_exists during hierarchy theming on %r: %s", target, e)
            return

        master = getattr(target, "master", None)
        # Skip or preserve internal backing label of Card/Frame (_bg_label)
        if master is not None and getattr(master, "_bg_label", None) is target:
            target_bg = getattr(master, "_parent_bg", container_bg or pal.bg)
            try:
                target.configure(background=target_bg)
            except Exception as e:
                logger.debug("Failed configuring Card/Frame _bg_label background: %s", e)
            return

        is_tkblend = hasattr(target, "_on_theme_changed")
        next_container_bg = container_bg or pal.bg

        if is_tkblend:
            # Card / Frame container surface
            if hasattr(target, "_bg_color"):
                if hasattr(target, "set_parent_bg"):
                    target.set_parent_bg(container_bg or pal.bg, force=not preserve_overrides)
                try:
                    target._on_theme_changed(pal)
                except Exception as e:
                    logger.debug("Exception in target._on_theme_changed for container %r: %s", target, e, exc_info=True)
                next_container_bg = str(target._bg_color)
            elif hasattr(target, "_header") and hasattr(target, "_content"):
                # Accordion container
                if hasattr(target, "set_parent_bg"):
                    target.set_parent_bg(container_bg or pal.bg, force=not preserve_overrides)
                try:
                    target._on_theme_changed(pal)
                except Exception as e:
                    logger.debug("Exception in target._on_theme_changed for accordion %r: %s", target, e, exc_info=True)
                next_container_bg = pal.surface
            else:
                # Vector leaf widget
                if hasattr(target, "set_parent_bg"):
                    target.set_parent_bg(container_bg or pal.bg, force=not preserve_overrides)
                try:
                    target._on_theme_changed(pal)
                except Exception as e:
                    logger.debug("Exception in target._on_theme_changed for widget %r: %s", target, e, exc_info=True)
        elif isinstance(target, (tk.Tk, tk.Toplevel)):
            try:
                target.configure(background=pal.bg)
                target._tkblend_injected_bg = pal.bg
            except Exception as e:
                logger.debug("Failed configuring Tk/Toplevel background on %r: %s", target, e)
            next_container_bg = pal.bg
        elif isinstance(target, (tk.Frame, tk.LabelFrame)):
            target_bg = container_bg or pal.bg
            try:
                curr_bg = str(target.cget("background")).lower()
                prev = _theme_manager.previous
                if (prev is not None and curr_bg == prev.surface.lower()) or curr_bg == pal.surface.lower():
                    target_bg = pal.surface
                elif (prev is not None and curr_bg == prev.card_bg.lower()) or curr_bg == pal.card_bg.lower():
                    target_bg = pal.card_bg
            except Exception as e:
                logger.debug("Failed querying Tk Frame cget background on %r: %s", target, e)
            if _check_preserve(target, pal):
                try:
                    target.configure(background=target_bg)
                    target._tkblend_injected_bg = target_bg
                except Exception as e:
                    logger.debug("Failed configuring Tk Frame background on %r: %s", target, e)
            next_container_bg = target_bg
        elif isinstance(target, tk.Label):
            target_bg = container_bg or pal.bg
            if _check_preserve(target, pal):
                try:
                    font_str = str(target.cget("font")).lower()
                    fg_col = pal.fg if "bold" in font_str else pal.text_muted
                    target.configure(background=target_bg, foreground=fg_col)
                    target._tkblend_injected_bg = target_bg
                except Exception as e:
                    logger.debug("Failed configuring Tk Label background/foreground on %r: %s", target, e)
        elif isinstance(target, tk.Canvas):
            target_bg = container_bg or pal.bg
            if _check_preserve(target, pal):
                try:
                    target.configure(background=target_bg)
                    target._tkblend_injected_bg = target_bg
                except Exception as e:
                    logger.debug("Failed configuring Tk Canvas background on %r: %s", target, e)
            next_container_bg = target_bg
        elif isinstance(target, tk.Text):
            target_bg = pal.surface if is_inside_card(target) else pal.input_bg
            if _check_preserve(target, pal):
                try:
                    target.configure(
                        background=target_bg,
                        foreground=pal.fg,
                        insertbackground=pal.primary,
                        selectbackground=pal.primary,
                        selectforeground=pal.primary_fg,
                    )
                    target._tkblend_injected_bg = target_bg
                except Exception as e:
                    logger.debug("Failed configuring Tk Text styling on %r: %s", target, e)
            next_container_bg = target_bg
        elif isinstance(target, tk.Entry):
            target_bg = pal.input_bg
            if _check_preserve(target, pal):
                try:
                    target.configure(
                        background=target_bg,
                        foreground=pal.fg,
                        insertbackground=pal.primary,
                        selectbackground=pal.primary,
                        selectforeground=pal.primary_fg,
                    )
                    target._tkblend_injected_bg = target_bg
                except Exception as e:
                    logger.debug("Failed configuring Tk Entry styling on %r: %s", target, e)
            next_container_bg = target_bg

        if recursive and hasattr(target, "winfo_children"):
            try:
                children = target.winfo_children()
            except Exception as e:
                logger.debug("Failed getting winfo_children on %r: %s", target, e)
                children = []
            for child in children:
                child_bg = next_container_bg
                if hasattr(target, "_content") and child is target._content:
                    child_bg = pal.surface
                _apply_hierarchy(child, pal, container_bg=child_bg)

    # Initial apply
    current_pal = get_theme()
    _style_ttk(current_pal)
    if sync_fonts:
        sync_tk_fonts(root, font=font, recursive=recursive, preserve_overrides=preserve_overrides)
    _apply_hierarchy(root, current_pal)

    # Auto-synchronization priority listener
    def _theme_listener(new_palette: Palette) -> None:
        if not hasattr(root, "winfo_exists"):
            remove_theme_listener(_theme_listener)
            return
        try:
            if not root.winfo_exists():
                remove_theme_listener(_theme_listener)
                return
        except Exception as e:
            logger.debug("Error verifying root existence in _theme_listener: %s", e)
            remove_theme_listener(_theme_listener)
            return
        _style_ttk(new_palette)
        if sync_fonts:
            sync_tk_fonts(root, font=font, recursive=recursive, preserve_overrides=preserve_overrides)
        _apply_hierarchy(root, new_palette)

    add_theme_listener(_theme_listener, priority=True)

    # Unregister automatically when root widget is destroyed
    def _on_destroy(event) -> None:
        if getattr(event, "widget", None) == root:
            remove_theme_listener(_theme_listener)
            if auto_detect:
                stop_auto_theme()

    try:
        root.bind("<Destroy>", _on_root_destroy if "_on_root_destroy" in locals() else _on_destroy, add="+")
    except Exception as e:
        logger.debug("Failed binding root <Destroy> in apply_theme: %s", e)

    def cleanup() -> None:
        remove_theme_listener(_theme_listener)
        if auto_detect:
            stop_auto_theme()

    return cleanup


inject_theme = apply_theme

