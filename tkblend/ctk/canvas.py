"""
TkBlendCanvas - Blend2D-backed Canvas for CustomTkinter widgets.
Intercepts CustomTkinter draw commands and tags, routing them seamlessly to Blend2D rasterization.
"""

from __future__ import annotations
import tkinter as tk
from typing import Union, Tuple, List, Any, Optional

VECTOR_TAGS = {
    "inner_parts",
    "inner_line_1",
    "inner_rectangle_1",
    "inner_rectangle_2",
    "border_parts",
    "border_line_1",
    "border_rectangle_1",
    "border_rectangle_2",
    "progress_parts",
    "progress_line_1",
    "slider_parts",
    "slider_line_1",
    "scrollbar_parts",
    "scrollbar_polygon_1",
    "checkmark",
    "dropdown_arrow",
    "dropdown_arrow_parts",
    "inner_parts_left",
    "inner_parts_right",
    "background_parts",
    "background_corner_top_left",
    "background_corner_top_right",
    "background_corner_bottom_right",
    "background_corner_bottom_left",
    "border_corner_part",
    "inner_corner_part",
    "slider_corner_part",
    "scrollbar_corner_part",
    "border_oval_1_a", "border_oval_1_b",
    "border_oval_2_a", "border_oval_2_b",
    "border_oval_3_a", "border_oval_3_b",
    "border_oval_4_a", "border_oval_4_b",
    "inner_oval_1_a", "inner_oval_1_b",
    "inner_oval_2_a", "inner_oval_2_b",
    "inner_oval_3_a", "inner_oval_3_b",
    "inner_oval_4_a", "inner_oval_4_b",
    "slider_oval_1_a", "slider_oval_1_b",
    "slider_oval_2_a", "slider_oval_2_b",
    "slider_oval_3_a", "slider_oval_3_b",
    "slider_oval_4_a", "slider_oval_4_b",
    "scrollbar_oval_1_a", "scrollbar_oval_1_b",
    "scrollbar_oval_2_a", "scrollbar_oval_2_b",
    "scrollbar_oval_3_a", "scrollbar_oval_3_b",
    "scrollbar_oval_4_a", "scrollbar_oval_4_b",
    "ctk_aa_circle_font_element",
}


class TkBlendCanvas(tk.Canvas):
    """
    Tkinter Canvas subclass designed for CustomTkinter integration.
    Renders background shapes via Blend2D Vector Surface while seamlessly supporting
    Tkinter text labels, image icons, and window items overlaid on top.
    """

    radius_to_char_fine = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._blend_engine = None
        self._aa_circle_canvas_ids = set()

    @classmethod
    def init_font_character_mapping(cls):
        """No-op compatibility hook for CTk's font character mapping."""
        pass

    def create_aa_circle(
        self,
        x_pos: int,
        y_pos: int,
        radius: int,
        angle: int = 0,
        fill: str = "white",
        tags: Union[str, Tuple[str, ...]] = "",
        anchor: str = tk.CENTER,
    ) -> int:
        """Compatibility method: Blend2D renders crisp circles directly in the draw engine."""
        return 0

    def configure(self, cnf=None, **kwargs):
        res = super().configure(cnf, **kwargs)
        if hasattr(self, "_blend_engine") and self._blend_engine is not None:
            bg = kwargs.get("bg") or kwargs.get("background")
            if bg is not None:
                self._blend_engine.set_canvas_bg(bg)
                self._blend_engine.render()
        return res

    def config(self, cnf=None, **kwargs):
        return self.configure(cnf, **kwargs)

    def itemcget(self, tag_or_id: Any, option: str) -> Any:
        if isinstance(tag_or_id, str) and tag_or_id in VECTOR_TAGS:
            if hasattr(self, "_blend_engine") and self._blend_engine is not None:
                if option in ("fill", "outline"):
                    return self._blend_engine.get_color(tag_or_id) or ""
        return super().itemcget(tag_or_id, option)

    def itemconfig(self, tag_or_id: Any, **kwargs) -> Optional[dict]:
        if isinstance(tag_or_id, str) and tag_or_id in VECTOR_TAGS:
            if hasattr(self, "_blend_engine") and self._blend_engine is not None:
                color = kwargs.get("fill") or kwargs.get("outline")
                if color is not None:
                    self._blend_engine.set_color(tag_or_id, color)
                    self._blend_engine.render()
            return None

        return super().itemconfig(tag_or_id, **kwargs)

    def itemconfigure(self, tag_or_id: Any, **kwargs) -> Optional[dict]:
        return self.itemconfig(tag_or_id, **kwargs)

    def coords(self, tag_or_id: Any, *args) -> List[float]:
        if isinstance(tag_or_id, str) and tag_or_id in VECTOR_TAGS:
            if len(args) == 0:
                w = float(self.winfo_width() or self.winfo_reqwidth() or 0)
                h = float(self.winfo_height() or self.winfo_reqheight() or 0)
                return [0.0, 0.0, w, h]
            return []

        return super().coords(tag_or_id, *args)

    def find_withtag(self, tag_or_id: Any) -> Tuple[int, ...]:
        if isinstance(tag_or_id, str) and tag_or_id in VECTOR_TAGS:
            if hasattr(self, "_blend_engine") and self._blend_engine is not None:
                if self._blend_engine.is_tag_active(tag_or_id):
                    img_id = getattr(self._blend_engine, "_image_id", None)
                    return (img_id if img_id is not None else 1,)
                return ()
            return (1,)

        return super().find_withtag(tag_or_id)

    def delete(self, *tags_or_ids: Any) -> None:
        has_vector_delete = False
        for item in tags_or_ids:
            if isinstance(item, str) and item in VECTOR_TAGS:
                if hasattr(self, "_blend_engine") and self._blend_engine is not None:
                    self._blend_engine.delete_part(item)
                    has_vector_delete = True
            else:
                super().delete(item)

    def tag_lower(self, *args) -> None:
        super().tag_lower(*args)
        # Keep Blend2D backing image at the very bottom
        if hasattr(self, "_blend_engine") and self._blend_engine is not None:
            img_id = getattr(self._blend_engine, "_image_id", None)
            if img_id is not None and self.find_withtag("tkblend_surface"):
                super().tag_lower("tkblend_surface")

    def tag_raise(self, *args) -> None:
        super().tag_raise(*args)
        # Keep Blend2D backing image at the very bottom
        if hasattr(self, "_blend_engine") and self._blend_engine is not None:
            img_id = getattr(self._blend_engine, "_image_id", None)
            if img_id is not None and self.find_withtag("tkblend_surface"):
                super().tag_lower("tkblend_surface")
