"""Puertos de services (spec 002): lo que services necesita del exterior, sin saber quién lo da."""

from datetime import UTC, datetime
from typing import Protocol

from pycronk.services.models import HistoryEntry, Kind
from pycronk.services.settings import Settings


class HistoryRepository(Protocol):
    def add(self, entry: HistoryEntry) -> int: ...

    def list(
        self, *, limit: int, offset: int = 0, kind: Kind | None = None
    ) -> list[HistoryEntry]: ...

    def delete(self, entry_id: int) -> None: ...

    def clear(self) -> None: ...

    def purge_older_than(self, cutoff: datetime) -> int: ...


class SettingsRepository(Protocol):
    def load(self) -> Settings: ...

    def save(self, settings: Settings) -> None: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        # UTC en almacenamiento; la UI convierte a hora local al mostrar.
        return datetime.now(UTC)
