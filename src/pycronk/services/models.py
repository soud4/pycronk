from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Operation(StrEnum):
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"


class Kind(StrEnum):
    TEXT = "text"
    FILE = "file"


class Status(StrEnum):
    OK = "ok"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class HistoryEntry:
    """Solo metadatos. No tiene (ni debe tener) campos para claves, texto o contenido: así es
    imposible filtrar datos sensibles al historial por descuido (spec 005)."""

    created_at: datetime
    operation: Operation
    kind: Kind
    engine_id: str
    status: Status
    label: str = ""
    input_size: int = 0
    output_path: str = ""
    duration_ms: int = 0
    id: int | None = None
