#!/usr/bin/env python3
"""
tkblend Showcase: Unified Showcase Hub.
The flagship launcher for all tkblend example applications.
Features:
  - Sleek modern sidebar navigation
  - Embedded live previews of all showcase apps
  - One-click launcher for detached standalone top-level windows
  - Global runtime theme switching across 13+ built-in presets
  - Process-level High-DPI scaling controls
"""

from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from typing import Optional, Dict, Any, Type

import tkblend as tb
from tkblend import (
    Card,
    Frame,
    Button,
    Badge,
    Avatar,
    OptionMenu,
    SegmentedButton,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    ScalingTracker,
)

import os
examples_dir = os.path.dirname(os.path.abspath(__file__))
if examples_dir not in sys.path:
    sys.path.insert(0, examples_dir)

# Import embedded showcase views
from analytics_dashboard import AnalyticsDashboard
from widget_gallery import WidgetGallery
from canvas_studio import CanvasStudio
from realtime_visualizer import RealtimeVisualizer
from custom_widget_cookbook import CustomWidgetCookbook
from ctk_showcase import CTKBridgeInfoFrame


SHOWCASE_MODULES = [
    {
        "id": "dashboard",
        "title": "Analytics Dashboard",
        "desc": "Real-time system telemetry, circular gauges, sparklines & live Bézier charts",
        "tag": "SaaS / Metrics",
        "script": "analytics_dashboard.py",
        "class": AnalyticsDashboard,
    },
    {
        "id": "gallery",
        "title": "Widget Catalog",
        "desc": "Complete interactive catalog of 20+ zero-TTK vector components",
        "tag": "Components",
        "script": "widget_gallery.py",
        "class": WidgetGallery,
    },
    {
        "id": "canvas",
        "title": "Canvas & Vector Studio",
        "desc": "Bézier paths, multi-stop gradients, composition blend modes & soft shadows",
        "tag": "2D Graphics",
        "script": "canvas_studio.py",
        "class": CanvasStudio,
    },
    {
        "id": "visualizer",
        "title": "60 FPS Visualizer",
        "desc": "High-speed particle physics swarm, audio spectrum & harmonic Lissajous",
        "tag": "Performance",
        "script": "realtime_visualizer.py",
        "class": RealtimeVisualizer,
    },
    {
        "id": "cookbook",
        "title": "Custom Widget Cookbook",
        "desc": "Architecture guide for building custom vector widgets (Radar, Speedo, Wizard)",
        "tag": "Developer Guide",
        "script": "custom_widget_cookbook.py",
        "class": CustomWidgetCookbook,
    },
    {
        "id": "ctk",
        "title": "CustomTkinter Bridge",
        "desc": "Drop-in subpixel anti-aliased vector acceleration for CustomTkinter apps",
        "tag": "Integration",
        "script": "ctk_showcase.py",
        "class": CTKBridgeInfoFrame,
    },
]


class ShowcaseHub(tk.Frame):
    """Unified flagship launcher and embedded preview host for tkblend."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._current_app_id = "dashboard"
        self._active_widget: Optional[tk.Widget] = None
        self._nav_buttons: Dict[str, Button] = {}

        self._build_ui()
        self._load_view(self._current_app_id)

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Left Sidebar Navigation Card
        self._sidebar = Card(self, width=270, height=720, rx=0, ry=0, elevation=4)
        self._sidebar.pack(side="left", fill="y")
        sb_body = self._sidebar.body

        # App Brand Header
        brand_box = tk.Frame(sb_body, background=self._sidebar.bg_color)
        brand_box.pack(fill="x", padx=16, pady=(20, 16))

        Avatar(brand_box, text="TB", size=40, bg_color=pal.primary).pack(side="left")

        title_col = tk.Frame(brand_box, background=self._sidebar.bg_color)
        title_col.pack(side="left", padx=10)

        tk.Label(title_col, text="tkblend", font=("Segoe UI", 15, "bold"), fg=pal.fg, bg=self._sidebar.bg_color).pack(anchor="w")
        Badge(title_col, text="v0.3.0 Vector", color=pal.accent, height=18).pack(anchor="w", pady=(2, 0))

        # Nav Divider
        tk.Frame(sb_body, height=1, background=pal.surface_border).pack(fill="x", padx=16, pady=8)

        # Nav Section Label
        tk.Label(sb_body, text="SHOWCASE APPLICATIONS", font=("Segoe UI", 8, "bold"), fg=pal.fg_subtle, bg=self._sidebar.bg_color).pack(anchor="w", padx=18, pady=(4, 8))

        # Nav Buttons List
        for mod in SHOWCASE_MODULES:
            m_id = mod["id"]
            btn = Button(
                sb_body,
                text=mod["title"],
                width=236,
                height=36,
                bootstyle="outline-primary" if m_id == self._current_app_id else "secondary",
                command=lambda mid=m_id: self._load_view(mid),
            )
            btn.pack(fill="x", padx=16, pady=3)
            self._nav_buttons[m_id] = btn

        # Bottom Sidebar Controls
        tk.Frame(sb_body, background=self._sidebar.bg_color).pack(fill="both", expand=True)

        bot_box = tk.Frame(sb_body, background=self._sidebar.bg_color)
        bot_box.pack(fill="x", padx=16, pady=(0, 20))

        tk.Label(bot_box, text="Theme Palette:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=self._sidebar.bg_color).pack(anchor="w", pady=(0, 4))
        self._theme_opt = OptionMenu(
            bot_box,
            values=list(get_available_themes()),
            default_value="dark",
            command=self._on_theme_changed,
            width=236,
            height=32,
        )
        self._theme_opt.pack(fill="x", pady=(0, 10))

        # Pop-out Detached Window Button
        Button(
            bot_box,
            text="⤢ Pop Out Standalone",
            width=236,
            height=32,
            bootstyle="primary",
            command=self._launch_detached_window,
        ).pack(fill="x")

        # Right Content Viewport Area
        self._viewport = tk.Frame(self, background=pal.bg)
        self._viewport.pack(side="right", fill="both", expand=True)

    def _load_view(self, app_id: str) -> None:
        self._current_app_id = app_id

        # Update button highlights
        for mid, btn in self._nav_buttons.items():
            btn.set_bootstyle("primary" if mid == app_id else "secondary")

        # Destroy active embedded view
        if self._active_widget is not None:
            try:
                self._active_widget.destroy()
            except Exception:
                pass
            self._active_widget = None

        # Instantiate target view
        target_mod = next((m for m in SHOWCASE_MODULES if m["id"] == app_id), SHOWCASE_MODULES[0])
        cls = target_mod["class"]
        self._active_widget = cls(self._viewport)
        self._active_widget.pack(fill="both", expand=True)

    def _launch_detached_window(self) -> None:
        target_mod = next((m for m in SHOWCASE_MODULES if m["id"] == self._current_app_id), None)
        if target_mod:
            script_path = f"examples/{target_mod['script']}"
            subprocess.Popen([sys.executable, script_path])

    def _on_theme_changed(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        self._viewport.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg)


def main():
    root = tk.Tk()
    root.title("tkblend Showcase Hub")
    root.geometry("1160x780")
    root.minsize(980, 640)

    ScalingTracker.activate_high_dpi_awareness()
    set_theme("dark")

    hub = ShowcaseHub(root)
    hub.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
