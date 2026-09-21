"""
Native TTK Theme Engine Bridge and Theme Helpers for Tkinter and Blend2D.
"""

from __future__ import annotations
import logging
import weakref
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Callable, Tuple, Union

logger = logging.getLogger(__name__)

try:
    from tkblend._tkblend import (  # type: ignore
        ThemeConfig,
        register_ttk_theme as _native_register_theme,
        set_theme_dark_mode as _native_set_dark_mode,
        set_theme_config as _native_set_config,
        get_theme_config as _native_get_config,
    )
except ImportError:
    ThemeConfig = None  # type: ignore
    _native_register_theme = None  # type: ignore
    _native_set_dark_mode = None  # type: ignore
    _native_set_config = None  # type: ignore
    _native_get_config = None  # type: ignore

# Default font for ThemedText widget
_DEFAULT_TEXT_FONT = ("Helvetica", 10)

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
    "card_bg": "#ffffff",
    "inputbg": "#ffffff",
    "inputfg": "#212529",
    "selectbg": "#0d6efd",
    "selectfg": "#ffffff",
}

# Maps apply_theme() keyword arg names → (cfg attribute, cast function)
_CFG_FLOAT_OVERRIDES: Tuple[Tuple[str, str], ...] = (
    ("button_radius",      "button_radius"),
    ("entry_radius",       "entry_radius"),
    ("check_radius",       "check_radius"),
    ("pbar_radius",        "pbar_radius"),
    ("scrollbar_radius",   "scrollbar_radius"),
    ("scale_radius",       "scale_radius"),
    ("scale_thumb_radius", "scale_thumb_radius"),
    ("focus_ring_width",   "focus_ring_width"),
    ("shadow_blur",        "shadow_blur"),
)


def _get_interp_addr(widget: Optional[tk.Misc] = None) -> int:
    """Safely extract Tcl_Interp memory address from Tk widget or default root."""
    if widget is None:
        widget = getattr(tk, "_default_root", None) or tk._get_default_root()
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
    check_radius: Optional[float] = None,
    pbar_radius: Optional[float] = None,
    scrollbar_radius: Optional[float] = None,
    scale_radius: Optional[float] = None,
    scale_thumb_radius: Optional[float] = None,
    focus_ring_width: Optional[float] = None,
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
    check_radius : float, optional
        Custom corner radius for checkbuttons.
    pbar_radius : float, optional
        Custom corner radius for progressbars.
    scrollbar_radius : float, optional
        Custom corner radius for scrollbars.
    scale_radius : float, optional
        Custom corner radius for scale trough.
    scale_thumb_radius : float, optional
        Custom radius for scale thumb slider.
    focus_ring_width : float, optional
        Custom stroke width for glowing focus rings.
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
        # Apply float overrides via DRY dict-driven loop
        local_vals = locals()
        for arg_name, attr_name in _CFG_FLOAT_OVERRIDES:
            val = local_vals[arg_name]
            if val is not None:
                setattr(cfg, attr_name, float(val))
        if enable_shadows is not None:
            cfg.enable_shadows = bool(enable_shadows)
        set_theme_config(cfg)

    register_theme(widget, theme_name=theme_name)

    style = ttk.Style(master=widget)
    style.theme_use(theme_name)

    # Sync root / toplevel background, hook autostyle, and broadcast <<ThemeChanged>>
    if widget is not None:
        _setup_card_autostyle_hook(widget)
        _sync_root_background(widget)
        sync_card_children(widget)

    return theme_name


_MAPPED_HOOKED_ROOTS: set[int] = set()


def is_inside_card(widget: tk.Misc) -> bool:
    """
    Check if a widget is nested inside a Card or Labelframe container.

    Traverses up the widget hierarchy inspecting parent classes and styles
    for 'TLabelframe', 'Labelframe', or style names containing 'Card' or 'Notebook'.
    """
    try:
        curr = widget
        parent_name = curr.winfo_parent()
        while parent_name:
            parent = curr._nametowidget(parent_name)
            p_class = parent.winfo_class()
            if p_class in ("TLabelframe", "Labelframe") or "Card" in p_class or "Notebook" in p_class:
                return True
            if hasattr(parent, "cget"):
                try:
                    s = str(parent.cget("style"))
                    if "Card" in s or "Notebook" in s or "TLabelframe" in s:
                        return True
                except (tk.TclError, Exception):
                    pass
            curr = parent
            parent_name = curr.winfo_parent()
    except Exception:
        pass
    return False


