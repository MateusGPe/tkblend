"""
Resilience, chaos, and unexpected termination tests for tkblend.
Proves memory safety, zero-leak teardown under abrupt terminations, exceptions,
interleaved thread storms, and invalid lifecycle states.
"""

import gc
import os
import sys
import time
import pytest
import threading
import subprocess
import tkinter as tk
from typing import List

import tkblend as tb
from tkblend._tkblend import (
    Surface as NativeSurface,
    Color as NativeColor,
    NativeWidgetController,
    NativeDecorator,
)
from tkblend.widgets import (
    BaseControl,
    Button,
    Switch,
    Slider,
    CheckBox,
    ProgressBar,
    RadioButton,
    Card,
    Label,
)


@pytest.fixture
def clean_gc():
    """Ensure clean garbage collection state before and after test."""
    gc.collect()
    yield
    gc.collect()


class TestAbruptTerminationAndLifecycleChaos:
    """Tests handling abrupt Tk root destruction without normal widget teardown."""

    def test_abrupt_root_destroy_with_active_animations(self, clean_gc):
        """Simulate closing the main window abruptly while 50 widgets are actively animating."""
        root = tk.Tk()
        root.withdraw()

        widgets: List[BaseControl] = []
        for i in range(25):
            sw = Switch(root, text=f"Switch {i}", animated=True)
            sw.pack()
            sw.toggle()  # starts property animation
            widgets.append(sw)

            pb = ProgressBar(root, mode="indeterminate", animated=True)
            pb.pack()
            pb.start(interval_ms=10)  # starts recursive after() loop
            widgets.append(pb)

        root.update_idletasks()

        # Abruptly kill the root window without calling widget.destroy()
        root.destroy()
        del widgets, root
        gc.collect()

        surfaces = [o for o in gc.get_objects() if isinstance(o, (NativeSurface, NativeWidgetController))]
        assert len(surfaces) == 0, f"Leaked {len(surfaces)} objects after abrupt root destruction"

    def test_tcl_native_destroy_bypass_python(self, clean_gc):
        """Destroy window directly via Tcl interpreter command bypass."""
        root = tk.Tk()
        root.withdraw()

        btn = Button(root, text="Native Target")
        btn.pack()
        sw = Switch(root, text="Native Switch", variable=tk.BooleanVar(value=True))
        sw.pack()
        root.update_idletasks()

        # Tcl evaluates direct destruction of widgets
        root.tk.eval(f"destroy {btn._w}")
        root.tk.eval(f"destroy {sw._w}")
        root.update_idletasks()

        # Widget should handle native destruction gracefully
        root.destroy()
        del btn, sw, root
        gc.collect()

        leaked = [o for o in gc.get_objects() if isinstance(o, (NativeWidgetController, NativeDecorator))]
        assert len(leaked) == 0

    def test_toplevel_destruction_storm(self, clean_gc):
        """Rapidly create and destroy Toplevel windows hosting complex widgets."""
        root = tk.Tk()
        root.withdraw()

        for step in range(15):
            top = tk.Toplevel(root)
            top.withdraw()

            card = Card(top, width=200, height=150)
            card.pack()
            btn = Button(card, text="Storm Button")
            btn.pack()
            sl = Slider(card, from_=0, to=100, value=50)
            sl.pack()
            pb = ProgressBar(card, mode="indeterminate")
            pb.pack()
            pb.start(5)

            top.update_idletasks()

            if step % 2 == 0:
                top.destroy()  # explicit destroy
            else:
                root.tk.eval(f"destroy {top._w}")  # abrupt Tcl destroy

        root.destroy()
        del root
        gc.collect()

        controllers = [o for o in gc.get_objects() if isinstance(o, NativeWidgetController)]
        assert len(controllers) == 0


class TestExceptionUnwindingAndErrorResilience:
    """Tests verify that exceptions in callbacks/rendering never corrupt state or leak C++ instances."""

    def test_controller_on_paint_exception_survival(self, clean_gc):
        """Native controller survives python exceptions thrown in on_paint callback."""
        root = tk.Tk()
        root.withdraw()

        call_count = 0

        def failing_paint(surf):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise RuntimeError(f"Simulated paint error {call_count}")
            surf.clear("#1e1e2e")

        ctrl = tb.NativeController(root, on_paint=failing_paint)
        ctrl.set_geometry_request(100, 40)
        root.update_idletasks()

        # Trigger paint multiple times through exceptions
        for _ in range(5):
            try:
                ctrl.paint_and_blit()
            except Exception:
                pass

        assert call_count >= 4
        ctrl.detach()
        root.destroy()
        del ctrl, root
        gc.collect()

        leaked = [o for o in gc.get_objects() if isinstance(o, NativeWidgetController)]
        assert len(leaked) == 0

    def test_widget_render_error_recovery(self, clean_gc):
        """Widget with a failing render method does not leak native controllers or surfaces."""
        root = tk.Tk()
        root.withdraw()

        class FaultyButton(Button):
            def render(self, surf, pal, w, h, scale):
                raise ValueError("Faulty render method")

        btn = FaultyButton(root, text="Crash")
        btn.pack()
        root.update_idletasks()

        try:
            btn.paint_and_blit()
        except ValueError:
            pass

        btn.destroy()
        root.destroy()
        del btn, root
        gc.collect()

        surfaces = [o for o in gc.get_objects() if isinstance(o, NativeSurface)]
        assert len(surfaces) == 0


