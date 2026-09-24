import struct
from collections.abc import Iterator, Sequence
from typing import Any, BinaryIO

from pycronk.core.errors import Cancelled, InvalidFormat
from pycronk.core.interfaces import (
    CancelToken,
    KeyDerivation,
    Keys,
    Layer,
    LayerContext,
    ProgressSink,
)
from pycronk.core.prng.lcg import Lcg32
from pycronk.core.symbols import bytes_to_symbols, pad_to_triplet, symbols_to_bytes
from pycronk.core.trace import LayerStep, Trace

# La longitud original viaja cifrada al principio del flujo (idea del prototipo) para que el
# descifrado no necesite parámetros externos; u64 elimina el límite de ~2 MB de la cabecera de
# 24 bits original.
_LENGTH = struct.Struct(">Q")


def chunk_bytes_for(chunk_symbols: int) -> int:
    # Múltiplo de 4 símbolos = múltiplo de 3 bytes: cada chunk se convierte sin bits sobrantes.
    if chunk_symbols <= 0 or chunk_symbols % 4:
        raise ValueError("Los símbolos por chunk deben ser un múltiplo positivo de 4.")
    return chunk_symbols * 3 // 4


def _read_chunks(src: BinaryIO, chunk_bytes: int, prefix: bytes = b"") -> Iterator[bytes]:
    pending = prefix
    eof = False
    while True:
        while not eof and len(pending) < chunk_bytes:
            data = src.read(chunk_bytes - len(pending))
            if not data:
                eof = True
            pending += data
        if not pending:
            return
        yield pending[:chunk_bytes]
        pending = pending[chunk_bytes:]


def _check(cancel: CancelToken | None) -> None:
    if cancel is not None and cancel.is_cancelled():
        raise Cancelled("Operación cancelada.")


class LayeredEngine:
    """Motor genérico: una KDF + una lista ordenada de capas reversibles."""

    def __init__(
        self,
        engine_id: str,
        title: str,
        kdf: KeyDerivation,
        layers: Sequence[Layer[Any]],
    ) -> None:
        self.id = engine_id
        self.title = title
        self._kdf = kdf
        self._layers = tuple(layers)

    def _context(self, keys: Keys) -> LayerContext:
        keystream_seed = self._kdf.derive(keys.keystream)
        return LayerContext(
            matrix_seed=self._kdf.derive(keys.matrix),
            keystream_seed=keystream_seed,
            prng=Lcg32(keystream_seed),
        )

    def _prepare(self, n: int, ctx: LayerContext) -> list[Any]:
        # Siempre en orden de cifrado: es el orden en que las capas consumen el PRNG compartido.
        return [layer.prepare(n, ctx) for layer in self._layers]

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
    ) -> None:
        ctx = self._context(keys)
        processed = 0
        for index, chunk in enumerate(
            _read_chunks(src, chunk_bytes_for(chunk_symbols), _LENGTH.pack(size))
        ):
            _check(cancel)
            symbols = bytes_to_symbols(pad_to_triplet(chunk))
            params = self._prepare(symbols.size, ctx)
            recorder = trace if index == 0 else None
            if recorder is not None:
                recorder.input_symbols = symbols
                recorder.length_bytes = size
            for layer, layer_params in zip(self._layers, params, strict=True):
                symbols = layer.forward(symbols, layer_params)
                if recorder is not None:
                    recorder.steps.append(
                        LayerStep(layer.id, layer.title, layer.describe(layer_params), symbols)
                    )
            dst.write(symbols_to_bytes(symbols))
            # El primer chunk incluye los 8 bytes de longitud, que no son datos del usuario.
            processed = min(size, processed + len(chunk) - (_LENGTH.size if index == 0 else 0))
            if progress is not None:
                progress(max(processed, 0), size)
        if progress is not None and size == 0:
            progress(0, 0)

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
    ) -> None:
        ctx = self._context(keys)
        processed = 0
        # La longitud puede quedar repartida entre chunks muy pequeños: se acumula hasta tener los
        # 8 bytes antes de empezar a escribir.
        pending = b""
        remaining = -1
        for index, chunk in enumerate(_read_chunks(src, chunk_bytes_for(chunk_symbols))):
            _check(cancel)
            if len(chunk) % 3:
                raise InvalidFormat("El cifrado está truncado o dañado.")
            symbols = bytes_to_symbols(chunk)
            params = self._prepare(symbols.size, ctx)
            recorder = trace if index == 0 else None
            if recorder is not None:
                recorder.input_symbols = symbols
            for layer, layer_params in reversed(list(zip(self._layers, params, strict=True))):
                symbols = layer.inverse(symbols, layer_params)
                if recorder is not None:
                    recorder.steps.append(
                        LayerStep(layer.id, layer.title, layer.describe(layer_params), symbols)
                    )
            plain = symbols_to_bytes(symbols)
            processed += len(chunk)
            if remaining < 0:
                pending += plain
                if len(pending) < _LENGTH.size:
                    continue
                (remaining,) = _LENGTH.unpack_from(pending)
                plain = pending[_LENGTH.size :]
                if trace is not None:
                    trace.length_bytes = remaining
            # Con una clave incorrecta la longitud es basura: se escribe lo disponible y nada más,
            # sin fallar, igual que el prototipo (no hay forma de detectarlo sin un MAC).
            data = plain[:remaining]
            dst.write(data)
            remaining -= len(data)
            if progress is not None:
                progress(processed, size)
        if remaining < 0:
            raise InvalidFormat("El cifrado está vacío o truncado.")
