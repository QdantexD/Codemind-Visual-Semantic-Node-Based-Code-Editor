from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath,
    QLinearGradient, QRadialGradient
)
from PySide6.QtCore import QRectF, QPointF, Qt


def _render_hat_pixmap(size: int, theme: str = "auto") -> QPixmap:
    """Renderiza un sombrero elegante con sombras, brillos y detalles en un QPixmap."""
    s = int(max(16, min(512, size)))
    pm = QPixmap(s, s)
    pm.fill(QColor(0, 0, 0, 0))

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)

    # Paleta elegante
    dark_bg_top = QColor(22, 27, 34, 88)
    dark_bg_bottom = QColor(12, 16, 20, 64)
    hat_dark_1 = QColor("#0b1220")
    hat_dark_2 = QColor("#111827")
    outline = QColor("#1e293b")
    band_amber_1 = QColor("#f59e0b")
    band_amber_2 = QColor("#d97706")
    accent_teal_1 = QColor("#14b8a6")
    accent_teal_2 = QColor("#0f766e")

    # Fondo con halo sutil
    bg = QLinearGradient(0, 0, 0, s)
    bg.setColorAt(0.0, dark_bg_top)
    bg.setColorAt(1.0, dark_bg_bottom)
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(bg))
    p.drawRoundedRect(QRectF(1, 1, s - 2, s - 2), s * 0.2, s * 0.2)

    # Sombra suave bajo el ala (brim)
    shadow_rect = QRectF(s * 0.12, s * 0.64, s * 0.76, s * 0.18)
    shadow = QRadialGradient(QPointF(shadow_rect.center().x(), shadow_rect.center().y()), s * 0.45)
    shadow.setColorAt(0.0, QColor(0, 0, 0, 70))
    shadow.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(QBrush(shadow))
    p.drawEllipse(shadow_rect)

    # Ala con gradiente y leve perspectiva
    brim_rect = QRectF(s * 0.1, s * 0.58, s * 0.80, s * 0.20)
    brim_grad = QLinearGradient(brim_rect.left(), brim_rect.top(), brim_rect.right(), brim_rect.bottom())
    brim_grad.setColorAt(0.0, accent_teal_1)
    brim_grad.setColorAt(1.0, accent_teal_2)
    p.setBrush(QBrush(brim_grad))
    p.setPen(QPen(QColor(20, 30, 40, 160), max(1.0, s * 0.02)))
    p.drawEllipse(brim_rect)

    # Copa con curvas suaves (más elegante)
    crown_top_y = s * 0.26
    crown_bottom_y = s * 0.56
    crown_left_x = s * 0.28
    crown_right_x = s * 0.72
    crown = QPainterPath()
    crown.moveTo(QPointF(crown_left_x, crown_bottom_y))
    crown.quadTo(QPointF(crown_left_x + s * 0.06, crown_top_y + s * 0.02), QPointF(crown_left_x + s * 0.09, crown_top_y))
    crown.lineTo(QPointF(crown_right_x - s * 0.09, crown_top_y))
    crown.quadTo(QPointF(crown_right_x - s * 0.06, crown_top_y + s * 0.02), QPointF(crown_right_x, crown_bottom_y))
    crown.closeSubpath()

    crown_grad = QLinearGradient(crown_left_x, crown_top_y, crown_right_x, crown_bottom_y)
    crown_grad.setColorAt(0.0, hat_dark_1)
    crown_grad.setColorAt(1.0, hat_dark_2)
    p.setBrush(QBrush(crown_grad))
    p.setPen(QPen(outline, max(1.0, s * 0.015)))
    p.drawPath(crown)

    # Banda dorada con brillo
    band_rect = QRectF(crown_left_x + s * 0.02, crown_top_y + s * 0.12,
                       (crown_right_x - s * 0.02) - (crown_left_x + s * 0.02), s * 0.06)
    band_grad = QLinearGradient(band_rect.left(), band_rect.top(), band_rect.right(), band_rect.bottom())
    band_grad.setColorAt(0.0, band_amber_1)
    band_grad.setColorAt(1.0, band_amber_2)
    p.setBrush(QBrush(band_grad))
    p.setPen(QPen(QColor(60, 45, 20, 200), max(1.0, s * 0.01)))
    p.drawRoundedRect(band_rect, s * 0.012, s * 0.012)

    # Reflejo suave en la copa
    p.setPen(QPen(QColor(255, 255, 255, 30), max(1.0, s * 0.012)))
    p.drawLine(QPointF(crown_left_x + s * 0.07, crown_top_y + s * 0.02),
               QPointF(crown_left_x + s * 0.22, crown_top_y + s * 0.09))

    # Sutileza extra: borde inferior de ala
    p.setPen(QPen(QColor(255, 255, 255, 36), max(1.0, s * 0.010)))
    p.drawArc(brim_rect, 200 * 16, 140 * 16)

    p.end()
    return pm


