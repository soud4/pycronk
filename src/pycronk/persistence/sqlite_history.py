import sqlite3
import threading
from datetime import datetime

from pycronk.services.models import HistoryEntry, Kind, Operation, Status

_COLUMNS = (
    "id, created_at, operation, kind, engine_id, label, input_size, output_path, duration_ms,"
    " status"
)


def _to_entry(row: tuple[object, ...]) -> HistoryEntry:
    (id_, created_at, operation, kind, engine_id, label, size, output, duration, status) = row
    return HistoryEntry(
        id=int(str(id_)),
        created_at=datetime.fromisoformat(str(created_at)),
        operation=Operation(operation),
        kind=Kind(kind),
        engine_id=str(engine_id),
        label=str(label),
        input_size=int(str(size)),
        output_path=str(output),
        duration_ms=int(str(duration)),
        status=Status(status),
    )


class SqliteHistoryRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._lock = threading.Lock()

    def add(self, entry: HistoryEntry) -> int:
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "INSERT INTO history (created_at, operation, kind, engine_id, label, input_size,"
                " output_path, duration_ms, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entry.created_at.isoformat(),
                    entry.operation.value,
                    entry.kind.value,
                    entry.engine_id,
                    entry.label,
                    entry.input_size,
                    entry.output_path,
                    entry.duration_ms,
                    entry.status.value,
                ),
            )
            return int(cursor.lastrowid or 0)

    def list(self, *, limit: int, offset: int = 0, kind: Kind | None = None) -> list[HistoryEntry]:
        query = f"SELECT {_COLUMNS} FROM history"
        params: list[object] = []
        if kind is not None:
            query += " WHERE kind = ?"
            params.append(kind.value)
        # `id` desempata entradas creadas en el mismo instante para que el orden sea estable.
        query += " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
        params += [limit, offset]
        with self._lock:
            return [_to_entry(row) for row in self._conn.execute(query, params)]

    def delete(self, entry_id: int) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))

    def clear(self) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM history")

    def purge_older_than(self, cutoff: datetime) -> int:
        # Las fechas se guardan en ISO-8601 UTC, así que la comparación de texto respeta el orden
        # cronológico.
        with self._lock, self._conn:
            cursor = self._conn.execute(
                "DELETE FROM history WHERE created_at < ?", (cutoff.isoformat(),)
            )
            return cursor.rowcount
