#!/usr/bin/env python3
"""
tkblend Showcase: Creative Canvas & Vector Art Studio.
Demonstrates:
  - Advanced BlendCanvas and Surface 2D vector graphics engine
  - Cubic and Quadratic Bézier curves, SVG-like Paths, and geometry clipping
  - Multi-stop Linear and Radial Gradients with extend modes (PAD, REPEAT, REFLECT)
  - Native 2D Composition Blend Modes (COMP_OP_MULTIPLY, SCREEN, OVERLAY, XOR, PLUS)
  - High-performance O(1) multi-layer drop shadows and glow effects
  - Interactive smooth freehand vector drawing scratchpad
"""

from __future__ import annotations

import math
import random
import tkinter as tk
from typing import Optional, List, Tuple

import tkblend as tb
from tkblend import (
    BlendCanvas,
    Surface,
    LinearGradient,
    RadialGradient,
    Path,
    Card,
    Button,
    Slider,
    SegmentedButton,
    OptionMenu,
    Switch,
    Badge,
    COMP_OP_SRC_OVER,
    COMP_OP_MULTIPLY,
    COMP_OP_SCREEN,
    COMP_OP_OVERLAY,
    COMP_OP_XOR,
    COMP_OP_PLUS,
    COMP_OP_DARKEN,
    COMP_OP_LIGHTEN,
    EXTEND_PAD,
    EXTEND_REPEAT,
    EXTEND_REFLECT,
    get_theme,
    set_theme,
    get_available_themes,
    cascade_bg_to_children,
    ScalingTracker,
)


