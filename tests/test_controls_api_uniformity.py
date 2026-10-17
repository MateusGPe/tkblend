import pytest
import tkinter as tk
from tkblend.theme import set_theme
from tkblend.widgets import (
    Button,
    Label,
    Checkbox,
    Radio,
    Switch,
    Badge,
    SegmentedButton,
    Slider,
    RangeSlider,
    Progressbar,
    CircularProgress,
    Gauge,
    ComboBox,
    OptionMenu,
    Entry,
    SearchEntry,
    TextBox,
    Frame,
    Card,
)


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_uniform_constructor_and_properties(root):
    set_theme("dark")

    # Button
    btn = Button(root, text="Uniform Button", width=140, height=40, min_width=100, max_width=200, anchor="w", corner_radius=10.0)
    assert btn.text == "Uniform Button"
    assert btn.width == 140
    assert btn.height == 40
    assert btn.min_width == 100
    assert btn.max_width == 200
    assert btn.anchor == "w"
    assert btn.corner_radius == 10.0
    btn.configure(text="Updated Button", anchor="e", state="disabled")
    assert btn.text == "Updated Button"
    assert btn.anchor == "e"
    assert btn.state == "disabled"
    assert btn.is_disabled is True
    btn.state = "normal"
    assert btn.is_disabled is False

    # Label
    lbl = Label(root, text="Uniform Label", anchor="e")
    assert lbl.text == "Uniform Label"
    assert lbl.anchor == "e"
    lbl.configure(text="Updated Label", anchor="w")
    assert lbl.text == "Updated Label"
    assert lbl.anchor == "w"

    # Checkbox
    cb_var = tk.BooleanVar(value=True)
    cb = Checkbox(root, text="Uniform Checkbox", variable=cb_var, anchor="w", min_width=120)
    assert cb.text == "Uniform Checkbox"
    assert cb.is_checked is True
    assert cb.anchor == "w"
    assert cb.min_width == 120
    cb.configure(state="disabled")
    assert cb.is_disabled is True

    # Radio
    r_var = tk.StringVar(value="b")
    r = Radio(root, text="Option B", value="b", variable=r_var)
    assert r.text == "Option B"
    assert r.is_selected is True
    r.configure(text="Option B Edited", state="disabled")
    assert r.text == "Option B Edited"
    assert r.is_disabled is True

    # Switch
    sw_var = tk.BooleanVar(value=False)
    sw = Switch(root, text="Uniform Switch", variable=sw_var)
    assert sw.text == "Uniform Switch"
    assert sw.is_checked is False
    sw.toggle()
    assert sw.is_checked is True
    assert sw_var.get() is True

    # Badge
    bg = Badge(root, text="Active", min_width=50, max_width=150)
    assert bg.text == "Active"
    assert bg.min_width == 50
    assert bg.max_width == 150
    bg.configure(text="Inactive")
    assert bg.text == "Inactive"

    # SegmentedButton
    sb = SegmentedButton(root, values=["Daily", "Weekly", "Monthly"], value="Weekly")
    assert sb.value == "Weekly"
    sb.configure(value="Daily")
    assert sb.value == "Daily"

    # Slider & RangeSlider
    sl = Slider(root, value=25.0, from_=0.0, to=100.0)
    assert sl.value == pytest.approx(25.0, abs=0.5)
    sl.configure(value=75.0)
    assert sl.value == pytest.approx(75.0, abs=0.5)

    rsl = RangeSlider(root, lower_value=10.0, upper_value=80.0)
    assert rsl.lower_value == pytest.approx(10.0, abs=0.5)
    assert rsl.upper_value == pytest.approx(80.0, abs=0.5)
    rsl.configure(lower_value=20.0, upper_value=90.0)
    assert rsl.lower_value == pytest.approx(20.0, abs=0.5)
    assert rsl.upper_value == pytest.approx(90.0, abs=0.5)

    # Progressbar & CircularProgress & Gauge
    pb = Progressbar(root, value=30.0, maximum=100.0)
    assert pb.get() == pytest.approx(30.0, abs=0.5)
    pb.step(10.0)
    assert pb.get() == pytest.approx(40.0, abs=0.5)

    cp = CircularProgress(root, value=50.0)
    assert cp.get() == pytest.approx(50.0, abs=0.5)
    cp.step(5.0)
    assert cp.get() == pytest.approx(55.0, abs=0.5)

    gg = Gauge(root, value=45.0)
    assert gg.get() == pytest.approx(45.0, abs=0.5)

    # ComboBox & OptionMenu
    combo = ComboBox(root, values=["First", "Second"], value="First")
    assert combo.get() == "First"
    combo.configure(value="Second")
    assert combo.get() == "Second"

    op = OptionMenu(root, values=["A", "B"], value="A")
    assert op.get() == "A"

    # Entry & SearchEntry & TextBox
    ent = Entry(root, placeholder="Type here...", text="Init Text")
    assert ent.text == "Init Text"
    ent.configure(text="Changed Text", state="disabled")
    assert ent.text == "Changed Text"
    assert ent.is_disabled is True

    se = SearchEntry(root, placeholder="Search items...")
    assert se.placeholder == "Search items..."

    tb_w = TextBox(root, width=300, height=120)
    assert tb_w.width == 300
    assert tb_w.height == 120
    tb_w.configure(state="disabled")
    assert tb_w.is_disabled is True

    # Frame & Card
    frm = Frame(root, width=220, height=160, min_width=150, max_width=400)
    assert frm.width == 220
    assert frm.height == 160
    assert frm.min_width == 150
    assert frm.max_width == 400

    crd = Card(root, width=250, height=180, min_width=180, max_width=500)
    assert crd.width == 250
    assert crd.height == 180


def test_switch_and_checkbox_checked_uniformity(root):
    set_theme("dark")

    calls = []
    sw = Switch(root, checked=True, command=lambda val: calls.append(val))
    assert sw.checked is True
    assert sw.is_checked is True

    sw.toggle()
    assert sw.checked is False
    assert calls == [False]

    sw["checked"] = True
    assert sw.checked is True

    sw.configure(checked=False)
    assert sw.checked is False
    sw.destroy()

    cb_calls = []
    cb = Checkbox(root, checked=True, command=lambda val: cb_calls.append(val))
    assert cb.checked is True
    assert cb.is_checked is True

    cb.toggle()
    assert cb.checked is False
    assert cb_calls == [False]
    cb.destroy()


def test_table_demo_toggles_integration():
    from examples.table_demo import TableDemoApp

    app = TableDemoApp()
    try:
        assert app.table.zebra_striping is True
        assert app.sw_zebra.is_checked is True
        assert app.table.multi_select is False
        assert app.sw_multi.is_checked is False

        # Toggle zebra switch off
        app.sw_zebra.toggle()
        assert app.sw_zebra.is_checked is False
        assert app.table.zebra_striping is False
        assert "disabled" in app.lbl_status.cget("text")

        # Toggle zebra switch back on
        app.sw_zebra.toggle()
        assert app.sw_zebra.is_checked is True
        assert app.table.zebra_striping is True
        assert "enabled" in app.lbl_status.cget("text")

        # Toggle multiselect switch on
        app.sw_multi.toggle()
        assert app.sw_multi.is_checked is True
        assert app.table.multi_select is True
        assert "Multi-Select" in app.lbl_status.cget("text")

        # Toggle multiselect switch off
        app.sw_multi.toggle()
        assert app.sw_multi.is_checked is False
        assert app.table.multi_select is False
        assert "Single-Select" in app.lbl_status.cget("text")
    finally:
        app.destroy()

