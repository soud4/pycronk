"""Genera el icono de la aplicación. Se versiona el resultado; este script existe para poder
regenerarlo si cambia el diseño, sin depender de herramientas gráficas externas.

    python packaging/icons/generate.py
"""

import sys
from pathlib import Path

import qtawesome as qta
from PIL import Image
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[2]
PNG = ROOT / "src" / "pycronk" / "ui" / "theme" / "app-icon.png"
ICO = ROOT / "packaging" / "icons" / "pycronk.ico"
SIZE = 512


def render() -> QImage:
    image = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Margen y radio (~22 %) de la rejilla de iconos de macOS; color sólido, sin degradado.
    margin = SIZE * 0.08
    body = QRectF(margin, margin, SIZE - 2 * margin, SIZE - 2 * margin)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#007AFF"))
    painter.drawRoundedRect(body, body.width() * 0.225, body.width() * 0.225)
    glyph = qta.icon("ph.shield-check", color="#FFFFFF").pixmap(int(SIZE * 0.74), int(SIZE * 0.74))
    painter.drawPixmap(int((SIZE - glyph.width()) / 2), int((SIZE - glyph.height()) / 2), glyph)
    painter.end()
    return image


def main() -> None:
    app = QApplication(sys.argv)  # noqa: F841 - qtawesome necesita una QApplication viva
    render().save(str(PNG))
    Image.open(PNG).save(
        ICO, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )
    print(f"{PNG}\n{ICO}")


if __name__ == "__main__":
    main()
