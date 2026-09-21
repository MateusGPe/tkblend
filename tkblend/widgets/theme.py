"""
Theming and design token management for tkblend modern UI widgets,
with seamless Tkinter and ttk integration.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
import os
import sys
from dataclasses import dataclass, field
from typing import Callable, Set, Dict, Union, Optional, List, Any


@dataclass
class Theme:
    """
    Design tokens and semantic colors for modern widgets and standard Tk/ttk controls.
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
    surface_raised: str = "#262638"
    surface_overlay: str = "#181825"

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
    warning="#f9e2af",
    danger="#f38ba8",
    info="#89dceb",
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
    warning="#df8e1d",
    danger="#d20f39",
    info="#209fb5",
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


def apply_ttk_theme(theme: Theme, style: Optional[ttk.Style] = None) -> ttk.Style:
    """
    Configure ttk.Style to seamlessly match the specified Theme tokens.
    """
    if style is None:
        style = ttk.Style()

    # Use 'clam' as base engine if available for reliable custom color control
    available_themes = style.theme_names()
    if "clam" in available_themes and style.theme_use() != "clam":
        try:
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

    # TFrame & TLabelframe
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

    # TLabel
    style.configure(
        "TLabel",
        background=theme.bg_card,
        foreground=theme.text,
    )
    style.configure(
        "Muted.TLabel",
        background=theme.bg_card,
        foreground=theme.text_muted,
    )
    style.configure(
        "Heading.TLabel",
        background=theme.bg_card,
        foreground=theme.primary,
        font=(theme.font_family, int(theme.font_size_lg), "bold"),
    )

    # TButton
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
        background=[
            ("pressed", theme.secondary_press),
            ("active", theme.secondary_hover),
            ("disabled", theme.bg_surface),
        ],
        foreground=[
            ("disabled", theme.text_disabled),
        ],
    )

    style.configure(
        "Primary.TButton",
        background=theme.primary,
        foreground=theme.primary_text,
        bordercolor=theme.border_focused,
        focuscolor=theme.border_focused,
        lightcolor=theme.primary_hover,
        darkcolor=theme.primary_press,
        padding=(12, 6),
    )
    style.map(
        "Primary.TButton",
        background=[
            ("pressed", theme.primary_press),
            ("active", theme.primary_hover),
            ("disabled", theme.secondary),
        ],
        foreground=[
            ("disabled", theme.text_disabled),
        ],
    )

    # Danger.TButton
    style.configure(
        "Danger.TButton",
        background=theme.danger,
        foreground="#ffffff",
        bordercolor=theme.danger,
        focuscolor=theme.border_focused,
        padding=(12, 6),
    )

    # Success.TButton
    style.configure(
        "Success.TButton",
        background=theme.success,
        foreground="#ffffff",
        bordercolor=theme.success,
        focuscolor=theme.border_focused,
        padding=(12, 6),
    )

    # TEntry & TCombobox
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
    style.map(
        "TEntry",
        bordercolor=[("focus", theme.border_focused)],
        lightcolor=[("focus", theme.border_focused)],
    )

    style.configure(
        "TCombobox",
        fieldbackground=theme.bg_input,
        background=theme.secondary,
        foreground=theme.text,
        arrowcolor=theme.text,
        bordercolor=theme.border,
        padding=4,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", theme.bg_input)],
        selectbackground=[("readonly", theme.selection_bg)],
        selectforeground=[("readonly", theme.selection_fg)],
    )

    # TNotebook (Tabs)
    style.configure(
        "TNotebook",
        background=theme.bg_card,
        bordercolor=theme.border,
        darkcolor=theme.border,
        lightcolor=theme.border,
        tabmargins=[2, 4, 2, 0],
    )
    style.configure(
        "TNotebook.Tab",
        background=theme.bg_surface_alt,
        foreground=theme.text_muted,
        padding=[14, 6],
        bordercolor=theme.border,
        darkcolor=theme.border,
        lightcolor=theme.border,
        focuscolor=theme.border,
    )
    style.map(
        "TNotebook.Tab",
        background=[
            ("selected", theme.bg_card),
            ("active", theme.bg_hover),
        ],
        foreground=[
            ("selected", theme.primary),
            ("active", theme.text),
        ],
        bordercolor=[
            ("selected", theme.border),
            ("active", theme.border),
        ],
        lightcolor=[
            ("selected", theme.border),
            ("active", theme.border),
        ],
        darkcolor=[
            ("selected", theme.border),
            ("active", theme.border),
        ],
    )

    # Treeview
    style.configure(
        "Treeview",
        background=theme.bg_card,
        foreground=theme.text,
        fieldbackground=theme.bg_card,
        bordercolor=theme.border,
        lightcolor=theme.border,
        darkcolor=theme.border,
        rowheight=28,
    )
    style.map(
        "Treeview",
        background=[("selected", theme.selection_bg)],
        foreground=[("selected", theme.selection_fg)],
    )
    style.configure(
        "Treeview.Heading",
        background=theme.bg_surface_alt,
        foreground=theme.text,
        bordercolor=theme.border,
        lightcolor=theme.border,
        darkcolor=theme.border,
        font=(theme.font_family, int(theme.font_size_sm), "bold"),
        padding=6,
    )
    style.map(
        "Treeview.Heading",
        background=[("active", theme.bg_hover)],
    )

    # TScrollbar
    style.configure(
        "TScrollbar",
        background=theme.scrollbar_thumb,
        troughcolor=theme.scrollbar_track,
        bordercolor=theme.scrollbar_track,
        arrowcolor=theme.text_muted,
    )
    style.map(
        "TScrollbar",
        background=[
            ("active", theme.scrollbar_thumb_hover),
            ("pressed", theme.primary),
        ],
    )

    # TProgressbar
    style.configure(
        "TProgressbar",
        troughcolor=theme.track,
        background=theme.primary,
        bordercolor=theme.border,
        lightcolor=theme.primary_hover,
        darkcolor=theme.primary_press,
    )

    # TSeparator
    style.configure("TSeparator", background=theme.border)

    # TRadiobutton & TCheckbutton
    style.configure(
        "TRadiobutton",
        background=theme.bg_window,
        foreground=theme.text,
        indicatorcolor=theme.bg_input,
    )
    style.map(
        "TRadiobutton",
        indicatorcolor=[("selected", theme.primary), ("active", theme.bg_hover)],
    )
    style.configure(
        "TCheckbutton",
        background=theme.bg_window,
        foreground=theme.text,
        indicatorcolor=theme.bg_input,
    )
    style.map(
        "TCheckbutton",
        indicatorcolor=[("selected", theme.primary), ("active", theme.bg_hover)],
    )

    return style


