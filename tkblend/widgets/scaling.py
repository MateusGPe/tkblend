"""
High-DPI scaling, monitor awareness, and logical-to-physical coordinate conversion
for tkblend widgets and Blend2D rendering buffers.

Harvested and adapted from CustomTkinter ScalingTracker and ttkbootstrap Scaling primitives.
"""

from __future__ import annotations
import sys
import tkinter as tk
from math import floor, ceil
from typing import Union, List, Tuple, Callable, Dict, Optional, Any


def _round_half_away(value: float) -> int:
    """Round halves away from zero without Banker's rounding bias."""
    if value >= 0:
        return floor(value + 0.5)
    return ceil(value - 0.5)


class ScalingTracker:
    """
    Manages process-level High-DPI awareness, Tk scaling factor tracking,
    and logical-to-physical pixel conversion for 4K / Retina displays.
    """

    _dpi_awareness_initialized: bool = False
    _deactivate_automatic_dpi: bool = False
    _user_widget_scaling: float = 1.0
    _user_window_scaling: float = 1.0
    _window_dpi_dict: Dict[tk.Misc, float] = {}

    @classmethod
    def activate_high_dpi_awareness(cls) -> None:
        """
        Enable Per-Monitor High-DPI awareness on Windows.
        On macOS (Darwin), DPI is handled automatically by the Cocoa backend.
        On Linux / X11, Tk scaling factor is utilized.
        """
        if cls._dpi_awareness_initialized or cls._deactivate_automatic_dpi:
            return

        if sys.platform.startswith("win"):
            try:
                import ctypes
                # PROCESS_PER_MONITOR_DPI_AWARE = 2
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    import ctypes
                    # PROCESS_SYSTEM_DPI_AWARE = 1 fallback
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

        cls._dpi_awareness_initialized = True

    @classmethod
    def get_scaling_factor(cls, widget_or_window: Optional[tk.Misc] = None) -> float:
        """
        Calculate effective display scaling factor (1.0 = standard 96 DPI).
        """
        if cls._deactivate_automatic_dpi or widget_or_window is None:
            return cls._user_widget_scaling

        try:
            # Tk windowing system check
            ws = str(widget_or_window.tk.call("tk", "windowingsystem"))
            baseline = 1.0 if (ws == "aqua" and tk.TkVersion < 8.7) else (4.0 / 3.0)
            raw_scaling = float(widget_or_window.tk.call("tk", "scaling"))
            factor = raw_scaling / baseline
            quarter = round(factor * 4.0) / 4.0
            if abs(factor - quarter) <= 0.005:
                factor = quarter
            return max(0.5, factor * cls._user_widget_scaling)
        except Exception:
            return max(0.5, cls._user_widget_scaling)

    @classmethod
    def scale(cls, value: Union[int, float, List, Tuple], widget: Optional[tk.Misc] = None) -> Any:
        """
        Convert logical UI units to physical pixel values for Blend2D surfaces.
        """
        factor = cls.get_scaling_factor(widget)
        if factor == 1.0:
            if isinstance(value, (int, float)):
                return int(value)
            return value

        if isinstance(value, (int, float)):
            if value == 0:
                return 0
            return _round_half_away(float(value) * factor)
        elif isinstance(value, (tuple, list)):
            return [cls.scale(v, widget) for v in value]
        return value

    @classmethod
    def set_widget_scaling(cls, factor: float) -> None:
        """Set manual user scaling factor multiplier (e.g. 1.25 for 125%)."""
        cls._user_widget_scaling = max(0.4, float(factor))


# Auto-activate DPI awareness early
ScalingTracker.activate_high_dpi_awareness()
