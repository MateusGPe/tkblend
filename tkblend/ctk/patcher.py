"""
CustomTkinter Blend2D Patcher.
Dynamically hooks TkBlendDrawEngine and TkBlendCanvas into CustomTkinter runtime.
"""

from __future__ import annotations
import sys
from typing import Dict, Any, Optional

from tkblend.ctk.draw_engine import TkBlendDrawEngine
from tkblend.ctk.canvas import TkBlendCanvas

_is_patched: bool = False
_originals: Dict[str, Any] = {}

# All widget modules in CustomTkinter that bind DrawEngine and CTkCanvas
_CTK_MODULES = [
    "customtkinter.windows.widgets.core_rendering",
    "customtkinter.windows.widgets.core_rendering.draw_engine",
    "customtkinter.windows.widgets.core_rendering.ctk_canvas",
    "customtkinter.windows.widgets.core_widget_classes.dropdown_menu",
    "customtkinter.windows.widgets.ctk_button",
    "customtkinter.windows.widgets.ctk_checkbox",
    "customtkinter.windows.widgets.ctk_combobox",
    "customtkinter.windows.widgets.ctk_entry",
    "customtkinter.windows.widgets.ctk_frame",
    "customtkinter.windows.widgets.ctk_label",
    "customtkinter.windows.widgets.ctk_optionmenu",
    "customtkinter.windows.widgets.ctk_progressbar",
    "customtkinter.windows.widgets.ctk_radiobutton",
    "customtkinter.windows.widgets.ctk_scrollbar",
    "customtkinter.windows.widgets.ctk_scrollable_frame",
    "customtkinter.windows.widgets.ctk_segmented_button",
    "customtkinter.windows.widgets.ctk_slider",
    "customtkinter.windows.widgets.ctk_switch",
    "customtkinter.windows.widgets.ctk_tabview",
    "customtkinter.windows.widgets.ctk_textbox",
]


def patch(enable_shadows: bool = False) -> None:
    """
    Patch CustomTkinter globally to use Blend2D vector surface rendering.
    
    Args:
        enable_shadows: If True, renders subtle Blend2D soft drop shadows behind buttons and frames.
    """
    global _is_patched, _originals

    TkBlendDrawEngine.enable_shadows_globally = enable_shadows

    import customtkinter
    import customtkinter.windows.widgets.core_rendering as core_rendering
    import customtkinter.windows.widgets.core_rendering.draw_engine as draw_engine_mod
    import customtkinter.windows.widgets.core_rendering.ctk_canvas as canvas_mod

    if not _originals:
        _originals["DrawEngine"] = draw_engine_mod.DrawEngine
        _originals["CTkCanvas"] = canvas_mod.CTkCanvas

    # Save original references in all loaded widget modules and patch them
    for mod_name in _CTK_MODULES:
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
            if hasattr(mod, "DrawEngine"):
                _originals[f"{mod_name}.DrawEngine"] = getattr(mod, "DrawEngine")
                setattr(mod, "DrawEngine", TkBlendDrawEngine)
            if hasattr(mod, "CTkCanvas"):
                _originals[f"{mod_name}.CTkCanvas"] = getattr(mod, "CTkCanvas")
                setattr(mod, "CTkCanvas", TkBlendCanvas)

    # Patch core rendering package
    core_rendering.DrawEngine = TkBlendDrawEngine
    core_rendering.CTkCanvas = TkBlendCanvas
    draw_engine_mod.DrawEngine = TkBlendDrawEngine
    canvas_mod.CTkCanvas = TkBlendCanvas

    # Patch top-level customtkinter namespace if exposed
    if hasattr(customtkinter, "DrawEngine"):
        setattr(customtkinter, "DrawEngine", TkBlendDrawEngine)
    if hasattr(customtkinter, "CTkCanvas"):
        setattr(customtkinter, "CTkCanvas", TkBlendCanvas)

    _is_patched = True


def unpatch() -> None:
    """Restore CustomTkinter's original Tkinter Canvas / font-based rendering engine."""
    global _is_patched, _originals
    if not _is_patched or not _originals:
        return

    import customtkinter
    import customtkinter.windows.widgets.core_rendering as core_rendering
    import customtkinter.windows.widgets.core_rendering.draw_engine as draw_engine_mod
    import customtkinter.windows.widgets.core_rendering.ctk_canvas as canvas_mod

    orig_engine = _originals.get("DrawEngine", draw_engine_mod.DrawEngine)
    orig_canvas = _originals.get("CTkCanvas", canvas_mod.CTkCanvas)

    for mod_name in _CTK_MODULES:
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
            if hasattr(mod, "DrawEngine"):
                setattr(mod, "DrawEngine", orig_engine)
            if hasattr(mod, "CTkCanvas"):
                setattr(mod, "CTkCanvas", orig_canvas)

    core_rendering.DrawEngine = orig_engine
    core_rendering.CTkCanvas = orig_canvas
    draw_engine_mod.DrawEngine = orig_engine
    canvas_mod.CTkCanvas = orig_canvas

    if hasattr(customtkinter, "DrawEngine"):
        setattr(customtkinter, "DrawEngine", orig_engine)
    if hasattr(customtkinter, "CTkCanvas"):
        setattr(customtkinter, "CTkCanvas", orig_canvas)

    _is_patched = False


def is_patched() -> bool:
    """Return whether CustomTkinter is currently patched with Blend2D engine."""
    return _is_patched
