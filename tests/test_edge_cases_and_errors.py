"""
Tests for edge cases, error handling, and stress conditions.
"""

import unittest
from tkblend import Surface, Color, Path, LinearGradient, RadialGradient


class TestEdgeCasesAndErrors(unittest.TestCase):
    def test_extreme_and_negative_dimensions(self):
        s = Surface(-100, -200)
        self.assertEqual(s.width, 1)
        self.assertEqual(s.height, 1)

        s.resize(-50, -50)
        self.assertEqual(s.width, 1)
        self.assertEqual(s.height, 1)

        s.resize(1000, 1)
        self.assertEqual(s.width, 1000)
        self.assertEqual(s.height, 1)

    def test_rapid_resize_stress_loop(self):
        s = Surface(50, 50)
        for dim in range(10, 150, 10):
            s.resize(dim, dim)
            s.clear("#181825")
            s.fill_rect(0, 0, dim, dim, "#89b4fa")
            s.flush()

    def test_empty_paths_and_resets(self):
        s = Surface(50, 50)
        p = Path()
        s.fill_path(p, "#ffffff")
        s.stroke_path(p, "#000000")

        p.clear().reset()
        s.fill_path(p, "#ffffff")

    def test_out_of_bounds_rendering_coordinates(self):
        s = Surface(50, 50)
        # Primitives completely outside surface bounds
        s.fill_rect(-200, -200, 50, 50, "#ffffff")
        s.stroke_rect(500, 500, 100, 100, "#ff0000")
        s.fill_circle(-100, -100, 50, "#00ff00")
        s.stroke_circle(1000, 1000, 50, "#0000ff")
        s.fill_ellipse(-50, -50, 20, 20, "#ffff00")
        s.draw_line(-100, -100, 500, 500, "#ffffff")
        s.draw_text("Outside", -500, -500)
        s.draw_shadow(-100, -100, 200, 200, 10, 10, blur_radius=20.0)
        s.flush()

    def test_decorator_class_hierarchy_and_panedwindow(self):
        import tkinter as tk
        from tkblend import BlendDecorator, is_inside_card
        root = tk.Tk()
        try:
            dec = BlendDecorator(root)
            self.assertIsInstance(dec, BlendDecorator)
            lbl = tk.Label(dec, text="Inside Decorator")
            self.assertTrue(is_inside_card(lbl))

            paned = tk.PanedWindow(root, orient="horizontal")
            pane_dec = BlendDecorator(paned)
            btn = tk.Button(pane_dec, text="Test")
            self.assertTrue(is_inside_card(btn))
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
