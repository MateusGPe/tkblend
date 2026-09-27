from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union, Tuple, Any, Dict, List, Callable
import logging
import re
import unicodedata

logger = logging.getLogger(__name__)


class MissingGlyphError(Exception):
    """Raised when a character/glyph is unsupported in strict mode."""
    pass


_CURRENT_FALLBACK_MODE: str = "warn"  # "strict", "warn", "silent"
_USER_REPLACEMENT_TABLE: Dict[str, str] = {}
_USER_FALLBACK_HOOKS: List[Callable[[str], Optional[str]]] = []

# Curated similarity transliteration table for common unicode symbols, typography, and emojis
SIMILARITY_REPLACEMENT_TABLE: Dict[str, str] = {
    # Typography & Punctuation
    "…": "...",
    "—": "--",
    "–": "-",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "«": "<<",
    "»": ">>",
    "•": "*",
    "·": "*",
    "‰": "%",
    "№": "No.",
    "™": "(TM)",
    "©": "(C)",
    "®": "(R)",
    "±": "+/-",
    "×": "x",
    "÷": "/",
    "≠": "!=",
    "≤": "<=",
    "≥": ">=",
    "≈": "~=",
    "∞": "inf",
    "√": "sqrt",
    "∑": "sum",
    "∆": "delta",
    "µ": "u",
    "°": "deg",
    "§": "sec.",
    "¶": "P",
    "†": "+",
    "‡": "++",

    # Mathematical / Directional Arrows
    "→": "->",
    "←": "<-",
    "↑": "^",
    "↓": "v",
    "↔": "<->",
    "⇒": "=>",
    "⇐": "<=",
    "⇔": "<=>",
    "➔": "->",
    "➜": "->",
    "►": ">",
    "◄": "<",
    "▲": "^",
    "▼": "v",

    # Common UI & Status Icons / Emojis
    "✓": "[v]",
    "✔": "[v]",
    "✅": "[v]",
    "✗": "[x]",
    "✘": "[x]",
    "❌": "[x]",
    "❎": "[x]",
    "⚠️": "[!]",
    "⚠": "[!]",
    "❗": "!",
    "❓": "?",
    "ℹ": "[i]",
    "ℹ️": "[i]",
    "⭐": "*",
    "★": "*",
    "☆": "*",
    "✨": "*",
    "❤️": "<3",
    "♥": "<3",
    "♡": "<3",
    "⚙": "[#]",
    "⚙️": "[#]",
    "🔍": "[?]",
    "🔎": "[?]",
    "💡": "[i]",
    "🚀": "=>",
    "🔥": "*",
    "👍": "+1",
    "👎": "-1",
    "🔒": "[lock]",
    "🔓": "[unlock]",
    "📁": "[dir]",
    "📂": "[dir]",
    "📄": "[doc]",
    "📝": "[edit]",
    "👤": "[user]",
    "👥": "[users]",
    "🔔": "[bell]",
    "🔕": "[mute]",
    "💬": "[msg]",
    "👁": "[view]",
    "🔗": "[link]",
    "🗑": "[del]",
    "📦": "[pkg]",
    "⏳": "[time]",
    "⏱": "[time]",
    "⏰": "[time]",
    "🔄": "[refresh]",
    "🔁": "[repeat]",
    "➕": "+",
    "➖": "-",
}


def set_glyph_fallback_mode(mode: str) -> None:
    """
    Set the global glyph fallback mode:
    - 'strict': Raises MissingGlyphError when a character cannot be natively resolved.
    - 'warn' (default): Emits logger.warning and substitutes with the most similar replacement.
    - 'silent': Transparently substitutes with the most similar replacement.
    """
    global _CURRENT_FALLBACK_MODE
    clean = str(mode).strip().lower()
    if clean not in ("strict", "warn", "silent"):
        raise ValueError(f"Invalid fallback mode '{mode}'. Choose from 'strict', 'warn', 'silent'.")
    _CURRENT_FALLBACK_MODE = clean


def get_glyph_fallback_mode() -> str:
    """Get the active global glyph fallback mode ('strict', 'warn', or 'silent')."""
    return _CURRENT_FALLBACK_MODE


