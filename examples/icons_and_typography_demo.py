#!/usr/bin/env python3
"""
tkblend Showcase: Embedded Icons & Advanced Vector Typography Demo.
Demonstrates:
  - Pure vector Font Awesome 6 & Lucide glyph rendering
  - Antialiased typography and multiline text measurements
  - Dynamic palette switching across 13+ themes
  - Zero-TTK pure BaseControl widgets (Card, Button, Label, Badge, TextBox, OptionMenu)
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional

import tkblend as tb
from tkblend import (
    Card,
    Frame,
    Button,
    Label,
    Badge,
    TextBox,
    OptionMenu,
    Icons,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    ScalingTracker,
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
        header = Card(self, height=72, corner_radius=10, bg_color=pal.card_bg)
        header.pack(fill="x", padx=16, pady=(16, 10))

        title_box = tk.Frame(header, bg=header.bg_color)
        title_box.pack(side="left", padx=16, pady=10)

        tk.Label(
            title_box,
            text="✨ Typography & Embedded Vector Icons Suite",
            font=("sans-serif", 14, "bold"),
            bg=header.bg_color,
            fg=pal.fg,
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Zero-copy Blend2D font rendering, FA6 & Lucide icons with sub-pixel antialiasing.",
            font=("sans-serif", 9),
            bg=header.bg_color,
            fg=pal.text_muted,
        ).pack(anchor="w", pady=(2, 0))

        # Theme Selector
        self._theme_opt = OptionMenu(
            header,
            values=get_available_themes(),
            default_value=pal.name,
            command=self._on_theme_change,
            width=130,
            height=30,
        )
        self._theme_opt.pack(side="right", padx=14)

        # Main 2-Column Layout
        cols_frame = tk.Frame(self, bg=pal.bg)
        cols_frame.pack(fill="both", expand=True, padx=16, pady=6)

        # Left Column: Buttons with Icons & Badges
        left_card = Card(cols_frame, corner_radius=10, bg_color=pal.card_bg)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(left_card, text="Interactive Vector Buttons & Icons", font=("sans-serif", 11, "bold"), bg=left_card.bg_color, fg=pal.fg).pack(anchor="w", padx=14, pady=(12, 6))

        btn_row1 = tk.Frame(left_card, bg=left_card.bg_color)
        btn_row1.pack(fill="x", padx=14, pady=4)

        Button(btn_row1, text="Rocket Launch", icon="rocket", width=130, height=32).pack(side="left", padx=(0, 4))
        Button(btn_row1, text="Search Files", icon="search", width=120, height=32).pack(side="left", padx=4)
        Button(btn_row1, text="Settings", icon="gear", width=100, height=32).pack(side="left", padx=4)

        btn_row2 = tk.Frame(left_card, bg=left_card.bg_color)
        btn_row2.pack(fill="x", padx=14, pady=4)

        Button(btn_row2, text="Download", icon="download", width=110, height=30).pack(side="left", padx=(0, 4))
        Button(btn_row2, text="Play Music", icon="play", width=110, height=30).pack(side="left", padx=4)
        Button(btn_row2, text="Bookmark", icon="bookmark", width=110, height=30).pack(side="left", padx=4)

        # Badges section
        tk.Label(left_card, text="Status & Categorical Badges", font=("sans-serif", 11, "bold"), bg=left_card.bg_color, fg=pal.fg).pack(anchor="w", padx=14, pady=(16, 6))

        badge_row = tk.Frame(left_card, bg=left_card.bg_color)
        badge_row.pack(fill="x", padx=14, pady=4)

        Badge(badge_row, text="ONLINE", variant="success", dot=True).pack(side="left", padx=(0, 4))
        Badge(badge_row, text="CRITICAL", variant="danger", dot=True).pack(side="left", padx=4)
        Badge(badge_row, text="WARNING", variant="warning", dot=True).pack(side="left", padx=4)
        Badge(badge_row, text="PRO V3.0", variant="primary").pack(side="left", padx=4)

        # Right Column: Typography & Text Layout
        right_card = Card(cols_frame, corner_radius=10, bg_color=pal.card_bg)
        right_card.pack(side="right", fill="both", expand=True, padx=(6, 0))

        tk.Label(right_card, text="Antialiased Typography & Text Metrics", font=("sans-serif", 11, "bold"), bg=right_card.bg_color, fg=pal.fg).pack(anchor="w", padx=14, pady=(12, 6))

        type_box = tk.Frame(right_card, bg=right_card.bg_color)
        type_box.pack(fill="both", expand=True, padx=14, pady=4)

        tk.Label(type_box, text="Display Title (20pt Bold)", font=("sans-serif", 18, "bold"), bg=right_card.bg_color, fg=pal.fg).pack(anchor="w", pady=2)
        tk.Label(type_box, text="Heading 2 (14pt Medium)", font=("sans-serif", 13, "bold"), bg=right_card.bg_color, fg=pal.primary).pack(anchor="w", pady=2)
        tk.Label(type_box, text="Body Text: High-performance pure vector typography rendering directly to Tkinter drawables with zero TTK dependencies.", font=("sans-serif", 10), bg=right_card.bg_color, fg=pal.fg, wraplength=340, justify="left").pack(anchor="w", pady=4)
        tk.Label(type_box, text="Caption / Muted metadata text (9pt)", font=("sans-serif", 9), bg=right_card.bg_color, fg=pal.text_muted).pack(anchor="w", pady=2)

        # Multiline code preview
        tk.Label(right_card, text="Syntax Highlight / Code Box:", font=("sans-serif", 10, "bold"), bg=right_card.bg_color, fg=pal.fg).pack(anchor="w", padx=14, pady=(10, 2))

        tb_box = TextBox(right_card, height=90, font_size=10.0)
        tb_box.pack(fill="both", expand=True, padx=14, pady=(2, 12))
        tb_box.insert("1.0", "import tkblend as tb\n\nbtn = tb.Button(master, text='Launch', icon='rocket')\nbtn.pack(padx=20, pady=20)\n")


        cascade_bg_to_children(self, pal.bg, palette=pal)

    def _on_theme_change(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg, palette=pal)


def main():
    root = tk.Tk()
    root.title("tkblend - Embedded Icons & Advanced Typography")
    root.geometry("880x560")
    root.minsize(740, 460)

    app = IconsAndTypographyDemo(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
