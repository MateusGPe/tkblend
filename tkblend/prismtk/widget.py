"""
PrismWidget and PrismApp implementations for tkblend.prismtk.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Union, Dict, Any, Callable, List

from tkblend.surface import Surface
from tkblend.theme import bind_theme_changed, get_theme
from tkblend.widgets.base import ScalingTracker
from tkblend.prismtk.dom import Node
from tkblend.prismtk.parser import parse_template
from tkblend.prismtk.css import StyleSheet, compute_node_style
from tkblend.prismtk.layout import compute_layout
from tkblend.prismtk.render import render_node
from tkblend.prismtk.events import EventManager
from tkblend.prismtk.state import ReactiveState


class PrismWidget(tk.Label):
    """
    Declarative, CSS-styled, state-driven vector widget powered by Blend2D.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        template: Optional[Union[str, Node]] = None,
        css: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
        width: int = 300,
        height: int = 200,
        **kwargs,
    ):
        self._logical_w = max(1, int(width))
        self._logical_h = max(1, int(height))
        self._scale = ScalingTracker.get_scaling_factor(master)
        self._widget_w = max(1, int(self._logical_w * self._scale))
        self._widget_h = max(1, int(self._logical_h * self._scale))

        # Backing PhotoImage and Blend2D Surface
        self._photo = tk.PhotoImage(master=master, width=self._widget_w, height=self._widget_h)
        self._surface = Surface(self._widget_w, self._widget_h)

        super().__init__(
            master,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            **kwargs,
        )

        # Parse Template & DOM
        if isinstance(template, Node):
            self.root_node = template
        elif isinstance(template, str) and template.strip():
            self.root_node = parse_template(template)
        else:
            self.root_node = Node("box")

        # Parse CSS Stylesheets
        self.stylesheets: List[StyleSheet] = []
        if css:
            self.stylesheets.append(StyleSheet(css))

        # Reactive State Store
        self.state = ReactiveState(state or {})
        self.state.add_listener(self._on_state_changed)

        # Event & Interaction Manager
        self.events = EventManager(self.root_node, self.request_repaint)

        # Bind Tkinter Events
        self.bind("<Configure>", self._on_configure)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

        # Auto-theming
        bind_theme_changed(self, self._on_theme_changed)

        self.after_idle(self.request_repaint)

    def load_template(self, template_str: str) -> None:
        self.root_node = parse_template(template_str)
        self.events.root_node = self.root_node
        self.request_repaint()

    def load_style(self, css_str: str) -> None:
        self.stylesheets.append(StyleSheet(css_str))
        self.request_repaint()

    def action(self, name: str) -> Callable[[Callable], Callable]:
        """Decorator for registering action handlers: @widget.action('on_click')"""
        def decorator(fn: Callable[[], None]) -> Callable[[], None]:
            self.events.register_action(name, fn)
            return fn
        return decorator

    def register_action(self, name: str, callback: Callable[[], None]) -> None:
        self.events.register_action(name, callback)

    def _on_state_changed(self, key: str, value: Any) -> None:
        self.request_repaint()

    def _on_motion(self, event) -> None:
        # Logical coordinates
        lx = event.x / self._scale
        ly = event.y / self._scale
        self.events.on_mouse_move(lx, ly)

    def _on_leave(self, event) -> None:
        self.events.on_mouse_leave()

    def _on_press(self, event) -> None:
        lx = event.x / self._scale
        ly = event.y / self._scale
        self.events.on_mouse_press(lx, ly)

    def _on_release(self, event) -> None:
        lx = event.x / self._scale
        ly = event.y / self._scale
        self.events.on_mouse_release(lx, ly)

    def _on_configure(self, event) -> None:
        if event.width <= 1 or event.height <= 1:
            return
        if self._surface is None or self._photo is None:
            return

        self._widget_w = event.width
        self._widget_h = event.height
        self._logical_w = self._widget_w / self._scale
        self._logical_h = self._widget_h / self._scale

        self._photo.configure(width=self._widget_w, height=self._widget_h)
        self._surface.resize(self._widget_w, self._widget_h)
        self.request_repaint()

    def _on_theme_changed(self) -> None:
        self.request_repaint()

    def request_repaint(self) -> None:
        """Performs style resolution, flexbox layout, Blend2D rendering, and zero-copy blit."""
        if not self.winfo_exists() or self._surface is None or self._photo is None:
            return

        # 1. Compute Styles for all nodes
        self._resolve_styles(self.root_node)

        # 2. Compute Flexbox & Box Model Layout
        compute_layout(self.root_node, self._logical_w, self._logical_h, 0.0, 0.0)

        # 3. Clear Surface with transparent or parent background
        self._surface.clear("#00000000")

        # 4. Render Scene Graph
        render_node(self._surface, self.root_node, self.state, self._scale)

        # 5. Zero-Copy Blit to Tkinter PhotoImage
        self._surface.blit(self._photo)

    def _resolve_styles(self, node: Node) -> None:
        compute_node_style(node, self.stylesheets)
        for child in node.children:
            self._resolve_styles(child)


class App:
    """
    Top-level standalone application runner for tkblend.prismtk.
    """

    def __init__(
        self,
        title: str = "PrismTK App",
        width: int = 500,
        height: int = 400,
        template: Optional[str] = None,
        css: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
    ):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")

        self.widget = PrismWidget(
            self.root,
            template=template,
            css=css,
            state=state,
            width=width,
            height=height,
        )
        self.widget.pack(fill="both", expand=True)

    @property
    def state(self) -> ReactiveState:
        return self.widget.state

    @state.setter
    def state(self, new_state: Dict[str, Any]) -> None:
        self.widget.state.update(new_state)

    def action(self, name: str) -> Callable[[Callable], Callable]:
        return self.widget.action(name)

    def load_template(self, template_str: str) -> None:
        self.widget.load_template(template_str)

    def load_style(self, css_str: str) -> None:
        self.widget.load_style(css_str)

    def run(self) -> None:
        self.root.mainloop()
