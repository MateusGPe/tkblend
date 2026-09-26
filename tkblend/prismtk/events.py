"""
Hit-Testing, Event Routing, and Autonomous Interaction Manager for tkblend.prismtk.
"""

from __future__ import annotations
from typing import Optional, List, Callable, Dict, Any
from tkblend.prismtk.dom import Node


def hit_test(node: Node, x: float, y: float) -> Optional[Node]:
    """
    Finds the deepest child node containing the point (x, y).
    """
    # Check if point inside this node
    if not (node.abs_x <= x <= node.abs_x + node.abs_width and node.abs_y <= y <= node.abs_y + node.abs_height):
        return None

    # Check children in reverse (top-most first)
    for child in reversed(node.children):
        hit = hit_test(child, x, y)
        if hit is not None:
            return hit

    return node


class EventManager:
    """
    Tracks pointer interaction states (:hover, :active) and dispatches action callbacks.
    """

    def __init__(self, root_node: Node, repaint_callback: Callable[[], None]):
        self.root_node: Node = root_node
        self.repaint_callback: Callable[[], None] = repaint_callback
        self.hovered_node: Optional[Node] = None
        self.active_node: Optional[Node] = None
        self.actions: Dict[str, Callable[[], None]] = {}

    def register_action(self, name: str, callback: Callable[[], None]) -> None:
        self.actions[name] = callback

    def on_mouse_move(self, x: float, y: float) -> bool:
        """
        Updates :hover states. Returns True if hover changed and repaint is needed.
        """
        new_hovered = hit_test(self.root_node, x, y)
        if new_hovered != self.hovered_node:
            # Clear previous hover
            if self.hovered_node:
                self.hovered_node.is_hovered = False
            # Set new hover
            if new_hovered:
                new_hovered.is_hovered = True
            self.hovered_node = new_hovered
            self.repaint_callback()
            return True
        return False

    def on_mouse_leave(self) -> None:
        if self.hovered_node:
            self.hovered_node.is_hovered = False
            self.hovered_node = None
            self.repaint_callback()

    def on_mouse_press(self, x: float, y: float) -> None:
        hit = hit_test(self.root_node, x, y)
        if hit:
            hit.is_active = True
            self.active_node = hit
            self.repaint_callback()

    def on_mouse_release(self, x: float, y: float) -> None:
        if self.active_node:
            self.active_node.is_active = False
            hit = hit_test(self.root_node, x, y)
            
            # If released on same node that was pressed, trigger click action
            if hit == self.active_node:
                action_name = hit.attributes.get("on_click")
                if action_name and action_name in self.actions:
                    try:
                        self.actions[action_name]()
                    except Exception as e:
                        print(f"[PrismTK] Error running action '{action_name}': {e}")

            self.active_node = None
            self.repaint_callback()
