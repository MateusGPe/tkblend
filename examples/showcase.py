"""
tkblend Modern UI Showcase Application.
Demonstrates soft elevation shadows, linear/radial gradients, antialiased vector geometry,
interactive modern widgets, and real-time Tkinter vector canvas rendering.
"""

import math
import time
import tkinter as tk
from tkblend import (
    Surface,
    BlendCanvas,
    LinearGradient,
    RadialGradient,
    Path,
    ModernFrame,
    ModernCard,
    ModernButton,
    ModernProgressBar,
    ModernSlider,
    ModernSwitch,
)


class ShowcaseApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("tkblend Modern Vector UI Showcase")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)
        self.root.configure(bg="#11111b")

        self._start_time = time.perf_counter()
        self._fps_frames = 0
        self._fps_last_time = time.perf_counter()
        self._fps = 60.0

        # Main Layout: Sidebar & Content Area
        self.sidebar = tk.Frame(root, bg="#181825", width=300)
        self.sidebar.pack(side="left", fill="y", padx=12, pady=12)
        self.sidebar.pack_propagate(False)

        self.content = tk.Frame(root, bg="#11111b")
        self.content.pack(side="right", fill="both", expand=True, padx=12, pady=12)

        self._setup_sidebar()
        self._setup_content()

    def _setup_sidebar(self):
        # Header Card
        header_card = ModernCard(
            self.sidebar,
            title="",
            width=276,
            height=90,
            rx=16,
            ry=16,
            bg_color="#1e1e2e",
            border_color="#313244",
            border_width=1.0,
            elevation=10.0,
            parent_bg="#181825",
        )
        header_card.pack(fill="x", pady=(0, 16))

        # Title Label within card
        lbl_title = tk.Label(
            header_card,
            text="tkblend Engine",
            font=("DejaVu Sans", 16, "bold"),
            fg="#cdd6f4",
            bg="#1e1e2e",
        )
        lbl_title.pack(anchor="w", padx=16, pady=(16, 2))

        lbl_sub = tk.Label(
            header_card,
            text="Blend2D + Tk_PhotoPutBlock",
            font=("DejaVu Sans", 10),
            fg="#a6adc8",
            bg="#1e1e2e",
        )
        lbl_sub.pack(anchor="w", padx=16)

        # Controls Section
        ctrl_card = ModernCard(
            self.sidebar,
            title="",
            width=276,
            height=540,
            rx=16,
            ry=16,
            bg_color="#1e1e2e",
            border_color="#313244",
            border_width=1.0,
            elevation=10.0,
            parent_bg="#181825",
        )
        ctrl_card.pack(fill="both", expand=True)

        # Action Buttons
        lbl_actions = tk.Label(
            ctrl_card,
            text="Interactive Widgets",
            font=("DejaVu Sans", 12, "bold"),
            fg="#cdd6f4",
            bg="#1e1e2e",
        )
        lbl_actions.pack(anchor="w", padx=16, pady=(16, 12))

        self.btn_primary = ModernButton(
            ctrl_card,
            text="Primary Action",
            command=self._on_btn_click,
            width=244,
            height=42,
            rx=12,
            ry=12,
            bg_color="#89b4fa",
            hover_color="#b4befe",
            press_color="#74c7ec",
            text_color="#11111b",
            font_size=13.0,
            elevation=6.0,
            parent_bg="#1e1e2e",
        )
        self.btn_primary.pack(fill="x", padx=16, pady=6)

        self.btn_secondary = ModernButton(
            ctrl_card,
            text="Accent Action",
            command=self._on_accent_click,
            width=244,
            height=42,
            rx=12,
            ry=12,
            bg_color="#a6e3a1",
            hover_color="#94e2d5",
            press_color="#89dceb",
            text_color="#11111b",
            font_size=13.0,
            elevation=6.0,
            parent_bg="#1e1e2e",
        )
        self.btn_secondary.pack(fill="x", padx=16, pady=6)

        # Progress Section
        lbl_progress = tk.Label(
            ctrl_card,
            text="Vector Progress",
            font=("DejaVu Sans", 11, "bold"),
            fg="#cdd6f4",
            bg="#1e1e2e",
        )
        lbl_progress.pack(anchor="w", padx=16, pady=(16, 6))

        self.progress_bar = ModernProgressBar(
            ctrl_card,
            width=244,
            height=14,
            value=65.0,
            fill_color_start="#f38ba8",
            fill_color_end="#fab387",
            parent_bg="#1e1e2e",
        )
        self.progress_bar.pack(fill="x", padx=16, pady=4)

        # Slider Section
        lbl_slider = tk.Label(
            ctrl_card,
            text="Elevation & Radius Slider",
            font=("DejaVu Sans", 11, "bold"),
            fg="#cdd6f4",
            bg="#1e1e2e",
        )
        lbl_slider.pack(anchor="w", padx=16, pady=(16, 6))

        self.slider = ModernSlider(
            ctrl_card,
            width=244,
            height=28,
            min_val=5.0,
            max_val=40.0,
            value=20.0,
            on_change=self._on_slider_change,
            active_track_color="#cba6f7",
            knob_color="#f5e0dc",
            parent_bg="#1e1e2e",
        )
        self.slider.pack(fill="x", padx=16, pady=4)

        # Toggle Switch Section
        switch_frame = tk.Frame(ctrl_card, bg="#1e1e2e")
        switch_frame.pack(fill="x", padx=16, pady=(20, 8))

        lbl_switch = tk.Label(
            switch_frame,
            text="Animated Wave Mode",
            font=("DejaVu Sans", 11),
            fg="#cdd6f4",
            bg="#1e1e2e",
        )
        lbl_switch.pack(side="left")

        self.switch = ModernSwitch(
            switch_frame,
            width=54,
            height=28,
            is_on=True,
            on_toggle=self._on_switch_toggle,
            on_color="#a6e3a1",
            off_color="#45475a",
            parent_bg="#1e1e2e",
        )
        self.switch.pack(side="right")

    def _setup_content(self):
        # BlendCanvas for live real-time interactive vector drawing
        self.canvas = BlendCanvas(
            self.content,
            width=760,
            height=680,
            bg="#11111b",
            on_draw=self._draw_scene,
        )
        self.canvas.pack(fill="both", expand=True)

        self._anim_radius = 20.0
        self._wave_active = True
        self._tick_anim()

    def _on_btn_click(self):
        self.progress_bar.value = (self.progress_bar.value + 15.0) % 100.0

    def _on_accent_click(self):
        self.progress_bar.value = 0.0

    def _on_slider_change(self, val: float):
        self._anim_radius = val

    def _on_switch_toggle(self, state: bool):
        self._wave_active = state

    def _draw_scene(self, surf: Surface):
        w, h = surf.width, surf.height
        t = time.perf_counter() - self._start_time

        # FPS calculation
        self._fps_frames += 1
        now = time.perf_counter()
        if now - self._fps_last_time >= 0.5:
            self._fps = self._fps_frames / (now - self._fps_last_time)
            self._fps_frames = 0
            self._fps_last_time = now

        # 1. Background Soft Radial Glow
        surf.clear("#11111b")
        glow_cx = w * 0.5 + math.cos(t * 0.8) * 150.0
        glow_cy = h * 0.4 + math.sin(t * 0.6) * 100.0
        glow_grad = RadialGradient(glow_cx, glow_cy, 0, glow_cx, glow_cy, max(w, h) * 0.7)
        glow_grad.add_stop(0.0, "#1e1e2e")
        glow_grad.add_stop(0.6, "#181825")
        glow_grad.add_stop(1.0, "#11111b")
        surf.fill_rect(0, 0, w, h, glow_grad)

        # 2. Dynamic Fluid Waves
        if self._wave_active:
            for layer, col in enumerate(["#89b4fa33", "#cba6f744", "#f38ba855"]):
                p = Path()
                p.move_to(0, h)
                p.line_to(0, h * 0.65)
                steps = 16
                for i in range(steps + 1):
                    x = (w / steps) * i
                    phase = t * 2.0 + layer * 1.5 + (i * 0.4)
                    y = h * (0.65 + layer * 0.06) + math.sin(phase) * 35.0
                    p.line_to(x, y)
                p.line_to(w, h)
                p.close()
                surf.fill_path(p, col)

        # 3. Interactive Floating Glassmorphic Cards
        card_w, card_h = 220, 140
        card1_x = 40.0
        card1_y = 60.0 + math.sin(t * 1.2) * 12.0

        # Gradient Card 1
        card1_grad = LinearGradient(card1_x, card1_y, card1_x + card_w, card1_y + card_h)
        card1_grad.add_stop(0.0, "#313244dd")
        card1_grad.add_stop(1.0, "#1e1e2edd")

        surf.draw_shadow(
            card1_x, card1_y, card_w, card_h,
            self._anim_radius, self._anim_radius,
            blur_radius=self._anim_radius * 1.2,
            shadow_color="#00000088",
            offset_y=8.0
        )
        surf.fill_rounded_rect(card1_x, card1_y, card_w, card_h, self._anim_radius, self._anim_radius, card1_grad)
        surf.stroke_rounded_rect(card1_x, card1_y, card_w, card_h, self._anim_radius, self._anim_radius, "#89b4fa66", 1.5)

        surf.draw_text("Vector Card Alpha", card1_x + 20, card1_y + 36, font_size=15, color="#cdd6f4")
        surf.draw_text("Anti-aliased subpixel text", card1_x + 20, card1_y + 64, font_size=12, color="#a6adc8")
        surf.fill_circle(card1_x + 180, card1_y + 105, 14, "#a6e3a1")

        # Card 2 (Radial Gradient Accent)
        card2_x = 300.0
        card2_y = 100.0 + math.cos(t * 1.4) * 12.0
        surf.draw_card(
            card2_x, card2_y, card_w, card_h,
            rx=self._anim_radius, ry=self._anim_radius,
            bg_color="#181825ee",
            border_color="#cba6f788",
            border_width=1.5,
            shadow_blur=self._anim_radius * 1.2,
            shadow_color="#00000088",
            shadow_offset_y=8.0
        )
        surf.draw_text("Zero-Copy Blit", card2_x + 20, card2_y + 36, font_size=15, color="#cdd6f4")
        surf.draw_text("Direct Tk_PhotoPutBlock", card2_x + 20, card2_y + 64, font_size=12, color="#a6adc8")
        surf.fill_rounded_rect(card2_x + 20, card2_y + 90, 120, 10, 5, 5, "#cba6f7")

        # 4. HUD / Status Overlay
        surf.draw_card(
            w - 180, 20, 160, 48, 12, 12,
            bg_color="#181825cc",
            border_color="#ffffff22",
            border_width=1.0,
            shadow_blur=8.0,
            shadow_color="#00000044"
        )
        surf.draw_text(f"{self._fps:.1f} FPS", w - 100, 50, font_size=16, color="#a6e3a1", align="center")

    def _tick_anim(self):
        self.canvas.redraw()
        self.root.after(16, self._tick_anim)  # ~60 FPS target


def main():
    root = tk.Tk()
    app = ShowcaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
