"""
Container widgets for tkblend: ModernFrame, ModernCard, ModernAccordion, ModernScrollableFrame.
"""

from __future__ import annotations
import tkinter as tk
from typing import Optional, Callable, List, Tuple, Any

from tkblend.surface import Surface, ColorLike, Path
from tkblend.widgets.base import _resolve_parent_bg
from tkblend.widgets.theme import Theme, ThemeManager


class ModernFrame(tk.Frame):
    """
    Modern container with dynamic corner radius, customizable border,
    and elevation / soft drop shadow. Allows nesting standard Tk child widgets.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 200,
        height: int = 150,
        rx: Optional[float] = None,
        ry: Optional[float] = None,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: Optional[float] = None,
        elevation: Optional[float] = None,
        shadow_color: Optional[ColorLike] = None,
        shadow_offset_y: float = 4.0,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._theme = t
        self._custom_rx = rx
        self._custom_ry = ry
        self._custom_bg_color = bg_color
        self._custom_border_color = border_color
        self._custom_border_width = border_width
        self._custom_elevation = elevation
        self._custom_shadow_color = shadow_color
        self._shadow_offset_y = shadow_offset_y
        self._custom_parent_bg = parent_bg
        self._parent_bg = _resolve_parent_bg(master, self._custom_parent_bg, self._theme)

        super().__init__(
            master,
            width=width,
            height=height,
            background=self._parent_bg,
            borderwidth=0,
            highlightthickness=0,
            **kwargs,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._widget_w = max(1, width)
        self._widget_h = max(1, height)

        # Background Label with Blend2D PhotoImage
        self._photo = tk.PhotoImage(master=self, width=self._widget_w, height=self._widget_h)
        self._surface = Surface(self._widget_w, self._widget_h)

        self._bg_label = tk.Label(
            self,
            image=self._photo,
            borderwidth=0,
            highlightthickness=0,
            background=self._parent_bg,
        )
        self._bg_label.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._bg_label.lower()

        # Dedicated inner content container
        elev = self._custom_elevation if self._custom_elevation is not None else self._theme.elevation_md
        pad = int(max(4.0, elev * 0.8) + 4)
        self.content = tk.Frame(
            self,
            background=str(self._bg_color),
            borderwidth=0,
            highlightthickness=0,
        )
        self.content.place(x=pad, y=pad, relwidth=1.0, relheight=1.0, width=-(pad * 2), height=-(pad * 2))

        self.bind("<Configure>", self._on_configure)

        ThemeManager.subscribe(self._on_theme_changed)
        self.bind("<Destroy>", lambda e: ThemeManager.unsubscribe(self._on_theme_changed))

        self.after_idle(self.render)

    @property
    def _bg_color(self) -> ColorLike:
        if self._custom_bg_color is not None:
            return self._custom_bg_color
        return self._theme.bg_surface

    @property
    def surface(self) -> Surface:
        return self._surface

    def _on_theme_changed(self, new_theme: Theme) -> None:
        if self.winfo_exists():
            self._theme = new_theme
            self._parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, new_theme)
            try:
                self.configure(background=self._parent_bg)
                self._bg_label.configure(background=self._parent_bg)
                self.content.configure(background=str(self._bg_color))
            except Exception:
                pass
            self.render()

    def _on_configure(self, event) -> None:
        new_w = max(1, event.width)
        new_h = max(1, event.height)
        if new_w != self._widget_w or new_h != self._widget_h:
            self._widget_w = new_w
            self._widget_h = new_h
            self._photo.configure(width=self._widget_w, height=self._widget_h)
            self._surface.resize(self._widget_w, self._widget_h)
            self.render()

    def set_background(self, bg_color: ColorLike) -> None:
        self._custom_bg_color = bg_color
        try:
            self.content.configure(background=str(self._bg_color))
        except Exception:
            pass
        self.render()

    def render(self) -> None:
        self._surface.clear(self._parent_bg)

        t = self._theme
        rx = self._custom_rx if self._custom_rx is not None else t.radius_lg
        ry = self._custom_ry if self._custom_ry is not None else rx
        bg_col = self._bg_color
        border_col = self._custom_border_color if self._custom_border_color is not None else t.border
        border_w = self._custom_border_width if self._custom_border_width is not None else t.border_width
        elevation = self._custom_elevation if self._custom_elevation is not None else t.elevation_md
        shadow_col = self._custom_shadow_color if self._custom_shadow_color is not None else t.shadow_color

        pad = max(4.0, elevation * 0.8)
        draw_x = pad
        draw_y = pad
        draw_w = max(1.0, self._widget_w - pad * 2.0)
        draw_h = max(1.0, self._widget_h - pad * 2.0)

        self._surface.draw_card(
            x=draw_x,
            y=draw_y,
            w=draw_w,
            h=draw_h,
            rx=rx,
            ry=ry,
            bg_color=bg_col,
            border_color=border_col,
            border_width=border_w,
            shadow_blur=elevation * 1.5,
            shadow_spread=0.0,
            shadow_offset_x=0.0,
            shadow_offset_y=self._shadow_offset_y,
            shadow_color=shadow_col if elevation > 0 else "#00000000",
        )
        self._surface.blit(self._photo)


class ModernCard(ModernFrame):
    """
    High-fidelity Card container with elevation drop shadow and optional title / subtitle.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        title: str = "",
        subtitle: str = "",
        width: int = 280,
        height: int = 180,
        rx: Optional[float] = None,
        ry: Optional[float] = None,
        bg_color: Optional[ColorLike] = None,
        border_color: Optional[ColorLike] = None,
        border_width: Optional[float] = None,
        elevation: Optional[float] = None,
        shadow_color: Optional[ColorLike] = None,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        self._title = title
        self._subtitle = subtitle
        t = theme or ThemeManager.get_theme()
        super().__init__(
            master=master,
            width=width,
            height=height,
            rx=rx if rx is not None else t.radius_lg,
            ry=ry if ry is not None else rx or t.radius_lg,
            bg_color=bg_color,
            border_color=border_color,
            border_width=border_width,
            elevation=elevation if elevation is not None else t.elevation_lg,
            shadow_color=shadow_color,
            parent_bg=parent_bg,
            theme=theme,
            **kwargs,
        )

        # Reposition content frame below title and subtitle
        elev = self._custom_elevation if self._custom_elevation is not None else self._theme.elevation_lg
        pad = int(max(4.0, elev * 0.8))
        header_h = 44 if (self._title and self._subtitle) else 32 if self._title else 4
        self.content.place_configure(
            x=pad + 12,
            y=pad + header_h,
            relwidth=1.0,
            relheight=1.0,
            width=-((pad + 12) * 2),
            height=-(pad + header_h + 12),
        )

    @property
    def _bg_color(self) -> ColorLike:
        if self._custom_bg_color is not None:
            return self._custom_bg_color
        return self._theme.bg_card

    def render(self) -> None:
        super().render()
        t = self._theme
        elevation = self._custom_elevation if self._custom_elevation is not None else t.elevation_lg
        pad = max(4.0, elevation * 0.8)
        start_y = pad + 24.0

        if self._title:
            self._surface.draw_text(
                self._title,
                x=pad + 16.0,
                y=start_y,
                font_size=t.font_size_lg,
                font_family=t.font_family,
                color=t.text,
            )
            start_y += 18.0

        if self._subtitle:
            self._surface.draw_text(
                self._subtitle,
                x=pad + 16.0,
                y=start_y,
                font_size=t.font_size_xs,
                font_family=t.font_family,
                color=t.text_muted,
            )

        if self._title or self._subtitle:
            self._surface.blit(self._photo)


