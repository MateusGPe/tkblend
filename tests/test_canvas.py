"""
Unit tests for tkblend.BlendCanvas widget.
"""

import unittest
import tkinter as tk
from unittest.mock import MagicMock
from tkblend import BlendCanvas, Surface, Path


class TestBlendCanvas(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_canvas_init_and_properties(self):
        canvas = BlendCanvas(self.root, width=400, height=300, bg="dark")
        canvas.pack()
        self.root.update_idletasks()

        self.assertEqual(canvas.canvas_width, 400)
        self.assertEqual(canvas.canvas_height, 300)
        self.assertIsInstance(canvas.surface, Surface)
        self.assertIsInstance(canvas.photo, tk.PhotoImage)

    def test_canvas_bootstyle_and_bg_options(self):
        # bootstyle used as background
        c1 = BlendCanvas(self.root, width=100, height=100, bootstyle="primary")
        c1.pack()
        self.assertEqual(c1._bg_color, "primary")

        # 9-char hex color background
        c2 = BlendCanvas(self.root, width=100, height=100, bg="#11223388")
        c2.pack()

    def test_canvas_draw_callback(self):
        drawn = [False]

        def draw(surface: Surface):
            surface.clear("dark")
            surface.fill_circle(50, 50, 20, "primary")
            drawn[0] = True

        canvas = BlendCanvas(self.root, width=100, height=100, on_draw=draw)
        canvas.pack()
        self.root.update_idletasks()
        canvas.redraw()

        self.assertTrue(drawn[0])

        # Test set_draw_callback with redraw_now=False and True
        canvas.set_draw_callback(None, redraw_now=False)
        canvas.set_draw_callback(draw, redraw_now=True)

    def test_canvas_drawing_methods(self):
        canvas = BlendCanvas(self.root, width=200, height=150)
        canvas.pack()
        self.root.update_idletasks()

        p = Path().move_to(0, 0).line_to(10, 10)

        # Method chaining with blit=False and blit=True
        (
            canvas.clear("bg", blit=True)
            .fill_rect(10, 10, 80, 40, "primary", blit=True)
            .stroke_rect(10, 10, 80, 40, "secondary", 2.0, blit=True)
            .fill_rounded_rect(100, 10, 80, 40, 6, 6, "success", blit=True)
            .stroke_rounded_rect(100, 10, 80, 40, 6, 6, "light", 1.5, blit=True)
            .fill_circle(50, 100, 20, "info", blit=True)
            .stroke_circle(50, 100, 20, "dark", 1.0, blit=True)
            .draw_line(100, 100, 180, 100, "warning", 2.0, blit=True)
            .draw_text("Hello", 100, 120, font_size=12.0, color="fg", blit=True)
            .draw_shadow(10, 10, 80, 40, 6, 6, blit=True)
            .draw_card(20, 20, 100, 50, bg_color="light", border_color="border", blit=True)
        )
        canvas.redraw()

    def test_canvas_render_context(self):
        canvas = BlendCanvas(self.root, width=100, height=100)
        canvas.pack()
        self.root.update_idletasks()

        with canvas.render(auto_blit=True) as s:
            s.clear("bg")
            s.fill_rect(0, 0, 50, 50, "primary")

        with canvas.render(auto_blit=False) as s:
            s.clear("bg")

    def test_canvas_configure_event(self):
        canvas = BlendCanvas(self.root, width=100, height=100)
        canvas.pack()
        self.root.update_idletasks()

        event = MagicMock()
        event.width = 250
        event.height = 180
        canvas._on_configure(event)

        self.assertEqual(canvas.canvas_width, 250)
        self.assertEqual(canvas.canvas_height, 180)

    def test_canvas_theme_changed(self):
        canvas = BlendCanvas(self.root, width=100, height=100, bg="bg")
        canvas.pack()
        self.root.update_idletasks()

        canvas._on_theme_changed()

        # Fire theme change event
        self.root.event_generate("<<ThemeChanged>>")
        self.root.update_idletasks()


if __name__ == "__main__":
    unittest.main()
