import os
import sys
import subprocess
import time
from PIL import Image

EXAMPLES = [
    "examples/widgets_showcase.py",
    "examples/analytics_dashboard.py",
    "examples/canvas_studio.py",
    "examples/ctk_showcase.py",
    "examples/custom_widget_cookbook.py",
    "examples/decorator_showcase.py",
    "examples/file_explorer.py",
    "examples/hub.py",
    "examples/icons_and_typography_demo.py",
    "examples/multimedia_dashboard.py",
    "examples/realtime_visualizer.py",
]

os.makedirs("/tmp/tkblend_examples", exist_ok=True)

runner_code = """
import sys
import os
import tkinter as tk
import time
from PIL import ImageGrab

target_file = sys.argv[1]
shot_name = sys.argv[2]

# Hook Tk.mainloop
orig_mainloop = tk.Tk.mainloop

def patched_mainloop(self, n=0):
    self.update()
    self.update_idletasks()
    time.sleep(0.4)
    x = self.winfo_rootx()
    y = self.winfo_rooty()
    w = self.winfo_width()
    h = self.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    img.save(shot_name)
    print(f"Captured {shot_name} ({w}x{h})")
    self.destroy()

tk.Tk.mainloop = patched_mainloop

with open(target_file, "r") as f:
    code = f.read()

# Execute target
sys.argv = [target_file]
exec(compile(code, target_file, "exec"), {"__name__": "__main__", "__file__": target_file})
"""

with open("/tmp/tkblend_examples/hook_runner.py", "w") as f:
    f.write(runner_code)

for ep in EXAMPLES:
    name = os.path.splitext(os.path.basename(ep))[0]
    out_png = f"/tmp/tkblend_examples/{name}.png"
    cmd = f'xvfb-run -a -s "-screen 0 1400x1000x24" uv run python /tmp/tkblend_examples/hook_runner.py {ep} {out_png}'
    print(f"Running {name}...")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    if res.returncode != 0:
        print(f"FAILED {name}: returncode {res.returncode}")
        print("STDOUT:", res.stdout[-500:])
        print("STDERR:", res.stderr[-500:])
    else:
        print(f"SUCCESS {name}: {res.stdout.strip()}")
