import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from tkblend.surface import Surface
from tkblend.theme import set_theme, get_theme
from tkblend.widgets.base import BaseControl, ScalingTracker
from tkblend.widgets import Button
from tkblend.widgets.utils import (
    draw_vector_checkmark,
    draw_vector_chevron,
    draw_vector_minus,
    draw_vector_plus,
    truncate_text,
    draw_focus_ring,
    draw_circular_focus_ring,
    compute_text_baseline_y,
    compute_icon_baseline_y,
    bind_variable_trace,
    unbind_variable_trace,
    compute_scrollbar_geometry,
    compute_scroll_drag_delta,
    compute_scroll_jump,
    get_measure_surface,
    normalize_anchor,
    measure_text_dimensions,
    invoke_callback,
)
from tkblend.utils.window_shape import (
    is_window_shaping_supported,
    apply_round_rect_shape,
    clear_window_shape,
)
from tkblend.utils.tcl_interp import extract_interp_address


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


# ==============================================================================
# BASE CONTROL TESTS
# ==============================================================================

def test_scaling_tracker_api(root):
    # Test ScalingTracker methods
    factor = ScalingTracker.get_scaling_factor(root)
    assert factor > 0.0

    # Test cache and reset
    ScalingTracker._cached_factor = 2.5
    assert ScalingTracker.get_scaling_factor(root) == 2.5
    ScalingTracker._cached_factor = None

    # Test get_scaling_factor with None
    factor2 = ScalingTracker.get_scaling_factor(None)
    assert factor2 > 0.0


def test_base_control_properties_and_configuration(root):
    set_theme("dark")
    btn = Button(root, text="Base Test", width=120, height=36)
    btn.pack()
    root.update_idletasks()

    # 1. Corner radius
    btn.corner_radius = 8.0
    assert btn.corner_radius == 8.0
    btn.corner_radius = None
    assert btn.corner_radius is None

    # 2. Font
    btn.font = ("Helvetica", 14, "bold")
    assert btn.font.family == "Helvetica"
    assert btn.font.size == 14

    # 3. Text overflow
    btn.text_overflow = "ellipsis"
    assert btn.text_overflow == "ellipsis"
    btn.text_overflow = "clip"
    assert btn.text_overflow == "clip"

    # 4. State
    btn.state = "disabled"
    assert btn.state == "disabled"
    assert btn.is_disabled is True
    btn.state = "normal"
    assert btn.state == "normal"
    assert btn.is_disabled is False

    # 5. Command
    cmd_called = []
    btn.command = lambda: cmd_called.append(True)
    assert callable(btn.command)

    # 6. Container layer
    btn.container_layer = 1
    assert btn.container_layer == 1
    btn.set_container_layer(0)
    assert btn.container_layer == 0

    # 7. CSS classes
    btn.add_class("primary-btn")
    assert btn.has_class("primary-btn") is True
    assert "primary-btn" in btn.classes
    assert "primary-btn" in btn.class_name

    btn.toggle_class("active-state")
    assert btn.has_class("active-state") is True
    btn.toggle_class("active-state")
    assert btn.has_class("active-state") is False

    btn.remove_class("primary-btn")
    assert btn.has_class("primary-btn") is False

    btn.classes = ["foo", "bar"]
    assert btn.has_class("foo") is True
    btn.class_name = "baz qux"
    assert btn.has_class("baz") is True

    # 8. Variable management and state properties
    btn.widget_class = "custom_btn"
    assert btn.widget_class == "custom_btn"

    btn.checked = True
    assert btn.checked is True
    btn.checked = False

    btn.parent_bg = "#112233"
    assert btn.parent_bg.lower() == "#112233"

    btn.bg_color = "#223344"
    assert btn.bg_color.lower() == "#223344"

    btn.is_disabled = True
    assert btn.is_disabled is True
    assert btn.is_hovered is False
    assert btn.is_pressed is False
    assert btn.is_focused is False
    btn.is_disabled = False

    btn.set_var("--custom-var", "42")
    assert btn.get_var("--custom-var") == "42"
    assert "42" in btn.vars.values()

    col = btn.get_color("primary")
    assert col.startswith("#")

    btn.set_var("my_color", "#aabbcc")
    assert btn.get_color("my_color") == "#aabbcc"
    assert btn.get_color("completely_unknown_color", fallback="#ff00ff") == "#ff00ff"

    btn.remove_var("--custom-var")
    assert btn.get_var("--custom-var") == ""
    btn.clear_vars()

    # 9. DrawBatch binding
    assert btn.has_batch is not None
    btn.clear_batch()

    # 10. Paint and redraw
    btn.paint_and_blit()
    btn.request_redraw()

    # 11. Controller hooks
    btn._on_controller_state_changed(1, 0)
    btn._on_controller_click(10, 10, 1)
    assert len(cmd_called) == 1

    ev_conf = tk.Event()
    ev_conf.widget = btn
    ev_conf.width = 150
    ev_conf.height = 40
    btn._on_tk_configure(ev_conf)

    btn._on_controller_resize(150, 40)
    btn._on_controller_change(0.5)

    # 12. Full configure and cget verification
    btn.configure(
        text="New Text",
        width=140,
        height=45,
        min_width=100,
        max_width=200,
        min_height=30,
        max_height=60,
        anchor="e",
        corner_radius=12.0,
        text_overflow="clip",
        cursor="hand2",
    )
    assert btn.cget("text") == "New Text"
    assert btn.cget("width") == 140
    assert btn.cget("height") == 45
    assert btn.cget("min_width") == 100
    assert btn.cget("max_width") == 200
    assert btn.cget("min_height") == 30
    assert btn.cget("max_height") == 60
    assert btn.cget("anchor") == "e"
    assert btn.cget("corner_radius") == 12.0
    assert btn.cget("text_overflow") == "clip"
    assert btn.cget("cursor") == "hand2"
    assert btn.cget("state") == "normal"

    # __getitem__ and __setitem__
    btn["text"] = "Item Syntax"
    assert btn["text"] == "Item Syntax"

    # Theme lifecycle
    btn._on_theme_changed(get_theme())

    btn.destroy()


