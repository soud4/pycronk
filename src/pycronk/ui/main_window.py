from collections.abc import Sequence

from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from pycronk.ui.pages.base import Page
from pycronk.ui.state import Navigator
from pycronk.ui.theme.icons import IconProvider
from pycronk.ui.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(
        self,
        pages: Sequence[Page],
        icons: IconProvider,
        navigator: Navigator,
        version: str,
    ) -> None:
        super().__init__()
        self.setWindowTitle("pycronk")
        self.resize(1040, 760)
        self.setMinimumSize(820, 600)
        self._pages = list(pages)

        root = QWidget()
        root.setObjectName("Root")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar(icons, "pycronk", f"Versión {version}")
        self.stack = QStackedWidget()
        self.stack.setObjectName("Content")
        for page in self._pages:
            self.sidebar.add_entry(page.title, page.icon)
            self.stack.addWidget(page.widget())
        self.sidebar.page_selected.connect(self._show)
        navigator.requested.connect(self.show_page)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        if self._pages:
            self.sidebar.select(0)

    def _show(self, index: int) -> None:
        if 0 <= index < len(self._pages):
            self.stack.setCurrentIndex(index)
            self._pages[index].on_activated()

    def show_page(self, page_id: str) -> None:
        for index, page in enumerate(self._pages):
            if page.page_id == page_id:
                self.sidebar.select(index)
                return
