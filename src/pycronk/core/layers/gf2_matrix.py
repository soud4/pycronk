from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import numpy.typing as npt

from pycronk.core.interfaces import LayerContext
from pycronk.core.trace import DetailValue, Symbols

BLOCK_BITS = 6
_FREE_BITS = BLOCK_BITS * (BLOCK_BITS - 1) // 2  # 15 posiciones libres en cada triangular
_WEIGHTS = np.array([32, 16, 8, 4, 2, 1], dtype=np.int64)


@dataclass(frozen=True)
class Gf2Params:
    matrix: npt.NDArray[np.uint8]
    table: Symbols
    inverse_table: Symbols


def build_matrix(seed: int) -> npt.NDArray[np.uint8]:
    # M = L·U con diagonales a 1 garantiza det(M) = 1 en GF(2): siempre invertible, sin tener que
    # buscar ni rechazar matrices singulares.
    lower = np.eye(BLOCK_BITS, dtype=np.int64)
    upper = np.eye(BLOCK_BITS, dtype=np.int64)
    rows, cols = np.tril_indices(BLOCK_BITS, k=-1)
    lower[rows, cols] = [(seed >> i) & 1 for i in range(_FREE_BITS)]
    # U toma el tramo siguiente de bits para que L y U no compartan información.
    rows, cols = np.triu_indices(BLOCK_BITS, k=1)
    upper[rows, cols] = [(seed >> (_FREE_BITS + i)) & 1 for i in range(_FREE_BITS)]
    return ((lower @ upper) % 2).astype(np.uint8)


def build_table(matrix: npt.NDArray[np.uint8]) -> Symbols:
    # Con bloques de 6 bits solo hay 64 entradas posibles: precalcular S[x] = M·x evita un
    # producto matricial por bloque y convierte la inversa en un simple argsort.
    inputs = (np.arange(64, dtype=np.int64)[:, None] >> _WEIGHTS.size - 1 - np.arange(6)) & 1
    outputs = (inputs @ matrix.T.astype(np.int64)) % 2
    return (outputs @ _WEIGHTS).astype(np.uint8)


@lru_cache(maxsize=32)
def _params_for(seed: int) -> Gf2Params:
    matrix = build_matrix(seed)
    table = build_table(matrix)
    return Gf2Params(matrix, table, np.argsort(table).astype(np.uint8))


class Gf2MatrixLayer:
    id = "gf2-matrix"
    title = "Capa 1 — Transformación matricial sobre GF(2)"

    def prepare(self, n: int, ctx: LayerContext) -> Gf2Params:
        return _params_for(ctx.matrix_seed)

    def forward(self, symbols: Symbols, params: Gf2Params) -> Symbols:
        return params.table[symbols]

    def inverse(self, symbols: Symbols, params: Gf2Params) -> Symbols:
        return params.inverse_table[symbols]

    def describe(self, params: Gf2Params) -> dict[str, DetailValue]:
        rows = "\n".join(" ".join(str(bit) for bit in row) for row in params.matrix)
        return {"Matriz M = L·U": rows, "Tabla de sustitución S[x]": params.table}
