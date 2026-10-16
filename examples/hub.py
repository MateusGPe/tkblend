#!/usr/bin/env python3
"""
tkblend Showcase: Unified Showcase Hub.
The flagship launcher for all tkblend example applications.
Features:
  - Sleek modern sidebar navigation with app badges and tags
  - Embedded live previews of all frame-based showcase applications
  - Direct process launcher for dedicated standalone full-window showcase apps
  - Global runtime theme switching across all built-in presets
  - High-DPI coordinate scaling and responsive layouts
"""

from __future__ import annotations

import os
import sys
import subprocess
import tkinter as tk
from pathlib import Path as FilePath
from typing import Optional, Dict, Any, Type, List

# Ensure project root is in sys.path
PROJECT_ROOT = FilePath(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

EXAMPLES_DIR = FilePath(__file__).resolve().parent
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))

import tkblend as tb
from tkblend import (
    Card,
    Button,
    Badge,
    OptionMenu,
    get_theme,
    set_theme,
    get_available_themes,
    add_theme_listener,
    remove_theme_listener,
    cascade_bg_to_children,
    ScalingTracker,
)

# Lazy-loaded embedded views
_EMBEDDED_CLASSES: Dict[str, Any] = {}

def get_app_class(app_id: str):
    if app_id not in _EMBEDDED_CLASSES:
        if app_id == "analytics":
            from analytics_dashboard import AnalyticsDashboard
            _EMBEDDED_CLASSES[app_id] = AnalyticsDashboard
        elif app_id == "multimedia":
            from multimedia_dashboard import MultimediaDashboard
            _EMBEDDED_CLASSES[app_id] = MultimediaDashboard
        elif app_id == "file_explorer":
            from file_explorer import FileExplorerApp
            _EMBEDDED_CLASSES[app_id] = FileExplorerApp
        elif app_id == "visualizer":
            from realtime_visualizer import RealtimeVisualizer
            _EMBEDDED_CLASSES[app_id] = RealtimeVisualizer
        elif app_id == "cookbook":
            from custom_widget_cookbook import CustomWidgetCookbook
            _EMBEDDED_CLASSES[app_id] = CustomWidgetCookbook
        elif app_id == "typography":
            from icons_and_typography_demo import IconsAndTypographyDemo
            _EMBEDDED_CLASSES[app_id] = IconsAndTypographyDemo
        elif app_id == "canvas_studio":
            from canvas_studio import CanvasStudio
            _EMBEDDED_CLASSES[app_id] = CanvasStudio
    return _EMBEDDED_CLASSES.get(app_id)


