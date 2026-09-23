"""
tkblend File Explorer Example
Modern Blend2D-powered Native TTK File Explorer.
Features:
- 3-Pane responsive layout with interactive Panedwindow
- Switchable views via SegmentedControl: Details Table (sortable) and Grid/Icon Tiles
- Rich multi-format preview panel: Image thumbnails (Pillow), text/code viewer (ThemedText), and metadata cards
- Lazy-loaded filesystem tree with vector chevrons and Pinned Quick Access favorites
- Full navigation toolbar: Back, Forward, Up, Refresh, SearchEntry, and Dark/Light mode switcher
- Safe context menu with path copying, OS file manager integration, and hidden file toggle
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
from tkinter import ttk, messagebox

# PIL for image thumbnail generation
try:
    from PIL import Image, ImageTk

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

import tkblend

# Shared theme parameters
_THEME_OPTS = dict(
    button_radius=8.0,
    entry_radius=8.0,
    shadow_blur=8.0,
)

# File extension categorizations for Badges & Icons
FILE_CATEGORIES = {
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
    """Format bytes into readable size string (B, KB, MB, GB)."""
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


class ScrolledFrame(ttk.Frame):
    """A smooth scrollable container frame with vertical scrollbar."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas)

        self.content.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self._window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self._window_id, width=e.width),
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self._bind_mousewheel(self.canvas)
        self._bind_mousewheel(self.content)

    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel, add="+")
        widget.bind("<Button-5>", self._on_mousewheel, add="+")

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-2, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(2, "units")
        elif event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120) * 2), "units")


class FileExplorerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend File Explorer")
        self.root.geometry("1180x760")
        self.root.minsize(960, 620)

        self.is_dark = True
        self.show_hidden_var = tk.BooleanVar(value=False)
        self.current_view_mode = "Details"
        self.search_query = ""
        self.sort_column = "name"
        self.sort_descending = False

        # Apply native Blend2D TTK theme
        tkblend.apply_theme(
            self.root, dark_mode=self.is_dark, enable_shadows=True, **_THEME_OPTS
        )

        # Initial directory is current workspace or user home
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
        self._build_panes()
        self._build_status_bar()
        self._build_context_menu()

        # Load initial location
        self.navigate_to(self.current_dir, record_history=False)

    # -------------------------------------------------------------------------
    # Top Navigation Toolbar
    # -------------------------------------------------------------------------
    def _build_toolbar(self):
        toolbar = ttk.Frame(self.root, padding=(16, 10, 16, 8))
        toolbar.pack(fill="x", side="top")

        # Left Nav Buttons: Back, Forward, Up, Refresh
        nav_box = ttk.Frame(toolbar)
        nav_box.pack(side="left", padx=(0, 10))

        self.btn_back = ttk.Button(
            nav_box, text="◀", width=3, style="Ghost.TButton", command=self.go_back
        )
        self.btn_back.pack(side="left", padx=2)

        self.btn_forward = ttk.Button(
            nav_box, text="▶", width=3, style="Ghost.TButton", command=self.go_forward
        )
        self.btn_forward.pack(side="left", padx=2)

        self.btn_up = ttk.Button(
            nav_box, text="▲", width=3, style="Ghost.TButton", command=self.go_up
        )
        self.btn_up.pack(side="left", padx=2)

        self.btn_refresh = ttk.Button(
            nav_box, text="🔄", width=3, style="Ghost.TButton", command=self.refresh
        )
        self.btn_refresh.pack(side="left", padx=(2, 6))

        # Path Entry / Location Bar
        path_box = ttk.Frame(toolbar)
        path_box.pack(side="left", fill="x", expand=True, padx=(0, 12))

        ttk.Label(path_box, text="📍", font=("Helvetica", 11)).pack(
            side="left", padx=(0, 4)
        )
        self.path_entry = tkblend.TextInput(path_box, placeholder="Enter folder path...", height=34)
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.path_entry.bind("<Return>", self._on_path_entered)

        # Right Action & View Controls
        actions_box = ttk.Frame(toolbar)
        actions_box.pack(side="right")

        # Live Search Field
        self.search_entry = tkblend.TextInput(
            actions_box, placeholder="Search files...", width=160, height=34
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        # Details vs Grid Segmented Control
        self.seg_view = tkblend.SegmentedControl(
            actions_box,
            values=["Details", "Grid"],
            command=self._on_view_mode_changed,
        )
        self.seg_view.pack(side="left", padx=(0, 12))

        # Hidden Files Toggle
        hidden_box = ttk.Frame(actions_box)
        hidden_box.pack(side="left", padx=(0, 12))
        ttk.Label(hidden_box, text="Hidden:").pack(side="left", padx=(0, 6))
        self.toggle_hidden = tkblend.ToggleSwitch(
            hidden_box,
            variable=self.show_hidden_var,
            command=self._on_toggle_hidden,
        )
        self.toggle_hidden.pack(side="left")

        # Theme Switcher Button
        self.btn_theme = ttk.Button(
            actions_box,
            text="☀️ Light" if self.is_dark else "🌙 Dark",
            style="Secondary.TButton",
            command=self.toggle_theme,
        )
        self.btn_theme.pack(side="left")

    # -------------------------------------------------------------------------
    # 3-Pane Responsive Layout (PanedWindow)
    # -------------------------------------------------------------------------
    def _build_panes(self):
        self.paned = ttk.Panedwindow(self.root, orient="horizontal")
        self.paned.pack(fill="both", expand=True, padx=16, pady=(4, 8))

        # Pane 1: Left Navigation Sidebar (Favorites + Directory Tree)
        self.sidebar_frame = ttk.Frame(self.paned, padding=4)
        self._build_sidebar(self.sidebar_frame)

        # Pane 2: Center File Content Area (Details Table or Grid Tiles)
        self.center_frame = ttk.Frame(self.paned, padding=4)
        self._build_center_area(self.center_frame)

        # Pane 3: Right Collapsible Preview & Inspector Panel
        self.preview_frame = tkblend.Card(self.paned, padding=12)
        self._build_preview_panel(self.preview_frame)

        # Add panes with default proportional weights
        self.paned.add(self.sidebar_frame, weight=1)
        self.paned.add(self.center_frame, weight=3)
        self.paned.add(self.preview_frame, weight=2)

    # -------------------------------------------------------------------------
    # Sidebar: Quick Access Favorites + Lazy-Loaded Treeview
    # -------------------------------------------------------------------------
    def _build_sidebar(self, parent: ttk.Frame):
        # Quick Access Favorites Card
        fav_card = ttk.Labelframe(parent, text=" Quick Access ", padding=8)
        fav_card.pack(fill="x", pady=(0, 8))

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

        for label, path in favs:
            btn = ttk.Button(
                fav_card,
                text=label,
                style="Ghost.TButton",
                command=lambda p=path: self.navigate_to(p),
            )
            btn.pack(fill="x", pady=1)

        # Filesystem Tree
        tree_box = ttk.Labelframe(parent, text=" File System ", padding=4)
        tree_box.pack(fill="both", expand=True)

        tree_container = ttk.Frame(tree_box)
        tree_container.pack(fill="both", expand=True)

        self.side_tree = ttk.Treeview(tree_container, show="tree", selectmode="browse")
        self.side_scroll = ttk.Scrollbar(
            tree_container, orient="vertical", command=self.side_tree.yview
        )
        self.side_tree.configure(yscrollcommand=self.side_scroll.set)

        self.side_scroll.pack(side="right", fill="y")
        self.side_tree.pack(side="left", fill="both", expand=True)

        self.side_tree.bind("<<TreeviewOpen>>", self._on_tree_node_open)
        self.side_tree.bind("<<TreeviewSelect>>", self._on_tree_node_select)

        # Populate top root node
        self._populate_sidebar_tree_roots()

    def _populate_sidebar_tree_roots(self):
        """Populate top-level root folders in sidebar tree."""
        self.side_tree.delete(*self.side_tree.get_children())
        roots = []

        workspace_path = Path(os.getcwd()).resolve()
        roots.append(("Workspace", workspace_path))

        if platform.system() == "Windows":
            import string

            for drive in string.ascii_uppercase:
                p = Path(f"{drive}:\\")
                if p.exists():
                    roots.append((f"Local Disk ({drive}:)", p))
        else:
            roots.append(("Root (/)", Path("/")))
            roots.append(("Home (~)", Path.home()))

        for name, path in roots:
            node_id = self.side_tree.insert(
                "", "end", text=f"📁 {name}", values=(str(path),)
            )
            # Insert dummy node for lazy-loading subdirectories
            self.side_tree.insert(node_id, "end", text="Loading...")

    def _on_tree_node_open(self, event):
        """Lazy-load directory children when tree node chevron is expanded."""
        sel = self.side_tree.focus()
        if not sel:
            return

        values = self.side_tree.item(sel, "values")
        if not values:
            return

        dir_path = Path(values[0])
        children = self.side_tree.get_children(sel)

        # If only dummy node exists, replace with real subdirectories
        if (
            len(children) == 1
            and self.side_tree.item(children[0], "text") == "Loading..."
        ):
            self.side_tree.delete(children[0])
            try:
                subdirs = [
                    p
                    for p in dir_path.iterdir()
                    if p.is_dir()
                    and (self.show_hidden_var.get() or not p.name.startswith("."))
                ]
                subdirs.sort(key=lambda p: p.name.lower())
                for sub in subdirs:
                    sub_node = self.side_tree.insert(
                        sel, "end", text=f"📁 {sub.name}", values=(str(sub),)
                    )
                    # Check if sub has children to add dummy placeholder
                    try:
                        has_children = any(c.is_dir() for c in sub.iterdir())
                        if has_children:
                            self.side_tree.insert(sub_node, "end", text="Loading...")
                    except (PermissionError, OSError):
                        pass
            except (PermissionError, OSError):
                pass

    def _on_tree_node_select(self, event):
        """Navigate to selected directory when clicking a node in sidebar."""
        sel = self.side_tree.focus()
        if not sel:
            return
        values = self.side_tree.item(sel, "values")
        if values:
            target = Path(values[0])
            if target.is_dir() and target != self.current_dir:
                self.navigate_to(target)

    # -------------------------------------------------------------------------
    # Center Pane: Details Table & Grid / Icon Tile Views
    # -------------------------------------------------------------------------
    def _build_center_area(self, parent: ttk.Frame):
        self.center_container = ttk.Frame(parent)
        self.center_container.pack(fill="both", expand=True)

        # 1. Details Table Frame (Card container with unified rounded border)
        self.details_frame = tkblend.Card(self.center_container, padding=2)

        columns = ("name", "size", "type", "modified", "permissions")
        self.table = ttk.Treeview(
            self.details_frame, columns=columns, show="headings", selectmode="browse"
        )
        self.table_scroll_y = ttk.Scrollbar(
            self.details_frame, orient="vertical", command=self.table.yview
        )
        self.table_scroll_x = ttk.Scrollbar(
            self.details_frame, orient="horizontal", command=self.table.xview
        )
        self.table.configure(
            yscrollcommand=self.table_scroll_y.set,
            xscrollcommand=self.table_scroll_x.set,
        )

        self.table.heading(
            "name", text="Name", command=lambda: self._sort_table_by("name")
        )
        self.table.heading(
            "size", text="Size", command=lambda: self._sort_table_by("size")
        )
        self.table.heading(
            "type", text="Type", command=lambda: self._sort_table_by("type")
        )
        self.table.heading(
            "modified",
            text="Date Modified",
            command=lambda: self._sort_table_by("modified"),
        )
        self.table.heading(
            "permissions",
            text="Permissions",
            command=lambda: self._sort_table_by("permissions"),
        )

        self.table.column("name", width=220, minwidth=130, stretch=True)
        self.table.column("size", width=80, minwidth=65, stretch=False, anchor="e")
        self.table.column("type", width=110, minwidth=80, stretch=False)
        self.table.column("modified", width=150, minwidth=110, stretch=False)
        self.table.column("permissions", width=95, minwidth=70, stretch=False)

        self.table_scroll_y.pack(side="right", fill="y")
        self.table_scroll_x.pack(side="bottom", fill="x")
        self.table.pack(side="left", fill="both", expand=True)

        self.table.bind("<<TreeviewSelect>>", self._on_table_select)
        self.table.bind("<Double-Button-1>", self._on_table_double_click)
        self.table.bind("<Button-3>", self._on_show_context_menu)

        # 2. Grid / Tiles Frame (ScrolledFrame)
        self.grid_frame = ScrolledFrame(self.center_container)
        self.grid_frame.content.bind("<Button-3>", self._on_show_context_menu)

        # Pack initial default view mode
        self.details_frame.pack(fill="both", expand=True)

    def _sort_table_by(self, column: str):
        """Toggle column sort order and re-render."""
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
            self.grid_frame.pack_forget()
            self.details_frame.pack(fill="both", expand=True)
        else:
            self.details_frame.pack_forget()
            self.grid_frame.pack(fill="both", expand=True)
            self._render_grid_view()

    # -------------------------------------------------------------------------
    # Right Pane: Multi-Format Preview & Inspector Panel
    # -------------------------------------------------------------------------
    def _build_preview_panel(self, parent: ttk.Frame):
        # Header Box with Title and File Type Badge
        self.p_header = ttk.Frame(parent)
        self.p_header.pack(fill="x", pady=(0, 8))

        self.p_title_var = tk.StringVar(value="Select an item")
        self.lbl_preview_title = ttk.Label(
            self.p_header,
            textvariable=self.p_title_var,
            font=("Helvetica", 12, "bold"),
            wraplength=220,
        )
        self.lbl_preview_title.pack(anchor="w")

        self.p_badge_box = ttk.Frame(self.p_header)
        self.p_badge_box.pack(anchor="w", pady=(4, 0))

        self.preview_badge = tkblend.Badge(
            self.p_badge_box, text="File Explorer", variant="primary", dot=True
        )
        self.preview_badge.pack(side="left")

        # Metadata Details Card
        meta_card = ttk.Labelframe(parent, text=" File Properties ", padding=8)
        meta_card.pack(fill="x", pady=(0, 10))

        self.meta_vars = {
            "Path": tk.StringVar(value="-"),
            "Size": tk.StringVar(value="-"),
            "Modified": tk.StringVar(value="-"),
            "Permissions": tk.StringVar(value="-"),
        }

        for idx, (label, var) in enumerate(self.meta_vars.items()):
            row = ttk.Frame(meta_card)
            row.pack(fill="x", pady=2)
            ttk.Label(
                row, text=f"{label}:", width=12, font=("Helvetica", 9, "bold")
            ).pack(side="left")
            ttk.Label(
                row, textvariable=var, font=("Helvetica", 9), wraplength=180
            ).pack(side="left", fill="x", expand=True)

        # Content Preview Section
        prev_section = ttk.Labelframe(parent, text=" Content Preview ", padding=6)
        prev_section.pack(fill="both", expand=True)

        self.prev_container = ttk.Frame(prev_section)
        self.prev_container.pack(fill="both", expand=True)

        # 1. Text Viewer (Text + Scrollbar in container)
        self.text_box = ttk.Frame(self.prev_container)
        self.text_scroll = ttk.Scrollbar(self.text_box, orient="vertical")
        self.text_preview = tk.Text(
            self.text_box,
            wrap="none",
            font=("Courier", 9),
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=self.text_scroll.set,
        )
        self.text_scroll.configure(command=self.text_preview.yview)
        self.text_scroll.pack(side="right", fill="y")
        self.text_preview.pack(side="left", fill="both", expand=True)

        # 2. Image / Visual Canvas
        self.image_preview_lbl = ttk.Label(
            self.prev_container, text="No preview available", anchor="center"
        )

        # Show empty placeholder initially
        self.image_preview_lbl.pack(fill="both", expand=True)

    # -------------------------------------------------------------------------
    # Status Bar
    # -------------------------------------------------------------------------
    def _build_status_bar(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side="bottom", fill="x")

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            padding=(16, 6),
            font=("Helvetica", 9),
        ).pack(side="left", fill="x", expand=True)

        self.sizegrip = ttk.Sizegrip(status_frame)
        self.sizegrip.pack(side="right", anchor="se", padx=2, pady=2)

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
        # Find item under cursor if clicking on tree
        item_id = self.table.identify_row(event.y)
        if item_id:
            self.table.selection_set(item_id)
            self._on_table_select(None)
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

            # Update Back/Forward button states
            self.btn_back.configure(state="normal" if self.history_back else "disabled")
            self.btn_forward.configure(
                state="normal" if self.history_forward else "disabled"
            )

            # Scan directory items
            self._scan_current_directory()
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
            show_hidden = self.show_hidden_var.get()
            with os.scandir(self.current_dir) as entries:
                for entry in entries:
                    if not show_hidden and entry.name.startswith("."):
                        continue
                    p = Path(entry.path)
                    items.append(get_file_info(p))
        except (PermissionError, OSError) as e:
            self.status_var.set(f"Scan warning: {e}")

        self.current_items = items

    def _refresh_content_views(self):
        """Filter, sort, and display items according to active search query and sort column."""
        filtered = self.current_items
        if self.search_query:
            query = self.search_query.lower()
            filtered = [it for it in filtered if query in it["name"].lower()]

        # Sort: Folders always first, then by selected column
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

        # Populate Details table
        self.table.delete(*self.table.get_children())
        for it in filtered:
            icon_prefix = it["icon"] + " "
            row_id = self.table.insert(
                "",
                "end",
                values=(
                    icon_prefix + it["name"],
                    it["size_str"],
                    it["category"],
                    it["mtime_str"],
                    it["permissions"],
                ),
            )
            # Store path in tag
            self.table.item(row_id, tags=(str(it["path"]),))

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

        # Clear existing grid content
        for widget in self.grid_frame.content.winfo_children():
            widget.destroy()

        columns_count = 4
        for idx, it in enumerate(items):
            row = idx // columns_count
            col = idx % columns_count

            # Card tile container
            card = tkblend.Card(self.grid_frame.content, padding=10)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            # Icon & Name
            lbl_icon = ttk.Label(card, text=it["icon"], font=("Helvetica", 24))
            lbl_icon.pack(pady=(4, 2))

            short_name = it["name"]
            if len(short_name) > 16:
                short_name = short_name[:13] + "..."
            lbl_name = ttk.Label(card, text=short_name, font=("Helvetica", 10, "bold"))
            lbl_name.pack()

            lbl_sub = ttk.Label(
                card,
                text=it["size_str"] if not it["is_dir"] else "Folder",
                font=("Helvetica", 8),
            )
            lbl_sub.pack(pady=(2, 4))

            # Bindings for selection and navigation
            for w in (card, lbl_icon, lbl_name, lbl_sub):
                w.bind("<Button-1>", lambda e, item=it: self._select_item(item))
                w.bind(
                    "<Double-Button-1>",
                    lambda e, item=it: self._on_item_double_click(item),
                )
                w.bind("<Button-3>", self._on_show_context_menu)

        for c in range(columns_count):
            self.grid_frame.content.columnconfigure(c, weight=1)

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
            self.text_box.pack_forget()
            self.image_preview_lbl.pack(fill="both", expand=True)
            try:
                sub_count = len(list(target_path.iterdir()))
                self.image_preview_lbl.configure(
                    image="",
                    text=f"📁 Folder\n\nContains {sub_count} items.\nDouble-click to browse folder.",
                    font=("Helvetica", 10),
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
                img.thumbnail((260, 240), Image.Resampling.LANCZOS)
                self._thumbnail_photo = ImageTk.PhotoImage(img)

                self.text_box.pack_forget()
                self.image_preview_lbl.pack(fill="both", expand=True)
                self.image_preview_lbl.configure(
                    image=self._thumbnail_photo,
                    text=f"\nImage Resolution: {img.width} × {img.height}",
                    compound="top",
                    font=("Helvetica", 9),
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
                    lines = [f.readline() for _ in range(300)]

                self.image_preview_lbl.pack_forget()
                self.text_box.pack(fill="both", expand=True)
                self.text_preview.delete("1.0", tk.END)

                # Format with line numbers for neat code display
                preview_lines = []
                for i, line in enumerate(lines, 1):
                    preview_lines.append(f"{i:4d} | {line}")
                self.text_preview.insert("1.0", "".join(preview_lines))
                return
            except Exception:
                pass

        # 4. Binary / Unsupported Preview Placeholder
        self.text_box.pack_forget()
        self.image_preview_lbl.pack(fill="both", expand=True)
        self.image_preview_lbl.configure(
            image="",
            text=f"⚙️ Binary / Structured File\n\nDirect preview not available.\nSize: {it['size_str']}",
            compound="none",
            font=("Helvetica", 10),
        )

    # -------------------------------------------------------------------------
    # Event Handlers & Actions
    # -------------------------------------------------------------------------
    def _on_table_select(self, event):
        sel = self.table.focus()
        if not sel:
            return
        tags = self.table.item(sel, "tags")
        if tags:
            selected_path = Path(tags[0])
            for it in self.current_items:
                if it["path"] == selected_path:
                    self._select_item(it)
                    break

    def _on_table_double_click(self, event):
        sel = self.table.focus()
        if not sel:
            return
        tags = self.table.item(sel, "tags")
        if tags:
            target = Path(tags[0])
            if target.is_dir():
                self.navigate_to(target)

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

    def _on_toggle_hidden(self):
        self._scan_current_directory()
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
        self._refresh_content_views()
        self.status_var.set(f"Refreshed: {self.current_dir.name}")

    def toggle_theme(self):
        """Toggle between Dark Mode and Light Mode with native Blend2D TTK theme."""
        self.is_dark = not self.is_dark
        tkblend.apply_theme(
            self.root, dark_mode=self.is_dark, enable_shadows=True, **_THEME_OPTS
        )
        self.btn_theme.configure(text="☀️ Light" if self.is_dark else "🌙 Dark")
        self.status_var.set(
            f"Theme switched to {'Dark' if self.is_dark else 'Light'} mode."
        )

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
                # Try common Linux terminal emulators
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


def main():
    root = tk.Tk()
    app = FileExplorerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
