"""Puntos de extensión del núcleo (spec 002). Todo lo reemplazable entra por aquí."""

from dataclasses import dataclass
from typing import BinaryIO, Protocol

from pycronk.core.prng.lcg import Lcg32
from pycronk.core.trace import DetailValue, Symbols, Trace


@dataclass(frozen=True)
class Keys:
    matrix: str
    keystream: str


@dataclass
class LayerContext:
    """Estado compartido por las capas durante una operación.

    `prng` es mutable a propósito: las capas 2 y 3 deben continuar la misma secuencia, también
    entre chunks, y compartir el objeto es la forma más directa de garantizarlo.
    """

    matrix_seed: int
    keystream_seed: int
    prng: Lcg32


class KeyDerivation(Protocol):
    id: str

    def derive(self, password: str) -> int: ...


class Layer[P](Protocol):
    """Transformación reversible sobre símbolos de 6 bits.

    Contrato: `inverse(forward(x, p), p) == x` para los mismos `p = prepare(len(x), ctx)`.
    `prepare` se llama siempre en orden de cifrado, también al descifrar, porque es la que consume
    el PRNG compartido.
    """

    id: str
    title: str

    def prepare(self, n: int, ctx: LayerContext) -> P: ...

    def forward(self, symbols: Symbols, params: P) -> Symbols: ...

    def inverse(self, symbols: Symbols, params: P) -> Symbols: ...

    def describe(self, params: P) -> dict[str, DetailValue]: ...


class ProgressSink(Protocol):
    def __call__(self, done: int, total: int) -> None: ...


class CancelToken(Protocol):
    def is_cancelled(self) -> bool: ...


class CipherEngine(Protocol):
    """Algoritmo completo sobre el payload (la cabecera del contenedor la gestiona `api`)."""

    id: str
    title: str

    def encrypt_stream(
        self,
        src: BinaryIO,
        dst: BinaryIO,
        *,
        size: int,
        keys: Keys,
        chunk_symbols: int,
        progress: ProgressSink | None = None,
        cancel: CancelToken | None = None,
        trace: Trace | None = None,
    ) -> None: ...

    def decrypt_stream(
        self,
        src: BinaryIO,
        dst: BinaryIO,
        *,
        size: int,
        keys: Keys,
        chunk_symbols: int,
        progress: ProgressSink | None = None,
        cancel: CancelToken | None = None,
        trace: Trace | None = None,
    ) -> None: ...


class TextArmor(Protocol):
    id: str

    def encode(self, payload: bytes) -> str: ...

    def decode(self, text: str) -> bytes: ...

    def detects(self, text: str) -> bool: ...


class CancelFlag:
    """Implementación mínima de `CancelToken`; la UI la marca desde otro hilo."""

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def is_cancelled(self) -> bool:
        return self._cancelled
