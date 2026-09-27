"""
Declarative theme engine and color palette management for tkblend.
Bridges to the high-performance C++ StyleEngine singleton with support for external .css theme files.
"""

from __future__ import annotations
import logging
import weakref
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Callable, Optional, Union, List, Set

import tkinter as tk
from tkblend._tkblend import (
    Color,
    StyleEngine,
    PseudoState,
    ComputedStyle,
)

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
    """Fail-safe color resolution supporting hex, CSS vars, named colors, and Tk system colors."""
    active_pal = palette or get_theme()
    default_bg = fallback or active_pal.bg

    if color is None:
        return default_bg

    if not isinstance(color, str):
        return default_bg

    c_clean = color.strip()
    if not c_clean:
        return default_bg

    # Check semantic token in active palette
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

    if hasattr(active_pal, token):
        val = getattr(active_pal, token)
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
            return f"#{hex_val}"

    # Named colors map
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

    # Try Tk winfo_rgb if master is provided
    win = master
    if win is None:
        try:
            win = getattr(tk, "_default_root", None)
        except Exception:
            pass

    if win is not None and hasattr(win, "winfo_rgb"):
        try:
            r16, g16, b16 = win.winfo_rgb(c_clean)
            r8, g8, b8 = (r16 >> 8) & 0xFF, (g16 >> 8) & 0xFF, (b16 >> 8) & 0xFF
            hex_str = f"#{r8:02x}{g8:02x}{b8:02x}"
            if alpha is not None:
                return f"{hex_str}{_format_alpha(alpha)}"
            return hex_str
        except Exception:
            pass

    return default_bg


def resolve_theme_color(c: str, alpha: Optional[Union[float, int]] = None) -> str:
    """Resolve a hex code, named color, or semantic palette token into a hex string."""
    return resolve_color_failsafe(c, alpha=alpha)


def to_tk_hex(color: Any, fallback: str = "#000000") -> str:
    """Convert any color (including 8-digit hex #rrggbbaa, rgba, named color, or palette token) to a Tkinter-safe 6-digit hex string (#rrggbb)."""
    if color is None:
        return fallback
    if not isinstance(color, str):
        return fallback
    c = color.strip()
    if not c:
        return fallback
    if c.startswith("#"):
        hex_part = c.lstrip("#")
        if len(hex_part) == 6:
            return f"#{hex_part.lower()}"
        if len(hex_part) == 8:
            return f"#{hex_part[:6].lower()}"
        if len(hex_part) == 3:
            return f"#{hex_part[0]*2}{hex_part[1]*2}{hex_part[2]*2}".lower()
        if len(hex_part) == 4:
            return f"#{hex_part[0]*2}{hex_part[1]*2}{hex_part[2]*2}".lower()

    if c.startswith("rgb"):
        try:
            inside = c[c.find("(") + 1 : c.find(")")]
            parts = [p.strip() for p in inside.split(",")]
            if len(parts) >= 3:
                r = int(float(parts[0]))
                g = int(float(parts[1]))
                b = int(float(parts[2]))
                return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"
        except Exception:
            pass

    resolved = resolve_color_failsafe(c, fallback=fallback)
    if resolved.startswith("#"):
        hex_part = resolved.lstrip("#")
        if len(hex_part) >= 6:
            return f"#{hex_part[:6].lower()}"
        if len(hex_part) == 3:
            return f"#{hex_part[0]*2}{hex_part[1]*2}{hex_part[2]*2}".lower()
    return fallback


to_tk_color = to_tk_hex


def blend_color_hex(c1: str, c2: str, t: float) -> Optional[str]:
    """Linearly interpolate between two hex color strings at factor t (0.0 to 1.0)."""
    if c1 is None or c2 is None or not isinstance(c1, str) or not isinstance(c2, str):
        logger.warning("Failed blending colors %r and %r: invalid color input", c1, c2)
        return None
    if t <= 0.0:
        return c1
    if t >= 1.0:
        return c2
    try:
        col1 = Color.from_hex(c1)
        col2 = Color.from_hex(c2)
        res = col1.lerp(col2, float(t))
        if col1.a < 255 or col2.a < 255:
            return f"#{res.r:02x}{res.g:02x}{res.b:02x}{res.a:02x}"
        return f"#{res.r:02x}{res.g:02x}{res.b:02x}"
    except Exception as e:
        logger.warning("Failed blending colors %r and %r: %s", c1, c2, e)
        return c1 if t < 0.5 else c2


