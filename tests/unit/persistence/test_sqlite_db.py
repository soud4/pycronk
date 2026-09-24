import sqlite3

from pycronk.persistence.sqlite_db import migrate, open_database


def test_migrate_from_zero_sets_version():
    conn = sqlite3.connect(":memory:")
    assert migrate(conn) == 1
    assert conn.execute("PRAGMA user_version").fetchone() == (1,)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"history", "settings"} <= tables
    conn.close()


def test_migrate_is_idempotent(memory_conn):
    assert migrate(memory_conn) == 1
    assert migrate(memory_conn) == 1


def test_open_database_creates_parent_folder(tmp_path):
    path = tmp_path / "a" / "b" / "pycronk.db"
    conn = open_database(path)
    assert path.exists()
    assert conn.execute("PRAGMA user_version").fetchone() == (1,)
    conn.close()