def _apply_card_style(widget: tk.Misc, pal: Dict[str, str]) -> None:
    """
    Apply card-level styling to a widget nested inside a Card/Labelframe.
    Only upgrades default unstyled widgets to avoid overriding custom user styles.
    """
    try:
        w_class = widget.winfo_class()
    except Exception:
        return

    # 1. TTK widgets (inspect style)
    if hasattr(widget, "cget"):
        try:
            current_style = str(widget.cget("style"))
        except (tk.TclError, Exception):
            current_style = ""

        if w_class == "TFrame":
            if current_style in ("", "TFrame"):
                try:
                    widget.configure(style="Card.TFrame")
                except tk.TclError:
                    pass
            return
        elif w_class == "TLabel":
            if current_style in ("", "TLabel"):
                try:
                    widget.configure(style="Card.TLabel")
                except tk.TclError:
                    pass
            return
        elif w_class == "TCheckbutton":
            if current_style in ("", "TCheckbutton"):
                try:
                    widget.configure(style="Card.TCheckbutton")
                except tk.TclError:
                    pass
            elif current_style == "Switch.TCheckbutton":
                try:
                    widget.configure(style="Card.Switch.TCheckbutton")
                except tk.TclError:
                    pass
            return
        elif w_class == "TRadiobutton":
            if current_style in ("", "TRadiobutton"):
                try:
                    widget.configure(style="Card.TRadiobutton")
                except tk.TclError:
                    pass
            return
        elif w_class == "Treeview":
            try:
                widget.configure(background=pal["card_bg"], fieldbackground=pal["card_bg"])
            except tk.TclError:
                pass
            return

    # 2. Classic Tk widgets
    try:
        if w_class == "Frame":
            widget.configure(background=pal["card_bg"])
        elif w_class == "Label":
            try:
                widget.configure(background=pal["card_bg"], foreground=pal["fg"])
            except tk.TclError:
                widget.configure(background=pal["card_bg"])
        elif w_class in ("Checkbutton", "Radiobutton"):
            widget.configure(
                background=pal["card_bg"],
                activebackground=pal["card_bg"],
                foreground=pal["fg"],
                selectcolor=pal["card_bg"],
            )
    except (tk.TclError, Exception):
        pass


def sync_card_children(root_or_container: tk.Misc) -> None:
    """
    Recursively scan all descendant widgets under root_or_container and
    synchronize their backgrounds/styles if nested inside a Card or Labelframe.
    """
    pal = get_theme_palette()

    def _walk(w: tk.Misc) -> None:
        try:
            if is_inside_card(w):
                _apply_card_style(w, pal)
            for child in w.winfo_children():
                _walk(child)
        except Exception:
            pass

    _walk(root_or_container)


def _setup_card_autostyle_hook(root: tk.Misc) -> None:
    """
    Hook a <Map> event listener on the toplevel window so newly created widgets
    mounted inside Cards/Labelframes are automatically styled with card background.
    """
    try:
        toplevel = root.winfo_toplevel()
    except Exception:
        return

    top_id = id(toplevel)
    if top_id in _MAPPED_HOOKED_ROOTS:
        return
    _MAPPED_HOOKED_ROOTS.add(top_id)

    def _on_map(event: Any) -> None:
        try:
            w = event.widget
            if isinstance(w, str):
                w = toplevel._nametowidget(w)
            if w and hasattr(w, "winfo_class") and is_inside_card(w):
                _apply_card_style(w, get_theme_palette())
        except Exception:
            pass

    def _on_destroy(event: Any) -> None:
        try:
            if event.widget is toplevel:
                _MAPPED_HOOKED_ROOTS.discard(top_id)
        except Exception:
            pass

    try:
        toplevel.bind_all("<Map>", _on_map, add="+")
        toplevel.bind("<Destroy>", _on_destroy, add="+")
    except Exception as exc:
        logger.debug("Failed to hook card autostyle events: %s", exc)


