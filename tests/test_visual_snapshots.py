"""
Pytest integration for TTK theme visual appearance and snapshot regression testing.
"""

import os
import pytest
from PIL import Image
from scripts.validate_theme_appearance import (
    BASELINES_DIR,
    REPORTS_DIR,
    ensure_dirs,
    build_showcase_window,
    capture_window_image,
    compare_images
)


@pytest.fixture(scope="session", autouse=True)
def setup_dirs():
    ensure_dirs()


class TestVisualAppearanceSnapshots:
    @pytest.mark.parametrize("target", [
        {"name": "showcase_dark_tab1", "dark": True, "tab": 0},
        {"name": "showcase_dark_tab2", "dark": True, "tab": 1},
        {"name": "showcase_light_tab1", "dark": False, "tab": 0},
        {"name": "showcase_light_tab2", "dark": False, "tab": 1},
    ])
    def test_theme_snapshot_matches_baseline(self, target):
        name = target["name"]
        baseline_file = os.path.join(BASELINES_DIR, f"{name}.png")

        root = build_showcase_window(dark=target["dark"], tab_index=target["tab"])
        try:
            actual = capture_window_image(root)
        finally:
            root.destroy()

        if not os.path.exists(baseline_file):
            actual.save(baseline_file)
            pytest.skip(f"Created initial baseline for {name}")

        baseline = Image.open(baseline_file).convert("RGB")
        match_pct, diff_img, heat_img = compare_images(actual, baseline)

        actual_out = os.path.join(REPORTS_DIR, f"{name}_actual.png")
        diff_out = os.path.join(REPORTS_DIR, f"{name}_diff.png")
        heat_out = os.path.join(REPORTS_DIR, f"{name}_heatmap.png")

        actual.save(actual_out)
        diff_img.save(diff_out)
        heat_img.save(heat_out)

        # Allow 98.5% match threshold to tolerate subtle subpixel font antialiasing variance across systems
        assert match_pct >= 98.5, f"Visual snapshot mismatch for {name}: {match_pct:.2f}% (diff saved to {diff_out})"
