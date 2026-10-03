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

    out_dir = "/tmp/tkblend_showcase_pages"
    os.makedirs(out_dir, exist_ok=True)

    def capture(name):
        root.update()
        root.update_idletasks()
        time.sleep(0.2)
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        img.save(f"{out_dir}/{name}.png")
        print(f"Saved {name}.png ({w}x{h})")

    pages = ["controls", "metrics", "containers", "playground", "themes"]

    # 1. Capture all pages in Dark Mode
    for p in pages:
        app._navigate_to(p)
        capture(f"dark_{p}")

    # 2. Switch to Light Mode and capture all pages
    app._change_theme("light")
    for p in pages:
        app._navigate_to(p)
        capture(f"light_{p}")

    # 3. Switch to Ocean Theme
    app._change_theme("ocean")
    app._navigate_to("controls")
    capture("ocean_controls")

    # 4. Switch to Neon Theme
    app._change_theme("neon")
    app._navigate_to("metrics")
    capture("neon_metrics")

    root.destroy()

if __name__ == "__main__":
    run()
