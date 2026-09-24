from PySide6.QtWidgets import QWidget

from pycronk.core.interfaces import Keys
from pycronk.ui.theme.icons import IconProvider
from pycronk.ui.widgets.grouped_list import GroupedList
from pycronk.ui.widgets.password_field import PasswordField


class KeysForm(GroupedList):
    def __init__(self, icons: IconProvider, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.matrix = PasswordField(icons, "Contraseña de la matriz")
        self.keystream = PasswordField(icons, "Contraseña del keystream")
        for field in (self.matrix, self.keystream):
            field.setMinimumWidth(260)
        self.add_row("Matriz", self.matrix, "Construye la matriz de la capa 1.")
        self.add_row("Keystream", self.keystream, "Alimenta el generador de las capas 2 y 3.")

    def keys(self) -> Keys | None:
        matrix, keystream = self.matrix.text(), self.keystream.text()
        if not matrix or not keystream:
            return None
        return Keys(matrix, keystream)
