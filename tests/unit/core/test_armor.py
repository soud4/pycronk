import pytest
from hypothesis import given
from hypothesis import strategies as st

from pycronk.core.armor.base64_armor import PREFIX, Base64Armor
from pycronk.core.errors import InvalidFormat

armor = Base64Armor()


@given(st.binary(max_size=500))
def test_round_trip(payload):
    assert armor.decode(armor.encode(payload)) == payload


def test_tolerates_line_breaks():
    text = armor.encode(b"hola mundo, esto es largo")
    wrapped = "\n".join(text[i : i + 10] for i in range(0, len(text), 10))
    assert armor.decode("  " + wrapped + "\n") == b"hola mundo, esto es largo"


def test_detects():
    assert armor.detects(armor.encode(b"x"))
    assert armor.detects("   " + PREFIX + "AAAA")
    assert not armor.detects("hola")


@pytest.mark.parametrize("text", ["hola", PREFIX + "###", PREFIX + "QUJD="])
def test_rejects_invalid(text):
    with pytest.raises(InvalidFormat):
        armor.decode(text)
