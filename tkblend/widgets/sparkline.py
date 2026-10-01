"""
High-performance pure vector Sparklines for compact data visualization.
Zero TTK dependencies. Supports line, area, bar, and win/loss modes with
smooth Bézier splines, dynamic theme adaptation, and real-time data streaming.
"""

from __future__ import annotations
import math
import tkinter as tk
from typing import Optional, Sequence, List, Union, Tuple

from tkblend.surface import Surface, Path, LinearGradient, ColorLike, parse_color
from tkblend.theme import get_theme, Palette
from tkblend.widgets.base import Widget, ScalingTracker, _resolve_color


class Sparkline(Widget):
    """
    Miniature vector sparkline widget for dashboards, tables, and stat panels.

    Supported kinds:
      - 'line': Smooth Bézier or straight connected line.
      - 'area': Line with translucent gradient fill to bottom.
      - 'bar': Crisp vertical value bars with rounded caps.
      - 'winloss': Binary win/loss/draw indicator bars (+1 = win, -1 = loss, 0 = tie).
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        data: Sequence[float] = (),
        kind: str = "line",
        width: int = 120,
        height: int = 36,
        color: Optional[ColorLike] = None,
        line_width: float = 2.0,
        smooth: bool = True,
        fill_alpha: float = 0.25,
        highlight_min: bool = False,
        highlight_max: bool = False,
        highlight_last: bool = True,
        min_color: Optional[ColorLike] = None,
        max_color: Optional[ColorLike] = None,
        last_color: Optional[ColorLike] = None,
        marker_radius: float = 3.0,
        baseline: Optional[float] = None,
        parent_bg: Optional[str] = None,
        **kwargs,
    ):
        self._data: List[float] = [float(v) for v in data]
        self._kind = kind.lower()
        self._explicit_color = color
        self._line_width = line_width
        self._smooth = smooth
        self._fill_alpha = max(0.0, min(1.0, float(fill_alpha)))
        self._highlight_min = highlight_min
        self._highlight_max = highlight_max
        self._highlight_last = highlight_last
        self._explicit_min_color = min_color
        self._explicit_max_color = max_color
        self._explicit_last_color = last_color
        self._marker_radius = marker_radius
        self._baseline = baseline

        super().__init__(
            master=master,
            width=width,
            height=height,
            bg=parent_bg,
            tag_name="sparkline",
            **kwargs,
        )

    # -------------------------------------------------------------------------
    # Properties & Getters/Setters
    # -------------------------------------------------------------------------

    @property
    def data(self) -> List[float]:
        return list(self._data)

    @data.setter
    def data(self, values: Sequence[float]) -> None:
        self.set_data(values)

    def set_data(self, values: Sequence[float]) -> None:
        """Update dataset and trigger immediate redraw."""
        self._data = [float(v) for v in values]
        self.render()

    def push_data(self, value: float, max_points: Optional[int] = 50) -> None:
        """Append a real-time point, optionally capping length, and redraw."""
        self._data.append(float(value))
        if max_points is not None and len(self._data) > max_points:
            self._data = self._data[-max_points:]
        self.render()

    @property
    def kind(self) -> str:
        return self._kind

    @kind.setter
    def kind(self, val: str) -> None:
        self._kind = val.lower()
        self.render()

    @property
    def color(self) -> ColorLike:
        pal = get_theme()
        return _resolve_color(self._explicit_color, pal.primary, pal)

    @color.setter
    def color(self, val: Optional[ColorLike]) -> None:
        self._explicit_color = val
        self.render()

    # -------------------------------------------------------------------------
    # Rendering Pipeline
    # -------------------------------------------------------------------------

    def render(self) -> None:
        if self._surface is None:
            return

        w = float(self._widget_w)
        h = float(self._widget_h)
        s = self._scale
        pal = get_theme()

        # Clear background
        self._surface.clear(self._parent_bg)

        if not self._data:
            self.end_render()
            return

        pad_x = 4.0 * s
        pad_y = 4.0 * s
        plot_w = max(1.0, w - 2.0 * pad_x)
        plot_h = max(1.0, h - 2.0 * pad_y)

        accent = self.color

        if self._kind in ("line", "area"):
            self._render_line_or_area(w, h, s, pad_x, pad_y, plot_w, plot_h, accent, pal)
        elif self._kind == "bar":
            self._render_bars(w, h, s, pad_x, pad_y, plot_w, plot_h, accent, pal)
        elif self._kind == "winloss":
            self._render_winloss(w, h, s, pad_x, pad_y, plot_w, plot_h, accent, pal)

        self.end_render()

    def _render_line_or_area(
        self,
        w: float,
        h: float,
        s: float,
        pad_x: float,
        pad_y: float,
        plot_w: float,
        plot_h: float,
        accent: ColorLike,
        pal: Palette,
    ) -> None:
        data = self._data
        n = len(data)
        if n == 1:
            # Single point: draw dot in center
            cx = w / 2.0
            cy = h / 2.0
            self._surface.fill_circle(cx, cy, 3.5 * s, accent)
            return

        min_v = min(data)
        max_v = max(data)
        rng = max_v - min_v
        if rng == 0.0:
            rng = 1.0

        pts: List[Tuple[float, float]] = []
        for i, val in enumerate(data):
            x = pad_x + (i / (n - 1)) * plot_w
            norm = (val - min_v) / rng
            y = (h - pad_y) - (norm * plot_h)
            pts.append((x, y))

        # Area gradient fill
        if self._kind == "area":
            path_fill = Path()
            path_fill.move_to(pts[0][0], h - pad_y)
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

            path_fill.line_to(pts[-1][0], h - pad_y)
            path_fill.close()

            grad = LinearGradient(0.0, pad_y, 0.0, h - pad_y)
            grad.add_stop(0.0, accent, alpha=self._fill_alpha)
            grad.add_stop(1.0, accent, alpha=0.02)
            self._surface.fill_path(path_fill, grad)

        # Stroke path
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

        self._surface.stroke_path(path_stroke, accent, stroke_width=self._line_width * s)

        # Highlight markers
        mr = self._marker_radius * s
        min_idx = data.index(min_v)
        max_idx = data.index(max_v)

        if self._highlight_min and min_idx not in (0, n - 1):
            col = _resolve_color(self._explicit_min_color, pal.danger if hasattr(pal, "danger") else "#ef4444", pal)
            self._surface.fill_circle(pts[min_idx][0], pts[min_idx][1], mr, col)
            self._surface.stroke_circle(pts[min_idx][0], pts[min_idx][1], mr + 1.5 * s, col, stroke_width=1.0 * s)

        if self._highlight_max and max_idx not in (0, n - 1):
            col = _resolve_color(self._explicit_max_color, pal.success if hasattr(pal, "success") else "#10b981", pal)
            self._surface.fill_circle(pts[max_idx][0], pts[max_idx][1], mr, col)
            self._surface.stroke_circle(pts[max_idx][0], pts[max_idx][1], mr + 1.5 * s, col, stroke_width=1.0 * s)

        if self._highlight_last:
            col = _resolve_color(self._explicit_last_color, accent, pal)
            self._surface.fill_circle(pts[-1][0], pts[-1][1], mr, col)
            self._surface.stroke_circle(pts[-1][0], pts[-1][1], mr + 1.5 * s, col, stroke_width=1.0 * s)

    def _render_bars(
        self,
        w: float,
        h: float,
        s: float,
        pad_x: float,
        pad_y: float,
        plot_w: float,
        plot_h: float,
        accent: ColorLike,
        pal: Palette,
    ) -> None:
        data = self._data
        n = len(data)
        min_v = min(0.0, min(data))
        max_v = max(0.0, max(data))
        rng = max(1.0, max_v - min_v)

        zero_y = (h - pad_y) - ((0.0 - min_v) / rng) * plot_h
        gap = max(1.0 * s, 2.0 * s)
        bar_w = max(2.0 * s, (plot_w - (n - 1) * gap) / n)

        for i, val in enumerate(data):
            bx = pad_x + i * (bar_w + gap)
            val_norm = ((val - min_v) / rng) * plot_h
            by = (h - pad_y) - val_norm

            if val >= 0:
                rect_y = by
                rect_h = max(2.0 * s, zero_y - by)
                col = accent
            else:
                rect_y = zero_y
                rect_h = max(2.0 * s, by - zero_y)
                col = _resolve_color(self._explicit_min_color, pal.danger if hasattr(pal, "danger") else "#ef4444", pal)

            rx = min(bar_w / 2.0, 2.0 * s)
            self._surface.fill_rounded_rect(bx, rect_y, bar_w, rect_h, rx, rx, col)

    def _render_winloss(
        self,
        w: float,
        h: float,
        s: float,
        pad_x: float,
        pad_y: float,
        plot_w: float,
        plot_h: float,
        accent: ColorLike,
        pal: Palette,
    ) -> None:
        data = self._data
        n = len(data)
        mid_y = h / 2.0
        bar_h = (plot_h / 2.0) - 1.0 * s
        gap = max(1.5 * s, 2.5 * s)
        bar_w = max(2.0 * s, (plot_w - (n - 1) * gap) / n)

        win_col = _resolve_color(self._explicit_color, pal.success if hasattr(pal, "success") else "#10b981", pal)
        loss_col = _resolve_color(self._explicit_min_color, pal.danger if hasattr(pal, "danger") else "#ef4444", pal)
        tie_col = pal.track_bg

        rx = min(bar_w / 2.0, 2.0 * s)

        for i, val in enumerate(data):
            bx = pad_x + i * (bar_w + gap)
            if val > 0:
                # Win (top half)
                self._surface.fill_rounded_rect(bx, mid_y - bar_h, bar_w, bar_h, rx, rx, win_col)
            elif val < 0:
                # Loss (bottom half)
                self._surface.fill_rounded_rect(bx, mid_y, bar_w, bar_h, rx, rx, loss_col)
            else:
                # Tie (center sliver)
                self._surface.fill_rounded_rect(bx, mid_y - 2.0 * s, bar_w, 4.0 * s, rx, rx, tie_col)
