# 002 — Interfaces y puntos de extensión

- Estado: Implementada
- Relacionadas: 001, 003

## Principio
Se abstrae **solo** lo que es reemplazable o removible. Se usa `typing.Protocol` (tipado estructural)
en vez de clases base abstractas: una implementación no necesita heredar nada y los dobles de test
son clases triviales.

## Núcleo — `pycronk.core.interfaces`

| Protocolo | Contrato | Implementaciones |
|---|---|---|
| `KeyDerivation` | `derive(password) -> int`, determinista | `PolybiusKdf` |
| `Layer` | `prepare(n, ctx) -> params`, `forward(sym, params)`, `inverse(sym, params)`, `describe(params)`. `inverse(forward(x)) == x` | `Gf2MatrixLayer`, `VigenereLcgLayer`, `FisherYatesLayer` |
| `CipherEngine` | `encrypt_stream` / `decrypt_stream` sobre el **payload** (sin cabecera de contenedor) | `LayeredEngine` |
| `TextArmor` | `encode(bytes) -> str`, `decode(str) -> bytes`, `detects(str) -> bool` | `Base64Armor` |
| `ProgressSink` | `__call__(done, total)` | lambda, señal Qt |
| `CancelToken` | `is_cancelled() -> bool` | `CancelFlag` |

### Por qué `Layer` tiene `prepare`
Las capas 2 y 3 consumen la **misma** secuencia LCG, en ese orden. Al descifrar, las inversas se
aplican en orden contrario (primero la 3), pero la secuencia debe generarse en el orden original.
Separar `prepare` (consume el PRNG, siempre en orden de cifrado) de `forward`/`inverse` (aplican la
transformación) resuelve esto sin que ninguna capa conozca a las demás. Además, los `params`
preparados son exactamente lo que el modo Proceso necesita mostrar.

### Cómo agregar una capa
1. Crear `core/layers/mi_capa.py` con una clase que cumpla `Layer`.
2. Añadir su test unitario de ida y vuelta.
3. Registrar un **nuevo motor** (`LayeredEngine("pycronk-v2", ..., [..., MiCapa()])`) en
   `core/api.py::default_engines`. No se modifica `pycronk-v1`: los archivos antiguos deben seguir
   descifrándose.

### Cómo agregar un motor completamente distinto (p. ej. AES-GCM)
Implementar `CipherEngine` y registrarlo. El contenedor guarda el id del motor, así que `decrypt`
lo elige solo; la UI lista los motores registrados en Ajustes.

## Servicios — `pycronk.services.ports`

| Protocolo | Para qué existe |
|---|---|
| `HistoryRepository` | Cambiar SQLite por otro almacenamiento o por un fake en tests |
| `SettingsRepository` | Idem para ajustes |
| `Clock` | Tests deterministas de fechas y duraciones |

## UI — `pycronk.ui`

| Protocolo | Para qué existe |
|---|---|
| `Page` (`ui/pages/base.py`) | Cada entrada del sidebar. `MainWindow` recibe una lista: agregar/quitar páginas es editar `app.py` |
| `IconProvider` (`ui/theme/icons.py`) | Nombres lógicos de iconos → `QIcon`. Cambiar de familia de iconos toca una sola clase |

## Registro — `pycronk.core.registry.Registry[T]`
Contenedor por id, sin estado global: `Cryptor` recibe sus registros por constructor. Registrar un id
duplicado es un error explícito para evitar sobrescrituras silenciosas.
