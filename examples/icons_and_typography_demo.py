#!/usr/bin/env python3
"""
tkblend Showcase: Embedded Icons & Advanced Vector Typography Demo.
Demonstrates:
  - Pure vector Font Awesome 6 & Lucide glyph rendering via Icons and NativeBlitCanvas
  - Subpixel anti-aliased typography and multiline text measurements
  - Dynamic palette switching across 13+ themes
  - Zero-TTK pure BaseControl widgets: Card, Button, Badge, TextBox, OptionMenu
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path as FilePath
from typing import Optional

# Ensure project root is in sys.path
PROJECT_ROOT = FilePath(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkblend as tb
from tkblend import (
    Card,
    Button,
    Badge,
    TextBox,
    OptionMenu,
    NativeBlitCanvas,
    Surface,
    Icons,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    ScalingTracker,
)


class IconShowcaseCanvas(NativeBlitCanvas):
    """Canvas demonstrating direct vector icon rasterization and inline icon markup."""

    def __init__(self, master: tk.Misc, width: int = 400, height: int = 140, **kwargs):
        super().__init__(master, width=width, height=height, on_paint=self._paint, **kwargs)

    def _paint(self, surf: Surface) -> None:
        pal = get_theme()
        s = ScalingTracker.get_scaling_factor(self)
        w, h = float(surf.width), float(surf.height)

        surf.clear(pal.card_bg)

        # 1. Direct FA and Lucide vector glyphs
        icons_to_draw = [
            (Icons.ROCKET, pal.primary, "Rocket"),
            (Icons.SEARCH, pal.secondary, "Search"),
            (Icons.GEAR, pal.accent, "Gear"),
            (Icons.DOWNLOAD, pal.success, "Download"),
            (Icons.PLAY, pal.warning, "Play"),
            (Icons.BOOKMARK, pal.danger, "Bookmark"),
        ]

        pad_x = 20.0 * s
        step_x = max(10.0, (w - pad_x * 2.0) / len(icons_to_draw))
        icon_y = 36.0 * s
        lbl_y = 66.0 * s

        for i, (glyph, col, label) in enumerate(icons_to_draw):
            ix = pad_x + i * step_x + step_x / 2.0
            surf.draw_icon(glyph, ix, icon_y, size=22.0 * s, color=col)
            surf.draw_text(label, ix, lbl_y, font_size=9.0 * s, color=pal.text_muted, align="center")

        # 2. Vector text with inline icon markup
        divider_y = 86.0 * s
        surf.stroke_line(pad_x, divider_y, w - pad_x, divider_y, pal.card_border, stroke_width=1.0 * s)

        surf.draw_text(
            "Markup: :fa:rocket: Blazing Speed • {lucide:sparkles} Subpixel Anti-aliasing",
            pad_x,
            112.0 * s,
            font_size=10.0 * s,
            color=pal.fg,
        )


class IconsAndTypographyDemo(tk.Frame):
    """Showcase of vector icons and typography."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Header Card
        header = Card(self, height=72)
        header.pack(fill="x", padx=16, pady=(16, 8))

        hdr_inner = tk.Frame(header, bg=pal.card_bg)
        hdr_inner.pack(fill="both", expand=True, padx=18, pady=(10, 14))

        title_box = tk.Frame(hdr_inner, bg=pal.card_bg)
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="✨ Typography & Embedded Vector Icons Suite",
            font=("sans-serif", 14, "bold"),
            bg=pal.card_bg,
            fg=pal.fg,
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Zero-copy Blend2D font rendering, FA6 & Lucide icons with sub-pixel antialiasing.",
            font=("sans-serif", 9),
            bg=pal.card_bg,
            fg=pal.text_muted,
        ).pack(anchor="w", pady=(2, 0))

        # Theme Selector
        self._theme_opt = OptionMenu(
            hdr_inner,
            values=sorted(get_available_themes()),
            current_value=pal.name,
            command=self._on_theme_change,
            width=130,
            height=30,
        )
        self._theme_opt.pack(side="right")

        # Main 2-Column Layout
        cols_frame = tk.Frame(self, bg=pal.bg)
        cols_frame.pack(fill="both", expand=True, padx=16, pady=6)

        # Left Column: Buttons with Icons & Badges
        left_card = Card(cols_frame)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        left_inner = tk.Frame(left_card, bg=pal.card_bg)
        left_inner.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(left_inner, text="Interactive Vector Buttons & Icons", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=(4, 6))

        btn_row1 = tk.Frame(left_inner, bg=pal.card_bg)
        btn_row1.pack(fill="x", pady=4)

        Button(btn_row1, text="🚀 Launch", width=115, height=34, auto_fit=True).pack(side="left", padx=(0, 4))
        Button(btn_row1, text="🔍 Search", width=115, height=34, auto_fit=True).pack(side="left", padx=4)
        Button(btn_row1, text="⚙️ Settings", width=115, height=34, auto_fit=True).pack(side="left", padx=4)

        btn_row2 = tk.Frame(left_inner, bg=pal.card_bg)
        btn_row2.pack(fill="x", pady=4)

        Button(btn_row2, text="📥 Download", width=115, height=32, auto_fit=True).pack(side="left", padx=(0, 4))
        Button(btn_row2, text="▶ Play", width=105, height=32, auto_fit=True).pack(side="left", padx=4)
        Button(btn_row2, text="🔖 Bookmark", width=115, height=32, auto_fit=True).pack(side="left", padx=4)

        # Vector Icon Canvas Display
        tk.Label(left_inner, text="Pure Vector Glyphs (NativeBlitCanvas)", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=(12, 4))

        self._icon_canvas = IconShowcaseCanvas(left_inner, height=130)
        self._icon_canvas.pack(fill="x", pady=(2, 8))

        # Badges section
        tk.Label(left_inner, text="Status & Categorical Badges", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=(8, 4))

        badge_row = tk.Frame(left_inner, bg=pal.card_bg)
        badge_row.pack(fill="x", pady=4)

        Badge(badge_row, text="ONLINE", variant="success", dot=True).pack(side="left", padx=(0, 4))
        Badge(badge_row, text="CRITICAL", variant="danger", dot=True).pack(side="left", padx=4)
        Badge(badge_row, text="WARNING", variant="warning", dot=True).pack(side="left", padx=4)
        Badge(badge_row, text="PRO V3.0", variant="primary").pack(side="left", padx=4)

        # Right Column: Typography & Text Layout
        right_card = Card(cols_frame)
        right_card.pack(side="right", fill="both", expand=True, padx=(6, 0))

        right_inner = tk.Frame(right_card, bg=pal.card_bg)
        right_inner.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(right_inner, text="Antialiased Typography & Text Metrics", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=(4, 6))

        type_box = tk.Frame(right_inner, bg=pal.card_bg)
        type_box.pack(fill="both", expand=True, pady=4)

        tk.Label(type_box, text="Display Title (18pt Bold)", font=("sans-serif", 18, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=2)
        tk.Label(type_box, text="Heading 2 (13pt Bold)", font=("sans-serif", 13, "bold"), bg=pal.card_bg, fg=pal.primary).pack(anchor="w", pady=2)
        tk.Label(type_box, text="Body Text: High-performance pure vector typography rendering directly to Tkinter drawables with zero TTK dependencies.", font=("sans-serif", 10), bg=pal.card_bg, fg=pal.fg, wraplength=380, justify="left").pack(anchor="w", pady=4)
        tk.Label(type_box, text="Caption / Muted metadata text (9pt)", font=("sans-serif", 9), bg=pal.card_bg, fg=pal.text_muted).pack(anchor="w", pady=2)

        # Multiline code preview
        tk.Label(right_inner, text="Syntax Highlight / Code Box:", font=("sans-serif", 10, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=(10, 2))

        tb_box = TextBox(right_inner, height=115)
        tb_box.pack(fill="both", expand=True, pady=(2, 6))
        tb_box.insert("1.0", "import tkblend as tb\n\nbtn = tb.Button(master, text='🚀 Launch')\nbtn.pack(padx=20, pady=20)\n")

        cascade_bg_to_children(self, pal.bg, palette=pal)

    def _on_theme_change(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg, palette=pal)
        self._icon_canvas.request_redraw()


def main():
    root = tk.Tk()
    root.title("tkblend - Embedded Icons & Advanced Typography")
    root.geometry("1020x680")
    root.minsize(880, 580)

    app = IconsAndTypographyDemo(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
