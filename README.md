# pycronk

Cifrado clásico híbrido con interfaz de escritorio: matriz sobre GF(2), Vigenère con keystream LCG
y transposición Fisher-Yates. Cifra **texto y archivos** y permite ver el recorrido capa por capa.

> **Aviso:** pycronk-v1 es un algoritmo **educativo**. No lo uses para proteger información real.
> Las razones están en [docs/specs/003-algoritmo.md](docs/specs/003-algoritmo.md#limitaciones-por-qué-es-educativo).

## Descargas

En [Releases](../../releases) hay binarios para:

| Sistema | Archivo |
|---|---|
| Windows 10/11 x64 | `pycronk-X.Y.Z-windows-x64-setup.exe` (instalador) o `-portable.zip` |
| Linux x86_64 | `pycronk-X.Y.Z-x86_64.AppImage` (`chmod +x` y ejecutar) |

### Verificar la descarga
Cada binario lleva una atestación de procedencia de GitHub (Sigstore) que prueba que se compiló en
este repositorio a partir de un commit concreto:

```bash
gh attestation verify pycronk-X.Y.Z-x86_64.AppImage --repo <owner>/pycronk
sha256sum -c SHA256SUMS.txt --ignore-missing
```

Windows mostrará igualmente el aviso de SmartScreen de "editor desconocido": la atestación no
equivale a una firma Authenticode. Pulsa **Más información → Ejecutar de todas formas**.

## Desarrollo

Requiere Python 3.12+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python -m pycronk          # interfaz gráfica
pycronk-cli --help         # línea de comandos
pytest                     # tests unitarios
ruff check . && pyright    # lint y tipos
```

### Línea de comandos

```bash
pycronk-cli encrypt foto.jpg -m "clave matriz" -k "clave keystream"      # → foto.jpg.pcrk
pycronk-cli decrypt foto.jpg.pcrk -m "clave matriz" -k "clave keystream" # → foto.jpg
echo "hola" | pycronk-cli encrypt-text -m a -k b                        # → PCRK1:...
```

Si omites `-m` o `-k`, la CLI pide la contraseña sin mostrarla en pantalla.

## Documentación

La arquitectura, las interfaces, el formato de archivo, el sistema de diseño y el proceso de release
están en [`docs/specs/`](docs/specs/README.md).

## Publicar una versión

```bash
git tag v0.1.0 && git push origin v0.1.0
```

El workflow `release.yml` compila Windows y Linux, genera `SHA256SUMS.txt`, firma las atestaciones y
crea el Release.
