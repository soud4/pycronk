"""Conversión bytes ⇄ símbolos de 6 bits.

Se trabaja siempre en grupos de 3 bytes = 4 símbolos: así la conversión es exacta en ambos
sentidos y no hace falta arrastrar bits sueltos entre chunks.
"""

import numpy as np

from pycronk.core.errors import InvalidFormat
from pycronk.core.trace import Symbols

SYMBOL_BITS = 6
ALPHABET_SIZE = 64


def pad_to_triplet(data: bytes) -> bytes:
    remainder = len(data) % 3
    return data + b"\x00" * (3 - remainder) if remainder else data


def bytes_to_symbols(data: bytes) -> Symbols:
    if len(data) % 3:
        raise InvalidFormat("La longitud debe ser múltiplo de 3 bytes.")
    groups = np.frombuffer(data, dtype=np.uint8).reshape(-1, 3).astype(np.uint32)
    word = (groups[:, 0] << 16) | (groups[:, 1] << 8) | groups[:, 2]
    shifts = np.array([18, 12, 6, 0], dtype=np.uint32)
    return ((word[:, None] >> shifts) & 0x3F).astype(np.uint8).reshape(-1)


def symbols_to_bytes(symbols: Symbols) -> bytes:
    if symbols.size % 4:
        raise InvalidFormat("La cantidad de símbolos debe ser múltiplo de 4.")
    quads = symbols.reshape(-1, 4).astype(np.uint32)
    word = (quads[:, 0] << 18) | (quads[:, 1] << 12) | (quads[:, 2] << 6) | quads[:, 3]
    out = np.stack([(word >> 16) & 0xFF, (word >> 8) & 0xFF, word & 0xFF], axis=1)
    return out.astype(np.uint8).tobytes()
