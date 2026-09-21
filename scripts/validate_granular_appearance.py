#!/usr/bin/env python3
"""
Granular Component & State Matrix Visual Validation Pipeline for tkblend.
Captures fine-grained, stateful, control-by-control rendering and verifies against golden baselines.
Generates an interactive HTML visual inspection and regression dashboard.
"""

import os
import sys
import time
import argparse
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageChops, ImageDraw, ImageGrab
import tkblend


BASELINES_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "visual_baselines", "granular")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "build", "visual_reports", "granular")


def ensure_dirs():
    os.makedirs(BASELINES_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


def capture_window_image(root: tk.Tk, wait_ms: int = 150) -> Image.Image:
    """Flush pending rendering passes and grab crisp window pixels."""
    root.update_idletasks()
    root.update()
    time.sleep(wait_ms / 1000.0)
    root.update_idletasks()
    root.update()

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()

    bbox = (x, y, x + w, y + h)
    img = ImageGrab.grab(bbox=bbox)
    return img.convert("RGB")


# =============================================================================
# Granular Matrix Window Builders
# =============================================================================

def build_buttons_matrix_window(dark: bool = True) -> tk.Tk:
    """Matrix of Button variants x widget states (Normal, Active, Pressed, Disabled, Focus)."""
    root = tk.Tk()
    root.title(f"Button Matrix - {'Dark' if dark else 'Light'}")
    root.geometry("860x520")
    root.resizable(False, False)

    tkblend.apply_theme(root, dark_mode=dark, button_radius=8.0, enable_shadows=True)

    header = ttk.Frame(root, padding=(16, 12))
    header.pack(fill="x")
    ttk.Label(header, text=f"Button States & Styles Matrix ({'Dark' if dark else 'Light'})", font=("Helvetica", 13, "bold")).pack(anchor="w")

    main = ttk.Frame(root, padding=16)
    main.pack(fill="both", expand=True)

    styles = [
        ("Standard", "TButton"),
        ("Primary / Accent", "Accent.TButton"),
        ("Secondary", "Secondary.TButton"),
        ("Destructive", "Destructive.TButton"),
        ("Ghost", "Ghost.TButton"),
        ("Outline", "Outline.TButton"),
    ]

    states = [
        ("Normal", []),
        ("Active (Hover)", ["active"]),
        ("Pressed", ["pressed"]),
        ("Disabled", ["disabled"]),
        ("Focus Ring", ["focus"]),
    ]

    # Header Row (States)
    ttk.Label(main, text="Style \\ State", font=("Helvetica", 10, "bold"), width=18).grid(row=0, column=0, padx=6, pady=6, sticky="w")
    for c_idx, (st_name, _) in enumerate(states, start=1):
        ttk.Label(main, text=st_name, font=("Helvetica", 10, "bold"), width=16, anchor="center").grid(row=0, column=c_idx, padx=6, pady=6)

    # Style Rows
    for r_idx, (sty_name, sty_class) in enumerate(styles, start=1):
        ttk.Label(main, text=sty_name, font=("Helvetica", 9, "bold")).grid(row=r_idx, column=0, padx=6, pady=6, sticky="w")
        for c_idx, (st_name, st_flags) in enumerate(states, start=1):
            btn = ttk.Button(main, text=sty_name.split()[0], style=sty_class)
            btn.grid(row=r_idx, column=c_idx, padx=6, pady=6, sticky="ew")
            if st_flags:
                btn.state(st_flags)

    return root


def build_inputs_matrix_window(dark: bool = True) -> tk.Tk:
    """Matrix of Text Entry, Combobox, and Spinbox x States (Normal, Focus Glow, Readonly, Disabled)."""
    root = tk.Tk()
    root.title(f"Inputs Matrix - {'Dark' if dark else 'Light'}")
    root.geometry("860x420")
    root.resizable(False, False)

    tkblend.apply_theme(root, dark_mode=dark, entry_radius=8.0, enable_shadows=True)

    header = ttk.Frame(root, padding=(16, 12))
    header.pack(fill="x")
    ttk.Label(header, text=f"Input Fields, Combobox & Spinbox Matrix ({'Dark' if dark else 'Light'})", font=("Helvetica", 13, "bold")).pack(anchor="w")

    main = ttk.Frame(root, padding=16)
    main.pack(fill="both", expand=True)

    states = [
        ("Normal", []),
        ("Active (Hover)", ["active"]),
        ("Focus Glow", ["focus"]),
        ("Readonly", ["readonly"]),
        ("Disabled", ["disabled"]),
    ]

    # Header Row
    ttk.Label(main, text="Control", font=("Helvetica", 10, "bold"), width=14).grid(row=0, column=0, padx=6, pady=8, sticky="w")
    for c_idx, (st_name, _) in enumerate(states, start=1):
        ttk.Label(main, text=st_name, font=("Helvetica", 10, "bold"), width=16, anchor="center").grid(row=0, column=c_idx, padx=6, pady=8)

    # Row 1: Entry
    ttk.Label(main, text="TEntry", font=("Helvetica", 9, "bold")).grid(row=1, column=0, padx=6, pady=8, sticky="w")
    for c_idx, (_, st_flags) in enumerate(states, start=1):
        e = ttk.Entry(main, width=13)
        e.insert(0, "TkBlend")
        e.grid(row=1, column=c_idx, padx=6, pady=8)
        if st_flags:
            e.state(st_flags)

    # Row 2: Combobox
    ttk.Label(main, text="TCombobox", font=("Helvetica", 9, "bold")).grid(row=2, column=0, padx=6, pady=8, sticky="w")
    for c_idx, (_, st_flags) in enumerate(states, start=1):
        cb = ttk.Combobox(main, values=["Option A", "Option B"], width=11)
        cb.current(0)
        cb.grid(row=2, column=c_idx, padx=6, pady=8)
        if st_flags:
            cb.state(st_flags)

    # Row 3: Spinbox
    ttk.Label(main, text="TSpinbox", font=("Helvetica", 9, "bold")).grid(row=3, column=0, padx=6, pady=8, sticky="w")
    for c_idx, (_, st_flags) in enumerate(states, start=1):
        sp = ttk.Spinbox(main, from_=1, to=100, width=11)
        sp.set(42)
        sp.grid(row=3, column=c_idx, padx=6, pady=8)
        if st_flags:
            sp.state(st_flags)

    return root


def build_check_radio_matrix_window(dark: bool = True) -> tk.Tk:
    """Matrix of Checkbutton (Unchecked, Checked, Tri-State/Alternate) and Radiobutton across states."""
    root = tk.Tk()
    root.title(f"Check & Radio Matrix - {'Dark' if dark else 'Light'}")
    root.geometry("860x420")
    root.resizable(False, False)

    tkblend.apply_theme(root, dark_mode=dark, check_radius=5.0)

    header = ttk.Frame(root, padding=(16, 12))
    header.pack(fill="x")
    ttk.Label(header, text=f"Vector Indicators: Checkbutton & Radiobutton Matrix ({'Dark' if dark else 'Light'})", font=("Helvetica", 13, "bold")).pack(anchor="w")

    main = ttk.Frame(root, padding=16)
    main.pack(fill="both", expand=True)

    # Section 1: Checkbuttons
    lf_check = ttk.Labelframe(main, text=" Checkbutton Variations & Indeterminate States ", padding=12)
    lf_check.pack(fill="x", pady=(0, 12))

    row_c = ttk.Frame(lf_check)
    row_c.pack(fill="x")

    c1 = ttk.Checkbutton(row_c, text="Unchecked")
    c1.pack(side="left", padx=10, pady=4)

    c2 = ttk.Checkbutton(row_c, text="Checked")
    c2.state(["selected"])
    c2.pack(side="left", padx=10, pady=4)

    c3 = ttk.Checkbutton(row_c, text="Tri-State (Alternate)")
    c3.state(["alternate"])
    c3.pack(side="left", padx=10, pady=4)

    c4 = ttk.Checkbutton(row_c, text="Disabled Unchecked")
    c4.state(["disabled"])
    c4.pack(side="left", padx=10, pady=4)

    c5 = ttk.Checkbutton(row_c, text="Disabled Checked")
    c5.state(["disabled", "selected"])
    c5.pack(side="left", padx=10, pady=4)

    c6 = ttk.Checkbutton(row_c, text="Focused")
    c6.state(["focus", "selected"])
    c6.pack(side="left", padx=10, pady=4)

    # Section 2: Radiobuttons
    lf_radio = ttk.Labelframe(main, text=" Radiobutton Options & Active Selections ", padding=12)
    lf_radio.pack(fill="x", pady=8)

    row_r = ttk.Frame(lf_radio)
    row_r.pack(fill="x")

    r1 = ttk.Radiobutton(row_r, text="Option 1 (Unselected)")
    r1.pack(side="left", padx=10, pady=4)

    r2 = ttk.Radiobutton(row_r, text="Option 2 (Selected)")
    r2.state(["selected"])
    r2.pack(side="left", padx=10, pady=4)

    r3 = ttk.Radiobutton(row_r, text="Option 3 (Hover Active)")
    r3.state(["active"])
    r3.pack(side="left", padx=10, pady=4)

    r4 = ttk.Radiobutton(row_r, text="Disabled Unselected")
    r4.state(["disabled"])
    r4.pack(side="left", padx=10, pady=4)

    r5 = ttk.Radiobutton(row_r, text="Disabled Selected")
    r5.state(["disabled", "selected"])
    r5.pack(side="left", padx=10, pady=4)

    r6 = ttk.Radiobutton(row_r, text="Focused Selected")
    r6.state(["focus", "selected"])
    r6.pack(side="left", padx=10, pady=4)

    return root


def build_sliders_progress_matrix_window(dark: bool = True) -> tk.Tk:
    """Matrix of Horizontal & Vertical Sliders (Scale) and Progressbars at varying levels (0%, 25%, 50%, 75%, 100%)."""
    root = tk.Tk()
    root.title(f"Sliders & Progress Matrix - {'Dark' if dark else 'Light'}")
    root.geometry("860x560")
    root.resizable(False, False)

    tkblend.apply_theme(root, dark_mode=dark, enable_shadows=True)

    header = ttk.Frame(root, padding=(16, 12))
    header.pack(fill="x")
    ttk.Label(header, text=f"Progressbars & Scale Sliders Matrix ({'Dark' if dark else 'Light'})", font=("Helvetica", 13, "bold")).pack(anchor="w")

    main = ttk.Frame(root, padding=16)
    main.pack(fill="both", expand=True)

    # Horizontal Progressbars
    lf_hp = ttk.Labelframe(main, text=" Horizontal Progressbars (0%, 25%, 50%, 75%, 100%) ", padding=12)
    lf_hp.pack(fill="x", pady=(0, 10))

    for val in [0, 25, 50, 75, 100]:
        row = ttk.Frame(lf_hp)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=f"{val}%", width=6).pack(side="left")
        pb = ttk.Progressbar(row, orient="horizontal", value=val, maximum=100)
        pb.pack(side="left", fill="x", expand=True, padx=6)

    # Horizontal Sliders
    lf_hs = ttk.Labelframe(main, text=" Horizontal Sliders / TScale (0%, 25%, 50%, 75%, 100%, Focus) ", padding=12)
    lf_hs.pack(fill="x", pady=10)

    for val in [0, 33, 66, 100]:
        row = ttk.Frame(lf_hs)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=f"{val}%", width=6).pack(side="left")
        sc = ttk.Scale(row, from_=0, to=100, value=val, orient="horizontal")
        sc.pack(side="left", fill="x", expand=True, padx=6)
        if val == 66:
            sc.state(["focus"])

    # Vertical Section
    v_frame = ttk.Frame(main)
    v_frame.pack(fill="x", pady=10)

    lf_vp = ttk.Labelframe(v_frame, text=" Vertical Progressbars ", padding=12)
    lf_vp.pack(side="left", fill="x", expand=True, padx=(0, 8))

    v_prow = ttk.Frame(lf_vp)
    v_prow.pack()
    for v_val in [15, 50, 85]:
        col = ttk.Frame(v_prow)
        col.pack(side="left", padx=16)
        vpb = ttk.Progressbar(col, orient="vertical", value=v_val, maximum=100, length=70)
        vpb.pack()
        ttk.Label(col, text=f"{v_val}%").pack(pady=(4, 0))

    lf_vs = ttk.Labelframe(v_frame, text=" Vertical Sliders ", padding=12)
    lf_vs.pack(side="left", fill="x", expand=True, padx=(8, 0))

    v_srow = ttk.Frame(lf_vs)
    v_srow.pack()
    for v_val in [20, 60, 90]:
        col = ttk.Frame(v_srow)
        col.pack(side="left", padx=16)
        vsc = ttk.Scale(col, from_=0, to=100, value=v_val, orient="vertical", length=70)
        vsc.pack()
        ttk.Label(col, text=f"{v_val}%").pack(pady=(4, 0))

    return root


