# 001 — Arquitectura

- Estado: Implementada
- Relacionadas: 002, 005

## Decisión

```
src/pycronk/
  core/         Algoritmo, formato y API pura. Sin Qt, sin rutas de disco.
  services/     Casos de uso (cifrar texto/archivo + registrar historial), ajustes, puertos.
  persistence/  Implementaciones SQLite de los puertos de services.
  ui/           PySide6: tema, widgets, páginas, workers, estado compartido (state.py) y raíz de
                composición (app.py).
  cli.py        Interfaz de línea de comandos sobre services.
```

### Regla de dependencias

```
ui ──► services ──► core
 │         ▲
 └──► persistence (solo en app.py / cli.py, para inyectarla)
```

- `core` no importa nada del proyecto ni de Qt: se puede probar y reutilizar sin interfaz.
- `services` depende de **protocolos** (`services/ports.py`), nunca de SQLite directamente.
- `persistence` implementa esos protocolos.
- `ui/app.py` y `cli.py` son las **raíces de composición**: el único lugar donde se eligen las
  implementaciones concretas y se conectan entre sí.

### Por qué así
- La lógica criptográfica es la parte que más se testea y la que más probablemente cambie de versión;
  aislarla permite testearla al 100 % sin levantar Qt.
- Tener una única raíz de composición hace que agregar/quitar una pieza (un motor, una página, otro
  almacenamiento) sea editar una lista, no buscar `import` por todo el proyecto.

## Flujo de un cifrado de archivo

```
FilesPage ──(QRunnable)──► CryptoService.encrypt_file
                               │  abre src/dst, mide tiempo con Clock
                               ▼
                           Cryptor.encrypt_stream ──► container.write_header
                               │                  └─► CipherEngine.encrypt_stream (por chunks)
                               ▼
                           HistoryRepository.add(metadatos)
```

El worker traduce `ProgressSink` / `CancelToken` a señales Qt; `core` nunca conoce Qt.

## Comunicación entre páginas
Las páginas no se importan entre sí. Comparten estado a través de objetos observables de
`ui/state.py`: `SettingsStore` (ajustes vigentes), `TraceStore` (última traza para Proceso) y
`Navigator` (pedir que se muestre otra página). Quitar una página no rompe a las demás.

## Alternativas descartadas
- **Arquitectura hexagonal completa con casos de uso por clase**: demasiada ceremonia para el tamaño
  del proyecto. Se toma solo la idea de puertos donde hay más de una implementación posible.
- **ORM (SQLAlchemy)**: dos tablas no justifican la dependencia (spec 005).
