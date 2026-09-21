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
        if button_radius is not None:
            cfg.button_radius = float(button_radius)
        if entry_radius is not None:
            cfg.entry_radius = float(entry_radius)
        if check_radius is not None:
            cfg.check_radius = float(check_radius)
        if pbar_radius is not None:
            cfg.pbar_radius = float(pbar_radius)
        if scrollbar_radius is not None:
            cfg.scrollbar_radius = float(scrollbar_radius)
        if scale_radius is not None:
            cfg.scale_radius = float(scale_radius)
        if scale_thumb_radius is not None:
            cfg.scale_thumb_radius = float(scale_thumb_radius)
        if focus_ring_width is not None:
            cfg.focus_ring_width = float(focus_ring_width)
        if enable_shadows is not None:
            cfg.enable_shadows = bool(enable_shadows)
        if shadow_blur is not None:
            cfg.shadow_blur = float(shadow_blur)
        set_theme_config(cfg)

    register_theme(widget, theme_name=theme_name)

    style = ttk.Style(master=widget)
    style.theme_use(theme_name)

    # Sync root / toplevel background and broadcast <<ThemeChanged>>
    if widget is not None:
        try:
            pal = get_theme_palette()
            if hasattr(widget, "configure"):
                try:
                    widget.configure(background=pal["bg"])
                except Exception:
                    pass
            toplevel = widget.winfo_toplevel()
            if toplevel is not None and toplevel is not widget and hasattr(toplevel, "configure"):
                try:
                    toplevel.configure(background=pal["bg"])
                except Exception:
                    pass

            widget.event_generate("<<ThemeChanged>>")
            if toplevel is not None and toplevel is not widget:
                toplevel.event_generate("<<ThemeChanged>>")
        except Exception:
            pass

    return theme_name


