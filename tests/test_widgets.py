"""
Unit and integration tests for pure Blend2D vector widgets (tkblend.widgets)
powered by NativeController.
"""

import pytest
import tkinter as tk

import tkblend as tb
from tkblend.widgets import (
    BaseControl,
    Button,
    Switch,
    Toggle,
    Slider,
    CheckBox,
    ProgressBar,
    Progress,
    RadioButton,
    Card,
    Label,
    ScalingTracker,
)
from tkblend.theme import set_theme, get_theme


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


class TestBaseControl:
    def test_initialization_and_scaling(self, tk_root):
        base = BaseControl(tk_root, width=120, height=40)
        base.pack()
        tk_root.update_idletasks()

        assert base.controller.is_attached
        assert base.surface is not None
        assert base.scale_factor >= 0.5
        assert not base.is_disabled
        assert not base.is_hovered

        # Geometry request
        base.set_geometry_request(150, 50)
        assert base.cget("width") == 150
        assert base.cget("height") == 50

    def test_disabled_state(self, tk_root):
        base = BaseControl(tk_root, state="disabled")
        assert base.is_disabled
        assert base.controller.is_disabled

        base.is_disabled = False
        assert not base.is_disabled
        assert not base.controller.is_disabled

    def test_property_animation(self, tk_root):
        base = BaseControl(tk_root)
        base.pack()
        tk_root.update_idletasks()

        vals = []
        base.animate_property("test_anim", 0.0, 1.0, duration_ms=50, on_update=lambda v: vals.append(v))
        # Pump Tk event loop
        for _ in range(10):
            tk_root.update()
            tk_root.after(10)

        assert len(vals) > 0
        assert vals[-1] <= 1.0


class TestButton:
    def test_button_invoke_and_command(self, tk_root):
        clicked = []
        btn = Button(tk_root, text="Click Me", command=lambda: clicked.append(True))
        btn.pack()
        tk_root.update_idletasks()

        assert btn.text == "Click Me"
        btn.invoke()
        assert len(clicked) == 1

        # Simulate click
        btn.on_click(10, 10, 1)
        assert len(clicked) == 2

        # Disabled button cannot be invoked
        btn.is_disabled = True
        btn.invoke()
        btn.on_click(10, 10, 1)
        assert len(clicked) == 2

    def test_button_rendering_and_icons(self, tk_root):
        btn = Button(tk_root, text="Rocket", icon="rocket", width=140, height=40)
        btn.pack()
        tk_root.update_idletasks()

        btn.paint_and_blit()
        assert btn.controller.width >= 1
        assert btn.controller.height >= 1

        btn.text = "New Label"
        assert btn.text == "New Label"
        btn.paint_and_blit()


class TestSwitch:
    def test_switch_toggle_and_variable(self, tk_root):
        var = tk.BooleanVar(value=False)
        actions = []
        sw = Switch(tk_root, text="Dark Mode", variable=var, command=lambda: actions.append(sw.get()))
        sw.pack()
        tk_root.update_idletasks()

        assert not sw.is_on()
        assert sw.get() is False

        sw.toggle()
        assert sw.is_on()
        assert sw.get() is True
        assert var.get() is True
        assert len(actions) == 1

        # Variable synchronization
        var.set(False)
        assert not sw.is_on()

        sw.select()
        assert sw.is_on()
        assert var.get() is True

        sw.deselect()
        assert not sw.is_on()
        assert var.get() is False

    def test_switch_rendering(self, tk_root):
        sw = Toggle(tk_root, text="Airplane Mode")
        sw.pack()
        tk_root.update_idletasks()
        sw.paint_and_blit()


