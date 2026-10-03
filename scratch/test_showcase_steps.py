import sys
import os
import tkinter as tk
import time
from PIL import ImageGrab

def run():
    import examples.widgets_showcase as ws
    
    root = tk.Tk()
    app = ws.WidgetsShowcaseApp(root)
    root.update()
    root.update_idletasks()
    time.sleep(0.3)

    os.makedirs("/tmp/tkblend_showcase_steps", exist_ok=True)

    def grab(name):
        root.update()
        root.update_idletasks()
        time.sleep(0.2)
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        img.save(f"/tmp/tkblend_showcase_steps/{name}.png")
        print(f"Saved {name}.png")

    # 1. Tab 1 Dark
    grab("tab1_dark")

    # 2. Toggle Theme to Light
    app._change_theme("light")
    grab("tab1_light")

    # 3. Tab 2 Light
    app._show_page("gauges")
    grab("tab2_light")

    # 4. Tab 3 Light
    app._show_page("playground")
    grab("tab3_light")

    # 5. Tab 4 Light
    app._show_page("themes")
    grab("tab4_light")

    # 6. Toggle back to Dark in matrix
    app._change_theme("dark")
    grab("tab4_dark")

    root.destroy()

if __name__ == "__main__":
    run()