def test_base_control_variable_trace_lifecycle(root):
    set_theme("dark")
    var = tk.StringVar(value="Hello")
    btn = Button(root, text="Var Button", variable=var)
    btn.pack()
    root.update_idletasks()

    assert btn.variable is var
    btn._sync_variable_out("Updated Var")
    assert var.get() == "Updated Var"

    # Teardown should cleanly detach trace
    btn.destroy()


# ==============================================================================
# WIDGETS UTILS TESTS
# ==============================================================================

def test_widgets_utils_drawing_and_math():
    surf = Surface(100, 100)

    # 1. Vector checkmark
    draw_vector_checkmark(surf, 50.0, 50.0, scale=1.0, color="#ffffff")

    # 2. Vector chevrons (all directions)
    for direction in ("up", "down", "left", "right"):
        draw_vector_chevron(surf, 50.0, 50.0, scale=1.0, direction=direction, color="#8b5cf6")

    # 3. Vector minus and plus
    draw_vector_minus(surf, 50.0, 50.0, arm=10.0, color="#ffffff")
    draw_vector_plus(surf, 50.0, 50.0, arm=10.0, color="#ffffff")

    # 4. Focus rings
    draw_focus_ring(surf, 10.0, 10.0, 80.0, 30.0, 6.0, 6.0, color="#3b82f6")
    draw_circular_focus_ring(surf, 50.0, 50.0, radius=20.0, color="#3b82f6")

    # 5. Baseline computations
    by = compute_text_baseline_y(50.0, 14.0)
    assert by > 50.0
    iy = compute_icon_baseline_y(50.0, 16.0)
    assert iy > 50.0

    # 6. Truncate text
    assert truncate_text("", 100, 12) == ""
    assert truncate_text("Short", 200, 12) == "Short"
    truncated = truncate_text("A very long sentence that definitely exceeds the maximum pixel width allowed", 50, 14)
    assert truncated.endswith("...")

    # 7. Anchor normalization
    assert normalize_anchor(None) == "center"
    assert normalize_anchor("w") == "w"
    assert normalize_anchor("left") == "w"
    assert normalize_anchor("west") == "w"
    assert normalize_anchor("e") == "e"
    assert normalize_anchor("right") == "e"
    assert normalize_anchor("east") == "e"
    assert normalize_anchor("center") == "center"
    assert normalize_anchor("c") == "center"
    assert normalize_anchor("middle") == "center"
    assert normalize_anchor("unknown") == "center"

    # 8. Measure text dimensions
    w, h = measure_text_dimensions("Hello World", font_size=14.0)
    assert w > 0
    assert h > 0

    w_empty, h_empty = measure_text_dimensions("", font_size=14.0)
    assert w_empty >= 0

    # 9. Legacy measure surface
    ms = get_measure_surface()
    assert ms is not None

    # 10. Scrollbar geometry utilities
    is_needed, thumb_off, thumb_len, track_len, max_scroll = compute_scrollbar_geometry(
        viewport_len=100.0,
        content_len=500.0,
        scroll_pos=50.0,
    )
    assert is_needed is True
    assert max_scroll > 0

    drag_delta = compute_scroll_drag_delta(10.0, max_scroll, track_len, thumb_len)
    assert drag_delta > 0

    jump_target = compute_scroll_jump(40.0, track_len, max_scroll)
    assert jump_target >= 0


