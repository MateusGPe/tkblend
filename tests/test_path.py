"""
Tests for Path builder and vector path operations.
"""

import unittest
from tkblend import Path
from tkblend._tkblend import Path as NativePath


class TestPath(unittest.TestCase):
    def test_path_builder_methods(self):
        p = Path()
        self.assertIsInstance(p.native, NativePath)

        # Chaining all methods
        res = (
            p.move_to(10.0, 10.0)
            .line_to(50.0, 10.0)
            .quad_to(70.0, 20.0, 80.0, 40.0)
            .cubic_to(85.0, 50.0, 90.0, 60.0, 95.0, 70.0)
            .arc_to(50.0, 50.0, 20.0, 20.0, 0.0, 3.14159)
            .add_rect(10.0, 10.0, 30.0, 30.0)
            .add_rounded_rect(15.0, 15.0, 25.0, 25.0, 4.0, 4.0)
            .add_circle(40.0, 40.0, 15.0)
            .add_ellipse(60.0, 60.0, 20.0, 10.0)
            .close()
        )
        self.assertIs(res, p)

        # Clear and Reset
        p.clear()
        p.move_to(0, 0).line_to(10, 10)
        p.reset()

    def test_native_path_direct(self):
        np = NativePath()
        (
            np.move_to(5, 5)
            .line_to(15, 5)
            .quad_to(20, 10, 25, 20)
            .cubic_to(30, 25, 35, 30, 40, 35)
            .arc_to(20, 20, 10, 10, 0, 1.57)
            .add_rect(0, 0, 50, 50)
            .add_rounded_rect(0, 0, 40, 40, 5, 5)
            .add_circle(25, 25, 10)
            .add_ellipse(25, 25, 15, 8)
            .close()
            .clear()
            .reset()
        )


if __name__ == "__main__":
    unittest.main()
