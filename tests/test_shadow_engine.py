"""
Tests for fast 3-pass box blur, shadow cache, and ShadowEngine.
"""

import unittest
from tkblend import Surface, Color


class TestShadowEngine(unittest.TestCase):
    def test_shadow_blur_radii_and_spread(self):
        s = Surface(400, 400)
        s.clear("#11111b")

        # Zero blur
        s.draw_shadow(10, 10, 50, 50, 8, 8, blur_radius=0.0, shadow_color="#00000088")

        # Small and large blur
        s.draw_shadow(20, 20, 100, 60, 12, 12, blur_radius=2.0, shadow_color="#00000088")
        s.draw_shadow(50, 50, 120, 80, 16, 16, blur_radius=18.0, spread=4.0, shadow_color="#00000088")

        # Negative spread
        s.draw_shadow(100, 100, 150, 90, 10, 10, blur_radius=10.0, spread=-2.0, shadow_color="#00000088")

        s.flush()

    def test_shadow_cache_and_lru_eviction(self):
        s = Surface(200, 200)

        # Draw identical shadow twice (hits cache)
        s.draw_shadow(10, 10, 60, 40, 6, 6, blur_radius=8.0, shadow_color="#000000aa")
        s.draw_shadow(10, 10, 60, 40, 6, 6, blur_radius=8.0, shadow_color="#000000aa")

        # Generate >130 distinct shadow keys to trigger LRU eviction loop (max_cache_entries_ is 128)
        for i in range(135):
            s.draw_shadow(
                0, 0,
                w=20 + i,
                h=20 + i,
                rx=4,
                ry=4,
                blur_radius=5.0,
                shadow_color=Color(0, 0, 0, 100)
            )

        s.flush()


if __name__ == "__main__":
    unittest.main()