def _sync_root_background(widget: tk.Misc) -> None:
    """Sync background color on root/toplevel and fire <<ThemeChanged>>."""
    try:
        pal = get_theme_palette()
        bg = pal["bg"]
        _try_configure_bg(widget, bg)
        toplevel = widget.winfo_toplevel()
        if toplevel is not widget:
            _try_configure_bg(toplevel, bg)
        sync_card_children(toplevel)
        widget.event_generate("<<ThemeChanged>>")
        if toplevel is not widget:
            toplevel.event_generate("<<ThemeChanged>>")
    except tk.TclError as exc:
        logger.debug("ThemeChanged sync error: %s", exc)


def _try_configure_bg(widget: tk.Misc, color: str) -> None:
    """Attempt to set background on a widget, silently ignoring unsupported options."""
    try:
        widget.configure(background=color)  # type: ignore[arg-type]
    except tk.TclError:
        pass


def get_theme_palette() -> Dict[str, str]:
    """
    Get the resolved hex color palette of the active theme.
    """
    cfg = get_theme_config()
    if cfg is not None:
        def _h(val: int) -> str:
            return f"#{val & 0x00FFFFFF:06x}"

        return {
            "bg":                 _h(cfg.bg_color),
            "fg":                 _h(cfg.fg_color),
            "card_bg":            _h(cfg.card_bg),
            "card_border":        _h(cfg.card_border),
            "primary":            _h(cfg.primary_color),
            "primary_hover":      _h(cfg.primary_hover),
            "primary_active":     _h(cfg.primary_active),
            "primary_fg":         _h(cfg.primary_fg),
            "secondary":          _h(cfg.secondary_color),
            "secondary_hover":    _h(cfg.secondary_hover),
            "secondary_fg":       _h(cfg.secondary_fg),
            "success":            _h(cfg.success_color),
            "warning":            _h(cfg.warning_color),
            "destructive":        _h(cfg.destructive_color),
            "danger":             _h(cfg.destructive_color),
            "input_bg":           _h(cfg.input_bg),
            "input_fg":           _h(cfg.fg_color),
            "input_border":       _h(cfg.input_border),
            "input_focus_border": _h(cfg.input_focus_border),
            "disabled_bg":        _h(cfg.disabled_bg),
            "disabled_fg":        _h(cfg.disabled_fg),
            "placeholder_fg":     _h(cfg.disabled_fg),
            "track_bg":           _h(cfg.track_bg),
            "thumb":              _h(cfg.thumb_color),
            "thumb_color":        _h(cfg.thumb_color),
            "thumb_hover":        _h(cfg.thumb_hover),
            "thumb_active":       _h(cfg.thumb_active),
            "select_bg":          _h(cfg.primary_color),
            "select_fg":          _h(cfg.primary_fg),
        }
    return dict(_FALLBACK_BOOTSTRAP_PALETTE)


