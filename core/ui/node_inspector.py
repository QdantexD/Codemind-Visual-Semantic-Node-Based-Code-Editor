from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QFormLayout, QInputDialog, QTextEdit, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt


class NodeInspector(QWidget):
    """
    Inspector minimalista y elegante para nodos.
    - Muestra título y tipo
    - Cuenta de puertos IN/OUT
    - Acciones rápidas para añadir y renombrar puertos
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._node = None
        self._updating_content = False

        self.setObjectName("NodeInspector")

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        header = QLabel("Inspector")
        header.setStyleSheet("font-weight: bold; color: #c9d1d9;")
        root.addWidget(header)

        # Separador sutil
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #2f3338;")
        root.addWidget(sep)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Título del nodo")
        self.title_edit.editingFinished.connect(self._apply_title)
        form.addRow("Título", self.title_edit)

        self.type_label = QLabel("-")
        form.addRow("Tipo", self.type_label)

        self.in_count = QLabel("0")
        self.out_count = QLabel("0")
        form.addRow("Puertos IN", self.in_count)
        form.addRow("Puertos OUT", self.out_count)

        root.addLayout(form)

        # Contenido editable del nodo
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Contenido del nodo…")
        self.content_edit.textChanged.connect(self._apply_content)
        root.addWidget(self.content_edit)

        # Acciones rápidas de puertos (grid 2x2 para evitar recortes)
        actions = QGridLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setHorizontalSpacing(6)
        actions.setVerticalSpacing(6)
        self.add_in_btn = QPushButton("Añadir IN…")
        self.add_out_btn = QPushButton("Añadir OUT…")
        self.rename_port_btn = QPushButton("Renombrar puerto…")
        self.remove_port_btn = QPushButton("Eliminar puerto…")
        for b in (self.add_in_btn, self.add_out_btn, self.rename_port_btn, self.remove_port_btn):
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setMinimumHeight(26)
            b.setToolTip(b.text())
        self.add_in_btn.clicked.connect(lambda: self._add_port("input"))
        self.add_out_btn.clicked.connect(lambda: self._add_port("output"))
        self.rename_port_btn.clicked.connect(self._rename_port)
        self.remove_port_btn.clicked.connect(self._remove_port)
        # Disposición en 2 filas, 2 columnas
        actions.addWidget(self.add_in_btn, 0, 0)
        actions.addWidget(self.add_out_btn, 0, 1)
        actions.addWidget(self.rename_port_btn, 1, 0)
        actions.addWidget(self.remove_port_btn, 1, 1)
        root.addLayout(actions)

        root.addStretch(1)

        # Estilo sobrio
        self.setStyleSheet(
            """
            QWidget#NodeInspector { background: #1e2024; }
            QLineEdit { background: #0d0f12; color: #c9d1d9; border: 1px solid #2f3338; padding: 4px; }
            QLabel { color: #9da5b4; }
            QPushButton { background: #2d3136; color: #c9d1d9; border: 1px solid #3a3f45; padding: 4px 8px; }
            QPushButton:hover { background: #383d43; }
            QFrame { background: #2f3338; }
            """
        )

    def set_node(self, node):
        self._node = node
        if node is None:
            self.title_edit.setText("")
            self.type_label.setText("-")
            self.in_count.setText("0")
            self.out_count.setText("0")
            self._updating_content = True
            try:
                self.content_edit.clear()
            finally:
                self._updating_content = False
            self.setEnabled(False)
            return

        self.setEnabled(True)
        title = getattr(node, "title", "")
        node_type = getattr(node, "node_type", "-")
        self.title_edit.setText(title)
        self.type_label.setText(str(node_type))
        # Cargar contenido
        self._updating_content = True
        try:
            content = node.to_plain_text() if hasattr(node, 'to_plain_text') else getattr(node, 'content', '')
            self.content_edit.setPlainText(content)
        except Exception:
            self.content_edit.setPlainText(getattr(node, 'content', ''))
        finally:
            self._updating_content = False

        try:
            ins = getattr(node, "input_ports", [])
            outs = getattr(node, "output_ports", [])
            self.in_count.setText(str(len(ins)))
            self.out_count.setText(str(len(outs)))
        except Exception:
            self.in_count.setText("-")
            self.out_count.setText("-")

    def _apply_title(self):
        if not self._node:
            return
        try:
            new_title = (self.title_edit.text() or "").strip()
            self._node.title = new_title
            if hasattr(self._node, "_refresh_title_text"):
                self._node._refresh_title_text()
            self._node.update()
        except Exception:
            pass

    def _apply_content(self):
        if not self._node or self._updating_content:
            return
        try:
            text = self.content_edit.toPlainText()
        except Exception:
            text = ""
        try:
            if hasattr(self._node, 'update_from_text'):
                self._node.update_from_text(text)
            else:
                self._node.content = text
            self._node.update()
        except Exception:
            pass

    def _add_port(self, port_type: str):
        if not self._node:
            return
        try:
            default = "input" if port_type == "input" else "output"
            name, ok = QInputDialog.getText(self, f"Añadir puerto {port_type}", "Nombre del puerto:", text=default)
        except Exception:
            ok = False
            name = ""
        if ok and name:
            try:
                if port_type == "input" and hasattr(self._node, "add_input_port"):
                    self._node.add_input_port((name or "").strip())
                elif port_type == "output" and hasattr(self._node, "add_output_port"):
                    self._node.add_output_port((name or "").strip())
                self.set_node(self._node)
            except Exception:
                pass

    def _rename_port(self):
        if not self._node:
            return
        # Elegir tipo de puerto
        try:
            port_type = "input"  # por defecto
            # Simple: alternar si no hay IN
            if not getattr(self._node, "input_ports", []):
                port_type = "output"
            ports = self._node.input_ports if port_type == "input" else self._node.output_ports
            names = [p.get("name", "") for p in ports] or []
            if not names:
                return
            old_name, ok_old = QInputDialog.getItem(self, "Puerto a renombrar", "Selecciona puerto:", names, 0, False)
        except Exception:
            ok_old = False
            old_name = ""
        if not ok_old or not old_name:
            return
        try:
            new_name, ok_new = QInputDialog.getText(self, "Nuevo nombre", "Nombre del puerto:", text=old_name)
        except Exception:
            ok_new = False
            new_name = old_name
        if ok_new and new_name:
            try:
                if hasattr(self._node, "rename_port"):
                    self._node.rename_port(old_name, (new_name or "").strip(), port_type)
                self.set_node(self._node)
            except Exception:
                pass

    def _remove_port(self):
        if not self._node:
            return
        # Elegir tipo y puerto
        try:
            # Selección de tipo
            types = ["input", "output"]
            port_type, ok_type = QInputDialog.getItem(self, "Tipo de puerto", "Selecciona tipo:", types, 0, False)
        except Exception:
            ok_type = False
            port_type = "input"
        if not ok_type:
            return
        try:
            ports = self._node.input_ports if port_type == "input" else self._node.output_ports
            names = [p.get("name", "") for p in ports] or []
            if not names:
                return
            name, ok_name = QInputDialog.getItem(self, "Eliminar puerto", "Selecciona puerto:", names, 0, False)
        except Exception:
            ok_name = False
            name = ""
        if ok_name and name:
            try:
                if hasattr(self._node, "remove_port"):
                    self._node.remove_port(name, port_type)
                self.set_node(self._node)
            except Exception:
                pass