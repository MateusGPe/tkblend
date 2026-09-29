"""
tkblend File Explorer Example
Modern Blend2D-powered Pure Vector File Explorer.
Zero TTK dependencies.

Features:
- 3-Pane responsive layout with pure Blend2D Card and Frame containers
- Switchable views via SegmentedButton: Details Table (sortable, filterable) and Grid Card Tiles
- Rich multi-format preview panel: Image thumbnails (Pillow), text/code viewer (TextBox), and metadata cards
- Quick Access favorites and directory navigation
- Full navigation toolbar: Back, Forward, Up, Refresh, Path TextInput, Live Search, Hidden Switch, and Theme Selector (OptionMenu)
- Context menu with path copying, OS file manager integration, and terminal launcher
- Dynamic reactive theming supporting all tkblend palette presets
"""

from __future__ import annotations
import os
import sys
import stat
import time
import shutil
import platform
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import tkinter as tk
from tkinter import messagebox

# PIL for image thumbnail generation
try:
    from PIL import Image, ImageTk

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

import tkblend as tb

# File extension categorizations for Badges & Icons
FILE_CATEGORIES: Dict[str, Tuple[str, str, str]] = {
    # Code
    ".py": ("Python", "primary", "🐍"),
    ".pyi": ("Python Stub", "primary", "🐍"),
    ".c": ("C Source", "primary", "⚡"),
    ".cpp": ("C++ Source", "primary", "⚡"),
    ".cc": ("C++ Source", "primary", "⚡"),
    ".h": ("C Header", "primary", "⚡"),
    ".hpp": ("C++ Header", "primary", "⚡"),
    ".rs": ("Rust", "primary", "🦀"),
    ".go": ("Go", "primary", "🐹"),
    ".js": ("JavaScript", "primary", "📜"),
    ".ts": ("TypeScript", "primary", "📜"),
    ".html": ("HTML", "primary", "🌐"),
    ".css": ("CSS", "primary", "🎨"),
    ".sh": ("Shell Script", "primary", "🐚"),
    ".bash": ("Shell Script", "primary", "🐚"),
    # Documents / Text
    ".txt": ("Text", "outline", "📄"),
    ".md": ("Markdown", "outline", "📝"),
    ".rst": ("reStructuredText", "outline", "📝"),
    ".pdf": ("PDF Document", "outline", "📕"),
    ".doc": ("Word Doc", "outline", "📘"),
    ".docx": ("Word Doc", "outline", "📘"),
    # Config / Data
    ".json": ("JSON Data", "warning", "⚙️"),
    ".toml": ("TOML Config", "warning", "⚙️"),
    ".yaml": ("YAML Config", "warning", "⚙️"),
    ".yml": ("YAML Config", "warning", "⚙️"),
    ".xml": ("XML Data", "warning", "⚙️"),
    ".ini": ("INI Config", "warning", "⚙️"),
    ".env": ("Environment", "warning", "🔒"),
    # Images
    ".png": ("PNG Image", "success", "🖼️"),
    ".jpg": ("JPEG Image", "success", "🖼️"),
    ".jpeg": ("JPEG Image", "success", "🖼️"),
    ".gif": ("GIF Image", "success", "🖼️"),
    ".webp": ("WebP Image", "success", "🖼️"),
    ".bmp": ("Bitmap Image", "success", "🖼️"),
    ".svg": ("Vector SVG", "success", "🎨"),
    ".ico": ("Icon", "success", "🖼️"),
    # Archives
    ".zip": ("Zip Archive", "warning", "📦"),
    ".tar": ("Tar Archive", "warning", "📦"),
    ".gz": ("GZip Archive", "warning", "📦"),
    ".bz2": ("BZip Archive", "warning", "📦"),
    ".xz": ("XZ Archive", "warning", "📦"),
    ".7z": ("7-Zip Archive", "warning", "📦"),
    # Binaries / System
    ".so": ("Shared Object", "destructive", "⚙️"),
    ".dylib": ("Dynamic Library", "destructive", "⚙️"),
    ".dll": ("Windows DLL", "destructive", "⚙️"),
    ".exe": ("Executable", "destructive", "⚙️"),
    ".bin": ("Binary", "destructive", "⚙️"),
    ".o": ("Object File", "destructive", "⚙️"),
    ".a": ("Static Library", "destructive", "⚙️"),
}