def build_tabs_cards_matrix_window(dark: bool = True) -> tk.Tk:
    """Matrix of Notebook Tabs and Labelframe container cards."""
    root = tk.Tk()
    root.title(f"Tabs & Cards Matrix - {'Dark' if dark else 'Light'}")
    root.geometry("860x480")
    root.resizable(False, False)

    tkblend.apply_theme(root, dark_mode=dark, button_radius=8.0, entry_radius=8.0)

    header = ttk.Frame(root, padding=(16, 12))
    header.pack(fill="x")
    ttk.Label(header, text=f"Tabs & Glassmorphic Card Containers ({'Dark' if dark else 'Light'})", font=("Helvetica", 13, "bold")).pack(anchor="w")

    main = ttk.Frame(root, padding=16)
    main.pack(fill="both", expand=True)

    nb = ttk.Notebook(main)
    nb.pack(fill="both", expand=True)

    t1 = ttk.Frame(nb, padding=16)
    t2 = ttk.Frame(nb, padding=16)
    t3 = ttk.Frame(nb, padding=16)

    nb.add(t1, text="  Active Overview  ")
    nb.add(t2, text="  Performance Specs  ")
    nb.add(t3, text="  Diagnostics  ")

    # Card inside tab 1
    card1 = ttk.Labelframe(t1, text=" System Performance Metrics ", padding=16)
    card1.pack(fill="x", pady=(0, 12))

    c1_row = ttk.Frame(card1)
    c1_row.pack(fill="x")
    ttk.Label(c1_row, text="JIT Engine:").pack(side="left", padx=(0, 6))
    ttk.Entry(c1_row, width=16).pack(side="left", padx=(0, 16))
    ttk.Button(c1_row, text="Inspect Cache", style="Secondary.TButton").pack(side="left", padx=4)
    ttk.Button(c1_row, text="Deploy Pipeline", style="Accent.TButton").pack(side="left", padx=4)

    card2 = ttk.Labelframe(t1, text=" Storage & Memory Allocation ", padding=16)
    card2.pack(fill="x", pady=8)
    pb = ttk.Progressbar(card2, orient="horizontal", value=74, maximum=100)
    pb.pack(fill="x", pady=6)
    ttk.Label(card2, text="Memory: 74% Utilized (Blend2D PRGB32 Direct Blit)").pack(anchor="w")

    return root


