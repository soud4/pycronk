"""Fachada pública del núcleo: contenedor + registro de motores + armor de texto."""

import io
from typing import BinaryIO

from pycronk.core.armor.base64_armor import Base64Armor
from pycronk.core.container import Header, Mode, read_header
from pycronk.core.errors import UnknownEngine
from pycronk.core.interfaces import CancelToken, CipherEngine, Keys, ProgressSink, TextArmor
from pycronk.core.kdf.polybius import PolybiusKdf
from pycronk.core.layers.fisher_yates import FisherYatesLayer
from pycronk.core.layers.gf2_matrix import Gf2MatrixLayer
from pycronk.core.layers.vigenere_lcg import VigenereLcgLayer
from pycronk.core.pipeline import LayeredEngine, chunk_bytes_for
from pycronk.core.registry import Registry
from pycronk.core.trace import Trace

# 2^16 símbolos = 48 KiB en claro por chunk. Fisher-Yates es un bucle Python con accesos aleatorios:
# con chunks que caben en la caché L2 va ~1.6x más rápido que con 2^20 (medido: 1.9 vs 1.2 MB/s).
# El tamaño viaja en la cabecera, así que cambiarlo no rompe archivos ya cifrados.
DEFAULT_CHUNK_SYMBOLS = 1 << 16
DEFAULT_ENGINE_ID = "pycronk-v1"


def default_engines() -> Registry[CipherEngine]:
    engines: Registry[CipherEngine] = Registry(UnknownEngine)
    engines.register(
        DEFAULT_ENGINE_ID,
        LayeredEngine(
            DEFAULT_ENGINE_ID,
            "pycronk v1 (educativo)",
            PolybiusKdf(),
            [Gf2MatrixLayer(), VigenereLcgLayer(), FisherYatesLayer()],
        ),
    )
    return engines


class Cryptor:
    def __init__(self, engines: Registry[CipherEngine], armor: TextArmor) -> None:
        self.engines = engines
        self.armor = armor

    @classmethod
    def default(cls) -> "Cryptor":
        return cls(default_engines(), Base64Armor())

    def encrypt_stream(
        self,
        src: BinaryIO,
        dst: BinaryIO,
        *,
        size: int,
        keys: Keys,
        engine_id: str = DEFAULT_ENGINE_ID,
        mode: Mode = Mode.FILE,
        chunk_symbols: int = DEFAULT_CHUNK_SYMBOLS,
        progress: ProgressSink | None = None,
        cancel: CancelToken | None = None,
        trace: Trace | None = None,
    ) -> None:
        engine = self.engines.get(engine_id)
        chunk_bytes_for(chunk_symbols)  # validar antes de escribir nada en dst
        dst.write(Header(engine_id, mode, chunk_symbols).encode())
        engine.encrypt_stream(
            src,
            dst,
            size=size,
            keys=keys,
            chunk_symbols=chunk_symbols,
            progress=progress,
            cancel=cancel,
            trace=trace,
        )

    def decrypt_stream(
        self,
        src: BinaryIO,
        dst: BinaryIO,
        *,
        size: int,
        keys: Keys,
        progress: ProgressSink | None = None,
        cancel: CancelToken | None = None,
        trace: Trace | None = None,
    ) -> Header:
        header = read_header(src)
        engine = self.engines.get(header.engine_id)
        engine.decrypt_stream(
            src,
            dst,
            size=size - header.size,
            keys=keys,
            chunk_symbols=header.chunk_symbols,
            progress=progress,
            cancel=cancel,
            trace=trace,
        )
        return header

    def encrypt_bytes(
        self,
        data: bytes,
        keys: Keys,
        *,
        engine_id: str = DEFAULT_ENGINE_ID,
        mode: Mode = Mode.FILE,
        chunk_symbols: int = DEFAULT_CHUNK_SYMBOLS,
        trace: Trace | None = None,
    ) -> bytes:
        out = io.BytesIO()
        self.encrypt_stream(
            io.BytesIO(data),
            out,
            size=len(data),
            keys=keys,
            engine_id=engine_id,
            mode=mode,
            chunk_symbols=chunk_symbols,
            trace=trace,
        )
        return out.getvalue()

    def decrypt_bytes(self, blob: bytes, keys: Keys, *, trace: Trace | None = None) -> bytes:
        out = io.BytesIO()
        self.decrypt_stream(io.BytesIO(blob), out, size=len(blob), keys=keys, trace=trace)
        return out.getvalue()

    def encrypt_text(
        self,
        text: str,
        keys: Keys,
        *,
        engine_id: str = DEFAULT_ENGINE_ID,
        trace: Trace | None = None,
    ) -> str:
        blob = self.encrypt_bytes(
            text.encode("utf-8"), keys, engine_id=engine_id, mode=Mode.TEXT, trace=trace
        )
        return self.armor.encode(blob)

    def decrypt_text(self, armored: str, keys: Keys, *, trace: Trace | None = None) -> str:
        plain = self.decrypt_bytes(self.armor.decode(armored), keys, trace=trace)
        # `replace` en vez de `strict`: con claves incorrectas el resultado es basura por diseño
        # (spec 003) y mostrarla es más didáctico que un error de decodificación.
        return plain.decode("utf-8", errors="replace")

    def looks_encrypted(self, text: str) -> bool:
        return self.armor.detects(text)
