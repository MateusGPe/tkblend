#!/usr/bin/env python3
"""
tkblend API Inspector — High-Performance Pure Vector REST Client
A practical, production-grade desktop HTTP inspector and API testing workbench.

Demonstrates real-world tkblend capabilities:
  - Zero-TTK pure Blend2D vector UI architecture
  - High-performance vector controls: Button, Entry, ComboBox, Table, Tabview, Card,
    TextBox, Sparkline, Badge, Switch, and ScrollableFrame
  - Semantic status badge variants (Success, Warning, Danger, Primary)
  - Interactive request history table with click-to-restore
  - Non-blocking threaded networking (urllib.request) with thread-safe GUI updates
  - Active Query Params URL compiler and Authorization Bearer header injector
  - Quick cURL generator and response clipboard export tools
  - Real-time latency sparkline charting response times
  - Comprehensive offline mock fallback for offline demos and testing
"""

from __future__ import annotations

import json
import os
import queue
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import tkinter as tk

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tkblend as tb
from tkblend import (
    Badge,
    Button,
    Card,
    ComboBox,
    Entry,
    Frame,
    Label,
    ScrollableFrame,
    Sparkline,
    Switch,
    Table,
    Tabview,
    TextBox,
    cascade_bg_to_children,
    get_theme,
    set_theme,
)


# ==============================================================================
# Sample Endpoints & Presets
# ==============================================================================

PRESETS = [
    {
        "name": "JSONPlaceholder: Fetch Post #1",
        "method": "GET",
        "url": "https://jsonplaceholder.typicode.com/posts/1",
        "headers": "Accept: application/json\nUser-Agent: tkblend-inspector/0.3",
        "params": "",
        "body": "",
    },
    {
        "name": "JSONPlaceholder: Fetch 10 Users",
        "method": "GET",
        "url": "https://jsonplaceholder.typicode.com/users",
        "headers": "Accept: application/json\nUser-Agent: tkblend-inspector/0.3",
        "params": "limit=10",
        "body": "",
    },
    {
        "name": "JSONPlaceholder: Create Post",
        "method": "POST",
        "url": "https://jsonplaceholder.typicode.com/posts",
        "headers": "Content-Type: application/json\nAccept: application/json",
        "params": "",
        "body": json.dumps(
            {
                "title": "tkblend High Performance Vector GUI",
                "body": "Zero-TTK Blend2D vector rendering for Python Tkinter.",
                "userId": 42,
            },
            indent=2,
        ),
    },
    {
        "name": "GitHub API: Zen Quote",
        "method": "GET",
        "url": "https://api.github.com/zen",
        "headers": "User-Agent: tkblend-inspector/0.3\nAccept: text/plain",
        "params": "",
        "body": "",
    },
    {
        "name": "HTTPBin: Echo Request Headers",
        "method": "GET",
        "url": "https://httpbin.org/headers",
        "headers": "X-Client: tkblend-0.3\nX-Vector-Engine: Blend2D",
        "params": "",
        "body": "",
    },
    {
        "name": "HTTPBin: Delayed Response (1s)",
        "method": "GET",
        "url": "https://httpbin.org/delay/1",
        "headers": "Accept: application/json",
        "params": "",
        "body": "",
    },
    {
        "name": "HTTPBin: Simulate 404 Not Found",
        "method": "GET",
        "url": "https://httpbin.org/status/404",
        "headers": "Accept: text/plain",
        "params": "",
        "body": "",
    },
    {
        "name": "Offline Mock: User Profile",
        "method": "GET",
        "url": "https://mock.local/api/v1/users/42",
        "headers": "Accept: application/json",
        "params": "",
        "body": "",
    },
    {
        "name": "Offline Mock: Create Order",
        "method": "POST",
        "url": "https://mock.local/api/v1/orders",
        "headers": "Content-Type: application/json",
        "params": "",
        "body": json.dumps(
            {
                "order_id": "ORD-9482",
                "item": "Blend2D Vector Graphics Core",
                "quantity": 1,
                "tier": "enterprise",
            },
            indent=2,
        ),
    },
]


# ==============================================================================
# Offline Mock Service
# ==============================================================================

def generate_mock_response(method: str, url: str, body: str) -> Tuple[int, str, Dict[str, str], str]:
    """Generate realistic offline mock response when offline or testing mock URLs."""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/")
    now = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Date": now,
        "Server": "tkblend-mock-daemon/1.0",
        "X-Powered-By": "Blend2D-Vector-Engine",
        "Connection": "close",
    }

    if "users" in path:
        data = {
            "id": 42,
            "username": "blend_master",
            "name": "Alex Mercer",
            "email": "alex.mercer@blend2d.org",
            "role": "Lead Systems Architect",
            "status": "active",
            "features": ["zero-ttk", "subpixel-antialiasing", "gpu-surface-blit"],
            "stats": {"requests_served": 128450, "uptime_hours": 742.5},
        }
        return 200, "OK", headers, json.dumps(data, indent=2)

    elif "orders" in path:
        try:
            req_json = json.loads(body) if body else {}
        except Exception:
            req_json = {"raw": body}
        data = {
            "status": "success",
            "message": "Order created successfully in mock database.",
            "order_id": req_json.get("order_id", "ORD-1001"),
            "created_at": time.time(),
            "details": req_json,
        }
        return 201, "Created", headers, json.dumps(data, indent=2)

    else:
        data = {
            "message": "Offline Mock Service Active",
            "method": method,
            "url": url,
            "simulated_at": now,
            "engine": "Blend2D 2D Vector Rasterizer",
            "tip": "Disable 'Offline Mock' in the header to send live network requests.",
        }
        return 200, "OK", headers, json.dumps(data, indent=2)


