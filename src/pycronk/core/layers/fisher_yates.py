import numpy as np
import numpy.typing as npt

from pycronk.core.interfaces import LayerContext
from pycronk.core.trace import DetailValue, Symbols

Permutation = npt.NDArray[np.intp]


class FisherYatesLayer:
    id = "fisher-yates"
    title = "Capa 3 — Transposición Fisher-Yates guiada por LCG"

    def prepare(self, n: int, ctx: LayerContext) -> Permutation:
        if n < 2:
            return np.arange(n, dtype=np.intp)
        # Los índices j se calculan vectorizados; solo los intercambios quedan en Python porque
        # cada uno depende del anterior.
        states = ctx.prng.next_states(n - 1)
        bounds = np.arange(n, 1, -1, dtype=np.uint64)
        targets = (states % bounds).tolist()
        pi = list(range(n))
        for i, j in zip(range(n - 1, 0, -1), targets, strict=True):
            pi[i], pi[j] = pi[j], pi[i]
        return np.array(pi, dtype=np.intp)

    def forward(self, symbols: Symbols, params: Permutation) -> Symbols:
        return symbols[params]

    def inverse(self, symbols: Symbols, params: Permutation) -> Symbols:
        restored = np.empty_like(symbols)
        restored[params] = symbols
        return restored

    def describe(self, params: Permutation) -> dict[str, DetailValue]:
        return {"Permutación π": params}
