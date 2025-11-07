import sys
import os
import logging
import traceback
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
#Creador Eddi Andreé Salazar Matos#
#Github: https://github.com/QdantexD#

# -----------------------------
# Imports de core usando el paquete
# -----------------------------
try:
    # Importaciones limpias desde la fachada 'core'
    from core import EditorWindow, MyNodeGraphController
    from core.ui.app_icons import make_hat_icon, make_hat_icon_neon, make_top_hat_icon
    from core.ui.app_icons_export import ensure_app_icon_assets
    from core.library.cpp_bibliotecas_generator import generate_all_cpp_bibliotecas
    # Logging con formato consistente
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    sys.exit(1)

def main():
    """Función principal de la aplicación."""
    try:
        app = QApplication(sys.argv)
        # Establecer un AppUserModelID explícito para que Windows use el icono del EXE
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CodemindEditor.Codemind")
        except Exception:
            pass
        # Alinear QSettings/AppName con EditorWindow para persistencia coherente
        try:
            app.setOrganizationName(getattr(EditorWindow, "ORGANIZATION", "Codemind-Visual"))
            app.setApplicationName(getattr(EditorWindow, "APP_NAME", "Semantic-Node-Editor"))
        except Exception:
            app.setApplicationName("Editor de Texto y Nodos")
        app.setApplicationVersion("1.0")
        
        # Generar assets del icono y usar .ico si está disponible
        try:
            ico_path = ensure_app_icon_assets()
            if ico_path.exists():
                app.setWindowIcon(QIcon(str(ico_path)))
            else:
                app.setWindowIcon(make_top_hat_icon(128))
        except Exception:
            try:
                app.setWindowIcon(make_top_hat_icon(128))
            except Exception:
                pass

        # Generar archivos de Bibliotecas C++ para facilitar conexiones de variables
        try:
            out_dir = generate_all_cpp_bibliotecas()
            if out_dir:
                print(f"[Init] Bibliotecas C++ generadas en: {out_dir}")
        except Exception as e:
            print(f"[Init] Error generando Bibliotecas C++: {e}")

        # Crear ventana principal
        window = EditorWindow()
        
        # Inicializar controlador de nodos dentro de la ventana
        controller = MyNodeGraphController()
        window.set_node_controller(controller)
        
        # Ya se estableció el icono global antes; mantener así para Taskbar.

        window.show()
        
        return app.exec()
    except Exception as e:
        logger.error(f"Error crítico en la aplicación: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
