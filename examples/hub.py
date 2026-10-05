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
    add_theme_listener,
    remove_theme_listener,
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
        self._in_theme_update = False

        self._build_ui()
        self._load_app(0)

        # Listen for global theme changes from inside embedded views or external callers
        self._theme_listener = self._on_global_theme_changed
        add_theme_listener(self._theme_listener)
        self.bind("<Destroy>", self._on_hub_destroy, add="+")

    def _on_hub_destroy(self, _event: tk.Event) -> None:
        try:
            remove_theme_listener(self._theme_listener)
        except Exception:
            pass

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Header Bar Card
        self._header_card = Card(self, height=64, corner_radius=10)
        self._header_card.pack(fill="x", padx=14, pady=(14, 8))

        # Brand / Logo
        self._logo_box = tk.Frame(self._header_card, bg=pal.card_bg)
        self._logo_box.pack(side="left", padx=14, pady=10)

        self._avatar = Avatar(self._logo_box, text="TB", size=38)
        self._avatar.pack(side="left", padx=(0, 10))

        self._title_box = tk.Frame(self._logo_box, bg=pal.card_bg)
        self._title_box.pack(side="left")

        self._title_lbl = tk.Label(
            self._title_box,
            text="tkblend Showcase Hub",
            font=("sans-serif", 14, "bold"),
            bg=pal.card_bg,
            fg=pal.fg,
        )
        self._title_lbl.pack(anchor="w")

        self._subtitle_lbl = tk.Label(
            self._title_box,
            text="Pure Blend2D C++ Vector Graphics Engine & Modern Controls",
            font=("sans-serif", 9),
            bg=pal.card_bg,
            fg=pal.text_muted,
        )
        self._subtitle_lbl.pack(anchor="w", pady=(1, 0))

        # Theme Selector
        self._theme_opt = OptionMenu(
            self._header_card,
            values=get_available_themes(),
            default_value=pal.name,
            command=self._on_theme_change,
            width=130,
            height=30,
        )
        self._theme_opt.pack(side="right", padx=14)

        # Launch Standalone Window Button
        self._btn_launch = Button(
            self._header_card,
            text="🚀 Launch in Detached Window",
            width=210,
            height=30,
            command=self._launch_standalone,
        )
        self._btn_launch.pack(side="right", padx=6)

        # Main Central Workspace
        self._workspace = tk.Frame(self, bg=pal.bg)
        self._workspace.pack(fill="both", expand=True, padx=14, pady=6)

        # 1. Left Sidebar: App Navigation List
        self._sidebar_card = Card(self._workspace, width=280, corner_radius=10)
        self._sidebar_card.pack(side="left", fill="y", padx=(0, 6))

        self._sidebar_hdr = tk.Label(
            self._sidebar_card,
            text="SHOWCASE APPLICATIONS",
            font=("sans-serif", 9, "bold"),
            bg=pal.card_bg,
            fg=pal.text_muted,
        )
        self._sidebar_hdr.pack(anchor="w", padx=14, pady=(14, 8))

        self._sidebar_buttons.clear()
        for i, app_info in enumerate(SHOWCASE_APPS):
            btn = Button(
                self._sidebar_card,
                text=f"{app_info['title']}",
                height=34,
                width=245,
                bg_color=pal.primary if i == 0 else pal.card_bg,
                fg_color=pal.primary_fg if i == 0 and hasattr(pal, "primary_fg") else pal.fg,
                command=lambda idx=i: self._load_app(idx),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self._sidebar_buttons.append(btn)

        # Sidebar footer info
        self._footer_box = tk.Frame(self._sidebar_card, bg=pal.card_bg)
        self._footer_box.pack(side="bottom", fill="x", padx=14, pady=14)

        scale_val = ScalingTracker.get_scaling_factor(self)
        self._badge_dpi = Badge(self._footer_box, text=f"DPI Scale: {scale_val:.2f}x", variant="outline")
        self._badge_dpi.pack(side="left")
        self._badge_zero = Badge(self._footer_box, text="Zero TTK", variant="success")
        self._badge_zero.pack(side="right")

        # 2. Right Column: Embedded Live App Viewport Card
        self._view_card = Card(self._workspace, corner_radius=10)
        self._view_card.pack(side="right", fill="both", expand=True, padx=(6, 0))

        self._view_container = tk.Frame(self._view_card, bg=pal.card_bg)
        self._view_container.pack(fill="both", expand=True, padx=4, pady=4)

        cascade_bg_to_children(self, pal.bg, palette=pal)

    def _load_app(self, app_idx: int) -> None:
        self._active_app_idx = app_idx
        app_info = SHOWCASE_APPS[app_idx]
        pal = get_theme()

        # Update sidebar button highlights
        for i, btn in enumerate(self._sidebar_buttons):
            if i == app_idx:
                btn.configure(
                    bg_color=pal.primary,
                    fg_color=pal.primary_fg if hasattr(pal, "primary_fg") else "#FFFFFF",
                )
            else:
                btn.configure(
                    bg_color=pal.card_bg,
                    fg_color=pal.fg,
                )

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
                bg=pal.card_bg,
            )
            err_lbl.pack(padx=20, pady=20)
            self._current_embedded_view = err_lbl

    def _launch_standalone(self) -> None:
        app_info = SHOWCASE_APPS[self._active_app_idx]
        script_name = app_info["script"]
        script_path = os.path.join(examples_dir, script_name)

        if os.path.exists(script_path):
            subprocess.Popen([sys.executable, script_path])

    def _on_global_theme_changed(self, pal: Palette) -> None:
        if self._in_theme_update or not self.winfo_exists():
            return
        self._apply_theme_to_hub(pal)

    def _on_theme_change(self, theme_name: str) -> None:
        if self._in_theme_update:
            return
        self._in_theme_update = True
        try:
            set_theme(theme_name)
            pal = get_theme()
            self._apply_theme_to_hub(pal)
        finally:
            self._in_theme_update = False

    def _apply_theme_to_hub(self, pal: Palette) -> None:
        self.configure(background=pal.bg)
        if hasattr(self, "_workspace") and self._workspace.winfo_exists():
            self._workspace.configure(background=pal.bg)

        # Update frame backgrounds
        for frame_attr in ("_logo_box", "_title_box", "_footer_box", "_view_container"):
            if hasattr(self, frame_attr):
                f = getattr(self, frame_attr)
                if f and f.winfo_exists():
                    f.configure(bg=pal.card_bg)

        # Update labels
        if hasattr(self, "_title_lbl") and self._title_lbl.winfo_exists():
            self._title_lbl.configure(bg=pal.card_bg, fg=pal.fg)
        if hasattr(self, "_subtitle_lbl") and self._subtitle_lbl.winfo_exists():
            self._subtitle_lbl.configure(bg=pal.card_bg, fg=pal.text_muted)
        if hasattr(self, "_sidebar_hdr") and self._sidebar_hdr.winfo_exists():
            self._sidebar_hdr.configure(bg=pal.card_bg, fg=pal.text_muted)

        # Synchronize theme option menu
        if hasattr(self, "_theme_opt") and self._theme_opt.winfo_exists():
            if self._theme_opt.get().lower() != pal.name.lower():
                self._theme_opt.set(pal.name)

        # Cascade colors to cards and children
        if hasattr(self, "_header_card") and self._header_card.winfo_exists():
            self._header_card.request_redraw()
            cascade_bg_to_children(self._header_card, pal.card_bg, palette=pal)

        if hasattr(self, "_sidebar_card") and self._sidebar_card.winfo_exists():
            self._sidebar_card.request_redraw()
            cascade_bg_to_children(self._sidebar_card, pal.card_bg, palette=pal)

        if hasattr(self, "_view_card") and self._view_card.winfo_exists():
            self._view_card.request_redraw()
            cascade_bg_to_children(self._view_card, pal.card_bg, palette=pal)

        # Reload embedded app and refresh sidebar buttons
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

