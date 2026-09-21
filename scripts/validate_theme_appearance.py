#!/usr/bin/env python3
"""
Visual Regression & Appearance Validation Pipeline for tkblend.
Captures real GUI rendering of TTK widgets and compares against golden baselines.
Generates pixel diffs and an HTML validation report.
"""

import os
import sys
import time
import argparse
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageChops, ImageDraw, ImageGrab
import tkblend


BASELINES_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "visual_baselines")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "build", "visual_reports")


def ensure_dirs():
    os.makedirs(BASELINES_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


def capture_window_image(root: tk.Tk, wait_ms: int = 150) -> Image.Image:
    """Flush pending rendering passes and grab crisp window pixels."""
    root.lift()
    root.attributes("-topmost", True)
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


def build_showcase_window(dark: bool = True, tab_index: int = 0) -> tk.Tk:
    """Constructs the canonical showcase window for visual testing."""
    root = tk.Tk()
    root.title(f"tkblend Showcase - {'Dark' if dark else 'Light'}")
    root.geometry("880x740")
    root.resizable(False, False)

    tkblend.apply_theme(
        root,
        dark_mode=dark,
        button_radius=8.0,
        entry_radius=8.0,
        enable_shadows=True,
        shadow_blur=8.0
    )

    # Top Header Bar
    header = ttk.Frame(root, padding=(24, 16, 24, 12))
    header.pack(fill="x")

    title_frame = ttk.Frame(header)
    title_frame.pack(side="left")

    title_lbl = ttk.Label(title_frame, text="Blend2D Native TTK Theme", font=("Helvetica", 16, "bold"))
    title_lbl.pack(anchor="w")

    subtitle_lbl = ttk.Label(
        title_frame,
        text="Shadcn Glassmorphism • Electric Indigo • JIT Accelerated Blitting",
        font=("Helvetica", 9)
    )
    subtitle_lbl.pack(anchor="w", pady=(2, 0))

    btn_box = ttk.Frame(header)
    btn_box.pack(side="right")

    mode_btn = ttk.Button(
        btn_box,
        text="☀️ Light Mode" if dark else "🌙 Dark Mode",
        style="Secondary.TButton"
    )
    mode_btn.pack(side="right")

    # Main Notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=20, pady=8)

    tab1 = ttk.Frame(notebook, padding=16)
    tab2 = ttk.Frame(notebook, padding=16)
    notebook.add(tab1, text="  Components & States  ")
    notebook.add(tab2, text="  Data & Indicators  ")

    # TAB 1: Components
    btn_frame = ttk.Labelframe(tab1, text=" Modern Buttons (Hover, Active, Pressed, Glow, Disabled) ", padding=16)
    btn_frame.pack(fill="x", pady=(0, 10))

    b_row = ttk.Frame(btn_frame)
    b_row.pack(fill="x")

    ttk.Button(b_row, text="Primary Action", style="Accent.TButton").pack(side="left", padx=6, pady=4)
    ttk.Button(b_row, text="Secondary Action", style="Secondary.TButton").pack(side="left", padx=6, pady=4)
    ttk.Button(b_row, text="Standard Action", style="TButton").pack(side="left", padx=6, pady=4)
    ttk.Button(b_row, text="Danger Action", style="Destructive.TButton").pack(side="left", padx=6, pady=4)
    ttk.Button(b_row, text="Disabled Button", style="TButton", state="disabled").pack(side="left", padx=6, pady=4)

    # Input Fields & Steppers
    input_frame = ttk.Labelframe(tab1, text=" Text Fields, Combobox & Spinbox (Focus Glow) ", padding=16)
    input_frame.pack(fill="x", pady=10)

    i_row = ttk.Frame(input_frame)
    i_row.pack(fill="x")

    ttk.Label(i_row, text="Username:").pack(side="left", padx=(0, 6))
    e1 = ttk.Entry(i_row, width=14)
    e1.insert(0, "antigravity_engineer")
    e1.pack(side="left", padx=(0, 14))

    ttk.Label(i_row, text="Status:").pack(side="left", padx=(0, 6))
    e2 = ttk.Entry(i_row, width=12)
    e2.insert(0, "JIT Accelerated")
    e2.state(["readonly"])
    e2.pack(side="left", padx=(0, 14))

    ttk.Label(i_row, text="Preset:").pack(side="left", padx=(0, 6))
    combo = ttk.Combobox(i_row, values=["High Performance", "Ultra Precision", "Battery Saver"], width=14)
    combo.current(0)
    combo.pack(side="left", padx=(0, 14))

    ttk.Label(i_row, text="Threads:").pack(side="left", padx=(0, 6))
    spin = ttk.Spinbox(i_row, from_=1, to=64, width=4)
    spin.set(8)
    spin.pack(side="left")

    # Metrics Frame
    metric_frame = ttk.Labelframe(tab1, text=" Sliders, Smooth Progressbar & Modern Docked Scrollbars ", padding=16)
    metric_frame.pack(fill="x", pady=10)

    s_row = ttk.Frame(metric_frame)
    s_row.pack(fill="x", pady=(0, 6))
    ttk.Label(s_row, text="Engine Throttle (TScale):", width=22).pack(side="left")
    scale = ttk.Scale(s_row, from_=0, to=100, value=68.0)
    scale.pack(side="left", fill="x", expand=True, padx=10)
    ttk.Label(s_row, text="68%", width=6).pack(side="right")

    p_row = ttk.Frame(metric_frame)
    p_row.pack(fill="x", pady=6)
    ttk.Label(p_row, text="Buffer Pipeline (Pill):", width=22).pack(side="left")
    pbar = ttk.Progressbar(p_row, orient="horizontal", value=68, maximum=100)
    pbar.pack(side="left", fill="x", expand=True, padx=10)
    ttk.Label(p_row, text="68%", width=6).pack(side="right")

    sc_row = ttk.Frame(metric_frame)
    sc_row.pack(fill="x", pady=6)
    ttk.Label(sc_row, text="Modern Pill Scrollbar:", width=22).pack(side="left")
    scroll = ttk.Scrollbar(sc_row, orient="horizontal")
    scroll.pack(side="left", fill="x", expand=True, padx=10)
    scroll.set(0.15, 0.65)
    ttk.Label(sc_row, text="15-65%", width=6).pack(side="right")

    # TAB 2: Indicators
    choice_frame = ttk.Labelframe(tab2, text=" Antialiased Vector Indicators (Check & Radio) ", padding=16)
    choice_frame.pack(fill="x", pady=(0, 10))

    c_row = ttk.Frame(choice_frame)
    c_row.pack(fill="x")

    v1 = tk.BooleanVar(value=True)
    v2 = tk.BooleanVar(value=True)
    v3 = tk.BooleanVar(value=False)
    ttk.Checkbutton(c_row, text="Hardware Soft Shadows", variable=v1).pack(side="left", padx=10)
    ttk.Checkbutton(c_row, text="Vector Antialiasing", variable=v2).pack(side="left", padx=10)
    ttk.Checkbutton(c_row, text="Glassmorphic Glow", variable=v3).pack(side="left", padx=10)

    r_row = ttk.Frame(choice_frame)
    r_row.pack(fill="x", pady=(10, 0))
    rv = tk.StringVar(value="r1")
    ttk.Radiobutton(r_row, text="Fast Path (Zero Copy)", value="r1", variable=rv).pack(side="left", padx=10)
    ttk.Radiobutton(r_row, text="AsmJit X86/ARM Pipeline", value="r2", variable=rv).pack(side="left", padx=10)
    ttk.Radiobutton(r_row, text="Fallback Renderer", value="r3", variable=rv).pack(side="left", padx=10)

    tree_frame = ttk.Labelframe(tab2, text=" Modern Treeview Data Table ", padding=16)
    tree_frame.pack(fill="both", expand=True, pady=10)

    cols = ("Component", "Backend", "Latency", "Status")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=4)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=140)
    tree.insert("", "end", values=("Button Element Spec", "Blend2D PRGB32", "0.04 ms", "⚡ JIT Accelerated"))
    tree.insert("", "end", values=("Combobox & Spinbox", "Blend2D Vector", "0.03 ms", "⚡ Vector Chevrons"))
    tree.insert("", "end", values=("Pill Progress Bar", "Blend2D Capsule", "0.05 ms", "⚡ Antialiased"))
    tree.insert("", "end", values=("Notebook & Cards", "Blend2D Rounded", "0.03 ms", "⚡ Glassmorphic"))
    tree.pack(fill="both", expand=True)

    # Status Bar
    status_bar = ttk.Label(root, text="Theme engine ready • Blend2D PRGB32 zero-copy rasterization active.", padding=(24, 8))
    status_bar.pack(side="bottom", fill="x")

    if tab_index == 1:
        notebook.select(tab2)

    return root


