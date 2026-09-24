import json
import sqlite3
import threading
from typing import Any

from pycronk.services.settings import Settings


class SqliteSettingsRepository:
    """Tabla clave-valor con valores JSON: agregar un ajuste no requiere migración."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._lock = threading.Lock()

    def load(self) -> Settings:
        values: dict[str, Any] = {}
        with self._lock:
            rows = self._conn.execute("SELECT key, value FROM settings").fetchall()
        for key, raw in rows:
            try:
                values[key] = json.loads(raw)
            except json.JSONDecodeError:
                continue  # un valor corrupto no debe impedir arrancar; se usa el defecto
        return Settings.from_mapping(values)

    def save(self, settings: Settings) -> None:
        rows = [(key, json.dumps(value)) for key, value in settings.to_mapping().items()]
        with self._lock, self._conn:
            self._conn.executemany(
                "INSERT INTO settings (key, value) VALUES (?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                rows,
            )
