"""
Pytest Integration for Granular TTK Component & State Matrix Visual Verification.
"""

import os
import pytest
from PIL import Image
from scripts.validate_granular_appearance import (
    BASELINES_DIR,
    REPORTS_DIR,
    TARGET_BUILDERS,
    ensure_dirs,
    capture_window_image,
    compare_images
)


@pytest.fixture(scope="session", autouse=True)
def setup_dirs():
    ensure_dirs()


class TestGranularVisualAppearance:
    @pytest.mark.parametrize("target_key", list(TARGET_BUILDERS.keys()))
    def test_granular_target_matches_baseline(self, target_key):
        desc, builder_fn = TARGET_BUILDERS[target_key]
        baseline_file = os.path.join(BASELINES_DIR, f"{target_key}.png")

        root = builder_fn()
        try:
            actual = capture_window_image(root)
        finally:
            root.destroy()

        if not os.path.exists(baseline_file):
            actual.save(baseline_file)
            pytest.skip(f"Created initial baseline for {target_key}")

        baseline = Image.open(baseline_file).convert("RGB")
        match_pct, diff_img, heat_img = compare_images(actual, baseline)

        actual_out = os.path.join(REPORTS_DIR, f"{target_key}_actual.png")
        diff_out = os.path.join(REPORTS_DIR, f"{target_key}_diff.png")
        heat_out = os.path.join(REPORTS_DIR, f"{target_key}_heatmap.png")

        actual.save(actual_out)
        diff_img.save(diff_out)
        heat_img.save(heat_out)

        # Allow 98.5% match tolerance for system font antialiasing variations
        assert match_pct >= 98.5, f"Visual mismatch for {target_key} ({desc}): {match_pct:.2f}% (diff saved to {diff_out})"
