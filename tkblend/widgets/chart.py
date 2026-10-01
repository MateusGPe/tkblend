"""
High-performance pure vector Chart widgets for tkblend.
Zero TTK dependencies. Provides LineChart, AreaChart, BarChart, PieChart, and DonutChart
with multi-series plotting, smooth Bézier curves, gradient backdrops, interactive hover tooltips,
legends, and real-time .push_data() streaming.
"""

from __future__ import annotations
import math
import tkinter as tk
from typing import Optional, Sequence, List, Dict, Union, Tuple, Any

from tkblend.surface import Surface, Path, LinearGradient, ColorLike, parse_color
from tkblend.theme import get_theme, Palette
from tkblend.widgets.base import Widget, ScalingTracker, _resolve_color


DEFAULT_SERIES_COLORS = [
    "#3b82f6",  # Blue
    "#10b981",  # Emerald
    "#f59e0b",  # Amber
    "#ef4444",  # Red
    "#8b5cf6",  # Purple
    "#06b6d4",  # Cyan
    "#ec4899",  # Pink
    "#14b8a6",  # Teal
]


class BaseChart(Widget):
    """
    Base class for interactive vector charts with High-DPI support,
    grid rendering, axis coordinate mapping, and hover tooltips.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 480,
        height: int = 240,
        title: str = "",
        show_grid: bool = True,
        show_legend: bool = True,
        show_tooltip: bool = True,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._title = title
        self._show_grid = show_grid
        self._show_legend = show_legend
        self._show_tooltip = show_tooltip
        self._hover_x: Optional[float] = None
        self._hover_y: Optional[float] = None
        self._hover_active: bool = False

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            tag_name="chart",
            **kwargs,
        )

        self.bind("<Motion>", self._on_mouse_motion)
        self.bind("<Leave>", self._on_mouse_leave)

    def _on_mouse_motion(self, event: tk.Event) -> None:
        if not self._show_tooltip:
            return
        self._hover_x = float(event.x)
        self._hover_y = float(event.y)
        self._hover_active = True
        self.render()

    def _on_mouse_leave(self, _event: tk.Event) -> None:
        if self._hover_active:
            self._hover_active = False
            self._hover_x = None
            self._hover_y = None
            self.render()

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, text: str) -> None:
        self._title = text
        self.render()


class LineChart(BaseChart):
    """
    Interactive multi-series vector line and spline chart.
    Supports real-time data streaming via .push_data().
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        data: Optional[Union[Sequence[float], Dict[str, Sequence[float]]]] = None,
        width: int = 500,
        height: int = 240,
        title: str = "",
        smooth: bool = True,
        fill_area: bool = False,
        line_width: float = 2.5,
        show_markers: bool = True,
        x_labels: Optional[Sequence[str]] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._series: Dict[str, Dict[str, Any]] = {}
        self._smooth = smooth
        self._fill_area = fill_area
        self._line_width = line_width
        self._show_markers = show_markers
        self._x_labels = list(x_labels) if x_labels else []

        if data is not None:
            if isinstance(data, dict):
                for idx, (name, values) in enumerate(data.items()):
                    color = DEFAULT_SERIES_COLORS[idx % len(DEFAULT_SERIES_COLORS)]
                    self._series[name] = {"data": [float(v) for v in values], "color": color}
            elif isinstance(data, (list, tuple)):
                self._series["Series 1"] = {"data": [float(v) for v in data], "color": DEFAULT_SERIES_COLORS[0]}

        super().__init__(
            master=master,
            width=width,
            height=height,
            title=title,
            parent_bg=parent_bg,
            **kwargs,
        )

    def add_series(
        self,
        name: str,
        data: Sequence[float],
        color: Optional[ColorLike] = None,
        fill_area: Optional[bool] = None,
    ) -> None:
        """Add or update a named series dataset."""
        idx = len(self._series)
        col = color or DEFAULT_SERIES_COLORS[idx % len(DEFAULT_SERIES_COLORS)]
        self._series[name] = {
            "data": [float(v) for v in data],
            "color": col,
            "fill_area": fill_area if fill_area is not None else self._fill_area,
        }
        self.render()

    def set_data(self, data: Sequence[float], name: str = "Series 1") -> None:
        """Set a single series dataset."""
        self._series = {name: {"data": [float(v) for v in data], "color": DEFAULT_SERIES_COLORS[0]}}
        self.render()

    def push_data(self, values: Union[float, Dict[str, float]], max_points: int = 50) -> None:
        """Stream new data points to active series and redraw."""
        if isinstance(values, dict):
            for name, val in values.items():
                if name not in self._series:
                    self.add_series(name, [val])
                else:
                    self._series[name]["data"].append(float(val))
                    if len(self._series[name]["data"]) > max_points:
                        self._series[name]["data"] = self._series[name]["data"][-max_points:]
        else:
            if not self._series:
                self.add_series("Series 1", [values])
            else:
                first_key = next(iter(self._series.keys()))
                self._series[first_key]["data"].append(float(values))
                if len(self._series[first_key]["data"]) > max_points:
                    self._series[first_key]["data"] = self._series[first_key]["data"][-max_points:]
        self.render()

    def render(self) -> None:
        if self._surface is None:
            return

        w = float(self._widget_w)
        h = float(self._widget_h)
        s = self._scale
        pal = get_theme()

        self._surface.clear(self._parent_bg)

        # Plot margins
        pad_l = 48.0 * s
        pad_r = 20.0 * s
        pad_t = 36.0 * s if (self._title or self._show_legend) else 16.0 * s
        pad_b = 32.0 * s

        plot_w = max(1.0, w - pad_l - pad_r)
        plot_h = max(1.0, h - pad_t - pad_b)

        # Title
        if self._title:
            self._surface.draw_text(self._title, pad_l, 14.0 * s, font_size=12.0 * s, bold=True, color=pal.fg)

        # Compute min/max across all series
        all_vals: List[float] = []
        max_n = 0
        for s_data in self._series.values():
            all_vals.extend(s_data["data"])
            max_n = max(max_n, len(s_data["data"]))

        if not all_vals or max_n < 2:
            self.end_render()
            return

        min_v = min(all_vals)
        max_v = max(all_vals)
        if min_v == max_v:
            min_v -= 1.0
            max_v += 1.0
        rng = max_v - min_v

        # Render Gridlines & Y-Axis labels
        if self._show_grid:
            grid_col = pal.card_border if hasattr(pal, "card_border") else "#334155"
            label_col = pal.secondary if hasattr(pal, "secondary") else "#94a3b8"
            steps = 4
            for i in range(steps + 1):
                gy = pad_t + (i / steps) * plot_h
                val = max_v - (i / steps) * rng
                self._surface.draw_line(pad_l, gy, w - pad_r, gy, grid_col, stroke_width=0.8 * s)
                # Y axis label
                lbl = f"{val:.1f}" if abs(val) < 10 else f"{int(round(val))}"
                self._surface.draw_text(lbl, pad_l - 6.0 * s, gy - 4.0 * s, font_size=9.0 * s, color=label_col, align="right")

        # Render Legends top right
        if self._show_legend and len(self._series) > 0:
            leg_x = w - pad_r
            for name, s_data in reversed(list(self._series.items())):
                col = s_data["color"]
                # measure text width approx
                txt_w = len(name) * 6.5 * s
                leg_x -= txt_w + 16.0 * s
                self._surface.fill_circle(leg_x + 4.0 * s, 18.0 * s, 3.5 * s, col)
                self._surface.draw_text(name, leg_x + 12.0 * s, 14.0 * s, font_size=9.5 * s, color=pal.fg)

        # Plot each series
        hover_idx: Optional[int] = None
        if self._hover_active and self._hover_x is not None:
            if pad_l <= self._hover_x <= w - pad_r:
                rel_x = (self._hover_x - pad_l) / plot_w
                hover_idx = max(0, min(max_n - 1, int(round(rel_x * (max_n - 1)))))

        tooltip_items: List[Tuple[str, str, ColorLike, float, float]] = []

        for name, s_data in self._series.items():
            pts: List[Tuple[float, float]] = []
            vals = s_data["data"]
            col = s_data["color"]
            n = len(vals)
            if n < 2:
                continue

            for i, v in enumerate(vals):
                x = pad_l + (i / (max_n - 1)) * plot_w
                y = (pad_t + plot_h) - ((v - min_v) / rng) * plot_h
                pts.append((x, y))

            # Fill Area
            if s_data.get("fill_area", self._fill_area):
                path_fill = Path()
                path_fill.move_to(pts[0][0], pad_t + plot_h)
                path_fill.line_to(pts[0][0], pts[0][1])

                if self._smooth and n > 2:
                    for i in range(1, len(pts)):
                        xc = (pts[i - 1][0] + pts[i][0]) / 2.0
                        yc = (pts[i - 1][1] + pts[i][1]) / 2.0
                        path_fill.quad_to(pts[i - 1][0], pts[i - 1][1], xc, yc)
                    path_fill.line_to(pts[-1][0], pts[-1][1])
                else:
                    for i in range(1, len(pts)):
                        path_fill.line_to(pts[i][0], pts[i][1])

                path_fill.line_to(pts[-1][0], pad_t + plot_h)
                path_fill.close()

                grad = LinearGradient(0.0, pad_t, 0.0, pad_t + plot_h)
                grad.add_stop(0.0, col, alpha=0.35)
                grad.add_stop(1.0, col, alpha=0.02)
                self._surface.fill_path(path_fill, grad)

            # Stroke Line
            path_stroke = Path()
            path_stroke.move_to(pts[0][0], pts[0][1])
            if self._smooth and n > 2:
                for i in range(1, len(pts)):
                    xc = (pts[i - 1][0] + pts[i][0]) / 2.0
                    yc = (pts[i - 1][1] + pts[i][1]) / 2.0
                    path_stroke.quad_to(pts[i - 1][0], pts[i - 1][1], xc, yc)
                path_stroke.line_to(pts[-1][0], pts[-1][1])
            else:
                for i in range(1, len(pts)):
                    path_stroke.line_to(pts[i][0], pts[i][1])

            self._surface.stroke_path(path_stroke, col, stroke_width=self._line_width * s)

            # Hover point record
            if hover_idx is not None and hover_idx < len(pts):
                hx, hy = pts[hover_idx]
                val_str = f"{vals[hover_idx]:.2f}" if abs(vals[hover_idx]) < 100 else f"{vals[hover_idx]:.1f}"
                tooltip_items.append((name, val_str, col, hx, hy))

        # Render Crosshair line
        if hover_idx is not None and tooltip_items:
            hx = tooltip_items[0][3]
            cross_col = pal.secondary if hasattr(pal, "secondary") else "#64748b"
            self._surface.draw_line(hx, pad_t, hx, pad_t + plot_h, cross_col, stroke_width=1.0 * s)

            # Highlight dots on crosshair
            for _, _, col, px, py in tooltip_items:
                self._surface.fill_circle(px, py, 4.5 * s, col)
                self._surface.stroke_circle(px, py, 6.5 * s, pal.bg, stroke_width=1.5 * s)

        # Floating Tooltip Badge
            self._render_tooltip_box(w, h, s, hx, pad_t, tooltip_items, pal)

        self.end_render()

    def _render_tooltip_box(
        self,
        w: float,
        h: float,
        s: float,
        anchor_x: float,
        anchor_y: float,
        items: List[Tuple[str, str, ColorLike, float, float]],
        pal: Palette,
    ) -> None:
        line_h = 16.0 * s
        box_w = 120.0 * s
        box_h = max(32.0 * s, len(items) * line_h + 12.0 * s)

        # Position box to the right or left of anchor_x
        box_x = anchor_x + 12.0 * s
        if box_x + box_w > w - 10.0 * s:
            box_x = anchor_x - box_w - 12.0 * s
        box_y = max(anchor_y, anchor_y + 10.0 * s)

        # Card shadow & background
        box_bg = pal.card_bg if hasattr(pal, "card_bg") else "#1e293b"
        border_col = pal.card_border if hasattr(pal, "card_border") else "#475569"
        self._surface.fill_rounded_rect(box_x, box_y, box_w, box_h, 6.0 * s, 6.0 * s, box_bg)
        self._surface.stroke_rounded_rect(box_x, box_y, box_w, box_h, 6.0 * s, 6.0 * s, border_col, stroke_width=1.0 * s)

        # Draw tooltip items
        for i, (name, val, col, _, _) in enumerate(items):
            iy = box_y + 8.0 * s + i * line_h
            self._surface.fill_circle(box_x + 10.0 * s, iy + 6.0 * s, 3.0 * s, col)
            self._surface.draw_text(name, box_x + 18.0 * s, iy + 2.0 * s, font_size=8.5 * s, color=pal.secondary)
            self._surface.draw_text(val, box_x + box_w - 8.0 * s, iy + 2.0 * s, font_size=9.0 * s, bold=True, color=pal.fg, align="right")


