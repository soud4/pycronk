# -*- mode: python ; coding: utf-8 -*-
# PyInstaller: pyinstaller packaging/pycronk.spec --noconfirm
# onedir en vez de onefile: arranca más rápido (no descomprime en cada ejecución) y dispara menos
# falsos positivos de antivirus en Windows (spec 007).
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

ROOT = Path(SPECPATH).parent
ICON = ROOT / "packaging" / "icons" / ("pycronk.ico" if sys.platform == "win32" else "pycronk.png")

a = Analysis(
    [str(ROOT / "src" / "pycronk" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    # Migraciones SQL, QSS, fuentes e iconos viven dentro del paquete y se leen en tiempo de
    # ejecución; qtawesome necesita sus fuentes de iconos.
    datas=collect_data_files("pycronk") + collect_data_files("qtawesome"),
    # Módulos de Qt que la app no usa: excluirlos reduce el tamaño del paquete a menos de la mitad.
    excludes=[
        "tkinter",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.Qt3DCore",
        "PySide6.QtMultimedia",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtPdf",
    ],
    noarchive=False,
)
# Algunos plugins opcionales de Qt (visor PDF, decoraciones Quick) arrastran librerías que la app
# no usa; sin ellos Qt simplemente no carga esos plugins.
_UNUSED = ("libQt6Quick", "libQt6Qml", "libQt6Pdf", "libqpdf", "Qt6Quick", "Qt6Qml", "Qt6Pdf")
a.binaries = [b for b in a.binaries if not any(name in b[0] for name in _UNUSED)]
# Solo se mantienen las traducciones de Qt en los idiomas de la interfaz.
a.datas = [
    d
    for d in a.datas
    if "translations" not in d[0] or any(f"_{lang}." in d[0] for lang in ("es", "en"))
]

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pycronk",
    console=False,
    icon=str(ICON),
)
coll = COLLECT(exe, a.binaries, a.datas, name="pycronk")
