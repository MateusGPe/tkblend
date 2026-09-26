"""
Unit Tests for tkblend.prismtk Declarative CSS Vector UI Engine.
"""

import pytest
import tkinter as tk
import tkblend.prismtk as prism
from tkblend.prismtk.dom import Node
from tkblend.prismtk.state import ReactiveState, interpolate_string
from tkblend.prismtk.parser import parse_template, Box, Text, Button
from tkblend.prismtk.css import StyleSheet, Selector, compute_node_style
from tkblend.prismtk.layout import compute_layout


def test_dom_node_and_dsl():
    # Test Python DSL building
    card = Box(id="main-card", class_name="card shadow")[
        Text("Hello World", class_name="title"),
        Button("Click Me", on_click="do_action", class_name="btn")
    ]

    assert card.tag == "box"
    assert card.id == "main-card"
    assert card.has_class("card")
    assert card.has_class("shadow")
    assert len(card.children) == 2

    title_node = card.find_by_class("title")[0]
    assert title_node.text_content == "Hello World"

    btn_node = card.find_by_tag("button")[0]
    assert btn_node.attributes.get("on_click") == "do_action"


def test_template_parser():
    markup = """
    <box id="profile" class="container">
        <text class="user-name">Alice</text>
        <button class="btn" on_click="save">Save</button>
    </box>
    """
    root = parse_template(markup)
    assert root.tag == "box"
    assert root.id == "profile"
    assert root.has_class("container")
    assert len(root.children) == 2
    assert root.children[0].tag == "text"
    assert root.children[0].text_content == "Alice"


def test_reactive_state_and_bindings():
    state = ReactiveState({"username": "Bob", "count": 10, "status": "online"})
    
    # Test property access and dict access
    assert state.username == "Bob"
    assert state["count"] == 10

    # Test interpolation
    interpolated = interpolate_string("User: {username} (Score: {count})", state)
    assert interpolated == "User: Bob (Score: 10)"

    # Test ternary expression
    expr = interpolate_string("{status == 'online' ? 'Active' : 'Offline'}", state)
    assert expr == "Active"

    # Test listener notification
    notifications = []
    state.add_listener(lambda k, v: notifications.append((k, v)))
    state.count = 20
    assert notifications == [("count", 20)]


def test_css_selectors_and_cascading():
    css = """
    box { background: #111111; width: 200px; }
    .card { background: #222222; border-radius: 8px; }
    #header { background: #333333; }
    .card:hover { background: #444444; }
    """
    sheet = StyleSheet(css)
    node = Node("box", id="header", class_name="card")

    # Initial style (ID has highest specificity: 100 > 10 > 1)
    styles = compute_node_style(node, [sheet])
    assert styles["background"] == "#333333"
    assert styles["border-radius"] == 8.0

    # Pseudo-class hover
    node.is_hovered = True
    hover_styles = compute_node_style(node, [sheet])
    # #header specificity = 100, .card:hover specificity = 10 + 10 = 20.
    # So #header still wins for background!
    assert hover_styles["background"] == "#333333"


def test_flex_layout():
    root = Node("box")
    root.computed_style = {
        "width": 300.0,
        "height": 100.0,
        "flex-direction": "row",
        "justify-content": "space-between",
        "align-items": "center",
        "padding": "10px"
    }

    child1 = Node("box")
    child1.computed_style = {"width": 50.0, "height": 40.0}

    child2 = Node("box")
    child2.computed_style = {"width": 50.0, "height": 40.0}

    root.add_child(child1)
    root.add_child(child2)

    compute_layout(root, 300.0, 100.0, 0.0, 0.0)

    # Root bounds
    assert root.abs_x == 0.0
    assert root.abs_y == 0.0
    assert root.abs_width == 300.0
    assert root.abs_height == 100.0

    # Child 1 at inner left (10px padding)
    assert child1.abs_x == 10.0
    # Child 2 at inner right (300 - 10 - 50 = 240)
    assert child2.abs_x == 240.0


def test_prism_widget_lifecycle():
    tk_root = tk.Tk()
    tk_root.withdraw()

    template = """
    <box class="card">
        <text class="label">{greeting}</text>
        <button class="btn" on_click="greet">Greet</button>
    </box>
    """
    css = """
    .card { background: #1e1e2e; padding: 12px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .label { color: #ffffff; font-size: 14px; }
    .btn { background: #3498db; color: #ffffff; }
    """
    widget = prism.PrismWidget(
        tk_root,
        template=template,
        css=css,
        state={"greeting": "Hello"},
        width=200,
        height=100
    )

    clicked = []
    @widget.action("greet")
    def on_greet():
        clicked.append(True)
        widget.state.greeting = "Welcome!"

    widget.request_repaint()
    assert widget.state.greeting == "Hello"

    # Trigger action manually via event manager
    widget.events.actions["greet"]()
    assert clicked == [True]
    assert widget.state.greeting == "Welcome!"

    tk_root.destroy()
