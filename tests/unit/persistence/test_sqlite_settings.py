from pycronk.persistence.sqlite_settings import SqliteSettingsRepository
from pycronk.services.settings import Settings, Theme


def test_load_empty_returns_defaults(memory_conn):
    assert SqliteSettingsRepository(memory_conn).load() == Settings()


def test_save_and_reload(memory_conn):
    repo = SqliteSettingsRepository(memory_conn)
    changed = Settings(theme=Theme.DARK, history_retention_days=7, output_dir="/tmp")
    repo.save(changed)
    assert SqliteSettingsRepository(memory_conn).load() == changed


def test_save_overwrites(memory_conn):
    repo = SqliteSettingsRepository(memory_conn)
    repo.save(Settings(theme=Theme.DARK))
    repo.save(Settings(theme=Theme.LIGHT))
    assert repo.load().theme is Theme.LIGHT


def test_corrupt_values_fall_back(memory_conn):
    memory_conn.execute("INSERT INTO settings VALUES ('theme', '{no json')")
    memory_conn.execute("INSERT INTO settings VALUES ('history_retention_days', '\"diez\"')")
    assert SqliteSettingsRepository(memory_conn).load() == Settings()
