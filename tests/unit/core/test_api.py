import io

import pytest

from pycronk.core.api import DEFAULT_ENGINE_ID, Cryptor, default_engines
from pycronk.core.armor.base64_armor import Base64Armor
from pycronk.core.container import Mode, read_header
from pycronk.core.errors import InvalidFormat, UnknownEngine
from pycronk.core.interfaces import Keys
from pycronk.core.trace import Trace

cryptor = Cryptor.default()


@pytest.mark.parametrize("text", ["", "a", "Hola mundo!", "ñandú — ✓ 漢字", "x" * 5000])
def test_text_round_trip(keys, text):
    armored = cryptor.encrypt_text(text, keys)
    assert cryptor.looks_encrypted(armored)
    assert cryptor.decrypt_text(armored, keys) == text


def test_bytes_round_trip_with_small_chunks(keys):
    data = bytes(range(256)) * 10
    blob = cryptor.encrypt_bytes(data, keys, chunk_symbols=8)
    assert cryptor.decrypt_bytes(blob, keys) == data


def test_header_records_engine_and_mode(keys):
    blob = cryptor.encrypt_bytes(b"x", keys, mode=Mode.TEXT, chunk_symbols=64)
    header = read_header(io.BytesIO(blob))
    assert header.engine_id == DEFAULT_ENGINE_ID
    assert header.mode is Mode.TEXT
    assert header.chunk_symbols == 64


def test_file_output_has_no_base64_overhead(keys):
    data = bytes(3000)
    blob = cryptor.encrypt_bytes(data, keys)
    header = read_header(io.BytesIO(blob))
    assert len(blob) - header.size == 3000 + 9  # + u64 de longitud + relleno a múltiplo de 3


def test_decrypt_picks_engine_from_header(keys):
    blob = cryptor.encrypt_bytes(b"data", keys)
    other = Cryptor(default_engines(), Base64Armor())
    assert other.decrypt_bytes(blob, keys) == b"data"


def test_unknown_engine(keys):
    with pytest.raises(UnknownEngine):
        cryptor.encrypt_bytes(b"x", keys, engine_id="no-existe")
    blob = bytearray(cryptor.encrypt_bytes(b"x", keys))
    blob[6:16] = b"pycronk-v9"
    with pytest.raises(UnknownEngine):
        cryptor.decrypt_bytes(bytes(blob), keys)


def test_invalid_chunk_writes_nothing(keys):
    out = io.BytesIO()
    with pytest.raises(ValueError):
        cryptor.encrypt_stream(io.BytesIO(b"x"), out, size=1, keys=keys, chunk_symbols=6)
    assert out.getvalue() == b""


def test_invalid_text_input(keys):
    with pytest.raises(InvalidFormat):
        cryptor.decrypt_text("texto normal", keys)


def test_wrong_keys_produce_garbage_not_errors(keys):
    armored = cryptor.encrypt_text("secreto", keys)
    assert cryptor.decrypt_text(armored, Keys("a", "b")) != "secreto"


def test_trace_available_for_text(keys):
    trace = Trace()
    cryptor.encrypt_text("hola", keys, trace=trace)
    assert len(trace.steps) == 3


def test_default_engines_lists_v1():
    assert default_engines().ids() == [DEFAULT_ENGINE_ID]
