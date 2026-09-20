"""
Comprehensive tests for BlendCanvas and Modern UI widgets.
"""

import unittest
import tkinter as tk
from types import SimpleNamespace
from tkblend import (
    Surface,
    BlendCanvas,
    ModernFrame,
    ModernCard,
    ModernButton,
    ModernProgressBar,
    ModernSlider,
    ModernSwitch,
)
from tkblend.widgets import ModernWidget


class TestWidgets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except Exception:
            cls.root = None

    @classmethod
    def tearDownClass(cls):
        if cls.root:
            cls.root.destroy()

    def test_blend_canvas(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        draw_called = []

        def draw_cb(s: Surface):
            draw_called.append(True)
            s.clear("#181825")
            s.fill_circle(50, 50, 20, "#89b4fa")

        canvas = BlendCanvas(self.root, width=120, height=80, on_draw=draw_cb)
        self.assertEqual(canvas.surface.width, 120)
        self.assertEqual(canvas.surface.height, 80)
        self.assertIsNotNone(canvas.photo)

        canvas.redraw()
        self.assertTrue(len(draw_called) > 0)

        # Update draw callback
        def new_draw_cb(s: Surface):
            s.clear("#ff0000")

        canvas.set_draw_callback(new_draw_cb)

        # Simulate resize configure event
        event = SimpleNamespace(width=200, height=150)
        canvas._on_configure(event)
        self.assertEqual(canvas.surface.width, 200)
        self.assertEqual(canvas.surface.height, 150)

        canvas.destroy()

    def test_modern_widget_base_events(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        w = ModernWidget(self.root, width=100, height=40)
        self.assertEqual(w.surface.width, 100)
        self.assertEqual(w.surface.height, 40)
        self.assertIsNotNone(w.photo)

        # Simulate hover and press events
        dummy_event = SimpleNamespace(x=50, y=20, width=100, height=40)
        w._on_enter(dummy_event)
        self.assertTrue(w._is_hovered)

        w._on_press(dummy_event)
        self.assertTrue(w._is_pressed)

        w._on_release(dummy_event)
        self.assertFalse(w._is_pressed)

        w._on_leave(dummy_event)
        self.assertFalse(w._is_hovered)

        # Disabled state ignores events
        w._is_disabled = True
        w._on_enter(dummy_event)
        self.assertFalse(w._is_hovered)

        # Configure event
        resize_event = SimpleNamespace(width=160, height=60)
        w._on_configure(resize_event)
        self.assertEqual(w.surface.width, 160)
        self.assertEqual(w.surface.height, 60)

        w.destroy()

    def test_modern_frame_and_card(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        frame = ModernFrame(self.root, width=220, height=160, bg_color="#1e1e2e")
        frame.render()
        frame.set_background("#24273a")

        # Nested widget inside modern frame
        btn = tk.Button(frame, text="Inside")
        btn.pack()

        # Resize event
        event = SimpleNamespace(width=300, height=200)
        frame._on_configure(event)
        self.assertEqual(frame._widget_w, 300)

        # Modern Card with and without title
        card1 = ModernCard(self.root, title="Card Title", width=250, height=180)
        card1.render()

        card2 = ModernCard(self.root, title="", width=200, height=100)
        card2.render()

        frame.destroy()
        card1.destroy()
        card2.destroy()

    def test_modern_button(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        clicks = []

        def on_click():
            clicks.append(1)

        btn = ModernButton(self.root, text="Action", command=on_click, width=120, height=40)
        btn.set_text("Updated")
        self.assertEqual(btn._text, "Updated")

        # Normal render
        btn.render()

        # Hover render
        btn._is_hovered = True
        btn.render()

        # Pressed render
        btn._is_pressed = True
        btn.render()

        # Release inside bounds triggers command
        in_event = SimpleNamespace(x=50, y=20)
        btn._handle_click(in_event)
        self.assertEqual(len(clicks), 1)

        # Release outside bounds does not trigger
        out_event = SimpleNamespace(x=500, y=200)
        btn._handle_click(out_event)
        self.assertEqual(len(clicks), 1)

        # Disabled button does not click
        btn._is_disabled = True
        btn._handle_click(in_event)
        self.assertEqual(len(clicks), 1)

        btn.destroy()

    def test_modern_progress_bar(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        pbar = ModernProgressBar(self.root, width=200, height=16, value=25.0)
        self.assertEqual(pbar.value, 25.0)

        pbar.set_value(75.5)
        self.assertEqual(pbar.value, 75.5)

        # Clamping
        pbar.value = -20.0
        self.assertEqual(pbar.value, 0.0)

        pbar.value = 150.0
        self.assertEqual(pbar.value, 100.0)

        pbar.render()
        pbar.destroy()

    def test_modern_slider(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        changes = []

        def on_change(val):
            changes.append(val)

        slider = ModernSlider(self.root, width=200, height=30, min_val=0.0, max_val=100.0, value=50.0, on_change=on_change)
        self.assertEqual(slider.value, 50.0)

        slider.value = 80.0
        self.assertEqual(slider.value, 80.0)

        # Drag event
        drag_event = SimpleNamespace(x=100, y=15)
        slider._on_drag(drag_event)
        self.assertTrue(len(changes) > 0)

        slider.destroy()

    def test_modern_switch(self):
        if not self.root:
            self.skipTest("Tkinter display not available")

        toggles = []

        def on_toggle(state):
            toggles.append(state)

        switch = ModernSwitch(self.root, is_on=False, on_toggle=on_toggle)
        self.assertFalse(switch.is_on)

        switch.is_on = True
        self.assertTrue(switch.is_on)

        switch.toggle()
        self.assertFalse(switch.is_on)
        self.assertEqual(toggles[-1], False)

        # Release inside bounds
        in_event = SimpleNamespace(x=10, y=10)
        switch._handle_toggle(in_event)
        self.assertTrue(switch.is_on)
        self.assertEqual(toggles[-1], True)

        # Release outside bounds
        out_event = SimpleNamespace(x=500, y=500)
        switch._handle_toggle(out_event)
        self.assertTrue(switch.is_on)

        switch.destroy()


if __name__ == "__main__":
    unittest.main()