def compare_images(actual: Image.Image, baseline: Image.Image):
    """Computes difference heatmap and pixel match statistics."""
    if actual.size != baseline.size:
        actual = actual.resize(baseline.size)

    diff = ImageChops.difference(actual, baseline)
    stat_diff = diff.convert("L")
    hist = stat_diff.histogram()
    total_pixels = actual.size[0] * actual.size[1]
    
    # Tolerant match: pixels with negligible RGB shift (< 4 per channel) are counted as matching
    exact_match_pixels = hist[0]
    near_match_pixels = sum(hist[:5])
    match_percentage = (near_match_pixels / total_pixels) * 100.0

    # Generate colorful heatmap image (highlighting differences)
    heatmap = Image.new("RGB", actual.size, (15, 23, 42))
    diff_data = stat_diff.load()
    actual_data = actual.load()
    heat_data = heatmap.load()

    for y in range(actual.size[1]):
        for x in range(actual.size[0]):
            d_val = diff_data[x, y]
            if d_val > 5:
                # Highlight diffs in neon magenta/red
                heat_data[x, y] = (255, 0, int(min(255, d_val * 4)))
            else:
                # Dimmed original pixel
                orig = actual_data[x, y]
                heat_data[x, y] = (orig[0] // 3, orig[1] // 3, orig[2] // 3)

    return match_percentage, diff, heatmap


def generate_html_report(results: list) -> str:
    """Builds a modern dark-themed HTML report displaying side-by-side visual diffs."""
    cards_html = ""
    for r in results:
        status_badge = (
            f'<span style="background: #10B981; color: white; padding: 4px 10px; border-radius: 999px; font-weight: bold;">PASSED ({r["match_pct"]:.2f}%)</span>'
            if r["passed"] else
            f'<span style="background: #EF4444; color: white; padding: 4px 10px; border-radius: 999px; font-weight: bold;">FAILED ({r["match_pct"]:.2f}%)</span>'
        )

        cards_html += f"""
        <div style="background: #1E293B; border-radius: 12px; padding: 24px; margin-bottom: 32px; border: 1px solid #334155;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h2 style="margin: 0; font-size: 1.25rem; color: #F8FAFC;">{r["name"]}</h2>
                {status_badge}
            </div>
            <p style="color: #94A3B8; margin-top: 0;">{r["description"]}</p>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
                <div>
                    <h4 style="color: #CBD5E1; margin: 4px 0 8px;">Expected Baseline</h4>
                    <img src="{r['baseline_rel']}" style="width: 100%; border-radius: 8px; border: 1px solid #475569;" alt="Baseline" />
                </div>
                <div>
                    <h4 style="color: #CBD5E1; margin: 4px 0 8px;">Actual Rendered</h4>
                    <img src="{r['actual_rel']}" style="width: 100%; border-radius: 8px; border: 1px solid #475569;" alt="Actual" />
                </div>
                <div>
                    <h4 style="color: #CBD5E1; margin: 4px 0 8px;">Difference Heatmap</h4>
                    <img src="{r['heatmap_rel']}" style="width: 100%; border-radius: 8px; border: 1px solid #475569;" alt="Diff" />
                </div>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>tkblend - Theme Visual Appearance Validation Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0F172A;
            color: #F8FAFC;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1280px;
            margin: 0 auto;
        }}
        .header {{
            border-bottom: 1px solid #334155;
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        h1 {{
            margin: 0;
            font-size: 2rem;
            color: #6366F1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>tkblend Visual Regression & Appearance Report</h1>
            <p style="color: #94A3B8; margin-top: 8px;">Automated Pixel-by-Pixel Verification of Native Blend2D TTK Themes</p>
        </div>
        {cards_html}
    </div>
</body>
</html>
"""
    report_path = os.path.join(REPORTS_DIR, "index.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    return report_path


def run_pipeline(update_baselines: bool = False, tolerance: float = 98.5) -> bool:
    """Executes the complete visual verification pipeline."""
    ensure_dirs()
    all_passed = True
    results = []

    test_targets = [
        {"name": "showcase_dark_tab1", "desc": "Showcase Theme - Dark Mode (Components)", "dark": True, "tab": 0},
        {"name": "showcase_dark_tab2", "desc": "Showcase Theme - Dark Mode (Data & Indicators)", "dark": True, "tab": 1},
        {"name": "showcase_light_tab1", "desc": "Showcase Theme - Light Mode (Components)", "dark": False, "tab": 0},
        {"name": "showcase_light_tab2", "desc": "Showcase Theme - Light Mode (Data & Indicators)", "dark": False, "tab": 1},
    ]

    print(f"==================================================================")
    print(f"🚀 Running tkblend Theme Appearance Pipeline ({'UPDATE BASELINES' if update_baselines else 'VERIFY'})")
    print(f"==================================================================")

    for target in test_targets:
        name = target["name"]
        print(f" Rendering [{name}] ...", end="", flush=True)

        root = build_showcase_window(dark=target["dark"], tab_index=target["tab"])
        img = capture_window_image(root)
        root.destroy()

        baseline_file = os.path.join(BASELINES_DIR, f"{name}.png")
        actual_file = os.path.join(REPORTS_DIR, f"{name}_actual.png")
        diff_file = os.path.join(REPORTS_DIR, f"{name}_diff.png")
        heat_file = os.path.join(REPORTS_DIR, f"{name}_heatmap.png")

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
            "name": target["name"],
            "description": target["desc"],
            "match_pct": match_pct,
            "passed": passed,
            "baseline_rel": os.path.relpath(baseline_file, REPORTS_DIR),
            "actual_rel": os.path.relpath(actual_file, REPORTS_DIR),
            "heatmap_rel": os.path.relpath(heat_file, REPORTS_DIR),
        })

    report_path = generate_html_report(results)
    print(f"==================================================================")
    print(f" Visual HTML Report generated at: {report_path}")
    print(f" Overall Status: {'SUCCESS (All baselines match)' if all_passed else 'REGRESSIONS DETECTED'}")
    print(f"==================================================================")

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="tkblend Visual Appearance & Regression Pipeline")
    parser.add_argument("--update-baselines", action="store_true", help="Generate or update baseline golden images")
    parser.add_argument("--tolerance", type=float, default=98.5, help="Minimum percentage match (default: 98.5%%)")
    args = parser.parse_args()

    success = run_pipeline(update_baselines=args.update_baselines, tolerance=args.tolerance)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
