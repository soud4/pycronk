import json
import os
import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from pycronk.core.interfaces import Keys
from pycronk.persistence.sqlite_db import migrate
from pycronk.services.models import HistoryEntry

# Los tests de widgets deben correr sin servidor gráfico (CI, SSH). Tiene que fijarse antes de que
# pytest-qt cree la QApplication.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def vectors() -> dict[str, Any]:
    # Generados ejecutando el prototipo original antes de refactorizar (spec 008).
    return json.loads((DATA / "prototype_vectors.json").read_text(encoding="utf-8"))


@pytest.fixture
def keys() -> Keys:
    return Keys(matrix="MAR7", keystream="otraClaveDistinta99")


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self.current = start

    def now(self) -> datetime:
        return self.current

    def advance(self, **delta: float) -> None:
        self.current += timedelta(**delta)


@pytest.fixture
def fake_clock() -> FakeClock:
    return FakeClock(datetime(2026, 1, 1, 12, 0, tzinfo=UTC))


@pytest.fixture
def memory_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(":memory:")
    migrate(conn)
    yield conn
    conn.close()


class FakeHistory:
    def __init__(self) -> None:
        self.entries: list[HistoryEntry] = []

    def add(self, entry: HistoryEntry) -> int:
        self.entries.append(entry)
        return len(self.entries)

    def list(self, *, limit: int, offset: int = 0, kind: str | None = None) -> list[HistoryEntry]:
        return self.entries[offset : offset + limit]

    def delete(self, entry_id: int) -> None:
        del self.entries[entry_id - 1]

    def clear(self) -> None:
        self.entries.clear()

    def purge_older_than(self, cutoff: datetime) -> int:
        before = len(self.entries)
        self.entries = [e for e in self.entries if e.created_at >= cutoff]
        return before - len(self.entries)


@pytest.fixture
def fake_history() -> FakeHistory:
    return FakeHistory()