class ModernAccordionItem(tk.Frame):
    """
    Individual expandable item in a ModernAccordion.
    """

    def __init__(
        self,
        master: tk.Misc,
        title: str = "Section",
        is_expanded: bool = False,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._theme = t
        self._title = title
        self._is_expanded = is_expanded
        self._header_h = 42

        super().__init__(master, bg=t.bg_surface, **kwargs)

        # Header bar
        self._header = tk.Frame(self, height=self._header_h, bg=t.bg_surface)
        self._header.pack(fill=tk.X, side=tk.TOP)
        self._header.pack_propagate(False)

        self._title_lbl = tk.Label(
            self._header,
            text=self._title,
            font=(t.font_family, int(t.font_size_md)),
            fg=t.text,
            bg=t.bg_surface,
            padx=12,
        )
        self._title_lbl.pack(side=tk.LEFT, fill=tk.Y)

        self._icon_lbl = tk.Label(
            self._header,
            text="▼" if self._is_expanded else "▶",
            font=(t.font_family, 10),
            fg=t.text_muted,
            bg=t.bg_surface,
            padx=12,
        )
        self._icon_lbl.pack(side=tk.RIGHT, fill=tk.Y)

        # Content container
        self.content_frame = tk.Frame(self, bg=t.bg_surface_alt, padx=12, pady=10)

        self._header.bind("<Button-1>", lambda e: self.toggle())
        self._title_lbl.bind("<Button-1>", lambda e: self.toggle())
        self._icon_lbl.bind("<Button-1>", lambda e: self.toggle())

        if self._is_expanded:
            self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

    def _on_theme_changed(self, new_theme: Theme) -> None:
        if self.winfo_exists():
            self._theme = new_theme
            self.configure(bg=new_theme.bg_surface)
            self._header.configure(bg=new_theme.bg_surface)
            self._title_lbl.configure(
                font=(new_theme.font_family, int(new_theme.font_size_md)),
                fg=new_theme.text,
                bg=new_theme.bg_surface,
            )
            self._icon_lbl.configure(
                font=(new_theme.font_family, 10),
                fg=new_theme.text_muted,
                bg=new_theme.bg_surface,
            )
            self.content_frame.configure(bg=new_theme.bg_surface_alt)

    def toggle(self) -> None:
        self._is_expanded = not self._is_expanded
        self._icon_lbl.configure(text="▼" if self._is_expanded else "▶")
        if self._is_expanded:
            self.content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        else:
            self.content_frame.pack_forget()


class ModernAccordion(tk.Frame):
    """
    Modern container managing multiple collapsible Accordion sections.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._theme = t
        super().__init__(master, bg=t.bg_surface, **kwargs)
        self._items: List[ModernAccordionItem] = []

        ThemeManager.subscribe(self._on_theme_changed)
        self.bind("<Destroy>", lambda e: ThemeManager.unsubscribe(self._on_theme_changed))

    def _on_theme_changed(self, new_theme: Theme) -> None:
        if self.winfo_exists():
            self._theme = new_theme
            self.configure(bg=new_theme.bg_surface)
            for item in self._items:
                item._on_theme_changed(new_theme)

    def add_section(self, title: str, is_expanded: bool = False) -> tk.Frame:
        item = ModernAccordionItem(self, title=title, is_expanded=is_expanded, theme=self._theme)
        item.pack(fill=tk.X, padx=4, pady=4)
        self._items.append(item)
        return item.content_frame


class ModernScrollableFrame(tk.Frame):
    """
    Scrollable frame container supporting mousewheel and custom modern styling.
    """

    def __init__(
        self,
        master: Optional[tk.Misc] = None,
        width: int = 300,
        height: int = 200,
        parent_bg: Optional[str] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        t = theme or ThemeManager.get_theme()
        self._theme = t
        self._custom_parent_bg = parent_bg
        self._parent_bg = _resolve_parent_bg(master, self._custom_parent_bg, self._theme)

        super().__init__(master, width=width, height=height, bg=self._parent_bg, **kwargs)

        self._canvas = tk.Canvas(
            self,
            bg=self._parent_bg,
            borderwidth=0,
            highlightthickness=0,
        )
        self._scrollbar = tk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.scrollable_content = tk.Frame(self._canvas, bg=self._parent_bg)

        self.scrollable_content.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )

        self._window_id = self._canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")

        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(self._window_id, width=e.width),
        )

        ThemeManager.subscribe(self._on_theme_changed)
        self.bind("<Destroy>", lambda e: ThemeManager.unsubscribe(self._on_theme_changed))

        # Mouse wheel binding
        self.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.bind("<Leave>", lambda e: self._unbind_mousewheel())

    def _on_theme_changed(self, new_theme: Theme) -> None:
        if self.winfo_exists():
            self._theme = new_theme
            self._parent_bg = _resolve_parent_bg(self.master, self._custom_parent_bg, new_theme)
            self.configure(bg=self._parent_bg)
            self._canvas.configure(bg=self._parent_bg)
            self.scrollable_content.configure(bg=self._parent_bg)
            try:
                self._scrollbar.configure(
                    bg=new_theme.scrollbar_thumb,
                    troughcolor=new_theme.scrollbar_track,
                    activebackground=new_theme.scrollbar_thumb_hover,
                )
            except Exception:
                pass

    def _on_mousewheel(self, event):
        if event.num == 5 or event.delta == -120:
            self._canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:
            self._canvas.yview_scroll(-1, "units")

    def _bind_mousewheel(self):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")
