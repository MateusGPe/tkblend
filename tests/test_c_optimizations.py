"""
Tests for high-performance C++ extensions in tkblend:
- Color math (lighten, darken, lerp, with_alpha)
- Typography metrics (measure_text, break_lines, draw_text_wrapped)
- Easing curves & spring physics (ease, spring)
- Display List / DrawBatch recording & execution
- Compound widget primitives (draw_button, draw_switch, draw_slider, draw_progress_bar, draw_checkbox)
"""

import pytest
from tkblend._tkblend import (
    Color,
    Surface as NativeSurface,
    DrawBatch,
    TextMetrics,
    EasingType,
    ease,
    spring,
)
from tkblend.surface import Surface, LinearGradient


class TestColorMath:
    def test_lighten_and_darken(self):
        c = Color(100, 100, 100, 255)
        lighter = c.lighten(1.5)
        assert lighter.r == 150
        assert lighter.g == 150
        assert lighter.b == 150
        assert lighter.a == 255

        darker = c.darken(0.5)
        assert darker.r == 50
        assert darker.g == 50
        assert darker.b == 50
        assert darker.a == 255

    def test_lerp_and_alpha(self):
        c1 = Color(0, 0, 0, 255)
        c2 = Color(200, 100, 50, 255)
        mid = c1.lerp(c2, 0.5)
        assert mid.r == 100
        assert mid.g == 50
        assert mid.b == 25
        assert mid.a == 255

        with_a = mid.with_alpha(128)
        assert with_a.a == 128
        assert with_a.r == 100

        with_af = mid.with_alpha_f(0.5)
        assert with_af.a in (127, 128)


class TestEasingMath:
    def test_standard_easings(self):
        assert ease(int(EasingType.Linear), 0.0) == 0.0
        assert ease(int(EasingType.Linear), 1.0) == 1.0
        assert ease(int(EasingType.Linear), 0.5) == 0.5

        assert ease(int(EasingType.QuadIn), 0.5) == 0.25
        assert ease(int(EasingType.QuadOut), 0.5) == 0.75
        assert ease(int(EasingType.CubicIn), 0.5) == 0.125
        assert ease(int(EasingType.CubicOut), 0.5) == 0.875

    def test_spring_physics(self):
        assert spring(0.0) == 0.0
        assert spring(1.0) == 1.0
        val = spring(0.5, mass=1.0, stiffness=100.0, damping=10.0)
        assert val > 0.9


class TestTypographyAndMetrics:
    def test_measure_text(self):
        surface = Surface(200, 100)
        tm = surface.measure_text("Hello Blend2D", font_size=16.0)
        assert isinstance(tm, TextMetrics)
        assert tm.width > 0
        assert tm.height > 0
        assert tm.ascent > 0
        assert tm.advance_x > 0

    def test_break_lines_and_wrapping(self):
        surface = Surface(400, 400)
        text = "The quick brown fox jumps over the lazy dog"
        lines = surface.break_lines(text, max_width=100.0, font_size=14.0)
        assert len(lines) > 1
        assert "quick" in lines[0] or "The" in lines[0]

    def test_ellipsis_truncation(self):
        surface = Surface(400, 400)
        text = "This is a very long text that should be truncated with an ellipsis after two lines"
        lines = surface.break_lines(
            text, max_width=120.0, font_size=14.0, truncate_ellipsis=True, max_lines=2
        )
        assert len(lines) <= 2
        assert lines[-1].endswith("...")

    def test_draw_text_wrapped(self):
        surface = Surface(300, 200)
        surface.clear("#ffffff")
        surface.draw_text_wrapped(
            "First line\nSecond line with wrapping\nThird line",
            x=10,
            y=20,
            max_width=150,
            font_size=14.0,
            color="#000000",
        )
        buf = surface.get_buffer()
        assert len(buf) > 0


class TestDrawBatchDisplayList:
    def test_draw_batch_recording_and_execution(self):
        batch = DrawBatch()
        assert len(batch) == 0

        batch.clear(Color(255, 255, 255, 255))
        batch.fill_rounded_rect(10, 10, 80, 40, 5, 5, Color(50, 100, 200, 255))
        batch.stroke_rounded_rect(10, 10, 80, 40, 5, 5, Color(20, 40, 100, 255), 1.5)
        batch.draw_text("Batch Text", 20, 30, 12.0, "default", Color(255, 255, 255, 255), 0, 400, False)
        assert len(batch) == 4

        surface = Surface(100, 100)
        surface.execute_batch(batch)
        buf = surface.get_buffer()
        assert len(buf) == 100 * 100 * 4

        batch.reset()
        assert len(batch) == 0


class TestCompoundWidgetPrimitives:
    def test_draw_button_primitive(self):
        surface = Surface(120, 40)
        surface.draw_button(
            x=5, y=5, w=110, h=30, rx=8, ry=8,
            bg_color="#3b82f6",
            border_color="#1d4ed8",
            border_width=1.0,
            fg_color="#ffffff",
            text="Click Me",
            font_size=13.0,
            shadow_blur=4.0,
            shadow_offset_y=2.0,
            shadow_color="#00000030",
            focus_ring_color="#60a5fa",
            focus_ring_width=1.5,
            is_pressed=False,
        )
        buf = surface.get_buffer()
        assert len(buf) > 0

    def test_draw_switch_primitive(self):
        surface = Surface(60, 30)
        surface.draw_switch(
            x=2, y=2, w=56, h=26,
            track_color="#10b981",
            thumb_color="#ffffff",
            thumb_border_color="#00000020",
            progress_t=1.0,
            is_hovered=True,
            focus_ring_color="#34d399",
            focus_ring_width=1.5,
        )
        buf = surface.get_buffer()
        assert len(buf) > 0

    def test_draw_slider_primitive(self):
        surface = Surface(200, 30)
        surface.draw_slider(
            x=10, y=0, w=180, h=30,
            track_bg="#e2e8f0",
            active_bg="#3b82f6",
            thumb_color="#ffffff",
            thumb_border_color="#94a3b8",
            value_t=0.6,
            track_thickness=6.0,
            thumb_radius=8.0,
            is_hovered=False,
            is_dragging=True,
        )
        buf = surface.get_buffer()
        assert len(buf) > 0

    def test_draw_progress_bar_primitive(self):
        surface = Surface(200, 20)
        surface.draw_progress_bar(
            x=2, y=2, w=196, h=16, rx=8, ry=8,
            track_bg="#e2e8f0",
            bar_bg="#3b82f6",
            progress_t=0.75,
            is_indeterminate=False,
        )
        # Also test indeterminate mode
        surface.draw_progress_bar(
            x=2, y=2, w=196, h=16, rx=8, ry=8,
            track_bg="#e2e8f0",
            bar_bg="#3b82f6",
            progress_t=0.0,
            is_indeterminate=True,
            phase_offset=0.3,
        )
        buf = surface.get_buffer()
        assert len(buf) > 0

    def test_draw_checkbox_primitive(self):
        surface = Surface(30, 30)
        surface.draw_checkbox(
            x=5, y=5, size=20, rx=4, ry=4,
            box_bg="#3b82f6",
            border_color="#1d4ed8",
            border_width=1.0,
            check_color="#ffffff",
            is_checked=True,
            is_hovered=False,
        )
        buf = surface.get_buffer()
        assert len(buf) > 0
