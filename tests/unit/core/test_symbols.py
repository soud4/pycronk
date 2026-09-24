import numpy as np
import pytest

from pycronk.core.errors import InvalidFormat
from pycronk.core.symbols import bytes_to_symbols, pad_to_triplet, symbols_to_bytes


@pytest.mark.parametrize("length", range(8))
def test_round_trip_after_padding(length):
    data = bytes(range(200, 200 + length))
    padded = pad_to_triplet(data)
    assert len(padded) % 3 == 0
    assert padded.startswith(data)
    symbols = bytes_to_symbols(padded)
    assert symbols.dtype == np.uint8
    assert symbols.size == len(padded) // 3 * 4
    assert symbols.size == 0 or int(symbols.max()) < 64
    assert symbols_to_bytes(symbols) == padded


def test_bit_order_is_msb_first():
    # 0b000001_000010_000011_000100 = 0x04 0x20 0xC4
    assert bytes_to_symbols(b"\x04\x20\xc4").tolist() == [1, 2, 3, 4]


def test_rejects_unaligned_input():
    with pytest.raises(InvalidFormat):
        bytes_to_symbols(b"ab")
    with pytest.raises(InvalidFormat):
        symbols_to_bytes(np.zeros(3, dtype=np.uint8))
