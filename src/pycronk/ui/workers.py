from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from pycronk.core.errors import Cancelled
from pycronk.core.interfaces import CancelFlag, CancelToken, ProgressSink

Job = Callable[[ProgressSink, CancelToken], Any]


class _Signals(QObject):
    # Progreso como fracción: una señal (int, int) se desbordaría con archivos > 2 GiB porque Qt
    # transporta int de 32 bits.
    progress = Signal(float)
    finished = Signal(object)
    failed = Signal(object)
    cancelled = Signal()


class Task(QRunnable):
    """Ejecuta un trabajo del núcleo fuera del hilo de la GUI.

    Traduce `ProgressSink`/`CancelToken` (interfaces del núcleo) a señales Qt, así `core` y
    `services` no conocen Qt.
    """

    def __init__(self, job: Job) -> None:
        super().__init__()
        self._job = job
        self._flag = CancelFlag()
        # Las señales se crean en el hilo de la GUI: así sus conexiones se entregan en ese hilo.
        self.signals = _Signals()

    def cancel(self) -> None:
        self._flag.cancel()

    def run(self) -> None:
        try:
            result = self._job(self._report, self._flag)
        except Cancelled:
            self.signals.cancelled.emit()
        except Exception as exc:
            # Todo fallo debe llegar a la UI: una excepción que escapa de un hilo del pool se
            # pierde en silencio y la interfaz quedaría esperando para siempre.
            self.signals.failed.emit(exc)
        else:
            self.signals.finished.emit(result)

    def _report(self, done: int, total: int) -> None:
        self.signals.progress.emit(1.0 if total == 0 else done / total)


class TaskRunner(QObject):
    """Mantiene viva cada tarea hasta que termina: sin una referencia Python, el recolector podría
    destruir las señales mientras el hilo aún las usa."""

    def __init__(self, parent: QObject | None = None, max_threads: int = 1) -> None:
        super().__init__(parent)
        self._pool = QThreadPool(self)
        # Un solo hilo: las operaciones de archivo compiten por disco, en paralelo no ganan nada
        # y el orden de la cola se volvería impredecible.
        self._pool.setMaxThreadCount(max_threads)
        self._running: set[Task] = set()

    def create(self, job: Job) -> Task:
        """Construye la tarea y conecta su limpieza sin encolarla todavía.

        Separado de `start` para que quien llame pueda conectar sus propias señales antes de que
        el job pueda ejecutarse: una vez encolada, un hilo del pool podría terminarla antes de que
        el llamador llegue a conectar, y una señal emitida sin oyentes se pierde para siempre.
        """
        task = Task(job)
        self._running.add(task)
        for signal in (task.signals.finished, task.signals.failed):
            signal.connect(lambda _r, t=task: self._running.discard(t))
        task.signals.cancelled.connect(lambda t=task: self._running.discard(t))
        return task

    def submit(self, task: Task) -> None:
        self._pool.start(task)

    def start(self, job: Job) -> Task:
        task = self.create(job)
        self.submit(task)
        return task

    def wait(self, msecs: int = -1) -> bool:
        return self._pool.waitForDone(msecs)