class AreaChart(LineChart):
    """Area Chart specialization with filled gradient backdrops enabled by default."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        kwargs.setdefault("fill_area", True)
        super().__init__(master=master, **kwargs)


class BarChart(BaseChart):
    """
    Crisp vector Bar Chart supporting single & grouped series with rounded bar caps.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        data: Optional[Union[Sequence[float], Dict[str, Sequence[float]]]] = None,
        categories: Optional[Sequence[str]] = None,
        width: int = 500,
        height: int = 240,
        title: str = "",
        show_values: bool = False,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._series: Dict[str, Dict[str, Any]] = {}
        self._categories = list(categories) if categories else []
        self._show_values = show_values

        if data is not None:
            if isinstance(data, dict):
                for idx, (name, values) in enumerate(data.items()):
                    color = DEFAULT_SERIES_COLORS[idx % len(DEFAULT_SERIES_COLORS)]
                    self._series[name] = {"data": [float(v) for v in values], "color": color}
            elif isinstance(data, (list, tuple)):
                self._series["Values"] = {"data": [float(v) for v in data], "color": DEFAULT_SERIES_COLORS[0]}

        super().__init__(
            master=master,
            width=width,
            height=height,
            title=title,
            parent_bg=parent_bg,
            **kwargs,
        )

    def set_data(self, data: Sequence[float], categories: Optional[Sequence[str]] = None) -> None:
        """Update single series data and optional category labels."""
        self._series = {"Values": {"data": [float(v) for v in data], "color": DEFAULT_SERIES_COLORS[0]}}
        if categories is not None:
            self._categories = list(categories)
        self.render()

    def add_series(self, name: str, data: Sequence[float], color: Optional[ColorLike] = None) -> None:
        """Add named grouped series to bar chart."""
        idx = len(self._series)
        col = color or DEFAULT_SERIES_COLORS[idx % len(DEFAULT_SERIES_COLORS)]
        self._series[name] = {"data": [float(v) for v in data], "color": col}
        self.render()

    def render(self) -> None:
        if self._surface is None:
            return

        w = float(self._widget_w)
        h = float(self._widget_h)
        s = self._scale
        pal = get_theme()

        self._surface.clear(self._parent_bg)

        pad_l = 48.0 * s
        pad_r = 20.0 * s
        pad_t = 36.0 * s if (self._title or self._show_legend) else 16.0 * s
        pad_b = 32.0 * s

        plot_w = max(1.0, w - pad_l - pad_r)
        plot_h = max(1.0, h - pad_t - pad_b)

        if self._title:
            self._surface.draw_text(self._title, pad_l, 14.0 * s, font_size=12.0 * s, bold=True, color=pal.fg)

        all_vals: List[float] = []
        num_cats = 0
        for s_data in self._series.values():
            all_vals.extend(s_data["data"])
            num_cats = max(num_cats, len(s_data["data"]))

        if not all_vals or num_cats == 0:
            self.end_render()
            return

        min_v = min(0.0, min(all_vals))
        max_v = max(0.0, max(all_vals))
        if min_v == max_v:
            max_v = 1.0
        rng = max_v - min_v

        # Render Gridlines
        if self._show_grid:
            grid_col = pal.card_border if hasattr(pal, "card_border") else "#334155"
            label_col = pal.secondary if hasattr(pal, "secondary") else "#94a3b8"
            steps = 4
            for i in range(steps + 1):
                gy = pad_t + (i / steps) * plot_h
                val = max_v - (i / steps) * rng
                self._surface.draw_line(pad_l, gy, w - pad_r, gy, grid_col, stroke_width=0.8 * s)
                lbl = f"{val:.1f}" if abs(val) < 10 else f"{int(round(val))}"
                self._surface.draw_text(lbl, pad_l - 6.0 * s, gy - 4.0 * s, font_size=9.0 * s, color=label_col, align="right")

        zero_y = (pad_t + plot_h) - ((0.0 - min_v) / rng) * plot_h

        # Category slot width
        cat_w = plot_w / num_cats
        num_series = len(self._series)
        bar_gap = 2.0 * s
        inner_w = cat_w * 0.75
        single_bar_w = max(3.0 * s, (inner_w - (num_series - 1) * bar_gap) / num_series)

        for cat_idx in range(num_cats):
            group_x = pad_l + cat_idx * cat_w + (cat_w - inner_w) / 2.0

            # Category x label
            if cat_idx < len(self._categories):
                lbl_text = self._categories[cat_idx]
                self._surface.draw_text(
                    lbl_text,
                    group_x + inner_w / 2.0,
                    pad_t + plot_h + 8.0 * s,
                    font_size=9.0 * s,
                    color=pal.secondary,
                    align="center",
                )

            for s_idx, (s_name, s_data) in enumerate(self._series.items()):
                vals = s_data["data"]
                if cat_idx >= len(vals):
                    continue
                v = vals[cat_idx]
                bx = group_x + s_idx * (single_bar_w + bar_gap)
                v_h = ((v - 0.0) / rng) * plot_h

                if v >= 0:
                    by = zero_y - v_h
                    bh = v_h
                else:
                    by = zero_y
                    bh = abs(v_h)

                rx = min(single_bar_w / 2.0, 3.0 * s)
                col = s_data["color"]

                # Highlight on hover
                if self._hover_active and self._hover_x is not None and self._hover_y is not None:
                    if bx <= self._hover_x <= bx + single_bar_w and min(by, zero_y) <= self._hover_y <= max(by + bh, zero_y):
                        # Glow outline
                        self._surface.fill_rounded_rect(bx - 1.5 * s, by - 1.5 * s, single_bar_w + 3.0 * s, bh + 3.0 * s, rx + 1.0 * s, rx + 1.0 * s, col)

                self._surface.fill_rounded_rect(bx, by, single_bar_w, max(2.0 * s, bh), rx, rx, col)

                if self._show_values:
                    val_str = f"{int(round(v))}" if abs(v) >= 10 else f"{v:.1f}"
                    self._surface.draw_text(
                        val_str,
                        bx + single_bar_w / 2.0,
                        by - 12.0 * s,
                        font_size=8.5 * s,
                        bold=True,
                        color=pal.fg,
                        align="center",
                    )

        self.end_render()


