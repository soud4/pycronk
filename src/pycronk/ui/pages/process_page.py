from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from pycronk.services.models import Operation
from pycronk.ui.pages.base import PageWidget
from pycronk.ui.state import TraceSnapshot, TraceStore
from pycronk.ui.theme.icons import IconProvider
from pycronk.ui.widgets.grouped_list import Card
from pycronk.ui.widgets.layer_card import LayerCard

# Textos didácticos por id de capa. Viven en la UI y no en el núcleo porque son presentación; una
# capa nueva sin texto aquí se muestra igual, solo que sin explicación.
DESCRIPTIONS = {
    "gf2-matrix": (
        "Cada bloque de 6 bits x se multiplica por una matriz invertible M = L·U sobre GF(2). "
        "Como solo hay 64 bloques posibles, la operación equivale a una tabla de sustitución."
    ),
    "vigenere-lcg": (
        "A cada símbolo se le suma (mod 64) un valor del keystream generado por un LCG sembrado "
        "con la contraseña del keystream. Rompe la relación fija bloque → símbolo de la capa 1."
    ),
    "fisher-yates": (
        "La misma secuencia LCG, continuada, genera una permutación π con Fisher-Yates: los "
        "símbolos cambian de posición sin cambiar de valor."
    ),
}


class ProcessPage(PageWidget):
    page_id = "process"
    title = "Proceso"
    icon = "process"
    subtitle = (
        "Recorrido capa por capa de la última operación de texto (hasta 4 KB). Muestra el primer "
        "bloque de datos tal como lo transforma cada capa."
    )

    def __init__(self, traces: TraceStore, icons: IconProvider) -> None:
        super().__init__()
        self._icons = icons
        self._area = QWidget()
        self._area_layout = QVBoxLayout(self._area)
        self._area_layout.setContentsMargins(0, 0, 0, 0)
        self._area_layout.setSpacing(12)
        self.content.addWidget(self._area)
        self.content.addStretch(1)
        traces.changed.connect(self.show_snapshot)
        self.show_snapshot(traces.latest)

    def _clear(self) -> None:
        while self._area_layout.count():
            item = self._area_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                # deleteLater espera al bucle de eventos; ocultarlo ya evita que se vea un
                # instante por debajo de las tarjetas nuevas.
                widget.hide()
                widget.deleteLater()

    def _empty_state(self) -> None:
        card = Card()
        card.body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.body.setContentsMargins(24, 40, 24, 40)
        icon = QLabel()
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icons.bind_pixmap(icon, "process", "secondary", 36)
        title = QLabel("Todavía no hay nada que mostrar")
        title.setObjectName("EmptyTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel("Cifra o descifra un texto en la sección Texto y vuelve aquí.")
        hint.setObjectName("Hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for widget in (icon, title, hint):
            card.body.addWidget(widget)
        self._area_layout.addWidget(card)

    def show_snapshot(self, snapshot: TraceSnapshot | None) -> None:
        self._clear()
        trace = snapshot.trace if snapshot is not None else None
        if snapshot is None or trace is None or trace.input_symbols is None:
            self._empty_state()
            return
        input_symbols = trace.input_symbols
        encrypt = snapshot.operation is Operation.ENCRYPT

        summary = LayerCard(
            "Cifrado" if encrypt else "Descifrado",
            f"Longitud original: {trace.length_bytes} bytes. Todas las capas trabajan sobre "
            "símbolos de 6 bits (0–63).",
        )
        summary.add_value("Entrada", snapshot.input_text)
        self._area_layout.addWidget(summary)

        first = LayerCard(
            "Símbolos de entrada",
            "Longitud (8 bytes) + mensaje en UTF-8, agrupados de a 6 bits."
            if encrypt
            else "Bytes del cifrado agrupados de a 6 bits.",
        )
        first.add_value("Símbolos", input_symbols)
        self._area_layout.addWidget(first)

        for step in trace.steps:
            title = step.title if encrypt else f"Inversa de {step.title[0].lower()}{step.title[1:]}"
            card = LayerCard(title, DESCRIPTIONS.get(step.layer_id, ""))
            for label, value in step.details.items():
                card.add_value(label, value)
            card.add_value("Resultado", step.output)
            self._area_layout.addWidget(card)

        final = LayerCard(
            "Salida",
            "Los símbolos se empaquetan en bytes, se antepone la cabecera del contenedor y el "
            "conjunto se codifica en Base64 con el prefijo PCRK1:."
            if encrypt
            else "Los símbolos se reagrupan en bytes, se descarta la cabecera de longitud y se "
            "decodifica como UTF-8.",
        )
        final.add_value("Texto", snapshot.output_text)
        self._area_layout.addWidget(final)
