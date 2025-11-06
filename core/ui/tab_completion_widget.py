"""
Widget de Autocompletado con TAB - Estilo FIGMA/Houdini
Autor: Eddi Andreé Salazar Matos
Descripción: Menú de sugerencias que aparece al presionar TAB
"""

from PySide6.QtWidgets import (QWidget, QListWidget, QListWidgetItem, QVBoxLayout, 
                              QHBoxLayout, QLabel, QFrame, QPushButton)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QPalette, QColor
from typing import List, Dict
from ..library.variable_library import variable_library

class TabCompletionWidget(QWidget):
    """Widget de autocompletado que aparece al presionar TAB"""
    
    # Señales
    variable_selected = Signal(str, str)  # tipo, nombre
    closed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Configuración visual
        self.setup_ui()
        self.current_suggestions = []
        self.selected_index = 0
        
        # Timer para cerrar automáticamente si no hay interacción
        self.close_timer = QTimer()
        self.close_timer.setSingleShot(True)
        self.close_timer.timeout.connect(self.close_widget)
        self.close_timer.start(5000)  # Cerrar después de 5 segundos
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Frame principal con estilo
        self.main_frame = QFrame()
        self.main_frame.setObjectName("completionFrame")
        self.main_frame.setStyleSheet("""
            QFrame#completionFrame {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        
        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(8, 8, 8, 8)
        frame_layout.setSpacing(4)
        
        # Header con título
        header_label = QLabel("Variables Disponibles")
        header_label.setStyleSheet("""
            QLabel {
                color: #e2e8f0;
                font-weight: bold;
                font-size: 12px;
                padding: 4px;
            }
        """)
        frame_layout.addWidget(header_label)
        
        # Lista de sugerencias
        self.suggestions_list = QListWidget()
        self.suggestions_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background-color: transparent;
                border: none;
                padding: 6px;
                margin: 2px 0;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: rgba(66, 153, 225, 0.2);
            }
            QListWidget::item:selected {
                background-color: #4299e1;
                color: white;
            }
        """)
        
        self.suggestions_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.suggestions_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.suggestions_list.setMaximumHeight(300)
        self.suggestions_list.setMinimumWidth(250)
        self.suggestions_list.itemClicked.connect(self.on_item_clicked)
        self.suggestions_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        frame_layout.addWidget(self.suggestions_list)
        
        # Footer con información
        footer_label = QLabel("Presiona TAB o ENTER para seleccionar")
        footer_label.setStyleSheet("""
            QLabel {
                color: #a0aec0;
                font-size: 10px;
                padding: 4px;
            }
        """)
        frame_layout.addWidget(footer_label)
        
        main_layout.addWidget(self.main_frame)
    
    def show_suggestions(self, partial_name: str = ""):
        """Mostrar sugerencias de variables"""
        # Obtener sugerencias del sistema
        suggestions = variable_library.get_tab_completion_suggestions(partial_name)
        self.current_suggestions = suggestions
        
        # Limpiar lista anterior
        self.suggestions_list.clear()
        
        # Agregar nuevas sugerencias
        for suggestion in suggestions:
            item_widget = self.create_suggestion_item(suggestion)
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            list_item.setData(Qt.UserRole, suggestion)
            
            self.suggestions_list.addItem(list_item)
            self.suggestions_list.setItemWidget(list_item, item_widget)
        
        # Seleccionar primer elemento
        if self.suggestions_list.count() > 0:
            self.suggestions_list.setCurrentRow(0)
            self.selected_index = 0
        
        # Ajustar tamaño
        self.adjust_size()
        
        # Mostrar widget
        self.show()
        self.raise_()
        self.activateWindow()
    
    def create_suggestion_item(self, suggestion: dict) -> QWidget:
        """Crear widget visual para una sugerencia"""
        item_widget = QWidget()
        layout = QHBoxLayout(item_widget)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Icono
        icon_label = QLabel(suggestion["icon"])
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)
        
        # Información principal
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        # Nombre de la variable
        name_label = QLabel(suggestion["name"])
        name_label.setStyleSheet("color: #e2e8f0; font-weight: 500;")
        info_layout.addWidget(name_label)
        
        # Tipo y descripción
        type_text = f"{suggestion['type']} - {suggestion['description']}"
        type_label = QLabel(type_text)
        type_label.setStyleSheet("color: #a0aec0; font-size: 10px;")
        info_layout.addWidget(type_label)
        
        layout.addWidget(info_widget)
        layout.addStretch()
        
        # Prioridad (si es alta)
        if suggestion.get("priority", 0) > 50:
            star_label = QLabel("⭐")
            star_label.setStyleSheet("color: #f6e05e; font-size: 12px;")
            layout.addWidget(star_label)
        
        return item_widget
    
    def adjust_size(self):
        """Ajustar el tamaño del widget"""
        # Calcular tamaño basado en el contenido
        item_count = self.suggestions_list.count()
        if item_count == 0:
            self.hide()
            return
        
        # Altura por elemento + header + footer
        item_height = 50  # Aproximado por elemento
        header_height = 30
        footer_height = 20
        total_height = min(400, header_height + (item_height * item_count) + footer_height)
        
        self.resize(300, total_height)
    
    def on_item_clicked(self, item):
        """Cuando se hace clic en un elemento"""
        suggestion = item.data(Qt.UserRole)
        if suggestion:
            self.selected_index = self.suggestions_list.row(item)
    
    def on_item_double_clicked(self, item):
        """Cuando se hace doble clic en un elemento"""
        suggestion = item.data(Qt.UserRole)
        if suggestion:
            self.select_variable(suggestion)
    
    def select_variable(self, suggestion: dict = None):
        """Seleccionar una variable y emitir señal"""
        if suggestion is None:
            current_item = self.suggestions_list.currentItem()
            if current_item:
                suggestion = current_item.data(Qt.UserRole)
        
        if suggestion:
            self.variable_selected.emit(suggestion["type"], suggestion["name"])
            
            # Agregar a recientes
            variable_library.add_recent_variable(
                suggestion["type"], 
                suggestion["name"], 
                None  # Valor se establecerá después
            )
            
            self.close_widget()
    
    def keyPressEvent(self, event):
        """Manejar eventos de teclado"""
        if event.key() == Qt.Key_Tab or event.key() == Qt.Key_Return:
            self.select_variable()
            event.accept()
        elif event.key() == Qt.Key_Escape:
            self.close_widget()
            event.accept()
        elif event.key() == Qt.Key_Up:
            self.move_selection(-1)
            event.accept()
        elif event.key() == Qt.Key_Down:
            self.move_selection(1)
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def move_selection(self, direction: int):
        """Mover la selección arriba/abajo"""
        current_row = self.suggestions_list.currentRow()
        new_row = current_row + direction
        
        # Limitar dentro del rango
        if 0 <= new_row < self.suggestions_list.count():
            self.suggestions_list.setCurrentRow(new_row)
            self.selected_index = new_row
    
    def close_widget(self):
        """Cerrar el widget"""
        self.close_timer.stop()
        self.closed.emit()
        self.close()
    
    def focusOutEvent(self, event):
        """Cuando pierde el foco"""
        self.close_widget()
        super().focusOutEvent(event)
    
    def show_at_position(self, global_pos, partial_name: str = ""):
        """Mostrar el widget en una posición específica"""
        self.show_suggestions(partial_name)
        
        # Ajustar posición para que no se salga de la pantalla
        screen_geometry = self.screen().geometry()
        widget_size = self.size()
        
        x = min(global_pos.x(), screen_geometry.width() - widget_size.width())
        y = min(global_pos.y(), screen_geometry.height() - widget_size.height())
        
        self.move(x, y)