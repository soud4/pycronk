from PySide6.QtWidgets import QWidget

from pycronk.ui.main_window import MainWindow
from pycronk.ui.state import Navigator


class FakePage(QWidget):
    def __init__(self, page_id: str) -> None:
        super().__init__()
        self.page_id = page_id
        self.title = page_id.title()
        self.icon = "text"
        self.activations = 0

    def widget(self) -> QWidget:
        return self

    def on_activated(self) -> None:
        self.activations += 1


def test_pages_are_listed_and_first_is_active(qtbot, icons):
    pages = [FakePage("a"), FakePage("b")]
    window = MainWindow(pages, icons, Navigator(), "1.0")
    qtbot.addWidget(window)
    assert window.sidebar.list.count() == 2
    assert window.stack.currentWidget() is pages[0]
    assert pages[0].activations == 1


def test_navigation_by_id(qtbot, icons):
    pages = [FakePage("a"), FakePage("b")]
    navigator = Navigator()
    window = MainWindow(pages, icons, navigator, "1.0")
    qtbot.addWidget(window)
    navigator.go("b")
    assert window.stack.currentWidget() is pages[1]
    assert pages[1].activations == 1
    navigator.go("no-existe")
    assert window.stack.currentWidget() is pages[1]
