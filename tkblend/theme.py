"""
Pure-Python vector theme and color palette management for tkblend.
Provides semantic colors, built-in Dark and Light themes, and dynamic theme change notification.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Callable, Optional, Union, Tuple, List


def _format_alpha(alpha: Optional[Union[float, int]]) -> str:
    if alpha is None:
        return ""
    a_int = int(alpha * 255) if isinstance(alpha, float) and alpha <= 1.0 else int(alpha)
    a_int = max(0, min(255, a_int))
    return f"{a_int:02x}"


def resolve_theme_color(c: str, alpha: Optional[Union[float, int]] = None) -> str:
    """
    Resolve a hex code, named color, or semantic palette token (e.g. 'primary', 'bg', 'card_bg')
    into a valid #RRGGBB or #RRGGBBAA hex string.
    """
    if not isinstance(c, str):
        c = str(c)

    c_clean = c.strip()
    # Check if semantic token in active palette
    palette = get_theme()
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

    if hasattr(palette, token):
        val = getattr(palette, token)
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
        return f"#{hex_val}"

    # Common named colors fallback
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
    }
    low = c_clean.lower()
    if low in named_map:
        base = named_map[low]
        if alpha is not None and len(base) == 7:
            return f"{base}{_format_alpha(alpha)}"
        return base

    return c_clean


def blend_color_hex(c1: str, c2: str, t: float) -> str:
    """Linearly interpolate between two hex color strings at factor t (0.0 to 1.0)."""
    if t <= 0.0:
        return c1
    if t >= 1.0:
        return c2

    def _to_rgb(s: str) -> Tuple[int, int, int]:
        s = s.lstrip("#")
        if len(s) == 3:
            s = "".join(c + c for c in s)
        val = int(s[:6], 16)
        return ((val >> 16) & 0xFF, (val >> 8) & 0xFF, val & 0xFF)

    try:
        r1, g1, b1 = _to_rgb(c1)
        r2, g2, b2 = _to_rgb(c2)
        inv = 1.0 - t
        r = int(r1 * inv + r2 * t)
        g = int(g1 * inv + g2 * t)
        b = int(b1 * inv + b2 * t)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return c1 if t < 0.5 else c2


def adjust_brightness(hex_code: str, factor: float) -> str:
    """Lighten (> 1.0) or darken (< 1.0) a hex color."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 3:
        hex_code = "".join(c + c for c in hex_code)
    try:
        r = int(hex_code[:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        r = min(255, max(0, int(r * factor)))
        g = min(255, max(0, int(g * factor)))
        b = min(255, max(0, int(b * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return f"#{hex_code}"


@dataclass
class Palette:
    """Semantic color palette definition for vector widgets."""
    name: str = "dark"
    dark_mode: bool = True

    # Canvas & Window background
    bg: str = "#1e1e2e"
    fg: str = "#cdd6f4"
    text_muted: str = "#a6adc8"

    # Surface & Containers
    card_bg: str = "#252538"
    card_border: str = "#313244"
    surface: str = "#181825"
    surface_border: str = "#313244"

    # Primary brand accent
    primary: str = "#89b4fa"
    primary_hover: str = "#b4befe"
    primary_active: str = "#74c7ec"
    primary_fg: str = "#11111b"

    # Secondary action
    secondary: str = "#313244"
    secondary_hover: str = "#45475a"
    secondary_active: str = "#585b70"
    secondary_fg: str = "#cdd6f4"

    # Status & Accent colors
    accent: str = "#cba6f7"
    success: str = "#a6e3a1"
    warning: str = "#f9e2af"
    destructive: str = "#f38ba8"

    # Inputs & Controls
    input_bg: str = "#181825"
    input_border: str = "#313244"
    input_focus: str = "#89b4fa"
    track_bg: str = "#313244"
    thumb_color: str = "#ffffff"
    shadow_color: str = "#00000066"


DARK_PALETTE = Palette(
    name="dark",
    dark_mode=True,
    bg="#1e1e2e",
    fg="#cdd6f4",
    text_muted="#a6adc8",
    card_bg="#252538",
    card_border="#313244",
    surface="#181825",
    surface_border="#313244",
    primary="#89b4fa",
    primary_hover="#b4befe",
    primary_active="#74c7ec",
    primary_fg="#11111b",
    secondary="#313244",
    secondary_hover="#45475a",
    secondary_active="#585b70",
    secondary_fg="#cdd6f4",
    accent="#cba6f7",
    success="#a6e3a1",
    warning="#f9e2af",
    destructive="#f38ba8",
    input_bg="#181825",
    input_border="#313244",
    input_focus="#89b4fa",
    track_bg="#313244",
    thumb_color="#ffffff",
    shadow_color="#00000066",
)

LIGHT_PALETTE = Palette(
    name="light",
    dark_mode=False,
    bg="#f8f9fa",
    fg="#1e293b",
    text_muted="#64748b",
    card_bg="#ffffff",
    card_border="#e2e8f0",
    surface="#f1f5f9",
    surface_border="#e2e8f0",
    primary="#2563eb",
    primary_hover="#1d4ed8",
    primary_active="#1e40af",
    primary_fg="#ffffff",
    secondary="#e2e8f0",
    secondary_hover="#cbd5e1",
    secondary_active="#94a3b8",
    secondary_fg="#1e293b",
    accent="#7c3aed",
    success="#16a34a",
    warning="#d97706",
    destructive="#dc2626",
    input_bg="#ffffff",
    input_border="#cbd5e1",
    input_focus="#2563eb",
    track_bg="#e2e8f0",
    thumb_color="#ffffff",
    shadow_color="#0000001f",
)


class ThemeManager:
    """Central singleton managing the active theme palette and listeners."""
    _instance: Optional[ThemeManager] = None

    def __new__(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._palettes = {
                "dark": DARK_PALETTE,
                "light": LIGHT_PALETTE,
            }
            cls._instance._current_palette = DARK_PALETTE
            cls._instance._listeners: List[Callable[[Palette], None]] = []
        return cls._instance

    @property
    def current(self) -> Palette:
        return self._current_palette

    def register_palette(self, name: str, palette: Palette) -> None:
        self._palettes[name.lower()] = palette

    def set_theme(self, theme_or_palette: Union[str, Palette]) -> None:
        if isinstance(theme_or_palette, Palette):
            self._current_palette = theme_or_palette
        elif isinstance(theme_or_palette, str):
            key = theme_or_palette.lower()
            if key in self._palettes:
                self._current_palette = self._palettes[key]
            elif key in ("true", "1", "dark"):
                self._current_palette = DARK_PALETTE
            elif key in ("false", "0", "light"):
                self._current_palette = LIGHT_PALETTE
            else:
                raise ValueError(f"Unknown theme '{theme_or_palette}'. Available: {list(self._palettes.keys())}")
        self.notify_listeners()

    def get_palette(self) -> Palette:
        return self._current_palette

    def add_listener(self, callback: Callable[[Palette], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[Palette], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify_listeners(self) -> None:
        for callback in list(self._listeners):
            try:
                callback(self._current_palette)
            except Exception:
                pass


# Global singleton and module-level convenience functions
_theme_manager = ThemeManager()

def get_theme() -> Palette:
    """Return the active Palette."""
    return _theme_manager.current

def get_palette() -> Palette:
    """Return the active Palette."""
    return _theme_manager.current

def set_theme(theme_or_palette: Union[str, Palette]) -> None:
    """Switch active theme ('dark', 'light', or custom Palette)."""
    _theme_manager.set_theme(theme_or_palette)

def set_dark_mode(dark: bool) -> None:
    """Set dark mode on or off."""
    set_theme("dark" if dark else "light")

def add_theme_listener(callback: Callable[[Palette], None]) -> None:
    """Register a callback for theme changes."""
    _theme_manager.add_listener(callback)

def remove_theme_listener(callback: Callable[[Palette], None]) -> None:
    """Unregister a theme callback."""
    _theme_manager.remove_listener(callback)

def bind_theme_changed(widget: Any, callback: Callable[[], None]) -> None:
    """Bind a widget callback to theme change events with auto-cleanup."""
    def _wrapper(palette: Palette) -> None:
        if hasattr(widget, "winfo_exists"):
            try:
                if not widget.winfo_exists():
                    remove_theme_listener(_wrapper)
                    return
            except Exception:
                pass
        callback()
    add_theme_listener(_wrapper)

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
