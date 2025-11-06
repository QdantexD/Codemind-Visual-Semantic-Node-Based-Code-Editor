"""
Nodo de Variable con Autocompletado Inteligente
Autor: Eddi Andreé Salazar Matos
Descripción: Nodo especial para variables con sistema de autocompletado tipo FIGMA/Houdini
"""

from PySide6.QtWidgets import (QGraphicsRectItem, QGraphicsSimpleTextItem, QLineEdit, 
                              QGraphicsProxyWidget, QVBoxLayout, QWidget, QLabel)
from PySide6.QtCore import QRectF, Qt, QPointF, Signal, QEvent
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QPainter, QPainterPath, QKeyEvent
from ..graph.node_item import NodeItem
from ..ui.tab_completion_widget import TabCompletionWidget
from ..library.variable_library import variable_library
import sys

class VariableNode(NodeItem):
    """Nodo especial para variables con autocompletado inteligente"""
    
    variable_changed = Signal(str, str, str)  # nombre, tipo, valor
    
    def __init__(self, title="Variable", x=0, y=0, w=200, h=120, node_type="variable"):
        # Llamar al constructor padre pero con tamaño ajustado
        super().__init__(title, x, y, w, h, node_type)
        
        # Configuración específica de variable
        self.variable_name = ""
        self.variable_type = "int"  # Default
        self.variable_value = None
        self._language = variable_library.current_language
        
        # Colores específicos para nodos de variable
        self._bg_color = QColor("#1a365d")  # Azul oscuro
        self._title_bg_color = QColor("#3182ce")  # Azul brillante
        self._border_color = QColor("#2b6cb0")
        self._selected_border_color = QColor("#63b3ed")
        
        # Crear interfaz de entrada
        self._create_variable_interface()
        
        # Widget de autocompletado
        self.completion_widget = None
        self._completion_active = False
        
        # Conectar señales
        variable_library.language_changed.connect(self._on_language_changed)
    
    def _create_variable_interface(self):
        """Crear la interfaz de entrada para la variable"""
        # Crear widget contenedor
        self.input_widget = QWidget()
        layout = QVBoxLayout(self.input_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Label para el nombre
        self.name_label = QLabel("Nombre:")
        self.name_label.setStyleSheet("color: #e2e8f0; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.name_label)
        
        # Campo de entrada para el nombre
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Escribe nombre o presiona TAB...")
        # Marcar para que el filtro global de TAB no lo intercepte
        try:
            self.name_input.setProperty('variable_input', True)
        except Exception:
            pass
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 6px;
                color: #e2e8f0;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3182ce;
                background-color: #2b6cb0;
            }
            QLineEdit:hover {
                border-color: #63b3ed;
            }
        """)
        layout.addWidget(self.name_input)
        
        # Label para el tipo
        self.type_label = QLabel("Tipo:")
        self.type_label.setStyleSheet("color: #e2e8f0; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.type_label)
        
        # Campo de entrada para el tipo (con autocompletado también)
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("int, str, bool, list...")
        # Marcar para que el filtro global de TAB no lo intercepte
        try:
            self.type_input.setProperty('variable_input', True)
        except Exception:
            pass
        self.type_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 6px;
                color: #e2e8f0;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3182ce;
                background-color: #2b6cb0;
            }
        """)
        layout.addWidget(self.type_input)
        
        # Label para el valor
        self.value_label = QLabel("Valor:")
        self.value_label.setStyleSheet("color: #e2e8f0; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        # Campo de entrada para el valor
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Valor inicial...")
        self.value_input.setStyleSheet("""
            QLineEdit {
                background-color: #1a202c;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 6px;
                color: #68d391;
                font-size: 12px;
                font-family: monospace;
            }
            QLineEdit:focus {
                border-color: #38a169;
                background-color: #22543d;
            }
        """)
        layout.addWidget(self.value_input)
        
        # Agregar widget al nodo gráfico
        self.proxy_widget = QGraphicsProxyWidget(self)
        self.proxy_widget.setWidget(self.input_widget)
        
        # Posicionar el widget dentro del nodo
        self.proxy_widget.setPos(10, self.title_h + 10)
        self.proxy_widget.setMinimumSize(180, 100)
        
        # Conectar señales
        self.name_input.textChanged.connect(self._on_name_changed)
        self.type_input.textChanged.connect(self._on_type_changed)
        self.value_input.textChanged.connect(self._on_value_changed)
        
        # Eventos de teclado para autocompletado
        self.name_input.installEventFilter(self)
        self.type_input.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Filtro de eventos para capturar TAB"""
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                # No interceptar TAB aquí; permitir que NodeView abra el menú TAB
                return False
            elif event.key() == Qt.Key_Escape and self._completion_active:
                self._hide_completion_menu()
                return True

        return super().eventFilter(obj, event)
    
    def _show_completion_menu(self, input_field):
        """Mostrar menú de autocompletado"""
        # Determinar qué tipo de sugerencias mostrar
        if input_field == self.name_input:
            # Para nombres, mostrar todas las sugerencias del tipo actual
            partial_text = self.name_input.text()
            self._show_variable_suggestions(partial_text, input_field)
        elif input_field == self.type_input:
            # Para tipos, mostrar tipos disponibles del lenguaje actual
            partial_text = self.type_input.text()
            self._show_type_suggestions(partial_text, input_field)
    
    def _show_variable_suggestions(self, partial_name: str, input_field):
        """Mostrar sugerencias de nombres de variables"""
        # Crear widget de autocompletado si no existe
        if not self.completion_widget:
            self.completion_widget = TabCompletionWidget()
            self.completion_widget.variable_selected.connect(self._on_variable_selected)
            self.completion_widget.closed.connect(self._on_completion_closed)
        
        # Obtener posición global del campo de entrada
        global_pos = input_field.mapToGlobal(input_field.rect().bottomLeft())
        
        # Mostrar sugerencias
        self.completion_widget.show_at_position(global_pos, partial_name)
        self._completion_active = True
    
    def _show_type_suggestions(self, partial_type: str, input_field):
        """Mostrar sugerencias de tipos de datos"""
        # Obtener tipos disponibles para el lenguaje actual
        available_types = variable_library.get_all_suggestions()
        
        # Filtrar por texto parcial
        filtered_types = {}
        for type_name, type_info in available_types.items():
            if not partial_type or partial_type.lower() in type_name.lower():
                filtered_types[type_name] = type_info
        
        # Mostrar en un menú simple (por ahora)
        # TODO: Crear un widget similar para tipos
        print(f"Sugerencias de tipos: {list(filtered_types.keys())}")
    
    def _on_variable_selected(self, var_type: str, var_name: str):
        """Cuando se selecciona una variable del menú"""
        # Actualizar campos
        self.variable_type = var_type
        self.variable_name = var_name
        
        self.name_input.setText(var_name)
        self.type_input.setText(var_type)
        
        # Establecer valor por defecto según el tipo
        default_values = {
            "int": "0",
            "str": "\"\"",
            "bool": "True",
            "list": "[]",
            "dict": "{}",
            "float": "0.0",
            "double": "0.0",
            "long double": "0.0",
            "number": "0",
            "string": "\"\"",
            "std::string": "\"\"",
            "std::wstring": "\"\"",
            "boolean": "True",
            "array": "[]",
            "object": "{}",
            "vector": "[]",
            "list": "[]",
            "deque": "[]",
            "set": "{}",
            "unordered_set": "{}",
            "map": "{}",
            "unordered_map": "{}",
            "pair": "{}",
            "optional": "nullopt",
            "variant": "{}",
            # C++ fundamentales adicionales
            "char": "'\\0'",
            "signed char": "'\\0'",
            "unsigned char": "'\\0'",
            "wchar_t": "'\\0'",
            "char16_t": "'\\0'",
            "char32_t": "'\\0'",
            "short": "0",
            "unsigned short": "0",
            "unsigned int": "0",
            "long": "0",
            "unsigned long": "0",
            "long long": "0",
            "unsigned long long": "0",
            "size_t": "0"
        }
        
        default_value = default_values.get(var_type, "None")
        self.value_input.setText(default_value)
        
        # Emitir señal
        self.variable_changed.emit(var_name, var_type, default_value)
    
    def _on_completion_closed(self):
        """Cuando se cierra el menú de autocompletado"""
        self._completion_active = False
    
    def _hide_completion_menu(self):
        """Ocultar menú de autocompletado"""
        if self.completion_widget:
            self.completion_widget.close_widget()
        self._completion_active = False
    
    def _on_name_changed(self, text):
        """Cuando cambia el nombre de la variable"""
        self.variable_name = text.strip()
        self.title = text.strip() or "Variable"
        self.title_item.setText(self.title)
        self._update_title_pos()
        
        # Emitir señal
        self.variable_changed.emit(self.variable_name, self.variable_type, self.variable_value)
    
    def _on_type_changed(self, text):
        """Cuando cambia el tipo de la variable"""
        self.variable_type = text.strip()
        
        # Emitir señal
        self.variable_changed.emit(self.variable_name, self.variable_type, self.variable_value)
    
    def _on_value_changed(self, text):
        """Cuando cambia el valor de la variable"""
        self.variable_value = text.strip()
        
        # Emitir señal
        self.variable_changed.emit(self.variable_name, self.variable_type, self.variable_value)
    
    def _on_language_changed(self, language: str):
        """Cuando cambia el lenguaje de programación"""
        self._language = language
        
        # Actualizar placeholder y sugerencias
        language_info = {
            "python": "int, str, bool, list, dict...",
            "cpp": "int, string, bool, vector, map...",
            "javascript": "number, string, boolean, array, object..."
        }
        
        self.type_input.setPlaceholderText(language_info.get(language, "Tipo de dato..."))
    
    def get_variable_info(self) -> dict:
        """Obtener información completa de la variable"""
        return {
            "name": self.variable_name,
            "type": self.variable_type,
            "value": self.variable_value,
            "language": self._language,
            "node_id": self.id
        }
    
    def set_variable_info(self, info: dict):
        """Establecer información de la variable"""
        if "name" in info:
            self.variable_name = info["name"]
            self.name_input.setText(info["name"])
        
        if "type" in info:
            self.variable_type = info["type"]
            self.type_input.setText(info["type"])
        
        if "value" in info:
            self.variable_value = info["value"]
            self.value_input.setText(str(info["value"]))
        
        if "language" in info:
            self._language = info["language"]
            variable_library.current_language = info["language"]
    
    def to_dict(self) -> dict:
        """Convertir a diccionario para guardar"""
        data = super().to_dict() if hasattr(super(), 'to_dict') else {}
        data.update({
            "type": "variable_node",
            "variable_info": self.get_variable_info()
        })
        return data
    
    @classmethod
    def from_dict(cls, data: dict):
        """Crear desde diccionario"""
        var_info = data.get("variable_info", {})
        node = cls(
            title=var_info.get("name", "Variable"),
            x=data.get("x", 0),
            y=data.get("y", 0)
        )
        node.set_variable_info(var_info)
        return node