def build_treeview_matrix_window(dark: bool = True) -> tk.Tk:
    """Matrix of Treeview table with headings, multiple rows, selection highlight, and column alignments."""
    root = tk.Tk()
    root.title(f"Treeview Matrix - {'Dark' if dark else 'Light'}")
    root.geometry("860x440")
    root.resizable(False, False)

    tkblend.apply_theme(root, dark_mode=dark)

    header = ttk.Frame(root, padding=(16, 12))
    header.pack(fill="x")
    ttk.Label(header, text=f"Treeview Data Table Matrix ({'Dark' if dark else 'Light'})", font=("Helvetica", 13, "bold")).pack(anchor="w")

    main = ttk.Frame(root, padding=16)
    main.pack(fill="both", expand=True)

    cols = ("ID", "Component", "Rasterizer", "Latency", "Status")
    tree = ttk.Treeview(main, columns=cols, show="headings", height=8)

    tree.heading("ID", text="ID")
    tree.heading("Component", text="Element Name")
    tree.heading("Rasterizer", text="Backend Pipeline")
    tree.heading("Latency", text="Blit Time")
    tree.heading("Status", text="Engine State")

    tree.column("ID", width=60, anchor="center")
    tree.column("Component", width=180)
    tree.column("Rasterizer", width=160)
    tree.column("Latency", width=120, anchor="center")
    tree.column("Status", width=140, anchor="center")

    rows = [
        ("01", "Button Spec", "Blend2D PRGB32", "0.03 ms", "⚡ Active"),
        ("02", "Check & Radio", "Blend2D Vector Paths", "0.02 ms", "⚡ Active"),
        ("03", "Text Entry & Halo", "Blend2D Rounded Rect", "0.03 ms", "⚡ Active"),
        ("04", "Combobox Chevrons", "Blend2D Antialiased", "0.02 ms", "⚡ Active"),
        ("05", "Progressbar Capsule", "Blend2D JIT Linear", "0.04 ms", "⚡ Active"),
        ("06", "Scale Slider Thumb", "Blend2D Circle Shadow", "0.03 ms", "⚡ Active"),
        ("07", "Notebook Tabs", "Blend2D Specular", "0.04 ms", "⚡ Active"),
    ]

    for r in rows:
        tree.insert("", "end", values=r)

    # Select row 2
    children = tree.get_children()
    if len(children) >= 2:
        tree.selection_set(children[1])

    tree.pack(fill="both", expand=True)

    return root


