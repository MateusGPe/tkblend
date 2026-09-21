"""
Comprehensive tests for tkblend open-source architecture enhancements:
- Color math & RampColor 50-950 tint/shade ramps (ttkbootstrap pattern)
- Extended Theme Presets (Nord, Dracula, Tokyo-Night) & JSON serialization
- TTK StyleBuilder with durable user options layer
- High-DPI ScalingTracker logical-to-physical conversion
- ModernWidget .configure() / .cget() / dict subscripting protocol parity (CustomTkinter pattern)
"""

import os
import tempfile
import unittest
import tkinter as tk
from tkinter import ttk

from tkblend import (
    Theme,
    DARK_THEME,
    LIGHT_THEME,
    NORD_THEME,
    DRACULA_THEME,
    TOKYO_NIGHT_THEME,
    RampColor,
    ThemeManager,
    apply_ttk_theme,
    apply_theme,
    mix_colors,
    tint,
    shade,
    lighten_color,
    darken_color,
    relative_luminance,
    contrast_ratio,
    accent_on_color,
    is_dark_color,
    StyleBuilderTTK,
    DURABLE_STYLE_OPTIONS,
    ScalingTracker,
    ModernButton,
    ModernSwitch,
    ModernSlider,
    ModernSegmentedControl,
    ModernEntry,
    ModernDropdown,
    ModernFrame,
    ModernCard,
    ModernProgressBar,
    ModernBadge,
    ModernAvatar,
    ModernLabel,
    ModernToast,
)


class TestColorMathAndRamps(unittest.TestCase):
    def test_mix_and_tints(self):
        white = "#ffffff"
        black = "#000000"
        gray = mix_colors(white, black, 0.5)
        self.assertEqual(gray.lower(), "#808080")

        c_tint = tint("#000000", 0.5)
        self.assertEqual(c_tint.lower(), "#808080")

        c_shade = shade("#ffffff", 0.5)
        self.assertEqual(c_shade.lower(), "#808080")

    def test_luminance_and_contrast(self):
        lum_white = relative_luminance("#ffffff")
        lum_black = relative_luminance("#000000")
        self.assertAlmostEqual(lum_white, 1.0, places=2)
        self.assertAlmostEqual(lum_black, 0.0, places=2)

        ratio = contrast_ratio("#ffffff", "#000000")
        self.assertGreater(ratio, 20.0)

        self.assertTrue(is_dark_color("#11111b"))
        self.assertFalse(is_dark_color("#ffffff"))

        # Test accent on-color logic
        on_dark = accent_on_color("#11111b")
        self.assertEqual(on_dark, "#ffffff")
        on_light = accent_on_color("#ffffff")
        self.assertEqual(on_light, "#11111b")

    def test_ramp_color(self):
        blue = RampColor("#1e66f5")
        self.assertEqual(str(blue), "#1e66f5")
        self.assertEqual(blue[500], "#1e66f5")
        self.assertTrue(blue[300].startswith("#"))
        self.assertTrue(blue[700].startswith("#"))
        # Verify 300 is lighter than 700
        self.assertGreater(relative_luminance(blue[300]), relative_luminance(blue[700]))
        # Standard string slicing still works
        self.assertEqual(blue[:2], "#1")


class TestThemePresetsAndSerialization(unittest.TestCase):
    def test_presets_exist_and_valid(self):
        for t in (DARK_THEME, LIGHT_THEME, NORD_THEME, DRACULA_THEME, TOKYO_NIGHT_THEME):
            self.assertIsInstance(t.primary, RampColor)
            self.assertTrue(t.primary.startswith("#"))
            self.assertTrue(t.bg_window.startswith("#"))
            self.assertIn(t.name, ThemeManager.get_registered_themes())

    def test_theme_dict_and_json_roundtrip(self):
        d = NORD_THEME.to_dict()
        self.assertEqual(d["name"], "nord")
        reconstructed = Theme.from_dict(d)
        self.assertEqual(reconstructed.name, "nord")
        self.assertEqual(reconstructed.primary, NORD_THEME.primary)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            ThemeManager.export_theme_json(DRACULA_THEME, tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            loaded = ThemeManager.load_theme_json(tmp_path)
            self.assertEqual(loaded.name, "dracula")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestTTKStyleBuilderDurableOptions(unittest.TestCase):
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
            try:
                cls.root.destroy()
            except Exception:
                pass

    def test_durable_style_options(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        builder = StyleBuilderTTK()
        builder.set_user_option("primary.TButton", padding=(16, 8))
        style = builder.apply(DARK_THEME)
        self.assertIsNotNone(style)


class TestScalingTracker(unittest.TestCase):
    def test_scaling_conversion(self):
        ScalingTracker.set_widget_scaling(1.0)
        self.assertEqual(ScalingTracker.scale(100), 100)
        self.assertEqual(ScalingTracker.scale([10, 20]), [10, 20])

        ScalingTracker.set_widget_scaling(1.5)
        self.assertEqual(ScalingTracker.scale(100), 150)
        self.assertEqual(ScalingTracker.scale([10, 20]), [15, 30])
        ScalingTracker.set_widget_scaling(1.0)


class TestWidgetConfigurationProtocol(unittest.TestCase):
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
            try:
                cls.root.destroy()
            except Exception:
                pass

    def test_button_configure_cget(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        btn = ModernButton(self.root, text="Initial", variant="secondary")
        self.assertEqual(btn.cget("text"), "Initial")
        self.assertEqual(btn["variant"], "secondary")

        btn.configure(text="Updated", variant="success")
        self.assertEqual(btn.cget("text"), "Updated")
        self.assertEqual(btn.cget("variant"), "success")

        btn["corner_radius"] = 14
        self.assertEqual(btn["corner_radius"], 14)
        btn.destroy()

    def test_entry_configure_cget(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        entry = ModernEntry(self.root, placeholder="Search...")
        self.assertEqual(entry.cget("placeholder"), "Search...")
        entry.configure(placeholder="Filter...", is_error=True)
        self.assertEqual(entry.cget("placeholder"), "Filter...")
        self.assertTrue(entry.cget("is_error"))
        entry.destroy()

    def test_slider_configure_cget(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        slider = ModernSlider(self.root, min_val=0, max_val=100, value=30)
        self.assertEqual(slider.cget("value"), 30.0)
        slider.configure(value=80.0)
        self.assertEqual(slider.get(), 80.0)
        slider.destroy()

    def test_dropdown_configure_cget(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        dd = ModernDropdown(self.root, options=["A", "B", "C"], selected_index=0)
        self.assertEqual(dd.get(), "A")
        dd.configure(selected_index=2)
        self.assertEqual(dd.get(), "C")
        dd.destroy()

    def test_frame_and_card_configure_cget(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        card = ModernCard(self.root, title="Old Title")
        self.assertEqual(card.cget("title"), "Old Title")
        card.configure(title="New Title", subtitle="Subtitle", corner_radius=16)
        self.assertEqual(card.cget("title"), "New Title")
        self.assertEqual(card.cget("subtitle"), "Subtitle")
        self.assertEqual(card.cget("corner_radius"), 16)
        card.destroy()

    def test_progressbar_configure_cget(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        pbar = ModernProgressBar(self.root, value=25.0, variant="primary")
        self.assertEqual(pbar.cget("value"), 25.0)
        pbar.configure(value=75.0, variant="success")
        self.assertEqual(pbar.cget("value"), 75.0)
        self.assertEqual(pbar.cget("variant"), "success")
        pbar.step(10.0)
        self.assertEqual(pbar.cget("value"), 85.0)
        pbar.destroy()


if __name__ == "__main__":
    unittest.main()
