import pytest
from PySide6.QtWidgets import QLabel

from pycronk.services.settings import Theme
from pycronk.ui.theme.icons import PHOSPHOR, ROLES


class Recorder:
    def __init__(self) -> None:
        self.icons = []

    def setIcon(self, icon) -> None:
        self.icons.append(icon)


@pytest.mark.parametrize("name", sorted(PHOSPHOR))
def test_every_logical_name_resolves(icons, name):
    for role in ROLES:
        assert not icons.icon(name, role).isNull()


def test_icons_are_cached_per_theme(icons, theme):
    first = icons.icon("copy")
    assert icons.icon("copy") is first
    theme.apply(Theme.DARK)
    assert icons.icon("copy") is not first


def test_bind_reapplies_on_theme_change(icons, theme):
    target = Recorder()
    icons.bind(target, "copy")
    theme.apply(Theme.DARK)
    assert len(target.icons) == 2
    assert target.icons[-1] is icons.icon("copy")


def test_rebinding_replaces_previous_binding(icons, theme):
    target = Recorder()
    icons.bind(target, "eye")
    icons.bind(target, "eye_off")
    theme.apply(Theme.DARK)
    assert len(target.icons) == 3
    assert target.icons[-1] is icons.icon("eye_off")


def test_dead_targets_are_dropped(icons, theme):
    target = Recorder()
    icons.bind(target, "copy")
    del target
    theme.apply(Theme.DARK)  # no debe fallar


def test_bind_pixmap(qtbot, icons):
    label = QLabel()
    qtbot.addWidget(label)
    icons.bind_pixmap(label, "upload", "accent", 32)
    assert not label.pixmap().isNull()
    assert label.pixmap().width() >= 32
