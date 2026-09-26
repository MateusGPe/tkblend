"""
Reactive State Management & Template Data-Binding Evaluator for tkblend.prismtk.
"""

from __future__ import annotations
import re
from typing import Any, Callable, Dict, Optional, Set


class ReactiveState:
    """
    Observable Dictionary & Object proxy that notifies listeners when properties are updated.
    Supports both dict-like `state['count']` and attribute `state.count`.
    """

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        super().__setattr__("_data", dict(initial_data or {}))
        super().__setattr__("_listeners", set())
        super().__setattr__("_frozen", False)

    def add_listener(self, callback: Callable[[str, Any], None]) -> None:
        self._listeners.add(callback)

    def remove_listener(self, callback: Callable[[str, Any], None]) -> None:
        self._listeners.discard(callback)

    def _notify(self, key: str, value: Any) -> None:
        for callback in list(self._listeners):
            try:
                callback(key, value)
            except Exception:
                pass

    def __getitem__(self, key: str) -> Any:
        return self._data.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        old_val = self._data.get(key)
        self._data[key] = value
        if old_val != value:
            self._notify(key, value)

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            return self._data[name]
        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, "_data") and name in self._data:
            self[name] = value
        elif hasattr(self, "_data") and not name.startswith("_"):
            self[name] = value
        else:
            super().__setattr__(name, value)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def update(self, new_data: Dict[str, Any]) -> None:
        for k, v in new_data.items():
            self[k] = v

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)


_BINDING_PATTERN = re.compile(r"\{([^}]+)\}")


def evaluate_expression(expr: str, state: ReactiveState) -> Any:
    """
    Safely evaluates simple state binding expressions like:
      - 'count' -> state['count']
      - 'status == "online" ? "active" : "offline"'
      - 'progress * 100'
    """
    expr = expr.strip()
    if not expr:
        return ""

    # Direct key lookup
    val = state.get(expr, None)
    if val is not None:
        return val

    # Ternary expression: cond ? val_true : val_false
    if "?" in expr and ":" in expr:
        parts = expr.split("?", 1)
        cond_str = parts[0].strip()
        rest = parts[1].split(":", 1)
        true_val = rest[0].strip().strip("'\"")
        false_val = rest[1].strip().strip("'\"")

        # Evaluate condition
        try:
            # Safe eval with state keys in scope
            res = eval(cond_str, {"__builtins__": {}}, state.to_dict())
            return true_val if res else false_val
        except Exception:
            return false_val

    # Generic safe math/string evaluation
    try:
        return eval(expr, {"__builtins__": {}}, state.to_dict())
    except Exception:
        return expr


def interpolate_string(template_str: str, state: ReactiveState) -> str:
    """
    Replaces {variable_name} or {expression} with the evaluated value from state.
    """
    if not template_str or "{" not in template_str:
        return template_str

    def _replace_match(match: re.Match) -> str:
        expr = match.group(1)
        res = evaluate_expression(expr, state)
        return str(res) if res is not None else ""

    return _BINDING_PATTERN.sub(_replace_match, template_str)
