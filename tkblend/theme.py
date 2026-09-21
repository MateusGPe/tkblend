"""
Native TTK Theme Engine Bridge and Theme Helpers for Tkinter and Blend2D.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Callable, Tuple, Union

try:
    from tkblend._tkblend import (  # type: ignore
        ThemeConfig,
        register_ttk_theme as _native_register_theme,
        set_theme_dark_mode as _native_set_dark_mode,
        set_theme_config as _native_set_config,
        get_theme_config as _native_get_config,
        Color as _NativeColor,
    )
except ImportError:
    ThemeConfig = None  # type: ignore
    _native_register_theme = None  # type: ignore
    _native_set_dark_mode = None  # type: ignore
    _native_set_config = None  # type: ignore
    _native_get_config = None  # type: ignore

# Standard bootstrap fallback colors if ttkbootstrap is not active
_FALLBACK_BOOTSTRAP_PALETTE = {
    "primary": "#0d6efd",
    "secondary": "#6c757d",
    "success": "#198754",
    "info": "#0dcaf0",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "light": "#f8f9fa",
    "dark": "#212529",
    "bg": "#ffffff",
    "fg": "#212529",
    "border": "#dee2e6",
    "inputbg": "#ffffff",
    "inputfg": "#212529",
    "selectbg": "#0d6efd",
    "selectfg": "#ffffff",
}


def _get_interp_addr(widget: Optional[tk.Misc] = None) -> int:
    """Safely extract Tcl_Interp memory address from Tk widget or default root."""
    if widget is None:
        widget = getattr(tk, "_default_root", None)
    if widget is None:
        widget = tk._get_default_root()
    if widget is not None and hasattr(widget, "tk") and hasattr(widget.tk, "interpaddr"):
        return int(widget.tk.interpaddr())
    return 0


def register_theme(widget: Optional[tk.Misc] = None, theme_name: str = "tkblend") -> bool:
    """
    Register the native Blend2D TTK theme into the Tcl/Tk interpreter.
    """
    if _native_register_theme is None:
        raise RuntimeError("Native _tkblend extension is not loaded")
    
    interp_addr = _get_interp_addr(widget)
    if not interp_addr:
        raise ValueError("Could not find active Tk interpreter address")
    
    return _native_register_theme(interp_addr, theme_name)


def set_dark_mode(dark: bool = True) -> None:
    """Switch theme mode between Dark Mode and Light Mode."""
    if _native_set_dark_mode is not None:
        _native_set_dark_mode(dark)


def set_theme_config(config: Any) -> None:
    """Set custom ThemeConfig structure in native engine."""
    if _native_set_config is not None:
        _native_set_config(config)


def get_theme_config() -> Any:
    """Get the active ThemeConfig structure from native engine."""
    if _native_get_config is not None:
        return _native_get_config()
    return None


def apply_theme(
    widget: Optional[tk.Misc] = None,
    dark_mode: bool = True,
    theme_name: str = "tkblend",
    button_radius: Optional[float] = None,
    entry_radius: Optional[float] = None,
    enable_shadows: Optional[bool] = None,
    shadow_blur: Optional[float] = None,
) -> str:
    """
    Register and activate the Native Blend2D TTK theme on the given Tk application.
    
    Parameters
    ----------
    widget : tk.Misc, optional
        A Tk widget or Tk instance (defaults to active root).
    dark_mode : bool
        Whether to use modern Dark or Light theme palette.
    theme_name : str
        The registered TTK theme name (default: "tkblend").
    button_radius : float, optional
        Custom corner radius for buttons.
    entry_radius : float, optional
        Custom corner radius for entries.
    enable_shadows : bool, optional
        Enable or disable soft drop shadows.
    shadow_blur : float, optional
        Custom blur radius for drop shadows.
        
    Returns
    -------
    str
        The active TTK theme name.
    """
    set_dark_mode(dark_mode)

    cfg = get_theme_config()
    if cfg is not None:
        if button_radius is not None:
            cfg.button_radius = float(button_radius)
        if entry_radius is not None:
            cfg.entry_radius = float(entry_radius)
        if enable_shadows is not None:
            cfg.enable_shadows = bool(enable_shadows)
        if shadow_blur is not None:
            cfg.shadow_blur = float(shadow_blur)
        set_theme_config(cfg)

    register_theme(widget, theme_name=theme_name)

    style = ttk.Style(master=widget)
    style.theme_use(theme_name)
    return theme_name


def is_ttkbootstrap_installed() -> bool:
    """Check if ttkbootstrap package is installed."""
    try:
        import ttkbootstrap  # noqa: F401
        return True
    except ImportError:
        return False


def get_active_style() -> Optional[Any]:
    """Retrieve active ttkbootstrap Style instance if available."""
    try:
        import ttkbootstrap as tb
        if hasattr(tb, "Style"):
            return tb.Style.get_instance()
    except Exception:
        pass
    return None


def get_active_theme_name() -> str:
    """Get the active ttkbootstrap theme name, or 'default'."""
    style = get_active_style()
    if style is not None and hasattr(style, "theme_use"):
        try:
            return style.theme_use()
        except Exception:
            pass
    return "default"


def get_theme_colors() -> Dict[str, str]:
    """
    Get all color mappings for the active ttkbootstrap theme, or fallback palette.
    """
    style = get_active_style()
    if style is not None and hasattr(style, "colors"):
        colors_obj = style.colors
        result = {}
        for attr in [
            "primary", "secondary", "success", "info", "warning", "danger",
            "light", "dark", "bg", "fg", "border", "inputbg", "inputfg",
            "selectbg", "selectfg"
        ]:
            if hasattr(colors_obj, attr):
                result[attr] = getattr(colors_obj, attr)
        return result
    return dict(_FALLBACK_BOOTSTRAP_PALETTE)


def resolve_theme_color(color: Union[str, Any], alpha: Optional[Union[float, int]] = None) -> str:
    """
    Resolve a color token (e.g. 'primary', 'dark', 'success') to a hex color string.
    Supports alpha blending notation:
      - 'primary:0.5' or 'primary/0.5' (float alpha 0.0-1.0)
      - 'primary:128' or 'primary#80' (int alpha 0-255 or 2 hex digits)
      - resolve_theme_color('primary', alpha=0.5)

    If the color is already a hex code (e.g. '#1e1e2e', '#ff000088'), it is returned or updated with alpha.
    """
    if not isinstance(color, str):
        return color

    raw = color.strip()
    parsed_alpha: Optional[float] = None

    if "/" in raw:
        name_part, alpha_part = raw.rsplit("/", 1)
        name_part = name_part.strip()
        try:
            val = float(alpha_part.strip())
            parsed_alpha = val if val <= 1.0 else val / 255.0
        except ValueError:
            pass
        raw = name_part
    elif ":" in raw and not raw.startswith("#"):
        name_part, alpha_part = raw.rsplit(":", 1)
        name_part = name_part.strip()
        try:
            val = float(alpha_part.strip())
            parsed_alpha = val if val <= 1.0 else val / 255.0
        except ValueError:
            pass
        raw = name_part

    if alpha is not None:
        parsed_alpha = float(alpha) if alpha <= 1.0 else float(alpha) / 255.0

    lower_name = raw.lower()
    style = get_active_style()

    hex_color: Optional[str] = None
    if style is not None and hasattr(style, "colors") and hasattr(style.colors, lower_name):
        hex_color = getattr(style.colors, lower_name)
    elif lower_name in _FALLBACK_BOOTSTRAP_PALETTE:
        hex_color = _FALLBACK_BOOTSTRAP_PALETTE[lower_name]
    else:
        hex_color = raw

    if parsed_alpha is not None and hex_color.startswith("#"):
        clean_hex = hex_color[1:]
        if len(clean_hex) == 8:
            clean_hex = clean_hex[:6]
        elif len(clean_hex) == 3 or len(clean_hex) == 4:
            clean_hex = "".join([c * 2 for c in clean_hex[:3]])

        alpha_byte = max(0, min(255, int(parsed_alpha * 255.0)))
        return f"#{clean_hex}{alpha_byte:02x}"

    return hex_color


def bind_theme_changed(widget: tk.Misc, callback: Callable[[], None]) -> None:
    """
    Bind a callback to be invoked whenever the ttk/ttkbootstrap theme changes.
    """
    def _on_theme_changed(event=None):
        callback()

    widget.bind("<<ThemeChanged>>", _on_theme_changed, add="+")
    try:
        toplevel = widget.winfo_toplevel()
        if toplevel is not widget:
            toplevel.bind("<<ThemeChanged>>", _on_theme_changed, add="+")
    except Exception:
        pass
