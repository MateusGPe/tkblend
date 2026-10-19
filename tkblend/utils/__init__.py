"""
Utility modules for tkblend.
"""

from tkblend.utils.window_shape import apply_round_rect_shape, clear_window_shape, is_window_shaping_supported
from tkblend.utils.tcl_interp import extract_interp_address
from tkblend.utils.screen import get_monitor_work_area

__all__ = [
    "apply_round_rect_shape",
    "clear_window_shape",
    "is_window_shaping_supported",
    "extract_interp_address",
    "get_monitor_work_area",
]

