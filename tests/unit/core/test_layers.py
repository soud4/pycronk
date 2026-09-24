import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from pycronk.core.interfaces import LayerContext
from pycronk.core.kdf.polybius import PolybiusKdf
from pycronk.core.layers.fisher_yates import FisherYatesLayer
from pycronk.core.layers.gf2_matrix import Gf2MatrixLayer, build_matrix, build_table
from pycronk.core.layers.vigenere_lcg import VigenereLcgLayer
from pycronk.core.prng.lcg import Lcg32

kdf = PolybiusKdf()
symbols_strategy = st.lists(st.integers(0, 63), max_size=300).map(
    lambda v: np.array(v, dtype=np.uint8)
)


def context(matrix_pw: str = "MAR7", keystream_pw: str = "otra") -> LayerContext:
    seed = kdf.derive(keystream_pw)
    return LayerContext(kdf.derive(matrix_pw), seed, Lcg32(seed))


def gf2_det(matrix: np.ndarray) -> int:
    m = matrix.copy() % 2
    n = m.shape[0]
    for col in range(n):
        pivot = next((r for r in range(col, n) if m[r, col]), None)
        if pivot is None:
            return 0
        m[[col, pivot]] = m[[pivot, col]]
        for r in range(n):
            if r != col and m[r, col]:
                m[r] ^= m[col]
    return 1


# --- Capa 1 -----------------------------------------------------------------


def test_gf2_matrix_and_table_match_prototype(vectors):
    for case in vectors["cases"]:
        matrix = build_matrix(vectors["kdf"][case["password_matrix"]])
        assert matrix.tolist() == case["matrix"]
        assert build_table(matrix).tolist() == case["substitution_table"]


def test_gf2_layer1_symbols_match_prototype(vectors):
    from pycronk.core.symbols import bytes_to_symbols, pad_to_triplet

    layer = Gf2MatrixLayer()
    for case in vectors["cases"]:
        data = pad_to_triplet(case["message"].encode("utf-8"))
        params = layer.prepare(0, context(case["password_matrix"]))
        out = layer.forward(bytes_to_symbols(data), params).tolist()
        expected = case["layer1_symbols"]
        # El prototipo rellenaba a múltiplo de 6 bits; aquí se rellena a múltiplo de 3 bytes,
        # así que solo pueden sobrar símbolos al final.
        assert out[: len(expected)] == expected


@given(st.integers(min_value=0, max_value=2**61))
def test_gf2_matrix_always_invertible_and_table_is_permutation(seed):
    matrix = build_matrix(seed)
    assert gf2_det(matrix) == 1
    assert sorted(build_table(matrix).tolist()) == list(range(64))


@given(symbols_strategy)
def test_gf2_round_trip(symbols):
    layer = Gf2MatrixLayer()
    params = layer.prepare(symbols.size, context())
    assert np.array_equal(layer.inverse(layer.forward(symbols, params), params), symbols)


def test_gf2_describe_exposes_matrix_and_table():
    layer = Gf2MatrixLayer()
    details = layer.describe(layer.prepare(0, context()))
    assert set(details) == {"Matriz M = L·U", "Tabla de sustitución S[x]"}


# --- Capa 2 -----------------------------------------------------------------


def test_vigenere_keystream_matches_prototype(vectors):
    layer = VigenereLcgLayer()
    for case in vectors["cases"]:
        ks = layer.prepare(40, context(keystream_pw=case["password_keystream"]))
        assert ks.tolist() == case["keystream_40"]


@given(symbols_strategy)
def test_vigenere_round_trip_and_range(symbols):
    layer = VigenereLcgLayer()
    ks = layer.prepare(symbols.size, context())
    encrypted = layer.forward(symbols, ks)
    assert encrypted.dtype == np.uint8
    assert encrypted.size == 0 or encrypted.max() < 64
    assert np.array_equal(layer.inverse(encrypted, ks), symbols)


def test_vigenere_empty_input():
    layer = VigenereLcgLayer()
    ks = layer.prepare(0, context())
    assert layer.forward(np.array([], dtype=np.uint8), ks).size == 0


# --- Capa 3 -----------------------------------------------------------------


def test_fisher_yates_matches_prototype(vectors):
    layer = FisherYatesLayer()
    for case in vectors["cases"]:
        ctx = context(keystream_pw=case["password_keystream"])
        ctx.prng.next_states(40)  # la capa 2 consume primero el keystream
        assert layer.prepare(40, ctx).tolist() == case["permutation_40"]


@pytest.mark.parametrize("n", [0, 1, 2, 5, 64, 1000])
def test_fisher_yates_is_permutation(n):
    pi = FisherYatesLayer().prepare(n, context())
    assert sorted(pi.tolist()) == list(range(n))


@given(symbols_strategy)
def test_fisher_yates_round_trip(symbols):
    layer = FisherYatesLayer()
    pi = layer.prepare(symbols.size, context())
    assert np.array_equal(layer.inverse(layer.forward(symbols, pi), pi), symbols)


def test_fisher_yates_consumes_n_minus_one_states():
    ctx = context()
    FisherYatesLayer().prepare(10, ctx)
    reference = Lcg32(ctx.keystream_seed)
    reference.next_states(9)
    assert ctx.prng.state == reference.state
