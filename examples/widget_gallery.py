"""
tkblend Modern Widget Suite Gallery - Comprehensive Interactive Demo
Demonstrates all modern Blend2D-powered Tkinter UI components with real-time theming.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional

from tkblend import (
    ThemeManager,
    DARK_THEME,
    LIGHT_THEME,
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
    ModernAccordion,
    ModernScrollableFrame,
    ModernDialog,
    show_alert,
)


class WidgetGalleryApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend Modern Widget Suite Showcase")
        self.root.geometry("1180x820")
        self.root.minsize(980, 720)

        # Set default theme
        ThemeManager.set_theme(DARK_THEME)
        ThemeManager.animations_enabled = True

        self._current_bg = ThemeManager.get_theme().bg_window
        self.root.configure(bg=self._current_bg)

        # Top Header Bar
        self._build_header()

        # Main 3-Column Layout Container
        self._build_main_content()

        # Subscribe root to theme changes
        ThemeManager.subscribe(self._on_theme_changed)

    def _on_theme_changed(self, theme):
        self._current_bg = theme.bg_window
        self.root.configure(bg=self._current_bg)
        self._header_frame.configure(bg=theme.bg_window)
        self._theme_badge.set_text(f"Theme: {theme.name.upper()}")

    def _build_header(self):
        t = ThemeManager.get_theme()
        self._header_frame = tk.Frame(self.root, bg=t.bg_window, height=60)
        self._header_frame.pack(fill=tk.X, padx=24, pady=(16, 8))

        # Title & Subtitle Frame
        title_box = tk.Frame(self._header_frame, bg=t.bg_window)
        title_box.pack(side=tk.LEFT, fill=tk.Y)

        title_lbl = tk.Label(
            title_box,
            text="tkblend UI Gallery",
            font=(t.font_family, 18, "bold"),
            fg=t.primary,
            bg=t.bg_window,
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            title_box,
            text="High-performance Blend2D vector-drawn Tkinter widgets",
            font=(t.font_family, 10),
            fg=t.text_muted,
            bg=t.bg_window,
        )
        sub_lbl.pack(anchor="w")

        # Right Header Actions
        right_box = tk.Frame(self._header_frame, bg=t.bg_window)
        right_box.pack(side=tk.RIGHT, fill=tk.Y)

        self._theme_badge = ModernBadge(right_box, text=f"Theme: {t.name.upper()}", variant="primary", dot=True)
        self._theme_badge.pack(side=tk.LEFT, padx=(0, 12), pady=8)

        theme_btn = ModernButton(
            right_box,
            text="Toggle Theme 🌓",
            variant="secondary",
            width=130,
            height=36,
            command=self._toggle_theme,
        )
        theme_btn.pack(side=tk.LEFT, pady=4)
        ModernTooltip(theme_btn, "Switch between Dark and Light mode")

    def _toggle_theme(self):
        ThemeManager.toggle_theme()

    def _build_main_content(self):
        content = tk.Frame(self.root, bg=self._current_bg)
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 16))

        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # ---------------- Column 1: Controls & Toggles ----------------
        col1 = tk.Frame(content, bg=self._current_bg)
        col1.grid(row=0, column=0, sticky="nsew", padx=8, pady=4)

        card_controls = ModernCard(
            col1,
            title="Interactive Controls",
            subtitle="Buttons, switches, sliders & selectors",
            height=680,
        )
        card_controls.pack(fill=tk.BOTH, expand=True)

        inner1 = tk.Frame(card_controls, bg=ThemeManager.get_theme().bg_card)
        inner1.place(x=16, y=65, relwidth=0.92, relheight=0.88)

        # Buttons row
        btn_row = tk.Frame(inner1, bg=ThemeManager.get_theme().bg_card)
        btn_row.pack(fill=tk.X, pady=4)

        b_pri = ModernButton(btn_row, text="Primary", variant="primary", width=90, height=36, command=lambda: self._on_btn("Primary"))
        b_pri.pack(side=tk.LEFT, padx=3)

        b_sec = ModernButton(btn_row, text="Secondary", variant="secondary", width=90, height=36, command=lambda: self._on_btn("Secondary"))
        b_sec.pack(side=tk.LEFT, padx=3)

        b_dan = ModernButton(btn_row, text="Danger", variant="danger", width=90, height=36, command=lambda: self._on_btn("Danger"))
        b_dan.pack(side=tk.LEFT, padx=3)

        # Segmented Control
        seg_lbl = tk.Label(inner1, text="Segmented View Mode:", font=("sans-serif", 10, "bold"), fg="#a6adc8", bg=ThemeManager.get_theme().bg_card)
        seg_lbl.pack(anchor="w", pady=(12, 4))

        seg = ModernSegmentedControl(inner1, items=["Day", "Week", "Month", "Year"], selected_index=1, width=280)
        seg.pack(anchor="w", pady=2)

        # Switch & Checkboxes
        sw_lbl = tk.Label(inner1, text="Toggles & Options:", font=("sans-serif", 10, "bold"), fg="#a6adc8", bg=ThemeManager.get_theme().bg_card)
        sw_lbl.pack(anchor="w", pady=(12, 4))

        sw_row = tk.Frame(inner1, bg=ThemeManager.get_theme().bg_card)
        sw_row.pack(fill=tk.X, pady=4)

        sw = ModernSwitch(sw_row, is_on=True, on_toggle=lambda state: self._toast(f"Switch: {state}"))
        sw.pack(side=tk.LEFT, padx=4)

        sw_text = tk.Label(sw_row, text="Enable Vector Anti-Aliasing", font=("sans-serif", 10), fg="#cdd6f4", bg=ThemeManager.get_theme().bg_card)
        sw_text.pack(side=tk.LEFT, padx=8)

        chk1 = ModernCheckbox(inner1, text="Hardware Acceleration", is_checked=True)
        chk1.pack(anchor="w", pady=2)

        chk2 = ModernCheckbox(inner1, text="Subpixel Font Hinting", is_checked=False)
        chk2.pack(anchor="w", pady=2)

        # Radio Group
        rg_lbl = tk.Label(inner1, text="Rendering Backend:", font=("sans-serif", 10, "bold"), fg="#a6adc8", bg=ThemeManager.get_theme().bg_card)
        rg_lbl.pack(anchor="w", pady=(12, 4))

        rgroup = ModernRadioGroup(inner1, options=["Direct Tk Blit", "Async Thread Pool", "Shared Memory"], selected_value="Direct Tk Blit")
        rgroup.pack(anchor="w", pady=2)

        # Slider with value display
        sl_lbl = tk.Label(inner1, text="Output Quality / Zoom:", font=("sans-serif", 10, "bold"), fg="#a6adc8", bg=ThemeManager.get_theme().bg_card)
        sl_lbl.pack(anchor="w", pady=(12, 4))

        self.slider_val_lbl = tk.Label(inner1, text="Scale: 75%", font=("sans-serif", 9), fg="#89b4fa", bg=ThemeManager.get_theme().bg_card)
        self.slider_val_lbl.pack(anchor="w")

        slider = ModernSlider(inner1, min_val=10.0, max_val=100.0, value=75.0, width=280, on_change=self._on_slider)
        slider.pack(anchor="w", pady=4)

        # ---------------- Column 2: Inputs & Containers ----------------
        col2 = tk.Frame(content, bg=self._current_bg)
        col2.grid(row=0, column=1, sticky="nsew", padx=8, pady=4)

        card_inputs = ModernCard(
            col2,
            title="Form Inputs & Dialogs",
            subtitle="Text fields, dropdowns, and modals",
            height=340,
        )
        card_inputs.pack(fill=tk.X, pady=(0, 12))

        inner2 = tk.Frame(card_inputs, bg=ThemeManager.get_theme().bg_card)
        inner2.place(x=16, y=65, relwidth=0.92, relheight=0.78)

        # Text input
        e_lbl = tk.Label(inner2, text="User Account Name:", font=("sans-serif", 9), fg="#a6adc8", bg=ThemeManager.get_theme().bg_card)
        e_lbl.pack(anchor="w")

        self.entry_user = ModernEntry(inner2, placeholder="e.g. blend_master", width=280, height=36)
        self.entry_user.pack(anchor="w", pady=(2, 8))

        # Dropdown
        dd_lbl = tk.Label(inner2, text="Display Profile:", font=("sans-serif", 9), fg="#a6adc8", bg=ThemeManager.get_theme().bg_card)
        dd_lbl.pack(anchor="w")

        dd = ModernDropdown(inner2, options=["High Precision sRGB", "Wide Gamut Display P3", "HDR Linear Float", "Custom Calibration"], selected_index=0, width=280, height=36)
        dd.pack(anchor="w", pady=(2, 12))

        # Modal Dialog Trigger
        btn_dialog = ModernButton(inner2, text="Open Modern Dialog 🚀", variant="primary", width=280, height=36, command=self._show_dialog)
        btn_dialog.pack(anchor="w")

        # Accordion Container Card
        card_acc = ModernCard(
            col2,
            title="Collapsible Sections",
            subtitle="Modern expandable accordion panels",
            height=320,
        )
        card_acc.pack(fill=tk.BOTH, expand=True)

        acc_box = tk.Frame(card_acc, bg=ThemeManager.get_theme().bg_card)
        acc_box.place(x=16, y=65, relwidth=0.92, relheight=0.76)

        accordion = ModernAccordion(acc_box)
        accordion.pack(fill=tk.BOTH, expand=True)

        sec1 = accordion.add_section("Display Engine Config", is_expanded=True)
        tk.Label(sec1, text="Blend2D JIT pipelines: Enabled (SSE4.2 / AVX2)\nPhotoPutBlock direct pointer: OK", font=("sans-serif", 9), fg="#cdd6f4", bg=ThemeManager.get_theme().bg_surface_alt, justify="left").pack(anchor="w")

        sec2 = accordion.add_section("Memory & Caching", is_expanded=False)
        tk.Label(sec2, text="Shadow LRU cache: 256 entries\nGlyph atlas size: 2048x2048", font=("sans-serif", 9), fg="#cdd6f4", bg=ThemeManager.get_theme().bg_surface_alt, justify="left").pack(anchor="w")

        # ---------------- Column 3: Status, Feedback & Feed ----------------
        col3 = tk.Frame(content, bg=self._current_bg)
        col3.grid(row=0, column=2, sticky="nsew", padx=8, pady=4)

        card_feedback = ModernCard(
            col3,
            title="Status & Visual Feedback",
            subtitle="Avatars, badges, spinner, progress",
            height=340,
        )
        card_feedback.pack(fill=tk.X, pady=(0, 12))

        inner3 = tk.Frame(card_feedback, bg=ThemeManager.get_theme().bg_card)
        inner3.place(x=16, y=65, relwidth=0.92, relheight=0.78)

        # Avatars & Spinner Row
        avatar_row = tk.Frame(inner3, bg=ThemeManager.get_theme().bg_card)
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
        badge_row = tk.Frame(inner3, bg=ThemeManager.get_theme().bg_card)
        badge_row.pack(fill=tk.X, pady=(10, 4))

        b1 = ModernBadge(badge_row, text="Active", variant="success", dot=True)
        b1.pack(side=tk.LEFT, padx=2)

        b2 = ModernBadge(badge_row, text="AVX2", variant="primary")
        b2.pack(side=tk.LEFT, padx=2)

        b3 = ModernBadge(badge_row, text="Beta v0.1.0", variant="neutral")
        b3.pack(side=tk.LEFT, padx=2)

        # Animated Progress Bar
        p_lbl = tk.Label(inner3, text="Vector Pipeline Progress:", font=("sans-serif", 9), fg="#a6adc8", bg=ThemeManager.get_theme().bg_card)
        p_lbl.pack(anchor="w", pady=(10, 2))

        self.pbar = ModernProgressBar(inner3, value=65.0, width=280, height=14)
        self.pbar.pack(anchor="w", pady=4)

        # Scrollable Feed Card
        card_feed = ModernCard(
            col3,
            title="Activity Feed",
            subtitle="Smooth scrollable modern container",
            height=320,
        )
        card_feed.pack(fill=tk.BOTH, expand=True)

        scroll_container = tk.Frame(card_feed, bg=ThemeManager.get_theme().bg_card)
        scroll_container.place(x=16, y=65, relwidth=0.92, relheight=0.76)

        s_frame = ModernScrollableFrame(scroll_container, width=280, height=180, parent_bg=ThemeManager.get_theme().bg_card)
        s_frame.pack(fill=tk.BOTH, expand=True)

        logs = [
            ("⚡ Blend2D JIT compiler initialized", "#a6e3a1"),
            ("🎨 Surface resized to 1920x1080", "#89b4fa"),
            ("🚀 Blit complete: 0.12ms (8333 FPS)", "#cba6f7"),
            ("✨ Drop shadow cache hit (radius=12.0)", "#f9e2af"),
            ("🛡️ Sanitizer memory check: 0 leaks", "#a6e3a1"),
            ("🌓 Theme switched to dynamic tokens", "#89dceb"),
            ("📦 Modular package loaded cleanly", "#cdd6f4"),
        ]

        for text, col in logs:
            row = tk.Frame(s_frame.scrollable_content, bg=ThemeManager.get_theme().bg_card, pady=3)
            row.pack(fill=tk.X)
            tk.Label(row, text="●", fg=col, bg=ThemeManager.get_theme().bg_card, font=("sans-serif", 8)).pack(side=tk.LEFT, padx=(2, 6))
            tk.Label(row, text=text, fg="#cdd6f4", bg=ThemeManager.get_theme().bg_card, font=("sans-serif", 8), anchor="w").pack(side=tk.LEFT)

    def _on_btn(self, name: str):
        self._toast(f"Clicked {name} Button")

    def _on_slider(self, val: float):
        if hasattr(self, "slider_val_lbl"):
            self.slider_val_lbl.configure(text=f"Scale: {val:.1f}%")
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


def main():
    root = tk.Tk()
    app = WidgetGalleryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
