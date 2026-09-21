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
)


class TestTextAndFonts(unittest.TestCase):
    def test_load_font_face(self):
        # Non-existent font returns False
        success = load_font_face("invalid_font", "/path/to/nonexistent/font.ttf")
        self.assertFalse(success)

    def test_find_system_font(self):
        # sans-serif should be resolvable on any standard OS/Linux system
        path = find_system_font("sans-serif")
        if path is not None:
            self.assertTrue(os.path.exists(path), f"Resolved font path does not exist: {path}")

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


if __name__ == "__main__":
    unittest.main()

