from dataclasses import dataclass, field
from typing import Any

import numpy as np
import numpy.typing as npt

Symbols = npt.NDArray[np.uint8]

# Los valores de detalle se limitan a lo que el modo Proceso sabe dibujar (listas de enteros o
# texto ya formateado), para que la UI no tenga que adivinar formatos.
DetailValue = npt.NDArray[np.integer[Any]] | str


@dataclass(frozen=True)
class LayerStep:
    layer_id: str
    title: str
    details: dict[str, DetailValue]
    output: Symbols


@dataclass
class Trace:
    """Recolector de pasos. Solo se registra el primer chunk: la traza es didáctica y un archivo
    grande produciría millones de valores que nadie puede leer."""

    input_symbols: Symbols | None = None
    steps: list[LayerStep] = field(default_factory=lambda: [])
    length_bytes: int = 0