# ==============================================================================
# Main Application Class
# ==============================================================================

class APIInspectorApp(tk.Tk):
    """Production-grade REST Client & API Inspector showcase application."""

    def __init__(self):
        super().__init__()
        self.title("tkblend API Inspector — High-Performance Vector REST Client")
        self.geometry("1220x840")
        self.minsize(1020, 700)

        # Apply initial cinematic theme
        self._current_theme = "cinematic"
        set_theme("cinematic")
        pal = get_theme()
        self.configure(bg=pal.bg)

        # Available themes
        self._avail_themes = sorted(tb.get_available_themes())
        if "debug" in self._avail_themes:
            self._avail_themes.remove("debug")

        # Concurrency & History state
        self._history_records: List[Dict[str, Any]] = []
        self._history_counter: int = 1
        self._latencies: List[float] = [45.0, 68.0, 52.0]
        self._is_request_in_flight: bool = False
        self._mock_mode: bool = False
        self._response_queue: queue.Queue[Dict[str, Any]] = queue.Queue()

        self.bind("<<RequestComplete>>", self._on_request_event)

        self._build_ui()
        cascade_bg_to_children(self, get_theme().bg)

        # Pre-seed history with 3 initial records for immediate rich demo experience
        self._seed_initial_history()

        # Load first preset into the editor
        self._apply_preset(PRESETS[0])

    # --------------------------------------------------------------------------
    # Status Badge Variant Helper
    # --------------------------------------------------------------------------

    @staticmethod
    def _status_variant(status_code: int) -> str:
        """Map HTTP status codes to semantic badge variant styles."""
        if status_code == 0:
            return "danger"
        elif 200 <= status_code < 300:
            return "success"
        elif 300 <= status_code < 400:
            return "warning"
        elif 400 <= status_code < 600:
            return "danger"
        return "primary"

    # --------------------------------------------------------------------------
    # UI Layout Construction
    # --------------------------------------------------------------------------

    def _build_ui(self):
        pal = get_theme()

        # ----------------------------------------------------------------------
        # 1. Header Bar
        # ----------------------------------------------------------------------
        header = tk.Frame(self, bg=pal.bg)
        header.pack(fill="x", padx=20, pady=(14, 10))

        # Title & Badges
        title_box = tk.Frame(header, bg=pal.bg)
        title_box.pack(side="left", fill="y")

        tag_badge = Badge(title_box, text="REST CLIENT", variant="primary", width=100, height=24)
        tag_badge.pack(side="left", padx=(0, 10))

        self.title_lbl = tk.Label(
            title_box,
            text="API Inspector",
            font=("sans-serif", 18, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        )
        self.title_lbl.pack(side="left")

        version_badge = Badge(title_box, text=f"v{tb.__version__}", width=62, height=24)
        version_badge.pack(side="left", padx=10)

        self.subtitle_lbl = tk.Label(
            title_box,
            text="• Pure Blend2D Surface UI",
            font=("sans-serif", 10),
            fg=getattr(pal, "text_muted", pal.fg_subtle),
            bg=pal.bg,
        )
        self.subtitle_lbl.pack(side="left")

        # Header Right Controls: Offline Switch & Theme Selector
        right_box = tk.Frame(header, bg=pal.bg)
        right_box.pack(side="right")

        # Adequate width (148px) ensures toggle track + text never truncates
        self.mock_switch = Switch(
            right_box,
            text="Offline Mock",
            is_checked=False,
            command=self._on_toggle_mock_mode,
            width=148,
            height=30,
        )
        self.mock_switch.pack(side="left", padx=(0, 18))

        self.theme_lbl = tk.Label(
            right_box,
            text="Theme:",
            font=("sans-serif", 10, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        )
        self.theme_lbl.pack(side="left", padx=(0, 8))

        self.theme_combo = ComboBox(
            right_box,
            values=[t.replace("_", " ").title() for t in self._avail_themes],
            value="Cinematic",
            command=self._on_theme_selected,
            width=150,
            height=32,
        )
        self.theme_combo.pack(side="left")

        # ----------------------------------------------------------------------
        # 2. Main Workspace Split (Sidebar + Main Stage)
        # ----------------------------------------------------------------------
        workspace = tk.Frame(self, bg=pal.bg)
        workspace.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # --- LEFT SIDEBAR (Comfortable 350px width for clean table columns) ---
        self.sidebar_frame = tk.Frame(workspace, bg=pal.bg, width=350)
        self.sidebar_frame.pack(side="left", fill="both", padx=(0, 14))
        self.sidebar_frame.pack_propagate(False)

        # Sidebar Card 1: Presets
        presets_card = Card(self.sidebar_frame, height=140)
        presets_card.pack(fill="x", pady=(0, 10))

        p_inner = tk.Frame(presets_card, bg=pal.card_bg)
        p_inner.pack(fill="both", expand=True, padx=18, pady=16)

        self.preset_title_lbl = tk.Label(
            p_inner,
            text="Quick Presets",
            font=("sans-serif", 11, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        self.preset_title_lbl.pack(anchor="w", pady=(0, 6))

        preset_names = [p["name"] for p in PRESETS]
        self.preset_combo = ComboBox(
            p_inner,
            values=preset_names,
            value=preset_names[0],
            command=self._on_preset_selected,
            width=305,
            height=32,
        )
        self.preset_combo.pack(fill="x", pady=(0, 6))

        btn_apply_preset = Button(
            p_inner,
            text="Load Preset to Editor",
            command=self._load_current_preset,
            height=28,
        )
        btn_apply_preset.pack(fill="x")

        # Sidebar Card 2: Request History with Table
        history_card = Card(self.sidebar_frame)
        history_card.pack(fill="both", expand=True)

        h_inner = tk.Frame(history_card, bg=pal.card_bg)
        h_inner.pack(fill="both", expand=True, padx=18, pady=16)

        h_top = tk.Frame(h_inner, bg=pal.card_bg)
        h_top.pack(fill="x", pady=(0, 6))

        self.history_title_lbl = tk.Label(
            h_top,
            text="Request History",
            font=("sans-serif", 11, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        self.history_title_lbl.pack(side="left")

        btn_clear_hist = Button(
            h_top,
            text="Clear",
            command=self._clear_history,
            width=58,
            height=26,
            auto_fit=True,
        )
        btn_clear_hist.pack(side="right")

        # Pure Blend2D History Table with generously sized column widths
        self.history_table = Table(
            h_inner,
            columns=["#", "Method", "Status", "Time", "Endpoint"],
            column_widths=[28, 62, 58, 54, 116],
            data=[],
            command=self._on_history_row_clicked,
            row_height=28,
            header_height=30,
            scrollbar_width=6,
            corner_radius=6.0,
            zebra_striping=True,
            multi_select=False,
        )
        self.history_table.pack(fill="both", expand=True)

        self.hist_hint_lbl = tk.Label(
            h_inner,
            text="Click a row above to restore request & response.",
            font=("sans-serif", 8),
            fg=getattr(pal, "text_muted", pal.fg_subtle),
            bg=pal.card_bg,
        )
        self.hist_hint_lbl.pack(anchor="w", pady=(6, 0))

        # --- RIGHT MAIN STAGE ---
        self.stage_frame = tk.Frame(workspace, bg=pal.bg)
        self.stage_frame.pack(side="right", fill="both", expand=True)

        # 1. URL Request Bar Card
        url_card = Card(self.stage_frame, height=68)
        url_card.pack(fill="x", pady=(0, 10))

        url_inner = tk.Frame(url_card, bg=pal.card_bg)
        url_inner.pack(fill="both", expand=True, padx=18, pady=(10, 14))

        self.method_combo = ComboBox(
            url_inner,
            values=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
            value="GET",
            command=self._on_method_changed,
            width=88,
            height=34,
        )
        self.method_combo.pack(side="left", padx=(0, 8))

        self.url_entry = Entry(
            url_inner,
            placeholder="Enter request URL (e.g. https://api.example.com/v1/data)",
            font=("sans-serif", 10),
            height=34,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.url_entry.bind("<Return>", lambda e: self._on_send_clicked())

        self.curl_btn = Button(
            url_inner,
            text="Copy cURL",
            command=self._copy_curl,
            width=95,
            height=34,
            auto_fit=True,
        )
        self.curl_btn.pack(side="right", padx=(8, 0))

        self.send_btn = Button(
            url_inner,
            text="Send Request",
            variant="primary",
            command=self._on_send_clicked,
            width=120,
            height=34,
            auto_fit=True,
        )
        self.send_btn.pack(side="right")

        # 2. Request Configuration Tabview
        self.req_tabs = Tabview(self.stage_frame, height=160)
        self.req_tabs.pack(fill="x", pady=(0, 10))

        # Tab: Headers
        tab_headers = self.req_tabs.add("Headers")
        self.headers_text = TextBox(tab_headers, font=("monospace", 9), height=110)
        self.headers_text.pack(fill="both", expand=True)

        # Tab: JSON Body
        tab_body = self.req_tabs.add("JSON Body")
        body_ctrl_box = tk.Frame(tab_body, bg=pal.bg)
        body_ctrl_box.pack(fill="x", pady=(0, 4))

        btn_format_json = Button(
            body_ctrl_box,
            text="Format JSON",
            command=self._format_request_json,
            width=110,
            height=28,
            auto_fit=True,
        )
        btn_format_json.pack(side="left", padx=(0, 6))

        btn_clear_body = Button(
            body_ctrl_box,
            text="Clear Body",
            command=lambda: self.body_text.delete("1.0", "end"),
            width=95,
            height=28,
            auto_fit=True,
        )
        btn_clear_body.pack(side="left")

        self.body_text = TextBox(tab_body, font=("monospace", 9), height=95)
        self.body_text.pack(fill="both", expand=True)

        # Tab: Query Params (Fully active and merged into request URL)
        tab_params = self.req_tabs.add("Query Params")
        self.params_text = TextBox(tab_params, font=("monospace", 9), height=110)
        self.params_text.pack(fill="both", expand=True)
        self.params_text.insert(
            "1.0",
            "# Enter query parameters (key=value, one per line):\npage=1\nlimit=20\n",
        )

        # Tab: Auth (Bearer Token / Basic Auth quick builder)
        tab_auth = self.req_tabs.add("Auth")
        auth_inner = tk.Frame(tab_auth, bg=pal.bg)
        auth_inner.pack(fill="both", expand=True, padx=8, pady=6)

        auth_top = tk.Frame(auth_inner, bg=pal.bg)
        auth_top.pack(fill="x", pady=(0, 6))

        self.auth_type_lbl = tk.Label(
            auth_top,
            text="Type:",
            font=("sans-serif", 9, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        )
        self.auth_type_lbl.pack(side="left", padx=(0, 8))

        self.auth_combo = ComboBox(
            auth_top,
            values=["None", "Bearer Token"],
            value="None",
            width=115,
            height=28,
        )
        self.auth_combo.pack(side="left", padx=(0, 14))

        self.auth_token_lbl = tk.Label(
            auth_top,
            text="Token:",
            font=("sans-serif", 9),
            fg=pal.fg,
            bg=pal.bg,
        )
        self.auth_token_lbl.pack(side="left", padx=(0, 6))

        self.auth_entry = Entry(
            auth_top,
            placeholder="Paste bearer token or API key...",
            font=("monospace", 9),
            height=28,
        )
        self.auth_entry.pack(side="left", fill="x", expand=True)

        self.auth_hint_lbl = tk.Label(
            auth_inner,
            text="When 'Bearer Token' is selected, 'Authorization: Bearer <token>' is automatically injected.",
            font=("sans-serif", 8),
            fg=getattr(pal, "text_muted", pal.fg_subtle),
            bg=pal.bg,
            anchor="w",
        )
        self.auth_hint_lbl.pack(fill="x")

        # 3. Response Inspector Card
        resp_card = Card(self.stage_frame)
        resp_card.pack(fill="both", expand=True)

        resp_inner = tk.Frame(resp_card, bg=pal.card_bg)
        resp_inner.pack(fill="both", expand=True, padx=18, pady=16)

        # Response Top Metrics Bar
        resp_metrics = tk.Frame(resp_inner, bg=pal.card_bg)
        resp_metrics.pack(fill="x", pady=(0, 8))

        # Status badge with semantic variant color-coding
        self.status_badge = Badge(resp_metrics, text="READY", variant="default", width=125, height=26)
        self.status_badge.pack(side="left", padx=(0, 8))

        # Latency badge
        self.time_badge = Badge(resp_metrics, text="0 ms", width=80, height=26)
        self.time_badge.pack(side="left", padx=(0, 8))

        # Size badge
        self.size_badge = Badge(resp_metrics, text="0 B", width=80, height=26)
        self.size_badge.pack(side="left", padx=(0, 14))

        # Sparkline Latency History
        self.spark_lbl = tk.Label(
            resp_metrics,
            text="Latency Trend:",
            font=("sans-serif", 9),
            fg=getattr(pal, "text_muted", pal.fg_subtle),
            bg=pal.card_bg,
        )
        self.spark_lbl.pack(side="left", padx=(0, 6))

        self.sparkline = Sparkline(
            resp_metrics,
            data=self._latencies,
            width=140,
            height=28,
        )
        self.sparkline.pack(side="left")

        # Response Viewers (Tabview)
        self.resp_tabs = Tabview(resp_inner)
        self.resp_tabs.pack(fill="both", expand=True)

        # Tab: Response Body
        tab_resp_body = self.resp_tabs.add("Response Body")

        resp_body_bar = tk.Frame(tab_resp_body, bg=pal.bg)
        resp_body_bar.pack(fill="x", pady=(0, 4))

        btn_copy_body = Button(
            resp_body_bar,
            text="Copy Body",
            command=self._copy_response_body,
            width=95,
            height=28,
            auto_fit=True,
        )
        btn_copy_body.pack(side="left", padx=(0, 6))

        btn_fmt_body = Button(
            resp_body_bar,
            text="Format JSON",
            command=self._format_response_json,
            width=110,
            height=28,
            auto_fit=True,
        )
        btn_fmt_body.pack(side="left")

        self.resp_body_text = TextBox(tab_resp_body, font=("monospace", 9))
        self.resp_body_text.pack(fill="both", expand=True)
        self.resp_body_text.insert(
            "1.0",
            "// Response payload will appear here after sending a request.\n"
            "// Ready to inspect real APIs or test with built-in presets.",
        )

        # Tab: Response Headers
        tab_resp_hdrs = self.resp_tabs.add("Headers")

        resp_hdrs_bar = tk.Frame(tab_resp_hdrs, bg=pal.bg)
        resp_hdrs_bar.pack(fill="x", pady=(0, 4))

        btn_copy_hdrs = Button(
            resp_hdrs_bar,
            text="Copy Headers",
            command=self._copy_response_headers,
            width=110,
            height=28,
            auto_fit=True,
        )
        btn_copy_hdrs.pack(side="left")

        self.resp_headers_text = TextBox(tab_resp_hdrs, font=("monospace", 9))
        self.resp_headers_text.pack(fill="both", expand=True)

        # Tab: Connection Info / Diagnostics
        tab_resp_info = self.resp_tabs.add("Diagnostics")

        resp_diag_bar = tk.Frame(tab_resp_info, bg=pal.bg)
        resp_diag_bar.pack(fill="x", pady=(0, 4))

        btn_copy_diag = Button(
            resp_diag_bar,
            text="Copy Report",
            command=self._copy_diagnostics,
            width=105,
            height=28,
            auto_fit=True,
        )
        btn_copy_diag.pack(side="left")

        self.resp_info_text = TextBox(tab_resp_info, font=("monospace", 9))
        self.resp_info_text.pack(fill="both", expand=True)

        # ----------------------------------------------------------------------
        # 3. Status Footer
        # ----------------------------------------------------------------------
        footer = tk.Frame(self, bg=pal.bg)
        footer.pack(fill="x", padx=20, pady=(4, 10))

        self.footer_status = tk.Label(
            footer,
            text="Ready. Select a preset or type a URL, then click Send Request (or press Enter).",
            font=("sans-serif", 9),
            fg=getattr(pal, "text_muted", pal.fg_subtle),
            bg=pal.bg,
            anchor="w",
        )
        self.footer_status.pack(side="left", fill="x", expand=True)

        self.footer_count = tk.Label(
            footer,
            text="Total Requests: 0",
            font=("sans-serif", 9, "bold"),
            fg=pal.primary,
            bg=pal.bg,
        )
        self.footer_count.pack(side="right")

    # --------------------------------------------------------------------------
    # Initial Pre-seeded History
    # --------------------------------------------------------------------------

    def _seed_initial_history(self):
        """Pre-populate 3 realistic request records so the workbench is active on launch."""
        demo_records = [
            {
                "id": 1,
                "method": "GET",
                "status": "200",
                "status_text": "200 OK",
                "time": "45ms",
                "elapsed_ms": 45.0,
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "headers_req": "Accept: application/json\nUser-Agent: tkblend-inspector/0.3",
                "body_req": "",
                "resp_body": json.dumps(
                    {
                        "userId": 1,
                        "id": 1,
                        "title": "sunt aut facere repellat provident occaecati excepturi optio",
                        "body": "quia et suscipit suscipit recusandae consequuntur expedita et cum...",
                    },
                    indent=2,
                ),
                "resp_headers": "content-type: application/json; charset=utf-8\nserver: cloudflare\ncache-control: max-age=43200",
                "size_str": "292 B",
            },
            {
                "id": 2,
                "method": "POST",
                "status": "201",
                "status_text": "201 Created",
                "time": "68ms",
                "elapsed_ms": 68.0,
                "url": "https://jsonplaceholder.typicode.com/posts",
                "headers_req": "Content-Type: application/json\nAccept: application/json",
                "body_req": json.dumps({"title": "tkblend High Performance Vector GUI", "userId": 42}, indent=2),
                "resp_body": json.dumps({"id": 101, "title": "tkblend High Performance Vector GUI", "userId": 42}, indent=2),
                "resp_headers": "content-type: application/json; charset=utf-8\nserver: cloudflare\nlocation: /posts/101",
                "size_str": "142 B",
            },
            {
                "id": 3,
                "method": "GET",
                "status": "200",
                "status_text": "200 OK",
                "time": "52ms",
                "elapsed_ms": 52.0,
                "url": "https://api.github.com/zen",
                "headers_req": "User-Agent: tkblend-inspector/0.3\nAccept: text/plain",
                "body_req": "",
                "resp_body": "Design for failure.",
                "resp_headers": "content-type: text/plain; charset=utf-8\nserver: github.com\nx-github-media-type: github.v3",
                "size_str": "19 B",
            },
        ]

        table_rows = []
        for r in demo_records:
            self._history_records.append(r)
            parsed_path = urllib.parse.urlparse(r["url"]).path or "/"
            table_rows.append([str(r["id"]), r["method"], r["status"], r["time"], parsed_path])

        self._history_counter = len(demo_records) + 1
        self.history_table.data = table_rows
        self.footer_count.config(text=f"Total Requests: {len(self._history_records)}")

        # Select first record to populate response viewer
        first = demo_records[0]
        self.status_badge.text = first["status_text"]
        self.status_badge.variant = self._status_variant(200)
        self.time_badge.text = first["time"]
        self.size_badge.text = first["size_str"]
        self.resp_body_text.delete("1.0", "end")
        self.resp_body_text.insert("1.0", first["resp_body"])
        self.resp_headers_text.delete("1.0", "end")
        self.resp_headers_text.insert("1.0", first["resp_headers"])

        # Populate diagnostics
        diag_lines = [
            f"Requested URL : {first['url']}",
            f"HTTP Method   : {first['method']}",
            f"Status Code   : {first['status_text']}",
            f"Round-trip    : {first['elapsed_ms']} ms",
            f"Payload Size  : {first['size_str']}",
            "Mock Mode     : Disabled (Pre-seeded Demo)",
            f"Timestamp     : {time.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        self.resp_info_text.delete("1.0", "end")
        self.resp_info_text.insert("1.0", "\n".join(diag_lines))

    # --------------------------------------------------------------------------
    # Preset Handling & Method Switching
    # --------------------------------------------------------------------------

    def _on_method_changed(self, method: str):
        method_upper = method.strip().upper()
        if method_upper in ("POST", "PUT", "PATCH"):
            self.req_tabs.set("JSON Body")
        elif method_upper in ("GET", "HEAD") and not self.body_text.get("1.0", "end-1c").strip():
            self.req_tabs.set("Headers")

    def _on_preset_selected(self, chosen: str):
        for p in PRESETS:
            if p["name"] == chosen:
                self._apply_preset(p)
                break

    def _load_current_preset(self):
        chosen = self.preset_combo.value
        self._on_preset_selected(chosen)

    def _apply_preset(self, p: Dict[str, str]):
        self.method_combo.set(p.get("method", "GET"))
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, p.get("url", ""))

        self.headers_text.delete("1.0", "end")
        if p.get("headers"):
            self.headers_text.insert("1.0", p["headers"])

        self.params_text.delete("1.0", "end")
        if p.get("params"):
            self.params_text.insert("1.0", p["params"])
        else:
            self.params_text.insert("1.0", "# Enter query parameters (key=value, one per line):\n")

        self.body_text.delete("1.0", "end")
        if p.get("body"):
            self.body_text.insert("1.0", p["body"])

        if p.get("body"):
            self.req_tabs.set("JSON Body")
        else:
            self.req_tabs.set("Headers")

        self.footer_status.config(text=f"Loaded preset: '{p['name']}'")

    # --------------------------------------------------------------------------
    # Clipboard & cURL Helpers
    # --------------------------------------------------------------------------

    def _copy_to_clipboard(self, text: str, confirmation_msg: str):
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()  # ensure clipboard update
            self.footer_status.config(text=confirmation_msg)
        except Exception as e:
            self.footer_status.config(text=f"Clipboard error: {e}")

    def _copy_response_body(self):
        content = self.resp_body_text.get("1.0", "end-1c")
        self._copy_to_clipboard(content, "Copied response body to clipboard.")

    def _copy_response_headers(self):
        content = self.resp_headers_text.get("1.0", "end-1c")
        self._copy_to_clipboard(content, "Copied response headers to clipboard.")

    def _copy_diagnostics(self):
        content = self.resp_info_text.get("1.0", "end-1c")
        self._copy_to_clipboard(content, "Copied connection diagnostics to clipboard.")

    def _copy_curl(self):
        """Generate ready-to-run cURL terminal command from editor state."""
        method = self.method_combo.value.strip().upper()
        raw_url = self._build_effective_url()
        headers_dict = self._get_request_headers_dict()
        body_str = self.body_text.get("1.0", "end-1c").strip()

        parts = [f"curl -X {method} '{raw_url}'"]
        for k, v in headers_dict.items():
            parts.append(f"  -H '{k}: {v}'")
        if method in ("POST", "PUT", "PATCH") and body_str:
            escaped = body_str.replace("'", "'\\''")
            parts.append(f"  -d '{escaped}'")

        curl_cmd = " \\\n".join(parts)
        self._copy_to_clipboard(curl_cmd, "Copied ready-to-run cURL command to clipboard.")

    def _build_effective_url(self) -> str:
        """Combine URL entry and active Query Params tab entries into a valid URL."""
        raw_url = self.url_entry.get().strip()
        if not raw_url:
            return ""
        if not raw_url.startswith(("http://", "https://")):
            raw_url = "https://" + raw_url

        # Parse query params tab
        params_str = self.params_text.get("1.0", "end-1c").strip()
        param_pairs = []
        for line in params_str.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                param_pairs.append((k.strip(), v.strip()))
            elif line:
                param_pairs.append((line, ""))

        if param_pairs:
            qs = urllib.parse.urlencode(param_pairs)
            sep = "&" if "?" in raw_url else "?"
            raw_url = f"{raw_url}{sep}{qs}"

        return raw_url

    def _get_request_headers_dict(self) -> Dict[str, str]:
        """Parse Headers tab and inject Auth tab token if configured."""
        headers_str = self.headers_text.get("1.0", "end-1c")
        headers_dict: Dict[str, str] = {}
        for line in headers_str.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and ":" in line:
                k, v = line.split(":", 1)
                headers_dict[k.strip()] = v.strip()

        # Bearer token auth injection
        auth_type = getattr(self, "auth_combo", None)
        if auth_type and auth_type.value == "Bearer Token":
            tok = self.auth_entry.get().strip()
            if tok and "Authorization" not in headers_dict:
                headers_dict["Authorization"] = f"Bearer {tok}"

        return headers_dict

    # --------------------------------------------------------------------------
    # Formatting Helpers
    # --------------------------------------------------------------------------

    def _format_request_json(self):
        raw = self.body_text.get("1.0", "end-1c").strip()
        if not raw:
            return
        try:
            parsed = json.loads(raw)
            formatted = json.dumps(parsed, indent=2)
            self.body_text.delete("1.0", "end")
            self.body_text.insert("1.0", formatted)
            self.footer_status.config(text="Formatted request JSON successfully.")
        except Exception as e:
            self.footer_status.config(text=f"Invalid request JSON: {e}")

    def _format_response_json(self):
        raw = self.resp_body_text.get("1.0", "end-1c").strip()
        if not raw:
            return
        try:
            parsed = json.loads(raw)
            formatted = json.dumps(parsed, indent=2)
            self.resp_body_text.delete("1.0", "end")
            self.resp_body_text.insert("1.0", formatted)
            self.footer_status.config(text="Formatted response JSON successfully.")
        except Exception as e:
            self.footer_status.config(text=f"Response body is not valid JSON: {e}")

    def _on_toggle_mock_mode(self):
        self._mock_mode = self.mock_switch.is_checked
        status = "ENABLED (Requests resolved locally)" if self._mock_mode else "DISABLED (Live network requests)"
        self.footer_status.config(text=f"Offline Mock Mode {status}")

    # --------------------------------------------------------------------------
    # Network Execution & Threading
    # --------------------------------------------------------------------------

    def _on_send_clicked(self):
        if self._is_request_in_flight:
            return

        method = self.method_combo.value.strip().upper()
        effective_url = self._build_effective_url()

        if not effective_url:
            self.footer_status.config(text="Error: URL cannot be empty.")
            return

        # Synchronize back to entry if query params were appended
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, effective_url)

        headers_dict = self._get_request_headers_dict()
        body_str = self.body_text.get("1.0", "end-1c")

        # Update UI to in-flight state
        self._is_request_in_flight = True
        self.send_btn.text = "Sending..."
        self.send_btn.is_disabled = True
        self.status_badge.text = "SENDING..."
        self.status_badge.variant = "primary"
        self.footer_status.config(text=f"Connecting to {urllib.parse.urlparse(effective_url).netloc}...")

        # Schedule queue poller in main thread
        self.after(25, self._check_response_queue)

        # Spawn background worker thread
        thread = threading.Thread(
            target=self._worker_execute_request,
            args=(method, effective_url, headers_dict, body_str, self._mock_mode),
            daemon=True,
        )
        thread.start()

    def _check_response_queue(self):
        """Poll and drain response queue on main Tkinter thread."""
        while not self._response_queue.empty():
            try:
                res = self._response_queue.get_nowait()
                self._on_request_finished(res)
            except queue.Empty:
                break
        if self._is_request_in_flight:
            self.after(25, self._check_response_queue)

    def _on_request_event(self, event=None):
        """Immediate event-triggered queue drain."""
        self._check_response_queue()

    def _dispatch_result(self, result: Dict[str, Any]):
        """Safely push result from background thread to main Tkinter thread."""
        self._response_queue.put(result)
        try:
            self.event_generate("<<RequestComplete>>", when="tail")
        except Exception:
            pass

    def _worker_execute_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body_str: str,
        mock_mode: bool,
    ):
        start_time = time.perf_counter()

        # Check if offline mock requested or url is mock
        if mock_mode or "mock.local" in url:
            time.sleep(0.045)  # Simulate small network roundtrip
            status_code, reason, resp_headers, resp_body = generate_mock_response(method, url, body_str)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result = {
                "success": True,
                "status_code": status_code,
                "reason": reason,
                "headers": resp_headers,
                "body": resp_body,
                "elapsed_ms": round(elapsed_ms, 1),
                "url": url,
                "method": method,
                "is_mock": True,
            }
            self._dispatch_result(result)
            return

        # Live network execution
        try:
            req_data = body_str.encode("utf-8") if method in ("POST", "PUT", "PATCH") and body_str else None
            req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

            with urllib.request.urlopen(req, timeout=10) as response:
                raw_bytes = response.read()
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                status_code = response.getcode()
                reason = getattr(response, "reason", "OK")
                resp_headers = dict(response.headers)
                resp_body = raw_bytes.decode("utf-8", errors="replace")

                result = {
                    "success": True,
                    "status_code": status_code,
                    "reason": reason,
                    "headers": resp_headers,
                    "body": resp_body,
                    "elapsed_ms": round(elapsed_ms, 1),
                    "url": url,
                    "method": method,
                    "is_mock": False,
                }

        except urllib.error.HTTPError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_bytes = e.read()
            resp_body = error_bytes.decode("utf-8", errors="replace")
            result = {
                "success": False,
                "status_code": e.code,
                "reason": getattr(e, "reason", "HTTP Error"),
                "headers": dict(e.headers) if hasattr(e, "headers") else {},
                "body": resp_body or f"HTTP Error {e.code}: {e.reason}",
                "elapsed_ms": round(elapsed_ms, 1),
                "url": url,
                "method": method,
                "is_mock": False,
            }

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result = {
                "success": False,
                "status_code": 0,
                "reason": "Connection Error",
                "headers": {},
                "body": (
                    f"Network Connection Failed:\n{type(e).__name__}: {e}\n\n"
                    "Tip: Toggle 'Offline Mock' in the top header to inspect simulated responses offline!"
                ),
                "elapsed_ms": round(elapsed_ms, 1),
                "url": url,
                "method": method,
                "is_mock": False,
            }

        self._dispatch_result(result)

    # --------------------------------------------------------------------------
    # Request Completion & Results Processing
    # --------------------------------------------------------------------------

    def _on_request_finished(self, res: Dict[str, Any]):
        self._is_request_in_flight = False
        self.send_btn.text = "Send Request"
        self.send_btn.is_disabled = False

        status_code = res["status_code"]
        reason = res["reason"]
        elapsed_ms = res["elapsed_ms"]
        raw_body = res["body"]
        headers = res["headers"]
        url = res["url"]
        method = res["method"]
        is_mock = res.get("is_mock", False)

        # 1. Update Status Badge with semantic variant color
        if status_code == 0:
            status_text = "ERR FAIL"
        else:
            status_text = f"{status_code} {reason}".strip()

        self.status_badge.text = status_text
        self.status_badge.variant = self._status_variant(status_code)

        # 2. Update Latency Badge & Sparkline
        self.time_badge.text = f"{elapsed_ms:.0f} ms"
        self._latencies.append(elapsed_ms)
        if len(self._latencies) > 15:
            self._latencies = self._latencies[-15:]
        self.sparkline.set_data(self._latencies)

        # 3. Update Payload Size Badge
        body_bytes = len(raw_body.encode("utf-8"))
        if body_bytes < 1024:
            size_str = f"{body_bytes} B"
        else:
            size_str = f"{body_bytes / 1024.0:.1f} KB"
        self.size_badge.text = size_str

        # 4. Format & Display Response Body
        self.resp_body_text.delete("1.0", "end")
        display_body = raw_body
        try:
            parsed_json = json.loads(raw_body)
            display_body = json.dumps(parsed_json, indent=2)
        except Exception:
            pass
        self.resp_body_text.insert("1.0", display_body)

        # 5. Display Response Headers
        self.resp_headers_text.delete("1.0", "end")
        if headers:
            hdrs_list = [f"{k}: {v}" for k, v in headers.items()]
            self.resp_headers_text.insert("1.0", "\n".join(hdrs_list))
        else:
            self.resp_headers_text.insert("1.0", "// No response headers received.")

        # 6. Display Diagnostics
        self.resp_info_text.delete("1.0", "end")
        diag_lines = [
            f"Requested URL : {url}",
            f"HTTP Method   : {method}",
            f"Status Code   : {status_code} ({reason})",
            f"Round-trip    : {elapsed_ms:.1f} ms",
            f"Payload Size  : {size_str} ({body_bytes} bytes)",
            f"Mock Mode     : {'Active (Local Emulation)' if is_mock else 'Disabled (Live Network)'}",
            f"Timestamp     : {time.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        self.resp_info_text.insert("1.0", "\n".join(diag_lines))

        # Default back to response body tab
        self.resp_tabs.set("Response Body")

        # 7. Record to Request History Table
        record = {
            "id": self._history_counter,
            "method": method,
            "status": str(status_code) if status_code else "ERR",
            "time": f"{elapsed_ms:.0f}ms",
            "url": url,
            "headers_req": self.headers_text.get("1.0", "end-1c"),
            "body_req": self.body_text.get("1.0", "end-1c"),
            "resp_body": display_body,
            "resp_headers": self.resp_headers_text.get("1.0", "end-1c"),
            "status_text": status_text,
            "status_code": status_code,
            "size_str": size_str,
            "elapsed_ms": elapsed_ms,
        }
        self._history_records.append(record)

        # Add row to Table
        short_url = urllib.parse.urlparse(url).path or "/"
        table_row = [
            str(self._history_counter),
            method,
            str(status_code) if status_code else "ERR",
            f"{elapsed_ms:.0f}ms",
            short_url,
        ]
        self.history_table.data = self.history_table.data + [table_row]
        self._history_counter += 1

        # 8. Update Footer Status
        mode_tag = " [Mock]" if is_mock else ""
        self.footer_status.config(
            text=f"Completed {method} {url}{mode_tag} in {elapsed_ms:.1f}ms • {size_str}"
        )
        self.footer_count.config(text=f"Total Requests: {len(self._history_records)}")

    # --------------------------------------------------------------------------
    # History Interaction
    # --------------------------------------------------------------------------

    def _on_history_row_clicked(self, *args):
        selected = self.history_table.get_selected()
        if not selected:
            return
        row_id_str = selected[0]
        # Match record by ID
        matched = None
        for r in self._history_records:
            if str(r["id"]) == str(row_id_str):
                matched = r
                break
        if not matched:
            return

        # Restore request inputs
        self.method_combo.set(matched["method"])
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, matched["url"])

        self.headers_text.delete("1.0", "end")
        self.headers_text.insert("1.0", matched["headers_req"])

        self.body_text.delete("1.0", "end")
        self.body_text.insert("1.0", matched["body_req"])

        # Restore response view & badge colors
        self.status_badge.text = matched["status_text"]
        code = matched.get("status_code", 200)
        self.status_badge.variant = self._status_variant(code)
        self.time_badge.text = matched["time"]
        self.size_badge.text = matched["size_str"]

        self.resp_body_text.delete("1.0", "end")
        self.resp_body_text.insert("1.0", matched["resp_body"])

        self.resp_headers_text.delete("1.0", "end")
        self.resp_headers_text.insert("1.0", matched["resp_headers"])

        # Diagnostics tab
        diag_lines = [
            f"Requested URL : {matched['url']}",
            f"HTTP Method   : {matched['method']}",
            f"Status Code   : {matched['status_text']}",
            f"Round-trip    : {matched.get('elapsed_ms', 0)} ms",
            f"Payload Size  : {matched['size_str']}",
            "Historical Snapshot Restored",
        ]
        self.resp_info_text.delete("1.0", "end")
        self.resp_info_text.insert("1.0", "\n".join(diag_lines))

        self.resp_tabs.set("Response Body")
        self.footer_status.config(text=f"Restored historical request #{matched['id']} ({matched['url']})")

    def _clear_history(self):
        self._history_records.clear()
        self.history_table.data = []
        self.footer_count.config(text="Total Requests: 0")
        self.footer_status.config(text="Request history cleared.")

    # --------------------------------------------------------------------------
    # Dynamic Runtime Theming
    # --------------------------------------------------------------------------

    def _on_theme_selected(self, chosen: str):
        theme_name = chosen.lower().replace(" ", "_")
        try:
            set_theme(theme_name)
            self._current_theme = theme_name
            pal = get_theme()

            # Update root window and standard Tkinter helper frames
            self.configure(bg=pal.bg)
            self.title_lbl.config(fg=pal.fg, bg=pal.bg)
            self.subtitle_lbl.config(fg=getattr(pal, "text_muted", pal.fg_subtle), bg=pal.bg)
            self.theme_lbl.config(fg=pal.fg, bg=pal.bg)
            self.footer_status.config(fg=getattr(pal, "text_muted", pal.fg_subtle), bg=pal.bg)
            self.footer_count.config(fg=pal.primary, bg=pal.bg)

            self.preset_title_lbl.config(fg=pal.fg, bg=pal.card_bg)
            self.history_title_lbl.config(fg=pal.fg, bg=pal.card_bg)
            self.hist_hint_lbl.config(fg=getattr(pal, "text_muted", pal.fg_subtle), bg=pal.card_bg)
            self.spark_lbl.config(fg=getattr(pal, "text_muted", pal.fg_subtle), bg=pal.card_bg)

            if hasattr(self, "auth_type_lbl"):
                self.auth_type_lbl.config(fg=pal.fg, bg=pal.bg)
                self.auth_token_lbl.config(fg=pal.fg, bg=pal.bg)
                self.auth_hint_lbl.config(fg=getattr(pal, "text_muted", pal.fg_subtle), bg=pal.bg)

            # Cascade background to all child frames
            cascade_bg_to_children(self, pal.bg)

            self.footer_status.config(text=f"Switched theme to '{chosen}'.")
        except Exception as e:
            self.footer_status.config(text=f"Theme switch error: {e}")


# ==============================================================================
# Main Entry Point
# ==============================================================================

if __name__ == "__main__":
    app = APIInspectorApp()
    app.mainloop()
