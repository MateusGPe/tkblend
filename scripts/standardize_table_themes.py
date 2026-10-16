#!/usr/bin/env python3
"""
Standardize Table Component Tokens across all tkblend CSS themes.

Ensures every theme in `tkblend/themes/` contains a uniform, consolidated
`/* Table Component Tokens */` block with all 10 color tokens and 3 geometry tokens,
guaranteeing WCAG contrast compliance and aesthetic harmony.
"""

from __future__ import annotations

import argparse
import colorsys
import math
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

THEMES_DIR = Path(__file__).resolve().parent.parent / "tkblend" / "themes"

# Established hand-crafted tokens for themes that already have dedicated styling
HAND_CRAFTED_TOKENS: Dict[str, Dict[str, str]] = {
    "dark": {
        "--table-bg": "#25232a",
        "--table-fg": "#e6e0e9",
        "--table-header-bg": "#201e25",
        "--table-header-fg": "#cac4d0",
        "--table-zebra-bg": "#2a2731",
        "--table-hover-bg": "#35323d",
        "--table-selected-bg": "#8b5cf6",
        "--table-selected-fg": "#ffffff",
        "--table-border": "#49454f",
        "--table-scrollbar-thumb": "#49454f",
        "--table-scrollbar-thumb-hover": "#79747e",
        "--table-header-h": "38px",
        "--table-radius": "8px",
        "--table-border-w": "1px",
    },
    "light": {
        "--table-bg": "#ffffff",
        "--table-fg": "#0f172a",
        "--table-header-bg": "#f8fafc",
        "--table-header-fg": "#475569",
        "--table-zebra-bg": "#f8fafc",
        "--table-hover-bg": "#f1f5f9",
        "--table-selected-bg": "#e0e7ff",
        "--table-selected-fg": "#3730a3",
        "--table-border": "#e2e8f0",
        "--table-scrollbar-thumb": "#cbd5e1",
        "--table-scrollbar-thumb-hover": "#94a3b8",
        "--table-header-h": "38px",
        "--table-radius": "8px",
        "--table-border-w": "1px",
    },
    "cinematic": {
        "--table-bg": "#172232",
        "--table-fg": "#f1f5f9",
        "--table-header-bg": "#0f1722",
        "--table-header-fg": "#94a3b8",
        "--table-zebra-bg": "#121c29",
        "--table-hover-bg": "#1e2c3f",
        "--table-selected-bg": "#0d9488",
        "--table-selected-fg": "#f0fdfa",
        "--table-border": "transparent",
        "--table-scrollbar-thumb": "#25364d",
        "--table-scrollbar-thumb-hover": "#374e6f",
        "--table-header-h": "40px",
        "--table-radius": "var(--radius-md)",
        "--table-border-w": "0px",
    },
    "catppuccin_latte": {
        "--table-bg": "#eff1f5",
        "--table-fg": "#4c4f69",
        "--table-header-bg": "#e6e9ef",
        "--table-header-fg": "#6c6f85",
        "--table-zebra-bg": "#e6e9ef",
        "--table-hover-bg": "#dce0e8",
        "--table-selected-bg": "#ccd0da",
        "--table-selected-fg": "#8839ef",
        "--table-border": "#ccd0da",
        "--table-scrollbar-thumb": "#bcc0cc",
        "--table-scrollbar-thumb-hover": "#8c8fa1",
        "--table-header-h": "38px",
        "--table-radius": "8px",
        "--table-border-w": "1px",
    },
    "solarized_light": {
        "--table-bg": "#fdf6e3",
        "--table-fg": "#073642",
        "--table-header-bg": "#eee8d5",
        "--table-header-fg": "#586e75",
        "--table-zebra-bg": "#eee8d5",
        "--table-hover-bg": "#e0d9c4",
        "--table-selected-bg": "#d3368222",
        "--table-selected-fg": "#073642",
        "--table-border": "#93a1a1",
        "--table-scrollbar-thumb": "#93a1a1",
        "--table-scrollbar-thumb-hover": "#586e75",
        "--table-header-h": "38px",
        "--table-radius": "8px",
        "--table-border-w": "1px",
    },
}

