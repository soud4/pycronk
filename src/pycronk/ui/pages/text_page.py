from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton

from pycronk.core.errors import PycronkError
from pycronk.services.crypto_service import CryptoService, TextOutcome
from pycronk.services.models import Operation
from pycronk.ui.pages.base import PageWidget
from pycronk.ui.state import Navigator, SettingsStore, TraceSnapshot, TraceStore
from pycronk.ui.theme.icons import IconProvider
from pycronk.ui.widgets.banner import Banner
from pycronk.ui.widgets.keys_form import KeysForm
from pycronk.ui.widgets.segmented_control import SegmentedControl
from pycronk.ui.workers import TaskRunner

_MODES = (Operation.ENCRYPT, Operation.DECRYPT)


def error_text(exc: object) -> str:
    if isinstance(exc, PycronkError):
        return str(exc)
    return f"Error inesperado: {exc}"


class TextPage(PageWidget):
    page_id = "text"
    title = "Texto"
    icon = "text"
    subtitle = (
        "Cifra o descifra mensajes. El texto cifrado empieza con PCRK1: y se puede pegar en "
        "cualquier sitio."
    )

    def __init__(
        self,
        service: CryptoService,
        icons: IconProvider,
        runner: TaskRunner,
        traces: TraceStore,
        settings: SettingsStore,
        navigator: Navigator,
    ) -> None:
        super().__init__()
        self._service = service
        self._icons = icons
        self._runner = runner
        self._traces = traces
        self._settings = settings
        self._navigator = navigator
        self._was_armored = False
        self._last_input = ""

        self.section("Claves")
        self.keys_form = KeysForm(icons)
        self.content.addWidget(self.keys_form)

        self.mode = SegmentedControl(["Cifrar", "Descifrar"])
        self.mode.changed.connect(self._on_mode_changed)
        row = QHBoxLayout()
        row.addWidget(self.mode)
        row.addStretch(1)
        self.content.addLayout(row)

        self.section("Entrada")
        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("Escribe un mensaje o pega un texto cifrado…")
        self.input.setMinimumHeight(120)
        self.input.textChanged.connect(self._on_input_changed)
        self.content.addWidget(self.input)

        actions = QHBoxLayout()
        self.run_button = QPushButton()
        self.run_button.setProperty("variant", "primary")
        self.run_button.clicked.connect(self.run)
        self.clear_button = QPushButton("Limpiar")
        icons.bind(self.clear_button, "clear")
        self.clear_button.clicked.connect(self.clear)
        actions.addWidget(self.run_button)
        actions.addWidget(self.clear_button)
        actions.addStretch(1)
        self.content.addLayout(actions)

        self.banner = Banner(icons)
        self.content.addWidget(self.banner)

        self.section("Resultado")
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setProperty("mono", True)
        self.output.setPlaceholderText("El resultado aparecerá aquí.")
        self.output.setMinimumHeight(120)
        self.content.addWidget(self.output)

        result_actions = QHBoxLayout()
        self.copy_button = QPushButton("Copiar")
        icons.bind(self.copy_button, "copy")
        self.copy_button.clicked.connect(self.copy_output)
        self.process_button = QPushButton("Ver proceso")
        self.process_button.setProperty("variant", "plain")
        icons.bind(self.process_button, "process", "accent")
        self.process_button.clicked.connect(lambda: self._navigator.go("process"))
        result_actions.addWidget(self.copy_button)
        result_actions.addWidget(self.process_button)
        result_actions.addStretch(1)
        self.content.addLayout(result_actions)
        self.content.addStretch(1)

        self._on_mode_changed(0)
        self._set_result_actions(False)

    @property
    def operation(self) -> Operation:
        return _MODES[self.mode.current_index()]

    def _on_mode_changed(self, index: int) -> None:
        encrypt = _MODES[index] is Operation.ENCRYPT
        self.run_button.setText("Cifrar" if encrypt else "Descifrar")
        self._icons.bind(self.run_button, "encrypt" if encrypt else "decrypt", "on_accent")

    def _on_input_changed(self) -> None:
        # Solo se cambia de modo cuando la entrada *pasa* a ser (o deja de ser) un cifrado, para no
        # pelear con el usuario si eligió el modo a mano.
        armored = self._service.cryptor.looks_encrypted(self.input.toPlainText())
        if armored != self._was_armored:
            self._was_armored = armored
            self.mode.set_current_index(1 if armored else 0)

    def _set_result_actions(self, enabled: bool, *, traced: bool = False) -> None:
        self.copy_button.setEnabled(enabled)
        self.process_button.setVisible(traced)

    def run(self) -> None:
        keys = self.keys_form.keys()
        if keys is None:
            self.banner.show_message("error", "Escribe las dos contraseñas antes de continuar.")
            return
        text = self.input.toPlainText()
        if not text.strip():
            self.banner.show_message("error", "No hay nada que procesar: la entrada está vacía.")
            return
        operation = self.operation
        self._last_input = text
        self.run_button.setEnabled(False)
        self.banner.hide()
        if operation is Operation.ENCRYPT:
            task = self._runner.start(
                lambda _p, _c: self._service.encrypt_text(text, keys, trace=True)
            )
        else:
            task = self._runner.start(
                lambda _p, _c: self._service.decrypt_text(text, keys, trace=True)
            )
        task.signals.finished.connect(lambda result: self._on_finished(operation, result))
        task.signals.failed.connect(self._on_failed)

    def _on_finished(self, operation: Operation, result: TextOutcome) -> None:
        self.run_button.setEnabled(True)
        self.output.setPlainText(result.text)
        self._set_result_actions(True, traced=result.trace is not None)
        if result.trace is not None:
            self._traces.publish(
                TraceSnapshot(operation, result.trace, self._last_input, result.text)
            )
        if operation is Operation.ENCRYPT:
            self.banner.show_message("success", "Mensaje cifrado.", timeout_ms=3000)
        else:
            self.banner.show_message(
                "info",
                "Texto descifrado. Si alguna contraseña es incorrecta, el resultado será texto sin "
                "sentido: el algoritmo no puede detectarlo.",
            )

    def _on_failed(self, exc: object) -> None:
        self.run_button.setEnabled(True)
        self.banner.show_message("error", error_text(exc))

    def copy_output(self) -> None:
        text = self.output.toPlainText()
        if not text:
            return
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        seconds = self._settings.current.clear_clipboard_seconds
        message = "Copiado al portapapeles."
        if seconds:
            message += f" Se borrará en {seconds} s."
            # Solo se borra si el portapapeles sigue teniendo lo que copiamos: no se pisa algo que
            # el usuario haya copiado después.
            QTimer.singleShot(
                seconds * 1000, lambda: clipboard.clear() if clipboard.text() == text else None
            )
        self.banner.show_message("success", message, timeout_ms=2500)

    def clear(self) -> None:
        self.input.clear()
        self.output.clear()
        self.banner.hide()
        self._set_result_actions(False)
