# 005 — Persistencia

- Estado: Implementada
- Relacionadas: 001, 002

## Decisión
`sqlite3` de la biblioteca estándar, SQL plano y migraciones numeradas en
`src/pycronk/persistence/migrations/NNN_*.sql`, aplicadas según `PRAGMA user_version`.
La base vive en `QStandardPaths.AppDataLocation/pycronk.db`; la ruta llega como `Path` desde la
raíz de composición para que `persistence` no dependa de Qt.

## Esquema (001_init.sql)

```sql
CREATE TABLE history (
  id          INTEGER PRIMARY KEY,
  created_at  TEXT NOT NULL,                -- ISO-8601 UTC
  operation   TEXT NOT NULL CHECK (operation IN ('encrypt','decrypt')),
  kind        TEXT NOT NULL CHECK (kind IN ('text','file')),
  engine_id   TEXT NOT NULL,
  label       TEXT,                         -- nombre de archivo o "Texto (N bytes)"
  input_size  INTEGER,
  output_path TEXT,
  duration_ms INTEGER,
  status      TEXT NOT NULL CHECK (status IN ('ok','error','cancelled'))
);
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);  -- valor JSON
```

## Qué NO se guarda
Contraseñas, texto en claro, texto cifrado, contenido de archivos. Solo metadatos.
Hay un test unitario que lo verifica.

## Ajustes
`Settings` es un dataclass inmutable con valores por defecto en código. Al cargar, las claves
desconocidas se ignoran y las ausentes toman su valor por defecto, de modo que agregar o quitar un
ajuste nunca rompe una base existente.

| Clave | Por defecto |
|---|---|
| `theme` | `system` (`light` / `dark`) |
| `engine_id` | `pycronk-v1` |
| `history_enabled` | `true` |
| `history_retention_days` | `90` |
| `output_dir` | `""` (misma carpeta que el original) |
| `clear_clipboard_seconds` | `0` (desactivado) |
| `chunk_symbols` | `65536` |

## Alternativas descartadas
- ORM: dos tablas no lo justifican.
- `QSettings` para ajustes: dispersaría el estado en dos almacenamientos distintos.