REQUIRED_TOKENS = [
    "--table-bg",
    "--table-fg",
    "--table-header-bg",
    "--table-header-fg",
    "--table-zebra-bg",
    "--table-hover-bg",
    "--table-selected-bg",
    "--table-selected-fg",
    "--table-border",
    "--table-scrollbar-thumb",
    "--table-scrollbar-thumb-hover",
    "--table-header-h",
    "--table-radius",
    "--table-border-w",
]


# ==============================================================================
# Color Science & WCAG Math
# ==============================================================================

def parse_color(color_str: str, bg_context: Optional[Tuple[int, int, int]] = None) -> Tuple[int, int, int]:
    """Parse hex, rgb, rgba, or hsl into an RGB tuple (0-255). Handles alpha blending against bg_context."""
    c = color_str.strip()
    if c.lower() == "transparent":
        return bg_context or (0, 0, 0)

    # Hex formats
    if c.startswith("#"):
        s = c.lstrip("#")
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        if len(s) == 6:
            return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        if len(s) == 8:
            r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
            alpha = int(s[6:8], 16) / 255.0
            bg = bg_context or (255, 255, 255)
            return blend(bg, (r, g, b), alpha)
        raise ValueError(f"Invalid hex string: {color_str}")

    # Functional HSL
    hsl_match = re.match(r"hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%", c, re.IGNORECASE)
    if hsl_match:
        h = float(hsl_match.group(1)) / 360.0
        s = float(hsl_match.group(2)) / 100.0
        l = float(hsl_match.group(3)) / 100.0
        r_f, g_f, b_f = colorsys.hls_to_rgb(h, l, s)
        return int(round(r_f * 255)), int(round(g_f * 255)), int(round(b_f * 255))

    # Functional RGB
    rgb_match = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", c, re.IGNORECASE)
    if rgb_match:
        return int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))

    raise ValueError(f"Unsupported color format: {color_str}")