def adjust_brightness(hex_code: str, factor: float) -> Optional[str]:
    """Lighten (> 1.0) or darken (< 1.0) a hex color."""
    if hex_code is None or not isinstance(hex_code, str):
        logger.warning("Failed adjusting brightness on %r: invalid color input", hex_code)
        return None
    try:
        col = Color.from_hex(hex_code)
        if factor >= 1.0:
            res = col.lighten(float(factor))
        else:
            res = col.darken(float(factor))
        if col.a < 255:
            return f"#{res.r:02x}{res.g:02x}{res.b:02x}{res.a:02x}"
        return f"#{res.r:02x}{res.g:02x}{res.b:02x}"
    except Exception as e:
        logger.warning("Failed adjusting brightness on %r: %s", hex_code, e)
        return hex_code


@dataclass
class Palette:
    """Semantic color palette definition queryable from StyleEngine variables."""
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

    @property
    def fg_subtle(self) -> str:
        return self.text_muted

    @property
    def danger(self) -> str:
        return self.destructive

    @classmethod
    def from_theme(cls, theme_name: str) -> Palette:
        """Create a Palette reflecting active StyleEngine CSS variables."""
        def v(key: str, default: str) -> str:
            res = StyleEngine.get_variable(f"--{key}", theme_name)
            if not res:
                res = StyleEngine.get_variable(key, theme_name)
            return res if res else default

        is_dark = theme_name not in ("light", "catppuccin_latte", "solarized_light")
        default_bg = "#100e14" if is_dark else "#f4f5f7"
        default_fg = "#e6e0e9" if is_dark else "#0f172a"

        return cls(
            name=theme_name,
            dark_mode=is_dark,
            bg=v("bg", default_bg),
            fg=v("fg", default_fg),
            text_muted=v("text-muted", "#cac4d0" if is_dark else "#475569"),
            card_bg=v("card-bg", "#25232a" if is_dark else "#ffffff"),
            card_border=v("card-border", "#49454f" if is_dark else "#cbd5e1"),
            surface=v("surface", "#1d1b20" if is_dark else "#e2e8f0"),
            surface_border=v("surface-border", "#36343b" if is_dark else "#cbd5e1"),
            primary=v("primary", "#d0bcff" if is_dark else "#6366f1"),
            primary_hover=v("primary-hover", "#e8def8" if is_dark else "#4f46e5"),
            primary_active=v("primary-active", "#b69df8" if is_dark else "#4338ca"),
            primary_fg=v("primary-fg", "#381e72" if is_dark else "#ffffff"),
            secondary=v("secondary", "#4a4458" if is_dark else "#e2e8f0"),
            secondary_hover=v("secondary-hover", "#585168" if is_dark else "#cbd5e1"),
            secondary_active=v("secondary-active", "#332d41" if is_dark else "#94a3b8"),
            secondary_fg=v("secondary-fg", "#e8def8" if is_dark else "#0f172a"),
            accent=v("accent", "#efb8c8" if is_dark else "#0ea5e9"),
            success=v("success", "#85d697" if is_dark else "#10b981"),
            warning=v("warning", "#ffb877" if is_dark else "#f59e0b"),
            destructive=v("destructive", "#ffb4ab" if is_dark else "#ef4444"),
            input_bg=v("input-bg", "#1d1b20" if is_dark else "#ffffff"),
            input_border=v("input-border", "#49454f" if is_dark else "#94a3b8"),
            input_focus=v("input-focus", "#d0bcff" if is_dark else "#6366f1"),
            track_bg=v("track-bg", "#36343b" if is_dark else "#e2e8f0"),
            thumb_color=v("thumb-color", "#d0bcff" if is_dark else "#6366f1"),
            shadow_color=v("shadow-color", "#00000055" if is_dark else "#00000018"),
        )


