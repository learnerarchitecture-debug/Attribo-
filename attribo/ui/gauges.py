"""
Custom-painted score rings for the summary dashboard.

(c) 2026 Attribo. All rights reserved.
"""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class ScoreRing(QWidget):
    def __init__(self, label: str = "", color: str = "#5B8CFF", parent=None):
        super().__init__(parent)
        self.label = label
        self.color = color
        self.value = 0.0
        self.setMinimumSize(140, 158)
        self.setMaximumHeight(158)

    def set_value(self, value) -> None:
        self.value = max(0.0, min(100.0, float(value)))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width, height = self.width(), self.height()
        size = min(width, height - 30) - 16
        if size <= 10:
            return
        rect = QRectF((width - size) / 2.0, 10.0, size, size)

        # track
        pen = QPen(QColor("#1B2333"), 11)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 225 * 16, -270 * 16)

        # value arc
        pen_value = QPen(QColor(self.color), 11)
        pen_value.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_value)
        painter.drawArc(rect, 225 * 16, int(-270 * 16 * self.value / 100.0))

        # value text
        painter.setPen(QColor("#E8EDF4"))
        font = QFont("Segoe UI", 20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, f"{self.value:.0f}")

        # label
        painter.setPen(QColor("#8A94A6"))
        font2 = QFont("Segoe UI", 8)
        painter.setFont(font2)
        painter.drawText(
            QRectF(0, 10 + size + 4, width, 24), Qt.AlignHCenter, self.label
        )
