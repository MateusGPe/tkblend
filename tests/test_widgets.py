import tkinter as tk
import pytest
import tkblend as tb
from tkblend import (
    Button,
    Switch,
    Checkbox,
    Radio,
    Slider,
    Progressbar,
    Badge,
    Card,
    Label,
    Frame,
    CircularProgress,
    Gauge,
    SegmentedButton,
    RangeSlider,
    Sparkline,
    ComboBox,
    OptionMenu,
    Entry,
    SearchEntry,
    TextBox,
    ScrollableFrame,
    VectorScrollbar,
    Tabview,
    Table,
    set_theme,
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


def test_button_widget(root):
    set_theme("dark")
    clicked = []
    btn = Button(root, text="Click", command=lambda: clicked.append(True), width=120, height=36)
    btn.pack()
    root.update_idletasks()

    assert btn.text == "Click"
    assert btn.widget_class == "button"
    btn.invoke()
    assert len(clicked) == 1

    btn.text = "Updated"
    assert btn.text == "Updated"

    # Variant tests
    assert btn.variant == "default"
    btn.variant = "primary"
    assert btn.variant == "primary"
    assert btn.has_class("btn-primary")

    btn.variant = "outline"
    assert btn.variant == "outline"
    assert not btn.has_class("btn-primary")
    assert btn.has_class("btn-outline")

    btn2 = Button(root, text="Tonal", variant="tonal")
    assert btn2.variant == "tonal"
    assert btn2.has_class("btn-tonal")
    btn2.destroy()


def test_switch_widget(root):
    set_theme("dark")
    sw_var = tk.BooleanVar(value=False)
    sw = Switch(root, text="Toggle", variable=sw_var, width=100, height=30)
    sw.pack()
    root.update_idletasks()

    assert not sw.is_checked
    sw.toggle()
    assert sw.is_checked
    assert sw_var.get() is True

    sw.toggle()
    assert not sw.is_checked
    assert sw_var.get() is False


def test_checkbox_widget(root):
    set_theme("dark")
    cb_var = tk.BooleanVar(value=True)
    cb = Checkbox(root, text="Agree", variable=cb_var, width=120, height=30)
    cb.pack()
    root.update_idletasks()

    assert cb.is_checked
    cb.toggle()
    assert not cb.is_checked
    assert cb_var.get() is False


def test_radio_widget(root):
    set_theme("dark")
    r_var = tk.StringVar(value="opt1")
    r1 = Radio(root, text="Option 1", value="opt1", variable=r_var)
    r2 = Radio(root, text="Option 2", value="opt2", variable=r_var)
    r1.pack()
    r2.pack()
    root.update_idletasks()

    assert r1.is_checked
    assert not r2.is_checked

    r2.select()
    assert r_var.get() == "opt2"
    assert r2.is_checked


def test_slider_widget(root):
    set_theme("dark")
    sl = Slider(root, from_=0.0, to=100.0, value=25.0, width=150, height=24)
    sl.pack()
    root.update_idletasks()

    assert sl.get() == pytest.approx(25.0, abs=1.0)
    sl.set(80.0)
    assert sl.get() == pytest.approx(80.0, abs=1.0)


def test_progressbar_widget(root):
    set_theme("dark")
    pb = Progressbar(root, value=10.0, maximum=100.0, width=150, height=10)
    pb.pack()
    root.update_idletasks()

    assert pb.get() == pytest.approx(10.0, abs=0.5)
    pb.step(15.0)
    assert pb.get() == pytest.approx(25.0, abs=0.5)


def test_badge_and_label_and_card(root):
    set_theme("dark")
    card = Card(root, width=200, height=150)
    card.pack()
    badge = Badge(card, text="Status", width=60, height=24)
    badge.pack()
    lbl = Label(card, text="Information", width=100, height=26)
    lbl.pack()
    root.update_idletasks()

    assert badge.text == "Status"
    assert lbl.text == "Information"


def test_frame_widget(root):
    set_theme("dark")
    frame = Frame(root, width=180, height=120, corner_radius=12.0, border_width=1.0)
    frame.pack()
    root.update_idletasks()
    assert frame.corner_radius == 12.0
    assert frame.border_width == 1.0


def test_circular_progress_and_gauge(root):
    set_theme("dark")
    cp = CircularProgress(root, size=100, value=50.0, min_value=0.0, max_value=100.0)
    cp.pack()
    root.update_idletasks()
    assert cp.get() == pytest.approx(50.0, abs=0.5)
    cp.step(10.0)
    assert cp.get() == pytest.approx(60.0, abs=0.5)

    g = Gauge(root, size=120, value=75.0, title="CPU", unit="%")
    g.pack()
    root.update_idletasks()
    assert g.get() == pytest.approx(75.0, abs=0.5)
    assert g.title == "CPU"


def test_segmented_button(root):
    set_theme("dark")
    clicked = []
    sb = SegmentedButton(
        root,
        values=["Day", "Week", "Month"],
        selected_index=0,
        command=lambda v: clicked.append(v),
        width=210,
        height=36,
    )
    sb.pack()
    root.update_idletasks()
    assert sb.get() == "Day"
    sb.select(1)
    assert sb.get() == "Week"
    assert len(clicked) == 1
    assert clicked[0] == "Week"


def test_range_slider(root):
    set_theme("dark")
    rs = RangeSlider(root, from_=0.0, to=100.0, values=(20.0, 80.0), width=180, height=32)
    rs.pack()
    root.update_idletasks()
    low, high = rs.get()
    assert low == pytest.approx(20.0, abs=1.0)
    assert high == pytest.approx(80.0, abs=1.0)
    rs.set(30.0, 70.0)
    low, high = rs.get()
    assert low == pytest.approx(30.0, abs=1.0)
    assert high == pytest.approx(70.0, abs=1.0)


def test_sparkline(root):
    set_theme("dark")
    sp = Sparkline(root, data=[5.0, 15.0, 8.0, 30.0], width=100, height=30)
    sp.pack()
    root.update_idletasks()
    assert sp.data == [5.0, 15.0, 8.0, 30.0]
    sp.set_data([1.0, 2.0, 3.0])
    assert sp.data == [1.0, 2.0, 3.0]


def test_combobox(root):
    set_theme("dark")
    cb = ComboBox(root, values=["Alpha", "Beta", "Gamma"], value="Beta", width=140, height=36)
    cb.pack()
    root.update_idletasks()
    assert cb.get() == "Beta"
    cb.set("Gamma")
    assert cb.get() == "Gamma"
    assert cb.values == ["Alpha", "Beta", "Gamma"]


def test_entry_and_textbox(root):
    set_theme("dark")
    entry = Entry(root, text="Hello Vector", width=160, height=36)
    entry.pack()
    root.update_idletasks()
    assert entry.get() == "Hello Vector"
    entry.delete(0, "end")
    entry.insert(0, "Updated")
    assert entry.get() == "Updated"

    search = SearchEntry(root, width=160, height=36)
    search.pack()
    root.update_idletasks()

    tb_widget = TextBox(root, width=200, height=100)
    tb_widget.pack()
    root.update_idletasks()
    tb_widget.insert("1.0", "Multiline text")
    assert "Multiline text" in tb_widget.get()


def test_scrollable_frame_and_scrollbar(root):
    set_theme("dark")
    sf = ScrollableFrame(root, width=200, height=150)
    sf.pack()
    lbl = tk.Label(sf.content, text="Inner Content")
    lbl.pack()
    root.update_idletasks()

    vs = VectorScrollbar(root, width=8, height=80)
    vs.pack()
    vs.set(0.2, 0.6)
    root.update_idletasks()


def test_tabview(root):
    set_theme("dark")
    tv = Tabview(root, width=250, height=180)
    tv.pack()
    page1 = tv.add("Tab 1")
    page2 = tv.add("Tab 2")
    tk.Label(page1, text="Page 1").pack()
    tk.Label(page2, text="Page 2").pack()
    root.update_idletasks()
    assert tv.get() == "Tab 1"
    tv.set("Tab 2")
    assert tv.get() == "Tab 2"


def test_table(root):
    set_theme("dark")
    tbl = Table(
        root,
        columns=["Name", "Role", "Score"],
        data=[
            ["Alice", "Admin", 95],
            ["Bob", "User", 82],
            ["Charlie", "Guest", 68],
        ],
        width=300,
        height=180,
    )
    tbl.pack()
    root.update_idletasks()
    assert len(tbl.data) == 3
    assert tbl.columns == ["Name", "Role", "Score"]
