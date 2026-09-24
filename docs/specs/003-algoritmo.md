# 003 — Algoritmo `pycronk-v1`

- Estado: Implementada
- Relacionadas: 004

Entrada: bytes. Alfabeto intermedio: símbolos de 6 bits (0..63).
Dos contraseñas independientes: `matrix` (capa 1) y `keystream` (capas 2 y 3).

## Capa 0 — KDF Polybius (`core/kdf/polybius.py`)
Cada carácter se proyecta en un cuadrado de Polybio 6×6 (`A-Z0-9`); fuera del alfabeto se usa
`(ord(c) mod 36) + 1`. Luego `N = Σ vᵢ · 37ⁱ mod (2⁶¹ − 1)`.
Base 37 por ser primo y coprimo con 36; módulo primo de Mersenne para distribuir bien el resultado.

## Capa 1 — Matriz sobre GF(2) (`core/layers/gf2_matrix.py`)
`M = L · U` con `L` triangular inferior y `U` triangular superior, ambas con diagonal 1, cuyas
15 + 15 posiciones libres salen de los bits de `N`. `det(M) = 1`, así que **siempre es invertible**.

Implementación: como un bloque tiene 6 bits, solo hay 64 entradas posibles. Se precalcula la tabla
`S[x] = M·x mod 2` y la capa se reduce a `S[sym]`; la inversa es `argsort(S)`.
La matriz `M` se conserva en la traza para el modo Proceso.

## Capa 2 — Vigenère con keystream LCG (`core/layers/vigenere_lcg.py`)
LCG de Numerical Recipes: `sₙ₊₁ = (1664525·sₙ + 1013904223) mod 2³²`, semilla `N mod 2³²`.
`kᵢ = sᵢ mod 64`, `cᵢ = (yᵢ + kᵢ) mod 64`.
El keystream se genera vectorizado con *jump-ahead*: `sₙ₊ₖ = Aₖ·sₙ + Cₖ` con `Aₖ`, `Cₖ` precalculados.

## Capa 3 — Transposición Fisher-Yates (`core/layers/fisher_yates.py`)
Continúa la **misma** secuencia LCG tras la capa 2: para `i = n−1 … 1`, `j = sᵢ mod (i+1)`,
intercambiar `π[i]` y `π[j]`. Salida: `out[i] = in[π[i]]`.

## Capa 4 — Codificación
- Archivos: los símbolos se empaquetan de nuevo a 8 bits (sin expansión).
- Texto: el contenedor completo se codifica en Base64 con el prefijo `PCRK1:` (spec 004).

## Cabecera de longitud
Antes de simbolizar se antepone la longitud original como `u64` big-endian. Viaja cifrada y
transpuesta con el resto (idea del prototipo), pero ya no limita el tamaño a 2 MB.

## Compatibilidad con el prototipo
Las capas 0–3 producen exactamente los mismos valores que el prototipo para las mismas entradas
(verificado con `tests/unit/data/prototype_vectors.json`). El **texto cifrado final** no es
compatible: cambian la cabecera de longitud (u64 en vez de 24 bits), el orden (la longitud también
pasa por la capa 1) y la codificación (contenedor versionado).

## Limitaciones (por qué es educativo)
- Sin nonce: mismo mensaje + mismas claves ⇒ mismo cifrado.
- LCG predecible; `s mod 64` usa los 6 bits bajos, que en un LCG módulo 2³² tienen periodo 64.
- Espacio de claves pequeño: 2³⁰ matrices y 2³² semillas; con contraseñas cortas `N` es aún menor.
- Sin integridad: una contraseña incorrecta produce datos basura en vez de un error.
Cada mejora se introduce como un motor nuevo (`pycronk-v2`, …) sin romper `v1`.
