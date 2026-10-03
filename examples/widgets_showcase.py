"""
tkblend Native Vector Widgets Showcase & Interactive Dashboard
Comprehensive demonstration of pure Blend2D vector UI controls powered by NativeController.
Zero TTK dependencies, zero PhotoImage allocations.
"""

from __future__ import annotations

import math
import random
import tkinter as tk
from typing import List, Optional, Tuple, Dict, Any

import tkblend as tb
from tkblend.widgets import (
    BaseControl,
    ScalingTracker,
    Button,
    Switch,
    Toggle,
    Slider,
    CheckBox,
    ProgressBar,
    CircularProgress,
    Gauge,
    RadioButton,
    Card,
    Label,
    Badge,
    Avatar,
    SegmentedButton,
    RangeSlider,
    ComboBox,
    OptionMenu,
    TextBox,
    Entry,
    SearchEntry,
    ScrollableFrame,
    Table,
    Tabview,
    Sparkline,
    Frame,
)
from tkblend.surface import Surface, ColorLike, LinearGradient, RadialGradient, Path
from tkblend.theme import (
    Palette,
    get_theme,
    set_theme,
    get_available_themes,
    apply_theme,
    resolve_color_failsafe,
    cascade_bg_to_children,
    to_tk_hex,
)


# ==============================================================================
# Custom Blend2D Radial Gauge Component
# ==============================================================================

