import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from pycronk.persistence.sqlite_history import SqliteHistoryRepository
from pycronk.services.models import HistoryEntry, Kind, Operation, Status

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def entry(minutes: int = 0, kind: Kind = Kind.TEXT, **kw) -> HistoryEntry:
    return HistoryEntry(
        created_at=T0 + timedelta(minutes=minutes),
        operation=kw.pop("operation", Operation.ENCRYPT),
        kind=kind,
        engine_id="pycronk-v1",
        status=kw.pop("status", Status.OK),
        **kw,
    )


@pytest.fixture
def repo(memory_conn) -> SqliteHistoryRepository:
    return SqliteHistoryRepository(memory_conn)


def test_add_and_list_round_trip(repo):
    original = entry(label="a.txt", input_size=10, output_path="/x", duration_ms=5)
    new_id = repo.add(original)
    (stored,) = repo.list(limit=10)
    assert stored.id == new_id
    assert stored == HistoryEntry(**{**vars(original), "id": new_id})


def test_list_newest_first_with_pagination(repo):
    for minute in range(5):
        repo.add(entry(minute, label=str(minute)))
    assert [e.label for e in repo.list(limit=2)] == ["4", "3"]
    assert [e.label for e in repo.list(limit=2, offset=2)] == ["2", "1"]


def test_list_filters_by_kind(repo):
    repo.add(entry(0, Kind.TEXT))
    repo.add(entry(1, Kind.FILE))
    assert [e.kind for e in repo.list(limit=10, kind=Kind.FILE)] == [Kind.FILE]


def test_delete_and_clear(repo):
    first = repo.add(entry(0))
    repo.add(entry(1))
    repo.delete(first)
    assert len(repo.list(limit=10)) == 1
    repo.clear()
    assert repo.list(limit=10) == []


def test_purge_older_than(repo):
    repo.add(entry(0))
    repo.add(entry(60 * 24 * 10))
    assert repo.purge_older_than(T0 + timedelta(days=5)) == 1
    assert len(repo.list(limit=10)) == 1


@pytest.mark.parametrize(
    ("column", "value"), [("operation", "borrar"), ("kind", "foto"), ("status", "raro")]
)
def test_check_constraints(memory_conn, column, value):
    row = {
        "created_at": T0.isoformat(),
        "operation": "encrypt",
        "kind": "text",
        "engine_id": "x",
        "status": "ok",
        column: value,
    }
    with pytest.raises(sqlite3.IntegrityError):
        memory_conn.execute(
            "INSERT INTO history (created_at, operation, kind, engine_id, status)"
            " VALUES (:created_at, :operation, :kind, :engine_id, :status)",
            row,
        )
