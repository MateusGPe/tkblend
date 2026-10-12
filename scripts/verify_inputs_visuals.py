import os
import sys
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageGrab

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkblend as tb
from tkblend.widgets import Entry, SearchEntry, TextBox, ComboBox, Card, Label
from tkblend.theme import set_theme, get_theme

def capture_visuals():
    root = tk.Tk()
    root.title("Inputs Visual Verification")
    root.geometry("600x520")
    set_theme("dark")
    root.configure(bg=get_theme().bg)

    pal = get_theme()

    card = Card(root, width=540, height=460)
    card.pack(fill="both", expand=True, padx=30, pady=30)

    content = tk.Frame(card, bg=pal.card_bg)
    content.pack(fill="both", expand=True, padx=20, pady=20)

    lbl = Label(content, text="Enhanced Anti-Aliased Inputs with Drop Shadows", width=480, height=26)
    lbl.pack(anchor="w", pady=(0, 10))

    combo = ComboBox(
        content,
        values=["High Performance", "Balanced", "Power Saver"],
        value="High Performance",
        width=300,
        height=38,
    )
    combo.pack(fill="x", pady=(0, 10))

    entry = Entry(content, text="Material Design 3 Vector Entry", width=300, height=38)
    entry.pack(fill="x", pady=(0, 10))

    search = SearchEntry(content, placeholder="Search vector primitives...", width=300, height=38)
    search.pack(fill="x", pady=(0, 10))

    textbox = TextBox(content, width=300, height=85)
    textbox.pack(fill="x", pady=(0, 10))
    textbox.insert("1.0", "Smooth anti-aliased multiline text editor frame with elevation shadow.")

    root.update_idletasks()
    root.update()

    for w in [card, combo, entry, search, textbox, lbl]:
        if hasattr(w, "paint_and_blit"):
            w.paint_and_blit()

    root.update_idletasks()
    root.update()

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()

    out_path = PROJECT_ROOT / "screenshots" / "inputs_verification.png"
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save(str(out_path))
    print(f"Captured: {out_path} ({img.size})")

    root.destroy()

if __name__ == "__main__":
    capture_visuals()
