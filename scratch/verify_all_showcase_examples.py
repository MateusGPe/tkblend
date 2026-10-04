import sys
import tkinter as tk
import time

def verify_all_examples():
    import examples.widgets_showcase as ws
    import examples.canvas_studio as cs
    import examples.decorator_showcase as ds

    print("1. Testing WidgetsShowcaseApp...")
    r1 = tk.Tk()
    app1 = ws.WidgetsShowcaseApp(r1)
    r1.update()
    
    # Test switching pages and themes
    for page in ["controls", "metrics", "containers", "playground", "themes"]:
        app1._navigate_to(page)
        r1.update()
    
    # Test playground sliders
    app1._navigate_to("playground")
    app1._on_pg_radius_changed(16.0)
    app1._on_pg_shadow_changed(12.0)
    app1._on_pg_icon_changed("Gear")
    r1.update()
    
    for th in ["light", "ocean", "neon", "dark"]:
        app1._change_theme(th)
        r1.update()
    r1.destroy()
    print("   WidgetsShowcaseApp PASSED!")

    print("2. Testing CanvasStudio...")
    r2 = tk.Tk()
    app2 = cs.CanvasStudio(r2)
    app2.pack(fill="both", expand=True)
    r2.update()
    for th in ["light", "ocean", "neon", "dark"]:
        app2._on_theme_changed(th)
        r2.update()
    r2.destroy()
    print("   CanvasStudio PASSED!")

    print("3. Testing DecoratorShowcase...")
    r3 = tk.Tk()
    app3 = ds.DecoratorShowcase(r3)
    app3.pack(fill="both", expand=True)
    r3.update()
    for th in ["light", "tokyo-night", "nord", "dark"]:
        app3._on_change_theme(th)
        r3.update()
    r3.destroy()
    print("   DecoratorShowcase PASSED!")

    print("\nALL SHOWCASE EXAMPLES VERIFIED CLEANLY WITH ZERO ERRORS!")

if __name__ == "__main__":
    verify_all_examples()