SHOWCASE_APPS = [
    {
        "id": "analytics",
        "title": "Analytics Dashboard",
        "desc": "Telemetry, circular gauges, sparklines & live Bézier charts",
        "tag": "SaaS / Metrics",
        "script": "analytics_dashboard.py",
        "embeddable": True,
    },
    {
        "id": "multimedia",
        "title": "Multimedia Studio",
        "desc": "Real-time audio visualizer, VU meters, sliders & track table",
        "tag": "Audio / DSP",
        "script": "multimedia_dashboard.py",
        "embeddable": True,
    },
    {
        "id": "file_explorer",
        "title": "File Explorer",
        "desc": "Vector file manager with breadcrumbs, table & preview",
        "tag": "Productivity",
        "script": "file_explorer.py",
        "embeddable": True,
    },
    {
        "id": "visualizer",
        "title": "60 FPS Engine Lab",
        "desc": "Particle physics swarm, neon spectrum & Lissajous curves",
        "tag": "Physics / 2D",
        "script": "realtime_visualizer.py",
        "embeddable": True,
    },
    {
        "id": "canvas_studio",
        "title": "Canvas Studio",
        "desc": "Interactive 2D path vector editor and shader canvas",
        "tag": "2D Vector Studio",
        "script": "canvas_studio.py",
        "embeddable": True,
    },
    {
        "id": "cookbook",
        "title": "Widget Cookbook",
        "desc": "Spider radar chart, analog speedometer & multi-step bar",
        "tag": "Developer Reference",
        "script": "custom_widget_cookbook.py",
        "embeddable": True,
    },
    {
        "id": "typography",
        "title": "Typography & Icons",
        "desc": "Font Awesome 6, Lucide vector icons & typography scaling",
        "tag": "Design System",
        "script": "icons_and_typography_demo.py",
        "embeddable": True,
    },
    {
        "id": "showcase",
        "title": "Master Widget Showcase",
        "desc": "Material Design 3 vector widgets matrix with hot-reloading",
        "tag": "Widget Catalog",
        "script": "showcase.py",
        "embeddable": False,
    },
    {
        "id": "table_demo",
        "title": "Vector Table Demo",
        "desc": "Resizable columns, click-to-sort, virtualized rows & scrollbars",
        "tag": "Data Grid",
        "script": "table_demo.py",
        "embeddable": False,
    },
    {
        "id": "api_inspector",
        "title": "API Inspector & REST",
        "desc": "Threaded HTTP client, status code badges, JSON viewer & history",
        "tag": "Desktop App",
        "script": "api_inspector.py",
        "embeddable": False,
    },
    {
        "id": "gradient_widgets",
        "title": "Gradient Widgets",
        "desc": "Multi-stop linear/radial gradients, range sliders & drop shadows",
        "tag": "Styling / Effects",
        "script": "gradient_widgets.py",
        "embeddable": False,
    },
    {
        "id": "cinematic_theme",
        "title": "Cinematic Theme Demo",
        "desc": "Peacock Teal and Warm Amber palette across vector cards and pills",
        "tag": "Theming",
        "script": "cinematic_theme_demo.py",
        "embeddable": False,
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
        self._header_card = Card(self, height=68)
        self._header_card.pack(fill="x", padx=16, pady=(16, 8))

        hdr_inner = tk.Frame(self._header_card, bg=pal.card_bg)
        hdr_inner.pack(fill="both", expand=True, padx=18, pady=(10, 14))

        # Brand / Title
        title_box = tk.Frame(hdr_inner, bg=pal.card_bg)
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="⚡ tkblend Showcase Hub",
            font=("sans-serif", 15, "bold"),
            bg=pal.card_bg,
            fg=pal.fg,
        ).pack(side="left")

        Badge(title_box, text="FLAGSHIP", variant="primary").pack(side="left", padx=10)

        tk.Label(
            title_box,
            text="Pure Blend2D C++ Vector Graphics Engine & Modern Controls",
            font=("sans-serif", 9),
            bg=pal.card_bg,
            fg=pal.text_muted,
        ).pack(side="left", padx=4)

        # Global Theme Selector
        self._theme_opt = OptionMenu(
            hdr_inner,
            values=sorted(get_available_themes()),
            current_value=pal.name,
            command=self._on_theme_change,
            width=140,
            height=30,
        )
        self._theme_opt.pack(side="right")

        # Main Workspace: Left Sidebar + Right Live Viewport Card
        self._workspace = tk.Frame(self, bg=pal.bg)
        self._workspace.pack(fill="both", expand=True, padx=16, pady=6)

        # Sidebar Card
        self._sidebar_card = Card(self._workspace, width=280)
        self._sidebar_card.pack(side="left", fill="y", padx=(0, 8))

        self._sidebar_inner = tk.Frame(self._sidebar_card, bg=pal.card_bg)
        self._sidebar_inner.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(
            self._sidebar_inner,
            text="Applications & Demos",
            font=("sans-serif", 10, "bold"),
            bg=pal.card_bg,
            fg=pal.text_muted,
        ).pack(anchor="w", pady=(2, 6))

        # Sidebar App Buttons
        self._sidebar_canvas = tk.Canvas(self._sidebar_inner, bg=pal.card_bg, highlightthickness=0, bd=0)
        self._sidebar_scroll_frame = tk.Frame(self._sidebar_canvas, bg=pal.card_bg)
        
        self._sidebar_canvas.pack(side="left", fill="both", expand=True)
        self._sidebar_win_id = self._sidebar_canvas.create_window((0, 0), window=self._sidebar_scroll_frame, anchor="nw")
        
        self._sidebar_scroll_frame.bind("<Configure>", lambda e: self._sidebar_canvas.configure(scrollregion=self._sidebar_canvas.bbox("all")))
        self._sidebar_canvas.bind("<Configure>", lambda e: self._sidebar_canvas.itemconfig(self._sidebar_win_id, width=e.width))

        self._sidebar_buttons.clear()
        for idx, app_info in enumerate(SHOWCASE_APPS):
            btn = Button(
                self._sidebar_scroll_frame,
                text=f"{app_info['title']}",
                variant="primary" if idx == 0 else "default",
                height=32,
                command=lambda i=idx: self._select_app(i),
            )
            btn.pack(fill="x", pady=2)
            self._sidebar_buttons.append(btn)

        # Right Live Viewport Card
        self._view_card = Card(self._workspace)
        self._view_card.pack(side="right", fill="both", expand=True)

        self._view_inner = tk.Frame(self._view_card, bg=pal.card_bg)
        self._view_inner.pack(fill="both", expand=True, padx=18, pady=16)

        # Action bar in view card (Header with Launch button)
        self._view_topbar = tk.Frame(self._view_inner, bg=pal.card_bg)
        self._view_topbar.pack(fill="x", pady=(2, 8))

        self._active_app_title = tk.Label(
            self._view_topbar,
            text="",
            font=("sans-serif", 13, "bold"),
            bg=pal.card_bg,
            fg=pal.fg,
        )
        self._active_app_title.pack(side="left")

        self._active_app_tag = Badge(self._view_topbar, text="", variant="secondary")
        self._active_app_tag.pack(side="left", padx=8)

        self._btn_launch_external = Button(
            self._view_topbar,
            text="🚀 Launch Standalone Window",
            width=230,
            height=32,
            auto_fit=True,
            command=self._launch_current_standalone,
        )
        self._btn_launch_external.pack(side="right")

        # Container where the active embedded view is mounted
        self._view_container = tk.Frame(self._view_inner, bg=pal.card_bg)
        self._view_container.pack(fill="both", expand=True)

        cascade_bg_to_children(self, pal.bg, palette=pal)

    def _select_app(self, idx: int) -> None:
        self._active_app_idx = idx
        for i, btn in enumerate(self._sidebar_buttons):
            btn.variant = "primary" if i == idx else "default"
        self._load_app(idx)

    def _load_app(self, idx: int) -> None:
        if idx < 0 or idx >= len(SHOWCASE_APPS):
            return

        app_info = SHOWCASE_APPS[idx]
        self._active_app_title.configure(text=app_info["title"])
        self._active_app_tag.text = app_info["tag"]

        # Teardown current embedded view
        if self._current_embedded_view is not None:
            try:
                self._current_embedded_view.destroy()
            except Exception:
                pass
            self._current_embedded_view = None

        pal = get_theme()

        if app_info["embeddable"]:
            app_cls = get_app_class(app_info["id"])
            if app_cls is not None:
                try:
                    view = app_cls(self._view_container)
                    view.pack(fill="both", expand=True)
                    self._current_embedded_view = view
                    cascade_bg_to_children(view, pal.card_bg, palette=pal)
                except Exception as err:
                    err_lbl = tk.Label(
                        self._view_container,
                        text=f"Error embedding demo: {err}",
                        font=("sans-serif", 11),
                        bg=pal.card_bg,
                        fg=pal.danger,
                    )
                    err_lbl.pack(padx=20, pady=20)
                    self._current_embedded_view = err_lbl
        else:
            # Standalone launcher landing card
            landing = tk.Frame(self._view_container, bg=pal.card_bg)
            landing.pack(fill="both", expand=True)
            self._current_embedded_view = landing

            center_box = tk.Frame(landing, bg=pal.card_bg)
            center_box.place(relx=0.5, rely=0.5, anchor="center")

            tk.Label(
                center_box,
                text=app_info["title"],
                font=("sans-serif", 18, "bold"),
                bg=pal.card_bg,
                fg=pal.fg,
            ).pack(pady=(0, 6))

            Badge(center_box, text=app_info["tag"], variant="primary").pack(pady=(0, 8))

            tk.Label(
                center_box,
                text=app_info["desc"],
                font=("sans-serif", 11),
                bg=pal.card_bg,
                fg=pal.text_muted,
                wraplength=460,
                justify="center",
            ).pack(pady=(0, 16))

            Button(
                center_box,
                text=f"Launch {app_info['title']} 🚀",
                width=240,
                height=38,
                variant="primary",
                command=self._launch_current_standalone,
            ).pack()

        cascade_bg_to_children(self._view_container, pal.card_bg, palette=pal)

    def _launch_current_standalone(self) -> None:
        if 0 <= self._active_app_idx < len(SHOWCASE_APPS):
            app_info = SHOWCASE_APPS[self._active_app_idx]
            script_path = str(EXAMPLES_DIR / app_info["script"])
            if os.path.exists(script_path):
                subprocess.Popen([sys.executable, script_path])

    def _on_global_theme_changed(self, pal) -> None:
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

    def _apply_theme_to_hub(self, pal) -> None:
        self.configure(background=pal.bg)
        if hasattr(self, "_workspace") and self._workspace.winfo_exists():
            self._workspace.configure(background=pal.bg)

        if hasattr(self, "_theme_opt") and self._theme_opt.winfo_exists():
            if self._theme_opt.get().lower() != pal.name.lower():
                self._theme_opt.set(pal.name)

        cascade_bg_to_children(self, pal.bg, palette=pal)
        self._load_app(self._active_app_idx)


def main():
    root = tk.Tk()
    root.title("tkblend - Unified Showcase Hub")
    root.geometry("1240x820")
    root.minsize(1040, 680)

    app = ShowcaseHub(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
