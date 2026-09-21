"""
Unit tests for expanded controls in tkblend:
- Native TTK elements: TSeparator, TSizegrip, TPanedwindow Sash, TMenubutton, Treeitem.indicator, Switch.TCheckbutton
- High-level Python components: ToggleSwitch, Badge, SegmentedControl, Card
"""

import tkinter as tk
from tkinter import ttk
import unittest
import tkblend


class TestNewControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()
        tkblend.apply_theme(cls.root, dark_mode=True)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except Exception:
            pass

    def test_blend_color_hex(self):
        c1 = "#000000"
        c2 = "#ffffff"
        self.assertEqual(tkblend.blend_color_hex(c1, c2, 0.0), c1)
        self.assertEqual(tkblend.blend_color_hex(c1, c2, 1.0), c2)
        mid = tkblend.blend_color_hex(c1, c2, 0.5)
        self.assertEqual(mid.lower(), "#7f7f7f")

    def test_native_separator(self):
        h_sep = ttk.Separator(self.root, orient="horizontal")
        h_sep.pack()
        v_sep = ttk.Separator(self.root, orient="vertical")
        v_sep.pack()
        self.root.update_idletasks()
        h_sep.destroy()
        v_sep.destroy()

    def test_native_sizegrip(self):
        sg = ttk.Sizegrip(self.root)
        sg.pack()
        self.root.update_idletasks()
        sg.destroy()

    def test_native_panedwindow_and_sash(self):
        paned = ttk.Panedwindow(self.root, orient="horizontal")
        f1 = ttk.Frame(paned, width=100, height=100)
        f2 = ttk.Frame(paned, width=100, height=100)
        paned.add(f1)
        paned.add(f2)
        paned.pack()
        self.root.update_idletasks()
        paned.destroy()

    def test_native_menubutton(self):
        mb = ttk.Menubutton(self.root, text="Options", style="Secondary.TMenubutton")
        menu = tk.Menu(mb, tearoff=0)
        menu.add_command(label="Item 1")
        menu.add_command(label="Item 2")
        mb.configure(menu=menu)
        mb.pack()

        # Test variants
        for variant in ["Primary.TMenubutton", "Outline.TMenubutton", "Ghost.TMenubutton", "Destructive.TMenubutton"]:
            mb.configure(style=variant)
            self.root.update_idletasks()

        mb.destroy()

    def test_native_treeview_indicator(self):
        tree = ttk.Treeview(self.root)
        tree.pack()
        parent = tree.insert("", "end", text="Folder 1", open=True)
        child = tree.insert(parent, "end", text="Sub-item 1")
        tree.insert("", "end", text="Folder 2", open=False)
        self.root.update_idletasks()

        # Toggle open state
        tree.item(parent, open=False)
        self.root.update_idletasks()
        tree.item(parent, open=True)
        self.root.update_idletasks()
        tree.destroy()

    def test_switch_checkbutton_style(self):
        var = tk.BooleanVar(value=True)
        sw = ttk.Checkbutton(self.root, text="Native Switch", style="Switch.TCheckbutton", variable=var)
        sw.pack()
        self.root.update_idletasks()
        var.set(False)
        self.root.update_idletasks()
        sw.destroy()

    def test_toggle_switch_widget(self):
        var = tk.BooleanVar(value=False)
        cmd_called = []
        sw = tkblend.ToggleSwitch(self.root, text="Airplane Mode", variable=var, command=lambda: cmd_called.append(True))
        sw.pack()
        self.root.update_idletasks()

        self.assertFalse(sw.get())
        sw.toggle()
        self.assertTrue(sw.get())
        self.assertTrue(var.get())

        sw.set(False)
        self.assertFalse(sw.get())
        self.assertFalse(var.get())

        # Test step animation
        sw._target_progress = 1.0
        sw._step_animation()
        self.root.update_idletasks()
        sw.destroy()

    def test_badge_widget(self):
        b1 = tkblend.Badge(self.root, text="Active", variant="success", dot=True)
        b1.pack()
        self.root.update_idletasks()

        for v in ["primary", "secondary", "warning", "destructive", "outline"]:
            b1.set_variant(v)
            b1.set_text(f"Status: {v}")
            self.root.update_idletasks()

        b1.destroy()

    def test_segmented_control_widget(self):
        vals = ["Day", "Week", "Month", "Year"]
        selected = []
        var = tk.StringVar(value="Week")
        sc = tkblend.SegmentedControl(self.root, values=vals, variable=var, command=lambda v: selected.append(v))
        sc.pack()
        self.root.update_idletasks()

        self.assertEqual(sc.get(), "Week")
        sc.set("Month")
        self.assertEqual(sc.get(), "Month")
        self.assertEqual(var.get(), "Month")
        self.assertIn("Month", selected)
        sc.destroy()

    def test_card_container_sync(self):
        card = tkblend.Card(self.root)
        lbl = ttk.Label(card, text="Card Label")
        chk = ttk.Checkbutton(card, text="Card Check", style="Switch.TCheckbutton")
        lbl.pack()
        chk.pack()
        card.pack()
        self.root.update_idletasks()

        # Theme toggle updates card and its children
        tkblend.apply_theme(self.root, dark_mode=False)
        self.root.update_idletasks()
        tkblend.apply_theme(self.root, dark_mode=True)
        self.root.update_idletasks()
        card.destroy()


if __name__ == "__main__":
    unittest.main()
