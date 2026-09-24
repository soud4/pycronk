from typing import Protocol

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class Page(Protocol):
    """Entrada del sidebar. `MainWindow` solo conoce este protocolo: agregar o quitar una página
    es editar la lista en `app.py`."""

    page_id: str
    title: str
    icon: str

    def widget(self) -> QWidget: ...

    def on_activated(self) -> None: ...


class PageWidget(QWidget):
    """Base práctica para páginas: título, subtítulo y cuerpo con scroll."""

    page_id = ""
    title = ""
    icon = ""
    subtitle = ""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Page")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("PageScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("PageBody")
        self.content = QVBoxLayout(body)
        self.content.setContentsMargins(32, 28, 32, 28)
        self.content.setSpacing(16)
        heading = QLabel(self.title)
        heading.setObjectName("PageTitle")
        self.content.addWidget(heading)
        if self.subtitle:
            sub = QLabel(self.subtitle)
            sub.setObjectName("PageSubtitle")
            sub.setWordWrap(True)
            self.content.addWidget(sub)
        scroll.setWidget(body)
        outer.addWidget(scroll)

    def section(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionTitle")
        self.content.addWidget(label)
        return label

    def widget(self) -> QWidget:
        return self

    def on_activated(self) -> None:
        pass