def format_file_size(size_bytes: int) -> str:
    """Format bytes into human readable size string (B, KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_timestamp(ts: float) -> str:
    """Format UNIX timestamp to human readable date string."""
    try:
        t = time.localtime(ts)
        return time.strftime("%Y-%m-%d %H:%M:%S", t)
    except Exception:
        return "-"


def format_permissions(mode: int) -> str:
    """Convert stat mode to standard rwxrwxrwx string."""
    try:
        return stat.filemode(mode)
    except Exception:
        return "-"


def get_file_info(path: Path) -> Dict[str, Any]:
    """Retrieve structured metadata and category info for a given path."""
    info: Dict[str, Any] = {
        "path": path,
        "name": path.name or str(path),
        "is_dir": False,
        "size": 0,
        "size_str": "-",
        "mtime": 0.0,
        "mtime_str": "-",
        "permissions": "-",
        "category": "File",
        "variant": "secondary",
        "icon": "📄",
        "extension": path.suffix.lower(),
    }
    try:
        st = path.stat()
        info["is_dir"] = stat.S_ISDIR(st.st_mode)
        info["size"] = st.st_size if not info["is_dir"] else 0
        info["size_str"] = format_file_size(st.st_size) if not info["is_dir"] else "-"
        info["mtime"] = st.st_mtime
        info["mtime_str"] = format_timestamp(st.st_mtime)
        info["permissions"] = format_permissions(st.st_mode)

        if info["is_dir"]:
            info["category"] = "Folder"
            info["variant"] = "secondary"
            info["icon"] = "📁"
        else:
            ext = info["extension"]
            if ext in FILE_CATEGORIES:
                cat, var, icn = FILE_CATEGORIES[ext]
                info["category"] = cat
                info["variant"] = var
                info["icon"] = icn
    except Exception:
        pass
    return info


class FileExplorerApp:
    def __init__(self, root: Optional[tk.Tk] = None):
        self._owns_root = root is None
        self.root = root if root is not None else tk.Tk()
        self.root.title("tkblend File Explorer - Pure Blend2D UI")
        self.root.geometry("1200x780")
        self.root.minsize(980, 640)

        # Default theme
        tb.set_theme("dark")
        pal = tb.get_theme()
        self.root.configure(background=pal.bg)

        # Navigation & sorting state
        self.show_hidden = False
        self.current_view_mode = "Details"
        self.search_query = ""
        self.sort_column = "name"
        self.sort_descending = False

        # Initial directory
        initial_dir = Path(os.getcwd()).resolve()
        if not initial_dir.exists():
            initial_dir = Path.home().resolve()
        self.current_dir = initial_dir

        # Navigation history stacks
        self.history_back: List[Path] = []
        self.history_forward: List[Path] = []

        # Current directory items cache
        self.current_items: List[Dict[str, Any]] = []
        self.selected_item: Optional[Dict[str, Any]] = None

        # Image thumbnail cache to prevent GC
        self._thumbnail_photo: Optional[Any] = None

        # Build UI layout
        self._build_toolbar()
        self._build_main_panes()
        self._build_status_bar()
        self._build_context_menu()

        # Connect theme listener
        tb.add_theme_listener(self._on_theme_changed)
        self._on_theme_changed(pal)

        # Load initial location
        self.navigate_to(self.current_dir, record_history=False)

    # -------------------------------------------------------------------------
    # Top Navigation Toolbar
    # -------------------------------------------------------------------------
    def _build_toolbar(self):
        self.toolbar_card = tb.Frame(
            self.root,
            rx=0,
            ry=0,
            elevation=2.0,
            height=54,
        )
        self.toolbar_card.pack(fill="x", side="top")

        # Container inside toolbar
        self.tb_inner = tk.Frame(self.toolbar_card, bg=self.toolbar_card.bg_color)
        self.tb_inner.pack(fill="both", expand=True, padx=12, pady=6)

        # Left Nav Buttons: Back, Forward, Up, Refresh
        self.nav_box = tk.Frame(self.tb_inner, bg=self.toolbar_card.bg_color)
        self.nav_box.pack(side="left", padx=(0, 8))

        self.btn_back = tb.Button(
            self.nav_box,
            text="◀",
            width=36,
            height=32,
            rx=6,
            ry=6,
            variant="secondary",
            command=self.go_back,
        )
        self.btn_back.pack(side="left", padx=2)

        self.btn_forward = tb.Button(
            self.nav_box,
            text="▶",
            width=36,
            height=32,
            rx=6,
            ry=6,
            variant="secondary",
            command=self.go_forward,
        )
        self.btn_forward.pack(side="left", padx=2)

        self.btn_up = tb.Button(
            self.nav_box,
            text="▲",
            width=36,
            height=32,
            rx=6,
            ry=6,
            variant="secondary",
            command=self.go_up,
        )
        self.btn_up.pack(side="left", padx=2)

        self.btn_refresh = tb.Button(
            self.nav_box,
            text="🔄",
            width=36,
            height=32,
            rx=6,
            ry=6,
            variant="secondary",
            command=self.refresh,
        )
        self.btn_refresh.pack(side="left", padx=(2, 6))

        # Path Location Entry
        self.path_box = tk.Frame(self.tb_inner, bg=self.toolbar_card.bg_color)
        self.path_box.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.path_entry = tb.TextInput(
            self.path_box,
            placeholder_text="Enter folder path...",
            height=32,
        )
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.path_entry.bind("<Return>", self._on_path_entered)

        # Right Action & View Controls
        self.actions_box = tk.Frame(self.tb_inner, bg=self.toolbar_card.bg_color)
        self.actions_box.pack(side="right")

        # Live Search Field
        self.search_entry = tb.TextInput(
            self.actions_box,
            placeholder_text="Search files...",
            width=160,
            height=32,
        )
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # Details vs Grid Segmented Button
        self.seg_view = tb.SegmentedButton(
            self.actions_box,
            values=["Details", "Grid"],
            selected_index=0,
            width=140,
            height=32,
            on_change=lambda idx, val: self._on_view_mode_changed(val),
        )
        self.seg_view.pack(side="left", padx=(0, 10))

        # Hidden Files Toggle Switch
        self.hidden_box = tk.Frame(self.actions_box, bg=self.toolbar_card.bg_color)
        self.hidden_box.pack(side="left", padx=(0, 10))

        self.lbl_hidden = tk.Label(
            self.hidden_box,
            text="Hidden:",
            font=("sans-serif", 9),
            bg=self.toolbar_card.bg_color,
            fg=tb.get_theme().fg,
        )
        self.lbl_hidden.pack(side="left", padx=(0, 4))

        self.toggle_hidden = tb.Switch(
            self.hidden_box,
            is_on=self.show_hidden,
            on_toggle=self._on_toggle_hidden,
            width=42,
            height=22,
        )
        self.toggle_hidden.pack(side="left")

        # Theme Selector Dropdown
        theme_names = list(tb.get_available_themes())
        self.theme_menu = tb.OptionMenu(
            self.actions_box,
            values=theme_names,
            selected_value=tb.get_theme().name,
            command=self._on_theme_selected,
            width=130,
            height=32,
        )
        self.theme_menu.pack(side="left")

    # -------------------------------------------------------------------------
    # Main 3-Pane Layout
    # -------------------------------------------------------------------------
    def _build_main_panes(self):
        self.panes_container = tk.Frame(self.root, bg=tb.get_theme().bg)
        self.panes_container.pack(fill="both", expand=True, padx=12, pady=(8, 4))

        self.panes_container.grid_columnconfigure(0, weight=1)  # Left Sidebar
        self.panes_container.grid_columnconfigure(1, weight=4)  # Center Files
        self.panes_container.grid_columnconfigure(2, weight=2)  # Right Inspector
        self.panes_container.grid_rowconfigure(0, weight=1)

        # Pane 1: Left Sidebar
        self.sidebar_card = tb.Card(self.panes_container, rx=10, ry=10, elevation=2.0)
        self.sidebar_card.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
        self._build_sidebar(self.sidebar_card)

        # Pane 2: Center File Content Area
        self.center_card = tb.Card(self.panes_container, rx=10, ry=10, elevation=2.0)
        self.center_card.grid(row=0, column=1, padx=4, sticky="nsew")
        self._build_center_area(self.center_card)

        # Pane 3: Right Collapsible Preview & Inspector Panel
        self.preview_card = tb.Card(self.panes_container, rx=10, ry=10, elevation=2.0)
        self.preview_card.grid(row=0, column=2, padx=(6, 0), sticky="nsew")
        self._build_preview_panel(self.preview_card)

    # -------------------------------------------------------------------------
    # Sidebar: Quick Access Favorites + Directory Hierarchy
    # -------------------------------------------------------------------------
    def _build_sidebar(self, parent: tb.Card):
        self.side_inner = tk.Frame(parent, bg=parent.bg_color)
        self.side_inner.pack(fill="both", expand=True, padx=10, pady=10)

        self.lbl_fav_title = tk.Label(
            self.side_inner,
            text="⚡ QUICK ACCESS",
            font=("sans-serif", 9, "bold"),
            bg=parent.bg_color,
            fg=tb.get_theme().primary,
            anchor="w",
        )
        self.lbl_fav_title.pack(fill="x", pady=(0, 6))

        workspace_path = Path(os.getcwd()).resolve()
        home_path = Path.home().resolve()
        doc_path = home_path / "Documents"
        down_path = home_path / "Downloads"
        root_path = Path(os.path.abspath(os.sep))

        favs = [
            ("📁 Project Workspace", workspace_path),
            ("🏠 Home Directory", home_path),
        ]
        if doc_path.exists():
            favs.append(("📄 Documents", doc_path))
        if down_path.exists():
            favs.append(("📥 Downloads", down_path))
        favs.append(("💻 System Root", root_path))

        self.fav_buttons: List[tb.Button] = []
        for label, path in favs:
            btn = tb.Button(
                self.side_inner,
                text=label,
                variant="secondary",
                rx=6,
                ry=6,
                height=30,
                command=lambda p=path: self.navigate_to(p),
            )
            btn.pack(fill="x", pady=2)
            self.fav_buttons.append(btn)

        # Divider
        self.lbl_tree_title = tk.Label(
            self.side_inner,
            text="📂 DIRECTORY BROWSER",
            font=("sans-serif", 9, "bold"),
            bg=parent.bg_color,
            fg=tb.get_theme().primary,
            anchor="w",
        )
        self.lbl_tree_title.pack(fill="x", pady=(14, 6))

        # Scrollable Folder List
        self.folder_scroll = tb.ScrollableFrame(
            self.side_inner,
            rx=8,
            ry=8,
            elevation=0.0,
        )
        self.folder_scroll.pack(fill="both", expand=True)
        self.folder_list_frame = self.folder_scroll.scrollable_frame

    def _populate_sidebar_folders(self):
        """Populate subdirectories of current directory in sidebar for quick navigation."""
        for child in self.folder_list_frame.winfo_children():
            child.destroy()

        try:
            subdirs = [
                p
                for p in self.current_dir.iterdir()
                if p.is_dir()
                and (self.show_hidden or not p.name.startswith("."))
            ]
            subdirs.sort(key=lambda p: p.name.lower())
        except (PermissionError, OSError):
            subdirs = []

        if not subdirs:
            lbl_empty = tk.Label(
                self.folder_list_frame,
                text="No subfolders",
                font=("sans-serif", 9),
                bg=self.folder_scroll.bg_color,
                fg=tb.get_theme().secondary_fg,
            )
            lbl_empty.pack(padx=8, pady=8)
            return

        for sub in subdirs:
            btn = tb.Button(
                self.folder_list_frame,
                text=f"📁 {sub.name}",
                variant="outline",
                rx=6,
                ry=6,
                height=28,
                command=lambda p=sub: self.navigate_to(p),
            )
            btn.pack(fill="x", padx=4, pady=1)

    # -------------------------------------------------------------------------
    # Center Pane: Details Table & Grid / Icon Tile Views
    # -------------------------------------------------------------------------
    def _build_center_area(self, parent: tb.Card):
        self.center_inner = tk.Frame(parent, bg=parent.bg_color)
        self.center_inner.pack(fill="both", expand=True, padx=8, pady=8)

        # 1. Details Table (tb.Table)
        columns = [
            {"id": "icon", "title": "", "width": 36, "align": "center"},
            {"id": "name", "title": "Name", "width": 240, "align": "left"},
            {"id": "size_str", "title": "Size", "width": 85, "align": "right"},
            {
                "id": "category",
                "title": "Type",
                "width": 110,
                "align": "center",
                "type": "badge",
                "badge_colors": {
                    "Folder": "#3b82f6",
                    "Python": "#10b981",
                    "Python Stub": "#10b981",
                    "C Source": "#8b5cf6",
                    "C++ Source": "#8b5cf6",
                    "Rust": "#f97316",
                    "Go": "#06b6d4",
                    "JavaScript": "#eab308",
                    "TypeScript": "#3b82f6",
                    "Text": "#64748b",
                    "Markdown": "#64748b",
                    "JSON Data": "#f59e0b",
                    "TOML Config": "#f59e0b",
                    "YAML Config": "#f59e0b",
                    "PNG Image": "#10b981",
                    "JPEG Image": "#10b981",
                    "Zip Archive": "#ec4899",
                },
                "badge_fg": "#ffffff",
            },
            {"id": "mtime_str", "title": "Date Modified", "width": 150, "align": "left"},
            {"id": "permissions", "title": "Permissions", "width": 100, "align": "left"},
        ]

        self.table = tb.Table(
            self.center_inner,
            columns=columns,
            data=[],
            select_mode="single",
            rx=8,
            ry=8,
            elevation=0.0,
            on_select=self._on_table_select,
            on_double_click=self._on_table_double_click,
        )
        self.table.pack(fill="both", expand=True)
        self.table.bind("<Button-3>", self._on_show_context_menu)

        # 2. Grid / Tiles Frame (tb.ScrollableFrame)
        self.grid_scroll = tb.ScrollableFrame(
            self.center_inner,
            rx=8,
            ry=8,
            elevation=0.0,
        )
        self.grid_content = self.grid_scroll.scrollable_frame
        self.grid_content.bind("<Button-3>", self._on_show_context_menu)

    def _sort_table_by(self, column: str):
        """Toggle column sort order and refresh views."""
        if self.sort_column == column:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = column
            self.sort_descending = False
        self._refresh_content_views()

    def _on_view_mode_changed(self, mode: str):
        """Switch between Details table and Grid tile views."""
        self.current_view_mode = mode
        if mode == "Details":
            self.grid_scroll.pack_forget()
            self.table.pack(fill="both", expand=True)
        else:
            self.table.pack_forget()
            self.grid_scroll.pack(fill="both", expand=True)
            self._render_grid_view()

    # -------------------------------------------------------------------------
    # Right Pane: Multi-Format Preview & Inspector Panel
    # -------------------------------------------------------------------------
    def _build_preview_panel(self, parent: tb.Card):
        self.preview_inner = tk.Frame(parent, bg=parent.bg_color)
        self.preview_inner.pack(fill="both", expand=True, padx=10, pady=10)

        # Header Box with Title and File Type Badge
        self.p_header = tk.Frame(self.preview_inner, bg=parent.bg_color)
        self.p_header.pack(fill="x", pady=(0, 8))

        self.p_title_var = tk.StringVar(value="Select an item")
        self.lbl_preview_title = tk.Label(
            self.p_header,
            textvariable=self.p_title_var,
            font=("sans-serif", 11, "bold"),
            bg=parent.bg_color,
            fg=tb.get_theme().fg,
            wraplength=230,
            justify="left",
            anchor="w",
        )
        self.lbl_preview_title.pack(fill="x")

        self.p_badge_box = tk.Frame(self.p_header, bg=parent.bg_color)
        self.p_badge_box.pack(anchor="w", pady=(6, 0))

        self.preview_badge = tb.Badge(
            self.p_badge_box, text="File Explorer", variant="primary"
        )
        self.preview_badge.pack(side="left")

        # Metadata Properties Card
        self.meta_card = tb.Frame(
            self.preview_inner,
            rx=8,
            ry=8,
            elevation=0.0,
        )
        self.meta_card.pack(fill="x", pady=(0, 10))

        self.meta_inner = tk.Frame(self.meta_card, bg=self.meta_card.bg_color)
        self.meta_inner.pack(fill="both", expand=True, padx=8, pady=8)

        self.meta_vars = {
            "Path": tk.StringVar(value="-"),
            "Size": tk.StringVar(value="-"),
            "Modified": tk.StringVar(value="-"),
            "Permissions": tk.StringVar(value="-"),
        }

        self.meta_labels: List[tk.Label] = []
        for label, var in self.meta_vars.items():
            row = tk.Frame(self.meta_inner, bg=self.meta_card.bg_color)
            row.pack(fill="x", pady=2)
            lbl_key = tk.Label(
                row,
                text=f"{label}:",
                width=11,
                font=("sans-serif", 9, "bold"),
                bg=self.meta_card.bg_color,
                fg=tb.get_theme().fg,
                anchor="w",
            )
            lbl_key.pack(side="left")
            self.meta_labels.append(lbl_key)

            lbl_val = tk.Label(
                row,
                textvariable=var,
                font=("sans-serif", 9),
                bg=self.meta_card.bg_color,
                fg=tb.get_theme().secondary_fg,
                wraplength=170,
                justify="left",
                anchor="w",
            )
            lbl_val.pack(side="left", fill="x", expand=True)
            self.meta_labels.append(lbl_val)

        # Content Preview Section
        self.prev_section_lbl = tk.Label(
            self.preview_inner,
            text="CONTENT PREVIEW",
            font=("sans-serif", 9, "bold"),
            bg=parent.bg_color,
            fg=tb.get_theme().primary,
            anchor="w",
        )
        self.prev_section_lbl.pack(fill="x", pady=(4, 6))

        self.prev_container = tk.Frame(self.preview_inner, bg=parent.bg_color)
        self.prev_container.pack(fill="both", expand=True)

        # 1. Text / Code Viewer (tb.TextBox)
        self.text_preview = tb.TextBox(
            self.prev_container,
            rx=8,
            ry=8,
            wrap="none",
            placeholder_text="No text content to preview...",
        )

        # 2. Image / Visual Label
        self.image_preview_lbl = tk.Label(
            self.prev_container,
            text="No preview available",
            bg=parent.bg_color,
            fg=tb.get_theme().secondary_fg,
            font=("sans-serif", 10),
            justify="center",
        )
        self.image_preview_lbl.pack(fill="both", expand=True)

    # -------------------------------------------------------------------------
    # Status Bar
    # -------------------------------------------------------------------------
    def _build_status_bar(self):
        self.status_card = tb.Frame(
            self.root,
            rx=0,
            ry=0,
            elevation=1.0,
            height=30,
        )
        self.status_card.pack(side="bottom", fill="x")

        self.status_var = tk.StringVar(value="Ready")
        self.lbl_status = tk.Label(
            self.status_card,
            textvariable=self.status_var,
            font=("sans-serif", 9),
            bg=self.status_card.bg_color,
            fg=tb.get_theme().fg,
            padx=16,
            pady=4,
            anchor="w",
        )
        self.lbl_status.pack(side="left", fill="x", expand=True)

    # -------------------------------------------------------------------------
    # Context Menu
    # -------------------------------------------------------------------------
    def _build_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(
            label="Open / Enter", command=self._on_action_open
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Copy Full Path", command=self._on_action_copy_path
        )
        self.context_menu.add_command(
            label="Copy Relative Path", command=self._on_action_copy_relative_path
        )
        self.context_menu.add_command(
            label="Copy File Name", command=self._on_action_copy_name
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Reveal in OS File Manager", command=self._on_action_reveal_os
        )
        self.context_menu.add_command(
            label="Open in Terminal", command=self._on_action_open_terminal
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Refresh", command=self.refresh)

    def _on_show_context_menu(self, event):
        """Popup right-click context menu."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    # -------------------------------------------------------------------------
    # Core Navigation & File Loading Logic
    # -------------------------------------------------------------------------
    def navigate_to(self, target_path: Path, record_history: bool = True):
        """Navigate center pane and views to target directory path."""
        try:
            target_path = target_path.resolve()
            if not target_path.exists() or not target_path.is_dir():
                messagebox.showerror(
                    "Cannot Open", f"Directory does not exist:\n{target_path}"
                )
                return

            if record_history and self.current_dir != target_path:
                self.history_back.append(self.current_dir)
                self.history_forward.clear()

            self.current_dir = target_path
            self.path_entry.set(str(self.current_dir))

            # Scan directory items
            self._scan_current_directory()
            self._populate_sidebar_folders()
            self._refresh_content_views()

        except PermissionError:
            messagebox.showerror(
                "Permission Denied", f"Access denied to folder:\n{target_path}"
            )
        except Exception as err:
            messagebox.showerror("Navigation Error", str(err))

    def _scan_current_directory(self):
        """Scan directory entries and cache metadata."""
        items: List[Dict[str, Any]] = []
        try:
            with os.scandir(self.current_dir) as entries:
                for entry in entries:
                    if not self.show_hidden and entry.name.startswith("."):
                        continue
                    p = Path(entry.path)
                    items.append(get_file_info(p))
        except (PermissionError, OSError) as e:
            self.status_var.set(f"Scan warning: {e}")

        # Default sort: folders first, then by sort_column
        self.current_items = items

    def _refresh_content_views(self):
        """Filter, sort, and display items according to active search query and sort column."""
        filtered = self.current_items
        if self.search_query:
            query = self.search_query.lower()
            filtered = [it for it in filtered if query in it["name"].lower()]

        def sort_key(it: Dict[str, Any]):
            is_folder = 0 if it["is_dir"] else 1
            val: Any = it["name"].lower()
            if self.sort_column == "size":
                val = it["size"]
            elif self.sort_column == "type":
                val = it["category"].lower()
            elif self.sort_column == "modified":
                val = it["mtime"]
            elif self.sort_column == "permissions":
                val = it["permissions"]
            return (is_folder, val)

        filtered.sort(key=sort_key, reverse=self.sort_descending)

        # Populate Table
        self.table.set_data(filtered)

        # Populate Grid View if active
        if self.current_view_mode == "Grid":
            self._render_grid_view(filtered)

        # Update status bar
        total_count = len(self.current_items)
        filtered_count = len(filtered)
        try:
            free_bytes = shutil.disk_usage(self.current_dir).free
            free_str = format_file_size(free_bytes)
        except Exception:
            free_str = "Unknown"

        status_msg = (
            f"{filtered_count} items (total: {total_count}) • Free space: {free_str}"
        )
        if self.selected_item:
            status_msg = (
                f"Selected: {self.selected_item['name']} ({self.selected_item['size_str']}) • "
                + status_msg
            )
        self.status_var.set(status_msg)

    # -------------------------------------------------------------------------
    # Grid / Tile View Rendering
    # -------------------------------------------------------------------------
    def _render_grid_view(self, items: Optional[List[Dict[str, Any]]] = None):
        """Render card tiles for all items in the scrollable grid frame."""
        if items is None:
            items = self.current_items
            if self.search_query:
                query = self.search_query.lower()
                items = [it for it in items if query in it["name"].lower()]

        for widget in self.grid_content.winfo_children():
            widget.destroy()

        columns_count = 4
        for idx, it in enumerate(items):
            row = idx // columns_count
            col = idx % columns_count

            card = tb.Card(self.grid_content, rx=8, ry=8, elevation=1.0)
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            card_inner = tk.Frame(card, bg=card.bg_color)
            card_inner.pack(fill="both", expand=True, padx=8, pady=8)

            lbl_icon = tk.Label(
                card_inner,
                text=it["icon"],
                font=("sans-serif", 24),
                bg=card.bg_color,
            )
            lbl_icon.pack(pady=(2, 2))

            short_name = it["name"]
            if len(short_name) > 14:
                short_name = short_name[:11] + "..."
            lbl_name = tk.Label(
                card_inner,
                text=short_name,
                font=("sans-serif", 9, "bold"),
                bg=card.bg_color,
                fg=tb.get_theme().fg,
            )
            lbl_name.pack()

            lbl_sub = tk.Label(
                card_inner,
                text=it["size_str"] if not it["is_dir"] else "Folder",
                font=("sans-serif", 8),
                bg=card.bg_color,
                fg=tb.get_theme().secondary_fg,
            )
            lbl_sub.pack(pady=(2, 2))

            for w in (card, card_inner, lbl_icon, lbl_name, lbl_sub):
                w.bind("<Button-1>", lambda e, item=it: self._select_item(item))
                w.bind(
                    "<Double-Button-1>",
                    lambda e, item=it: self._on_item_double_click(item),
                )
                w.bind("<Button-3>", self._on_show_context_menu)

        for c in range(columns_count):
            self.grid_content.columnconfigure(c, weight=1)

    # -------------------------------------------------------------------------
    # Item Selection & Multi-Format Preview Display
    # -------------------------------------------------------------------------
    def _select_item(self, it: Dict[str, Any]):
        """Select an item and update preview inspector."""
        self.selected_item = it
        self.p_title_var.set(it["name"])
        self.meta_vars["Path"].set(str(it["path"]))
        self.meta_vars["Size"].set(it["size_str"])
        self.meta_vars["Modified"].set(it["mtime_str"])
        self.meta_vars["Permissions"].set(it["permissions"])

        # Update Badge
        self.preview_badge.set_text(it["category"])
        self.preview_badge.set_variant(it["variant"])

        # Update status message
        self.status_var.set(
            f"Selected: {it['name']} • {it['category']} • {it['size_str']} • Modified: {it['mtime_str']}"
        )

        # Trigger content preview
        self._update_preview_content(it)

    def _update_preview_content(self, it: Dict[str, Any]):
        """Load and display preview based on file format (image, text, folder)."""
        target_path: Path = it["path"]

        # 1. Directory Preview
        if it["is_dir"]:
            self.text_preview.pack_forget()
            self.image_preview_lbl.pack(fill="both", expand=True)
            try:
                sub_count = len(list(target_path.iterdir()))
                self.image_preview_lbl.configure(
                    image="",
                    text=f"📁 Folder\n\nContains {sub_count} items.\nDouble-click to browse folder.",
                    font=("sans-serif", 10),
                )
            except Exception:
                self.image_preview_lbl.configure(
                    image="", text="📁 Folder\n\nAccess restricted."
                )
            return

        # 2. Image Preview (using PIL)
        ext = it["extension"]
        if HAS_PIL and ext in (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".bmp",
            ".ico",
        ):
            try:
                img = Image.open(target_path)
                img.thumbnail((260, 220), Image.Resampling.LANCZOS)
                self._thumbnail_photo = ImageTk.PhotoImage(img)

                self.text_preview.pack_forget()
                self.image_preview_lbl.pack(fill="both", expand=True)
                self.image_preview_lbl.configure(
                    image=self._thumbnail_photo,
                    text=f"\nImage Resolution: {img.width} × {img.height}",
                    compound="top",
                    font=("sans-serif", 9),
                )
                return
            except Exception as err:
                self.image_preview_lbl.configure(
                    image="", text=f"Image preview error:\n{err}", compound="none"
                )
                return

        # 3. Text / Code Preview
        is_text_candidate = ext in (
            ".py",
            ".pyi",
            ".txt",
            ".md",
            ".json",
            ".toml",
            ".yaml",
            ".yml",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".rs",
            ".go",
            ".js",
            ".ts",
            ".html",
            ".css",
            ".sh",
            ".bash",
            ".xml",
            ".ini",
            ".env",
            ".rst",
            ".cmake",
        )
        if is_text_candidate or it["size"] < 256 * 1024:
            try:
                with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = [f.readline() for _ in range(250)]

                self.image_preview_lbl.pack_forget()
                self.text_preview.pack(fill="both", expand=True)
                self.text_preview.clear()

                preview_lines = []
                for i, line in enumerate(lines, 1):
                    preview_lines.append(f"{i:3d} | {line}")
                self.text_preview.set_text("".join(preview_lines))
                return
            except Exception:
                pass

        # 4. Binary / Unsupported Preview Placeholder
        self.text_preview.pack_forget()
        self.image_preview_lbl.pack(fill="both", expand=True)
        self.image_preview_lbl.configure(
            image="",
            text=f"⚙️ Binary / Structured File\n\nDirect preview not available.\nSize: {it['size_str']}",
            compound="none",
            font=("sans-serif", 10),
        )

    # -------------------------------------------------------------------------
    # Event Handlers & Actions
    # -------------------------------------------------------------------------
    def _on_table_select(self, indices: Any, rows: Any = None):
        selected_rows = self.table.get_selected_rows()
        if selected_rows:
            row = selected_rows[0]
            if isinstance(row, dict):
                self._select_item(row)

    def _on_table_double_click(self, row_idx: int, row_data: Any):
        if isinstance(row_data, dict):
            if row_data.get("is_dir"):
                self.navigate_to(row_data["path"])

    def _on_item_double_click(self, it: Dict[str, Any]):
        if it["is_dir"]:
            self.navigate_to(it["path"])

    def _on_path_entered(self, event):
        val = self.path_entry.get().strip()
        if val:
            self.navigate_to(Path(val))

    def _on_search_changed(self, event):
        self.search_query = self.search_entry.get().strip()
        self._refresh_content_views()

    def _on_toggle_hidden(self, is_on: bool):
        self.show_hidden = is_on
        self._scan_current_directory()
        self._populate_sidebar_folders()
        self._refresh_content_views()

    def go_back(self):
        if self.history_back:
            dest = self.history_back.pop()
            self.history_forward.append(self.current_dir)
            self.navigate_to(dest, record_history=False)

    def go_forward(self):
        if self.history_forward:
            dest = self.history_forward.pop()
            self.history_back.append(self.current_dir)
            self.navigate_to(dest, record_history=False)

    def go_up(self):
        parent = self.current_dir.parent
        if parent != self.current_dir:
            self.navigate_to(parent)

    def refresh(self):
        self._scan_current_directory()
        self._populate_sidebar_folders()
        self._refresh_content_views()
        self.status_var.set(f"Refreshed: {self.current_dir.name}")

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        cur = tb.get_theme()
        new_theme = "light" if cur.dark_mode else "dark"
        tb.set_theme(new_theme)

    def _on_theme_selected(self, theme_name: str):
        tb.set_theme(theme_name)

    def _on_theme_changed(self, palette: tb.Palette):
        if not self.root.winfo_exists():
            return
        self.root.configure(background=palette.bg)
        self.panes_container.configure(background=palette.bg)
        self.theme_menu.set(palette.name)

        # Update label colors
        self.lbl_fav_title.configure(bg=self.sidebar_card.bg_color, fg=palette.primary)
        self.lbl_tree_title.configure(bg=self.sidebar_card.bg_color, fg=palette.primary)
        self.lbl_preview_title.configure(bg=self.preview_card.bg_color, fg=palette.fg)
        self.prev_section_lbl.configure(bg=self.preview_card.bg_color, fg=palette.primary)
        self.lbl_hidden.configure(bg=self.toolbar_card.bg_color, fg=palette.fg)
        self.lbl_status.configure(bg=self.status_card.bg_color, fg=palette.fg)
        self.image_preview_lbl.configure(bg=self.preview_card.bg_color, fg=palette.secondary_fg)

        for lbl in self.meta_labels:
            lbl.configure(bg=self.meta_card.bg_color)

        tb.cascade_bg_to_children(self.root, palette.bg)

    # -------------------------------------------------------------------------
    # Context Menu Actions
    # -------------------------------------------------------------------------
    def _on_action_open(self):
        if self.selected_item and self.selected_item["is_dir"]:
            self.navigate_to(self.selected_item["path"])
        elif self.selected_item:
            self._on_action_reveal_os()

    def _on_action_copy_path(self):
        if self.selected_item:
            p = str(self.selected_item["path"])
            self.root.clipboard_clear()
            self.root.clipboard_append(p)
            self.status_var.set(f"Copied path to clipboard: {p}")

    def _on_action_copy_relative_path(self):
        if self.selected_item:
            try:
                rel = str(self.selected_item["path"].relative_to(Path.cwd()))
            except Exception:
                rel = str(self.selected_item["path"])
            self.root.clipboard_clear()
            self.root.clipboard_append(rel)
            self.status_var.set(f"Copied relative path: {rel}")

    def _on_action_copy_name(self):
        if self.selected_item:
            name = self.selected_item["name"]
            self.root.clipboard_clear()
            self.root.clipboard_append(name)
            self.status_var.set(f"Copied file name: {name}")

    def _on_action_reveal_os(self):
        target = self.selected_item["path"] if self.selected_item else self.current_dir
        try:
            if platform.system() == "Windows":
                os.startfile(str(target))
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(target)], check=False)
            else:
                subprocess.run(["xdg-open", str(target)], check=False)
            self.status_var.set(f"Revealed in OS file manager: {target.name}")
        except Exception as err:
            self.status_var.set(f"Reveal failed: {err}")

    def _on_action_open_terminal(self):
        target_dir = (
            self.selected_item["path"]
            if (self.selected_item and self.selected_item["is_dir"])
            else self.current_dir
        )
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["cmd.exe", "/K", f"cd /d {target_dir}"], shell=True)
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-a", "Terminal", str(target_dir)], check=False)
            else:
                terminals = [
                    "x-terminal-emulator",
                    "gnome-terminal",
                    "alacritty",
                    "kitty",
                    "konsole",
                    "xterm",
                ]
                for term in terminals:
                    if shutil.which(term):
                        subprocess.Popen([term], cwd=str(target_dir))
                        self.status_var.set(
                            f"Launched terminal {term} in {target_dir.name}"
                        )
                        return
                self.status_var.set("No recognized terminal emulator found.")
        except Exception as err:
            self.status_var.set(f"Open terminal failed: {err}")

    def destroy(self):
        """Clean up theme listeners and widgets."""
        try:
            tb.remove_theme_listener(self._on_theme_changed)
        except Exception:
            pass
        if hasattr(self, "toolbar_card") and self.toolbar_card.winfo_exists():
            self.toolbar_card.destroy()
        if hasattr(self, "panes_container") and self.panes_container.winfo_exists():
            self.panes_container.destroy()
        if hasattr(self, "status_card") and self.status_card.winfo_exists():
            self.status_card.destroy()
        if hasattr(self, "context_menu") and self.context_menu.winfo_exists():
            self.context_menu.destroy()
        if self._owns_root and self.root.winfo_exists():
            self.root.destroy()

    def mainloop(self):
        self.root.mainloop()


def main():
    app = FileExplorerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