def register_theme(name: str, css_text: str) -> None:
    """Register custom CSS theme in C++ StyleEngine."""
    StyleEngine.register_theme(name, css_text)


def load_theme_file(filepath: Union[str, Path], name: Optional[str] = None) -> str:
    """Load and register a CSS theme stylesheet from a file path."""
    p = Path(filepath)
    if not p.is_file():
        raise FileNotFoundError(f"Theme file not found: {p}")
    css_text = p.read_text(encoding="utf-8")
    theme_name = name or p.stem.lower()
    register_theme(theme_name, css_text)
    if "THEME_PRESETS" in globals():
        THEME_PRESETS[theme_name] = Palette.from_theme(theme_name)
    return theme_name


def load_theme_dir(dirpath: Union[str, Path]) -> List[str]:
    """Load and register all .css theme stylesheets from a directory."""
    p = Path(dirpath)
    if not p.is_dir():
        return []
    loaded = []
    for css_file in sorted(p.glob("*.css")):
        try:
            t_name = load_theme_file(css_file)
            loaded.append(t_name)
        except Exception as e:
            logger.warning("Failed loading theme file %s: %s", css_file, e)
    return loaded


def _load_builtin_themes() -> None:
    """Load all built-in .css theme files from tkblend/themes/."""
    builtin_dir = Path(__file__).parent / "themes"
    if builtin_dir.is_dir():
        load_theme_dir(builtin_dir)


_load_builtin_themes()

DARK_PALETTE = Palette.from_theme("dark")
LIGHT_PALETTE = Palette.from_theme("light")
NORD_PALETTE = Palette.from_theme("nord")
DRACULA_PALETTE = Palette.from_theme("dracula")
TOKYO_NIGHT_PALETTE = Palette.from_theme("tokyo_night")
CATPPUCCIN_MOCHA_PALETTE = Palette.from_theme("catppuccin_mocha")
CATPPUCCIN_LATTE_PALETTE = Palette.from_theme("catppuccin_latte")
EMERALD_PALETTE = Palette.from_theme("emerald")
EMERALD_FOREST_PALETTE = Palette.from_theme("emerald_forest")
OCEAN_PALETTE = Palette.from_theme("ocean")
SUNSET_PALETTE = Palette.from_theme("sunset")
SUNSET_AMBER_PALETTE = Palette.from_theme("sunset_amber")
MONOKAI_PALETTE = Palette.from_theme("monokai")
MONOKAI_PRO_PALETTE = Palette.from_theme("monokai_pro")
CYBERPUNK_PALETTE = Palette.from_theme("cyberpunk")
SOLARIZED_DARK_PALETTE = Palette.from_theme("solarized_dark")
SOLARIZED_LIGHT_PALETTE = Palette.from_theme("solarized_light")

THEME_PRESETS: Dict[str, Palette] = {
    "dark": DARK_PALETTE,
    "light": LIGHT_PALETTE,
    "nord": NORD_PALETTE,
    "dracula": DRACULA_PALETTE,
    "tokyo_night": TOKYO_NIGHT_PALETTE,
    "catppuccin_mocha": CATPPUCCIN_MOCHA_PALETTE,
    "catppuccin_latte": CATPPUCCIN_LATTE_PALETTE,
    "emerald": EMERALD_PALETTE,
    "emerald_forest": EMERALD_FOREST_PALETTE,
    "ocean": OCEAN_PALETTE,
    "sunset": SUNSET_PALETTE,
    "sunset_amber": SUNSET_AMBER_PALETTE,
    "monokai": MONOKAI_PALETTE,
    "monokai_pro": MONOKAI_PRO_PALETTE,
    "cyberpunk": CYBERPUNK_PALETTE,
    "solarized_dark": SOLARIZED_DARK_PALETTE,
    "solarized_light": SOLARIZED_LIGHT_PALETTE,
}