class CanvasStudio(tk.Frame):
    """Interactive vector graphics studio demonstrating Blend2D surface rendering."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._active_mode = "Paths & Curves"
        self._brush_size = 6.0
        self._brush_color = "#3b82f6"
        self._shadow_blur = 16.0
        self._shadow_spread = 0.0
        self._shadow_offset_y = 6.0
        self._comp_mode = "SRC_OVER"
        self._freehand_strokes: List[List[Tuple[float, float, str, float]]] = []
        self._current_stroke: List[Tuple[float, float, str, float]] = []

        self._build_ui()

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # Header Bar
        hdr = tk.Frame(self, background=pal.bg)
        hdr.pack(fill="x", padx=20, pady=(16, 8))

        tbox = tk.Frame(hdr, background=pal.bg)
        tbox.pack(side="left")

        tk.Label(tbox, text="Creative Canvas & Vector Studio", font=("Segoe UI", 18, "bold"), fg=pal.fg, bg=pal.bg).pack(anchor="w")
        tk.Label(tbox, text="Hardware-accelerated 2D vector primitives, gradients, shadows & blend operators", font=("Segoe UI", 10), fg=pal.fg_subtle, bg=pal.bg).pack(anchor="w")

        cbox = tk.Frame(hdr, background=pal.bg)
        cbox.pack(side="right")

        tk.Label(cbox, text="Theme:", font=("Segoe UI", 10), fg=pal.fg_subtle, bg=pal.bg).pack(side="left", padx=(8, 4))
        OptionMenu(
            cbox,
            values=list(get_available_themes()),
            default_value="dark",
            command=self._on_theme_changed,
            width=140,
            height=32,
        ).pack(side="left", padx=6)

        # Mode Selection Bar
        mode_bar = tk.Frame(self, background=pal.bg)
        mode_bar.pack(fill="x", padx=20, pady=6)

        self._mode_seg = SegmentedButton(
            mode_bar,
            values=["Paths & Curves", "Gradients & Extends", "Composition Modes", "Shadows & Glow", "Freehand Scratchpad"],
            default_value="Paths & Curves",
            command=self._set_mode,
            width=760,
            height=32,
        )
        self._mode_seg.pack(side="left")

        # Main Workspace: Left Main BlendCanvas + Right Param Controls
        workspace = tk.Frame(self, background=pal.bg)
        workspace.pack(fill="both", expand=True, padx=20, pady=(6, 16))

        # Main Vector Canvas Card
        canvas_card = Card(workspace, width=640, height=540, rx=14, ry=14, elevation=6)
        canvas_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        c_body = canvas_card.body
        self._canvas = BlendCanvas(c_body, width=620, height=520, bg="surface", on_draw=self._draw_canvas)
        self._canvas.pack(fill="both", expand=True, padx=6, pady=6)

        # Mouse bindings for scratchpad
        self._canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self._canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        # Right Control Panel Card
        self._param_card = Card(workspace, title="Studio Controls", width=290, height=540, rx=14, ry=14, elevation=6)
        self._param_card.pack(side="right", fill="y", padx=(6, 0))
        self._setup_param_panel(self._param_card.body)

        from tkblend.theme import add_theme_listener
        add_theme_listener(lambda p: self._on_global_theme_changed(p))

        cascade_bg_to_children(self, pal.bg)

    def _setup_param_panel(self, container: tk.Frame) -> None:
        pal = get_theme()

        self._ctrl_frame = tk.Frame(container, background=pal.card_bg)
        self._ctrl_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self._update_ctrl_panel()

    def _update_ctrl_panel(self) -> None:
        # Clear existing controls
        for child in self._ctrl_frame.winfo_children():
            child.destroy()

        pal = get_theme()

        if self._active_mode == "Paths & Curves":
            tk.Label(self._ctrl_frame, text="Geometry & Curve Demos", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg).pack(anchor="w", pady=(0, 4))
            tk.Label(self._ctrl_frame, text="Features demonstrated:\n• Anti-aliased cubic Bezier\n• Smooth quadratic arcs\n• Rotated multi-star polygon\n• SVG-like path icons", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg, justify="left").pack(anchor="w", pady=4)
            Button(self._ctrl_frame, text="Re-seed Curve Points", width=220, height=32, command=self._canvas.redraw).pack(pady=12)

        elif self._active_mode == "Gradients & Extends":
            tk.Label(self._ctrl_frame, text="Gradient Matrix", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg).pack(anchor="w", pady=(0, 4))
            tk.Label(self._ctrl_frame, text="Demonstrating:\n• Linear multi-stop gradients\n• Radial focal gradients\n• EXTEND_PAD\n• EXTEND_REPEAT\n• EXTEND_REFLECT", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg, justify="left").pack(anchor="w", pady=4)
            Button(self._ctrl_frame, text="Invert Gradient Stops", width=220, height=32, command=self._canvas.redraw).pack(pady=12)

        elif self._active_mode == "Composition Modes":
            tk.Label(self._ctrl_frame, text="Blend Composition Operator", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg).pack(anchor="w", pady=(0, 4))
            modes = ["SRC_OVER", "MULTIPLY", "SCREEN", "OVERLAY", "XOR", "PLUS", "DARKEN", "LIGHTEN"]
            OptionMenu(
                self._ctrl_frame,
                values=modes,
                default_value=self._comp_mode,
                command=self._set_comp_mode,
                width=220,
                height=32,
            ).pack(pady=6)
            tk.Label(self._ctrl_frame, text="Blends RGB channel math between layered vector shapes natively at JIT speed.", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg, justify="left").pack(anchor="w", pady=8)

        elif self._active_mode == "Shadows & Glow":
            tk.Label(self._ctrl_frame, text="Drop Shadow Parameters", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg).pack(anchor="w", pady=(0, 4))

            tk.Label(self._ctrl_frame, text="Blur Radius:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w")
            Slider(self._ctrl_frame, from_=0, to=40, value=self._shadow_blur, width=220, height=22, command=self._set_blur).pack(fill="x", pady=2)

            tk.Label(self._ctrl_frame, text="Offset Y:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w", pady=(6, 0))
            Slider(self._ctrl_frame, from_=-20, to=40, value=self._shadow_offset_y, width=220, height=22, command=self._set_offset_y).pack(fill="x", pady=2)

            tk.Label(self._ctrl_frame, text="Spread:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w", pady=(6, 0))
            Slider(self._ctrl_frame, from_=-10, to=20, value=self._shadow_spread, width=220, height=22, command=self._set_spread).pack(fill="x", pady=2)

        elif self._active_mode == "Freehand Scratchpad":
            tk.Label(self._ctrl_frame, text="Brush Properties", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg).pack(anchor="w", pady=(0, 4))

            tk.Label(self._ctrl_frame, text="Brush Size:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w")
            Slider(self._ctrl_frame, from_=1, to=30, value=self._brush_size, width=220, height=22, command=self._set_brush_size).pack(fill="x", pady=2)

            tk.Label(self._ctrl_frame, text="Color Palette:", font=("Segoe UI", 9), fg=pal.fg_subtle, bg=pal.card_bg).pack(anchor="w", pady=(8, 4))
            pal_row = tk.Frame(self._ctrl_frame, background=pal.card_bg)
            pal_row.pack(fill="x", pady=2)

            colors = ["#3b82f6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#ffffff"]
            for col in colors:
                btn = tk.Button(pal_row, bg=col, activebackground=col, width=2, height=1, relief="flat", command=lambda c=col: self._set_brush_color(c))
                btn.pack(side="left", padx=2)

            Button(self._ctrl_frame, text="Clear Scratchpad", width=220, height=32, bootstyle="danger", command=self._clear_scratchpad).pack(pady=16)

    def _set_mode(self, mode_name: str) -> None:
        self._active_mode = mode_name
        self._update_ctrl_panel()
        self._canvas.redraw()

    def _set_comp_mode(self, mode: str) -> None:
        self._comp_mode = mode
        self._canvas.redraw()

    def _set_blur(self, val: float) -> None:
        self._shadow_blur = float(val)
        self._canvas.redraw()

    def _set_offset_y(self, val: float) -> None:
        self._shadow_offset_y = float(val)
        self._canvas.redraw()

    def _set_spread(self, val: float) -> None:
        self._shadow_spread = float(val)
        self._canvas.redraw()

    def _set_brush_size(self, val: float) -> None:
        self._brush_size = float(val)

    def _set_brush_color(self, col: str) -> None:
        self._brush_color = col

    def _clear_scratchpad(self) -> None:
        self._freehand_strokes.clear()
        self._current_stroke.clear()
        self._canvas.redraw()

    def _on_canvas_press(self, event) -> None:
        if self._active_mode == "Freehand Scratchpad":
            self._current_stroke = [(float(event.x), float(event.y), self._brush_color, self._brush_size)]
            self._freehand_strokes.append(self._current_stroke)
            self._canvas.redraw()

    def _on_canvas_drag(self, event) -> None:
        if self._active_mode == "Freehand Scratchpad" and self._current_stroke:
            self._current_stroke.append((float(event.x), float(event.y), self._brush_color, self._brush_size))
            self._canvas.redraw()

    def _on_canvas_release(self, _event) -> None:
        if self._active_mode == "Freehand Scratchpad":
            self._current_stroke = []

    def _draw_canvas(self, surf: Surface) -> None:
        pal = get_theme()
        w = float(surf.width)
        h = float(surf.height)

        surf.clear(pal.card_bg)

        if self._active_mode == "Paths & Curves":
            self._draw_paths_mode(surf, w, h, pal)
        elif self._active_mode == "Gradients & Extends":
            self._draw_gradients_mode(surf, w, h, pal)
        elif self._active_mode == "Composition Modes":
            self._draw_comp_mode(surf, w, h, pal)
        elif self._active_mode == "Shadows & Glow":
            self._draw_shadows_mode(surf, w, h, pal)
        elif self._active_mode == "Freehand Scratchpad":
            self._draw_scratchpad_mode(surf, w, h, pal)

    def _draw_paths_mode(self, surf: Surface, w: float, h: float, pal) -> None:
        # 1. Cubic Bezier Ribbon
        p1 = Path()
        p1.move_to(30.0, 120.0)
        p1.cubic_to(120.0, 20.0, 240.0, 220.0, 320.0, 100.0)
        p1.cubic_to(400.0, -20.0, 520.0, 180.0, 580.0, 80.0)

        surf.stroke_path(p1, pal.primary or "#3b82f6", stroke_width=4.0)

        # 2. Geometric Star Polygon with Transformations
        with surf.saved():
            surf.translate(140.0, 320.0)
            star_path = Path()
            points = 8
            r_out = 70.0
            r_in = 32.0
            for i in range(points * 2):
                r = r_out if i % 2 == 0 else r_in
                angle = i * (math.pi / points)
                px = r * math.cos(angle)
                py = r * math.sin(angle)
                if i == 0:
                    star_path.move_to(px, py)
                else:
                    star_path.line_to(px, py)
            star_path.close()

            grad = LinearGradient(-70, -70, 70, 70)
            grad.add_stop(0.0, pal.primary or "#3b82f6")
            grad.add_stop(1.0, pal.secondary or "#06b6d4")
            surf.fill_path(star_path, grad)
            surf.stroke_path(star_path, "#ffffff", stroke_width=2.0)

        # 3. Concentric Antialiased Nested Arcs
        cx, cy = 420.0, 320.0
        for idx, (rad, sw, col) in enumerate([(80.0, 6.0, pal.accent), (64.0, 5.0, pal.primary), (48.0, 4.0, pal.secondary), (32.0, 3.0, pal.success)]):
            arc = Path()
            start_ang = (idx * 0.4) * math.pi
            sweep_ang = 1.4 * math.pi
            arc.arc_to(cx, cy, rad, rad, start_ang, sweep_ang)
            surf.stroke_path(arc, col, stroke_width=sw)

        surf.draw_text("Cubic Bézier Multi-Segment Wave", 30.0, 30.0, font_size=12.0, color=pal.fg)
        surf.draw_text("Vector Star Polygon", 80.0, 430.0, font_size=11.0, color=pal.fg_subtle)
        surf.draw_text("Antialiased Nested Vector Arcs", 340.0, 430.0, font_size=11.0, color=pal.fg_subtle)

    def _draw_gradients_mode(self, surf: Surface, w: float, h: float, pal) -> None:
        # Linear Gradient Box
        lx, ly, lw, lh = 30.0, 50.0, 260.0, 180.0
        lin_grad = LinearGradient(lx, ly, lx + lw, ly + lh)
        lin_grad.add_stop(0.0, "#3b82f6")
        lin_grad.add_stop(0.5, "#8b5cf6")
        lin_grad.add_stop(1.0, "#ec4899")
        surf.fill_rounded_rect(lx, ly, lw, lh, 14.0, 14.0, lin_grad)
        surf.draw_text("Linear Gradient (3-Stop)", lx + 12.0, ly + 24.0, font_size=11.0, color="#ffffff")

        # Radial Gradient Box
        rx, ry, rw, rh = 320.0, 50.0, 260.0, 180.0
        rad_grad = RadialGradient(rx + rw / 2.0, ry + rh / 2.0, 80.0)
        rad_grad.add_stop(0.0, "#f59e0b")
        rad_grad.add_stop(0.6, "#ef4444")
        rad_grad.add_stop(1.0, "#1e1b4b")
        surf.fill_rounded_rect(rx, ry, rw, rh, 14.0, 14.0, rad_grad)
        surf.draw_text("Radial Gradient (Focal)", rx + 12.0, ry + 24.0, font_size=11.0, color="#ffffff")

        # Multi-Ring Wave with Gradients
        bx, by, bw, bh = 30.0, 260.0, 550.0, 220.0
        surf.stroke_rounded_rect(bx, by, bw, bh, 14.0, 14.0, pal.surface_border, stroke_width=1.0)

        for i in range(6):
            cx = bx + 80.0 + i * 75.0
            cy = by + 110.0
            r_g = RadialGradient(cx, cy, 32.0)
            r_g.add_stop(0.0, pal.accent if i % 2 == 0 else pal.primary)
            r_g.add_stop(1.0, "#00000000")
            surf.fill_circle(cx, cy, 32.0, r_g)
            surf.stroke_circle(cx, cy, 32.0, pal.fg_subtle, stroke_width=1.0)

        surf.draw_text("Dynamic Particle Light Dispersion", bx + 16.0, by + 28.0, font_size=11.0, color=pal.fg)

    def _draw_comp_mode(self, surf: Surface, w: float, h: float, pal) -> None:
        comp_map = {
            "SRC_OVER": COMP_OP_SRC_OVER,
            "MULTIPLY": COMP_OP_MULTIPLY,
            "SCREEN": COMP_OP_SCREEN,
            "OVERLAY": COMP_OP_OVERLAY,
            "XOR": COMP_OP_XOR,
            "PLUS": COMP_OP_PLUS,
            "DARKEN": COMP_OP_DARKEN,
            "LIGHTEN": COMP_OP_LIGHTEN,
        }
        op = comp_map.get(self._comp_mode, COMP_OP_SRC_OVER)

        cx, cy = w / 2.0, h / 2.0
        r = 100.0
        d = 60.0

        surf.draw_text(f"Active Blend Operator: COMP_OP_{self._comp_mode}", 30.0, 30.0, font_size=13.0, color=pal.fg)

        # Base circle 1 (Cyan)
        surf.set_comp_op(COMP_OP_SRC_OVER)
        surf.fill_circle(cx - d, cy - d / 2.0, r, "#06b6d4cc")

        # Blend circle 2 (Magenta) with selected composition op
        surf.set_comp_op(op)
        surf.fill_circle(cx + d, cy - d / 2.0, r, "#ec4899cc")

        # Blend circle 3 (Yellow) with selected composition op
        surf.fill_circle(cx, cy + d, r, "#f59e0bcc")

        # Reset composition operator to default
        surf.set_comp_op(COMP_OP_SRC_OVER)

    def _draw_shadows_mode(self, surf: Surface, w: float, h: float, pal) -> None:
        surf.draw_text("High-Performance Soft Drop Shadows & Glow", 30.0, 30.0, font_size=13.0, color=pal.fg)

        # Card with custom live shadow
        cx, cy, cw, ch = 50.0, 80.0, 240.0, 180.0
        surf.fill_shadowed_rounded_rect(
            cx, cy, cw, ch, 16.0, 16.0,
            fill=pal.card_bg,
            border=pal.primary,
            border_width=1.5,
            shadow_blur=self._shadow_blur,
            shadow_spread=self._shadow_spread,
            shadow_offset_y=self._shadow_offset_y,
            shadow_color="#00000077",
        )
        surf.draw_text("Dynamic Shadow Card", cx + 20.0, cy + 30.0, font_size=12.0, color=pal.fg)
        surf.draw_text(f"Blur: {self._shadow_blur:.1f}px\nSpread: {self._shadow_spread:.1f}px\nOffset Y: {self._shadow_offset_y:.1f}px", cx + 20.0, cy + 60.0, font_size=10.0, color=pal.fg_subtle)

        # Glowing Neon Floating Badge Card
        nx, ny, nw, nh = 330.0, 80.0, 240.0, 180.0
        surf.fill_shadowed_rounded_rect(
            nx, ny, nw, nh, 16.0, 16.0,
            fill="#0f172a",
            border="#38bdf8",
            border_width=2.0,
            shadow_blur=24.0,
            shadow_spread=2.0,
            shadow_offset_y=0.0,
            shadow_color="#38bdf866",
        )
        surf.draw_text("Neon Cyan Glow", nx + 20.0, ny + 30.0, font_size=12.0, color="#38bdf8")
        surf.draw_text("Zero blur degradation\nO(1) cached shadow kernel", nx + 20.0, ny + 70.0, font_size=10.0, color="#94a3b8")

        # Multi-layer layered cards demonstration
        for idx in range(3):
            lx = 80.0 + idx * 140.0
            ly = 320.0 + idx * 20.0
            surf.fill_shadowed_rounded_rect(
                lx, ly, 180.0, 110.0, 12.0, 12.0,
                fill=pal.card_bg,
                border=pal.surface_border,
                border_width=1.0,
                shadow_blur=14.0 + idx * 6.0,
                shadow_offset_y=4.0 + idx * 4.0,
                shadow_color="#00000066",
            )
            surf.draw_text(f"Layer {idx + 1} (Elev {idx + 1})", lx + 16.0, ly + 24.0, font_size=10.0, color=pal.fg)

    def _draw_scratchpad_mode(self, surf: Surface, w: float, h: float, pal) -> None:
        surf.draw_text("Interactive Freehand Vector Drawing (Drag mouse on canvas)", 20.0, 24.0, font_size=11.0, color=pal.fg_subtle)

        # Draw all stroke paths
        for stroke in self._freehand_strokes:
            if len(stroke) < 2:
                if len(stroke) == 1:
                    sx, sy, scol, ssz = stroke[0]
                    surf.fill_circle(sx, sy, ssz / 2.0, scol)
                continue

            p = Path()
            p.move_to(stroke[0][0], stroke[0][1])
            for i in range(1, len(stroke)):
                xc = (stroke[i - 1][0] + stroke[i][0]) / 2.0
                yc = (stroke[i - 1][1] + stroke[i][1]) / 2.0
                p.quad_to(stroke[i - 1][0], stroke[i - 1][1], xc, yc)
            p.line_to(stroke[-1][0], stroke[-1][1])

            stroke_col = stroke[0][2]
            stroke_sz = stroke[0][3]
            surf.stroke_path(p, stroke_col, stroke_width=stroke_sz)

    def _on_theme_changed(self, theme_name: str) -> None:
        set_theme(theme_name)

    def _on_global_theme_changed(self, pal) -> None:
        try:
            self.configure(background=pal.bg)
            cascade_bg_to_children(self, pal.bg)
            self._update_ctrl_panel()
            self._canvas.redraw()
        except Exception:
            pass


def main():
    root = tk.Tk()
    root.title("tkblend Creative Canvas & Vector Art Studio")
    root.geometry("1020x720")
    root.minsize(900, 600)

    ScalingTracker.activate_high_dpi_awareness()
    set_theme("dark")

    studio = CanvasStudio(root)
    studio.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
