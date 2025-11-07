from __future__ import annotations

from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
import math


def draw_background_grid(
    painter: QPainter,
    rect: QRectF,
    bg_color: QColor,
    grid_color: QColor,
    major_grid_color: QColor,
    base_grid: float = 40.0,
    major_factor: int = 4,
):
    """Dibuja el fondo y la retícula (grid) principal.

    Extraído desde NodeView para modularidad y reutilización.
    """
    painter.fillRect(rect, bg_color)
    grid = float(base_grid)
    major = int(major_factor)

    left = math.floor(rect.left() / grid) * grid
    top = math.floor(rect.top() / grid) * grid
    right = rect.right()
    bottom = rect.bottom()

    fine_pen = QPen(grid_color)
    fine_pen.setWidthF(0.0)
    major_pen = QPen(major_grid_color)
    major_pen.setWidthF(0.0)

    # Líneas verticales
    x, i = left, 0
    while x <= right:
        painter.setPen(major_pen if i % major == 0 else fine_pen)
        painter.drawLine(QPointF(x + 0.5, top), QPointF(x + 0.5, bottom))
        x += grid
        i += 1

    # Líneas horizontales
    y, i = top, 0
    while y <= bottom:
        painter.setPen(major_pen if i % major == 0 else fine_pen)
        painter.drawLine(QPointF(left, y + 0.5), QPointF(right, y + 0.5))
        y += grid
        i += 1