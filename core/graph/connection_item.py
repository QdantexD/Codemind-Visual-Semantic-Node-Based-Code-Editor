from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPen, QColor, QPainterPath, QBrush
from PySide6.QtCore import QPointF, QRectF, Qt
import math

class ConnectionItem(QGraphicsPathItem):
    """Item gráfico para conexiones entre nodos con curvas bezier."""
    
    def __init__(self, start_item, end_item=None, start_port="output", end_port="input"):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.start_port = start_port
        self.end_port = end_port
        self._temp_end_pos = None  # posición temporal mientras se arrastra
        
        # Configuración visual
        self.pen = QPen(QColor(100, 200, 255))
        self.pen.setWidth(2)
        self.setPen(self.pen)
        
        # Habilitar selección sólo con botón derecho; no interferir con arrastre del nodo
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        try:
            self.setAcceptedMouseButtons(Qt.RightButton)
        except Exception:
            pass
        self.setZValue(-1)  # Detrás de los nodos

        # Estado de animación (Blueprint-style)
        self._anim_t = 0.0           # 0..1 para burbujas que recorren el cable
        self._anim_dash_offset = 0.0 # desplazamiento de guiones para efecto de flujo
        self._anim_speed = 0.02      # velocidad de avance de las burbujas
        self._dash_speed = 1.5       # velocidad del desplazamiento de guiones

        self.update_path()

    def set_temp_end(self, pos: QPointF):
        """Establece una posición temporal de final mientras se arrastra."""
        self._temp_end_pos = pos
        self.update_path()
    
    def get_port_position(self, item, port_type, port_name):
        """Obtiene la posición del puerto usando API del nodo si está disponible."""
        try:
            if hasattr(item, 'get_port_position'):
                return item.get_port_position(port_name, port_type)
        except Exception:
            pass
        # Fallback a centro del borde correspondiente
        rect = item.rect()
        pos = item.scenePos()
        if port_type == "output":
            return pos + QPointF(rect.width(), rect.height() / 2)
        else:
            return pos + QPointF(0, rect.height() / 2)
    
    def update_path(self):
        """Actualiza la ruta de la conexión."""
        if not self.start_item:
            return
            
        start_pos = self.get_port_position(self.start_item, "output", self.start_port)
        
        if self.end_item:
            end_pos = self.get_port_position(self.end_item, "input", self.end_port)
        elif self._temp_end_pos is not None:
            end_pos = self._temp_end_pos
        else:
            # Si no hay nodo final ni posición temporal, usar una posición base
            end_pos = start_pos + QPointF(120, 0)
        
        # Crear curva bezier
        path = QPainterPath()
        path.moveTo(start_pos)
        
        # Calcular puntos de control para la curva
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        
        # Distancia de control proporcional a la distancia entre nodos
        ctrl_dist = max(abs(dx) * 0.5, 50)
        
        ctrl1 = start_pos + QPointF(ctrl_dist, 0)
        ctrl2 = end_pos - QPointF(ctrl_dist, 0)
        
        path.cubicTo(ctrl1, ctrl2, end_pos)
        self.setPath(path)

    def finalize_end(self):
        """Limpia el estado temporal una vez fijado el nodo destino."""
        self._temp_end_pos = None
    
    def shape(self):
        """Define la forma de hit más estrecha para evitar capturar clics sobre nodos."""
        path = self.path()
        stroke_path = QPainterPath()
        if not path.isEmpty():
            rect = path.boundingRect()
            stroke_path.addRect(rect.adjusted(-3, -3, 3, 3))
        return stroke_path
    
    def paint(self, painter, option, widget=None):
        """Pinta la conexión con un estilo más elegante y discreto (Nuke/Houdini)."""
        # Sombra suave bajo la línea
        if not self.path().isEmpty():
            painter.save()
            shadow_pen = QPen(QColor(0, 0, 0, 80))
            shadow_pen.setWidth(3)
            painter.setPen(shadow_pen)
            painter.drawPath(self.path().translated(0, 1))
            painter.restore()

        # Línea principal
        if self.isSelected():
            self.pen.setColor(QColor("#f59e0b"))  # amber para selección
            self.pen.setWidth(3)
            self.pen.setStyle(Qt.SolidLine)
        else:
            self.pen.setColor(QColor("#546b8b"))  # azul grisáceo para línea
            self.pen.setWidth(2)
            # Durante arrastre, usar línea discontinua con desplazamiento animado
            if self.end_item is None:
                try:
                    self.pen.setStyle(Qt.DashLine)
                    self.pen.setDashPattern([8, 6])
                    self.pen.setDashOffset(self._anim_dash_offset)
                except Exception:
                    pass
            else:
                self.pen.setStyle(Qt.SolidLine)
        # Estilo Blueprint: línea sólida y terminales circulares
        # (se mantiene animación interna para futuros efectos si se desea)
        self.setPen(self.pen)
        super().paint(painter, option, widget)

        # Terminales: círculo al inicio y punta de flecha al final (direccional)
        if not self.path().isEmpty():
            start_pos = self.path().pointAtPercent(0)
            end_pos = self.path().pointAtPercent(1)
            painter.setPen(Qt.NoPen)
            term_color = QColor("#93c5fd") if not self.isSelected() else QColor("#f59e0b")
            painter.setBrush(QBrush(term_color))
            # círculo en origen
            painter.drawEllipse(QRectF(start_pos.x() - 3, start_pos.y() - 3, 6, 6))
            # flecha en destino
            try:
                # Aproximar dirección con diferencia de puntos sobre la curva
                ref_pos = self.path().pointAtPercent(0.98)
                dir_vec = QPointF(end_pos.x() - ref_pos.x(), end_pos.y() - ref_pos.y())
                length = math.hypot(dir_vec.x(), dir_vec.y()) or 1.0
                dir_unit = QPointF(dir_vec.x() / length, dir_vec.y() / length)
                # perpendicular
                perp = QPointF(-dir_unit.y(), dir_unit.x())
                size = 8.0
                tip = end_pos
                base = QPointF(end_pos.x() - dir_unit.x() * size, end_pos.y() - dir_unit.y() * size)
                p1 = QPointF(base.x() + perp.x() * (size * 0.45), base.y() + perp.y() * (size * 0.45))
                p2 = QPointF(base.x() - perp.x() * (size * 0.45), base.y() - perp.y() * (size * 0.45))
                arrow_path = QPainterPath()
                arrow_path.moveTo(tip)
                arrow_path.lineTo(p1)
                arrow_path.lineTo(p2)
                arrow_path.closeSubpath()
                painter.drawPath(arrow_path)
            except Exception:
                # Fallback: círculo si hay error
                painter.drawEllipse(QRectF(end_pos.x() - 3, end_pos.y() - 3, 6, 6))

        # Burbujas de flujo que recorren la curva (Blueprint-like)
        if not self.path().isEmpty():
            path = self.path()
            painter.save()
            painter.setPen(Qt.NoPen)
            bubble_color = QColor("#93c5fd") if not self.isSelected() else QColor("#f59e0b")
            bubble_color.setAlpha(200)
            painter.setBrush(QBrush(bubble_color))
            lead_t = self._anim_t
            for i in range(3):
                t = lead_t - i * 0.15
                if t < 0:
                    continue
                p = path.pointAtPercent(t)
                size = 6 - i  # burbujas decrecientes
                painter.drawEllipse(QRectF(p.x() - size/2, p.y() - size/2, size, size))
            painter.restore()

    def tick_animation(self):
        """Avanza el estado de animación y solicita repintado."""
        self._anim_t += self._anim_speed
        if self._anim_t > 1.0:
            self._anim_t -= 1.0
        self._anim_dash_offset += self._dash_speed
        if self._anim_dash_offset > 1000.0:
            self._anim_dash_offset = 0.0
        self.update()
