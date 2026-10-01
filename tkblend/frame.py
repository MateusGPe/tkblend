"""
BlendFrame - High-performance native vector canvas frame powered by Blend2D.
Intercepts native Tk Expose and Configure events directly on the OS window.
"""

from __future__ import annotations
import logging
import tkinter as tk
from typing import Optional, Callable, Any
from contextlib import contextmanager
import ctypes

logger = logging.getLogger(__name__)

from tkblend._tkblend import attach_widget as _native_attach_widget  # type: ignore
from tkblend.surface import Surface, ColorLike
from tkblend.theme import (
    resolve_theme_color,
    add_theme_listener,
    remove_theme_listener,
    is_inside_card,
)


def get_interp_addr(tk_obj: Any) -> int:
    """Extract the raw Tcl_Interp* pointer address from a tkinter object."""
    if hasattr(tk_obj, "interpaddr"):
        return int(tk_obj.interpaddr())
    try:
        class _Tkapp(ctypes.Structure):
            _fields_ = [
                ("ob_refcnt", ctypes.c_ssize_t),
                ("ob_type", ctypes.c_void_p),
                ("interp", ctypes.c_void_p),
            ]
        tkapp = _Tkapp.from_address(id(tk_obj))
        if tkapp.interp:
            return int(tkapp.interp)
    except Exception as e:
        logger.debug("Failed ctypes interpaddr extraction: %s", e)
    raise RuntimeError("Unable to extract Tcl_Interp pointer address from tkinter instance")


