from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
)

from pycronk.services.models import HistoryEntry, Kind, Operation, Status
from pycronk.services.ports import HistoryRepository
from pycronk.ui.pages.base import PageWidget
from pycronk.ui.pages.files_page import human_size
from pycronk.ui.theme.icons import IconProvider
from pycronk.ui.widgets.segmented_control import SegmentedControl

_FILTERS: tuple[Kind | None, ...] = (None, Kind.TEXT, Kind.FILE)
_OPERATIONS = {Operation.ENCRYPT: "Cifrado", Operation.DECRYPT: "Descifrado"}
_KINDS = {Kind.TEXT: "Texto", Kind.FILE: "Archivo"}
_STATUS = {
    Status.OK: ("Correcto", "success", "success"),
    Status.ERROR: ("Error", "error", "danger"),
    Status.CANCELLED: ("Cancelado", "close", "secondary"),
}
PAGE_SIZE = 500


class HistoryPage(PageWidget):
    page_id = "history"
    title = "Historial"
    icon = "history"
    subtitle = "Solo se guardan metadatos: nunca contraseñas, textos ni contenido de archivos."

    def __init__(self, history: HistoryRepository, icons: IconProvider) -> None:
        super().__init__()
        self._history = history
        self._icons = icons

        top = QHBoxLayout()
        self.filter = SegmentedControl(["Todo", "Texto", "Archivos"])
        self.filter.changed.connect(lambda _i: self.reload())
        top.addWidget(self.filter)
        top.addStretch(1)
        self.delete_button = QPushButton("Eliminar")
        icons.bind(self.delete_button, "trash")
        self.delete_button.clicked.connect(self.delete_selected)
        self.clear_button = QPushButton("Vaciar historial")
        self.clear_button.clicked.connect(self.clear)
        top.addWidget(self.delete_button)
        top.addWidget(self.clear_button)
        self.content.addLayout(top)

        self.table = QTreeWidget()
        self.table.setRootIsDecorated(False)
        self.table.setAlternatingRowColors(True)
        self.table.setUniformRowHeights(True)
        self.table.setHeaderLabels(
            ["Fecha", "Operación", "Tipo", "Nombre", "Tamaño", "Duración", "Estado"]
        )
        header = self.table.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(380)
        self.table.itemSelectionChanged.connect(self._refresh_buttons)
        self.content.addWidget(self.table, 1)
        self.reload()

    def on_activated(self) -> None:
        self.reload()

    def reload(self) -> None:
        kind = _FILTERS[self.filter.current_index()]
        self.table.clear()
        for entry in self._history.list(limit=PAGE_SIZE, kind=kind):
            self.table.addTopLevelItem(self._item(entry))
        self._refresh_buttons()

    def _item(self, entry: HistoryEntry) -> QTreeWidgetItem:
        status_text, icon, role = _STATUS[entry.status]
        item = QTreeWidgetItem(
            [
                entry.created_at.astimezone().strftime("%d/%m/%Y %H:%M"),
                _OPERATIONS[entry.operation],
                _KINDS[entry.kind],
                entry.label,
                human_size(entry.input_size),
                f"{entry.duration_ms} ms",
                status_text,
            ]
        )
        item.setIcon(6, self._icons.icon(icon, role))
        if entry.output_path:
            item.setToolTip(3, entry.output_path)
        item.setData(0, 256, entry.id)  # Qt.UserRole
        return item

    def _refresh_buttons(self) -> None:
        self.delete_button.setEnabled(bool(self.table.selectedItems()))
        self.clear_button.setEnabled(self.table.topLevelItemCount() > 0)

    def delete_selected(self) -> None:
        for item in self.table.selectedItems():
            self._history.delete(int(item.data(0, 256)))
        self.reload()

    def clear(self) -> None:
        # Confirmación modal solo para lo irreversible y masivo.
        answer = QMessageBox.question(
            self, "Vaciar historial", "Se eliminarán todas las entradas. ¿Continuar?"
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._history.clear()
            self.reload()
