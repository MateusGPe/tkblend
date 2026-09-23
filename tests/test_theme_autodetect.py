"""
Tests for OS dark mode auto-detection and synchronization using darkdetect.
"""

import sys
import types
import threading
import time
import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch

import tkblend
from tkblend.theme import (
    Palette,
    DARK_PALETTE,
    LIGHT_PALETTE,
    TOKYO_NIGHT_PALETTE,
    CATPPUCCIN_LATTE_PALETTE,
    detect_system_theme,
    is_system_dark,
    auto_theme,
    stop_auto_theme,
    set_theme,
    get_theme,
    apply_theme,
)


@pytest.fixture
def root():
    try:
        r = tk.Tk()
        r.withdraw()
        yield r
        r.destroy()
    except tk.TclError:
        pytest.skip("Tkinter display not available")


@pytest.fixture(autouse=True)
def cleanup_theme():
    yield
    stop_auto_theme()
    set_theme("dark")


def test_detect_system_theme_dark():
    mock_dd = types.ModuleType("darkdetect")
    mock_dd.theme = MagicMock(return_value="Dark")
    mock_dd.isDark = MagicMock(return_value=True)
    mock_dd.isLight = MagicMock(return_value=False)

    with patch.dict(sys.modules, {"darkdetect": mock_dd}):
        assert detect_system_theme() == "dark"
        assert is_system_dark() is True


def test_detect_system_theme_light():
    mock_dd = types.ModuleType("darkdetect")
    mock_dd.theme = MagicMock(return_value="Light")
    mock_dd.isDark = MagicMock(return_value=False)
    mock_dd.isLight = MagicMock(return_value=True)

    with patch.dict(sys.modules, {"darkdetect": mock_dd}):
        assert detect_system_theme() == "light"
        assert is_system_dark() is False


def test_detect_system_theme_boolean_fallback():
    mock_dd = types.ModuleType("darkdetect")
    mock_dd.theme = MagicMock(return_value=None)
    mock_dd.isDark = MagicMock(return_value=True)
    mock_dd.isLight = MagicMock(return_value=False)

    with patch.dict(sys.modules, {"darkdetect": mock_dd}):
        assert detect_system_theme() == "dark"

    mock_dd.isDark = MagicMock(return_value=False)
    mock_dd.isLight = MagicMock(return_value=True)

    with patch.dict(sys.modules, {"darkdetect": mock_dd}):
        assert detect_system_theme() == "light"


def test_detect_system_theme_missing_module():
    # Force ImportError on darkdetect
    with patch.dict(sys.modules, {"darkdetect": None}):
        assert detect_system_theme(fallback="light") == "light"
        assert detect_system_theme(fallback="dark") == "dark"
        assert is_system_dark(fallback=False) is False
        assert is_system_dark(fallback=True) is True


def test_set_theme_system_and_auto():
    mock_dd = types.ModuleType("darkdetect")
    mock_dd.theme = MagicMock(return_value="Light")
    mock_dd.isDark = MagicMock(return_value=False)

    with patch.dict(sys.modules, {"darkdetect": mock_dd}):
        set_theme("system")
        assert get_theme().name == "light"

    mock_dd.theme = MagicMock(return_value="Dark")
    mock_dd.isDark = MagicMock(return_value=True)

    with patch.dict(sys.modules, {"darkdetect": mock_dd}):
        set_theme("auto")
        assert get_theme().name == "dark"


def test_auto_theme_custom_palettes():
    mock_dd = types.ModuleType("darkdetect")
    mock_dd.theme = MagicMock(return_value="Dark")
    mock_dd.isDark = MagicMock(return_value=True)

    with patch.dict(sys.modules, {"darkdetect": mock_dd}):
        auto_theme(dark="tokyo_night", light="catppuccin_latte", listen=False)
        assert get_theme().name == "tokyo_night"

    mock_dd.theme = MagicMock(return_value="Light")
    mock_dd.isDark = MagicMock(return_value=False)

    with patch.dict(sys.modules, {"darkdetect": mock_dd}):
        auto_theme(dark="tokyo_night", light="catppuccin_latte", listen=False)
        assert get_theme().name == "catppuccin_latte"


def test_auto_theme_live_listener_dispatch(root):
    listener_cb = None

    def fake_listener(cb):
        nonlocal listener_cb
        listener_cb = cb

    mock_dd = types.ModuleType("darkdetect")
    mock_dd.theme = MagicMock(return_value="Dark")
    mock_dd.isDark = MagicMock(return_value=True)
    mock_dd.listener = fake_listener

    with patch.dict(sys.modules, {"darkdetect": mock_dd}):
        cleanup = auto_theme(root=root, dark="dark", light="light", listen=True)
        assert get_theme().name == "dark"
        assert listener_cb is not None

        # Simulate OS dark mode change to Light
        listener_cb("Light")
        root.update()
        assert get_theme().name == "light"

        # Simulate OS dark mode change to Dark
        listener_cb("Dark")
        root.update()
        assert get_theme().name == "dark"

        # Test cleanup stops auto theme
        cleanup()
        listener_cb("Light")
        root.update()
        # Should stay dark because listener was stopped
        assert get_theme().name == "dark"


def test_apply_theme_auto_detect(root):
    listener_cb = None

    def fake_listener(cb):
        nonlocal listener_cb
        listener_cb = cb

    mock_dd = types.ModuleType("darkdetect")
    mock_dd.theme = MagicMock(return_value="Light")
    mock_dd.isDark = MagicMock(return_value=False)
    mock_dd.listener = fake_listener

    with patch.dict(sys.modules, {"darkdetect": mock_dd}):
        cleanup = apply_theme(root, auto_detect=True)
        assert get_theme().name == "light"

        if listener_cb:
            listener_cb("Dark")
            root.update()
            assert get_theme().name == "dark"

        cleanup()


def test_exports_in_tkblend():
    assert hasattr(tkblend, "detect_system_theme")
    assert hasattr(tkblend, "is_system_dark")
    assert hasattr(tkblend, "auto_theme")
    assert hasattr(tkblend, "stop_auto_theme")
