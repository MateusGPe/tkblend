from __future__ import annotations

import sys
import tkinter as tk
from typing import Optional, Tuple



if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        _user32 = ctypes.windll.user32
        _user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
        _user32.MonitorFromPoint.restype = wintypes.HMONITOR

        _user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        _user32.MonitorFromWindow.restype = wintypes.HMONITOR

        _user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
        _user32.GetMonitorInfoW.restype = wintypes.BOOL
    except Exception:
        _user32 = None
        MONITORINFO = None
else:
    _user32 = None
    MONITORINFO = None


def get_monitor_work_area(
    x: int,
    y: int,
    widget: Optional[tk.Misc] = None,
) -> Tuple[int, int, int, int]:
    """
    Returns the usable work area bounding box (left, top, right, bottom)
    of the monitor containing the point (x, y).

    On Windows, uses Win32 User32 APIs (MonitorFromPoint + GetMonitorInfoW)
    to accurately retrieve the per-monitor work area (excluding taskbars and docked bars).
    On other platforms or on failure, falls back to Tk virtual root or screen bounds.
    """
    if sys.platform == "win32" and _user32 is not None:
        try:
            import ctypes
            from ctypes import wintypes

            MONITOR_DEFAULTTONEAREST = 2
            pt = wintypes.POINT(int(x), int(y))
            hmonitor = _user32.MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST)

            if not hmonitor and widget is not None:
                try:
                    hwnd = widget.winfo_id()
                    hmonitor = _user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
                except Exception:
                    hmonitor = None

            if hmonitor:
                info = MONITORINFO()
                info.cbSize = ctypes.sizeof(MONITORINFO)
                if _user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                    left = int(info.rcWork.left)
                    top = int(info.rcWork.top)
                    right = int(info.rcWork.right)
                    bottom = int(info.rcWork.bottom)
                    if right > left and bottom > top:
                        return (left, top, right, bottom)
        except Exception:
            pass

    # Cross-platform / fallback behavior
    target_widget = widget or getattr(tk, "_default_root", None)
    if target_widget is not None:
        try:
            vx = target_widget.winfo_vrootx()
            vy = target_widget.winfo_vrooty()
            vw = target_widget.winfo_vrootwidth()
            vh = target_widget.winfo_vrootheight()
            if vw > 0 and vh > 0:
                return (vx, vy, vx + vw, vy + vh)
        except Exception:
            pass

        try:
            sw = target_widget.winfo_screenwidth()
            sh = target_widget.winfo_screenheight()
            if sw > 0 and sh > 0:
                return (0, 0, sw, sh)
        except Exception:
            pass

    return (0, 0, 1024, 768)

