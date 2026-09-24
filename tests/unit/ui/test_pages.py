from dataclasses import replace

import pytest
from PySide6.QtWidgets import QMessageBox

from pycronk.core.api import Cryptor
from pycronk.core.interfaces import Keys
from pycronk.persistence.sqlite_settings import SqliteSettingsRepository
from pycronk.services.crypto_service import CryptoService
from pycronk.services.models import Kind, Operation, Status
from pycronk.services.settings import Settings, Theme
from pycronk.ui.pages.files_page import FilesPage
from pycronk.ui.pages.history_page import HistoryPage
from pycronk.ui.pages.process_page import ProcessPage
from pycronk.ui.pages.settings_page import SettingsPage
from pycronk.ui.pages.text_page import TextPage
from pycronk.ui.state import Navigator, SettingsStore, TraceSnapshot, TraceStore
from pycronk.ui.widgets.layer_card import LayerCard
from pycronk.ui.workers import TaskRunner

KEYS = Keys("MAR7", "otra")


@pytest.fixture
def store(memory_conn) -> SettingsStore:
    store = SettingsStore(SqliteSettingsRepository(memory_conn))
    store.update(chunk_symbols=64)  # varios chunks con archivos pequeños
    return store


@pytest.fixture
def service(fake_history, fake_clock, store) -> CryptoService:
    return CryptoService(Cryptor.default(), fake_history, fake_clock, lambda: store.current)


@pytest.fixture
def runner(qapp):
    runner = TaskRunner()
    yield runner
    runner.wait(5000)


@pytest.fixture
def text_page(qtbot, service, icons, runner, store) -> tuple[TextPage, TraceStore, Navigator]:
    traces, navigator = TraceStore(), Navigator()
    page = TextPage(service, icons, runner, traces, store, navigator)
    qtbot.addWidget(page)
    return page, traces, navigator


def fill_keys(form) -> None:
    form.matrix.setText(KEYS.matrix)
    form.keystream.setText(KEYS.keystream)


# --- Texto -----------------------------------------------------------------


def test_text_requires_keys_and_input(text_page):
    page, _, _ = text_page
    page.run()
    assert "contraseñas" in page.banner.message()
    fill_keys(page.keys_form)
    page.run()
    assert "vacía" in page.banner.message()


def test_text_encrypt_then_decrypt(qtbot, text_page):
    page, traces, _ = text_page
    fill_keys(page.keys_form)
    page.input.setPlainText("hola mundo")
    with qtbot.waitSignal(traces.changed):
        page.run()
    armored = page.output.toPlainText()
    assert armored.startswith("PCRK1:")
    assert traces.latest is not None and traces.latest.operation is Operation.ENCRYPT
    assert page.process_button.isVisibleTo(page)

    page.input.setPlainText(armored)
    assert page.operation is Operation.DECRYPT  # autodetectado
    with qtbot.waitSignal(traces.changed):
        page.run()
    assert page.output.toPlainText() == "hola mundo"


def test_text_autodetect_only_on_transition(text_page):
    page, _, _ = text_page
    page.input.setPlainText("PCRK1:AAAA")
    assert page.operation is Operation.DECRYPT
    page.mode.set_current_index(0)  # el usuario fuerza Cifrar
    page.input.setPlainText("PCRK1:AAAAAAAA")
    assert page.operation is Operation.ENCRYPT
    page.input.setPlainText("texto normal")
    assert page.operation is Operation.ENCRYPT


def test_text_error_is_shown(qtbot, text_page):
    page, _, _ = text_page
    fill_keys(page.keys_form)
    page.input.setPlainText("PCRK1:@@@")
    page.run()
    qtbot.waitUntil(lambda: page.run_button.isEnabled())
    assert page.banner.property("kind") == "error"


def test_text_copy_and_clear(qtbot, qapp, text_page, store):
    page, _, _ = text_page
    store.update(clear_clipboard_seconds=30)
    page.output.setPlainText("resultado")
    page.copy_output()
    assert qapp.clipboard().text() == "resultado"
    assert "30 s" in page.banner.message()
    page.clear()
    assert page.output.toPlainText() == ""
    assert not page.copy_button.isEnabled()


def test_text_process_button_navigates(qtbot, text_page):
    page, _, navigator = text_page
    with qtbot.waitSignal(navigator.requested) as blocker:
        page.process_button.click()
    assert blocker.args == ["process"]


# --- Archivos --------------------------------------------------------------


@pytest.fixture
def files_page(qtbot, service, icons, runner) -> FilesPage:
    page = FilesPage(service, icons, runner)
    qtbot.addWidget(page)
    return page


