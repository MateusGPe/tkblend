"""
tkblend Modern Widget Suite Gallery - Comprehensive Interactive Demo
Demonstrates Blend2D-powered Tkinter UI components, TTK durable styles,
preset themes (Dark, Light, Nord, Dracula, Tokyo-Night), and CustomTkinter-style configure / cget.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional

from tkblend import (
    ThemeManager,
    DARK_THEME,
    LIGHT_THEME,
    NORD_THEME,
    DRACULA_THEME,
    TOKYO_NIGHT_THEME,
    apply_ttk_theme,
    apply_theme,
    detect_system_theme,
    ModernFrame,
    ModernCard,
    ModernButton,
    ModernCheckbox,
    ModernRadioButton,
    ModernRadioGroup,
    ModernSwitch,
    ModernSlider,
    ModernSegmentedControl,
    ModernEntry,
    ModernDropdown,
    ModernProgressBar,
    ModernSpinner,
    ModernBadge,
    ModernAvatar,
    ModernTooltip,
    ModernLabel,
    ModernToast,
    ModernAccordion,
    ModernScrollableFrame,
    ModernDialog,
    show_alert,
)


class WidgetGalleryApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend Modern Widget Suite & Theming Showcase")
        self.root.geometry("1240x860")
        self.root.minsize(1040, 760)

        # Default theme
        ThemeManager.set_theme(DARK_THEME)
        ThemeManager.animations_enabled = True

        # Automatically bind root window for live bidirectional theme synchronization
        ThemeManager.bind_root(self.root)

        # Top Header Bar
        self._build_header()

        # Main Layout Container
        self._build_main_content()

        # Subscribe to update dynamic badge text
        ThemeManager.subscribe(self._on_theme_changed)

        # Apply theme across standard Tk/ttk elements in the entire tree
        apply_theme(self.root)

    def _on_theme_changed(self, theme):
        if hasattr(self, "_theme_badge"):
            self._theme_badge.configure(text=f"Theme: {theme.name.upper()}")

    def _build_header(self):
        t = ThemeManager.get_theme()
        self._header_frame = tk.Frame(self.root, bg=t.bg_window, height=64)
        self._header_frame.pack(fill=tk.X, padx=24, pady=(16, 8))

        # Title & Subtitle Frame
        title_box = tk.Frame(self._header_frame, bg=t.bg_window)
        title_box.pack(side=tk.LEFT, fill=tk.Y)

        title_lbl = ModernLabel(
            title_box,
            text="tkblend UI Gallery",
            variant="heading",
            font_size=18,
            bold=True,
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ModernLabel(
            title_box,
            text="Blend2D vector acceleration + ttkbootstrap semantic tokens + CustomTkinter API parity",
            variant="muted",
            font_size=10,
        )
        sub_lbl.pack(anchor="w")

        # Right Header Actions
        right_box = tk.Frame(self._header_frame, bg=t.bg_window)
        right_box.pack(side=tk.RIGHT, fill=tk.Y)

        self._theme_badge = ModernBadge(right_box, text=f"Theme: {t.name.upper()}", variant="primary", dot=True)
        self._theme_badge.pack(side=tk.LEFT, padx=(0, 12), pady=8)

        # Preset Theme Selector Dropdown
        theme_names = ["Dark", "Light", "Nord", "Dracula", "Tokyo-Night"]
        self._theme_dropdown = ModernDropdown(
            right_box,
            options=theme_names,
            selected_index=0,
            width=140,
            height=36,
            command=self._on_theme_selected,
        )
        self._theme_dropdown.pack(side=tk.LEFT, padx=4)
        ModernTooltip(self._theme_dropdown, "Switch between Theme Presets")

        theme_btn = ModernButton(
            right_box,
            text="Toggle 🌓",
            variant="secondary",
            width=90,
            height=36,
            command=self._toggle_theme,
        )
        theme_btn.pack(side=tk.LEFT, padx=(4, 0), pady=4)
        ModernTooltip(theme_btn, "Toggle Dark / Light Mode")

    def _on_theme_selected(self, theme_name: str):
        key = theme_name.lower().replace(" ", "-")
        ThemeManager.set_theme(key)
        self._toast(f"Theme changed to {theme_name}")

    def _toggle_theme(self):
        new_theme = ThemeManager.toggle_theme()
        if hasattr(self, "_theme_dropdown"):
            display_name = new_theme.name.capitalize()
            self._theme_dropdown.set(display_name)
        self._toast(f"Toggled theme to {new_theme.name}")

    def _build_main_content(self):
        content = tk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 16))

        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # ---------------- Column 1: Controls & Toggles ----------------
        col1 = tk.Frame(content)
        col1.grid(row=0, column=0, sticky="nsew", padx=8, pady=4)

        card_controls = ModernCard(
            col1,
            title="Interactive Controls",
            subtitle="Buttons, switches, sliders & selectors",
            height=720,
        )
        card_controls.pack(fill=tk.BOTH, expand=True)

        inner1 = card_controls.content

        # Buttons row
        btn_row = tk.Frame(inner1)
        btn_row.pack(fill=tk.X, pady=4)

        b_pri = ModernButton(btn_row, text="Primary", variant="primary", width=90, height=36, command=lambda: self._on_btn("Primary"))
        b_pri.pack(side=tk.LEFT, padx=3)

        b_sec = ModernButton(btn_row, text="Secondary", variant="secondary", width=90, height=36, command=lambda: self._on_btn("Secondary"))
        b_sec.pack(side=tk.LEFT, padx=3)

        b_dan = ModernButton(btn_row, text="Danger", variant="danger", width=90, height=36, command=lambda: self._on_btn("Danger"))
        b_dan.pack(side=tk.LEFT, padx=3)

        # Additional semantic variants
        btn_row2 = tk.Frame(inner1)
        btn_row2.pack(fill=tk.X, pady=4)

        b_suc = ModernButton(btn_row2, text="Success", variant="success", width=90, height=36, command=lambda: self._on_btn("Success"))
        b_suc.pack(side=tk.LEFT, padx=3)

        b_out = ModernButton(btn_row2, text="Outline", variant="outline", width=90, height=36, command=lambda: self._on_btn("Outline"))
        b_out.pack(side=tk.LEFT, padx=3)

        b_dyn = ModernButton(btn_row2, text="Dynamic", variant="secondary", width=90, height=36, command=self._demo_dynamic_configure)
        b_dyn.pack(side=tk.LEFT, padx=3)
        self._dyn_btn = b_dyn
        ModernTooltip(b_dyn, "Demonstrates .configure(text=..., variant=...)")

        # Segmented Control
        seg_lbl = ModernLabel(inner1, text="Segmented View Mode:", font_size=10, bold=True)
        seg_lbl.pack(anchor="w", pady=(12, 4))

        seg = ModernSegmentedControl(inner1, items=["Day", "Week", "Month", "Year"], selected_index=1, width=280)
        seg.pack(anchor="w", pady=2)

        # Switch & Checkboxes
        sw_lbl = ModernLabel(inner1, text="Toggles & Options:", font_size=10, bold=True)
        sw_lbl.pack(anchor="w", pady=(12, 4))

        sw_row = tk.Frame(inner1)
        sw_row.pack(fill=tk.X, pady=4)

        sw = ModernSwitch(sw_row, is_on=True, on_toggle=lambda state: self._toast(f"Switch: {state}"))
        sw.pack(side=tk.LEFT, padx=4)

        sw_text = ModernLabel(sw_row, text="Enable Vector Anti-Aliasing", font_size=10)
        sw_text.pack(side=tk.LEFT, padx=8)

        chk1 = ModernCheckbox(inner1, text="Hardware Acceleration", is_checked=True)
        chk1.pack(fill=tk.X, anchor="w", pady=2)

        chk2 = ModernCheckbox(inner1, text="Subpixel Font Hinting", is_checked=False)
        chk2.pack(fill=tk.X, anchor="w", pady=2)

        # Radio Group
        rg_lbl = ModernLabel(inner1, text="Rendering Backend:", font_size=10, bold=True)
        rg_lbl.pack(anchor="w", pady=(12, 4))

        rgroup = ModernRadioGroup(inner1, options=["Direct Tk Blit", "Async Thread Pool", "Shared Memory"], selected_value="Direct Tk Blit")
        rgroup.pack(fill=tk.X, anchor="w", pady=2)

        # Slider with value display
        sl_lbl = ModernLabel(inner1, text="Output Quality / Zoom:", font_size=10, bold=True)
        sl_lbl.pack(anchor="w", pady=(12, 4))

        self.slider_val_lbl = ModernLabel(inner1, text="Scale: 75%", variant="muted", font_size=9)
        self.slider_val_lbl.pack(anchor="w")

        slider = ModernSlider(inner1, min_val=10.0, max_val=100.0, value=75.0, width=280, on_change=self._on_slider)
        slider.pack(anchor="w", pady=4)

        # ---------------- Column 2: Inputs, TTK & Containers ----------------
        col2 = tk.Frame(content)
        col2.grid(row=0, column=1, sticky="nsew", padx=8, pady=4)

        card_inputs = ModernCard(
            col2,
            title="Form Inputs & Dialogs",
            subtitle="Text fields, dropdowns, and modals",
            height=340,
        )
        card_inputs.pack(fill=tk.X, pady=(0, 12))

        inner2 = card_inputs.content

        # Text input
        e_lbl = ModernLabel(inner2, text="User Account Name:", variant="muted", font_size=9)
        e_lbl.pack(anchor="w")

        self.entry_user = ModernEntry(inner2, placeholder="e.g. blend_master", width=280, height=36)
        self.entry_user.pack(anchor="w", pady=(2, 8))

        # Dropdown
        dd_lbl = ModernLabel(inner2, text="Display Profile:", variant="muted", font_size=9)
        dd_lbl.pack(anchor="w")

        dd = ModernDropdown(inner2, options=["High Precision sRGB", "Wide Gamut Display P3", "HDR Linear Float", "Custom Calibration"], selected_index=0, width=280, height=36)
        dd.pack(anchor="w", pady=(2, 12))

        # Modal Dialog Trigger
        btn_dialog = ModernButton(inner2, text="Open Modern Dialog ↗", variant="primary", width=280, height=36, command=self._show_dialog)
        btn_dialog.pack(anchor="w")

        # Tabs Card showing standard ttk widgets styled with tkblend
        card_ttk = ModernCard(
            col2,
            title="ttk Style Integration",
            subtitle="Standard ttk components styled automatically",
            height=350,
        )
        card_ttk.pack(fill=tk.BOTH, expand=True)

        ttk_box = card_ttk.content

        notebook = ttk.Notebook(ttk_box)
        notebook.pack(fill=tk.BOTH, expand=True)

        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="Buttons & Progress")

        tab1_inner = tk.Frame(tab1)
        tab1_inner.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ModernLabel(tab1_inner, text="Semantic TTK Styles", variant="heading", font_size=10, bold=True).pack(anchor="w", pady=(0, 4))
        
        ttk_btn_row = tk.Frame(tab1_inner)
        ttk_btn_row.pack(fill=tk.X, pady=4)
        ttk.Button(ttk_btn_row, text="Primary", style="primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(ttk_btn_row, text="Success", style="success.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(ttk_btn_row, text="Danger", style="danger.TButton").pack(side=tk.LEFT, padx=2)

        p_ttk = ttk.Progressbar(tab1_inner, style="success.Horizontal.TProgressbar", value=70, length=240)
        p_ttk.pack(anchor="w", pady=(8, 4))

        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="Treeview")

        tree = ttk.Treeview(tab2, columns=("col1", "col2"), show="headings", height=4)
        tree.heading("col1", text="Pipeline")
        tree.heading("col2", text="Status")
        tree.column("col1", width=120)
        tree.column("col2", width=100)
        tree.insert("", "end", values=("JIT Engine", "Active"))
        tree.insert("", "end", values=("Photo Blit", "Zero-Copy"))
        tree.insert("", "end", values=("DPI Awareness", "Per-Monitor"))
        tree.insert("", "end", values=("Style Builder", "Durable"))
        tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # ---------------- Column 3: Status, Feedback & Feed ----------------
        col3 = tk.Frame(content)
        col3.grid(row=0, column=2, sticky="nsew", padx=8, pady=4)

        card_feedback = ModernCard(
            col3,
            title="Status & Visual Feedback",
            subtitle="Avatars, badges, spinner, progress",
            height=340,
        )
        card_feedback.pack(fill=tk.X, pady=(0, 12))

        inner3 = card_feedback.content

        # Avatars & Spinner Row
        avatar_row = tk.Frame(inner3)
        avatar_row.pack(fill=tk.X, pady=4)

        av1 = ModernAvatar(avatar_row, text="AG", size=42, status="online")
        av1.pack(side=tk.LEFT, padx=4)
        ModernTooltip(av1, "Agent Active (Online)")

        av2 = ModernAvatar(avatar_row, text="TK", size=42, bg_color="#cba6f7", status="busy")
        av2.pack(side=tk.LEFT, padx=4)
        ModernTooltip(av2, "Tkinter Kernel (Busy)")

        spinner = ModernSpinner(avatar_row, size=38, color="#89b4fa")
        spinner.pack(side=tk.RIGHT, padx=8)
        ModernTooltip(spinner, "Blend2D 60FPS JIT Renderer Active")

        # Badges Row
        badge_row = tk.Frame(inner3)
        badge_row.pack(fill=tk.X, pady=(10, 4))

        b1 = ModernBadge(badge_row, text="Active", variant="success", dot=True)
        b1.pack(side=tk.LEFT, padx=2)

        b2 = ModernBadge(badge_row, text="AVX2", variant="primary")
        b2.pack(side=tk.LEFT, padx=2)

        b3 = ModernBadge(badge_row, text="Beta v0.1.0", variant="neutral")
        b3.pack(side=tk.LEFT, padx=2)

        # Animated Progress Bar
        p_lbl = ModernLabel(inner3, text="Vector Pipeline Progress:", variant="muted", font_size=9)
        p_lbl.pack(anchor="w", pady=(10, 2))

        self.pbar = ModernProgressBar(inner3, value=65.0, width=280, height=14)
        self.pbar.pack(anchor="w", pady=4)

        # Scrollable Feed Card
        card_feed = ModernCard(
            col3,
            title="Activity Feed",
            subtitle="Smooth scrollable modern container",
            height=350,
        )
        card_feed.pack(fill=tk.BOTH, expand=True)

        scroll_container = card_feed.content

        s_frame = ModernScrollableFrame(scroll_container, width=280, height=180)
        s_frame.pack(fill=tk.BOTH, expand=True)

        logs = [
            ("⚡ Blend2D JIT compiler initialized", "#a6e3a1"),
            ("🎨 Surface resized to 1920x1080", "#89b4fa"),
            ("🚀 Blit complete: 0.12ms (8333 FPS)", "#cba6f7"),
            ("✨ Drop shadow cache hit (radius=12.0)", "#f9e2af"),
            ("🛡️ High-DPI auto scaling configured", "#a6e3a1"),
            ("🌓 Theme switched to dynamic tokens", "#89dceb"),
            ("📦 Modular package loaded cleanly", "#cdd6f4"),
        ]

        for text, col in logs:
            row = tk.Frame(s_frame.scrollable_content, pady=3)
            row.pack(fill=tk.X)
            tk.Label(row, text="●", fg=col, font=("sans-serif", 8)).pack(side=tk.LEFT, padx=(2, 6))
            tk.Label(row, text=text, font=("sans-serif", 8), anchor="w").pack(side=tk.LEFT)

    def _on_btn(self, name: str):
        self._toast(f"Clicked {name} Button")

    def _demo_dynamic_configure(self):
        cur_text = self._dyn_btn.cget("text")
        if cur_text == "Dynamic":
            self._dyn_btn.configure(text="Updated! ✨", variant="success")
        else:
            self._dyn_btn.configure(text="Dynamic", variant="secondary")
        self._toast("Configured button dynamically via .configure()")

    def _on_slider(self, val: float):
        if hasattr(self, "slider_val_lbl"):
            self.slider_val_lbl.set_text(f"Scale: {val:.1f}%")
        if hasattr(self, "pbar"):
            self.pbar.value = val

    def _show_dialog(self):
        ModernDialog(
            self.root,
            title="Export Vector Bundle",
            message="Do you want to compile and export the high-resolution Blend2D vector assets to the active workspace?",
            confirm_text="Export",
            cancel_text="Cancel",
            on_confirm=lambda: self._toast("Export initiated!"),
            on_cancel=lambda: self._toast("Export cancelled."),
        )

    def _toast(self, msg: str):
        print(f"[UI Event]: {msg}")
        ModernToast.show(self.root, message=msg, title="Gallery Event", duration_ms=2500)


def main():
    root = tk.Tk()
    app = WidgetGalleryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
