import re
import sqlite3
from importlib import resources
from pathlib import Path

_MIGRATION_NAME = re.compile(r"^(\d{3})_.+\.sql$")


def open_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Los workers de la UI escriben el historial desde otros hilos. El módulo sqlite3 se compila en
    # modo serializado (threadsafety == 3) y los repositorios además serializan con un lock.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode = WAL")
    migrate(conn)
    return conn


def _migrations() -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for entry in resources.files("pycronk.persistence.migrations").iterdir():
        match = _MIGRATION_NAME.match(entry.name)
        if match:
            found.append((int(match.group(1)), entry.read_text(encoding="utf-8")))
    return sorted(found)


def migrate(conn: sqlite3.Connection) -> int:
    """Aplica las migraciones pendientes y devuelve la versión final del esquema.

    `PRAGMA user_version` evita una tabla extra de control: SQLite ya reserva ese entero para que
    la aplicación guarde su versión de esquema.
    """
    (current,) = conn.execute("PRAGMA user_version").fetchone()
    for number, script in _migrations():
        if number <= current:
            continue
        with conn:
            conn.executescript(script)
            conn.execute(f"PRAGMA user_version = {number:d}")
        current = number
    return current
