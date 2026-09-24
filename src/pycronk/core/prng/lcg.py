import numpy as np
import numpy.typing as npt

# Constantes de Numerical Recipes: cumplen Hull-Dobell (periodo completo 2^32) y son las que usó
# el prototipo; cambiarlas rompería los archivos cifrados con pycronk-v1.
MULTIPLIER = 1664525
INCREMENT = 1013904223
MODULUS = 2**32
_MASK = np.uint64(MODULUS - 1)

# Bloque del jump-ahead: suficientemente grande para amortizar la llamada a numpy y
# suficientemente pequeño para que las tablas ocupen solo 64 KiB.
_BLOCK = 4096


def _jump_tables(block: int) -> tuple[npt.NDArray[np.uint64], npt.NDArray[np.uint64]]:
    # s_{n+k} = A_k * s_n + C_k (mod 2^32). Precalcular A_k y C_k permite generar k estados
    # de golpe en numpy en lugar de un bucle Python por símbolo.
    a = np.empty(block, dtype=np.uint64)
    c = np.empty(block, dtype=np.uint64)
    ak, ck = MULTIPLIER, INCREMENT
    for k in range(block):
        a[k], c[k] = ak, ck
        ak = (ak * MULTIPLIER) % MODULUS
        ck = (ck * MULTIPLIER + INCREMENT) % MODULUS
    return a, c


_JUMP_A, _JUMP_C = _jump_tables(_BLOCK)


class Lcg32:
    def __init__(self, seed: int) -> None:
        self.state = seed % MODULUS

    def next_states(self, n: int) -> npt.NDArray[np.uint64]:
        """Devuelve los próximos `n` estados y avanza el generador."""
        out = np.empty(n, dtype=np.uint64)
        state = self.state
        for start in range(0, n, _BLOCK):
            k = min(_BLOCK, n - start)
            # A_k * s cabe en 64 bits (ambos < 2^32); si la suma desborda 2^64 el resultado
            # módulo 2^32 sigue siendo correcto porque 2^32 divide a 2^64.
            block = (_JUMP_A[:k] * np.uint64(state) + _JUMP_C[:k]) & _MASK
            out[start : start + k] = block
            state = int(block[-1])
        self.state = state
        return out
