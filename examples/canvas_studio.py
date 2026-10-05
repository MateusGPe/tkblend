#!/usr/bin/env python3
"""
tkblend Showcase: Creative Canvas & Vector Art Studio.
Demonstrates:
  - Pure Blend2D surface & vector widget architecture (Zero TTK dependencies)
  - Interactive SegmentedButton, ComboBox, Slider, Card, Button, Badge & Label controls
  - Advanced BlendCanvas and Surface 2D vector graphics engine
  - Cubic and Quadratic Bézier curves, SVG-like Paths, and geometry clipping
  - Multi-stop Linear and Radial Gradients with extend modes (PAD, REPEAT, REFLECT)
  - Native 2D Composition Blend Modes (COMP_OP_MULTIPLY, SCREEN, OVERLAY, XOR, PLUS, etc.)
  - High-performance O(1) multi-layer drop shadows and glow effects
  - Interactive smooth freehand vector drawing scratchpad with undo and live palette
"""

from __future__ import annotations

import math
import random
import tkinter as tk
from typing import Optional, List, Tuple, Dict

import tkblend as tb
from tkblend import (
    BlendCanvas,
    Surface,
    LinearGradient,
    RadialGradient,
    Path,
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
)
from tkblend.widgets import (
    Button,
    Card,
    ComboBox,
    Label,
    Badge,
    SegmentedButton,
    Slider,
)