class PieChart(BaseChart):
    """
    Radial slice chart supporting Pie and Donut visualizations with hover explode effects.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        data: Optional[Dict[str, float]] = None,
        width: int = 320,
        height: int = 240,
        inner_radius: float = 0.0,
        title: str = "",
        show_legend: bool = True,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._data: Dict[str, float] = dict(data) if data else {}
        self._inner_radius_ratio = max(0.0, min(0.85, float(inner_radius)))
        self._hover_slice: Optional[str] = None

        super().__init__(
            master=master,
            width=width,
            height=height,
            title=title,
            show_legend=show_legend,
            parent_bg=parent_bg,
            **kwargs,
        )

    def set_data(self, data: Dict[str, float]) -> None:
        """Update slice dataset and trigger redraw."""
        self._data = {k: float(v) for k, v in data.items()}
        self.render()

    def render(self) -> None:
        if self._surface is None:
            return

        w = float(self._widget_w)
        h = float(self._widget_h)
        s = self._scale
        pal = get_theme()

        self._surface.clear(self._parent_bg)

        if self._title:
            self._surface.draw_text(self._title, 16.0 * s, 14.0 * s, font_size=12.0 * s, bold=True, color=pal.fg)

        total = sum(self._data.values())
        if total <= 0:
            self.end_render()
            return

        # Chart center and outer radius
        top_offset = 24.0 * s if self._title else 0.0
        legend_w = 110.0 * s if self._show_legend else 0.0

        avail_w = w - legend_w
        cx = avail_w / 2.0
        cy = (h + top_offset) / 2.0
        radius = min(avail_w / 2.0 - 16.0 * s, (h - top_offset) / 2.0 - 16.0 * s)
        inner_r = radius * self._inner_radius_ratio

        # Determine hover angle if mouse is over pie
        hover_key: Optional[str] = None
        if self._hover_active and self._hover_x is not None and self._hover_y is not None:
            dx = self._hover_x - cx
            dy = self._hover_y - cy
            dist = math.hypot(dx, dy)
            if inner_r <= dist <= radius + 10.0 * s:
                angle = math.atan2(dy, dx)
                # Drawing starts at -pi/2 (12 o'clock) and goes clockwise
                start_angle = -math.pi / 2.0
                rel_angle = (angle - start_angle) % (2.0 * math.pi)
                # Map relative angle to slice
                curr_a = 0.0
                for k, val in self._data.items():
                    span = (val / total) * 2.0 * math.pi
                    if curr_a <= rel_angle <= curr_a + span:
                        hover_key = k
                        break
                    curr_a += span

        # Render Slices using path arcs
        curr_angle = -math.pi / 2.0  # Start at 12 o'clock
        for idx, (label, val) in enumerate(self._data.items()):
            span = (val / total) * 2.0 * math.pi
            col = DEFAULT_SERIES_COLORS[idx % len(DEFAULT_SERIES_COLORS)]

            # Explode hovered slice slightly outward
            slice_cx = cx
            slice_cy = cy
            if label == hover_key:
                mid_a = curr_angle + span / 2.0
                explode_dist = 6.0 * s
                slice_cx += math.cos(mid_a) * explode_dist
                slice_cy += math.sin(mid_a) * explode_dist

            path = Path()
            # Outer arc
            x0 = slice_cx + radius * math.cos(curr_angle)
            y0 = slice_cy + radius * math.sin(curr_angle)
            path.move_to(x0, y0)
            path.arc_to(slice_cx, slice_cy, radius, radius, curr_angle, span)

            if inner_r > 0:
                # Donut inner arc in reverse
                x_in_end = slice_cx + inner_r * math.cos(curr_angle + span)
                y_in_end = slice_cy + inner_r * math.sin(curr_angle + span)
                path.line_to(x_in_end, y_in_end)
                path.arc_to(slice_cx, slice_cy, inner_r, inner_r, curr_angle + span, -span)
            else:
                path.line_to(slice_cx, slice_cy)

            path.close()
            self._surface.fill_path(path, col)
            self._surface.stroke_path(path, self._parent_bg, stroke_width=2.0 * s)

            curr_angle += span

        # Center label for Donut
        if self._inner_radius_ratio > 0.35:
            if hover_key and hover_key in self._data:
                val = self._data[hover_key]
                pct = (val / total) * 100.0
                self._surface.draw_text(f"{pct:.1f}%", cx, cy - 6.0 * s, font_size=13.0 * s, bold=True, color=pal.fg, align="center")
                self._surface.draw_text(hover_key, cx, cy + 10.0 * s, font_size=8.5 * s, color=pal.secondary, align="center")
            else:
                self._surface.draw_text(f"{int(total)}", cx, cy - 6.0 * s, font_size=13.0 * s, bold=True, color=pal.fg, align="center")
                self._surface.draw_text("Total", cx, cy + 10.0 * s, font_size=8.5 * s, color=pal.secondary, align="center")

        # Render Legend on the right
        if self._show_legend:
            leg_x = avail_w + 10.0 * s
            leg_y = top_offset + 20.0 * s
            for idx, (label, val) in enumerate(self._data.items()):
                col = DEFAULT_SERIES_COLORS[idx % len(DEFAULT_SERIES_COLORS)]
                pct = (val / total) * 100.0
                iy = leg_y + idx * 20.0 * s
                self._surface.fill_circle(leg_x + 4.0 * s, iy + 6.0 * s, 4.0 * s, col)
                self._surface.draw_text(label, leg_x + 14.0 * s, iy + 1.0 * s, font_size=9.0 * s, color=pal.fg)
                self._surface.draw_text(f"{pct:.0f}%", leg_x + legend_w - 14.0 * s, iy + 1.0 * s, font_size=8.5 * s, color=pal.secondary, align="right")

        self.end_render()


class DonutChart(PieChart):
    """Donut Chart specialization with a default inner radius of 0.60."""

    def __init__(self, master: Optional[tk.Misc] = None, inner_radius: float = 0.60, **kwargs):
        super().__init__(master=master, inner_radius=inner_radius, **kwargs)
