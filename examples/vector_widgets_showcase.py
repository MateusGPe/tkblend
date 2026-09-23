"""
tkblend Vector Widgets Gallery & Showcase
Demonstrates pure Blend2D vector widgets: Tabview, ScrollableFrame, TextBox,
Table, ComboBox, OptionMenu, SegmentedButton, VectorIcon, and more.
"""

from __future__ import annotations
import tkinter as tk
import tkblend as tb


class VectorWidgetsShowcase(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("tkblend Vector Widgets Gallery - Pure Blend2D UI")
        self.geometry("980x740")
        self.minsize(860, 620)

        # Set default theme
        tb.set_theme("dark")
        pal = tb.get_theme()
        self.configure(background=pal.bg)

        # Build Main UI
        self._build_ui()
        tb.add_theme_listener(self._on_theme_changed)

    def _build_ui(self):
        # Top App Bar
        self.top_bar = tb.Frame(
            self,
            rx=0,
            ry=0,
            elevation=2.0,
            height=54,
            parent_bg=tb.get_theme().bg,
        )
        self.top_bar.pack(fill="x", side="top")

        # App Title & Icon
        self.app_icon = tb.VectorIcon(
            self.top_bar,
            icon_name="checkmark",
            size=28,
            parent_bg=self.top_bar.bg_color,
        )
        self.app_icon.pack(side="left", padx=(16, 6), pady=10)

        self.title_label = tb.IconLabel(
            self.top_bar,
            text="tkblend Vector Suite",
            icon="dot",
            font_size=14,
            parent_bg=self.top_bar.bg_color,
        )
        self.title_label.pack(side="left", padx=4, pady=10)

        # Theme Selector Dropdown
        theme_names = list(tb.get_available_themes())
        self.theme_menu = tb.OptionMenu(
            self.top_bar,
            values=theme_names,
            selected_value="dark",
            command=self._on_theme_selected,
            width=140,
            height=32,
            parent_bg=self.top_bar.bg_color,
        )
        self.theme_menu.pack(side="right", padx=16, pady=10)

        self.theme_lbl = tb.IconLabel(
            self.top_bar,
            text="Theme:",
            icon="dot",
            font_size=11,
            width=65,
            parent_bg=self.top_bar.bg_color,
        )
        self.theme_lbl.pack(side="right", padx=4, pady=10)

        # Main Tabview
        self.tabview = tb.Tabview(
            self,
            rx=12,
            ry=12,
            elevation=4.0,
            parent_bg=tb.get_theme().bg,
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(10, 16))

        # Create Tabs
        tab_dash = self.tabview.add("Dashboard & Controls")
        tab_table = self.tabview.add("Vector Data Table")
        tab_forms = self.tabview.add("Forms & Editor")
        tab_about = self.tabview.add("About Engine")

        self._build_dashboard_tab(tab_dash)
        self._build_table_tab(tab_table)
        self._build_forms_tab(tab_forms)
        self._build_about_tab(tab_about)

    # -------------------------------------------------------------
    # TAB 1: DASHBOARD & CONTROLS
    # -------------------------------------------------------------
    def _build_dashboard_tab(self, parent: tb.Frame):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        # Segmented Button Bar at Top
        self.seg_bar = tb.SegmentedButton(
            parent,
            values=["Analytics", "Servers", "Revenue", "Performance"],
            selected_index=0,
            width=420,
            height=34,
            parent_bg=parent.bg_color,
            on_change=lambda idx, val: self._on_seg_changed(val),
        )
        self.seg_bar.grid(row=0, column=0, columnspan=2, padx=12, pady=(10, 8), sticky="ew")

        # Left Column: Scrollable Metrics & Toggles
        self.left_scroll = tb.ScrollableFrame(
            parent,
            rx=10,
            ry=10,
            elevation=2.0,
            parent_bg=parent.bg_color,
        )
        self.left_scroll.grid(row=1, column=0, padx=(12, 6), pady=(0, 12), sticky="nsew")

        scroll_inner = self.left_scroll.scrollable_frame

        # Metric Badges
        badge_row = tk.Frame(scroll_inner, background=self.left_scroll._card.bg_color)
        badge_row.pack(fill="x", padx=10, pady=8)

        b1 = tb.Badge(badge_row, text="Active", variant="success", parent_bg=self.left_scroll._card.bg_color)
        b1.pack(side="left", padx=4)
        b2 = tb.Badge(badge_row, text="High Load", variant="warning", parent_bg=self.left_scroll._card.bg_color)
        b2.pack(side="left", padx=4)
        b3 = tb.Badge(badge_row, text="Blend2D v0.3", variant="primary", parent_bg=self.left_scroll._card.bg_color)
        b3.pack(side="left", padx=4)

        # Interactive Sliders & Progress
        self.dash_slider = tb.Slider(
            scroll_inner,
            value=65.0,
            width=280,
            height=26,
            on_change=self._on_dash_slider_change,
            parent_bg=self.left_scroll._card.bg_color,
        )
        self.dash_slider.pack(fill="x", padx=12, pady=6)

        self.dash_progress = tb.ProgressBar(
            scroll_inner,
            value=65.0,
            width=280,
            height=14,
            parent_bg=self.left_scroll._card.bg_color,
        )
        self.dash_progress.pack(fill="x", padx=12, pady=6)

        # Switches & Checkboxes
        sw_row = tk.Frame(scroll_inner, background=self.left_scroll._card.bg_color)
        sw_row.pack(fill="x", padx=12, pady=6)
        sw_lbl = tb.IconLabel(sw_row, text="Hardware Acceleration", icon="dot", font_size=11, width=180, parent_bg=self.left_scroll._card.bg_color)
        sw_lbl.pack(side="left")
        self.sw1 = tb.Switch(sw_row, is_on=True, parent_bg=self.left_scroll._card.bg_color)
        self.sw1.pack(side="right")

        chk_row = tk.Frame(scroll_inner, background=self.left_scroll._card.bg_color)
        chk_row.pack(fill="x", padx=12, pady=6)
        self.chk1 = tb.Checkbox(chk_row, text="Enable Subpixel Vector AA", is_checked=True, parent_bg=self.left_scroll._card.bg_color)
        self.chk1.pack(side="left")

        # Right Column: Controls & Card
        self.right_card = tb.Card(
            parent,
            rx=10,
            ry=10,
            elevation=2.0,
            parent_bg=parent.bg_color,
        )
        self.right_card.grid(row=1, column=1, padx=(6, 12), pady=(0, 12), sticky="nsew")

        # Dropdowns and ComboBox
        card_inner_bg = self.right_card.bg_color
        combo_lbl = tb.IconLabel(self.right_card, text="Select Region:", icon="chevron_right", font_size=11, parent_bg=card_inner_bg)
        combo_lbl.pack(anchor="w", padx=16, pady=(12, 4))

        self.combo = tb.ComboBox(
            self.right_card,
            values=["US-East (N. Virginia)", "US-West (Oregon)", "EU-Central (Frankfurt)", "AP-Southeast (Tokyo)"],
            parent_bg=card_inner_bg,
        )
        self.combo.pack(fill="x", padx=16, pady=4)

        opt_lbl = tb.IconLabel(self.right_card, text="Deployment Target:", icon="chevron_right", font_size=11, parent_bg=card_inner_bg)
        opt_lbl.pack(anchor="w", padx=16, pady=(10, 4))

        self.opt_menu = tb.OptionMenu(
            self.right_card,
            values=["Production Cluster", "Staging Environment", "Local Dev Node"],
            parent_bg=card_inner_bg,
        )
        self.opt_menu.pack(fill="x", padx=16, pady=4)

        # Action Buttons
        btn_row = tk.Frame(self.right_card, background=card_inner_bg)
        btn_row.pack(fill="x", padx=16, pady=(16, 8))

        btn_deploy = tb.Button(
            btn_row,
            text="Deploy Cluster",
            rx=8,
            ry=8,
            width=130,
            height=34,
            parent_bg=card_inner_bg,
            command=lambda: print("Deploy clicked!"),
        )
        btn_deploy.pack(side="left", padx=(0, 6))

        btn_cancel = tb.Button(
            btn_row,
            text="Cancel",
            variant="secondary",
            rx=8,
            ry=8,
            width=100,
            height=34,
            parent_bg=card_inner_bg,
        )
        btn_cancel.pack(side="left")

    def _on_dash_slider_change(self, val: float):
        self.dash_progress.set_value(val)

    def _on_seg_changed(self, val: str):
        print(f"Segment switched to: {val}")

    # -------------------------------------------------------------
    # TAB 2: VECTOR DATA TABLE
    # -------------------------------------------------------------
    def _build_table_tab(self, parent: tb.Frame):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=0)

        columns = [
            {"id": "id", "title": "ID", "width": 55, "align": "center"},
            {"id": "name", "title": "Host Name", "width": 140, "align": "left"},
            {"id": "region", "title": "Region", "width": 110, "align": "left"},
            {"id": "cpu", "title": "CPU %", "width": 75, "align": "right"},
            {"id": "mem", "title": "Memory", "width": 85, "align": "right"},
            {"id": "status", "title": "Status", "width": 90, "align": "center"},
        ]

        sample_data = [
            {"id": "01", "name": "prod-api-edge-01", "region": "US-East", "cpu": "34.2%", "mem": "4.2 GB", "status": "Healthy"},
            {"id": "02", "name": "prod-api-edge-02", "region": "US-East", "cpu": "58.7%", "mem": "6.8 GB", "status": "Healthy"},
            {"id": "03", "name": "db-cluster-primary", "region": "EU-West", "cpu": "78.4%", "mem": "32.1 GB", "status": "Warning"},
            {"id": "04", "name": "redis-cache-master", "region": "US-East", "cpu": "12.0%", "mem": "16.0 GB", "status": "Healthy"},
            {"id": "05", "name": "auth-gateway-svc", "region": "AP-Tokyo", "cpu": "22.5%", "mem": "2.1 GB", "status": "Healthy"},
            {"id": "06", "name": "worker-queue-node-1", "region": "US-West", "cpu": "91.8%", "mem": "14.5 GB", "status": "Critical"},
            {"id": "07", "name": "worker-queue-node-2", "region": "US-West", "cpu": "45.0%", "mem": "8.2 GB", "status": "Healthy"},
            {"id": "08", "name": "analytics-ingest", "region": "EU-Central", "cpu": "64.1%", "mem": "18.4 GB", "status": "Healthy"},
            {"id": "09", "name": "backup-sync-daemon", "region": "US-East", "cpu": "08.3%", "mem": "1.4 GB", "status": "Idle"},
            {"id": "10", "name": "billing-webhook-svc", "region": "US-East", "cpu": "15.9%", "mem": "3.0 GB", "status": "Healthy"},
        ]

        self.table = tb.Table(
            parent,
            columns=columns,
            data=sample_data,
            on_select=self._on_table_row_selected,
            parent_bg=parent.bg_color,
        )
        self.table.grid(row=0, column=0, padx=12, pady=10, sticky="nsew")

        # Table Control Bar
        ctrl_bar = tk.Frame(parent, background=parent.bg_color)
        ctrl_bar.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.lbl_selected_info = tb.IconLabel(
            ctrl_bar,
            text="Selected Host: None",
            icon="dot",
            font_size=11,
            width=240,
            parent_bg=parent.bg_color,
        )
        self.lbl_selected_info.pack(side="left", padx=4)

        btn_add = tb.Button(
            ctrl_bar,
            text="+ Add Node",
            rx=6,
            ry=6,
            width=100,
            height=30,
            command=self._on_table_add_row,
            parent_bg=parent.bg_color,
        )
        btn_add.pack(side="right", padx=4)

        btn_del = tb.Button(
            ctrl_bar,
            text="Delete Selected",
            variant="secondary",
            rx=6,
            ry=6,
            width=120,
            height=30,
            command=self._on_table_del_row,
            parent_bg=parent.bg_color,
        )
        btn_del.pack(side="right", padx=4)

    def _on_table_row_selected(self, idx: int, row: dict):
        host = row.get("name", "Unknown")
        status = row.get("status", "Unknown")
        self.lbl_selected_info.set_text(f"Selected: {host} ({status})")

    def _on_table_add_row(self):
        new_id = f"{len(self.table._data) + 1:02d}"
        new_row = {
            "id": new_id,
            "name": f"worker-node-{new_id}",
            "region": "US-East",
            "cpu": "25.0%",
            "mem": "4.0 GB",
            "status": "Healthy",
        }
        self.table.insert_row(new_row)

    def _on_table_del_row(self):
        sel = self.table.get_selected_index()
        if sel is not None:
            self.table.delete_row(sel)
            self.lbl_selected_info.set_text("Selected Host: None")

    # -------------------------------------------------------------
    # TAB 3: FORMS & MULTILINE TEXTBOX
    # -------------------------------------------------------------
    def _build_forms_tab(self, parent: tb.Frame):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        # Left: Single-line inputs & spinboxes
        left_form = tb.Card(parent, rx=10, ry=10, elevation=2.0, parent_bg=parent.bg_color)
        left_form.grid(row=0, column=0, padx=(12, 6), pady=12, sticky="nsew")

        fbg = left_form.bg_color
        tb.IconLabel(left_form, text="Project Name:", icon="dot", font_size=11, parent_bg=fbg).pack(anchor="w", padx=16, pady=(12, 2))
        self.proj_name = tb.TextInput(left_form, placeholder_text="Enter repository name...", parent_bg=fbg)
        self.proj_name.pack(fill="x", padx=16, pady=4)

        tb.IconLabel(left_form, text="Cluster Replica Count:", icon="dot", font_size=11, parent_bg=fbg).pack(anchor="w", padx=16, pady=(8, 2))
        self.spin = tb.SpinBox(left_form, from_=1, to=64, value=3, parent_bg=fbg)
        self.spin.pack(fill="x", padx=16, pady=4)

        tb.IconLabel(left_form, text="Deployment Environment:", icon="dot", font_size=11, parent_bg=fbg).pack(anchor="w", padx=16, pady=(8, 2))
        self.env_radio = tb.RadioGroup(
            left_form,
            options=["Development", "Staging", "Production"],
            selected="Staging",
            parent_bg=fbg,
        )
        self.env_radio.pack(fill="x", padx=16, pady=4)

        # Right: Multiline TextBox Editor
        right_form = tb.Card(parent, rx=10, ry=10, elevation=2.0, parent_bg=parent.bg_color)
        right_form.grid(row=0, column=1, padx=(6, 12), pady=12, sticky="nsew")

        rf_bg = right_form.bg_color
        tb.IconLabel(right_form, text="Configuration Notes (TextBox):", icon="dot", font_size=11, parent_bg=rf_bg).pack(anchor="w", padx=16, pady=(12, 4))

        self.textbox = tb.TextBox(
            right_form,
            placeholder_text="Enter detailed deployment notes or release changelog here...",
            height=180,
            parent_bg=rf_bg,
        )
        self.textbox.pack(fill="both", expand=True, padx=16, pady=4)
        self.textbox.insert("1.0", "# Deployment Checklist\n- Verified Blend2D vector anti-aliasing\n- Checked subpixel DPI scaling\n- Dynamic theme listener active\n")

        # Buttons
        tb_actions = tk.Frame(right_form, background=rf_bg)
        tb_actions.pack(fill="x", padx=16, pady=(8, 12))

        btn_clear = tb.Button(
            tb_actions,
            text="Clear Text",
            variant="secondary",
            rx=6,
            ry=6,
            width=90,
            height=30,
            command=self.textbox.clear,
            parent_bg=rf_bg,
        )
        btn_clear.pack(side="left", padx=(0, 6))

        btn_save = tb.Button(
            tb_actions,
            text="Save Configuration",
            rx=6,
            ry=6,
            width=140,
            height=30,
            command=lambda: print("Saved notes:\n", self.textbox.get()),
            parent_bg=rf_bg,
        )
        btn_save.pack(side="right")

    # -------------------------------------------------------------
    # TAB 4: ABOUT ENGINE
    # -------------------------------------------------------------
    def _build_about_tab(self, parent: tb.Frame):
        about_card = tb.Card(parent, rx=12, ry=12, elevation=2.0, parent_bg=parent.bg_color)
        about_card.pack(fill="both", expand=True, padx=16, pady=16)

        ac_bg = about_card.bg_color
        tb.IconLabel(about_card, text="Blend2D Pure Vector Architecture", icon="checkmark", font_size=14, parent_bg=ac_bg).pack(anchor="w", padx=20, pady=(16, 6))

        desc = (
            "tkblend provides hardware-accelerated, crisp vector rasterization directly into Tkinter\n"
            "buffers via zero-copy Tk_PhotoPutBlock with ZERO dependencies on the legacy TTK engine.\n\n"
            "Key Architectural Highlights:\n"
            "• Pure Blend2D C++ vector graphics engine with subpixel anti-aliasing\n"
            "• Zero TTK theme dependencies (no Ttk_RegisterElement or ttk.Style limitations)\n"
            "• High-DPI coordinate scaling across Windows, macOS, and Linux\n"
            "• Dynamic reactive theming with seamless dark/light switching\n"
            "• Drop-in CustomTkinter compatibility bridge (tkblend.ctk)\n"
            "• Full component suite: Tabview, ScrollableFrame, TextBox, Table, ComboBox, OptionMenu, Sliders, and more."
        )

        lbl_desc = tk.Label(
            about_card,
            text=desc,
            justify="left",
            font=("sans-serif", 10),
            background=ac_bg,
            foreground=tb.get_theme().fg,
        )
        lbl_desc.pack(anchor="w", padx=20, pady=10)

    def _on_theme_selected(self, theme_name: str):
        tb.set_theme(theme_name)

    def _on_theme_changed(self, palette: tb.Palette):
        if not self.winfo_exists():
            return
        self.configure(background=palette.bg)
        self.title_label.render()
        self.app_icon.render()


def main():
    app = VectorWidgetsShowcase()
    app.mainloop()


if __name__ == "__main__":
    main()
