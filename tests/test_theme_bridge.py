"""
Unit tests for tkblend.theme color resolution and ttkbootstrap bridging.
"""

import sys
import types
import unittest
import tkinter as tk
from unittest.mock import MagicMock, patch
from tkblend.theme import (
    resolve_theme_color,
    get_theme_colors,
    get_active_theme_name,
    get_active_style,
    is_ttkbootstrap_installed,
    bind_theme_changed,
)
from tkblend.surface import parse_color, Surface
from tkblend import Color


class DummyColors:
    primary = "#123456"
    secondary = "#654321"
    success = "#112233"
    info = "#445566"
    warning = "#778899"
    danger = "#aabbcc"
    light = "#ddeeff"
    dark = "#001122"
    bg = "#ffffff"
    fg = "#000000"
    border = "#cccccc"
    inputbg = "#ffffff"
    inputfg = "#000000"
    selectbg = "#123456"
    selectfg = "#ffffff"


class DummyStyle:
    def __init__(self):
        self.colors = DummyColors()

    @classmethod
    def get_instance(cls):
        return cls()

    def theme_use(self):
        return "cosmo"


class TestThemeBridge(unittest.TestCase):
    def test_bootstrap_token_resolution(self):
        # Fallback tokens
        primary = resolve_theme_color("primary")
        self.assertTrue(primary.startswith("#"))

        success = resolve_theme_color("success")
        self.assertTrue(success.startswith("#"))

        dark = resolve_theme_color("dark")
        self.assertTrue(dark.startswith("#"))

        # Non-string passthrough
        self.assertEqual(resolve_theme_color(12345), 12345)

        # Invalid alpha string fallthrough
        res_invalid = resolve_theme_color("primary/invalid")
        self.assertTrue(res_invalid.startswith("#"))

        res_invalid_colon = resolve_theme_color("primary:invalid")
        self.assertTrue(res_invalid_colon.startswith("#"))

    def test_alpha_notation_resolution(self):
        # Slash notation
        c_slash = resolve_theme_color("primary/0.5")
        self.assertTrue(c_slash.startswith("#"))
        self.assertEqual(len(c_slash), 9)  # #rrggbbaa

        # Colon notation
        c_colon = resolve_theme_color("danger:128")
        self.assertTrue(c_colon.startswith("#"))
        self.assertEqual(len(c_colon), 9)

        # 8-char hex with alpha override
        c_8hex = resolve_theme_color("#11223344", alpha=0.5)
        self.assertEqual(len(c_8hex), 9)

        # 3-char hex with alpha override
        c_3hex = resolve_theme_color("#abc", alpha=0.5)
        self.assertEqual(len(c_3hex), 9)

        # Keyword alpha argument
        c_kw = resolve_theme_color("#123456", alpha=0.5)
        self.assertEqual(len(c_kw), 9)
        self.assertTrue(c_kw.startswith("#123456"))

    def test_parse_color_with_tokens(self):
        native_primary = parse_color("primary")
        self.assertIsInstance(native_primary, Color)
        self.assertEqual(native_primary.a, 255)

        native_alpha = parse_color("primary/0.5")
        self.assertIsInstance(native_alpha, Color)
        self.assertAlmostEqual(native_alpha.a, 127, delta=2)

        # Direct Color object
        c = Color(255, 0, 0, 200)
        self.assertEqual(parse_color(c), c)

        # Int u32
        u32_c = parse_color(0xFF0000FF)
        self.assertIsInstance(u32_c, Color)

        # RGB tuple with alpha
        tup_c = parse_color((100, 150, 200), alpha=0.5)
        self.assertEqual(tup_c.r, 100)
        self.assertEqual(tup_c.g, 150)
        self.assertEqual(tup_c.b, 200)
        self.assertAlmostEqual(tup_c.a, 127, delta=2)

        # RGBA tuple
        tup4_c = parse_color((100, 150, 200, 250), alpha=0.5)
        self.assertAlmostEqual(tup4_c.a, 127, delta=2)

        with self.assertRaises(ValueError):
            parse_color({"invalid": "object"})

    def test_get_theme_colors(self):
        colors = get_theme_colors()
        self.assertIn("primary", colors)
        self.assertIn("secondary", colors)
        self.assertIn("bg", colors)
        self.assertIn("fg", colors)

    def test_theme_name_and_status(self):
        name = get_active_theme_name()
        self.assertIsInstance(name, str)
        status = is_ttkbootstrap_installed()
        self.assertIsInstance(status, bool)

    def test_bind_theme_changed(self):
        root = tk.Tk()
        root.withdraw()
        root.update()
        try:
            called = [False]
            def _cb():
                called[0] = True

            lbl = tk.Label(root)
            lbl.pack()
            bind_theme_changed(lbl, _cb)
            root.event_generate("<<ThemeChanged>>", when="now")
            self.assertTrue(called[0])
        finally:
            root.destroy()

    def test_mocked_ttkbootstrap_integration(self):
        fake_module = types.ModuleType("ttkbootstrap")
        fake_module.Style = DummyStyle

        with patch.dict(sys.modules, {"ttkbootstrap": fake_module}):
            self.assertTrue(is_ttkbootstrap_installed())
            style = get_active_style()
            self.assertIsNotNone(style)
            self.assertEqual(get_active_theme_name(), "cosmo")

            colors = get_theme_colors()
            self.assertEqual(colors["primary"], "#123456")

            # Resolve using active theme colors
            resolved = resolve_theme_color("primary")
            self.assertEqual(resolved, "#123456")


if __name__ == "__main__":
    unittest.main()