def make_hat_icon(size: int = 64) -> QIcon:
    """Genera un QIcon multi‑resolución con sombrero elegante (HiDPI)."""
    try:
        base = int(max(32, min(256, size)))
    except Exception:
        base = 64

    icon = QIcon()
    # Añadir múltiples tamaños para que Qt escoja el mejor en cada contexto
    for s in (16, 24, 32, 48, 64, 96, 128, 256):
        if s <= base * 4:  # límite de memoria razonable
            icon.addPixmap(_render_hat_pixmap(s))
    return icon


# --------- Variante NEÓN ---------
def _render_hat_pixmap_neon(size: int, glow: QColor) -> QPixmap:
    """Sombrero con resplandor neón: halo, borde brillante y realce en banda."""
    s = int(max(16, min(512, size)))
    pm = QPixmap(s, s)
    pm.fill(QColor(0, 0, 0, 0))

    # Render base primero
    base = _render_hat_pixmap(s)

    # Crear lienzo y pintar base
    final_pm = QPixmap(s, s)
    final_pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(final_pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.drawPixmap(0, 0, base)

    # Halo neón detrás
    halo = QRadialGradient(QPointF(s * 0.5, s * 0.5), s * 0.55)
    halo.setColorAt(0.0, QColor(glow.red(), glow.green(), glow.blue(), 80))
    halo.setColorAt(0.6, QColor(glow.red(), glow.green(), glow.blue(), 28))
    halo.setColorAt(1.0, QColor(glow.red(), glow.green(), glow.blue(), 0))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(halo))
    p.drawRoundedRect(QRectF(0, 0, s, s), s * 0.22, s * 0.22)

    # Borde brillando alrededor de la copa (trazo múltiple para bloom)
    center_y = s * 0.42
    left_x = s * 0.28
    right_x = s * 0.72
    for i, alpha in enumerate((120, 70, 40, 22)):
        p.setPen(QPen(QColor(glow.red(), glow.green(), glow.blue(), alpha), max(1.0, s * (0.010 + i * 0.006))))
        p.drawLine(QPointF(left_x, center_y), QPointF(right_x, center_y))

    # Realce de ala (arco inferior con glow)
    brim_rect = QRectF(s * 0.10, s * 0.58, s * 0.80, s * 0.20)
    for i, alpha in enumerate((110, 60, 30)):
        p.setPen(QPen(QColor(glow.red(), glow.green(), glow.blue(), alpha), max(1.0, s * (0.012 + i * 0.006))))
        p.drawArc(brim_rect, 210 * 16, 120 * 16)

    # Puntos de luz sobre la banda
    p.setPen(QPen(QColor(glow.red(), glow.green(), glow.blue(), 160), max(1.0, s * 0.012)))
    p.drawPoint(QPointF(s * 0.50, s * 0.36))
    p.drawPoint(QPointF(s * 0.58, s * 0.37))

    p.end()
    return final_pm


def make_hat_icon_neon(size: int = 64, color: str = "magenta") -> QIcon:
    """QIcon con variante neón. Colores: 'magenta', 'cyan', 'violet', 'lime'."""
    try:
        base = int(max(32, min(256, size)))
    except Exception:
        base = 64

    palette = {
        "magenta": QColor(255, 80, 214),
        "cyan": QColor(34, 211, 238),
        "violet": QColor(167, 139, 250),
        "lime": QColor(132, 204, 22),
    }
    glow = palette.get(color, palette["magenta"])

    icon = QIcon()
    for s in (16, 24, 32, 48, 64, 96, 128, 256):
        if s <= base * 4:
            icon.addPixmap(_render_hat_pixmap_neon(s, glow))
    return icon


