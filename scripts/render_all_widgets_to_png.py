"""
Generates comprehensive PNG snapshots of all tkblend widgets across Dark and Light themes.
"""
import os
import gc
import tkinter as tk
from PIL import Image

from tkblend import (
    Button,
    Badge,
    Avatar,
    TextInput,
    SpinBox,
    Switch,
    Checkbutton,
    Radiobutton,
    SegmentedControl,
    Progressbar,
    CircularProgress,
    Slider,
    RangeSlider,
    Card,
    Dropdown,
    set_theme,
    get_theme,
    clear_caches,
)

def save_widget(widget, name, theme):
    try:
        widget.render()
        w, h = widget._widget_w, widget._widget_h
        buf = widget.surface.get_buffer()
        stride = widget.surface.stride()
        img = Image.frombuffer("RGBA", (w, h), bytes(buf), "raw", "BGRA", stride, 1)
        os.makedirs("artifacts/snapshots", exist_ok=True)
        filename = f"artifacts/snapshots/{theme}_{name}.png"
        img.save(filename)
        print(f"Saved {filename} ({w}x{h})")
        return filename
    except Exception as e:
        print(f"Error saving {theme}_{name}: {e}")
        return None

def render_suite():
    for theme in ["dark", "light"]:
        set_theme(theme)
        pal = get_theme()

        root = tk.Tk()
        root.configure(bg=pal.bg)
        root.geometry("800x600")

        # Buttons
        b_pri = Button(root, text="Primary", variant="primary", width=140, height=36)
        b_pri.pack()
        b_sec = Button(root, text="Secondary", variant="secondary", width=140, height=36)
        b_sec.pack()
        b_dest = Button(root, text="Destructive", variant="destructive", width=140, height=36)
        b_dest.pack()
        b_out = Button(root, text="Outline", variant="outline", width=140, height=36)
        b_out.pack()

        # Badges & Avatar
        badge_suc = Badge(root, text="Success", variant="success")
        badge_suc.pack()
        badge_warn = Badge(root, text="Warning", variant="warning")
        badge_warn.pack()
        badge_dest = Badge(root, text="Critical", variant="destructive")
        badge_dest.pack()
        avatar = Avatar(root, text="JD", size=44)
        avatar.pack()

        # Inputs
        inp = TextInput(root, placeholder="Search products...", width=200, height=36)
        inp.pack()
        spin = SpinBox(root, from_=1, to=100, width=110, height=36)
        spin.pack()

        # Selection
        sw_on = Switch(root, text="Notifications", is_on=True, width=150, height=32)
        sw_on.pack()
        sw_off = Switch(root, text="Muted", is_on=False, width=150, height=32)
        sw_off.pack()
        cb = Checkbutton(root, text="Remember session", is_checked=True, width=170, height=32)
        cb.pack()
        rb = Radiobutton(root, text="Annual billing", is_selected=True, width=160, height=32)
        rb.pack()
        seg = SegmentedControl(root, values=["Daily", "Weekly", "Monthly"], width=270, height=34)
        seg.pack()

        # Sliders & Progress
        sl = Slider(root, from_=0, to=100, value=75, width=220, height=32)
        sl.pack()
        rsl = RangeSlider(root, from_=0, to=100, low_val=20, high_val=80, width=220, height=32)
        rsl.pack()
        pb = Progressbar(root, value=65, width=240, height=18)
        pb.pack()
        cp = CircularProgress(root, value=78, size=72, thickness=7.0)
        cp.pack()

        # Card & Dropdown
        card = Card(root, title="Analytics Summary", width=340, height=220)
        card.pack()
        dd = Dropdown(root, options=["Option Alpha", "Option Beta", "Option Gamma"], width=170, height=36)
        dd.pack()

        root.update()

        save_widget(b_pri, "button_primary", theme)
        save_widget(b_sec, "button_secondary", theme)
        save_widget(b_dest, "button_destructive", theme)
        save_widget(b_out, "button_outline", theme)
        save_widget(badge_suc, "badge_success", theme)
        save_widget(badge_warn, "badge_warning", theme)
        save_widget(badge_dest, "badge_destructive", theme)
        save_widget(avatar, "avatar", theme)
        save_widget(inp, "textinput", theme)
        save_widget(spin, "spinbox", theme)
        save_widget(sw_on, "switch_on", theme)
        save_widget(sw_off, "switch_off", theme)
        save_widget(cb, "checkbutton", theme)
        save_widget(rb, "radiobutton", theme)
        save_widget(seg, "segmented_control", theme)
        save_widget(sl, "slider", theme)
        save_widget(rsl, "range_slider", theme)
        save_widget(pb, "progressbar", theme)
        save_widget(cp, "circular_progress", theme)
        save_widget(card, "card", theme)
        save_widget(dd, "dropdown", theme)

        # Proactive teardown
        for child in list(root.winfo_children()):
            if hasattr(child, "destroy"):
                child.destroy()
        root.destroy()
        del b_pri, b_sec, b_dest, b_out, badge_suc, badge_warn, badge_dest, avatar
        del inp, spin, sw_on, sw_off, cb, rb, seg, sl, rsl, pb, cp, card, dd, root
        gc.collect()

    clear_caches()
    print("ALL WIDGET SNAPSHOTS RENDERED AND SAVED!")

if __name__ == "__main__":
    render_suite()
