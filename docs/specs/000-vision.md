# 000 — Visión y alcance

- Estado: Implementada

## Contexto
pycronk nace como proyecto de criptografía: un cifrado clásico híbrido propio (matriz sobre GF(2),
Vigenère con keystream LCG, transposición Fisher-Yates) con una interfaz que permite **ver** cada capa.
El prototipo (`src/main.py` + `src/cifrado_final.py`, ya retirados) funcionaba solo con texto,
tenía un límite de ~2 MB y bloqueaba la interfaz.

## Objetivos
1. Cifrar y descifrar **texto y archivos** de cualquier tamaño con memoria acotada.
2. Mantener el modo **Proceso** (traza capa por capa) como herramienta didáctica.
3. Arquitectura modular: todo lo reemplazable entra por interfaces (spec 002).
4. Interfaz de escritorio con estética macOS: colores sólidos, bordes finos, sin emojis.
5. Historial y ajustes locales en SQLite, sin guardar nunca datos sensibles.
6. Releases automáticos en GitHub para **Windows** (.exe) y **Linux** (AppImage), con
   procedencia verificable mediante GitHub Artifact Attestations.

## Fuera de alcance (por ahora)
- Binarios para macOS.
- Firma de código con certificados de pago (Authenticode, Apple Developer ID).
- Tests de integración / end-to-end (solo unitarios, spec 008).
- Declarar el algoritmo apto para proteger datos reales: es **educativo** (ver spec 003, §Limitaciones).