class CanvasStudio(tk.Frame):
    """Interactive vector graphics studio demonstrating Blend2D surface rendering and native widgets."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self._active_mode = "Paths & Curves"

        # Paths state
        self._star_points = 8
        self._path_stroke_width = 4.0
        self._seed_offset = 0.0

        # Gradients state
        self._extend_mode_name = "PAD"
        self._gradient_inverted = False

        # Composition state
        self._comp_mode = "SRC_OVER"

        # Shadow state
        self._shadow_blur = 16.0
        self._shadow_spread = 0.0
        self._shadow_offset_y = 6.0
        self._shadow_opacity = 0.55

        # Scratchpad state
        self._brush_size = 6.0
        self._brush_color = "#3b82f6"
        self._freehand_strokes: List[List[Tuple[float, float, str, float]]] = []
        self._current_stroke: List[Tuple[float, float, str, float]] = []

        # Inspector panels map
        self._panels: Dict[str, tk.Frame] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        pal = get_theme()
        self.configure(background=pal.bg)

        # ----------------------------------------------------------------------
        # Top Header Bar
        # ----------------------------------------------------------------------
        hdr_frame = tk.Frame(self, background=pal.bg)
        hdr_frame.pack(fill="x", padx=20, pady=(16, 8))

        # Title & Subtitle
        tbox = tk.Frame(hdr_frame, background=pal.bg)
        tbox.pack(side="left", fill="y")

        title_row = tk.Frame(tbox, background=pal.bg)
        title_row.pack(anchor="w")

        Label(
            title_row,
            text="Creative Canvas & Vector Studio",
            font_size=18.0,
            bold=True,
            fg_color=pal.fg,
            parent_bg=pal.bg,
        ).pack(side="left")

        Badge(
            title_row,
            text="Blend2D JIT",
            variant="primary",
            parent_bg=pal.bg,
        ).pack(side="left", padx=(10, 0))

        Label(
            tbox,
            text="Hardware-accelerated 2D vector primitives, gradients, shadows & blend operators",
            font_size=11.0,
            fg_color=pal.fg_subtle,
            parent_bg=pal.bg,
        ).pack(anchor="w", pady=(2, 0))

        # Right Theme Selector
        cbox = tk.Frame(hdr_frame, background=pal.bg)
        cbox.pack(side="right", fill="y")

        Label(
            cbox,
            text="Theme",
            font_size=11.0,
            fg_color=pal.fg_subtle,
            parent_bg=pal.bg,
        ).pack(side="left", padx=(0, 8))

        themes = list(get_available_themes())
        current_theme = pal.name if pal.name in themes else ("dark" if "dark" in themes else themes[0])
        self._theme_combo = ComboBox(
            cbox,
            values=themes,
            selected_value=current_theme,
            width=130,
            height=34,
            command=self._on_theme_changed,
            parent_bg=pal.bg,
        )
        self._theme_combo.pack(side="left")

        # ----------------------------------------------------------------------
        # Mode Switcher Bar (SegmentedButton)
        # ----------------------------------------------------------------------
        mode_bar = tk.Frame(self, background=pal.bg)
        mode_bar.pack(fill="x", padx=20, pady=(4, 10))

        modes = [
            "Paths & Curves",
            "Gradients & Extends",
            "Composition Modes",
            "Shadows & Glow",
            "Freehand Scratchpad",
        ]
        self._mode_seg = SegmentedButton(
            mode_bar,
            values=modes,
            selected_value=self._active_mode,
            command=self._set_mode,
            height=36,
            parent_bg=pal.bg,
        )
        self._mode_seg.pack(fill="x")

        # ----------------------------------------------------------------------
        # Main Workspace: Left Main BlendCanvas Card + Right Parameter Inspector Card
        # ----------------------------------------------------------------------
        workspace = tk.Frame(self, background=pal.bg)
        workspace.pack(fill="both", expand=True, padx=20, pady=(4, 16))

        # Left Vector Canvas Card
        self._canvas_card = Card(
            workspace,
            corner_radius=14.0,
            shadow_blur=12.0,
            bg_color=pal.card_bg,
            border_color=pal.card_border,
            border_width=1.0,
            parent_bg=pal.bg,
        )
        self._canvas_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self._canvas = BlendCanvas(
            self._canvas_card,
            width=640,
            height=520,
            bg="surface",
            on_draw=self._draw_canvas,
        )
        self._canvas.pack(fill="both", expand=True, padx=8, pady=8)

        # Mouse bindings for scratchpad drawing
        self._canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self._canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

        # Right Parameter Inspector Card
        self._inspector_card = Card(
            workspace,
            width=320,
            corner_radius=14.0,
            shadow_blur=12.0,
            bg_color=pal.card_bg,
            border_color=pal.card_border,
            border_width=1.0,
            parent_bg=pal.bg,
        )
        self._inspector_card.pack(side="right", fill="y", padx=(6, 0))
        self._inspector_card.pack_propagate(False)

        self._build_inspector_panels(self._inspector_card)

        # Theme listener
        from tkblend.theme import add_theme_listener
        add_theme_listener(self._on_global_theme_changed)

        cascade_bg_to_children(self, pal.bg)

    # --------------------------------------------------------------------------
    # Inspector Panels Creation (Pre-built for Instant Switching)
    # --------------------------------------------------------------------------

    def _build_inspector_panels(self, container: tk.Widget) -> None:
        pal = get_theme()

        # 1. Paths & Curves Panel
        p_paths = tk.Frame(container, background=pal.card_bg)
        self._panels["Paths & Curves"] = p_paths

        Label(p_paths, text="Vector Geometry & Paths", font_size=13.0, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(16, 2))
        Label(p_paths, text="Anti-aliased cubic Bézier ribbons, star polygons, and nested vector arcs.", font_size=10.0, fg_color=pal.fg_subtle, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(0, 14))

        Label(p_paths, text="Star Polygon Points", font_size=10.5, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(4, 2))
        Slider(p_paths, from_=3, to=16, number_of_steps=13, value=self._star_points, command=self._set_star_points, height=28, parent_bg=pal.card_bg).pack(fill="x", padx=16, pady=(0, 10))

        Label(p_paths, text="Wave Stroke Width", font_size=10.5, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(4, 2))
        Slider(p_paths, from_=1.0, to=12.0, value=self._path_stroke_width, command=self._set_path_stroke_width, height=28, parent_bg=pal.card_bg).pack(fill="x", padx=16, pady=(0, 16))

        Button(p_paths, text="Re-seed Curve Points", height=34, command=self._reseed_curves, parent_bg=pal.card_bg).pack(fill="x", padx=16, pady=4)

        # 2. Gradients & Extends Panel
        p_grad = tk.Frame(container, background=pal.card_bg)
        self._panels["Gradients & Extends"] = p_grad

        Label(p_grad, text="Gradient Matrix & Extends", font_size=13.0, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(16, 2))
        Label(p_grad, text="Multi-stop Linear and Radial gradients with native hardware repeat extend modes.", font_size=10.0, fg_color=pal.fg_subtle, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(0, 14))

        Label(p_grad, text="Extend Mode", font_size=10.5, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(4, 2))
        ComboBox(p_grad, values=["PAD", "REPEAT", "REFLECT"], selected_value=self._extend_mode_name, command=self._set_extend_mode, height=34, parent_bg=pal.card_bg).pack(fill="x", padx=16, pady=(0, 14))

        Button(p_grad, text="Invert Gradient Stops", height=34, command=self._invert_gradients, parent_bg=pal.card_bg).pack(fill="x", padx=16, pady=6)

        # 3. Composition Modes Panel
        p_comp = tk.Frame(container, background=pal.card_bg)
        self._panels["Composition Modes"] = p_comp

        Label(p_comp, text="Composition Blend Operators", font_size=13.0, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(16, 2))
        Label(p_comp, text="GPU-accelerated channel blending math between overlapping vector layers.", font_size=10.0, fg_color=pal.fg_subtle, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(0, 14))

        Label(p_comp, text="Active Blend Operator", font_size=10.5, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(4, 2))
        modes = ["SRC_OVER", "MULTIPLY", "SCREEN", "OVERLAY", "XOR", "PLUS", "DARKEN", "LIGHTEN"]
        ComboBox(p_comp, values=modes, selected_value=self._comp_mode, command=self._set_comp_mode, height=34, parent_bg=pal.card_bg).pack(fill="x", padx=16, pady=(0, 14))

        Badge(p_comp, text="JIT Accelerated Math", variant="outline", parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=6)

        # 4. Shadows & Glow Panel
        p_shad = tk.Frame(container, background=pal.card_bg)
        self._panels["Shadows & Glow"] = p_shad

        Label(p_shad, text="Drop Shadow & Glow", font_size=13.0, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(16, 2))
        Label(p_shad, text="Multi-layer soft shadows rendered with O(1) gaussian convolution kernels.", font_size=10.0, fg_color=pal.fg_subtle, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(0, 14))

        Label(p_shad, text="Blur Radius", font_size=10.5, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(4, 2))
        Slider(p_shad, from_=0.0, to=40.0, value=self._shadow_blur, command=self._set_blur, height=28, parent_bg=pal.card_bg).pack(fill="x", padx=16, pady=(0, 8))

        Label(p_shad, text="Offset Y", font_size=10.5, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(4, 2))
        Slider(p_shad, from_=-20.0, to=40.0, value=self._shadow_offset_y, command=self._set_offset_y, height=28, parent_bg=pal.card_bg).pack(fill="x", padx=16, pady=(0, 8))

        Label(p_shad, text="Spread", font_size=10.5, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(4, 2))
        Slider(p_shad, from_=-10.0, to=20.0, value=self._shadow_spread, command=self._set_spread, height=28, parent_bg=pal.card_bg).pack(fill="x", padx=16, pady=(0, 8))

        Label(p_shad, text="Shadow Opacity", font_size=10.5, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(4, 2))
        Slider(p_shad, from_=0.1, to=1.0, value=self._shadow_opacity, command=self._set_shadow_opacity, height=28, parent_bg=pal.card_bg).pack(fill="x", padx=16, pady=(0, 12))

        # 5. Freehand Scratchpad Panel
        p_pad = tk.Frame(container, background=pal.card_bg)
        self._panels["Freehand Scratchpad"] = p_pad

        Label(p_pad, text="Vector Scratchpad", font_size=13.0, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(16, 2))
        Label(p_pad, text="Realtime smoothed Bézier pen strokes with variable width and palette.", font_size=10.0, fg_color=pal.fg_subtle, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(0, 14))

        Label(p_pad, text="Brush Size", font_size=10.5, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(4, 2))
        Slider(p_pad, from_=1.0, to=30.0, value=self._brush_size, command=self._set_brush_size, height=28, parent_bg=pal.card_bg).pack(fill="x", padx=16, pady=(0, 10))

        Label(p_pad, text="Ink Palette", font_size=10.5, bold=True, fg_color=pal.fg, parent_bg=pal.card_bg).pack(anchor="w", padx=16, pady=(4, 6))

        # Color chips grid
        colors = ["#3b82f6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#f8fafc"]
        color_grid = tk.Frame(p_pad, background=pal.card_bg)
        color_grid.pack(fill="x", padx=14, pady=(0, 14))

        for idx, col in enumerate(colors):
            c_btn = Button(
                color_grid,
                text="",
                width=30,
                height=30,
                corner_radius=15,
                bg_color=col,
                hover_color=col,
                pressed_color=col,
                border_color="#ffffff" if col == self._brush_color else "#00000033",
                border_width=2.0 if col == self._brush_color else 1.0,
                command=lambda c=col: self._set_brush_color(c),
                parent_bg=pal.card_bg,
            )
            c_btn.grid(row=idx // 4, column=idx % 4, padx=3, pady=3)

        btn_row = tk.Frame(p_pad, background=pal.card_bg)
        btn_row.pack(fill="x", padx=16, pady=6)

        Button(
            btn_row,
            text="Undo",
            bg_color=pal.card_bg,
            border_color=pal.card_border,
            border_width=1.0,
            fg_color=pal.fg,
            height=34,
            command=self._undo_stroke,
            parent_bg=pal.card_bg,
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        Button(
            btn_row,
            text="Clear",
            bg_color="#ef4444",
            hover_color="#dc2626",
            fg_color="#ffffff",
            height=34,
            command=self._clear_scratchpad,
            parent_bg=pal.card_bg,
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Show initial panel
        self._show_panel(self._active_mode)

    def _show_panel(self, mode_name: str) -> None:
        for name, panel in self._panels.items():
            if name == mode_name:
                panel.pack(fill="both", expand=True)
            else:
                panel.pack_forget()

    # --------------------------------------------------------------------------
    # Interactive State Handlers
    # --------------------------------------------------------------------------

    def _set_mode(self, mode_name: str) -> None:
        self._active_mode = mode_name
        self._show_panel(mode_name)
        self._canvas.redraw()

    def _set_star_points(self, val: float) -> None:
        self._star_points = int(round(val))
        self._canvas.redraw()

    def _set_path_stroke_width(self, val: float) -> None:
        self._path_stroke_width = float(val)
        self._canvas.redraw()

    def _reseed_curves(self) -> None:
        self._seed_offset = random.uniform(-40.0, 40.0)
        self._canvas.redraw()

    def _set_extend_mode(self, mode_name: str) -> None:
        self._extend_mode_name = mode_name
        self._canvas.redraw()

    def _invert_gradients(self) -> None:
        self._gradient_inverted = not self._gradient_inverted
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

    def _set_shadow_opacity(self, val: float) -> None:
        self._shadow_opacity = float(val)
        self._canvas.redraw()

    def _set_brush_size(self, val: float) -> None:
        self._brush_size = float(val)

    def _set_brush_color(self, col: str) -> None:
        self._brush_color = col

    def _undo_stroke(self) -> None:
        if self._freehand_strokes:
            self._freehand_strokes.pop()
            self._canvas.redraw()

    def _clear_scratchpad(self) -> None:
        self._freehand_strokes.clear()
        self._current_stroke.clear()
        self._canvas.redraw()

    # --------------------------------------------------------------------------
    # Canvas Drawing Dispatcher & Renderers
    # --------------------------------------------------------------------------

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
        # 1. Cubic Bezier Wave Ribbon
        so = self._seed_offset
        p1 = Path()
        p1.move_to(30.0, 120.0 + so)
        p1.cubic_to(120.0, 20.0 - so, 240.0, 220.0 + so, 320.0, 100.0)
        p1.cubic_to(400.0, -20.0 - so, 520.0, 180.0 + so, w - 40.0, 80.0)

        surf.stroke_path(p1, pal.primary or "#3b82f6", stroke_width=self._path_stroke_width)

        # 2. Geometric Star Polygon with Dynamic Point Count
        with surf.saved():
            surf.translate(140.0, 320.0)
            star_path = Path()
            points = self._star_points
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
        cx, cy = w - 180.0, 320.0
        colors = [pal.accent, pal.primary, pal.secondary, pal.success]
        for idx, (rad, sw, col) in enumerate([(80.0, 6.0, colors[0]), (64.0, 5.0, colors[1]), (48.0, 4.0, colors[2]), (32.0, 3.0, colors[3])]):
            arc = Path()
            start_ang = (idx * 0.4) * math.pi
            sweep_ang = 1.4 * math.pi
            arc.arc_to(cx, cy, rad, rad, start_ang, sweep_ang)
            surf.stroke_path(arc, col, stroke_width=sw)

        surf.draw_text("Cubic Bézier Multi-Segment Wave", 30.0, 30.0, font_size=12.0, color=pal.fg)
        surf.draw_text(f"Vector Star Polygon ({self._star_points}-gon)", 70.0, 430.0, font_size=11.0, color=pal.fg_subtle)
        surf.draw_text("Antialiased Nested Vector Arcs", w - 240.0, 430.0, font_size=11.0, color=pal.fg_subtle)

    def _draw_gradients_mode(self, surf: Surface, w: float, h: float, pal) -> None:
        extend_map = {
            "PAD": EXTEND_PAD,
            "REPEAT": EXTEND_REPEAT,
            "REFLECT": EXTEND_REFLECT,
        }
        ext = extend_map.get(self._extend_mode_name, EXTEND_PAD)

        # Colors
        c1 = "#ec4899" if self._gradient_inverted else "#3b82f6"
        c2 = "#8b5cf6"
        c3 = "#3b82f6" if self._gradient_inverted else "#ec4899"

        # Linear Gradient Box
        lx, ly, lw, lh = 30.0, 50.0, 260.0, 180.0
        lin_grad = LinearGradient(lx, ly, lx + lw, ly + lh)
        lin_grad.add_stop(0.0, c1)
        lin_grad.add_stop(0.5, c2)
        lin_grad.add_stop(1.0, c3)
        lin_grad.set_extend_mode(ext)

        surf.fill_rounded_rect(lx, ly, lw, lh, 14.0, 14.0, lin_grad)
        surf.draw_text(f"Linear Gradient ({self._extend_mode_name})", lx + 12.0, ly + 24.0, font_size=11.0, color="#ffffff")

        # Radial Gradient Box
        rx, ry, rw, rh = 320.0, 50.0, 260.0, 180.0
        rad_grad = RadialGradient(rx + rw / 2.0, ry + rh / 2.0, 80.0)
        rad_grad.add_stop(0.0, "#f59e0b" if not self._gradient_inverted else "#1e1b4b")
        rad_grad.add_stop(0.6, "#ef4444")
        rad_grad.add_stop(1.0, "#1e1b4b" if not self._gradient_inverted else "#f59e0b")
        rad_grad.set_extend_mode(ext)

        surf.fill_rounded_rect(rx, ry, rw, rh, 14.0, 14.0, rad_grad)
        surf.draw_text("Radial Gradient (Focal)", rx + 12.0, ry + 24.0, font_size=11.0, color="#ffffff")

        # Multi-Ring Wave with Gradients
        bx, by, bw, bh = 30.0, 260.0, w - 60.0, 220.0
        surf.stroke_rounded_rect(bx, by, bw, bh, 14.0, 14.0, pal.surface_border, stroke_width=1.0)

        num_rings = max(4, int(bw // 85))
        for i in range(num_rings):
            cx = bx + 60.0 + i * (bw - 120.0) / max(1, num_rings - 1)
            cy = by + 110.0
            r_g = RadialGradient(cx, cy, 32.0)
            r_g.add_stop(0.0, pal.accent if i % 2 == 0 else pal.primary)
            r_g.add_stop(1.0, "#00000000")
            r_g.set_extend_mode(ext)
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
        r = min(100.0, w / 6.0)
        d = r * 0.6

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

        # Shadow alpha hex
        alpha_hex = f"{int(self._shadow_opacity * 255):02x}"
        shadow_col = f"#000000{alpha_hex}"

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
            shadow_color=shadow_col,
        )
        surf.draw_text("Dynamic Shadow Card", cx + 20.0, cy + 30.0, font_size=12.0, color=pal.fg)
        surf.draw_text(
            f"Blur: {self._shadow_blur:.1f}px\nSpread: {self._shadow_spread:.1f}px\nOffset Y: {self._shadow_offset_y:.1f}px\nOpacity: {int(self._shadow_opacity * 100)}%",
            cx + 20.0,
            cy + 60.0,
            font_size=10.0,
            color=pal.fg_subtle,
        )

        # Glowing Neon Floating Badge Card
        nx, ny, nw, nh = 320.0, 80.0, 240.0, 180.0
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
            lx = 60.0 + idx * 130.0
            ly = 300.0 + idx * 24.0
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
            self._canvas.redraw()
        except Exception:
            pass


def main():
    root = tk.Tk()
    root.title("tkblend Creative Canvas & Vector Art Studio")
    root.geometry("1060x740")
    root.minsize(920, 620)

    set_theme("dark")

    studio = CanvasStudio(root)
    studio.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
