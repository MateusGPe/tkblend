"""
Unit and integration tests for tkblend.
"""

import unittest
import os
import sys

# Add project root to sys.path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tkinter as tk
from tkblend import (
    Surface,
    Color,
    Gradient,
    LinearGradient,
    RadialGradient,
    Path,
    BlendCanvas,
    resolve_theme_color,
    get_theme_colors,
)


class TestColor(unittest.TestCase):
    def test_color_creation(self):
        c = Color(255, 128, 64, 200)
        self.assertEqual(c.r, 255)
        self.assertEqual(c.g, 128)
        self.assertEqual(c.b, 64)
        self.assertEqual(c.a, 200)

    def test_hex_parsing(self):
        c1 = Color.from_hex("#ff8040")
        self.assertEqual(c1.r, 255)
        self.assertEqual(c1.g, 128)
        self.assertEqual(c1.b, 64)
        self.assertEqual(c1.a, 255)

        c2 = Color.from_hex("#12345678")
        self.assertEqual(c2.r, 0x12)
        self.assertEqual(c2.g, 0x34)
        self.assertEqual(c2.b, 0x56)
        self.assertEqual(c2.a, 0x78)

    def test_u32_conversion(self):
        c = Color(10, 20, 30, 255)
        u32 = c.to_u32()
        c2 = Color.from_u32(u32)
        self.assertEqual(c.r, c2.r)
        self.assertEqual(c.g, c2.g)
        self.assertEqual(c.b, c2.b)
        self.assertEqual(c.a, c2.a)


class TestSurface(unittest.TestCase):
    def test_surface_creation_and_resize(self):
        surf = Surface(200, 100)
        self.assertEqual(surf.width, 200)
        self.assertEqual(surf.height, 100)

        surf.resize(400, 300)
        self.assertEqual(surf.width, 400)
        self.assertEqual(surf.height, 300)

    def test_drawing_primitives(self):
        surf = Surface(100, 100)
        surf.clear("#1e1e2e")

        # Rectangles & Rounded Rectangles
        surf.fill_rect(10, 10, 50, 50, "#89b4fa")
        surf.stroke_rect(10, 10, 50, 50, "#ffffff", 2.0)
        surf.fill_rounded_rect(20, 20, 40, 40, 8, 8, "#f38ba8")
        surf.stroke_rounded_rect(20, 20, 40, 40, 8, 8, "#ffffff", 1.0)

        # Circles & Ellipses
        surf.fill_circle(50, 50, 20, "#a6e3a1")
        surf.stroke_circle(50, 50, 20, "#ffffff", 1.5)
        surf.fill_ellipse(50, 50, 30, 15, "#f9e2af")
        surf.stroke_ellipse(50, 50, 30, 15, "#ffffff", 1.0)

        # Lines
        surf.draw_line(0, 0, 100, 100, "#fab387", 2.0)

        # Text
        surf.draw_text("Test", 10, 50, font_size=14, color="#ffffff")

        # Shadows & Cards
        surf.draw_shadow(10, 10, 60, 40, 8, 8, blur_radius=8.0, shadow_color="#00000088")
        surf.draw_card(10, 10, 60, 40, rx=8, ry=8, bg_color="#313244", border_color="#cdd6f4", border_width=1.0)

        surf.flush()

    def test_gradients(self):
        surf = Surface(100, 100)
        grad = LinearGradient(0, 0, 100, 100)
        grad.add_stop(0.0, "#ff0000")
        grad.add_stop(1.0, "#0000ff")
        surf.fill_rect(0, 0, 100, 100, grad)

        rad_grad = RadialGradient(50, 50, 0, 50, 50, 50)
        rad_grad.add_stop(0.0, "#ffff00")
        rad_grad.add_stop(1.0, "#00ff00")
        surf.fill_circle(50, 50, 40, rad_grad)
        surf.flush()

    def test_path(self):
        surf = Surface(100, 100)
        p = Path()
        p.move_to(10, 10).line_to(90, 10).line_to(50, 90).close()
        surf.fill_path(p, "#fab387")
        surf.stroke_path(p, "#ffffff", 2.0)
        surf.flush()


class TestTkinterIntegration(unittest.TestCase):
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

    def test_blit_to_photo(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        photo = tk.PhotoImage(master=self.root, width=64, height=64)
        surf = Surface(64, 64)
        surf.clear("#ff0000")
        surf.fill_circle(32, 32, 20, "#00ff00")
        surf.blit(photo)

    def test_blend_canvas_widget(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        def draw(s: Surface):
            s.clear("#181825")
            s.fill_rounded_rect(10, 10, 80, 40, 8, 8, "#89b4fa")

        canvas = BlendCanvas(self.root, width=100, height=60, on_draw=draw)
        canvas.redraw()
        canvas.destroy()


if __name__ == "__main__":
    unittest.main()