def register_glyph_replacement(char_or_symbol: str, replacement: str) -> None:
    """Register a custom character/emoji fallback replacement string."""
    _USER_REPLACEMENT_TABLE[char_or_symbol] = replacement


def register_glyph_fallback_hook(hook: Callable[[str], Optional[str]]) -> None:
    """Register a custom callback hook for resolving missing character replacements."""
    _USER_FALLBACK_HOOKS.append(hook)


def get_similar_glyph(char: str) -> str:
    """
    Find the most visually/semantically similar ASCII or unicode replacement for an unsupported character:
    1. User custom replacement table
    2. User fallback hooks
    3. Curated similarity replacement table
    4. Unicode NFKD decomposition (stripping combining diacritics/accents)
    5. Fallback placeholder '?'
    """
    if not char:
        return char

    # 1. Custom user table
    if char in _USER_REPLACEMENT_TABLE:
        return _USER_REPLACEMENT_TABLE[char]

    # 2. Custom hooks
    for hook in _USER_FALLBACK_HOOKS:
        try:
            res = hook(char)
            if res is not None:
                return res
        except Exception as e:
            logger.debug("Error in user glyph fallback hook: %s", e)

    # 3. Curated table
    if char in SIMILARITY_REPLACEMENT_TABLE:
        return SIMILARITY_REPLACEMENT_TABLE[char]

    # 4. Unicode NFKD decomposition (e.g. 'é' -> 'e', 'ō' -> 'o')
    decomposed = unicodedata.normalize("NFKD", char)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    if stripped and stripped != char and stripped.isascii():
        return stripped

    # 5. Unicode character category fallback
    cat = unicodedata.category(char)
    if cat.startswith("Z"):  # Separator / space
        return " "
    elif cat.startswith("P"):  # Punctuation
        return "-"
    elif cat.startswith("S"):  # Symbol
        return "*"

    return "?"


def sanitize_text(
    text: str,
    font_family: str = "default",
    mode: Optional[str] = None,
    weight: int = 400,
    italic: bool = False,
    font_size: float = 14.0,
) -> str:
    """
    Sanitizes text by verifying glyph availability in the primary and fallback fonts.
    Applies configurable strictness mode ('strict', 'warn', 'silent') when missing characters occur.
    """
    if not text:
        return text

    effective_mode = mode.lower() if mode else _CURRENT_FALLBACK_MODE

    # Check if all characters are simple ASCII
    if text.isascii():
        return text

    try:
        try:
            from tkblend._tkblend import font_has_glyph, ensure_embedded_fonts
        except ImportError:
            from _tkblend import font_has_glyph, ensure_embedded_fonts
        ensure_embedded_fonts()
    except Exception as e:
        logger.debug("Failed checking font_has_glyph in sanitize_text: %s", e)
        return text

    result_chars = []
    i = 0
    while i < len(text):
        c = text[i]
        cp = ord(c)

        # ASCII characters always render cleanly
        if cp < 128:
            result_chars.append(c)
            i += 1
            continue

        # Check primary font
        has = font_has_glyph(font_family, cp, font_size, weight, italic)
        if not has:
            # Check embedded icon fonts & system fallbacks
            for fb_fam in ("fa-solid", "fa-regular", "fa-brands", "lucide", "sans-serif"):
                if font_has_glyph(fb_fam, cp, font_size, weight, italic):
                    has = True
                    break

        if has:
            result_chars.append(c)
        else:
            # Handle missing glyph according to strictness mode
            sub = get_similar_glyph(c)
            if effective_mode == "strict":
                raise MissingGlyphError(
                    f"Font '{font_family}' has no glyph for '{c}' (U+{cp:04X}, name={unicodedata.name(c, 'UNKNOWN')})"
                )
            elif effective_mode == "warn":
                logger.warning(
                    "Font '%s' missing glyph for '%s' (U+%04X); replaced with '%s'",
                    font_family,
                    c,
                    cp,
                    sub,
                )
            result_chars.append(sub)

        i += 1

    return "".join(result_chars)



