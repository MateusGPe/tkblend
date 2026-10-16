#!/usr/bin/env python3
"""
Dedicated Blend2D Pure Vector Table Example & Interactive Test Harness.
Demonstrates:
  - Pure Blend2D subpixel vector typography and smooth rounded clipping
  - Interactive drag-to-resize column headers
  - Column sorting with ascending/descending indicators
  - Dual smart auto-hiding VectorScrollbars (vertical & horizontal)
  - Virtualized row rendering handling large datasets seamlessly
  - Configurable Single-select and Multi-select modes
  - Dynamic Theme Switching (Dark & Light)
  - Dynamic dataset mutation (add, clear, filter)
"""

from __future__ import annotations

import os
import random
import sys
import tkinter as tk
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import tkblend as tb
from tkblend.widgets import (
    Button,
    Card,
    Switch,
    Table,
    Label,
    SegmentedButton,
)


class TableDemoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("tkblend - Dedicated Vector Table Showcase")
        self.geometry("1020x760")
        self.minsize(800, 600)

        # Start in dark mode
        self._current_theme = "dark"
        tb.set_theme("dark")
        self.configure(bg=tb.get_theme().bg)

        self._row_counter = 1
        self._build_ui()

    def _build_ui(self):
        pal = tb.get_theme()

        # Header bar
        self.header_frame = tk.Frame(self, bg=pal.bg)
        self.header_frame.pack(fill="x", padx=24, pady=(20, 12))

        self.title_lbl = tk.Label(
            self.header_frame,
            text="Vector Data Table",
            font=("sans-serif", 18, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        )
        self.title_lbl.pack(side="left")

        self.sub_lbl = tk.Label(
            self.header_frame,
            text="Pure Blend2D surface rendering • Resizable columns • Virtualized scroll",
            font=("sans-serif", 10),
            fg=pal.text_muted,
            bg=pal.bg,
        )
        self.sub_lbl.pack(side="left", padx=(16, 0), pady=(4, 0))

        # Theme Switcher
        self.btn_theme = Button(
            self.header_frame,
            text="Switch to Light Theme",
            command=self._toggle_theme,
            width=170,
            height=34,
        )
        self.btn_theme.pack(side="right")

        # Control Toolbar
        toolbar_card = Card(self, height=64)
        toolbar_card.pack(fill="x", padx=24, pady=(0, 16))

        tool_content = tk.Frame(toolbar_card, bg=pal.card_bg)
        tool_content.pack(fill="both", expand=True, padx=18, pady=(10, 14))

        # Multi-select toggle
        self.sw_multi = Switch(
            tool_content,
            text="Multi-Select Mode",
            checked=False,
            command=self._on_multiselect_toggle,
            width=160,
            height=32,
        )
        self.sw_multi.pack(side="left", padx=(0, 16))

        # Zebra striping toggle
        self.sw_zebra = Switch(
            tool_content,
            text="Zebra Striping",
            checked=True,
            command=self._on_zebra_toggle,
            width=140,
            height=32,
        )
        self.sw_zebra.pack(side="left", padx=(0, 16))

        # Add 10 Rows
        self.btn_add_10 = Button(
            tool_content,
            text="+10 Rows",
            command=lambda: self._add_rows(10),
            width=90,
            height=32,
        )
        self.btn_add_10.pack(side="left", padx=(0, 8))

        # Add 100 Rows (Virtualization test)
        self.btn_add_100 = Button(
            tool_content,
            text="+100 Rows",
            command=lambda: self._add_rows(100),
            width=100,
            height=32,
        )
        self.btn_add_100.pack(side="left", padx=(0, 8))

        # Clear Selection
        self.btn_clear_sel = Button(
            tool_content,
            text="Clear Selection",
            command=self._clear_selection,
            width=120,
            height=32,
        )
        self.btn_clear_sel.pack(side="left", padx=(0, 8))

        # Reset Data
        self.btn_reset = Button(
            tool_content,
            text="Reset Data",
            command=self._reset_sample_data,
            width=100,
            height=32,
        )
        self.btn_reset.pack(side="right")

        # Main Table Card Container
        main_card = Card(self)
        main_card.pack(fill="both", expand=True, padx=24, pady=(0, 12))

        main_card_inner = tk.Frame(main_card, bg=pal.card_bg)
        main_card_inner.pack(fill="both", expand=True, padx=18, pady=16)

        self.table_header_lbl = tk.Label(
            main_card_inner,
            text="System Telemetry & Architecture Services (Double-click Service Name, Status, or Latency to edit)",
            font=("sans-serif", 12, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        self.table_header_lbl.pack(anchor="w", pady=(0, 8))

        # Initialize Table
        self.table = Table(
            main_card_inner,
            columns=[
                "ID",
                "Service Name",
                "Architecture",
                "Cluster Zone",
                "Status",
                "Latency (ms)",
                "Memory (MB)",
                "Uptime",
            ],
            data=[],
            command=self._on_table_select,
            editable_columns=["Service Name", "Status", "Latency (ms)"],
            column_editors={
                "Status": {
                    "type": "combobox",
                    "values": ["HEALTHY", "WARNING", "CRITICAL", "OFFLINE"],
                },
                "Service Name": "entry",
                "Latency (ms)": "entry",
            },
            on_cell_edit=self._on_cell_edit,
            height=320,
            corner_radius=8.0,
            row_height=34,
            header_height=38,
            scrollbar_width=9,
            sort_column=0,
            sort_ascending=True,
        )
        self.table.pack(fill="both", expand=True)

        # Status Bar Card
        status_card = Card(self, height=48)
        status_card.pack(fill="x", padx=24, pady=(0, 18))

        status_content = tk.Frame(status_card, bg=pal.card_bg)
        status_content.pack(fill="both", expand=True, padx=18, pady=(8, 12))

        self.lbl_status = tk.Label(
            status_content,
            text="Ready. Click rows to select, drag column borders to resize, or click headers to sort.",
            font=("sans-serif", 9),
            fg=pal.text_muted,
            bg=pal.card_bg,
            anchor="w",
        )
        self.lbl_status.pack(side="left", fill="x", expand=True)

        self.lbl_row_count = tk.Label(
            status_content,
            text="Total Rows: 0",
            font=("sans-serif", 9, "bold"),
            fg=pal.primary,
            bg=pal.card_bg,
        )
        self.lbl_row_count.pack(side="right")

        # Populate initial rows
        self._reset_sample_data()

    def _sample_records(self) -> list:
        records = [
            ("Core-Compositor", "Blend2D C++ Pipeline", "us-east-1a", "Healthy", 1.2, 48.5, "99.99%"),
            ("VectorRasterizer", "Direct Blit / Drawable", "us-east-1b", "Healthy", 0.8, 32.1, "100.00%"),
            ("GlyphLayoutEngine", "Native Subpixel HarfBuzz", "us-east-1c", "Healthy", 2.4, 64.0, "99.98%"),
            ("StyleResolver", "CSS Cascade Dynamic", "us-west-2a", "Warning", 8.7, 112.4, "98.75%"),
            ("InputDispatcher", "X11 / Win32 Native Event", "us-west-2b", "Healthy", 0.4, 16.2, "99.99%"),
            ("ThemeManager", "Palette Observer Token", "eu-central-1", "Healthy", 1.5, 24.8, "99.95%"),
            ("DisplayListCache", "DrawBatch FIFO Buffer", "eu-west-1", "Healthy", 0.9, 88.0, "99.99%"),
            ("ImageDecoder", "Async GIL-Scoped Loader", "ap-southeast", "Critical", 24.1, 256.3, "96.40%"),
            ("DpiTracker", "Process Scaling Monitor", "sa-east-1", "Healthy", 0.2, 8.4, "100.00%"),
            ("SurfaceRegistry", "Unique Handle UUID Map", "global-any", "Healthy", 0.6, 19.7, "99.99%"),
            ("EasingEngine", "Spring Physics Interp", "us-east-1a", "Healthy", 0.5, 12.0, "99.99%"),
            ("PathGeometry", "Cubic Bezier Arc Segment", "us-west-1", "Healthy", 1.1, 41.5, "99.96%"),
            ("CardLayerManager", "Native Window Stacking", "eu-west-2", "Healthy", 1.8, 38.9, "99.94%"),
            ("DropShadowRenderer", "Multi-pass Gaussian Blur", "ap-northeast", "Warning", 11.2, 180.2, "98.90%"),
        ]
        res = []
        for svc, arch, zone, st, lat, mem, up in records:
            res.append([f"SRV-{self._row_counter:04d}", svc, arch, zone, st, lat, mem, up])
            self._row_counter += 1
        return res

    def _reset_sample_data(self):
        self._row_counter = 1
        data = self._sample_records()
        self.table.data = data
        self._update_counter_label()
        self.lbl_status.config(text=f"Loaded {len(data)} sample records into table.")

    def _add_rows(self, count: int):
        services = ["CacheWorker", "MetricsCollector", "NetTunnel", "AuthProxy", "LogIngest", "BlobStash", "EventBridge"]
        archs = ["Blend2D Pipeline", "C++ Native Worker", "Direct Blitter", "Micro-Daemon", "Batch Streamer"]
        zones = ["us-east-1", "us-west-2", "eu-central-1", "ap-northeast-1"]
        statuses = ["Healthy", "Healthy", "Healthy", "Warning", "Critical"]

        new_rows = []
        for _ in range(count):
            svc = random.choice(services)
            arch = random.choice(archs)
            zone = random.choice(zones)
            st = random.choice(statuses)
            lat = round(random.uniform(0.3, 18.5), 1)
            mem = round(random.uniform(12.0, 320.0), 1)
            up = f"{round(random.uniform(97.0, 100.0), 2)}%"
            new_rows.append([f"SRV-{self._row_counter:04d}", svc, arch, zone, st, lat, mem, up])
            self._row_counter += 1

        self.table.data = self.table.data + new_rows
        self._update_counter_label()
        self.lbl_status.config(text=f"Appended {count} rows. Total rows: {len(self.table.data)}")

    def _clear_selection(self):
        self.table.clear_selection()
        self.lbl_status.config(text="Selection cleared.")

    def _on_multiselect_toggle(self, checked: bool):
        self.table.multi_select = checked
        mode_str = "Multi-Select (Ctrl / Shift + Click)" if checked else "Single-Select"
        self.lbl_status.config(text=f"Table selection mode changed to: {mode_str}")

    def _on_zebra_toggle(self, checked: bool):
        self.table.zebra_striping = checked
        self.lbl_status.config(text=f"Zebra striping {'enabled' if checked else 'disabled'}.")

    def _on_table_select(self, *args):
        if self.table.multi_select:
            sel_indices = self.table.selected_rows
            self.lbl_status.config(text=f"Multi-selected {len(sel_indices)} rows: indices {sel_indices[:8]}{'...' if len(sel_indices) > 8 else ''}")
        else:
            sel = self.table.get_selected()
            if sel:
                self.lbl_status.config(text=f"Selected row #{self.table.selected_row}: {sel[0]} - {sel[1]} [{sel[4]}] ({sel[5]}ms)")

    def _on_cell_edit(self, row: int, col: int, old_val: Any, new_val: Any) -> bool:
        col_name = self.table.columns[col] if col < len(self.table.columns) else f"Col {col}"
        self.lbl_status.config(text=f"Edited row #{row} [{col_name}]: '{old_val}' → '{new_val}'")
        return True

    def _update_counter_label(self):
        self.lbl_row_count.config(text=f"Total Rows: {len(self.table.data)}")

    def _toggle_theme(self):
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self._current_theme = new_theme
        tb.set_theme(new_theme)
        pal = tb.get_theme()
        self.configure(bg=pal.bg)
        self.header_frame.configure(bg=pal.bg)
        self.title_lbl.configure(fg=pal.fg, bg=pal.bg)
        self.sub_lbl.configure(fg=pal.text_muted, bg=pal.bg)
        self.table_header_lbl.configure(fg=pal.fg, bg=pal.card_bg)
        self.btn_theme.text = "Switch to Dark Theme" if new_theme == "light" else "Switch to Light Theme"
        tb.cascade_bg_to_children(self, pal.bg)
        self.lbl_status.config(fg=pal.text_muted, bg=pal.card_bg)
        self.lbl_row_count.config(fg=pal.primary, bg=pal.card_bg)


def main():
    app = TableDemoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
