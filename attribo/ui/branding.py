"""
Attribo branding - the app logo drawn programmatically.

Mark: "Attribo = attribution" - a bold quotation mark (giving credit to
sources), verified by an emerald check badge (quotations, checked).

Exports an application icon (packaging/appicon.ico when available, a
drawn fallback otherwise) and the header/tray pixmaps. Rendering is
memoised; drawing at supersampled resolution keeps the mark sharp from
the 16px taskbar up to 512px docs.

(c) 2026 Ayush Gupta (Attribo). All rights reserved.
"""
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QIcon,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)

ACCENT_TOP = "#8FB0FF"
ACCENT_MID = "#5B7BFF"
ACCENT_DEEP = "#3D46D8"
CHECK_GREEN = "#31D08C"

_QUOTE_FAMILIES = ["Georgia", "Cambria", "Times New Roman", "serif"]

_cache: dict = {}


# ----------------------------------------------------------------- drawing
def _squircle(painter: QPainter, c: float) -> None:
    """Gradient rounded-square base with a soft top-left glow."""
    m = c * 0.028
    rect = QRectF(m, m, c - 2 * m, c - 2 * m)
    radius = rect.width() * 0.235
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)

    grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
    grad.setColorAt(0.0, QColor(ACCENT_TOP))
    grad.setColorAt(0.5, QColor(ACCENT_MID))
    grad.setColorAt(1.0, QColor(ACCENT_DEEP))
    painter.setPen(Qt.NoPen)
    painter.fillPath(path, grad)

    glow = QRadialGradient(
        QPointF(rect.left() + rect.width() * 0.30, rect.top() + rect.height() * 0.22),
        rect.width() * 0.85,
    )
    glow.setColorAt(0.0, QColor(255, 255, 255, 60))
    glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    painter.fillPath(path, glow)


def _quote_glyph(painter: QPainter, c: float, size_frac: float,
                 cx: float, cy: float) -> None:
    """Opening double-quote glyph centred on (cx, cy) of the canvas."""
    font = QFont()
    font.setFamilies(list(_QUOTE_FAMILIES))
    font.setBold(True)
    font.setPixelSize(max(2, int(c * size_frac)))
    painter.setFont(font)
    painter.setPen(QColor("#FFFFFF"))
    fm = QFontMetricsF(font)
    glyph = "\u201C"
    br = fm.tightBoundingRect(glyph)
    x = c * cx - br.width() / 2.0 - br.left()
    y = c * cy - br.height() / 2.0 - br.top()
    painter.drawText(QPointF(x, y), glyph)


def _check_badge(painter: QPainter, c: float, cx: float, cy: float, r_frac: float) -> None:
    """Emerald verified badge with a white check."""
    r = c * r_frac
    painter.setPen(QPen(QColor(255, 255, 255, 232), c * 0.030))
    painter.setBrush(QColor(CHECK_GREEN))
    painter.drawEllipse(QPointF(c * cx, c * cy), r, r)

    pen = QPen(QColor("#FFFFFF"), c * 0.066)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    pts = [(-0.32, 0.02), (-0.06, 0.28), (0.34, -0.22)]
    start = QPointF(c * (cx + pts[0][0] * r_frac), c * (cy + pts[0][1] * r_frac))
    path = QPainterPath(start)
    for px, py in pts[1:]:
        path.lineTo(QPointF(c * (cx + px * r_frac), c * (cy + py * r_frac)))
    painter.drawPath(path)


def draw_logo(painter: QPainter, c: float) -> None:
    """Draw the complete mark on a c-by-c square canvas."""
    _squircle(painter, c)
    _quote_glyph(painter, c, 0.68, 0.468, 0.428)
    _check_badge(painter, c, 0.745, 0.745, 0.168)


def logo_image(size: int) -> QImage:
    """The mark as a square QImage (memoised)."""
    key = ("img", size)
    if key in _cache:
        return _cache[key]
    supersample = 8 if size <= 96 else 4
    big = size * supersample
    img = QImage(big, big, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    draw_logo(painter, float(big))
    painter.end()
    img = img.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    _cache[key] = img
    return img


def logo_pixmap(size: int = 64, dpr: float = 1.0) -> QPixmap:
    """The mark as a QPixmap; dpr>1 renders HiDPI-crisp logical-size pixmaps."""
    key = ("pix", size, dpr)
    if key in _cache:
        return _cache[key]
    physical = max(1, int(round(size * dpr)))
    pix = QPixmap.fromImage(logo_image(physical))
    if dpr != 1.0:
        pix.setDevicePixelRatio(dpr)
    _cache[key] = pix
    return pix


# ----------------------------------------------------------------- icons
def _ico_paths() -> list:
    paths = []
    if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None):
        paths.append(Path(sys._MEIPASS) / "appicon.ico")
    root = Path(__file__).resolve().parents[2]
    paths.append(root / "packaging" / "appicon.ico")
    return paths


def app_icon() -> QIcon:
    """Application icon: the packaged .ico when present, drawn mark otherwise."""
    if "app_icon" in _cache:
        return _cache["app_icon"]
    for path in _ico_paths():
        if path.is_file():
            icon = QIcon(str(path))
            if not icon.isNull():
                _cache["app_icon"] = icon
                return icon
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(QPixmap.fromImage(logo_image(size)))
    _cache["app_icon"] = icon
    return icon
