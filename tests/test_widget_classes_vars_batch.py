import tkinter as tk
import pytest
from tkblend import (
    Card,
    Button,
    Switch,
    CheckBox,
    RadioButton,
    Slider,
    ProgressBar,
    Badge,
    BaseControl,
    DrawBatch,
    Color,
    set_theme,
)


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_card_classes_vars_and_batch(root):
    set_theme("dark")
    card = Card(root, width=200, height=100, corner_radius=12)
    card.pack()
    root.update_idletasks()

    assert card.has_class("card")
    assert card.has_class("elevated")
    assert card.has_batch

    # Verify dynamic variables
    assert "--card-bg" in card.vars
    assert "--card-border" in card.vars
    assert "--card-shadow" in card.vars
    assert "--card-rx" in card.vars

    # Update variable and verify
    card.set_var("--card-bg", "#ff0088")
    assert card.get_var("--card-bg") == "#ff0088"
    root.update_idletasks()


def test_button_classes_and_vars(root):
    set_theme("dark")
    btn = Button(root, text="Action Button")
    btn.pack()
    root.update_idletasks()

    assert btn.has_class("button")
    assert "--btn-bg" in btn.vars
    assert "--btn-fg" in btn.vars

    # Test adding and toggling custom CSS classes
    btn.add_class("primary")
    assert btn.has_class("primary")
    assert "primary" in btn.classes

    btn.toggle_class("active")
    assert btn.has_class("active")
    btn.toggle_class("active")
    assert not btn.has_class("active")


def test_switch_classes_and_vars(root):
    set_theme("dark")
    sw = Switch(root, text="Enable notifications", is_on=False)
    sw.pack()
    root.update_idletasks()

    assert sw.has_class("switch")
    assert not sw.has_class("checked")
    assert "--track-bg" in sw.vars
    assert "--thumb-bg" in sw.vars

    sw.toggle()
    root.update_idletasks()
    assert sw.has_class("checked")
    assert sw.is_on()

    sw.deselect()
    root.update_idletasks()
    assert not sw.has_class("checked")
    assert not sw.is_on()


def test_checkbox_classes_and_vars(root):
    set_theme("dark")
    cb = CheckBox(root, text="Remember me")
    cb.pack()
    root.update_idletasks()

    assert cb.has_class("checkbox")
    assert not cb.has_class("checked")
    assert "--box-bg" in cb.vars
    assert "--check-color" in cb.vars

    cb.select()
    root.update_idletasks()
    assert cb.has_class("checked")
    assert cb.is_checked()


def test_radio_classes_and_vars(root):
    set_theme("dark")
    r1 = RadioButton(root, text="Option A", value="A")
    r1.pack()
    root.update_idletasks()

    assert r1.has_class("radio")
    assert not r1.has_class("selected")
    assert "--dot-color" in r1.vars

    r1.select()
    root.update_idletasks()
    assert r1.has_class("selected")


def test_slider_classes_and_vars(root):
    set_theme("dark")
    s = Slider(root, from_=0, to=100, value=50)
    s.pack()
    root.update_idletasks()

    assert s.has_class("slider")
    assert s.has_class("horizontal")
    assert "--track-bg" in s.vars
    assert "--thumb-pos" in s.vars

    s.set(75)
    root.update_idletasks()
    assert float(s.get_var("--thumb-pos")) == pytest.approx(0.75, rel=1e-3)


def test_progressbar_classes_and_vars(root):
    set_theme("dark")
    pb = ProgressBar(root, value=0.4)
    pb.pack()
    root.update_idletasks()

    assert pb.has_class("progressbar")
    assert pb.has_class("determinate")
    assert "--track-bg" in pb.vars
    assert "--progress" in pb.vars

    pb.set(0.8)
    root.update_idletasks()
    assert float(pb.get_var("--progress")) == pytest.approx(0.8, rel=1e-3)


def test_badge_classes_and_vars(root):
    set_theme("dark")
    b = Badge(root, text="Active", variant="success")
    b.pack()
    root.update_idletasks()

    assert b.has_class("badge")
    assert b.has_class("success")
    assert "--badge-bg" in b.vars
    assert "--badge-fg" in b.vars

    b.variant = "danger"
    root.update_idletasks()
    assert b.has_class("danger")
    assert not b.has_class("success")