@dataclass
class FontConfig:
    """
    Immutable-style font configuration descriptor for Blend2D text rendering.
    """
    family: str = "default"
    size: float = 12.0
    weight: int = 400
    bold: bool = False
    italic: bool = False

    @property
    def effective_weight(self) -> int:
        if self.bold and self.weight <= 400:
            return 700
        return self.weight

    def copy_with(
        self,
        family: Optional[str] = None,
        size: Optional[float] = None,
        weight: Optional[int] = None,
        bold: Optional[bool] = None,
        italic: Optional[bool] = None,
    ) -> FontConfig:
        return FontConfig(
            family=self.family if family is None else family,
            size=self.size if size is None else float(size),
            weight=self.weight if weight is None else int(weight),
            bold=self.bold if bold is None else bool(bold),
            italic=self.italic if italic is None else bool(italic),
        )

    def to_tk_font(self, root: Optional[Any] = None) -> Union[Tuple[Any, ...], Any]:
        """
        Convert this FontConfig to a Tk-compatible font specification tuple or
        tkinter.font.Font instance if a root widget is provided.
        """
        fam = extract_font_family(self.family)
        f_size = max(1, int(round(self.size)))
        is_bold = self.bold or self.effective_weight >= 600
        weight_str = "bold" if is_bold else "normal"
        slant_str = "italic" if self.italic else "roman"

        if root is not None:
            try:
                import tkinter.font as tkfont
                return tkfont.Font(root, family=fam, size=f_size, weight=weight_str, slant=slant_str)
            except Exception as e:
                logger.debug("Failed creating tkinter.font.Font for root %r: %s", root, e)

        style_parts = []
        if is_bold:
            style_parts.append("bold")
        if self.italic:
            style_parts.append("italic")

        if style_parts:
            return (fam, f_size, " ".join(style_parts))
        return (fam, f_size)


def extract_font_family(family_or_path: str) -> str:
    """
    Extract a clean font family name suitable for Tkinter/TTK from either a
    family name, 'default', or a font file path (.ttf, .otf, .ttc).
    """
    import os
    import sys

    raw = str(family_or_path or "").strip()

    if not raw or raw.lower() == "default":
        try:
            from _tkblend import get_active_font
            active = get_active_font()
            if active and active.lower() != "default":
                raw = active
        except Exception as e:
            logger.debug("Failed querying get_active_font: %s", e)

    if not raw or raw.lower() == "default":
        if sys.platform == "win32":
            return "Segoe UI"
        elif sys.platform == "darwin":
            return "SF Pro Display"
        else:
            return "DejaVu Sans"

    # If it's a file path
    if (
        raw.lower().endswith((".ttf", ".otf", ".ttc", ".woff", ".woff2"))
        or "/" in raw
        or "\\" in raw
    ):
        norm_path = raw.replace("\\", "/")
        base = os.path.splitext(os.path.basename(norm_path))[0]
        # Clean common weight/style suffixes from font file names
        cleaned = re.sub(
            r"[-_](?:Regular|Bold|Italic|Oblique|Light|Thin|Medium|SemiBold|Black|ExtraBold|ExtraLight)",
            "",
            base,
            flags=re.IGNORECASE,
        )
        cleaned = cleaned.replace("-", " ").replace("_", " ").strip()
        return cleaned or base

    return raw


