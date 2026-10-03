"""
Tcl/Tk Interpreter extraction and interoperability utilities for tkblend.
Supports Tk 8.6, 9.0+, CPython, and PyPy runtimes.
"""

from typing import Any, Union


def extract_interp_address(widget_or_tk: Any) -> int:
    """Safely extracts the 64-bit memory address of the underlying Tcl_Interp pointer.

    Supports CPython Tkinter (`interpaddr()`), PyPy CFFI (`interp`), and direct integer handles.

    Parameters:
        widget_or_tk: A Tkinter widget, PhotoImage, or Tk root instance.

    Returns:
        int: The 64-bit pointer address of the Tcl_Interp.

    Raises:
        ValueError: If a valid non-zero pointer address cannot be resolved.
    """
    if widget_or_tk is None:
        raise ValueError("Cannot extract Tcl interpreter address from None")

    if isinstance(widget_or_tk, int):
        if widget_or_tk == 0:
            raise ValueError("Invalid NULL Tcl_Interp pointer address (0)")
        return widget_or_tk

    # Resolve the underlying tk engine object
    tk_engine = getattr(widget_or_tk, "tk", widget_or_tk)

    # 1. CPython Tkinter: interpaddr() method
    if hasattr(tk_engine, "interpaddr"):
        try:
            addr = int(tk_engine.interpaddr())
            if addr != 0:
                return addr
        except (TypeError, ValueError):
            pass

    # 2. PyPy / CFFI: inspect tk_engine.interp
    if hasattr(tk_engine, "interp"):
        interp_attr = getattr(tk_engine, "interp")
        if isinstance(interp_attr, int) and interp_attr != 0:
            return interp_attr
        try:
            import cffi  # type: ignore

            ffi = cffi.FFI()
            addr = int(ffi.cast("uintptr_t", interp_attr))
            if addr != 0:
                return addr
        except Exception:
            pass

    # 3. Fallback: Check for private _interp or id
    if hasattr(tk_engine, "_interp"):
        _interp = getattr(tk_engine, "_interp")
        if isinstance(_interp, int) and _interp != 0:
            return _interp

    raise ValueError(
        f"Supplied object ({type(widget_or_tk).__name__}) does not expose a valid Tcl_Interp pointer address."
    )
