import sys
import os
import logging
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
#Creador Eddi Andreé Salazar Matos#
#Github: https://github.com/QdantexD#

# -----------------------------
# Imports de core usando el paquete
# -----------------------------
try:
    from core.app.editor_window import EditorWindow
    from core.app.node_view_adapter import MyNodeGraphController
    from core.library.cpp_bibliotecas_generator import generate_all_cpp_bibliotecas
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    sys.exit(1)

def main():
    """Función principal de la aplicación."""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Editor de Texto y Nodos")
        app.setApplicationVersion("1.0")
        
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
        
        window.show()
        
        return app.exec()
    except Exception as e:
        logger.error(f"Error crítico en la aplicación: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
