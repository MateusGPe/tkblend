"""
Regression tests for TLabelframe layout and dynamic child control resize.
Verifies that controls resizing inside a Labelframe do not produce duplicate label nodes
or visual artifacts from improper layout nesting.
"""

import pytest
import tkinter as tk
from tkinter import ttk
import tkblend


@pytest.fixture
def root():
    try:
        r = tk.Tk()
        r.withdraw()
        yield r
        r.destroy()
    except tk.TclError:
        pytest.skip("Tk display not available in environment")


def test_labelframe_layout_structure(root):
    """Verify that TLabelframe uses standard Labelframe.border layout without nested duplicate label."""
    tkblend.apply_theme(root, dark_mode=True)
    style = ttk.Style(master=root)

    layout = style.layout("TLabelframe")
    # Layout must be [('Labelframe.border', {'sticky': 'nswe'})]
    assert len(layout) == 1
    elem_name, opts = layout[0]
    assert elem_name == "Labelframe.border"
    assert opts.get("sticky") == "nswe"

    # Crucially, Labelframe.border should NOT contain children with Labelframe.label
    # (since Tk's LabelframeDisplay separately renders label.labelLayout)
    children = opts.get("children", [])
    for child_name, child_opts in children:
        assert child_name != "Labelframe.label"
        for sub_name, _ in child_opts.get("children", []):
            assert sub_name != "Labelframe.label"


def test_labelframe_child_label_shrink(root):
    """Verify that a Labelframe and its child label shrink cleanly when multiline text is reduced."""
    tkblend.apply_theme(root, dark_mode=True)
    root.deiconify()

    card = ttk.Labelframe(root, text=" File Properties ", padding=8)
    card.pack(fill="x", padx=10, pady=10)

    row = ttk.Frame(card)
    row.pack(fill="x", pady=2)

    var = tk.StringVar(value="Line 1 of very long text\nLine 2 of text that causes wrap")
    lbl = ttk.Label(row, textvariable=var, font=("Helvetica", 9), wraplength=180)
    lbl.pack(side="left", fill="x", expand=True)

    root.update()
    h_before = card.winfo_height()
    lbl_h_before = lbl.winfo_height()
    assert h_before > 0
    assert lbl_h_before > 0

    # Shrink text to 1 line
    var.set("Short Name")
    root.update()

    h_after = card.winfo_height()
    lbl_h_after = lbl.winfo_height()

    assert lbl_h_after < lbl_h_before, "Child label height should decrease with fewer lines"
    assert h_after < h_before, "Labelframe height should shrink when child control shrinks"
