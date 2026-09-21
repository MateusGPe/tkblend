"""
tkblend - High-performance Blend2D vector graphics addon for ttkbootstrap and Tkinter.
"""

from tkblend._tkblend import (  # type: ignore
    Color,
    Gradient,
    load_font_face,
    COMP_OP_SRC_OVER,
    COMP_OP_SRC_COPY,
    COMP_OP_SRC_IN,
    COMP_OP_SRC_OUT,
    COMP_OP_SRC_ATOP,
    COMP_OP_DST_OVER,
    COMP_OP_DST_IN,
    COMP_OP_DST_OUT,
    COMP_OP_DST_ATOP,
    COMP_OP_XOR,
    COMP_OP_CLEAR,
    COMP_OP_PLUS,
    COMP_OP_MULTIPLY,
    COMP_OP_SCREEN,
    COMP_OP_OVERLAY,
    COMP_OP_DARKEN,
    COMP_OP_LIGHTEN,
    EXTEND_PAD,
    EXTEND_REPEAT,
    EXTEND_REFLECT,
)

from tkblend.surface import (
    Surface,
    LinearGradient,
    RadialGradient,
    Path,
    parse_color,
    ColorLike,
    GradientLike,
)

from tkblend.canvas import BlendCanvas

from tkblend.theme import (
    resolve_theme_color,
    get_theme_colors,
    get_active_theme_name,
    is_ttkbootstrap_installed,
    bind_theme_changed,
)

# Friendly aliases
resolve_color = resolve_theme_color
get_theme_color = resolve_theme_color
is_ttkbootstrap_active = is_ttkbootstrap_installed

__version__ = "0.2.0"
__all__ = [
    # Core Graphics
    "Surface",
    "BlendCanvas",
    "LinearGradient",
    "RadialGradient",
    "Path",
    "Color",
    "Gradient",
    "parse_color",
    "ColorLike",
    "GradientLike",
    # Theme & ttkbootstrap bridge
    "resolve_theme_color",
    "resolve_color",
    "get_theme_color",
    "get_theme_colors",
    "get_active_theme_name",
    "is_ttkbootstrap_installed",
    "is_ttkbootstrap_active",
    "bind_theme_changed",
    # Blend2D font & native composition operators
    "load_font_face",
    "COMP_OP_SRC_OVER",
    "COMP_OP_SRC_COPY",
    "COMP_OP_SRC_IN",
    "COMP_OP_SRC_OUT",
    "COMP_OP_SRC_ATOP",
    "COMP_OP_DST_OVER",
    "COMP_OP_DST_IN",
    "COMP_OP_DST_OUT",
    "COMP_OP_DST_ATOP",
    "COMP_OP_XOR",
    "COMP_OP_CLEAR",
    "COMP_OP_PLUS",
    "COMP_OP_MULTIPLY",
    "COMP_OP_SCREEN",
    "COMP_OP_OVERLAY",
    "COMP_OP_DARKEN",
    "COMP_OP_LIGHTEN",
    "EXTEND_PAD",
    "EXTEND_REPEAT",
    "EXTEND_REFLECT",
]
