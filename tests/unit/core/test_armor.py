import base64

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pycronk.core.armor.base64_armor import B64_MAGIC, LEGACY_PREFIX, Base64Armor
from pycronk.core.container import MAGIC
from pycronk.core.errors import InvalidFormat

armor = Base64Armor()

# El armor solo transporta contenedores, así que las propiedades se comprueban sobre payloads
# que empiezan por el magic; sin él, `decode` rechaza por diseño.
containers = st.binary(max_size=500).map(lambda rest: MAGIC + rest)


@given(containers)
def test_round_trip(payload):
    assert armor.decode(armor.encode(payload)) == payload


def test_no_prefix():
    assert not armor.encode(MAGIC + b"x").startswith(LEGACY_PREFIX)


@given(containers)
def test_decodes_legacy_prefix(payload):
    assert armor.decode(LEGACY_PREFIX + armor.encode(payload)) == payload


def test_tolerates_line_breaks():
    text = armor.encode(MAGIC + b"hola mundo, esto es largo")
    wrapped = "\n".join(text[i : i + 10] for i in range(0, len(text), 10))
    assert armor.decode("  " + wrapped + "\n") == MAGIC + b"hola mundo, esto es largo"


def test_detects():
    assert armor.detects(armor.encode(MAGIC + b"x"))
    assert armor.detects("   " + armor.encode(MAGIC + b"x"))
    assert armor.detects("   " + LEGACY_PREFIX + "AAAA")
    assert not armor.detects("hola")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("hola", "no es un cifrado"),
        (LEGACY_PREFIX + "###", "no es un cifrado"),
        # Base64 válido, pero el contenedor no es de pycronk
        (base64.b64encode(b"hola mundo").decode(), "no es un cifrado"),
        # empieza por el magic en Base64, pero el 4.º byte del magic no cuadra
        (base64.b64encode(b"PCRX" + bytes(8)).decode(), "no es un cifrado"),
        # cortado por la mitad de un grupo Base64; una poda en frontera de grupo sigue siendo
        # Base64 válido y la detecta `read_header`, no el armor
        (armor.encode(MAGIC + b"relleno")[:-3], "dañado"),
        (B64_MAGIC + "@@", "dañado"),  # caracteres inválidos
    ],
)
def test_rejects_invalid(text, message):
    with pytest.raises(InvalidFormat, match=message):
        armor.decode(text)
