import sys
import types
import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch
from tkblend.surface import Surface
from tkblend.controller import NativeController
from tkblend.theme import (
    Palette,
    set_theme,
    get_theme,
    get_available_themes,
    to_tk_hex,
    resolve_color_failsafe,
    resolve_theme_color,
    bind_theme_changed,
    unbind_theme_changed,
    flush_theme_queue,
    is_system_dark,
    detect_system_theme,
    auto_theme,
    stop_auto_theme,
    apply_theme,
    inject_theme,
    get_palette,
    set_dark_mode,
    set_theme_variable,
    get_preset_semantic_colors,
    SafeWeakMethod,
    blend_color_hex,
    adjust_brightness,
    get_contrast_color,
    to_tk_color,
)
from tkblend.font import (
    FontConfig,
    parse_font,
    sync_tk_fonts,
    extract_font_family,
    get_similar_glyph,
    sanitize_text,
    register_glyph_fallback_hook,
    set_glyph_fallback_mode,
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


# ==============================================================================
# THEME TESTS
# ==============================================================================

def test_to_tk_hex_comprehensive():
    # Null and empty
    assert to_tk_hex(None) == "#000000"
    assert to_tk_hex(123) == "#000000"
    assert to_tk_hex("") == "#000000"
    assert to_tk_hex("transparent") == "#000000"
    assert to_tk_hex("none") == "#000000"

    # Hex variations
    assert to_tk_hex("#112233") == "#112233"
    assert to_tk_hex("#112233aa") == "#112233"
    assert to_tk_hex("#abc") == "#aabbcc"
    assert to_tk_hex("#abcd") == "#aabbcc"

    # RGB strings
    assert to_tk_hex("rgb(255, 128, 0)") == "#ff8000"
    assert to_tk_hex("rgba(0, 255, 0, 0.5)") == "#00ff00"


def test_resolve_theme_color_and_failsafe():
    set_theme("dark")

    # Transparent & None
    assert resolve_color_failsafe("transparent") == "#00000000"
    assert resolve_color_failsafe("none") == "#00000000"

    # Semantic tokens
    res = resolve_theme_color("primary")
    assert res.startswith("#")

    # Alpha parameter
    with_alpha = resolve_color_failsafe("#ffffff", alpha=0.5)
    assert len(with_alpha) == 9  # #rrggbbaa


def test_theme_listeners_and_queue():
    called = []
    cb = lambda p: called.append(p.name)

    bind_theme_changed(cb)
    set_theme("light")
    assert "light" in called

    unbind_theme_changed(cb)
    called.clear()
    set_theme("dark")
    assert len(called) == 0

    flush_theme_queue()


def test_system_theme_detection_and_autotheme(root):
    # Test system dark and detect system theme with fallback
    assert isinstance(is_system_dark(), bool)
    assert detect_system_theme() in ("dark", "light")

    # Mock darkdetect
    mock_dd_dark = types.ModuleType("darkdetect")
    mock_dd_dark.isDark = lambda: True
    mock_dd_dark.theme = lambda: "Dark"
    mock_dd_dark.isLight = lambda: False
    with patch.dict(sys.modules, {"darkdetect": mock_dd_dark}):
        assert is_system_dark() is True
        assert detect_system_theme() == "dark"

    mock_dd_light = types.ModuleType("darkdetect")
    mock_dd_light.isDark = lambda: False
    mock_dd_light.isLight = lambda: True
    mock_dd_light.theme = lambda: "Light"
    with patch.dict(sys.modules, {"darkdetect": mock_dd_light}):
        assert is_system_dark() is False
        assert detect_system_theme() == "light"

    # Auto theme
    cleanup = auto_theme(root=root, listen=False)
    assert callable(cleanup)
    cleanup()
    stop_auto_theme()


def test_apply_and_inject_theme_recursive(root):
    # Setup standard Tk widgets
    frm = tk.Frame(root)
    frm.pack()
    lbl = tk.Label(frm, text="Test Label")
    lbl.pack()
    cnv = tk.Canvas(frm, width=50, height=50)
    cnv.pack()
    root.update_idletasks()

    # Apply theme
    cleanup = apply_theme(root, "dark", recursive=True, preserve_overrides=False)
    root.update_idletasks()
    assert str(root.cget("background")).startswith("#")

    # Switch theme
    set_theme("light")
    root.update_idletasks()

    cleanup()


# ==============================================================================
# FONT TESTS
# ==============================================================================

def test_font_config_and_parsing(root):
    # Parse from FontConfig
    fc = FontConfig(family="Roboto", size=15.0, weight=600, italic=True)
    assert parse_font(fc) == fc
    assert fc.family == "Roboto"
    assert fc.size == 15.0
    assert fc.weight == 600
    assert fc.italic is True
    assert fc.effective_weight == 600

    # to_tk_font tuple
    tk_spec = fc.to_tk_font(None)
    assert tk_spec == ("Roboto", 15, "bold italic")
    fc_over = fc.copy_with(size=18.0)
    assert fc_over.size == 18.0

    # to_tk_font with root
    tk_font = fc.to_tk_font(root)
    assert tk_font is not None

    # Parse from tuple
    p_tup = parse_font(("Courier", 12, "bold"))
    assert p_tup.family == "Courier"
    assert p_tup.size == 12.0
    assert p_tup.weight == 700

    # Parse from kwargs
    p_dict = parse_font(font_family="Arial", font_size=13.0, weight=400)
    assert p_dict.family == "Arial"
    assert p_dict.size == 13.0

    # Parse from string
    p_str = parse_font("Consolas 14")
    assert p_str.family == "Consolas"
    assert p_str.size == 14.0

    # Extract font family
    assert extract_font_family("/usr/share/fonts/Roboto-Bold.ttf") == "Roboto"
    assert extract_font_family("Arial") == "Arial"


def test_sync_tk_fonts_extended(root):
    lbl = tk.Label(root, text="Font Sync")
    lbl.pack()
    root.update_idletasks()

    # Sync with root=None
    sync_tk_fonts(None)

    # Sync with root and preserve_overrides=True
    sync_tk_fonts(root, font=("Arial", 12), preserve_overrides=True)

    # Sync with preserve_overrides=False
    sync_tk_fonts(root, font=("Courier", 14), preserve_overrides=False)
    root.update_idletasks()


# ==============================================================================
# CONTROLLER AND SURFACE COVERAGE
# ==============================================================================

def test_controller_extended_methods(root):
    ctrl = NativeController(root)
    assert ctrl.is_attached is True

    # 1. State mutators
    ctrl.set_hovered(True)
    assert ctrl.is_hovered is True
    ctrl.set_pressed(True)
    assert ctrl.is_pressed is True
    ctrl.set_focused(True)
    assert ctrl.is_focused is True
    ctrl.set_disabled(True)
    assert ctrl.is_disabled is True
    ctrl.set_checked(True)
    assert ctrl.is_checked is True

    ctrl.auto_hover = False
    assert ctrl.auto_hover is False
    ctrl.auto_press = False
    assert ctrl.auto_press is False
    ctrl.auto_focus = False
    assert ctrl.auto_focus is False

    ctrl.state = 0
    assert ctrl.state == 0

    ctrl.animated = False
    assert ctrl.animated is False
    ctrl.hover_t = 0.5
    assert ctrl.hover_t == pytest.approx(0.5, abs=0.01)
    ctrl.press_t = 0.5
    assert ctrl.press_t == pytest.approx(0.5, abs=0.01)
    ctrl.focus_t = 0.5
    assert ctrl.focus_t == pytest.approx(0.5, abs=0.01)

    # 2. Parent background
    ctrl.parent_bg = "#ff0000"
    ctrl.clear_parent_bg()

    # 3. Geometry request
    ctrl.set_geometry_request(100, 50)

    # 4. Surface binding and blitting
    surf = Surface(80, 40)
    ctrl.bind_surface(surf)
    assert ctrl.has_bound_surface is True
    assert isinstance(ctrl.bound_surface_id, int)
    ctrl.blit_surface(surf)
    ctrl.unbind_surface()
    assert ctrl.has_bound_surface is False

    with pytest.raises(TypeError):
        ctrl.bind_surface("invalid_type")

    with pytest.raises(TypeError):
        ctrl.blit_surface("invalid_type")

    # 5. Callback registration and clearing with bound methods and functions
    class CallbackTarget:
        def on_paint(self, s): pass
        def on_state(self, n, o): pass
        def on_click(self, x, y, b): pass
        def on_resize(self, w, h): pass
        def on_change(self, v): pass

    target = CallbackTarget()

    # Bound methods (test weakref obj_ref branch)
    ctrl.set_on_paint(target.on_paint)
    ctrl.set_on_state_changed(target.on_state)
    ctrl.set_on_click(target.on_click)
    ctrl.set_on_resize(target.on_resize)
    ctrl.set_on_change(target.on_change)

    # Clear callbacks
    ctrl.clear_on_paint()
    ctrl.clear_on_state_changed()
    ctrl.clear_on_click()
    ctrl.clear_on_resize()
    ctrl.clear_on_change()

    # Plain lambdas
    ctrl.set_on_paint(lambda s: None)
    ctrl.set_on_state_changed(lambda n, o: None)
    ctrl.set_on_click(lambda x, y, b: None)
    ctrl.set_on_resize(lambda w, h: None)
    ctrl.detach()


def test_theme_manager_and_weak_methods(root):
    # 1. get_palette and set_dark_mode
    pal = get_palette()
    assert pal is not None
    set_dark_mode(True)
    assert get_theme().name == "dark"
    set_dark_mode(False)
    assert get_theme().name == "light"

    # 2. set_theme_variable
    set_theme_variable("--test-theme-var", "#123456")

    # 3. get_preset_semantic_colors
    presets = get_preset_semantic_colors()
    assert "bg" in presets
    assert len(presets["bg"]) > 0

    # 4. SafeWeakMethod
    class ListenerObj:
        def on_theme(self, p):
            pass

    obj = ListenerObj()
    dead_called = []
    swm = SafeWeakMethod(obj.on_theme, dead_cb=lambda m: dead_called.append(m))
    assert swm() is not None
    assert swm == obj.on_theme
    assert hash(swm) is not None

    del obj
    # Object is now dead
    assert swm() is None


def test_color_manipulation_functions():
    # blend_color_hex
    assert blend_color_hex(None, "#ffffff", 0.5) is None
    assert blend_color_hex("#000000", "#ffffff", 0.0) == "#000000"
    assert blend_color_hex("#000000", "#ffffff", 1.0) == "#ffffff"
    blended = blend_color_hex("#000000", "#ffffff", 0.5)
    assert blended is not None

    # adjust_brightness
    assert adjust_brightness(None, 1.2) is None
    brighter = adjust_brightness("#888888", 1.5)
    assert brighter is not None
    darker = adjust_brightness("#888888", 0.5)
    assert darker is not None

    # get_contrast_color
    assert get_contrast_color(None) == "#ffffff"
    contrast_dark = get_contrast_color("#000000")
    assert contrast_dark == "#ffffff"
    contrast_light = get_contrast_color("#ffffff")
    assert contrast_light == "#0f172a"

    # to_tk_color alias
    assert to_tk_color("#123456") == "#123456"


def test_font_glyph_sanitization_and_fallbacks():
    # 1. get_similar_glyph
    assert get_similar_glyph("") == ""
    assert get_similar_glyph("a") in ("a", "?")
    assert get_similar_glyph("é") == "e"
    # Category fallbacks
    assert get_similar_glyph("\u2003") == " "  # em space -> space

    # Custom glyph fallback hook
    hook_called = []
    def custom_hook(char):
        if char == "¶":
            hook_called.append(char)
            return "P"
        if char == "§":
            raise RuntimeError("Testing hook error handling")
        return None

    register_glyph_fallback_hook(custom_hook)
    assert get_similar_glyph("¶") == "P"
    assert len(hook_called) == 1
    # Hook error handling branch (lines 179-180 in font.py)
    _ = get_similar_glyph("§")

    # 2. sanitize_text
    assert sanitize_text("") == ""
    assert sanitize_text("Simple ASCII") == "Simple ASCII"

    set_glyph_fallback_mode("silent")
    res_silent = sanitize_text("Hello é World", font_family="default")
    assert "Hello" in res_silent

    set_glyph_fallback_mode("warn")
    res_warn = sanitize_text("Text", font_family="default")
    assert res_warn == "Text"


def test_theme_presets_and_loaders(tmp_path, root):
    from tkblend.theme import (
        Palette,
        load_theme_file,
        load_theme_dir,
        cascade_bg_to_children,
        is_inside_card,
        is_ttkbootstrap_installed,
        stop_auto_theme,
    )
    import tkblend.theme as th

    # 1. Palette dict access and methods
    pal = get_palette()
    assert repr(pal).startswith("Palette(")
    assert pal["bg"] is not None
    assert pal["card-border"] is not None
    assert pal.get("bg") is not None
    assert pal.get("nonexistent_prop_xyz", "#abcdef") == "#abcdef"
    p_from = Palette.from_theme("dark")
    assert p_from.name == "dark"
    d = pal.to_dict()
    assert isinstance(d, dict)

    # 2. Theme file and dir loaders
    with pytest.raises(FileNotFoundError):
        load_theme_file(tmp_path / "does_not_exist.css")

    assert load_theme_dir(tmp_path / "nonexistent_dir") == []

    test_css = tmp_path / "custom_theme.css"
    test_css.write_text(":root { --primary: #334455; }", encoding="utf-8")
    loaded = load_theme_dir(tmp_path)
    assert "custom_theme" in loaded

    # 3. Background cascading
    f = tk.Frame(root)
    lbl = tk.Label(f, text="Nested")
    lbl.pack()
    f.pack()
    root.update_idletasks()

    cascade_bg_to_children(f, "#112233")
    assert not is_inside_card(lbl)

    # 4. Timer cleanup
    mock_timer = MagicMock()
    th._auto_theme_timer = mock_timer
    stop_auto_theme()
    assert mock_timer.cancel.called
    assert th._auto_theme_timer is None

    f.destroy()



