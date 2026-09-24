from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLineEdit, QWidget

from pycronk.ui.theme.icons import IconProvider


class PasswordField(QLineEdit):
    """El botón de mostrar/ocultar va dentro del campo (acción de QLineEdit), como en macOS, en vez
    de un botón suelto al lado que desalinea los formularios."""

    def __init__(
        self, icons: IconProvider, placeholder: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._icons = icons
        self.setPlaceholderText(placeholder)
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.toggle_action = QAction(self)
        self.toggle_action.setToolTip("Mostrar contraseña")
        self.toggle_action.triggered.connect(self.toggle_visibility)
        self.addAction(self.toggle_action, QLineEdit.ActionPosition.TrailingPosition)
        icons.bind(self.toggle_action, "eye", "secondary")

    @property
    def revealed(self) -> bool:
        return self.echoMode() == QLineEdit.EchoMode.Normal

    def toggle_visibility(self) -> None:
        reveal = not self.revealed
        self.setEchoMode(QLineEdit.EchoMode.Normal if reveal else QLineEdit.EchoMode.Password)
        self._icons.bind(self.toggle_action, "eye_off" if reveal else "eye", "secondary")
        self.toggle_action.setToolTip("Ocultar contraseña" if reveal else "Mostrar contraseña")