def _find_ancestral_bg(widget: tk.Misc, theme: Theme) -> str:
    """Find effective contextual background for a standard Tk widget."""
    cur = getattr(widget, "master", None)
    while cur is not None:
        try:
            # If container is a ModernCard or its content
            if hasattr(cur, "_title") and (hasattr(cur, "_surface") or hasattr(cur, "surface")):
                if hasattr(cur, "_custom_bg_color") and cur._custom_bg_color is not None:
                    return str(cur._custom_bg_color)
                return theme.bg_card

            master = getattr(cur, "master", None)
            if master is not None and hasattr(master, "content") and master.content is cur:
                if hasattr(master, "_custom_bg_color") and master._custom_bg_color is not None:
                    return str(master._custom_bg_color)
                return theme.bg_card

            # If container is a ModernFrame / custom surface
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
    Recursively apply theme styling to a standard Tk widget hierarchy with context awareness.
    """
    t = theme or ThemeManager.get_theme()
    if not root_or_widget.winfo_exists():
        return

    # Apply TTK theme once at the root entry point
    try:
        apply_ttk_theme(t)
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


class _ThemeManager:
    """
    Global theme manager singleton managing registered themes, listeners,
    and automatic root window live synchronization.
    """

    def __init__(self):
        self._current_theme: Theme = DARK_THEME
        self._registry: Dict[str, Theme] = {
            "dark": DARK_THEME,
            "light": LIGHT_THEME,
        }
        self._listeners: Set[Callable[[Theme], None]] = set()
        self._bound_roots: Set[tk.Misc] = set()
        self.animations_enabled: bool = True

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

        # Configure ttk styles if available
        try:
            apply_ttk_theme(self._current_theme)
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

    def bind_root(self, root: tk.Misc) -> None:
        """
        Bind a root or toplevel window for automatic live synchronization on theme change.
        """
        self._bound_roots.add(root)
        if root.winfo_exists():
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