class RadialGauge(BaseControl):
    """
    Modern circular radial meter / activity gauge rendered natively with Blend2D.
    Supports animated sweep angles, track gradients, and center metric typography.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 140,
        value: float = 65.0,
        min_value: float = 0.0,
        max_value: float = 100.0,
        title: str = "CPU Load",
        unit: str = "%",
        color: Optional[ColorLike] = None,
        track_color: Optional[ColorLike] = None,
        thickness: float = 10.0,
        **kwargs,
    ):
        self._value = float(value)
        self._min_value = float(min_value)
        self._max_value = float(max_value)
        self._title = title
        self._unit = unit
        self._custom_color = color
        self._custom_track_color = track_color
        self._thickness = float(thickness)
        super().__init__(master=master, width=size, height=size, takefocus=False, **kwargs)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float) -> None:
        self._value = max(self._min_value, min(self._max_value, float(val)))
        self.request_redraw()

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, text: str) -> None:
        self._title = text
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)
        cx = w / 2.0
        cy = h / 2.0
        thick = self._thickness * s
        r = min(cx, cy) - thick - (4.0 * s)
        if r <= 2.0:
            return

        # Gauge angles (from 135 deg to 405 deg = 270 deg span)
        start_angle_deg = 135.0
        total_span_deg = 270.0
        start_rad = math.radians(start_angle_deg)
        total_span_rad = math.radians(total_span_deg)

        surf.clear(self._resolved_parent_bg)

        # 1. Track arc background
        track_col = resolve_color_failsafe(self._custom_track_color or pal.track_bg, palette=pal)
        path_track = Path()
        path_track.arc_to(cx, cy, r, r, start_rad, total_span_rad)
        surf.stroke_path(path_track, track_col, stroke_width=thick)

        # 2. Value progress arc
        norm = (self._value - self._min_value) / max(0.001, (self._max_value - self._min_value))
        norm = max(0.0, min(1.0, norm))
        val_span_rad = total_span_rad * norm

        color_active = resolve_color_failsafe(self._custom_color or pal.primary, palette=pal)

        if val_span_rad > 0.005:
            path_val = Path()
            path_val.arc_to(cx, cy, r, r, start_rad, val_span_rad)
            surf.stroke_path(path_val, color_active, stroke_width=thick)

            # Tip indicator glow point
            tip_angle = start_rad + val_span_rad
            tip_x = cx + r * math.cos(tip_angle)
            tip_y = cy + r * math.sin(tip_angle)
            surf.fill_circle(tip_x, tip_y, thick * 0.42, "#ffffff")

        # 3. Metric typography in center
        val_text = f"{int(self._value)}{self._unit}"
        fg_col = pal.fg
        sub_fg = getattr(pal, "text_muted", "#888888")

        surf.draw_text(
            val_text,
            cx,
            cy - (2.0 * s),
            font_size=16.0 * s,
            color=fg_col,
            bold=True,
            align="center",
        )
        surf.draw_text(
            self._title,
            cx,
            cy + (14.0 * s),
            font_size=10.0 * s,
            color=sub_fg,
            align="center",
        )


# ==============================================================================
# Main Widgets Showcase Application
# ==============================================================================

class WidgetsShowcaseApp:
    """
    State-of-the-Art Vector UI Showcase and Interactive Component Explorer.
    Demonstrates 18+ pure Blend2D vector widgets with zero TTK dependencies.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend Vector UI - Component Showcase & Explorer")
        self.root.geometry("1240x860")
        self.root.minsize(1080, 720)

        # Theme & State
        self.current_theme_name = "dark"
        self.active_page = "controls"
        self._all_widgets: List[BaseControl] = []
        self._disabled_var = tk.BooleanVar(value=False)
        self._sim_running = True

        # Interactive state vars
        self._wifi_var = tk.BooleanVar(value=True)
        self._bluetooth_var = tk.BooleanVar(value=False)
        self._notifications_var = tk.BooleanVar(value=True)
        self._agree_var = tk.BooleanVar(value=True)

        self._slider_val_var = tk.DoubleVar(value=68.0)
        self._range_vals = (25.0, 75.0)
        self._progress_val_var = tk.DoubleVar(value=0.72)
        self._radio_var = tk.StringVar(value="turbo")

        # Live data buffers for sparklines
        self._spark_cpu_data = [random.uniform(20, 80) for _ in range(24)]
        self._spark_mem_data = [random.uniform(40, 90) for _ in range(24)]
        self._spark_net_data = [random.uniform(10, 60) for _ in range(24)]

        # Playground dynamic state
        self._pg_radius_var = tk.DoubleVar(value=10.0)
        self._pg_elevation_var = tk.DoubleVar(value=8.0)
        self._pg_icon_name = "fa:rocket"
        self._pg_button_text = "Deploy Vector App"

        # Initialize UI structure
        self.pal = get_theme()
        self._build_dashboard_layout()
        self._change_theme("dark")
        self._navigate_to("controls")
        self._start_simulation_loop()

    # --------------------------------------------------------------------------
    # Master Layout: Sidebar + Header + Content Switcher
    # --------------------------------------------------------------------------

    def _build_dashboard_layout(self):
        self.pages: Dict[str, tk.Frame] = {}
        self.nav_buttons: Dict[str, Button] = {}

        # Master container
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        # 1. Left Sidebar
        self.sidebar = tk.Frame(self.container, width=230)
        self.sidebar.pack(side="left", fill="y", padx=(14, 6), pady=14)
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        # 2. Right Workspace Area
        self.workspace = tk.Frame(self.container)
        self.workspace.pack(side="right", fill="both", expand=True, padx=(6, 14), pady=14)

        # Workspace Header
        self.header_frame = tk.Frame(self.workspace, height=52)
        self.header_frame.pack(fill="x", pady=(0, 10))

        self.lbl_page_title = Label(
            self.header_frame,
            text="Form & Input Controls",
            icon="fa:sliders",
            font_size=17,
            bold=True,
            height=34,
        )
        self.lbl_page_title.pack(side="left")

        # Status & Click Log Banner
        self.log_badge = Label(
            self.header_frame,
            text="System Ready",
            icon="fa:circle-check",
            fg_color="#34d399",
            corner_radius=8,
            height=32,
            align="center",
        )
        self.log_badge.pack(side="right")

        # Content Viewports Container
        self.content_frame = tk.Frame(self.workspace)
        self.content_frame.pack(fill="both", expand=True)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

        # Instantiate Pages
        self.pages["controls"] = self._create_controls_page()
        self.pages["metrics"] = self._create_metrics_page()
        self.pages["containers"] = self._create_containers_page()
        self.pages["playground"] = self._create_playground_page()
        self.pages["themes"] = self._create_themes_page()

    def _build_sidebar(self):
        # Brand Card / Header
        brand_card = Card(self.sidebar, height=72, corner_radius=12)
        brand_card.pack(fill="x", pady=(0, 12))

        brand_lbl = Label(
            brand_card,
            text="tkblend UI",
            icon="fa:cubes",
            font_size=15,
            bold=True,
            height=28,
        )
        brand_lbl.pack(anchor="w", padx=14, pady=(12, 2))

        sub_lbl = Label(
            brand_card,
            text="Blend2D Vector Engine",
            font_size=10,
            fg_color="#8b5cf6",
            height=18,
        )
        sub_lbl.pack(anchor="w", padx=16, pady=(0, 10))

        # Nav Buttons Section
        nav_items = [
            ("controls", "Form & Controls", "fa:sliders"),
            ("metrics", "Data & Metrics", "fa:chart-line"),
            ("containers", "Containers & Layout", "fa:layer-group"),
            ("playground", "Live Playground", "fa:flask"),
            ("themes", "Theme Matrix", "fa:palette"),
        ]

        self.sidebar_nav_frame = tk.Frame(self.sidebar)
        self.sidebar_nav_frame.pack(fill="x", pady=4)

        for page_id, label_text, icon_name in nav_items:
            btn = Button(
                self.sidebar_nav_frame,
                text=label_text,
                icon=icon_name,
                width=202,
                height=38,
                corner_radius=10,
                font_size=11,
                command=lambda pid=page_id: self._navigate_to(pid),
            )
            btn.pack(fill="x", pady=3)
            self.nav_buttons[page_id] = btn

        # Spacer
        spacer = tk.Frame(self.sidebar)
        spacer.pack(fill="both", expand=True)

        # Bottom Controls Card
        bot_card = Card(self.sidebar, height=125, corner_radius=12)
        bot_card.pack(fill="x", pady=(10, 0))

        lbl_bot = Label(bot_card, text="Global Options", font_size=11, bold=True, height=20)
        lbl_bot.pack(anchor="w", padx=14, pady=(10, 4))

        dis_sw = Switch(
            bot_card,
            text="Disable All",
            variable=self._disabled_var,
            command=self._on_toggle_disabled,
            width=170,
            height=26,
        )
        dis_sw.pack(anchor="w", padx=14, pady=2)

        btn_toggle_theme = Button(
            bot_card,
            text="Toggle Dark / Light",
            icon="fa:circle-half-stroke",
            width=174,
            height=30,
            corner_radius=8,
            font_size=10,
            command=self._quick_toggle_dark_light,
        )
        btn_toggle_theme.pack(padx=14, pady=(6, 10))

    def _navigate_to(self, page_id: str):
        self.active_page = page_id

        # Update sidebar button states
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.configure(
                    bg_color=self.pal.primary,
                    fg_color="#ffffff",
                    hover_color=self.pal.primary_hover,
                )
            else:
                btn.configure(
                    bg_color=self.pal.card_bg,
                    fg_color=self.pal.fg,
                    hover_color=self.pal.card_border,
                )

        # Raise active page frame and trigger redraw for visible controls
        for pid, page_frame in self.pages.items():
            if pid == page_id:
                page_frame.grid(row=0, column=0, sticky="nsew")
                self._redraw_hierarchy(page_frame)
            else:
                page_frame.grid_forget()

        # Update header title
        titles = {
            "controls": ("Form & Input Controls", "fa:sliders"),
            "metrics": ("Data, Metrics & Status", "fa:chart-line"),
            "containers": ("Containers & Layouts", "fa:layer-group"),
            "playground": ("Live Widget Playground & Inspector", "fa:flask"),
            "themes": ("Theme Matrix & Palette Gallery", "fa:palette"),
        }
        t, ic = titles.get(page_id, ("Showcase", "fa:cubes"))
        self.lbl_page_title.text = t
        self.lbl_page_title.icon = ic

    def _redraw_hierarchy(self, widget: tk.Misc) -> None:
        if isinstance(widget, BaseControl):
            widget.request_redraw()
        for child in widget.winfo_children():
            self._redraw_hierarchy(child)

    # --------------------------------------------------------------------------
    # Page 1: Form & Input Controls
    # --------------------------------------------------------------------------

    def _create_controls_page(self) -> tk.Frame:
        page = tk.Frame(self.content_frame)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=1)
        page.columnconfigure(2, weight=1)
        page.rowconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)

        # Column 1: Buttons & Actions
        card_btn = Card(page, corner_radius=12)
        card_btn.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        lbl1 = Label(card_btn, text="Buttons & Elevation", icon="fa:hand-pointer", font_size=12, bold=True)
        lbl1.pack(anchor="w", padx=14, pady=(12, 10))

        btn_pri = Button(
            card_btn,
            text="Primary Rocket",
            icon="fa:rocket",
            width=190,
            height=34,
            command=lambda: self._log("Primary button invoked!"),
        )
        btn_pri.pack(padx=14, pady=3)
        self._all_widgets.append(btn_pri)

        btn_sec = Button(
            card_btn,
            text="Secondary Action",
            icon="fa:gear",
            bg_color=self.pal.secondary,
            hover_color=self.pal.primary_hover,
            width=190,
            height=34,
            command=lambda: self._log("Secondary button clicked!"),
        )
        btn_sec.pack(padx=14, pady=3)
        self._all_widgets.append(btn_sec)

        btn_suc = Button(
            card_btn,
            text="Success Save",
            icon="fa:check",
            bg_color="#10b981",
            hover_color="#059669",
            width=190,
            height=34,
            command=lambda: self._log("Changes saved successfully!"),
        )
        btn_suc.pack(padx=14, pady=3)
        self._all_widgets.append(btn_suc)

        btn_del = Button(
            card_btn,
            text="Delete Item",
            icon="fa:trash",
            bg_color="#ef4444",
            hover_color="#dc2626",
            width=190,
            height=34,
            command=lambda: self._log("Delete triggered!"),
        )
        btn_del.pack(padx=14, pady=3)
        self._all_widgets.append(btn_del)

        # Column 2: Toggles & Selectors
        card_tog = Card(page, corner_radius=12)
        card_tog.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        lbl2 = Label(card_tog, text="Toggles & Options", icon="fa:toggle-on", font_size=12, bold=True)
        lbl2.pack(anchor="w", padx=14, pady=(12, 10))

        sw_wifi = Switch(
            card_tog,
            text="Wi-Fi Connection",
            variable=self._wifi_var,
            width=190,
            height=28,
            command=lambda: self._log(f"Wi-Fi: {self._wifi_var.get()}"),
        )
        sw_wifi.pack(anchor="w", padx=14, pady=3)
        self._all_widgets.append(sw_wifi)

        sw_bt = Switch(
            card_tog,
            text="Bluetooth Sync",
            variable=self._bluetooth_var,
            width=190,
            height=28,
            command=lambda: self._log(f"Bluetooth: {self._bluetooth_var.get()}"),
        )
        sw_bt.pack(anchor="w", padx=14, pady=3)
        self._all_widgets.append(sw_bt)

        chk_terms = CheckBox(
            card_tog,
            text="Hardware Accel",
            variable=self._agree_var,
            width=190,
            height=28,
            command=lambda: self._log(f"Hardware Accel: {self._agree_var.get()}"),
        )
        chk_terms.pack(anchor="w", padx=14, pady=3)
        self._all_widgets.append(chk_terms)

        lbl_prof = Label(card_tog, text="Engine Profile:", font_size=10, bold=True)
        lbl_prof.pack(anchor="w", padx=14, pady=(6, 2))

        rb_eco = RadioButton(
            card_tog,
            text="Eco Saver",
            value="eco",
            variable=self._radio_var,
            width=180,
            height=24,
            command=lambda: self._log("Profile: Eco Saver"),
        )
        rb_eco.pack(anchor="w", padx=14, pady=2)
        self._all_widgets.append(rb_eco)

        rb_turbo = RadioButton(
            card_tog,
            text="Turbo Blend2D",
            value="turbo",
            variable=self._radio_var,
            width=180,
            height=24,
            command=lambda: self._log("Profile: Turbo Blend2D"),
        )
        rb_turbo.pack(anchor="w", padx=14, pady=2)
        self._all_widgets.append(rb_turbo)

        # Column 3: Advanced Selectors & Sliders
        card_sel = Card(page, corner_radius=12)
        card_sel.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)

        lbl3 = Label(card_sel, text="Dropdowns & Selectors", icon="fa:list-check", font_size=12, bold=True)
        lbl3.pack(anchor="w", padx=14, pady=(12, 10))

        lbl_cb = Label(card_sel, text="ComboBox Selector:", font_size=10, bold=True)
        lbl_cb.pack(anchor="w", padx=14, pady=(2, 2))

        cb_opt = ComboBox(
            card_sel,
            values=["High Performance", "Balanced Profile", "Ultra Quality", "Low Power"],
            selected_value="High Performance",
            width=200,
            height=32,
            command=lambda val: self._log(f"ComboBox selected: {val}"),
        )
        cb_opt.pack(anchor="w", padx=14, pady=(0, 6))
        self._all_widgets.append(cb_opt)

        lbl_seg = Label(card_sel, text="Segmented Switcher:", font_size=10, bold=True)
        lbl_seg.pack(anchor="w", padx=14, pady=(2, 2))

        seg_ctrl = SegmentedButton(
            card_sel,
            values=["Day", "Week", "Month", "Year"],
            selected_index=1,
            width=200,
            height=30,
            command=lambda val: self._log(f"Segment: {val}"),
        )
        seg_ctrl.pack(anchor="w", padx=14, pady=(0, 6))
        self._all_widgets.append(seg_ctrl)

        lbl_rsl = Label(card_sel, text="Dual RangeSlider (25 - 75):", font_size=10, bold=True)
        lbl_rsl.pack(anchor="w", padx=14, pady=(2, 2))

        rslider = RangeSlider(
            card_sel,
            values=(25.0, 75.0),
            width=200,
            height=28,
            command=lambda vals: self._log(f"Range: {int(vals[0])} - {int(vals[1])}"),
        )
        rslider.pack(anchor="w", padx=14, pady=(0, 4))
        self._all_widgets.append(rslider)

        # Row 1 Bottom: Text Inputs Card & Sliders
        card_bot = Card(page, corner_radius=12)
        card_bot.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=6, pady=6)

        lbl_inputs = Label(card_bot, text="Text Inputs & Interactive Sliders", icon="fa:keyboard", font_size=12, bold=True)
        lbl_inputs.pack(anchor="w", padx=14, pady=(10, 6))

        in_row = tk.Frame(card_bot, background="")
        in_row.pack(fill="x", padx=14, pady=4)

        # Search Entry
        search_in = SearchEntry(
            in_row,
            placeholder="Search vector assets...",
            width=220,
            height=32,
        )
        search_in.pack(side="left", padx=(0, 12))
        self._all_widgets.append(search_in)

        # Standard Entry
        txt_entry = Entry(
            in_row,
            placeholder="User API token",
            icon="fa:key",
            width=220,
            height=32,
        )
        txt_entry.pack(side="left", padx=(0, 12))
        self._all_widgets.append(txt_entry)

        # Standard Slider
        slider_ctrl = Slider(
            in_row,
            from_=0,
            to=100,
            value=65,
            width=220,
            height=30,
            command=lambda v: self._log(f"Slider: {int(v)}%"),
        )
        slider_ctrl.pack(side="left", padx=(0, 12))
        self._all_widgets.append(slider_ctrl)

        # TextBox Multiline
        tb_box = TextBox(
            card_bot,
            width=680,
            height=54,
            font_size=10,
        )
        tb_box.insert("1.0", "Blend2D vector engine renders typography and vector paths directly into Tk window drawables with zero latency.")
        tb_box.pack(fill="x", padx=14, pady=(4, 10))
        self._all_widgets.append(tb_box)

        return page

    # --------------------------------------------------------------------------
    # Page 2: Data & Metrics Visualizations
    # --------------------------------------------------------------------------

    def _create_metrics_page(self) -> tk.Frame:
        page = tk.Frame(self.content_frame)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=1)
        page.rowconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)

        # Card 1: Gauges & Circular Progress
        card_gauges = Card(page, corner_radius=12)
        card_gauges.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        lbl_g = Label(card_gauges, text="Activity & Radial Gauges", icon="fa:chart-pie", font_size=12, bold=True)
        lbl_g.pack(anchor="w", padx=14, pady=(12, 6))

        g_row = tk.Frame(card_gauges, background="")
        g_row.pack(fill="both", expand=True, padx=10, pady=4)

        self.gauge_cpu = RadialGauge(g_row, size=130, value=65, title="CPU Core", unit="%", color="#6366f1")
        self.gauge_cpu.pack(side="left", expand=True, padx=6)
        self._all_widgets.append(self.gauge_cpu)

        self.circ_mem = CircularProgress(g_row, size=115, value=78, unit="%", stroke_width=9.0, fill_color="#3b82f6")
        self.circ_mem.pack(side="left", expand=True, padx=6)
        self._all_widgets.append(self.circ_mem)

        self.circ_disk = CircularProgress(g_row, size=115, value=42, unit="%", stroke_width=9.0, fill_color="#10b981")
        self.circ_disk.pack(side="left", expand=True, padx=6)
        self._all_widgets.append(self.circ_disk)

        # Card 2: Badges, Avatars & Sparklines
        card_status = Card(page, corner_radius=12)
        card_status.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        lbl_s = Label(card_status, text="Status Badges & Avatars", icon="fa:shield-halved", font_size=12, bold=True)
        lbl_s.pack(anchor="w", padx=14, pady=(12, 6))

        # Avatar Row
        av_row = tk.Frame(card_status, background="")
        av_row.pack(fill="x", padx=14, pady=3)

        av1 = Avatar(av_row, text="MG", size=36, status="online")
        av1.pack(side="left", padx=4)
        av2 = Avatar(av_row, text="BL", size=36, status="busy", bg_color="#6366f1")
        av2.pack(side="left", padx=4)
        av3 = Avatar(av_row, icon="fa:user-ninja", size=36, status="active", bg_color="#ec4899")
        av3.pack(side="left", padx=4)

        bdg_on = Badge(av_row, text="ACTIVE", variant="success", dot=True)
        bdg_on.pack(side="left", padx=(12, 4))
        bdg_warn = Badge(av_row, text="WARNING", variant="warning")
        bdg_warn.pack(side="left", padx=4)
        bdg_err = Badge(av_row, text="CRITICAL", variant="danger")
        bdg_err.pack(side="left", padx=4)

        # Sparklines Row
        lbl_sp = Label(card_status, text="Realtime Sparkline Streams:", font_size=10, bold=True)
        lbl_sp.pack(anchor="w", padx=14, pady=(8, 2))

        sp_row = tk.Frame(card_status, background="")
        sp_row.pack(fill="x", padx=14, pady=3)

        self.spark_cpu = Sparkline(sp_row, data=self._spark_cpu_data, kind="area", width=140, height=36, color="#6366f1")
        self.spark_cpu.pack(side="left", padx=4, expand=True)

        self.spark_mem = Sparkline(sp_row, data=self._spark_mem_data, kind="line", width=140, height=36, color="#3b82f6")
        self.spark_mem.pack(side="left", padx=4, expand=True)

        self.spark_net = Sparkline(sp_row, data=self._spark_net_data, kind="bar", width=140, height=36, color="#10b981")
        self.spark_net.pack(side="left", padx=4, expand=True)

        # Card 3 Bottom: Vector Data Table
        card_tbl = Card(page, corner_radius=12)
        card_tbl.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)

        lbl_tbl = Label(card_tbl, text="Vector Data Table & Process Monitor", icon="fa:table", font_size=12, bold=True)
        lbl_tbl.pack(anchor="w", padx=14, pady=(10, 4))

        table_cols = [
            {"name": "pid", "title": "PID", "width": 70},
            {"name": "process", "title": "Process Name", "width": 200},
            {"name": "cpu", "title": "CPU %", "width": 90},
            {"name": "memory", "title": "Memory", "width": 110},
            {"name": "threads", "title": "Threads", "width": 90},
            {"name": "status", "title": "Status", "width": 120},
        ]

        table_rows = [
            {"pid": 1042, "process": "blend2d_renderer_x11", "cpu": "3.8%", "memory": "42 MB", "threads": 8, "status": "Running"},
            {"pid": 1048, "process": "tkblend_event_pump", "cpu": "1.2%", "memory": "28 MB", "threads": 4, "status": "Active"},
            {"pid": 1055, "process": "fontconfig_glyph_cache", "cpu": "0.4%", "memory": "16 MB", "threads": 2, "status": "Idle"},
            {"pid": 1062, "process": "nanobind_ffi_bridge", "cpu": "0.1%", "memory": "12 MB", "threads": 1, "status": "Idle"},
            {"pid": 1070, "process": "surface_blitter_daemon", "cpu": "2.4%", "memory": "34 MB", "threads": 6, "status": "Running"},
        ]

        self.table = Table(
            card_tbl,
            columns=table_cols,
            data=table_rows,
            width=700,
            height=140,
            on_select=lambda idx, row: self._log(f"Table selected: {row['process']} (PID {row['pid']})"),
        )
        self.table.pack(fill="both", expand=True, padx=14, pady=(2, 10))
        self._all_widgets.append(self.table)

        return page

    # --------------------------------------------------------------------------
    # Page 3: Containers & Layouts
    # --------------------------------------------------------------------------

    def _create_containers_page(self) -> tk.Frame:
        page = tk.Frame(self.content_frame)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=1)
        page.rowconfigure(0, weight=1)

        # Container 1: Vector Tabview
        card_tv = Card(page, corner_radius=12)
        card_tv.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        lbl_tv = Label(card_tv, text="Vector Tabview Navigation", icon="fa:folder-tree", font_size=12, bold=True)
        lbl_tv.pack(anchor="w", padx=14, pady=(12, 6))

        tv = Tabview(card_tv, width=340, height=280)
        tv.pack(fill="both", expand=True, padx=14, pady=(4, 14))

        tab_dash = tv.add("Dashboard")
        tab_perf = tv.add("Performance")
        tab_logs = tv.add("System Logs")

        # Tab 1 contents
        lbl_t1 = Label(tab_dash, text="Active Dashboard View", font_size=11, bold=True)
        lbl_t1.pack(padx=10, pady=8)
        pb1 = ProgressBar(tab_dash, value=0.65, width=240, height=8)
        pb1.pack(padx=10, pady=4)
        btn_t1 = Button(tab_dash, text="Sync Now", icon="fa:arrows-rotate", width=140, height=30)
        btn_t1.pack(padx=10, pady=8)

        # Tab 2 contents
        lbl_t2 = Label(tab_perf, text="Hardware Engine Metrics", font_size=11, bold=True)
        lbl_t2.pack(padx=10, pady=8)
        sw_t2 = Switch(tab_perf, text="GPU Acceleration", width=180, height=26)
        sw_t2.pack(padx=10, pady=4)

        # Tab 3 contents
        lbl_t3 = Label(tab_logs, text="Event Stream Active", font_size=11, bold=True)
        lbl_t3.pack(padx=10, pady=8)
        bdg_t3 = Badge(tab_logs, text="LOGGING ENABLED", variant="info")
        bdg_t3.pack(padx=10, pady=4)

        self._all_widgets.append(tv)

        # Container 2: ScrollableFrame
        card_sc = Card(page, corner_radius=12)
        card_sc.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        lbl_sc = Label(card_sc, text="ScrollableFrame with Vector Scrollbar", icon="fa:arrows-up-down", font_size=12, bold=True)
        lbl_sc.pack(anchor="w", padx=14, pady=(12, 6))

        scroll = ScrollableFrame(card_sc, width=340, height=280)
        scroll.pack(fill="both", expand=True, padx=14, pady=(4, 14))

        content = scroll.scrollable_frame
        for i in range(1, 13):
            row_card = Frame(content, width=300, height=38, corner_radius=6, bg_color=self.pal.card_bg)
            row_card.pack(fill="x", pady=2, padx=4)

            lbl_row = Label(row_card, text=f"Scrollable Component Item #{i:02d}", font_size=10)
            lbl_row.place(x=8, y=8)

            bdg_row = Badge(row_card, text="ONLINE" if i % 2 == 0 else "IDLE", variant="success" if i % 2 == 0 else "primary")
            bdg_row.place(x=220, y=7)

        self._all_widgets.append(scroll)
        return page

    # --------------------------------------------------------------------------
    # Page 4: Interactive Live Playground
    # --------------------------------------------------------------------------

    def _create_playground_page(self) -> tk.Frame:
        page = tk.Frame(self.content_frame)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=1)
        page.rowconfigure(0, weight=1)

        # Left Column: Parameter Sliders
        card_params = Card(page, corner_radius=12)
        card_params.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        lbl_pg = Label(card_params, text="Live Component Customizer", icon="fa:sliders", font_size=12, bold=True)
        lbl_pg.pack(anchor="w", padx=14, pady=(12, 10))

        # Corner Radius Slider
        lbl_cr = Label(card_params, text="Corner Radius:", font_size=10, bold=True)
        lbl_cr.pack(anchor="w", padx=14, pady=(4, 2))
        sl_cr = Slider(
            card_params,
            from_=0,
            to=24,
            value=10,
            width=260,
            height=28,
            command=self._on_pg_radius_changed,
        )
        sl_cr.pack(anchor="w", padx=14, pady=(0, 6))

        # Shadow Blur Slider
        lbl_sh = Label(card_params, text="Shadow Elevation Blur:", font_size=10, bold=True)
        lbl_sh.pack(anchor="w", padx=14, pady=(4, 2))
        sl_sh = Slider(
            card_params,
            from_=0,
            to=20,
            value=8,
            width=260,
            height=28,
            command=self._on_pg_shadow_changed,
        )
        sl_sh.pack(anchor="w", padx=14, pady=(0, 6))

        # Icon Selector Segmented
        lbl_ic = Label(card_params, text="Button Icon:", font_size=10, bold=True)
        lbl_ic.pack(anchor="w", padx=14, pady=(4, 2))
        seg_ic = SegmentedButton(
            card_params,
            values=["Rocket", "Gear", "Shield", "Cubes"],
            selected_index=0,
            width=260,
            height=28,
            command=self._on_pg_icon_changed,
        )
        seg_ic.pack(anchor="w", padx=14, pady=(0, 6))

        # Right Column: Live Vector Preview Canvas
        card_prev = Card(page, corner_radius=12)
        card_prev.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        lbl_pv = Label(card_prev, text="Instant Vector Rendering Preview", icon="fa:eye", font_size=12, bold=True)
        lbl_pv.pack(anchor="w", padx=14, pady=(12, 10))

        self.pg_preview_btn = Button(
            card_prev,
            text=self._pg_button_text,
            icon=self._pg_icon_name,
            width=240,
            height=46,
            corner_radius=10.0,
            shadow_blur=8.0,
            font_size=13,
            command=lambda: self._log("Playground button activated!"),
        )
        self.pg_preview_btn.pack(pady=30)

        self.lbl_code_snippet = Label(
            card_prev,
            text='Button(root, text="Deploy Vector App", icon="fa:rocket", corner_radius=10.0)',
            font_size=9,
            fg_color="#8b5cf6",
            height=24,
            align="center",
        )
        self.lbl_code_snippet.pack(fill="x", padx=14, pady=(10, 10))

        return page

    def _on_pg_radius_changed(self, val: float):
        r = float(val)
        self.pg_preview_btn.configure(corner_radius=r)
        self._update_code_snippet()

    def _on_pg_shadow_changed(self, val: float):
        sh = float(val)
        self.pg_preview_btn.configure(shadow_blur=sh)
        self._update_code_snippet()

    def _on_pg_icon_changed(self, val: str):
        mapping = {
            "Rocket": "fa:rocket",
            "Gear": "fa:gear",
            "Shield": "fa:shield-halved",
            "Cubes": "fa:cubes",
        }
        self._pg_icon_name = mapping.get(val, "fa:rocket")
        self.pg_preview_btn.configure(icon=self._pg_icon_name)
        self._update_code_snippet()

    def _update_code_snippet(self):
        r = self.pg_preview_btn._corner_radius
        sh = self.pg_preview_btn._shadow_blur
        code = f'Button(root, text="Deploy Vector App", icon="{self._pg_icon_name}", corner_radius={r:.1f}, shadow_blur={sh:.1f})'
        self.lbl_code_snippet.text = code

    # --------------------------------------------------------------------------
    # Page 5: Theme Matrix & Palette Gallery
    # --------------------------------------------------------------------------

    def _create_themes_page(self) -> tk.Frame:
        page = tk.Frame(self.content_frame)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=1)
        page.columnconfigure(2, weight=1)
        page.columnconfigure(3, weight=1)

        themes_list = [
            ("Dark Modern", "dark", "#100e14", "#8b5cf6", "#f8f9fa"),
            ("Clean Light", "light", "#f8f9fa", "#4f46e5", "#1e293b"),
            ("Deep Ocean", "ocean", "#091428", "#0284c7", "#f1f5f9"),
            ("Slate Neutral", "slate", "#0f172a", "#38bdf8", "#f8fafc"),
            ("Sunset Glow", "sunset", "#180c1e", "#f43f5e", "#fff1f2"),
            ("Forest Green", "forest", "#0a1912", "#10b981", "#ecfdf5"),
            ("Neon Cyber", "neon", "#05050d", "#a855f7", "#00ffcc"),
            ("Dracula Gothic", "dracula", "#282a36", "#bd93f9", "#f8f8f2"),
        ]

        for i, (title, name, bg_hex, pri_hex, fg_hex) in enumerate(themes_list):
            row = i // 4
            col = i % 4

            card = Card(page, height=130, corner_radius=12)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

            lbl = Label(card, text=title, font_size=11, bold=True)
            lbl.pack(anchor="w", padx=12, pady=(10, 4))

            # Color swatches row
            swatch_row = tk.Frame(card, background="")
            swatch_row.pack(fill="x", padx=12, pady=4)

            sw1 = Frame(swatch_row, width=20, height=20, corner_radius=4, bg_color=bg_hex)
            sw1.pack(side="left", padx=2)
            sw2 = Frame(swatch_row, width=20, height=20, corner_radius=4, bg_color=pri_hex)
            sw2.pack(side="left", padx=2)
            sw3 = Frame(swatch_row, width=20, height=20, corner_radius=4, bg_color=fg_hex)
            sw3.pack(side="left", padx=2)

            btn_apply = Button(
                card,
                text="Apply Theme",
                width=100,
                height=26,
                corner_radius=6,
                font_size=9,
                command=lambda t_name=name: self._change_theme(t_name),
            )
            btn_apply.pack(anchor="w", padx=12, pady=(8, 10))

        return page

    # --------------------------------------------------------------------------
    # Simulation & Interactive Update Handlers
    # --------------------------------------------------------------------------

    def _start_simulation_loop(self):
        def _sim_step():
            if not self._sim_running or not self.root.winfo_exists():
                return

            # Jitter gauge and sparkline data
            if hasattr(self, "gauge_cpu") and self.gauge_cpu.winfo_exists():
                val = 45.0 + 35.0 * math.sin(math.radians(random.uniform(0, 360)))
                self.gauge_cpu.value = val
                self.spark_cpu.push(val)

            if hasattr(self, "circ_mem") and self.circ_mem.winfo_exists():
                m_val = max(20.0, min(95.0, self.circ_mem.value + random.uniform(-3, 3)))
                self.circ_mem.value = m_val
                self.spark_mem.push(m_val)

            if hasattr(self, "spark_net") and self.spark_net.winfo_exists():
                self.spark_net.push(random.uniform(10, 65))

            self.root.after(1200, _sim_step)

        self.root.after(1000, _sim_step)

    def _log(self, msg: str):
        self.log_badge.text = msg
        self.log_badge.request_redraw()

    def _on_toggle_disabled(self):
        is_dis = self._disabled_var.get()
        for w in self._all_widgets:
            w.is_disabled = is_dis
        self._log("All widgets disabled." if is_dis else "All widgets enabled.")

    def _quick_toggle_dark_light(self):
        new_theme = "light" if self.current_theme_name == "dark" else "dark"
        self._change_theme(new_theme)

    def _change_theme(self, theme_name: str):
        self.current_theme_name = theme_name
        set_theme(theme_name)
        apply_theme(self.root, theme_name)
        self.pal = get_theme()

        # Update container backgrounds
        bg_col = self.pal.bg
        self.root.configure(bg=bg_col)
        self.container.configure(bg=bg_col)
        self.sidebar.configure(bg=bg_col)
        self.workspace.configure(bg=bg_col)
        self.header_frame.configure(bg=bg_col)
        self.content_frame.configure(bg=bg_col)
        self.sidebar_nav_frame.configure(bg=bg_col)

        for p in self.pages.values():
            p.configure(bg=bg_col)
            cascade_bg_to_children(p, bg_col, palette=self.pal)

        self._log(f"Theme: {theme_name.title()}")
        self._navigate_to(self.active_page)


def main():
    root = tk.Tk()
    app = WidgetsShowcaseApp(root)
    try:
        root.mainloop()
    finally:
        del app
        try:
            root.destroy()
        except Exception:
            pass
        import gc
        gc.collect()


if __name__ == "__main__":
    main()
