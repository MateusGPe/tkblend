"""
Tests for Font discovery, FontManager, and text rendering.
"""

import os
import tempfile
import time
import unittest
from tkblend import (
    Surface,
    Color,
    load_font_face,
    load_font,
    register_font,
    find_system_font,
    get_loaded_fonts,
    register_font_directory,
    set_emoji_font,
    get_emoji_font,
)
import tkblend


class TestTextAndFonts(unittest.TestCase):
    def test_load_font_face(self):
        # Non-existent font returns False
        success = load_font_face("invalid_font", "/path/to/nonexistent/font.ttf")
        self.assertFalse(success)

    def test_find_system_font(self):
        # sans-serif should be resolvable on any standard OS/Linux system
        path = find_system_font("sans-serif")
        self.assertIsNotNone(path, "sans-serif font must be resolved on standard systems")
        self.assertTrue(os.path.exists(path), f"Resolved font path does not exist: {path}")

    def test_find_system_font_generic_aliases(self):
        # Generic CSS-like font families
        for alias in ["sans-serif", "serif", "monospace", "default"]:
            path = find_system_font(alias)
            if path is not None:
                self.assertTrue(os.path.exists(path), f"Resolved path for {alias} does not exist: {path}")

    def test_find_system_font_specific_and_case_insensitive(self):
        # Try resolving specific known system fonts
        for family in ["DejaVu Sans", "Noto Sans", "Liberation Sans", "Ubuntu", "Arial"]:
            path = find_system_font(family)
            if path:
                self.assertTrue(os.path.exists(path), f"Font path for {family} does not exist: {path}")
                # Case insensitivity test
                lower_path = find_system_font(family.lower())
                self.assertEqual(path, lower_path, f"Case mismatch resolution for {family}")
                break

    def test_find_system_font_nonexistent(self):
        # Non-existent font families should return None
        path = find_system_font("absolutely_nonexistent_font_family_xyz_12345")
        self.assertIsNone(path)

    def test_loaded_fonts_registry(self):
        # Ensure get_loaded_fonts returns a list
        loaded = get_loaded_fonts()
        self.assertIsInstance(loaded, list)

        # Drawing text with a font should load and cache it
        s = Surface(100, 50)
        s.draw_text("Test", 10, 20, font_size=12.0, font_family="sans-serif")
        s.flush()

        updated_loaded = get_loaded_fonts()
        self.assertIn("sans-serif", updated_loaded)

    def test_load_and_register_font(self):
        # Find an existing font on the system
        system_font = find_system_font("sans-serif")
        if system_font and os.path.exists(system_font):
            success = register_font("my_custom_alias", system_font)
            self.assertTrue(success)
            self.assertIn("my_custom_alias", get_loaded_fonts())

            # load_font is an alias to register_font / load_font_face
            success2 = load_font("my_custom_alias_2", system_font)
            self.assertTrue(success2)
            self.assertIn("my_custom_alias_2", get_loaded_fonts())

    def test_register_font_directory(self):
        # Empty directory should return 0 loaded
        with tempfile.TemporaryDirectory() as tmpdir:
            count = register_font_directory(tmpdir)
            self.assertEqual(count, 0)

    def test_startup_and_draw_latency(self):
        # Zero startup delay: drawing text should be fast
        t0 = time.perf_counter()
        s = Surface(100, 50)
        s.draw_text("Fast text", 10, 20, font_size=12.0)
        s.flush()
        elapsed = time.perf_counter() - t0
        # Should complete in less than 50ms (typically <2ms)
        self.assertLess(elapsed, 0.5)

    def test_draw_text_alignments(self):
        s = Surface(200, 100)
        s.clear("#181825")

        # Left alignment
        s.draw_text("Left text", 10, 30, font_size=16.0, font_family="sans-serif", color="#ffffff", align="left")

        # Center alignment
        s.draw_text("Center text", 100, 60, font_size=14.0, font_family="default", color="#89b4fa", align="center")

        # Right alignment
        s.draw_text("Right text", 190, 90, font_size=12.0, font_family="sans-serif", color="#a6e3a1", align="right")

        # Empty text
        s.draw_text("", 50, 50, font_size=14.0, color="#ffffff")

        # Custom/Unknown font family fallback
        s.draw_text("Fallback font", 10, 50, font_size=14.0, font_family="nonexistent_custom_font_family")

        s.flush()

    def test_draw_text_with_emojis(self):
        s = Surface(300, 150)
        s.clear("#181825")

        # Mixed emoji and text
        s.draw_text("🌙 Dark Mode", 20, 40, font_size=16.0, font_family="sans-serif", color="#cdd6f4")
        s.draw_text("☀️ Light Mode", 20, 80, font_size=16.0, font_family="sans-serif", color="#f9e2af")

        # Multiple and standalone emojis
        s.draw_text("⚡🚀🔥", 20, 120, font_size=18.0)
        s.flush()

    def test_draw_text_alignments_with_emojis(self):
        s = Surface(300, 150)
        s.clear("#181825")

        s.draw_text("🌙 Dark", 150, 40, font_size=15.0, align="center")
        s.draw_text("☀️ Light", 280, 80, font_size=15.0, align="right")
        s.draw_text("🚀 Fast", 10, 120, font_size=15.0, align="left")
        s.flush()

    def test_active_font_getter_and_setter(self):
        # Default active font should be resolvable string
        orig_active = tkblend.get_active_font()
        self.assertIsInstance(orig_active, str)

        # Set active font to a valid family
        success = tkblend.set_active_font("monospace")
        self.assertTrue(success)
        self.assertEqual(tkblend.get_active_font(), "monospace")

        # Non-existent font family shouldn't crash
        bad_set = tkblend.set_active_font("nonexistent_random_font_xyz")
        self.assertFalse(bad_set)

        # Restore
        tkblend.set_active_font(orig_active)

    def test_internal_and_system_fonts_listing(self):
        # Internal loaded fonts list
        internal = tkblend.get_internal_fonts()
        self.assertIsInstance(internal, list)
        loaded = tkblend.get_loaded_fonts()
        self.assertEqual(internal, loaded)

        # System fonts list
        sys_fonts = tkblend.get_system_fonts()
        self.assertIsInstance(sys_fonts, list)
        self.assertGreater(len(sys_fonts), 0, "Should discover installed system fonts")

        # System fonts refresh
        sys_fonts_refreshed = tkblend.get_system_fonts(refresh=True)
        self.assertEqual(len(sys_fonts), len(sys_fonts_refreshed))

    def test_parse_font_formats(self):
        # 1. Tuples
        f1 = tkblend.parse_font(("Helvetica", 16, "bold italic"))
        self.assertEqual(f1.family, "Helvetica")
        self.assertEqual(f1.size, 16.0)
        self.assertTrue(f1.bold)
        self.assertTrue(f1.italic)
        self.assertEqual(f1.weight, 700)

        # 2. String specs
        f2 = tkblend.parse_font("Segoe UI 14 bold")
        self.assertEqual(f2.family, "Segoe UI")
        self.assertEqual(f2.size, 14.0)
        self.assertTrue(f2.bold)
        self.assertFalse(f2.italic)
        self.assertEqual(f2.weight, 700)

        # 3. Discrete kwargs
        f3 = tkblend.parse_font(font_family="Roboto", font_size=18, weight=300, italic=True)
        self.assertEqual(f3.family, "Roboto")
        self.assertEqual(f3.size, 18.0)
        self.assertEqual(f3.weight, 300)
        self.assertTrue(f3.italic)
        self.assertFalse(f3.bold)

        # 4. FontConfig copy_with
        f4 = f3.copy_with(bold=True, size=20)
        self.assertTrue(f4.bold)
        self.assertEqual(f4.size, 20.0)
        self.assertEqual(f4.family, "Roboto")

    def test_draw_text_with_weights_bold_italic(self):
        s = Surface(300, 200)
        s.clear("#1e1e2e")

        # Bold & Italic text
        s.draw_text("Bold Text", 10, 40, font_size=16, font_family="sans-serif", bold=True)
        s.draw_text("Italic Text", 10, 80, font_size=16, font_family="sans-serif", italic=True)
        s.draw_text("Bold Italic", 10, 120, font_size=16, font_family="sans-serif", bold=True, italic=True)
        s.draw_text("Light Text", 10, 160, font_size=16, font_family="sans-serif", weight=300)

        # Tuple font
        s.draw_text("Tuple Font", 150, 40, font=("DejaVu Sans", 14, "bold"))
        s.flush()

if __name__ == "__main__":
    unittest.main()



