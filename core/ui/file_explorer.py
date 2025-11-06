from PySide6.QtWidgets import (
    QWidget, QTreeView, QVBoxLayout, QFileSystemModel, QMenu, QLineEdit, QLabel
)
from PySide6.QtCore import QDir, Signal, Qt
from PySide6.QtGui import QIcon
import os

class FileExplorer(QWidget):
    """
    Explorador de archivos avanzado, estilo Visual Studio Code.
    Soporta:
    - Filtros dinámicos por extensión o nombre
    - Iconos por tipo de archivo
    - Menú contextual para abrir, renombrar y eliminar
    - Señal para abrir archivos en un editor externo o pestañas internas
    """
    file_opened = Signal(str)

    def __init__(self, root_path=None):
        super().__init__()

        self.root_path = root_path or QDir.currentPath()
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        # Campo de búsqueda rápida
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Buscar archivos...")
        self.search_bar.textChanged.connect(self.filter_files)
        self.layout.addWidget(self.search_bar)

        # Etiqueta de ruta actual
        self.path_label = QLabel(f"Explorando: {self.root_path}")
        self.layout.addWidget(self.path_label)

        # Modelo del sistema de archivos
        self.model = QFileSystemModel()
        self.model.setRootPath(self.root_path)
        self.model.setNameFilters(["*.py", "*.txt", "*.json"])
        self.model.setNameFilterDisables(False)  # Ocultar archivos no filtrados

        # Vista de árbol
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.root_path))
        self.tree.setHeaderHidden(True)
        self.tree.doubleClicked.connect(self.on_file_open)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        # Permitir arrastrar archivos hacia NodeView u otras vistas
        try:
            self.tree.setDragEnabled(True)
            self.tree.setDragDropMode(QTreeView.DragOnly)
        except Exception:
            pass

        self.layout.addWidget(self.tree)

        # Iconos por tipo de archivo
        self.icons = {
            ".py": QIcon.fromTheme("application-python"),
            ".txt": QIcon.fromTheme("text-plain"),
            ".json": QIcon.fromTheme("application-json"),
            "folder": QIcon.fromTheme("folder"),
        }

    def filter_files(self, text):
        """
        Filtra archivos que contengan el texto ingresado en el search_bar.
        """
        text = text.lower()
        root_index = self.model.index(self.root_path)
        self._recursive_filter(root_index, text)

    def _recursive_filter(self, index, text):
        """
        Recursivamente muestra/oculta elementos según el filtro.
        """
        if not index.isValid():
            return
        file_name = self.model.fileName(index).lower()
        is_match = text in file_name
        self.tree.setRowHidden(index.row(), index.parent(), not is_match)
        if self.model.isDir(index):
            for i in range(self.model.rowCount(index)):
                child_index = self.model.index(i, 0, index)
                self._recursive_filter(child_index, text)

    def open_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        if not index.isValid():
            return
        menu = QMenu()
        open_action = menu.addAction("Abrir")
        rename_action = menu.addAction("Renombrar")
        delete_action = menu.addAction("Eliminar")
        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        file_path = self.model.filePath(index)
        if action == open_action:
            self.file_opened.emit(file_path)
        elif action == rename_action:
            self.tree.edit(index)
        elif action == delete_action and os.path.exists(file_path):
            if os.path.isdir(file_path):
                os.rmdir(file_path)
            else:
                os.remove(file_path)

    def on_file_open(self, index):
        """
        Señaliza que un archivo ha sido abierto.
        """
        file_path = self.model.filePath(index)
        if os.path.isfile(file_path):
            self.file_opened.emit(file_path)

    def set_root(self, path):
        """
        Cambia la carpeta raíz del explorador y actualiza la vista.
        """
        self.root_path = path
        self.model.setRootPath(path)
        self.tree.setRootIndex(self.model.index(path))
        self.path_label.setText(f"Explorando: {path}")