def get_theme_palette() -> Dict[str, str]:
    """
    Get the resolved hex color palette of the active theme.
    """
    cfg = get_theme_config()
    if cfg is not None:
        def _h(val: int) -> str:
            return f"#{val & 0x00FFFFFF:06x}"

        return {
            "bg": _h(cfg.bg_color),
            "fg": _h(cfg.fg_color),
            "card_bg": _h(cfg.card_bg),
            "card_border": _h(cfg.card_border),
            "primary": _h(cfg.primary_color),
            "secondary": _h(cfg.secondary_color),
            "input_bg": _h(cfg.input_bg),
            "input_fg": _h(cfg.fg_color),
            "input_border": _h(cfg.input_border),
            "input_focus_border": _h(cfg.input_focus_border),
            "disabled_bg": _h(cfg.disabled_bg),
            "disabled_fg": _h(cfg.disabled_fg),
            "placeholder_fg": _h(cfg.disabled_fg),
            "track_bg": _h(cfg.track_bg),
            "thumb_color": _h(cfg.thumb_color),
            "thumb_hover": _h(cfg.thumb_hover),
            "thumb_active": _h(cfg.thumb_active),
            "select_bg": _h(cfg.primary_color),
            "select_fg": _h(cfg.primary_fg),
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
            widget.configure(  # type: ignore
                background=pal["card_bg"],
                foreground=pal["fg"],
                insertbackground=pal["fg"],
                selectbackground=pal["select_bg"],
                selectforeground=pal["select_fg"],
            )
        elif w_type == "Canvas":
            widget.configure(background=pal["card_bg"])  # type: ignore
        elif w_type == "Entry":
            widget.configure(  # type: ignore
                background=pal["input_bg"],
                foreground=pal["input_fg"],
                insertbackground=pal["input_fg"],
                selectbackground=pal["select_bg"],
                selectforeground=pal["select_fg"],
            )
    except Exception:
        pass


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
        self._user_var = kwargs.get("textvariable")
        super().__init__(master, **kwargs)

        self._placeholder_style = f"Placeholder.{self.winfo_name()}.TEntry"
        
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


class FloatingScrollbar(ttk.Scrollbar):
    """
    Modern floating overlay scrollbar that sits directly on top of scrollable views
    (Canvas, Text, Treeview). Features auto-hiding when idle, smooth dynamic expansion
    on hover (6px slim to 10px interactive pill), drag-lock, and multi-platform wheel support.
    """
    def __init__(
        self,
        master=None,
        target: Optional[tk.Widget] = None,
        autohide: bool = True,
        hide_delay_ms: int = 1200,
        **kwargs
    ):
        orient = kwargs.get("orient", "vertical")
        self._orient = str(orient).lower()
        if "style" not in kwargs:
            kwargs["style"] = "Floating.Vertical.TScrollbar" if self._orient == "vertical" else "Floating.Horizontal.TScrollbar"
        super().__init__(master, **kwargs)

        self.target = target
        self.autohide = autohide
        self.hide_delay_ms = hide_delay_ms
        self._hide_after_id = None
        self._is_hovered = False
        self._is_dragging = False
        self._is_expanded = False
        self._is_scrollable = False

        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")
        self.bind("<ButtonPress-1>", self._on_press, add="+")
        self.bind("<ButtonRelease-1>", self._on_release, add="+")
        self.bind("<B1-Motion>", self._on_motion, add="+")

        # Scrollbar mousewheel handling
        self.bind("<MouseWheel>", self._on_wheel_scroll, add="+")
        self.bind("<Button-4>", lambda e: self._handle_wheel(-1), add="+")
        self.bind("<Button-5>", lambda e: self._handle_wheel(1), add="+")

        bind_theme_changed(self, self._on_theme_changed)

        if self.target is not None:
            self.attach_to(self.target)

    def _get_orient(self) -> str:
        try:
            val = str(self.cget("orient")).lower()
            if "vert" in val:
                return "vertical"
            if "horiz" in val:
                return "horizontal"
        except Exception:
            pass
        return self._orient

    def attach_to(self, target: tk.Widget):
        """Attach this floating scrollbar to float on top of the given scrollable widget."""
        self.target = target
        orient = self._get_orient()
        if orient == "vertical":
            target.configure(yscrollcommand=self._on_target_scroll)
            self.configure(command=target.yview)
        else:
            target.configure(xscrollcommand=self._on_target_scroll)
            self.configure(command=target.xview)

        # Place initial overlay
        self._apply_placement()

        # Target bindings for reveal on activity & wheel
        target.bind("<Enter>", lambda e: self._on_target_enter(), add="+")
        target.bind("<Leave>", lambda e: self._on_target_leave(), add="+")
        target.bind("<MouseWheel>", self._on_target_wheel, add="+")
        target.bind("<Button-4>", lambda e: self._on_target_linux_wheel(-1), add="+")
        target.bind("<Button-5>", lambda e: self._on_target_linux_wheel(1), add="+")
        target.bind("<Configure>", lambda e: self._on_target_configure(), add="+")

        self._schedule_hide()

    def _apply_placement(self):
        if self.target is None:
            return
        orient = self._get_orient()
        thickness = 10 if self._is_expanded else 6
        if orient == "vertical":
            self.place(in_=self.target, relx=1.0, rely=0.0, relheight=1.0, anchor="ne", width=thickness)
        else:
            self.place(in_=self.target, relx=0.0, rely=1.0, relwidth=1.0, anchor="sw", height=thickness)
        self.lift()

    def _set_expanded(self, expanded: bool):
        if self._is_expanded == expanded:
            return
        self._is_expanded = expanded
        orient = self._get_orient()
        if orient == "vertical":
            style_name = "Hover.Floating.Vertical.TScrollbar" if expanded else "Floating.Vertical.TScrollbar"
        else:
            style_name = "Hover.Floating.Horizontal.TScrollbar" if expanded else "Floating.Horizontal.TScrollbar"
        try:
            self.configure(style=style_name)
        except Exception:
            pass
        if self.winfo_ismapped() and self.target is not None:
            self._apply_placement()

    def _on_target_scroll(self, first, last):
        self.set(first, last)
        try:
            f, l = float(first), float(last)
            self._is_scrollable = (f > 0.0 or l < 1.0)
        except Exception:
            self._is_scrollable = True

        if not self._is_scrollable:
            # Content fits completely, hide overlay
            self.place_forget()
        else:
            if not self.winfo_ismapped() and self.target is not None:
                self._apply_placement()
            self.show()
            self._schedule_hide()

    def show(self):
        self._cancel_hide()
        if not self._is_scrollable and self.target is not None:
            return
        if not self.winfo_ismapped() and self.target is not None:
            self._apply_placement()
        else:
            self.lift()

    def hide(self):
        if self.autohide and not self._is_hovered and not self._is_dragging:
            self.place_forget()

    def _cancel_hide(self):
        if self._hide_after_id:
            try:
                self.after_cancel(self._hide_after_id)
            except Exception:
                pass
            self._hide_after_id = None

    def _schedule_hide(self):
        if not self.autohide or self._is_hovered or self._is_dragging:
            return
        self._cancel_hide()
        self._hide_after_id = self.after(self.hide_delay_ms, self.hide)

    def _on_enter(self, event=None):
        self._is_hovered = True
        self._set_expanded(True)
        self.show()

    def _on_leave(self, event=None):
        self._is_hovered = False
        if not self._is_dragging:
            self._set_expanded(False)
            self._schedule_hide()

    def _on_press(self, event=None):
        self._is_dragging = True
        self._cancel_hide()
        self.lift()

    def _on_release(self, event=None):
        self._is_dragging = False
        if not self._is_hovered:
            self._set_expanded(False)
            self._schedule_hide()

    def _on_motion(self, event=None):
        self._cancel_hide()

    def _on_target_enter(self):
        if self._is_scrollable:
            self.show()
            self._schedule_hide()

    def _on_target_leave(self):
        if not self._is_hovered and not self._is_dragging:
            self._schedule_hide()

    def _on_target_configure(self):
        if self.winfo_ismapped() and self.target is not None:
            self._apply_placement()

    def _handle_wheel(self, delta_units: int):
        if self.target is None:
            return
        orient = self._get_orient()
        try:
            if orient == "vertical":
                self.target.yview_scroll(delta_units, "units")
            else:
                self.target.xview_scroll(delta_units, "units")
        except Exception:
            pass
        self.show()
        self._schedule_hide()

    def _on_wheel_scroll(self, event):
        if event.delta:
            delta_units = -1 if event.delta > 0 else 1
            self._handle_wheel(delta_units)

    def _on_target_wheel(self, event):
        self._on_wheel_scroll(event)

    def _on_target_linux_wheel(self, delta_units: int):
        self._handle_wheel(delta_units)

    def _on_theme_changed(self):
        orient = self._get_orient()
        if self._is_expanded:
            style_name = "Hover.Floating.Vertical.TScrollbar" if orient == "vertical" else "Hover.Floating.Horizontal.TScrollbar"
        else:
            style_name = "Floating.Vertical.TScrollbar" if orient == "vertical" else "Floating.Horizontal.TScrollbar"
        try:
            self.configure(style=style_name)
        except Exception:
            pass


class ThemedText(ttk.Frame):
    """
    Modern scrollable multi-line text editor with Blend2D palette synchronization
    and an integrated FloatingScrollbar overlay.
    """
    def __init__(self, master=None, autohide_scrollbar: bool = True, **kwargs):
        super().__init__(master)

        text_opts = {
            "relief": "flat",
            "highlightthickness": 0,
            "padx": 12,
            "pady": 12,
            "wrap": "word",
            "font": ("Helvetica", 10),
        }
        text_opts.update(kwargs)

        self.text = tk.Text(self, **text_opts)
        self.text.pack(fill="both", expand=True)

        self.scrollbar = FloatingScrollbar(
            self, target=self.text, orient="vertical", autohide=autohide_scrollbar
        )

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
    Modern scrollable frame container with canvas blitting and attached FloatingScrollbar.
    """
    def __init__(self, master=None, autohide_scrollbar: bool = True, **kwargs):
        super().__init__(master, **kwargs)

        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.canvas.pack(fill="both", expand=True)

        self.content = ttk.Frame(self.canvas)
        self._window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.scrollbar = FloatingScrollbar(
            self, target=self.canvas, orient="vertical", autohide=autohide_scrollbar
        )

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.content.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

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
        pal = get_theme_palette()
        self.canvas.configure(background=pal["bg"])

