"""
tkblend Extended Vector Canvas Showcase Application.
A comprehensive catalog of 15+ modern, self-contained vector widgets built strictly from
scratch using Blend2D's Surface and BlendCanvas without any TTK theme dependencies.

Features:
- DPI-aware coordinate scaling with ScalingTracker
- Zero-copy Tk_PhotoPutBlock blitting via Surface.blit()
- Comprehensive widget catalog:
    * ModernButton (multiple variants, hover/press elevation depth)
    * ModernProgressBar (capsule linear gradient)
    * ModernCircularProgress (vector arc ring / radial gauge with readout)
    * ModernSlider (smooth draggable track & glowing thumb)
    * ModernRangeSlider (dual-thumb min/max range selector)
    * ModernSwitch (iOS / Fluent style toggle pill)
    * ModernCheckbox (rounded vector box with animated vector checkmark path)
    * ModernRadio & ModernRadioGroup (concentric animated dot vector radios)
    * ModernSegmentedControl (capsule track with elevated active pill indicator)
    * ModernTextInput (rounded focus-ring input with placeholder & clear icon)
    * ModernDropdown (vector selector with chevron and popup menu)
    * ModernSpinBox (numeric stepper with vector +/- buttons)
    * ModernBadge (status pills: primary, success, warning, destructive, outline)
    * ModernAvatar (circular gradient avatar with status dot)
    * ModernAccordion (collapsible card with rotating vector chevron)
    * ModernCard & ModernFrame (elevated containers with soft drop shadow)
- 4-View Category Navigation via ModernSegmentedControl:
    1. Controls & Forms
    2. Sliders & Gauges
    3. Display & Cards
    4. Live Vector Canvas (60 FPS fluid waves, glassmorphic cards, HUD FPS)
- Real-time interconnected state: adjusting controls updates gauges & live canvas parameters.
"""

from __future__ import annotations
import math
import sys
import time
import tkinter as tk
from math import floor, ceil
from typing import Optional, Callable, Union, List, Tuple, Any

from tkblend import (
    Surface,
    BlendCanvas,
    LinearGradient,
    RadialGradient,
    Path,
    ColorLike,
    parse_color,
)

from tkblend.widgets import (
    ScalingTracker,
    ModernWidget,
    Widget,
    ModernFrame,
    Frame,
    ModernCard,
    Card,
    ModernButton,
    Button,
    ModernProgressBar,
    ProgressBar,
    ModernCircularProgress,
    CircularProgress,
    ModernSlider,
    Slider,
    ModernRangeSlider,
    RangeSlider,
    ModernSwitch,
    Switch,
    ToggleSwitch,
    ModernCheckbox,
    Checkbox,
    ModernRadio,
    Radio,
    ModernRadioGroup,
    RadioGroup,
    ModernSegmentedControl,
    SegmentedControl,
    ModernTextInput,
    TextInput,
    ModernSpinBox,
    SpinBox,
    ModernBadge,
    Badge,
    ModernAvatar,
    Avatar,
    ModernAccordion,
    Accordion,
    ModernDropdown,
    Dropdown,
    DropdownItem,
    ModernScrollbar,
    VectorScrollbar,
)


# ============================================================================
# Main Showcase Application
# ============================================================================

class ExtendedCanvasShowcaseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend Extended Vector Canvas Showcase - All Modern Widgets")
        self._scale = ScalingTracker.get_scaling_factor(root)

        w = int(1140 * self._scale)
        h = int(740 * self._scale)
        self.root.geometry(f"{w}x{h}")
        self.root.minsize(int(960 * self._scale), int(640 * self._scale))
        self.root.configure(bg="#11111b")

        self._start_time = time.perf_counter()
        self._fps_frames = 0
        self._fps_last_time = time.perf_counter()
        self._fps = 60.0

        # Live interconnected state
        self._shared_progress = 65.0
        self._wave_speed = 1.0
        self._wave_amplitude = 35.0
        self._anim_radius = 20.0 * self._scale
        self._wave_active = True

        self._setup_top_nav()
        self._setup_views()

        # Start 60 FPS animation loop
        self._tick_anim()

    def _setup_top_nav(self):
        s = self._scale
        top_bar = tk.Frame(self.root, bg="#181825", height=int(56 * s))
        top_bar.pack(fill="x", padx=int(12 * s), pady=(int(12 * s), int(8 * s)))
        top_bar.pack_propagate(False)

        # Title & Subtitle on left
        title_box = tk.Frame(top_bar, bg="#181825")
        title_box.pack(side="left", padx=int(16 * s), pady=int(6 * s))

        tk.Label(
            title_box,
            text="tkblend Vector Suite",
            font=("DejaVu Sans", int(14 * s), "bold"),
            fg="#cdd6f4",
            bg="#181825",
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="15+ Pure Surface Vector Widgets",
            font=("DejaVu Sans", int(9 * s)),
            fg="#a6adc8",
            bg="#181825",
        ).pack(anchor="w")

        # Category Navigator Pill Switcher
        self.nav_tabs = ModernSegmentedControl(
            top_bar,
            values=["Controls & Forms", "Sliders & Gauges", "Display & Cards", "Live Vector Canvas"],
            selected_index=0,
            on_change=self._on_tab_changed,
            width=580,
            height=36,
            active_color="#89b4fa",
            parent_bg="#181825",
        )
        self.nav_tabs.pack(side="right", padx=int(16 * s))

    def _setup_views(self):
        s = self._scale
        self.views_container = tk.Frame(self.root, bg="#11111b")
        self.views_container.pack(fill="both", expand=True, padx=int(12 * s), pady=(0, int(12 * s)))

        # Create the 4 View frames
        self.view_controls = tk.Frame(self.views_container, bg="#11111b")
        self.view_sliders = tk.Frame(self.views_container, bg="#11111b")
        self.view_display = tk.Frame(self.views_container, bg="#11111b")
        self.view_canvas = tk.Frame(self.views_container, bg="#11111b")

        self._build_view_controls()
        self._build_view_sliders()
        self._build_view_display()
        self._build_view_canvas()

        # Display first view
        self._show_view(0)

    def _on_tab_changed(self, idx: int, name: str):
        self._show_view(idx)

    def _show_view(self, idx: int):
        for v in (self.view_controls, self.view_sliders, self.view_display, self.view_canvas):
            v.pack_forget()
        views = [self.view_controls, self.view_sliders, self.view_display, self.view_canvas]
        if 0 <= idx < len(views):
            views[idx].pack(fill="both", expand=True)

    # ------------------------------------------------------------------------
    # View 1: Controls & Forms
    # ------------------------------------------------------------------------
    def _build_view_controls(self):
        s = self._scale
        # 3-Column Card Layout
        col1 = ModernCard(self.view_controls, title="Buttons & Variants", width=340, height=600, parent_bg="#11111b")
        col1.pack(side="left", fill="both", expand=True, padx=int(6 * s))

        col2 = ModernCard(self.view_controls, title="Selection & Toggles", width=340, height=600, parent_bg="#11111b")
        col2.pack(side="left", fill="both", expand=True, padx=int(6 * s))

        col3 = ModernCard(self.view_controls, title="Text & Dropdowns", width=340, height=600, parent_bg="#11111b")
        col3.pack(side="left", fill="both", expand=True, padx=int(6 * s))

        # Buttons column
        btn_box = tk.Frame(col1, bg="#181825")
        btn_box.pack(fill="both", expand=True, padx=int(16 * s), pady=(int(52 * s), int(16 * s)))

        ModernButton(btn_box, text="Primary Action", variant="primary", command=self._inc_progress, width=280, height=40, parent_bg="#181825").pack(pady=int(6 * s))
        ModernButton(btn_box, text="Secondary Action", variant="secondary", width=280, height=40, parent_bg="#181825").pack(pady=int(6 * s))
        ModernButton(btn_box, text="Accent Action", variant="accent", command=self._reset_progress, width=280, height=40, parent_bg="#181825").pack(pady=int(6 * s))
        ModernButton(btn_box, text="Destructive Button", variant="destructive", width=280, height=40, parent_bg="#181825").pack(pady=int(6 * s))
        ModernButton(btn_box, text="Outline Button", variant="outline", width=280, height=40, parent_bg="#181825").pack(pady=int(6 * s))

        # Selection column
        sel_box = tk.Frame(col2, bg="#181825")
        sel_box.pack(fill="both", expand=True, padx=int(16 * s), pady=(int(52 * s), int(16 * s)))

        tk.Label(sel_box, text="Toggle Switches:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(0, int(6 * s)))
        switch_row = tk.Frame(sel_box, bg="#181825")
        switch_row.pack(fill="x", pady=int(4 * s))
        tk.Label(switch_row, text="Dynamic Wave Animation", fg="#a6adc8", bg="#181825").pack(side="left")
        ModernSwitch(switch_row, is_on=True, on_toggle=self._on_wave_toggle, parent_bg="#181825").pack(side="right")

        tk.Label(sel_box, text="Vector Checkboxes:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(14 * s), int(6 * s)))
        ModernCheckbox(sel_box, text="Hardware Acceleration", checked=True, width=280, parent_bg="#181825").pack(pady=int(3 * s))
        ModernCheckbox(sel_box, text="High-DPI Per-Monitor", checked=True, width=280, parent_bg="#181825").pack(pady=int(3 * s))
        ModernCheckbox(sel_box, text="Enable Bloom Shaders", checked=False, width=280, parent_bg="#181825").pack(pady=int(3 * s))

        tk.Label(sel_box, text="Radio Option Group:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(14 * s), int(6 * s)))
        self.radio_group = ModernRadioGroup()
        ModernRadio(sel_box, text="Vector Engine 2D", value="blend2d", group=self.radio_group, width=280, parent_bg="#181825").pack(pady=int(3 * s))
        ModernRadio(sel_box, text="Direct Blit Pipeline", value="direct", group=self.radio_group, width=280, parent_bg="#181825").pack(pady=int(3 * s))
        ModernRadio(sel_box, text="Legacy GDI Mode", value="legacy", group=self.radio_group, width=280, parent_bg="#181825").pack(pady=int(3 * s))

        # Inputs column
        inp_box = tk.Frame(col3, bg="#181825")
        inp_box.pack(fill="both", expand=True, padx=int(16 * s), pady=(int(52 * s), int(16 * s)))

        tk.Label(inp_box, text="Vector Text Input:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(0, int(6 * s)))
        self.txt_input = ModernTextInput(inp_box, placeholder="Type something...", width=280, height=38, parent_bg="#181825")
        self.txt_input.pack(fill="x", pady=int(4 * s))
        self.txt_input.set("tkblend vector canvas")

        tk.Label(inp_box, text="Dropdown Selector (Scrollable & Vector):", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(16 * s), int(6 * s)))
        self.dropdown = ModernDropdown(
            inp_box,
            options=[
                "High Quality (60 FPS)",
                "Balanced (30 FPS)",
                "Power Saver (15 FPS)",
                "Ultra Vector HD",
                "Cinematic 120 FPS",
                "Eco Mode (Minimal GPU)",
                "Low Latency Gaming",
                "Custom Dynamic Scaling",
            ],
            selected="High Quality (60 FPS)",
            max_visible_items=5,
            width=280,
            height=36,
            parent_bg="#181825",
        )
        self.dropdown.pack(fill="x", pady=int(4 * s))

        tk.Label(inp_box, text="Numeric Stepper:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(16 * s), int(6 * s)))
        self.spinbox = ModernSpinBox(inp_box, min_val=0, max_val=100, value=int(self._shared_progress), on_change=self._on_stepper_change, width=280, height=36, parent_bg="#181825")
        self.spinbox.pack(fill="x", pady=int(4 * s))

    # ------------------------------------------------------------------------
    # View 2: Sliders & Gauges
    # ------------------------------------------------------------------------
    def _build_view_sliders(self):
        s = self._scale
        col1 = ModernCard(self.view_sliders, title="Progress Indicators", width=520, height=600, parent_bg="#11111b")
        col1.pack(side="left", fill="both", expand=True, padx=int(6 * s))

        col2 = ModernCard(self.view_sliders, title="Continuous & Range Sliders", width=520, height=600, parent_bg="#11111b")
        col2.pack(side="right", fill="both", expand=True, padx=int(6 * s))

        # Progress side
        p_box = tk.Frame(col1, bg="#181825")
        p_box.pack(fill="both", expand=True, padx=int(20 * s), pady=(int(52 * s), int(16 * s)))

        tk.Label(p_box, text="Capsule Linear Progress:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(0, int(6 * s)))
        self.progress_linear = ModernProgressBar(p_box, width=460, height=18, value=self._shared_progress, parent_bg="#181825")
        self.progress_linear.pack(fill="x", pady=int(4 * s))

        tk.Label(p_box, text="Accent Secondary Progress:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(16 * s), int(6 * s)))
        self.progress_accent = ModernProgressBar(p_box, width=460, height=14, value=40.0, fill_color_start="#a6e3a1", fill_color_end="#94e2d5", parent_bg="#181825")
        self.progress_accent.pack(fill="x", pady=int(4 * s))

        tk.Label(p_box, text="Circular Gauges / Radial Progress:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(20 * s), int(10 * s)))
        gauge_row = tk.Frame(p_box, bg="#181825")
        gauge_row.pack(fill="x", pady=int(6 * s))

        self.gauge_main = ModernCircularProgress(gauge_row, size=110, value=self._shared_progress, stroke_width=8.0, fill_color="#89b4fa", parent_bg="#181825")
        self.gauge_main.pack(side="left", padx=int(16 * s))

        self.gauge_secondary = ModernCircularProgress(gauge_row, size=110, value=85.0, stroke_width=8.0, fill_color="#cba6f7", unit="°C", parent_bg="#181825")
        self.gauge_secondary.pack(side="left", padx=int(16 * s))

        self.gauge_accent = ModernCircularProgress(gauge_row, size=110, value=42.0, stroke_width=8.0, fill_color="#a6e3a1", unit=" FPS", parent_bg="#181825")
        self.gauge_accent.pack(side="left", padx=int(16 * s))

        # Sliders side
        s_box = tk.Frame(col2, bg="#181825")
        s_box.pack(fill="both", expand=True, padx=int(20 * s), pady=(int(52 * s), int(16 * s)))

        tk.Label(s_box, text="Master Shared Slider (Wires to all gauges):", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(0, int(6 * s)))
        self.slider_master = ModernSlider(s_box, width=460, height=30, value=self._shared_progress, on_change=self._on_slider_change, parent_bg="#181825")
        self.slider_master.pack(fill="x", pady=int(4 * s))

        tk.Label(s_box, text="Wave Speed & Amplitude Slider:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(18 * s), int(6 * s)))
        self.slider_wave = ModernSlider(s_box, width=460, height=30, min_val=10.0, max_val=60.0, value=self._wave_amplitude, on_change=self._on_wave_amp_change, active_track_color="#cba6f7", parent_bg="#181825")
        self.slider_wave.pack(fill="x", pady=int(4 * s))

        tk.Label(s_box, text="Dual-Thumb Min/Max Range Slider:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(18 * s), int(6 * s)))
        self.range_slider = ModernRangeSlider(s_box, width=460, height=30, low_val=25.0, high_val=75.0, parent_bg="#181825")
        self.range_slider.pack(fill="x", pady=int(4 * s))

    # ------------------------------------------------------------------------
    # View 3: Display & Cards
    # ------------------------------------------------------------------------
    def _build_view_display(self):
        s = self._scale
        col1 = ModernCard(self.view_display, title="Badges, Avatars & Tags", width=520, height=600, parent_bg="#11111b")
        col1.pack(side="left", fill="both", expand=True, padx=int(6 * s))

        col2 = ModernCard(self.view_display, title="Collapsible Accordion Cards", width=520, height=600, parent_bg="#11111b")
        col2.pack(side="right", fill="both", expand=True, padx=int(6 * s))

        # Display items
        d_box = tk.Frame(col1, bg="#181825")
        d_box.pack(fill="both", expand=True, padx=int(20 * s), pady=(int(52 * s), int(16 * s)))

        tk.Label(d_box, text="Vector Badges / Status Pills:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(0, int(6 * s)))
        badge_row1 = tk.Frame(d_box, bg="#181825")
        badge_row1.pack(fill="x", pady=int(4 * s))
        ModernBadge(badge_row1, text="Primary", variant="primary", dot=True, parent_bg="#181825").pack(side="left", padx=int(4 * s))
        ModernBadge(badge_row1, text="Success", variant="success", dot=True, parent_bg="#181825").pack(side="left", padx=int(4 * s))
        ModernBadge(badge_row1, text="Warning", variant="warning", dot=True, parent_bg="#181825").pack(side="left", padx=int(4 * s))
        ModernBadge(badge_row1, text="Error", variant="destructive", dot=True, parent_bg="#181825").pack(side="left", padx=int(4 * s))

        tk.Label(d_box, text="Profile Avatars with Status Badges:", font=("DejaVu Sans", int(11 * s), "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w", pady=(int(20 * s), int(8 * s)))
        avatar_row = tk.Frame(d_box, bg="#181825")
        avatar_row.pack(fill="x", pady=int(4 * s))
        ModernAvatar(avatar_row, initials="AG", status="online", size=48, parent_bg="#181825").pack(side="left", padx=int(8 * s))
        ModernAvatar(avatar_row, initials="BL", status="busy", size=48, bg_gradient_start="#a6e3a1", bg_gradient_end="#94e2d5", parent_bg="#181825").pack(side="left", padx=int(8 * s))
        ModernAvatar(avatar_row, initials="TK", status="offline", size=48, bg_gradient_start="#f38ba8", bg_gradient_end="#fab387", parent_bg="#181825").pack(side="left", padx=int(8 * s))

        # Accordions
        a_box = tk.Frame(col2, bg="#181825")
        a_box.pack(fill="both", expand=True, padx=int(16 * s), pady=(int(52 * s), int(16 * s)))

        self.acc1 = ModernAccordion(a_box, title="Zero-Copy Pipeline Architecture", width=460, parent_bg="#181825")
        self.acc1.pack(fill="x", pady=int(6 * s))
        tk.Label(
            self.acc1.content_frame,
            text="Blend2D renders directly to an internal PRGB32 buffer,\nwhich is blitted directly into Tkinter's PhotoImage via\nTk_PhotoPutBlock with 0 Python heap allocations.",
            fg="#a6adc8",
            bg="#181825",
            justify="left",
            font=("DejaVu Sans", int(10 * s)),
        ).pack(anchor="w")

        self.acc2 = ModernAccordion(a_box, title="Antialiasing & Vector Paths", width=460, parent_bg="#181825")
        self.acc2.pack(fill="x", pady=int(6 * s))
        tk.Label(
            self.acc2.content_frame,
            text="Subpixel font rasterization and analytic antialiased\ngeometric primitives eliminate jagged edges on any display DPI.",
            fg="#a6adc8",
            bg="#181825",
            justify="left",
            font=("DejaVu Sans", int(10 * s)),
        ).pack(anchor="w")

        self.acc3 = ModernAccordion(a_box, title="Pure Surface Independence", width=460, parent_bg="#181825")
        self.acc3.pack(fill="x", pady=int(6 * s))
        tk.Label(
            self.acc3.content_frame,
            text="Every widget in this showcase is built strictly from\nscratch using Blend2D's Surface and BlendCanvas, completely\nfree of any TTK or theme dependencies.",
            fg="#a6adc8",
            bg="#181825",
            justify="left",
            font=("DejaVu Sans", int(10 * s)),
        ).pack(anchor="w")

    # ------------------------------------------------------------------------
    # View 4: Live Vector Canvas (Fluid Waves, HUD, 60 FPS)
    # ------------------------------------------------------------------------
    def _build_view_canvas(self):
        s = self._scale
        self.blend_canvas = BlendCanvas(
            self.view_canvas,
            width=int(1100 * s),
            height=int(660 * s),
            bg="#11111b",
            on_draw=self._draw_canvas_scene,
        )
        self.blend_canvas.pack(fill="both", expand=True)

    def _draw_canvas_scene(self, surf: Surface):
        w, h = surf.width, surf.height
        s = self._scale
        t = time.perf_counter() - self._start_time

        # FPS calculation
        self._fps_frames += 1
        now = time.perf_counter()
        if now - self._fps_last_time >= 0.5:
            self._fps = self._fps_frames / (now - self._fps_last_time)
            self._fps_frames = 0
            self._fps_last_time = now

        # Background Soft Radial Glow
        surf.clear("#11111b")
        glow_cx = w * 0.5 + math.cos(t * 0.8) * 150.0 * s
        glow_cy = h * 0.4 + math.sin(t * 0.6) * 100.0 * s
        glow_grad = RadialGradient(glow_cx, glow_cy, 0, glow_cx, glow_cy, max(w, h) * 0.7)
        glow_grad.add_stop(0.0, "#1e1e2e")
        glow_grad.add_stop(0.6, "#181825")
        glow_grad.add_stop(1.0, "#11111b")
        surf.fill_rect(0, 0, w, h, glow_grad)

        # Dynamic Fluid Waves (wired to controls)
        if self._wave_active:
            for layer, col in enumerate(["#89b4fa33", "#cba6f744", "#f38ba855"]):
                p = Path()
                p.move_to(0, h)
                p.line_to(0, h * 0.65)
                steps = 18
                for i in range(steps + 1):
                    x = (w / steps) * i
                    phase = t * (1.8 * self._wave_speed) + layer * 1.5 + (i * 0.4)
                    y = h * (0.65 + layer * 0.06) + math.sin(phase) * (self._wave_amplitude * s)
                    p.line_to(x, y)
                p.line_to(w, h)
                p.close()
                surf.fill_path(p, col)

        # Floating Glassmorphic Cards
        card_w, card_h = 240.0 * s, 150.0 * s
        card1_x = 60.0 * s
        card1_y = 60.0 * s + math.sin(t * 1.2) * 12.0 * s

        card1_grad = LinearGradient(card1_x, card1_y, card1_x + card_w, card1_y + card_h)
        card1_grad.add_stop(0.0, "#313244dd")
        card1_grad.add_stop(1.0, "#1e1e2edd")

        surf.draw_shadow(
            card1_x, card1_y, card_w, card_h,
            self._anim_radius, self._anim_radius,
            blur_radius=self._anim_radius * 1.2,
            shadow_color="#00000088",
            offset_y=8.0 * s,
        )
        surf.fill_rounded_rect(card1_x, card1_y, card_w, card_h, self._anim_radius, self._anim_radius, card1_grad)
        surf.stroke_rounded_rect(card1_x, card1_y, card_w, card_h, self._anim_radius, self._anim_radius, "#89b4fa66", 1.5 * s)

        surf.draw_text("Vector Card Alpha", card1_x + 20 * s, card1_y + 36 * s, font_size=15 * s, color="#cdd6f4")
        surf.draw_text("Anti-aliased subpixel text", card1_x + 20 * s, card1_y + 64 * s, font_size=12 * s, color="#a6adc8")
        surf.fill_circle(card1_x + 190 * s, card1_y + 110 * s, 14 * s, "#a6e3a1")

        # Card 2
        card2_x = 340.0 * s
        card2_y = 100.0 * s + math.cos(t * 1.4) * 12.0 * s
        surf.draw_card(
            card2_x, card2_y, card_w, card_h,
            rx=self._anim_radius, ry=self._anim_radius,
            bg_color="#181825ee",
            border_color="#cba6f788",
            border_width=1.5 * s,
            shadow_blur=self._anim_radius * 1.2,
            shadow_color="#00000088",
            shadow_offset_y=8.0 * s,
        )
        surf.draw_text("Zero-Copy Blit", card2_x + 20 * s, card2_y + 36 * s, font_size=15 * s, color="#cdd6f4")
        surf.draw_text("Tk_PhotoPutBlock Direct", card2_x + 20 * s, card2_y + 64 * s, font_size=12 * s, color="#a6adc8")
        surf.fill_rounded_rect(card2_x + 20 * s, card2_y + 100 * s, 140 * s, 10 * s, 5 * s, 5 * s, "#cba6f7")

        # HUD / Status Overlay
        hud_w, hud_h = 160.0 * s, 48.0 * s
        hud_x = w - hud_w - 20.0 * s
        hud_y = 20.0 * s

        surf.draw_card(
            hud_x, hud_y, hud_w, hud_h,
            rx=12 * s, ry=12 * s,
            bg_color="#181825cc",
            border_color="#ffffff22",
            border_width=1.0,
            shadow_blur=8.0 * s,
            shadow_color="#00000044",
        )
        surf.draw_text(
            f"{self._fps:.1f} FPS",
            hud_x + hud_w / 2.0,
            hud_y + hud_h / 2.0 + 5.0 * s,
            font_size=16 * s,
            color="#a6e3a1",
            align="center",
        )

    # ------------------------------------------------------------------------
    # State Synchronization Callbacks
    # ------------------------------------------------------------------------
    def _inc_progress(self):
        self._shared_progress = (self._shared_progress + 15.0) % 100.0
        self._sync_progress_widgets()

    def _reset_progress(self):
        self._shared_progress = 0.0
        self._sync_progress_widgets()

    def _on_slider_change(self, val: float):
        self._shared_progress = val
        self._sync_progress_widgets()

    def _on_stepper_change(self, val: int):
        self._shared_progress = float(val)
        self._sync_progress_widgets()

    def _sync_progress_widgets(self):
        val = self._shared_progress
        self.progress_linear.value = val
        self.gauge_main.value = val
        self.spinbox.value = int(val)
        self.slider_master.value = val

    def _on_wave_amp_change(self, val: float):
        self._wave_amplitude = val

    def _on_wave_toggle(self, state: bool):
        self._wave_active = state

    def _tick_anim(self):
        if hasattr(self, "blend_canvas") and self.blend_canvas.winfo_exists():
            self.blend_canvas.redraw()
        self.root.after(16, self._tick_anim)  # ~60 FPS


def main():
    root = tk.Tk()
    app = ExtendedCanvasShowcaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
