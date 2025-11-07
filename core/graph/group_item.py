from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QLinearGradient


class GroupItem(QGraphicsRectItem):
    """
    Contenedor visual para agrupar nodos seleccionados.
    - Dibuja un rectángulo translúcido estilo backdrop (Nuke/Houdini).
    - Al mover el grupo, desplaza todos los nodos miembros.
    """

    def __init__(self, members, title="Grupo"):
        super().__init__()
        self.members = [m for m in (members or [])]
        self.title = title or "Grupo"
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable
            | QGraphicsRectItem.ItemIsSelectable
            | QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

        # Cache en coordenadas de dispositivo para mantener bordes nítidos al cambiar zoom
        try:
            self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        except Exception:
            pass

        # Calcular rectángulo que englobe miembros con padding
        if not self.members:
            self.setRect(QRectF(0, 0, 200, 120))
        else:
            combined = self.members[0].sceneBoundingRect()
            for it in self.members[1:]:
                combined = combined.united(it.sceneBoundingRect())
            pad = max(24.0, max(combined.width(), combined.height()) * 0.08)
            rect = combined.adjusted(-pad, -pad, pad, pad)
            self.setRect(rect)
            # Posicionar el grupo en la esquina superior izquierda del rectángulo
            self.setPos(rect.topLeft())

        # Título
        self._title_item = QGraphicsTextItem(self.title, self)
        self._title_item.setDefaultTextColor(QColor(220, 230, 240))
        self._title_item.setPos(12, 8)

        self._last_pos = self.pos()

    def paint(self, painter: QPainter, option, widget=None):
        rect = QRectF(0, 0, self.rect().width(), self.rect().height())

        # Fondo translúcido con degradado sutil
        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        grad.setColorAt(0.0, QColor(40, 48, 58, 85))
        grad.setColorAt(1.0, QColor(28, 32, 38, 85))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 12, 12)

        # Borde
        border = QPen(QColor(90, 110, 130, 160), 1.6)
        painter.setPen(border)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 12, 12)

        # Indicador de selección
        if self.isSelected():
            sel = QPen(QColor(120, 200, 255, 180), 2.0)
            painter.setPen(sel)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 11, 11)

    def itemChange(self, change, value):
        # Desplazar miembros cuando el grupo se mueve
        if change == QGraphicsRectItem.ItemPositionHasChanged:
            new_pos: QPointF = value
            delta = new_pos - self._last_pos
            if delta.manhattanLength() != 0:
                for m in self.members:
                    try:
                        m.setPos(m.pos() + delta)
                    except Exception:
                        pass
                self._last_pos = new_pos
        return super().itemChange(change, value)