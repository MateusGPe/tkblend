"""
Utility modules for tkblend.
"""

from tkblend.utils.window_shape import apply_round_rect_shape, clear_window_shape, is_window_shaping_supported
from tkblend.utils.tcl_interp import extract_interp_address

__all__ = [
    "apply_round_rect_shape",
    "clear_window_shape",
    "is_window_shaping_supported",
    "extract_interp_address",
]
