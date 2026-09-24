# 009 — Convenciones

- Estado: Implementada

## Comentarios: el *por qué*, no el *qué*
El qué lo cuentan los nombres y los tipos. Un comentario existe para explicar una decisión que el
código no puede expresar: una restricción, una alternativa descartada, una compatibilidad.

```python
# Mal: describe lo que ya se lee
# multiplica la matriz por cada bloque
table = build_table(matrix)

# Bien: explica por qué se hizo así
# Con bloques de 6 bits solo hay 64 entradas posibles: precalcular la tabla evita un producto
# matricial por bloque y convierte la inversa en un simple argsort.
table = build_table(matrix)
```

- Si un comentario solo repite el código, se borra.
- Los docstrings se reservan para **contratos** públicos (interfaces, funciones de API): entradas,
  salidas, excepciones. No para narrar la implementación.
- Los números mágicos llevan su justificación (por qué 37, por qué 2⁶¹ − 1, por qué 2²⁰).

## Idioma
Código (identificadores) en inglés. Comentarios, docstrings, specs y textos de interfaz en español.

## Estilo
- `ruff` para lint y formato (líneas de 100). `pyright` en modo estricto para `core`, `services` y
  `persistence`.
- Sin estado global mutable: las dependencias entran por constructor.
- Dataclasses `frozen=True` para valores; `Protocol` para puntos de extensión (spec 002).
- Una clase o grupo cohesivo de funciones por módulo.
- Nada de emojis en el código de interfaz (spec 006).
