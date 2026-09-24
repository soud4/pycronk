# 007 — Release y firma

- Estado: Implementada

## Plataformas
| Plataforma | Artefacto | Herramienta |
|---|---|---|
| Windows x64 | `pycronk-X.Y.Z-windows-x64-setup.exe` + `pycronk-X.Y.Z-windows-x64-portable.zip` | PyInstaller (onedir) + Inno Setup |
| Linux x86_64 | `pycronk-X.Y.Z-x86_64.AppImage` | PyInstaller (onedir) + appimagetool |

**onedir** en vez de onefile: arranca más rápido (no descomprime en cada ejecución) y dispara menos
falsos positivos de antivirus en Windows.
Linux se construye en `ubuntu-22.04` porque un AppImage solo funciona en distros con una glibc igual
o más nueva que la de la máquina donde se compiló.

## Workflows
- `.github/workflows/ci.yml` — push / pull request: ruff, pyright y tests unitarios en Ubuntu y Windows.
- `.github/workflows/release.yml` — tag `v*.*.*`:
  1. `build-windows` y `build-linux` en paralelo (tests → PyInstaller → instalador/AppImage).
  2. `publish`: descarga artefactos → `SHA256SUMS.txt` → **attestation** → GitHub Release con notas
     generadas automáticamente.

La versión se toma del tag mediante `hatch-vcs` (sin tag: `0.0.0`).

## Firma: GitHub Artifact Attestations
Cada artefacto recibe una atestación de procedencia firmada con Sigstore por la identidad OIDC del
workflow (`actions/attest-build-provenance`). Demuestra que el binario salió **de este repositorio,
de este commit y de este workflow**, sin certificados ni secretos que custodiar.

Verificación por el usuario:
```bash
gh attestation verify pycronk-1.0.0-x86_64.AppImage --repo <owner>/pycronk
sha256sum -c SHA256SUMS.txt
```

### Limitaciones conocidas
- Windows SmartScreen seguirá mostrando "editor desconocido": ese aviso solo desaparece con firma
  Authenticode (certificado de pago o SignPath Foundation). Queda como trabajo futuro.
- Requiere que el repositorio sea público (o GitHub Enterprise Cloud para repos privados).

## Cómo publicar
```bash
git tag v0.1.0 && git push origin v0.1.0
```
