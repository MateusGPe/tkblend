"""
Native Blend2D Surface Decorator Mega-Widget for Tkinter.
Provides pure C++ double-buffered rounded cards, soft drop shadows,
hover and focus rings around standard Tk/TTK child widgets.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Union, Tuple, Sequence, Any, Callable

from tkblend._tkblend import (
    NativeDecorator as _NativeDecorator,
    Color as _NativeColor,
)
from tkblend.surface import ColorLike, parse_color
from tkblend.theme import get_theme, add_theme_listener, remove_theme_listener, Palette, resolve_ancestor_bg
from tkblend.utils.tcl_interp import extract_interp_address


class BlendDecorator(tk.Widget):
    """
    Surface-based Decorator Canvas that acts as a container for native Tk widgets.
    
    Renders soft drop shadows, rounded corners, borders, and focus rings using
    Blend2D vector primitives and Tk-exported double-buffered Pixmap presentation
    without any intermediate PhotoImage allocations.
    """
    _counter: int = 0

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 200,
        height: int = 45,
        rx: float = 8.0,
        ry: float = 8.0,
        radius: Optional[float] = None,
        bg_color: Optional[ColorLike] = None,
        hover_bg_color: Optional[ColorLike] = None,
        focus_bg_color: Optional[ColorLike] = None,
        parent_bg: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_hover_color: Optional[ColorLike] = None,
        border_focus_color: Optional[ColorLike] = None,
        border_width: float = 1.0,
        shadow_color: Optional[ColorLike] = None,
        shadow_blur: float = 8.0,
        shadow_spread: float = 0.0,
        shadow_offset_x: float = 0.0,
        shadow_offset_y: float = 2.0,
        shadow_enabled: bool = True,
        focus_ring_color: Optional[ColorLike] = None,
        focus_ring_width: float = 2.0,
        focus_ring_offset: float = 2.0,
        clip_child: bool = False,
        child_rx: Optional[float] = None,
        child_ry: Optional[float] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        if master is None:
            master = tk._default_root
            if master is None:
                master = tk.Tk()

        BlendDecorator._counter += 1
        widget_name = name or f"blend_decorator_{BlendDecorator._counter}"
        parent_path = getattr(master, "_w", ".")

        # Obtain Tcl_Interp address from Tkinter interpreter
        interp_addr = extract_interp_address(master)

        # Store requested inner card geometry
        self._card_width = int(width)
        self._card_height = int(height)

        # Instantiate the underlying C++ NativeDecorator
        self._native = _NativeDecorator(
            interp_addr,
            parent_path,
            widget_name,
            int(width),
            int(height),
        )

        # Initialize tkinter.Widget with the C++ created Tk_Window path
        tk.Widget.__init__(self, master, None, {"name": widget_name})

        # Save style overrides
        self._explicit_bg = bg_color is not None
        self._explicit_border = border_color is not None
        self._explicit_focus_ring = focus_ring_color is not None
        self._explicit_parent_bg = parent_bg is not None

        if radius is not None:
            rx = radius
            ry = radius

        # Resolve initial theme palette
        pal = get_theme()

        init_bg = parse_color(bg_color) if bg_color is not None else parse_color(pal.card_bg)
        init_parent_bg = parse_color(parent_bg) if parent_bg is not None else parse_color(resolve_ancestor_bg(master, pal))
        init_border = parse_color(border_color) if border_color is not None else parse_color(pal.card_border)
        init_focus_ring = parse_color(focus_ring_color) if focus_ring_color is not None else parse_color(pal.primary)

        init_hover_bg = parse_color(hover_bg_color) if hover_bg_color is not None else None
        init_focus_bg = parse_color(focus_bg_color) if focus_bg_color is not None else None
        init_border_hover = parse_color(border_hover_color) if border_hover_color is not None else None
        init_border_focus = parse_color(border_focus_color) if border_focus_color is not None else None
        init_shadow_color = parse_color(shadow_color) if shadow_color is not None else _NativeColor(0, 0, 0, 30)

        self._hover_bg_hex = (
            f"#{init_hover_bg.r:02x}{init_hover_bg.g:02x}{init_hover_bg.b:02x}"
            if init_hover_bg is not None else None
        )
        self._focus_bg_hex = (
            f"#{init_focus_bg.r:02x}{init_focus_bg.g:02x}{init_focus_bg.b:02x}"
            if init_focus_bg is not None else None
        )

        self._native.set_style(
            bg_color=init_bg,
            hover_bg_color=init_hover_bg,
            focus_bg_color=init_focus_bg,
            parent_bg=init_parent_bg,
            border_color=init_border,
            border_hover_color=init_border_hover,
            border_focus_color=init_border_focus,
            border_width=float(border_width),
            rx=float(rx),
            ry=float(ry),
            shadow_color=init_shadow_color,
            shadow_blur=float(shadow_blur),
            shadow_spread=float(shadow_spread),
            shadow_offset_x=float(shadow_offset_x),
            shadow_offset_y=float(shadow_offset_y),
            shadow_enabled=bool(shadow_enabled),
            focus_ring_color=init_focus_ring,
            focus_ring_width=float(focus_ring_width),
            focus_ring_offset=float(focus_ring_offset),
            clip_child=bool(clip_child),
            child_rx=float(child_rx) if child_rx is not None else None,
            child_ry=float(child_ry) if child_ry is not None else None,
        )

        self._child: Optional[tk.Widget] = None
        self._child_padding: Tuple[int, int, int, int] = (8, 6, 8, 6)
        self._match_bg: bool = True

        # Calculate outer geometry accounting for drop shadow and focus ring insets
        self._update_geometry_request()

        # Register dynamic theme listener and destruction cleanup
        self.bind("<Destroy>", self._on_destroy_event, add="+")
        self.bind("<Enter>", lambda e: self._on_hover_state_change(True), add="+")
        self.bind("<Leave>", lambda e: self._on_hover_state_change(False), add="+")
        add_theme_listener(self._on_theme_changed)

    def _update_geometry_request(self) -> None:
        """Update outer Tk window requested geometry to enclose card plus insets."""
        insets = self._native.get_insets()
        outer_w = int(self._card_width + insets[0] + insets[2])
        outer_h = int(self._card_height + insets[1] + insets[3])
        self._native.set_geometry_request(max(1, outer_w), max(1, outer_h))
        self._reposition_child()

    def _on_destroy_event(self, event=None) -> None:
        """Proactively release listeners and child hooks when destroyed."""
        if event is not None:
            w = getattr(event, "widget", None)
            if w is not None and w != self and str(w) != str(self):
                return
        try:
            remove_theme_listener(self._on_theme_changed)
        except Exception:
            pass
        self.detach()

    def redraw(self) -> None:
        """Request immediate or asynchronous redraw of the decorator."""
        self._native.request_redraw()

    def request_redraw(self) -> None:
        """Request redraw of the decorator."""
        self._native.request_redraw()

    def set_hovered(self, hovered: bool) -> None:
        """Explicitly set or simulate the hover state."""
        self._native.set_hovered(bool(hovered))
        self._sync_child_state_bg()

    def set_focused(self, focused: bool) -> None:
        """Explicitly set or simulate the focus state."""
        self._native.set_focused(bool(focused))
        self._sync_child_state_bg()

    def _on_hover_state_change(self, hovered: bool) -> None:
        self._sync_child_state_bg()

    def _sync_child_state_bg(self) -> None:
        """Ensure decorated child matches active hover/focus/normal background and class styles."""
        if self._child is None or not self._match_bg:
            return

        target_bg = None
        if self.is_focused and self._focus_bg_hex:
            target_bg = self._focus_bg_hex
        elif self.is_hovered and self._hover_bg_hex:
            target_bg = self._hover_bg_hex
        else:
            c = self._native.bg_color
            target_bg = f"#{c.r:02x}{c.g:02x}{c.b:02x}"

        if self.classes:
            try:
                from tkblend._tkblend import StyleEngine, PseudoState
                pseudo = 0
                if self.is_focused:
                    pseudo |= int(PseudoState.Focused)
                if self.is_hovered:
                    pseudo |= int(PseudoState.Hover)
                elem_tag = self._child.winfo_class().lower() if hasattr(self._child, "winfo_class") else ""
                cs = StyleEngine.resolve(elem_tag, self.class_name, pseudo)
                if cs.bg_color.a > 0 and not self._explicit_bg:
                    target_bg = f"#{cs.bg_color.r:02x}{cs.bg_color.g:02x}{cs.bg_color.b:02x}"
                if cs.fg_color.a > 0:
                    fg_hex = f"#{cs.fg_color.r:02x}{cs.fg_color.g:02x}{cs.fg_color.b:02x}"
                    try:
                        self._child.configure(fg=fg_hex)
                    except Exception:
                        try:
                            self._child.configure(foreground=fg_hex)
                        except Exception:
                            pass
            except Exception:
                pass

        try:
            self._child.configure(bg=target_bg)
        except Exception:
            try:
                self._child.configure(background=target_bg)
            except Exception:
                pass

    def _on_theme_changed(self, pal: Palette) -> None:
        """Update decorator styling when global theme changes."""
        try:
            if not self._explicit_bg:
                self._native.bg_color = parse_color(pal.card_bg)
            if not self._explicit_parent_bg:
                self._native.parent_bg = parse_color(resolve_ancestor_bg(self.master, pal))
            if not self._explicit_border:
                self._native.border_color = parse_color(pal.card_border)
            if not self._explicit_focus_ring:
                self._native.focus_ring_color = parse_color(pal.primary)
            self._native.request_redraw()

            if self._child is not None and self._match_bg:
                self._sync_child_state_bg()

                fg_hex = f"#{pal.fg.r:02x}{pal.fg.g:02x}{pal.fg.b:02x}" if hasattr(pal.fg, "r") else pal.fg
                try:
                    self._child.configure(fg=fg_hex)
                except Exception:
                    try:
                        self._child.configure(foreground=fg_hex)
                    except Exception:
                        pass
        except Exception:
            pass

    @property
    def bg_color(self) -> str:
        """Active inner card surface background color hex."""
        c = self._native.bg_color
        return f"#{c.r:02x}{c.g:02x}{c.b:02x}"

    @property
    def native(self) -> _NativeDecorator:
        """Underlying C++ NativeDecorator instance."""
        return self._native

    @property
    def child(self) -> Optional[tk.Widget]:
        """Currently decorated child widget."""
        return self._child

    @property
    def insets(self) -> Tuple[float, float, float, float]:
        """Current internal insets (left, top, right, bottom) preventing shadow/focus clipping."""
        return self._native.get_insets()

    @property
    def is_focused(self) -> bool:
        """True if the decorator or its child has input focus."""
        return self._native.is_focused

    @is_focused.setter
    def is_focused(self, val: bool) -> None:
        self.set_focused(bool(val))

    @property
    def is_hovered(self) -> bool:
        """True if the mouse cursor is over the decorator or child widget."""
        return self._native.is_hovered

    @is_hovered.setter
    def is_hovered(self, val: bool) -> None:
        self.set_hovered(bool(val))

    @property
    def clip_child(self) -> bool:
        """True if the embedded child Tk window is shaped/clipped to match rounded card corners."""
        return self._native.clip_child

    @clip_child.setter
    def clip_child(self, val: bool) -> None:
        self._native.clip_child = bool(val)

    @property
    def child_rx(self) -> Optional[float]:
        """Explicit horizontal corner radius for child window shaping (None = automatic)."""
        return self._native.child_rx

    @child_rx.setter
    def child_rx(self, val: Optional[float]) -> None:
        self._native.child_rx = float(val) if val is not None else None

    @property
    def child_ry(self) -> Optional[float]:
        """Explicit vertical corner radius for child window shaping (None = automatic)."""
        return self._native.child_ry

    @child_ry.setter
    def child_ry(self, val: Optional[float]) -> None:
        self._native.child_ry = float(val) if val is not None else None

    # CSS Class Management
    def add_class(self, name: str) -> BlendDecorator:
        """Add a CSS class and trigger auto-redraw and child styling sync."""
        self._native.add_class(str(name))
        self._sync_child_state_bg()
        return self

    def remove_class(self, name: str) -> BlendDecorator:
        """Remove a CSS class and trigger auto-redraw and child styling sync."""
        self._native.remove_class(str(name))
        self._sync_child_state_bg()
        return self

    def toggle_class(self, name: str) -> BlendDecorator:
        """Toggle a CSS class on the decorator."""
        self._native.toggle_class(str(name))
        self._sync_child_state_bg()
        return self

    def has_class(self, name: str) -> bool:
        """Return True if the decorator has the specified CSS class."""
        return self._native.has_class(str(name))

    @property
    def classes(self) -> list[str]:
        """List of active CSS classes."""
        return list(self._native.classes)

    @classes.setter
    def classes(self, val: Sequence[str]) -> None:
        self._native.classes = [str(x) for x in val]
        self._sync_child_state_bg()

    @property
    def class_name(self) -> str:
        """Space-separated string of active CSS classes."""
        return self._native.class_name

    @class_name.setter
    def class_name(self, val: str) -> None:
        self._native.class_name = str(val)
        self._sync_child_state_bg()

    # Dynamic Variable Management
    def set_var(self, key: str, value: Any) -> BlendDecorator:
        """Set a local scoped variable (color, scalar curve/dimension, or string) and trigger auto-redraw."""
        self._native.set_var(str(key), str(value))
        self._sync_child_state_bg()
        return self

    def get_var(self, key: str, default: Optional[str] = None) -> str:
        """Get the value of a scoped or global variable."""
        res = self._native.get_var(str(key))
        if not res and default is not None:
            return default
        return res

    def remove_var(self, key: str) -> BlendDecorator:
        """Remove a locally scoped variable override."""
        self._native.remove_var(str(key))
        self._sync_child_state_bg()
        return self

    def clear_vars(self) -> BlendDecorator:
        """Clear all locally scoped variable overrides."""
        self._native.clear_vars()
        self._sync_child_state_bg()
        return self

    @property
    def vars(self) -> dict[str, str]:
        """Dictionary of all local variable overrides."""
        return dict(self._native.get_vars())

    @vars.setter
    def vars(self, d: dict[str, Any]) -> None:
        self._native.clear_vars()
        for k, v in d.items():
            self._native.set_var(str(k), str(v))
        self._sync_child_state_bg()

    # DrawBatch Binding for Zero-Python Rendering
    def bind_batch(self, batch: Any) -> BlendDecorator:
        """Bind a C++ DrawBatch display list for zero-GIL, zero-Python rendering."""
        if hasattr(batch, "native"):
            batch = batch.native
        self._native.bind_batch(batch)
        return self

    def clear_batch(self) -> BlendDecorator:
        """Clear any bound DrawBatch and return to standard card rendering."""
        self._native.clear_batch()
        return self

    @property
    def has_batch(self) -> bool:
        """Return True if a C++ DrawBatch is actively bound."""
        return self._native.has_batch

    def _reposition_child(self) -> None:
        """Recalculate and place child widget based on active insets and padding."""
        if self._child is None:
            return

        insets = self._native.get_insets()
        pad = self._child_padding

        pl = int(insets[0] + pad[0])
        pt = int(insets[1] + pad[1])
        pr = int(insets[2] + pad[2])
        pb = int(insets[3] + pad[3])

        self._child.place(
            x=pl,
            y=pt,
            relwidth=1.0,
            relheight=1.0,
            width=-(pl + pr),
            height=-(pt + pb),
        )

    def decorate(
        self,
        child_widget: tk.Widget,
        padding: Union[int, float, Sequence[Union[int, float]]] = (8, 6, 8, 6),
        match_bg: bool = True,
        clip_child: Optional[bool] = None,
        child_rx: Optional[float] = None,
        child_ry: Optional[float] = None,
    ) -> tk.Widget:
        """
        Embed and passively monitor a child widget inside this decorator.
        
        Removes borders on inputs (Entry, Combobox, Text, etc.) and places
        the child with appropriate padding accounting for drop shadow insets.
        Optionally enables native OS-level window shaping on the child widget.
        """
        # Normalize padding to (left, top, right, bottom)
        if isinstance(padding, (int, float)):
            pad = (int(padding), int(padding), int(padding), int(padding))
        elif len(padding) == 2:
            pad = (int(padding[0]), int(padding[1]), int(padding[0]), int(padding[1]))
        elif len(padding) >= 4:
            pad = (int(padding[0]), int(padding[1]), int(padding[2]), int(padding[3]))
        else:
            pad = (8, 6, 8, 6)

        self._child_padding = pad
        self._child = child_widget
        self._match_bg = match_bg

        if clip_child is not None:
            self._native.clip_child = bool(clip_child)
        if child_rx is not None:
            self._native.child_rx = float(child_rx)
        if child_ry is not None:
            self._native.child_ry = float(child_ry)

        # Configure child widget to be borderless if applicable
        self._apply_borderless_style(child_widget)

        # Match child background and foreground if requested
        if match_bg:
            self._sync_child_state_bg()

        pal = get_theme()
        fg_hex = f"#{pal.fg.r:02x}{pal.fg.g:02x}{pal.fg.b:02x}" if hasattr(pal.fg, "r") else pal.fg
        try:
            child_widget.configure(fg=fg_hex)
        except Exception:
            try:
                child_widget.configure(foreground=fg_hex)
            except Exception:
                pass

        # Calculate placement inside shadow insets
        self._reposition_child()

        # Attach child in C++ native event monitoring
        child_path = getattr(child_widget, "_w", "")
        if child_path:
            self._native.attach_child(child_path)

        # Hook focus and hover on child to sync bg color in Python
        child_widget.bind("<FocusIn>", lambda e: self._sync_child_state_bg(), add="+")
        child_widget.bind("<FocusOut>", lambda e: self._sync_child_state_bg(), add="+")
        child_widget.bind("<Enter>", lambda e: self._sync_child_state_bg(), add="+")
        child_widget.bind("<Leave>", lambda e: self._sync_child_state_bg(), add="+")

        return child_widget

    def _apply_borderless_style(self, widget: tk.Widget) -> None:
        """Remove ugly default Tk bevels/borders from nested widgets."""
        if isinstance(widget, (tk.Entry, ttk.Entry, tk.Text, tk.Spinbox)):
            try:
                widget.configure(relief="flat", bd=0, highlightthickness=0)
            except Exception:
                pass
        else:
            for opt in ({"relief": "flat", "bd": 0, "highlightthickness": 0}, {"relief": "flat", "borderwidth": 0}):
                try:
                    widget.configure(**opt)
                    break
                except Exception:
                    pass

    def detach(self) -> None:
        """Detach current child widget and stop event monitoring."""
        self._native.detach_child()
        self._child = None

    def configure(self, cnf=None, **kwargs):
        """Update decorator styles or widget options."""
        if cnf is not None:
            kwargs.update(cnf)

        style_args = {}
        if "bg_color" in kwargs:
            self._explicit_bg = True
            c = parse_color(kwargs.pop("bg_color"))
            style_args["bg_color"] = c
        if "hover_bg_color" in kwargs:
            val = kwargs.pop("hover_bg_color")
            if val is not None:
                c = parse_color(val)
                style_args["hover_bg_color"] = c
                self._hover_bg_hex = f"#{c.r:02x}{c.g:02x}{c.b:02x}"
            else:
                style_args["hover_bg_color"] = None
                self._hover_bg_hex = None
        if "focus_bg_color" in kwargs:
            val = kwargs.pop("focus_bg_color")
            if val is not None:
                c = parse_color(val)
                style_args["focus_bg_color"] = c
                self._focus_bg_hex = f"#{c.r:02x}{c.g:02x}{c.b:02x}"
            else:
                style_args["focus_bg_color"] = None
                self._focus_bg_hex = None
        if "parent_bg" in kwargs:
            self._explicit_parent_bg = True
            style_args["parent_bg"] = parse_color(kwargs.pop("parent_bg"))
        if "border_color" in kwargs:
            self._explicit_border = True
            style_args["border_color"] = parse_color(kwargs.pop("border_color"))
        if "border_hover_color" in kwargs:
            val = kwargs.pop("border_hover_color")
            style_args["border_hover_color"] = parse_color(val) if val is not None else None
        if "border_focus_color" in kwargs:
            val = kwargs.pop("border_focus_color")
            style_args["border_focus_color"] = parse_color(val) if val is not None else None
        if "border_width" in kwargs:
            style_args["border_width"] = float(kwargs.pop("border_width"))
        if "radius" in kwargs:
            r = float(kwargs.pop("radius"))
            style_args["rx"] = r
            style_args["ry"] = r
        if "rx" in kwargs:
            style_args["rx"] = float(kwargs.pop("rx"))
        if "ry" in kwargs:
            style_args["ry"] = float(kwargs.pop("ry"))
        if "shadow_color" in kwargs:
            style_args["shadow_color"] = parse_color(kwargs.pop("shadow_color"))
        if "shadow_blur" in kwargs:
            style_args["shadow_blur"] = float(kwargs.pop("shadow_blur"))
        if "shadow_spread" in kwargs:
            style_args["shadow_spread"] = float(kwargs.pop("shadow_spread"))
        if "shadow_offset_x" in kwargs:
            style_args["shadow_offset_x"] = float(kwargs.pop("shadow_offset_x"))
        if "shadow_offset_y" in kwargs:
            style_args["shadow_offset_y"] = float(kwargs.pop("shadow_offset_y"))
        if "shadow_enabled" in kwargs:
            style_args["shadow_enabled"] = bool(kwargs.pop("shadow_enabled"))
        if "focus_ring_color" in kwargs:
            self._explicit_focus_ring = True
            style_args["focus_ring_color"] = parse_color(kwargs.pop("focus_ring_color"))
        if "focus_ring_width" in kwargs:
            style_args["focus_ring_width"] = float(kwargs.pop("focus_ring_width"))
        if "focus_ring_offset" in kwargs:
            style_args["focus_ring_offset"] = float(kwargs.pop("focus_ring_offset"))
        if "clip_child" in kwargs:
            style_args["clip_child"] = bool(kwargs.pop("clip_child"))
        if "child_rx" in kwargs:
            val = kwargs.pop("child_rx")
            style_args["child_rx"] = float(val) if val is not None else None
        if "child_ry" in kwargs:
            val = kwargs.pop("child_ry")
            style_args["child_ry"] = float(val) if val is not None else None

        if "width" in kwargs:
            self._card_width = int(kwargs.pop("width"))
        if "height" in kwargs:
            self._card_height = int(kwargs.pop("height"))

        if style_args:
            self._native.set_style(**style_args)

        self._update_geometry_request()
        self._sync_child_state_bg()

        if kwargs:
            try:
                return super().configure(**kwargs)
            except Exception:
                pass
        return None

    config = configure

    def destroy(self) -> None:
        """Safely clean up listeners and window resources."""
        self._on_destroy_event()
        super().destroy()