def sync_tk_fonts(
    root: Any,
    font: Optional[Union[FontConfig, Tuple[Any, ...], str, Any]] = None,
    recursive: bool = True,
    preserve_overrides: bool = True,
) -> None:
    """
    Synchronize standard Tk named fonts, TTK styles, and classic Tk widgets
    with the specified tkblend font or active typography settings.

    Args:
        root: The Tk root, Toplevel, or container widget.
        font: Font specification (FontConfig, tuple, string, or None for active font).
        recursive: If True (default), traverses all child Tk widgets.
        preserve_overrides: If True (default), preserves widgets with custom fonts.
    """
    parsed = parse_font(font)
    fam = extract_font_family(parsed.family)
    f_size = max(1, int(round(parsed.size)))
    is_bold = parsed.bold or parsed.effective_weight >= 600
    is_italic = parsed.italic
    weight_str = "bold" if is_bold else "normal"
    slant_str = "italic" if is_italic else "roman"

    style_parts = []
    if is_bold:
        style_parts.append("bold")
    if is_italic:
        style_parts.append("italic")
    style_str = " ".join(style_parts)

    tk_font_tuple = (fam, f_size, style_str) if style_str else (fam, f_size)

    # 1. Update standard Tk named fonts
    try:
        import tkinter.font as tkfont
        named_fonts = {
            "TkDefaultFont": (f_size, weight_str, slant_str),
            "TkTextFont": (f_size, "normal", slant_str),
            "TkHeadingFont": (max(1, int(round(f_size * 1.25))), "bold", slant_str),
            "TkMenuFont": (f_size, "normal", "roman"),
            "TkCaptionFont": (f_size, "bold", "roman"),
            "TkSmallCaptionFont": (max(7, int(round(f_size * 0.85))), "normal", "roman"),
            "TkTooltipFont": (max(7, int(round(f_size * 0.85))), "normal", "roman"),
            "TkIconFont": (f_size, "normal", "roman"),
        }
        for name, (s, w, sl) in named_fonts.items():
            try:
                nf = tkfont.nametofont(name)
                kw = {"size": s, "weight": w, "slant": sl}
                if fam and fam != "default":
                    kw["family"] = fam
                nf.configure(**kw)
            except Exception as e:
                logger.debug("Failed updating Tk named font '%s': %s", name, e)
    except Exception as e:
        logger.debug("Failed configuring Tk named fonts: %s", e)

    # 2. Update TTK root and widget element styles
    try:
        import tkinter.ttk as ttk
        ttk_style = ttk.Style()
        ttk_style.configure(".", font=tk_font_tuple)
        ttk_style.configure("TLabel", font=tk_font_tuple)
        ttk_style.configure("TButton", font=tk_font_tuple)
        ttk_style.configure("TEntry", font=tk_font_tuple)
        ttk_style.configure("TCheckbutton", font=tk_font_tuple)
        ttk_style.configure("TRadiobutton", font=tk_font_tuple)
        ttk_style.configure("TNotebook.Tab", font=tk_font_tuple)
        heading_tuple = (fam, max(1, int(round(f_size * 1.25))), "bold")
        ttk_style.configure("Heading", font=heading_tuple)
    except Exception as e:
        logger.debug("Failed configuring TTK styles in sync_tk_fonts: %s", e)

    # 3. Recursively update classic Tk widgets
    if root is None:
        return

    import tkinter as tk

    def _sync_widget_font(w: Any) -> None:
        if not hasattr(w, "winfo_exists"):
            return
        try:
            if not w.winfo_exists():
                return
        except Exception as e:
            logger.debug("Error checking winfo_exists during font sync on %r: %s", w, e)
            return

        # Handle composite vector widgets with internal text entries (TextInput, SpinBox)
        if hasattr(w, "_update_entry_font") and hasattr(w, "_font_config"):
            if not preserve_overrides:
                setattr(w, "_custom_font_override", False)
                w._font_config = parsed
                w._update_entry_font()
            elif not getattr(w, "_custom_font_override", False):
                w._font_config = parsed
                w._update_entry_font()
            return

        # Skip pure tkblend vector widgets (they manage their own drawing surface)
        if hasattr(w, "_on_theme_changed") or hasattr(w, "_surface"):
            return

        if isinstance(w, (tk.Label, tk.Button, tk.Entry, tk.Text, tk.Listbox, tk.Checkbutton, tk.Radiobutton, tk.Message, tk.Spinbox, tk.OptionMenu, tk.LabelFrame)):
            if preserve_overrides:
                if getattr(w, "_tkblend_custom_font_override", False):
                    pass
                else:
                    try:
                        prev_injected = getattr(w, "_tkblend_injected_font", None)
                        curr_font = w.cget("font")
                        if prev_injected is not None and curr_font != prev_injected:
                            w._tkblend_custom_font_override = True
                        else:
                            w.configure(font=tk_font_tuple)
                            w._tkblend_injected_font = tk_font_tuple
                    except Exception as e:
                        logger.debug("Failed updating font on widget %r: %s", w, e)
            else:
                try:
                    w.configure(font=tk_font_tuple)
                    w._tkblend_injected_font = tk_font_tuple
                    if hasattr(w, "_tkblend_custom_font_override"):
                        w._tkblend_custom_font_override = False
                except Exception as e:
                    logger.debug("Failed configuring font on widget %r: %s", w, e)

        if recursive and hasattr(w, "winfo_children"):
            try:
                children = w.winfo_children()
            except Exception as e:
                logger.debug("Failed getting children during font sync on %r: %s", w, e)
                children = []
            for child in children:
                _sync_widget_font(child)

    _sync_widget_font(root)


