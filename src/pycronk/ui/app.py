"""Raíz de composición de la GUI: el único lugar donde se eligen implementaciones concretas."""

import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from pycronk import __version__
from pycronk.core.api import Cryptor
from pycronk.persistence.sqlite_db import open_database
from pycronk.persistence.sqlite_history import SqliteHistoryRepository
from pycronk.persistence.sqlite_settings import SqliteSettingsRepository
from pycronk.services.crypto_service import CryptoService
from pycronk.services.ports import SystemClock
from pycronk.services.settings import Settings
from pycronk.ui.main_window import MainWindow
from pycronk.ui.pages.base import Page
from pycronk.ui.pages.files_page import FilesPage
from pycronk.ui.pages.history_page import HistoryPage
from pycronk.ui.pages.process_page import ProcessPage
from pycronk.ui.pages.settings_page import SettingsPage
from pycronk.ui.pages.text_page import TextPage
from pycronk.ui.state import Navigator, SettingsStore, TraceStore
from pycronk.ui.theme.builder import ASSETS, ThemeManager, load_fonts
from pycronk.ui.theme.icons import QtAwesomeIconProvider
from pycronk.ui.workers import TaskRunner


def main() -> None:
    QApplication.setApplicationName("pycronk")
    QApplication.setOrganizationName("pycronk")
    app = QApplication(sys.argv)
    # Fusion es el único estilo que se ve igual en Windows y Linux y respeta por completo la paleta;
    # los estilos nativos ignoran parte de ella y romperían el tema.
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(str(ASSETS / "app-icon.png")))
    ui_family, mono_family = load_fonts()
    font = QFont(ui_family)
    font.setPixelSize(13)
    app.setFont(font)

    data_dir = Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    )
    conn = open_database(data_dir / "pycronk.db")
    settings = SettingsStore(SqliteSettingsRepository(conn))
    history = SqliteHistoryRepository(conn)

    theme = ThemeManager(app, mono_family)
    theme.apply(settings.current.theme)
    applied_theme = [settings.current.theme]

    def on_settings(changed: Settings) -> None:
        # Reaplicar el QSS repinta toda la app: solo se hace si el tema cambió de verdad.
        if changed.theme is not applied_theme[0]:
            applied_theme[0] = changed.theme
            theme.apply(changed.theme)

    settings.changed.connect(on_settings)

    icons = QtAwesomeIconProvider(theme)
    service = CryptoService(Cryptor.default(), history, SystemClock(), lambda: settings.current)
    service.purge_history()

    runner = TaskRunner(app)
    traces = TraceStore()
    navigator = Navigator()
    pages: list[Page] = [
        TextPage(service, icons, runner, traces, settings, navigator),
        FilesPage(service, icons, runner),
        ProcessPage(traces, icons),
        HistoryPage(history, icons),
        SettingsPage(settings, service.cryptor),
    ]
    window = MainWindow(pages, icons, navigator, __version__)
    window.show()

    code = app.exec()
    runner.wait()
    conn.close()
    sys.exit(code)
