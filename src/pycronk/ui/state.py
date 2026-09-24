"""Estado observable compartido entre páginas. Las páginas no se conocen entre sí: se comunican a
través de estos objetos, así que agregar o quitar una página no rompe a las demás."""

from dataclasses import dataclass, replace
from typing import Any

from PySide6.QtCore import QObject, Signal

from pycronk.core.trace import Trace
from pycronk.services.models import Operation
from pycronk.services.ports import SettingsRepository
from pycronk.services.settings import Settings


class SettingsStore(QObject):
    changed = Signal(object)  # Settings

    def __init__(self, repository: SettingsRepository) -> None:
        super().__init__()
        self._repository = repository
        self._current = repository.load()

    @property
    def current(self) -> Settings:
        return self._current

    def update(self, **changes: Any) -> None:
        updated = replace(self._current, **changes)
        if updated == self._current:
            return
        self._repository.save(updated)
        self._current = updated
        self.changed.emit(updated)


@dataclass(frozen=True)
class TraceSnapshot:
    operation: Operation
    trace: Trace
    input_text: str
    output_text: str


class TraceStore(QObject):
    changed = Signal(object)  # TraceSnapshot | None

    def __init__(self) -> None:
        super().__init__()
        self.latest: TraceSnapshot | None = None

    def publish(self, snapshot: TraceSnapshot | None) -> None:
        self.latest = snapshot
        self.changed.emit(snapshot)


class Navigator(QObject):
    """Permite que una página pida mostrar otra sin tener referencia a ella ni a la ventana."""

    requested = Signal(str)  # page_id

    def go(self, page_id: str) -> None:
        self.requested.emit(page_id)
