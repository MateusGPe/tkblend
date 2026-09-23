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
        except Exception:
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
    except Exception:
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
    except Exception:
        return hex_code


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
            cls._instance._previous_palette: Optional[Palette] = None
            cls._instance._listeners: List[Callable[[Palette], None]] = []
            cls._instance._priority_listeners: List[Callable[[Palette], None]] = []
        return cls._instance

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
            if key in self._palettes:
                self._current_palette = self._palettes[key]
            elif key in ("true", "1", "dark"):
                self._current_palette = DARK_PALETTE
            elif key in ("false", "0", "light"):
                self._current_palette = LIGHT_PALETTE
            else:
                raise ValueError(f"Unknown theme '{theme_or_palette}'. Available: {list(self._palettes.keys())}")
        self._previous_palette = old_pal
        self.notify_listeners()

    def get_palette(self) -> Palette:
        return self._current_palette

    def add_listener(self, callback: Callable[[Palette], None], priority: bool = False) -> None:
        if priority:
            if callback not in self._priority_listeners:
                self._priority_listeners.append(callback)
        else:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def add_priority_listener(self, callback: Callable[[Palette], None]) -> None:
        if callback not in self._priority_listeners:
            self._priority_listeners.append(callback)

    def remove_listener(self, callback: Callable[[Palette], None]) -> None:
        if callback in self._priority_listeners:
            self._priority_listeners.remove(callback)
        if callback in self._listeners:
            self._listeners.remove(callback)

    def remove_priority_listener(self, callback: Callable[[Palette], None]) -> None:
        if callback in self._priority_listeners:
            self._priority_listeners.remove(callback)

    def notify_listeners(self) -> None:
        # Priority listeners (e.g. root hierarchy apply_theme) execute FIRST top-down
        for callback in list(self._priority_listeners):
            try:
                callback(self._current_palette)
            except Exception:
                pass
        # Standard listeners execute next
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

def add_theme_listener(callback: Callable[[Palette], None], priority: bool = False) -> None:
    """Register a callback for theme changes."""
    _theme_manager.add_listener(callback, priority=priority)

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
                except Exception:
                    pass

        # Check ttk container style background
        if hasattr(curr, "winfo_class"):
            try:
                import tkinter.ttk as ttk
                style = ttk.Style()
                style_name = ""
                if hasattr(curr, "cget"):
                    try:
                        style_name = curr.cget("style")
                    except Exception:
                        pass
                if not style_name:
                    style_name = curr.winfo_class()
                ttk_bg = style.lookup(style_name, "background")
                if ttk_bg and str(ttk_bg).strip() not in ("", "None"):
                    res = resolve_color_failsafe(ttk_bg, master=curr, fallback=None)
                    if res:
                        return res
            except Exception:
                pass

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
        **kwargs: Extra options accepted for backward compatibility.

    Returns:
        A cleanup function to unregister the theme listener.
    """
    import tkinter as tk
    from .font import sync_tk_fonts

    if dark_mode is not None:
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
        except Exception:
            pass
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
        except Exception:
            pass

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
        except Exception:
            pass
        return True

    def _apply_hierarchy(target: Any, pal: Palette, container_bg: Optional[str] = None) -> None:
        if not hasattr(target, "winfo_exists"):
            return
        try:
            if not target.winfo_exists():
                return
        except Exception:
            return

        master = getattr(target, "master", None)
        # Skip or preserve internal backing label of Card/Frame (_bg_label)
        if master is not None and getattr(master, "_bg_label", None) is target:
            target_bg = getattr(master, "_parent_bg", container_bg or pal.bg)
            try:
                target.configure(background=target_bg)
            except Exception:
                pass
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
                except Exception:
                    pass
                next_container_bg = str(target._bg_color)
            elif hasattr(target, "_header") and hasattr(target, "_content"):
                # Accordion container
                if hasattr(target, "set_parent_bg"):
                    target.set_parent_bg(container_bg or pal.bg, force=not preserve_overrides)
                try:
                    target._on_theme_changed(pal)
                except Exception:
                    pass
                next_container_bg = pal.surface
            else:
                # Vector leaf widget
                if hasattr(target, "set_parent_bg"):
                    target.set_parent_bg(container_bg or pal.bg, force=not preserve_overrides)
                try:
                    target._on_theme_changed(pal)
                except Exception:
                    pass
        elif isinstance(target, (tk.Tk, tk.Toplevel)):
            try:
                target.configure(background=pal.bg)
                target._tkblend_injected_bg = pal.bg
            except Exception:
                pass
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
            except Exception:
                pass
            if _check_preserve(target, pal):
                try:
                    target.configure(background=target_bg)
                    target._tkblend_injected_bg = target_bg
                except Exception:
                    pass
            next_container_bg = target_bg
        elif isinstance(target, tk.Label):
            target_bg = container_bg or pal.bg
            if _check_preserve(target, pal):
                try:
                    font_str = str(target.cget("font")).lower()
                    fg_col = pal.fg if "bold" in font_str else pal.text_muted
                    target.configure(background=target_bg, foreground=fg_col)
                    target._tkblend_injected_bg = target_bg
                except Exception:
                    pass
        elif isinstance(target, tk.Canvas):
            target_bg = container_bg or pal.bg
            if _check_preserve(target, pal):
                try:
                    target.configure(background=target_bg)
                    target._tkblend_injected_bg = target_bg
                except Exception:
                    pass
            next_container_bg = target_bg

        if recursive and hasattr(target, "winfo_children"):
            try:
                children = target.winfo_children()
            except Exception:
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
        except Exception:
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

    try:
        root.bind("<Destroy>", _on_destroy, add="+")
    except Exception:
        pass

    def cleanup() -> None:
        remove_theme_listener(_theme_listener)

    return cleanup


inject_theme = apply_theme