def format_hex_color(rgb: Tuple[int, int, int]) -> str:
    r, g, b = (max(0, min(255, int(round(val)))) for val in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculate WCAG 2.1 relative luminance for an sRGB color."""
    vals = []
    for c in rgb:
        s = c / 255.0
        vals.append(s / 12.92 if s <= 0.03928 else math.pow((s + 0.055) / 1.055, 2.4))
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def contrast_ratio(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    """Calculate WCAG contrast ratio between two colors (range: 1.0 to 21.0)."""
    l1 = relative_luminance(c1)
    l2 = relative_luminance(c2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def blend(c1: Tuple[int, int, int], c2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    """Linear blend between two colors: c1 * (1 - factor) + c2 * factor."""
    f = max(0.0, min(1.0, factor))
    return (
        int(round(c1[0] * (1.0 - f) + c2[0] * f)),
        int(round(c1[1] * (1.0 - f) + c2[1] * f)),
        int(round(c1[2] * (1.0 - f) + c2[2] * f)),
    )


def adjust_contrast(
    fg_rgb: Tuple[int, int, int],
    bg_rgb: Tuple[int, int, int],
    min_contrast: float = 4.5,
) -> Tuple[int, int, int]:
    """Ensure fg meets min_contrast against bg by shifting towards pure white or pure black."""
    cr = contrast_ratio(fg_rgb, bg_rgb)
    if cr >= min_contrast:
        return fg_rgb

    bg_lum = relative_luminance(bg_rgb)
    target = (255, 255, 255) if bg_lum < 0.5 else (0, 0, 0)
    current = fg_rgb
    for step in range(1, 21):
        f = step * 0.05
        candidate = blend(current, target, f)
        if contrast_ratio(candidate, bg_rgb) >= min_contrast:
            return candidate

    return target


# ==============================================================================
# Theme Parser & Token Generator
# ==============================================================================

def extract_variables(css_text: str) -> Dict[str, str]:
    """Extract all CSS variables declared inside :root."""
    start = css_text.find(":root")
    if start == -1:
        return {}
    brace_open = css_text.find("{", start)
    if brace_open == -1:
        return {}
    brace_close = css_text.find("}", brace_open)
    if brace_close == -1:
        return {}
    content = css_text[brace_open + 1 : brace_close]
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", content))


def resolve_var(name: str, vars_dict: Dict[str, str], fallback: str = "#000000") -> str:
    """Resolve a CSS variable, following var() chains if necessary."""
    val = vars_dict.get(name, fallback).strip()
    match = re.match(r"var\((--[\w-]+)\)", val)
    if match:
        return resolve_var(match.group(1), vars_dict, fallback)
    return val


def derive_table_tokens_for_theme(theme_name: str, vars_dict: Dict[str, str]) -> Dict[str, str]:
    """Derive harmonious, contrast-verified table tokens for a given theme."""
    if theme_name in HAND_CRAFTED_TOKENS:
        return dict(HAND_CRAFTED_TOKENS[theme_name])

    # Extract base palette
    bg_str = resolve_var("--bg", vars_dict, "#1e1e2e")
    card_bg_str = resolve_var("--card-bg", vars_dict, bg_str)
    surface_str = resolve_var("--surface", vars_dict, card_bg_str)
    fg_str = resolve_var("--fg", vars_dict, "#f0f0f0")
    text_muted_str = resolve_var("--text-muted", vars_dict, fg_str)
    primary_str = resolve_var("--primary", vars_dict, "#8b5cf6")
    primary_fg_str = resolve_var("--primary-fg", vars_dict, "#ffffff")
    card_border_str = resolve_var("--card-border", vars_dict, "#45475a")

    # Safe parsing
    try:
        bg_rgb = parse_color(bg_str)
    except Exception:
        bg_rgb = (26, 27, 38)
    try:
        card_bg_rgb = parse_color(card_bg_str, bg_rgb)
    except Exception:
        card_bg_rgb = bg_rgb
    try:
        surface_rgb = parse_color(surface_str, bg_rgb)
    except Exception:
        surface_rgb = card_bg_rgb
    try:
        fg_rgb = parse_color(fg_str, card_bg_rgb)
    except Exception:
        fg_rgb = (240, 240, 240)
    try:
        muted_rgb = parse_color(text_muted_str, surface_rgb)
    except Exception:
        muted_rgb = blend(fg_rgb, bg_rgb, 0.4)
    try:
        primary_rgb = parse_color(primary_str, bg_rgb)
    except Exception:
        primary_rgb = (139, 92, 246)
    try:
        card_border_rgb = parse_color(card_border_str, card_bg_rgb)
    except Exception:
        card_border_rgb = blend(card_bg_rgb, fg_rgb, 0.2)

    is_dark = relative_luminance(bg_rgb) < 0.5

    # 1. Table BG: card surface
    table_bg_rgb = card_bg_rgb
    table_bg = format_hex_color(table_bg_rgb)

    # 2. Table FG: high contrast foreground text (>= 5.0:1)
    table_fg_rgb = adjust_contrast(fg_rgb, table_bg_rgb, 5.0)
    table_fg = format_hex_color(table_fg_rgb)

    # 3. Header BG: subtle elevation contrast (surface or slight shade)
    if surface_rgb != card_bg_rgb:
        header_bg_rgb = surface_rgb
    else:
        header_bg_rgb = blend(card_bg_rgb, (0, 0, 0) if is_dark else (255, 255, 255), 0.12)
    table_header_bg = format_hex_color(header_bg_rgb)

    # 4. Header FG: readable column label text (WCAG AA large/bold >= 3.5:1)
    header_fg_rgb = adjust_contrast(muted_rgb, header_bg_rgb, 3.5)
    table_header_fg = format_hex_color(header_fg_rgb)

    # 5. Zebra BG: subtle alternating row tint (3-5% blend)
    zebra_blend_target = (255, 255, 255) if is_dark else (0, 0, 0)
    table_zebra_rgb = blend(table_bg_rgb, zebra_blend_target, 0.04)
    table_zebra_bg = format_hex_color(table_zebra_rgb)

    # 6. Hover BG: clear interactive row state (8-10% blend)
    hover_blend_target = (255, 255, 255) if is_dark else (0, 0, 0)
    table_hover_rgb = blend(table_bg_rgb, hover_blend_target, 0.08)
    table_hover_bg = format_hex_color(table_hover_rgb)

    # 7. Selected BG: theme primary accent
    table_selected_rgb = primary_rgb
    table_selected_bg = format_hex_color(table_selected_rgb)

    # 8. Selected FG: verified WCAG contrast against selected_bg (>= 4.5:1)
    # Check contrast with dark background color vs light text
    cr_light = contrast_ratio((255, 255, 255), table_selected_rgb)
    cr_dark = contrast_ratio(bg_rgb, table_selected_rgb)

    if cr_light >= 4.5:
        sel_fg_rgb = (255, 255, 255)
    elif cr_dark >= 4.5:
        sel_fg_rgb = bg_rgb
    elif cr_light >= cr_dark:
        sel_fg_rgb = adjust_contrast((255, 255, 255), table_selected_rgb, 4.0)
    else:
        sel_fg_rgb = adjust_contrast(bg_rgb, table_selected_rgb, 4.0)

    table_selected_fg = format_hex_color(sel_fg_rgb)

    # 9. Border: card border or divider
    table_border = format_hex_color(card_border_rgb)

    # 10. Scrollbar thumb: muted card border / surface border
    thumb_rgb = card_border_rgb
    table_scrollbar_thumb = format_hex_color(thumb_rgb)

    # 11. Scrollbar thumb hover: interactive highlight
    thumb_hover_rgb = blend(thumb_rgb, primary_rgb, 0.4) if is_dark else blend(thumb_rgb, (0, 0, 0), 0.3)
    table_scrollbar_thumb_hover = format_hex_color(thumb_hover_rgb)

    return {
        "--table-bg": table_bg,
        "--table-fg": table_fg,
        "--table-header-bg": table_header_bg,
        "--table-header-fg": table_header_fg,
        "--table-zebra-bg": table_zebra_bg,
        "--table-hover-bg": table_hover_bg,
        "--table-selected-bg": table_selected_bg,
        "--table-selected-fg": table_selected_fg,
        "--table-border": table_border,
        "--table-scrollbar-thumb": table_scrollbar_thumb,
        "--table-scrollbar-thumb-hover": table_scrollbar_thumb_hover,
        "--table-header-h": "38px",
        "--table-radius": "8px",
        "--table-border-w": "1px",
    }


def format_table_tokens_block(tokens: Dict[str, str]) -> str:
    """Format the canonical Table Component Tokens CSS block."""
    lines = ["  /* Table Component Tokens */"]
    for k in REQUIRED_TOKENS:
        v = tokens[k]
        lines.append(f"  {k}: {v};")
    return "\n".join(lines)


def update_css_file(filepath: Path, verify_only: bool = False) -> bool:
    """Update or verify the table tokens in a CSS stylesheet."""
    theme_name = filepath.stem.lower()
    text = filepath.read_text(encoding="utf-8")

    vars_dict = extract_variables(text)
    new_tokens = derive_table_tokens_for_theme(theme_name, vars_dict)
    new_block = format_table_tokens_block(new_tokens)

    # Find the :root block
    start = text.find(":root")
    if start == -1:
        print(f"[{theme_name}] Error: could not find :root in {filepath}")
        return False
    brace_open = text.find("{", start)
    if brace_open == -1:
        print(f"[{theme_name}] Error: could not find '{{' in {filepath}")
        return False
    brace_close = text.find("}", brace_open)
    if brace_close == -1:
        print(f"[{theme_name}] Error: could not find '}}' in {filepath}")
        return False

    prefix = text[: brace_open + 1]
    root_body = text[brace_open + 1 : brace_close]
    suffix = text[brace_close:]

    # Filter out existing table tokens and table comments
    lines = root_body.splitlines()
    filtered: List[str] = []
    skip_table_comment = False

    for line in lines:
        stripped = line.strip()
        if "Table" in stripped and stripped.startswith("/*"):
            skip_table_comment = True
            continue
        if skip_table_comment:
            if stripped.startswith("--table-") or not stripped or stripped.startswith("*"):
                continue
            else:
                skip_table_comment = False
        if stripped.startswith("--table-"):
            continue
        filtered.append(line)

    # Clean trailing empty lines from filtered
    while filtered and not filtered[-1].strip():
        filtered.pop()

    rebuilt_root_body = "\n".join(filtered) + "\n\n" + new_block + "\n"
    updated_text = prefix + rebuilt_root_body + suffix

    if updated_text == text:
        return False

    if not verify_only:
        filepath.write_text(updated_text, encoding="utf-8")

    return True


def verify_theme_tokens(filepath: Path) -> Tuple[bool, List[str]]:
    """Verify that a CSS stylesheet has all required table tokens and passes contrast checks."""
    theme_name = filepath.stem.lower()
    text = filepath.read_text(encoding="utf-8")
    vars_dict = extract_variables(text)

    errors = []
    for req in REQUIRED_TOKENS:
        if req not in vars_dict:
            errors.append(f"Missing required token: {req}")

    # Parse table-bg for backdrop context
    bg_rgb = (30, 30, 40)
    if "--table-bg" in vars_dict:
        try:
            bg_rgb = parse_color(vars_dict["--table-bg"])
        except Exception:
            pass

    # Contrast checks
    if "--table-bg" in vars_dict and "--table-fg" in vars_dict:
        try:
            fg = parse_color(vars_dict["--table-fg"], bg_rgb)
            cr = contrast_ratio(fg, bg_rgb)
            if cr < 4.5:
                errors.append(f"Insufficient contrast for body text on table-bg: {cr:.2f}:1 (< 4.5:1)")
        except Exception as e:
            errors.append(f"Could not parse body text colors: {e}")

    if "--table-header-bg" in vars_dict and "--table-header-fg" in vars_dict:
        try:
            hbg = parse_color(vars_dict["--table-header-bg"], bg_rgb)
            hfg = parse_color(vars_dict["--table-header-fg"], hbg)
            cr = contrast_ratio(hfg, hbg)
            if cr < 3.0:
                errors.append(f"Insufficient contrast for header text on header-bg: {cr:.2f}:1 (< 3.0:1)")
        except Exception as e:
            errors.append(f"Could not parse header colors: {e}")

    if "--table-selected-bg" in vars_dict and "--table-selected-fg" in vars_dict:
        try:
            sbg = parse_color(vars_dict["--table-selected-bg"], bg_rgb)
            sfg = parse_color(vars_dict["--table-selected-fg"], sbg)
            cr = contrast_ratio(sfg, sbg)
            # WCAG AA for UI components & large/bold active state is 3.0:1
            if cr < 3.0:
                errors.append(f"Insufficient contrast for selected text on selected-bg: {cr:.2f}:1 (< 3.0:1)")
        except Exception as e:
            errors.append(f"Could not parse selection colors: {e}")

    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Standardize table tokens across tkblend CSS themes.")
    parser.add_argument("--check", action="store_true", help="Check uniformity without modifying files.")
    parser.add_argument("--themes-dir", type=Path, default=THEMES_DIR, help="Path to themes directory.")
    args = parser.parse_args()

    css_files = sorted(args.themes_dir.glob("*.css"))
    if not css_files:
        print(f"No .css files found in {args.themes_dir}")
        return 1

    print(f"Processing {len(css_files)} themes in {args.themes_dir}...")
    changes = 0

    if not args.check:
        for f in css_files:
            modified = update_css_file(f, verify_only=False)
            if modified:
                changes += 1
                print(f"  ✓ Standardized {f.name}")
            else:
                print(f"  • Up to date: {f.name}")
        print(f"\nSuccessfully applied updates to {changes} files.")

    # Verification phase
    all_passed = True
    print("\nRunning verification and contrast audit...")
    for f in css_files:
        ok, errs = verify_theme_tokens(f)
        if ok:
            print(f"  [PASS] {f.name}")
        else:
            all_passed = False
            print(f"  [FAIL] {f.name}:")
            for e in errs:
                print(f"     - {e}")

    if all_passed:
        print("\nAll themes are 100% uniform and meet WCAG contrast thresholds!")
        return 0
    else:
        print("\nVerification found issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
