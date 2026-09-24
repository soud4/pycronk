# Especificaciones de pycronk

Cada spec es el contrato de un área del proyecto: **qué** se construye y **por qué** se decidió así.
El código debe poder leerse junto a su spec; si el código cambia una decisión, la spec se actualiza en el mismo commit.

| # | Spec | Estado |
|---|------|--------|
| 000 | [Visión y alcance](000-vision.md) | Implementada |
| 001 | [Arquitectura](001-arquitectura.md) | Implementada |
| 002 | [Interfaces y puntos de extensión](002-interfaces.md) | Implementada |
| 003 | [Algoritmo pycronk-v1](003-algoritmo.md) | Implementada |
| 004 | [Formato de contenedor](004-formato-contenedor.md) | Implementada |
| 005 | [Persistencia](005-persistencia.md) | Implementada |
| 006 | [Sistema de diseño](006-sistema-de-diseno.md) | Implementada |
| 007 | [Release y firma](007-release-y-firma.md) | Implementada |
| 008 | [Testing](008-testing.md) | Implementada |
| 009 | [Convenciones](009-convenciones.md) | Implementada |

Estados posibles: **Borrador** → **Aprobada** → **Implementada** (→ **Reemplazada por NNN**).

## Plantilla

```markdown
# NNN — Título

- Estado: Borrador
- Relacionadas: 00X, 00Y

## Contexto
Qué problema existe y por qué hay que decidir algo.

## Decisión
Qué se hace. Interfaces, formatos, tablas.

## Alternativas descartadas
Qué otra cosa se consideró y por qué no.

## Consecuencias
Qué se gana, qué se pierde, qué queda pendiente.
```
