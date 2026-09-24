# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado semántico.

## [Sin publicar]

### Añadido
- Arquitectura modular `core` / `services` / `persistence` / `ui` con puntos de extensión por
  `Protocol` (motores, capas, KDF, armor, repositorios, páginas, iconos). Ver `docs/specs/`.
- Cifrado de **archivos** de cualquier tamaño por chunks, con progreso y cancelación.
- Contenedor binario versionado (`PCRK`) que registra el motor usado; texto como `PCRK1:` + Base64.
- Interfaz estilo macOS (colores sólidos, tema claro/oscuro que sigue al sistema, iconos Phosphor).
- Historial y ajustes en SQLite (solo metadatos).
- CLI `pycronk-cli`.
- Tests unitarios (núcleo al 100 % de cobertura) y vectores de regresión del prototipo.
- Releases automáticos para Windows (instalador + portable) y Linux (AppImage) con atestaciones
  de procedencia de GitHub.

### Cambiado
- Migración de PyQt6 a PySide6 (licencia LGPL).
- La cabecera de longitud pasa de 24 bits (~2 MB) a 64 bits. Los textos cifrados con el
  prototipo **no** son compatibles con este formato.
