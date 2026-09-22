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

    def test_badge_resize_preservation(self):
        import tkinter as tk
        from tkblend import Badge
        root = tk.Tk()
        try:
            badge = Badge(root, text="Production Ready", variant="success", dot=True)
            initial_w = badge._preferred_width
            self.assertGreaterEqual(initial_w, 80)

            # Simulate configure event squeezing width
            class MockEvent:
                width = 30
                height = 24
            badge._on_configure(MockEvent())

            # Verify badge clamped to preferred width and did not permanently shrink
            self.assertGreaterEqual(badge.canvas_width, initial_w)

            # Enlarge event
            class LargeEvent:
                width = 200
                height = 30
            badge._on_configure(LargeEvent())
            self.assertEqual(badge.canvas_width, 200)
            self.assertEqual(badge.canvas_height, 30)
        finally:
            root.destroy()

    def test_card_class_hierarchy_and_panedwindow(self):
        import tkinter as tk
        from tkinter import ttk
        from tkblend import Card, is_inside_card
        root = tk.Tk()
        try:
            card = Card(root)
            self.assertEqual(card.winfo_class(), "Card")
            lbl = ttk.Label(card, text="Inside Card")
            self.assertTrue(is_inside_card(lbl))

            paned = ttk.Panedwindow(root, orient="horizontal")
            pane_card = Card(paned)
            btn = ttk.Button(pane_card, text="Test")
            self.assertTrue(is_inside_card(btn))
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
