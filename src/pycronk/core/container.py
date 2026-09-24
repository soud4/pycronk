import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import BinaryIO

from pycronk.core.errors import InvalidFormat, UnsupportedVersion

MAGIC = b"PCRK"
FORMAT_VERSION = 1
_TAIL = struct.Struct("<BBI")  # modo, flags, símbolos por chunk


class Mode(IntEnum):
    TEXT = 0
    FILE = 1


@dataclass(frozen=True)
class Header:
    engine_id: str
    mode: Mode
    chunk_symbols: int
    version: int = FORMAT_VERSION

    def encode(self) -> bytes:
        engine = self.engine_id.encode("ascii")
        if not 1 <= len(engine) <= 255:
            raise ValueError("El id de motor debe tener entre 1 y 255 caracteres ASCII.")
        return (
            MAGIC
            + bytes([self.version, len(engine)])
            + engine
            + _TAIL.pack(self.mode, 0, self.chunk_symbols)
        )

    @property
    def size(self) -> int:
        return len(MAGIC) + 2 + len(self.engine_id) + _TAIL.size


def _read_exact(src: BinaryIO, n: int) -> bytes:
    data = src.read(n)
    if len(data) != n:
        raise InvalidFormat("Cabecera truncada: el archivo no es un cifrado de pycronk completo.")
    return data


def read_header(src: BinaryIO) -> Header:
    if _read_exact(src, len(MAGIC)) != MAGIC:
        raise InvalidFormat("No es un archivo cifrado con pycronk.")
    version, engine_len = _read_exact(src, 2)
    if version != FORMAT_VERSION:
        raise UnsupportedVersion(
            f"Versión de formato {version} no soportada; actualiza pycronk para abrirlo."
        )
    if engine_len == 0:
        raise InvalidFormat("Cabecera inválida: id de motor vacío.")
    try:
        engine_id = _read_exact(src, engine_len).decode("ascii")
    except UnicodeDecodeError:
        raise InvalidFormat("Cabecera inválida: id de motor no ASCII.") from None
    mode, flags, chunk_symbols = _TAIL.unpack(_read_exact(src, _TAIL.size))
    # Los flags están reservados: aceptar valores desconocidos haría que una versión futura que
    # los use se descifrara mal en silencio con esta versión.
    if flags != 0:
        raise UnsupportedVersion("El archivo usa opciones que esta versión no conoce.")
    try:
        parsed_mode = Mode(mode)
    except ValueError:
        raise InvalidFormat(f"Modo de contenedor desconocido: {mode}.") from None
    return Header(engine_id, parsed_mode, chunk_symbols, version)
