"""
Template & Markup Parser + Python DSL helpers for tkblend.prismtk.
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any, Union
from tkblend.prismtk.dom import Node


def _parse_element_tree(elem: ET.Element) -> Node:
    tag = elem.tag.lower()
    attribs = dict(elem.attrib)
    
    node_id = attribs.pop("id", None)
    class_name = attribs.pop("class", None)
    style = attribs.pop("style", None)

    # Text content (if non-whitespace)
    text_val = elem.text.strip() if elem.text and elem.text.strip() else None

    node = Node(
        tag=tag,
        id=node_id,
        class_name=class_name,
        style=style,
        attributes=attribs,
        text=text_val
    )

    for child_elem in elem:
        node.add_child(_parse_element_tree(child_elem))

    return node


def parse_template(markup: str) -> Node:
    """
    Parses an HTML/XML template string into a Node tree.
    Wraps multiple root elements into an implicit <root> container if needed.
    """
    cleaned = markup.strip()
    # If the markup doesn't start with a single root tag or has multiple roots, wrap it
    try:
        root_elem = ET.fromstring(cleaned)
    except ET.ParseError:
        # Try wrapping in <prism-root>
        wrapped = f"<prism-root>{cleaned}</prism-root>"
        root_elem = ET.fromstring(wrapped)

    return _parse_element_tree(root_elem)


# ---------------------------------------------------------------------------
# Python Declarative DSL Node Factory Classes
# ---------------------------------------------------------------------------

class Box(Node):
    def __init__(self, id: Optional[str] = None, class_name: Optional[Union[str, List[str]]] = None, style: Optional[str] = None, **kwargs):
        super().__init__("box", id=id, class_name=class_name, style=style, attributes=kwargs)

class Stack(Node):
    def __init__(self, id: Optional[str] = None, class_name: Optional[Union[str, List[str]]] = None, style: Optional[str] = None, **kwargs):
        super().__init__("stack", id=id, class_name=class_name, style=style, attributes=kwargs)

class Text(Node):
    def __init__(self, text: str = "", id: Optional[str] = None, class_name: Optional[Union[str, List[str]]] = None, style: Optional[str] = None, **kwargs):
        super().__init__("text", id=id, class_name=class_name, style=style, text=text, attributes=kwargs)

class Button(Node):
    def __init__(self, text: str = "", on_click: Optional[str] = None, id: Optional[str] = None, class_name: Optional[Union[str, List[str]]] = None, style: Optional[str] = None, **kwargs):
        attribs = dict(kwargs)
        if on_click:
            attribs["on_click"] = on_click
        super().__init__("button", id=id, class_name=class_name, style=style, text=text, attributes=attribs)

class Circle(Node):
    def __init__(self, id: Optional[str] = None, class_name: Optional[Union[str, List[str]]] = None, style: Optional[str] = None, **kwargs):
        super().__init__("circle", id=id, class_name=class_name, style=style, attributes=kwargs)

class Image(Node):
    def __init__(self, src: str = "", id: Optional[str] = None, class_name: Optional[Union[str, List[str]]] = None, style: Optional[str] = None, **kwargs):
        attribs = dict(kwargs)
        if src:
            attribs["src"] = src
        super().__init__("image", id=id, class_name=class_name, style=style, attributes=attribs)

class Progress(Node):
    def __init__(self, value: float = 0.0, max: float = 100.0, id: Optional[str] = None, class_name: Optional[Union[str, List[str]]] = None, style: Optional[str] = None, **kwargs):
        attribs = dict(kwargs)
        attribs["value"] = value
        attribs["max"] = max
        super().__init__("progress", id=id, class_name=class_name, style=style, attributes=attribs)
