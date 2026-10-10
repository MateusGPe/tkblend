import tkinter as tk
import pytest
import tkblend as tb
from tkblend import (
    Button,
    Switch,
    Checkbox,
    Radio,
    Slider,
    Progressbar,
    Badge,
    Card,
    Label,
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


def test_button_widget(root):
    set_theme("dark")
    clicked = []
    btn = Button(root, text="Click", command=lambda: clicked.append(True), width=120, height=36)
    btn.pack()
    root.update_idletasks()

    assert btn.text == "Click"
    assert btn.widget_class == "button"
    btn.invoke()
    assert len(clicked) == 1

    btn.text = "Updated"
    assert btn.text == "Updated"


def test_switch_widget(root):
    set_theme("dark")
    sw_var = tk.BooleanVar(value=False)
    sw = Switch(root, text="Toggle", variable=sw_var, width=100, height=30)
    sw.pack()
    root.update_idletasks()

    assert not sw.is_checked
    sw.toggle()
    assert sw.is_checked
    assert sw_var.get() is True

    sw.toggle()
    assert not sw.is_checked
    assert sw_var.get() is False


def test_checkbox_widget(root):
    set_theme("dark")
    cb_var = tk.BooleanVar(value=True)
    cb = Checkbox(root, text="Agree", variable=cb_var, width=120, height=30)
    cb.pack()
    root.update_idletasks()

    assert cb.is_checked
    cb.toggle()
    assert not cb.is_checked
    assert cb_var.get() is False


def test_radio_widget(root):
    set_theme("dark")
    r_var = tk.StringVar(value="opt1")
    r1 = Radio(root, text="Option 1", value="opt1", variable=r_var)
    r2 = Radio(root, text="Option 2", value="opt2", variable=r_var)
    r1.pack()
    r2.pack()
    root.update_idletasks()

    assert r1.is_checked
    assert not r2.is_checked

    r2.select()
    assert r_var.get() == "opt2"
    assert r2.is_checked


def test_slider_widget(root):
    set_theme("dark")
    sl = Slider(root, from_=0.0, to=100.0, value=25.0, width=150, height=24)
    sl.pack()
    root.update_idletasks()

    assert sl.get() == pytest.approx(25.0, abs=1.0)
    sl.set(80.0)
    assert sl.get() == pytest.approx(80.0, abs=1.0)


def test_progressbar_widget(root):
    set_theme("dark")
    pb = Progressbar(root, value=10.0, maximum=100.0, width=150, height=10)
    pb.pack()
    root.update_idletasks()

    assert pb.get() == pytest.approx(10.0, abs=0.5)
    pb.step(15.0)
    assert pb.get() == pytest.approx(25.0, abs=0.5)


def test_badge_and_label_and_card(root):
    set_theme("dark")
    card = Card(root, width=200, height=150)
    card.pack()
    badge = Badge(card, text="Status", width=60, height=24)
    badge.pack()
    lbl = Label(card, text="Information", width=100, height=26)
    lbl.pack()
    root.update_idletasks()

    assert badge.text == "Status"
    assert lbl.text == "Information"
