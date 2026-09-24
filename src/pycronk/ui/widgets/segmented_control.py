from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QFontMetrics, QMouseEvent, QPainter, QPaintEvent, QPalette, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget


class SegmentedControl(QWidget):
    """Equivalente a NSSegmentedControl. Se pinta a mano porque QSS no puede dibujar un segmento
    activo "elevado" sobre una pista continua como hace macOS."""

    changed = Signal(int)

    _PADDING = 2
    _HEIGHT = 28

    def __init__(self, options: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._options = options
        self._index = 0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def current_index(self) -> int:
        return self._index

    def set_current_index(self, index: int, *, notify: bool = True) -> None:
        if index == self._index or not 0 <= index < len(self._options):
            return
        self._index = index
        self.update()
        if notify:
            self.changed.emit(index)

    def sizeHint(self) -> QSize:
        metrics = QFontMetrics(self.font())
        widest = max(metrics.horizontalAdvance(text) for text in self._options)
        return QSize((widest + 28) * len(self._options) + self._PADDING * 2, self._HEIGHT)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        width = self.width() / len(self._options)
        self.set_current_index(min(int(event.position().x() // width), len(self._options) - 1))

    def keyPressEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.key() == Qt.Key.Key_Left:
            self.set_current_index(max(0, self._index - 1))
        elif event.key() == Qt.Key.Key_Right:
            self.set_current_index(min(len(self._options) - 1, self._index + 1))
        else:
            super().keyPressEvent(event)

    def paintEvent(self, _event: QPaintEvent) -> None:
        palette = self.palette()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        track = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(palette.color(QPalette.ColorRole.Midlight))
        painter.drawRoundedRect(track, 7, 7)

        width = (track.width() - self._PADDING * 2) / len(self._options)
        thumb = QRectF(
            track.left() + self._PADDING + width * self._index,
            track.top() + self._PADDING,
            width,
            track.height() - self._PADDING * 2,
        )
        painter.setBrush(palette.color(QPalette.ColorRole.Light))
        painter.setPen(QPen(palette.color(QPalette.ColorRole.Mid), 1))
        painter.drawRoundedRect(thumb, 5.5, 5.5)
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(palette.color(QPalette.ColorRole.Highlight), 2))
            painter.drawRoundedRect(track.adjusted(1, 1, -1, -1), 6, 6)

        for i, text in enumerate(self._options):
            cell = QRectF(
                track.left() + self._PADDING + width * i, track.top(), width, track.height()
            )
            font = self.font()
            font.setWeight(font.Weight.DemiBold if i == self._index else font.Weight.Normal)
            painter.setFont(font)
            painter.setPen(palette.color(QPalette.ColorRole.WindowText))
            painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, text)
