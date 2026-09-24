from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from pycronk.ui.theme.icons import IconProvider


class Sidebar(QWidget):
    page_selected = Signal(int)

    def __init__(self, icons: IconProvider, title: str, footer: str) -> None:
        super().__init__()
        self._icons = icons
        self.setObjectName("Sidebar")
        self.setFixedWidth(210)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 12)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("SidebarTitle")
        self.list = QListWidget()
        self.list.setObjectName("SidebarList")
        self.list.setIconSize(QSize(18, 18))
        self.list.currentRowChanged.connect(self.page_selected)
        version = QLabel(footer)
        version.setObjectName("SidebarFooter")
        layout.addWidget(heading)
        layout.addWidget(self.list, 1)
        layout.addWidget(version)
        self._items: list[QListWidgetItem] = []

    def add_entry(self, title: str, icon: str) -> None:
        item = QListWidgetItem(title)
        self._icons.bind(item, icon, "accent")
        self.list.addItem(item)
        self._items.append(item)

    def select(self, index: int) -> None:
        self.list.setCurrentRow(index)