def test_widgets_utils_callbacks_and_traces(root):
    # 1. invoke_callback
    assert invoke_callback(None) is None
    assert invoke_callback(lambda: 42) == 42
    assert invoke_callback(lambda x: x * 2, 21) == 42
    assert invoke_callback(lambda *args: sum(args), 10, 20, 12) == 42
    # Non-inspectable / built-in
    assert invoke_callback(int, "42") == 42

    # 2. bind and unbind variable trace
    assert bind_variable_trace(None, lambda *a: None) is None
    unbind_variable_trace(None, "dummy_id")

    var = tk.StringVar(value="Init")
    trace_id = bind_variable_trace(var, lambda *a: None)
    assert trace_id is not None
    unbind_variable_trace(var, trace_id)

    # Trace fallbacks for older Tkinter / legacy Tcl
    mock_var = MagicMock()
    mock_var.trace_add.side_effect = RuntimeError("fallback")
    bind_variable_trace(mock_var, lambda *a: None)
    assert mock_var.trace.called

    mock_var.trace_remove.side_effect = RuntimeError("fallback")
    unbind_variable_trace(mock_var, "trace_id")
    assert mock_var.trace_vdelete.called

    # invoke_callback inspect exception fallback
    with patch("inspect.signature", side_effect=TypeError):
        def f_no_arg():
            return 99
        assert invoke_callback(f_no_arg, "arg1", "arg2") == 99



# ==============================================================================
# WINDOW SHAPING TESTS
# ==============================================================================

def test_window_shaping_utilities(root):
    # is_window_shaping_supported
    res = is_window_shaping_supported()
    assert isinstance(res, bool)

    # Frame widget shaping
    frm = tk.Frame(root, width=100, height=100)
    frm.pack()
    root.update_idletasks()

    # Valid shaping call
    applied = apply_round_rect_shape(frm, 100, 100, 12.0, 12.0)
    assert isinstance(applied, bool)

    # Invalid geometry -> delegates to clear_window_shape
    cleared = apply_round_rect_shape(frm, 0, 0, 0, 0)
    assert isinstance(cleared, bool)

    # Direct clear
    cleared2 = clear_window_shape(frm)
    assert isinstance(cleared2, bool)

    # Non-existent widget
    frm.destroy()
    assert apply_round_rect_shape(frm, 100, 100, 10.0, 10.0) is False
    assert clear_window_shape(frm) is False


# ==============================================================================
# TCL INTERPRETER EXTRACTION TESTS
# ==============================================================================

def test_tcl_interp_address_extraction(root):
    # None raises ValueError
    with pytest.raises(ValueError, match="Cannot extract Tcl interpreter address from None"):
        extract_interp_address(None)

    # 0 raises ValueError
    with pytest.raises(ValueError, match="Invalid NULL Tcl_Interp pointer address"):
        extract_interp_address(0)

    # Valid integer returns unchanged
    assert extract_interp_address(0x12345678) == 0x12345678

    # Real Tkinter root window
    addr = extract_interp_address(root)
    assert isinstance(addr, int)
    assert addr != 0

    # Object with interpaddr
    mock_obj = MagicMock(spec=["interpaddr"])
    mock_obj.interpaddr.return_value = 0x999999
    assert extract_interp_address(mock_obj) == 0x999999

    # Object with interp attribute
    mock_pypy = MagicMock(spec=[])
    mock_pypy.interp = 0x888888
    assert extract_interp_address(mock_pypy) == 0x888888

    # Object with _interp attribute
    mock_fallback = MagicMock(spec=[])
    mock_fallback._interp = 0x777777
    assert extract_interp_address(mock_fallback) == 0x777777

    # Unsupported object
    with pytest.raises(ValueError, match="does not expose a valid Tcl_Interp"):
        extract_interp_address("invalid_object")
