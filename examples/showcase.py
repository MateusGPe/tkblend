#!/usr/bin/env python3
"""
tkblend Vector UI Showcase Demo
A modern, zero-TTK vector widget showcase powered by Blend2D and C++ NativeController.
"""

from __future__ import annotations

import tkinter as tk
import tkblend as tb
from tkblend import (
    Button,
    Switch,
    Checkbox,
    Radio,
    Slider,
    Progressbar,
    Badge,
    Card,
    Label,
    set_theme,
    get_theme,
)


class ShowcaseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("tkblend Vector UI Showcase")
        self.geometry("900x720")
        self.minsize(800, 640)

        # Start with dark theme
        set_theme("dark")
        self._current_theme = "dark"
        self.configure(bg=get_theme().bg)

        self._click_count = 0
        self._radio_var = tk.StringVar(value="performance")
        self._check_notif = tk.BooleanVar(value=True)
        self._check_gpu = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        pal = get_theme()

        # Header Frame
        header = tk.Frame(self, bg=pal.bg)
        header.pack(fill="x", padx=32, pady=(24, 16))

        title_box = tk.Frame(header, bg=pal.bg)
        title_box.pack(side="left", fill="y")

        title_lbl = tk.Label(
            title_box,
            text="tkblend Showcase",
            font=("sans-serif", 20, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        )
        title_lbl.pack(side="left")

        version_badge = Badge(title_box, text="v0.3.0 Vector", width=105, height=26)
        version_badge.pack(side="left", padx=12)

        # Theme Switcher in Header
        theme_box = tk.Frame(header, bg=pal.bg)
        theme_box.pack(side="right")

        self.theme_switch = Switch(
            theme_box,
            text="Dark Theme",
            is_checked=True,
            command=self._on_theme_toggle,
            width=135,
            height=30,
        )
        self.theme_switch.pack(side="right")

        # Main Scrollable / Grid Content Container
        main_frame = tk.Frame(self, bg=pal.bg)
        main_frame.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        # Left Column Cards
        col_left = tk.Frame(main_frame, bg=pal.bg)
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # Right Column Cards
        col_right = tk.Frame(main_frame, bg=pal.bg)
        col_right.pack(side="right", fill="both", expand=True, padx=(12, 0))

        # -------------------------------------------------------------
        # Card 1: Buttons & Interactive Actions (Left)
        # -------------------------------------------------------------
        c1 = Card(col_left, width=380, height=290)
        c1.pack(fill="x", pady=(0, 16))

        c1_content = tk.Frame(c1, bg=pal.card_bg)
        c1_content.pack(fill="both", expand=True, padx=20, pady=16)

        c1_title = tk.Label(
            c1_content,
            text="Interactive Push Controls",
            font=("sans-serif", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        c1_title.pack(anchor="w", pady=(0, 12))

        btn_row1 = tk.Frame(c1_content, bg=pal.card_bg)
        btn_row1.pack(fill="x", pady=6)

        self.btn_counter = Button(
            btn_row1,
            text="Clicked: 0 times",
            command=self._on_btn_click,
            width=150,
            height=36,
        )
        self.btn_counter.pack(side="left", padx=(0, 10))

        self.btn_reset = Button(
            btn_row1,
            text="Reset Counter",
            command=self._on_btn_reset,
            width=130,
            height=36,
        )
        self.btn_reset.pack(side="left")

        btn_row2 = tk.Frame(c1_content, bg=pal.card_bg)
        btn_row2.pack(fill="x", pady=(12, 6))

        b_prod = Badge(btn_row2, text="Production", width=95, height=26)
        b_prod.pack(side="left", padx=(0, 8))

        b_live = Badge(btn_row2, text="Hardware Accelerated", width=175, height=26)
        b_live.pack(side="left")

        self.lbl_status = Label(
            c1_content,
            text="Ready. Blend2D vector pipeline active.",
            width=320,
            height=26,
        )
        self.lbl_status.pack(anchor="w", pady=(12, 0))

        # -------------------------------------------------------------
        # Card 2: Toggles & Selections (Left)
        # -------------------------------------------------------------
        c2 = Card(col_left, width=380, height=310)
        c2.pack(fill="both", expand=True)

        c2_content = tk.Frame(c2, bg=pal.card_bg)
        c2_content.pack(fill="both", expand=True, padx=20, pady=16)

        c2_title = tk.Label(
            c2_content,
            text="Toggles & Preferences",
            font=("sans-serif", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        c2_title.pack(anchor="w", pady=(0, 10))

        self.sw_notif = Switch(
            c2_content,
            text="Enable Notifications",
            is_checked=True,
            command=self._on_pref_change,
            width=180,
            height=30,
        )
        self.sw_notif.pack(anchor="w", pady=4)

        self.sw_sound = Switch(
            c2_content,
            text="Haptic Sound Effects",
            is_checked=False,
            command=self._on_pref_change,
            width=180,
            height=30,
        )
        self.sw_sound.pack(anchor="w", pady=4)

        # Checkboxes
        self.cb_gpu = Checkbox(
            c2_content,
            text="Zero-Copy Direct Blits",
            is_checked=True,
            command=self._on_pref_change,
            width=200,
            height=30,
        )
        self.cb_gpu.pack(anchor="w", pady=4)

        self.cb_debug = Checkbox(
            c2_content,
            text="Anti-Aliased Vectors",
            is_checked=True,
            command=self._on_pref_change,
            width=200,
            height=30,
        )
        self.cb_debug.pack(anchor="w", pady=4)

        # -------------------------------------------------------------
        # Card 3: Real-Time Metrics & Sliders (Right)
        # -------------------------------------------------------------
        c3 = Card(col_right, width=380, height=290)
        c3.pack(fill="x", pady=(0, 16))

        c3_content = tk.Frame(c3, bg=pal.card_bg)
        c3_content.pack(fill="both", expand=True, padx=20, pady=16)

        c3_title = tk.Label(
            c3_content,
            text="Real-time Metrics & Sliders",
            font=("sans-serif", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        c3_title.pack(anchor="w", pady=(0, 8))

        self.lbl_slider_val = tk.Label(
            c3_content,
            text="Resolution Scale: 65%",
            font=("sans-serif", 10),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        self.lbl_slider_val.pack(anchor="w", pady=(0, 4))

        self.slider = Slider(
            c3_content,
            from_=0.0,
            to=100.0,
            value=65.0,
            command=self._on_slider_moved,
            width=320,
            height=30,
        )
        self.slider.pack(fill="x", pady=(0, 12))

        self.lbl_prog_val = tk.Label(
            c3_content,
            text="Buffer Cache Utilization: 65%",
            font=("sans-serif", 10),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        self.lbl_prog_val.pack(anchor="w", pady=(0, 4))

        self.progress = Progressbar(
            c3_content,
            value=65.0,
            maximum=100.0,
            width=320,
            height=12,
        )
        self.progress.pack(fill="x", pady=(0, 14))

        prog_btns = tk.Frame(c3_content, bg=pal.card_bg)
        prog_btns.pack(fill="x")

        btn_step = Button(
            prog_btns,
            text="+10% Step",
            command=self._on_step_progress,
            width=110,
            height=32,
        )
        btn_step.pack(side="left", padx=(0, 10))

        btn_reset_prog = Button(
            prog_btns,
            text="Reset Progress",
            command=self._on_reset_progress,
            width=120,
            height=32,
        )
        btn_reset_prog.pack(side="left")

        # -------------------------------------------------------------
        # Card 4: Selection Groups & Radios (Right)
        # -------------------------------------------------------------
        c4 = Card(col_right, width=380, height=310)
        c4.pack(fill="both", expand=True)

        c4_content = tk.Frame(c4, bg=pal.card_bg)
        c4_content.pack(fill="both", expand=True, padx=20, pady=16)

        c4_title = tk.Label(
            c4_content,
            text="Render Pipeline Profile",
            font=("sans-serif", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        c4_title.pack(anchor="w", pady=(0, 10))

        self.radio_perf = Radio(
            c4_content,
            text="High Performance (Zero-Copy)",
            value="performance",
            variable=self._radio_var,
            command=self._on_radio_change,
            width=250,
            height=30,
        )
        self.radio_perf.pack(anchor="w", pady=4)
        self.radio_perf.is_checked = True

        self.radio_quality = Radio(
            c4_content,
            text="Ultra Quality (Super-sampling)",
            value="quality",
            variable=self._radio_var,
            command=self._on_radio_change,
            width=250,
            height=30,
        )
        self.radio_quality.pack(anchor="w", pady=4)

        self.radio_balanced = Radio(
            c4_content,
            text="Power Balanced Mode",
            value="balanced",
            variable=self._radio_var,
            command=self._on_radio_change,
            width=250,
            height=30,
        )
        self.radio_balanced.pack(anchor="w", pady=4)

        self.lbl_radio_status = Label(
            c4_content,
            text="Active Profile: High Performance",
            width=300,
            height=26,
        )
        self.lbl_radio_status.pack(anchor="w", pady=(16, 0))

    def _on_btn_click(self):
        self._click_count += 1
        self.btn_counter.text = f"Clicked: {self._click_count} times"
        self.lbl_status.text = f"Button triggered at iteration #{self._click_count}"

    def _on_btn_reset(self):
        self._click_count = 0
        self.btn_counter.text = "Clicked: 0 times"
        self.lbl_status.text = "Counter reset to zero."

    def _on_slider_moved(self, val: float):
        self.lbl_slider_val.config(text=f"Resolution Scale: {int(val)}%")
        self.progress.set(val)
        self.lbl_prog_val.config(text=f"Buffer Cache Utilization: {int(val)}%")

    def _on_step_progress(self):
        new_val = min(100.0, self.progress.get() + 10.0)
        self.progress.set(new_val)
        self.slider.set(new_val)
        self.lbl_slider_val.config(text=f"Resolution Scale: {int(new_val)}%")
        self.lbl_prog_val.config(text=f"Buffer Cache Utilization: {int(new_val)}%")

    def _on_reset_progress(self):
        self.progress.set(0.0)
        self.slider.set(0.0)
        self.lbl_slider_val.config(text="Resolution Scale: 0%")
        self.lbl_prog_val.config(text="Buffer Cache Utilization: 0%")

    def _on_pref_change(self):
        notif = "ON" if self.sw_notif.is_checked else "OFF"
        gpu = "Enabled" if self.cb_gpu.is_checked else "Disabled"
        self.lbl_status.text = f"Preferences: Notifications {notif}, Blit {gpu}"

    def _on_radio_change(self):
        val = self._radio_var.get()
        names = {
            "performance": "High Performance (Zero-Copy)",
            "quality": "Ultra Quality (Super-sampling)",
            "balanced": "Power Balanced Mode",
        }
        self.lbl_radio_status.text = f"Active Profile: {names.get(val, val)}"
        # Uncheck others visually
        self.radio_perf.is_checked = (val == "performance")
        self.radio_quality.is_checked = (val == "quality")
        self.radio_balanced.is_checked = (val == "balanced")

    def _on_theme_toggle(self):
        is_dark = self.theme_switch.is_checked
        new_theme = "dark" if is_dark else "light"
        self._current_theme = new_theme
        self.theme_switch.text = "Dark Theme" if is_dark else "Light Theme"
        set_theme(new_theme)
        pal = get_theme()
        self.configure(bg=pal.bg)
        # Update standard tk.Frames/Labels background
        self._update_theme_colors(self, pal)

    def _update_theme_colors(self, widget, pal):
        for child in widget.winfo_children():
            if isinstance(child, tk.Frame) and not isinstance(child, Card):
                # If child is inside a card, set card_bg, else bg
                parent = child.master
                is_in_card = False
                while parent is not None:
                    if isinstance(parent, Card):
                        is_in_card = True
                        break
                    parent = getattr(parent, "master", None)
                child.configure(bg=pal.card_bg if is_in_card else pal.bg)
            elif isinstance(child, tk.Label):
                parent = child.master
                is_in_card = False
                while parent is not None:
                    if isinstance(parent, Card):
                        is_in_card = True
                        break
                    parent = getattr(parent, "master", None)
                child.configure(
                    fg=pal.fg,
                    bg=pal.card_bg if is_in_card else pal.bg,
                )
            self._update_theme_colors(child, pal)


def main():
    app = ShowcaseApp()
    app.mainloop()


if __name__ == "__main__":
    main()
