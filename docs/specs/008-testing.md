# 008 — Testing

- Estado: Implementada

## Alcance
Por ahora **solo tests unitarios**: cada test ejercita una unidad (función, clase, widget aislado)
sin red, sin disco real (salvo `tmp_path`) y sin ventana principal completa.

## Herramientas
| Herramienta | Por qué |
|---|---|
| `pytest` | Runner estándar, fixtures |
| `hypothesis` | Propiedades (ida y vuelta para *cualquier* entrada) encuentran casos límite que nadie escribe a mano |
| `pytest-cov` | Umbral mínimo de cobertura en CI |
| `pytest-qt` | Widgets aislados (`qtbot`), en modo `offscreen` |

Ejecutar: `pytest` (la configuración vive en `pyproject.toml`).

## Organización
Espejo del código: `tests/unit/<paquete>/test_<módulo>.py`. Fixtures compartidos en
`tests/unit/conftest.py`: `keys`, `vectors`, `fake_clock`, `memory_conn`, `fake_history`.

### Vectores de regresión
`tests/unit/data/prototype_vectors.json` se generó ejecutando el prototipo original **antes** de la
refactorización. Garantiza que las capas 0–3 conservan su matemática.

## Matriz de casos

| Módulo | Casos |
|---|---|
| `core/kdf/polybius` | Vectores del prototipo · insensible a mayúsculas · contraseña vacía = 0 · caracteres fuera del alfabeto · un carácter distinto cambia `N` |
| `core/prng/lcg` | Secuencia igual al prototipo · jump-ahead ≡ pasos secuenciales (hypothesis) · continuación entre bloques · `n = 0` |
| `core/layers/gf2_matrix` | Matriz y tabla iguales al prototipo · `S` es permutación de 0..63 para todo `N` (hypothesis) · ida y vuelta · símbolos de capa 1 iguales al prototipo |
| `core/layers/vigenere_lcg` | Keystream igual al prototipo · ida y vuelta · entrada vacía |
| `core/layers/fisher_yates` | Permutación igual al prototipo · es permutación válida · ida y vuelta · `n ∈ {0, 1}` |
| `core/symbols` | bytes ⇄ símbolos (0..7 bytes) · dtype y rango · longitud no múltiplo de 4 rechazada |
| `core/container` | Ida y vuelta de cabecera · magic, versión, truncado, flags e id inválidos |
| `core/armor/base64_armor` | Ida y vuelta · `detects` · Base64 corrupto |
| `core/registry` | Registrar/obtener · duplicado · inexistente · orden de `ids()` |
| `core/pipeline` | Ida y vuelta (hypothesis) · límites de chunk (0, 1, k−1, k, k+1) · progreso monótono hasta el total · cancelación · traza con un paso por capa · claves incorrectas no recuperan el original · determinismo |
| `core/api` | Texto y bytes ida y vuelta · detección de motor desde la cabecera · motor desconocido · `chunk_symbols` inválido |
| `services/settings` | Por defecto · claves desconocidas ignoradas · faltantes rellenadas · valores inválidos → por defecto |
| `services/crypto_service` | Historial en ok / error / cancelado · historial desactivado · **ningún dato sensible en el historial** · duración desde `Clock` · archivo parcial eliminado al cancelar |
| `persistence/*` | Migraciones desde 0 e idempotentes · CRUD de historial · filtro por tipo · purga por antigüedad · `CHECK` rechaza valores inválidos · ajustes persisten |
| `ui/theme` | QSS sin placeholders · paleta completa en ambos temas · contraste de texto ≥ 4.5:1 |
| `ui/theme/icons` | Todos los nombres lógicos resuelven en todos los roles · caché por tema · `bind` reaplica al cambiar de tema y reemplaza enlaces previos |
| `ui/widgets` | `PasswordField` alterna eco · `SegmentedControl` (programático, ratón, teclado) · `Switch` · `GroupedList` · `Banner` (tipos y auto-ocultado) · `KeysForm` · formato de valores |
| `ui/workers` | Resultado y progreso · total 0 · fallo · cancelación |
| `ui/state` | `SettingsStore` guarda y emite, ignora cambios nulos · `TraceStore` · `Navigator` |
| `ui/main_window` | Lista páginas, activa la primera, navega por id (con páginas falsas) |
| `ui/pages` | Con servicios reales sobre SQLite en memoria: validaciones, cifrado/descifrado de texto, autodetección de modo, cola de archivos, errores, traza renderizada, historial (filtro/borrado), ajustes |
| `cli` | Texto (argumento y stdin), archivos, pedir contraseñas, códigos de salida |

## Umbrales
`core` ≥ 95 % de cobertura; `services` y `persistence` ≥ 90 %. La UI no tiene umbral: se prueban
los widgets con lógica propia.
