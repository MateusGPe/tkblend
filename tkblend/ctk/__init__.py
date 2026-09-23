"""
tkblend.ctk - Blend2D Vector Rendering Bridge for CustomTkinter.

Enables crisp, high-performance vector anti-aliasing for CustomTkinter widgets
with zero TTK dependencies and zero upstream CustomTkinter code modifications.

Usage options:

Option 1 (Explicit patch for existing CustomTkinter apps):
    import customtkinter as ctk
    import tkblend.ctk
    tkblend.ctk.patch()

Option 2 (Direct drop-in replacement module):
    import tkblend.ctk as ctk
    app = ctk.CTk()
    btn = ctk.CTkButton(app, text="Crisp Blend2D Button")
    btn.pack(padx=20, pady=20)
    app.mainloop()
"""

from __future__ import annotations
import logging
import sys
from tkblend.ctk.draw_engine import TkBlendDrawEngine
from tkblend.ctk.canvas import TkBlendCanvas
from tkblend.ctk.patcher import patch, unpatch, is_patched

logger = logging.getLogger(__name__)

# Auto-patch CustomTkinter when tkblend.ctk is imported as drop-in namespace
try:
    import customtkinter
    patch()
except ImportError as e:
    logger.debug("customtkinter is not installed in the environment: %s", e)
    customtkinter = None


_ALIASES = {
    "CTkCheckbox": "CTkCheckBox",
    "CTkRadiobutton": "CTkRadioButton",
    "CTkProgressbar": "CTkProgressBar",
    "CTkCombobox": "CTkComboBox",
}


def __getattr__(name: str):
    """Dynamically delegate any attribute or widget class lookup to customtkinter."""
    if customtkinter is not None:
        if hasattr(customtkinter, name):
            return getattr(customtkinter, name)
        if name in _ALIASES and hasattr(customtkinter, _ALIASES[name]):
            return getattr(customtkinter, _ALIASES[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "TkBlendDrawEngine",
    "TkBlendCanvas",
    "patch",
    "unpatch",
    "is_patched",
]