# --------- Sombrero de copa (chistera) negro ---------
def _render_top_hat_pixmap(size: int, neon: QColor | None = None) -> QPixmap:
    """Renderiza un sombrero de copa elegante completamente negro.

    Si 'neon' se especifica, añade un halo muy sutil alrededor.
    """
    s = int(max(16, min(512, size)))
    pm = QPixmap(s, s)
    pm.fill(QColor(0, 0, 0, 0))

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)

    # Halo neón opcional (muy tenue)
    if neon is not None:
        halo = QRadialGradient(QPointF(s * 0.5, s * 0.5), s * 0.6)
        halo.setColorAt(0.0, QColor(neon.red(), neon.green(), neon.blue(), 26))
        halo.setColorAt(1.0, QColor(neon.red(), neon.green(), neon.blue(), 0))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(halo))
        p.drawRoundedRect(QRectF(1, 1, s - 2, s - 2), s * 0.2, s * 0.2)

    # Paleta negros
    black_1 = QColor(10, 10, 10)
    black_2 = QColor(18, 18, 18)
    black_3 = QColor(28, 28, 28)
    outline = QColor(50, 50, 50)

    # Ala: elipse muy fina y ancha
    brim_rect = QRectF(s * 0.08, s * 0.66, s * 0.84, s * 0.16)
    brim_grad = QLinearGradient(brim_rect.left(), brim_rect.top(), brim_rect.right(), brim_rect.bottom())
    brim_grad.setColorAt(0.0, black_2)
    brim_grad.setColorAt(1.0, black_1)
    p.setBrush(QBrush(brim_grad))
    p.setPen(QPen(outline, max(1.0, s * 0.02)))
    p.drawEllipse(brim_rect)

    # Cuerpo cilíndrico: tapa superior elíptica + pared recta
    top_ellipse = QRectF(s * 0.28, s * 0.20, s * 0.44, s * 0.12)
    body_rect = QRectF(s * 0.26, s * 0.26, s * 0.48, s * 0.40)

    # Pared con gradiente vertical
    body_grad = QLinearGradient(body_rect.center().x(), body_rect.top(), body_rect.center().x(), body_rect.bottom())
    body_grad.setColorAt(0.0, black_3)
    body_grad.setColorAt(1.0, black_1)
    p.setBrush(QBrush(body_grad))
    p.setPen(QPen(outline, max(1.0, s * 0.016)))
    p.drawRoundedRect(body_rect, s * 0.02, s * 0.02)

    # Tapa superior (brillo muy leve)
    top_grad = QLinearGradient(top_ellipse.left(), top_ellipse.top(), top_ellipse.right(), top_ellipse.bottom())
    top_grad.setColorAt(0.0, black_2)
    top_grad.setColorAt(1.0, black_1)
    p.setBrush(QBrush(top_grad))
    p.setPen(QPen(outline, max(1.0, s * 0.016)))
    p.drawEllipse(top_ellipse)

    # Banda negra (apenas distinguible)
    band_rect = QRectF(body_rect.left() + s * 0.02, body_rect.top() + s * 0.22,
                       body_rect.width() - s * 0.04, s * 0.06)
    band_grad = QLinearGradient(band_rect.left(), band_rect.top(), band_rect.right(), band_rect.bottom())
    band_grad.setColorAt(0.0, QColor(32, 32, 32))
    band_grad.setColorAt(1.0, QColor(22, 22, 22))
    p.setBrush(QBrush(band_grad))
    p.setPen(QPen(QColor(40, 40, 40), max(1.0, s * 0.010)))
    p.drawRoundedRect(band_rect, s * 0.012, s * 0.012)

    # Brillos mínimos para elegancia
    p.setPen(QPen(QColor(255, 255, 255, 22), max(1.0, s * 0.010)))
    p.drawLine(QPointF(body_rect.left() + s * 0.06, body_rect.top() + s * 0.04),
               QPointF(body_rect.left() + s * 0.20, body_rect.top() + s * 0.12))

    p.end()
    return pm


def make_top_hat_icon(size: int = 64, neon_color: str | None = None) -> QIcon:
    """Crea un QIcon de sombrero de copa negro.

    Si se pasa 'neon_color' en {'magenta','cyan','violet','lime'}, se añade halo sutil.
    """
    try:
        base = int(max(32, min(256, size)))
    except Exception:
        base = 64

    palette = {
        "magenta": QColor(255, 80, 214),
        "cyan": QColor(34, 211, 238),
        "violet": QColor(167, 139, 250),
        "lime": QColor(132, 204, 22),
    }
    glow = palette.get(neon_color) if neon_color else None

    icon = QIcon()
    for s in (16, 24, 32, 48, 64, 96, 128, 256):
        if s <= base * 4:
            icon.addPixmap(_render_top_hat_pixmap(s, glow))
    return icon