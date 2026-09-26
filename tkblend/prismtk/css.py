"""
CSS Parser, Selector Matcher, and Cascading Style Resolver for tkblend.prismtk.
"""

from __future__ import annotations
import re
from typing import Dict, List, Tuple, Optional, Any
from tkblend.prismtk.dom import Node
from tkblend.theme import resolve_theme_color


class Selector:
    """
    Represents a parsed CSS selector component.
    Examples: 'box', '.card', '#header', 'button:hover', '.item:active'
    """

    def __init__(self, raw: str):
        self.raw = raw.strip()
        self.tag: Optional[str] = None
        self.id: Optional[str] = None
        self.classes: List[str] = []
        self.pseudo: Optional[str] = None
        self.specificity: int = 0
        self._parse()

    def _parse(self) -> None:
        text = self.raw
        # Check pseudo-class (:hover, :active, :focus, :disabled)
        if ":" in text:
            parts = text.split(":", 1)
            text = parts[0]
            self.pseudo = parts[1].strip()
            self.specificity += 10

        # Check ID (#id)
        if "#" in text:
            parts = text.split("#", 1)
            text = parts[0]
            id_part = parts[1]
            if "." in id_part:
                id_sub = id_part.split(".", 1)
                self.id = id_sub[0]
                text += "." + id_sub[1]
            else:
                self.id = id_part
            self.specificity += 100

        # Check Classes (.class1.class2)
        if "." in text:
            parts = text.split(".")
            if parts[0]:
                self.tag = parts[0].lower()
                self.specificity += 1
            for cls in parts[1:]:
                if cls:
                    self.classes.append(cls)
                    self.specificity += 10
        elif text:
            self.tag = text.lower()
            self.specificity += 1

    def matches(self, node: Node) -> bool:
        if self.tag and self.tag != node.tag:
            return False
        if self.id and self.id != node.id:
            return False
        for cls in self.classes:
            if not node.has_class(cls):
                return False
        if self.pseudo:
            if self.pseudo == "hover" and not node.is_hovered:
                return False
            if self.pseudo == "active" and not node.is_active:
                return False
            if self.pseudo == "focus" and not node.is_focused:
                return False
            if self.pseudo == "disabled" and not node.is_disabled:
                return False
        return True


class Rule:
    def __init__(self, selectors: List[Selector], declarations: Dict[str, str], order: int):
        self.selectors = selectors
        self.declarations = declarations
        self.order = order


class StyleSheet:
    """
    Parses and stores CSS rules.
    """

    def __init__(self, css_text: str = ""):
        self.rules: List[Rule] = []
        if css_text:
            self.parse(css_text)

    def parse(self, css_text: str) -> None:
        # Strip comments /* ... */
        clean_css = re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)
        
        # Split rules by '}'
        order = 0
        for block in clean_css.split("}"):
            block = block.strip()
            if not block or "{" not in block:
                continue
            selector_part, decl_part = block.split("{", 1)
            selectors = [Selector(s) for s in selector_part.split(",") if s.strip()]
            
            declarations: Dict[str, str] = {}
            for line in decl_part.split(";"):
                line = line.strip()
                if not line or ":" not in line:
                    continue
                prop, val = line.split(":", 1)
                declarations[prop.strip().lower()] = val.strip()

            if selectors and declarations:
                self.rules.append(Rule(selectors, declarations, order))
                order += 1


def resolve_css_value(value_str: str) -> Any:
    """
    Resolves CSS variables like var(--primary) or var(--card-bg) to active theme hex colors,
    and converts pixel units (e.g. '12px' -> 12.0).
    """
    value_str = value_str.strip()

    # Resolve CSS variable: var(--token-name) or var(--token-name, fallback)
    if "var(" in value_str:
        def _replace_var(m):
            var_name = m.group(1).strip()
            # Convert CSS variable --token-name to theme token name
            token = var_name.lstrip("-").replace("-", "_")
            fallback = m.group(2).strip() if m.group(2) else "#ffffff"
            try:
                resolved = resolve_theme_color(token)
                return resolved if resolved else fallback
            except Exception:
                return fallback

        value_str = re.sub(r"var\(\s*([a-zA-Z0-9_-]+)(?:\s*,\s*([^)]+))?\s*\)", _replace_var, value_str)

    # Unit parsing
    if value_str.endswith("px"):
        try:
            return float(value_str[:-2].strip())
        except ValueError:
            pass
    elif value_str.endswith("deg"):
        try:
            return float(value_str[:-3].strip())
        except ValueError:
            pass

    return value_str


def parse_inline_declarations(style_str: str) -> Dict[str, str]:
    declarations: Dict[str, str] = {}
    if not style_str:
        return declarations
    for line in style_str.split(";"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        prop, val = line.split(":", 1)
        declarations[prop.strip().lower()] = val.strip()
    return declarations


def compute_node_style(node: Node, stylesheets: List[StyleSheet]) -> Dict[str, Any]:
    """
    Resolves full cascading styles for a Node given active stylesheets and inline styles.
    """
    # Collect matching rules: (specificity, rule_order, declarations)
    matched_rules: List[Tuple[int, int, Dict[str, str]]] = []

    for sheet in stylesheets:
        for rule in sheet.rules:
            highest_spec = -1
            for sel in rule.selectors:
                if sel.matches(node):
                    if sel.specificity > highest_spec:
                        highest_spec = sel.specificity
            if highest_spec >= 0:
                matched_rules.append((highest_spec, rule.order, rule.declarations))

    # Sort matched rules by specificity, then by source order
    matched_rules.sort(key=lambda item: (item[0], item[1]))

    # Merge declarations
    merged: Dict[str, str] = {}
    for _, _, decls in matched_rules:
        merged.update(decls)

    # Apply inline style with highest priority
    if node.inline_style:
        merged.update(parse_inline_declarations(node.inline_style))

    # Resolve all values (units, var(--...))
    computed: Dict[str, Any] = {}
    for prop, raw_val in merged.items():
        computed[prop] = resolve_css_value(raw_val)

    node.computed_style = computed
    return computed
