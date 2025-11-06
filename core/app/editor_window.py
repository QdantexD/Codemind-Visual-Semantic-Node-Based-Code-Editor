from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QFileDialog, QMessageBox, QSplitter, QStatusBar, QLabel, QTextEdit, QTabWidget, QPushButton, QCheckBox
)
from PySide6.QtCore import QTimer
from ..graph.node_item import NodeItem
from PySide6.QtGui import QAction  # ✅ Correcto
from PySide6.QtCore import Qt, QTimer, QEvent
import importlib
import logging

logger = logging.getLogger("core.editor_window")


class EditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor de Texto y Nodos")
        self._current_node = None
        self._editing_mode = False
        self._updating_text = False
        self._node_controller = None
        self._inline_editor_node = None

        central = QWidget(self)
        # Splitter externo: Explorer | panel principal
        self.outer_splitter = QSplitter(Qt.Horizontal, central)
        self.outer_splitter.setChildrenCollapsible(False)
        self.outer_splitter.setHandleWidth(8)
        self._sidebar_collapsed = False
        self._sidebar_last_size = 240

        # --- Sidebar Explorer estilo VS Code ---
        try:
            from ..ui.file_explorer import FileExplorer
            self.file_explorer = FileExplorer()
            self.file_explorer.setMinimumWidth(220)
            self.file_explorer.file_opened.connect(self._on_file_opened)
            self.outer_splitter.addWidget(self.file_explorer)
        except Exception:
            self.file_explorer = None
            placeholder_sidebar = QWidget()
            placeholder_sidebar.setMinimumWidth(180)
            self.outer_splitter.addWidget(placeholder_sidebar)

        # --- Panel principal: editor de texto + NodeView + Inspector ---
        main_panel = QWidget()
        self.inner_splitter = QSplitter(Qt.Horizontal, main_panel)
        self.inner_splitter.setChildrenCollapsible(False)
        self.inner_splitter.setHandleWidth(6)

        # --- Panel izquierdo: editor de texto + barra de vista previa ---
        from ..ui.text_editor import TextEditor, PythonHighlighter
        left_panel = QWidget()
        left_vbox = QVBoxLayout(left_panel)
        left_vbox.setContentsMargins(0, 0, 0, 0)
        left_vbox.setSpacing(0)

        # Editor principal
        self.text_editor = TextEditor()
        self.text_editor.setPlaceholderText(
            "Selecciona un nodo para ver su contenido. Doble‑click para editar."
        )
        # Resaltado sintáctico básico (Python por ahora)
        try:
            self._syntax = PythonHighlighter(self.text_editor.document())
        except Exception:
            self._syntax = None
        self.text_editor.textChanged.connect(self.on_text_changed)
        left_vbox.addWidget(self.text_editor)

        # Visor inferior con pestañas estilo Houdini
        try:
            self.viewer_tabs = QTabWidget()
            self.viewer_tabs.setTabPosition(QTabWidget.South)
            self.viewer_tabs.setDocumentMode(True)
            self.viewer_tabs.setStyleSheet("QTabWidget::pane{border-top:1px solid #2a2f39;} QTabBar::tab{padding:6px 10px;}")
            # Pestaña Selección
            self.preview_selected = QTextEdit()
            self.preview_selected.setReadOnly(True)
            self.preview_selected.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            self.preview_selected.setContextMenuPolicy(Qt.NoContextMenu)
            self.preview_selected.setPlaceholderText("Selección: vista previa de nodo (solo lectura)")
            self.preview_selected.setStyleSheet("QTextEdit{background:#121417;color:#cdd7e1;font:11px 'Consolas','Segoe UI',monospace;padding:6px;}")
            # Pestaña Outputs (todos)
            self.preview_outputs = QTextEdit()
            self.preview_outputs.setReadOnly(True)
            self.preview_outputs.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            self.preview_outputs.setContextMenuPolicy(Qt.NoContextMenu)
            self.preview_outputs.setPlaceholderText("Outputs: combinación de todos los nodos Output")
            self.preview_outputs.setStyleSheet("QTextEdit{background:#0f1318;color:#d7e3f0;font:11px 'Consolas','Segoe UI',monospace;padding:6px;}")
            self.viewer_tabs.addTab(self.preview_selected, "Selección")
            self.viewer_tabs.addTab(self.preview_outputs, "Outputs")
            self.viewer_tabs.setMaximumHeight(170)
            left_vbox.addWidget(self.viewer_tabs)
            # Botón rápido para guardar el combinado como nodo
            self._save_combined_btn = QPushButton("Guardar combinado → Nodo")
            self._save_combined_btn.setStyleSheet("QPushButton{background:#1d2330;color:#cbd5e1;border:1px solid #2a2f39;padding:4px 8px;} QPushButton:hover{background:#20283a;}")
            self._save_combined_btn.clicked.connect(self._save_combined_as_node)
            left_vbox.addWidget(self._save_combined_btn)
            # Toggle: combinar todos los nodos en Outputs
            self._combine_all_mode = False
            self._combine_all_toggle = QCheckBox("Combinar todo")
            self._combine_all_toggle.setToolTip("Combina el texto de todos los nodos y lo muestra en Outputs")
            self._combine_all_toggle.toggled.connect(self._on_combine_all_toggled)
            left_vbox.addWidget(self._combine_all_toggle)
            # Toggle: combinar por camino hacia el Output seleccionado
            self._combine_by_path_toggle = QCheckBox("Por camino al Output")
            self._combine_by_path_toggle.setToolTip("Combina sólo los nodos conectados aguas arriba del Output seleccionado, en orden de flujo")
            self._combine_by_path_toggle.toggled.connect(lambda *_: self._update_outputs_tab())
            left_vbox.addWidget(self._combine_by_path_toggle)

            # Timers de debounce para mejorar rendimiento
            self._outputs_update_timer = QTimer(self)
            self._outputs_update_timer.setSingleShot(True)
            # Intervalo más corto para respuesta visual rápida
            self._outputs_update_timer.setInterval(60)
            self._outputs_update_timer.timeout.connect(self._update_outputs_tab)

            self._graph_eval_timer = QTimer(self)
            self._graph_eval_timer.setSingleShot(True)
            # Evaluación más ágil pero protegida contra ráfagas
            self._graph_eval_timer.setInterval(35)
            self._graph_eval_timer.timeout.connect(self._evaluate_graph_safe)
        except Exception:
            # Fallback a barra simple si falla la creación de tabs
            self.preview_bar = QTextEdit()
            try:
                self.preview_bar.setReadOnly(True)
                self.preview_bar.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
                self.preview_bar.setContextMenuPolicy(Qt.NoContextMenu)
                self.preview_bar.setMaximumHeight(140)
                self.preview_bar.setPlaceholderText("Vista previa del nodo seleccionado (solo lectura)")
                self.preview_bar.setStyleSheet(
                    "QTextEdit{background:#121417;color:#cdd7e1;border-top:1px solid #2a2f39;font:11px 'Consolas','Segoe UI',monospace;padding:6px;}"
                )
            except Exception:
                pass
            left_vbox.addWidget(self.preview_bar)

        self.inner_splitter.addWidget(left_panel)

        # Nodo actualmente editado
        self.current_node = None

        # --- Panel derecho: NodeView ---
        self.node_view = self._load_node_view()
        self.inner_splitter.addWidget(self.node_view)
        # Actualizar pestaña Outputs cuando se evalúe el grafo
        try:
            # Usar debounce para refrescar Outputs tras evaluar el grafo
            self.node_view.graphEvaluated.connect(self._schedule_update_outputs)
            # Inicializar la pestaña Outputs al arrancar (puede perderse la
            # primera emisión si NodeView evalúa antes de conectar la señal)
            self._schedule_update_outputs()
        except Exception:
            pass
        
        # Inspector (derecha)
        try:
            from ..ui.node_inspector import NodeInspector
            self.node_inspector = NodeInspector()
        except Exception:
            self.node_inspector = QWidget()
        self.node_inspector.setMinimumWidth(220)
        self.inner_splitter.addWidget(self.node_inspector)
        try:
            self.inner_splitter.setSizes([360, 820, 260])
        except Exception:
            pass
        # Colocar el splitter interno dentro del panel principal
        main_layout = QHBoxLayout(main_panel)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.inner_splitter)
        self.outer_splitter.addWidget(main_panel)
        # Tamaños iniciales: sidebar más estrecha
        try:
            self.outer_splitter.setSizes([self._sidebar_last_size, 900])
        except Exception:
            pass
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.outer_splitter)
        self.setCentralWidget(central)

        # --- Toolbar ---
        self._setup_toolbar()

        # --- Status bar ---
        self._setup_status_bar()

        # Interceptar TAB a nivel global para menú estilo Houdini
        try:
            from PySide6.QtWidgets import QApplication
            QApplication.instance().installEventFilter(self)
        except Exception:
            pass

        # --- Timer de edición ---
        # Se elimina el cierre automático por temporizador para evitar
        # que el modo edición se "suelte" o cierre inesperadamente.
        self._editing_timer = None

    # ------------------------------
    # Toggle minimalista: ocultar/mostrar Explorer
    # ------------------------------
    def _toggle_sidebar(self):
        try:
            sizes = self.outer_splitter.sizes()
            total = sum(sizes) if sizes else 1140
            if not self._sidebar_collapsed:
                # Colapsar: guardar tamaño actual y ocultar
                self._sidebar_last_size = max(180, sizes[0]) if sizes else self._sidebar_last_size
                if self.file_explorer:
                    self.file_explorer.setVisible(False)
                self.outer_splitter.setSizes([0, total])
                self._sidebar_collapsed = True
                if hasattr(self, "_sidebar_toggle_action"):
                    self._sidebar_toggle_action.setText("Mostrar Explorer")
            else:
                # Expandir: restaurar tamaño
                if self.file_explorer:
                    self.file_explorer.setVisible(True)
                left = min(self._sidebar_last_size, total - 200)
                self.outer_splitter.setSizes([left, max(200, total - left)])
                self._sidebar_collapsed = False
                if hasattr(self, "_sidebar_toggle_action"):
                    self._sidebar_toggle_action.setText("Ocultar Explorer")
        except Exception:
            pass

    # ------------------------------
    # Abrir archivo del Explorer como nodo
    # ------------------------------
    def _on_file_opened(self, file_path: str):
        try:
            # Leer contenido del archivo
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir el archivo:\n{e}")
            return

        # Crear nodo en el centro de la vista con nombre del archivo
        try:
            import os
            title = os.path.basename(file_path)
            center = self.node_view.mapToScene(self.node_view.viewport().rect().center())
            node = self.node_view.add_node_with_ports(
                title=title,
                x=center.x(),
                y=center.y(),
                node_type="input",
                inputs=["input"],
                outputs=["output"],
                content=text,
            )
            node.setSelected(True)
            self.node_view.centerOn(node)
        except Exception:
            # Fallback mínimo
            self.node_view.add_node(title=title, x=0, y=0, node_type="generic", content=text)

    # -----------------------------
    # Node Controller
    # ------------------------------
    def set_node_controller(self, controller):
        """Establece el controlador de nodos."""
        self._node_controller = controller
        logger.info("Controlador de nodos establecido")

    # ------------------------------
    # NodeView dinámico
    # ------------------------------
    def _load_node_view(self):
        try:
            from ..graph.node_view import NodeView
            node_view = NodeView()
            node_view.selectedNodeChanged.connect(self.on_node_selected)
            node_view.editNodeRequested.connect(self.start_edit_node)
            # Sincronizar salida de edición desde el botón dentro del nodo
            node_view.editingExited.connect(self._on_node_edit_exited)
            logger.info("NodeView cargado correctamente")
            return node_view
        except Exception as e:
            logger.exception("No se pudo cargar NodeView: %s", e)
            placeholder = QTextEdit()
            placeholder.setReadOnly(True)
            placeholder.setPlainText(
                f"NodeView no disponible.\n\nRazón:\n{e}\n\nRevisa editor.log para más detalles."
            )
            placeholder.setMinimumSize(400, 300)
            return placeholder

    # ------------------------------
    # Toolbar
    # ------------------------------
    def _setup_toolbar(self):
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        edit_toggle = QAction("Editar nodo", self)
        edit_toggle.setShortcut("Ctrl+E")
        edit_toggle.triggered.connect(self.toggle_edit_mode)
        toolbar.addAction(edit_toggle)
        self._edit_toggle_action = edit_toggle

        save_action = QAction("Guardar nodo", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_node_from_editor)
        toolbar.addAction(save_action)
        
        save_proj = QAction("Guardar proyecto", self)
        save_proj.triggered.connect(self.save_project)
        toolbar.addAction(save_proj)

        load_proj = QAction("Cargar proyecto", self)
        load_proj.triggered.connect(self.load_project)
        toolbar.addAction(load_proj)

        # Atajo para ampliar la última ventana de conexión
        expand_conn = QAction("Ampliar conexión reciente", self)
        expand_conn.setShortcut("Ctrl+M")
        expand_conn.triggered.connect(self._expand_last_connection_editor)
        toolbar.addAction(expand_conn)

        # Toggle Explorer minimalista (como VS Code: Ctrl+B)
        sidebar_toggle = QAction("Ocultar Explorer", self)
        sidebar_toggle.setShortcut("Ctrl+B")
        sidebar_toggle.triggered.connect(self._toggle_sidebar)
        toolbar.addAction(sidebar_toggle)
        self._sidebar_toggle_action = sidebar_toggle

        # Toggle Minimapa
        minimap_toggle = QAction("Minimapa", self)
        minimap_toggle.setCheckable(True)
        minimap_toggle.setChecked(True)
        minimap_toggle.setShortcut("N")
        minimap_toggle.triggered.connect(self._toggle_minimap)
        toolbar.addAction(minimap_toggle)
        self._minimap_toggle_action = minimap_toggle

    def _expand_last_connection_editor(self):
        try:
            if hasattr(self, "node_view") and self.node_view:
                self.node_view.open_last_connection_editor(expand=True)
        except Exception:
            logger.exception("No se pudo ampliar la última ventana de conexión")

    def _toggle_minimap(self):
        try:
            if hasattr(self, 'node_view') and hasattr(self.node_view, '_minimap') and self.node_view._minimap is not None:
                vis = self.node_view._minimap.isVisible()
                self.node_view._minimap.setVisible(not vis)
                if not vis:
                    try:
                        self.node_view._update_minimap_fit()
                        self.node_view._layout_minimap()
                    except Exception:
                        pass
        except Exception:
            logger.exception("No se pudo alternar el minimapa")

    # ------------------------------
    # Status bar estilo VS Code
    # ------------------------------
    def _setup_status_bar(self):
        try:
            status = QStatusBar(self)
            self.setStatusBar(status)
            self._lbl_zoom = QLabel("Zoom: 100%")
            self._lbl_sel = QLabel("Selección: 0")
            self._lbl_mode = QLabel("Modo: lectura")
            for w in (self._lbl_zoom, self._lbl_sel, self._lbl_mode):
                w.setStyleSheet("color: #a0a6b0; padding: 0 8px;")
                status.addPermanentWidget(w)
            # Conectar señales desde la vista
            try:
                self.node_view.zoomChanged.connect(self._on_zoom_changed)
                self.node_view.selectionCountChanged.connect(self._on_selection_count)
            except Exception:
                pass
        except Exception:
            pass

    def _on_zoom_changed(self, scale_x: float):
        try:
            pct = int(max(1.0, scale_x) * 100)
            self._lbl_zoom.setText(f"Zoom: {pct}%")
        except Exception:
            pass

    def _on_selection_count(self, count: int):
        try:
            self._lbl_sel.setText(f"Selección: {int(count)}")
        except Exception:
            pass

    # ------------------------------
    # Nodo seleccionado
    # ------------------------------
    def on_node_selected(self, node):
        """Cuando se selecciona un nodo, cargar su contenido en el editor."""
        # Guardar cambios del nodo anterior si existe
        if self.current_node and hasattr(self.current_node, 'update_from_text'):
            try:
                # No hacer commit para nodos Output: su contenido lo controla el runtime/snapshot
                prev_type = str(getattr(self.current_node, 'node_type', '')).lower()
                if prev_type != 'output':
                    current_text = self.text_editor.toPlainText()
                    self.current_node.update_from_text(current_text)
            except Exception:
                pass

        # Desconectar editor incrustado previo si existía
        self._disconnect_inline_editor_signals()

        # Si no hay nodo, limpiar
        if node is None:
            self.on_node_deselected()
            return

        # Establecer nuevo nodo actual
        self.current_node = node
        self._clear_previous_node()
        self._current_node = node
        self._editing_mode = False
        
        # Mostrar contenido del nodo en modo sólo lectura
        self._updating_text = True
        try:
            content = node.to_plain_text() if hasattr(node, 'to_plain_text') else getattr(node, 'content', '')
            self.text_editor.setPlainText(content)
        except Exception:
            self.text_editor.setPlainText(getattr(node, 'content', ''))
        self.text_editor.setReadOnly(True)
        self.text_editor.setEnabled(True)
        # Actualizar barra de vista previa compacta
        try:
            self._update_preview_bar(node)
        except Exception:
            pass
        # Mantener sincronizada la pestaña de Outputs al cambiar la selección
        try:
            self._schedule_update_outputs()
        except Exception:
            pass
        self.setWindowTitle(f"Seleccionado: {getattr(node, 'title', 'Node')}")
        self._updating_text = False
        # Actualizar texto de acción
        if hasattr(self, "_edit_toggle_action"):
            self._edit_toggle_action.setText("Editar nodo")
        # Actualizar Inspector
        try:
            if hasattr(self, "node_inspector") and self.node_inspector:
                self.node_inspector.set_node(node)
        except Exception:
            pass

    def on_node_deselected(self):
        """Cuando se deselecciona un nodo, limpia el editor."""
        # Guardar cambios del nodo anterior si existe
        if self.current_node and hasattr(self.current_node, 'update_from_text'):
            try:
                prev_type = str(getattr(self.current_node, 'node_type', '')).lower()
                if prev_type != 'output':
                    current_text = self.text_editor.toPlainText()
                    self.current_node.update_from_text(current_text)
            except Exception:
                pass
        
        # Limpiar nodo actual
        self.current_node = None
        self.text_editor.setPlainText('')
        self.text_editor.setEnabled(False)
        try:
            if hasattr(self, "node_inspector") and self.node_inspector:
                self.node_inspector.set_node(None)
        except Exception:
            pass
        # Refrescar pestaña Outputs aunque no haya selección
        try:
            self._schedule_update_outputs()
        except Exception:
            pass

    def _clear_previous_node(self):
        if self._current_node and hasattr(self._current_node, "set_editing"):
            try:
                self._current_node.set_editing(False)
            except Exception:
                pass
        self._disconnect_inline_editor_signals()

    def _update_text_editor_preview(self):
        """Mantener compatibilidad: muestra el contenido actual en modo lectura."""
        self._updating_text = True
        if self._current_node is None:
            self.text_editor.clear()
            self.text_editor.setReadOnly(True)
            self.text_editor.setEnabled(False)
            self.setWindowTitle("Editor de Texto y Nodos")
            try:
                if hasattr(self, 'preview_selected'):
                    self.preview_selected.clear()
                if hasattr(self, 'preview_outputs'):
                    self.preview_outputs.clear()
            except Exception:
                pass
        else:
            try:
                content = self._current_node.to_plain_text() if hasattr(self._current_node, 'to_plain_text') else getattr(self._current_node, 'content', '')
                self.text_editor.setPlainText(content)
            except Exception:
                self.text_editor.setPlainText(getattr(self._current_node, 'content', ''))
            self.text_editor.setReadOnly(True)
            self.text_editor.setEnabled(True)
            try:
                self._update_preview_bar(self._current_node)
                self._schedule_update_outputs()
            except Exception:
                pass
            self.setWindowTitle(f"Seleccionado: {getattr(self._current_node, 'title', 'Node')}")
        self._updating_text = False

    def _update_preview_bar(self, node):
        """Actualiza el visor inferior con la vista previa de Selección."""
        try:
            if node is None:
                if hasattr(self, 'preview_selected'):
                    self.preview_selected.clear()
                elif hasattr(self, 'preview_bar'):
                    self.preview_bar.clear()
                return
            content = node.to_plain_text() if hasattr(node, 'to_plain_text') else getattr(node, 'content', '')
            target = getattr(self, 'preview_selected', None)
            if target is None:
                target = getattr(self, 'preview_bar', None)
            if target:
                target.setPlainText(content or "")
        except Exception:
            try:
                target = getattr(self, 'preview_selected', None)
                if target is None:
                    target = getattr(self, 'preview_bar', None)
                if target:
                    target.setPlainText(getattr(node, 'content', ''))
            except Exception:
                pass

    def _update_outputs_tab(self):
        """Combina el contenido de todos los nodos Output y lo muestra en pestaña Outputs."""
        try:
            target = getattr(self, 'preview_outputs', None)
            if target is None:
                return
            if not hasattr(self.node_view, '_scene'):
                target.clear()
                return
            # Importante: no reevaluar aquí para evitar recursión con la señal graphEvaluated
            # Modo: combinar todos los nodos vs sólo outputs
            combine_all = False
            try:
                combine_all = bool(getattr(self, '_combine_all_mode', False) or (getattr(self, '_combine_all_toggle', None) and self._combine_all_toggle.isChecked()))
            except Exception:
                combine_all = False
            # Modo: por camino al Output seleccionado
            combine_by_path = False
            try:
                combine_by_path = bool(getattr(self, '_combine_by_path_toggle', None) and self._combine_by_path_toggle.isChecked())
            except Exception:
                combine_by_path = False
            parts = []
            items = []
            if combine_by_path:
                # Buscar Output seleccionado o el primero
                out_node = self._find_selected_output_or_first()
                if out_node is not None:
                    # En modo camino, mostrar directamente el valor que LLEGA al Output
                    final_text = self._get_node_display_text(out_node, prefer_input_for_output=True)
                    parts = [str(final_text)] if final_text else []
                    items = []
            if not items:
                # Fallback según modos existentes
                items = [it for it in self.node_view._scene.items() if isinstance(it, NodeItem)]
                try:
                    items.sort(key=lambda it: getattr(it, 'pos')().x() if hasattr(it, 'pos') else 0.0)
                except Exception:
                    pass
            for it in items:
                try:
                    if getattr(it, 'is_snapshot', False):
                        continue
                    txt = self._get_node_display_text(it, prefer_input_for_output=False)
                    if txt:
                        parts.append(str(txt))
                except Exception:
                    pass
            combined = "\n".join(parts)
            # Evitar trabajo de UI si el texto no cambió
            if getattr(self, '_last_outputs_text', None) != combined:
                self._last_outputs_text = combined
                try:
                    prev_upd = target.updatesEnabled()
                    target.setUpdatesEnabled(False)
                except Exception:
                    prev_upd = True
                prev_block = False
                try:
                    prev_block = target.blockSignals(True)
                except Exception:
                    pass
                try:
                    target.setPlainText(combined)
                finally:
                    try:
                        target.blockSignals(prev_block)
                    except Exception:
                        pass
                    try:
                        target.setUpdatesEnabled(prev_upd)
                    except Exception:
                        pass
            # Si el usuario activó "Combinar todo", reflejar en un nodo Output dedicado
            try:
                if combine_all or combine_by_path:
                    # Evitar trabajo si no hay cambios
                    if getattr(self, '_last_combined_text', None) != combined:
                        self._last_combined_text = combined
                        self._sync_combined_to_output_node(combined)
            except Exception:
                pass
        except Exception:
            try:
                getattr(self, 'preview_outputs', QTextEdit()).clear()
            except Exception:
                pass

    def _on_combine_all_toggled(self, checked: bool):
        try:
            self._combine_all_mode = bool(checked)
            self._schedule_update_outputs()
        except Exception:
            pass

    def _sync_combined_to_output_node(self, combined_text: str):
        """Refleja el texto combinado en un nodo Output con título 'Output Combined'.
        Si no existe, crea uno como snapshot y lo centra.
        """
        try:
            if not hasattr(self.node_view, '_scene'):
                return
            # Buscar nodo Output con título específico
            target_node = None
            for it in self.node_view._scene.items():
                try:
                    if str(getattr(it, 'node_type', '')).lower() == 'output' and str(getattr(it, 'title', '')) == 'Output Combined':
                        target_node = it
                        break
                except Exception:
                    pass
            if target_node is None:
                # Crear uno nuevo centrado
                center = self.node_view.mapToScene(self.node_view.viewport().rect().center())
                target_node = self.node_view.add_node(title="Output Combined", x=center.x(), y=center.y(), node_type="output", content=combined_text)
                try:
                    setattr(target_node, 'is_snapshot', True)
                    if hasattr(target_node, '_refresh_title_text'):
                        target_node._refresh_title_text()
                except Exception:
                    pass
                target_node.setSelected(True)
                self.node_view.centerOn(target_node)
            else:
                # Actualizar contenido del existente, manteniendo snapshot
                try:
                    if hasattr(target_node, 'update_from_text'):
                        target_node.update_from_text(combined_text)
                    else:
                        target_node.content = combined_text
                except Exception:
                    pass
                try:
                    setattr(target_node, 'is_snapshot', True)
                    if hasattr(target_node, '_refresh_title_text'):
                        target_node._refresh_title_text()
                except Exception:
                    pass
        except Exception:
            pass

    def _schedule_update_outputs(self):
        try:
            timer = getattr(self, '_outputs_update_timer', None)
            if timer:
                # Leading-edge: primera actualización inmediata, luego throttle
                if not timer.isActive():
                    try:
                        self._update_outputs_tab()
                    except Exception:
                        pass
                timer.start()
            else:
                self._update_outputs_tab()
        except Exception:
            try:
                self._update_outputs_tab()
            except Exception:
                pass

    def _schedule_evaluate_graph(self):
        try:
            timer = getattr(self, '_graph_eval_timer', None)
            if timer:
                # Leading-edge: evaluar inmediatamente si no hay otro en curso
                if not timer.isActive():
                    try:
                        self._evaluate_graph_safe()
                    except Exception:
                        pass
                timer.start()
            else:
                self._evaluate_graph_safe()
        except Exception:
            self._evaluate_graph_safe()

    def _evaluate_graph_safe(self):
        try:
            if hasattr(self, 'node_view') and self.node_view:
                self.node_view.evaluate_graph()
        except Exception:
            pass

    def _find_selected_output_or_first(self):
        try:
            # Preferir Output seleccionado
            selected = []
            try:
                selected = [it for it in self.node_view._scene.selectedItems()]
            except Exception:
                selected = []
            for it in selected:
                try:
                    if str(getattr(it, 'node_type', '')).lower() == 'output':
                        return it
                except Exception:
                    pass
            # Buscar primer Output en la escena
            for it in self.node_view._scene.items():
                try:
                    if str(getattr(it, 'node_type', '')).lower() == 'output':
                        return it
                except Exception:
                    pass
            return None
        except Exception:
            return None

    def _collect_upstream_nodes_ordered(self, out_node):
        """Devuelve nodos conectados aguas arriba del Output en orden de flujo (fuentes → … → Output)."""
        try:
            conns = list(getattr(self.node_view, 'connections', []) or [])
            # BFS inversa desde el Output para obtener profundidad (distancia al Output)
            depth = {out_node: 0}
            queue = [out_node]
            visited = set([out_node])
            upstream = set()
            while queue:
                cur = queue.pop(0)
                for c in conns:
                    try:
                        if getattr(c, 'end_item', None) is cur:
                            src = getattr(c, 'start_item', None)
                            if src is None:
                                continue
                            upstream.add(src)
                            if src not in visited:
                                visited.add(src)
                                depth[src] = depth.get(cur, 0) + 1
                                queue.append(src)
                    except Exception:
                        pass
            ordered = list(upstream)
            try:
                ordered.sort(key=lambda it: (-depth.get(it, 0), getattr(it, 'pos')().x() if hasattr(it, 'pos') else 0.0))
            except Exception:
                ordered.sort(key=lambda it: -depth.get(it, 0))
            return ordered
        except Exception:
            return []

    def _get_node_display_text(self, node, prefer_input_for_output: bool = True):
        """Devuelve el texto evaluado para mostrar en Outputs.

        - Para `input`, `generic`, `variable`, `process`, usa `output_values` del puerto por defecto.
        - Para `combine`, idem.
        - Para `output`, si `prefer_input_for_output` está activo, usa su `input_values` (lo que recibe);
          si no, y `forward_output` está activo, usa su `output_values`; fallback a contenido.
        """
        try:
            node_type = str(getattr(node, 'node_type', 'generic') or 'generic').lower()
            if node_type == 'output':
                if prefer_input_for_output:
                    # Mostrar lo que llega al Output
                    iv = getattr(node, 'input_values', {}) or {}
                    if iv:
                        # Puerto por defecto 'input' o primero
                        val = iv.get('input', None)
                        if val is None and len(iv) > 0:
                            try:
                                key = next(iter(iv.keys()))
                                val = iv.get(key, None)
                            except Exception:
                                val = None
                        if isinstance(val, (str, bytes)):
                            return val if isinstance(val, str) else val.decode('utf-8', 'ignore')
                        if val is not None:
                            return str(val)
                # Si no se prefiere input o no hay, mostrar salida si reenvía
                try:
                    if getattr(node, 'forward_output', False):
                        ov = getattr(node, 'output_values', {}) or {}
                        if ov:
                            val = ov.get('output', None)
                            if val is None and len(ov) > 0:
                                key = next(iter(ov.keys()))
                                val = ov.get(key, None)
                            return str(val) if val is not None else ''
                except Exception:
                    pass
                # Fallback
                try:
                    return node.to_plain_text()
                except Exception:
                    return getattr(node, 'content', '') or ''

            # No-Output: tomar salida evaluada
            ov = getattr(node, 'output_values', {}) or {}
            if ov:
                val = ov.get('output', None)
                if val is None and len(ov) > 0:
                    try:
                        key = next(iter(ov.keys()))
                        val = ov.get(key, None)
                    except Exception:
                        val = None
                if isinstance(val, (str, bytes)):
                    return val if isinstance(val, str) else val.decode('utf-8', 'ignore')
                if val is not None:
                    return str(val)
            # Fallback a contenido
            try:
                return node.to_plain_text()
            except Exception:
                return getattr(node, 'content', '') or ''
        except Exception:
            return ''

    def _save_combined_as_node(self):
        """Crea un nodo Output con el texto combinado mostrado en pestaña Outputs."""
        try:
            target = getattr(self, 'preview_outputs', None)
            combined = target.toPlainText() if target else ""
            if not combined:
                QMessageBox.information(self, "Sin contenido", "No hay texto combinado para guardar.")
                return
            center = self.node_view.mapToScene(self.node_view.viewport().rect().center())
            node = self.node_view.add_node(title="Output Combined", x=center.x(), y=center.y(), node_type="output", content=combined)
            try:
                # Marcar como snapshot para que el runtime no lo sobrescriba
                setattr(node, 'is_snapshot', True)
                if hasattr(node, '_refresh_title_text'):
                    node._refresh_title_text()
            except Exception:
                pass
            node.setSelected(True)
            self.node_view.centerOn(node)
            # Actualizar visor
            self._update_outputs_tab()
            try:
                # Forzar reevaluación para sincronizar vistas
                self.node_view.evaluate_graph()
            except Exception:
                pass
        except Exception as e:
            logger.exception("No se pudo guardar combinado como nodo: %s", e)
            QMessageBox.warning(self, "Error", f"No se pudo crear el nodo combinado: {e}")

    # ------------------------------
    # Editar nodo
    # ------------------------------
    def start_edit_node(self, node):
        if node is None:
            return
        self._current_node = node
        # Bloquear modo edición para nodos Output: su contenido es controlado por runtime/snapshot
        node_type = str(getattr(node, 'node_type', '')).lower()
        is_output = (node_type == 'output')
        self._editing_mode = not is_output

        # seleccionar nodo en la escena
        if hasattr(self.node_view, "_scene"):
            for it in self.node_view._scene.selectedItems():
                it.setSelected(False)
            node.setSelected(True)

        # actualizar editor
        self._updating_text = True
        try:
            self.text_editor.setPlainText(node.to_plain_text())
        except Exception:
            self.text_editor.setPlainText(getattr(node, "content", ""))
        # Si es Output, mantener lectura; si no, permitir edición
        self.text_editor.setReadOnly(is_output)
        self.text_editor.setEnabled(True)
        self._updating_text = False

        # Sólo marcar edición y conectar señales si no es Output
        if not is_output:
            try:
                node.set_editing(True)
            except Exception:
                pass
            # Conectar señales del editor incrustado del nodo para sincronizar con el lateral
            self._connect_inline_editor_signals(node)

            self.text_editor.setFocus()
            # Actualizar acción
            if hasattr(self, "_edit_toggle_action"):
                self._edit_toggle_action.setText("Salir de edición")
        else:
            # Para Output, reflejar en acción que no se edita
            if hasattr(self, "_edit_toggle_action"):
                self._edit_toggle_action.setText("Editar nodo")

    def on_text_changed(self):
        """Cuando el texto del editor cambia, actualiza el nodo seleccionado."""
        if self._updating_text:
            return
        if self.current_node and hasattr(self.current_node, 'update_from_text'):
            try:
                text = self.text_editor.toPlainText()
                self.current_node.update_from_text(text)
                # Si el nodo está en modo edición y tiene editor incrustado, sincronizarlo
                try:
                    if getattr(self.current_node, '_editing', False) and hasattr(self.current_node, 'content_editor'):
                        editor = self.current_node.content_editor
                        if editor.toPlainText() != text:
                            prev = editor.blockSignals(True)
                            editor.setPlainText(text)
                            editor.blockSignals(prev)
                except Exception:
                    pass
                # Reevaluar grafo usando debounce para refrescar Outputs en tiempo real
                try:
                    self._schedule_evaluate_graph()
                except Exception:
                    pass
            except Exception:
                pass
        # No auto-cerrar edición: el usuario decide salir con el botón o al cambiar de nodo

    def _clear_node_editing_state(self):
        if self._current_node and hasattr(self._current_node, "set_editing"):
            try:
                self._current_node.set_editing(False)
            except Exception:
                pass
        self._disconnect_inline_editor_signals()
        if hasattr(self, "_edit_toggle_action"):
            self._edit_toggle_action.setText("Editar nodo")

    # ------------------------------
    # Guardar nodo
    # ------------------------------
    def save_node_from_editor(self):
        if not self._current_node or not self._editing_mode:
            return
        text = self.text_editor.toPlainText()
        try:
            self._current_node.update_from_text(text)
        except Exception as e:
            logger.exception("Error guardando nodo: %s", e)

        self._editing_mode = False
        self._clear_node_editing_state()
        self._update_text_editor_preview()
        if hasattr(self, "_edit_toggle_action"):
            self._edit_toggle_action.setText("Editar nodo")

    def _on_node_edit_exited(self, node):
        """Salida de edición solicitada desde el propio nodo (botón incrustado)."""
        try:
            # Asegurar referencia al nodo actual
            self._current_node = node
            self.current_node = node
            # Guardar cambios mínimos desde el editor lateral si estaba en modo edición
            # No hacer commit para nodos Output
            node_type = str(getattr(node, 'node_type', '')).lower()
            if node_type != 'output':
                text = self.text_editor.toPlainText()
                try:
                    node.update_from_text(text)
                except Exception:
                    pass
            # Salir de edición y actualizar interfaz
            self._editing_mode = False
            self._clear_node_editing_state()
            self._update_text_editor_preview()
            if hasattr(self, "_edit_toggle_action"):
                self._edit_toggle_action.setText("Editar nodo")
            # Reevaluar grafo tras salir de edición (debounced)
            try:
                self._schedule_evaluate_graph()
            except Exception:
                pass
        except Exception:
            pass

    # ------------------------------
    # Sincronización con editor incrustado en nodo
    # ------------------------------
    def _connect_inline_editor_signals(self, node):
        try:
            if hasattr(node, 'content_editor'):
                node.content_editor.textChanged.connect(self.on_node_inline_text_changed)
                self._inline_editor_node = node
        except Exception:
            pass

    def _disconnect_inline_editor_signals(self):
        try:
            node = getattr(self, '_inline_editor_node', None)
            if node and hasattr(node, 'content_editor'):
                node.content_editor.textChanged.disconnect(self.on_node_inline_text_changed)
        except Exception:
            pass

    # ------------------------------
    # Filtro global de eventos (capturar TAB)
    # ------------------------------
    def eventFilter(self, obj, event):
        try:
            if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
                # Capturar TAB globalmente y abrir el menú de creación en NodeView
                try:
                    if hasattr(self, 'node_view') and self.node_view:
                        self.node_view._show_tab_menu()
                        return True
                except Exception:
                    pass
                # Si falla, no bloquear el evento
                return False
        except Exception:
            pass
        return super().eventFilter(obj, event)
        self._inline_editor_node = None

    def on_node_inline_text_changed(self):
        node = getattr(self, '_inline_editor_node', None)
        if node is None:
            return
        try:
            text = node.content_editor.toPlainText()
        except Exception:
            text = getattr(node, 'content', '')
        # Actualizar editor lateral sin recursión
        self._updating_text = True
        try:
            self.text_editor.setPlainText(text)
        finally:
            self._updating_text = False
        # Actualizar modelo del nodo
        try:
            if hasattr(node, 'update_from_text'):
                node.update_from_text(text)
            else:
                node.content = text
            # Reevaluar grafo (debounced) para reflejar cambios desde el editor incrustado
            try:
                self._schedule_evaluate_graph()
            except Exception:
                pass
        except Exception:
            pass

    # ------------------------------
    # Guardar/Cargar proyecto
    # ------------------------------
    def _collect_models_from_scene(self):
        """Recopila los modelos de todos los nodos y conexiones en la escena."""
        models = []
        connections = []
        try:
            from ..graph.node_item import NodeItem
            from ..graph.node_model import NodeModel
            if not hasattr(self.node_view, "_scene"):
                return models, connections
                
            # Recopilar nodos
            for item in self.node_view._scene.items():
                if isinstance(item, NodeItem):
                    pos = item.scenePos()
                    # Combinar meta semántica con flags de editor
                    base_meta = {}
                    try:
                        if isinstance(getattr(item, "semantic_meta", None), dict):
                            base_meta = dict(getattr(item, "semantic_meta", {}) or {})
                    except Exception:
                        base_meta = {}
                    try:
                        base_meta["is_snapshot"] = bool(getattr(item, "is_snapshot", False))
                        base_meta["forward_output"] = bool(getattr(item, "forward_output", False))
                    except Exception:
                        pass
                    nm = NodeModel(
                        id=getattr(item, "id", str(id(item))),
                        type=getattr(item, "node_type", "generic"),
                        title=getattr(item, "title", ""),
                        x=pos.x(),
                        y=pos.y(),
                        content=getattr(item, "content", ""),
                        meta=base_meta
                    )
                    models.append(nm)
            
            # Recopilar conexiones
            for connection in getattr(self.node_view, 'connections', []):
                conn_data = {
                    'start_node_id': str(id(connection.start_item)),
                    'end_node_id': str(id(connection.end_item)) if connection.end_item else None,
                    'start_port': connection.start_port,
                    'end_port': connection.end_port
                }
                connections.append(conn_data)
                    
        except Exception:
            logger.exception("Error recolectando modelos desde escena")
        return models, connections

    def save_project(self):
        """Guarda el proyecto actual con nodos y conexiones."""
        path, _ = QFileDialog.getSaveFileName(self, "Guardar proyecto", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            import json
            models, connections = self._collect_models_from_scene()
            # Serializar nodos
            try:
                from ..graph.node_model import NodeModel
                nodes_serialized = [m.to_dict() if isinstance(m, NodeModel) else m for m in models]
            except Exception:
                nodes_serialized = [getattr(m, 'to_dict', lambda: {})() for m in models]

            # Vista y UI
            try:
                t = self.node_view.transform()
                view_center = self.node_view.mapToScene(self.node_view.viewport().rect().center())
                view_state = {
                    'transform': {
                        'm11': t.m11(), 'm12': t.m12(), 'm13': t.m13(),
                        'm21': t.m21(), 'm22': t.m22(), 'm23': t.m23(),
                        'm31': t.m31(), 'm32': t.m32(), 'm33': t.m33(),
                    },
                    'center': {'x': float(view_center.x()), 'y': float(view_center.y())}
                }
            except Exception:
                view_state = {}

            try:
                ui_state = {
                    'outer_splitter': self.outer_splitter.sizes(),
                    'inner_splitter': getattr(self, 'inner_splitter', self.outer_splitter).sizes()
                }
            except Exception:
                ui_state = {}

            project_data = {
                'metadata': {
                    'name': getattr(self, 'current_project_name', 'Proyecto'),
                    'version': '1.0'
                },
                'nodes': nodes_serialized,
                'connections': connections,
                'view': view_state,
                'ui': ui_state,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Éxito", f"Proyecto guardado en {path}")
            self.statusBar().showMessage(f'Proyecto guardado: {path}', 2000)
            self.setWindowModified(False)
        except Exception as e:
            logger.exception("Error guardando proyecto: %s", e)
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")
            return False

    def load_project(self):
        """Carga un proyecto desde archivo JSON."""
        path, _ = QFileDialog.getOpenFileName(self, "Cargar proyecto", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            import json
            from ..graph.node_model import project_from_dict
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            nodes = project_from_dict(data)
            if hasattr(self.node_view, "clear_nodes"):
                self.node_view.clear_nodes()
                node_map = {}
                for n in nodes:
                    node = self.node_view.add_node(n.title, n.x, n.y, node_type=n.type, content=n.content)
                    # Restaurar flags/meta
                    try:
                        if isinstance(getattr(n, 'meta', None), dict):
                            setattr(node, 'semantic_meta', dict(n.meta or {}))
                            # Flags del editor
                            setattr(node, 'is_snapshot', bool((n.meta or {}).get('is_snapshot', False)))
                            setattr(node, 'forward_output', bool((n.meta or {}).get('forward_output', False)))
                            if hasattr(node, '_refresh_title_text'):
                                node._refresh_title_text()
                    except Exception:
                        pass
                    node_map[n.id] = node
                # Restaurar conexiones
                for conn_data in data.get('connections', []):
                    start_id = conn_data.get('start_node_id')
                    end_id = conn_data.get('end_node_id')
                    start_port = conn_data.get('start_port', 'output')
                    end_port = conn_data.get('end_port', 'input')
                    if start_id in node_map and end_id in node_map:
                        start_node = node_map[start_id]
                        end_node = node_map[end_id]
                        self.node_view.add_connection(start_node, end_node, start_port, end_port)
                # Restaurar estado de vista
                try:
                    from PySide6.QtGui import QTransform
                    view_data = data.get('view', {})
                    tf = view_data.get('transform')
                    if tf:
                        t = QTransform(
                            float(tf.get('m11', 1)), float(tf.get('m12', 0)), float(tf.get('m13', 0)),
                            float(tf.get('m21', 0)), float(tf.get('m22', 1)), float(tf.get('m23', 0)),
                            float(tf.get('m31', 0)), float(tf.get('m32', 0)), float(tf.get('m33', 1))
                        )
                        self.node_view.setTransform(t)
                    center = view_data.get('center')
                    if center:
                        self.node_view.centerOn(float(center.get('x', 0)), float(center.get('y', 0)))
                except Exception:
                    pass
                # Restaurar UI (tamaños de splitters)
                try:
                    ui_data = data.get('ui', {})
                    outer_sizes = ui_data.get('outer_splitter')
                    inner_sizes = ui_data.get('inner_splitter')
                    if outer_sizes:
                        self.outer_splitter.setSizes(outer_sizes)
                    if inner_sizes and hasattr(self, 'inner_splitter'):
                        self.inner_splitter.setSizes(inner_sizes)
                except Exception:
                    pass
            QMessageBox.information(self, "Éxito", f"Proyecto cargado desde {path}")
        except Exception as e:
            logger.exception("Error cargando proyecto: %s", e)
            QMessageBox.critical(self, "Error", f"No se pudo cargar: {e}")

    def toggle_edit_mode(self):
        """Alterna entre selección (vista previa) y edición del nodo actual."""
        node = self._current_node or getattr(self, 'current_node', None)
        if node is None:
            return
        if not self._editing_mode:
            # Entrar en edición usando flujo existente
            self.start_edit_node(node)
            # Centrar y elevar en la vista
            try:
                self.node_view.centerOn(node)
            except Exception:
                pass
        else:
            # Salir de edición guardando
            self.save_node_from_editor()
