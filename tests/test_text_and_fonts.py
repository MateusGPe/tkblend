"""
Tests for Font discovery, FontManager, and text rendering.
"""

import unittest
from tkblend import Surface, Color
from tkblend._tkblend import load_font_face


class TestTextAndFonts(unittest.TestCase):
    def test_load_font_face(self):
        # Non-existent font returns False
        success = load_font_face("invalid_font", "/path/to/nonexistent/font.ttf")
        self.assertFalse(success)

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
