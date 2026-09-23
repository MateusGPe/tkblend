"""
Typography, FontConfig, and universal font parser for tkblend.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union, Tuple, Any
import re


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
            except Exception:
                pass

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
        except Exception:
            pass

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
            except Exception:
                pass
    except Exception:
        pass

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
    except Exception:
        pass

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
        except Exception:
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
                    except Exception:
                        pass
            else:
                try:
                    w.configure(font=tk_font_tuple)
                    w._tkblend_injected_font = tk_font_tuple
                    if hasattr(w, "_tkblend_custom_font_override"):
                        w._tkblend_custom_font_override = False
                except Exception:
                    pass

        if recursive and hasattr(w, "winfo_children"):
            try:
                children = w.winfo_children()
            except Exception:
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
            except (ValueError, TypeError):
                pass
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
        except Exception:
            pass

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