def get_preset_semantic_colors() -> Dict[str, Set[str]]:
    """Return dictionary of sets containing all known semantic surface colors across presets."""
    res: Dict[str, Set[str]] = {
        "bg": set(),
        "card_bg": set(),
        "surface": set(),
        "input_bg": set(),
        "track_bg": set(),
    }
    for pal in THEME_PRESETS.values():
        res["bg"].add(pal.bg.lower())
        res["card_bg"].add(pal.card_bg.lower())
        res["surface"].add(pal.surface.lower())
        res["input_bg"].add(pal.input_bg.lower())
        res["track_bg"].add(pal.track_bg.lower())
    return res



class ThemeManager:
    """Singleton managing dynamic theme notifications and Palette queries."""
    _instance: Optional[ThemeManager] = None

    def __new__(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners = []
            cls._instance._priority_listeners = []
            cls._instance._current_palette = Palette.from_theme(StyleEngine.get_theme())
            cls._instance._pending_renders = weakref.WeakSet()
            cls._instance._render_scheduled = False
        return cls._instance

    @property
    def current(self) -> Palette:
        return self._current_palette

    @property
    def palette(self) -> Palette:
        return self._current_palette

    def set_theme(self, name: str) -> None:
        target_name = name
        if str(name).lower() in ("system", "auto"):
            target_name = detect_system_theme()
        StyleEngine.set_theme(target_name)
        self._current_palette = Palette.from_theme(target_name)

        try:
            r = getattr(tk, "_default_root", None)
            if r is not None and hasattr(r, "winfo_exists") and r.winfo_exists():
                cur_bg = str(r.cget("background")).lower()
                known_bgs = [preset.bg.lower() for preset in THEME_PRESETS.values()]
                if cur_bg in ("#d9d9d9", "#2c2c2c", "#f0f0f0", "gray85", "systembuttonface") or cur_bg in known_bgs or getattr(r, "_tkblend_theme_bg", None) is not None:
                    r.configure(background=self._current_palette.bg)
                    r._tkblend_theme_bg = self._current_palette.bg
        except Exception:
            pass

        self.notify_listeners(self._current_palette)

    def notify_listeners(self, palette: Optional[Palette] = None) -> None:
        pal = palette or self._current_palette
        for target_list in (self._priority_listeners, self._listeners):
            for item in list(target_list):
                if isinstance(item, weakref.ref):
                    cb = item()
                    if cb is None:
                        if item in target_list:
                            target_list.remove(item)
                    else:
                        try:
                            cb(pal)
                        except Exception as e:
                            logger.error("Error executing theme listener: %s", e)
                elif item is not None:
                    try:
                        item(pal)
                    except Exception as e:
                        logger.error("Error executing theme listener: %s", e)

    def add_listener(self, callback: Callable[[Palette], None], priority: bool = False) -> None:
        target_list = self._priority_listeners if priority else self._listeners
        # If already added, ignore
        for item in target_list:
            cb = item() if isinstance(item, weakref.ref) else item
            if cb == callback:
                return

        if hasattr(callback, "__self__"):
            target_list.append(weakref.WeakMethod(callback, lambda ref: self._remove_dead_ref(ref, target_list)))  # type: ignore
        else:
            target_list.append(callback)

    def remove_listener(self, callback: Callable[[Palette], None]) -> None:
        for target_list in (self._priority_listeners, self._listeners):
            for item in list(target_list):
                cb = item() if isinstance(item, weakref.ref) else item
                if cb == callback:
                    target_list.remove(item)

    def _remove_dead_ref(self, ref: Any, target_list: List) -> None:
        if ref in target_list:
            target_list.remove(ref)

    def queue_render(self, widget: Any) -> None:
        """Schedule non-blocking widget render batch."""
        self._pending_renders.add(widget)
        if not self._render_scheduled:
            self._render_scheduled = True
            try:
                if hasattr(widget, "after_idle"):
                    widget.after_idle(self._flush_renders)
                else:
                    self._flush_renders()
            except Exception:
                self._flush_renders()

    def _flush_renders(self) -> None:
        self._render_scheduled = False
        batch = list(self._pending_renders)
        self._pending_renders.clear()
        pal = self._current_palette
        for w in batch:
            try:
                if hasattr(w, "winfo_exists") and w.winfo_exists():
                    if hasattr(w, "_apply_theme_update"):
                        w._apply_theme_update(pal)
                    elif hasattr(w, "render"):
                        w.render()
            except Exception:
                pass


    def add_priority_listener(self, callback: Callable[[Palette], None]) -> None:
        self.add_listener(callback, priority=True)

    def remove_priority_listener(self, callback: Callable[[Palette], None]) -> None:
        self.remove_listener(callback)

    def add_theme_listener(self, callback: Callable[[Palette], None], priority: bool = False) -> None:
        self.add_listener(callback, priority=priority)

    def remove_theme_listener(self, callback: Callable[[Palette], None]) -> None:
        self.remove_listener(callback)


_theme_manager = ThemeManager()


def get_theme() -> Palette:
    """Return the active semantic Palette."""
    return _theme_manager.current


def get_palette() -> Palette:
    """Alias for get_theme()."""
    return _theme_manager.current


def set_theme(name: str) -> None:
    """Switch active theme via StyleEngine and notify all vector components."""
    _theme_manager.set_theme(name)


def set_dark_mode(is_dark: bool) -> None:
    """Toggle dark or light theme."""
    set_theme("dark" if is_dark else "light")


def get_available_themes() -> List[str]:
    """Return all available registered theme names."""
    return StyleEngine.get_available_themes()



def add_theme_listener(callback: Callable[[Palette], None], priority: bool = False) -> None:
    """Register a callback to be notified on theme changes."""
    _theme_manager.add_listener(callback, priority=priority)


def remove_theme_listener(callback: Callable[[Palette], None]) -> None:
    """Unregister a theme change callback."""
    _theme_manager.remove_listener(callback)


def resolve_ancestor_bg(widget: Optional[tk.Misc], palette: Optional[Palette] = None) -> str:
    """Declarative resolution of background color from nearest container or theme."""
    active_pal = palette or get_theme()
    if widget is None:
        return active_pal.bg

    curr = widget
    while curr is not None:
        if hasattr(curr, "bg_color") and curr.bg_color:
            return resolve_color_failsafe(curr.bg_color, palette=active_pal)
        if hasattr(curr, "_bg_color") and curr._bg_color:
            return resolve_color_failsafe(curr._bg_color, palette=active_pal)
        if hasattr(curr, "_parent_bg") and curr._parent_bg and getattr(curr, "_explicit_bg", None):
            return resolve_color_failsafe(curr._explicit_bg, palette=active_pal)

        if isinstance(curr, tk.Misc):
            try:
                bg = str(curr.cget("background")).lower()
                if bg:
                    for p_name, p_pal in THEME_PRESETS.items():
                        if p_name != active_pal.name:
                            if bg == p_pal.bg.lower():
                                return active_pal.bg
                            if bg == p_pal.card_bg.lower():
                                return active_pal.card_bg
                            if bg == p_pal.surface.lower():
                                return active_pal.surface
                    if bg not in ("#d9d9d9", "#2c2c2c", "#f0f0f0", "gray85", "systembuttonface"):
                        return resolve_color_failsafe(bg, master=curr, palette=active_pal)
            except Exception:
                pass
            curr = getattr(curr, "master", None)
        else:
            break

    return active_pal.bg


def cascade_bg_to_children(container: tk.Misc, bg_color: str, preserve_overrides: bool = True, render: bool = True, palette: Optional[Palette] = None) -> None:
    """Update background color of container and direct vector children."""
    resolved = resolve_color_failsafe(bg_color)
    pal = palette or get_theme()
    try:
        container.configure(background=resolved)
    except Exception:
        pass

    if hasattr(container, "winfo_children"):
        try:
            for child in container.winfo_children():
                if hasattr(child, "set_parent_bg"):
                    child.set_parent_bg(resolved, render=render)
                elif isinstance(child, tk.Label):
                    try:
                        child.configure(background=resolved, foreground=pal.text_muted)
                    except Exception:
                        try:
                            child.configure(background=resolved)
                        except Exception:
                            pass
                elif isinstance(child, tk.Frame):
                    try:
                        child.configure(background=resolved)
                    except Exception:
                        pass
        except Exception:
            pass


def is_inside_card(widget: Optional[tk.Misc]) -> bool:
    """Return True if widget is nested within a Card container."""
    curr = widget
    while curr is not None:
        if getattr(curr, "__class__", None).__name__ == "Card":
            return True
        curr = getattr(curr, "master", None)
    return False


def is_ttkbootstrap_installed() -> bool:
    """Check if ttkbootstrap package is importable in current environment."""
    import sys
    return "ttkbootstrap" in sys.modules


def apply_theme(
    root: tk.Misc,
    theme_name: str = "dark",
    preserve_overrides: bool = True,
    recursive: bool = True,
    auto_detect: bool = False,
    sync_fonts: bool = False,
    font: Optional[Any] = None,
    **kwargs,
) -> Callable[[], None]:
    """Apply theme to root window and style standard Tk container children."""
    if auto_detect:
        theme_name = detect_system_theme()

    set_theme(theme_name)
    pal = get_theme()

    if sync_fonts or font is not None or "font" in kwargs:
        from tkblend.font import sync_tk_fonts
        f_spec = font if font is not None else kwargs.get("font")
        sync_tk_fonts(root, font=f_spec, preserve_overrides=preserve_overrides)

    def _apply(w, p, container_bg=None):
        eff_bg = container_bg or p.bg
        try:
            if hasattr(w, "configure"):
                if isinstance(w, (tk.Tk, tk.Toplevel)):
                    w.configure(background=p.bg)
                    w._tkblend_theme_bg = p.bg
                elif hasattr(w, "_bg_label") and hasattr(w, "set_parent_bg"):
                    w.set_parent_bg(eff_bg)
                    if hasattr(w, "_bg_label") and w._bg_label.winfo_exists():
                        w._bg_label.configure(background=eff_bg)
                    if hasattr(w, "set_background") and getattr(w, "_explicit_bg_color", None) is None:
                        w._bg_color = p.card_bg
                        w.render()
                elif hasattr(w, "set_parent_bg"):
                    w.set_parent_bg(eff_bg)
                elif isinstance(w, (tk.Frame, tk.LabelFrame)):
                    cur = str(w.cget("background")).lower()
                    last_set = getattr(w, "_tkblend_theme_bg", None)
                    known_bgs = [preset.bg.lower() for preset in THEME_PRESETS.values()]
                    if last_set is not None or cur in ("#d9d9d9", "#2c2c2c", "#f0f0f0", "gray85", "systembuttonface") or not preserve_overrides or cur in known_bgs:
                        w.configure(background=eff_bg)
                        w._tkblend_theme_bg = eff_bg
                elif isinstance(w, (tk.Label, tk.Canvas)):
                    cur = str(w.cget("background")).lower()
                    last_set = getattr(w, "_tkblend_theme_bg", None)
                    known_bgs = [preset.bg.lower() for preset in THEME_PRESETS.values()]
                    if last_set is not None or cur in ("#d9d9d9", "#2c2c2c", "#f0f0f0", "gray85", "systembuttonface") or not preserve_overrides or cur in known_bgs:
                        w.configure(background=eff_bg)
                        w._tkblend_theme_bg = eff_bg
        except Exception:
            pass

        if recursive and hasattr(w, "winfo_children"):
            try:
                for c in w.winfo_children():
                    if hasattr(w, "_bg_label") and c is getattr(w, "_bg_label", None):
                        continue
                    child_bg = eff_bg
                    if hasattr(w, "bg_color") and w.bg_color:
                        child_bg = w.bg_color
                    elif hasattr(w, "_bg_color") and w._bg_color:
                        child_bg = w._bg_color
                    if hasattr(w, "content_frame") and c is getattr(w, "content_frame", None):
                        child_bg = p.surface
                    _apply(c, p, child_bg)
            except Exception:
                pass

    _apply(root, pal)

    def _on_change(new_pal: Palette):
        try:
            if root.winfo_exists():
                _apply(root, new_pal)
        except Exception:
            pass

    add_theme_listener(_on_change, priority=True)

    auto_cleanup = None
    if auto_detect:
        auto_cleanup = auto_theme(root=root, listen=True)

    def cleanup():
        remove_theme_listener(_on_change)
        if auto_cleanup:
            auto_cleanup()

    return cleanup


inject_theme = apply_theme


def bind_theme_changed(widget_or_cb: Any, callback: Optional[Callable[[Palette], None]] = None) -> None:
    if callback is not None:
        add_theme_listener(callback)
    elif callable(widget_or_cb):
        add_theme_listener(widget_or_cb)


def unbind_theme_changed(widget_or_cb: Any, callback: Optional[Callable[[Palette], None]] = None) -> None:
    if callback is not None:
        remove_theme_listener(callback)
    elif callable(widget_or_cb):
        remove_theme_listener(widget_or_cb)


def flush_theme_queue() -> None:
    """Flush any pending theme renders immediately."""
    _theme_manager._flush_renders()


def is_system_dark(fallback: bool = True) -> bool:
    """Detect if OS is in dark mode using darkdetect if available."""
    try:
        import darkdetect
        if hasattr(darkdetect, "isDark"):
            res = darkdetect.isDark()
            if isinstance(res, bool):
                return res
        if hasattr(darkdetect, "theme"):
            mode = darkdetect.theme()
            if mode:
                return mode.lower() == "dark"
        if hasattr(darkdetect, "isLight"):
            res = darkdetect.isLight()
            if isinstance(res, bool):
                return not res
        return fallback
    except Exception:
        return fallback


def detect_system_theme(fallback: str = "dark") -> str:
    """Return 'dark' or 'light' matching OS preference."""
    try:
        import darkdetect
        if hasattr(darkdetect, "theme"):
            mode = darkdetect.theme()
            if mode:
                return mode.lower()
        if hasattr(darkdetect, "isDark"):
            res = darkdetect.isDark()
            if isinstance(res, bool):
                return "dark" if res else "light"
        if hasattr(darkdetect, "isLight"):
            res = darkdetect.isLight()
            if isinstance(res, bool):
                return "light" if res else "dark"
        return fallback
    except Exception:
        return fallback


_auto_theme_timer = None


def auto_theme(
    root: Optional[tk.Misc] = None,
    dark: str = "dark",
    light: str = "light",
    interval_ms: int = 2000,
    listen: bool = True,
    **kwargs,
) -> Callable[[], None]:
    """Start listening or polling OS theme and update active theme when OS changes."""
    global _auto_theme_timer
    dark_theme = kwargs.get("dark_theme", dark)
    light_theme = kwargs.get("light_theme", light)

    # Initial apply
    is_dark = is_system_dark()
    initial_target = dark_theme if is_dark else light_theme
    set_theme(initial_target)

    stop_requested = False

    def _on_os_change(theme_val):
        if stop_requested:
            return
        if isinstance(theme_val, bool):
            target = dark_theme if theme_val else light_theme
        elif isinstance(theme_val, str):
            target = dark_theme if theme_val.lower() == "dark" else light_theme
        else:
            target = dark_theme if is_system_dark() else light_theme
        if get_theme().name != target:
            set_theme(target)
            if root is not None:
                try:
                    root.update()
                except Exception:
                    pass

    try:
        import darkdetect
    except ImportError:
        darkdetect = None

    if listen and darkdetect is not None and hasattr(darkdetect, "listener"):
        try:
            darkdetect.listener(_on_os_change)
        except Exception as e:
            logger.debug("Failed registering darkdetect listener: %s", e)

    def cleanup():
        nonlocal stop_requested
        stop_requested = True
        stop_auto_theme()

    return cleanup


def stop_auto_theme() -> None:
    """Stop auto-theme polling."""
    global _auto_theme_timer
    if _auto_theme_timer is not None:
        try:
            _auto_theme_timer.cancel()
        except Exception:
            pass
        _auto_theme_timer = None
