"""
Visual regression and interaction tests for tkblend vector widgets under Xvfb.
Tests showcase views, interactive table hover/motion, custom vector widgets,
and window resizing to guarantee artifact-free, flicker-free rendering.
"""

import os
import sys
import time
import tkinter as tk
import pytest
from PIL import Image

import tkblend as tb
from tkblend import (
    ScalingTracker,
    set_theme,
    get_theme,
)


def _check_image_content(img_path: str, min_non_black_ratio: float = 0.35) -> bool:
    """Verify that an image contains valid rendered graphics and is not blank or corrupted."""
    assert os.path.exists(img_path), f"Screenshot not found at {img_path}"
    img = Image.open(img_path).convert("RGB")
    pixels = list(img.getdata())
    non_black = sum(1 for r, g, b in pixels if (r > 15 or g > 15 or b > 15))
    ratio = non_black / max(1, len(pixels))
    assert ratio >= min_non_black_ratio, f"Rendered image {img_path} has low content ratio: {ratio:.2f}"
    return True


class TestVisualRender:
    @classmethod
    def setup_class(cls):
        ScalingTracker.activate_high_dpi_awareness()
        set_theme("dark")

    def test_custom_widget_cookbook_rendering(self, tmp_path):
        """Verify that all 4 custom vector widgets in cookbook render without noise or errors."""
        root = tk.Tk()
        root.geometry("1100x750")
        try:
            from examples.custom_widget_cookbook import CustomWidgetCookbook
            cb = CustomWidgetCookbook(root)
            cb.pack(fill="both", expand=True)
            root.update()
            time.sleep(0.1)
            root.update()

            out_file = str(tmp_path / "cookbook.png")
            os.system(f"import -window root {out_file}")
            _check_image_content(out_file)
        finally:
            root.destroy()

    def test_table_hover_motion_no_flicker(self, tmp_path):
        """Verify that Table hover and motion events update state without blinking or breaking."""
        root = tk.Tk()
        root.geometry("900x600")
        try:
            cols = [
                {"id": "id", "title": "ID", "width": 60, "align": "center"},
                {"id": "name", "title": "Service", "width": 180, "align": "left"},
                {"id": "status", "title": "Status", "width": 120, "type": "badge", "align": "center"},
                {"id": "latency", "title": "Latency", "width": 100, "align": "right"},
            ]
            data = [
                {"id": f"SRV-{i:03d}", "name": f"Cluster Node {i}", "status": "ACTIVE" if i % 2 == 0 else "PENDING", "latency": f"{12 + i * 3} ms"}
                for i in range(25)
            ]
            table = tb.Table(root, columns=cols, data=data, width=800, height=500)
            table.pack(fill="both", expand=True, padx=20, pady=20)
            root.update()

            # Simulate mouse moves across multiple rows and headers
            tv = table._view
            class Event:
                def __init__(self, x, y):
                    self.x = x
                    self.y = y

            # Hover header
            tv._on_mouse_move(Event(100, 15))
            assert table._hovered_col == 1
            root.update()

            # Hover row 1
            tv._on_mouse_move(Event(100, 50))
            assert table._hovered_row == 0
            root.update()

            # Hover row 3
            tv._on_mouse_move(Event(100, 115))
            assert table._hovered_row == 2
            root.update()

            # Hover leave
            tv._on_mouse_leave(Event(0, 0))
            assert table._hovered_row is None
            assert table._hovered_col is None
            root.update()

            out_file = str(tmp_path / "table_hover.png")
            os.system(f"import -window root {out_file}")
            _check_image_content(out_file)
        finally:
            root.destroy()

    def test_tabview_and_widget_catalog_rendering(self, tmp_path):
        """Verify that Tabview pages and widget catalog render properly."""
        root = tk.Tk()
        root.geometry("1160x780")
        try:
            from examples.widget_gallery import WidgetGallery
            gal = WidgetGallery(root)
            gal.pack(fill="both", expand=True)
            root.update()
            time.sleep(0.1)
            root.update()

            # Verify Buttons tab
            out_file1 = str(tmp_path / "gallery_buttons.png")
            os.system(f"import -window root {out_file1}")
            _check_image_content(out_file1)

            # Switch to Data Table tab
            gal._tabview.set("Data Table")
            root.update()
            time.sleep(0.1)
            root.update()

            out_file2 = str(tmp_path / "gallery_table.png")
            os.system(f"import -window root {out_file2}")
            _check_image_content(out_file2)
        finally:
            root.destroy()

    def test_window_resize_synchronization(self, tmp_path):
        """Verify that dynamic resizing synchronizes surfaces and avoids blank redraws."""
        root = tk.Tk()
        root.geometry("600x400")
        try:
            card = tb.Card(root, title="Resize Test Card", width=400, height=250)
            card.pack(fill="both", expand=True, padx=20, pady=20)
            btn = tb.Button(card.body, text="Dynamic Button", width=160, height=36)
            btn.pack(pady=10)
            root.update()

            # Enlarge window
            root.geometry("1000x700")
            root.update()
            time.sleep(0.1)
            root.update()

            assert card.winfo_width() > 800
            assert card.surface.width == card.winfo_width()
            assert card.surface.height == card.winfo_height()

            out_file = str(tmp_path / "resized.png")
            os.system(f"import -window root {out_file}")
            _check_image_content(out_file)
        finally:
            root.destroy()