def sync_widget_colors(widget: tk.Misc) -> None:
    """
    Synchronize colors on standard Tk widgets (tk.Text, tk.Canvas, tk.Entry) to match the active theme.
    """
    pal = get_theme_palette()
    w_type = widget.winfo_class() if hasattr(widget, "winfo_class") else ""
    try:
        if w_type == "Text":
            widget.configure(  # type: ignore[arg-type]
                background=pal["card_bg"],
                foreground=pal["fg"],
                insertbackground=pal["fg"],
                selectbackground=pal["select_bg"],
                selectforeground=pal["select_fg"],
            )
        elif w_type == "Canvas":
            widget.configure(background=pal["card_bg"])  # type: ignore[arg-type]
        elif w_type == "Entry":
            widget.configure(  # type: ignore[arg-type]
                background=pal["input_bg"],
                foreground=pal["input_fg"],
                insertbackground=pal["input_fg"],
                selectbackground=pal["select_bg"],
                selectforeground=pal["select_fg"],
            )
    except tk.TclError as exc:
        logger.debug("sync_widget_colors error on %s: %s", w_type, exc)


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
        except tk.TclError:
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

    # Parse inline alpha suffix: 'token/0.5' or 'token:0.5'
    for sep in ("/", ":"):
        if sep in raw and not (sep == ":" and raw.startswith("#")):
            name_part, alpha_part = raw.rsplit(sep, 1)
            # Always consume the separator — resolve the base token even if alpha is invalid
            raw = name_part.strip()
            try:
                val = float(alpha_part.strip())
                parsed_alpha = val if val <= 1.0 else val / 255.0
            except ValueError:
                pass  # invalid alpha portion — base token still resolved
            break  # only one separator applies

    if alpha is not None:
        parsed_alpha = float(alpha) if alpha <= 1.0 else float(alpha) / 255.0

    lower_name = raw.lower()
    style = get_active_style()

    hex_color: Optional[str] = None
    if style is not None and hasattr(style, "colors") and hasattr(style.colors, lower_name):
        hex_color = getattr(style.colors, lower_name)
    else:
        pal = get_theme_palette()
        if lower_name in pal:
            hex_color = pal[lower_name]
        elif lower_name in _FALLBACK_BOOTSTRAP_PALETTE:
            hex_color = _FALLBACK_BOOTSTRAP_PALETTE[lower_name]
        else:
            hex_color = raw

    if parsed_alpha is not None and hex_color.startswith("#"):
        clean_hex = hex_color[1:]
        if len(clean_hex) == 8:
            clean_hex = clean_hex[:6]
        elif len(clean_hex) in (3, 4):
            clean_hex = "".join(c * 2 for c in clean_hex[:3])
        alpha_byte = max(0, min(255, int(parsed_alpha * 255.0)))
        return f"#{clean_hex}{alpha_byte:02x}"

    return hex_color


def bind_theme_changed(widget: tk.Misc, callback: Callable[[], None]) -> None:
    """
    Bind a callback to be invoked whenever the ttk/ttkbootstrap theme changes.
    Safely handles widget destruction without leaking references or callback closures.
    """
    if hasattr(callback, "__self__"):
        w_ref = weakref.ref(callback.__self__)
        func = callback.__func__
        def _safe_callback():
            inst = w_ref()
            if inst is not None:
                try:
                    if hasattr(inst, "winfo_exists") and not inst.winfo_exists():
                        return
                    func(inst)
                except Exception:
                    pass
    else:
        def _safe_callback():
            try:
                if hasattr(widget, "winfo_exists") and not widget.winfo_exists():
                    return
                callback()
            except Exception:
                pass

    top_bind_id = None
    toplevel = None

    def _on_theme(event=None):
        _safe_callback()

    def _cleanup(event=None):
        nonlocal top_bind_id, toplevel
        if event is not None and getattr(event, "widget", None) != widget:
            return
        if toplevel is not None and top_bind_id is not None:
            try:
                toplevel.unbind("<<ThemeChanged>>", top_bind_id)
            except Exception:
                pass
            top_bind_id = None

    widget.bind("<<ThemeChanged>>", _on_theme, add="+")
    widget.bind("<Destroy>", _cleanup, add="+")

    try:
        toplevel = widget.winfo_toplevel()
        if toplevel is not widget:
            top_bind_id = toplevel.bind("<<ThemeChanged>>", _on_theme, add="+")
    except (tk.TclError, Exception) as exc:
        logger.debug("bind_theme_changed error: %s", exc)


# =============================================================================
# Modern Reactive Widgets
# =============================================================================

