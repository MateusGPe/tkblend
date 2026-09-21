"""
Theme bridge and color resolution for ttkbootstrap and Tkinter.
"""

from __future__ import annotations
import re
import tkinter as tk
from typing import Optional, Dict, Any, Callable, Tuple, Union

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
        # Return singleton instance if it exists
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

    # Check for slash or colon alpha modifier (e.g. "primary/0.5", "danger:128")
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
        # Strip existing alpha if 8-char hex
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

