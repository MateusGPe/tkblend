"""
Unit tests for embedded font suite, Font Awesome & Lucide icons,
glyph detection, and similarity fallback system in tkblend.
"""

import pytest
import tkblend as tb
from tkblend.icons import (
    Icons,
    parse_icon_markup,
    FA_SOLID,
    FA_REGULAR,
    FA_BRANDS,
    LUCIDE,
)
from tkblend.font import (
    MissingGlyphError,
    set_glyph_fallback_mode,
    get_glyph_fallback_mode,
    register_glyph_replacement,
    register_glyph_fallback_hook,
    get_similar_glyph,
    sanitize_text,
)


class TestEmbeddedFontsAndIcons:
    def test_embedded_fonts_registered(self):
        """Verify embedded icon fonts are loaded into FontManager."""
        loaded = tb.get_loaded_fonts()
        for expected in ("fa-solid", "fa-regular", "fa-brands", "lucide"):
            assert expected in loaded, f"Expected {expected} in loaded fonts: {loaded}"

    def test_icon_constants_and_lookups(self):
        """Test accessing icons via constants, attributes, and lookups."""
        assert Icons.ROCKET == "\uf135"
        assert Icons.SEARCH == "\uf002"
        assert Icons.LUCIDE.sparkles == "\ue412"
        assert FA_SOLID["rocket"] == "\uf135"
        assert "rocket" in FA_SOLID
        assert "sparkles" in LUCIDE

        # Direct name lookup with prefixes
        assert Icons.get("fa:rocket") == "\uf135"
        assert Icons.get("fa-solid:rocket") == "\uf135"
        assert Icons.get("lucide:sparkles") == "\ue412"
        assert Icons.get("non-existent", "default_val") == "default_val"

    def test_inline_markup_parsing(self):
        """Test inline markup parser with :fa:...: and {...} syntax."""
        text = "Launch :fa:rocket: with {lucide:sparkles} and {heart}!"
        parsed = parse_icon_markup(text)
        assert "\uf135" in parsed
        assert "\ue412" in parsed
        assert parsed != text

        # Empty and plain text
        assert parse_icon_markup("") == ""
        assert parse_icon_markup("Plain text") == "Plain text"

    def test_similarity_fallback_transliteration(self):
        """Test character transliteration and similarity replacement."""
        assert get_similar_glyph("→") == "->"
        assert get_similar_glyph("←") == "<-"
        assert get_similar_glyph("✓") == "[v]"
        assert get_similar_glyph("❌") == "[x]"
        assert get_similar_glyph("⚠️") == "[!]"
        assert get_similar_glyph("é") == "e"
        assert get_similar_glyph("—") == "--"
        assert get_similar_glyph("…") == "..."

    def test_custom_glyph_replacement_and_hooks(self):
        """Test registering custom fallback replacements and hook callbacks."""
        register_glyph_replacement("Ω", "Ohm")
        assert get_similar_glyph("Ω") == "Ohm"

        def custom_hook(char: str):
            if char == "§":
                return "[SECTION]"
            return None

        register_glyph_fallback_hook(custom_hook)
        assert get_similar_glyph("§") == "[SECTION]"

    def test_fallback_strictness_modes(self):
        """Test strict, warn, and silent fallback modes."""
        # Unmapped unicode codepoint
        unmapped_str = "Test \U000E0001 symbol"

        # 1. Strict mode must raise MissingGlyphError
        set_glyph_fallback_mode("strict")
        assert get_glyph_fallback_mode() == "strict"
        with pytest.raises(MissingGlyphError):
            sanitize_text(unmapped_str, font_family="sans-serif")

        # 2. Silent mode must substitute without error
        set_glyph_fallback_mode("silent")
        assert get_glyph_fallback_mode() == "silent"
        res = sanitize_text(unmapped_str, font_family="sans-serif")
        assert res != unmapped_str
        assert "\U000E0001" not in res

        # 3. Warn mode
        set_glyph_fallback_mode("warn")
        assert get_glyph_fallback_mode() == "warn"
        res_warn = sanitize_text(unmapped_str, font_family="sans-serif")
        assert "\U000E0001" not in res_warn

        # Invalid mode
        with pytest.raises(ValueError):
            set_glyph_fallback_mode("invalid_mode")

    def test_surface_draw_icon_and_markup(self):
        """Test drawing icons and markup text on Surface without errors."""
        surface = tb.Surface(300, 150)
        surface.clear("#181825")

        # Draw icon directly
        surface.draw_icon(Icons.ROCKET, 10, 30, size=20.0, color="#f38ba8")
        surface.draw_icon("sparkles", 40, 30, size=20.0, family="lucide", color="#f9e2af")

        # Draw text with markup
        surface.draw_text("Deploy :fa:rocket: Now!", 70, 30, font_size=14.0, color="#cdd6f4")
        surface.draw_text("Features: {lucide:sparkles} Fast {check}", 10, 70, font_size=14.0, color="#a6e3a1")

        # Verify pixels were drawn
        assert surface.width == 300
        assert surface.height == 150
