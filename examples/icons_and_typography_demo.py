"""
Comprehensive demonstration of embedded Font Awesome & Lucide icons,
inline icon markup, character similarity fallback, and strictness modes in tkblend.
"""

import tkinter as tk
import tkblend as tb
from tkblend.icons import Icons, parse_icon_markup
from tkblend.font import (
    sanitize_text,
    get_similar_glyph,
    set_glyph_fallback_mode,
    MissingGlyphError,
)


def main():
    root = tk.Tk()
    root.title("tkblend - Embedded Icons & Advanced Typography Demo")
    root.geometry("820x680")
    root.configure(bg="#11111b")

    tb.set_theme("tokyo_night")

    # Header Card
    header = tb.Card(root, padding=16)
    header.pack(fill="x", padx=16, pady=(16, 8))

    tb.Label(
        header,
        text=f"{Icons.ROCKET} tkblend Typography & Embedded Icons Suite {Icons.SPARKLES}",
        font=("Segoe UI", 18, "bold"),
    ).pack(anchor="w")

    tb.Label(
        header,
        text="Pure vector icons from embedded Font Awesome 6 & Lucide fonts with zero external file requirements.",
        font=("Segoe UI", 11),
    ).pack(anchor="w", pady=(4, 0))

    # Main Content Area
    main_frame = tb.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=16, pady=8)

    # Left Column: Icon Gallery & Inline Markup
    left_card = tb.Card(main_frame, padding=16)
    left_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

    tb.Label(left_card, text="Embedded Icon Sets & Helpers", font=("Segoe UI", 13, "bold")).pack(anchor="w")

    # Direct Buttons with Icons
    btn_row = tb.Frame(left_card)
    btn_row.pack(fill="x", pady=10)

    tb.Button(btn_row, text=f"{Icons.ROCKET} Launch", style="accent").pack(side="left", padx=(0, 6))
    tb.Button(btn_row, text=f"{Icons.SEARCH} Search").pack(side="left", padx=6)
    tb.Button(btn_row, text=f"{Icons.SETTINGS} Settings").pack(side="left", padx=6)

    # Inline Markup Demonstration
    tb.Label(left_card, text="Inline String Markup Tags:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12, 4))
    
    markup_examples = [
        "Deploy :fa:rocket: with {lucide:sparkles} high speed",
        "System status: :fa:check: Healthy {sun}",
        "Storage: {folder} / {file} ready",
    ]
    for ex in markup_examples:
        parsed = parse_icon_markup(ex)
        tb.Label(left_card, text=f"• {parsed}", font=("Segoe UI", 11)).pack(anchor="w", pady=2)

    # Right Column: Character Fallback & Strictness Modes
    right_card = tb.Card(main_frame, padding=16)
    right_card.pack(side="right", fill="both", expand=True, padx=(8, 0))

    tb.Label(right_card, text="Similarity Fallback & Character Sanitization", font=("Segoe UI", 13, "bold")).pack(anchor="w")

    tb.Label(
        right_card,
        text="Automatic transliteration for unsupported symbols, emojis, and special punctuation:",
        font=("Segoe UI", 10),
    ).pack(anchor="w", pady=(4, 8))

    fallback_pairs = [
        ("→ (Arrow Right)", get_similar_glyph("→")),
        ("⚠️ (Warning)", get_similar_glyph("⚠️")),
        ("✅ (Check Mark)", get_similar_glyph("✅")),
        ("❤️ (Heart)", get_similar_glyph("❤️")),
        ("— (Em Dash)", get_similar_glyph("—")),
        ("é (Accented e)", get_similar_glyph("é")),
    ]

    for original, sub in fallback_pairs:
        tb.Label(right_card, text=f"{original}  ⟶  '{sub}'", font=("Consolas", 10)).pack(anchor="w", pady=2)

    # Canvas Direct Vector Drawing Area
    canvas_card = tb.Card(root, padding=12)
    canvas_card.pack(fill="x", padx=16, pady=(8, 16))

    tb.Label(canvas_card, text="Direct Vector Surface Rendering:", font=("Segoe UI", 11, "bold")).pack(anchor="w")

    canvas = tb.BlendCanvas(canvas_card, width=760, height=80, bg="#181825", highlightthickness=0)
    canvas.pack(fill="x", pady=6)

    def draw_canvas(surf):
        surf.clear("#181825")
        # Direct icon drawing
        surf.draw_icon(Icons.ROCKET, 20, 48, size=28.0, color="#f38ba8")
        surf.draw_icon("sparkles", 70, 48, size=28.0, family="lucide", color="#f9e2af")
        surf.draw_icon("heart", 120, 48, size=28.0, family="fa-solid", color="#a6e3a1")
        surf.draw_icon("gear", 170, 48, size=28.0, family="fa-solid", color="#89b4fa")

        # Mixed Text & Icons
        surf.draw_text("Surface::draw_icon & rich fallback runs", 230, 48, font_size=15.0, color="#cdd6f4")

    canvas.on_draw(draw_canvas)

    root.mainloop()


if __name__ == "__main__":
    main()
