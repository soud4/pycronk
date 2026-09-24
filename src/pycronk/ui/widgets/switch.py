from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPalette, QPen
from PySide6.QtWidgets import QAbstractButton, QWidget


class Switch(QAbstractButton):
    """Interruptor tipo macOS. QCheckBox no se puede convertir en un switch solo con QSS."""

    _W, _H = 38, 22

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._offset = 0.0
        self._animation = QPropertyAnimation(self, b"offset", self)
        self._animation.setDuration(140)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate)

    def sizeHint(self) -> QSize:
        return QSize(self._W, self._H)

    def _get_offset(self) -> float:
        return self._offset

    def _set_offset(self, value: float) -> None:
        self._offset = value
        self.update()

    offset = Property(float, _get_offset, _set_offset)

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        # Un cambio programático (p. ej. al cargar ajustes) no debe animarse.
        self._animation.stop()
        self._set_offset(1.0 if checked else 0.0)

    def _animate(self, checked: bool) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._offset)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def paintEvent(self, _event: QPaintEvent) -> None:
        palette = self.palette()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(0, 0, self._W, self._H).translated(
            (self.width() - self._W) / 2, (self.height() - self._H) / 2
        )
        off = palette.color(QPalette.ColorRole.Dark)
        on = palette.color(QPalette.ColorRole.Highlight)
        # Interpolar el color junto con la posición evita un salto brusco a mitad de animación.
        color = QColor(
            round(off.red() + (on.red() - off.red()) * self._offset),
            round(off.green() + (on.green() - off.green()) * self._offset),
            round(off.blue() + (on.blue() - off.blue()) * self._offset),
        )
        if not self.isEnabled():
            color.setAlphaF(0.5)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(track, self._H / 2, self._H / 2)

        knob = self._H - 4
        x = track.left() + 2 + (self._W - knob - 4) * self._offset
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(QPen(palette.color(QPalette.ColorRole.Mid), 0.5))
        painter.drawEllipse(QRectF(x, track.top() + 2, knob, knob))