class BlendFrame(tk.Frame):
    """
    Flicker-free, high-performance 2D vector drawing frame powered by Blend2D.
    Directly renders to the widget's native OS window (X11/HWND/NSView) upon Expose events,
    completely bypassing tk.Canvas and tk.PhotoImage.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 300,
        height: int = 200,
        bg: Optional[str] = None,
        bootstyle: Optional[str] = None,
        on_draw: Optional[Callable[[Surface], None]] = None,
        auto_theme_redraw: bool = True,
        **kwargs,
    ):
        self._logical_w = max(1, int(width))
        self._logical_h = max(1, int(height))
        self._on_draw = on_draw
        self._bootstyle = bootstyle
        self._auto_theme_redraw = auto_theme_redraw
        self._is_destroyed = False
        self._photo: Optional[Any] = None

        # Resolve initial background color
        if bg is not None:
            self._bg_color = bg
        elif bootstyle is not None:
            self._bg_color = bootstyle
        else:
            self._bg_color = "bg"

        bg_token = self._bg_color
        if bg_token in ("bg", "card_bg") and is_inside_card(master if master is not None else self):
            bg_token = "card_bg"

        resolved_bg = resolve_theme_color(bg_token)
        if resolved_bg.startswith("#") and len(resolved_bg) == 9:
            resolved_bg = resolved_bg[:7]

        # Filter kwargs to only valid tk.Frame options
        FRAME_VALID_KEYS = {
            "background", "bd", "bg", "border", "borderwidth", "class", "colormap",
            "container", "cursor", "height", "highlightbackground", "highlightcolor",
            "highlightthickness", "padx", "pady", "relief", "takefocus", "visual", "width"
        }
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in FRAME_VALID_KEYS}

        super().__init__(
            master,
            background=resolved_bg,
            **filtered_kwargs,
        )

        # Force window existence and attach native Blend2D surface hook
        interp_ptr = get_interp_addr(self.tk)
        self._handle = _native_attach_widget(interp_ptr, str(self._w))
        self._surface = Surface(self._handle)
        if self._logical_w > 1 or self._logical_h > 1:
            self._surface.resize(self._logical_w, self._logical_h)

        self.bind("<Configure>", self._on_configure, add="+")
        self.bind("<Destroy>", self._on_destroy_event, add="+")

        if self._auto_theme_redraw:
            self._tkblend_theme_cb = lambda pal=None: self._on_theme_changed() if self.winfo_exists() else None
            add_theme_listener(self._tkblend_theme_cb)

        self.after_idle(lambda: self.redraw() if (self.winfo_exists() and not self._is_destroyed) else None)

    @property
    def photo(self) -> Optional[Any]:
        """Legacy photo accessor (returns None for native vector widgets)."""
        return self._photo

    @property
    def surface(self) -> Optional[Surface]:
        """Access the underlying native Blend2D Surface."""
        return self._surface

    @property
    def canvas_width(self) -> int:
        return self._surface.width if self._surface is not None else self._logical_w

    @property
    def canvas_height(self) -> int:
        return self._surface.height if self._surface is not None else self._logical_h

    @property
    def _canvas_width(self) -> int:
        return self.canvas_width

    @property
    def _canvas_height(self) -> int:
        return self.canvas_height

    def set_draw_callback(self, callback: Optional[Callable[[Surface], None]], redraw_now: bool = True) -> None:
        """Set or update the custom rendering callback function."""
        self._on_draw = callback
        if redraw_now:
            self.redraw()

    @contextmanager
    def render(self, auto_present: bool = True):
        """
        Context manager for custom rendering blocks.
        Automatically presents vector changes upon block exit if auto_present is True.
        """
        if self._surface is None or self._is_destroyed:
            raise RuntimeError("Cannot render on a destroyed BlendFrame")
        yield self._surface
        if auto_present and self._surface is not None:
            self._surface.present()

    def present(self) -> None:
        """Immediately blit the current Blend2D buffer to the native OS window."""
        if self._surface is not None and not self._is_destroyed and self.winfo_exists():
            self._surface.present()

    def redraw(self) -> None:
        """Execute the draw callback or subclass _redraw and present to screen."""
        if not self.winfo_exists() or self._is_destroyed:
            return
        if self._on_draw is not None and self._surface is not None:
            self._on_draw(self._surface)
            self._surface.present()
        elif hasattr(self, "_redraw") and callable(getattr(self, "_redraw")):
            self._redraw()
            if self._surface is not None:
                self._surface.present()
        elif hasattr(self, "_render") and callable(getattr(self, "_render")):
            self._render()
            if self._surface is not None:
                self._surface.present()
        elif self._surface is not None:
            self._surface.present()

    def _on_configure(self, event) -> None:
        """Handle window resize and reallocate Blend2D image surface if dimensions changed."""
        if event is not None:
            w = getattr(event, "widget", None)
            if w is not None and w != self and str(w) != str(self):
                return
        if event is not None and (event.width <= 1 or event.height <= 1):
            return
        if event is not None and (event.width != self._logical_w or event.height != self._logical_h):
            self._logical_w = event.width
            self._logical_h = event.height
            if self._surface is not None:
                self._surface.resize(self._logical_w, self._logical_h)
            self.redraw()

    def _on_theme_changed(self) -> None:
        """Handle theme change event."""
        if not self.winfo_exists() or self._is_destroyed:
            return
        bg_token = self._bg_color
        if bg_token in ("bg", "card_bg"):
            bg_token = "card_bg" if is_inside_card(self) else "bg"
        resolved_bg = resolve_theme_color(bg_token)
        if resolved_bg.startswith("#") and len(resolved_bg) == 9:
            resolved_bg = resolved_bg[:7]
        try:
            self.configure(background=resolved_bg)
        except Exception as e:
            logger.debug("Failed configuring frame background: %s", e)
        self.redraw()

    def _on_destroy_event(self, event=None) -> None:
        """Proactively release native surface hook and theme listeners upon destruction."""
        if event is not None:
            w = getattr(event, "widget", None)
            if w is not None and w != self and str(w) != str(self):
                return
        if self._is_destroyed:
            return
        self._is_destroyed = True
        self._on_draw = None

        cb = getattr(self, "_tkblend_theme_cb", None)
        if cb is not None:
            try:
                remove_theme_listener(cb)
            except Exception:
                pass

        if self._surface is not None:
            try:
                self._surface.close()
            except Exception:
                pass
            self._surface = None
        self._handle = None
