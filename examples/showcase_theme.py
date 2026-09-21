"""
Native TTK Theme Engine Showcase with Blend2D.
Demonstrates modern Shadcn Dark Glassmorphic vector-rendered TTK widgets in Dark and Light modes.
"""

import tkinter as tk
from tkinter import ttk
import tkblend


# Shared theme options — referenced by both initial apply and toggle
_THEME_OPTS = dict(
    button_radius=8.0,
    entry_radius=8.0,
    shadow_blur=8.0,
)


class ThemeShowcaseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend - Modern Blend2D Native TTK Theme Engine")
        self.root.geometry("880x760")
        self.root.minsize(780, 640)

        self.is_dark = True
        self.check1_var = tk.BooleanVar(value=True)  # shadows — declared early for apply_theme

        tkblend.apply_theme(self.root, dark_mode=self.is_dark, enable_shadows=True, **_THEME_OPTS)

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

        ttk.Label(
            title_frame, text="Blend2D Native TTK Theme", font=("Helvetica", 16, "bold")
        ).pack(anchor="w")
        ttk.Label(
            title_frame,
            text="Shadcn Glassmorphism • Electric Indigo • JIT Accelerated Blitting",
            font=("Helvetica", 9),
        ).pack(anchor="w", pady=(2, 0))

        btn_box = ttk.Frame(header)
        btn_box.pack(side="right")

        self.toggle_btn = ttk.Button(
            btn_box,
            text="☀️ Light Mode" if self.is_dark else "🌙 Dark Mode",
            style="Secondary.TButton",
            command=self.toggle_mode,
        )
        self.toggle_btn.pack(side="right", padx=(8, 0))

        # Main Content Notebook / Tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=20, pady=8)

        tab1 = ttk.Frame(notebook, style="Card.TFrame", padding=16)
        tab2 = ttk.Frame(notebook, style="Card.TFrame", padding=16)
        tab3 = ttk.Frame(notebook, style="Card.TFrame", padding=16)
        notebook.add(tab1, text="  Components & States  ")
        notebook.add(tab2, text="  Data & Indicators  ")
        notebook.add(tab3, text="  Floating Scroll & Editor  ")

        self._build_tab_components(tab1)
        self._build_tab_data(tab2)
        self._build_tab_editor(tab3)

        # Bottom Status Bar
        self.status_var = tk.StringVar(
            value="Theme engine ready • Blend2D PRGB32 zero-copy rasterization active."
        )
        ttk.Label(
            self.root, textvariable=self.status_var, padding=(24, 8), font=("Helvetica", 10)
        ).pack(side="bottom", fill="x")

    def _build_tab_components(self, parent: ttk.Frame):
        # Section 1: Modern Buttons
        btn_frame = ttk.Labelframe(
            parent,
            text=" Modern Buttons (Hover, Active, Pressed, Glow, Disabled) ",
            padding=16,
        )
        btn_frame.pack(fill="x", pady=(0, 10))

        b_row = ttk.Frame(btn_frame)
        b_row.pack(fill="x")

        button_specs = [
            ("Primary Action",  "Accent.TButton",      "Primary Action clicked: Electric Indigo button triggered."),
            ("Secondary",       "Secondary.TButton",   "Secondary Action clicked: Dark glass slate surface."),
            ("Outline",         "Outline.TButton",     "Outline Action clicked."),
            ("Ghost",           "Ghost.TButton",        "Ghost Action clicked."),
            ("Danger",          "Destructive.TButton", "Destructive Action clicked: Rose/Red state."),
        ]
        for label, style, msg in button_specs:
            ttk.Button(
                b_row, text=label, style=style,
                command=lambda m=msg: self.status_var.set(m),
            ).pack(side="left", padx=4, pady=4)

        ttk.Button(b_row, text="Disabled", style="TButton", state="disabled").pack(
            side="left", padx=4, pady=4
        )

        # Section 2: Input Fields & Dropdowns
        input_frame = ttk.Labelframe(
            parent,
            text=" Text Fields, Search, Combobox & Spinbox (Focus Glow & Placeholders) ",
            padding=16,
        )
        input_frame.pack(fill="x", pady=10)

        i_row1 = ttk.Frame(input_frame)
        i_row1.pack(fill="x", pady=(0, 8))

        ttk.Label(i_row1, text="Search Bar:", width=12).pack(side="left")
        self.search_entry = tkblend.SearchEntry(
            i_row1, placeholder="Search widgets, symbols, tokens...", width=28
        )
        self.search_entry.pack(side="left", padx=(0, 14))

        ttk.Label(i_row1, text="Placeholder Entry:", width=16).pack(side="left")
        self.entry_placeholder = tkblend.ThemedEntry(
            i_row1, placeholder="e.g. user@tkblend.io", width=20
        )
        self.entry_placeholder.pack(side="left")

        i_row2 = ttk.Frame(input_frame)
        i_row2.pack(fill="x", pady=(4, 0))

        ttk.Label(i_row2, text="Readonly:", width=12).pack(side="left")
        self.entry2 = ttk.Entry(i_row2, width=16)
        self.entry2.insert(0, "JIT Accelerated")
        self.entry2.state(["readonly"])
        self.entry2.pack(side="left", padx=(0, 14))

        ttk.Label(i_row2, text="Dropdown:", width=12).pack(side="left")
        self.combo = ttk.Combobox(
            i_row2, values=["High Performance", "Ultra Precision", "Battery Saver"], width=16
        )
        self.combo.current(0)
        self.combo.pack(side="left", padx=(0, 14))

        ttk.Label(i_row2, text="Threads:", width=8).pack(side="left")
        self.spin = ttk.Spinbox(i_row2, from_=1, to=64, width=6)
        self.spin.set(8)
        self.spin.pack(side="left")

        # Section 3: Sliders & Progress
        metric_frame = ttk.Labelframe(
            parent,
            text=" Sliders, Smooth Progressbar & Modern Docked Scrollbars ",
            padding=16,
        )
        metric_frame.pack(fill="x", pady=10)

        s_row = ttk.Frame(metric_frame)
        s_row.pack(fill="x", pady=(0, 6))
        ttk.Label(s_row, text="Engine Throttle (TScale):", width=22).pack(side="left")
        self.scale_var = tk.DoubleVar(value=68.0)
        self.scale = ttk.Scale(
            s_row, from_=0, to=100, variable=self.scale_var, command=self._on_scale_change
        )
        self.scale.pack(side="left", fill="x", expand=True, padx=10)
        self.scale_lbl = ttk.Label(s_row, text="68%", width=6)
        self.scale_lbl.pack(side="right")

        p_row = ttk.Frame(metric_frame)
        p_row.pack(fill="x", pady=6)
        ttk.Label(p_row, text="Buffer Pipeline (Pill):", width=22).pack(side="left")
        self.pbar = ttk.Progressbar(p_row, orient="horizontal", value=68, maximum=100)
        self.pbar.pack(side="left", fill="x", expand=True, padx=10)
        self.pbar_lbl = ttk.Label(p_row, text="68%", width=6)
        self.pbar_lbl.pack(side="right")

        sc_row = ttk.Frame(metric_frame)
        sc_row.pack(fill="x", pady=6)
        ttk.Label(sc_row, text="Modern Pill Scrollbar:", width=22).pack(side="left")
        self.scroll = ttk.Scrollbar(
            sc_row, orient="horizontal"
        )
        self.scroll.pack(side="left", fill="x", expand=True, padx=10)
        self.scroll.set(0.15, 0.65)
        ttk.Label(sc_row, text="15-65%", width=6).pack(side="right")

    def _build_tab_data(self, parent: ttk.Frame):
        # Checkbuttons & Radiobuttons
        choice_frame = ttk.Labelframe(
            parent,
            text=" Antialiased Vector Indicators (Check & Radio) ",
            padding=16,
        )
        choice_frame.pack(fill="x", pady=(0, 10))

        c_row = ttk.Frame(choice_frame)
        c_row.pack(fill="x")

        self.check2_var = tk.BooleanVar(value=True)
        self.check3_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            c_row, text="Hardware Soft Shadows",
            variable=self.check1_var, command=self.update_shadows,
        ).pack(side="left", padx=8)
        ttk.Checkbutton(c_row, text="Vector Antialiasing", variable=self.check2_var).pack(
            side="left", padx=8
        )
        ttk.Checkbutton(c_row, text="Glassmorphic Glow", variable=self.check3_var).pack(
            side="left", padx=8
        )
        tri = ttk.Checkbutton(c_row, text="Tri-State Pipeline")
        tri.state(["alternate"])
        tri.pack(side="left", padx=8)

        r_row = ttk.Frame(choice_frame)
        r_row.pack(fill="x", pady=(10, 0))

        self.radio_var = tk.StringVar(value="r1")
        for text, val in [
            ("Fast Path (Zero Copy)", "r1"),
            ("AsmJit X86/ARM Pipeline", "r2"),
            ("Fallback Renderer", "r3"),
        ]:
            ttk.Radiobutton(r_row, text=text, value=val, variable=self.radio_var).pack(
                side="left", padx=10
            )

        # Treeview Data Grid
        tree_frame = ttk.Labelframe(
            parent,
            text=" Modern Treeview Data Table With Docked Scrollbar ",
            padding=16,
        )
        tree_frame.pack(fill="both", expand=True, pady=10)

        tree_container = ttk.Frame(tree_frame)
        tree_container.pack(fill="both", expand=True)

        cols = ("Component", "Backend", "Latency", "Status")
        self.tree = ttk.Treeview(tree_container, columns=cols, show="headings", height=5)
        self.tree_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)

        self.tree.heading("Component", text="Engine Component")
        self.tree.heading("Backend", text="Rasterizer")
        self.tree.heading("Latency", text="Draw Latency")
        self.tree.heading("Status", text="State")
        self.tree.column("Component", width=180)
        self.tree.column("Backend", width=140)
        self.tree.column("Latency", width=120)
        self.tree.column("Status", width=120)

        demo_rows = [
            ("Button Element Spec",    "Blend2D PRGB32",  "0.04 ms", "⚡ JIT Accelerated"),
            ("Entry & Focus Halo",     "Blend2D PRGB32",  "0.03 ms", "⚡ Active"),
            ("Pill Progress Bar",      "Blend2D Vector",  "0.05 ms", "⚡ Realtime"),
            ("Indicator Vector Paths", "Blend2D Exact",   "0.02 ms", "⚡ Antialiased"),
            ("Docked Scrollbar",       "Blend2D PRGB32",  "0.03 ms", "⚡ Docked"),
            ("Themed Text Buffer",     "Blend2D Synced",  "0.02 ms", "⚡ Auto Sync"),
            ("Search Entry & Glow",    "Blend2D Focus",   "0.03 ms", "⚡ Halo Glow"),
            ("Scale Slider Trough",    "Blend2D Vector",  "0.03 ms", "⚡ Active"),
            ("Notebook Glass Tabs",    "Blend2D PRGB32",  "0.04 ms", "⚡ Smooth"),
            ("Dynamic Color Cache",    "Blend2D LRU",     "0.01 ms", "⚡ Cached"),
            ("Vector Antialiasing",    "Blend2D HighQ",   "0.02 ms", "⚡ Antialiased"),
            ("Async Surface Flush",    "Blend2D PRGB32",  "0.05 ms", "⚡ Zero-Copy"),
        ]
        for row in demo_rows:
            self.tree.insert("", "end", values=row)

        self.tree_scroll.pack(side="right", fill="y", padx=(2, 4), pady=2)
        self.tree.pack(side="left", fill="both", expand=True)

    def _build_tab_editor(self, parent: ttk.Frame):
        editor_frame = ttk.Labelframe(
            parent,
            text=" Themed Text Editor & Docked Pill Scrollbar ",
            padding=16,
        )
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
            "# Multi-line text editor with modern docked pill scrollbar\n"
            "editor = tkblend.ThemedText(root)\n"
            "editor.pack(fill='both', expand=True, padx=20, pady=10)\n\n"
            "# Seamless Dark / Light switching:\n"
            "# Calling tkblend.apply_theme(root, dark_mode=False) re-renders\n"
            "# all native Blend2D TTK elements, updates caret and selection colors,\n"
            "# and broadcasts <<ThemeChanged>> across all active windows.\n\n"
            "root.mainloop()\n"
        )

        self.themed_editor = tkblend.ThemedText(
            editor_frame, font=("Courier New", 10)
        )
        self.themed_editor.pack(fill="both", expand=True)
        self.themed_editor.insert("1.0", sample_code)

    # -------------------------------------------------------------------------
    # Event handlers
    # -------------------------------------------------------------------------

    def _on_scale_change(self, val):
        v = float(val)
        pct = f"{int(v)}%"
        self.scale_lbl.configure(text=pct)
        self.pbar_val = v
        self.pbar["value"] = v
        self.pbar_lbl.configure(text=pct)
        self.scale.update_idletasks()

    def _start_progress_animation(self):
        def _step():
            if not self.root.winfo_exists():
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
            enable_shadows=self.check1_var.get(),
            **_THEME_OPTS,
        )
        self.toggle_btn.configure(
            text="☀️ Light Mode" if self.is_dark else "🌙 Dark Mode"
        )
        self.status_var.set(
            f"Switched to {'Shadcn Dark' if self.is_dark else 'Apple-Clean Light'} mode."
        )

    def update_shadows(self):
        """Toggle shadow state without changing theme palette."""
        cfg = tkblend.get_theme_config()
        if cfg:
            cfg.enable_shadows = self.check1_var.get()
            tkblend.set_theme_config(cfg)
            self.root.update_idletasks()


def main():
    root = tk.Tk()
    ThemeShowcaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
