from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class Card(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(16, 14, 16, 14)
        self.body.setSpacing(10)


class GroupedRow(QWidget):
    def __init__(self, label: str, control: QWidget | None, hint: str) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 12, 10)
        layout.setSpacing(12)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addWidget(QLabel(label))
        # La ayuda existe siempre (oculta si está vacía) para poder actualizarla después, p. ej.
        # la carpeta de salida elegida.
        self.hint = QLabel(hint)
        self.hint.setObjectName("Hint")
        self.hint.setWordWrap(True)
        self.hint.setVisible(bool(hint))
        texts.addWidget(self.hint)
        layout.addLayout(texts, 1)
        if control is not None:
            layout.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)

    def set_hint(self, text: str) -> None:
        self.hint.setText(text)
        self.hint.setVisible(bool(text))


class GroupedList(QFrame):
    """Filas dentro de una tarjeta con separadores internos, como Ajustes del Sistema de macOS."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._rows = 0

    def add_row(self, label: str, control: QWidget | None = None, hint: str = "") -> GroupedRow:
        if self._rows:
            separator = QFrame()
            separator.setObjectName("RowSeparator")
            wrapper = QHBoxLayout()
            # El separador arranca con sangría, igual que en macOS, para que las filas se lean
            # como un grupo y no como tarjetas apiladas.
            wrapper.setContentsMargins(16, 0, 0, 0)
            wrapper.addWidget(separator)
            self._layout.addLayout(wrapper)
        row = GroupedRow(label, control, hint)
        self._layout.addWidget(row)
        self._rows += 1
        return row