def build_edge_cases_matrix_window(dark: bool = True) -> tk.Tk:
    """Matrix of Edge Cases: Sharp (0px) vs Large (16px) vs Pill Corner Radii, Custom Hex Colors, and Zero Size."""
    root = tk.Tk()
    root.title(f"Edge Cases & Configurations - {'Dark' if dark else 'Light'}")
    root.geometry("860x460")
    root.resizable(False, False)

    tkblend.apply_theme(root, dark_mode=dark, button_radius=14.0, entry_radius=14.0, enable_shadows=False)

    header = ttk.Frame(root, padding=(16, 12))
    header.pack(fill="x")
    ttk.Label(header, text=f"Edge Cases, Custom Radii & Color Configurations ({'Dark' if dark else 'Light'})", font=("Helvetica", 13, "bold")).pack(anchor="w")

    main = ttk.Frame(root, padding=16)
    main.pack(fill="both", expand=True)

    # Custom Radii Showcase
    lf_rad = ttk.Labelframe(main, text=" Large Radius (14px) & Pill Controls ", padding=12)
    lf_rad.pack(fill="x", pady=(0, 10))

    r_row = ttk.Frame(lf_rad)
    r_row.pack(fill="x")

    ttk.Button(r_row, text="14px Accent", style="Accent.TButton").pack(side="left", padx=6)
    ttk.Button(r_row, text="14px Secondary", style="Secondary.TButton").pack(side="left", padx=6)
    ttk.Button(r_row, text="14px Destructive", style="Destructive.TButton").pack(side="left", padx=6)
    e = ttk.Entry(r_row, width=16)
    e.insert(0, "14px Radius Entry")
    e.pack(side="left", padx=6)

    # Dynamic Custom Colors
    lf_col = ttk.Labelframe(main, text=" Dynamic Custom Hex Styled Buttons ", padding=12)
    lf_col.pack(fill="x", pady=10)

    # Define custom ttk styles with hex colors
    style = ttk.Style(master=root)
    style.configure("Emerald.TButton", background="#10b981", foreground="#ffffff")
    style.configure("Pink.TButton", background="#ec4899", foreground="#ffffff")
    style.configure("Amber.TButton", background="#f59e0b", foreground="#ffffff")
    style.configure("Cyan.TButton", background="#06b6d4", foreground="#ffffff")

    c_row = ttk.Frame(lf_col)
    c_row.pack(fill="x")

    ttk.Button(c_row, text="Emerald (#10B981)", style="Emerald.TButton").pack(side="left", padx=6)
    ttk.Button(c_row, text="Pink (#EC4899)", style="Pink.TButton").pack(side="left", padx=6)
    ttk.Button(c_row, text="Amber (#F59E0B)", style="Amber.TButton").pack(side="left", padx=6)
    ttk.Button(c_row, text="Cyan (#06B6D4)", style="Cyan.TButton").pack(side="left", padx=6)

    return root


