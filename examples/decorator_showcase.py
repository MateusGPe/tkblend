"""
Interactive Showcase: Native Surface Decorator (BlendDecorator)
Demonstrates pure Blend2D double-buffered rounded cards, soft drop shadows,
focus rings, and passive state monitoring around standard Tk/TTK child widgets.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Tuple

import tkblend as tb
from tkblend import BlendDecorator


class DecoratorShowcase(tk.Frame):
    """Interactive gallery and live playground for BlendDecorator."""

    def __init__(self, master: Optional[tk.Misc] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill="both", expand=True)

        self._current_radius = 12.0
        self._current_border_w = 1.5
        self._current_blur = 10.0
        self._current_spread = 0.0
        self._current_offset_y = 3.0
        self._current_focus_ring_w = 2.5
        self._current_focus_ring_offset = 2.0
        self._shadows_enabled = True

        self._is_simulated_hover = False
        self._is_simulated_focus = False
        self._is_error_state = False

        # Registry for dynamic theme tracking
        self._bg_frames: List[tk.Frame] = []
        self._card_frames: List[tk.Widget] = []
        self._primary_labels: List[tk.Label] = []
        self._muted_labels: List[tk.Label] = []
        self._entries: List[tk.Widget] = []
        self._decorators: List[BlendDecorator] = []
        self._slider_controls: List[dict] = []

        self._build_ui()

    def _build_ui(self):
        pal = tb.get_theme()
        self.configure(bg=pal.bg)
        self._bg_frames.append(self)

        # ----------------------------------------------------------------------
        # Header bar
        # ----------------------------------------------------------------------
        self.header = tk.Frame(self, bg=pal.bg)
        self.header.pack(fill="x", padx=20, pady=(12, 6))
        self._bg_frames.append(self.header)

        title_lbl = tk.Label(
            self.header,
            text="BlendDecorator Surface Showcase",
            font=("Segoe UI", 16, "bold"),
            fg=pal.fg,
            bg=pal.bg,
        )
        title_lbl.pack(side="left")
        self._primary_labels.append(title_lbl)

        # Theme selector buttons
        self.theme_bar = tk.Frame(self.header, bg=pal.bg)
        self.theme_bar.pack(side="right")
        self._bg_frames.append(self.theme_bar)

        theme_lbl = tk.Label(self.theme_bar, text="Theme:", font=("Segoe UI", 10), fg=pal.text_muted, bg=pal.bg)
        theme_lbl.pack(side="left", padx=(0, 6))
        self._muted_labels.append(theme_lbl)

        for theme_name in ("dark", "light", "tokyo-night", "dracula", "nord"):
            btn = tk.Button(
                self.theme_bar,
                text=theme_name.capitalize(),
                font=("Segoe UI", 9),
                bg=pal.card_bg,
                fg=pal.fg,
                activebackground=pal.primary,
                activeforeground="#ffffff",
                relief="flat",
                padx=6,
                pady=2,
                command=lambda t=theme_name: self._on_change_theme(t),
            )
            btn.pack(side="left", padx=2)
            self._card_frames.append(btn)

        # ----------------------------------------------------------------------
        # Main content container (2 columns: Practical Demos & Live Studio)
        # ----------------------------------------------------------------------
        self.body = tk.Frame(self, bg=pal.bg)
        self.body.pack(fill="both", expand=True, padx=20, pady=(4, 12))
        self._bg_frames.append(self.body)

        self.body.columnconfigure(0, weight=1, uniform="col")
        self.body.columnconfigure(1, weight=1, uniform="col")
        self.body.rowconfigure(0, weight=1)

        # ======================================================================
        # Left Column: Practical UI Components & State Demos
        # ======================================================================
        self.left_col = BlendDecorator(self.body, radius=14, shadow_blur=10, bg_color=pal.card_bg)
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        self._decorators.append(self.left_col)

        self.left_inner = tk.Frame(self.left_col, bg=pal.card_bg)
        self.left_inner.pack(fill="both", expand=True, padx=16, pady=14)
        self._card_frames.append(self.left_inner)

        col1_title = tk.Label(
            self.left_inner,
            text="Practical Components & State Triggers",
            font=("Segoe UI", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        col1_title.pack(anchor="w", pady=(0, 8))
        self._primary_labels.append(col1_title)

        # 1. Pill Search Input with Action Button
        p1_lbl = tk.Label(self.left_inner, text="1. Pill Search Input with Action Button", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg)
        p1_lbl.pack(anchor="w", pady=(0, 3))
        self._primary_labels.append(p1_lbl)

        self.search_dec = BlendDecorator(
            self.left_inner,
            width=320,
            height=46,
            radius=20.0,
            border_width=1.2,
            shadow_blur=8.0,
            shadow_offset_y=2.0,
            focus_ring_width=2.5,
        )
        self.search_dec.pack(fill="x", pady=(0, 8))
        self._decorators.append(self.search_dec)

        search_box = tk.Frame(self.search_dec, bg=self.search_dec.bg_color)
        self.search_entry = tk.Entry(search_box, font=("Segoe UI", 10), bg=self.search_dec.bg_color, fg=pal.fg, relief="flat", bd=0, highlightthickness=0)
        self.search_entry.insert(0, "Search documents, commands, and assets...")
        self.search_entry.pack(side="left", fill="both", expand=True, padx=(8, 6))
        self._entries.append(self.search_entry)

        search_btn = tk.Button(
            search_box,
            text="Search",
            font=("Segoe UI", 9),
            bg=pal.primary,
            fg="#ffffff",
            relief="flat",
            padx=8,
            pady=2,
            command=lambda: self.search_entry.delete(0, tk.END),
        )
        search_btn.pack(side="right", padx=(0, 4))
        self.search_dec.decorate(search_box, padding=(4, 4, 4, 4))

        # 2. Credentials & Interactive Focus Hooking
        p2_lbl = tk.Label(self.left_inner, text="2. Floating Credentials (Passive Focus Hooking)", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg)
        p2_lbl.pack(anchor="w", pady=(0, 3))
        self._primary_labels.append(p2_lbl)

        self.user_dec = BlendDecorator(
            self.left_inner,
            width=320,
            height=38,
            radius=9.0,
            border_width=1.0,
            shadow_blur=6.0,
            shadow_offset_y=2.0,
        )
        self.user_dec.pack(fill="x", pady=(0, 6))
        self._decorators.append(self.user_dec)

        self.user_entry = tk.Entry(self.user_dec, font=("Segoe UI", 10), bg=self.user_dec.bg_color, fg=pal.fg, relief="flat", bd=0)
        self.user_entry.insert(0, "developer@antigravity.io")
        self.user_dec.decorate(self.user_entry, padding=(10, 4, 10, 4))
        self._entries.append(self.user_entry)

        self.pass_dec = BlendDecorator(
            self.left_inner,
            width=320,
            height=38,
            radius=9.0,
            border_width=1.0,
            shadow_blur=6.0,
            shadow_offset_y=2.0,
        )
        self.pass_dec.pack(fill="x", pady=(0, 6))
        self._decorators.append(self.pass_dec)

        self.pass_entry = tk.Entry(self.pass_dec, font=("Segoe UI", 10), show="•", bg=self.pass_dec.bg_color, fg=pal.fg, relief="flat", bd=0)
        self.pass_entry.insert(0, "SecretPassword123!")
        self.pass_dec.decorate(self.pass_entry, padding=(10, 4, 10, 4))
        self._entries.append(self.pass_entry)

        # Focus hook control bar
        focus_bar = tk.Frame(self.left_inner, bg=pal.card_bg)
        focus_bar.pack(fill="x", pady=(0, 8))
        self._card_frames.append(focus_bar)

        for text, cmd in [
            ("Focus User", self.user_entry.focus_set),
            ("Focus Password", self.pass_entry.focus_set),
            ("Unfocus All", self.focus_set),
        ]:
            b = tk.Button(focus_bar, text=text, font=("Segoe UI", 9), bg=pal.input_bg, fg=pal.fg, relief="flat", padx=6, pady=2, command=cmd)
            b.pack(side="left", padx=2)
            self._card_frames.append(b)

        # 3. Dynamic Validation & Error State Trigger
        p3_lbl = tk.Label(self.left_inner, text="3. Dynamic Validation / Error State", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg)
        p3_lbl.pack(anchor="w", pady=(0, 3))
        self._primary_labels.append(p3_lbl)

        val_row = tk.Frame(self.left_inner, bg=pal.card_bg)
        val_row.pack(fill="x", pady=(0, 6))
        self._card_frames.append(val_row)

        self.val_dec = BlendDecorator(
            val_row,
            width=230,
            height=38,
            radius=9.0,
            border_width=1.0,
            shadow_blur=6.0,
            shadow_offset_y=2.0,
        )
        self.val_dec.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._decorators.append(self.val_dec)

        self.val_entry = tk.Entry(self.val_dec, font=("Segoe UI", 10), bg=self.val_dec.bg_color, fg=pal.fg, relief="flat", bd=0)
        self.val_entry.insert(0, "BLND-8941-XJ92 (Valid)")
        self.val_dec.decorate(self.val_entry, padding=(10, 4, 10, 4))
        self._entries.append(self.val_entry)

        self._err_var = tk.BooleanVar(value=False)
        self.val_switch = ttk.Checkbutton(
            val_row,
            text="Simulate Error",
            variable=self._err_var,
            command=self._on_toggle_error_state,
        )
        self.val_switch.pack(side="right")

        # 4. Multiline Borderless Text Snippet
        p4_lbl = tk.Label(self.left_inner, text="4. Borderless Code / Note Decorator", font=("Segoe UI", 10, "bold"), fg=pal.fg, bg=pal.card_bg)
        p4_lbl.pack(anchor="w", pady=(0, 3))
        self._primary_labels.append(p4_lbl)

        self.text_dec = BlendDecorator(
            self.left_inner,
            width=320,
            height=80,
            radius=10.0,
            border_width=1.0,
            shadow_blur=8.0,
            shadow_offset_y=2.0,
        )
        self.text_dec.pack(fill="both", expand=True, pady=(0, 2))
        self._decorators.append(self.text_dec)

        self.text_widget = tk.Text(self.text_dec, font=("Consolas", 9), height=3, bg=self.text_dec.bg_color, fg=pal.fg, relief="flat", bd=0)
        self.text_widget.insert("1.0", "# Pure Blend2D Surface Decorator\nimport tkblend as tb\ndec = tb.BlendDecorator(root, radius=12)\ndec.decorate(entry)")
        self.text_dec.decorate(self.text_widget, padding=(10, 6, 10, 6))
        self._entries.append(self.text_widget)

        # ======================================================================
        # Right Column: Live Style Studio & Inset Inspector
        # ======================================================================
        self.right_col = BlendDecorator(self.body, radius=14, shadow_blur=10, bg_color=pal.card_bg)
        self.right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)
        self._decorators.append(self.right_col)

        self.right_inner = tk.Frame(self.right_col, bg=pal.card_bg)
        self.right_inner.pack(fill="both", expand=True, padx=16, pady=14)
        self._card_frames.append(self.right_inner)

        col2_title = tk.Label(
            self.right_inner,
            text="Live Style Studio & Inset Inspector",
            font=("Segoe UI", 13, "bold"),
            fg=pal.fg,
            bg=pal.card_bg,
        )
        col2_title.pack(anchor="w", pady=(0, 6))
        self._primary_labels.append(col2_title)

        # Target Live Preview Box
        self.preview_box = tk.Frame(self.right_inner, bg=pal.card_bg)
        self.preview_box.pack(fill="x", pady=(0, 4))
        self._card_frames.append(self.preview_box)

        self.live_dec = BlendDecorator(
            self.preview_box,
            width=340,
            height=68,
            radius=self._current_radius,
            border_width=self._current_border_w,
            shadow_blur=self._current_blur,
            shadow_spread=self._current_spread,
            shadow_offset_y=self._current_offset_y,
            focus_ring_width=self._current_focus_ring_w,
            focus_ring_offset=self._current_focus_ring_offset,
        )
        self.live_dec.pack(fill="x", padx=4, pady=2)
        self._decorators.append(self.live_dec)

        self.live_entry = tk.Entry(self.live_dec, font=("Segoe UI", 11, "bold"), bg=self.live_dec.bg_color, fg=pal.fg, relief="flat", bd=0)
        self.live_entry.insert(0, "Live Decorated Entry Box")
        self.live_dec.decorate(self.live_entry, padding=(12, 4, 12, 4))
        self._entries.append(self.live_entry)

        # Simulation state buttons
        sim_bar = tk.Frame(self.right_inner, bg=pal.card_bg)
        sim_bar.pack(fill="x", pady=(0, 6))
        self._card_frames.append(sim_bar)

        sim_lbl = tk.Label(sim_bar, text="Preview State:", font=("Segoe UI", 9), fg=pal.text_muted, bg=pal.card_bg)
        sim_lbl.pack(side="left", padx=(0, 6))
        self._muted_labels.append(sim_lbl)

        self.hover_btn = tk.Button(sim_bar, text="Hover", font=("Segoe UI", 9), bg=pal.input_bg, fg=pal.fg, relief="flat", padx=6, pady=2, command=self._toggle_sim_hover)
        self.hover_btn.pack(side="left", padx=2)
        self._card_frames.append(self.hover_btn)

        self.focus_btn = tk.Button(sim_bar, text="Focus", font=("Segoe UI", 9), bg=pal.input_bg, fg=pal.fg, relief="flat", padx=6, pady=2, command=self._toggle_sim_focus)
        self.focus_btn.pack(side="left", padx=2)
        self._card_frames.append(self.focus_btn)

        reset_btn = tk.Button(sim_bar, text="Reset", font=("Segoe UI", 9), bg=pal.input_bg, fg=pal.fg, relief="flat", padx=6, pady=2, command=self._reset_sim_states)
        reset_btn.pack(side="left", padx=2)
        self._card_frames.append(reset_btn)

        # Inset Readout
        insets = self.live_dec.insets
        self.insets_lbl = tk.Label(
            self.right_inner,
            text=f"Active Insets: L={insets[0]:.1f}px, T={insets[1]:.1f}px, R={insets[2]:.1f}px, B={insets[3]:.1f}px",
            font=("Segoe UI", 9),
            fg=pal.text_muted,
            bg=pal.card_bg,
        )
        self.insets_lbl.pack(anchor="w", pady=(0, 6))
        self._muted_labels.append(self.insets_lbl)

        # Style Presets Bar
        presets_box = tk.Frame(self.right_inner, bg=pal.card_bg)
        presets_box.pack(fill="x", pady=(0, 6))
        self._card_frames.append(presets_box)

        presets_lbl = tk.Label(presets_box, text="Quick Presets:", font=("Segoe UI", 9), fg=pal.text_muted, bg=pal.card_bg)
        presets_lbl.pack(side="left", padx=(0, 6))
        self._muted_labels.append(presets_lbl)

        presets = [
            ("Pill", 22.0, 1.5, 10.0, 3.0, 2.5),
            ("Subtle", 8.0, 1.0, 6.0, 2.0, 2.0),
            ("Neon Glow", 14.0, 2.0, 12.0, 0.0, 3.5),
            ("Flat", 6.0, 1.5, 0.0, 0.0, 2.0),
        ]
        for name, r, bw, blur, off_y, ring_w in presets:
            pb = tk.Button(
                presets_box,
                text=name,
                font=("Segoe UI", 8),
                bg=pal.input_bg,
                fg=pal.fg,
                relief="flat",
                padx=4,
                pady=1,
                command=lambda r=r, bw=bw, bl=blur, oy=off_y, rw=ring_w: self._apply_preset(r, bw, bl, oy, rw),
            )
            pb.pack(side="left", padx=2)
            self._card_frames.append(pb)

        # Sliders Controls
        self.controls = tk.Frame(self.right_inner, bg=pal.card_bg)
        self.controls.pack(fill="both", expand=True)
        self._card_frames.append(self.controls)

        self._slider_controls.clear()
        self.sl_radius = self._create_slider(self.controls, "Corner Radius", 0.0, 26.0, self._current_radius, self._on_radius_changed)
        self.sl_border = self._create_slider(self.controls, "Border Width", 0.0, 5.0, self._current_border_w, self._on_border_w_changed)
        self.sl_blur = self._create_slider(self.controls, "Shadow Blur", 0.0, 25.0, self._current_blur, self._on_blur_changed)
        self.sl_offset_y = self._create_slider(self.controls, "Shadow Offset Y", -5.0, 15.0, self._current_offset_y, self._on_offset_y_changed)
        self.sl_ring_w = self._create_slider(self.controls, "Focus Ring Width", 0.0, 6.0, self._current_focus_ring_w, self._on_focus_ring_w_changed)

        # Shadow toggle switch
        self.switch_row = tk.Frame(self.controls, bg=pal.card_bg)
        self.switch_row.pack(fill="x", pady=(4, 0))
        self._card_frames.append(self.switch_row)

        self._shadow_var = tk.BooleanVar(value=True)
        self.shadow_sw = ttk.Checkbutton(
            self.switch_row,
            text="Enable Soft Drop Shadow",
            variable=self._shadow_var,
            command=lambda: self._on_toggle_shadows(self._shadow_var.get()),
        )
        self.shadow_sw.pack(side="left")

    def _create_slider(self, parent, label_text, min_val, max_val, init_val, callback) -> dict:
        pal = tb.get_theme()
        row = tk.Frame(parent, bg=pal.card_bg)
        row.pack(fill="x", pady=1)
        self._card_frames.append(row)

        val_lbl = tk.Label(row, text=f"{label_text}: {init_val:.1f}px", font=("Segoe UI", 9), fg=pal.fg, bg=pal.card_bg)
        val_lbl.pack(anchor="w")
        self._primary_labels.append(val_lbl)

        def on_val(v_str):
            v = float(v_str)
            val_lbl.config(text=f"{label_text}: {v:.1f}px")
            callback(v)

        sl = ttk.Scale(
            row,
            from_=min_val,
            to=max_val,
            value=init_val,
            command=on_val,
        )
        sl.pack(fill="x", pady=(1, 2))

        ctrl = {
            "name": label_text,
            "row": row,
            "label": val_lbl,
            "slider": sl,
            "set_fn": lambda v: (val_lbl.config(text=f"{label_text}: {v:.1f}px"), sl.set(v)),
        }
        self._slider_controls.append(ctrl)
        return ctrl

    def _apply_preset(self, radius: float, border_w: float, blur: float, offset_y: float, ring_w: float):
        self._current_radius = radius
        self._current_border_w = border_w
        self._current_blur = blur
        self._current_offset_y = offset_y
        self._current_focus_ring_w = ring_w

        self.sl_radius["set_fn"](radius)
        self.sl_border["set_fn"](border_w)
        self.sl_blur["set_fn"](blur)
        self.sl_offset_y["set_fn"](offset_y)
        self.sl_ring_w["set_fn"](ring_w)

        self.live_dec.configure(
            radius=radius,
            border_width=border_w,
            shadow_blur=blur,
            shadow_offset_y=offset_y,
            focus_ring_width=ring_w,
        )
        self._update_insets_display()

    def _on_radius_changed(self, val: float):
        self._current_radius = val
        self.live_dec.configure(radius=val)
        self._update_insets_display()

    def _on_border_w_changed(self, val: float):
        self._current_border_w = val
        self.live_dec.configure(border_width=val)
        self._update_insets_display()

    def _on_blur_changed(self, val: float):
        self._current_blur = val
        self.live_dec.configure(shadow_blur=val)
        self._update_insets_display()

    def _on_offset_y_changed(self, val: float):
        self._current_offset_y = val
        self.live_dec.configure(shadow_offset_y=val)
        self._update_insets_display()

    def _on_focus_ring_w_changed(self, val: float):
        self._current_focus_ring_w = val
        self.live_dec.configure(focus_ring_width=val)
        self._update_insets_display()

    def _on_toggle_shadows(self, enabled: bool):
        self._shadows_enabled = enabled
        self.live_dec.configure(shadow_enabled=enabled)
        self._update_insets_display()

    def _on_toggle_error_state(self):
        is_err = self._err_var.get()
        self._is_error_state = is_err
        pal = tb.get_theme()
        if is_err:
            self.val_dec.configure(
                border_color="#ef4444",
                border_hover_color="#f87171",
                focus_ring_color="#ef4444",
                shadow_color="#ef444455",
            )
            self.val_entry.delete(0, tk.END)
            self.val_entry.insert(0, "Error: Invalid License Key Format")
            self.val_entry.configure(fg="#ef4444")
        else:
            self.val_dec.configure(
                border_color=pal.border,
                border_hover_color=pal.primary,
                focus_ring_color=pal.primary,
                shadow_color="#00000033",
            )
            self.val_entry.delete(0, tk.END)
            self.val_entry.insert(0, "BLND-8941-XJ92 (Valid)")
            self.val_entry.configure(fg=pal.fg)

    def _toggle_sim_hover(self):
        self._is_simulated_hover = not self._is_simulated_hover
        self.live_dec.native.set_hovered(self._is_simulated_hover)
        self.live_dec.redraw()

    def _toggle_sim_focus(self):
        self._is_simulated_focus = not self._is_simulated_focus
        self.live_dec.native.set_focused(self._is_simulated_focus)
        self.live_dec.redraw()

    def _reset_sim_states(self):
        self._is_simulated_hover = False
        self._is_simulated_focus = False
        self.live_dec.native.set_hovered(False)
        self.live_dec.native.set_focused(False)
        self.live_dec.redraw()

    def _update_insets_display(self):
        insets = self.live_dec.insets
        self.insets_lbl.config(
            text=f"Active Insets: L={insets[0]:.1f}px, T={insets[1]:.1f}px, R={insets[2]:.1f}px, B={insets[3]:.1f}px"
        )

    def _on_change_theme(self, theme_name: str):
        tb.set_theme(theme_name)
        pal = tb.get_theme()

        # Update root and background frames
        for f in self._bg_frames:
            try:
                f.configure(bg=pal.bg)
            except Exception:
                pass

        # Update card inner frames
        for f in self._card_frames:
            try:
                f.configure(bg=pal.card_bg)
            except Exception:
                pass

        # Update labels with active theme palette
        for lbl in self._primary_labels:
            try:
                lbl.configure(fg=pal.fg, bg=pal.card_bg)
            except Exception:
                pass

        for lbl in self._muted_labels:
            try:
                lbl.configure(fg=pal.text_muted, bg=pal.card_bg)
            except Exception:
                pass

        # Update entries & text widgets
        for entry in self._entries:
            try:
                entry.configure(bg=pal.card_bg, fg=pal.fg, insertbackground=pal.fg)
            except Exception:
                pass

        if not self._is_error_state:
            try:
                self.val_entry.configure(fg=pal.fg)
            except Exception:
                pass

        self._update_insets_display()


def main():
    root = tk.Tk()
    root.title("tkblend - BlendDecorator Showcase")
    root.geometry("960x640")
    root.minsize(940, 600)

    tb.set_theme("tokyo-night")

    app = DecoratorShowcase(root)

    def on_close():
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
