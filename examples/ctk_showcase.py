#!/usr/bin/env python3
"""
tkblend Showcase: CustomTkinter Vector Acceleration Bridge (`tkblend.ctk`).
Demonstrates:
  - Drop-in vector acceleration for CustomTkinter (CTk) applications
  - Replacing CTk's default Tkinter Canvas rasterizer with Blend2D JIT subpixel anti-aliasing
  - Zero modifications required to upstream CTK code
"""

from __future__ import annotations

import sys
import tkinter as tk
from typing import Optional

import tkblend as tb
from tkblend import (
    BlendDecorator,
    get_theme,
    set_theme,
)

# Attempt to load customtkinter with tkblend.ctk vector patch
_HAS_CTK = False
try:
    import customtkinter as ctk
    import tkblend.ctk
    tkblend.ctk.patch()
    _HAS_CTK = True
except ImportError:
    ctk = None  # type: ignore


class CTKBridgeInfoFrame(tk.Frame):
    """Fallback frame displayed when customtkinter package is not installed."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._build_ui()

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        card = BlendDecorator(self, radius=16, bg_color=pal.card_bg, shadow_blur=8, shadow_enabled=True)
        card.pack(fill="both", expand=True, padx=24, pady=24)

        body = tk.Frame(card, bg=pal.card_bg)
        body.pack(fill="both", expand=True, padx=16, pady=16)

        # Header info
        h_row = tk.Frame(body, background=pal.card_bg)
        h_row.pack(fill="x", padx=16, pady=(12, 6))

        tag1 = tk.Label(h_row, text="ZERO-COPY BRIDGE", fg=pal.primary, bg=pal.card_bg, font=("Segoe UI", 9, "bold"))
        tag1.pack(side="left")
        tag2 = tk.Label(h_row, text="SUBPIXEL ANTIALIASING", fg=pal.accent, bg=pal.card_bg, font=("Segoe UI", 9, "bold"))
        tag2.pack(side="left", padx=12)

        info_lbl = tk.Label(
            body,
            text=(
                "tkblend provides a drop-in acceleration bridge for CustomTkinter applications.\n\n"
                "By intercepting CustomTkinter's canvas draw calls and replacing them with Blend2D C++\n"
                "vector drawing primitives, your existing CTk apps gain:\n\n"
                "  1. 100% Subpixel Anti-Aliased rounded corners & borders (eliminating jagged edges)\n"
                "  2. Ultra-smooth gradients & soft elevation drop shadows\n"
                "  3. Direct Tk_PhotoPutBlock zero-copy blits for 60+ FPS performance\n"
                "  4. Complete compatibility with CTkButton, CTkFrame, CTkSlider, CTkSwitch, CTkEntry, etc."
            ),
            font=("Segoe UI", 10),
            fg=pal.fg,
            bg=pal.card_bg,
            justify="left",
        )
        info_lbl.pack(anchor="w", padx=16, pady=12)

        # Code snippet display
        code_card = BlendDecorator(body, radius=10, bg_color=pal.input_bg, shadow_blur=4, shadow_enabled=True)
        code_card.pack(fill="both", expand=True, padx=16, pady=8)

        code_text = (
            "import customtkinter as ctk\n"
            "import tkblend.ctk\n"
            "tkblend.ctk.patch()  # Auto-replaces canvas draw engine with Blend2D!\n\n"
            "app = ctk.CTk()\n"
            "btn = ctk.CTkButton(app, text='Vector Smooth Button')\n"
            "btn.pack(padx=20, pady=20)"
        )
        tk.Label(code_card, text=code_text, font=("Consolas", 9), fg=pal.fg, bg=pal.input_bg, justify="left").pack(anchor="w", padx=12, pady=6)


class CTKShowcaseApp:
    """Full CustomTkinter showcase window running on Blend2D vector acceleration."""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("tkblend.ctk Vector-Accelerated CustomTkinter Showcase")
        self.root.geometry("880x620")
        self.root.minsize(780, 500)
        ctk.set_appearance_mode("dark")

        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self.root, corner_radius=12)
        hdr.pack(fill="x", padx=20, pady=(16, 10))

        title = ctk.CTkLabel(hdr, text="CustomTkinter + Blend2D Vector Engine", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(side="left", padx=16, pady=12)

        mode_sw = ctk.CTkSwitch(hdr, text="Light Mode", command=self._toggle_mode)
        mode_sw.pack(side="right", padx=16, pady=12)

        # Main Content Grid
        content = ctk.CTkFrame(self.root, corner_radius=12)
        content.pack(fill="both", expand=True, padx=20, pady=(4, 16))

        # Left Column: Buttons, Sliders, Progress
        col1 = ctk.CTkFrame(content, corner_radius=10)
        col1.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(col1, text="Interactive Controls", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 6))

        btn1 = ctk.CTkButton(col1, text="Vector CTkButton", corner_radius=10)
        btn1.pack(fill="x", padx=14, pady=6)

        btn2 = ctk.CTkButton(col1, text="Secondary Style", fg_color="transparent", border_width=2, corner_radius=10)
        btn2.pack(fill="x", padx=14, pady=6)

        ctk.CTkLabel(col1, text="CTkSlider:").pack(anchor="w", padx=14, pady=(8, 2))
        slider = ctk.CTkSlider(col1, from_=0, to=100)
        slider.set(65)
        slider.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(col1, text="CTkProgressBar:").pack(anchor="w", padx=14, pady=(8, 2))
        pbar = ctk.CTkProgressBar(col1)
        pbar.set(0.75)
        pbar.pack(fill="x", padx=14, pady=4)

        # Right Column: Inputs, Tabs, Switches
        col2 = ctk.CTkFrame(content, corner_radius=10)
        col2.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(col2, text="Forms & Selection", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=14, pady=(12, 6))

        entry = ctk.CTkEntry(col2, placeholder_text="Enter text here...")
        entry.pack(fill="x", padx=14, pady=6)

        chk = ctk.CTkCheckBox(col2, text="Hardware Anti-Aliasing Active")
        chk.select()
        chk.pack(anchor="w", padx=14, pady=6)

        sw = ctk.CTkSwitch(col2, text="Zero-Copy PutBlock")
        sw.select()
        sw.pack(anchor="w", padx=14, pady=6)

        seg = ctk.CTkSegmentedButton(col2, values=["Option A", "Option B", "Option C"])
        seg.set("Option A")
        seg.pack(fill="x", padx=14, pady=12)

    def _toggle_mode(self):
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Light" if current == "Dark" else "Dark")

    def run(self):
        self.root.mainloop()


def main():
    if _HAS_CTK:
        app = CTKShowcaseApp()
        app.run()
    else:
        root = tk.Tk()
        root.title("tkblend.ctk Bridge Overview")
        root.geometry("820x560")
        root.minsize(700, 480)

        ScalingTracker.activate_high_dpi_awareness()
        set_theme("dark")

        frame = CTKBridgeInfoFrame(root)
        frame.pack(fill="both", expand=True)

        root.mainloop()


if __name__ == "__main__":
    main()
