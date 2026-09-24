from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from pycronk.ui.theme.icons import IconProvider

_ICONS = {
    "info": ("info", "accent"),
    "success": ("success", "success"),
    "error": ("error", "danger"),
}


class Banner(QFrame):
    """Mensajes en línea. Se prefieren a QMessageBox porque no interrumpen: el usuario puede
    corregir la contraseña sin cerrar antes un diálogo modal."""

    def __init__(self, icons: IconProvider, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._icons = icons
        self.setObjectName("Banner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(10)
        self._icon = QLabel()
        self._text = QLabel()
        self._text.setWordWrap(True)
        self._text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        close = QPushButton()
        close.setProperty("variant", "plain")
        close.setFixedSize(QSize(24, 24))
        close.setToolTip("Cerrar")
        close.clicked.connect(self.hide)
        icons.bind(close, "close", "secondary")
        layout.addWidget(self._icon, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._text, 1)
        layout.addWidget(close, 0, Qt.AlignmentFlag.AlignTop)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.hide()

    def show_message(self, kind: str, text: str, *, timeout_ms: int = 0) -> None:
        self.setProperty("kind", kind)
        # Qt no recalcula el QSS al cambiar una propiedad dinámica; hay que forzarlo.
        self.style().unpolish(self)
        self.style().polish(self)
        name, role = _ICONS[kind]
        self._icons.bind_pixmap(self._icon, name, role)
        self._text.setText(text)
        self.show()
        if timeout_ms:
            self._timer.start(timeout_ms)
        else:
            self._timer.stop()

    def message(self) -> str:
        return self._text.text()
