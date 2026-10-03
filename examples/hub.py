#!/usr/bin/env python3
"""
tkblend Showcase: Unified Showcase Hub.
The flagship launcher for all tkblend example applications.
Features:
  - Sleek modern sidebar navigation with app badges and tags
  - Embedded live previews of all showcase applications
  - One-click launcher for detached standalone top-level windows
  - Global runtime theme switching across 13+ built-in presets
  - Process-level High-DPI scaling controls and telemetry
"""

from __future__ import annotations

import os
import sys
import subprocess
import tkinter as tk
from typing import Optional, Dict, Any, Type, List

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

examples_dir = os.path.dirname(os.path.abspath(__file__))
if examples_dir not in sys.path:
    sys.path.insert(0, examples_dir)

# Import embedded showcase views
from analytics_dashboard import AnalyticsDashboard
from multimedia_dashboard import MultimediaDashboard
from file_explorer import FileExplorerApp
from realtime_visualizer import RealtimeVisualizer
from custom_widget_cookbook import CustomWidgetCookbook
from icons_and_typography_demo import IconsAndTypographyDemo
from canvas_studio import CanvasStudio


SHOWCASE_APPS = [
    {
        "id": "analytics",
        "title": "Analytics Dashboard",
        "desc": "Telemetry, circular gauges, sparklines & live Bézier charts",
        "tag": "SaaS / Metrics",
        "script": "analytics_dashboard.py",
        "icon": "chart-line",
        "class": AnalyticsDashboard,
    },
    {
        "id": "multimedia",
        "title": "Multimedia Studio",
        "desc": "Real-time audio visualizer, VU meters, sliders & track table",
        "tag": "Audio / DSP",
        "script": "multimedia_dashboard.py",
        "icon": "headphones",
        "class": MultimediaDashboard,
    },
    {
        "id": "file_explorer",
        "title": "File Explorer",
        "desc": "Vector file manager with breadcrumbs, table & preview",
        "tag": "Productivity",
        "script": "file_explorer.py",
        "icon": "folder",
        "class": FileExplorerApp,
    },
    {
        "id": "visualizer",
        "title": "60 FPS Engine Lab",
        "desc": "Particle physics swarm, neon spectrum & Lissajous curves",
        "tag": "Physics / 2D",
        "script": "realtime_visualizer.py",
        "icon": "bolt",
        "class": RealtimeVisualizer,
    },
    {
        "id": "cookbook",
        "title": "Widget Cookbook",
        "desc": "Spider radar chart, analog speedometer & multi-step bar",
        "tag": "Developer Reference",
        "script": "custom_widget_cookbook.py",
        "icon": "flask",
        "class": CustomWidgetCookbook,
    },
    {
        "id": "typography",
        "title": "Typography & Icons",
        "desc": "Font Awesome 6, Lucide vector icons & typography scaling",
        "tag": "Design System",
        "script": "icons_and_typography_demo.py",
        "icon": "font",
        "class": IconsAndTypographyDemo,
    },
    {
        "id": "canvas_studio",
        "title": "Canvas Studio",
        "desc": "Interactive 2D path vector editor and shader canvas",
        "tag": "2D Vector Studio",
        "script": "canvas_studio.py",
        "icon": "palette",
        "class": CanvasStudio,
    },
]


