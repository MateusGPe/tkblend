"""
DOM / Scene Graph Node Hierarchy for tkblend.prismtk.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any, Union, Callable
import re


class Node:
    """
    Base Scene Graph Node in the Prism DOM tree.
    """

    def __init__(
        self,
        tag: str,
        id: Optional[str] = None,
        class_name: Optional[Union[str, List[str]]] = None,
        style: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        children: Optional[List[Node]] = None,
        text: Optional[str] = None,
    ):
        self.tag: str = tag.lower()
        self.id: Optional[str] = id
        self._classes: set[str] = set()
        if class_name:
            if isinstance(class_name, list):
                self._classes.update(class_name)
            else:
                self._classes.update(class_name.strip().split())

        self.inline_style: str = style or ""
        self.attributes: Dict[str, Any] = attributes or {}
        self.children: List[Node] = []
        self.parent: Optional[Node] = None
        self.text_content: Optional[str] = text

        # Pseudo-classes
        self.is_hovered: bool = False
        self.is_active: bool = False
        self.is_focused: bool = False
        self.is_disabled: bool = bool(self.attributes.get("disabled", False))

        # Computed Layout Box (set during layout pass)
        self.layout_x: float = 0.0
        self.layout_y: float = 0.0
        self.layout_width: float = 0.0
        self.layout_height: float = 0.0

        # Absolute screen bounds (for hit-testing)
        self.abs_x: float = 0.0
        self.abs_y: float = 0.0
        self.abs_width: float = 0.0
        self.abs_height: float = 0.0

        # Computed CSS styles
        self.computed_style: Dict[str, Any] = {}

        if children:
            for child in children:
                self.add_child(child)

    @property
    def classes(self) -> set[str]:
        return self._classes

    def has_class(self, cls: str) -> bool:
        return cls in self._classes

    def add_class(self, cls: str) -> Node:
        self._classes.add(cls)
        return self

    def remove_class(self, cls: str) -> Node:
        self._classes.discard(cls)
        return self

    def toggle_class(self, cls: str, state: Optional[bool] = None) -> Node:
        if state is None:
            if cls in self._classes:
                self._classes.remove(cls)
            else:
                self._classes.add(cls)
        elif state:
            self._classes.add(cls)
        else:
            self._classes.discard(cls)
        return self

    def add_child(self, child: Node) -> Node:
        child.parent = self
        self.children.append(child)
        return self

    def remove_child(self, child: Node) -> Node:
        if child in self.children:
            child.parent = None
            self.children.remove(child)
        return self

    def find_by_id(self, node_id: str) -> Optional[Node]:
        clean_id = node_id.lstrip("#")
        if self.id == clean_id:
            return self
        for child in self.children:
            found = child.find_by_id(clean_id)
            if found is not None:
                return found
        return None

    def find_by_tag(self, tag_name: str) -> List[Node]:
        res: List[Node] = []
        if self.tag == tag_name.lower():
            res.append(self)
        for child in self.children:
            res.extend(child.find_by_tag(tag_name))
        return res

    def find_by_class(self, class_name: str) -> List[Node]:
        clean_cls = class_name.lstrip(".")
        res: List[Node] = []
        if self.has_class(clean_cls):
            res.append(self)
        for child in self.children:
            res.extend(child.find_by_class(clean_cls))
        return res

    def __getitem__(self, children_list: Union[Node, List[Node]]) -> Node:
        """Enables Python DSL syntax: Box()[ Child1(), Child2() ]"""
        if isinstance(children_list, Node):
            self.add_child(children_list)
        elif isinstance(children_list, (list, tuple)):
            for child in children_list:
                if isinstance(child, Node):
                    self.add_child(child)
        return self

    def __repr__(self) -> str:
        id_str = f" id='{self.id}'" if self.id else ""
        class_str = f" class='{' '.join(self.classes)}'" if self.classes else ""
        return f"<{self.tag}{id_str}{class_str} ({len(self.children)} children)>"
