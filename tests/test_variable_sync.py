import tkinter as tk
import pytest
from tkblend.widgets.base import VariableSync, Widget
from tkblend.widgets.selection import Switch, Checkbutton, Radiobutton
from tkblend.widgets.combobox import OptionMenu


@pytest.fixture
def root():
    try:
        r = tk.Tk()
        r.withdraw()
        yield r
        r.destroy()
    except tk.TclError:
        pytest.skip("Tkinter display not available")


def test_variable_sync_standalone_no_variable():
    """VariableSync functions properly without a Tkinter variable."""
    changes = []
    sync = VariableSync(
        variable=None,
        initial_value=42,
        on_change=lambda v: changes.append(v),
        type_caster=int,
    )
    assert sync.get() == 42
    assert sync.has_variable is False
    assert sync.variable is None

    sync.set(100)
    assert sync.get() == 100
    # Internal set should not trigger on_change listener
    assert len(changes) == 0

    sync.cleanup()


def test_variable_sync_with_tk_variable(root):
    """VariableSync synchronizes bidirectionally with Tk variable."""
    var = tk.StringVar(value="initial")
    changes = []

    sync = VariableSync(
        variable=var,
        initial_value="fallback",
        on_change=lambda v: changes.append(v),
        type_caster=str,
    )
    assert sync.has_variable is True
    assert sync.variable is var
    assert sync.get() == "initial"

    # External variable modification triggers on_change
    var.set("updated")
    assert sync.get() == "updated"
    assert changes == ["updated"]

    # Programmatic set through VariableSync updates var without redundant trace echo
    sync.set("from_sync")
    assert var.get() == "from_sync"
    assert sync.get() == "from_sync"
    # No extra item appended to changes due to suppress_trace
    assert changes == ["updated"]

    # Cleanup unbinds trace
    sync.cleanup()
    assert sync._trace_id is None
    var.set("after_cleanup")
    assert len(changes) == 1


def test_variable_sync_dynamic_variable_rebinding(root):
    """VariableSync supports rebinding variables dynamically."""
    var1 = tk.IntVar(value=10)
    var2 = tk.IntVar(value=20)
    changes = []

    sync = VariableSync(
        variable=var1,
        on_change=lambda v: changes.append(v),
        type_caster=int,
    )
    assert sync.get() == 10

    var1.set(15)
    assert changes == [15]

    # Rebind to var2
    sync.set_variable(var2)
    assert sync.get() == 20

    # Old var changes should no longer trigger callback
    var1.set(99)
    assert changes == [15]

    # New var changes trigger callback
    var2.set(25)
    assert changes == [15, 25]

    # Unbind variable completely
    sync.set_variable(None)
    assert sync.has_variable is False
    var2.set(30)
    assert changes == [15, 25]


def test_switch_variable_sync(root):
    """Switch interacts cleanly with VariableSync."""
    var = tk.BooleanVar(value=True)
    sw = Switch(root, variable=var)
    sw.pack()
    root.update()

    assert sw.is_on is True
    assert sw._var_sync.has_variable is True

    # Widget toggling
    sw.toggle()
    assert sw.is_on is False
    assert var.get() is False

    # Variable updating
    var.set(True)
    assert sw.is_on is True

    # Property setter
    sw.is_on = False
    assert var.get() is False

    sw.destroy()
    # Trace cleaned up on destroy
    assert sw._var_sync._trace_id is None


def test_checkbutton_variable_sync(root):
    """Checkbutton interacts cleanly with VariableSync."""
    var = tk.BooleanVar(value=False)
    cb = Checkbutton(root, text="Test Check", variable=var)
    cb.pack()
    root.update()

    assert cb.get() is False
    assert cb.checked is False

    cb.toggle()
    assert cb.checked is True
    assert var.get() is True

    var.set(False)
    assert cb.checked is False
    assert cb.get() is False

    cb.set(True)
    assert var.get() is True

    cb.destroy()
    assert cb._var_sync._trace_id is None


def test_radiobutton_variable_sync(root):
    """Radiobutton interacts cleanly with VariableSync."""
    var = tk.StringVar(value="B")
    r1 = Radiobutton(root, text="Option A", value="A", variable=var)
    r2 = Radiobutton(root, text="Option B", value="B", variable=var)
    r1.pack()
    r2.pack()
    root.update()

    assert r1.selected is False
    assert r2.selected is True

    # Selecting r1 updates variable and deselects r2
    r1.selected = True
    assert var.get() == "A"
    assert r2.selected is False

    # Changing variable selects r2 and deselects r1
    var.set("B")
    assert r1.selected is False
    assert r2.selected is True

    r1.destroy()
    r2.destroy()


def test_option_menu_variable_sync(root):
    """OptionMenu interacts cleanly with VariableSync."""
    var = tk.StringVar(value="Option 2")
    menu = OptionMenu(
        root,
        values=["Option 1", "Option 2", "Option 3"],
        variable=var,
    )
    menu.pack()
    root.update()

    assert menu.get() == "Option 2"

    menu.set("Option 3")
    assert var.get() == "Option 3"

    var.set("Option 1")
    assert menu.get() == "Option 1"

    menu.destroy()
    assert menu._var_sync._trace_id is None
