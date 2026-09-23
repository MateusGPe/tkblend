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
        self._on_theme_changed(pal)

    def _build_ui(self):
        # Top App Bar
        self.top_bar = tb.Frame(
            self,
            rx=0,
            ry=0,
            elevation=2.0,
            height=54,
        )
        self.top_bar.pack(fill="x", side="top")

        # App Title & Icon
        self.app_icon = tb.VectorIcon(
            self.top_bar,
            icon_name="checkmark",
            size=28,
        )
        self.app_icon.pack(side="left", padx=(16, 6), pady=10)

        self.title_label = tb.IconLabel(
            self.top_bar,
            text="tkblend Vector Suite",
            icon="dot",
            font_size=14,
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
        )
        self.theme_menu.pack(side="right", padx=16, pady=10)

        self.theme_lbl = tb.IconLabel(
            self.top_bar,
            text="Theme:",
            icon="dot",
            font_size=11,
            width=65,
        )
        self.theme_lbl.pack(side="right", padx=4, pady=10)

        # Main Tabview
        self.tabview = tb.Tabview(
            self,
            rx=12,
            ry=12,
            elevation=4.0,
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
            on_change=lambda idx, val: self._on_seg_changed(val),
        )
        self.seg_bar.grid(row=0, column=0, columnspan=2, padx=12, pady=(10, 8), sticky="ew")

        # Left Column: Scrollable Metrics & Toggles
        self.left_scroll = tb.ScrollableFrame(
            parent,
            rx=10,
            ry=10,
            elevation=2.0,
        )
        self.left_scroll.grid(row=1, column=0, padx=(12, 6), pady=(0, 12), sticky="nsew")

        scroll_inner = self.left_scroll.scrollable_frame

        # Metric Badges
        badge_row = tk.Frame(scroll_inner)
        badge_row.pack(fill="x", padx=10, pady=8)

        b1 = tb.Badge(badge_row, text="Active", variant="success")
        b1.pack(side="left", padx=4)
        b2 = tb.Badge(badge_row, text="High Load", variant="warning")
        b2.pack(side="left", padx=4)
        b3 = tb.Badge(badge_row, text="Blend2D v0.3", variant="primary")
        b3.pack(side="left", padx=4)

        # Interactive Sliders & Progress
        self.dash_slider = tb.Slider(
            scroll_inner,
            value=65.0,
            width=280,
            height=26,
            on_change=self._on_dash_slider_change,
        )
        self.dash_slider.pack(fill="x", padx=12, pady=6)

        self.dash_progress = tb.ProgressBar(
            scroll_inner,
            value=65.0,
            width=280,
            height=14,
        )
        self.dash_progress.pack(fill="x", padx=12, pady=6)

        # Switches & Checkboxes
        sw_row = tk.Frame(scroll_inner)
        sw_row.pack(fill="x", padx=12, pady=6)
        sw_lbl = tb.IconLabel(sw_row, text="Hardware Acceleration", icon="dot", font_size=11, width=180)
        sw_lbl.pack(side="left")
        self.sw1 = tb.Switch(sw_row, is_on=True)
        self.sw1.pack(side="right")

        chk_row = tk.Frame(scroll_inner)
        chk_row.pack(fill="x", padx=12, pady=6)
        self.chk1 = tb.Checkbox(chk_row, text="Enable Subpixel Vector AA", is_checked=True)
        self.chk1.pack(side="left")

        # Right Column: Controls & Card
        self.right_card = tb.Card(
            parent,
            rx=10,
            ry=10,
            elevation=2.0,
        )
        self.right_card.grid(row=1, column=1, padx=(6, 12), pady=(0, 12), sticky="nsew")

        # Dropdowns and ComboBox
        combo_lbl = tb.IconLabel(self.right_card, text="Select Region:", icon="chevron_right", font_size=11)
        combo_lbl.pack(anchor="w", padx=16, pady=(12, 4))

        self.combo = tb.ComboBox(
            self.right_card,
            values=["US-East (N. Virginia)", "US-West (Oregon)", "EU-Central (Frankfurt)", "AP-Southeast (Tokyo)"],
        )
        self.combo.pack(fill="x", padx=16, pady=4)

        opt_lbl = tb.IconLabel(self.right_card, text="Deployment Target:", icon="chevron_right", font_size=11)
        opt_lbl.pack(anchor="w", padx=16, pady=(10, 4))

        self.opt_menu = tb.OptionMenu(
            self.right_card,
            values=["Production Cluster", "Staging Environment", "Local Dev Node"],
        )
        self.opt_menu.pack(fill="x", padx=16, pady=4)

        # Action Buttons
        btn_row = tk.Frame(self.right_card)
        btn_row.pack(fill="x", padx=16, pady=(16, 8))

        btn_deploy = tb.Button(
            btn_row,
            text="Deploy Cluster",
            rx=8,
            ry=8,
            width=130,
            height=34,
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
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_rowconfigure(2, weight=0)

        # Top Action & Filter Toolbar
        top_bar = tk.Frame(parent)
        top_bar.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="ew")

        lbl_filter = tb.IconLabel(top_bar, text="Filter:", icon="search" if hasattr(tb, "VectorIcon") else "dot", font_size=11)
        lbl_filter.pack(side="left", padx=(0, 6))

        self.txt_filter = tb.TextInput(
            top_bar,
            placeholder_text="Search hostname, region, status...",
            width=260,
            height=30,
        )
        self.txt_filter.pack(side="left", padx=(0, 10))
        self.txt_filter.bind("<KeyRelease>", lambda e: self._on_table_filter_changed(self.txt_filter.get()))

        btn_autofit = tb.Button(
            top_bar,
            text="Auto-Fit Columns",
            variant="secondary",
            rx=6,
            ry=6,
            width=120,
            height=30,
            command=lambda: self.table.auto_fit_all_columns(),
        )
        btn_autofit.pack(side="left", padx=4)

        btn_copy = tb.Button(
            top_bar,
            text="Copy Selected",
            variant="secondary",
            rx=6,
            ry=6,
            width=110,
            height=30,
            command=lambda: self.table.copy_to_clipboard(),
        )
        btn_copy.pack(side="left", padx=4)

        columns = [
            {"id": "id", "title": "ID", "width": 55, "align": "center"},
            {"id": "name", "title": "Host Name (Double-click to edit)", "width": 210, "align": "left", "editable": True},
            {"id": "region", "title": "Region", "width": 110, "align": "left", "editable": True},
            {"id": "cpu", "title": "CPU %", "width": 120, "type": "progress", "align": "left"},
            {"id": "mem", "title": "Memory", "width": 85, "align": "right"},
            {
                "id": "status",
                "title": "Status",
                "width": 100,
                "align": "center",
                "type": "badge",
                "badge_colors": {
                    "Healthy": "#10b981",
                    "Warning": "#f59e0b",
                    "Critical": "#ef4444",
                    "Idle": "#64748b",
                },
                "badge_fg": "#ffffff",
            },
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
            {"id": "11", "name": "ml-inference-gpu-01", "region": "US-East", "cpu": "88.0%", "mem": "64.0 GB", "status": "Warning"},
            {"id": "12", "name": "ml-inference-gpu-02", "region": "US-East", "cpu": "96.5%", "mem": "64.0 GB", "status": "Critical"},
            {"id": "13", "name": "elastic-search-hot-1", "region": "EU-Central", "cpu": "41.2%", "mem": "32.0 GB", "status": "Healthy"},
            {"id": "14", "name": "elastic-search-hot-2", "region": "EU-Central", "cpu": "43.9%", "mem": "32.0 GB", "status": "Healthy"},
            {"id": "15", "name": "notification-dispatcher", "region": "AP-Tokyo", "cpu": "05.1%", "mem": "1.0 GB", "status": "Idle"},
        ]

        self.table = tb.Table(
            parent,
            columns=columns,
            data=sample_data,
            select_mode="extended",
            on_select=self._on_table_row_selected,
        )
        self.table.grid(row=1, column=0, padx=12, pady=6, sticky="nsew")

        # Table Bottom Control Bar
        ctrl_bar = tk.Frame(parent)
        ctrl_bar.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.lbl_selected_info = tb.IconLabel(
            ctrl_bar,
            text="Selected Host: None",
            icon="dot",
            font_size=11,
            width=280,
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
        )
        btn_del.pack(side="right", padx=4)

    def _on_table_filter_changed(self, text: str):
        self.table.filter_by(text)

    def _on_table_row_selected(self, indices: Any, rows: Any = None):
        selected_rows = self.table.get_selected_rows()
        if not selected_rows:
            self.lbl_selected_info.set_text("Selected Host: None")
        elif len(selected_rows) == 1:
            row = selected_rows[0]
            host = row.get("name", "Unknown") if isinstance(row, dict) else str(row)
            status = row.get("status", "Unknown") if isinstance(row, dict) else ""
            self.lbl_selected_info.set_text(f"Selected: {host} ({status})")
        else:
            self.lbl_selected_info.set_text(f"Selected: {len(selected_rows)} nodes")

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
        left_form = tb.Card(parent, rx=10, ry=10, elevation=2.0)
        left_form.grid(row=0, column=0, padx=(12, 6), pady=12, sticky="nsew")

        tb.IconLabel(left_form, text="Project Name:", icon="dot", font_size=11).pack(anchor="w", padx=16, pady=(12, 2))
        self.proj_name = tb.TextInput(left_form, placeholder_text="Enter repository name...")
        self.proj_name.pack(fill="x", padx=16, pady=4)

        tb.IconLabel(left_form, text="Cluster Replica Count:", icon="dot", font_size=11).pack(anchor="w", padx=16, pady=(8, 2))
        self.spin = tb.SpinBox(left_form, from_=1, to=64, value=3)
        self.spin.pack(fill="x", padx=16, pady=4)

        tb.IconLabel(left_form, text="Deployment Environment:", icon="dot", font_size=11).pack(anchor="w", padx=16, pady=(8, 2))
        self.env_radio = tb.RadioGroup(
            left_form,
            options=["Development", "Staging", "Production"],
            selected="Staging",
        )
        self.env_radio.pack(fill="x", padx=16, pady=4)

        # Right: Multiline TextBox Editor
        right_form = tb.Card(parent, rx=10, ry=10, elevation=2.0)
        right_form.grid(row=0, column=1, padx=(6, 12), pady=12, sticky="nsew")

        tb.IconLabel(right_form, text="Configuration Notes (TextBox):", icon="dot", font_size=11).pack(anchor="w", padx=16, pady=(12, 4))

        self.textbox = tb.TextBox(
            right_form,
            placeholder_text="Enter detailed deployment notes or release changelog here...",
            height=180,
        )
        self.textbox.pack(fill="both", expand=True, padx=16, pady=4)
        self.textbox.insert("1.0", "# Deployment Checklist\n- Verified Blend2D vector anti-aliasing\n- Checked subpixel DPI scaling\n- Dynamic theme listener active\n")

        # Buttons
        tb_actions = tk.Frame(right_form)
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
        )
        btn_save.pack(side="right")

    # -------------------------------------------------------------
    # TAB 4: ABOUT ENGINE
    # -------------------------------------------------------------
    def _build_about_tab(self, parent: tb.Frame):
        about_card = tb.Card(parent, rx=12, ry=12, elevation=2.0)
        about_card.pack(fill="both", expand=True, padx=16, pady=16)

        tb.IconLabel(about_card, text="Blend2D Pure Vector Architecture", icon="checkmark", font_size=14).pack(anchor="w", padx=20, pady=(16, 6))

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

        pal = tb.get_theme()
        self.lbl_desc = tk.Label(
            about_card,
            text=desc,
            justify="left",
            font=("sans-serif", 10),
            background=pal.card_bg,
            foreground=pal.fg,
        )
        self.lbl_desc.pack(anchor="w", padx=20, pady=10)

    def _on_theme_selected(self, theme_name: str):
        tb.set_theme(theme_name)

    def _on_theme_changed(self, palette: tb.Palette):
        if not self.winfo_exists():
            return
        self.configure(background=palette.bg)
        self.theme_menu.set(palette.name)
        if hasattr(self, "lbl_desc") and self.lbl_desc.winfo_exists():
            self.lbl_desc.configure(
                background=palette.card_bg,
                foreground=palette.fg,
            )
        tb.cascade_bg_to_children(self, palette.bg)


def main():
    app = VectorWidgetsShowcase()
    app.mainloop()


if __name__ == "__main__":
    main()