def parse_font(
    font: Union[FontConfig, Tuple[Any, ...], str, None] = None,
    font_size: Optional[float] = None,
    font_family: Optional[str] = None,
    bold: Optional[bool] = None,
    italic: Optional[bool] = None,
    weight: Optional[Union[int, str]] = None,
    default_family: str = "default",
    default_size: float = 12.0,
) -> FontConfig:
    """
    Universally parse a font specification from Tkinter-style tuples, strings,
    FontConfig instances, tkinter.font.Font objects, or discrete kwargs.

    Supported formats:
    - Tuple: ("Segoe UI", 14, "bold italic") or ("Helvetica", 12) or ("Arial",)
    - String: "Segoe UI 14 bold italic" or "Consolas 12"
    - FontConfig instance
    - Kwargs: font_family="Segoe UI", font_size=14, bold=True, italic=False
    """
    family = default_family
    size = default_size
    is_bold = False
    is_italic = False
    num_weight = 400

    if isinstance(font, FontConfig):
        family = font.family
        size = font.size
        is_bold = font.bold
        is_italic = font.italic
        num_weight = font.weight
    elif isinstance(font, (tuple, list)):
        if len(font) >= 1 and font[0]:
            family = str(font[0])
        if len(font) >= 2 and font[1] is not None:
            try:
                size = abs(float(font[1]))
            except (ValueError, TypeError) as e:
                logger.debug("Failed parsing font size from tuple index 1 (%r): %s", font[1], e)
        if len(font) >= 3 and font[2]:
            style_spec = str(font[2]).lower()
            if "bold" in style_spec:
                is_bold = True
            if "italic" in style_spec or "oblique" in style_spec:
                is_italic = True
    elif isinstance(font, str) and font.strip():
        # Check for string representation e.g. "Helvetica 14 bold"
        tokens = font.strip().split()
        style_tokens = []
        parsed_size = None
        fam_tokens = []

        for token in reversed(tokens):
            lower_tok = token.lower()
            if lower_tok in ("bold", "italic", "oblique", "roman", "normal", "underline", "overstrike"):
                style_tokens.append(lower_tok)
            elif parsed_size is None and re.match(r"^-?\d+(\.\d+)?$", token):
                parsed_size = abs(float(token))
            else:
                fam_tokens.insert(0, token)

        if fam_tokens:
            family = " ".join(fam_tokens)
        if parsed_size is not None:
            size = parsed_size
        if "bold" in style_tokens:
            is_bold = True
        if "italic" in style_tokens or "oblique" in style_tokens:
            is_italic = True
    elif hasattr(font, "actual") and callable(getattr(font, "actual")):
        # Support tkinter.font.Font objects
        try:
            act = font.actual()
            family = act.get("family", family)
            size = abs(float(act.get("size", size)))
            is_bold = act.get("weight") == "bold"
            is_italic = act.get("slant") == "italic"
        except Exception as e:
            logger.debug("Failed querying font.actual() on %r: %s", font, e)

    # Apply explicit keyword overrides
    if font_family is not None:
        family = font_family
    if font_size is not None:
        size = float(font_size)
    if bold is not None:
        is_bold = bool(bold)
    if italic is not None:
        is_italic = bool(italic)
    if weight is not None:
        if isinstance(weight, str):
            w_lower = weight.lower()
            if w_lower in ("bold", "heavy", "black"):
                num_weight = 700
                is_bold = True
            elif w_lower in ("light", "thin"):
                num_weight = 300
            elif w_lower in ("normal", "regular", "medium"):
                num_weight = 400
            elif w_lower.isdigit():
                num_weight = int(w_lower)
        else:
            num_weight = int(weight)
            if num_weight >= 600:
                is_bold = True

    if is_bold and num_weight <= 400:
        num_weight = 700

    return FontConfig(
        family=family,
        size=size,
        weight=num_weight,
        bold=is_bold,
        italic=is_italic,
    )
