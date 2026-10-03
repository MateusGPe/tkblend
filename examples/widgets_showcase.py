"""
tkblend Native Vector Widgets Showcase
Interactive demonstration of pure Blend2D vector UI controls powered by NativeController.
Zero TTK dependencies, zero PhotoImage allocations.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional

import tkblend as tb
from tkblend.widgets import (
    Button,
    Switch,
    Toggle,
    Slider,
    CheckBox,
    ProgressBar,
    RadioButton,
    Card,
    Label,
)
from tkblend.theme import (
    get_theme,
    set_theme,
    get_available_themes,
    apply_theme,
)


class WidgetsShowcaseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend Native Vector Widgets Showcase")
        self.root.geometry("1080x780")
        self.root.minsize(900, 680)

        # Apply initial theme
        apply_theme(self.root, "dark")
        self.pal = get_theme()

        self._all_widgets = []
        self._disabled_var = tk.BooleanVar(value=False)
        self._wifi_var = tk.BooleanVar(value=True)
        self._bluetooth_var = tk.BooleanVar(value=False)
        self._notifications_var = tk.BooleanVar(value=True)

        self._slider_val_var = tk.DoubleVar(value=45.0)
        self._slider_step_var = tk.DoubleVar(value=3.0)
        self._progress_val_var = tk.DoubleVar(value=0.65)
        self._radio_var = tk.StringVar(value="balanced")

        self._setup_ui()

    def _setup_ui(self):
        # Top App Bar
        self.top_bar = tk.Frame(self.root, height=60)
        self.top_bar.pack(fill="x", padx=20, pady=(15, 10))

        # Title Label
        title_lbl = Label(
            self.top_bar,
            text="Native Vector Controls",
            icon="fa:cubes",
            font_size=18,
            bold=True,
            width=260,
            height=36,
        )
        title_lbl.pack(side="left")

        # Global Disable Toggle
        dis_switch = Switch(
            self.top_bar,
            text="Disable All",
            variable=self._disabled_var,
            command=self._on_toggle_disabled,
            width=130,
            height=28,
        )
        dis_switch.pack(side="right", padx=(10, 0))

        # Theme Selector Buttons
        theme_frame = tk.Frame(self.top_bar)
        theme_frame.pack(side="right", padx=10)

        themes = ["dark", "light", "dracula", "nord", "tokyo_night", "catppuccin_mocha", "cyberpunk"]
        for t_name in themes:
            btn = Button(
                theme_frame,
                text=t_name.replace("_", " ").title(),
                width=85,
                height=28,
                corner_radius=6,
                font_size=10,
                command=lambda name=t_name: self._change_theme(name),
            )
            btn.pack(side="left", padx=3)

        # Main Scrollable / Grid Container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # ==========================================
        # CARD 1: Buttons & Interactive Actions
        # ==========================================
        c1 = Card(main_frame, corner_radius=12)
        c1.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        self._build_buttons_section(c1)

        # ==========================================
        # CARD 2: Toggles, Checkboxes & Radios
        # ==========================================
        c2 = Card(main_frame, corner_radius=12)
        c2.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        self._build_selectors_section(c2)

        # ==========================================
        # CARD 3: Sliders & Numeric Inputs
        # ==========================================
        c3 = Card(main_frame, corner_radius=12)
        c3.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")
        self._build_sliders_section(c3)

        # ==========================================
        # CARD 4: Progress Bars & Loading
        # ==========================================
        c4 = Card(main_frame, corner_radius=12)
        c4.grid(row=1, column=0, columnspan=2, padx=8, pady=8, sticky="nsew")
        self._build_progress_section(c4)

        # ==========================================
        # CARD 5: Badges, Status & Feedback
        # ==========================================
        c5 = Card(main_frame, corner_radius=12)
        c5.grid(row=1, column=2, padx=8, pady=8, sticky="nsew")
        self._build_badges_section(c5)

    def _build_buttons_section(self, parent: Card):
        header = Label(parent, text="Buttons & Elevation", icon="fa:hand-pointer", font_size=14, bold=True, width=200, height=28)
        header.pack(anchor="w", padx=16, pady=(16, 12))

        # Primary Button with Icon
        b1 = Button(
            parent,
            text="Primary Action",
            icon="fa:rocket",
            width=200,
            height=38,
            corner_radius=8,
            command=lambda: self._log("Primary Action Clicked!"),
        )
        b1.pack(padx=16, pady=6)
        self._all_widgets.append(b1)

        # Secondary Button
        b2 = Button(
            parent,
            text="Secondary Button",
            icon="fa:gear",
            bg_color=self.pal.secondary,
            hover_color=self.pal.secondary_hover,
            pressed_color=self.pal.secondary_active,
            fg_color=self.pal.secondary_fg,
            width=200,
            height=36,
            corner_radius=8,
            command=lambda: self._log("Settings Clicked!"),
        )
        b2.pack(padx=16, pady=6)
        self._all_widgets.append(b2)

        # Accent / Success Button
        b3 = Button(
            parent,
            text="Success Save",
            icon="fa:check",
            bg_color="#10b981",
            hover_color="#059669",
            pressed_color="#047857",
            fg_color="#ffffff",
            width=200,
            height=36,
            corner_radius=8,
            command=lambda: self._log("Save Success!"),
        )
        b3.pack(padx=16, pady=6)
        self._all_widgets.append(b3)

        # Destructive Button
        b4 = Button(
            parent,
            text="Delete Item",
            icon="fa:trash",
            bg_color="#ef4444",
            hover_color="#dc2626",
            pressed_color="#b91c1c",
            fg_color="#ffffff",
            width=200,
            height=36,
            corner_radius=8,
            command=lambda: self._log("Delete Item Clicked!"),
        )
        b4.pack(padx=16, pady=6)
        self._all_widgets.append(b4)

    def _build_selectors_section(self, parent: Card):
        header = Label(parent, text="Toggles & Selectors", icon="fa:toggle-on", font_size=14, bold=True, width=200, height=28)
        header.pack(anchor="w", padx=16, pady=(16, 12))

        # Switches
        sw1 = Switch(parent, text="Wi-Fi Connection", variable=self._wifi_var, width=180, height=28)
        sw1.pack(anchor="w", padx=16, pady=4)
        self._all_widgets.append(sw1)

        sw2 = Switch(parent, text="Bluetooth", variable=self._bluetooth_var, width=180, height=28)
        sw2.pack(anchor="w", padx=16, pady=4)
        self._all_widgets.append(sw2)

        sw3 = Switch(parent, text="Push Notifications", variable=self._notifications_var, width=180, height=28)
        sw3.pack(anchor="w", padx=16, pady=4)
        self._all_widgets.append(sw3)

        # Checkboxes
        self._agree_var = tk.BooleanVar(value=True)
        cb1 = CheckBox(parent, text="Enable Hardware Acceleration", variable=self._agree_var, width=220, height=28)
        cb1.pack(anchor="w", padx=16, pady=4)
        self._all_widgets.append(cb1)

        # Radio Group
        lbl_mode = Label(parent, text="Performance Mode:", font_size=11, bold=True, width=160, height=20)
        lbl_mode.pack(anchor="w", padx=16, pady=(10, 2))

        r1 = RadioButton(parent, text="Power Saver", value="saver", variable=self._radio_var, width=160, height=24)
        r1.pack(anchor="w", padx=20, pady=2)
        self._all_widgets.append(r1)

        r2 = RadioButton(parent, text="Balanced", value="balanced", variable=self._radio_var, width=160, height=24)
        r2.pack(anchor="w", padx=20, pady=2)
        self._all_widgets.append(r2)

        r3 = RadioButton(parent, text="Ultra Performance", value="performance", variable=self._radio_var, width=160, height=24)
        r3.pack(anchor="w", padx=20, pady=2)
        self._all_widgets.append(r3)

    def _build_sliders_section(self, parent: Card):
        header = Label(parent, text="Sliders & Controls", icon="fa:sliders", font_size=14, bold=True, width=200, height=28)
        header.pack(anchor="w", padx=16, pady=(16, 12))

        # Continuous Slider
        lbl_v = Label(parent, text=f"Master Volume: {int(self._slider_val_var.get())}%", font_size=12, width=200, height=22)
        lbl_v.pack(anchor="w", padx=16, pady=(4, 0))

        def _on_vol_change(val):
            lbl_v.text = f"Master Volume: {int(val)}%"

        sl1 = Slider(
            parent,
            from_=0.0,
            to=100.0,
            variable=self._slider_val_var,
            command=_on_vol_change,
            width=220,
            height=26,
            track_thickness=5.0,
            thumb_radius=9.0,
        )
        sl1.pack(padx=16, pady=(4, 14))
        self._all_widgets.append(sl1)

        # Stepped Slider
        lbl_step = Label(parent, text=f"Quality Tier: {int(self._slider_step_var.get())} of 5", font_size=12, width=200, height=22)
        lbl_step.pack(anchor="w", padx=16, pady=(4, 0))

        def _on_step_change(val):
            lbl_step.text = f"Quality Tier: {int(val)} of 5"

        sl2 = Slider(
            parent,
            from_=1.0,
            to=5.0,
            number_of_steps=4,
            variable=self._slider_step_var,
            command=_on_step_change,
            width=220,
            height=26,
            active_color="#8b5cf6",
            thumb_color="#8b5cf6",
        )
        sl2.pack(padx=16, pady=(4, 14))
        self._all_widgets.append(sl2)

    def _build_progress_section(self, parent: Card):
        header = Label(parent, text="Progress & Activity", icon="fa:chart-line", font_size=14, bold=True, width=220, height=28)
        header.pack(anchor="w", padx=16, pady=(16, 12))

        # Determinate Bar
        row1 = tk.Frame(parent)
        row1.pack(fill="x", padx=16, pady=4)

        lbl_p = Label(row1, text=f"Task Progress ({int(self._progress_val_var.get() * 100)}%)", width=180, height=24)
        lbl_p.pack(side="left")

        self.pb_det = ProgressBar(
            parent,
            mode="determinate",
            variable=self._progress_val_var,
            width=480,
            height=10,
            corner_radius=5,
        )
        self.pb_det.pack(fill="x", padx=16, pady=(4, 12))
        self._all_widgets.append(self.pb_det)

        # Controls for Determinate
        btn_row = tk.Frame(parent)
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        def _add_p(delta):
            v = max(0.0, min(1.0, self._progress_val_var.get() + delta))
            self._progress_val_var.set(v)
            lbl_p.text = f"Task Progress ({int(v * 100)}%)"

        b_minus = Button(btn_row, text="-10%", width=70, height=28, corner_radius=6, command=lambda: _add_p(-0.1))
        b_minus.pack(side="left", padx=4)
        self._all_widgets.append(b_minus)

        b_plus = Button(btn_row, text="+10%", width=70, height=28, corner_radius=6, command=lambda: _add_p(0.1))
        b_plus.pack(side="left", padx=4)
        self._all_widgets.append(b_plus)

        # Indeterminate Marquee Bar
        lbl_ind = Label(parent, text="Indeterminate Background Worker", width=260, height=24)
        lbl_ind.pack(anchor="w", padx=16, pady=(6, 2))

        self.pb_ind = ProgressBar(
            parent,
            mode="indeterminate",
            width=480,
            height=8,
            corner_radius=4,
            progress_color="#06b6d4",
        )
        self.pb_ind.pack(fill="x", padx=16, pady=(4, 10))
        self.pb_ind.start()
        self._all_widgets.append(self.pb_ind)

        ind_row = tk.Frame(parent)
        ind_row.pack(fill="x", padx=16, pady=(0, 12))

        b_stop = Button(ind_row, text="Stop Worker", width=95, height=28, corner_radius=6, command=self.pb_ind.stop)
        b_stop.pack(side="left", padx=4)
        self._all_widgets.append(b_stop)

        b_start = Button(ind_row, text="Start Worker", width=95, height=28, corner_radius=6, command=self.pb_ind.start)
        b_start.pack(side="left", padx=4)
        self._all_widgets.append(b_start)

    def _build_badges_section(self, parent: Card):
        header = Label(parent, text="Badges & Feedback", icon="fa:shield-halved", font_size=14, bold=True, width=200, height=28)
        header.pack(anchor="w", padx=16, pady=(16, 12))

        # Status Badges
        b_ok = Label(parent, text="Active & Synced", icon="fa:circle-check", bg_color="#065f46", fg_color="#34d399", corner_radius=6, width=150, height=28, align="center")
        b_ok.pack(padx=16, pady=4)

        b_warn = Label(parent, text="Update Available", icon="fa:triangle-exclamation", bg_color="#78350f", fg_color="#fbbf24", corner_radius=6, width=150, height=28, align="center")
        b_warn.pack(padx=16, pady=4)

        b_info = Label(parent, text="Blend2D Direct Blit", icon="fa:bolt", bg_color="#1e3a8a", fg_color="#93c5fd", corner_radius=6, width=150, height=28, align="center")
        b_info.pack(padx=16, pady=4)

        # Log Output Box
        self.log_lbl = Label(parent, text="Ready.", font_size=11, fg_color=self.pal.text_muted, width=220, height=26, align="center")
        self.log_lbl.pack(padx=16, pady=(16, 8))

    def _log(self, msg: str):
        self.log_lbl.text = msg

    def _on_toggle_disabled(self):
        is_dis = self._disabled_var.get()
        for w in self._all_widgets:
            w.is_disabled = is_dis

    def _change_theme(self, theme_name: str):
        set_theme(theme_name)
        apply_theme(self.root, theme_name)
        self.pal = get_theme()
        self.log_lbl.text = f"Switched theme to: {theme_name.title()}"


def main():
    root = tk.Tk()
    app = WidgetsShowcaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