class TestSlider:
    def test_slider_value_and_bounds(self, tk_root):
        var = tk.DoubleVar(value=25.0)
        updates = []
        slider = Slider(tk_root, from_=0.0, to=100.0, variable=var, command=lambda v: updates.append(v))
        slider.pack()
        tk_root.update_idletasks()

        assert slider.get() == 25.0

        slider.set(75.0)
        assert slider.get() == 75.0
        assert var.get() == 75.0

        # Out of bounds clamping
        slider.set(150.0)
        assert slider.get() == 100.0
        slider.set(-20.0)
        assert slider.get() == 0.0

    def test_slider_quantization_steps(self, tk_root):
        slider = Slider(tk_root, from_=0.0, to=10.0, number_of_steps=5)
        slider.set(3.2)
        assert slider.get() == 4.0  # nearest discrete step (0, 2, 4, 6, 8, 10)

    def test_slider_vertical_orientation(self, tk_root):
        slider = Slider(tk_root, from_=0.0, to=100.0, orientation="vertical", width=24, height=150)
        slider.pack()
        tk_root.update()
        slider.paint_and_blit()
        assert slider.cget("height") == 150
        assert slider.winfo_reqheight() >= 100


class TestCheckBox:
    def test_checkbox_toggle_and_variable(self, tk_root):
        var = tk.StringVar(value="off")
        cb = CheckBox(tk_root, text="Agree", variable=var, onvalue="on", offvalue="off")
        cb.pack()
        tk_root.update_idletasks()

        assert not cb.is_checked()
        assert cb.get() == "off"

        cb.toggle()
        assert cb.is_checked()
        assert cb.get() == "on"
        assert var.get() == "on"

        cb.deselect()
        assert not cb.is_checked()
        assert var.get() == "off"

        cb.select()
        assert cb.is_checked()
        assert var.get() == "on"

    def test_checkbox_render(self, tk_root):
        cb = CheckBox(tk_root, text="Remember me")
        cb.pack()
        tk_root.update_idletasks()
        cb.paint_and_blit()


class TestProgressBar:
    def test_progressbar_determinate(self, tk_root):
        var = tk.DoubleVar(value=0.2)
        pb = ProgressBar(tk_root, variable=var)
        pb.pack()
        tk_root.update_idletasks()

        assert pb.get() == 0.2
        pb.set(0.8)
        assert pb.get() == 0.8
        assert var.get() == 0.8

        pb.step(0.1)
        assert abs(pb.get() - 0.9) < 1e-4

        pb.paint_and_blit()

    def test_progressbar_indeterminate(self, tk_root):
        pb = Progress(tk_root, mode="indeterminate")
        pb.pack()
        tk_root.update_idletasks()

        pb.start()
        assert pb._running
        pb.stop()
        assert not pb._running


class TestRadioButton:
    def test_radio_group(self, tk_root):
        var = tk.StringVar(value="opt1")
        r1 = RadioButton(tk_root, text="Option 1", value="opt1", variable=var)
        r2 = RadioButton(tk_root, text="Option 2", value="opt2", variable=var)
        r1.pack()
        r2.pack()
        tk_root.update_idletasks()

        assert r1._is_selected
        assert not r2._is_selected

        r2.select()
        assert not r1._is_selected
        assert r2._is_selected
        assert var.get() == "opt2"


class TestCardAndLabel:
    def test_card_container_and_bg_cascade(self, tk_root):
        card = Card(tk_root, width=200, height=120)
        card.pack()
        lbl = Label(card, text="Inside Card")
        lbl.pack()
        tk_root.update_idletasks()

        assert card.bg_color is not None
        card.paint_and_blit()
        lbl.paint_and_blit()

    def test_label_icon_and_styling(self, tk_root):
        lbl = Label(tk_root, text="Status", icon="fa:circle-check", bg_color="#10b981", corner_radius=6)
        lbl.pack()
        tk_root.update_idletasks()
        lbl.paint_and_blit()


class TestThemingIntegration:
    def test_theme_switch_updates_widgets(self, tk_root):
        btn = Button(tk_root, text="Theme Button")
        sw = Switch(tk_root, text="Theme Switch")
        card = Card(tk_root)
        btn.pack()
        sw.pack()
        card.pack()
        tk_root.update_idletasks()

        # Switch to light
        set_theme("light")
        tk_root.update_idletasks()
        assert get_theme().name == "light"
        btn.paint_and_blit()
        sw.paint_and_blit()
        card.paint_and_blit()

        # Switch back to dark
        set_theme("dark")
        tk_root.update_idletasks()
        assert get_theme().name == "dark"
        btn.paint_and_blit()


