"""
Comprehensive test suite for tkblend modern UI widget library.
"""

import unittest
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

from tkblend import (
    Theme,
    DARK_THEME,
    LIGHT_THEME,
    ThemeManager,
    apply_ttk_theme,
    apply_theme,
    detect_system_theme,
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
    ModernLabel,
    ModernDialog,
    show_alert,
)
from tkblend.widgets.base import _resolve_parent_bg


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
        if self.root:
            ThemeManager.bind_root(self.root)

    def tearDown(self):
        if self.root:
            ThemeManager.unbind_root(self.root)

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

    def test_custom_theme_registry(self):
        custom_theme = Theme(name="custom_neon", primary="#00ffcc", bg_window="#000011")
        ThemeManager.register_theme("custom_neon", custom_theme)

        registered = ThemeManager.get_registered_themes()
        self.assertIn("custom_neon", registered)

        ThemeManager.set_theme("custom_neon")
        self.assertEqual(ThemeManager.get_theme().primary, "#00ffcc")

        # Invalid registrations
        with self.assertRaises(ValueError):
            ThemeManager.register_theme("", custom_theme)

        with self.assertRaises(TypeError):
            ThemeManager.register_theme("bad", 123)  # type: ignore

        # Cannot unregister builtin
        with self.assertRaises(ValueError):
            ThemeManager.unregister_theme("dark")

        ThemeManager.unregister_theme("custom_neon")
        self.assertNotIn("custom_neon", ThemeManager.get_registered_themes())

    def test_parent_bg_auto_resolution(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        # Direct on root -> resolves to bg_window
        btn_root = ModernButton(self.root, text="On Root")
        self.assertEqual(btn_root._parent_bg, DARK_THEME.bg_window)

        # Inside ModernCard -> resolves to bg_card
        card = ModernCard(self.root, bg_color="#223344")
        btn_card = ModernButton(card, text="On Card")
        self.assertEqual(btn_card._parent_bg, "#223344")

        # Inside nested tk.Frame with custom bg
        custom_frame = tk.Frame(self.root, bg="#556677")
        btn_frame = ModernButton(custom_frame, text="On Frame")
        self.assertEqual(btn_frame._parent_bg, "#556677")

        # Explicit parent_bg override takes priority
        btn_explicit = ModernButton(card, text="Explicit", parent_bg="#990000")
        self.assertEqual(btn_explicit._parent_bg, "#990000")

        # Check resolution utility directly
        self.assertEqual(_resolve_parent_bg(None, None, DARK_THEME), DARK_THEME.bg_window)
        self.assertEqual(_resolve_parent_bg(self.root, "#123456", DARK_THEME), "#123456")

        btn_root.destroy()
        btn_card.destroy()
        card.destroy()
        btn_frame.destroy()
        custom_frame.destroy()
        btn_explicit.destroy()

    def test_dynamic_theme_propagation_and_custom_color_preservation(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        # Button with default primary color vs button with custom color
        btn_default = ModernButton(self.root, text="Default")
        btn_custom = ModernButton(self.root, text="Custom", bg_color="#ff0088")

        # In Dark theme
        self.assertEqual(btn_default._resolve_colors()[0], DARK_THEME.primary)
        self.assertEqual(btn_custom._resolve_colors()[0], "#ff0088")

        # Switch to Light theme
        ThemeManager.set_theme(LIGHT_THEME)
        self.assertEqual(btn_default._resolve_colors()[0], LIGHT_THEME.primary)
        self.assertEqual(btn_custom._resolve_colors()[0], "#ff0088")  # Preserved!

        # Switch widget with custom on_color
        sw = ModernSwitch(self.root, on_color="#ffcc00")
        sw.render()
        self.assertEqual(sw._custom_on_color, "#ffcc00")

        btn_default.destroy()
        btn_custom.destroy()
        sw.destroy()

    def test_ttk_theming_and_root_binding(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        # Test apply_ttk_theme
        style = apply_ttk_theme(DARK_THEME)
        self.assertIsNotNone(style)

        # Test apply_theme recursive tree
        test_frame = tk.Frame(self.root)
        test_lbl = tk.Label(test_frame, text="Hello")
        test_entry = tk.Entry(test_frame)
        test_frame.pack()
        test_lbl.pack()
        test_entry.pack()

        apply_theme(test_frame, DARK_THEME, recurse=True)
        self.assertEqual(test_lbl.cget("bg"), DARK_THEME.bg_window)
        self.assertEqual(test_entry.cget("bg"), DARK_THEME.bg_input)

        # Test ThemeManager.bind_root
        ThemeManager.bind_root(self.root)
        ThemeManager.set_theme(LIGHT_THEME)
        self.assertEqual(test_lbl.cget("bg"), LIGHT_THEME.bg_window)

        ThemeManager.unbind_root(self.root)
        test_frame.destroy()

    def test_system_theme_detection(self):
        detected = detect_system_theme()
        self.assertIn(detected, ("dark", "light"))

        ThemeManager.detect_and_apply_system_theme()
        self.assertIn(ThemeManager.get_theme().name, ("dark", "light"))

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

    def test_card_content_and_contextual_theming(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        card = ModernCard(self.root, title="Card Title", subtitle="Subtitle")
        self.assertIsNotNone(card.content)
        self.assertEqual(card.content.cget("bg"), str(card._bg_color))

        # Standard Tk label inside card.content
        lbl_in_card = tk.Label(card.content, text="Inside Card")
        lbl_on_root = tk.Label(self.root, text="On Root")

        apply_theme(self.root, DARK_THEME, recurse=True)
        self.assertEqual(lbl_on_root.cget("bg"), DARK_THEME.bg_window)
        self.assertEqual(lbl_in_card.cget("bg"), DARK_THEME.bg_card)

        # Switch to Light Theme
        apply_theme(self.root, LIGHT_THEME, recurse=True)
        self.assertEqual(lbl_on_root.cget("bg"), LIGHT_THEME.bg_window)
        self.assertEqual(lbl_in_card.cget("bg"), LIGHT_THEME.bg_card)

        # Modern button in card.content
        btn_in_card = ModernButton(card.content, text="Card Button")
        self.assertEqual(btn_in_card._parent_bg, LIGHT_THEME.bg_card)

        btn_in_card.destroy()
        lbl_in_card.destroy()
        lbl_on_root.destroy()
        card.destroy()

    def test_additional_coverage_paths(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        # show_alert
        alert = show_alert(self.root, title="Alert", message="Notice message", wait=False)
        alert._handle_confirm()
        self.assertTrue(alert.result)

        # Dropdown popup opening, hovering, selection
        sel_res = []
        dd = ModernDropdown(self.root, options=["Alpha", "Beta"], on_select=lambda i, v: sel_res.append(v))
        self.assertEqual(dd.selected_value, "Alpha")
        dd._open_popup()
        self.assertTrue(dd._is_open)
        self.assertIsNotNone(dd._popup_window)
        # Select item
        dd._select_item(1)
        self.assertFalse(dd._is_open)
        self.assertEqual(dd.selected_value, "Beta")
        self.assertIn("Beta", sel_res)
        # Toggle open
        dd._on_toggle_open(SimpleNamespace(x=10, y=10))
        dd._close_popup()
        dd.destroy()

        # ModernScrollableFrame mousewheel
        s_frame = ModernScrollableFrame(self.root, width=200, height=150)
        s_frame._on_mousewheel(SimpleNamespace(num=5, delta=-120))
        s_frame._on_mousewheel(SimpleNamespace(num=4, delta=120))
        s_frame._bind_mousewheel()
        s_frame._unbind_mousewheel()
        s_frame.destroy()

        # ModernWidget base properties
        w = ModernWidget(self.root, width=80, height=30)
        w.theme = LIGHT_THEME
        self.assertEqual(w.theme.name, "light")
        w.is_disabled = True
        self.assertTrue(w.is_disabled)
        w.is_disabled = False
        w.resolve_parent_bg()
        dummy_ev = SimpleNamespace(x=10, y=10, width=80, height=30)
        w._on_enter(dummy_ev)
        w._on_press(dummy_ev)
        w._on_release(dummy_ev)
        w._on_leave(dummy_ev)
        w._on_map(dummy_ev)
        w.destroy()

        # ModernEntry placeholder hiding/showing
        entry = ModernEntry(self.root, placeholder="Type here...", show="")
        entry._on_focus_in(SimpleNamespace())
        self.assertFalse(entry._placeholder_active)
        entry._on_focus_out(SimpleNamespace())
        self.assertTrue(entry._placeholder_active)
        entry.destroy()

        # ModernAccordion and AccordionItem toggle & theming
        accordion = ModernAccordion(self.root)
        sec = accordion.add_section("Settings", is_expanded=False)
        self.assertIsNotNone(sec)
        item = accordion._items[0]
        item.toggle()
        self.assertTrue(item._is_expanded)
        item.toggle()
        self.assertFalse(item._is_expanded)
        accordion.destroy()

        # _resolve_parent_bg branch testing
        dummy_parent = SimpleNamespace(_bg_color="#123456", _custom_bg_color="#654321", _card_bg="#abcdef", _parent_bg="#fedcba", master=None)
        self.assertEqual(_resolve_parent_bg(dummy_parent, None, DARK_THEME), "#123456")
        dummy_parent2 = SimpleNamespace(_custom_bg_color="#654321", master=None)
        self.assertEqual(_resolve_parent_bg(dummy_parent2, None, DARK_THEME), "#654321")
        dummy_parent3 = SimpleNamespace(_card_bg="#abcdef", master=None)
        self.assertEqual(_resolve_parent_bg(dummy_parent3, None, DARK_THEME), "#abcdef")
        dummy_parent4 = SimpleNamespace(_parent_bg="#fedcba", master=None)
        self.assertEqual(_resolve_parent_bg(dummy_parent4, None, DARK_THEME), "#fedcba")

        # Standard Tk widgets theming (Text, Listbox, Scrollbar, Canvas, Button)
        box = tk.Frame(self.root)
        txt = tk.Text(box)
        lb = tk.Listbox(box)
        sb = tk.Scrollbar(box)
        cv = tk.Canvas(box)
        btn = tk.Button(box)
        apply_theme(box, DARK_THEME, recurse=True)
        self.assertEqual(txt.cget("bg"), DARK_THEME.bg_input)
        self.assertEqual(lb.cget("bg"), DARK_THEME.bg_input)
        self.assertEqual(cv.cget("bg"), DARK_THEME.bg_window)
        self.assertEqual(btn.cget("bg"), DARK_THEME.secondary)
        box.destroy()

        # ModernWidget disabled animations & zero duration
        ThemeManager.animations_enabled = False
        w2 = ModernWidget(self.root)
        anim_done = []
        w2.animate_property(0, 10, duration_ms=0, on_update=lambda v: None, on_complete=lambda: anim_done.append(True))
        self.assertEqual(len(anim_done), 1)
        w2.destroy()
        ThemeManager.animations_enabled = True

        # ModernEntry and ModernDropdown configure and theme change
        entry2 = ModernEntry(self.root, bg_color="#334455")
        entry2._on_theme_changed(LIGHT_THEME)
        entry2._on_configure(SimpleNamespace(width=250, height=50))
        entry2.destroy()

        dd2 = ModernDropdown(self.root, options=["One", "Two"])
        dd2._on_theme_changed(LIGHT_THEME)
        dd2._on_configure(SimpleNamespace(width=220, height=45))
        dd2.destroy()

    def test_modern_label(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        # Test various variants and colors
        lbl_default = ModernLabel(self.root, text="Default Text", variant="default")
        lbl_default.render()
        self.assertEqual(lbl_default.text, "Default Text")

        lbl_default.text = "Updated Text"
        self.assertEqual(lbl_default.text, "Updated Text")
        lbl_default.set_text("Set Text")
        self.assertEqual(lbl_default.text, "Set Text")

        lbl_muted = ModernLabel(self.root, text="Muted Text", variant="muted")
        self.assertEqual(lbl_muted._resolve_text_color(), DARK_THEME.text_muted)
        lbl_muted.render()

        lbl_heading = ModernLabel(self.root, text="Heading Text", variant="heading")
        self.assertEqual(lbl_heading._resolve_text_color(), DARK_THEME.primary)
        lbl_heading.render()

        lbl_danger = ModernLabel(self.root, text="Danger Text", variant="danger")
        self.assertEqual(lbl_danger._resolve_text_color(), DARK_THEME.danger)

        lbl_success = ModernLabel(self.root, text="Success Text", variant="success")
        self.assertEqual(lbl_success._resolve_text_color(), DARK_THEME.success)

        lbl_warning = ModernLabel(self.root, text="Warning Text", variant="warning")
        self.assertEqual(lbl_warning._resolve_text_color(), DARK_THEME.warning)

        lbl_custom = ModernLabel(self.root, text="Custom Color", color="#ff00ff", align="center")
        self.assertEqual(lbl_custom._resolve_text_color(), "#ff00ff")
        lbl_custom.render()

        lbl_right = ModernLabel(self.root, text="Right Aligned", align="right")
        lbl_right.render()

        # Theme change propagation
        lbl_default._on_theme_changed(LIGHT_THEME)
        self.assertEqual(lbl_default._theme.name, "light")

        lbl_default.destroy()
        lbl_muted.destroy()
        lbl_heading.destroy()
        lbl_danger.destroy()
        lbl_success.destroy()
        lbl_warning.destroy()
        lbl_custom.destroy()
        lbl_right.destroy()

    def test_widget_auto_sizing(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        long_text = "This is a very long checkbox label that should never be truncated"
        chk = ModernCheckbox(self.root, text=long_text)
        self.assertGreater(chk._widget_w, 160)
        chk.destroy()

        radio = ModernRadioButton(self.root, text=long_text)
        self.assertGreater(radio._widget_w, 150)
        radio.destroy()

    def test_theme_toggle_widget_size_stability(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        self.root.deiconify()
        try:
            box = tk.Frame(self.root)
            box.pack(side=tk.RIGHT, fill=tk.Y)

            badge = ModernBadge(box, text="Theme: DARK", dot=True)
            badge.pack(side=tk.LEFT, padx=(0, 12), pady=8)

            btn = ModernButton(box, text="Toggle Theme", width=130, height=36)
            btn.pack(side=tk.LEFT, pady=4)

            self.root.update()
            self.assertEqual(btn.winfo_width(), 130)
            self.assertEqual(btn.winfo_reqwidth(), 130)

            for _ in range(6):
                ThemeManager.toggle_theme()
                badge.set_text(f"Theme: {ThemeManager.get_theme().name.upper()}")
                self.root.update()
                self.assertEqual(btn.winfo_width(), 130)
                self.assertEqual(btn._widget_w, 130)
                self.assertEqual(btn._photo.width(), 130)
                self.assertEqual(btn.winfo_reqwidth(), 130)

            box.destroy()
        finally:
            self.root.withdraw()

    def test_radiogroup_and_header_labels_theme_propagation(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        ThemeManager.set_theme(DARK_THEME)
        card = ModernCard(self.root, title="Controls Card")
        card.pack()
        rgroup = ModernRadioGroup(card.content, options=["Opt 1", "Opt 2"], selected_value="Opt 1")
        rgroup.pack()

        header_frame = tk.Frame(self.root, bg=DARK_THEME.bg_window)
        header_frame.pack()
        lbl = ModernLabel(header_frame, text="Header Title", variant="heading")
        lbl.pack()

        self.root.update()
        self.assertEqual(rgroup._parent_bg, DARK_THEME.bg_card)
        self.assertEqual(rgroup._buttons[0]._parent_bg, DARK_THEME.bg_card)

        # Toggle to LIGHT
        ThemeManager.set_theme(LIGHT_THEME)
        apply_theme(self.root, LIGHT_THEME)
        self.root.update()

        self.assertEqual(rgroup._parent_bg, LIGHT_THEME.bg_card)
        self.assertEqual(rgroup._buttons[0]._parent_bg, LIGHT_THEME.bg_card)
        self.assertEqual(lbl._parent_bg, LIGHT_THEME.bg_window)

        card.destroy()
        header_frame.destroy()



if __name__ == "__main__":
    unittest.main()
