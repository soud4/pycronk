from PySide6.QtWidgets import QComboBox, QFileDialog, QHBoxLayout, QLabel, QPushButton, QWidget

from pycronk import __version__
from pycronk.core.api import Cryptor
from pycronk.services.settings import Settings, Theme
from pycronk.ui.pages.base import PageWidget
from pycronk.ui.state import SettingsStore
from pycronk.ui.widgets.grouped_list import GroupedList
from pycronk.ui.widgets.segmented_control import SegmentedControl
from pycronk.ui.widgets.switch import Switch

_THEMES = (Theme.SYSTEM, Theme.LIGHT, Theme.DARK)
_RETENTION = [("7 días", 7), ("30 días", 30), ("90 días", 90), ("1 año", 365), ("Siempre", 0)]
_CLIPBOARD = [("Nunca", 0), ("30 segundos", 30), ("1 minuto", 60), ("2 minutos", 120)]


def _combo(options: list[tuple[str, int]], current: int) -> QComboBox:
    combo = QComboBox()
    for label, value in options:
        combo.addItem(label, value)
    index = combo.findData(current)
    # Un valor guardado que no está en la lista (editado a mano) se muestra igualmente.
    if index == -1:
        combo.addItem(str(current), current)
        index = combo.count() - 1
    combo.setCurrentIndex(index)
    return combo


class SettingsPage(PageWidget):
    page_id = "settings"
    title = "Ajustes"
    icon = "settings"

    def __init__(self, store: SettingsStore, cryptor: Cryptor) -> None:
        super().__init__()
        self._store = store
        current = store.current

        self.section("Apariencia")
        appearance = GroupedList()
        self.theme = SegmentedControl(["Sistema", "Claro", "Oscuro"])
        self.theme.set_current_index(_THEMES.index(current.theme), notify=False)
        self.theme.changed.connect(lambda i: store.update(theme=_THEMES[i]))
        appearance.add_row("Tema", self.theme)
        self.content.addWidget(appearance)

        self.section("Cifrado")
        crypto = GroupedList()
        self.engine = QComboBox()
        for engine in cryptor.engines:
            self.engine.addItem(engine.title, engine.id)
        self.engine.setCurrentIndex(max(0, self.engine.findData(current.engine_id)))
        self.engine.currentIndexChanged.connect(
            lambda _i: store.update(engine_id=self.engine.currentData())
        )
        crypto.add_row(
            "Algoritmo",
            self.engine,
            "Se usa al cifrar. Al descifrar, el algoritmo se detecta desde el propio archivo.",
        )
        self.content.addWidget(crypto)

        self.section("Historial")
        history = GroupedList()
        self.history_enabled = Switch()
        self.history_enabled.setChecked(current.history_enabled)
        self.history_enabled.toggled.connect(lambda on: store.update(history_enabled=on))
        history.add_row(
            "Guardar historial", self.history_enabled, "Solo metadatos, nunca contenido."
        )
        self.retention = _combo(_RETENTION, current.history_retention_days)
        self.retention.currentIndexChanged.connect(
            lambda _i: store.update(history_retention_days=self.retention.currentData())
        )
        history.add_row("Conservar durante", self.retention)
        self.content.addWidget(history)

        self.section("Archivos")
        files = GroupedList()
        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        choose = QPushButton("Elegir…")
        choose.clicked.connect(self._choose_folder)
        reset = QPushButton("Restablecer")
        reset.clicked.connect(lambda: store.update(output_dir=""))
        buttons_layout.addWidget(choose)
        buttons_layout.addWidget(reset)
        self.output_row = files.add_row("Carpeta de salida", buttons)
        self.content.addWidget(files)

        self.section("Privacidad")
        privacy = GroupedList()
        self.clipboard = _combo(_CLIPBOARD, current.clear_clipboard_seconds)
        self.clipboard.currentIndexChanged.connect(
            lambda _i: store.update(clear_clipboard_seconds=self.clipboard.currentData())
        )
        privacy.add_row(
            "Borrar portapapeles",
            self.clipboard,
            "Tras copiar un resultado, lo elimina del portapapeles pasado este tiempo.",
        )
        self.content.addWidget(privacy)

        self.section("Acerca de")
        about = GroupedList()
        about.add_row("Versión", QLabel(__version__))
        about.add_row(
            "Seguridad",
            None,
            "pycronk-v1 es un algoritmo educativo: no lo uses para proteger información real. "
            "Los detalles están en docs/specs/003-algoritmo.md.",
        )
        self.content.addWidget(about)
        self.content.addStretch(1)

        store.changed.connect(self._sync)
        self._sync(current)

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de salida")
        if folder:
            self._store.update(output_dir=folder)

    def _sync(self, settings: Settings) -> None:
        self.output_row.set_hint(settings.output_dir or "Junto al archivo original")
