#!/usr/bin/env bash
# Construye el AppImage a partir de dist/pycronk (salida de PyInstaller).
#   packaging/linux/build-appimage.sh 1.2.3
set -euo pipefail

VERSION="${1:?uso: build-appimage.sh VERSION}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
APPDIR="$ROOT/build/AppDir"
TOOL="$ROOT/build/appimagetool-x86_64.AppImage"

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib"
cp -r "$ROOT/dist/pycronk" "$APPDIR/usr/lib/pycronk"
install -m 755 "$ROOT/packaging/linux/AppRun" "$APPDIR/AppRun"
install -m 644 "$ROOT/packaging/linux/pycronk.desktop" "$APPDIR/pycronk.desktop"
install -m 644 "$ROOT/packaging/icons/pycronk.png" "$APPDIR/pycronk.png"

if [ ! -x "$TOOL" ]; then
    curl -fsSL -o "$TOOL" \
        https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x "$TOOL"
fi

# Los runners de CI no tienen FUSE: la herramienta se autoextrae en lugar de montarse.
ARCH=x86_64 APPIMAGE_EXTRACT_AND_RUN=1 "$TOOL" "$APPDIR" "$ROOT/dist/pycronk-$VERSION-x86_64.AppImage"
