"""
tkblend.ctk Showcase - CustomTkinter rendered with Blend2D Vector Engine.

Demonstrates crisp, hardware-accelerated vector anti-aliasing across CustomTkinter widgets
with real-time theme toggling and comparison.
"""

from __future__ import annotations
import tkinter as tk
import tkblend.ctk as ctk


class CTkBlendShowcase(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("tkblend + CustomTkinter Vector Showcase")
        self.geometry("860x700")
        self.minsize(750, 580)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self._build_ui()

    def _build_ui(self):
        # Grid layout configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ----------------- SIDEBAR -----------------
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="tkblend.ctk",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Blend2D Vector Surface",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        self.sidebar_btn_1 = ctk.CTkButton(
            self.sidebar_frame,
            text="Dashboard",
            corner_radius=8,
            command=lambda: print("Dashboard clicked"),
        )
        self.sidebar_btn_1.grid(row=2, column=0, padx=20, pady=10)

        self.sidebar_btn_2 = ctk.CTkButton(
            self.sidebar_frame,
            text="Analytics",
            corner_radius=8,
            fg_color="transparent",
            border_width=2,
            text_color=("gray10", "#DCE4EE"),
            command=lambda: print("Analytics clicked"),
        )
        self.sidebar_btn_2.grid(row=3, column=0, padx=20, pady=10)

        # Engine Status Badge
        self.status_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="✓ Blend2D Active",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#10b981",
        )
        self.status_label.grid(row=5, column=0, padx=20, pady=10)

        # Appearance Mode Controls
        self.appearance_mode_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Appearance Mode:",
            anchor="w",
        )
        self.appearance_mode_label.grid(row=7, column=0, padx=20, pady=(10, 0))

        self.appearance_mode_optionmenu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Dark", "Light", "System"],
            command=self._change_appearance_mode_event,
        )
        self.appearance_mode_optionmenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # ----------------- MAIN CONTENT -----------------
        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.grid(row=0, column=1, padx=20, pady=(20, 20), sticky="nsew")

        self.tabview.add("Interactive Widgets")
        self.tabview.add("Form & Inputs")
        self.tabview.add("About Engine")

        self._setup_widgets_tab()
        self._setup_inputs_tab()
        self._setup_about_tab()

    def _setup_widgets_tab(self):
        tab = self.tabview.tab("Interactive Widgets")
        tab.grid_columnconfigure((0, 1), weight=1)

        # Left Column - Buttons & Controls
        left_frame = ctk.CTkFrame(tab, corner_radius=10)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        lbl_1 = ctk.CTkLabel(left_frame, text="Buttons & States", font=ctk.CTkFont(size=15, weight="bold"))
        lbl_1.pack(padx=15, pady=(15, 10), anchor="w")

        btn_primary = ctk.CTkButton(left_frame, text="Primary Rounded Button", corner_radius=20)
        btn_primary.pack(padx=15, pady=8, fill="x")

        btn_bordered = ctk.CTkButton(
            left_frame,
            text="Bordered Accent Button",
            corner_radius=10,
            border_width=2,
            border_color="#3b82f6",
            fg_color="#1e293b",
            hover_color="#334155",
        )
        btn_bordered.pack(padx=15, pady=8, fill="x")

        # Switches & Checkboxes
        sw_1 = ctk.CTkSwitch(left_frame, text="Smooth Toggle Switch")
        sw_1.select()
        sw_1.pack(padx=15, pady=10, anchor="w")

        chk_1 = ctk.CTkCheckBox(left_frame, text="Vector Checkbox")
        chk_1.select()
        chk_1.pack(padx=15, pady=8, anchor="w")

        # Right Column - Progress & Sliders
        right_frame = ctk.CTkFrame(tab, corner_radius=10)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        lbl_2 = ctk.CTkLabel(right_frame, text="Sliders & Gauges", font=ctk.CTkFont(size=15, weight="bold"))
        lbl_2.pack(padx=15, pady=(15, 10), anchor="w")

        self.slider_label = ctk.CTkLabel(right_frame, text="Slider Value: 60%")
        self.slider_label.pack(padx=15, pady=(5, 2), anchor="w")

        self.slider = ctk.CTkSlider(
            right_frame,
            from_=0,
            to=100,
            command=self._on_slider_change,
            progress_color="#10b981",
            button_color="#34d399",
        )
        self.slider.set(60)
        self.slider.pack(padx=15, pady=10, fill="x")

        lbl_pbar = ctk.CTkLabel(right_frame, text="Vector Progress Bar:")
        lbl_pbar.pack(padx=15, pady=(10, 2), anchor="w")

        self.progressbar = ctk.CTkProgressBar(right_frame, corner_radius=8, progress_color="#8b5cf6")
        self.progressbar.set(0.6)
        self.progressbar.pack(padx=15, pady=10, fill="x")

        # Radio buttons
        lbl_radio = ctk.CTkLabel(right_frame, text="Radio Group:")
        lbl_radio.pack(padx=15, pady=(10, 2), anchor="w")

        self.radio_var = tk.IntVar(value=1)
        r1 = ctk.CTkRadioButton(right_frame, text="Option A (Vector Antialiased)", variable=self.radio_var, value=1)
        r1.pack(padx=15, pady=5, anchor="w")
        r2 = ctk.CTkRadioButton(right_frame, text="Option B (High Precision)", variable=self.radio_var, value=2)
        r2.pack(padx=15, pady=5, anchor="w")

    def _setup_inputs_tab(self):
        tab = self.tabview.tab("Form & Inputs")
        tab.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(tab, corner_radius=12)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        title = ctk.CTkLabel(card, text="Vector-Rendered Text Inputs & Selectors", font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(padx=20, pady=(20, 15), anchor="w")

        entry = ctk.CTkEntry(card, placeholder_text="Type something here...", width=320, corner_radius=8)
        entry.pack(padx=20, pady=10, fill="x")

        opt_menu = ctk.CTkOptionMenu(
            card,
            values=["Vector Preset 1 (High Quality)", "Vector Preset 2 (Balanced)", "Vector Preset 3 (Fast)"],
            corner_radius=8,
        )
        opt_menu.pack(padx=20, pady=10, fill="x")

        combo = ctk.CTkComboBox(
            card,
            values=["Item 1", "Item 2", "Item 3", "Item 4"],
            corner_radius=8,
        )
        combo.pack(padx=20, pady=10, fill="x")

        txt = ctk.CTkTextbox(card, height=120, corner_radius=8)
        txt.insert("1.0", "Blend2D renders all outer rounded borders, backgrounds, and drop shadows with true sub-pixel vector anti-aliasing directly in C++.")
        txt.pack(padx=20, pady=10, fill="both", expand=True)

    def _setup_about_tab(self):
        tab = self.tabview.tab("About Engine")
        card = ctk.CTkFrame(tab, corner_radius=12)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        title = ctk.CTkLabel(card, text="Blend2D Backend for CustomTkinter", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(padx=20, pady=(20, 10), anchor="w")

        info = (
            "This application uses CustomTkinter widgets seamlessly backed by tkblend's Blend2D vector engine.\n\n"
            "Key Advantages:\n"
            " • No TTK dependencies or font-glyph circle hacks\n"
            " • Pure subpixel vector anti-aliasing for all rounded corners and borders\n"
            " • Ultra fast C++ rasterization via Tk_PhotoPutBlock zero-copy blit\n"
            " • 100% backward compatible with existing CustomTkinter layouts and codebases\n"
        )
        lbl_info = ctk.CTkLabel(card, text=info, justify="left", font=ctk.CTkFont(size=13))
        lbl_info.pack(padx=20, pady=10, anchor="w")

    def _on_slider_change(self, value):
        self.slider_label.configure(text=f"Slider Value: {int(value)}%")
        self.progressbar.set(value / 100.0)

    def _change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)


if __name__ == "__main__":
    app = CTkBlendShowcase()
    app.mainloop()
