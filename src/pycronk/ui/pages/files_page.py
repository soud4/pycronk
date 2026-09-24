from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from pycronk.core.interfaces import Keys
from pycronk.services.crypto_service import ENCRYPTED_SUFFIX, CryptoService
from pycronk.services.models import Operation
from pycronk.ui.pages.base import PageWidget
from pycronk.ui.pages.text_page import error_text
from pycronk.ui.theme.icons import IconProvider
from pycronk.ui.widgets.banner import Banner
from pycronk.ui.widgets.drop_zone import DropZone
from pycronk.ui.widgets.grouped_list import Card
from pycronk.ui.widgets.keys_form import KeysForm
from pycronk.ui.widgets.segmented_control import SegmentedControl
from pycronk.ui.workers import Task, TaskRunner

_MODES = (Operation.ENCRYPT, Operation.DECRYPT)


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


class FileRow(QWidget):
    def __init__(self, path: Path, icons: IconProvider) -> None:
        super().__init__()
        self.path = path
        self.output: Path | None = None
        self.state = "pending"
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)
        icon = QLabel()
        icons.bind_pixmap(icon, "file", "secondary", 22)
        texts = QVBoxLayout()
        texts.setSpacing(4)
        name = QLabel(path.name)
        self.status = QLabel(human_size(path.stat().st_size) if path.exists() else "")
        self.status.setObjectName("Hint")
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        self.progress.hide()
        texts.addWidget(name)
        texts.addWidget(self.status)
        texts.addWidget(self.progress)
        self.reveal = QPushButton("Mostrar")
        self.reveal.setProperty("variant", "plain")
        icons.bind(self.reveal, "folder", "accent")
        self.reveal.clicked.connect(self._reveal)
        self.reveal.hide()
        layout.addWidget(icon)
        layout.addLayout(texts, 1)
        layout.addWidget(self.reveal)

    def start(self) -> None:
        self.state = "running"
        self.status.setText("Procesando…")
        self.progress.setValue(0)
        self.progress.show()

    def set_progress(self, fraction: float) -> None:
        self.progress.setValue(round(fraction * 1000))

    def finish(self, output: Path) -> None:
        self.state = "done"
        self.output = output
        self.progress.hide()
        self.status.setText(f"Listo → {output.name}")
        self.reveal.show()

    def fail(self, message: str) -> None:
        self.state = "error"
        self.progress.hide()
        self.status.setText(message)

    def cancel(self) -> None:
        self.state = "cancelled"
        self.progress.hide()
        self.status.setText("Cancelado")

    def _reveal(self) -> None:
        if self.output is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output.parent)))


