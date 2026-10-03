import os
import sys
import tkinter as tk
import time
from PIL import Image, ImageGrab

import tkblend as tb
from tkblend.widgets import (
    Button,
    Switch,
    Slider,
    CheckBox,
    ProgressBar,
    CircularProgress,
    Gauge,
    RadioButton,
    Card,
    Label,
    Badge,
    Avatar,
    SegmentedButton,
    RangeSlider,
    ComboBox,
    TextBox,
    Entry,
    SearchEntry,
    ScrollableFrame,
    Table,
    Tabview,
    Sparkline,
    Frame,
)
from tkblend.theme import set_theme, get_theme, get_available_themes, apply_theme

def run():
    root = tk.Tk()
    root.title("Visual Test")
    root.geometry("1000x800")
    apply_theme(root, "dark")

    # Main container
    scroll = ScrollableFrame(root, width=980, height=780)
    scroll.pack(fill="both", expand=True, padx=10, pady=10)
    parent = scroll.scrollable_frame

    lbl = Label(parent, text="tkblend Controls Visual Inspection", font_size=16, bold=True)
    lbl.pack(pady=10)

    # Row 1: ComboBox & Popups
    card1 = Card(parent, width=940, height=120)
    card1.pack(fill="x", pady=5, padx=5)
    
    cb1 = ComboBox(card1, values=["Option 1 (Alpha)", "Option 2 (Beta)", "Option 3 (Gamma)", "Option 4 (Delta)"], width=200)
    cb1.place(x=20, y=30)

    btn = Button(card1, text="Test Button", width=120)
    btn.place(x=250, y=30)

    seg = SegmentedButton(card1, values=["Day", "Week", "Month", "Year"], width=280)
    seg.place(x=400, y=30)

    # Row 2: RangeSlider & Sliders & Badges
    card2 = Card(parent, width=940, height=120)
    card2.pack(fill="x", pady=5, padx=5)

    rslider = RangeSlider(card2, width=250, values=(20, 80))
    rslider.place(x=20, y=30)

    slider = Slider(card2, width=200, value=60)
    slider.place(x=300, y=35)

    badge = Badge(card2, text="ACTIVE", variant="success")
    badge.place(x=530, y=35)

    avatar = Avatar(card2, text="MG", size=40)
    avatar.place(x=620, y=25)

    root.update()
    root.update_idletasks()
    time.sleep(0.5)

    # Grab window screenshot
    os.makedirs("/tmp/tkblend_shots", exist_ok=True)
    
    # Take screenshot of main window
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save("/tmp/tkblend_shots/initial_dark.png")
    print("Saved initial_dark.png")

    # Now click ComboBox to open popup
    cb1._on_click(None)
    root.update()
    root.update_idletasks()
    time.sleep(0.5)

    img_popup = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img_popup.save("/tmp/tkblend_shots/combobox_popup.png")
    print("Saved combobox_popup.png")

    # Switch theme to light
    apply_theme(root, "light")
    root.update()
    root.update_idletasks()
    time.sleep(0.5)

    img_light = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img_light.save("/tmp/tkblend_shots/switched_light.png")
    print("Saved switched_light.png")

    root.destroy()

if __name__ == "__main__":
    run()
