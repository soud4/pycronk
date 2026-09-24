from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, fields, replace
from enum import StrEnum
from typing import Any

from pycronk.core.api import DEFAULT_CHUNK_SYMBOLS, DEFAULT_ENGINE_ID


class Theme(StrEnum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


def _non_negative(value: Any) -> bool:
    return value >= 0


def _valid_chunk(value: Any) -> bool:
    return value > 0 and value % 4 == 0


def _valid_theme(value: Any) -> bool:
    return value in Theme._value2member_map_


# Validaciones por campo: un valor corrupto en la base no debe impedir que la app arranque;
# se descarta y se usa el valor por defecto.
_VALIDATORS: dict[str, Callable[[Any], bool]] = {
    "theme": _valid_theme,
    "history_retention_days": _non_negative,
    "clear_clipboard_seconds": _non_negative,
    "chunk_symbols": _valid_chunk,
}


@dataclass(frozen=True)
class Settings:
    theme: Theme = Theme.SYSTEM
    engine_id: str = DEFAULT_ENGINE_ID
    history_enabled: bool = True
    history_retention_days: int = 90
    output_dir: str = ""
    clear_clipboard_seconds: int = 0
    chunk_symbols: int = DEFAULT_CHUNK_SYMBOLS

    def to_mapping(self) -> dict[str, Any]:
        return {
            key: str(value) if isinstance(value, Theme) else value
            for key, value in asdict(self).items()
        }

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "Settings":
        defaults = cls()
        accepted: dict[str, Any] = {}
        for field in fields(cls):
            if field.name not in values:
                continue
            value = values[field.name]
            default: object = getattr(defaults, field.name)
            # El tema se guarda como texto en JSON; se valida como str y se convierte al final.
            expected: type[object] = str if isinstance(default, Theme) else type(default)
            # bool es subclase de int: sin esta comprobación `true` pasaría como número de días.
            if type(value) is bool and expected is not bool:
                continue
            if not isinstance(value, expected):
                continue
            validator = _VALIDATORS.get(field.name)
            if validator is not None and not validator(value):
                continue
            accepted[field.name] = Theme(value) if field.name == "theme" else value
        return replace(defaults, **accepted)