class ThemedEntry(ttk.Entry):
    """
    Modern TTK Entry with built-in placeholder text, crisp focus handling,
    and automatic theme synchronization.
    """
    def __init__(self, master=None, placeholder: str = "", **kwargs):
        self._placeholder = placeholder
        self._has_placeholder = False
        super().__init__(master, **kwargs)

        # Use id(self) for a guaranteed-unique style name across all instances
        self._placeholder_style = f"Placeholder.{id(self)}.TEntry"

        self.bind("<FocusIn>", self._on_focus_in, add="+")
        self.bind("<FocusOut>", self._on_focus_out, add="+")
        bind_theme_changed(self, self._on_theme_changed)

        self._configure_placeholder_style()
        if self._placeholder and not self.get():
            self._show_placeholder()

    def _configure_placeholder_style(self):
        pal = get_theme_palette()
        style = ttk.Style(master=self)
        style.configure(self._placeholder_style, foreground=pal["placeholder_fg"])

    def _show_placeholder(self):
        if not self._has_placeholder and not super().get():
            self._has_placeholder = True
            self.configure(style=self._placeholder_style)
            super().insert(0, self._placeholder)

    def _hide_placeholder(self):
        if self._has_placeholder:
            self._has_placeholder = False
            self.configure(style="TEntry")
            super().delete(0, tk.END)

    def _on_focus_in(self, event=None):
        if self._has_placeholder:
            self._hide_placeholder()

    def _on_focus_out(self, event=None):
        if not super().get() and self._placeholder:
            self._show_placeholder()

    def _on_theme_changed(self):
        self._configure_placeholder_style()
        if self._has_placeholder:
            self.configure(style=self._placeholder_style)
        else:
            self.configure(style="TEntry")

    def get(self) -> str:
        if self._has_placeholder:
            return ""
        return super().get()

    def set(self, value: str):
        self._hide_placeholder()
        super().delete(0, tk.END)
        super().insert(0, value)
        if not value and self._placeholder:
            self._show_placeholder()


class SearchEntry(ThemedEntry):
    """
    Modern search input field with placeholder text and search icon styling.
    """
    def __init__(self, master=None, placeholder: str = "Search...", **kwargs):
        super().__init__(master, placeholder=placeholder, **kwargs)


class ThemedText(ttk.Frame):
    """
    Modern scrollable multi-line text editor with Blend2D palette synchronization
    and an integrated docked native TTK scrollbar.
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master)

        text_opts = {
            "relief": "flat",
            "highlightthickness": 0,
            "padx": 12,
            "pady": 12,
            "wrap": "word",
            "font": _DEFAULT_TEXT_FONT,
        }
        kwargs.pop("autohide_scrollbar", None)
        text_opts.update(kwargs)

        self.scrollbar = ttk.Scrollbar(self, orient="vertical")
        self.text = tk.Text(self, **text_opts)

        self.scrollbar.configure(command=self.text.yview)
        self.text.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y", padx=(2, 4), pady=2)
        self.text.pack(side="left", fill="both", expand=True)

        self.text.bind("<Button-4>", lambda e: self.text.yview_scroll(-1, "units"), add="+")
        self.text.bind("<Button-5>", lambda e: self.text.yview_scroll(1, "units"), add="+")

        self._sync_theme()
        bind_theme_changed(self, self._sync_theme)

    def _sync_theme(self):
        sync_widget_colors(self.text)

    def insert(self, *args, **kwargs):
        return self.text.insert(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.text.delete(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.text.get(*args, **kwargs)


class ThemedScrolledFrame(ttk.Frame):
    """
    Modern scrollable frame container with canvas blitting and attached docked TTK scrollbar.
    """
    def __init__(self, master=None, **kwargs):
        kwargs.pop("autohide_scrollbar", None)
        super().__init__(master, **kwargs)

        self.scrollbar = ttk.Scrollbar(self, orient="vertical")
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)

        self.scrollbar.configure(command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y", padx=(2, 4), pady=2)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.content = ttk.Frame(self.canvas)
        self._window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.content.bind("<MouseWheel>", self._on_mousewheel)
        # Linux wheel bindings delegate to the canvas directly
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
        self.content.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.content.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        self._sync_theme()
        bind_theme_changed(self, self._sync_theme)

    def _on_content_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self._window_id, width=event.width)

    def _on_mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _sync_theme(self):
        # Use card_bg: this frame is a content container, not a root surface
        pal = get_theme_palette()
        self.canvas.configure(background=pal["card_bg"])
