"""
OS-level window region shaping and clipping for Tkinter widgets.

Delegates directly to the native C++ library (_tkblend) to clip Tkinter child windows
(such as container body frames) to rounded rectangle shapes across Linux (X11 / XShape),
Windows (GDI / User32), and macOS (Cocoa NSView).
"""

from __future__ import annotations
import logging
import tkinter as tk

try:
    from tkblend import _tkblend  # type: ignore
except Exception:
    _tkblend = None

logger = logging.getLogger(__name__)


def is_window_shaping_supported() -> bool:
    """Return True if the current operating system and windowing environment support window shaping."""
    if _tkblend is not None and hasattr(_tkblend, "is_window_shaping_supported"):
        try:
            return bool(_tkblend.is_window_shaping_supported())
        except Exception as e:
            logger.debug("Error checking window shaping support: %s", e)
    return False


def apply_round_rect_shape(
    widget: tk.Misc,
    width: int,
    height: int,
    rx: float,
    ry: float,
) -> bool:
    """
    Clip a Tkinter widget's OS window region to a rounded rectangle via native C++ library.

    Args:
        widget: The Tkinter widget whose native window will be shaped.
        width: Pixel width of the shaped region.
        height: Pixel height of the shaped region.
        rx: Horizontal corner radius in pixels.
        ry: Vertical corner radius in pixels.

    Returns:
        True if the shape mask was successfully applied, False otherwise.
    """
    if width <= 0 or height <= 0 or rx <= 0 or ry <= 0:
        return clear_window_shape(widget)

    try:
        if not widget.winfo_exists():
            return False

        wid = widget.winfo_id()
        if not wid:
            return False

        if _tkblend is not None and hasattr(_tkblend, "apply_round_rect_shape"):
            return bool(_tkblend.apply_round_rect_shape(wid, int(width), int(height), float(rx), float(ry)))

        return False
    except Exception as e:
        logger.debug("Failed applying round rect shape to widget %s: %s", widget, e)
        return False


def clear_window_shape(widget: tk.Misc) -> bool:
    """
    Reset the window region shaping to default rectangle via native C++ library.
    """
    try:
        if not widget.winfo_exists():
            return False

        wid = widget.winfo_id()
        if not wid:
            return False

        if _tkblend is not None and hasattr(_tkblend, "clear_window_shape"):
            return bool(_tkblend.clear_window_shape(wid))

        return False
    except Exception as e:
        logger.debug("Failed clearing window shape on widget %s: %s", widget, e)
        return False
