from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

try:
    # Importar el generador del sombrero de copa negro
    from .app_icons import make_top_hat_icon
except Exception:
    make_top_hat_icon = None  # type: ignore


def ensure_app_icon_assets(project_root: Optional[Path] = None, neon_color: Optional[str] = None) -> Path:
    """Genera PNGs multi‑resolución y un .ico en 'assets/'.

    Devuelve la ruta esperada del .ico (puede no existir si falta Pillow).
    """
    root = Path(project_root) if project_root else Path(__file__).resolve().parents[2]
    assets = root / "assets"
    assets.mkdir(exist_ok=True)

    sizes = [16, 24, 32, 48, 64, 96, 128, 256]
    png_paths = []

    # Renderizar icono base
    try:
        if make_top_hat_icon is None:
            raise RuntimeError("make_top_hat_icon no disponible")
        icon: QIcon = make_top_hat_icon(256, neon_color)
        for s in sizes:
            pm = icon.pixmap(QSize(s, s))
            out_png = assets / f"app-{s}.png"
            try:
                pm.save(str(out_png), "PNG")
                png_paths.append(out_png)
            except Exception:
                pass
    except Exception:
        # Si falla, aún devolvemos la ruta del .ico para flujo posterior
        pass

    ico_path = assets / "app.ico"
    # Crear .ico multi‑tamaño con Pillow si está disponible
    try:
        from PIL import Image
        if png_paths:
            images = [Image.open(str(p)) for p in png_paths]
            base_img = images[0]
            sizes_tuple = [(im.width, im.height) for im in images]
            base_img.save(str(ico_path), format="ICO", sizes=sizes_tuple)
    except Exception:
        # Si Pillow no está instalado, el .ico podría no generarse
        pass

    return ico_path


__all__ = ["ensure_app_icon_assets"]