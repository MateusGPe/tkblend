#!/usr/bin/env python3
"""
tkblend File Explorer Example.
Modern Blend2D-powered Pure Vector File Explorer.
Zero TTK dependencies.

Features:
- 3-Pane responsive layout with pure Blend2D Card and Frame containers
- Directory details Table with sortable column headers and file size formatting
- Rich preview panel with file metadata and text/code viewer (TextBox)
- Quick Access favorites and directory navigation tree
- Full navigation toolbar: Back, Forward, Up, Refresh, Path Entry, Live Search, Hidden Switch, Theme Selector
- Dynamic reactive theming supporting all tkblend palette presets
"""

from __future__ import annotations

import os
import sys
import stat
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import tkinter as tk

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkblend as tb
from tkblend import (
    Card,
    Button,
    Table,
    TextBox,
    Entry,
    SearchEntry,
    Switch,
    Badge,
    OptionMenu,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    ScalingTracker,
)


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024.0:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024.0 * 1024.0):.1f} MB"
    else:
        return f"{size_bytes / (1024.0 * 1024.0 * 1024.0):.1f} GB"


class FileExplorerApp(tk.Frame):
    """High-performance vector file manager."""

    def __init__(self, master: Optional[tk.Misc] = None, initial_dir: Optional[str] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._current_path = Path(initial_dir or os.getcwd()).resolve()
        self._history: List[Path] = [self._current_path]
        self._history_idx = 0
        self._show_hidden = False
        self._search_filter = ""
        self._files: List[Dict[str, Any]] = []

        self._build_ui()
        self._load_directory(self._current_path)

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Top Navigation Toolbar Card
        nav_card = Card(self, height=68)
        nav_card.pack(fill="x", padx=16, pady=(16, 8))

        nav_inner = tk.Frame(nav_card, bg=pal.card_bg)
        nav_inner.pack(fill="both", expand=True, padx=18, pady=(10, 14))

        # Back / Forward / Up buttons
        btn_back = Button(nav_inner, text="◀", width=36, height=30, command=self._nav_back)
        btn_back.pack(side="left", padx=(4, 2))

        btn_fwd = Button(nav_inner, text="▶", width=36, height=30, command=self._nav_forward)
        btn_fwd.pack(side="left", padx=2)

        btn_up = Button(nav_inner, text="▲", width=36, height=30, command=self._nav_up)
        btn_up.pack(side="left", padx=2)

        btn_refresh = Button(nav_inner, text="🔄", width=36, height=30, command=self._refresh)
        btn_refresh.pack(side="left", padx=2)

        # Path Entry Box
        self._path_entry = Entry(nav_inner, text=str(self._current_path), width=320, height=30)
        self._path_entry.pack(side="left", fill="x", expand=True, padx=8)
        self._path_entry.entry.bind("<Return>", self._on_path_entered)

        # Search Entry Box
        self._search_box = SearchEntry(nav_inner, placeholder="Search folder...", width=160, height=30)
        self._search_box.pack(side="left", padx=4)
        self._search_box.entry.bind("<KeyRelease>", self._on_search_typed)

        # Theme OptionMenu
        self._theme_opt = OptionMenu(
            nav_inner,
            values=sorted(get_available_themes()),
            current_value=pal.name,
            command=self._on_theme_change,
            width=120,
            height=30,
        )
        self._theme_opt.pack(side="right", padx=(6, 4))

        # Hidden switch
        self._hidden_switch = Switch(
            nav_inner,
            text="Hidden",
            is_checked=False,
            command=self._toggle_hidden,
            width=75,
            height=26,
        )
        self._hidden_switch.pack(side="right", padx=4)

        # Main Central Workspace (Sidebar + Table + Preview)
        workspace = tk.Frame(self, bg=pal.bg)
        workspace.pack(fill="both", expand=True, padx=16, pady=6)

        # 1. Left Sidebar: Quick Access
        sidebar_card = Card(workspace, width=190)
        sidebar_card.pack(side="left", fill="y", padx=(0, 8))

        sidebar_inner = tk.Frame(sidebar_card, bg=pal.card_bg)
        sidebar_inner.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(sidebar_inner, text="Quick Access", font=("sans-serif", 10, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", padx=6, pady=(4, 6))

        shortcuts = [
            ("🏠 Home", Path.home()),
            ("📁 Projects", Path.home() / "projects"),
            ("💻 Workspace", Path(os.getcwd())),
            ("📥 Downloads", Path.home() / "Downloads"),
            ("🖥️ Desktop", Path.home() / "Desktop"),
            ("⚙️ Root (/)", Path("/")),
        ]

        for label, target_path in shortcuts:
            btn = Button(
                sidebar_inner,
                text=label,
                width=150,
                height=28,
                command=lambda p=target_path: self._navigate_to(p),
            )
            btn.pack(fill="x", pady=2)

        # 2. Center: File Table Card
        table_card = Card(workspace)
        table_card.pack(side="left", fill="both", expand=True, padx=6)

        table_inner = tk.Frame(table_card, bg=pal.card_bg)
        table_inner.pack(fill="both", expand=True, padx=18, pady=16)

        cols = ["Name", "Type", "Size", "Modified"]
        self._file_table = Table(
            table_inner,
            columns=cols,
            column_widths=[240, 80, 80, 130],
            command=self._on_table_click,
        )
        self._file_table.pack(fill="both", expand=True)
        self._file_table.bind("<Double-Button-1>", self._on_double_click_item, add="+")

        # 3. Right: File Details & Preview Panel
        preview_card = Card(workspace, width=270)
        preview_card.pack(side="right", fill="y", padx=(8, 0))

        prev_inner = tk.Frame(preview_card, bg=pal.card_bg)
        prev_inner.pack(fill="both", expand=True, padx=18, pady=16)

        tk.Label(prev_inner, text="Item Details", font=("sans-serif", 10, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=(4, 4))

        self._lbl_prev_name = tk.Label(prev_inner, text="No selection", font=("sans-serif", 11, "bold"), bg=pal.card_bg, fg=pal.fg, wraplength=220)
        self._lbl_prev_name.pack(anchor="w", pady=2)

        self._badge_prev_type = Badge(prev_inner, text="FOLDER", variant="primary", height=20)
        self._badge_prev_type.pack(anchor="w", pady=4)

        self._lbl_prev_size = tk.Label(prev_inner, text="Size: -", font=("sans-serif", 9), bg=pal.card_bg, fg=pal.text_muted)
        self._lbl_prev_size.pack(anchor="w", pady=1)

        self._lbl_prev_mod = tk.Label(prev_inner, text="Modified: -", font=("sans-serif", 9), bg=pal.card_bg, fg=pal.text_muted)
        self._lbl_prev_mod.pack(anchor="w", pady=1)

        tk.Label(prev_inner, text="Content Snippet:", font=("sans-serif", 9, "bold"), bg=pal.card_bg, fg=pal.fg).pack(anchor="w", pady=(10, 2))

        self._preview_text = TextBox(prev_inner, width=220, height=200)
        self._preview_text.pack(fill="both", expand=True, pady=(2, 6))

        # Bottom Status Bar Card
        status_card = Card(self, height=48)
        status_card.pack(fill="x", padx=16, pady=(4, 16))

        status_inner = tk.Frame(status_card, bg=pal.card_bg)
        status_inner.pack(fill="both", expand=True, padx=18, pady=(8, 12))

        self._status_lbl = tk.Label(status_inner, text="Ready", font=("sans-serif", 9), bg=pal.card_bg, fg=pal.text_muted)
        self._status_lbl.pack(side="left")

        cascade_bg_to_children(self, pal.bg, palette=pal)

    def _load_directory(self, target_path: Path) -> None:
        try:
            target_path = target_path.resolve()
            if not target_path.exists() or not target_path.is_dir():
                return

            self._current_path = target_path
            self._path_entry.delete(0, "end")
            self._path_entry.insert(0, str(target_path))

            entries = []
            try:
                for entry in os.scandir(target_path):
                    if entry.name.startswith(".") and not self._show_hidden:
                        continue
                    if self._search_filter and self._search_filter.lower() not in entry.name.lower():
                        continue

                    try:
                        st = entry.stat()
                        is_dir = entry.is_dir()
                        entries.append({
                            "name": ("📁 " if is_dir else "📄 ") + entry.name,
                            "raw_name": entry.name,
                            "path": Path(entry.path),
                            "is_dir": is_dir,
                            "type": "Folder" if is_dir else (Path(entry.name).suffix.upper() or "File"),
                            "size": "--" if is_dir else format_file_size(st.st_size),
                            "size_bytes": 0 if is_dir else st.st_size,
                            "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
                        })
                    except Exception:
                        pass
            except PermissionError:
                pass

            # Sort folders first, then alphabetically
            entries.sort(key=lambda x: (not x["is_dir"], x["raw_name"].lower()))
            self._files = entries

            # Populate table data
            table_rows = [
                [e["name"], e["type"], e["size"], e["modified"]]
                for e in entries
            ]
            self._file_table.data = table_rows
            self._status_lbl.configure(text=f"{len(entries)} items | {str(target_path)}")

        except Exception as err:
            self._status_lbl.configure(text=f"Error loading path: {err}")

    def _navigate_to(self, path: Path) -> None:
        if path.exists() and path.is_dir():
            if self._history_idx < len(self._history) - 1:
                self._history = self._history[: self._history_idx + 1]
            self._history.append(path)
            self._history_idx = len(self._history) - 1
            self._load_directory(path)

    def _nav_back(self) -> None:
        if self._history_idx > 0:
            self._history_idx -= 1
            self._load_directory(self._history[self._history_idx])

    def _nav_forward(self) -> None:
        if self._history_idx < len(self._history) - 1:
            self._history_idx += 1
            self._load_directory(self._history[self._history_idx])

    def _nav_up(self) -> None:
        parent = self._current_path.parent
        if parent != self._current_path:
            self._navigate_to(parent)

    def _refresh(self) -> None:
        self._load_directory(self._current_path)

    def _on_path_entered(self, _event: tk.Event) -> None:
        entered = self._path_entry.get().strip()
        p = Path(entered).expanduser().resolve()
        if p.exists() and p.is_dir():
            self._navigate_to(p)
        else:
            self._path_entry.delete(0, "end")
            self._path_entry.insert(0, str(self._current_path))

    def _on_search_typed(self, _event: tk.Event) -> None:
        self._search_filter = self._search_box.get().strip()
        self._load_directory(self._current_path)

    def _toggle_hidden(self) -> None:
        self._show_hidden = self._hidden_switch.is_checked
        self._load_directory(self._current_path)

    def _on_table_click(self) -> None:
        idx = self._file_table.selected_row
        if idx is not None and 0 <= idx < len(self._files):
            self._show_preview(self._files[idx])

    def _show_preview(self, row_data: Dict[str, Any]) -> None:
        name = row_data.get("raw_name", "")
        is_dir = row_data.get("is_dir", False)
        fpath: Path = row_data.get("path", self._current_path / name)

        self._lbl_prev_name.configure(text=name)
        self._badge_prev_type.text = "FOLDER" if is_dir else row_data.get("type", "FILE")
        self._badge_prev_type.variant = "primary" if is_dir else "secondary"
        self._lbl_prev_size.configure(text=f"Size: {row_data.get('size', '--')}")
        self._lbl_prev_mod.configure(text=f"Modified: {row_data.get('modified', '--')}")

        self._preview_text.delete("1.0", "end")
        if not is_dir and fpath.exists():
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(2048)
                    self._preview_text.insert("1.0", content)
            except Exception:
                self._preview_text.insert("1.0", "[Binary or Unreadable File]")
        elif is_dir:
            self._preview_text.insert("1.0", f"Directory: {fpath}")

    def _on_double_click_item(self, _event: tk.Event) -> None:
        idx = self._file_table.selected_row
        if idx is not None and 0 <= idx < len(self._files):
            item = self._files[idx]
            if item.get("is_dir"):
                target: Path = item.get("path")
                if target:
                    self._navigate_to(target)

    def _on_theme_change(self, theme_name: str) -> None:
        set_theme(theme_name)
        pal = get_theme()
        self.configure(background=pal.bg)
        cascade_bg_to_children(self, pal.bg, palette=pal)
        self._file_table.request_redraw()
        self._path_entry.request_redraw()
        self._search_box.request_redraw()
        self._preview_text.request_redraw()


def main():
    root = tk.Tk()
    root.title("tkblend - Pure Vector File Explorer")
    root.geometry("1040x680")
    root.minsize(860, 540)

    app = FileExplorerApp(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
