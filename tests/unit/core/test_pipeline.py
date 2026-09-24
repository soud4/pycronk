import io
import os

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pycronk.core.errors import Cancelled, InvalidFormat
from pycronk.core.interfaces import CancelFlag, Keys
from pycronk.core.kdf.polybius import PolybiusKdf
from pycronk.core.layers.fisher_yates import FisherYatesLayer
from pycronk.core.layers.gf2_matrix import Gf2MatrixLayer
from pycronk.core.layers.vigenere_lcg import VigenereLcgLayer
from pycronk.core.pipeline import LayeredEngine, chunk_bytes_for
from pycronk.core.trace import Trace

CHUNK = 16  # símbolos = 12 bytes: fuerza varios chunks con entradas pequeñas
LAYERS = [Gf2MatrixLayer(), VigenereLcgLayer(), FisherYatesLayer()]
engine = LayeredEngine("test", "Test", PolybiusKdf(), LAYERS)


def encrypt(data: bytes, keys: Keys, chunk: int = CHUNK, **kw) -> bytes:
    out = io.BytesIO()
    engine.encrypt_stream(
        io.BytesIO(data), out, size=len(data), keys=keys, chunk_symbols=chunk, **kw
    )
    return out.getvalue()


def decrypt(blob: bytes, keys: Keys, chunk: int = CHUNK, **kw) -> bytes:
    out = io.BytesIO()
    engine.decrypt_stream(
        io.BytesIO(blob), out, size=len(blob), keys=keys, chunk_symbols=chunk, **kw
    )
    return out.getvalue()


@settings(max_examples=60)
@given(
    st.binary(max_size=400),
    st.text(max_size=12),
    st.text(max_size=12),
    st.sampled_from([4, 8, 16, 1024]),
)
def test_round_trip_any_input(data, matrix_pw, keystream_pw, chunk):
    keys = Keys(matrix_pw, keystream_pw)
    assert decrypt(encrypt(data, keys, chunk), keys, chunk) == data


@pytest.mark.parametrize("delta", [-1, 0, 1])
@pytest.mark.parametrize("chunks", [1, 2, 3])
def test_chunk_boundaries(keys, delta, chunks):
    # 8 bytes de la cabecera de longitud forman parte del primer chunk.
    size = max(0, chunk_bytes_for(CHUNK) * chunks - 8 + delta)
    data = os.urandom(size)
    blob = encrypt(data, keys)
    assert len(blob) % 3 == 0
    assert decrypt(blob, keys) == data


def test_empty_input(keys):
    assert decrypt(encrypt(b"", keys), keys) == b""


def test_is_deterministic(keys):
    assert encrypt(b"mismo mensaje", keys) == encrypt(b"mismo mensaje", keys)


def test_different_keys_change_ciphertext(keys):
    assert encrypt(b"mensaje", keys) != encrypt(b"mensaje", Keys("otra", keys.keystream))
    assert encrypt(b"mensaje", keys) != encrypt(b"mensaje", Keys(keys.matrix, "otra"))


def test_wrong_keys_do_not_recover_plaintext(keys):
    data = b"informacion secreta de prueba" * 4
    assert decrypt(encrypt(data, keys), Keys("mala", "clave")) != data


def test_progress_is_monotonic_and_complete(keys):
    data = os.urandom(200)
    calls: list[tuple[int, int]] = []
    blob = encrypt(data, keys, progress=lambda d, t: calls.append((d, t)))
    done = [d for d, _ in calls]
    assert done == sorted(done)
    assert calls[-1] == (200, 200)

    calls.clear()
    decrypt(blob, keys, progress=lambda d, t: calls.append((d, t)))
    assert calls[-1] == (len(blob), len(blob))


def test_progress_reports_empty_input(keys):
    calls: list[tuple[int, int]] = []
    encrypt(b"", keys, progress=lambda d, t: calls.append((d, t)))
    assert calls[-1] == (0, 0)


def test_cancel_stops_encryption(keys):
    flag = CancelFlag()
    flag.cancel()
    with pytest.raises(Cancelled):
        encrypt(os.urandom(100), keys, cancel=flag)


def test_cancel_midway(keys):
    flag = CancelFlag()

    def progress(done: int, total: int) -> None:
        if done > 20:
            flag.cancel()

    with pytest.raises(Cancelled):
        encrypt(os.urandom(500), keys, progress=progress, cancel=flag)


def test_trace_records_first_chunk_in_order(keys):
    trace = Trace()
    blob = encrypt(b"hola", keys, chunk=1024, trace=trace)
    assert [s.layer_id for s in trace.steps] == [layer.id for layer in LAYERS]
    assert trace.length_bytes == 4
    assert trace.input_symbols is not None

    back = Trace()
    decrypt(blob, keys, chunk=1024, trace=back)
    assert [s.layer_id for s in back.steps] == [layer.id for layer in reversed(LAYERS)]
    assert back.length_bytes == 4
    assert np.array_equal(back.steps[-1].output, trace.input_symbols)


def test_trace_is_optional(keys):
    assert decrypt(encrypt(b"abc", keys, trace=None), keys) == b"abc"


def test_decrypt_rejects_truncated_payload(keys):
    with pytest.raises(InvalidFormat):
        decrypt(b"", keys)
    with pytest.raises(InvalidFormat):
        decrypt(encrypt(b"abcdef", keys)[:-1], keys)
    with pytest.raises(InvalidFormat):
        decrypt(encrypt(b"", keys)[:3], keys, chunk=4)


@pytest.mark.parametrize("chunk", [0, -4, 6])
def test_invalid_chunk_size(chunk):
    with pytest.raises(ValueError):
        chunk_bytes_for(chunk)
