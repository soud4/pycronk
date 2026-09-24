import pytest

from pycronk.core.api import DEFAULT_CHUNK_SYMBOLS, DEFAULT_ENGINE_ID
from pycronk.services.settings import Settings, Theme


def test_defaults():
    s = Settings()
    assert s.theme is Theme.SYSTEM
    assert s.engine_id == DEFAULT_ENGINE_ID
    assert s.history_enabled is True
    assert s.history_retention_days == 90
    assert s.chunk_symbols == DEFAULT_CHUNK_SYMBOLS


def test_round_trip_through_mapping():
    s = Settings(theme=Theme.DARK, history_enabled=False, output_dir="/tmp/x")
    assert Settings.from_mapping(s.to_mapping()) == s


def test_mapping_is_json_friendly():
    assert Settings().to_mapping()["theme"] == "system"


def test_unknown_keys_are_ignored():
    assert Settings.from_mapping({"no_existe": 1, "theme": "light"}) == Settings(theme=Theme.LIGHT)


def test_missing_keys_take_defaults():
    assert Settings.from_mapping({}) == Settings()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("theme", "violeta"),
        ("theme", 3),
        ("history_retention_days", -1),
        ("history_retention_days", "90"),
        ("history_retention_days", True),
        ("history_enabled", 1),
        ("chunk_symbols", 6),
        ("chunk_symbols", 0),
        ("clear_clipboard_seconds", -5),
        ("output_dir", None),
    ],
)
def test_invalid_values_fall_back_to_default(key, value):
    assert getattr(Settings.from_mapping({key: value}), key) == getattr(Settings(), key)
