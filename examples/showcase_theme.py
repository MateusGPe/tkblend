"""
Native TTK Theme Engine Showcase with Blend2D.
Demonstrates modern Shadcn Dark Glassmorphic vector-rendered TTK widgets in Dark and Light modes.
"""

import tkinter as tk
from tkinter import ttk
import tkblend


class ThemeShowcaseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend - Modern Blend2D Native TTK Theme Engine")
        self.root.geometry("880x760")
        self.root.minsize(780, 640)

        # Apply Blend2D TTK Dark Theme initially
        self.is_dark = True
        tkblend.apply_theme(
            self.root,
            dark_mode=self.is_dark,
            button_radius=8.0,
            entry_radius=8.0,
            enable_shadows=True,
            shadow_blur=8.0
        )

        self.anim_dir = 1
        self.pbar_val = 68.0

        self._build_ui()
        self._start_progress_animation()

    def _build_ui(self):
        # Top Header Bar
        header = ttk.Frame(self.root, padding=(24, 16, 24, 12))
        header.pack(fill="x")

        title_frame = ttk.Frame(header)
        title_frame.pack(side="left")

        title_lbl = ttk.Label(title_frame, text="Blend2D Native TTK Theme", font=("Helvetica", 16, "bold"))
        title_lbl.pack(anchor="w")

        subtitle_lbl = ttk.Label(
            title_frame,
            text="Shadcn Glassmorphism • Electric Indigo • JIT Accelerated Blitting",
            font=("Helvetica", 9)
        )
        subtitle_lbl.pack(anchor="w", pady=(2, 0))

        btn_box = ttk.Frame(header)
        btn_box.pack(side="right")

        self.toggle_btn = ttk.Button(
            btn_box,
            text="☀️ Light Mode" if self.is_dark else "🌙 Dark Mode",
            style="Secondary.TButton",
            command=self.toggle_mode
        )
        self.toggle_btn.pack(side="right", padx=(8, 0))

        # Main Content Notebook / Tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=20, pady=8)

        tab1 = ttk.Frame(notebook, padding=16)
        tab2 = ttk.Frame(notebook, padding=16)
        tab3 = ttk.Frame(notebook, padding=16)
        notebook.add(tab1, text="  Components & States  ")
        notebook.add(tab2, text="  Data & Indicators  ")
        notebook.add(tab3, text="  Floating Scroll & Editor  ")

        # =========================================================================
        # TAB 1: Components & States
        # =========================================================================

        # Section 1: Modern Buttons (Primary, Standard, Secondary, Destructive, Disabled)
        btn_frame = ttk.Labelframe(tab1, text=" Modern Buttons (Hover, Active, Pressed, Glow, Disabled) ", padding=16)
        btn_frame.pack(fill="x", pady=(0, 10))

        b_row = ttk.Frame(btn_frame)
        b_row.pack(fill="x")

        b1 = ttk.Button(
            b_row,
            text="Primary Action",
            style="Accent.TButton",
            command=lambda: self.status_var.set("Primary Action clicked: Electric Indigo button triggered.")
        )
        b1.pack(side="left", padx=4, pady=4)

        b2 = ttk.Button(
            b_row,
            text="Secondary",
            style="Secondary.TButton",
            command=lambda: self.status_var.set("Secondary Action clicked: Dark glass slate surface.")
        )
        b2.pack(side="left", padx=4, pady=4)

        b3 = ttk.Button(
            b_row,
            text="Outline",
            style="Outline.TButton",
            command=lambda: self.status_var.set("Outline Action clicked.")
        )
        b3.pack(side="left", padx=4, pady=4)

        b4 = ttk.Button(
            b_row,
            text="Ghost",
            style="Ghost.TButton",
            command=lambda: self.status_var.set("Ghost Action clicked.")
        )
        b4.pack(side="left", padx=4, pady=4)

        b5 = ttk.Button(
            b_row,
            text="Danger",
            style="Destructive.TButton",
            command=lambda: self.status_var.set("Destructive Action clicked: Rose/Red state.")
        )
        b5.pack(side="left", padx=4, pady=4)

        b6 = ttk.Button(b_row, text="Disabled", style="TButton", state="disabled")
        b6.pack(side="left", padx=4, pady=4)

        # Section 2: Input Fields & Dropdowns
        input_frame = ttk.Labelframe(tab1, text=" Text Fields, Search, Combobox & Spinbox (Focus Glow & Placeholders) ", padding=16)
        input_frame.pack(fill="x", pady=10)

        i_row1 = ttk.Frame(input_frame)
        i_row1.pack(fill="x", pady=(0, 8))

        ttk.Label(i_row1, text="Search Bar:", width=12).pack(side="left")
        self.search_entry = tkblend.SearchEntry(i_row1, placeholder="Search widgets, symbols, tokens...", width=28)
        self.search_entry.pack(side="left", padx=(0, 14))

        ttk.Label(i_row1, text="Placeholder Entry:", width=16).pack(side="left")
        self.entry_placeholder = tkblend.ThemedEntry(i_row1, placeholder="e.g. user@tkblend.io", width=20)
        self.entry_placeholder.pack(side="left")

        i_row2 = ttk.Frame(input_frame)
        i_row2.pack(fill="x", pady=(4, 0))

        ttk.Label(i_row2, text="Readonly:", width=12).pack(side="left")
        self.entry2 = ttk.Entry(i_row2, width=16)
        self.entry2.insert(0, "JIT Accelerated")
        self.entry2.state(["readonly"])
        self.entry2.pack(side="left", padx=(0, 14))

        ttk.Label(i_row2, text="Dropdown:", width=12).pack(side="left")
        self.combo = ttk.Combobox(i_row2, values=["High Performance", "Ultra Precision", "Battery Saver"], width=16)
        self.combo.current(0)
        self.combo.pack(side="left", padx=(0, 14))

        ttk.Label(i_row2, text="Threads:", width=8).pack(side="left")
        self.spin = ttk.Spinbox(i_row2, from_=1, to=64, width=6)
        self.spin.set(8)
        self.spin.pack(side="left")

        # Section 3: Sliders & Smooth Progress
        metric_frame = ttk.Labelframe(tab1, text=" Sliders, Smooth Progressbar & Floating Pill Scrollbars ", padding=16)
        metric_frame.pack(fill="x", pady=10)

        # Slider (Scale)
        s_row = ttk.Frame(metric_frame)
        s_row.pack(fill="x", pady=(0, 6))
        ttk.Label(s_row, text="Engine Throttle (TScale):", width=22).pack(side="left")
        self.scale_var = tk.DoubleVar(value=68.0)
        self.scale = ttk.Scale(s_row, from_=0, to=100, variable=self.scale_var, command=self._on_scale_change)
        self.scale.pack(side="left", fill="x", expand=True, padx=10)
        self.scale_lbl = ttk.Label(s_row, text="68%", width=6)
        self.scale_lbl.pack(side="right")

        # Progressbar
        p_row = ttk.Frame(metric_frame)
        p_row.pack(fill="x", pady=6)
        ttk.Label(p_row, text="Buffer Pipeline (Pill):", width=22).pack(side="left")
        self.pbar = ttk.Progressbar(p_row, orient="horizontal", value=68, maximum=100)
        self.pbar.pack(side="left", fill="x", expand=True, padx=10)
        self.pbar_lbl = ttk.Label(p_row, text="68%", width=6)
        self.pbar_lbl.pack(side="right")

        # Pill Scrollbar
        sc_row = ttk.Frame(metric_frame)
        sc_row.pack(fill="x", pady=6)
        ttk.Label(sc_row, text="Floating Pill Scrollbar:", width=22).pack(side="left")
        self.scroll = ttk.Scrollbar(sc_row, orient="horizontal", style="Floating.Horizontal.TScrollbar")
        self.scroll.pack(side="left", fill="x", expand=True, padx=10)
        self.scroll.set(0.15, 0.65)
        ttk.Label(sc_row, text="15-65%", width=6).pack(side="right")

        # =========================================================================
        # TAB 2: Data & Indicators
        # =========================================================================

        # Checkbuttons & Radiobuttons
        choice_frame = ttk.Labelframe(tab2, text=" Antialiased Vector Indicators (Check & Radio) ", padding=16)
        choice_frame.pack(fill="x", pady=(0, 10))

        c_row = ttk.Frame(choice_frame)
        c_row.pack(fill="x")

        self.check1_var = tk.BooleanVar(value=True)
        self.check2_var = tk.BooleanVar(value=True)
        self.check3_var = tk.BooleanVar(value=False)

        c1 = ttk.Checkbutton(c_row, text="Hardware Soft Shadows", variable=self.check1_var, command=self.update_shadows)
        c1.pack(side="left", padx=8)

        c2 = ttk.Checkbutton(c_row, text="Vector Antialiasing", variable=self.check2_var)
        c2.pack(side="left", padx=8)

        c3 = ttk.Checkbutton(c_row, text="Glassmorphic Glow", variable=self.check3_var)
        c3.pack(side="left", padx=8)

        c4 = ttk.Checkbutton(c_row, text="Tri-State Pipeline")
        c4.state(["alternate"])
        c4.pack(side="left", padx=8)

        r_row = ttk.Frame(choice_frame)
        r_row.pack(fill="x", pady=(10, 0))

        self.radio_var = tk.StringVar(value="r1")
        r1 = ttk.Radiobutton(r_row, text="Fast Path (Zero Copy)", value="r1", variable=self.radio_var)
        r2 = ttk.Radiobutton(r_row, text="AsmJit X86/ARM Pipeline", value="r2", variable=self.radio_var)
        r3 = ttk.Radiobutton(r_row, text="Fallback Renderer", value="r3", variable=self.radio_var)
        r1.pack(side="left", padx=10)
        r2.pack(side="left", padx=10)
        r3.pack(side="left", padx=10)

        # Treeview Data Grid
        tree_frame = ttk.Labelframe(tab2, text=" Modern Treeview Data Table With Floating Scrollbar ", padding=16)
        tree_frame.pack(fill="both", expand=True, pady=10)

        cols = ("Component", "Backend", "Latency", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=5)
        self.tree.heading("Component", text="Engine Component")
        self.tree.heading("Backend", text="Rasterizer")
        self.tree.heading("Latency", text="Draw Latency")
        self.tree.heading("Status", text="State")

        self.tree.column("Component", width=180)
        self.tree.column("Backend", width=140)
        self.tree.column("Latency", width=120)
        self.tree.column("Status", width=120)

        demo_rows = [
            ("Button Element Spec", "Blend2D PRGB32", "0.04 ms", "⚡ JIT Accelerated"),
            ("Entry & Focus Halo", "Blend2D PRGB32", "0.03 ms", "⚡ Active"),
            ("Pill Progress Bar", "Blend2D Vector", "0.05 ms", "⚡ Realtime"),
            ("Indicator Vector Paths", "Blend2D Exact", "0.02 ms", "⚡ Antialiased"),
            ("Floating Scrollbar", "Blend2D PRGB32", "0.03 ms", "⚡ Floating"),
            ("Themed Text Buffer", "Blend2D Synced", "0.02 ms", "⚡ Auto Sync"),
            ("Search Entry & Glow", "Blend2D Focus", "0.03 ms", "⚡ Halo Glow"),
            ("Scale Slider Trough", "Blend2D Vector", "0.03 ms", "⚡ Active"),
            ("Notebook Glass Tabs", "Blend2D PRGB32", "0.04 ms", "⚡ Smooth"),
            ("Dynamic Color Cache", "Blend2D LRU", "0.01 ms", "⚡ Cached"),
            ("Vector Antialiasing", "Blend2D HighQ", "0.02 ms", "⚡ Antialiased"),
            ("Async Surface Flush", "Blend2D PRGB32", "0.05 ms", "⚡ Zero-Copy"),
        ]
        for row in demo_rows:
            self.tree.insert("", "end", values=row)

        self.tree.pack(fill="both", expand=True)
        self.tree_scroller = tkblend.FloatingScrollbar(tree_frame, target=self.tree, orient="vertical", autohide=True)

        # =========================================================================
        # TAB 3: Floating Scroll & Editor
        # =========================================================================
        editor_frame = ttk.Labelframe(tab3, text=" Themed Text Editor & Floating Overlay Scrollbars (Auto-Hide on Idle) ", padding=16)
        editor_frame.pack(fill="both", expand=True, pady=(0, 10))

        sample_code = (
            "# tkblend Modern Native Blend2D TTK Theme Showcase\n"
            "# High-performance zero-copy rasterization with antialiasing and glow halos.\n\n"
            "import tkinter as tk\n"
            "import tkblend\n\n"
            "root = tk.Tk()\n"
            "tkblend.apply_theme(root, dark_mode=True, entry_radius=8.0, button_radius=8.0)\n\n"
            "# Themed Entry with automatic placeholder handling and focus glow\n"
            "entry = tkblend.ThemedEntry(root, placeholder='Enter search term...')\n"
            "entry.pack(padx=20, pady=10)\n\n"
            "# Multi-line text editor with auto-hiding floating scrollbar overlay\n"
            "editor = tkblend.ThemedText(root, autohide_scrollbar=True)\n"
            "editor.pack(fill='both', expand=True, padx=20, pady=10)\n\n"
            "# Seamless Dark / Light switching:\n"
            "# Calling tkblend.apply_theme(root, dark_mode=False) re-renders\n"
            "# all native Blend2D TTK elements, updates caret and selection colors,\n"
            "# and broadcasts <<ThemeChanged>> across all active windows.\n\n"
            "root.mainloop()\n"
        )

        self.themed_editor = tkblend.ThemedText(editor_frame, autohide_scrollbar=True, font=("Courier New", 10))
        self.themed_editor.pack(fill="both", expand=True)
        self.themed_editor.insert("1.0", sample_code)

        # Bottom Status Bar
        self.status_var = tk.StringVar(value="Theme engine ready • Blend2D PRGB32 zero-copy rasterization active.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, padding=(24, 8), font=("Helvetica", 10))
        status_bar.pack(side="bottom", fill="x")

    def _on_scale_change(self, val):
        v = float(val)
        self.scale_lbl.configure(text=f"{int(v)}%")
        self.pbar_val = v
        self.pbar["value"] = v
        self.pbar_lbl.configure(text=f"{int(v)}%")
        self.scale.update_idletasks()

    def _start_progress_animation(self):
        def _step():
            if not hasattr(self, "root") or not self.root.winfo_exists():
                return
            self.pbar_val += 0.4 * self.anim_dir
            if self.pbar_val >= 98.0:
                self.anim_dir = -1
            elif self.pbar_val <= 12.0:
                self.anim_dir = 1
            self.pbar["value"] = self.pbar_val
            self.pbar_lbl.configure(text=f"{int(self.pbar_val)}%")
            self.root.after(40, _step)

        self.root.after(200, _step)

    def toggle_mode(self):
        self.is_dark = not self.is_dark
        tkblend.apply_theme(
            self.root,
            dark_mode=self.is_dark,
            button_radius=8.0,
            entry_radius=8.0,
            enable_shadows=self.check1_var.get(),
            shadow_blur=8.0
        )
        self.toggle_btn.configure(
            text="☀️ Light Mode" if self.is_dark else "🌙 Dark Mode"
        )
        self.status_var.set(f"Switched to {'Shadcn Dark' if self.is_dark else 'Apple-Clean Light'} mode.")

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
