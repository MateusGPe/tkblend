"""
Native TTK Theme Engine Showcase with Blend2D.
Demonstrates modern vector-rendered TTK widgets in Dark and Light modes.
"""

import tkinter as tk
from tkinter import ttk
import tkblend


class ThemeShowcaseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend - Native TTK Theme Engine Showcase")
        self.root.geometry("820x680")
        self.root.minsize(700, 560)

        # Apply Blend2D TTK Dark Theme initially
        self.is_dark = True
        tkblend.apply_theme(self.root, dark_mode=self.is_dark, button_radius=8.0, entry_radius=8.0, enable_shadows=True)

        self._build_ui()

    def _build_ui(self):
        # Top Header Bar
        header = ttk.Frame(self.root, padding=20)
        header.pack(fill="x")

        title_lbl = ttk.Label(header, text="Blend2D Native TTK Theme Engine", font=("Helvetica", 16, "bold"))
        title_lbl.pack(side="left")

        self.toggle_btn = ttk.Button(
            header,
            text="☀️ Switch to Light Mode" if self.is_dark else "🌙 Switch to Dark Mode",
            command=self.toggle_mode
        )
        self.toggle_btn.pack(side="right")

        # Main Content Area
        content = ttk.Frame(self.root, padding=20)
        content.pack(fill="both", expand=True)

        # Section 1: Buttons & States
        btn_frame = ttk.Labelframe(content, text=" Modern Buttons (Hover, Active, Pressed, Disabled) ", padding=16)
        btn_frame.pack(fill="x", pady=8)

        b_row = ttk.Frame(btn_frame)
        b_row.pack(fill="x")

        b1 = ttk.Button(b_row, text="Primary Action", style="Accent.TButton", command=lambda: self.status_var.set("Primary Clicked!"))
        b1.pack(side="left", padx=8, pady=4)

        b2 = ttk.Button(b_row, text="Standard Action", style="TButton", command=lambda: self.status_var.set("Standard Clicked!"))
        b2.pack(side="left", padx=8, pady=4)

        b3 = ttk.Button(b_row, text="Disabled Button", style="TButton", state="disabled")
        b3.pack(side="left", padx=8, pady=4)

        # Section 2: Input Fields
        input_frame = ttk.Labelframe(content, text=" Text Fields & Entries ", padding=16)
        input_frame.pack(fill="x", pady=8)

        i_row = ttk.Frame(input_frame)
        i_row.pack(fill="x")

        ttk.Label(i_row, text="Username:").pack(side="left", padx=(0, 6))
        self.entry1 = ttk.Entry(i_row, width=20)
        self.entry1.insert(0, "antigravity_engineer")
        self.entry1.pack(side="left", padx=(0, 16))

        ttk.Label(i_row, text="Engine Status:").pack(side="left", padx=(0, 6))
        self.entry2 = ttk.Entry(i_row, width=18)
        self.entry2.insert(0, "JIT Accelerated")
        self.entry2.state(["readonly"])
        self.entry2.pack(side="left", padx=(0, 16))

        # Section 3: Checkbuttons & Radiobuttons
        choice_frame = ttk.Labelframe(content, text=" Indicators (Vector Antialiased Check & Radio) ", padding=16)
        choice_frame.pack(fill="x", pady=8)

        c_row = ttk.Frame(choice_frame)
        c_row.pack(fill="x")

        self.check1_var = tk.BooleanVar(value=True)
        self.check2_var = tk.BooleanVar(value=True)
        c1 = ttk.Checkbutton(c_row, text="Hardware Shadows", variable=self.check1_var, command=self.update_shadows)
        c1.pack(side="left", padx=10)

        c2 = ttk.Checkbutton(c_row, text="Vector Antialiasing", variable=self.check2_var)
        c2.pack(side="left", padx=10)

        self.radio_var = tk.StringVar(value="r1")
        r1 = ttk.Radiobutton(c_row, text="Fast Path", value="r1", variable=self.radio_var)
        r2 = ttk.Radiobutton(c_row, text="AsmJit X86/ARM", value="r2", variable=self.radio_var)
        r1.pack(side="left", padx=10)
        r2.pack(side="left", padx=10)

        # Section 4: Progressbar & Scrollbar
        metric_frame = ttk.Labelframe(content, text=" Smooth Progress & Pill Scrollbars ", padding=16)
        metric_frame.pack(fill="x", pady=8)

        self.pbar = ttk.Progressbar(metric_frame, orient="horizontal", value=72, maximum=100)
        self.pbar.pack(fill="x", padx=6, pady=6)

        self.scroll = ttk.Scrollbar(metric_frame, orient="horizontal")
        self.scroll.pack(fill="x", padx=6, pady=6)

        # Bottom Status Bar
        self.status_var = tk.StringVar(value="Theme engine ready • Blend2D PRGB32 zero-copy rasterization active.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, padding=(20, 8), font=("Helvetica", 10))
        status_bar.pack(side="bottom", fill="x")

    def toggle_mode(self):
        self.is_dark = not self.is_dark
        tkblend.apply_theme(
            self.root,
            dark_mode=self.is_dark,
            button_radius=8.0,
            entry_radius=8.0,
            enable_shadows=self.check1_var.get()
        )
        self.toggle_btn.configure(
            text="☀️ Switch to Light Mode" if self.is_dark else "🌙 Switch to Dark Mode"
        )
        self.status_var.set(f"Switched to {'Dark' if self.is_dark else 'Light'} mode.")

    def update_shadows(self):
        cfg = tkblend.get_theme_config()
        if cfg:
            cfg.enable_shadows = self.check1_var.get()
            tkblend.set_theme_config(cfg)
            self.root.update_idletasks()


def main():
    root = tk.Tk()
    app = ThemeShowcaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