class ShowcaseHub(tk.Frame):
    """Master flagship launcher for tkblend."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._active_app_idx = 0
        self._current_embedded_view: Optional[tk.Widget] = None
        self._sidebar_buttons: List[Button] = []

        self._build_ui()
        self._load_app(0)

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Header Bar Card
        header = Card(self, height=64, corner_radius=10, bg_color=pal.card_bg)
        header.pack(fill="x", padx=14, pady=(14, 8))

        # Brand / Logo
        logo_box = tk.Frame(header, bg=header.bg_color)
        logo_box.pack(side="left", padx=14, pady=10)

        Avatar(logo_box, text="TB", size=38, bg_color=pal.primary).pack(side="left", padx=(0, 10))

        title_box = tk.Frame(logo_box, bg=header.bg_color)
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="tkblend Showcase Hub",
            font=("sans-serif", 14, "bold"),
            bg=header.bg_color,
            fg=pal.fg,
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Pure Blend2D C++ Vector Graphics Engine & Modern Controls",
            font=("sans-serif", 9),
            bg=header.bg_color,
            fg=pal.text_muted,
        ).pack(anchor="w", pady=(1, 0))

        # Theme Selector
        self._theme_opt = OptionMenu(
            header,
            values=get_available_themes(),
            default_value="dark",
            command=self._on_theme_change,
            width=130,
            height=30,
        )
        self._theme_opt.pack(side="right", padx=14)

        # Launch Standalone Window Button
        btn_launch = Button(
            header,
            text="🚀 Launch in Detached Window",
            width=210,
            height=30,
            command=self._launch_standalone,
        )
        btn_launch.pack(side="right", padx=6)

        # Main Central Workspace
        workspace = tk.Frame(self, bg=pal.bg)
        workspace.pack(fill="both", expand=True, padx=14, pady=6)

        # 1. Left Sidebar: App Navigation List
        sidebar = Card(workspace, width=280, corner_radius=10, bg_color=pal.card_bg)
        sidebar.pack(side="left", fill="y", padx=(0, 6))

        tk.Label(
            sidebar,
            text="SHOWCASE APPLICATIONS",
            font=("sans-serif", 9, "bold"),
            bg=sidebar.bg_color,
            fg=pal.text_muted,
        ).pack(anchor="w", padx=14, pady=(14, 8))

        self._sidebar_buttons.clear()
        for i, app_info in enumerate(SHOWCASE_APPS):
            btn = Button(
                sidebar,
                text=f"{app_info['title']}",
                height=34,
                width=245,
                bg_color=pal.primary if i == 0 else sidebar.bg_color,
                command=lambda idx=i: self._load_app(idx),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self._sidebar_buttons.append(btn)

        # Sidebar footer info
        footer_box = tk.Frame(sidebar, bg=sidebar.bg_color)
        footer_box.pack(side="bottom", fill="x", padx=14, pady=14)

        scale_val = ScalingTracker.get_scaling_factor(self)
        Badge(footer_box, text=f"DPI Scale: {scale_val:.2f}x", variant="outline").pack(side="left")
        Badge(footer_box, text="Zero TTK", variant="success").pack(side="right")

        # 2. Right Column: Embedded Live App Viewport Card
        self._view_card = Card(workspace, corner_radius=10, bg_color=pal.card_bg)
        self._view_card.pack(side="right", fill="both", expand=True, padx=(6, 0))

        self._view_container = tk.Frame(self._view_card, bg=self._view_card.bg_color)
        self._view_container.pack(fill="both", expand=True, padx=4, pady=4)

        cascade_bg_to_children(self, pal.bg, palette=pal)

    def _load_app(self, app_idx: int) -> None:
        self._active_app_idx = app_idx
        app_info = SHOWCASE_APPS[app_idx]
        pal = get_theme()

        # Update sidebar button highlight
        for i, btn in enumerate(self._sidebar_buttons):
            if i == app_idx:
                btn.configure(bg_color=pal.primary, fg_color="#FFFFFF")
            else:
                btn.configure(bg_color=pal.card_bg, fg_color=pal.fg)

        # Teardown previous embedded view
        if self._current_embedded_view is not None:
            try:
                self._current_embedded_view.destroy()
            except Exception:
                pass
            self._current_embedded_view = None

        # Instantiate new embedded view
        view_cls = app_info["class"]
        try:
            self._current_embedded_view = view_cls(self._view_container)
            self._current_embedded_view.pack(fill="both", expand=True)
            cascade_bg_to_children(self._current_embedded_view, pal.bg, palette=pal)
        except Exception as err:
            err_lbl = tk.Label(
                self._view_container,
                text=f"Error loading embedded view: {err}",
                font=("sans-serif", 11),
                fg="red",
                bg=self._view_card.bg_color,
            )
            err_lbl.pack(padx=20, pady=20)
            self._current_embedded_view = err_lbl

    def _launch_standalone(self) -> None:
        app_info = SHOWCASE_APPS[self._active_app_idx]
        script_name = app_info["script"]
        script_path = os.path.join(examples_dir, script_name)

        if os.path.exists(script_path):
            subprocess.Popen([sys.executable, script_path])

    def _on_theme_change(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg, palette=pal)
        # Refresh current app with new theme
        self._load_app(self._active_app_idx)


def main():
    root = tk.Tk()
    root.title("tkblend - Unified Showcase Hub")
    root.geometry("1180x780")
    root.minsize(980, 640)

    app = ShowcaseHub(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
