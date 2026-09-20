"""
Tests for Tkinter blit bridge (Tk_PhotoPutBlock).
"""

import unittest
import tkinter as tk
from tkblend import Surface, Color


class TestBlitting(unittest.TestCase):
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

    def test_valid_photo_blit_and_offsets(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        photo = tk.PhotoImage(master=self.root, width=128, height=128)
        surf = Surface(64, 64)
        surf.clear("#ff8000")
        surf.fill_circle(32, 32, 16, "#00ff00")

        # Standard blit at (0, 0)
        surf.blit(photo)

        # Blit with offsets
        surf.blit(photo, dst_x=32, dst_y=32)

    def test_invalid_interp_or_photo_name(self):
        surf = Surface(32, 32)
        native = surf.native

        # Invalid interp address (0 / NULL)
        with self.assertRaises((RuntimeError, ValueError)) as ctx:
            native.blit_to_photo(0, "nonexistent_photo", 0, 0)
        self.assertIn("Invalid Tcl_Interp", str(ctx.exception))

        if self.root:
            interp_addr = int(self.root.tk.interpaddr())
            # Non-existent photo handle
            with self.assertRaises((RuntimeError, ValueError)) as ctx:
                native.blit_to_photo(interp_addr, "nonexistent_photo_name_12345", 0, 0)
            self.assertIn("Tk_FindPhoto", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
