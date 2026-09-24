# 004 — Formato de contenedor

- Estado: Implementada
- Relacionadas: 003

## Cabecera (en claro)

| Offset | Tamaño | Campo | Notas |
|---|---|---|---|
| 0 | 4 | magic | `b"PCRK"` |
| 4 | 1 | versión de formato | `1` |
| 5 | 1 | `n` = largo del id de motor | 1..255 |
| 6 | n | id de motor | ASCII, p. ej. `pycronk-v1` |
| 6+n | 1 | modo | `0` texto, `1` archivo |
| 7+n | 1 | flags | reservado, debe ser `0` |
| 8+n | 4 | símbolos por chunk | `u32` little-endian, múltiplo de 4 |

Después viene el **payload**, producido por el motor.

### Por qué el id del motor va en claro
Permite elegir el motor correcto al descifrar sin preguntar al usuario, y convivir con motores
futuros. No revela nada de la clave.

## Payload de `pycronk-v1`
Flujo lógico en claro: `u64 longitud` ‖ `datos` ‖ relleno con ceros hasta múltiplo de 3 bytes.
Se procesa en chunks de `símbolos por chunk` (por defecto 2¹⁶ = 48 KiB en claro; ver
§Rendimiento):

- Cada chunk de `k` bytes en claro (múltiplo de 3) → `4k/3` símbolos → capas → `k` bytes cifrados.
- El LCG **continúa** de un chunk al siguiente; cada chunk genera su propia permutación.

### Por qué el relleno a múltiplos de 3
3 bytes = 24 bits = 4 símbolos exactos. Sin relleno, al descifrar no se podría saber cuántos
símbolos tenía el último chunk (18 bits y 24 bits ocupan ambos 3 bytes), y la permutación depende
de ese número.

## Rendimiento
Las capas 1 y 2 y la conversión de bits están vectorizadas con numpy (cientos de MB/s). El límite
lo pone Fisher-Yates: cada intercambio depende del anterior y se ejecuta en Python puro
(~2 MB/s con chunks de 2¹⁶; ~1.2 MB/s con 2²⁰, porque los accesos aleatorios dejan de caber en
caché). Para ir más rápido habría que compilar ese bucle (numba o una extensión C) o definir un
motor `pycronk-v2` con una permutación vectorizable; `v1` no puede cambiar sin romper archivos.

## Texto
`PCRK1:` + Base64 estándar del contenedor completo. El prefijo permite que la app detecte
automáticamente si lo pegado es un cifrado.

## Errores
| Situación | Excepción |
|---|---|
| Magic incorrecto / Base64 inválido / cabecera truncada | `InvalidFormat` |
| Versión de formato desconocida | `UnsupportedVersion` |
| Id de motor no registrado | `UnknownEngine` |
