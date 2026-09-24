import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget

from pycronk.core.trace import DetailValue
from pycronk.ui.widgets.grouped_list import Card

# Una fila de símbolos más larga no aporta nada a la explicación y hace lento el layout.
MAX_VALUES = 96


def format_value(value: DetailValue) -> str:
    if isinstance(value, str):
        return value
    values = np.asarray(value).tolist()
    shown = ", ".join(str(v) for v in values[:MAX_VALUES])
    suffix = f", …  ({len(values)} en total)" if len(values) > MAX_VALUES else f"  ({len(values)})"
    return f"[{shown}]{suffix}"


class LayerCard(Card):
    def __init__(self, title: str, description: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        heading = QLabel(title)
        heading.setObjectName("EmptyTitle")
        self.body.addWidget(heading)
        if description:
            hint = QLabel(description)
            hint.setObjectName("Hint")
            hint.setWordWrap(True)
            self.body.addWidget(hint)

    def add_value(self, label: str, value: DetailValue) -> None:
        caption = QLabel(label)
        caption.setObjectName("SectionTitle")
        text = QLabel(format_value(value))
        text.setObjectName("Mono")
        text.setWordWrap(True)
        # Sin esto, QLabel con ajuste de línea reclama como ancho mínimo el de su palabra más
        # larga (p. ej. un Base64 entero) y empuja la página fuera de la ventana.
        text.setMinimumWidth(1)
        text.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.body.addWidget(caption)
        self.body.addWidget(text)