class FilesPage(PageWidget):
    page_id = "files"
    title = "Archivos"
    icon = "files"
    subtitle = (
        "Cifra cualquier archivo, del tamaño que sea. El resultado se guarda junto al original "
        f"con la extensión {ENCRYPTED_SUFFIX}, o en la carpeta elegida en Ajustes."
    )

    def __init__(self, service: CryptoService, icons: IconProvider, runner: TaskRunner) -> None:
        super().__init__()
        self._service = service
        self._icons = icons
        self._runner = runner
        self._rows: list[FileRow] = []
        self._current: tuple[FileRow, Task] | None = None
        self._keys: Keys | None = None
        self._operation = Operation.ENCRYPT

        self.section("Claves")
        self.keys_form = KeysForm(icons)
        self.content.addWidget(self.keys_form)

        self.mode = SegmentedControl(["Cifrar", "Descifrar"])
        self.mode.changed.connect(self._on_mode_changed)
        mode_row = QHBoxLayout()
        mode_row.addWidget(self.mode)
        mode_row.addStretch(1)
        self.content.addLayout(mode_row)

        self.drop_zone = DropZone(icons)
        self.drop_zone.files_selected.connect(self.add_files)
        self.content.addWidget(self.drop_zone)

        self.queue_title = self.section("Cola")
        self.queue = Card()
        self.content.addWidget(self.queue)

        actions = QHBoxLayout()
        self.run_button = QPushButton()
        self.run_button.setProperty("variant", "primary")
        self.run_button.clicked.connect(self.start)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.cancel)
        self.clear_button = QPushButton("Vaciar lista")
        icons.bind(self.clear_button, "trash")
        self.clear_button.clicked.connect(self.clear)
        actions.addWidget(self.run_button)
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.clear_button)
        actions.addStretch(1)
        self.content.addLayout(actions)

        self.banner = Banner(icons)
        self.content.addWidget(self.banner)
        self.content.addStretch(1)

        self._on_mode_changed(0)
        self._refresh()

    @property
    def busy(self) -> bool:
        return self._current is not None

    def _on_mode_changed(self, index: int) -> None:
        self._operation = _MODES[index]
        encrypt = self._operation is Operation.ENCRYPT
        self.run_button.setText("Cifrar archivos" if encrypt else "Descifrar archivos")
        self._icons.bind(self.run_button, "encrypt" if encrypt else "decrypt", "on_accent")

    def add_files(self, paths: list[Path]) -> None:
        known = {row.path for row in self._rows}
        # dict.fromkeys conserva el orden y quita duplicados dentro de la misma selección.
        new = [p for p in dict.fromkeys(paths) if p not in known]
        for path in new:
            row = FileRow(path, self._icons)
            self._rows.append(row)
            self.queue.body.addWidget(row)
        # Si todo lo agregado ya está cifrado, lo más probable es que se quiera descifrar.
        if new and not self.busy:
            all_encrypted = all(p.suffix == ENCRYPTED_SUFFIX for p in new)
            self.mode.set_current_index(1 if all_encrypted else 0)
        self._refresh()

    def _pending(self) -> list[FileRow]:
        return [row for row in self._rows if row.state == "pending"]

    def _refresh(self) -> None:
        has_rows = bool(self._rows)
        self.queue.setVisible(has_rows)
        self.queue_title.setVisible(has_rows)
        self.run_button.setEnabled(bool(self._pending()) and not self.busy)
        self.cancel_button.setVisible(self.busy)
        self.clear_button.setEnabled(has_rows and not self.busy)
        self.mode.setEnabled(not self.busy)

    def start(self) -> None:
        keys = self.keys_form.keys()
        if keys is None:
            self.banner.show_message("error", "Escribe las dos contraseñas antes de continuar.")
            return
        # Las claves se fijan al empezar: cambiarlas a mitad de cola mezclaría resultados.
        self._keys = keys
        self.banner.hide()
        self._next()

    def _next(self) -> None:
        pending = self._pending()
        if not pending or self._keys is None:
            self._current = None
            self._refresh()
            self._summarize()
            return
        row, keys, operation = pending[0], self._keys, self._operation
        row.start()
        if operation is Operation.ENCRYPT:
            task = self._runner.start(
                lambda p, c: self._service.encrypt_file(row.path, keys, progress=p, cancel=c)
            )
        else:
            task = self._runner.start(
                lambda p, c: self._service.decrypt_file(row.path, keys, progress=p, cancel=c)
            )
        self._current = (row, task)
        task.signals.progress.connect(row.set_progress)
        task.signals.finished.connect(lambda out: (row.finish(out), self._next()))
        task.signals.failed.connect(lambda exc: (row.fail(error_text(exc)), self._next()))
        task.signals.cancelled.connect(lambda: self._on_cancelled(row))
        self._refresh()

    def _on_cancelled(self, row: FileRow) -> None:
        row.cancel()
        self._current = None
        self._refresh()

    def _summarize(self) -> None:
        done = sum(row.state == "done" for row in self._rows)
        failed = sum(row.state == "error" for row in self._rows)
        if failed:
            self.banner.show_message("error", f"{done} completados, {failed} con errores.")
        elif done:
            self.banner.show_message("success", f"{done} archivo(s) procesados.", timeout_ms=4000)

    def cancel(self) -> None:
        if self._current is not None:
            self._current[1].cancel()

    def clear(self) -> None:
        if self.busy:
            return
        for row in self._rows:
            row.hide()
            row.deleteLater()
        self._rows.clear()
        self.banner.hide()
        self._refresh()