class TestVariableTraceChaosAndThreadRaces:
    """Tests chaotic variable operations, unsetting, reassignment, and thread-safety."""

    def test_rapid_variable_churn_and_unsetting(self, clean_gc):
        """Rapidly reassign and delete Tk variables connected to active widgets."""
        root = tk.Tk()
        root.withdraw()

        sw = Switch(root, text="Churn Switch")
        sw.pack()
        sl = Slider(root)
        sl.pack()

        for i in range(20):
            var_b = tk.BooleanVar(value=(i % 2 == 0))
            var_d = tk.DoubleVar(value=float(i * 5))

            sw.configure(variable=var_b)
            sl.configure(variable=var_d)

            var_b.set(not var_b.get())
            var_d.set(float(i * 10))
            root.update_idletasks()

            # Set variable to None
            sw.configure(variable=None)
            sl.configure(variable=None)

        sw.destroy()
        sl.destroy()
        root.destroy()
        del sw, sl, root
        gc.collect()

        assert len([o for o in gc.get_objects() if isinstance(o, NativeWidgetController)]) == 0

    def test_concurrent_multithreaded_rendering_torture(self, clean_gc):
        """Stress concurrent Blend2D surface rendering across multiple OS threads."""
        errors = []

        def worker(tid: int):
            for i in range(20):
                try:
                    s = tb.Surface(120, 40)
                    s.clear("#181825")
                    s.fill_rounded_rect(5, 5, 110, 30, 8, 8, "#89b4fa")
                    s.draw_text(f"Thread {tid}-{i}", 15, 22, font_size=12, color="#ffffff")
                    s.flush()
                    s.close()
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        gc.collect()
        assert len(errors) == 0
        assert len([o for o in gc.get_objects() if isinstance(o, NativeSurface)]) == 0


class TestSurfacePinningAndBufferSafety:
    """Verify Surface pinned buffer protections against illegal resize/destruction."""

    def test_buffer_pinned_resize_prevention_and_recovery(self, clean_gc):
        """Verify active memoryview strictly prevents resize and can be released cleanly."""
        surf = tb.Surface(100, 100)
        buf = surf.get_buffer()
        mv = memoryview(buf)

        # Resizing while memoryview is alive MUST raise
        with pytest.raises(RuntimeError):
            surf.resize(200, 200)

        # Closing while memoryview is alive MUST raise
        with pytest.raises(RuntimeError):
            surf.close()

        # Release memoryview
        del mv, buf
        gc.collect()

        # Now resize and close succeed without leak
        surf.resize(200, 200)
        assert surf.width == 200
        assert surf.height == 200
        surf.close()
        del surf
        gc.collect()

        assert len([o for o in gc.get_objects() if isinstance(o, NativeSurface)]) == 0


class TestSubprocessIsolatedLeakProof:
    """Run an isolated Python sub-process executing extreme widget stress to assert zero nanobind leaks at exit."""

    def test_isolated_subprocess_zero_nanobind_leaks(self):
        code = """
import gc
import tkinter as tk
import tkblend as tb
from tkblend.widgets import Switch, Slider, Button, ProgressBar, CheckBox, RadioButton, Card

root = tk.Tk()
root.withdraw()

for _ in range(30):
    c = Card(root, width=300, height=200)
    c.pack()
    btn = Button(c, text="Click", icon="rocket")
    btn.pack()
    sw = Switch(c, text="Toggle", variable=tk.BooleanVar(value=True))
    sw.pack()
    sl = Slider(c, variable=tk.DoubleVar(value=50.0))
    sl.pack()
    cb = CheckBox(c, text="Check", variable=tk.BooleanVar(value=False))
    cb.pack()
    pb = ProgressBar(c, mode="indeterminate")
    pb.pack()
    pb.start(10)
    root.update_idletasks()
    c.destroy()

root.destroy()
gc.collect()
"""
        env = os.environ.copy()
        env["PYTHONDEVMODE"] = "1"
        res = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            env=env,
        )

        assert res.returncode == 0, f"Subprocess failed: {res.stderr}"
        assert "nanobind: leaked" not in res.stderr, f"Nanobind leak reported: {res.stderr}"
        assert "nanobind: leaked" not in res.stdout, f"Nanobind leak reported: {res.stdout}"
