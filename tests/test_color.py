"""
Tests for Color and parse_color helper.
"""

import unittest
import pytest
from tkblend import Color
from tkblend.surface import parse_color
from tkblend._tkblend import Color as NativeColor


class TestColor(unittest.TestCase):
    def test_constructor_defaults_and_values(self):
        c_default = Color()
        self.assertEqual(c_default.r, 0)
        self.assertEqual(c_default.g, 0)
        self.assertEqual(c_default.b, 0)
        self.assertEqual(c_default.a, 255)

        c = Color(10, 20, 30, 40)
        self.assertEqual(c.r, 10)
        self.assertEqual(c.g, 20)
        self.assertEqual(c.b, 30)
        self.assertEqual(c.a, 40)

        # Mutate read-write properties
        c.r = 100
        c.g = 150
        c.b = 200
        c.a = 250
        self.assertEqual(c.r, 100)
        self.assertEqual(c.g, 150)
        self.assertEqual(c.b, 200)
        self.assertEqual(c.a, 250)

    def test_hex_parsing_formats(self):
        # #RGB (3 hex digits)
        c3 = Color.from_hex("#f80")
        self.assertEqual((c3.r, c3.g, c3.b, c3.a), (255, 136, 0, 255))

        # RGB without hash
        c3_no_hash = Color.from_hex("0fa")
        self.assertEqual((c3_no_hash.r, c3_no_hash.g, c3_no_hash.b, c3_no_hash.a), (0, 255, 170, 255))

        # #RGBA (4 hex digits)
        c4 = Color.from_hex("#1234")
        self.assertEqual((c4.r, c4.g, c4.b, c4.a), (17, 34, 51, 68))

        # #RRGGBB (6 hex digits)
        c6 = Color.from_hex("#aabbcc")
        self.assertEqual((c6.r, c6.g, c6.b, c6.a), (0xaa, 0xbb, 0xcc, 255))

        # #RRGGBBAA (8 hex digits)
        c8 = Color.from_hex("#11223344")
        self.assertEqual((c8.r, c8.g, c8.b, c8.a), (0x11, 0x22, 0x33, 0x44))

        # Fallback on invalid length hex
        c_inv = Color.from_hex("#12345")
        self.assertEqual((c_inv.r, c_inv.g, c_inv.b, c_inv.a), (0, 0, 0, 255))

    def test_u32_roundtrip(self):
        c = Color(0x12, 0x34, 0x56, 0x78)
        u32 = c.to_u32()
        c2 = Color.from_u32(u32)
        self.assertEqual((c2.r, c2.g, c2.b, c2.a), (0x12, 0x34, 0x56, 0x78))

    def test_repr(self):
        c = Color(1, 2, 3, 4)
        self.assertEqual(repr(c), "Color(r=1, g=2, b=3, a=4)")

    def test_parse_color_types(self):
        # Native Color
        c_orig = Color(10, 20, 30, 40)
        self.assertIs(parse_color(c_orig), c_orig)

        # String hex
        c_str = parse_color("#ff0000")
        self.assertEqual((c_str.r, c_str.g, c_str.b, c_str.a), (255, 0, 0, 255))

        # Int u32 ARGB
        c_int = parse_color(0xFF112233)
        self.assertEqual((c_int.r, c_int.g, c_int.b, c_int.a), (0x11, 0x22, 0x33, 0xFF))

        # RGB 3-tuple / list
        c_t3 = parse_color((100, 150, 200))
        self.assertEqual((c_t3.r, c_t3.g, c_t3.b, c_t3.a), (100, 150, 200, 255))

        c_l3 = parse_color([10, 20, 30])
        self.assertEqual((c_l3.r, c_l3.g, c_l3.b, c_l3.a), (10, 20, 30, 255))

        # RGBA 4-tuple / list
        c_t4 = parse_color((10, 20, 30, 40))
        self.assertEqual((c_t4.r, c_t4.g, c_t4.b, c_t4.a), (10, 20, 30, 40))

        c_l4 = parse_color([50, 60, 70, 80])
        self.assertEqual((c_l4.r, c_l4.g, c_l4.b, c_l4.a), (50, 60, 70, 80))

        # Invalid type / tuple length
        with self.assertRaises(ValueError):
            parse_color((1, 2))

        with self.assertRaises(ValueError):
            parse_color(None)


if __name__ == "__main__":
    unittest.main()
