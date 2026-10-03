"""
tkblend Native Vector Widgets Showcase & Interactive Dashboard
Comprehensive demonstration of pure Blend2D vector UI controls powered by NativeController.
Zero TTK dependencies, zero PhotoImage allocations.
"""

from __future__ import annotations

import math
import random
import tkinter as tk
from typing import List, Optional, Tuple

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
    RadioButton,
    Card,
    Label,
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
)


# ==============================================================================
# Custom Blend2D Pure Vector Widgets for Dashboard
# ==============================================================================

class RadialGauge(BaseControl):
    """
    Modern circular radial meter / activity gauge rendered natively with Blend2D.
    Supports animated sweep angles, track gradients, and center metric typography.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        size: int = 150,
        value: float = 65.0,
        min_value: float = 0.0,
        max_value: float = 100.0,
        title: str = "CPU Load",
        unit: str = "%",
        color: Optional[ColorLike] = None,
        track_color: Optional[ColorLike] = None,
        thickness: float = 11.0,
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
        r = min(cx, cy) - thick - (6.0 * s)
        if r <= 2.0:
            return

        # Gauge angles (from 135 deg to 405 deg = 270 deg span)
        start_angle_deg = 135.0
        total_span_deg = 270.0
        start_rad = math.radians(start_angle_deg)
        total_span_rad = math.radians(total_span_deg)

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
        sub_fg = pal.text_muted if hasattr(pal, "text_muted") else "#888888"

        surf.draw_text(
            val_text,
            cx,
            cy - (2.0 * s),
            font_size=17.0 * s,
            color=fg_col,
            bold=True,
            align="center",
        )
        surf.draw_text(
            self._title,
            cx,
            cy + (15.0 * s),
            font_size=10.0 * s,
            color=sub_fg,
            bold=False,
            align="center",
        )


class SparklineChart(BaseControl):
    """
    Real-time vector sparkline/waveform chart powered by Blend2D.
    Features smooth antialiased Bézier curves and vertical area gradient fill.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 340,
        height: int = 140,
        max_points: int = 32,
        line_color: Optional[ColorLike] = None,
        title: str = "Throughput Stream (MB/s)",
        **kwargs,
    ):
        self._max_points = max_points
        self._custom_color = line_color
        self._title = title
        # Initial sinusoidal / random wave
        self._data: List[float] = [
            25.0 + 15.0 * math.sin(i * 0.4) + random.uniform(-3, 3)
            for i in range(max_points)
        ]
        super().__init__(master=master, width=width, height=height, takefocus=False, **kwargs)

    def push_value(self, val: float) -> None:
        self._data.append(float(val))
        if len(self._data) > self._max_points:
            self._data.pop(0)
        self.request_redraw()

    def render(self, surf: Surface, pal: Palette, width: int, height: int, scale: float) -> None:
        s = scale
        w = float(width)
        h = float(height)

        pad_x = 16.0 * s
        pad_top = 34.0 * s
        pad_bot = 16.0 * s

        chart_w = w - 2 * pad_x
        chart_h = h - pad_top - pad_bot
        if chart_w <= 10 or chart_h <= 10 or len(self._data) < 2:
            return

        # Header info
        title_col = pal.fg
        accent_col = resolve_color_failsafe(self._custom_color or pal.primary, palette=pal)
        cur_val = self._data[-1] if self._data else 0.0

        surf.draw_text(
            self._title,
            pad_x,
            18.0 * s,
            font_size=11.5 * s,
            color=title_col,
            bold=True,
            align="left",
        )
        surf.draw_text(
            f"{cur_val:.1f} MB/s",
            w - pad_x,
            18.0 * s,
            font_size=11.5 * s,
            color=accent_col,
            bold=True,
            align="right",
        )

        # Subtle grid horizontal lines
        grid_col = resolve_color_failsafe(pal.card_border, palette=pal, alpha=0.35)
        for i in range(3):
            gy = pad_top + (chart_h * (i + 1) / 3.0)
            surf.draw_line(pad_x, gy, w - pad_x, gy, stroke=grid_col, stroke_width=1.0 * s)

        # Compute point coordinates
        min_v = min(self._data)
        max_v = max(self._data)
        rng = max(1.0, max_v - min_v)
        n = len(self._data)
        step_x = chart_w / (n - 1)

        pts: List[Tuple[float, float]] = []
        for i, val in enumerate(self._data):
            px = pad_x + i * step_x
            norm = (val - min_v) / rng
            py = pad_top + chart_h - (norm * (chart_h - 10.0 * s)) - 5.0 * s
            pts.append((px, py))

        # Build Bézier smooth curve path & Area path
        line_path = Path()
        line_path.move_to(pts[0][0], pts[0][1])

        area_path = Path()
        area_path.move_to(pts[0][0], pad_top + chart_h)
        area_path.line_to(pts[0][0], pts[0][1])

        for i in range(len(pts) - 1):
            p0 = pts[i]
            p1 = pts[i + 1]
            cx1 = p0[0] + (p1[0] - p0[0]) * 0.5
            cy1 = p0[1]
            cx2 = p0[0] + (p1[0] - p0[0]) * 0.5
            cy2 = p1[1]
            line_path.cubic_to(cx1, cy1, cx2, cy2, p1[0], p1[1])
            area_path.cubic_to(cx1, cy1, cx2, cy2, p1[0], p1[1])

        area_path.line_to(pts[-1][0], pad_top + chart_h)
        area_path.close()

        # Fill area gradient
        grad = LinearGradient(0, pad_top, 0, pad_top + chart_h)
        grad.add_stop(0.0, accent_col, alpha=0.35)
        grad.add_stop(1.0, accent_col, alpha=0.01)
        surf.fill_path(area_path, grad)

        # Stroke curve line
        surf.stroke_path(line_path, accent_col, stroke_width=2.4 * s)

        # Glowing dot on latest point
        lx, ly = pts[-1]
        surf.fill_circle(lx, ly, 4.5 * s, accent_col)
        surf.stroke_circle(lx, ly, 6.5 * s, "#ffffff", stroke_width=1.5 * s)


