from hypothesis import given
from hypothesis import strategies as st

from pycronk.core.kdf.polybius import PolybiusKdf

kdf = PolybiusKdf()


def test_matches_prototype(vectors):
    for password, expected in vectors["kdf"].items():
        assert kdf.derive(password) == expected


def test_is_case_insensitive():
    assert kdf.derive("abc") == kdf.derive("ABC")


def test_empty_password_is_zero():
    assert kdf.derive("") == 0


def test_characters_outside_alphabet_contribute():
    assert kdf.derive("a!") != kdf.derive("a")
    assert kdf.derive("ñ") != 0


@given(st.text(min_size=1, max_size=40))
def test_is_deterministic_and_bounded(password):
    value = kdf.derive(password)
    assert value == kdf.derive(password)
    assert 0 <= value < 2**61 - 1


def test_single_character_change_changes_seed():
    assert kdf.derive("clave1") != kdf.derive("clave2")
