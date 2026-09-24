import io
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import BinaryIO

from pycronk.core.api import Cryptor
from pycronk.core.container import read_header
from pycronk.core.errors import Cancelled
from pycronk.core.interfaces import CancelToken, Keys, ProgressSink
from pycronk.core.trace import Trace
from pycronk.services.models import HistoryEntry, Kind, Operation, Status
from pycronk.services.ports import Clock, HistoryRepository
from pycronk.services.settings import Settings

ENCRYPTED_SUFFIX = ".pcrk"
# La traza es para leerla en pantalla: más allá de unos KB solo produce listas ilegibles y
# ralentiza la UI al dibujarlas.
TRACE_LIMIT_BYTES = 4096


@dataclass(frozen=True)
class TextOutcome:
    text: str
    trace: Trace | None


@dataclass
class _Record:
    engine_id: str
    output_path: str = ""


class CryptoService:
    """Casos de uso de cifrado. Cada operación queda registrada en el historial (si está activo),
    incluso cuando falla o se cancela, para que el usuario vea qué ocurrió."""

    def __init__(
        self,
        cryptor: Cryptor,
        history: HistoryRepository,
        clock: Clock,
        settings: Callable[[], Settings],
    ) -> None:
        self._cryptor = cryptor
        self._history = history
        self._clock = clock
        # Se recibe una función y no un valor para leer siempre los ajustes vigentes sin tener
        # que recrear el servicio cuando el usuario los cambia.
        self._settings = settings

    @property
    def cryptor(self) -> Cryptor:
        return self._cryptor

    # --- Texto ------------------------------------------------------------

    def encrypt_text(self, text: str, keys: Keys, *, trace: bool = False) -> TextOutcome:
        engine_id = self._settings().engine_id
        size = len(text.encode("utf-8"))
        collector = Trace() if trace and size <= TRACE_LIMIT_BYTES else None
        with self._tracked(Operation.ENCRYPT, Kind.TEXT, f"Texto ({size} B)", size, engine_id):
            result = self._cryptor.encrypt_text(text, keys, engine_id=engine_id, trace=collector)
        return TextOutcome(result, collector)

    def decrypt_text(self, armored: str, keys: Keys, *, trace: bool = False) -> TextOutcome:
        size = len(armored)
        collector = Trace() if trace and size <= TRACE_LIMIT_BYTES * 2 else None
        with self._tracked(Operation.DECRYPT, Kind.TEXT, f"Texto ({size} B)", size, "") as record:
            result = self._cryptor.decrypt_text(armored, keys, trace=collector)
            record.engine_id = self._engine_of_text(armored)
        return TextOutcome(result, collector)

    # --- Archivos ---------------------------------------------------------

    def encrypt_file(
        self,
        src: Path,
        keys: Keys,
        *,
        dst: Path | None = None,
        progress: ProgressSink | None = None,
        cancel: CancelToken | None = None,
    ) -> Path:
        target = dst or self.suggest_output(src, Operation.ENCRYPT)
        settings = self._settings()
        size = src.stat().st_size
        with self._tracked(Operation.ENCRYPT, Kind.FILE, src.name, size, settings.engine_id) as rec:
            rec.output_path = str(target)
            with self._atomic_output(target) as out, src.open("rb") as inp:
                self._cryptor.encrypt_stream(
                    inp,
                    out,
                    size=size,
                    keys=keys,
                    engine_id=settings.engine_id,
                    chunk_symbols=settings.chunk_symbols,
                    progress=progress,
                    cancel=cancel,
                )
        return target

    def decrypt_file(
        self,
        src: Path,
        keys: Keys,
        *,
        dst: Path | None = None,
        progress: ProgressSink | None = None,
        cancel: CancelToken | None = None,
    ) -> Path:
        target = dst or self.suggest_output(src, Operation.DECRYPT)
        size = src.stat().st_size
        with self._tracked(Operation.DECRYPT, Kind.FILE, src.name, size, "") as rec:
            rec.output_path = str(target)
            with self._atomic_output(target) as out, src.open("rb") as inp:
                header = self._cryptor.decrypt_stream(
                    inp, out, size=size, keys=keys, progress=progress, cancel=cancel
                )
            rec.engine_id = header.engine_id
        return target

    def suggest_output(self, src: Path, operation: Operation) -> Path:
        folder = Path(self._settings().output_dir or src.parent)
        if operation is Operation.ENCRYPT:
            name = src.name + ENCRYPTED_SUFFIX
        elif src.suffix == ENCRYPTED_SUFFIX:
            name = src.stem
        else:
            name = src.name + ".descifrado"
        return _unique(folder / name)

    # --- Historial --------------------------------------------------------

    def purge_history(self) -> int:
        days = self._settings().history_retention_days
        if days == 0:  # 0 = conservar para siempre
            return 0
        return self._history.purge_older_than(self._clock.now() - timedelta(days=days))

    @contextmanager
    def _tracked(
        self, operation: Operation, kind: Kind, label: str, size: int, engine_id: str
    ) -> Generator[_Record]:
        record = _Record(engine_id)
        started_at = self._clock.now()
        # perf_counter mide la duración real; el reloj inyectable solo marca la fecha. Se usan
        # ambos para que los tests puedan fijar la fecha sin depender del tiempo de ejecución.
        start = time.perf_counter()
        status = Status.ERROR
        try:
            yield record
            status = Status.OK
        except Cancelled:
            status = Status.CANCELLED
            raise
        finally:
            if self._settings().history_enabled:
                self._history.add(
                    HistoryEntry(
                        created_at=started_at,
                        operation=operation,
                        kind=kind,
                        engine_id=record.engine_id or "desconocido",
                        status=status,
                        label=label,
                        input_size=size,
                        output_path=record.output_path,
                        duration_ms=int((time.perf_counter() - start) * 1000),
                    )
                )

    @contextmanager
    def _atomic_output(self, target: Path) -> Generator[BinaryIO]:
        # Se escribe en un .part y se renombra al final: si algo falla o se cancela, nunca queda
        # un archivo a medio escribir con el nombre definitivo.
        partial = target.with_name(target.name + ".part")
        try:
            with partial.open("wb") as out:
                yield out
            partial.replace(target)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise

    def _engine_of_text(self, armored: str) -> str:
        return read_header(io.BytesIO(self._cryptor.armor.decode(armored))).engine_id


def _unique(path: Path) -> Path:
    if not path.exists():
        return path
    for n in range(1, 10_000):
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(path)
