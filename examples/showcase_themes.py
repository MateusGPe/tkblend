"""
tkblend Theme Studio & Custom Theme Gallery Showcase.

An interactive showcase demonstrating tkblend's pure Blend2D vector theme architecture:
- 12+ Curated Theme Presets (Dracula, Nord, Tokyo Night, Catppuccin, Cyberpunk, etc.)
- Visual Theme Card Selector with live color swatches
- Interactive 3-Tab Experience:
    1. 🎨 Theme Gallery & Widget Playground (all 15+ modern vector widgets)
    2. ✨ 60 FPS Live Vector Canvas (fluid waves, glassmorphism, glowing orbs)
    3. 🛠️ Theme Studio & Code Exporter (live palette tweaking & 1-click Python/JSON export)
- High-DPI ScalingTracker support with zero TTK dependencies.
"""

from __future__ import annotations
import json
import math
import sys
import time
import tkinter as tk
from typing import Optional, Callable, Union, List, Tuple, Dict, Any

from tkblend import (
    Surface,
    BlendCanvas,
    LinearGradient,
    RadialGradient,
    Path,
    ColorLike,
    parse_color,
    Palette,
    THEME_PRESETS,
    get_theme,
    set_theme,
    get_available_themes,
    apply_theme,
)

from tkblend.widgets import (
    ScalingTracker,
    ModernWidget,
    ModernFrame,
    ModernCard,
    ModernButton,
    ModernProgressBar,
    ModernCircularProgress,
    ModernSlider,
    ModernRangeSlider,
    ModernSwitch,
    ModernCheckbox,
    ModernRadio,
    ModernRadioGroup,
    ModernSegmentedControl,
    ModernTextInput,
    ModernSpinBox,
    ModernBadge,
    ModernAvatar,
    ModernAccordion,
    ModernDropdown,
)


THEME_DISPLAY_NAMES = {
    "dark": "Material Dark",
    "light": "Material Light",
    "dracula": "Dracula",
    "nord": "Nord Frost",
    "tokyo_night": "Tokyo Night",
    "catppuccin_mocha": "Catppuccin Mocha",
    "catppuccin_latte": "Catppuccin Latte",
    "cyberpunk": "Cyberpunk Neon",
    "emerald_forest": "Emerald Forest",
    "sunset_amber": "Sunset Amber",
    "monokai_pro": "Monokai Pro",
    "solarized_dark": "Solarized Dark",
    "solarized_light": "Solarized Light",
}


class ThemeCardWidget(ModernWidget):
    """
    A clickable visual card that represents a theme preset,
    displaying theme name, dark/light pill, and 6 color swatches.
    """
    def __init__(
        self,
        master: Any,
        preset_key: str,
        palette: Palette,
        on_select: Callable[[str], None],
        width: int = 240,
        height: int = 76,
        **kwargs: Any,
    ):
        self.preset_key = preset_key
        self.preset_palette = palette
        self.on_select = on_select
        self._is_active = False
        self._is_hovered = False
        super().__init__(master, width=width, height=height, **kwargs)

        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")
        self.bind("<Button-1>", self._on_click, add="+")

    def set_active(self, active: bool):
        if self._is_active != active:
            self._is_active = active
            self.render()

    def _on_enter(self, event):
        self._is_hovered = True
        self.config(cursor="hand2")
        self.render()

    def _on_leave(self, event):
        self._is_hovered = False
        self.config(cursor="")
        self.render()

    def _on_click(self, event):
        if self.on_select:
            self.on_select(self.preset_key)

    def render(self) -> None:
        s = self._scale
        active_theme = get_theme()
        p = self.preset_palette
        surf = self._surface
        w = float(self._widget_w)
        h = float(self._widget_h)

        surf.clear(self._parent_bg)

        pad_x = 4.0 * s
        pad_y = 3.0 * s
        card_w = w - pad_x * 2
        card_h = h - pad_y * 2
        rx = 10.0 * s

        # Container styling
        if self._is_active:
            border_col = active_theme.primary
            border_w = 2.0 * s
            bg_col = active_theme.card_bg
            shadow_blur = 10.0 * s
            shadow_col = f"{active_theme.primary[:7]}55"
        elif self._is_hovered:
            border_col = active_theme.primary_hover
            border_w = 1.2 * s
            bg_col = active_theme.surface
            shadow_blur = 6.0 * s
            shadow_col = active_theme.shadow_color
        else:
            border_col = active_theme.card_border
            border_w = 1.0 * s
            bg_col = active_theme.card_bg
            shadow_blur = 3.0 * s
            shadow_col = active_theme.shadow_color

        surf.draw_card(
            pad_x, pad_y, card_w, card_h,
            rx=rx, ry=rx,
            bg_color=bg_col,
            border_color=border_col,
            border_width=border_w,
            shadow_blur=shadow_blur,
            shadow_color=shadow_col,
            shadow_offset_y=2.0 * s,
        )

        # Theme Name
        title = THEME_DISPLAY_NAMES.get(self.preset_key, self.preset_key.replace("_", " ").title())
        title_font_size = 12.0 * s
        surf.draw_text(
            title,
            pad_x + 12.0 * s,
            pad_y + 18.0 * s,
            font_size=title_font_size,
            color=active_theme.fg,
            weight="bold" if self._is_active else "normal",
        )

        # Mode Badge (Dark / Light)
        mode_text = "DARK" if p.dark_mode else "LIGHT"
        mode_bg = f"{active_theme.primary[:7]}22" if self._is_active else active_theme.surface_border
        mode_fg = active_theme.primary if self._is_active else active_theme.text_muted
        badge_w = 42.0 * s
        badge_h = 16.0 * s
        badge_x = card_w + pad_x - badge_w - 10.0 * s
        badge_y = pad_y + 8.0 * s
        surf.fill_rounded_rect(badge_x, badge_y, badge_w, badge_h, 8.0 * s, 8.0 * s, mode_bg)
        surf.draw_text(
            mode_text,
            badge_x + badge_w / 2.0,
            badge_y + badge_h / 2.0 + 3.0 * s,
            font_size=8.5 * s,
            color=mode_fg,
            align="center",
            weight="bold",
        )

        # Color Swatches row
        swatches = [
            p.primary,
            p.accent,
            p.surface,
            p.bg,
            p.success,
            p.destructive,
        ]
        swatch_count = len(swatches)
        swatch_w = (card_w - 24.0 * s - (swatch_count - 1) * 4.0 * s) / swatch_count
        swatch_h = 16.0 * s
        swatch_y = pad_y + card_h - swatch_h - 10.0 * s

        for i, col in enumerate(swatches):
            sw_x = pad_x + 12.0 * s + i * (swatch_w + 4.0 * s)
            surf.fill_rounded_rect(sw_x, swatch_y, swatch_w, swatch_h, 3.5 * s, 3.5 * s, col)
            surf.stroke_rounded_rect(sw_x, swatch_y, swatch_w, swatch_h, 3.5 * s, 3.5 * s, f"{active_theme.fg[:7]}22", 0.75 * s)

        surf.blit(self._photo)


