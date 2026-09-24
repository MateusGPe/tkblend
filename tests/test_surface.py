"""
Comprehensive tests for Surface and Native Surface rendering operations.
"""

import unittest
from tkblend import (
    Surface,
    Color,
    Path,
    LinearGradient,
    RadialGradient,
)
from tkblend._tkblend import (
    Surface as NativeSurface,
    Path as NativePath,
    Gradient as NativeGradient,
    COMP_OP_SRC_OVER,
    COMP_OP_SRC_COPY,
    COMP_OP_PLUS,
    COMP_OP_MULTIPLY,
    COMP_OP_SCREEN,
    COMP_OP_CLEAR,
    COMP_OP_XOR,
)


class TestSurface(unittest.TestCase):
    def test_surface_init_and_resize(self):
        s = Surface(150, 120)
        self.assertEqual(s.width, 150)
        self.assertEqual(s.height, 120)
        self.assertIsInstance(s.native, NativeSurface)

        # Zero or negative clamps to at least 1
        s_min = Surface(0, -5)
        self.assertEqual(s_min.width, 1)
        self.assertEqual(s_min.height, 1)

        # Resize to same size (no-op fast path)
        s.resize(150, 120)
        self.assertEqual(s.width, 150)
        self.assertEqual(s.height, 120)

        # Resize to new size
        s.resize(300, 200)
        self.assertEqual(s.width, 300)
        self.assertEqual(s.height, 200)

        # Resize to 0
        s.resize(0, 0)
        self.assertEqual(s.width, 1)
        self.assertEqual(s.height, 1)

    def test_clear_and_clear_rect(self):
        s = Surface(100, 100)
        # Transparent clear (a=0)
        s.clear("#00000000")
        s.clear(Color(0, 0, 0, 0))

        # Solid clear
        s.clear("#181825")
        s.clear((255, 128, 64, 255))
        s.clear_rect(10, 10, 30, 30)

    def test_transformations_and_context_manager(self):
        s = Surface(100, 100)
        s.save()
        s.translate(10.0, 20.0)
        s.scale(1.5, 1.5)
        s.rotate(0.5)
        s.reset_transform()
        s.restore()

        with s.saved():
            s.translate(5.0, 5.0)
            s.rotate(1.0)
            s.fill_rect(0, 0, 20, 20, "#ff0000")

    def test_clipping(self):
        s = Surface(100, 100)
        s.clip_rect(10, 10, 80, 80)
        s.fill_circle(50, 50, 40, "#00ff00")
        s.reset_clip()

        s.clip_rounded_rect(5, 5, 90, 90, 8, 8)
        s.fill_rect(0, 0, 100, 100, "#0000ff")
        s.reset_clip()

    def test_comp_op_and_global_alpha(self):
        s = Surface(100, 100)
        s.set_comp_op(COMP_OP_SRC_OVER)
        s.set_comp_op(COMP_OP_SRC_COPY)
        s.set_comp_op(COMP_OP_PLUS)
        s.set_comp_op(COMP_OP_MULTIPLY)
        s.set_comp_op(COMP_OP_SCREEN)
        s.set_comp_op(COMP_OP_CLEAR)
        s.set_comp_op(COMP_OP_XOR)

        # Clamping global alpha
        s.set_global_alpha(0.5)
        s.set_global_alpha(-0.2)  # Clamped to 0.0
        s.set_global_alpha(1.5)   # Clamped to 1.0

    def test_rectangles_and_rounded_rects(self):
        s = Surface(200, 200)

        # Solid fills & strokes
        s.fill_rect(10, 10, 50, 40, "#ff8000")
        s.stroke_rect(10, 10, 50, 40, "#ffffff", 2.0)

        s.fill_rounded_rect(70, 10, 50, 40, 6, 6, (120, 200, 80))
        s.stroke_rounded_rect(70, 10, 50, 40, 6, 6, "#ffffff", 1.5)

        # Gradient fills
        lg = LinearGradient(0, 0, 100, 100).add_stop(0.0, "#ff0000").add_stop(1.0, "#0000ff")
        s.fill_rect(0, 0, 100, 100, lg)
        s.fill_rounded_rect(10, 10, 80, 80, 10, 10, lg)

        rg = RadialGradient(50, 50, 0, 50, 50, 40).add_stop(0.0, "#ffff00").add_stop(1.0, "#ff00ff")
        s.fill_rect(0, 0, 100, 100, rg)
        s.fill_rounded_rect(10, 10, 80, 80, 10, 10, rg)

    def test_circles_and_ellipses(self):
        s = Surface(100, 100)
        s.fill_circle(50, 50, 30, "#89b4fa")
        s.stroke_circle(50, 50, 30, "#ffffff", 2.0)

        lg = LinearGradient(20, 20, 80, 80).add_stop(0.0, "#f38ba8").add_stop(1.0, "#a6e3a1")
        s.fill_circle(50, 50, 25, lg)

        s.fill_ellipse(50, 50, 40, 20, "#fab387")
        s.stroke_ellipse(50, 50, 40, 20, "#ffffff", 1.0)

    def test_lines_and_paths(self):
        s = Surface(100, 100)
        s.draw_line(0, 0, 100, 100, "#f9e2af", 3.0)

        # Path wrapper
        p = Path().move_to(10, 10).line_to(90, 50).line_to(10, 90).close()
        s.fill_path(p, "#cba6f7")
        s.stroke_path(p, "#ffffff", 1.5)

        # Gradient on path
        lg = LinearGradient(0, 0, 100, 100).add_stop(0.0, "#ffffff").add_stop(1.0, "#000000")
        s.fill_path(p, lg)

        # NativePath direct
        np = NativePath()
        np.add_circle(50, 50, 20)
        s.fill_path(np, "#a6e3a1")
        s.stroke_path(np, "#000000", 2.0)
        s.fill_path(np, lg)

    def test_shadow_and_card(self):
        s = Surface(300, 200)
        s.clear("#11111b")

        # Zero alpha shadow (noop branch)
        s.draw_shadow(10, 10, 100, 50, 8, 8, shadow_color="#00000000")

        # Active soft drop shadows
        s.draw_shadow(20, 20, 120, 60, 12, 12, blur_radius=10.0, spread=2.0, offset_x=0.0, offset_y=4.0, shadow_color="#00000077")

        # Card with border and shadow
        s.draw_card(
            x=20, y=20, w=150, h=80, rx=10, ry=10,
            bg_color="#1e1e2e", border_color="#89b4fa", border_width=1.5,
            shadow_blur=8.0, shadow_spread=0.0, shadow_offset_x=0.0, shadow_offset_y=3.0,
            shadow_color="#00000066"
        )

        # Card without border or shadow
        s.draw_card(
            x=50, y=50, w=60, h=40, rx=5, ry=5,
            bg_color="#313244", border_color="#00000000", border_width=0.0,
            shadow_blur=0.0, shadow_color="#00000000"
        )

    def test_buffer_access_and_flush(self):
        s = Surface(64, 48)
        s.clear("#ff112233")
        s.flush()

        buf = s.get_buffer()
        self.assertIsInstance(buf, memoryview)
        self.assertEqual(len(buf), 64 * 48 * 4)

        # Native surface methods
        ns = s.native
        self.assertGreater(ns.stride(), 0)
        self.assertEqual(ns.size_in_bytes(), 64 * 48 * 4)


if __name__ == "__main__":
    unittest.main()
