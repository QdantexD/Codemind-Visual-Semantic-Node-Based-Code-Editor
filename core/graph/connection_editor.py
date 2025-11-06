from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ConnectionEditor(QWidget):
    """Ventana ligera para gestionar la conexión entre dos nodos.

    Muestra información de origen/destino, puertos y un panel para
    notas o configuración de variables. Se puede ampliar con Ctrl+M.
    """

    def __init__(self, connection, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor de Conexión")
        self.setWindowFlag(Qt.Window)
        self._expanded = False
        self._connection = connection

        # Datos de conexión
        start_item = getattr(connection, "start_item", None)
        end_item = getattr(connection, "end_item", None)
        start_port = getattr(connection, "start_port", "output")
        end_port = getattr(connection, "end_port", "input")

        # Layout principal
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Cabecera
        title = QLabel("Conexión entre nodos")
        title.setFont(QFont("Sans", 12, QFont.Bold))
        title.setAlignment(Qt.AlignLeft)
        root.addWidget(title)

        # Línea de contexto de nodos
        info_layout = QVBoxLayout()
        lbl_a = QLabel(f"Origen: {getattr(start_item, 'title', 'Node')} • Puerto: {start_port}")
        lbl_b = QLabel(f"Destino: {getattr(end_item, 'title', 'Node')} • Puerto: {end_port}")
        for lbl in (lbl_a, lbl_b):
            lbl.setStyleSheet("color: #e2e8f0; font-size: 12px;")
        info_layout.addWidget(lbl_a)
        info_layout.addWidget(lbl_b)
        root.addLayout(info_layout)

        # Panel de variables / notas (placeholder funcional)
        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "Opcional: describe el mapeo de variables, reglas o notas de esta conexión."
        )
        self.notes.setStyleSheet(
            "QTextEdit { background-color: #0f172a; color: #e2e8f0;"
            " border: 1px solid #334155; }"
        )
        self.notes.setMinimumHeight(100)
        root.addWidget(self.notes)

        # Controles inferiores
        controls = QHBoxLayout()
        self.expand_btn = QPushButton("Ampliar")
        self.expand_btn.clicked.connect(self.expand)
        # Crear nodo compuesto entre origen y destino
        self.compose_btn = QPushButton("Insertar nodo compuesto")
        self.compose_btn.clicked.connect(self.create_composite_between)
        self.close_btn = QPushButton("Cerrar")
        self.close_btn.clicked.connect(self.close)
        controls.addWidget(self.expand_btn)
        controls.addWidget(self.compose_btn)
        controls.addStretch(1)
        controls.addWidget(self.close_btn)
        root.addLayout(controls)

        # Tamaño inicial compacto
        self.resize(420, 240)

    def expand(self):
        """Ampliar/contraer la ventana para ver más contenido."""
        if not self._expanded:
            self.resize(720, 480)
            self._expanded = True
            self.expand_btn.setText("Contraer")
        else:
            self.resize(420, 240)
            self._expanded = False
            self.expand_btn.setText("Ampliar")

    def bring_to_front(self):
        """Traer la ventana al frente y enfocarla."""
        try:
            self.show()
            self.raise_()
            self.activateWindow()
        except Exception:
            pass

    def create_composite_between(self):
        """Crea e inserta un nodo 'compuesto' entre el origen y destino.

        - Inserta un nuevo nodo con puertos input/output.
        - Reemplaza la conexión actual por dos: origen→compuesto y compuesto→destino.
        - Posiciona el nodo compuesto a mitad de camino.
        """
        try:
            conn = self._connection
            start_item = getattr(conn, "start_item", None)
            end_item = getattr(conn, "end_item", None)
            if start_item is None or end_item is None:
                return
            scene = getattr(start_item, 'scene', lambda: None)()
            view = None
            try:
                views = scene.views() if scene else []
                view = views[0] if views else None
            except Exception:
                view = None
            if view is None:
                return
            # Posición media entre ambos nodos
            a = getattr(start_item, 'scenePos', lambda: None)()
            b = getattr(end_item, 'scenePos', lambda: None)()
            if a is None or b is None:
                return
            mid = (a + (b - a) * 0.5)
            # Crear nodo compuesto
            title = f"{getattr(start_item, 'title', 'Nodo A')} ➜ {getattr(end_item, 'title', 'Nodo B')}"
            composite = view.add_node_with_ports(
                title=title,
                x=mid.x(),
                y=mid.y(),
                node_type="process",
                inputs=["input"],
                outputs=["output"],
                content=f"COMPOSE({getattr(start_item, 'title', 'A')} -> {getattr(end_item, 'title', 'B')})"
            )
            if composite is None:
                return
            # Quitar la conexión original y crear dos nuevas
            try:
                view.remove_connection(conn)
            except Exception:
                pass
            try:
                view.add_connection(start_item, composite, start_port=getattr(conn, 'start_port', 'output'), end_port='input')
            except Exception:
                pass
            try:
                view.add_connection(composite, end_item, start_port='output', end_port=getattr(conn, 'end_port', 'input'))
            except Exception:
                pass
            # Centrar y cerrar editor
            try:
                view.centerOn(composite)
            except Exception:
                pass
            self.close()
        except Exception:
            # Evitar que errores rompan la sesión; el botón es optativo
            pass