# ============================================================================
# Main Showcase Application
# ============================================================================

class CustomThemeShowcaseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend Theme Studio & Custom Theme Samples Gallery")
        self._scale = ScalingTracker.get_scaling_factor(root)

        w = int(1220 * self._scale)
        h = int(820 * self._scale)
        self.root.geometry(f"{w}x{h}")
        self.root.minsize(int(1020 * self._scale), int(680 * self._scale))
        pal = get_theme()
        self.root.configure(bg=pal.bg)

        # State
        self._active_tab = 0
        self._theme_card_widgets: Dict[str, ThemeCardWidget] = {}
        self._shared_progress = 72.0
        self._wave_speed = 1.0
        self._wave_amplitude = 40.0
        self._anim_radius = 20.0 * self._scale
        self._wave_active = True
        self._fps_last_time = time.perf_counter()
        self._fps = 60.0
        self._running = True
        self._tick_id = None

        self._setup_top_bar()
        self._setup_main_layout()

        # Connect unified root theme propagation
        apply_theme(self.root, recursive=True)

        # Synchronize initial active theme card
        self._update_theme_cards_selection(pal.name)

        self.root.bind("<Destroy>", lambda e: self.stop() if getattr(e, "widget", None) == self.root else None, add="+")

        # Start animation loop
        self._tick_anim()

    # ------------------------------------------------------------------------
    # Top Navigation Bar
    # ------------------------------------------------------------------------
    def _setup_top_bar(self):
        s = self._scale
        pal = get_theme()

        self.top_bar = tk.Frame(self.root, bg=pal.surface, height=int(58 * s))
        self.top_bar.pack(fill="x", padx=int(12 * s), pady=(int(10 * s), int(6 * s)))
        self.top_bar.pack_propagate(False)

        # Brand Title & Badge
        self.title_box = tk.Frame(self.top_bar, bg=pal.surface)
        self.title_box.pack(side="left", padx=int(14 * s), pady=int(6 * s))

        self.title_lbl = tk.Label(
            self.title_box,
            text="tkblend Theme Studio",
            font=("DejaVu Sans", int(14 * s), "bold"),
            fg=pal.fg,
            bg=pal.surface,
        )
        self.title_lbl.pack(side="left")

        self.theme_badge = ModernBadge(
            self.title_box,
            text=f"Preset: {THEME_DISPLAY_NAMES.get(pal.name, pal.name)}",
            variant="primary",
            parent_bg=pal.surface,
        )
        self.theme_badge.pack(side="left", padx=(int(10 * s), 0))

        # Right Side Quick Mode Switcher
        self.mode_switcher = ModernSegmentedControl(
            self.top_bar,
            values=["🌙 Dark", "☀️ Light"],
            selected_index=0 if pal.dark_mode else 1,
            on_change=self._on_quick_mode_switch,
            width=140,
            height=34,
            parent_bg=pal.surface,
        )
        self.mode_switcher.pack(side="right", padx=(int(8 * s), int(14 * s)))

        # View Tabs Navigator
        self.nav_tabs = ModernSegmentedControl(
            self.top_bar,
            values=["🎨 Theme Gallery & Playground", "✨ 60 FPS Live Vector Canvas", "🛠️ Theme Studio & Exporter"],
            selected_index=0,
            on_change=self._on_tab_changed,
            width=580,
            height=34,
            parent_bg=pal.surface,
        )
        self.nav_tabs.pack(side="right", padx=(0, int(8 * s)))

    def _on_quick_mode_switch(self, idx: int, _):
        theme_name = "dark" if idx == 0 else "light"
        self._select_theme(theme_name)

    def _on_tab_changed(self, idx: int, _):
        self._active_tab = idx
        self._refresh_tab_visibility()

    # ------------------------------------------------------------------------
    # Main Layout: Sidebar & Content Area
    # ------------------------------------------------------------------------
    def _setup_main_layout(self):
        s = self._scale
        pal = get_theme()

        self.main_split = tk.Frame(self.root, bg=pal.bg)
        self.main_split.pack(fill="both", expand=True, padx=int(12 * s), pady=(0, int(10 * s)))

        # Left Sidebar: Scrollable Theme Preset Cards
        self._setup_theme_sidebar()

        # Right Content Area: Multi-tab Views
        self.content_area = tk.Frame(self.main_split, bg=pal.bg)
        self.content_area.pack(side="left", fill="both", expand=True, padx=(int(8 * s), 0))

        # Build the 3 Tab Views
        self._build_playground_view()
        self._build_live_canvas_view()
        self._build_theme_studio_view()

        self._refresh_tab_visibility()

    # ------------------------------------------------------------------------
    # Left Sidebar: Theme Presets
    # ------------------------------------------------------------------------
    def _setup_theme_sidebar(self):
        s = self._scale
        pal = get_theme()

        self.sidebar_frame = tk.Frame(self.main_split, bg=pal.surface, width=int(265 * s))
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        # Header
        sb_hdr = tk.Frame(self.sidebar_frame, bg=pal.surface)
        sb_hdr.pack(fill="x", padx=int(12 * s), pady=(int(10 * s), int(6 * s)))

        sb_lbl = tk.Label(
            sb_hdr,
            text="PALETTE PRESETS",
            font=("DejaVu Sans", int(9 * s), "bold"),
            fg=pal.text_muted,
            bg=pal.surface,
        )
        sb_lbl.pack(side="left")

        count_badge = ModernBadge(
            sb_hdr,
            text=f"{len(THEME_PRESETS)}",
            variant="outline",
            parent_bg=pal.surface,
        )
        count_badge.pack(side="right")

        # Scrollable Canvas container for Theme Cards
        self.sb_canvas = tk.Canvas(
            self.sidebar_frame,
            bg=pal.surface,
            highlightthickness=0,
            bd=0,
        )
        self.sb_scroll_frame = tk.Frame(self.sb_canvas, bg=pal.surface)
        self.sb_canvas_window = self.sb_canvas.create_window((0, 0), window=self.sb_scroll_frame, anchor="nw")

        self.sb_canvas.pack(fill="both", expand=True, padx=int(6 * s), pady=(0, int(6 * s)))

        self.sb_scroll_frame.bind(
            "<Configure>",
            lambda e: self.sb_canvas.configure(scrollregion=self.sb_canvas.bbox("all")),
        )
        self.sb_canvas.bind(
            "<Configure>",
            lambda e: self.sb_canvas.itemconfig(self.sb_canvas_window, width=e.width),
        )
        self.sb_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.sb_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        # Populate Theme Cards
        for key, p in THEME_PRESETS.items():
            card = ThemeCardWidget(
                self.sb_scroll_frame,
                preset_key=key,
                palette=p,
                on_select=self._select_theme,
                width=240,
                height=72,
                parent_bg=pal.surface,
            )
            card.pack(fill="x", pady=int(3 * s))
            self._theme_card_widgets[key] = card

    def _select_theme(self, theme_key: str):
        if theme_key in THEME_PRESETS:
            set_theme(theme_key)
            pal = get_theme()
            self._update_theme_cards_selection(theme_key)
            self.theme_badge.text = f"Preset: {THEME_DISPLAY_NAMES.get(theme_key, theme_key)}"
            self.mode_switcher.selected_index = 0 if pal.dark_mode else 1
            self._sync_studio_inputs()

    def _update_theme_cards_selection(self, active_key: str):
        for key, card in self._theme_card_widgets.items():
            card.set_active(key == active_key)

    # ------------------------------------------------------------------------
    # Tab Switching
    # ------------------------------------------------------------------------
    def _refresh_tab_visibility(self):
        self.playground_tab.pack_forget()
        self.canvas_tab.pack_forget()
        self.studio_tab.pack_forget()

        if self._active_tab == 0:
            self.playground_tab.pack(fill="both", expand=True)
        elif self._active_tab == 1:
            self.canvas_tab.pack(fill="both", expand=True)
        else:
            self.studio_tab.pack(fill="both", expand=True)

    # ------------------------------------------------------------------------
    # Tab 1: Theme Gallery & Widget Playground
    # ------------------------------------------------------------------------
    def _build_playground_view(self):
        s = self._scale
        pal = get_theme()

        self.playground_tab = tk.Frame(self.content_area, bg=pal.bg)

        # 2x2 Grid Layout
        self.grid_container = tk.Frame(self.playground_tab, bg=pal.bg)
        self.grid_container.pack(fill="both", expand=True)
        self.grid_container.columnconfigure(0, weight=1)
        self.grid_container.columnconfigure(1, weight=1)
        self.grid_container.rowconfigure(0, weight=1)
        self.grid_container.rowconfigure(1, weight=1)

        # Card 1: Buttons & Interactive Actions
        card1 = ModernCard(
            self.grid_container,
            title="Buttons & Interactive Actions",
            parent_bg=pal.bg,
        )
        card1.grid(row=0, column=0, sticky="nsew", padx=int(4 * s), pady=int(4 * s))

        c1_content = tk.Frame(card1, bg=pal.card_bg)
        c1_content.pack(fill="both", expand=True, padx=int(14 * s), pady=(int(46 * s), int(10 * s)))

        row1_a = tk.Frame(c1_content, bg=pal.card_bg)
        row1_a.pack(fill="x", pady=(0, int(8 * s)))
        b_elev = ModernButton(row1_a, text="Elevated", variant="elevated", width=90, height=34, parent_bg=pal.card_bg)
        b_elev.pack(side="left", padx=(0, int(6 * s)))
        b_filled = ModernButton(row1_a, text="Primary", variant="filled", width=90, height=34, parent_bg=pal.card_bg)
        b_filled.pack(side="left", padx=(0, int(6 * s)))
        b_tonal = ModernButton(row1_a, text="Tonal", variant="tonal", width=90, height=34, parent_bg=pal.card_bg)
        b_tonal.pack(side="left", padx=(0, int(6 * s)))
        b_outline = ModernButton(row1_a, text="Outlined", variant="outlined", width=90, height=34, parent_bg=pal.card_bg)
        b_outline.pack(side="left")

        row1_b = tk.Frame(c1_content, bg=pal.card_bg)
        row1_b.pack(fill="x")
        b_destruct = ModernButton(row1_b, text="Destructive", variant="destructive", width=105, height=34, parent_bg=pal.card_bg)
        b_destruct.pack(side="left", padx=(0, int(6 * s)))
        b_text = ModernButton(row1_b, text="Text Button", variant="text", width=95, height=34, parent_bg=pal.card_bg)
        b_text.pack(side="left", padx=(0, int(6 * s)))
        b_icon = ModernButton(row1_b, text="★ Star", variant="filled", width=85, height=34, parent_bg=pal.card_bg)
        b_icon.pack(side="left")

        # Card 2: Form Inputs & Selectors
        card2 = ModernCard(
            self.grid_container,
            title="Inputs & Selection Controls",
            parent_bg=pal.bg,
        )
        card2.grid(row=0, column=1, sticky="nsew", padx=int(4 * s), pady=int(4 * s))

        c2_content = tk.Frame(card2, bg=pal.card_bg)
        c2_content.pack(fill="both", expand=True, padx=int(14 * s), pady=(int(46 * s), int(10 * s)))

        row2_a = tk.Frame(c2_content, bg=pal.card_bg)
        row2_a.pack(fill="x", pady=(0, int(10 * s)))

        txt_in = ModernTextInput(
            row2_a,
            placeholder="Focus ring text input...",
            width=195,
            height=34,
            parent_bg=pal.card_bg,
        )
        txt_in.pack(side="left", padx=(0, int(8 * s)))

        dropdown = ModernDropdown(
            row2_a,
            options=["Vector Surface", "Blend2D Core", "Direct Blit Pipeline"],
            selected="Vector Surface",
            width=165,
            height=34,
            parent_bg=pal.card_bg,
        )
        dropdown.pack(side="left")

        row2_b = tk.Frame(c2_content, bg=pal.card_bg)
        row2_b.pack(fill="x")

        sw1 = ModernSwitch(row2_b, is_on=True, width=48, height=26, parent_bg=pal.card_bg)
        sw1.pack(side="left", padx=(0, int(8 * s)))

        cb1 = ModernCheckbox(row2_b, text="Vector Checkbox", checked=True, parent_bg=pal.card_bg)
        cb1.pack(side="left", padx=(0, int(10 * s)))

        rg = ModernRadioGroup()
        r1 = ModernRadio(row2_b, text="Option A", value="A", group=rg, width=85, parent_bg=pal.card_bg)
        r1.pack(side="left", padx=(0, int(4 * s)))
        r2 = ModernRadio(row2_b, text="Option B", value="B", group=rg, width=85, parent_bg=pal.card_bg)
        r2.pack(side="left")
        rg.select("A")

        # Card 3: Sliders, Ranges & Dynamic Gauges
        card3 = ModernCard(
            self.grid_container,
            title="Sliders, Progress & Radial Gauges",
            parent_bg=pal.bg,
        )
        card3.grid(row=1, column=0, sticky="nsew", padx=int(4 * s), pady=int(4 * s))

        c3_content = tk.Frame(card3, bg=pal.card_bg)
        c3_content.pack(fill="both", expand=True, padx=int(14 * s), pady=(int(46 * s), int(10 * s)))

        row3_a = tk.Frame(c3_content, bg=pal.card_bg)
        row3_a.pack(fill="both", expand=True)

        self.gauge_main = ModernCircularProgress(
            row3_a,
            value=self._shared_progress,
            size=80,
            stroke_width=7.5,
            parent_bg=pal.card_bg,
        )
        self.gauge_main.pack(side="left", padx=(0, int(14 * s)))

        sliders_box = tk.Frame(row3_a, bg=pal.card_bg)
        sliders_box.pack(side="left", fill="both", expand=True)

        self.slider_master = ModernSlider(
            sliders_box,
            value=self._shared_progress,
            min_val=0.0,
            max_val=100.0,
            on_change=self._on_slider_change,
            height=26,
            parent_bg=pal.card_bg,
        )
        self.slider_master.pack(fill="x", pady=(0, int(4 * s)))

        self.range_slider = ModernRangeSlider(
            sliders_box,
            min_val=0.0,
            max_val=100.0,
            low_val=20.0,
            high_val=80.0,
            height=26,
            parent_bg=pal.card_bg,
        )
        self.range_slider.pack(fill="x", pady=(0, int(4 * s)))

        self.progress_linear = ModernProgressBar(
            sliders_box,
            value=self._shared_progress,
            height=10,
            parent_bg=pal.card_bg,
        )
        self.progress_linear.pack(fill="x")

        # Card 4: Badges, Avatars & Accordion Containers
        card4 = ModernCard(
            self.grid_container,
            title="Badges, Avatars & Structure",
            parent_bg=pal.bg,
        )
        card4.grid(row=1, column=1, sticky="nsew", padx=int(4 * s), pady=int(4 * s))

        c4_content = tk.Frame(card4, bg=pal.card_bg)
        c4_content.pack(fill="both", expand=True, padx=int(14 * s), pady=(int(46 * s), int(10 * s)))

        # Row 4a: Status Badges (4 pills)
        row4_badges = tk.Frame(c4_content, bg=pal.card_bg)
        row4_badges.pack(fill="x", pady=(0, int(6 * s)))

        b_p = ModernBadge(row4_badges, text="Primary", variant="primary", width=75, height=22, parent_bg=pal.card_bg)
        b_p.pack(side="left", padx=(0, int(6 * s)))
        b_s = ModernBadge(row4_badges, text="Success", variant="success", width=75, height=22, parent_bg=pal.card_bg)
        b_s.pack(side="left", padx=(0, int(6 * s)))
        b_w = ModernBadge(row4_badges, text="Warning", variant="warning", width=75, height=22, parent_bg=pal.card_bg)
        b_w.pack(side="left", padx=(0, int(6 * s)))
        b_d = ModernBadge(row4_badges, text="Destruct", variant="destructive", width=75, height=22, parent_bg=pal.card_bg)
        b_d.pack(side="left")

        # Row 4b: Avatars & Status
        row4_avatars = tk.Frame(c4_content, bg=pal.card_bg)
        row4_avatars.pack(fill="x", pady=(0, int(6 * s)))

        av1 = ModernAvatar(row4_avatars, initials="TB", status="online", size=30, parent_bg=pal.card_bg)
        av1.pack(side="left", padx=(0, int(6 * s)))
        lbl_av1 = tk.Label(row4_avatars, text="Online", font=("DejaVu Sans", int(8.5 * s), "bold"), fg=pal.success, bg=pal.card_bg)
        lbl_av1.pack(side="left", padx=(0, int(16 * s)))

        av2 = ModernAvatar(row4_avatars, initials="UI", status="busy", size=30, parent_bg=pal.card_bg)
        av2.pack(side="left", padx=(0, int(6 * s)))
        lbl_av2 = tk.Label(row4_avatars, text="Busy", font=("DejaVu Sans", int(8.5 * s), "bold"), fg=pal.warning, bg=pal.card_bg)
        lbl_av2.pack(side="left")

        # Accordion
        accordion = ModernAccordion(
            c4_content,
            title="Surface Vector Architecture",
            parent_bg=pal.card_bg,
        )
        accordion.pack(fill="x")
        acc_lbl = tk.Label(
            accordion.content_frame,
            text="High performance 2D vector rendering powered directly by Blend2D C++ engine. Features subpixel antialiasing and automatic color theme sync.",
            wraplength=int(380 * s),
            justify="left",
            font=("DejaVu Sans", int(8.5 * s)),
            fg=pal.text_muted,
            bg=pal.surface,
        )
        acc_lbl.pack(padx=int(8 * s), pady=int(6 * s), anchor="w")

    def _on_slider_change(self, val: float):
        self._shared_progress = val
        self.progress_linear.value = val
        self.gauge_main.value = val

    # ------------------------------------------------------------------------
    # Tab 2: Interactive 60 FPS Live Vector Canvas
    # ------------------------------------------------------------------------
    def _build_live_canvas_view(self):
        s = self._scale
        pal = get_theme()

        self.canvas_tab = tk.Frame(self.content_area, bg=pal.bg)

        # Control Strip on top
        ctrl_strip = ModernFrame(self.canvas_tab, height=52, parent_bg=pal.bg)
        ctrl_strip.pack(fill="x", pady=(0, int(8 * s)))

        speed_lbl = tk.Label(ctrl_strip, text="Wave Speed:", font=("DejaVu Sans", int(9 * s), "bold"), fg=pal.fg, bg=pal.card_bg)
        speed_lbl.pack(side="left", padx=(int(14 * s), int(6 * s)))
        speed_slider = ModernSlider(ctrl_strip, value=1.0, min_val=0.1, max_val=3.0, on_change=self._on_speed_change, width=120, height=24, parent_bg=pal.card_bg)
        speed_slider.pack(side="left", padx=(0, int(16 * s)))

        amp_lbl = tk.Label(ctrl_strip, text="Amplitude:", font=("DejaVu Sans", int(9 * s), "bold"), fg=pal.fg, bg=pal.card_bg)
        amp_lbl.pack(side="left", padx=(0, int(6 * s)))
        amp_slider = ModernSlider(ctrl_strip, value=40.0, min_val=5.0, max_val=80.0, on_change=self._on_amp_change, width=120, height=24, parent_bg=pal.card_bg)
        amp_slider.pack(side="left", padx=(0, int(16 * s)))

        sw_wave = ModernSwitch(ctrl_strip, is_on=True, on_toggle=self._on_wave_toggle, width=48, height=26, parent_bg=pal.card_bg)
        sw_wave.pack(side="left")
        sw_lbl = tk.Label(ctrl_strip, text="Animate", font=("DejaVu Sans", int(9 * s)), fg=pal.text_muted, bg=pal.card_bg)
        sw_lbl.pack(side="left", padx=(int(4 * s), 0))

        # BlendCanvas rendering surface
        self.live_canvas = BlendCanvas(
            self.canvas_tab,
            width=int(800 * s),
            height=int(500 * s),
            on_draw=self._draw_live_canvas,
            bg=pal.bg,
        )
        self.live_canvas.pack(fill="both", expand=True)

    def _on_speed_change(self, val: float):
        self._wave_speed = val

    def _on_amp_change(self, val: float):
        self._wave_amplitude = val

    def _on_wave_toggle(self, state: bool):
        self._wave_active = state

    def _draw_live_canvas(self, surf: Surface):
        w, h = float(surf.width), float(surf.height)
        s = self._scale
        pal = get_theme()
        t = time.perf_counter() * self._wave_speed if self._wave_active else 0.0

        # FPS calculation
        now = time.perf_counter()
        dt = now - self._fps_last_time
        if dt > 0.3:
            self._fps = 1.0 / max(0.001, dt)
            self._fps_last_time = now

        # Background gradient fill
        bg_grad = LinearGradient(0, 0, 0, float(h))
        bg_grad.add_stop(0.0, pal.bg)
        bg_grad.add_stop(1.0, pal.surface)
        surf.fill_rect(0, 0, w, h, bg_grad)

        # Background glowing radial orb
        orb_x = w * 0.75 + math.cos(t * 0.8) * 60.0 * s
        orb_y = h * 0.35 + math.sin(t * 0.6) * 40.0 * s
        rad_grad = RadialGradient(orb_x, orb_y, 0.0, orb_x, orb_y, 220.0 * s)
        rad_grad.add_stop(0.0, f"{pal.primary[:7]}55")
        rad_grad.add_stop(0.5, f"{pal.accent[:7]}22")
        rad_grad.add_stop(1.0, f"{pal.bg[:7]}00")
        surf.fill_circle(orb_x, orb_y, 220.0 * s, rad_grad)

        # Flowing Sine Vector Waves
        wave_steps = 80
        for wave_idx, (phase_offset, alpha, col) in enumerate([
            (0.0, "44", pal.primary),
            (1.6, "66", pal.accent),
            (3.2, "99", pal.primary_hover),
        ]):
            path = Path()
            path.move_to(0, float(h))
            for i in range(wave_steps + 1):
                norm_x = i / float(wave_steps)
                x = norm_x * w
                freq = 2.5 + wave_idx * 0.8
                y = h * 0.65 + math.sin(norm_x * math.pi * freq + t * 1.5 + phase_offset) * (self._wave_amplitude * s)
                if i == 0:
                    path.line_to(x, y)
                else:
                    path.line_to(x, y)
            path.line_to(float(w), float(h))
            path.close()
            surf.fill_path(path, f"{col[:7]}{alpha}")

        # Glassmorphic floating card 1
        card1_w, card1_h = 280.0 * s, 140.0 * s
        card1_x = 50.0 * s
        card1_y = 60.0 * s + math.sin(t * 1.2) * 14.0 * s

        surf.draw_card(
            card1_x, card1_y, card1_w, card1_h,
            rx=16.0 * s, ry=16.0 * s,
            bg_color=f"{pal.card_bg[:7]}ee" if pal.dark_mode else "#ffffffee",
            border_color=pal.primary,
            border_width=1.5 * s,
            shadow_blur=14.0 * s,
            shadow_color=pal.shadow_color,
            shadow_offset_y=6.0 * s,
        )
        surf.draw_text("Vector Glass Card", card1_x + 20 * s, card1_y + 36 * s, font_size=15 * s, color=pal.fg, weight="bold")
        surf.draw_text(f"Active Theme: {THEME_DISPLAY_NAMES.get(pal.name, pal.name)}", card1_x + 20 * s, card1_y + 64 * s, font_size=11 * s, color=pal.text_muted)
        surf.fill_rounded_rect(card1_x + 20 * s, card1_y + 92 * s, 180 * s, 8 * s, 4 * s, 4 * s, pal.primary)
        surf.fill_circle(card1_x + 230 * s, card1_y + 96 * s, 12 * s, pal.accent)

        # FPS HUD Overlay Card
        hud_w, hud_h = 140.0 * s, 46.0 * s
        hud_x = w - hud_w - 20.0 * s
        hud_y = 20.0 * s
        surf.draw_card(
            hud_x, hud_y, hud_w, hud_h,
            rx=10.0 * s, ry=10.0 * s,
            bg_color=f"{pal.surface[:7]}dd" if pal.dark_mode else "#ffffffdd",
            border_color=pal.surface_border,
            border_width=1.0 * s,
            shadow_blur=8.0 * s,
            shadow_color=pal.shadow_color,
            shadow_offset_y=3.0 * s,
        )
        surf.draw_text(
            f"{self._fps:.1f} FPS",
            hud_x + hud_w / 2.0,
            hud_y + hud_h / 2.0 + 4.0 * s,
            font_size=14 * s,
            color=pal.success,
            align="center",
            weight="bold",
        )

    # ------------------------------------------------------------------------
    # Tab 3: Theme Studio & Code Exporter
    # ------------------------------------------------------------------------
    def _build_theme_studio_view(self):
        s = self._scale
        pal = get_theme()

        self.studio_tab = tk.Frame(self.content_area, bg=pal.bg)
        self.studio_tab.columnconfigure(0, weight=1)
        self.studio_tab.columnconfigure(1, weight=1)
        self.studio_tab.rowconfigure(0, weight=1)

        # Left Column: Palette Token Color Tweakers
        self.studio_controls_card = ModernCard(
            self.studio_tab,
            title="Live Palette Token Tweaker",
            parent_bg=pal.bg,
        )
        self.studio_controls_card.grid(row=0, column=0, sticky="nsew", padx=int(4 * s), pady=int(4 * s))

        studio_ctrl_content = tk.Frame(self.studio_controls_card, bg=pal.card_bg)
        studio_ctrl_content.pack(fill="both", expand=True, padx=int(14 * s), pady=(int(46 * s), int(10 * s)))

        self.token_inputs: Dict[str, ModernTextInput] = {}
        tokens_list = [
            ("name", "Theme Name", pal.name),
            ("primary", "Primary Accent", pal.primary),
            ("accent", "Secondary Accent", pal.accent),
            ("bg", "App Background", pal.bg),
            ("surface", "Surface / Sidebar", pal.surface),
            ("card_bg", "Card Background", pal.card_bg),
            ("card_border", "Card Border", pal.card_border),
            ("fg", "Foreground / Text", pal.fg),
            ("text_muted", "Muted Text", pal.text_muted),
            ("success", "Success Color", pal.success),
            ("destructive", "Destructive Color", pal.destructive),
        ]

        # Scrollable container for single-column token list
        token_canvas = tk.Canvas(
            studio_ctrl_content,
            bg=pal.card_bg,
            highlightthickness=0,
            bd=0,
        )
        token_scroll_frame = tk.Frame(token_canvas, bg=pal.card_bg)
        token_canvas_window = token_canvas.create_window((0, 0), window=token_scroll_frame, anchor="nw")

        token_canvas.pack(side="top", fill="both", expand=True, pady=(0, int(8 * s)))

        token_scroll_frame.bind(
            "<Configure>",
            lambda e: token_canvas.configure(scrollregion=token_canvas.bbox("all")),
        )
        token_canvas.bind(
            "<Configure>",
            lambda e: token_canvas.itemconfig(token_canvas_window, width=e.width),
        )
        token_canvas.bind_all(
            "<MouseWheel>",
            lambda e: token_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units") if self._active_tab == 2 else None,
        )

        for row_idx, (token_key, label_txt, init_val) in enumerate(tokens_list):
            row_frame = tk.Frame(token_scroll_frame, bg=pal.card_bg)
            row_frame.pack(fill="x", pady=int(3 * s))

            lbl = tk.Label(
                row_frame,
                text=label_txt,
                font=("DejaVu Sans", int(9 * s), "bold"),
                fg=pal.fg,
                bg=pal.card_bg,
                width=16,
                anchor="w",
            )
            lbl.pack(side="left", padx=(0, int(8 * s)))

            in_widget = ModernTextInput(
                row_frame,
                placeholder="#RRGGBB",
                width=160,
                height=28,
                parent_bg=pal.card_bg,
            )
            in_widget.value = str(init_val)
            in_widget.pack(side="left", fill="x", expand=True)
            self.token_inputs[token_key] = in_widget

        # Action Buttons Row (pinned at bottom)
        actions_row = tk.Frame(studio_ctrl_content, bg=pal.card_bg)
        actions_row.pack(side="bottom", fill="x", pady=(int(6 * s), 0))

        btn_apply = ModernButton(
            actions_row,
            text="⚡ Apply Custom Theme",
            variant="filled",
            width=175,
            height=34,
            command=self._apply_custom_theme_from_studio,
            parent_bg=pal.card_bg,
        )
        btn_apply.pack(side="left", padx=(0, int(8 * s)))

        btn_reset = ModernButton(
            actions_row,
            text="🔄 Reset to Preset",
            variant="tonal",
            width=135,
            height=34,
            command=lambda: self._select_theme(get_theme().name),
            parent_bg=pal.card_bg,
        )
        btn_reset.pack(side="left")

        # Right Column: Live Code Exporter
        self.studio_code_card = ModernCard(
            self.studio_tab,
            title="Generated Palette Code & Export",
            parent_bg=pal.bg,
        )
        self.studio_code_card.grid(row=0, column=1, sticky="nsew", padx=int(4 * s), pady=int(4 * s))

        studio_code_content = tk.Frame(self.studio_code_card, bg=pal.card_bg)
        studio_code_content.pack(fill="both", expand=True, padx=int(14 * s), pady=(int(46 * s), int(10 * s)))

        # Code Text Area
        self.code_text = tk.Text(
            studio_code_content,
            wrap="none",
            font=("Monospace", int(9.5 * s)),
            bg=pal.surface,
            fg=pal.fg,
            insertbackground=pal.primary,
            relief="flat",
            bd=0,
            padx=int(10 * s),
            pady=int(10 * s),
        )
        self.code_text.pack(fill="both", expand=True, pady=(0, int(8 * s)))

        # Export Buttons
        btn_export_row = tk.Frame(studio_code_content, bg=pal.card_bg)
        btn_export_row.pack(fill="x")

        self.btn_copy_py = ModernButton(
            btn_export_row,
            text="📋 Copy Python Code",
            variant="filled",
            width=165,
            height=34,
            command=self._copy_python_code,
            parent_bg=pal.card_bg,
        )
        self.btn_copy_py.pack(side="left", padx=(0, int(8 * s)))

        self.btn_copy_json = ModernButton(
            btn_export_row,
            text="📋 Copy JSON",
            variant="outlined",
            width=125,
            height=34,
            command=self._copy_json_code,
            parent_bg=pal.card_bg,
        )
        self.btn_copy_json.pack(side="left")

        self._sync_studio_inputs()

    def _sync_studio_inputs(self):
        pal = get_theme()
        for key, widget in self.token_inputs.items():
            if hasattr(pal, key):
                widget.value = str(getattr(pal, key))
        self._refresh_code_export()

    def _apply_custom_theme_from_studio(self):
        try:
            curr = get_theme()
            custom_name = self.token_inputs["name"].value.strip() or "custom"
            new_pal = Palette(
                name=custom_name,
                dark_mode=curr.dark_mode,
                primary=self.token_inputs["primary"].value.strip(),
                accent=self.token_inputs["accent"].value.strip(),
                bg=self.token_inputs["bg"].value.strip(),
                surface=self.token_inputs["surface"].value.strip(),
                card_bg=self.token_inputs["card_bg"].value.strip(),
                card_border=self.token_inputs["card_border"].value.strip(),
                fg=self.token_inputs["fg"].value.strip(),
                text_muted=self.token_inputs["text_muted"].value.strip(),
                success=self.token_inputs["success"].value.strip(),
                destructive=self.token_inputs["destructive"].value.strip(),
            )
            set_theme(new_pal)
            self._refresh_code_export()
        except Exception as e:
            print(f"Error applying custom theme: {e}")

    def _refresh_code_export(self):
        pal = get_theme()
        py_code = f'''from tkblend.theme import Palette, set_theme

CUSTOM_PALETTE = Palette(
    name="{pal.name}",
    dark_mode={pal.dark_mode},
    bg="{pal.bg}",
    fg="{pal.fg}",
    text_muted="{pal.text_muted}",
    card_bg="{pal.card_bg}",
    card_border="{pal.card_border}",
    surface="{pal.surface}",
    surface_border="{pal.surface_border}",
    primary="{pal.primary}",
    primary_hover="{pal.primary_hover}",
    primary_active="{pal.primary_active}",
    primary_fg="{pal.primary_fg}",
    secondary="{pal.secondary}",
    secondary_hover="{pal.secondary_hover}",
    secondary_active="{pal.secondary_active}",
    secondary_fg="{pal.secondary_fg}",
    accent="{pal.accent}",
    success="{pal.success}",
    warning="{pal.warning}",
    destructive="{pal.destructive}",
    input_bg="{pal.input_bg}",
    input_border="{pal.input_border}",
    input_focus="{pal.input_focus}",
    track_bg="{pal.track_bg}",
    thumb_color="{pal.thumb_color}",
)

# Activate anywhere in tkblend:
set_theme(CUSTOM_PALETTE)
'''
        self.code_text.delete("1.0", "end")
        self.code_text.insert("1.0", py_code)

    def _copy_python_code(self):
        code = self.code_text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self.btn_copy_py.text = "✓ Copied!"
        self.root.after(2000, lambda: setattr(self.btn_copy_py, "text", "📋 Copy Python Code"))

    def _copy_json_code(self):
        pal = get_theme()
        data = {
            "name": pal.name,
            "dark_mode": pal.dark_mode,
            "bg": pal.bg,
            "fg": pal.fg,
            "text_muted": pal.text_muted,
            "card_bg": pal.card_bg,
            "card_border": pal.card_border,
            "surface": pal.surface,
            "surface_border": pal.surface_border,
            "primary": pal.primary,
            "accent": pal.accent,
            "success": pal.success,
            "warning": pal.warning,
            "destructive": pal.destructive,
        }
        json_str = json.dumps(data, indent=2)
        self.root.clipboard_clear()
        self.root.clipboard_append(json_str)
        self.btn_copy_json.text = "✓ Copied JSON!"
        self.root.after(2000, lambda: setattr(self.btn_copy_json, "text", "📋 Copy JSON"))

    # ------------------------------------------------------------------------
    # Animation Loop
    # ------------------------------------------------------------------------
    def _tick_anim(self):
        if not getattr(self, "_running", True):
            return
        try:
            if not hasattr(self, "root") or not self.root.winfo_exists():
                return
            if hasattr(self, "live_canvas") and self.live_canvas.winfo_exists() and self._active_tab == 1:
                self.live_canvas.redraw()
            if getattr(self, "_running", True) and self.root.winfo_exists():
                self._tick_id = self.root.after(16, self._tick_anim)
        except Exception:
            pass

    def stop(self):
        self._running = False
        if getattr(self, "_tick_id", None):
            try:
                self.root.after_cancel(self._tick_id)
            except Exception:
                pass
            self._tick_id = None


def main():
    root = tk.Tk()
    app = CustomThemeShowcaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