class TestExtendedBaseControlWidgets:
    def test_frame_container(self, tk_root):
        f = tb.Frame(tk_root, width=200, height=100, corner_radius=8)
        f.pack()
        tk_root.update_idletasks()
        assert f.bg_color is not None
        f.paint_and_blit()

    def test_badge_and_avatar(self, tk_root):
        b = tb.Badge(tk_root, text="ONLINE", variant="success", dot=True)
        b.pack()
        a = tb.Avatar(tk_root, text="TB", size=36)
        a.pack()
        tk_root.update_idletasks()
        b.paint_and_blit()
        a.paint_and_blit()

    def test_circular_progress_and_gauge(self, tk_root):
        cp = tb.CircularProgress(tk_root, size=100, value=75.0, title="CPU")
        cp.pack()
        g = tb.Gauge(tk_root, size=120, value=50.0)
        g.pack()
        tk_root.update_idletasks()
        cp.set(80.0)
        assert cp.get() == 80.0
        cp.paint_and_blit()
        g.paint_and_blit()

    def test_segmented_button(self, tk_root):
        sb = tb.SegmentedButton(tk_root, values=["Tab 1", "Tab 2", "Tab 3"])
        sb.pack()
        tk_root.update_idletasks()
        assert sb.get() == "Tab 1"
        sb.set("Tab 2")
        assert sb.get() == "Tab 2"
        sb.paint_and_blit()

    def test_range_slider(self, tk_root):
        rs = tb.RangeSlider(tk_root, from_=0, to=100, values=(20, 80))
        rs.pack()
        tk_root.update_idletasks()
        assert rs.get() == (20.0, 80.0)
        rs.set(30.0, 70.0)
        assert rs.get() == (30.0, 70.0)
        rs.paint_and_blit()

    def test_combobox(self, tk_root):
        cb = tb.ComboBox(tk_root, values=["Red", "Green", "Blue"], selected_value="Red")
        cb.pack()
        tk_root.update_idletasks()
        assert cb.get() == "Red"
        cb.set("Blue")
        assert cb.get() == "Blue"
        cb.paint_and_blit()

    def test_textbox_and_entry(self, tk_root):
        entry = tb.Entry(tk_root, text="Hello", placeholder="Search...")
        entry.pack()
        s_entry = tb.SearchEntry(tk_root)
        s_entry.pack()
        txt = tb.TextBox(tk_root, width=200, height=80)
        txt.pack()
        tk_root.update_idletasks()
        assert entry.get() == "Hello"
        txt.insert("1.0", "Sample content")
        assert "Sample" in txt.get()
        entry.paint_and_blit()
        txt.paint_and_blit()

    def test_scrollable_frame(self, tk_root):
        sf = tb.ScrollableFrame(tk_root, width=200, height=150)
        sf.pack()
        lbl = tb.Label(sf.content_frame, text="Inside Scrollable")
        lbl.pack()
        tk_root.update_idletasks()
        assert sf.bg_color is not None
        sf.paint_and_blit()

    def test_table(self, tk_root):
        cols = [{"name": "id", "title": "ID", "width": 50}, {"name": "name", "title": "Name", "width": 100}]
        data = [{"id": "1", "name": "Alpha"}, {"id": "2", "name": "Beta"}]
        tbl = tb.Table(tk_root, columns=cols, data=data)
        tbl.pack()
        tk_root.update_idletasks()
        tbl.set_selection(0)
        assert tbl.get_selected_index() == 0
        tbl.sort_by(1)
        tbl.paint_and_blit()

    def test_tabview(self, tk_root):
        tv = tb.Tabview(tk_root, width=300, height=200)
        tv.pack()
        t1 = tv.add("First")
        t2 = tv.add("Second")
        lbl = tb.Label(t1, text="Tab 1 content")
        lbl.pack()
        tk_root.update_idletasks()
        tv.set("Second")
        assert tv.get() == "Second"
        tv.paint_and_blit()

    def test_sparkline(self, tk_root):
        sp = tb.Sparkline(tk_root, data=[10, 25, 18, 40, 32, 60], kind="area")
        sp.pack()
        tk_root.update_idletasks()
        sp.push(75.0)
        assert len(sp.data) == 7
        sp.paint_and_blit()

