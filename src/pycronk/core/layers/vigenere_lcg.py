import numpy as np

from pycronk.core.interfaces import LayerContext
from pycronk.core.trace import DetailValue, Symbols


class VigenereLcgLayer:
    id = "vigenere-lcg"
    title = "Capa 2 — Vigenère con keystream LCG"

    def prepare(self, n: int, ctx: LayerContext) -> Symbols:
        # `mod 64` (bits bajos) replica al prototipo; es una debilidad conocida documentada en la
        # spec 003 y se corrige en un motor futuro, no aquí, para no romper pycronk-v1.
        return (ctx.prng.next_states(n) & 0x3F).astype(np.uint8)

    def forward(self, symbols: Symbols, params: Symbols) -> Symbols:
        return ((symbols + params) & 0x3F).astype(np.uint8, copy=False)

    def inverse(self, symbols: Symbols, params: Symbols) -> Symbols:
        # Se resta en uint8 aprovechando el desborde: (a - b) & 63 da el resultado mod 64.
        return ((symbols - params) & 0x3F).astype(np.uint8, copy=False)

    def describe(self, params: Symbols) -> dict[str, DetailValue]:
        return {"Keystream": params}
