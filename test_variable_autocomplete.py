#!/usr/bin/env python3
"""
Prueba del sistema de autocompletado de variables
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from core.graph.node_view import NodeView

def test_variable_autocomplete():
    """Prueba el sistema de autocompletado de variables"""
    app = QApplication(sys.argv)
    
    # Crear ventana principal
    window = QWidget()
    window.setWindowTitle("Editor de Nodos - Sistema de Variables con Autocompletado")
    window.resize(1200, 800)
    
    # Crear layout
    layout = QVBoxLayout()
    
    # Añadir etiqueta con instrucciones
    label = QLabel("""
    <h3>Editor de Variables con Autocompletado Inteligente</h3>
    <p><b>Instrucciones:</b></p>
    <ul>
        <li>Presiona <b>TAB</b> para abrir el menú de creación de nodos</li>
        <li>Selecciona "Variable Python/C++/JavaScript (con autocompletado)"</li>
        <li>Haz clic en el campo de nombre o tipo de la variable</li>
        <li>Presiona <b>TAB</b> dentro del campo para ver las sugerencias</li>
        <li>Usa las flechas del teclado para navegar y Enter para seleccionar</li>
    </ul>
    <p><b>Lenguajes soportados:</b> Python, C++, JavaScript</p>
    """)
    label.setStyleSheet("""
        QLabel {
            background-color: #2d3139;
            color: #ffffff;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)
    label.setWordWrap(True)
    label.setTextFormat(Qt.RichText)
    
    # Crear el visor de nodos
    node_view = NodeView()
    node_view.setStyleSheet("""
        QGraphicsView {
            background-color: #1c1e22;
            border: 2px solid #3c4043;
            border-radius: 8px;
        }
    """)
    
    # Añadir widgets al layout
    layout.addWidget(label)
    layout.addWidget(node_view)
    
    window.setLayout(layout)
    window.show()
    
    print("🚀 Sistema de Variables con Autocompletado iniciado!")
    print("Presiona TAB para crear variables con autocompletado inteligente")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_variable_autocomplete()