# =============================================================================
# Image Comparison & HTML Report Generation
# =============================================================================

def compare_images(actual: Image.Image, baseline: Image.Image):
    """Computes difference heatmap and pixel match statistics."""
    if actual.size != baseline.size:
        actual = actual.resize(baseline.size)

    diff = ImageChops.difference(actual, baseline)
    stat_diff = diff.convert("L")
    hist = stat_diff.histogram()
    total_pixels = actual.size[0] * actual.size[1]

    # Tolerant match: subpixel shift <= 4
    near_match_pixels = sum(hist[:5])
    match_percentage = (near_match_pixels / total_pixels) * 100.0

    # Heatmap
    heatmap = Image.new("RGB", actual.size, (15, 23, 42))
    diff_data = stat_diff.load()
    actual_data = actual.load()
    heat_data = heatmap.load()

    for y in range(actual.size[1]):
        for x in range(actual.size[0]):
            d_val = diff_data[x, y]
            if d_val > 5:
                heat_data[x, y] = (255, 0, int(min(255, d_val * 4)))
            else:
                orig = actual_data[x, y]
                heat_data[x, y] = (orig[0] // 3, orig[1] // 3, orig[2] // 3)

    return match_percentage, diff, heatmap


def generate_html_report(results: list) -> str:
    """Builds an interactive dark-themed HTML report displaying side-by-side granular visual diffs."""
    cards_html = ""
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)

    for r in results:
        status_badge = (
            f'<span style="background: #10B981; color: white; padding: 4px 12px; border-radius: 999px; font-weight: bold; font-size: 0.85rem;">✅ PASSED ({r["match_pct"]:.2f}%)</span>'
            if r["passed"] else
            f'<span style="background: #EF4444; color: white; padding: 4px 12px; border-radius: 999px; font-weight: bold; font-size: 0.85rem;">❌ FAILED ({r["match_pct"]:.2f}%)</span>'
        )

        cards_html += f"""
        <div style="background: #1E293B; border-radius: 12px; padding: 24px; margin-bottom: 28px; border: 1px solid #334155;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                <div>
                    <h2 style="margin: 0; font-size: 1.2rem; color: #F8FAFC;">{r["name"]}</h2>
                    <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 0.9rem;">{r["description"]}</p>
                </div>
                {status_badge}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px;">
                <div>
                    <h4 style="color: #CBD5E1; margin: 0 0 8px 0; font-size: 0.85rem;">Golden Baseline</h4>
                    <img src="{r['baseline_rel']}" style="width: 100%; border-radius: 8px; border: 1px solid #475569;" alt="Baseline" />
                </div>
                <div>
                    <h4 style="color: #CBD5E1; margin: 0 0 8px 0; font-size: 0.85rem;">Actual Rendered</h4>
                    <img src="{r['actual_rel']}" style="width: 100%; border-radius: 8px; border: 1px solid #475569;" alt="Actual" />
                </div>
                <div>
                    <h4 style="color: #CBD5E1; margin: 0 0 8px 0; font-size: 0.85rem;">Diff Heatmap</h4>
                    <img src="{r['heatmap_rel']}" style="width: 100%; border-radius: 8px; border: 1px solid #475569;" alt="Diff" />
                </div>
            </div>
        </div>
        """

    summary_banner = (
        f'<div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; padding: 16px; border-radius: 8px; margin-bottom: 24px;">'
        f'<h3 style="margin: 0; color: #10B981;">All Granular Verification Targets Passed ({passed_count}/{total_count})</h3>'
        f'</div>'
        if passed_count == total_count else
        f'<div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; padding: 16px; border-radius: 8px; margin-bottom: 24px;">'
        f'<h3 style="margin: 0; color: #EF4444;">Visual Regressions Detected ({total_count - passed_count}/{total_count} Failed)</h3>'
        f'</div>'
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>tkblend - Granular Visual Appearance Validation Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0F172A;
            color: #F8FAFC;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1320px;
            margin: 0 auto;
        }}
        .header {{
            border-bottom: 1px solid #334155;
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        h1 {{
            margin: 0;
            font-size: 1.85rem;
            color: #6366F1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>tkblend Granular Appearance & State Matrix Report</h1>
            <p style="color: #94A3B8; margin-top: 6px;">Granular, control-by-control, stateful verification for native Blend2D TTK theme elements.</p>
        </div>
        {summary_banner}
        {cards_html}
    </div>
</body>
</html>
"""
    report_path = os.path.join(REPORTS_DIR, "index.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    return report_path


TARGET_BUILDERS = {
    "matrix_buttons_dark": ("Buttons Matrix (Dark Mode)", lambda: build_buttons_matrix_window(dark=True)),
    "matrix_buttons_light": ("Buttons Matrix (Light Mode)", lambda: build_buttons_matrix_window(dark=False)),
    "matrix_inputs_dark": ("Input Fields Matrix (Dark Mode)", lambda: build_inputs_matrix_window(dark=True)),
    "matrix_inputs_light": ("Input Fields Matrix (Light Mode)", lambda: build_inputs_matrix_window(dark=False)),
    "matrix_check_radio_dark": ("Check & Radio Matrix (Dark Mode)", lambda: build_check_radio_matrix_window(dark=True)),
    "matrix_check_radio_light": ("Check & Radio Matrix (Light Mode)", lambda: build_check_radio_matrix_window(dark=False)),
    "matrix_sliders_progress_dark": ("Sliders & Progress Matrix (Dark Mode)", lambda: build_sliders_progress_matrix_window(dark=True)),
    "matrix_sliders_progress_light": ("Sliders & Progress Matrix (Light Mode)", lambda: build_sliders_progress_matrix_window(dark=False)),
    "matrix_tabs_cards_dark": ("Tabs & Cards Matrix (Dark Mode)", lambda: build_tabs_cards_matrix_window(dark=True)),
    "matrix_tabs_cards_light": ("Tabs & Cards Matrix (Light Mode)", lambda: build_tabs_cards_matrix_window(dark=False)),
    "matrix_treeview_dark": ("Treeview Table Matrix (Dark Mode)", lambda: build_treeview_matrix_window(dark=True)),
    "matrix_treeview_light": ("Treeview Table Matrix (Light Mode)", lambda: build_treeview_matrix_window(dark=False)),
    "matrix_edge_cases_dark": ("Edge Cases & Custom Colors (Dark Mode)", lambda: build_edge_cases_matrix_window(dark=True)),
    "matrix_edge_cases_light": ("Edge Cases & Custom Colors (Light Mode)", lambda: build_edge_cases_matrix_window(dark=False)),
}


def run_granular_pipeline(update_baselines: bool = False, tolerance: float = 98.5) -> bool:
    """Runs granular control-by-control verification."""
    ensure_dirs()
    all_passed = True
    results = []

    print(f"==================================================================")
    print(f"🚀 Running Granular Theme Appearance Pipeline ({'UPDATE BASELINES' if update_baselines else 'VERIFY'})")
    print(f"==================================================================")

    for target_key, (desc, builder_fn) in TARGET_BUILDERS.items():
        print(f" Rendering [{target_key}] ...", end="", flush=True)

        root = builder_fn()
        img = capture_window_image(root)
        root.destroy()

        baseline_file = os.path.join(BASELINES_DIR, f"{target_key}.png")
        actual_file = os.path.join(REPORTS_DIR, f"{target_key}_actual.png")
        diff_file = os.path.join(REPORTS_DIR, f"{target_key}_diff.png")
        heat_file = os.path.join(REPORTS_DIR, f"{target_key}_heatmap.png")

        img.save(actual_file)

        if update_baselines or not os.path.exists(baseline_file):
            img.save(baseline_file)
            print(f"  [SAVED BASELINE]")
            match_pct = 100.0
            passed = True
            _, diff_img, heat_img = compare_images(img, img)
            diff_img.save(diff_file)
            heat_img.save(heat_file)
        else:
            baseline = Image.open(baseline_file).convert("RGB")
            match_pct, diff_img, heat_img = compare_images(img, baseline)
            diff_img.save(diff_file)
            heat_img.save(heat_file)
            passed = match_pct >= tolerance
            if not passed:
                all_passed = False
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} ({match_pct:.2f}% match)")

        results.append({
            "name": target_key,
            "description": desc,
            "match_pct": match_pct,
            "passed": passed,
            "baseline_rel": os.path.relpath(baseline_file, REPORTS_DIR),
            "actual_rel": os.path.relpath(actual_file, REPORTS_DIR),
            "heatmap_rel": os.path.relpath(heat_file, REPORTS_DIR),
        })

    report_path = generate_html_report(results)
    print(f"==================================================================")
    print(f" Visual HTML Report generated at: {report_path}")
    print(f" Overall Status: {'SUCCESS (All targets match baselines)' if all_passed else 'REGRESSIONS DETECTED'}")
    print(f"==================================================================")

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="tkblend Granular Appearance Validation")
    parser.add_argument("--update-baselines", action="store_true", help="Generate or update baseline golden images")
    parser.add_argument("--tolerance", type=float, default=98.5, help="Minimum percentage match (default: 98.5%)")
    args = parser.parse_args()

    success = run_granular_pipeline(update_baselines=args.update_baselines, tolerance=args.tolerance)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
