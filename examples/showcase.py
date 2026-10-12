#!/usr/bin/env python3
"""
tkblend Vector UI Showcase Demo
A modern, zero-TTK Material Design 3 vector widget showcase powered by Blend2D and C++ NativeController.
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
    Frame,
    CircularProgress,
    Gauge,
    SegmentedButton,
    RangeSlider,
    Sparkline,
    ComboBox,
    OptionMenu,
    Entry,
    SearchEntry,
    TextBox,
    ScrollableFrame,
    VectorScrollbar,
    Tabview,
    Table,
    set_theme,
    get_theme,
)


class ShowcaseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("tkblend Vector UI Showcase - Material Design 3")
        self.geometry("1060x860")
        self.minsize(920, 720)

        # Start with dark theme
        set_theme("dark")
        self._current_theme = "dark"
        self.configure(bg=get_theme().bg)

        # Available themes mapping
        self._avail_themes = sorted(tb.get_available_themes())
        if "debug" in self._avail_themes:
            self._avail_themes.remove("debug")
        self._theme_title_to_name = {self._format_theme_title(t): t for t in self._avail_themes}
        self._theme_name_to_title = {t: self._format_theme_title(t) for t in self._avail_themes}

        self._click_count = 0
        self._radio_var = tk.StringVar(value="performance")
        self._check_notif = tk.BooleanVar(value=True)
        self._check_gpu = tk.BooleanVar(value=True)

        self._build_ui()

    def _format_theme_title(self, name: str) -> str:
        return name.replace("_", " ").title()

    def _build_ui(self):
        pal = get_theme()

        # Header Frame
        header = tk.Frame(self, bg=pal.bg)
        header.pack(fill="x", padx=32, pady=(20, 14))

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

        version_badge = Badge(title_box, text="v0.3.0 M3", width=95, height=26)
        version_badge.pack(side="left", padx=12)

        # Theme Switcher in Header using native vector ComboBox
        theme_box = tk.Frame(header, bg=pal.bg)
        theme_box.pack(side="right")

        self.theme_lbl = tk.Label(
            theme_box,
            text="Theme:",
            font=("sans-serif", 10, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        )
        self.theme_lbl.pack(side="left", padx=(0, 8))

        self.theme_combo = ComboBox(
            theme_box,
            values=list(self._theme_title_to_name.keys()),
            value=self._format_theme_title(self._current_theme),
            command=self._on_theme_combo_selected,
            width=165,
            height=36,
        )
        self.theme_combo.pack(side="left")

        # Main Scrollable Frame Container for entire showcase dashboard
        scroll_container = ScrollableFrame(self, width=1000, height=760)
        scroll_container.pack(fill="both", expand=True, padx=32, pady=(0, 20))
        main_content = scroll_container.content

        # 2-column responsive layout
        cols_row = tk.Frame(main_content, bg=pal.bg)
        cols_row.pack(fill="x", expand=True)

        col_left = tk.Frame(cols_row, bg=pal.bg)
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        col_right = tk.Frame(cols_row, bg=pal.bg)
        col_right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # -------------------------------------------------------------
        # Card 1: Buttons & Interactive Push Controls (Left)
        # -------------------------------------------------------------
        c1 = Card(col_left, width=460, height=330)
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
        c1_title.pack(anchor="w", pady=(0, 10))

        btn_row1 = tk.Frame(c1_content, bg=pal.card_bg)
        btn_row1.pack(fill="x", pady=4)

        self.btn_counter = Button(
            btn_row1,
            text="Clicked: 0 times",
            variant="primary",
            command=self._on_btn_click,
            width=160,
            height=38,
        )
        self.btn_counter.pack(side="left", padx=(0, 10))

        self.btn_reset = Button(
            btn_row1,
            text="Reset Counter",
            variant="outline",
            command=self._on_btn_reset,
            width=130,
            height=38,
        )
        self.btn_reset.pack(side="left")

        btn_row2 = tk.Frame(c1_content, bg=pal.card_bg)
        btn_row2.pack(fill="x", pady=6)

        btn_tonal = Button(btn_row2, text="Secondary", variant="secondary", width=120, height=36)
        btn_tonal.pack(side="left", padx=(0, 8))

        btn_danger = Button(btn_row2, text="Destructive", variant="destructive", width=120, height=36)
        btn_danger.pack(side="left", padx=(0, 8))

        btn_ghost = Button(btn_row2, text="Ghost Action", variant="ghost", width=110, height=36)
        btn_ghost.pack(side="left")

        self.lbl_status = Label(
            c1_content,
            text="Ready. Click any interactive button to inspect native blits.",
            width=360,
            height=26,
        )
        self.lbl_status.pack(anchor="w", pady=(14, 0))

        # -------------------------------------------------------------
        # Card 2: Form Toggles & Switches (Left)
        # -------------------------------------------------------------
        c2 = Card(col_left, width=460, height=260)
        c2.pack(fill="x", pady=(0, 16))

        c2_content = tk.Frame(c2, bg=pal.card_bg)
        c2_content.pack(fill="both", expand=True, padx=20, pady=16)

        c2_title = tk.Label(
            c2_content,
            text="Form Toggles & Segment Switchers",
            font=("sans-serif", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        c2_title.pack(anchor="w", pady=(0, 8))

        self.seg_button = SegmentedButton(
            c2_content,
            values=["Standard", "Balanced", "Performance"],
            selected_index=0,
            command=self._on_segment_click,
            height=38,
        )
        self.seg_button.pack(fill="x", pady=(0, 12))

        sw_row = tk.Frame(c2_content, bg=pal.card_bg)
        sw_row.pack(fill="x", pady=3)

        self.sw_notif = Switch(sw_row, command=self._on_pref_change, width=44, height=24)
        self.sw_notif.pack(side="left", padx=(0, 10))
        self.sw_notif.is_checked = True

        lbl_sw = tk.Label(sw_row, text="Real-time Blend2D Compositor", font=("sans-serif", 10), fg=pal.fg, bg=pal.card_bg)
        lbl_sw.pack(side="left")

        self.cb_gpu = Checkbox(
            c2_content,
            text="Hardware Direct Drawable Blits",
            is_checked=True,
            command=self._on_pref_change,
            width=240,
            height=32,
        )
        self.cb_gpu.pack(anchor="w", pady=2)

        # -------------------------------------------------------------
        # Card 3: Text Input Fields (Left)
        # -------------------------------------------------------------
        c_inputs = Card(col_left, width=460, height=270)
        c_inputs.pack(fill="x", pady=(0, 16))

        c_inputs_content = tk.Frame(c_inputs, bg=pal.card_bg)
        c_inputs_content.pack(fill="both", expand=True, padx=20, pady=16)

        ci_title = tk.Label(
            c_inputs_content,
            text="Text Inputs & Editors",
            font=("sans-serif", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        ci_title.pack(anchor="w", pady=(0, 8))

        self.txt_entry = Entry(c_inputs_content, text="Antigravity C++ Vector", width=380, height=38)
        self.txt_entry.pack(fill="x", pady=(0, 8))

        self.search_entry = SearchEntry(c_inputs_content, placeholder="Search vector components...", width=380, height=38)
        self.search_entry.pack(fill="x", pady=(0, 8))

        self.textbox = TextBox(c_inputs_content, width=380, height=75)
        self.textbox.pack(fill="x")
        self.textbox.insert("1.0", "Material Design 3 multiline text editor with native vector border highlight.")

        # -------------------------------------------------------------
        # Card 4: Metrics, Circular Gauges & Sliders (Right)
        # -------------------------------------------------------------
        c3 = Card(col_right, width=460, height=400)
        c3.pack(fill="x", pady=(0, 16))

        c3_content = tk.Frame(c3, bg=pal.card_bg)
        c3_content.pack(fill="both", expand=True, padx=20, pady=16)

        c3_title = tk.Label(
            c3_content,
            text="Radial Gauges & Sliders",
            font=("sans-serif", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        c3_title.pack(anchor="w", pady=(0, 8))

        # Radial Gauge & Progress row
        gauge_row = tk.Frame(c3_content, bg=pal.card_bg)
        gauge_row.pack(fill="x", pady=(0, 10))

        self.circular_prog = CircularProgress(
            gauge_row,
            size=95,
            value=65.0,
            title="Load",
            unit="%",
        )
        self.circular_prog.pack(side="left", padx=(10, 20))

        self.speed_gauge = Gauge(
            gauge_row,
            size=115,
            value=84.0,
            title="FPS",
            unit="",
        )
        self.speed_gauge.pack(side="left")

        # Range Slider
        self.lbl_range = tk.Label(
            c3_content,
            text="Active Range Span: 25.0% - 75.0%",
            font=("sans-serif", 10),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        self.lbl_range.pack(anchor="w", pady=(2, 2))

        self.range_slider = RangeSlider(
            c3_content,
            from_=0.0,
            to=100.0,
            values=(25.0, 75.0),
            command=self._on_range_slider_moved,
            height=32,
        )
        self.range_slider.pack(fill="x", pady=(0, 8))

        # Standard Linear Slider
        self.lbl_slider_val = tk.Label(
            c3_content,
            text="Resolution Scale: 65%",
            font=("sans-serif", 10),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        self.lbl_slider_val.pack(anchor="w", pady=(2, 2))

        self.slider = Slider(
            c3_content,
            from_=0.0,
            to=100.0,
            value=65.0,
            command=self._on_slider_moved,
            height=32,
        )
        self.slider.pack(fill="x", pady=(0, 8))

        self.progress = Progressbar(c3_content, value=65.0, maximum=100.0, height=10)
        self.progress.pack(fill="x", pady=(0, 10))

        prog_btns = tk.Frame(c3_content, bg=pal.card_bg)
        prog_btns.pack(fill="x")

        btn_step = Button(prog_btns, text="+10% Step", variant="primary", command=self._on_step_progress, width=110, height=40)
        btn_step.pack(side="left", padx=(0, 8))

        btn_reset_prog = Button(prog_btns, text="Reset", variant="outline", command=self._on_reset_progress, width=90, height=40)
        btn_reset_prog.pack(side="left")

        # -------------------------------------------------------------
        # Card 5: Sparkline Charts & Trend Analytics (Right)
        # -------------------------------------------------------------
        c_trends = Card(col_right, width=460, height=220)
        c_trends.pack(fill="x", pady=(0, 16))

        c_trends_content = tk.Frame(c_trends, bg=pal.card_bg)
        c_trends_content.pack(fill="both", expand=True, padx=20, pady=16)

        ct_title = tk.Label(
            c_trends_content,
            text="Trend Analytics & Sparklines",
            font=("sans-serif", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        ct_title.pack(anchor="w", pady=(0, 8))

        spark_row = tk.Frame(c_trends_content, bg=pal.card_bg)
        spark_row.pack(fill="x", pady=4)

        lbl_s1 = tk.Label(spark_row, text="Frame Latency (ms):", font=("sans-serif", 10), fg=pal.fg, bg=pal.card_bg)
        lbl_s1.pack(side="left", padx=(0, 10))

        self.spark1 = Sparkline(spark_row, data=[4.2, 3.8, 5.1, 4.0, 3.2, 3.5, 2.9, 3.1], width=160, height=32)
        self.spark1.pack(side="right")

        spark_row2 = tk.Frame(c_trends_content, bg=pal.card_bg)
        spark_row2.pack(fill="x", pady=8)

        lbl_s2 = tk.Label(spark_row2, text="Memory Throughput (GB/s):", font=("sans-serif", 10), fg=pal.fg, bg=pal.card_bg)
        lbl_s2.pack(side="left", padx=(0, 10))

        self.spark2 = Sparkline(spark_row2, data=[12.0, 18.5, 15.2, 24.0, 28.5, 31.0, 34.2], width=160, height=32)
        self.spark2.pack(side="right")

        # -------------------------------------------------------------
        # Card 6: Tabview Container (Right)
        # -------------------------------------------------------------
        c_tabs = Card(col_right, width=460, height=230)
        c_tabs.pack(fill="x", pady=(0, 16))

        c_tabs_content = tk.Frame(c_tabs, bg=pal.card_bg)
        c_tabs_content.pack(fill="both", expand=True, padx=16, pady=14)

        self.tabview = Tabview(c_tabs_content, width=420, height=180)
        self.tabview.pack(fill="both", expand=True)

        tab1 = self.tabview.add("Engine")
        tk.Label(tab1, text="Blend2D Direct Pipeline v0.3.0", font=("sans-serif", 11, "bold"), fg=pal.fg, bg=pal.card_bg).pack(pady=10)
        tk.Label(tab1, text="Zero TTK overhead, immediate blit directly to window.", font=("sans-serif", 9), fg=pal.text_muted, bg=pal.card_bg).pack()

        tab2 = self.tabview.add("Surface")
        tk.Label(tab2, text="Surface Buffer Engine", font=("sans-serif", 11, "bold"), fg=pal.fg, bg=pal.card_bg).pack(pady=10)
        tk.Label(tab2, text="Zero-copy blitting without intermediate PhotoImage allocations.", font=("sans-serif", 9), fg=pal.text_muted, bg=pal.card_bg).pack()

        tab3 = self.tabview.add("Theme")
        tk.Label(tab3, text="Dynamic Palette Cascade", font=("sans-serif", 11, "bold"), fg=pal.fg, bg=pal.card_bg).pack(pady=10)
        tk.Label(tab3, text="18+ Built-in Material themes with dynamic CSS token mapping.", font=("sans-serif", 9), fg=pal.text_muted, bg=pal.card_bg).pack()

        # -------------------------------------------------------------
        # Full-Width Card: High-Performance Data Table
        # -------------------------------------------------------------
        c_tbl = Card(main_content, width=960, height=260)
        c_tbl.pack(fill="x", pady=(0, 20))

        c_tbl_content = tk.Frame(c_tbl, bg=pal.card_bg)
        c_tbl_content.pack(fill="both", expand=True, padx=20, pady=16)

        tbl_title_row = tk.Frame(c_tbl_content, bg=pal.card_bg)
        tbl_title_row.pack(fill="x", pady=(0, 8))

        tk.Label(
            tbl_title_row,
            text="High-Performance Vector Data Table",
            font=("sans-serif", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        ).pack(side="left")

        self.lbl_tbl_sel = tk.Label(
            tbl_title_row,
            text="Click a row to select or column header to sort.",
            font=("sans-serif", 9),
            fg=pal.text_muted,
            bg=pal.card_bg,
        )
        self.lbl_tbl_sel.pack(side="right")

        self.table = Table(
            c_tbl_content,
            columns=["Component Class", "Engine Architecture", "Rendering Path", "Status"],
            data=[
                ["Button", "BaseControl + NativeController", "C++ DrawEngine / Blend2D", "Active"],
                ["CircularProgress", "BaseControl + NativeController", "BLPath ArcTo / DrawBatch", "Active"],
                ["SegmentedButton", "BaseControl + NativeController", "M3 Capsule Pill / DrawBatch", "Active"],
                ["RangeSlider", "BaseControl + NativeController", "Dual Knob / C++ MotionNotify", "Active"],
                ["Sparkline", "BaseControl + NativeController", "Continuous Polyline / Gradient", "Active"],
                ["ComboBox", "BaseControl + NativeController", "M3 Popup Surface / Vector List", "Active"],
                ["ScrollableFrame", "BaseControl + VectorScrollbar", "Smooth Viewport Blit", "Active"],
            ],
            command=self._on_table_row_select,
            height=160,
        )
        self.table.pack(fill="x")

    def _on_btn_click(self):
        self._click_count += 1
        self.btn_counter.text = f"Clicked: {self._click_count} times"
        self.lbl_status.text = f"Button triggered at iteration #{self._click_count}"

    def _on_btn_reset(self):
        self._click_count = 0
        self.btn_counter.text = "Clicked: 0 times"
        self.lbl_status.text = "Counter reset to zero."

    def _on_segment_click(self, val: str):
        self.lbl_status.text = f"Profile segment switched to: {val}"

    def _on_slider_moved(self, val: float):
        self.lbl_slider_val.config(text=f"Resolution Scale: {int(val)}%")
        self.progress.set(val)
        self.circular_prog.set(val)

    def _on_range_slider_moved(self, vals):
        low, high = vals
        self.lbl_range.config(text=f"Active Range Span: {low:.1f}% - {high:.1f}%")

    def _on_step_progress(self):
        new_val = min(100.0, self.progress.get() + 10.0)
        self.progress.set(new_val)
        self.slider.set(new_val)
        self.circular_prog.set(new_val)
        self.lbl_slider_val.config(text=f"Resolution Scale: {int(new_val)}%")

    def _on_reset_progress(self):
        self.progress.set(0.0)
        self.slider.set(0.0)
        self.circular_prog.set(0.0)
        self.lbl_slider_val.config(text="Resolution Scale: 0%")

    def _on_pref_change(self):
        notif = "ON" if self.sw_notif.is_checked else "OFF"
        gpu = "Enabled" if self.cb_gpu.is_checked else "Disabled"
        self.lbl_status.text = f"Preferences: Compositor {notif}, Direct Blits {gpu}"

    def _on_table_row_select(self, row_idx: int, row_data: list):
        if row_data:
            self.lbl_tbl_sel.config(text=f"Selected: {row_data[0]} ({row_data[1]})")

    def _on_theme_combo_selected(self, selected_title: str):
        theme_name = self._theme_title_to_name.get(selected_title)
        if theme_name and theme_name != self._current_theme:
            self._select_theme(theme_name)

    def _select_theme(self, theme_name: str):
        if theme_name == self._current_theme:
            return
        self._current_theme = theme_name
        title = self._format_theme_title(theme_name)
        if self.theme_combo.get() != title:
            self.theme_combo.set(title)
        set_theme(theme_name)
        pal = get_theme()
        self.configure(bg=pal.bg)
        self._update_theme_colors(self, pal)
        tb.cascade_bg_to_children(self, pal.bg)

    def _update_theme_colors(self, widget, pal):
        for child in widget.winfo_children():
            if isinstance(child, tk.Frame) and not isinstance(child, Card):
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
