"""
TkBlendDrawEngine - High-performance Blend2D Vector Rendering Engine for CustomTkinter.
Replaces CustomTkinter's default Tkinter Canvas polygon/font rendering with crisp Blend2D C++ vector rasterization.
"""

from __future__ import annotations
import math
import tkinter as tk
from typing import Union, Optional, Dict, Any
from tkblend.surface import Surface, Path


class TkBlendDrawEngine:
    """
    Blend2D Vector Rendering Engine for CustomTkinter widgets.
    Renders rounded rectangles, borders, sliders, progress bars, checkmarks,
    and dropdown arrows directly to a Blend2D Surface blitted onto a Canvas PhotoImage.
    """

    DRAWING_METHODS = ["blend2d_vector", "polygon_shapes", "font_shapes", "circle_shapes"]
    preferred_drawing_method = "blend2d_vector"
    enable_shadows_globally: bool = False

    def __init__(self, canvas: tk.Canvas):
        self._canvas = canvas
        self._canvas._blend_engine = self
        self._round_width_to_even_numbers: bool = True
        self._round_height_to_even_numbers: bool = True
        self._canvas_bg: Optional[str] = None

        # Rendering state
        self._shape_type: Optional[str] = None
        self._params: Dict[str, Any] = {}
        self._colors: Dict[str, Optional[str]] = {
            "inner_parts": None,
            "border_parts": None,
            "progress_parts": None,
            "slider_parts": None,
            "scrollbar_parts": None,
            "checkmark": None,
            "dropdown_arrow": None,
            "dropdown_arrow_parts": None,
            "inner_parts_left": None,
            "inner_parts_right": None,
            "background_corner_top_left": None,
            "background_corner_top_right": None,
            "background_corner_bottom_right": None,
            "background_corner_bottom_left": None,
        }

        # Active surface & photo image managed on canvas
        self._surface: Optional[Surface] = None
        self._photo: Optional[tk.PhotoImage] = None
        self._image_id: Optional[int] = None
        self._surface_w: int = 0
        self._surface_h: int = 0

        # Optional visual enhancements
        self._enable_shadows: bool = TkBlendDrawEngine.enable_shadows_globally
        self._shadow_blur: float = 8.0
        self._shadow_color: str = "#00000033"

    def set_round_to_even_numbers(
        self,
        round_width_to_even_numbers: bool = True,
        round_height_to_even_numbers: bool = True,
    ) -> None:
        self._round_width_to_even_numbers = round_width_to_even_numbers
        self._round_height_to_even_numbers = round_height_to_even_numbers

    def set_canvas_bg(self, bg: str) -> None:
        """Store canvas background color configured by CustomTkinter."""
        self._canvas_bg = bg

    def set_color(self, tag: str, color: Optional[str]) -> None:
        """Update color for a vector element tag."""
        if color is not None:
            self._colors[tag] = color
            if tag == "dropdown_arrow":
                self._colors["dropdown_arrow_parts"] = color
            elif tag == "dropdown_arrow_parts":
                self._colors["dropdown_arrow"] = color

    def get_color(self, tag: str) -> Optional[str]:
        return self._colors.get(tag)

    def is_tag_active(self, tag: str) -> bool:
        """Check whether a virtual vector tag is currently active in the current geometry."""
        if self._shape_type is None:
            return False
        if tag in ("inner_parts", "inner_line_1", "inner_rectangle_1"):
            return bool(self._params.get("width", 0) > 0 and self._params.get("height", 0) > 0)
        if tag in ("border_parts", "border_line_1", "border_rectangle_1"):
            return bool(self._params.get("border_width", 0) > 0 or self._params.get("border_spacing", 0) > 0)
        if tag in ("progress_parts", "progress_line_1"):
            return self._shape_type in ("progress_bar", "slider")
        if tag in ("slider_parts", "slider_line_1"):
            return self._shape_type == "slider"
        if tag in ("scrollbar_parts", "scrollbar_polygon_1"):
            return self._shape_type == "scrollbar"
        if tag == "checkmark":
            return bool(self._params.get("checkmark_active", False))
        if tag in ("dropdown_arrow", "dropdown_arrow_parts"):
            return bool(self._params.get("dropdown_arrow_active", False))
        if tag in ("inner_parts_left", "inner_parts_right"):
            return self._shape_type == "vertical_split"
        if tag.startswith("background_corner_"):
            return bool(self._params.get("background_corners_active", False))
        if tag == "background_parts":
            return bool(self._params.get("background_corners_active", False))
        return False

    def _resolve_bg_color(self) -> str:
        """
        Resolve the effective background color of the widget / master.
        Used to pre-fill the Blend2D surface so subpixel anti-aliasing renders
        with smooth alpha blending against the exact parent background,
        completely eliminating dark alpha-fringes and black halos.
        """
        # 1. Background corner colors if defined
        for tag in (
            "background_corner_top_left",
            "background_corner_top_right",
            "background_corner_bottom_left",
            "background_corner_bottom_right",
        ):
            c = self._colors.get(tag)
            if c and c != "transparent":
                return c

        # 2. Canvas bg attribute explicitly set
        if self._canvas_bg and self._canvas_bg != "transparent":
            return self._canvas_bg

        try:
            bg = self._canvas.cget("bg")
            if bg and bg != "transparent":
                return bg
        except Exception:
            pass

        # 3. Traverse parent hierarchy for CTk _bg_color / _fg_color or Tk cget('bg')
        curr = getattr(self._canvas, "master", None)
        while curr is not None:
            try:
                app_mode = getattr(curr, "_apply_appearance_mode", None)
                for attr in ("_fg_color", "_bg_color"):
                    if hasattr(curr, attr):
                        val = getattr(curr, attr)
                        if val:
                            resolved = app_mode(val) if app_mode else val
                            if resolved and resolved != "transparent":
                                return resolved
                bg = curr.cget("bg")
                if bg and bg != "transparent":
                    return bg
            except Exception:
                pass
            curr = getattr(curr, "master", None)

        # 4. Fallback based on CustomTkinter appearance mode
        try:
            import customtkinter as ctk
            mode = ctk.get_appearance_mode()
            return "#242424" if str(mode).lower() == "dark" else "#ebebeb"
        except Exception:
            return "#242424"

    def _ensure_surface(self, width: int, height: int) -> Surface:
        """Ensure the backing Blend2D Surface and Tk PhotoImage match the requested dimensions."""
        w = max(1, int(width))
        h = max(1, int(height))

        if self._surface is None or self._surface_w != w or self._surface_h != h:
            self._surface_w = w
            self._surface_h = h
            self._surface = Surface(w, h)

            if self._photo is None:
                self._photo = tk.PhotoImage(master=self._canvas, width=w, height=h)
            else:
                try:
                    self._photo.configure(width=w, height=h)
                except Exception:
                    self._photo = tk.PhotoImage(master=self._canvas, width=w, height=h)

            if self._image_id is None or not self._canvas.find_withtag("tkblend_surface"):
                self._image_id = self._canvas.create_image(0, 0, anchor="nw", image=self._photo, tags="tkblend_surface")
            else:
                self._canvas.itemconfig(self._image_id, image=self._photo)

            self._canvas.tag_lower("tkblend_surface")

        return self._surface

    def draw_background_corners(self, width: Union[float, int], height: Union[float, int]) -> bool:
        if self._round_width_to_even_numbers:
            width = math.floor(width / 2) * 2
        if self._round_height_to_even_numbers:
            height = math.floor(height / 2) * 2

        self._params["bg_w"] = width
        self._params["bg_h"] = height
        self._params["background_corners_active"] = True

        requires_recoloring = (
            self._colors.get("background_corner_top_left") is None
            or self._colors.get("background_corner_top_right") is None
            or self._colors.get("background_corner_bottom_right") is None
            or self._colors.get("background_corner_bottom_left") is None
        )
        self.render()
        return requires_recoloring

    def draw_rounded_rect_with_border(
        self,
        width: Union[float, int],
        height: Union[float, int],
        corner_radius: Union[float, int],
        border_width: Union[float, int],
        overwrite_preferred_drawing_method: Optional[str] = None,
    ) -> bool:
        if self._round_width_to_even_numbers:
            width = math.floor(width / 2) * 2
        if self._round_height_to_even_numbers:
            height = math.floor(height / 2) * 2

        corner_radius = round(corner_radius)
        if corner_radius > width / 2 or corner_radius > height / 2:
            corner_radius = min(width / 2, height / 2)

        border_width = round(border_width)

        self._shape_type = "rounded_rect"
        self._params.update({
            "width": width,
            "height": height,
            "corner_radius": corner_radius,
            "border_width": border_width,
        })

        self.render()
        return True

    def draw_rounded_rect_with_border_vertical_split(
        self,
        width: Union[float, int],
        height: Union[float, int],
        corner_radius: Union[float, int],
        border_width: Union[float, int],
        overwrite_preferred_drawing_method: Optional[str] = None,
    ) -> bool:
        if self._round_width_to_even_numbers:
            width = math.floor(width / 2) * 2
        if self._round_height_to_even_numbers:
            height = math.floor(height / 2) * 2

        corner_radius = round(corner_radius)
        if corner_radius > width / 2 or corner_radius > height / 2:
            corner_radius = min(width / 2, height / 2)

        border_width = round(border_width)

        self._shape_type = "vertical_split"
        self._params.update({
            "width": width,
            "height": height,
            "corner_radius": corner_radius,
            "border_width": border_width,
        })

        self.render()
        return True

    def draw_rounded_progress_bar_with_border(
        self,
        width: Union[float, int],
        height: Union[float, int],
        corner_radius: Union[float, int],
        border_width: Union[float, int],
        progress_value_1: float,
        progress_value_2: float,
        orientation: str,
    ) -> bool:
        if self._round_width_to_even_numbers:
            width = math.floor(width / 2) * 2
        if self._round_height_to_even_numbers:
            height = math.floor(height / 2) * 2

        if corner_radius > width / 2 or corner_radius > height / 2:
            corner_radius = min(width / 2, height / 2)

        border_width = round(border_width)

        self._shape_type = "progress_bar"
        self._params.update({
            "width": width,
            "height": height,
            "corner_radius": corner_radius,
            "border_width": border_width,
            "progress_value_1": progress_value_1,
            "progress_value_2": progress_value_2,
            "orientation": orientation,
        })

        self.render()
        return True

    def draw_rounded_slider_with_border_and_button(
        self,
        width: Union[float, int],
        height: Union[float, int],
        corner_radius: Union[float, int],
        border_width: Union[float, int],
        button_length: Union[float, int],
        button_corner_radius: Union[float, int],
        slider_value: float,
        orientation: str,
    ) -> bool:
        if self._round_width_to_even_numbers:
            width = math.floor(width / 2) * 2
        if self._round_height_to_even_numbers:
            height = math.floor(height / 2) * 2

        if corner_radius > width / 2 or corner_radius > height / 2:
            corner_radius = min(width / 2, height / 2)

        if button_corner_radius > width / 2 or button_corner_radius > height / 2:
            button_corner_radius = min(width / 2, height / 2)

        button_length = round(button_length)
        border_width = round(border_width)
        button_corner_radius = round(button_corner_radius)

        self._shape_type = "slider"
        self._params.update({
            "width": width,
            "height": height,
            "corner_radius": corner_radius,
            "border_width": border_width,
            "button_length": button_length,
            "button_corner_radius": button_corner_radius,
            "slider_value": slider_value,
            "orientation": orientation,
        })

        self.render()
        return True

    def draw_rounded_scrollbar(
        self,
        width: Union[float, int],
        height: Union[float, int],
        corner_radius: Union[float, int],
        border_spacing: Union[float, int],
        start_value: float,
        end_value: float,
        orientation: str,
    ) -> bool:
        if self._round_width_to_even_numbers:
            width = math.floor(width / 2) * 2
        if self._round_height_to_even_numbers:
            height = math.floor(height / 2) * 2

        if corner_radius > width / 2 or corner_radius > height / 2:
            corner_radius = min(width / 2, height / 2)

        border_spacing = round(border_spacing)

        self._shape_type = "scrollbar"
        self._params.update({
            "width": width,
            "height": height,
            "corner_radius": corner_radius,
            "border_spacing": border_spacing,
            "start_value": start_value,
            "end_value": end_value,
            "orientation": orientation,
        })

        self.render()
        return True

    def draw_checkmark(
        self,
        width: Union[float, int],
        height: Union[float, int],
        size: Union[int, float],
    ) -> bool:
        self._params["checkmark_w"] = width
        self._params["checkmark_h"] = height
        self._params["checkmark_size"] = round(size)
        self._params["checkmark_active"] = True

        self.render()
        return True

    def draw_dropdown_arrow(
        self,
        x_position: Union[int, float],
        y_position: Union[int, float],
        size: Union[int, float],
    ) -> bool:
        self._params["arrow_x"] = round(x_position)
        self._params["arrow_y"] = round(y_position)
        self._params["arrow_size"] = round(size)
        self._params["dropdown_arrow_active"] = True

        self.render()
        return True

    def delete_part(self, tag: str) -> None:
        """Handle deletion of a specific vector tag (e.g. checkmark or border)."""
        if tag == "checkmark":
            self._params["checkmark_active"] = False
        elif tag in ("dropdown_arrow", "dropdown_arrow_parts"):
            self._params["dropdown_arrow_active"] = False
        elif tag in ("border_parts", "border_line_1", "border_rectangle_1"):
            self._params["border_width"] = 0
            self._params["border_spacing"] = 0
        elif tag in ("background_parts", "background_corner_top_left", "background_corner_top_right", "background_corner_bottom_right", "background_corner_bottom_left"):
            self._params["background_corners_active"] = False
        self.render()

    def render(self) -> None:
        """Rasterize the full vector state into the backing Blend2D surface and blit to PhotoImage."""
        w = int(self._params.get("width", self._params.get("bg_w", self._canvas.winfo_reqwidth() or 10)))
        h = int(self._params.get("height", self._params.get("bg_h", self._canvas.winfo_reqheight() or 10)))

        if w <= 0 or h <= 0:
            return

        surface = self._ensure_surface(w, h)
        bg = self._resolve_bg_color()

        # Fill base background cleanly with resolved parent color
        # This completely eliminates dark alpha halos & black fringe artifacts
        surface.fill_rect(0, 0, w, h, bg)

        # 1. Background Corners (if quadrant corner colors differ)
        if self._params.get("background_corners_active"):
            bg_w = self._params.get("bg_w", w)
            bg_h = self._params.get("bg_h", h)
            mid_w, mid_h = round(bg_w / 2), round(bg_h / 2)

            tl = self._colors.get("background_corner_top_left") or bg
            tr = self._colors.get("background_corner_top_right") or bg
            br = self._colors.get("background_corner_bottom_right") or bg
            bl = self._colors.get("background_corner_bottom_left") or bg

            if tl and tl != "transparent":
                surface.fill_rect(0, 0, mid_w, mid_h, tl)
            if tr and tr != "transparent":
                surface.fill_rect(mid_w, 0, bg_w - mid_w, mid_h, tr)
            if br and br != "transparent":
                surface.fill_rect(mid_w, mid_h, bg_w - mid_w, bg_h - mid_h, br)
            if bl and bl != "transparent":
                surface.fill_rect(0, mid_h, mid_w, bg_h - mid_h, bl)

        # 2. Render based on active shape
        shape = self._shape_type
        if shape == "rounded_rect":
            self._render_rounded_rect(surface, w, h, bg)
        elif shape == "vertical_split":
            self._render_vertical_split(surface, w, h, bg)
        elif shape == "progress_bar":
            self._render_progress_bar(surface, w, h, bg)
        elif shape == "slider":
            self._render_slider(surface, w, h, bg)
        elif shape == "scrollbar":
            self._render_scrollbar(surface, w, h, bg)

        # 3. Checkmark overlay (if active)
        if self._params.get("checkmark_active"):
            self._render_checkmark(surface)

        # 4. Dropdown Arrow overlay (if active)
        if self._params.get("dropdown_arrow_active"):
            self._render_dropdown_arrow(surface)

        # 5. Zero-copy blit to Tk PhotoImage
        if self._photo is not None:
            surface.blit(self._photo)
            self._canvas.tag_lower("tkblend_surface")

    def _render_rounded_rect(self, surface: Surface, width: float, height: float, bg: str) -> None:
        r = float(self._params.get("corner_radius", 0))
        bw = float(self._params.get("border_width", 0))
        r = min(r, width / 2.0, height / 2.0)
        inner_color = self._colors.get("inner_parts")
        border_color = self._colors.get("border_parts")

        # Optional subtle drop shadow for enhanced Blend2D rendering
        if (self._enable_shadows or TkBlendDrawEngine.enable_shadows_globally) and inner_color and inner_color != "transparent":
            surface.draw_shadow(
                0, 1, width, height, r, r,
                blur_radius=self._shadow_blur,
                shadow_color=self._shadow_color
            )

        if bw > 0 and border_color and border_color != "transparent":
            # Outer border fill
            surface.fill_rounded_rect(0, 0, width, height, r, r, border_color)

            # Inner foreground fill
            effective_inner = inner_color if (inner_color and inner_color != "transparent") else bg
            inner_r = max(0.0, r - bw)
            inner_w = max(0.0, width - 2 * bw)
            inner_h = max(0.0, height - 2 * bw)
            if inner_w > 0 and inner_h > 0:
                surface.fill_rounded_rect(bw, bw, inner_w, inner_h, inner_r, inner_r, effective_inner)
        else:
            if inner_color and inner_color != "transparent":
                surface.fill_rounded_rect(0, 0, width, height, r, r, inner_color)

    def _render_vertical_split(self, surface: Surface, width: float, height: float, bg: str) -> None:
        r = float(self._params.get("corner_radius", 0))
        bw = float(self._params.get("border_width", 0))
        r = min(r, width / 2.0, height / 2.0)
        split_width = height  # Typical dropdown button width on right
        split_x = max(0.0, width - split_width)

        border_color = self._colors.get("border_parts")
        left_color = self._colors.get("inner_parts_left") or self._colors.get("inner_parts") or bg
        right_color = self._colors.get("inner_parts_right") or self._colors.get("inner_parts") or bg

        if left_color == "transparent":
            left_color = bg
        if right_color == "transparent":
            right_color = bg

        if bw > 0 and border_color and border_color != "transparent":
            surface.fill_rounded_rect(0, 0, width, height, r, r, border_color)
            inner_r = max(0.0, r - bw)
            inner_w = max(0.0, width - 2 * bw)
            inner_h = max(0.0, height - 2 * bw)

            # Left section with clip
            with surface.saved():
                surface.clip_rect(bw, bw, max(0.0, split_x - bw), inner_h)
                surface.fill_rounded_rect(bw, bw, inner_w, inner_h, inner_r, inner_r, left_color)

            # Right section with clip
            with surface.saved():
                surface.clip_rect(split_x, bw, max(0.0, width - bw - split_x), inner_h)
                surface.fill_rounded_rect(bw, bw, inner_w, inner_h, inner_r, inner_r, right_color)

            # Vertical separator line
            surface.draw_line(split_x, bw, split_x, height - bw, border_color, stroke_width=bw)
        else:
            # Left section
            with surface.saved():
                surface.clip_rect(0, 0, split_x, height)
                surface.fill_rounded_rect(0, 0, width, height, r, r, left_color)

            # Right section
            with surface.saved():
                surface.clip_rect(split_x, 0, max(0.0, width - split_x), height)
                surface.fill_rounded_rect(0, 0, width, height, r, r, right_color)

    def _render_progress_bar(self, surface: Surface, width: float, height: float, bg: str) -> None:
        r = float(self._params.get("corner_radius", 0))
        bw = float(self._params.get("border_width", 0))
        r = min(r, width / 2.0, height / 2.0)
        val1 = float(self._params.get("progress_value_1", 0.0))
        val2 = float(self._params.get("progress_value_2", 0.0))
        orientation = str(self._params.get("orientation", "w")).lower()

        track_color = self._colors.get("inner_parts") or bg
        border_color = self._colors.get("border_parts")
        prog_color = self._colors.get("progress_parts")

        if track_color == "transparent":
            track_color = bg

        # 1. Base track & border
        if bw > 0 and border_color and border_color != "transparent":
            surface.fill_rounded_rect(0, 0, width, height, r, r, border_color)
            inner_r = max(0.0, r - bw)
            inner_w = max(0.0, width - 2 * bw)
            inner_h = max(0.0, height - 2 * bw)
            if inner_w > 0 and inner_h > 0:
                surface.fill_rounded_rect(bw, bw, inner_w, inner_h, inner_r, inner_r, track_color)
        else:
            surface.fill_rounded_rect(0, 0, width, height, r, r, track_color)

        # 2. Progress fill (clipped to rounded track for crisp edges)
        min_val = min(val1, val2)
        max_val = max(val1, val2)
        if prog_color and prog_color != "transparent" and max_val > min_val:
            with surface.saved():
                surface.clip_rounded_rect(bw, bw, max(0.0, width - 2 * bw), max(0.0, height - 2 * bw), max(0.0, r - bw), max(0.0, r - bw))
                if orientation in ("w", "horizontal"):  # Left to right
                    px0 = bw + (width - 2 * bw) * min_val
                    px1 = bw + (width - 2 * bw) * max_val
                    surface.fill_rect(px0, bw, max(0.0, px1 - px0), height - 2 * bw, prog_color)
                elif orientation == "e":  # Right to left
                    px0 = bw + (width - 2 * bw) * (1.0 - max_val)
                    px1 = bw + (width - 2 * bw) * (1.0 - min_val)
                    surface.fill_rect(px0, bw, max(0.0, px1 - px0), height - 2 * bw, prog_color)
                elif orientation in ("s", "vertical"):  # Bottom to top
                    py0 = bw + (height - 2 * bw) * (1.0 - max_val)
                    py1 = bw + (height - 2 * bw) * (1.0 - min_val)
                    surface.fill_rect(bw, py0, width - 2 * bw, max(0.0, py1 - py0), prog_color)
                elif orientation == "n":  # Top to bottom
                    py0 = bw + (height - 2 * bw) * min_val
                    py1 = bw + (height - 2 * bw) * max_val
                    surface.fill_rect(bw, py0, width - 2 * bw, max(0.0, py1 - py0), prog_color)

    def _render_slider(self, surface: Surface, width: float, height: float, bg: str) -> None:
        # First draw the background track and progress
        self._render_progress_bar(surface, width, height, bg)

        r = float(self._params.get("corner_radius", 0))
        btn_len = float(self._params.get("button_length", 0))
        btn_r = float(self._params.get("button_corner_radius", 0))
        slider_val = float(self._params.get("slider_value", 0.0))
        slider_val = max(0.0, min(1.0, slider_val))
        orientation = str(self._params.get("orientation", "w")).lower()
        slider_color = self._colors.get("slider_parts")
        border_color = self._colors.get("border_parts")

        if slider_color and slider_color != "transparent":
            if orientation in ("w", "horizontal"):
                sx = r + (btn_len / 2.0) + (width - 2.0 * r - btn_len) * slider_val
                bx = sx - (btn_len / 2.0)
                by = 0.0
                bw = btn_len
                bh = height
            elif orientation in ("s", "vertical"):
                sy = r + (btn_len / 2.0) + (height - 2.0 * r - btn_len) * (1.0 - slider_val)
                bx = 0.0
                by = sy - (btn_len / 2.0)
                bw = width
                bh = btn_len
            else:
                return

            btn_r = min(btn_r, bw / 2.0, bh / 2.0)
            # Draw slider thumb with subtle shadow and border
            if self._enable_shadows or TkBlendDrawEngine.enable_shadows_globally:
                surface.draw_shadow(bx, by + 1.0, bw, bh, btn_r, btn_r, blur_radius=4.0, shadow_color="#00000040")
            surface.fill_rounded_rect(bx, by, bw, bh, btn_r, btn_r, slider_color)
            if border_color and border_color != "transparent":
                surface.stroke_rounded_rect(bx + 0.5, by + 0.5, max(0.0, bw - 1.0), max(0.0, bh - 1.0), btn_r, btn_r, border_color, stroke_width=1.0)

    def _render_scrollbar(self, surface: Surface, width: float, height: float, bg: str) -> None:
        r = float(self._params.get("corner_radius", 0))
        r = min(r, width / 2.0, height / 2.0)
        spacing = float(self._params.get("border_spacing", 0))
        s_val = float(self._params.get("start_value", 0.0))
        e_val = float(self._params.get("end_value", 1.0))
        orientation = str(self._params.get("orientation", "vertical")).lower()

        track_color = self._colors.get("border_parts") or self._colors.get("inner_parts") or bg
        thumb_color = self._colors.get("scrollbar_parts")

        if track_color == "transparent":
            track_color = bg

        # Track
        surface.fill_rounded_rect(0, 0, width, height, r, r, track_color)

        # Thumb
        if thumb_color and thumb_color != "transparent":
            thumb_r = max(0.0, r - spacing)
            if orientation == "vertical":
                y0 = r + (height - 2.0 * r) * s_val
                y1 = r + (height - 2.0 * r) * e_val
                thumb_h = max(4.0, y1 - y0)
                thumb_w = max(1.0, width - 2.0 * spacing)
                thumb_r = min(thumb_r, thumb_w / 2.0, thumb_h / 2.0)
                surface.fill_rounded_rect(spacing, y0, thumb_w, thumb_h, thumb_r, thumb_r, thumb_color)
            elif orientation == "horizontal":
                x0 = r + (width - 2.0 * r) * s_val
                x1 = r + (width - 2.0 * r) * e_val
                thumb_w = max(4.0, x1 - x0)
                thumb_h = max(1.0, height - 2.0 * spacing)
                thumb_r = min(thumb_r, thumb_w / 2.0, thumb_h / 2.0)
                surface.fill_rounded_rect(x0, spacing, thumb_w, thumb_h, thumb_r, thumb_r, thumb_color)

    def _render_checkmark(self, surface: Surface) -> None:
        chk_color = self._colors.get("checkmark")
        if not chk_color or chk_color == "transparent":
            return

        w = float(self._params.get("checkmark_w", self._params.get("width", 20)))
        h = float(self._params.get("checkmark_h", self._params.get("height", 20)))
        size = float(self._params.get("checkmark_size", min(w, h) * 0.7))

        cx = w / 2.0
        cy = h / 2.0
        r = size / 2.8

        stroke_w = max(1.8, min(w, h) / 8.0)
        p = Path()
        p.move_to(cx - r, cy + r / 6.0)
        p.line_to(cx - r / 4.0, cy + r * 0.8)
        p.line_to(cx + r, cy - r)

        surface.stroke_path(p, chk_color, stroke_width=stroke_w)

    def _render_dropdown_arrow(self, surface: Surface) -> None:
        arrow_color = self._colors.get("dropdown_arrow") or self._colors.get("dropdown_arrow_parts")
        if not arrow_color or arrow_color == "transparent":
            return

        ax = float(self._params.get("arrow_x", 0))
        ay = float(self._params.get("arrow_y", 0))
        size = float(self._params.get("arrow_size", 10))

        stroke_w = max(1.8, size / 4.5)
        p = Path()
        p.move_to(ax - size / 2.0, ay - size / 5.0)
        p.line_to(ax, ay + size / 5.0)
        p.line_to(ax + size / 2.0, ay - size / 5.0)

        surface.stroke_path(p, arrow_color, stroke_width=stroke_w)
