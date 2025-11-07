from __future__ import annotations

from typing import Dict, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from ..ui.text_editor import TextEditor
from ..graph.node_item import NodeItem


class OutputPreviewWindow(QtWidgets.QMainWindow):
    """Ventana de preview en vivo para todos los nodos de tipo Output.

    - Crea pestañas por cada nodo Output presente en la escena.
    - Se actualiza automáticamente cuando el grafo se evalúa.
    - Muestra los valores que llegan al/los puertos de entrada del Output.
    """

    def __init__(self, node_view, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Preview de Outputs")
        self.resize(800, 500)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self._node_view = node_view

        # Tabs por cada nodo Output (cada pestaña contiene subpestañas: Realtime y Auto)
        self.tabs = QtWidgets.QTabWidget(self)
        self.setCentralWidget(self.tabs)

        # Barra de herramientas para control de modo Auto
        self._toolbar = QtWidgets.QToolBar(self)
        self._toolbar.setMovable(False)
        self._toolbar.setFloatable(False)
        self.addToolBar(QtCore.Qt.TopToolBarArea, self._toolbar)
        act_process = QtGui.QAction("Procesar ahora", self)
        act_process.triggered.connect(self._snapshot_all_outputs)
        self._toolbar.addAction(act_process)
        self._auto_follow = False
        self._toggle_follow = QtGui.QAction("Auto (seguir)", self)
        self._toggle_follow.setCheckable(True)
        self._toggle_follow.toggled.connect(self._set_auto_follow)
        self._toolbar.addAction(self._toggle_follow)
        act_clear = QtGui.QAction("Limpiar Auto", self)
        act_clear.triggered.connect(self._clear_auto_outputs)
        self._toolbar.addAction(act_clear)

        # Mapa: nodo -> { 'realtime': TextEditor, 'auto': TextEditor }
        self._editors: Dict[NodeItem, Dict[str, TextEditor]] = {}
        # Mapa: nodo -> widget contenedor de su pestaña superior
        self._tab_widgets: Dict[NodeItem, QtWidgets.QWidget] = {}

        # Timer de refresco en vivo (fallback por si alguna señal no llega)
        self._live_timer = QtCore.QTimer(self)
        self._live_timer.setInterval(200)
        self._live_timer.timeout.connect(self.refresh_contents)
        try:
            self._live_timer.start()
        except Exception:
            pass

        # Actualización inicial y conexión a señales
        self.refresh_tabs()
        try:
            self._node_view.graphEvaluated.connect(self.refresh_tabs)
            self._node_view.graphEvaluated.connect(self.refresh_contents)
        except Exception:
            pass

    def _collect_outputs(self) -> list:
        try:
            scene = getattr(self._node_view, "_scene", None)
            items = list(scene.items()) if scene else []
            return [
                it for it in items
                if isinstance(it, NodeItem) and str(getattr(it, 'node_type', '')).lower() in ('output', 'group_output')
            ]
        except Exception:
            return []

    def refresh_tabs(self) -> None:
        """Sincroniza las pestañas con los nodos Output presentes."""
        outputs = self._collect_outputs()
        existing_nodes = set(self._editors.keys())
        desired_nodes = set(outputs)

        # Eliminar pestañas de nodos que ya no existen
        for removed in existing_nodes - desired_nodes:
            self._editors.pop(removed, None)
            w = self._tab_widgets.pop(removed, None)
            if w is not None:
                for i in range(self.tabs.count()):
                    if self.tabs.widget(i) is w:
                        self.tabs.removeTab(i)
                        break

        # Agregar pestañas nuevas (cada una con subpestañas Realtime/Auto)
        for node in desired_nodes - existing_nodes:
            container = QtWidgets.QWidget()
            lay = QtWidgets.QVBoxLayout(container)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(0)
            mode_tabs = QtWidgets.QTabWidget(container)
            lay.addWidget(mode_tabs)

            rt = TextEditor()
            rt.setReadOnly(True)
            rt.setPlaceholderText("Esperando evaluación del grafo…")
            au = TextEditor()
            au.setReadOnly(True)
            au.setPlaceholderText("Aún no procesado. Usa ‘Procesar ahora’.")
            mode_tabs.addTab(rt, "Realtime")
            mode_tabs.addTab(au, "Auto")
            self._editors[node] = {"realtime": rt, "auto": au}
            self._tab_widgets[node] = container

            title = str(getattr(node, 'title', 'Output') or 'Output')
            self.tabs.addTab(container, title)

        # Actualizar títulos por si cambian
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            node = next((n for n, tw in self._tab_widgets.items() if w is tw), None)
            if node is not None:
                self.tabs.setTabText(i, str(getattr(node, 'title', 'Output') or 'Output'))

        # Rellenar contenidos actuales
        self.refresh_contents()

    def closeEvent(self, event) -> None:
        """Detiene el refresco en vivo al cerrar la ventana."""
        try:
            if hasattr(self, '_live_timer') and self._live_timer is not None:
                self._live_timer.stop()
        except Exception:
            pass
        super().closeEvent(event)

    def refresh_contents(self) -> None:
        """Actualiza el texto de TODAS las pestañas de outputs en tiempo real.

        - Ya no requiere selección: siempre refleja los valores actuales
          que llegan a cada nodo Output.
        - Mantiene fallback al contenido del nodo cuando no hay entradas.
        """
        for node, editors in list(self._editors.items()):
            try:
                parts = []
                for p in (getattr(node, 'input_ports', []) or []):
                    name = p.get('name', 'input')
                    val = (getattr(node, 'input_values', {}) or {}).get(name, None)
                    if val is None:
                        continue
                    if isinstance(val, list):
                        for sv in val:
                            if sv is not None:
                                parts.append(str(sv))
                    else:
                        parts.append(str(val))
                text = "\n".join(parts)
                # Fallback: si no hay entradas, usar el contenido actual del nodo
                if not text:
                    try:
                        text = node.to_plain_text()
                    except Exception:
                        text = str(getattr(node, 'content', '') or '')
                # Mostrar placeholder solo si está vacío y no hay nada que mostrar
                if not text:
                    editors['realtime'].setPlaceholderText("Sin datos de entrada…")
                editors['realtime'].setPlainText(text)
                # Desplazar al final para ver cambios recientes
                cur = editors['realtime'].textCursor()
                cur.movePosition(QtGui.QTextCursor.End)
                editors['realtime'].setTextCursor(cur)

                # Modo Auto: actualizar solo si seguimiento activo
                if getattr(self, '_auto_follow', False):
                    editors['auto'].setPlainText(text)
            except Exception:
                pass

    # ---- Utilidades de Auto ----
    def _snapshot_all_outputs(self) -> None:
        """Captura el estado actual de Realtime en todas las pestañas Auto."""
        for node, editors in list(self._editors.items()):
            try:
                editors['auto'].setPlainText(editors['realtime'].toPlainText())
            except Exception:
                pass

    def _set_auto_follow(self, enabled: bool) -> None:
        self._auto_follow = bool(enabled)

    def _clear_auto_outputs(self) -> None:
        for node, editors in list(self._editors.items()):
            try:
                editors['auto'].clear()
                editors['auto'].setPlaceholderText("Aún no procesado. Usa ‘Procesar ahora’.")
            except Exception:
                pass


__all__ = ["OutputPreviewWindow"]