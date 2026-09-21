"""
Native TTK Theme Engine Showcase with Blend2D.
Demonstrates modern Shadcn Dark Glassmorphic vector-rendered TTK widgets in Dark and Light modes.
Expanded control suite:
- Native TTK: Buttons, Entries, Check/Radio, Progressbar, Scrollbar, Scale, Notebook,
              Separator, Sizegrip, Panedwindow Sash, Menubutton, Treeitem Chevron.
- Modern Components: ToggleSwitch (animated), Badge, SegmentedControl, Card.
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
        self.root.geometry("920x800")
        self.root.minsize(820, 680)

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

        # Main Content Notebook / Tabs (4-Tab Comprehensive Showcase)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=20, pady=8)

        tab1 = ttk.Frame(notebook, style="Card.TFrame", padding=16)
        tab2 = ttk.Frame(notebook, style="Card.TFrame", padding=16)
        tab3 = ttk.Frame(notebook, style="Card.TFrame", padding=16)
        tab4 = ttk.Frame(notebook, style="Card.TFrame", padding=16)
        notebook.add(tab1, text="  Buttons, Menus & Badges  ")
        notebook.add(tab2, text="  Inputs, Switches & Sliders  ")
        notebook.add(tab3, text="  Data & Panes  ")
        notebook.add(tab4, text="  Editor, Surfaces & Containers  ")

        self._build_tab_actions(tab1)
        self._build_tab_inputs(tab2)
        self._build_tab_data(tab3)
        self._build_tab_editor(tab4)

        # Bottom Status Bar with TSizegrip
        status_bar = ttk.Frame(self.root)
        status_bar.pack(side="bottom", fill="x")

        self.status_var = tk.StringVar(
            value="Theme engine ready • Blend2D PRGB32 zero-copy rasterization active."
        )
        ttk.Label(
            status_bar, textvariable=self.status_var, padding=(24, 8), font=("Helvetica", 10)
        ).pack(side="left", fill="x", expand=True)

        self.sizegrip = ttk.Sizegrip(status_bar)
        self.sizegrip.pack(side="right", anchor="se", padx=2, pady=2)

    def _build_tab_actions(self, parent: ttk.Frame):
        # Section 1: Modern Buttons & Menubuttons
        btn_frame = ttk.Labelframe(
            parent,
            text=" Modern Buttons & Dropdown Menubuttons (Vector Chevrons & Glass Surfaces) ",
            padding=16,
        )
        btn_frame.pack(fill="x", pady=(0, 10))

        b_row1 = ttk.Frame(btn_frame)
        b_row1.pack(fill="x", pady=(0, 6))

        button_specs = [
            ("Primary Action",  "Accent.TButton",      "Primary Action clicked: Electric Indigo button triggered."),
            ("Secondary",       "Secondary.TButton",   "Secondary Action clicked: Dark glass slate surface."),
            ("Outline",         "Outline.TButton",     "Outline Action clicked."),
            ("Ghost",           "Ghost.TButton",       "Ghost Action clicked."),
            ("Danger",          "Destructive.TButton", "Destructive Action clicked: Rose/Red state."),
        ]
        for label, style, msg in button_specs:
            ttk.Button(
                b_row1, text=label, style=style,
                command=lambda m=msg: self.status_var.set(m),
            ).pack(side="left", padx=4, pady=2)

        ttk.Button(b_row1, text="Disabled", style="TButton", state="disabled").pack(
            side="left", padx=4, pady=2
        )

        # Menubuttons row
        b_row2 = ttk.Frame(btn_frame)
        b_row2.pack(fill="x", pady=(6, 0))

        mb_specs = [
            ("Actions",       "Secondary.TMenubutton"),
            ("Deploy",        "Accent.TMenubutton"),
            ("Filter Mode",   "Outline.TMenubutton"),
            ("Quick Options", "Ghost.TMenubutton"),
        ]
        for label, style in mb_specs:
            mb = ttk.Menubutton(b_row2, text=label, style=style)
            menu = tk.Menu(mb, tearoff=0)
            menu.add_command(label=f"{label} - Preset Alpha", command=lambda l=label: self.status_var.set(f"{l}: Preset Alpha selected"))
            menu.add_command(label=f"{label} - High Accuracy", command=lambda l=label: self.status_var.set(f"{l}: High Accuracy selected"))
            menu.add_separator()
            menu.add_command(label="Reset Defaults", command=lambda: self.status_var.set("Reset defaults triggered"))
            mb.configure(menu=menu)
            mb.pack(side="left", padx=4, pady=2)

        # Section 2: Status Badges & Chips
        badge_frame = ttk.Labelframe(
            parent,
            text=" Antialiased Status Badges & Chips (Pill Geometry & Dynamic Palette Sync) ",
            padding=16,
        )
        badge_frame.pack(fill="x", pady=10)

        badge_row = ttk.Frame(badge_frame)
        badge_row.pack(fill="x")

        badges = [
            ("Production", "success", True),
            ("Electric Indigo", "primary", True),
            ("Under Review", "warning", True),
            ("Critical Alert", "destructive", True),
            ("Cached LRU", "secondary", False),
            ("Vector v0.2", "outline", False),
        ]
        for text, variant, dot in badges:
            b = tkblend.Badge(badge_row, text=text, variant=variant, dot=dot)
            b.pack(side="left", padx=6, pady=4)

        # Section 3: Input Fields & Dropdowns
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

    def _build_tab_inputs(self, parent: ttk.Frame):
        # Section 1: Animated Toggle Switches
        sw_frame = ttk.Labelframe(
            parent,
            text=" Interactive Toggle Switches (60fps Animated Sliding Thumb & Native Element) ",
            padding=16,
        )
        sw_frame.pack(fill="x", pady=(0, 10))

        sw_row = ttk.Frame(sw_frame)
        sw_row.pack(fill="x")

        self.sw1_var = tk.BooleanVar(value=True)
        self.sw2_var = tk.BooleanVar(value=False)
        self.sw3_var = tk.BooleanVar(value=True)

        sw1_box = ttk.Frame(sw_row)
        sw1_box.pack(side="left", padx=12)
        ttk.Label(sw1_box, text="Hardware Acceleration:").pack(side="left", padx=(0, 8))
        self.sw1 = tkblend.ToggleSwitch(
            sw1_box, variable=self.sw1_var,
            command=lambda: self.status_var.set(f"Hardware Acceleration toggled: {self.sw1_var.get()}")
        )
        self.sw1.pack(side="left")

        sw2_box = ttk.Frame(sw_row)
        sw2_box.pack(side="left", padx=12)
        ttk.Label(sw2_box, text="Subpixel Antialiasing:").pack(side="left", padx=(0, 8))
        self.sw2 = tkblend.ToggleSwitch(
            sw2_box, variable=self.sw2_var,
            command=lambda: self.status_var.set(f"Subpixel AA toggled: {self.sw2_var.get()}")
        )
        self.sw2.pack(side="left")

        # Native TTK Switch.TCheckbutton
        sw3_box = ttk.Frame(sw_row)
        sw3_box.pack(side="left", padx=12)
        self.native_switch = ttk.Checkbutton(
            sw3_box, text="Native Switch.TCheckbutton", style="Switch.TCheckbutton",
            variable=self.sw3_var,
            command=lambda: self.status_var.set(f"Native Switch element toggled: {self.sw3_var.get()}")
        )
        self.native_switch.pack(side="left")

        # Section 2: Segmented Controls
        seg_frame = ttk.Labelframe(
            parent,
            text=" Segmented Pill Switcher (macOS / Shadcn Tab Groups) ",
            padding=16,
        )
        seg_frame.pack(fill="x", pady=10)

        seg_row = ttk.Frame(seg_frame)
        seg_row.pack(fill="x")

        ttk.Label(seg_row, text="Rasterizer Engine:").pack(side="left", padx=(0, 12))
        self.seg_ctrl = tkblend.SegmentedControl(
            seg_row,
            values=["Blend2D JIT", "AsmJit X86_64", "Skia Simd", "Fallback"],
            command=lambda v: self.status_var.set(f"Segment selected: {v}"),
        )
        self.seg_ctrl.pack(side="left", padx=4)

        # Section 3: Checkbuttons & Radiobuttons
        choice_frame = ttk.Labelframe(
            parent,
            text=" Antialiased Vector Indicators (Check & Radio) ",
            padding=16,
        )
        choice_frame.pack(fill="x", pady=10)

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

        # Section 4: Sliders & Progress
        metric_frame = ttk.Labelframe(
            parent,
            text=" Sliders & Smooth Vector Progressbar ",
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

    def _build_tab_data(self, parent: ttk.Frame):
        # Interactive Resizable PanedWindow
        pane_frame = ttk.Labelframe(
            parent,
            text=" Interactive Resizable Panedwindow (Live Sash Hover Glow & Grip) ",
            padding=12,
        )
        pane_frame.pack(fill="x", pady=(0, 10))

        paned = ttk.Panedwindow(pane_frame, orient="horizontal")
        paned.pack(fill="x", expand=True, pady=4)

        pane_left = tkblend.Card(paned, padding=12)
        ttk.Label(pane_left, text="Left Pane: Realtime Telemetry", font=("Helvetica", 10, "bold")).pack(anchor="w")
        ttk.Label(pane_left, text="Drag the sash splitter to resize panes.\nNotice the interactive hover glow.", font=("Helvetica", 9)).pack(anchor="w", pady=(4, 0))

        pane_right = tkblend.Card(paned, padding=12)
        ttk.Label(pane_right, text="Right Pane: Active Shaders", font=("Helvetica", 10, "bold")).pack(anchor="w")
        ttk.Label(pane_right, text="Zero-copy PRGB32 pipelines active across both surfaces.", font=("Helvetica", 9)).pack(anchor="w", pady=(4, 0))

        paned.add(pane_left, weight=1)
        paned.add(pane_right, weight=2)

        # Hierarchical Treeview with Modern Vector Chevrons
        tree_frame = ttk.Labelframe(
            parent,
            text=" Hierarchical Treeview Grid (Collapsible Nodes With Vector Chevron Disclosure) ",
            padding=16,
        )
        tree_frame.pack(fill="both", expand=True, pady=10)

        tree_container = ttk.Frame(tree_frame)
        tree_container.pack(fill="both", expand=True)

        cols = ("Type", "Backend", "Status")
        self.tree = ttk.Treeview(tree_container, columns=cols, selectmode="browse", height=7)
        self.tree_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.tree_scroll.set)

        self.tree.heading("#0", text="Engine Component / Hierarchy")
        self.tree.heading("Type", text="Element Spec")
        self.tree.heading("Backend", text="Rasterizer")
        self.tree.heading("Status", text="State")

        self.tree.column("#0", width=240)
        self.tree.column("Type", width=140)
        self.tree.column("Backend", width=130)
        self.tree.column("Status", width=120)

        # Hierarchical tree structure showing our modern chevron expand/collapse indicators
        core = self.tree.insert("", "end", text="Core Graphics Subsystem", open=True)
        self.tree.insert(core, "end", text="Blend2D JIT Engine", values=("Engine Core", "PRGB32 Pipeline", "⚡ Active"))
        self.tree.insert(core, "end", text="Zero-Copy Native Blit", values=("X11 / GDI / Cocoa", "Direct PutBlock", "⚡ 0.02 ms"))

        ui = self.tree.insert("", "end", text="Modern Controls & Elements", open=True)
        self.tree.insert(ui, "end", text="Buttons & Menubuttons", values=("Button Spec", "Vector Surfaces", "⚡ Themed"))
        self.tree.insert(ui, "end", text="Toggle Switches & Indicators", values=("Switch Spec", "60fps Animated", "⚡ Active"))
        self.tree.insert(ui, "end", text="Panedwindow Sash & Separators", values=("Sash Spec", "Hover Glow", "⚡ Responsive"))
        self.tree.insert(ui, "end", text="Treeitem Disclosure Chevron", values=("Indicator Spec", "Subpixel Vector", "⚡ Antialiased"))

        data = self.tree.insert("", "end", text="Data Buffers & Textures", open=False)
        self.tree.insert(data, "end", text="LRU Font & Path Cache", values=("Cache Spec", "Shared Memory", "⚡ 0.01 ms"))
        self.tree.insert(data, "end", text="Surface Pool", values=("Memory Alloc", "Zero-Copy Heap", "⚡ Active"))

        self.tree_scroll.pack(side="right", fill="y", padx=(2, 4), pady=2)
        self.tree.pack(side="left", fill="both", expand=True)

    def _build_tab_editor(self, parent: ttk.Frame):
        # Top Section: Card container & Separator demo
        surface_frame = ttk.Labelframe(
            parent,
            text=" Elevated Cards & Hairline Separators ",
            padding=16,
        )
        surface_frame.pack(fill="x", pady=(0, 10))

        c_box = ttk.Frame(surface_frame)
        c_box.pack(fill="x")

        card_demo = tkblend.Card(c_box, padding=12)
        card_demo.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Label(card_demo, text="Card Container Alpha", font=("Helvetica", 10, "bold")).pack(anchor="w")
        ttk.Label(card_demo, text="Rounded card surface with auto-synced child colors.").pack(anchor="w", pady=(2, 6))

        # Horizontal Separator
        ttk.Separator(card_demo, orient="horizontal").pack(fill="x", pady=4)
        ttk.Label(card_demo, text="Notice the crisp 1px separator hairline above.", font=("Helvetica", 8)).pack(anchor="w")

        card_demo2 = tkblend.Card(c_box, padding=12)
        card_demo2.pack(side="right", fill="x", expand=True, padx=(8, 0))
        ttk.Label(card_demo2, text="Card Container Beta", font=("Helvetica", 10, "bold")).pack(anchor="w")
        ttk.Label(card_demo2, text="Seamless Light & Dark theme transition.").pack(anchor="w", pady=(2, 6))
        ttk.Separator(card_demo2, orient="horizontal").pack(fill="x", pady=4)
        ttk.Label(card_demo2, text="Synchronized palette and selection highlights.", font=("Helvetica", 8)).pack(anchor="w")

        # Bottom Section: Themed Multi-line Text Editor
        editor_frame = ttk.Labelframe(
            parent,
            text=" Themed Text Editor & Docked Pill Scrollbar ",
            padding=16,
        )
        editor_frame.pack(fill="both", expand=True, pady=10)

        sample_code = (
            "# tkblend Modern Native Blend2D TTK Theme Suite\n"
            "# Full control expansion: Separators, Sizegrip, Panedwindow Sash,\n"
            "# Menubuttons, Treeview Chevrons, Toggle Switches, Badges & Cards.\n\n"
            "import tkinter as tk\n"
            "import tkblend\n\n"
            "root = tk.Tk()\n"
            "tkblend.apply_theme(root, dark_mode=True, entry_radius=8.0, button_radius=8.0)\n\n"
            "# 1. Animated Toggle Switch\n"
            "switch = tkblend.ToggleSwitch(root, text='Hardware Acceleration')\n"
            "switch.pack(padx=16, pady=8)\n\n"
            "# 2. Status Badge\n"
            "badge = tkblend.Badge(root, text='Production Ready', variant='success', dot=True)\n"
            "badge.pack(padx=16, pady=8)\n\n"
            "# 3. Segmented Control Switcher\n"
            "seg = tkblend.SegmentedControl(root, values=['Overview', 'Telemetry', 'Logs'])\n"
            "seg.pack(padx=16, pady=8)\n\n"
            "# 4. Resizable PanedWindow & Docked Text Editor\n"
            "editor = tkblend.ThemedText(root)\n"
            "editor.pack(fill='both', expand=True, padx=16, pady=8)\n\n"
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
