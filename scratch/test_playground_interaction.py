import sys
import tkinter as tk
import tkblend as tb
from tkblend.widgets import Button, Slider, Frame, Card, Switch, Radiobutton, Checkbox, ProgressBar, RangeSlider, Label

def test_playground_and_properties():
    root = tk.Tk()
    btn = Button(root, text="Test Button", corner_radius=10.0, shadow_blur=8.0)
    
    # Test configuring custom vector options
    btn.configure(shadow_blur=16.0)
    assert btn.cget("shadow_blur") == 16.0 or btn._shadow_blur == 16.0
    
    btn.configure(corner_radius=20.0)
    assert btn.cget("corner_radius") == 20.0
    
    btn.configure(bg_color="#ff0000", fg_color="#00ff00", hover_color="#0000ff")
    assert btn._custom_bg_color == "#ff0000"
    assert btn._custom_fg_color == "#00ff00"
    
    # Test slider
    slider = Slider(root, from_=0, to=100, value=50, track_color="#123456", thumb_radius=12.0)
    slider.configure(value=75, track_color="#654321", thumb_radius=15.0)
    assert slider.get() == 75.0
    assert slider._custom_track_color == "#654321"
    assert slider._thumb_radius == 15.0
    
    # Test RangeSlider
    rs = RangeSlider(root, values=(10, 90))
    rs.configure(values=(20, 80))
    assert rs.get() == (20.0, 80.0)
    
    # Test Card
    card = Card(root, corner_radius=14.0, shadow_blur=12.0, bg_color="#202020")
    card.configure(corner_radius=18.0, shadow_blur=6.0, bg_color="#303030")
    assert card.cget("corner_radius") == 18.0
    assert card._shadow_blur == 6.0
    assert card._custom_card_bg == "#303030"
    
    # Test Frame
    frame = Frame(root, corner_radius=8.0, bg_color="#404040")
    frame.configure(corner_radius=12.0, bg_color="#505050")
    assert frame.cget("corner_radius") == 12.0
    assert frame._custom_bg_color == "#505050"

    # Test dynamic theme switching with nested widgets
    tb.set_theme("dark")
    tb.apply_theme(root, "dark")
    dark_bg = tb.get_theme().bg
    
    tb.set_theme("light")
    tb.apply_theme(root, "light")
    light_bg = tb.get_theme().bg
    assert dark_bg != light_bg
    
    # Test resizing
    root.geometry("800x600")
    root.update_idletasks()
    root.update()
    
    root.geometry("1000x800")
    root.update_idletasks()
    root.update()
    
    root.destroy()
    print("All playground and property tests passed successfully!")

if __name__ == "__main__":
    test_playground_and_properties()
