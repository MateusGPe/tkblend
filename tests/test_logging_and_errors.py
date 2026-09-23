"""
Unit tests for structured logging and error handling in tkblend.
"""

import logging
import pytest
import tkinter as tk
from tkblend.theme import (
    ThemeManager,
    Palette,
    DARK_PALETTE,
    LIGHT_PALETTE,
    blend_color_hex,
    adjust_brightness,
    resolve_color_failsafe,
    add_theme_listener,
    remove_theme_listener,
)
from tkblend.font import parse_font, extract_font_family, sync_tk_fonts
from tkblend.widgets import (
    Button,
    Slider,
    Dropdown,
    Switch,
    cascade_bg_to_children,
)


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_root_logger_null_handler():
    """Verify tkblend package has a NullHandler configured."""
    pkg_logger = logging.getLogger("tkblend")
    handler_types = [type(h) for h in pkg_logger.handlers]
    assert logging.NullHandler in handler_types


def test_theme_listener_error_logging(caplog):
    """Verify that a failing theme listener is logged at ERROR level and doesn't halt others."""
    tm = ThemeManager()
    calls = []

    def failing_listener(pal: Palette):
        raise RuntimeError("Test listener intentional failure")

    def succeeding_listener(pal: Palette):
        calls.append(pal)

    tm.add_listener(failing_listener)
    tm.add_listener(succeeding_listener)

    try:
        with caplog.at_level(logging.ERROR, logger="tkblend.theme"):
            tm.notify_listeners()

        assert len(calls) == 1
        assert any("Error executing theme listener" in record.message for record in caplog.records)
        assert any(record.levelno == logging.ERROR for record in caplog.records)
    finally:
        tm.remove_listener(failing_listener)
        tm.remove_listener(succeeding_listener)


def test_color_functions_warning_logging(caplog):
    """Verify that color blend / brightness failures log at WARNING level."""
    with caplog.at_level(logging.WARNING, logger="tkblend.theme"):
        res = blend_color_hex(None, None, 0.5)  # type: ignore
        assert res is None

        res_bright = adjust_brightness(None, 1.5)  # type: ignore
        assert res_bright is None

    warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any("Failed blending colors" in m for m in warning_messages)
    assert any("Failed adjusting brightness" in m for m in warning_messages)


def test_dropdown_callback_error_logging(root, caplog):
    """Verify that a failing Dropdown on_select callback is logged at ERROR level."""
    def failing_callback(val):
        raise ValueError("Invalid option chosen")

    dd = Dropdown(root, options=["Option A", "Option B"], on_select=failing_callback)
    with caplog.at_level(logging.ERROR, logger="tkblend.widgets.dropdown"):
        dd._select_option("Option B", notify=True, close=True)

    assert any("Error executing Dropdown on_select callback" in r.message for r in caplog.records)
    assert any(r.levelno == logging.ERROR for r in caplog.records)


def test_widget_debug_logging_on_render_failure(root, caplog):
    """Verify that render exceptions in widgets log at DEBUG level."""
    btn = Button(root, text="Test Button")

    # Simulate render failure by forcing invalid surface state
    original_surface = btn._surface
    btn._surface = None  # type: ignore

    with caplog.at_level(logging.DEBUG, logger="tkblend.widgets.button"):
        btn.render()

    btn._surface = original_surface

    debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    assert any("Render failed in Button" in m for m in debug_messages)


def test_font_parse_debug_logging(caplog):
    """Verify font parsing errors are logged cleanly at DEBUG level."""
    with caplog.at_level(logging.DEBUG, logger="tkblend.font"):
        cfg = parse_font(("Segoe UI", "not-a-number", "bold"))
        assert cfg.family == "Segoe UI"
        assert cfg.bold is True

    debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    assert any("Failed parsing font size" in m for m in debug_messages)


def test_cascade_bg_error_handling(root, caplog):
    """Verify cascade_bg_to_children handles child background updates cleanly."""
    f = tk.Frame(root)
    b = Button(f, text="Child")
    f.pack()

    with caplog.at_level(logging.DEBUG, logger="tkblend.widgets.base"):
        cascade_bg_to_children(f, "#123456")
