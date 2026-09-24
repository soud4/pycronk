import numpy as np
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QLabel, QLineEdit

from pycronk.ui.pages.files_page import human_size
from pycronk.ui.widgets.banner import Banner
from pycronk.ui.widgets.grouped_list import GroupedList
from pycronk.ui.widgets.keys_form import KeysForm
from pycronk.ui.widgets.layer_card import MAX_VALUES, format_value
from pycronk.ui.widgets.password_field import PasswordField
from pycronk.ui.widgets.segmented_control import SegmentedControl
from pycronk.ui.widgets.switch import Switch


def test_password_field_toggles_visibility(qtbot, icons):
    field = PasswordField(icons, "clave")
    qtbot.addWidget(field)
    assert field.echoMode() == QLineEdit.EchoMode.Password
    field.toggle_action.trigger()
    assert field.revealed
    assert field.toggle_action.toolTip() == "Ocultar contraseña"
    field.toggle_action.trigger()
    assert not field.revealed


def test_segmented_control_programmatic(qtbot):
    control = SegmentedControl(["A", "B", "C"])
    qtbot.addWidget(control)
    with qtbot.waitSignal(control.changed) as blocker:
        control.set_current_index(2)
    assert blocker.args == [2]
    with qtbot.assertNotEmitted(control.changed):
        control.set_current_index(0, notify=False)
        control.set_current_index(9)
        control.set_current_index(0)
    assert control.current_index() == 0


def test_segmented_control_mouse_and_keyboard(qtbot):
    control = SegmentedControl(["A", "B"])
    qtbot.addWidget(control)
    control.resize(200, 28)
    with qtbot.waitSignal(control.changed) as blocker:
        qtbot.mouseClick(control, Qt.MouseButton.LeftButton, pos=QPoint(150, 14))
    assert blocker.args == [1]
    qtbot.keyClick(control, Qt.Key.Key_Left)
    assert control.current_index() == 0


def test_switch_toggles_and_sets_offset_without_animation(qtbot):
    switch = Switch()
    qtbot.addWidget(switch)
    switch.setChecked(True)
    assert switch.isChecked()
    assert switch.offset == 1.0
    with qtbot.waitSignal(switch.toggled) as blocker:
        qtbot.mouseClick(switch, Qt.MouseButton.LeftButton)
    assert blocker.args == [False]


def test_grouped_list_rows_and_hints(qtbot):
    group = GroupedList()
    qtbot.addWidget(group)
    first = group.add_row("Uno")
    second = group.add_row("Dos", QLabel("x"), "ayuda")
    group.show()
    assert first.hint.isHidden()
    assert second.hint.isVisible() and second.hint.text() == "ayuda"
    first.set_hint("nueva")
    assert first.hint.isVisible()


def test_banner_kinds_and_timeout(qtbot, icons):
    banner = Banner(icons)
    qtbot.addWidget(banner)
    assert banner.isHidden()
    banner.show_message("error", "falló")
    assert banner.property("kind") == "error"
    assert banner.message() == "falló"
    assert banner.isVisible()
    banner.show_message("success", "ok", timeout_ms=10)
    qtbot.waitUntil(banner.isHidden, timeout=1000)


def test_keys_form_requires_both(qtbot, icons):
    form = KeysForm(icons)
    qtbot.addWidget(form)
    assert form.keys() is None
    form.matrix.setText("a")
    assert form.keys() is None
    form.keystream.setText("b")
    keys = form.keys()
    assert keys is not None and (keys.matrix, keys.keystream) == ("a", "b")


def test_format_value():
    assert format_value("texto") == "texto"
    assert format_value(np.array([1, 2, 3], dtype=np.uint8)) == "[1, 2, 3]  (3)"
    long = format_value(np.arange(MAX_VALUES + 5))
    assert long.endswith(f"({MAX_VALUES + 5} en total)")
    assert f", {MAX_VALUES}," not in long


def test_human_size():
    assert human_size(0) == "0 B"
    assert human_size(1536) == "1.5 KB"
    assert human_size(5 * 1024**3) == "5.0 GB"
