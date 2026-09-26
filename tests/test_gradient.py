"""
Tests for Gradient, LinearGradient, and RadialGradient.
"""

import unittest
from tkblend import (
    LinearGradient,
    RadialGradient,
    Color,
    EXTEND_PAD,
    EXTEND_REPEAT,
    EXTEND_REFLECT,
)
from tkblend._tkblend import Gradient as NativeGradient
from tkblend.surface import _unwrap_gradient


class TestGradient(unittest.TestCase):
    def test_linear_gradient(self):
        lg = LinearGradient(0.0, 0.0, 100.0, 200.0)
        ret = lg.add_stop(0.0, "#ff0000")
        self.assertIs(ret, lg)
        lg.add_stop(0.5, (0, 255, 0, 128))
        lg.add_stop(1.0, Color(0, 0, 255, 255))
        lg.set_extend_mode(EXTEND_REPEAT)

        self.assertIsInstance(lg.native, NativeGradient)
        self.assertIs(_unwrap_gradient(lg), lg.native)

    def test_radial_gradient(self):
        rg = RadialGradient(50.0, 50.0, 0.0, 50.0, 50.0, 40.0)
        ret = rg.add_stop(0.0, "#ffffff")
        self.assertIs(ret, rg)
        rg.add_stop(1.0, "#000000")
        rg.set_extend_mode(EXTEND_REFLECT)

        self.assertIsInstance(rg.native, NativeGradient)
        self.assertIs(_unwrap_gradient(rg), rg.native)

        # Also test 3-arg constructor RadialGradient(cx, cy, r)
        rg3 = RadialGradient(50.0, 50.0, 40.0)
        rg3.add_stop(0.0, "#ffffff").add_stop(1.0, "#000000")
        self.assertIsInstance(rg3.native, NativeGradient)
        self.assertIs(_unwrap_gradient(rg3), rg3.native)

    def test_native_gradient_direct(self):
        g_lin = NativeGradient.linear(10, 20, 30, 40)
        g_lin.add_stop(0.0, Color(255, 0, 0, 255))
        g_lin.add_stop(-0.5, Color(0, 255, 0, 255))  # Clamped to 0.0
        g_lin.add_stop(1.5, Color(0, 0, 255, 255))   # Clamped to 1.0
        g_lin.set_extend_mode(EXTEND_PAD)

        g_rad = NativeGradient.radial(10, 20, 5, 30, 40, 50)
        g_rad.add_stop(0.5, Color(128, 128, 128, 255))

        self.assertIs(_unwrap_gradient(g_lin), g_lin)


if __name__ == "__main__":
    unittest.main()
