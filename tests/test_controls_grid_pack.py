import pytest
import tkinter as tk
from tkblend.theme import set_theme
from tkblend.widgets import Button, Label, Switch, Checkbox, Radio, Frame


@pytest.fixture
def root():
    r = tk.Tk()
    r.geometry("600x500")
    r.deiconify()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_controls_pack_fill_and_expand(root):
    set_theme("dark")

    container = Frame(root, width=500, height=300)
    container.pack_propagate(False)
    container.pack(fill="both", expand=True)
    root.update()

    # Pack fill='x'
    btn = Button(container, text="Wide Button", anchor="w")
    btn.pack(fill="x", padx=10, pady=5)
    root.update()

    assert btn.winfo_width() > 100
    assert btn.anchor == "w"

    # Pack centered label
    lbl = Label(container, text="Centered Label", anchor="center")
    lbl.pack(fill="x", padx=10, pady=5)
    root.update()

    assert lbl.winfo_width() > 100
    assert lbl.anchor == "center"


def test_controls_grid_sticky_and_anchors(root):
    set_theme("dark")

    grid_parent = Frame(root, width=500, height=400)
    grid_parent.grid_propagate(False)
    grid_parent.pack(fill="both", expand=True)
    grid_parent.grid_columnconfigure(0, weight=1)
    grid_parent.grid_columnconfigure(1, weight=1)

    # Left-aligned switch
    sw = Switch(grid_parent, text="Notifications", anchor="w")
    sw.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

    # Right-aligned checkbox
    chk = Checkbox(grid_parent, text="Confirm", anchor="e")
    chk.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

    # Radio button in grid
    rb = Radio(grid_parent, text="Choice", anchor="center")
    rb.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

    root.update()

    assert sw.winfo_width() > 50
    assert sw.anchor == "w"
    assert chk.winfo_width() > 50
    assert chk.anchor == "e"
    assert rb.winfo_width() > 100
    assert rb.anchor == "center"
