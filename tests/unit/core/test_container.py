import io

import pytest

from pycronk.core.container import MAGIC, Header, Mode, read_header
from pycronk.core.errors import InvalidFormat, UnsupportedVersion


def encoded(**overrides) -> bytes:
    fields = {"engine_id": "pycronk-v1", "mode": Mode.FILE, "chunk_symbols": 1024} | overrides
    return Header(**fields).encode()


def test_round_trip():
    header = Header("pycronk-v1", Mode.TEXT, 4096)
    raw = header.encode()
    assert len(raw) == header.size
    stream = io.BytesIO(raw + b"payload")
    assert read_header(stream) == header
    assert stream.read() == b"payload"


def test_rejects_wrong_magic():
    with pytest.raises(InvalidFormat):
        read_header(io.BytesIO(b"NOPE" + encoded()[4:]))


def test_rejects_unknown_version():
    raw = bytearray(encoded())
    raw[len(MAGIC)] = 99
    with pytest.raises(UnsupportedVersion):
        read_header(io.BytesIO(bytes(raw)))


@pytest.mark.parametrize("cut", [0, 3, 5, 8, 15])
def test_rejects_truncated_header(cut):
    with pytest.raises(InvalidFormat):
        read_header(io.BytesIO(encoded()[:cut]))


def test_rejects_unknown_flags():
    raw = bytearray(encoded())
    raw[-5] = 1  # byte de flags, justo antes del u32 final
    with pytest.raises(UnsupportedVersion):
        read_header(io.BytesIO(bytes(raw)))


def test_rejects_unknown_mode():
    raw = bytearray(encoded())
    raw[-6] = 7
    with pytest.raises(InvalidFormat):
        read_header(io.BytesIO(bytes(raw)))


def test_rejects_empty_or_non_ascii_engine_id():
    with pytest.raises(InvalidFormat):
        read_header(io.BytesIO(MAGIC + bytes([1, 0]) + b"\x00" * 6))
    with pytest.raises(InvalidFormat):
        read_header(io.BytesIO(MAGIC + bytes([1, 1]) + b"\xff" + b"\x00" * 6))


def test_encode_rejects_invalid_engine_id():
    with pytest.raises(ValueError):
        Header("", Mode.FILE, 4).encode()
    with pytest.raises(ValueError):
        Header("x" * 256, Mode.FILE, 4).encode()
