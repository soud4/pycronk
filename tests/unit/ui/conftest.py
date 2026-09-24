import pytest

from pycronk.services.settings import Theme
from pycronk.ui.theme.builder import ThemeManager
from pycronk.ui.theme.icons import QtAwesomeIconProvider


@pytest.fixture
def theme(qapp) -> ThemeManager:
    manager = ThemeManager(qapp, "monospace")
    manager.apply(Theme.LIGHT)
    return manager


@pytest.fixture
def icons(theme) -> QtAwesomeIconProvider:
    return QtAwesomeIconProvider(theme)