# ==============================================================================
# Main Application Dashboard
# ==============================================================================

class WidgetsShowcaseApp:
    """
    Comprehensive Modern Vector UI Showcase Application.
    Designed with a responsive multi-page dashboard layout.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend UI — Native Vector UI Showcase")
        self.root.geometry("1180x820")
        self.root.minsize(960, 680)

        # Theme & State
        self.current_theme_name = "dark"
        self.active_page = "controls"
        self._all_widgets = []
        self._disabled_var = tk.BooleanVar(value=False)
        self._sim_running = True

        # Interactive state vars
        self._wifi_var = tk.BooleanVar(value=True)
        self._bluetooth_var = tk.BooleanVar(value=False)
        self._notifications_var = tk.BooleanVar(value=True)
        self._agree_var = tk.BooleanVar(value=True)

        self._slider_val_var = tk.DoubleVar(value=68.0)
        self._slider_step_var = tk.DoubleVar(value=3.0)
        self._progress_val_var = tk.DoubleVar(value=0.72)
        self._radio_var = tk.StringVar(value="turbo")

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
        self.pages = {}
        self.nav_buttons = {}

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
        self.header_frame = tk.Frame(self.workspace, height=56)
        self.header_frame.pack(fill="x", pady=(0, 10))

        self.lbl_page_title = Label(
            self.header_frame,
            text="Core Controls & Widgets",
            icon="fa:sliders",
            font_size=17,
            bold=True,
            width=320,
            height=34,
        )
        self.lbl_page_title.pack(side="left")

        # Status & Click Log Banner
        self.log_badge = Label(
            self.header_frame,
            text="System Ready",
            icon="fa:circle-check",
            bg_color=self.pal.card_bg,
            fg_color="#34d399",
            corner_radius=8,
            width=220,
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
        self.pages["gauges"] = self._create_gauges_page()
        self.pages["playground"] = self._create_playground_page()
        self.pages["themes"] = self._create_themes_page()

    def _build_sidebar(self):
        # Brand Card / Header
        brand_card = Card(self.sidebar, height=72, corner_radius=12)
        brand_card.pack(fill="x", pady=(0, 14))

        brand_lbl = Label(
            brand_card,
            text="tkblend UI",
            icon="fa:cubes",
            font_size=15,
            bold=True,
            width=180,
            height=30,
        )
        brand_lbl.pack(anchor="w", padx=14, pady=(12, 2))

        sub_lbl = Label(
            brand_card,
            text="Blend2D Native Engine",
            font_size=10,
            fg_color="#8b5cf6",
            width=180,
            height=18,
        )
        sub_lbl.pack(anchor="w", padx=16, pady=(0, 10))

        # Nav Buttons Section
        nav_items = [
            ("controls", "Controls & Widgets", "fa:sliders"),
            ("gauges", "Gauges & Charts", "fa:chart-line"),
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
                height=40,
                corner_radius=10,
                font_size=11,
                command=lambda pid=page_id: self._navigate_to(pid),
            )
            btn.pack(fill="x", pady=4)
            self.nav_buttons[page_id] = btn

        # Spacer
        spacer = tk.Frame(self.sidebar)
        spacer.pack(fill="both", expand=True)

        # Bottom Controls Card
        bot_card = Card(self.sidebar, height=130, corner_radius=12)
        bot_card.pack(fill="x", pady=(10, 0))

        lbl_bot = Label(bot_card, text="Global Settings", font_size=11, bold=True, width=170, height=22)
        lbl_bot.pack(anchor="w", padx=14, pady=(12, 4))

        dis_sw = Switch(
            bot_card,
            text="Disable All",
            variable=self._disabled_var,
            command=self._on_toggle_disabled,
            width=170,
            height=28,
        )
        dis_sw.pack(anchor="w", padx=14, pady=3)

        btn_toggle_theme = Button(
            bot_card,
            text="Dark / Light Toggle",
            icon="fa:circle-half-stroke",
            width=174,
            height=30,
            corner_radius=8,
            font_size=10,
            command=self._quick_toggle_dark_light,
        )
        btn_toggle_theme.pack(padx=14, pady=(6, 12))

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
            "controls": ("Core Controls & Widgets", "fa:sliders"),
            "gauges": ("Vector Visualizations & Gauges", "fa:chart-line"),
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
    # Page 1: Core Controls & Widgets Grid
    # --------------------------------------------------------------------------

    def _create_controls_page(self) -> tk.Frame:
        page = tk.Frame(self.content_frame)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=1)
        page.columnconfigure(2, weight=1)
        page.rowconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)

        # Card 1: Buttons
        c1 = Card(page, corner_radius=12)
        c1.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        self._build_buttons_section(c1)

        # Card 2: Selectors & Toggles
        c2 = Card(page, corner_radius=12)
        c2.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
        self._build_selectors_section(c2)

        # Card 3: Sliders
        c3 = Card(page, corner_radius=12)
        c3.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")
        self._build_sliders_section(c3)

        # Card 4: Progress Activity
        c4 = Card(page, corner_radius=12)
        c4.grid(row=1, column=0, columnspan=2, padx=6, pady=6, sticky="nsew")
        self._build_progress_section(c4)

        # Card 5: Badges & Elevation Tags
        c5 = Card(page, corner_radius=12)
        c5.grid(row=1, column=2, padx=6, pady=6, sticky="nsew")
        self._build_badges_section(c5)

        return page

    def _build_buttons_section(self, parent: Card):
        header = Label(parent, text="Buttons & Elevation", icon="fa:hand-pointer", font_size=13, bold=True, width=190, height=26)
        header.pack(anchor="w", padx=16, pady=(14, 8))

        b1 = Button(
            parent,
            text="Primary Rocket",
            icon="fa:rocket",
            width=190,
            height=36,
            corner_radius=8,
            command=lambda: self._log("Primary Action Clicked!"),
        )
        b1.pack(padx=16, pady=4)
        self._all_widgets.append(b1)

        b2 = Button(
            parent,
            text="Secondary Settings",
            icon="fa:gear",
            bg_color=self.pal.secondary,
            hover_color=self.pal.secondary_hover,
            pressed_color=self.pal.secondary_active,
            fg_color=self.pal.secondary_fg,
            width=190,
            height=34,
            corner_radius=8,
            command=lambda: self._log("Settings Clicked!"),
        )
        b2.pack(padx=16, pady=4)
        self._all_widgets.append(b2)

        b3 = Button(
            parent,
            text="Success Save",
            icon="fa:check",
            bg_color="#10b981",
            hover_color="#059669",
            pressed_color="#047857",
            fg_color="#ffffff",
            width=190,
            height=34,
            corner_radius=8,
            command=lambda: self._log("Save Success!"),
        )
        b3.pack(padx=16, pady=4)
        self._all_widgets.append(b3)

        b4 = Button(
            parent,
            text="Delete Item",
            icon="fa:trash",
            bg_color="#ef4444",
            hover_color="#dc2626",
            pressed_color="#b91c1c",
            fg_color="#ffffff",
            width=190,
            height=34,
            corner_radius=8,
            command=lambda: self._log("Delete Item Clicked!"),
        )
        b4.pack(padx=16, pady=4)
        self._all_widgets.append(b4)

    def _build_selectors_section(self, parent: Card):
        header = Label(parent, text="Toggles & Selectors", icon="fa:toggle-on", font_size=13, bold=True, width=190, height=26)
        header.pack(anchor="w", padx=16, pady=(14, 8))

        sw1 = Switch(parent, text="Wi-Fi Connection", variable=self._wifi_var, width=180, height=26)
        sw1.pack(anchor="w", padx=16, pady=3)
        self._all_widgets.append(sw1)

        sw2 = Switch(parent, text="Bluetooth Sync", variable=self._bluetooth_var, width=180, height=26)
        sw2.pack(anchor="w", padx=16, pady=3)
        self._all_widgets.append(sw2)

        cb1 = CheckBox(parent, text="Hardware Accel", variable=self._agree_var, width=180, height=26)
        cb1.pack(anchor="w", padx=16, pady=3)
        self._all_widgets.append(cb1)

        lbl_mode = Label(parent, text="Engine Profile:", font_size=11, bold=True, width=140, height=20)
        lbl_mode.pack(anchor="w", padx=16, pady=(8, 2))

        r1 = RadioButton(parent, text="Eco Saver", value="eco", variable=self._radio_var, width=140, height=22)
        r1.pack(anchor="w", padx=18, pady=1)
        self._all_widgets.append(r1)

        r2 = RadioButton(parent, text="Turbo Blend2D", value="turbo", variable=self._radio_var, width=140, height=22)
        r2.pack(anchor="w", padx=18, pady=1)
        self._all_widgets.append(r2)

    def _build_sliders_section(self, parent: Card):
        header = Label(parent, text="Sliders & Controls", icon="fa:sliders", font_size=13, bold=True, width=190, height=26)
        header.pack(anchor="w", padx=16, pady=(14, 8))

        lbl_v = Label(parent, text=f"Volume: {int(self._slider_val_var.get())}%", font_size=11, width=180, height=20)
        lbl_v.pack(anchor="w", padx=16, pady=(2, 0))

        def _on_vol_change(val):
            lbl_v.text = f"Volume: {int(val)}%"

        sl1 = Slider(
            parent,
            from_=0.0,
            to=100.0,
            variable=self._slider_val_var,
            command=_on_vol_change,
            width=200,
            height=24,
            track_thickness=5.0,
            thumb_radius=8.0,
        )
        sl1.pack(padx=16, pady=(2, 10))
        self._all_widgets.append(sl1)

        lbl_step = Label(parent, text=f"Step Tier: {int(self._slider_step_var.get())} / 5", font_size=11, width=180, height=20)
        lbl_step.pack(anchor="w", padx=16, pady=(2, 0))

        def _on_step_change(val):
            lbl_step.text = f"Step Tier: {int(val)} / 5"

        sl2 = Slider(
            parent,
            from_=1.0,
            to=5.0,
            number_of_steps=4,
            variable=self._slider_step_var,
            command=_on_step_change,
            width=200,
            height=24,
            active_color="#8b5cf6",
            thumb_color="#8b5cf6",
        )
        sl2.pack(padx=16, pady=(2, 10))
        self._all_widgets.append(sl2)

    def _build_progress_section(self, parent: Card):
        header = Label(parent, text="Progress & Background Workers", icon="fa:chart-line", font_size=13, bold=True, width=240, height=26)
        header.pack(anchor="w", padx=16, pady=(14, 8))

        # Determinate Row
        row1 = tk.Frame(parent)
        row1.pack(fill="x", padx=16, pady=2)

        lbl_p = Label(row1, text=f"Task Progress ({int(self._progress_val_var.get() * 100)}%)", width=180, height=22)
        lbl_p.pack(side="left")

        def _add_p(delta):
            v = max(0.0, min(1.0, self._progress_val_var.get() + delta))
            self._progress_val_var.set(v)
            lbl_p.text = f"Task Progress ({int(v * 100)}%)"

        b_plus = Button(row1, text="+10%", width=56, height=24, corner_radius=6, command=lambda: _add_p(0.1))
        b_plus.pack(side="right", padx=2)
        b_minus = Button(row1, text="-10%", width=56, height=24, corner_radius=6, command=lambda: _add_p(-0.1))
        b_minus.pack(side="right", padx=2)
        self._all_widgets.extend([b_plus, b_minus])

        self.pb_det = ProgressBar(
            parent,
            mode="determinate",
            variable=self._progress_val_var,
            width=440,
            height=9,
            corner_radius=4,
        )
        self.pb_det.pack(fill="x", padx=16, pady=(4, 10))
        self._all_widgets.append(self.pb_det)

        # Indeterminate Row
        row2 = tk.Frame(parent)
        row2.pack(fill="x", padx=16, pady=2)

        lbl_ind = Label(row2, text="Indeterminate Marquee Pulse", width=220, height=22)
        lbl_ind.pack(side="left")

        self.pb_ind = ProgressBar(
            parent,
            mode="indeterminate",
            width=440,
            height=8,
            corner_radius=4,
            progress_color="#06b6d4",
        )
        self.pb_ind.pack(fill="x", padx=16, pady=(4, 10))
        self.pb_ind.start()
        self._all_widgets.append(self.pb_ind)

    def _build_badges_section(self, parent: Card):
        header = Label(parent, text="Status & Indicators", icon="fa:shield-halved", font_size=13, bold=True, width=190, height=26)
        header.pack(anchor="w", padx=16, pady=(14, 8))

        b_ok = Label(parent, text="Active & Synced", icon="fa:circle-check", bg_color="#065f46", fg_color="#34d399", corner_radius=6, width=150, height=26, align="center")
        b_ok.pack(padx=16, pady=3)

        b_warn = Label(parent, text="Update Available", icon="fa:triangle-exclamation", bg_color="#78350f", fg_color="#fbbf24", corner_radius=6, width=150, height=26, align="center")
        b_warn.pack(padx=16, pady=3)

        b_info = Label(parent, text="Blend2D Zero-Copy", icon="fa:bolt", bg_color="#1e3a8a", fg_color="#93c5fd", corner_radius=6, width=150, height=26, align="center")
        b_info.pack(padx=16, pady=3)

    # --------------------------------------------------------------------------
    # Page 2: Blend2D Vector Gauges & Real-Time Charts
    # --------------------------------------------------------------------------

    def _create_gauges_page(self) -> tk.Frame:
        page = tk.Frame(self.content_frame)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=1)
        page.columnconfigure(2, weight=1)
        page.rowconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)

        # 3 Radial Gauges (CPU, RAM, GPU)
        c_cpu = Card(page, corner_radius=12)
        c_cpu.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        self.gauge_cpu = RadialGauge(c_cpu, size=150, value=74.0, title="CPU Core", unit="%", color="#ef4444")
        self.gauge_cpu.pack(expand=True, pady=16)

        c_ram = Card(page, corner_radius=12)
        c_ram.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
        self.gauge_ram = RadialGauge(c_ram, size=150, value=58.0, title="Memory", unit="%", color="#3b82f6")
        self.gauge_ram.pack(expand=True, pady=16)

        c_gpu = Card(page, corner_radius=12)
        c_gpu.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")
        self.gauge_gpu = RadialGauge(c_gpu, size=150, value=88.0, title="GPU VRAM", unit="%", color="#10b981")
        self.gauge_gpu.pack(expand=True, pady=16)

        # Real-Time Sparkline Chart Card (Span 2 cols)
        c_chart = Card(page, corner_radius=12)
        c_chart.grid(row=1, column=0, columnspan=2, padx=6, pady=6, sticky="nsew")
        self.sparkline = SparklineChart(c_chart, height=180, title="Network Bandwidth Stream (MB/s)", line_color="#8b5cf6")
        self.sparkline.pack(fill="both", expand=True, padx=14, pady=14)

        # Simulation & Tuning Controls Card
        c_sim = Card(page, corner_radius=12)
        c_sim.grid(row=1, column=2, padx=6, pady=6, sticky="nsew")

        lbl_sim = Label(c_sim, text="Live Telemetry", icon="fa:wave-square", font_size=13, bold=True, width=190, height=26)
        lbl_sim.pack(anchor="w", padx=16, pady=(14, 8))

        self.sw_sim = Switch(c_sim, text="Live 60fps Stream", variable=tk.BooleanVar(value=True), command=self._toggle_sim, width=170, height=28)
        self.sw_sim.pack(anchor="w", padx=16, pady=4)

        btn_spike = Button(c_sim, text="Trigger Load Spike", icon="fa:bolt", width=170, height=34, corner_radius=8, command=self._trigger_spike)
        btn_spike.pack(padx=16, pady=8)

        btn_reset = Button(c_sim, text="Normalize Meters", icon="fa:rotate-right", width=170, height=34, corner_radius=8, command=self._normalize_gauges)
        btn_reset.pack(padx=16, pady=4)

        return page

    def _toggle_sim(self):
        self._sim_running = not self._sim_running
        self._log("Simulation stream toggled.")

    def _trigger_spike(self):
        self.gauge_cpu.value = min(100.0, self.gauge_cpu.value + 25.0)
        self.gauge_gpu.value = min(100.0, self.gauge_gpu.value + 15.0)
        self.sparkline.push_value(95.0 + random.uniform(-5, 5))
        self._log("Load spike triggered!")

    def _normalize_gauges(self):
        self.gauge_cpu.value = 45.0
        self.gauge_ram.value = 50.0
        self.gauge_gpu.value = 60.0
        self._log("Telemetry normalized.")

    # --------------------------------------------------------------------------
    # Page 3: Live Interactive Widget Playground & Inspector
    # --------------------------------------------------------------------------

    def _create_playground_page(self) -> tk.Frame:
        page = tk.Frame(self.content_frame)
        page.columnconfigure(0, weight=3)
        page.columnconfigure(1, weight=2)
        page.rowconfigure(0, weight=1)

        # Left Stage: Live Preview Canvas Card
        stage_card = Card(page, corner_radius=14)
        stage_card.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        lbl_stage = Label(stage_card, text="Interactive Canvas Preview", icon="fa:eye", font_size=14, bold=True, width=240, height=28)
        lbl_stage.pack(anchor="w", padx=18, pady=(16, 12))

        # Preview Container in center
        self.preview_box = tk.Frame(stage_card)
        self.preview_box.pack(fill="both", expand=True, padx=20, pady=20)

        self.pg_preview_btn = Button(
            self.preview_box,
            text=self._pg_button_text,
            icon=self._pg_icon_name,
            width=220,
            height=46,
            corner_radius=self._pg_radius_var.get(),
            font_size=13,
            bold=True,
            command=lambda: self._log("Playground Button Clicked!"),
        )
        self.pg_preview_btn.place(relx=0.5, rely=0.4, anchor="center")

        # Live Code Snippet Display
        self.lbl_code_snippet = Label(
            stage_card,
            text='tb.Button(root, text="Deploy Vector App", corner_radius=10)',
            font="monospace",
            font_size=10,
            bg_color=resolve_color_failsafe(self.pal.bg, palette=self.pal),
            fg_color="#38bdf8",
            corner_radius=8,
            width=460,
            height=36,
            align="center",
        )
        self.lbl_code_snippet.pack(fill="x", padx=18, pady=(0, 16))

        # Right Stage: Inspector Controls
        inspector_card = Card(page, corner_radius=14)
        inspector_card.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        lbl_insp = Label(inspector_card, text="Widget Inspector", icon="fa:sliders", font_size=14, bold=True, width=190, height=28)
        lbl_insp.pack(anchor="w", padx=16, pady=(16, 12))

        # Corner Radius
        lbl_cr = Label(inspector_card, text=f"Corner Radius: {int(self._pg_radius_var.get())}px", font_size=11, width=190, height=20)
        lbl_cr.pack(anchor="w", padx=16, pady=(4, 0))

        def _on_radius_change(val):
            lbl_cr.text = f"Corner Radius: {int(val)}px"
            self.pg_preview_btn.configure(corner_radius=float(val))
            self._update_snippet()

        sl_cr = Slider(
            inspector_card,
            from_=0.0,
            to=24.0,
            variable=self._pg_radius_var,
            command=_on_radius_change,
            width=220,
            height=24,
        )
        sl_cr.pack(padx=16, pady=(2, 10))

        # Icon Switcher Row
        lbl_icons = Label(inspector_card, text="Icon Preset:", font_size=11, bold=True, width=180, height=20)
        lbl_icons.pack(anchor="w", padx=16, pady=(4, 2))

        icons_row = tk.Frame(inspector_card)
        icons_row.pack(fill="x", padx=16, pady=2)

        test_icons = [("Rocket", "fa:rocket"), ("Bolt", "fa:bolt"), ("Heart", "fa:heart"), ("Shield", "fa:shield-halved")]
        for label_ic, icon_val in test_icons:
            b_ic = Button(
                icons_row,
                text="",
                icon=icon_val,
                width=46,
                height=32,
                corner_radius=6,
                command=lambda ic=icon_val: self._set_pg_icon(ic),
            )
            b_ic.pack(side="left", padx=3)

        # Color Accent Preset
        lbl_colors = Label(inspector_card, text="Accent Color:", font_size=11, bold=True, width=180, height=20)
        lbl_colors.pack(anchor="w", padx=16, pady=(10, 2))

        color_row = tk.Frame(inspector_card)
        color_row.pack(fill="x", padx=16, pady=2)

        test_colors = [("#3b82f6", "Blue"), ("#10b981", "Green"), ("#8b5cf6", "Purple"), ("#ef4444", "Red")]
        for col_hex, _ in test_colors:
            b_c = Button(
                color_row,
                text="",
                bg_color=col_hex,
                hover_color=col_hex,
                width=46,
                height=26,
                corner_radius=6,
                command=lambda c=col_hex: self._set_pg_color(c),
            )
            b_c.pack(side="left", padx=3)

        # State Toggle
        self.pg_dis_var = tk.BooleanVar(value=False)
        sw_pg_dis = Switch(
            inspector_card,
            text="Disabled State",
            variable=self.pg_dis_var,
            command=self._on_pg_disabled,
            width=180,
            height=28,
        )
        sw_pg_dis.pack(anchor="w", padx=16, pady=(16, 4))

        return page

    def _set_pg_icon(self, icon_name: str):
        self._pg_icon_name = icon_name
        self.pg_preview_btn.configure(icon=icon_name)
        self._update_snippet()
        self._log(f"Playground icon set to {icon_name}")

    def _set_pg_color(self, color_hex: str):
        self.pg_preview_btn.configure(bg_color=color_hex, hover_color=color_hex)
        self._update_snippet()
        self._log(f"Playground color set to {color_hex}")

    def _on_pg_disabled(self):
        self.pg_preview_btn.is_disabled = self.pg_dis_var.get()
        self._update_snippet()

    def _update_snippet(self):
        r = int(self._pg_radius_var.get())
        ic = self._pg_icon_name
        dis = self.pg_dis_var.get()
        dis_str = ", state='disabled'" if dis else ""
        self.lbl_code_snippet.text = f'tb.Button(root, text="Deploy Vector App", icon="{ic}", corner_radius={r}{dis_str})'

    # --------------------------------------------------------------------------
    # Page 4: Theme Matrix & Palette Gallery
    # --------------------------------------------------------------------------

    def _create_themes_page(self) -> tk.Frame:
        page = tk.Frame(self.content_frame)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=1)
        page.columnconfigure(2, weight=1)

        themes_list = [
            ("Dark (Default)", "dark", "#121118", "#7c3aed", "#ffffff"),
            ("Light", "light", "#f8fafc", "#2563eb", "#0f172a"),
            ("Dracula", "dracula", "#282a36", "#bd93f9", "#f8f8f2"),
            ("Nord", "nord", "#2e3440", "#88c0d0", "#eceff4"),
            ("Tokyo Night", "tokyo_night", "#1a1b26", "#7aa2f7", "#c0caf5"),
            ("Catppuccin Mocha", "catppuccin_mocha", "#1e1e2e", "#cba6f7", "#cdd6f4"),
            ("Cyberpunk", "cyberpunk", "#0d0221", "#ff007f", "#00f0ff"),
        ]

        for i, (title, name, bg_hex, pri_hex, fg_hex) in enumerate(themes_list):
            row = i // 3
            col = i % 3

            c = Card(page, corner_radius=12)
            c.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            lbl_t = Label(c, text=title, font_size=13, bold=True, width=190, height=24)
            lbl_t.pack(anchor="w", padx=14, pady=(12, 4))

            # Swatch preview
            swatch_frame = tk.Frame(c, height=48, bg=bg_hex)
            swatch_frame.pack(fill="x", padx=14, pady=4)
            swatch_frame.pack_propagate(False)

            dot1 = tk.Frame(swatch_frame, width=20, height=20, bg=pri_hex)
            dot1.pack(side="left", padx=(10, 4), pady=14)

            dot2 = tk.Frame(swatch_frame, width=20, height=20, bg=fg_hex)
            dot2.pack(side="left", padx=4, pady=14)

            btn_apply = Button(
                c,
                text="Apply Theme",
                icon="fa:check",
                width=170,
                height=30,
                corner_radius=6,
                font_size=10,
                command=lambda t_name=name: self._change_theme(t_name),
            )
            btn_apply.pack(padx=14, pady=(8, 12))

        return page

    # --------------------------------------------------------------------------
    # Telemetry Simulation & Event Handlers
    # --------------------------------------------------------------------------

    def _start_simulation_loop(self):
        def _tick():
            if self._sim_running:
                # Update gauges smoothly
                if hasattr(self, "gauge_cpu"):
                    delta_cpu = random.uniform(-2.5, 2.5)
                    self.gauge_cpu.value = max(10.0, min(95.0, self.gauge_cpu.value + delta_cpu))

                if hasattr(self, "gauge_ram"):
                    delta_ram = random.uniform(-0.8, 0.8)
                    self.gauge_ram.value = max(20.0, min(85.0, self.gauge_ram.value + delta_ram))

                # Update sparkline
                if hasattr(self, "sparkline"):
                    new_val = max(5.0, min(99.0, self.sparkline._data[-1] + random.uniform(-6, 6)))
                    self.sparkline.push_value(new_val)

            # Schedule next frame (~30-60 fps cadence)
            self.root.after(100, _tick)

        self.root.after(100, _tick)

    def _log(self, msg: str):
        self.log_badge.text = msg

    def _on_toggle_disabled(self):
        is_dis = self._disabled_var.get()
        for w in self._all_widgets:
            w.is_disabled = is_dis
        self._log("Disabled state toggled." if is_dis else "Widgets enabled.")

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

        if hasattr(self, "preview_box"):
            self.preview_box.configure(bg=self.pal.card_bg)
            if hasattr(self, "lbl_code_snippet"):
                self.lbl_code_snippet.configure(bg_color=self.pal.bg)

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
