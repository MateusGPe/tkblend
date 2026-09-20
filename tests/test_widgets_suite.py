"""
Comprehensive test suite for tkblend modern UI widget library.
"""

import unittest
import tkinter as tk
from types import SimpleNamespace

from tkblend import (
    Theme,
    DARK_THEME,
    LIGHT_THEME,
    ThemeManager,
    ModernWidget,
    ModernFrame,
    ModernCard,
    ModernAccordion,
    ModernScrollableFrame,
    ModernButton,
    ModernCheckbox,
    ModernRadioButton,
    ModernRadioGroup,
    ModernProgressBar,
    ModernSlider,
    ModernSwitch,
    ModernSegmentedControl,
    ModernEntry,
    ModernDropdown,
    ModernSpinner,
    ModernBadge,
    ModernAvatar,
    ModernTooltip,
    ModernDialog,
    show_alert,
)


class TestWidgetSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except Exception:
            cls.root = None

    @classmethod
    def tearDownClass(cls):
        if cls.root:
            cls.root.destroy()

    def setUp(self):
        ThemeManager.animations_enabled = False
        ThemeManager.set_theme(DARK_THEME)

    def test_theme_and_theme_manager(self):
        self.assertEqual(ThemeManager.get_theme().name, "dark")

        # Toggle to light
        t = ThemeManager.toggle_theme()
        self.assertEqual(t.name, "light")
        self.assertEqual(ThemeManager.get_theme().name, "light")

        # Set string theme
        ThemeManager.set_theme("dark")
        self.assertEqual(ThemeManager.get_theme().name, "dark")

        ThemeManager.set_theme("light")
        self.assertEqual(ThemeManager.get_theme().name, "light")

        # Invalid theme name
        with self.assertRaises(ValueError):
            ThemeManager.set_theme("invalid_theme")

        with self.assertRaises(TypeError):
            ThemeManager.set_theme(123)  # type: ignore

        # Subscription
        notified = []

        def listener(thm):
            notified.append(thm.name)

        ThemeManager.subscribe(listener)
        ThemeManager.set_theme(DARK_THEME)
        self.assertIn("dark", notified)

        ThemeManager.unsubscribe(listener)
        ThemeManager.set_theme(LIGHT_THEME)
        self.assertEqual(len(notified), 1)

    def test_modern_button_variants(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        for var in ["primary", "secondary", "danger", "success", "custom"]:
            btn = ModernButton(self.root, text=f"{var} Button", variant=var)
            btn.render()
            btn._is_hovered = True
            btn.render()
            btn._is_pressed = True
            btn.render()
            btn.is_disabled = True
            btn.render()
            btn.destroy()

    def test_modern_checkbox(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        changes = []
        chk = ModernCheckbox(
            self.root,
            text="Accept Terms",
            is_checked=False,
            on_change=lambda val: changes.append(val),
        )
        self.assertFalse(chk.is_checked)

        chk.toggle()
        self.assertTrue(chk.is_checked)
        self.assertEqual(changes, [True])

        chk.is_checked = False
        self.assertFalse(chk.is_checked)

        # Click inside
        ev = SimpleNamespace(x=10, y=10)
        chk._handle_click(ev)
        self.assertTrue(chk.is_checked)

        # Disabled click
        chk.is_disabled = True
        chk._handle_click(ev)
        self.assertTrue(chk.is_checked)

        chk.render()
        chk.destroy()

    def test_modern_radio_and_group(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        selected = []
        group = ModernRadioGroup(
            self.root,
            options=["Option A", "Option B", "Option C"],
            selected_value="Option A",
            on_change=lambda val: selected.append(val),
        )
        self.assertEqual(group.value, "Option A")

        group.set_value("Option B")
        self.assertEqual(group.value, "Option B")

        # Add another option dynamically
        btn_d = group.add_option("Option D", "Option D")
        btn_d.select()
        self.assertEqual(group.value, "Option D")
        self.assertIn("Option D", selected)

        group.destroy()

    def test_modern_segmented_control(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        selections = []
        seg = ModernSegmentedControl(
            self.root,
            items=["Day", "Week", "Month", "Year"],
            selected_index=0,
            on_select=lambda idx, name: selections.append((idx, name)),
        )
        self.assertEqual(seg.selected_index, 0)

        seg.selected_index = 2
        self.assertEqual(seg.selected_index, 2)

        # Click segment 3
        ev = SimpleNamespace(x=220, y=18)
        seg._handle_click(ev)
        self.assertTrue(len(selections) > 0)

        seg.render()
        seg.destroy()

    def test_modern_entry(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        entry = ModernEntry(
            self.root,
            placeholder="Enter username...",
            text="",
            is_password=False,
        )
        self.assertEqual(entry.get(), "")

        entry.set_text("antigravity_user")
        self.assertEqual(entry.get(), "antigravity_user")

        # Focus in / out
        dummy_event = SimpleNamespace()
        entry._on_focus_in(dummy_event)
        self.assertTrue(entry._is_focused)

        entry._on_focus_out(dummy_event)
        self.assertFalse(entry._is_focused)

        # Error state
        entry.is_error = True
        self.assertTrue(entry.is_error)
        entry.render()

        # Resize
        cfg = SimpleNamespace(width=300, height=45)
        entry._on_configure(cfg)
        self.assertEqual(entry._widget_w, 300)

        entry.destroy()

    def test_modern_dropdown(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        chosen = []
        dd = ModernDropdown(
            self.root,
            options=["Profile", "Settings", "Billing", "Logout"],
            selected_index=0,
            on_select=lambda idx, val: chosen.append(val),
        )
        self.assertEqual(dd.selected_value, "Profile")

        # Open popup
        dd._open_popup()
        self.assertTrue(dd._is_open)
        self.assertIsNotNone(dd._popup_window)

        # Select item
        dd._select_item(1)
        self.assertEqual(dd.selected_value, "Settings")
        self.assertFalse(dd._is_open)
        self.assertIn("Settings", chosen)

        # Toggle open/close
        dummy = SimpleNamespace()
        dd._on_toggle_open(dummy)
        self.assertTrue(dd._is_open)
        dd._on_toggle_open(dummy)
        self.assertFalse(dd._is_open)

        dd.destroy()

    def test_modern_accordion(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        acc = ModernAccordion(self.root)
        sec1 = acc.add_section("General Settings", is_expanded=True)
        lbl1 = tk.Label(sec1, text="Content 1")
        lbl1.pack()

        sec2 = acc.add_section("Security", is_expanded=False)
        lbl2 = tk.Label(sec2, text="Content 2")
        lbl2.pack()

        self.assertEqual(len(acc._items), 2)
        self.assertTrue(acc._items[0]._is_expanded)
        self.assertFalse(acc._items[1]._is_expanded)

        # Toggle item
        acc._items[1].toggle()
        self.assertTrue(acc._items[1]._is_expanded)

        acc.destroy()

    def test_modern_scrollable_frame(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        sframe = ModernScrollableFrame(self.root, width=200, height=150)
        for i in range(10):
            lbl = tk.Label(sframe.scrollable_content, text=f"Row {i}")
            lbl.pack()

        # Simulate wheel
        ev_down = SimpleNamespace(num=5, delta=-120)
        sframe._on_mousewheel(ev_down)

        ev_up = SimpleNamespace(num=4, delta=120)
        sframe._on_mousewheel(ev_up)

        sframe.destroy()

    def test_modern_feedback_widgets(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        # Spinner
        spinner = ModernSpinner(self.root, size=32)
        self.assertTrue(spinner._is_spinning)
        spinner._spin_step()
        spinner.stop()
        self.assertFalse(spinner._is_spinning)
        spinner.start()
        self.assertTrue(spinner._is_spinning)
        spinner.stop()
        spinner.destroy()

        # Badges
        for variant in ["primary", "success", "warning", "danger", "neutral"]:
            badge = ModernBadge(self.root, text="Status", variant=variant, dot=True)
            badge.set_text("Active")
            badge.render()
            badge.destroy()

        # Avatar
        for stat in ["online", "busy", "away", "offline", None]:
            avatar = ModernAvatar(self.root, text="JD", size=40, status=stat)
            avatar.render()
            avatar.destroy()

        # Tooltip
        btn = tk.Button(self.root, text="Hover me")
        btn.pack()
        tip = ModernTooltip(btn, text="Helpful hint", delay_ms=10)
        tip._show_tip()
        self.assertIsNotNone(tip._tip_window)
        tip._on_leave()
        self.assertIsNone(tip._tip_window)
        btn.destroy()

    def test_modern_dialog(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        confirmed = []
        cancelled = []

        # Confirm action
        dlg1 = ModernDialog(
            self.root,
            title="Confirm Action",
            message="Are you sure you want to proceed?",
            on_confirm=lambda: confirmed.append(True),
        )
        dlg1._handle_confirm()
        self.assertTrue(dlg1.result)
        self.assertEqual(len(confirmed), 1)

        # Cancel action
        dlg2 = ModernDialog(
            self.root,
            title="Cancel Action",
            message="Do you want to cancel?",
            on_cancel=lambda: cancelled.append(True),
        )
        dlg2._handle_cancel()
        self.assertFalse(dlg2.result)
        self.assertEqual(len(cancelled), 1)

    def test_animations_and_easings(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        from tkblend.widgets.base import ease_out_cubic, ease_in_out_cubic, linear

        self.assertAlmostEqual(ease_out_cubic(0.0), 0.0)
        self.assertAlmostEqual(ease_out_cubic(1.0), 1.0)
        self.assertAlmostEqual(ease_in_out_cubic(0.0), 0.0)
        self.assertAlmostEqual(ease_in_out_cubic(1.0), 1.0)
        self.assertAlmostEqual(linear(0.5), 0.5)

        w = ModernWidget(self.root, width=100, height=40)
        ThemeManager.animations_enabled = True

        vals = []
        done = []
        w.animate_property(
            start_val=0.0,
            end_val=10.0,
            duration_ms=20,
            on_update=lambda v: vals.append(v),
            on_complete=lambda: done.append(True),
            easing="ease_in_out",
        )

        # Let event loop process step
        self.root.update()
        w.destroy()

    def test_dynamic_theme_propagation(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        entry = ModernEntry(self.root, placeholder="Name", is_password=True)
        dd = ModernDropdown(self.root, options=["A", "B"])
        frame = ModernFrame(self.root)

        ThemeManager.set_theme(LIGHT_THEME)
        self.assertEqual(entry._theme.name, "light")
        self.assertEqual(dd._theme.name, "light")

        ThemeManager.set_theme(DARK_THEME)
        self.assertEqual(entry._theme.name, "dark")

        entry.destroy()
        dd.destroy()
        frame.destroy()


if __name__ == "__main__":
    unittest.main()
