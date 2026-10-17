import pytest
import tkinter as tk
from tkblend.theme import set_theme
from tkblend.widgets import Button, Label, Badge, Checkbox, Switch, ComboBox, Entry


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_button_and_label_fit_to_content(root):
    set_theme("dark")

    # Short vs Long Label auto-fit
    lbl_short = Label(root, text="Short")
    lbl_short.pack()
    root.update_idletasks()
    w_lbl_short = lbl_short.winfo_reqwidth()
    h_lbl_short = lbl_short.winfo_reqheight()

    lbl_long = Label(root, text="A significantly longer title that requires wider geometry")
    lbl_long.pack()
    root.update_idletasks()
    w_lbl_long = lbl_long.winfo_reqwidth()
    assert w_lbl_long > w_lbl_short

    # Multi-line label expands height
    lbl_multiline = Label(root, text="Line One\nLine Two\nLine Three")
    lbl_multiline.pack()
    root.update_idletasks()
    assert lbl_multiline.winfo_reqheight() > h_lbl_short * 2

    # Dynamic text mutation resizes natural geometry
    lbl_short.text = "Now expanded dynamically to be very long indeed"
    root.update_idletasks()
    assert lbl_short.winfo_reqwidth() > w_lbl_short

    # Button auto-fit
    btn_short = Button(root, text="OK")
    btn_short.pack()
    root.update_idletasks()
    w_btn_short = btn_short.winfo_reqwidth()

    btn_long = Button(root, text="Execute Complex Operation With Confirmations")
    btn_long.pack()
    root.update_idletasks()
    assert btn_long.winfo_reqwidth() > w_btn_short


def test_min_and_max_width_clamping(root):
    set_theme("dark")

    # Clamped by min_width
    btn_min = Button(root, text="X", min_width=180)
    btn_min.pack()
    root.update_idletasks()
    assert btn_min.width >= 180
    assert btn_min.winfo_reqwidth() >= int(round(180 * btn_min.scale_factor))

    # Clamped by max_width
    btn_max = Button(root, text="Extremely elongated action button text that would exceed limits", max_width=150)
    btn_max.pack()
    root.update_idletasks()
    assert btn_max.width <= 150
    assert btn_max.winfo_reqwidth() <= int(round(150 * btn_max.scale_factor))


def test_combobox_and_checkbox_fit_to_content(root):
    set_theme("dark")

    # ComboBox auto-fit to longest item
    cb_short = ComboBox(root, values=["A", "B", "C"])
    cb_short.pack()
    root.update_idletasks()
    w_cb_short = cb_short.winfo_reqwidth()

    cb_long = ComboBox(root, values=["Short", "A substantially lengthy option name in the list", "Mid"])
    cb_long.pack()
    root.update_idletasks()
    w_cb_long = cb_long.winfo_reqwidth()
    assert w_cb_long > w_cb_short

    # Checkbox auto-fit
    chk_short = Checkbox(root, text="Yes")
    chk_short.pack()
    root.update_idletasks()
    w_chk_short = chk_short.winfo_reqwidth()

    chk_long = Checkbox(root, text="I agree to all terms and conditions detailed above")
    chk_long.pack()
    root.update_idletasks()
    assert chk_long.winfo_reqwidth() > w_chk_short