def test_files_mode_follows_extension(files_page, tmp_path):
    enc = tmp_path / "a.txt.pcrk"
    enc.write_bytes(b"x")
    files_page.add_files([enc])
    assert files_page.mode.current_index() == 1
    plain = tmp_path / "b.txt"
    plain.write_bytes(b"x")
    files_page.add_files([plain, plain])
    assert files_page.mode.current_index() == 0
    assert len(files_page._rows) == 2  # los duplicados se ignoran


def test_files_requires_keys(files_page, tmp_path):
    src = tmp_path / "a.txt"
    src.write_bytes(b"x")
    files_page.add_files([src])
    files_page.start()
    assert "contraseñas" in files_page.banner.message()


def test_files_encrypt_queue(qtbot, files_page, tmp_path):
    sources = []
    for name in ("uno.bin", "dos.bin"):
        path = tmp_path / name
        path.write_bytes(bytes(range(256)) * 10)
        sources.append(path)
    files_page.add_files(sources)
    fill_keys(files_page.keys_form)
    files_page.start()
    qtbot.waitUntil(lambda: not files_page.busy and not files_page.banner.isHidden(), timeout=5000)
    assert [row.state for row in files_page._rows] == ["done", "done"]
    assert (tmp_path / "uno.bin.pcrk").exists()
    assert files_page.banner.property("kind") == "success"
    files_page.clear()
    assert files_page._rows == []


def test_files_errors_are_reported(qtbot, files_page, tmp_path):
    bad = tmp_path / "roto.pcrk"
    bad.write_bytes(b"no es un contenedor")
    files_page.add_files([bad])
    fill_keys(files_page.keys_form)
    files_page.start()
    qtbot.waitUntil(lambda: not files_page.busy and not files_page.banner.isHidden(), timeout=5000)
    assert files_page._rows[0].state == "error"
    assert files_page.banner.property("kind") == "error"


# --- Proceso ---------------------------------------------------------------


def test_process_page_renders_trace(qtbot, icons, service):
    traces = TraceStore()
    page = ProcessPage(traces, icons)
    qtbot.addWidget(page)
    assert page.findChildren(LayerCard) == []
    outcome = service.encrypt_text("hola", KEYS, trace=True)
    assert outcome.trace is not None
    traces.publish(TraceSnapshot(Operation.ENCRYPT, outcome.trace, "hola", outcome.text))
    cards = [c for c in page.findChildren(LayerCard) if not c.isHidden()]
    assert len(cards) == 2 + len(outcome.trace.steps) + 1  # resumen, entrada, capas, salida
    traces.publish(None)
    qtbot.waitUntil(lambda: not [c for c in page.findChildren(LayerCard) if not c.isHidden()])


# --- Historial -------------------------------------------------------------


def test_history_page_lists_filters_and_deletes(qtbot, icons, memory_conn, monkeypatch):
    from pycronk.persistence.sqlite_history import SqliteHistoryRepository
    from tests.unit.persistence.test_sqlite_history import entry

    repo = SqliteHistoryRepository(memory_conn)
    repo.add(entry(0, Kind.TEXT))
    repo.add(entry(1, Kind.FILE, status=Status.ERROR, output_path="/x"))
    page = HistoryPage(repo, icons)
    qtbot.addWidget(page)
    assert page.table.topLevelItemCount() == 2
    page.filter.set_current_index(2)
    assert page.table.topLevelItemCount() == 1
    assert page.table.topLevelItem(0).text(6) == "Error"

    page.table.topLevelItem(0).setSelected(True)
    page.delete_selected()
    assert page.table.topLevelItemCount() == 0

    page.filter.set_current_index(0)
    monkeypatch.setattr(QMessageBox, "question", lambda *a: QMessageBox.StandardButton.Yes)
    page.clear()
    assert repo.list(limit=10) == []


# --- Ajustes ---------------------------------------------------------------


def test_settings_page_updates_store(qtbot, store):
    page = SettingsPage(store, Cryptor.default())
    qtbot.addWidget(page)
    page.theme.set_current_index(2)
    assert store.current.theme is Theme.DARK
    page.history_enabled.click()
    assert store.current.history_enabled is False
    page.retention.setCurrentIndex(page.retention.findData(7))
    assert store.current.history_retention_days == 7
    page.clipboard.setCurrentIndex(page.clipboard.findData(60))
    assert store.current.clear_clipboard_seconds == 60
    store.update(output_dir="/tmp/salida")
    assert page.output_row.hint.text() == "/tmp/salida"


def test_settings_page_shows_unknown_saved_values(qtbot, memory_conn):
    repo = SqliteSettingsRepository(memory_conn)
    repo.save(replace(Settings(), history_retention_days=45))
    page = SettingsPage(SettingsStore(repo), Cryptor.default())
    qtbot.addWidget(page)
    assert page.retention.currentData() == 45
